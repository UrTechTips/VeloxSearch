#!/bin/bash

echo "Running database migrations or setup tasks..."
# alembic upgrade head 

echo "Starting FastAPI..."
exec uvicorn main:app --host 0.0.0.0 --port 8000