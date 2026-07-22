

CLASS_SEVERITY_WEIGHT = {
    "BENIGN": 0.0,
    "PortScan": 0.4,       # reconnaissance -- precursor, not direct damage
    "Brute_Force": 0.6,    # active compromise attempt
    "DoS_Attack": 0.75,    # active service disruption
    "DoS Hulk": 0.75,
    "DDoS": 0.9,           # highest disruption potential
}

WEIGHTS = {
    "confidence": 0.35,
    "rule_support": 0.25,
    "class_severity": 0.25,
    "anomaly_intensity": 0.15,
}

SEVERITY_BANDS = [
    (0.85, "Critical"),
    (0.65, "High"),
    (0.40, "Medium"),
    (0.0, "Low"),
]


def _rule_support_ratio(triggered_rules: list, total_relevant_rules: int) -> float:
    if total_relevant_rules == 0:
        return 0.0
    return min(1.0, len(triggered_rules) / total_relevant_rules)


def _anomaly_intensity(evidence: list, cap: float = 0.5) -> float:
    """Normalize mean |SHAP contribution| of the top evidence features into [0,1].
    `cap` is the |SHAP| value treated as "maximally anomalous" -- chosen from
    observed SHAP magnitude ranges during model evaluation; tune if the model
    is retrained and magnitudes shift."""
    if not evidence:
        return 0.0
    mean_abs = sum(abs(e["shap_contribution"]) for e in evidence) / len(evidence)
    return min(1.0, mean_abs / cap)


def score(predicted_class: str, adjusted_confidence: float, triggered_rules: list,
          total_relevant_rules: int, evidence: list | None = None) -> dict:
    if predicted_class == "BENIGN":
        return {
            "risk_score": 0.0,
            "severity": "Low",
            "components": {
                "confidence_component": 0.0,
                "rule_support_component": 0.0,
                "class_severity_component": 0.0,
                "anomaly_intensity_component": 0.0,
            },
        }

    rule_support = _rule_support_ratio(triggered_rules, total_relevant_rules)
    class_severity = CLASS_SEVERITY_WEIGHT.get(predicted_class, 0.5)
    anomaly = _anomaly_intensity(evidence or [])

    components = {
        "confidence_component": WEIGHTS["confidence"] * adjusted_confidence,
        "rule_support_component": WEIGHTS["rule_support"] * rule_support,
        "class_severity_component": WEIGHTS["class_severity"] * class_severity,
        "anomaly_intensity_component": WEIGHTS["anomaly_intensity"] * anomaly,
    }
    risk_score = sum(components.values())

    severity = next(label for threshold, label in SEVERITY_BANDS if risk_score >= threshold)

    return {
        "risk_score": round(risk_score, 4),
        "severity": severity,
        "components": {k: round(v, 4) for k, v in components.items()},
    }


if __name__ == "__main__":
    result = score(
        predicted_class="Brute_Force",
        adjusted_confidence=1.0,
        triggered_rules=[{"id": "R_BF_01"}, {"id": "R_BF_02"}, {"id": "R_BF_03"}, {"id": "R_BF_04"}],
        total_relevant_rules=4,
        evidence=[{"shap_contribution": 0.31}, {"shap_contribution": 0.22}],
    )
    import json
    print(json.dumps(result, indent=2))
