# Audit Dashboard API (v1)

**Base Path**: `/api/v1/audit`

Frontend-compatible API endpoints for the Lexecon Audit Dashboard.

---

## Authentication

All endpoints support optional authentication via:
- **Cookie**: `session_id` cookie
- **Header**: `Authorization: Bearer <session_id>`

If authenticated, requires `VIEW_AUDIT_LOGS` permission.

---

## Endpoints

### 1. List Decisions

**GET** `/api/v1/audit/decisions`

Get paginated list of audit decisions with filtering.

#### Query Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `search` | string | Text search (ID, action, actor) | - |
| `risk_level` | string | Filter by risk (minimal, low, medium, high, critical) | - |
| `outcome` | string | Filter by outcome (approved, denied, escalated, override) | - |
| `start_date` | string | ISO date string | - |
| `end_date` | string | ISO date string | - |
| `verified_only` | boolean | Only verified entries | false |
| `limit` | number | Max results | 100 |
| `offset` | number | Pagination offset | 0 |

#### Response

```json
{
  "decisions": [
    {
      "id": "DEC-2847",
      "timestamp": "2026-01-10T14:32:15Z",
      "action": "Model inference request approved",
      "actor": "system@lexecon.ai",
      "riskLevel": "low",
      "outcome": "approved",
      "signature": "a4f3e8d2c9b1a7f5...",
      "previousHash": "b5e4f9d3c2a8b6e1...",
      "policyVersion": "v2.1.0",
      "verified": true,
      "appliedPolicies": [
        {
          "name": "Data Access Control",
          "result": "passed"
        }
      ],
      "context": {}
    }
  ],
  "total": 2847,
  "offset": 0,
  "limit": 100
}
```

#### Example

```bash
curl "http://localhost:8000/api/v1/audit/decisions?risk_level=high&limit=10"
```

---

### 2. Get Decision Details

**GET** `/api/v1/audit/decisions/{decision_id}`

Get detailed information for a specific decision, including verification status.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `decision_id` | string | Decision ID (e.g., "DEC-2847") |

#### Response

```json
{
  "id": "DEC-2847",
  "timestamp": "2026-01-10T14:32:15Z",
  "action": "Model inference request approved",
  "actor": "system@lexecon.ai",
  "riskLevel": "low",
  "outcome": "approved",
  "signature": "a4f3e8d2c9b1a7f5...",
  "previousHash": "b5e4f9d3c2a8b6e1...",
  "policyVersion": "v2.1.0",
  "verified": true,
  "appliedPolicies": [
    {
      "name": "Data Access Control",
      "result": "passed"
    },
    {
      "name": "Risk Assessment",
      "result": "passed"
    }
  ],
  "context": {},
  "verification": {
    "signatureValid": true,
    "chainIntegrityValid": true,
    "calculatedHash": "a4f3e8d2c9b1a7f5...",
    "recordedHash": "a4f3e8d2c9b1a7f5..."
  },
  "fullData": {
    "request_id": "req-123",
    "tool": "model_inference",
    "user_intent": "Generate text"
  }
}
```

#### Example

```bash
curl "http://localhost:8000/api/v1/audit/decisions/DEC-2847"
```

---

### 3. Get Dashboard Statistics

**GET** `/api/v1/audit/stats`

Get aggregated statistics for audit dashboard overview.

#### Response

```json
{
  "totalDecisions": 2847,
  "totalDecisionsChange": "+12%",
  "verifiedEntries": 2847,
  "verifiedPercentage": 100.0,
  "escalations": 23,
  "escalationsChange": "-8%",
  "highRiskCount": 156,
  "criticalRiskCount": 12,
  "highRiskStatus": "Requiring oversight",
  "outcomeBreakdown": {
    "approved": 2670,
    "denied": 154,
    "escalated": 23,
    "override": 0
  },
  "riskBreakdown": {
    "high": 156,
    "critical": 12
  }
}
```

#### Example

```bash
curl "http://localhost:8000/api/v1/audit/stats"
```

---

### 4. Verify Ledger Integrity

**POST** `/api/v1/audit/verify`

Verify cryptographic integrity of entire audit ledger.

#### Response

