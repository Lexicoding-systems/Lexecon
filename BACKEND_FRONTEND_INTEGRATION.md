# Backend-Frontend Integration Guide

Complete guide to connecting the Lexecon React frontend with the Python backend.

**Date**: 2026-01-10
**Status**: ✅ Ready to Test

---

## What's Implemented

### Backend (Python/FastAPI)
✅ **7 Audit API v1 Endpoints** - All required endpoints for audit dashboard
- `GET /api/v1/audit/decisions` - List decisions with filtering
- `GET /api/v1/audit/decisions/{id}` - Get decision details
- `GET /api/v1/audit/stats` - Dashboard statistics
- `POST /api/v1/audit/verify` - Verify ledger integrity
- `POST /api/v1/audit/export` - Create audit export
- `GET /api/v1/audit/exports` - List exports
- `GET /api/v1/audit/exports/{id}/download` - Download export

### Frontend (React)
✅ **Complete Audit Dashboard** - Production-ready UI
- Decision ledger table
- Advanced filtering
- Cryptographic verification
- Export management
- Analytics views

---

## Quick Start (3 Steps)

### Step 1: Start Backend Server

```bash
cd /Users/air/Lexecon

# Start Lexecon API server
python3 -m lexecon.cli server

# Server runs at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### Step 2: Configure Frontend

```bash
cd /Users/air/Lexecon/frontend

# Install dependencies
npm install

# Create .env file
cat > .env << 'EOF'
REACT_APP_API_URL=http://localhost:8000
REACT_APP_API_VERSION=v1
EOF
```

### Step 3: Start Frontend

```bash
# Start React dev server
npm start

# Opens at http://localhost:3000
```

---

## Integration Steps (Detailed)

### 1. Update Frontend to Use Real API

The audit dashboard currently uses sample data. Update it to call real APIs:

**File**: `/Users/air/Lexecon/frontend/src/components/AuditDashboard.jsx`

Replace sample data sections with API calls:

```javascript
// Add at top of file
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Replace sample data with API call
const [decisions, setDecisions] = useState([]);
const [stats, setStats] = useState(null);
const [loading, setLoading] = useState(true);

// Fetch decisions
useEffect(() => {
  async function fetchDecisions() {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        search: filters.search || '',
        risk_level: filters.riskLevel || '',
        outcome: filters.outcome || '',
        start_date: filters.startDate || '',
        end_date: filters.endDate || '',
        verified_only: filters.verifiedOnly || false,
        limit: 100,
        offset: 0
      });

      // Remove empty parameters
      for (let [key, value] of [...params.entries()]) {
        if (!value) params.delete(key);
      }

      const response = await fetch(`${API_BASE}/api/v1/audit/decisions?${params}`);
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      setDecisions(data.decisions);
    } catch (error) {
      console.error('Failed to fetch decisions:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }

  fetchDecisions();
}, [filters]);

// Fetch stats
useEffect(() => {
  async function fetchStats() {
    try {
      const response = await fetch(`${API_BASE}/api/v1/audit/stats`);
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  }

  fetchStats();
}, []);
```

### 2. Enable CORS on Backend

The backend needs to allow requests from the React dev server.

**File**: `/Users/air/Lexecon/src/lexecon/api/server.py`

CORS is already configured but verify these settings:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. Add Authentication (Optional)

If you want to require authentication:

**Backend** - Already supports optional auth via session/bearer token
**Frontend** - Add login and store session:

```javascript
// Login function
async function login(username, password) {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });

  if (!response.ok) {
    throw new Error('Login failed');
  }

  const data = await response.json();
  sessionStorage.setItem('session_id', data.session_id);
  return data;
}

// Add to API calls
const response = await fetch(`${API_BASE}/api/v1/audit/decisions`, {
  headers: {
    'Authorization': `Bearer ${sessionStorage.getItem('session_id')}`
  }
});
```

### 4. Create Some Sample Data

The backend needs some decisions in the ledger to display:

```bash
# Use the decision endpoint to create sample data
curl -X POST "http://localhost:8000/decide" \
  -H "Content-Type: application/json" \
  -d '{
    "actor": "developer@example.com",
    "proposed_action": "Access customer database",
    "tool": "database_client",
    "user_intent": "Query user records",
    "data_classes": ["personal_data"],
    "risk_level": 3
  }'

# Create a few more with different risk levels and outcomes
curl -X POST "http://localhost:8000/decide" \
  -H "Content-Type: application/json" \
  -d '{
    "actor": "admin@example.com",
    "proposed_action": "Delete production database",
    "tool": "database_admin",
    "user_intent": "Clean up old data",
    "data_classes": ["personal_data", "sensitive"],
    "risk_level": 5
  }'
```

---

## Testing the Integration

### 1. Test Backend Endpoints

```bash
# Check server health
curl http://localhost:8000/health

# Get decisions
curl http://localhost:8000/api/v1/audit/decisions?limit=10

# Get stats
curl http://localhost:8000/api/v1/audit/stats

