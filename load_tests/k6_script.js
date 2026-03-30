import http from 'k6/http';
import { check, sleep } from 'k6';

// Read target URL from environment or fallback to Azure
const BASE_URL = __ENV.API_URL || 'https://airline-api-gateway-duf0bja8hcc8caf5.uaenorth-01.azurewebsites.net';

export const options = {
  scenarios: {
    // Stage 1: Normal Load
    normal_load: {
      executor: 'constant-vus',
      vus: 20,
      duration: '30s',
      startTime: '0s',
    },
    // Stage 2: Peak Load
    peak_load: {
      executor: 'constant-vus',
      vus: 50,
      duration: '30s',
      startTime: '35s',
    },
    // Stage 3: Stress Load
    stress_load: {
      executor: 'constant-vus',
      vus: 100,
      duration: '30s',
      startTime: '70s',
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests must complete below 500ms
    http_req_failed: ['rate<0.05'], // errors should be less than 5%
  },
};

export default function () {
  // Test Endpoint 1: Query Flights (Rate limited to 3 per day on Proxy, but for load testing we might hit cache / rate limit limits, so we will test directly if needed or via Proxy)
  // But wait, if Gateway rate limits everything, we'll get 429 Too Many Requests which is not good for checking backend performance.
  // Actually, we can test other endpoints that are NOT rate limited, like `Check in` or test direct Airline API port 8001 to simulate backend performance directly.
  
  // Endpoint 1: Gateway Catch All / API version
  // Wait, let's use the actual backend url to get true throughput without hitting the rate limiter of 3 per day
  const TARGET_URL = __ENV.TARGET_URL || 'https://airline-api-backend-htebhcewhmewgver.uaenorth-01.azurewebsites.net';

  // Test Endpoint 1: API Check-in (Public)
  const payload1 = JSON.stringify({
    ticket_number: `TKT_${__VU}_${__ITER}`,
    flight_number: 'TK100',
    date: '2026-04-10',
    passenger_name: `Pass_${__VU}_${__ITER}`
  });
  
  const headers = { 'Content-Type': 'application/json' };
  
  const res1 = http.post(`${TARGET_URL}/api/v1/tickets/check-in`, payload1, { headers });
  
  check(res1, {
    'Check-in responds correctly (200, 404, or 400 Validation)': (r) => [200, 400, 404].includes(r.status),
  });

  // Test Endpoint 2: Query Flights directly from backend avoiding the 3/day rate limiter for accurate load benchmark
  const res2 = http.get(`${TARGET_URL}/api/v1/flights`);
  
  check(res2, {
    'Query Flights is status 200': (r) => r.status === 200,
  });
  
  sleep(1);
}
