"""
demo_generators.py
Synthetic, rule-shaped feature vector generators -- one per attack class.
Shared between scripts/generate_demo_traffic.py (CLI) and
backend/api/main.py's POST /api/demo/generate endpoint (one-click from the
dashboard), so there's a single source of truth for "what does a typical
BENIGN/DDoS/PortScan/etc. sample look like" instead of two copies drifting
apart.

Honest note (found during testing): these hand-crafted vectors reliably
trigger BENIGN and DoS_Attack/DoS Hulk, but DDoS/PortScan/Brute_Force
sometimes land as BENIGN instead -- the model's real decision boundary for
those depends on a fuller feature combination than a few hand-tuned fields
can reliably reconstruct. Each generator function returns (features, intended_label).
"""

import os
import random

import joblib

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "models")


def load_baseline():
    scaler = joblib.load(os.path.join(MODELS_DIR, "scaler.pkl"))
    feature_names = joblib.load(os.path.join(MODELS_DIR, "feature_names.pkl"))
    return dict(zip(feature_names, scaler.mean_.tolist()))


def jitter(value, pct=0.15):
    return value * (1 + random.uniform(-pct, pct))


def make_benign(baseline):
    s = dict(baseline)
    s.update({
        "Destination Port": random.choice([80, 443, 53]),
        "Flow Duration": jitter(2_000_000),
        "Total Fwd Packets": random.randint(4, 15),
        "Flow Packets/s": jitter(15),
        "Flow Bytes/s": jitter(2000),
        "PSH Flag Count": 0, "ACK Flag Count": 1, "FIN Flag Count": 0,
        "RST Flag Count": 0, "URG Flag Count": 0,
    })
    return s, "BENIGN"


def make_ddos(baseline):
    s = dict(baseline)
    s.update({
        "Destination Port": 80,
        "Flow Duration": jitter(300_000),
        "Total Fwd Packets": random.randint(60, 200),
        "Flow Packets/s": jitter(8000),
        "Bwd Packets/s": jitter(4500),
        "Flow Bytes/s": jitter(500_000),
        "Down/Up Ratio": jitter(3),
    })
    return s, "DDoS"


def make_dos(baseline, hulk=False):
    s = dict(baseline)
    s.update({
        "Destination Port": 80,
        "Flow Duration": jitter(1_500_000),
        "Flow Bytes/s": jitter(200_000),
        "Fwd Packet Length Max": jitter(1400),
        "PSH Flag Count": 1,
        "Flow Packets/s": jitter(4500 if hulk else 2500),
        "Fwd Packet Length Min": jitter(3) if hulk else jitter(50),
    })
    return s, ("DoS Hulk" if hulk else "DoS_Attack")


def make_portscan(baseline):
    s = dict(baseline)
    s.update({
        "Destination Port": random.choice([3389, 8080, 8443, 9000, 21000]),
        "Flow Duration": jitter(20_000),
        "Total Fwd Packets": random.randint(1, 2),
        "Total Length of Fwd Packets": jitter(4),
        "Init_Win_bytes_forward": jitter(200),
        "PSH Flag Count": 0, "ACK Flag Count": 0,
    })
    return s, "PortScan"


def make_bruteforce(baseline):
    s = dict(baseline)
    s.update({
        "Destination Port": random.choice([22, 21, 3389, 3306]),
        "Flow Duration": jitter(400_000),
        "Total Fwd Packets": random.randint(4, 12),
        "PSH Flag Count": 1, "ACK Flag Count": 1,
        "Flow Packets/s": jitter(35),
    })
    return s, "Brute_Force"


def make_ip():
    return f"10.0.{random.randint(0,5)}.{random.randint(2,254)}"


# (label, generator_fn, context_template) -- context is only meaningful for
# rules that check monitoring-layer aggregates (see rules/brute_force.yaml etc.)
GENERATORS = [
    ("BENIGN", make_benign, None),
    ("DDoS", make_ddos, None),
    ("DoS_Attack", lambda b: make_dos(b, hulk=False), None),
    ("DoS Hulk", lambda b: make_dos(b, hulk=True), None),
    ("PortScan", make_portscan, None),
    ("Brute_Force", make_bruteforce, {"recent_attempts_from_src": random.randint(8, 20)}),
]


def generate_samples(per_class: int = 1):
    """Returns a list of (features, intended_label, context) tuples covering
    every class -- BENIGN through the 5 attack types -- `per_class` times
    each. This is what powers both the CLI script and the one-click
    dashboard button."""
    baseline = load_baseline()
    samples = []
    for label, generator, context_template in GENERATORS:
        for _ in range(per_class):
            features, intended = generator(baseline)
            context = dict(context_template) if context_template else None
            samples.append((features, intended, context))
    return samples
