#!/usr/bin/env bash
set -euo pipefail

# If you created a backend/.env, load it
if [ -f "backend/.env" ]; then
  export $(grep -v '^#' backend/.env | xargs)
fi

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
