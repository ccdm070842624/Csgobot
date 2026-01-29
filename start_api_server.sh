#!/bin/bash

# CS:GO Trading Bot API Server Starter
# Usage: ./start_api_server.sh

echo "🚀 Starting CS:GO Trading Bot API Server..."
echo ""

# Check if required packages are installed
python3 -c "import fastapi, uvicorn" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Required packages not found. Installing..."
    pip install -r requirements_api.txt
fi

# Get local IP address
echo "📡 Server will be available at:"
echo "   - Local: http://localhost:8000"
echo "   - Network: http://$(hostname -I | awk '{print $1}'):8000"
echo ""

# Start server
echo "✅ Starting server..."
python3 api_server.py
