

import json
from sqlalchemy import func
from sqlalchemy.orm import Session

from .models import Event, MonitoringSession


def create_event(db: Session, *, src_ip=None, dst_ip=None, src_port=None, dst_port=None,
                  protocol=None, features: dict, predicted_class: str, confidence: float,
                  adjusted_confidence: float, severity: str, risk_score: float,
                  triggered_rules: list, conflicting_rules: list, evidence: list,
                  explanation_text: str) -> Event:
    event = Event(
        src_ip=src_ip, dst_ip=dst_ip, src_port=src_port, dst_port=dst_port, protocol=protocol,
        features_json=json.dumps(features),
        predicted_class=predicted_class,
        confidence=confidence,
        adjusted_confidence=adjusted_confidence,
        severity=severity,
        risk_score=risk_score,
        triggered_rules_json=json.dumps(triggered_rules),
        conflicting_rules_json=json.dumps(conflicting_rules),
        evidence_json=json.dumps(evidence),
        explanation_text=explanation_text,
        status="new",
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_event(db: Session, event_id: int) -> Event | None:
    return db.query(Event).filter(Event.id == event_id).first()


def list_events(db: Session, limit: int = 50, offset: int = 0,
                 predicted_class: str | None = None, severity: str | None = None) -> list[Event]:
    query = db.query(Event)
    if predicted_class:
        query = query.filter(Event.predicted_class == predicted_class)
    if severity:
        query = query.filter(Event.severity == severity)
    return query.order_by(Event.timestamp.desc()).offset(offset).limit(limit).all()


def overview_stats(db: Session) -> dict:
    total = db.query(func.count(Event.id)).scalar() or 0
    benign = db.query(func.count(Event.id)).filter(Event.predicted_class == "BENIGN").scalar() or 0
    attacks = total - benign
    high_risk = db.query(func.count(Event.id)).filter(
        Event.severity.in_(["High", "Critical"])
    ).scalar() or 0
    return {
        "total_events": total,
        "benign_events": benign,
        "detected_attacks": attacks,
        "high_risk_alerts": high_risk,
    }


def attack_distribution(db: Session) -> list[dict]:
    rows = (
        db.query(Event.predicted_class, func.count(Event.id))
        .group_by(Event.predicted_class)
        .all()
    )
    return [{"class": cls, "count": count} for cls, count in rows]


def severity_distribution(db: Session) -> list[dict]:
    rows = (
        db.query(Event.severity, func.count(Event.id))
        .filter(Event.predicted_class != "BENIGN")
        .group_by(Event.severity)
        .all()
    )
    return [{"severity": sev, "count": count} for sev, count in rows]


def start_monitoring_session(db: Session, source: str, mode: str = "manual") -> MonitoringSession:
    session = MonitoringSession(source=source, mode=mode, status="running")
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def stop_monitoring_session(db: Session, session_id: int):
    from datetime import datetime, timezone
    session = db.query(MonitoringSession).filter(MonitoringSession.id == session_id).first()
    if session:
        session.status = "stopped"
        session.stopped_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(session)
    return session


def current_monitoring_session(db: Session) -> MonitoringSession | None:
    return (
        db.query(MonitoringSession)
        .filter(MonitoringSession.status == "running")
        .order_by(MonitoringSession.started_at.desc())
        .first()
    )
