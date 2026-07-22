


def _build_reasoning_text(predicted_class: str, triggered_rules: list, conflicting_rules: list) -> str:
    if predicted_class == "BENIGN":
        if not conflicting_rules:
            return "No rule-based indicators of malicious behavior were found in this flow; it is consistent with normal traffic."
        conflict_names = sorted({r["class"] for r in conflicting_rules})
        conflict_evidence = "; ".join(r["evidence_text"] for r in conflicting_rules[:3])
        return (
            f"The model classified this flow as benign, but {conflict_evidence}, which overlaps with "
            f"indicators typically associated with {', '.join(conflict_names)}. Confidence was reduced "
            f"accordingly; this flow may be worth a second look rather than being fully dismissed."
        )

    if not triggered_rules:
        return (
            f"The neural network classified this flow as {predicted_class}, but no symbolic "
            f"rules found supporting evidence in the observed features. Treat this prediction "
            f"with caution -- it relies on the model alone."
        )

    evidence_sentence = "; ".join(r["evidence_text"] for r in triggered_rules[:3])
    reasoning = (
        f"The observed traffic shows {evidence_sentence}, which is consistent with {predicted_class} "
        f"behavior."
    )
    if conflicting_rules:
        conflict_names = ", ".join(sorted({r["class"] for r in conflicting_rules}))
        reasoning += (
            f" Note: some indicators typically associated with {conflict_names} were also present, "
            f"so this classification should be reviewed if it recurs."
        )
    return reasoning


def build_explanation(prediction: dict, symbolic_result: dict, risk_result: dict) -> dict:
    """
    prediction: output of IDSPredictor.predict() from backend/ml/predict.py
    symbolic_result: output of RuleEngine.evaluate()
    risk_result: output of risk_engine.score()
    """
    predicted_class = symbolic_result["predicted_class"]

    return {
        "detection": predicted_class,
        "confidence": round(symbolic_result["adjusted_confidence"] * 100, 2),
        "model_confidence": round(symbolic_result["base_confidence"] * 100, 2),
        "evidence": [
            {
                "feature": e["feature"],
                "value": e["value"],
                "shap_contribution": e["shap_contribution"],
            }
            for e in prediction.get("evidence", [])
        ],
        "triggered_rules": [
            {"id": r["id"], "description": r["description"]}
            for r in symbolic_result["triggered_rules"]
        ],
        "conflicting_rules": [
            {"id": r["id"], "class": r["class"], "description": r["description"]}
            for r in symbolic_result["conflicting_rules"]
        ],
        "final_reasoning": _build_reasoning_text(
            predicted_class,
            symbolic_result["triggered_rules"],
            symbolic_result["conflicting_rules"],
        ),
        "risk_level": risk_result["severity"],
        "risk_score": risk_result["risk_score"],
        "risk_components": risk_result["components"],
    }


if __name__ == "__main__":
    fake_prediction = {"evidence": [{"feature": "PSH Flag Count", "value": 1.0, "shap_contribution": 0.31}]}
    fake_symbolic = {
        "predicted_class": "Brute_Force",
        "base_confidence": 0.94,
        "adjusted_confidence": 1.0,
        "triggered_rules": [
            {"id": "R_BF_01", "class": "Brute_Force", "description": "Short authentication-like exchange",
             "evidence_text": "a short handshake-like exchange with 6 forward packets"},
        ],
        "conflicting_rules": [],
    }
    fake_risk = {"severity": "High", "risk_score": 0.83, "components": {}}
    import json
    print(json.dumps(build_explanation(fake_prediction, fake_symbolic, fake_risk), indent=2))
