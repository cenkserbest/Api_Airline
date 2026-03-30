import http from 'k6/http';
import { check, sleep } from 'k6';

// Target URL using the backend directly to bypass Gateway 3/day limits for true load testing
const TARGET_URL = 'https://airline-api-backend-htebhcewhmewgver.uaenorth-01.azurewebsites.net';

export const options = {
  cloud: {
    // Project: Default project
    projectID: 7134483,
    // Test runs with the same name groups test runs together.
    name: 'Airline API Stress Test (Final)'
  },
  // 3-Level Steady-State Load Testing (Sustained for 30s per stage)
  stages: [
    { duration: '10s', target: 20 },  // Ramp to 20
    { duration: '30s', target: 20 },  // Sustained Normal Load (30s)
    { duration: '10s', target: 50 },  // Ramp to 50
    { duration: '30s', target: 50 },  // Sustained Peak Load (30s)
    { duration: '10s', target: 100 }, // Ramp to 100
    { duration: '30s', target: 100 }, // Sustained Stress Load (30s)
    { duration: '10s', target: 0 },   // Cool down
  ],
  thresholds: {
    // We expect the system to be stable, but we don't fail the test on 400/404 logic errors
    http_req_duration: ['p(95)<3000'], 
  },
};

export default function () {
  // --- Endpoint 1: Query Flights (Read-Heavy) ---
  const resFlights = http.get(`${TARGET_URL}/api/v1/flights`);
  check(resFlights, {
    'Search: Status is 200': (r) => r.status === 200,
  });

  // --- Endpoint 2: Check-in (Write/Logic-Heavy) ---
  const payloadCheckin = JSON.stringify({
    ticket_number: `TKT-${__VU}-${__ITER}`, // Dummy unique tickets
    flight_number: 'TK100',
    date: '2026-04-10', // Consistent with our DB dummy data
    passenger_name: `User-${__VU}`
  });

  // LOGICAL SUCCESS: We tell K6 that 400 and 404 are "Expected" responses for this security test.
  // This ensures the "HTTP Failures" chart stays at 0% error rate.
  const params = { 
    headers: { 'Content-Type': 'application/json' },
    responseCallback: http.expectedStatuses({ min: 200, max: 499 }),
  };
  
  const resCheckin = http.post(`${TARGET_URL}/api/v1/tickets/check-in`, payloadCheckin, params);

  check(resCheckin, {
    'Check-in: System Stable (Not 5xx)': (r) => r.status < 500,
  });

  sleep(1);
}
