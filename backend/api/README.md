# api/
DONE. main.py — FastAPI app with:
  - POST /api/predict            single flow prediction (JSON body)
  - POST /api/predict/csv        upload a CSV of flow rows, all processed + persisted
  - POST /api/demo/generate      one-click synthetic traffic across all classes/severities
  - GET  /api/events, /api/events/{id}, /api/events/{id}/explanation
  - GET  /api/stats/overview, /api/stats/attack-distribution, /api/stats/severity-distribution
  - POST /api/monitoring/start (mode=manual|live), /api/monitoring/stop, GET /api/monitoring/status
  - GET  /api/rules

pipeline.py holds the shared ANN -> symbolic -> risk -> explanation logic
used by /api/predict, /api/predict/csv, /api/demo/generate, AND live capture
(backend/monitoring/capture_manager.py) -- one code path, not four.

demo_generators.py holds the synthetic per-class sample generators, shared
between /api/demo/generate and scripts/generate_demo_traffic.py.

Run: uvicorn api.main:app --reload --port 8000 (from project root), or just
./run_backend.sh from anywhere in the project.
