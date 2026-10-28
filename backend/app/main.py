"""FastAPI application for Aether Archive dashboard & API."""
from __future__ import annotations
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.engines import topic_engine, pipeline as pipe
from app.models.schemas import TopicCandidate

setup_logging()
settings = get_settings()

app = FastAPI(
    title="Aether Archive Pipeline API",
    version="0.1.0",
    description="Automated cinematic documentary production for mysterious history & unexplained phenomena.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    topic: str | None = None
    mode: str = "demo"


@app.get("/health")
def health():
    return {"status": "ok", "env": settings.app_env, "channel": "Aether Archive"}


@app.get("/topics")
def list_topics():
    candidates = topic_engine.load_latest_candidates()
    if not candidates:
        candidates = topic_engine.discover_seed_topics()
        topic_engine.save_candidates(candidates)
    return [c.model_dump(mode="json") for c in candidates]


@app.post("/pipeline/run")
def run_pipeline(req: RunRequest):
    if settings.require_human_review and req.mode == "full" and not settings.auto_script_approve:
        # In production this would enqueue and wait for approval
        pass
    summary = pipe.run_demo_pipeline(topic_title=req.topic)
    return summary


@app.get("/")
def root():
    return {
        "channel": "Aether Archive",
        "tagline": "Where evidence meets the unknown.",
        "docs": "/docs",
    }
