/**
 * Lexecon Load Test Script (k6)
 * 
 * Tests performance under realistic load conditions:
 * - Decision API (most critical path)
 * - Status/health endpoints
 * - Audit queries
 * 
 * Run: k6 run load_test.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');

export let options = {
  stages: [
    { duration: '30s', target: 50 },   // Ramp up to 50 users
    { duration: '2m', target: 50 },    // Stay at 50 users
    { duration: '30s', target: 100 },  // Ramp up to 100 users
    { duration: '2m', target: 100 },   // Stay at 100 users
    { duration: '30s', target: 0 },    // Ramp down
  ],
  thresholds: {
    'http_req_duration': ['p(95)<200'],  // 95% of requests under 200ms
    'errors': ['rate<0.01'],             // Error rate under 1%
    'http_req_failed': ['rate<0.01'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function() {
  // Test 1: Health check (lightweight)
  let healthRes = http.get(`${BASE_URL}/health`);
  check(healthRes, {
    'health status 200': (r) => r.status === 200,
    'health response valid': (r) => r.json('status') === 'healthy',
  }) || errorRate.add(1);

  // Test 2: Status endpoint
  let statusRes = http.get(`${BASE_URL}/status`);
  check(statusRes, {
    'status 200': (r) => r.status === 200,
    'status operational': (r) => r.json('status') === 'operational',
  }) || errorRate.add(1);

  // Test 3: Decision API (most critical)
  let decisionPayload = JSON.stringify({
    actor: `test_user_${__VU}`,
    proposed_action: 'database:read',
    tool: 'postgresql',
    user_intent: 'Load testing',
    data_classes: ['public'],
    risk_level: 1,
    context: {
      environment: 'testing',
      load_test: true,
      vu: __VU,
    }
  });

  let decisionRes = http.post(
    `${BASE_URL}/decide`,
    decisionPayload,
    { headers: { 'Content-Type': 'application/json' } }
  );
  
  check(decisionRes, {
    'decision status 200': (r) => r.status === 200,
    'decision has outcome': (r) => r.json('outcome') !== undefined,
  }) || errorRate.add(1);

  // Test 4: Audit decisions query
  let auditParams = {
    limit: 10,
    offset: 0,
  };
  let auditRes = http.get(`${BASE_URL}/api/v1/audit/decisions`, auditParams);
  check(auditRes, {
    'audit status 200': (r) => r.status === 200,
    'audit has decisions': (r) => Array.isArray(r.json('decisions')),
  }) || errorRate.add(1);

  // Test 5: Compliance statistics
  let complianceRes = http.get(`${BASE_URL}/api/governance/compliance/statistics`);
  check(complianceRes, {
    'compliance status 200': (r) => r.status === 200,
    'compliance has stats': (r) => r.json('total_controls') !== undefined,
  }) || errorRate.add(1);

  // Random sleep to simulate realistic patterns
  sleep(Math.random() * 2 + 1); // 1-3 seconds between requests
}

// Smoke test configuration
export function smokeTest() {
  options.stages = [
    { duration: '10s', target: 5 },
  ];
  
  options.thresholds = {
    'http_req_duration': ['p(95)<500'],
  };
}

// Stress test configuration  
export function stressTest() {
  options.stages = [
    { duration: '1m', target: 200 },
    { duration: '5m', target: 200 },
    { duration: '1m', target: 500 },
    { duration: '5m', target: 500 },
    { duration: '1m', target: 0 },
  ];
  
  options.thresholds = {
    'http_req_duration': ['p(99)<1000'],
    'errors': ['rate<0.05'],
  };
}
