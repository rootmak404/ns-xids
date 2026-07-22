

import os
import sys
import joblib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from backend.api.main import app

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")


def _bruteforce_shaped_sample():
    scaler = joblib.load(os.path.join(MODELS_DIR, "scaler.pkl"))
    feature_names = joblib.load(os.path.join(MODELS_DIR, "feature_names.pkl"))
    sample = dict(zip(feature_names, scaler.mean_.tolist()))
    sample.update({
        "Destination Port": 22, "Flow Duration": 500000, "Total Fwd Packets": 6,
        "PSH Flag Count": 1, "ACK Flag Count": 1, "Flow Packets/s": 40,
        "Flow Bytes/s": 3000, "Total Length of Fwd Packets": 300,
        "Fwd Packet Length Max": 100, "Fwd Packet Length Min": 20,
        "Init_Win_bytes_forward": 8192, "Bwd Packets/s": 20,
    })
    return sample


def test_predict_endpoint_returns_full_explanation():
    with TestClient(app) as client:
        payload = {
            "features": _bruteforce_shaped_sample(),
            "context": {"recent_attempts_from_src": 14},
            "src_ip": "10.0.0.5", "dst_ip": "10.0.0.100",
            "src_port": 51234, "dst_port": 22, "protocol": "TCP",
        }
        r = client.post("/api/predict", json=payload)
        assert r.status_code == 200
        body = r.json()
        for key in ("detection", "confidence", "evidence", "triggered_rules",
                    "final_reasoning", "risk_level", "risk_score"):
            assert key in body, f"missing key: {key}"


def test_events_and_stats_after_predict():
    with TestClient(app) as client:
        payload = {"features": _bruteforce_shaped_sample()}
        r = client.post("/api/predict", json=payload)
        assert r.status_code == 200
        event_id = r.json()["event_id"]

        r2 = client.get("/api/events")
        assert r2.status_code == 200
        assert len(r2.json()) >= 1

        r3 = client.get(f"/api/events/{event_id}")
        assert r3.status_code == 200
        assert "features" in r3.json()

        r4 = client.get("/api/stats/overview")
        assert r4.status_code == 200
        assert r4.json()["total_events"] >= 1


def test_monitoring_start_stop_lifecycle():
    with TestClient(app) as client:
        r1 = client.post("/api/monitoring/start", json={"source": "test", "mode": "manual"})
        assert r1.status_code == 200
        assert r1.json()["mode"] == "manual"
        r2 = client.post("/api/monitoring/start", json={"source": "test", "mode": "manual"})
        assert r2.status_code == 400  # already running
        r3 = client.post("/api/monitoring/stop")
        assert r3.status_code == 200


def test_live_monitoring_fails_cleanly_on_bad_interface():
    """A bad/nonexistent interface should return a clean 400, not hang or crash,
    and must NOT leave a dangling 'running' monitoring session behind."""
    with TestClient(app) as client:
        r1 = client.post("/api/monitoring/start",
                          json={"source": "nonexistent_iface_xyz", "mode": "live"})
        assert r1.status_code == 400

        r2 = client.get("/api/monitoring/status")
        assert r2.status_code == 200
        assert r2.json()["status"] == "stopped"  # no dangling session


def test_invalid_features_returns_400():
    with TestClient(app) as client:
        r = client.post("/api/predict", json={"features": {"Destination Port": 80}})
        assert r.status_code == 400


def test_demo_generate_produces_multiple_severities():
    """The one-click 'Generate Test Traffic' button should produce events
    spanning more than one severity level in a single call."""
    with TestClient(app) as client:
        r = client.post("/api/demo/generate", json={"per_class": 2})
        assert r.status_code == 200
        body = r.json()
        assert body["generated"] == 12  # 6 classes x 2 per class
        assert len(body["severity_counts"]) >= 2  # spans multiple severities


def test_csv_upload_processes_valid_rows_and_skips_malformed():
    import csv
    import tempfile

    feature_names = joblib.load(os.path.join(MODELS_DIR, "feature_names.pkl"))
    scaler = joblib.load(os.path.join(MODELS_DIR, "scaler.pkl"))
    baseline = dict(zip(feature_names, scaler.mean_.tolist()))

    good_row = dict(baseline)
    bad_row = dict(baseline)
    bad_row["Destination Port"] = "not_a_number"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=feature_names)
        writer.writeheader()
        writer.writerow(good_row)
        writer.writerow(bad_row)
        csv_path = f.name

    with TestClient(app) as client:
        with open(csv_path, "rb") as f:
            r = client.post("/api/predict/csv", files={"file": ("test.csv", f, "text/csv")})
        assert r.status_code == 200
        body = r.json()
        assert body["rows_processed"] == 1
        assert body["rows_skipped"] == 1

    os.unlink(csv_path)


def test_csv_upload_rejects_missing_columns():
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
        f.write("Destination Port,Flow Duration\n80,1000\n")
        csv_path = f.name

    with TestClient(app) as client:
        with open(csv_path, "rb") as f:
            r = client.post("/api/predict/csv", files={"file": ("bad.csv", f, "text/csv")})
        assert r.status_code == 400

    os.unlink(csv_path)


if __name__ == "__main__":
    test_predict_endpoint_returns_full_explanation()
    test_events_and_stats_after_predict()
    test_monitoring_start_stop_lifecycle()
    test_live_monitoring_fails_cleanly_on_bad_interface()
    test_invalid_features_returns_400()
    test_demo_generate_produces_multiple_severities()
    test_csv_upload_processes_valid_rows_and_skips_malformed()
    test_csv_upload_rejects_missing_columns()
    print("All tests passed.")
