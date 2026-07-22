# NS-XIDS — Neuro-Symbolic Explainable Intrusion Detection System

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

