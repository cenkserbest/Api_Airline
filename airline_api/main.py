from fastapi import FastAPI
from database import engine, Base
from api.v1 import auth, flights, tickets

# Important for Swagger documentation per requirements
app = FastAPI(
    title="Airline Ticketing API",
    description="Service-Oriented Airline Management API",
    version="1.0.0",
    docs_url="/docs",      # Swagger UI
    redoc_url="/redoc"
)

# Create all DB tables
Base.metadata.create_all(bind=engine)

# Include API versioning as per requirements
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(flights.router, prefix="/api/v1/flights", tags=["Flights"])
app.include_router(tickets.router, prefix="/api/v1/tickets", tags=["Tickets"])

if __name__ == "__main__":
    import uvicorn
    # Airline API will run internally on 8001
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
