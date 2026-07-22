"""
main.py
FastAPI backend for NS-XIDS. Wires together:
    backend/ml/predict.py            (ANN + SHAP)
    backend/symbolic_reasoning       (rule engine)
    backend/risk_scoring             (risk score)
    backend/explainability           (final explanation object)
    backend/database                 (SQLite persistence)

Run with:
    uvicorn backend.api.main:app --reload --port 8000
(run from the project root, ns-xids/)
"""

from datetime import datetime
from typing import Optional
import io

from fastapi import FastAPI, Depends, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
import pandas as pd

from backend.database.models import init_db, get_db
from backend.database import crud
from backend.api.pipeline import process_flow, predictor, rule_engine, _RULES_PER_CLASS
from backend.monitoring.capture_manager import capture_manager
from backend.api.demo_generators import generate_samples, make_ip

app = FastAPI(title="NS-XIDS API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()




class PredictRequest(BaseModel):
    features: dict[str, float]
    context: Optional[dict] = None
    src_ip: Optional[str] = None
    dst_ip: Optional[str] = None
    src_port: Optional[int] = None
    dst_port: Optional[int] = None
    protocol: Optional[str] = None


class MonitoringStartRequest(BaseModel):
    source: str = "manual"          
    mode: str = "manual"             



@app.post("/api/predict")
def predict(req: PredictRequest, db: Session = Depends(get_db)):
    try:
        event, explanation = process_flow(
            db,
            features=req.features, context=req.context,
            src_ip=req.src_ip, dst_ip=req.dst_ip,
            src_port=req.src_port, dst_port=req.dst_port, protocol=req.protocol,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"event_id": event.id, "timestamp": event.timestamp, **explanation}


@app.post("/api/predict/csv")
async def predict_csv(db: Session = Depends(get_db), file: UploadFile = File(...)):
   
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file")

    raw = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(raw))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {e}")

    df.columns = df.columns.str.strip()
    required_features = list(predictor.feature_names)
    missing = [f for f in required_features if f not in df.columns]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"CSV is missing {len(missing)} required feature column(s), e.g. {missing[:5]}. "
                   f"See models/README.md for the full required column list.",
        )

    results = []
    processed, skipped = 0, 0
    for _, row in df.iterrows():
        try:
            features = {f: float(row[f]) for f in required_features}
        except (ValueError, TypeError):
            skipped += 1
            continue

        try:
            event, explanation = process_flow(db, features=features)
        except Exception:
            skipped += 1
            continue

        processed += 1
        results.append({
            "event_id": event.id,
            "predicted_class": explanation["detection"],
            "confidence": explanation["confidence"],
            "severity": explanation["risk_level"],
        })

    severity_counts = {}
    for r in results:
        severity_counts[r["severity"]] = severity_counts.get(r["severity"], 0) + 1

    return {
        "filename": file.filename,
        "rows_processed": processed,
        "rows_skipped": skipped,
        "severity_counts": severity_counts,
        "results": results,
    }


class DemoGenerateRequest(BaseModel):
    per_class: int = 1   


@app.post("/api/demo/generate")
def demo_generate(req: DemoGenerateRequest, db: Session = Depends(get_db)):
   
    samples = generate_samples(per_class=max(1, min(req.per_class, 10)))  # cap at 10/class to avoid abuse

    results = []
    for features, intended, context in samples:
        event, explanation = process_flow(
            db, features=features, context=context,
            src_ip=make_ip(), dst_ip=make_ip(),
            src_port=None, dst_port=int(features.get("Destination Port", 0)), protocol="TCP",
        )
        results.append({
            "event_id": event.id,
            "intended_class": intended,
            "predicted_class": explanation["detection"],
            "confidence": explanation["confidence"],
            "severity": explanation["risk_level"],
        })

    severity_counts = {}
    for r in results:
        severity_counts[r["severity"]] = severity_counts.get(r["severity"], 0) + 1

    return {"generated": len(results), "severity_counts": severity_counts, "results": results}




