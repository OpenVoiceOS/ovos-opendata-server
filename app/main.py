import os

from fastapi import FastAPI, Request, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy import Column, Integer, String, DateTime, func, LargeBinary
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base

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


class Intent(Base):
    __tablename__ = "intents"

    id = Column(Integer, primary_key=True, index=True)
    utterance = Column(String, nullable=False)
    intent = Column(String, nullable=False)
    language = Column(String, nullable=False)
    match_data = Column(String, nullable=True)  # JSON as String
    timestamp = Column(DateTime, server_default=func.now())


class WakeWord(Base):
    __tablename__ = "wake_words"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    language = Column(String, nullable=True)
    model = Column(String, nullable=False)
    plugin = Column(String, nullable=False)
    plugin_config = Column(String, nullable=True)  # JSON as String
    audio = Column(LargeBinary, nullable=False)
    timestamp = Column(DateTime, server_default=func.now())


class Utterance(Base):
    __tablename__ = "stt"

    id = Column(Integer, primary_key=True, index=True)
    transcript = Column(String, nullable=False)
    language = Column(String, nullable=True)
    model = Column(String, nullable=False)
    plugin = Column(String, nullable=False)
    plugin_config = Column(String, nullable=True)  # JSON as String
    audio = Column(LargeBinary, nullable=False)
    timestamp = Column(DateTime, server_default=func.now())


app = FastAPI()

# Ensure tables are created
Base.metadata.create_all(bind=engine)

EXPECTED_USER_AGENT = "ovos-metrics"


@app.post("/intents")
async def upload_intent(
        request: Request,
        utterance: str = Form(...),
        intent: str = Form(...),
        lang: str = Form(...),
        match_data: str = Form(None),
        db: Session = Depends(get_db)):

    # Check User-Agent header
    user_agent = request.headers.get("User-Agent", "")
    if user_agent.lower() != EXPECTED_USER_AGENT:
        raise HTTPException(status_code=404, detail="Not Found")

    new_metric = Intent(
        utterance=utterance,
        language=lang.lower(),
        intent=intent,
        match_data=match_data
    )
    db.add(new_metric)
    db.commit()
    return {"status": "success"}


@app.post("/wake_word")
async def upload_wake_word(
        request: Request,
        name: str = Form(...),
        audio: UploadFile = File(...),
        model: str = Form(None),
        lang: str = Form(None),
        plugin: str = Form(None),
        plugin_config: str = Form(None),
        db: Session = Depends(get_db)):
    user_agent = request.headers.get("User-Agent", "")
    if user_agent.lower() != EXPECTED_USER_AGENT:
        raise HTTPException(status_code=404, detail="Not Found")

    audio_bytes = await audio.read()
    config_json = plugin_config if plugin_config else None

    new_wake_word = WakeWord(
        name=name,
        language=lang,
        model=model,
        plugin=plugin,
        plugin_config=config_json,
        audio=audio_bytes
    )

    db.add(new_wake_word)
    db.commit()

    return {"status": "success"}


@app.post("/stt")
async def upload_stt_utterance(
        request: Request,
        transcript: str = Form(...),
        lang: str = Form(...),
        audio: UploadFile = File(...),
        model: str = Form(None),
        plugin: str = Form(None),
        plugin_config: str = Form(None),
        db: Session = Depends(get_db)):
    user_agent = request.headers.get("User-Agent", "")
    if user_agent.lower() != EXPECTED_USER_AGENT:
        raise HTTPException(status_code=404, detail="Not Found")

    audio_bytes = await audio.read()
    config_json = plugin_config if plugin_config else None

    new_utterance = Utterance(
        transcript=transcript,
        model=model,
        plugin=plugin,
        language=lang,
        plugin_config=config_json,
        audio=audio_bytes
    )

    db.add(new_utterance)
    db.commit()

    return {"status": "success"}
