#!/bin/bash
# Load environment variables from .env file and start backend

# Change to backend directory
cd "$(dirname "$0")"

# Export environment variables from .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Start the backend
./venv/bin/python -m uvicorn app.main:app --reload --port 8000
