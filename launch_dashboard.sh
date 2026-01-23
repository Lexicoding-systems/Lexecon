#!/bin/bash

# Lexecon Developer Dashboard & IP Vault Launcher

echo "🚀 Launching Lexecon Developer Dashboard..."
echo "🔐 Engineering Workspace & IP Registry"
echo ""

# Check if we can use Python 3
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Error: Python not found. Please install Python 3."
    exit 1
fi

# Check if port is available
if lsof -Pi :8002 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 8002 is already in use. Using port 8003..."
    PORT=8003
else
    PORT=8002
fi

# Launch browser
echo "📊 Opening dashboard at http://localhost:$PORT/ENGINEER_DASHBOARD.html"
echo ""
echo "📋 Features:"
echo "  ✓ Complete development timeline from Jan 1, 2026"
echo "  ✓ IP registry with 5 patentable innovations"
echo "  ✓ Commit activity heat map"
echo "  ✓ Current sprint goals & metrics"
echo "  ✓ Exportable cryptographic proof of inventions"
echo ""
echo "💾 Data stored locally in your browser for privacy"
echo "⌨️  Press Ctrl+C to stop the server"
echo ""

# Open browser in background
sleep 2 && 
if command -v open &> /dev/null; then
    open "http://localhost:$PORT/ENGINEER_DASHBOARD.html"
elif command -v xdg-open &> /dev/null; then
    xdg-open "http://localhost:$PORT/ENGINEER_DASHBOARD.html"
else
    echo "🌐 Please open: http://localhost:$PORT/ENGINEER_DASHBOARD.html"
fi &

# Start web server
cd /Users/air/Lexecon
$PYTHON_CMD -m http.server "$PORT"
