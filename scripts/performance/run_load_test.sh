#!/bin/bash
# Load testing runner script for Lexecon (Phase 8)

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
HOST="${LEXECON_HOST:-http://localhost:8000}"
USERS="${LOAD_TEST_USERS:-100}"
SPAWN_RATE="${LOAD_TEST_SPAWN_RATE:-10}"
DURATION="${LOAD_TEST_DURATION:-10m}"

echo -e "${GREEN}🚀 Lexecon Load Testing${NC}"
echo "=================================="
echo "Host: $HOST"
echo "Users: $USERS"
echo "Spawn Rate: $SPAWN_RATE users/sec"
echo "Duration: $DURATION"
echo ""

# Check if Locust is installed
if ! command -v locust &> /dev/null; then
    echo -e "${RED}❌ Locust is not installed${NC}"
    echo "Install with: pip install locust"
    exit 1
fi

# Check if host is reachable
echo -e "${YELLOW}📡 Checking if host is reachable...${NC}"
if curl -s -o /dev/null -w "%{http_code}" "$HOST/health" | grep -q "200"; then
    echo -e "${GREEN}✅ Host is reachable${NC}"
else
    echo -e "${RED}❌ Host is not reachable${NC}"
    echo "Make sure Lexecon is running at $HOST"
    exit 1
fi

# Run load test
echo ""
echo -e "${YELLOW}🔥 Starting load test...${NC}"
echo ""

locust -f tests/load/locustfile.py \
    --host="$HOST" \
    --users="$USERS" \
    --spawn-rate="$SPAWN_RATE" \
    --run-time="$DURATION" \
    --headless \
    --html=load-test-report.html \
    --csv=load-test-results

echo ""
echo -e "${GREEN}✅ Load test complete${NC}"
echo ""
echo "📊 Results:"
echo "  - HTML Report: load-test-report.html"
echo "  - CSV Results: load-test-results_stats.csv"
echo ""

# Parse results
if [ -f "load-test-results_stats.csv" ]; then
    echo "📈 Performance Summary:"
    echo ""
    
    # Extract key metrics (assuming standard Locust CSV format)
    # This is a simple parser - adjust based on actual CSV format
    echo "See load-test-report.html for detailed analysis"
fi

echo ""
echo -e "${YELLOW}💡 Next Steps:${NC}"
echo "  1. Open load-test-report.html in your browser"
echo "  2. Review p95/p99 latency metrics"
echo "  3. Check for error rates"
echo "  4. Compare with baseline metrics"
echo "  5. Identify bottlenecks using Grafana dashboards"
