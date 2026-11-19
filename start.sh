#!/usr/bin/env bash
set -e

echo "========================================================="
echo "  Starting GH Wealth Management AI Coach (gh-wm-coach)   "
echo "========================================================="

# 1. Start FastAPI Backend
echo "Starting FastAPI Backend (Dual-Store & GraphRAG Agent) on http://127.0.0.1:8000..."
cd backend && ./venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!

# 2. Start Next.js Frontend
echo "Starting Next.js UI (Active Interaction & Snapshot Space) on http://127.0.0.1:3000..."
cd ../frontend && npm run dev &
FRONTEND_PID=$!

trap "echo 'Shutting down services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true" EXIT INT TERM

echo ""
echo "Services are running:"
echo " - Web UI:  http://localhost:3000"
echo " - API Docs: http://localhost:8000/docs"
echo "Press Ctrl+C to stop both servers."
wait