@app.get("/api/events")
def get_events(limit: int = Query(50, le=200), offset: int = 0,
                predicted_class: Optional[str] = None, severity: Optional[str] = None,
                db: Session = Depends(get_db)):
    events = crud.list_events(db, limit=limit, offset=offset,
                               predicted_class=predicted_class, severity=severity)
    return [_serialize_event(e) for e in events]


@app.get("/api/events/{event_id}")
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = crud.get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return _serialize_event(event, include_features=True)


@app.get("/api/events/{event_id}/explanation")
def get_event_explanation(event_id: int, db: Session = Depends(get_db)):
    import json
    event = crud.get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return {
        "detection": event.predicted_class,
        "confidence": round(event.adjusted_confidence * 100, 2),
        "model_confidence": round(event.confidence * 100, 2),
        "risk_level": event.severity,
        "risk_score": event.risk_score,
        "triggered_rules": json.loads(event.triggered_rules_json),
        "conflicting_rules": json.loads(event.conflicting_rules_json) if event.conflicting_rules_json else [],
        "evidence": json.loads(event.evidence_json) if event.evidence_json else [],
        "final_reasoning": event.explanation_text,
    }


def _serialize_event(e, include_features: bool = False) -> dict:
    import json
    data = {
        "id": e.id,
        "timestamp": e.timestamp,
        "src_ip": e.src_ip, "dst_ip": e.dst_ip,
        "src_port": e.src_port, "dst_port": e.dst_port, "protocol": e.protocol,
        "predicted_class": e.predicted_class,
        "confidence": round(e.confidence * 100, 2) if e.confidence is not None else None,
        "adjusted_confidence": round(e.adjusted_confidence * 100, 2) if e.adjusted_confidence is not None else None,
        "severity": e.severity,
        "risk_score": e.risk_score,
        "status": e.status,
    }
    if include_features:
        data["features"] = json.loads(e.features_json)
        data["triggered_rules"] = json.loads(e.triggered_rules_json)
        data["evidence"] = json.loads(e.evidence_json) if e.evidence_json else []
        data["explanation_text"] = e.explanation_text
    return data



@app.get("/api/stats/overview")
def stats_overview(db: Session = Depends(get_db)):
    stats = crud.overview_stats(db)
    session = crud.current_monitoring_session(db)
    stats["monitoring_status"] = "running" if session else "stopped"
    return stats


@app.get("/api/stats/attack-distribution")
def stats_attack_distribution(db: Session = Depends(get_db)):
    return crud.attack_distribution(db)


@app.get("/api/stats/severity-distribution")
def stats_severity_distribution(db: Session = Depends(get_db)):
    return crud.severity_distribution(db)



@app.post("/api/monitoring/start")
def monitoring_start(req: MonitoringStartRequest, db: Session = Depends(get_db)):
    existing = crud.current_monitoring_session(db)
    if existing:
        raise HTTPException(status_code=400, detail="Monitoring session already running")

    if req.mode == "live":
        try:
            capture_manager.start(req.source)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to start live capture on interface '{req.source}': {e}. "
                       f"Live capture needs root/administrator privileges and a valid "
                       f"interface name (e.g. 'en0', 'eth0').",
            )

    session = crud.start_monitoring_session(db, source=req.source, mode=req.mode)
    return {"session_id": session.id, "status": session.status, "source": session.source, "mode": session.mode}


@app.post("/api/monitoring/stop")
def monitoring_stop(db: Session = Depends(get_db)):
    session = crud.current_monitoring_session(db)
    if not session:
        raise HTTPException(status_code=400, detail="No monitoring session running")

    if session.mode == "live" and capture_manager.is_running:
        capture_manager.stop()

    session = crud.stop_monitoring_session(db, session.id)
    return {"session_id": session.id, "status": session.status}


@app.get("/api/monitoring/status")
def monitoring_status(db: Session = Depends(get_db)):
    session = crud.current_monitoring_session(db)
    if not session:
        return {"status": "stopped"}
    return {"status": "running", "session_id": session.id, "source": session.source,
             "mode": session.mode, "started_at": session.started_at}



@app.get("/api/rules")
def get_rules():
    return [
        {"id": r["id"], "class": r["class"], "description": r["description"], "weight": r["weight"]}
        for r in rule_engine.rules
    ]
