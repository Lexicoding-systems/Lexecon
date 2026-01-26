#!/bin/bash
# Lexecon Server Startup Script

set -e

echo "Starting Lexecon Governance Server..."
echo "=================================="

# Set PYTHONPATH
export PYTHONPATH=/Users/air/Lexecon/src:$PYTHONPATH

# Change to Lexecon directory
cd /Users/air/Lexecon

# Check if .env exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found. Using defaults."
fi

# Start server
echo "Starting uvicorn server on http://localhost:8000"
echo "API docs available at http://localhost:8000/docs"
echo ""
python3 -m uvicorn lexecon.api.server:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level info
