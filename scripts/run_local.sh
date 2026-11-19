#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "   EvalForge: LLM Evaluation & Observability Platform   "
echo "=========================================================="

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BASE_DIR="$( dirname "$SCRIPT_DIR" )"

echo ""
echo "[1/2] Seeding database..."
cd "$BASE_DIR/backend"
export PYTHONPATH="."
python seed_data.py

echo ""
echo "[2/2] Starting backend and frontend in parallel..."
(python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload) &
BACKEND_PID=$!

cd "$BASE_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "EvalForge running!"
echo "Frontend: http://localhost:3000"
echo "Backend:  http://127.0.0.1:8000/api/v1/docs"

trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