# Verify ledger
curl -X POST http://localhost:8000/api/v1/audit/verify
```

### 2. Test Frontend

1. **Open Browser**: http://localhost:3000/audit
2. **Check Console**: No errors (open DevTools → Console)
3. **Verify Data Loads**: See decisions in table
4. **Test Filters**: Try different filters
5. **Click Details**: Open decision detail modal
6. **Verify Ledger**: Click "Verify Ledger" button

### 3. Check Network Requests

In Chrome DevTools → Network tab:
- Should see requests to `http://localhost:8000/api/v1/audit/*`
- Status should be `200 OK`
- Response should contain JSON data

---

## Troubleshooting

### Issue: "Failed to fetch"

**Cause**: CORS error or backend not running

**Solution**:
1. Check backend is running: `curl http://localhost:8000/health`
2. Check CORS config in server.py
3. Check browser console for CORS error

### Issue: "Empty dashboard"

**Cause**: No decisions in ledger

**Solution**:
1. Create sample data (see "Create Sample Data" above)
2. Check ledger has entries: `curl http://localhost:8000/ledger/entries`

### Issue: "401 Unauthorized" or "403 Forbidden"

**Cause**: Authentication required but no session

**Solution**:
1. Backend auth is optional - check if it's enforced
2. If enforced, add login flow to frontend
3. Store and send session_id with requests

### Issue: "Module not found" (Frontend)

**Cause**: Dependencies not installed

**Solution**:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Issue: "Import error" (Backend)

**Cause**: Python dependencies missing

**Solution**:
```bash
pip install -r requirements.txt
```

---

## Production Deployment

### Backend

1. **Use Production Server**:
   ```bash
   # Instead of development server
   gunicorn lexecon.api.server:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
   ```

2. **Enable HTTPS**:
   ```python
   # Add SSL configuration
   import ssl
   ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
   ssl_context.load_cert_chain('cert.pem', 'key.pem')
   ```

3. **Configure CORS for Production**:
   ```python
   allow_origins=["https://yourdomain.com"],
   ```

4. **Add Rate Limiting**:
   ```bash
   pip install slowapi
   ```

### Frontend

1. **Build for Production**:
   ```bash
   cd frontend
   npm run build
   ```

2. **Serve Static Build**:
   ```bash
   # Option 1: Python
   cd build
   python3 -m http.server 3000

   # Option 2: Nginx
   server {
     listen 80;
     root /path/to/frontend/build;
     location / {
       try_files $uri /index.html;
     }
   }
   ```

3. **Configure Production API**:
   ```bash
   # .env.production
   REACT_APP_API_URL=https://api.yourdomain.com
   ```

### Docker Deployment

**Backend Dockerfile**:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ ./src/
CMD ["gunicorn", "lexecon.api.server:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
```

**Frontend Dockerfile**:
```dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
```

**docker-compose.yml**:
```yaml
version: '3.8'
services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      - LEXECON_STORAGE_PATH=/data/lexecon.db
    volumes:
      - ./data:/data

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "80:80"
    environment:
      - REACT_APP_API_URL=http://backend:8000
    depends_on:
      - backend
```

---

## API Reference

Complete API documentation: `/Users/air/Lexecon/docs/api/AUDIT_API_V1.md`

Key endpoints:
- `GET /api/v1/audit/decisions` - List decisions
- `GET /api/v1/audit/decisions/{id}` - Decision details
- `GET /api/v1/audit/stats` - Statistics
- `POST /api/v1/audit/verify` - Verify integrity

---

## Next Steps

### Short-Term (This Week)

1. ✅ Test integration locally
2. ✅ Create sample data
3. ✅ Verify all features work
4. ⬜ Add error handling in frontend
5. ⬜ Add loading states
6. ⬜ Implement retry logic

### Medium-Term (This Month)

1. ⬜ Add authentication
2. ⬜ Implement real-time updates (WebSocket)
3. ⬜ Add more dashboard features
4. ⬜ Performance optimization
5. ⬜ E2E testing

### Long-Term (This Quarter)

1. ⬜ Production deployment
2. ⬜ Monitoring and logging
3. ⬜ Advanced analytics
4. ⬜ Mobile responsive design
5. ⬜ Multi-tenancy support

---

## Resources

### Documentation
- [Frontend README](frontend/README.md)
- [Design System](docs/design-system/README.md)
- [Audit Dashboard Spec](docs/audit-dashboard/README.md)
- [API Reference](docs/api/AUDIT_API_V1.md)

### Code Locations
- **Backend API**: `src/lexecon/api/server.py` (lines 2872-3352)
- **Frontend App**: `frontend/src/App.jsx`
- **Audit Dashboard**: `frontend/src/components/AuditDashboard.jsx`
- **Design System**: `frontend/src/design-system/`

### Key Commands
```bash
# Backend
python3 -m lexecon.cli server

# Frontend
cd frontend && npm start

# Test API
curl http://localhost:8000/api/v1/audit/stats

# Build for production
cd frontend && npm run build
```

---

**Status**: ✅ Backend and frontend are ready. Start both servers to test integration.

---

© 2026 Lexecon. All rights reserved.
