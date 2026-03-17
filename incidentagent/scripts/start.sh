#!/bin/bash
set -e

echo "Starting IncidentAgent services..."

# Start API server in background
uvicorn incidentagent.api.app:app --host 0.0.0.0 --port 8000 &
API_PID=$!

# Wait for API to be ready
echo "Waiting for API to start..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        echo "API is ready!"
        break
    fi
    sleep 1
done

# Start Streamlit dashboard
echo "Starting dashboard..."
streamlit run incidentagent/ui/dashboard.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true &
DASH_PID=$!

echo "Services started:"
echo "  API:       http://localhost:8000"
echo "  Dashboard: http://localhost:8501"

# Wait for any process to exit
wait -n $API_PID $DASH_PID

# Exit with status of the first process that exits
exit $?