```json
{
  "verified": true,
  "totalEntries": 2848,
  "verifiedEntries": 2848,
  "failedEntries": [],
  "integrityPercentage": 100.0,
  "details": {
    "valid": true,
    "message": "All entries verified successfully"
  },
  "timestamp": "2026-01-10T15:42:30Z"
}
```

#### Example

```bash
curl -X POST "http://localhost:8000/api/v1/audit/verify"
```

---

### 5. Create Audit Export

**POST** `/api/v1/audit/export`

Create a new audit export request.

**Note**: This is an alias for `/api/governance/audit-export/request`.

#### Request Body

```json
{
  "requester": "auditor@example.com",
  "purpose": "Q4 Compliance Audit",
  "scope": "full",
  "format": "json",
  "start_date": "2026-01-01T00:00:00Z",
  "end_date": "2026-01-10T23:59:59Z",
  "include_deleted": false,
  "metadata": {
    "audit_type": "regulatory"
  }
}
```

#### Response

```json
{
  "export_id": "exp-abc123",
  "requester": "auditor@example.com",
  "purpose": "Q4 Compliance Audit",
  "scope": "full",
  "format": "json",
  "start_date": "2026-01-01T00:00:00+00:00",
  "end_date": "2026-01-10T23:59:59+00:00",
  "include_deleted": false,
  "requested_at": "2026-01-10T15:45:00+00:00",
  "status": "pending",
  "metadata": {
    "audit_type": "regulatory"
  }
}
```

#### Example

```bash
curl -X POST "http://localhost:8000/api/v1/audit/export" \
  -H "Content-Type: application/json" \
  -d '{
    "requester": "auditor@example.com",
    "purpose": "Q4 Compliance Audit",
    "scope": "full",
    "format": "json"
  }'
```

---

### 6. List Audit Exports

**GET** `/api/v1/audit/exports`

List all audit export requests with pagination.

#### Query Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `status` | string | Filter by status (pending, completed, failed) | - |
| `limit` | number | Max results | 50 |
| `offset` | number | Pagination offset | 0 |

#### Response

```json
{
  "exports": [
    {
      "exportId": "exp-abc123",
      "requester": "auditor@example.com",
      "purpose": "Q4 Compliance Audit",
      "format": "json",
      "scope": "full",
      "status": "completed",
      "requestedAt": "2026-01-10T15:45:00+00:00",
      "startDate": "2026-01-01T00:00:00+00:00",
      "endDate": "2026-01-10T23:59:59+00:00",
      "generatedAt": "2026-01-10T15:46:30+00:00",
      "sizeBytes": 1048576,
      "recordCount": 2847
    }
  ],
  "total": 1,
  "offset": 0,
  "limit": 50
}
```

#### Example

```bash
curl "http://localhost:8000/api/v1/audit/exports?status=completed"
```

---

### 7. Download Audit Export

**GET** `/api/v1/audit/exports/{export_id}/download`

Download a completed audit export package.

**Note**: This is an alias for `/api/governance/audit-export/{export_id}/download`.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `export_id` | string | Export ID (e.g., "exp-abc123") |

#### Response

Returns file download (JSON, CSV, or PDF based on export format).

#### Example

```bash
curl "http://localhost:8000/api/v1/audit/exports/exp-abc123/download" \
  -o audit_export.json
```

---

## Data Models

### Decision

```typescript
interface Decision {
  id: string;                    // Decision ID
  timestamp: string;              // ISO date string
  action: string;                 // Action description
  actor: string;                  // Who requested the action
  riskLevel: string;              // minimal | low | medium | high | critical
  outcome: string;                // approved | denied | escalated | override
  signature: string;              // Cryptographic signature (entry hash)
  previousHash: string;           // Hash of previous entry
  policyVersion: string;          // Policy version applied
  verified: boolean;              // Integrity verification status
  appliedPolicies: Policy[];      // Policies applied
  context: Record<string, any>;   // Additional context
}
```

### Applied Policy

```typescript
interface Policy {
  name: string;      // Policy name
  result: string;    // passed | failed
}
```

### Verification Details

