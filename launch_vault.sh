#!/bin/bash

# Personal Engineer Vault - Quick Launcher
# Opens your secure workspace vault

echo "🚀 Launching Personal Engineer Vault..."
echo "🔐 Your intellectual property is cryptographically protected"
echo ""

# Check if port 8001 is in use
if lsof -Pi :8001 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 8001 is already in use. Using different port..."
    PORT=8002
else
    PORT=8001
fi

# Start the server
echo "📡 Starting web server on port $PORT..."
echo "💡 Your vault is now accessible at: http://localhost:$PORT/vault_minimal.html"
echo ""
echo "Keyboard shortcuts:"
echo "  Ctrl+N - New note"
echo "  Ctrl+S - Save note"
echo "  Ctrl+K - Search"
echo "  Ctrl+E - Export all"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Open browser automatically
sleep 2 && open "http://localhost:$PORT/vault_minimal.html" 2>/dev/null || \
  xdg-open "http://localhost:$PORT/vault_minimal.html" 2>/dev/null || \
  echo "🌐 Please open: http://localhost:$PORT/vault_minimal.html"

# Start Python HTTP server
cd /Users/air/Lexecon && python3 -m http.server "$PORT"
