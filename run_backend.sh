

set -e
cd "$(dirname "$0")"   # always run from the project root, wherever this script lives

if [ ! -d "backend/venv" ]; then
    echo "No venv found at backend/venv. Set it up first:"
    echo "  cd backend && python3.12 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && cd .."
    exit 1
fi

if [ "$1" == "--live" ]; then
    echo "Starting backend with sudo (required for live interface capture)..."
    sudo backend/venv/bin/uvicorn backend.api.main:app --port 8000
else
    echo "Starting backend (manual/demo mode only -- use --live for real capture)..."
    backend/venv/bin/uvicorn backend.api.main:app --reload --port 8000
fi
