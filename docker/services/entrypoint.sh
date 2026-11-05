#!/bin/bash
set -e

# Function to restart API on file changes
restart_api_on_change() {
    inotifywait -m -r --format '%w%f' /app \
        --event create --event delete --event modify --event move \
        | while read changed_file; do
        echo "🔄 Detected changes in: $changed_file"
        echo "🚀 Restarting API..."
        kill -TERM $API_PID 2>/dev/null || true
        sleep 2
        exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level info &
        API_PID=$!
    done
}

# Start API
echo "🏃 Starting QURAN AI API..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level info &
API_PID=$!

# Start file watcher in background
restart_api_on_change &
WATCHER_PID=$!

# Wait for both processes
trap 'kill $API_PID $WATCHER_PID 2>/dev/null || true' TERM INT
wait $API_PID $WATCHER_PID