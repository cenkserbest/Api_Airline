import os
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import StreamingResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import httpx
from dotenv import load_dotenv

load_dotenv()

from fastapi.middleware.cors import CORSMiddleware

from fastapi.openapi.docs import get_swagger_ui_html

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="API Gateway",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# The target microservice URL
AIRLINE_API_URL = os.getenv("AIRLINE_API_URL", "http://localhost:8001")

async def proxy_request(request: Request, target_url: str):
    async with httpx.AsyncClient() as client:
        # Forward headers, query params, and body
        url = httpx.URL(target_url, path=request.url.path, query=request.url.query.encode("utf-8"))
        body = await request.body()
        headers = dict(request.headers)
        headers.pop("host", None) # Remove host header so httpx sets it correctly
        
        try:
            req = client.build_request(
                method=request.method,
                url=url,
                headers=headers,
                content=body
            )
            response = await client.send(req)
            
            # Filter headers that cause browser decoding crashes when proxied
            proxy_headers = {}
            for k, v in response.headers.items():
                if k.lower() not in ["content-encoding", "content-length", "transfer-encoding", "connection"]:
                    proxy_headers[k] = v
            
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=proxy_headers,
                media_type=response.headers.get("content-type")
            )
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Bad Gateway: Unable to route request to {target_url}")

@app.get("/openapi.json", include_in_schema=False)
async def custom_openapi_schema():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{AIRLINE_API_URL}/openapi.json")
            if response.status_code == 200:
                schema = response.json()
                schema["servers"] = [{"url": "https://airline-api-gateway-duf0bja8hcc8caf5.uaenorth-01.azurewebsites.net", "description": "Azure Production Gateway"}]
                return schema
            return Response(status_code=response.status_code)
        except httpx.RequestError:
            raise HTTPException(status_code=502, detail="Backend schema unreachable")

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    return get_swagger_ui_html(openapi_url="/openapi.json", title="API Gateway - Swagger UI")

# Rate Limiter configured: 3 calls per day for querying flights (Midterm Requirement)
@app.api_route("/api/v1/flights", methods=["GET"])
@app.api_route("/api/v1/flights/", methods=["GET"])
@limiter.limit("3/day")
async def proxy_query_flights(request: Request):
    return await proxy_request(request, AIRLINE_API_URL)

# Fallback route to catch all other paths and proxy them without rate limits
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def catch_all(request: Request, path: str):
    return await proxy_request(request, AIRLINE_API_URL)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
