

set -e
cd "$(dirname "$0")/frontend"

if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies (first run only)..."
    npm install
fi

echo "Starting frontend dev server -- open http://localhost:5173"
npm run dev
