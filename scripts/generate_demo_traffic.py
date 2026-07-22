

import argparse
import random
import time
import sys
import os

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.api.demo_generators import generate_samples, load_baseline, make_ip  # noqa: E402


def load_real_samples_from_csv(csv_path, per_class=5, label_col="Label"):
    """More reliable alternative to synthetic generation: sample real rows
    from the original training CSV, grouped by class."""
    import pandas as pd
    import joblib

    feature_names = joblib.load(os.path.join(os.path.dirname(__file__), "..", "models", "feature_names.pkl"))
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()

    samples = []
    for label, group in df.groupby(label_col):
        missing = [f for f in feature_names if f not in group.columns]
        if missing:
            print(f"WARNING: dataset missing columns {missing} for class {label}, skipping")
            continue
        chosen = group.sample(n=min(per_class, len(group)), random_state=random.randint(0, 10_000))
        for _, row in chosen.iterrows():
            features = {f: float(row[f]) for f in feature_names}
            samples.append((features, str(label).strip(), None))
    return samples


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="http://127.0.0.1:8000")
    parser.add_argument("--per-class", type=int, default=3)
    parser.add_argument("--delay", type=float, default=0.15, help="seconds between requests")
    parser.add_argument("--from-dataset", default=None,
                         help="Path to a labeled CSV to sample REAL rows from instead of "
                              "synthetic vectors. More reliable for DDoS/PortScan/Brute_Force.")
    args = parser.parse_args()

    if args.from_dataset:
        print(f"Sampling real rows from {args.from_dataset} ...")
        samples = load_real_samples_from_csv(args.from_dataset, per_class=args.per_class)
    else:
        samples = generate_samples(per_class=args.per_class)

    print(f"{'Intended':14} {'Predicted':14} {'Confidence':11} {'Severity':10} {'Event ID'}")
    print("-" * 65)

    sent, failed = 0, 0
    for features, intended, context in samples:
        payload = {
            "features": features,
            "context": context,
            "src_ip": make_ip(),
            "dst_ip": make_ip(),
            "src_port": random.randint(1024, 65535),
            "dst_port": int(features.get("Destination Port", 0)),
            "protocol": "TCP",
        }
        try:
            r = requests.post(f"{args.host}/api/predict", json=payload, timeout=15)
            r.raise_for_status()
            body = r.json()
            print(f"{intended:14} {body['detection']:14} {body['confidence']:>9.1f}%  "
                  f"{body['risk_level']:10} #{body['event_id']}")
            sent += 1
        except Exception as e:
            print(f"{intended:14} FAILED: {e}")
            failed += 1
        time.sleep(args.delay)

    print("-" * 65)
    print(f"Sent: {sent}  Failed: {failed}")
    print("Open the dashboard (http://localhost:5173) to see the results.")


if __name__ == "__main__":
    main()
