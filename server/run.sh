#!/bin/bash

# Navigate to server directory
cd "$(dirname "$0")"

echo "Starting Student Assistant Backend Server..."
echo "API will be available at: http://localhost:8000"
echo "API docs will be available at: http://localhost:8000/docs"
echo ""
echo "Loading configuration from: $(pwd)/src/config.yml"
echo ""

# Run the server from src directory so it can find config.yml
cd src
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
