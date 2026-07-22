# SETUP.md — Getting NS-XIDS Running

This guide exists because setting this up the first time surfaces a handful
of predictable snags (wrong Python version, wrong directory, port already in
use, etc.). Everything below was hit and fixed once already -- read this
before debugging from scratch.

## 1. Prerequisites

- **Python 3.10, 3.11, 3.12, or 3.13** -- NOT 3.14. TensorFlow does not yet
  publish wheels for Python 3.14. If `python3 --version` shows 3.14, install
  an older version instead:
  ```bash
  brew install python@3.12
  ```
- **Node.js 18+** for the frontend:
  ```bash
  brew install node
  ```
- macOS/Linux. (Windows works too, but paths/sudo commands below differ --
  ask if you need Windows-specific instructions.)

## 2. One-time setup

```bash
cd ns-xids
cd backend
python3.12 -m venv venv          # use the SAME python3.12 you installed above, not plain python3
source venv/bin/activate
pip install -r requirements.txt   # takes a few minutes, TensorFlow is large
cd ..

cd frontend
npm install
cd ..
```

## 3. Running it (recommended: use the helper scripts)

```bash
./run_backend.sh          # normal mode -- run from ANY directory inside the project
./run_frontend.sh         # in a second terminal
```

Open **http://localhost:5173**.

These scripts exist specifically because manually running `uvicorn` trips
people up in two ways (see section 5) -- the scripts handle both
automatically, from whatever directory you call them from.

For live packet capture (sniffing a real interface), use:
```bash
./run_backend.sh --live
```
This runs uvicorn with `sudo`, which live capture requires.

## 4. Verifying it's actually working

```bash
curl http://127.0.0.1:8000/api/rules
```
Should return a JSON list of ~18 rules. If you get this, the model, scaler,
and rule engine all loaded correctly.

```bash
python tests/test_pipeline_e2e.py
```
Should print `All tests passed.` (5 automated tests covering the full
predict -> symbolic reasoning -> risk -> DB -> monitoring pipeline).

## 5. Common problems and exact fixes

### `ModuleNotFoundError: No module named 'backend'`
You ran `uvicorn` from inside `backend/` instead of the project root
(`ns-xids/`), OR you used `api.main:app` instead of `backend.api.main:app`.
Fix: use `./run_backend.sh` instead of running uvicorn manually -- it handles
this for you regardless of your current directory.

### `pip: command not found`
Use `pip3`, or better, always work inside an activated venv (`source
backend/venv/bin/activate`) where plain `pip` resolves correctly.

### `ERROR: Could not find a version that satisfies the requirement tensorflow`
Your Python is too new (3.14). See section 1 -- install Python 3.12 and
recreate the venv with `python3.12 -m venv venv`, not plain `python3`.

### `sudo: backend/venv/bin/uvicorn: command not found`
You're running the `sudo` command from inside `backend/`, which makes the
relative path wrong (it becomes `backend/backend/venv/...`). Either `cd ..`
to the project root first, or just use `./run_backend.sh --live`, which
handles this automatically.

### `[Errno 48] address already in use`
Something's already running on port 8000 -- almost always a previous
`uvicorn` still alive in another terminal tab. Find and stop it:
```bash
kill $(lsof -t -i:8000)
```

### `zsh: no matches found: http://.../api/events?limit=10`
zsh treats `?` as a glob character. Quote the URL:
```bash
curl "http://127.0.0.1:8000/api/events?limit=10"
```

### `{"detail":[{"type":"less_than_equal","loc":["query","limit"],...}]}`
The API caps `limit` at 200 per request. Use `limit=200` or lower, and
paginate with `offset` if you need more.

### Live capture connects but everything shows severity Low
This is very likely CORRECT, not a bug -- ordinary browsing/DNS traffic
genuinely is benign and should show Low severity. To generate something
worth flagging, scan a real device on your LAN (not `localhost` -- that
traffic never reaches a real network interface):
```bash
nmap -p 1-200 <your-router-ip>     # find it with: netstat -nr | grep default
```
Then filter events by destination IP to find the scan traffic specifically:
```bash
python scripts/find_events.py --dst <router-ip> --explain
```
Expect BENIGN predictions with visibly reduced confidence and populated
`conflicting_rules` -- that's the symbolic layer correctly flagging
suspicious-but-not-reclassified traffic, which is the intended behavior
(see `backend/feature_extraction/README.md` for the documented limitation
on why single-packet probes don't always get relabeled PortScan outright).

## 6. Populating the dashboard for a demo without live capture

```bash
python scripts/generate_demo_traffic.py
# or, more reliably, with real dataset rows:
python scripts/generate_demo_traffic.py --from-dataset path/to/Combined_Dataset.csv
```
