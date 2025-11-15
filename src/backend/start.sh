#!/bin/bash

# Start script for TPA API

echo "🚀 Starting TPA - Travel Planning Agent API..."
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create a .env file with your API keys"
    exit 1
fi

# Start the API
echo "📡 Starting server on http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "📖 ReDoc: http://localhost:8000/redoc"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
