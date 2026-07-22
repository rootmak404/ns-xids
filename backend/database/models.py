

from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker

DB_PATH = "sqlite:///./ns_xids.db"
engine = create_engine(DB_PATH, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    src_ip = Column(String, nullable=True)
    dst_ip = Column(String, nullable=True)
    src_port = Column(Integer, nullable=True)
    dst_port = Column(Integer, nullable=True)
    protocol = Column(String, nullable=True)

    features_json = Column(Text)              
    predicted_class = Column(String, index=True)
    confidence = Column(Float)                
    adjusted_confidence = Column(Float)        
    severity = Column(String, index=True)       
    risk_score = Column(Float)

    triggered_rules_json = Column(Text)         
    conflicting_rules_json = Column(Text, nullable=True)  
    evidence_json = Column(Text, nullable=True)  
    explanation_text = Column(Text)

    status = Column(String, default="new")     


class MonitoringSession(Base):
    __tablename__ = "monitoring_sessions"

    id = Column(Integer, primary_key=True, index=True)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    stopped_at = Column(DateTime, nullable=True)
    source = Column(String, default="unspecified")   
    mode = Column(String, default="manual")            
    total_events = Column(Integer, default=0)
    status = Column(String, default="running")       


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
