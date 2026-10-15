import http from 'k6/http';
import { check, sleep } from 'k6';

const baseUrl = (__ENV.BASE_URL || 'http://localhost:8002').replace(/\/$/, '');
if (!/^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(baseUrl)) {
  throw new Error('This low-load script only targets localhost. Do not run it against production.');
}

export const options = {
  scenarios: {
    local_read_only_smoke_load: {
      executor: 'constant-vus',
      vus: 3,
      duration: '30s',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<1000'],
  },
};

export default function () {
  const health = http.get(`${baseUrl}/health/ready`, { tags: { endpoint: 'health' } });
  check(health, { 'readiness endpoint returns 200': (response) => response.status === 200 });

  const itineraries = http.get(`${baseUrl}/api/v1/itineraries`, {
    tags: { endpoint: 'itineraries-list' },
  });
  check(itineraries, {
    'itinerary list returns 200': (response) => response.status === 200,
    'itinerary list returns JSON array': (response) => {
      try {
        return Array.isArray(response.json());
      } catch (_error) {
        return false;
      }
    },
  });

  sleep(1);
}
