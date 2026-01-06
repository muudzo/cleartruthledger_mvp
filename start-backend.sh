#!/bin/bash

# Start ClearLedger Backend
echo "Starting ClearLedger backend..."
cd "$(dirname "$0")"
source venv/bin/activate
uvicorn backend.app.main:app --reload --port 8000
