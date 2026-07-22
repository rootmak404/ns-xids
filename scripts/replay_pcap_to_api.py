

import argparse
import sys
import os

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.feature_extraction.pcap_replay import replay_pcap  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pcap_path")
    parser.add_argument("--host", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    print(f"{'Source':22} {'Destination':22} {'Pkts':>5} {'Detection':14} {'Confidence':10} {'Severity'}")
    print("-" * 95)

    sent, failed = 0, 0
    for features, meta in replay_pcap(args.pcap_path):
        payload = {
            "features": features,
            "src_ip": meta["src_ip"], "dst_ip": meta["dst_ip"],
            "src_port": meta["src_port"], "dst_port": meta["dst_port"],
            "protocol": meta["protocol"],
        }
        try:
            r = requests.post(f"{args.host}/api/predict", json=payload, timeout=15)
            r.raise_for_status()
            body = r.json()
            src = f"{meta['src_ip']}:{meta['src_port']}"
            dst = f"{meta['dst_ip']}:{meta['dst_port']}"
            print(f"{src:22} {dst:22} {meta['packet_count']:>5} {body['detection']:14} "
                  f"{body['confidence']:>8.1f}%  {body['risk_level']}")
            sent += 1
        except Exception as e:
            print(f"Flow {meta['src_ip']}->{meta['dst_ip']} FAILED: {e}")
            failed += 1

    print("-" * 95)
    print(f"Sent: {sent}  Failed: {failed}")
    print("Open the dashboard (http://localhost:5173) to see the results.")


if __name__ == "__main__":
    main()
