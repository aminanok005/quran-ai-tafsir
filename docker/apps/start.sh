#!/bin/bash
set -e

# Check if using Turbopack (Next.js 14+)
if grep -q "turbo" package.json; then
    echo "🚀 Starting Next.js with Turbopack hot reload..."
    NEXT_CMD="next dev --turbopack --port 3000"
else
    echo "🚀 Starting Next.js with Webpack hot reload..."
    NEXT_CMD="next dev --port 3000"
fi

# Function to restart frontend on file changes
restart_frontend_on_change() {
    inotifywait -m -r --format '%w%f' /app \
        --event create --event delete --event modify --event move \
        --exclude 'node_modules/.*' \
        --exclude '*.log' \
        --exclude '*.tmp' \
        | while read changed_file; do
        echo "🔄 Detected changes in: $changed_file"
        echo "🔄 Rebuilding frontend..."
        # Only rebuild if it's a source file
        if [[ "$changed_file" == *.tsx ]] || [[ "$changed_file" == *.ts ]] || [[ "$changed_file" == *.jsx ]] || [[ "$changed_file" == *.js ]] || [[ "$changed_file" == *.json ]]; then
            npm run build
            echo "✅ Frontend rebuilt successfully"
            # Send reload signal to browser
            curl -X POST http://localhost:3000/api/next-reload 2>/dev/null || true
        fi
    done
}

# Start Next.js
echo "🌐 Starting Next.js frontend..."
eval $NEXT_CMD &
FRONTEND_PID=$!

# Start file watcher in background
restart_frontend_on_change &
WATCHER_PID=$!

# Wait for both processes
trap 'kill $FRONTEND_PID $WATCHER_PID 2>/dev/null || true' TERM INT
wait $FRONTEND_PID $WATCHER_PID