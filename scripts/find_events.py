

import argparse
import requests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="http://127.0.0.1:8000")
    parser.add_argument("--dst", default=None, help="Filter by destination IP")
    parser.add_argument("--src", default=None, help="Filter by source IP")
    parser.add_argument("--limit", type=int, default=200, help="Max events to fetch (API caps at 200)")
    parser.add_argument("--explain", action="store_true", help="Print full explanation of the first match")
    args = parser.parse_args()

    r = requests.get(f"{args.host}/api/events", params={"limit": min(args.limit, 200)})
    r.raise_for_status()
    events = r.json()

    matched = [
        e for e in events
        if (args.dst is None or e["dst_ip"] == args.dst)
        and (args.src is None or e["src_ip"] == args.src)
    ]

    print(f"Found {len(matched)} matching event(s) out of {len(events)} fetched")
    print(f"{'ID':>6} {'Port':>6} {'Class':14} {'Confidence':>11} {'Severity':10}")
    print("-" * 55)
    for e in matched[:30]:
        print(f"{e['id']:>6} {e['dst_port']:>6} {e['predicted_class']:14} "
              f"{e['adjusted_confidence']:>9.1f}%  {e['severity']:10}")

    if args.explain and matched:
        target_id = matched[0]["id"]
        print(f"\n--- Full explanation for event #{target_id} ---")
        r2 = requests.get(f"{args.host}/api/events/{target_id}/explanation")
        r2.raise_for_status()
        exp = r2.json()
        print(f"Detection: {exp['detection']} ({exp['confidence']}%, model said {exp['model_confidence']}%)")
        print(f"Risk: {exp['risk_level']} (score {exp['risk_score']})")
        print(f"Triggered rules: {exp['triggered_rules']}")
        print(f"Conflicting rules: {exp['conflicting_rules']}")
        print(f"Reasoning: {exp['final_reasoning']}")


if __name__ == "__main__":
    main()
