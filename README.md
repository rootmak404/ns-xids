# NS-XIDS — Neuro-Symbolic Explainable Intrusion Detection System

## Current status

| Component | Status |
|---|---|
| Dataset + training pipeline (leakage-fixed) | ✅ Done — `training/train_ann_model.ipynb` |
| ANN model, scaler, encoder, feature list, IQR bounds, SHAP background | ✅ **Locked** — `models/` |
| Reference prediction pipeline (bug-fixed) | ✅ Done — `backend/ml/predict.py` |
| Symbolic reasoning engine | ✅ Done — `backend/symbolic_reasoning/rule_engine.py` + `rules/*.yaml` |
| Risk scoring | ✅ Done — `backend/risk_scoring/risk_engine.py` |
| Explainability formatter (incl. conflicting-rules bug fix) | ✅ Done — `backend/explainability/explainer.py` |
| FastAPI backend + SQLite DB | ✅ Done — `backend/api/main.py`, `backend/database/` |
| React dashboard (6 pages) | ✅ Done — `frontend/` |
| Feature extraction (pcap -> 35-feature vector) | ✅ Done, tested end-to-end — `backend/feature_extraction/` |
| Live monitoring (`/api/monitoring/start` -> real capture thread) | ✅ Done, verified on real traffic — `backend/monitoring/capture_manager.py` |
| **CSV upload -> dashboard results** | ✅ Done — `POST /api/predict/csv`, Test Data page |
| **One-click "generate all severity levels"** | ✅ Done — `POST /api/demo/generate`, Test Data page |
| Demo/test tooling (CLI) | ✅ Done — `scripts/generate_demo_traffic.py`, `scripts/replay_pcap_to_api.py`, `scripts/find_events.py` |
| End-to-end tests | ✅ 8/8 passing — `tests/test_pipeline_e2e.py` |
| Setup/run scripts | ✅ Done — `run_backend.sh`, `run_frontend.sh`, `SETUP.md` |

## Project structure

```
ns-xids/
├── backend/
│   ├── api/                 REST endpoints (FastAPI)
│   ├── monitoring/          traffic capture agent
│   ├── feature_extraction/  live traffic -> 35-feature vector
│   ├── ml/                  predict.py (LOCKED, working)
│   ├── symbolic_reasoning/  rule engine
│   ├── explainability/      explanation formatting
│   ├── risk_scoring/        risk score calculation
│   └── database/            SQLAlchemy models, SQLite
├── frontend/                dashboard (Overview, Live, Alerts, Explainability, Analytics)
├── models/                  LOCKED model artifacts (see models/README.md)
├── datasets/                raw/processed training data
├── training/                train_ann_model.ipynb (offline training path)
├── rules/                   YAML/JSON symbolic rule definitions
├── tests/                   unit tests per module
└── documentation/           report, architecture docs, results
```

Each subfolder has its own `README.md` explaining what belongs there and current status.

## Quick start

**See [SETUP.md](SETUP.md) for full setup instructions and a troubleshooting
guide** covering every real issue hit while getting this running (Python
version conflicts, directory/import errors, port conflicts, etc.).

Short version, after one-time setup (see SETUP.md section 2):
```bash
./run_backend.sh          # terminal 1 -- works from any directory
./run_frontend.sh         # terminal 2
```
Open **http://localhost:5173**.

For live packet capture: `./run_backend.sh --live` (needs sudo).

**Populate the dashboard with demo data** — either via the dashboard's Test
Data page (upload a CSV, or click "Generate Test Traffic" for a one-click
spread across every severity level), or from the command line:
```bash
python scripts/generate_demo_traffic.py
# or, more reliably, using real dataset rows if you have Combined_Dataset.csv:
python scripts/generate_demo_traffic.py --from-dataset path/to/Combined_Dataset.csv
```

**Feed real captured/replayed traffic through the pipeline** (with backend running):
```bash
python scripts/replay_pcap_to_api.py path/to/capture.pcap
```

**Try live capture for real** (requires sudo/admin + a real interface):
```bash
./run_backend.sh --live
```
Then in the dashboard: Live Monitoring → mode "Live capture" → enter your
interface name (`en0` on macOS, `eth0` on most Linux) → Start.

**Verified working end-to-end on a real machine**, including a real bug
found and fixed during that testing: the symbolic layer was correctly
detecting scan-shaped traffic and reducing confidence even when the ANN
called it BENIGN, but the human-readable explanation didn't say why for
BENIGN predictions specifically (conflicting rules weren't being persisted
or mentioned in the reasoning text). Both are now fixed — see
`backend/explainability/explainer.py` and the `conflicting_rules_json`
column in `backend/database/models.py`.

## Next step

The full pipeline is built, tested, and verified against real captured
traffic end-to-end. What's left is validation/polish, not new components:
1. Validate `backend/feature_extraction/flow.py`'s features against real
   CICFlowMeter output on the same pcap, since it's a best-effort
   reimplementation (see that file's docstring).
2. Write up the report sections (problem statement through evaluation —
   happy to help draft these next).
