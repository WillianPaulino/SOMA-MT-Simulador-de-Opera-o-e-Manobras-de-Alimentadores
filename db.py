import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, Float, String, JSON, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

DB_URL = os.getenv("SIM_DB_URL", "sqlite:///./runs.db")

engine = create_engine(DB_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

class Run(Base):
    __tablename__ = "runs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    feeder = Column(String(64))
    event_type = Column(String(32))
    target = Column(String(64))
    interruption_min = Column(Float)
    result_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(engine)
