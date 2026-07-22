

import threading

from backend.ml.predict import IDSPredictor
from backend.symbolic_reasoning.rule_engine import RuleEngine
from backend.risk_scoring import risk_engine as risk_engine_module
from backend.explainability.explainer import build_explanation
from backend.database import crud

predictor = IDSPredictor()
rule_engine = RuleEngine()
_predict_lock = threading.Lock()

_RULES_PER_CLASS = {}
for _r in rule_engine.rules:
    _RULES_PER_CLASS[_r["class"]] = _RULES_PER_CLASS.get(_r["class"], 0) + 1


def process_flow(db, *, features: dict, context: dict | None = None,
                  src_ip=None, dst_ip=None, src_port=None, dst_port=None, protocol=None):
    """Runs one raw feature dict through the full pipeline and persists the
    resulting event. Returns (event, explanation_dict)."""

    with _predict_lock:
        prediction = predictor.predict(features, explain=True)

    symbolic_result = rule_engine.evaluate(
        predicted_class=prediction["predicted_class"],
        confidence=prediction["confidence"],
        features=features,
        context=context,
    )

    total_relevant_rules = _RULES_PER_CLASS.get(prediction["predicted_class"], 0)
    risk_result = risk_engine_module.score(
        predicted_class=prediction["predicted_class"],
        adjusted_confidence=symbolic_result["adjusted_confidence"],
        triggered_rules=symbolic_result["triggered_rules"],
        total_relevant_rules=total_relevant_rules,
        evidence=prediction.get("evidence", []),
    )

    explanation = build_explanation(prediction, symbolic_result, risk_result)

    event = crud.create_event(
        db,
        src_ip=src_ip, dst_ip=dst_ip, src_port=src_port, dst_port=dst_port, protocol=protocol,
        features=features,
        predicted_class=prediction["predicted_class"],
        confidence=prediction["confidence"],
        adjusted_confidence=symbolic_result["adjusted_confidence"],
        severity=risk_result["severity"],
        risk_score=risk_result["risk_score"],
        triggered_rules=explanation["triggered_rules"],
        conflicting_rules=explanation["conflicting_rules"],
        evidence=explanation["evidence"],
        explanation_text=explanation["final_reasoning"],
    )

    return event, explanation