```typescript
interface Verification {
  signatureValid: boolean;        // Hash verification
  chainIntegrityValid: boolean;   // Chain integrity
  calculatedHash: string;         // Recalculated hash
  recordedHash: string;           // Recorded hash
}
```

---

## Error Responses

All endpoints return standard HTTP error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid parameter: risk_level must be one of minimal, low, medium, high, critical"
}
```

### 403 Forbidden
```json
{
  "detail": "Insufficient permissions for audit logs"
}
```

### 404 Not Found
```json
{
  "detail": "Decision DEC-2847 not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Failed to retrieve decisions: Database connection error"
}
```

---

## Integration Example

### React Frontend

```javascript
// API configuration
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Fetch decisions with filters
async function fetchDecisions(filters) {
  const params = new URLSearchParams({
    search: filters.search || '',
    risk_level: filters.riskLevel || '',
    outcome: filters.outcome || '',
    start_date: filters.startDate || '',
    end_date: filters.endDate || '',
    verified_only: filters.verifiedOnly || false,
    limit: filters.limit || 100,
    offset: filters.offset || 0
  });

  // Remove empty parameters
  for (let [key, value] of [...params.entries()]) {
    if (!value) params.delete(key);
  }

  const response = await fetch(
    `${API_BASE}/api/v1/audit/decisions?${params}`,
    {
      headers: {
        'Authorization': `Bearer ${sessionStorage.getItem('session_id')}`
      }
    }
  );

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}

// Get decision details
async function getDecisionDetails(decisionId) {
  const response = await fetch(
    `${API_BASE}/api/v1/audit/decisions/${decisionId}`,
    {
      headers: {
        'Authorization': `Bearer ${sessionStorage.getItem('session_id')}`
      }
    }
  );

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}

// Get dashboard statistics
async function getStats() {
  const response = await fetch(
    `${API_BASE}/api/v1/audit/stats`,
    {
      headers: {
        'Authorization': `Bearer ${sessionStorage.getItem('session_id')}`
      }
    }
  );

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}

// Verify ledger
async function verifyLedger() {
  const response = await fetch(
    `${API_BASE}/api/v1/audit/verify`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${sessionStorage.getItem('session_id')}`
      }
    }
  );

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}
```

---

## Testing

### Manual Testing

```bash
# Start server
python3 -m lexecon.cli server

# Test endpoints
curl "http://localhost:8000/api/v1/audit/decisions?limit=5"
curl "http://localhost:8000/api/v1/audit/stats"
curl -X POST "http://localhost:8000/api/v1/audit/verify"
```

### Automated Testing

```python
import pytest
from fastapi.testclient import TestClient
from lexecon.api.server import app

client = TestClient(app)

def test_get_decisions():
    response = client.get("/api/v1/audit/decisions?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "decisions" in data
    assert "total" in data

def test_get_decision_details():
    # First get a decision ID
    response = client.get("/api/v1/audit/decisions?limit=1")
    decisions = response.json()["decisions"]
    if len(decisions) > 0:
        decision_id = decisions[0]["id"]
        response = client.get(f"/api/v1/audit/decisions/{decision_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == decision_id

def test_get_stats():
    response = client.get("/api/v1/audit/stats")
    assert response.status_code == 200
    data = response.json()
    assert "totalDecisions" in data
    assert "verifiedEntries" in data

def test_verify_ledger():
    response = client.post("/api/v1/audit/verify")
    assert response.status_code == 200
    data = response.json()
    assert "verified" in data
    assert "totalEntries" in data
```

---

## Performance Considerations

- **Pagination**: Always use `limit` and `offset` for large result sets
- **Filtering**: Use specific filters to reduce result set size
- **Caching**: Consider caching stats endpoint (updates infrequently)
- **Verification**: Full ledger verification can be slow for large ledgers

---

## Security

- Authentication is optional but recommended for production
- All endpoints respect `VIEW_AUDIT_LOGS` permission
- No sensitive data in URLs (use POST body for filters when possible)
- Rate limiting recommended for public deployments

---

## See Also

- [Frontend Integration Guide](../FRONTEND_INTEGRATION.md)
- [Audit Dashboard Documentation](../audit-dashboard/README.md)
- [Full API Reference](./API_REFERENCE.md)
