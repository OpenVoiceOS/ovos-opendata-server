import os

from fastapi import FastAPI, Request, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/ovos_metrics")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Metrics(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    utterance = Column(String, nullable=False)
    intent = Column(String, nullable=False)
    language = Column(String, nullable=False)
    timestamp = Column(DateTime, server_default=func.now())


app = FastAPI()

# Ensure tables are created
Base.metadata.create_all(bind=engine)

EXPECTED_USER_AGENT = "ovos-core-metrics"


# Pydantic model for API input
class MetricsData(BaseModel):
    utterance: str
    intent: str
    language: str


@app.post("/collect")
async def collect_metrics(request: Request, data: MetricsData, db: Session = Depends(get_db)):
    # Check User-Agent header
    user_agent = request.headers.get("User-Agent", "")
    if user_agent.lower() != EXPECTED_USER_AGENT:
        raise HTTPException(status_code=404, detail="Not Found")

    # Insert data into PostgreSQL
    new_metric = Metrics(**data.model_dump())
    db.add(new_metric)
    db.commit()

    return {"status": "success"}
