#!/bin/bash
# Quick server test script

echo "=================================="
echo "Lexecon Server Test"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test 1: Health check
echo "Test 1: Health Check"
response=$(curl -s http://localhost:8000/health 2>&1)
if echo "$response" | grep -q "healthy"; then
    echo -e "${GREEN}✓ PASS${NC} - Server is healthy"
    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
else
    echo -e "${RED}✗ FAIL${NC} - Server not responding"
    echo "Response: $response"
    echo ""
    echo "Make sure server is running:"
    echo "  ./start_server.sh"
    exit 1
fi

echo ""
echo "=================================="

# Test 2: System status
echo "Test 2: System Status"
response=$(curl -s http://localhost:8000/status 2>&1)
if echo "$response" | grep -q "operational"; then
    echo -e "${GREEN}✓ PASS${NC} - System operational"
    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
else
    echo -e "${RED}✗ FAIL${NC} - Status check failed"
fi

echo ""
echo "=================================="

# Test 3: Decision API
echo "Test 3: Decision Request"
response=$(curl -s -X POST http://localhost:8000/decide \
  -H "Content-Type: application/json" \
  -d '{
    "actor": "user:test",
    "proposed_action": "test_action",
    "tool": "test_tool",
    "user_intent": "testing",
    "data_classes": ["test_data"],
    "risk_level": 1
  }' 2>&1)

if echo "$response" | grep -q "decision_id"; then
    echo -e "${GREEN}✓ PASS${NC} - Decision API working"
    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
else
    echo -e "${RED}✗ FAIL${NC} - Decision API failed"
    echo "Response: $response"
fi

echo ""
echo "=================================="
echo "All tests complete!"
echo ""
echo "To view API docs, open in browser:"
echo "  http://localhost:8000/docs"
echo ""
echo "To test with HTML interface, open:"
echo "  file:///Users/air/Lexecon/test_api.html"
echo ""
