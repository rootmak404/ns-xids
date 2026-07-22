

import os
import glob
import yaml

RULES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "rules")


_SAFE_BUILTINS = {"abs": abs, "min": min, "max": max, "len": len}


class RuleEngine:
    def __init__(self, rules_dir: str = RULES_DIR):
        self.rules = self._load_rules(rules_dir)

    def _load_rules(self, rules_dir: str) -> list:
        rules = []
        for path in sorted(glob.glob(os.path.join(rules_dir, "*.yaml"))):
            with open(path, "r") as f:
                doc = yaml.safe_load(f) or {}
            for rule in doc.get("rules", []):
                required = {"id", "class", "condition", "weight", "evidence_text"}
                missing = required - set(rule.keys())
                if missing:
                    raise ValueError(f"Rule in {path} missing fields: {missing}")
                rules.append(rule)
        return rules

    def _evaluate_condition(self, condition: str, features: dict, context: dict | None) -> bool:
        try:
            return bool(
                eval(
                    condition,
                    {"__builtins__": _SAFE_BUILTINS},
                    {"features": features, "context": context},
                )
            )
        except (KeyError, TypeError, ZeroDivisionError):
            
            return False

    def _format_evidence(self, template: str, features: dict, context: dict | None) -> str:
        merged = dict(features)
        if context:
            merged.update(context)
        try:
            return template.format(**merged)
        except (KeyError, ValueError):
            return template  # fall back to the raw template if a field is absent

    def evaluate(self, predicted_class: str, confidence: float, features: dict,
                 context: dict | None = None) -> dict:
        supporting_rules, conflicting_rules = [], []

        for rule in self.rules:
            fired = self._evaluate_condition(rule["condition"], features, context)
            if not fired:
                continue

            evidence_text = self._format_evidence(rule["evidence_text"], features, context)
            entry = {
                "id": rule["id"],
                "class": rule["class"],
                "description": rule["description"],
                "weight": rule["weight"],
                "evidence_text": evidence_text,
            }
            if rule["class"] == predicted_class:
                supporting_rules.append(entry)
            else:
                conflicting_rules.append(entry)

        support_boost = sum(r["weight"] for r in supporting_rules)
        conflict_penalty = sum(r["weight"] for r in conflicting_rules)

        adjusted_confidence = confidence + (support_boost * 0.5) - (conflict_penalty * 0.5)
        adjusted_confidence = max(0.0, min(1.0, adjusted_confidence))

        return {
            "predicted_class": predicted_class,
            "base_confidence": confidence,
            "adjusted_confidence": adjusted_confidence,
            "triggered_rules": supporting_rules,
            "supporting_evidence": [r["evidence_text"] for r in supporting_rules],
            "conflicting_rules": conflicting_rules,
            "conflicting_evidence": [r["evidence_text"] for r in conflicting_rules],
        }


if __name__ == "__main__":
    # Smoke test with a synthetic Brute_Force-shaped sample
    engine = RuleEngine()
    sample_features = {
        "Destination Port": 22, "Flow Duration": 500000, "Total Fwd Packets": 6,
        "PSH Flag Count": 1, "ACK Flag Count": 1, "Flow Packets/s": 40,
        "Flow Bytes/s": 3000, "Total Length of Fwd Packets": 300,
        "Fwd Packet Length Max": 100, "Fwd Packet Length Min": 20,
        "Init_Win_bytes_forward": 8192, "Bwd Packets/s": 20,
    }
    result = engine.evaluate("Brute_Force", 0.94, sample_features,
                              context={"recent_attempts_from_src": 14})
    import json
    print(json.dumps(result, indent=2))
