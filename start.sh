#!/bin/sh
# Start script for Railway deployment
# This ensures PORT variable is properly expanded

PORT=${PORT:-8000}
echo "Starting server on port $PORT"
exec uvicorn backend.main:app --host 0.0.0.0 --port $PORT
