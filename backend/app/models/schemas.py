"""Pydantic schemas for pipeline entities."""
from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field, HttpUrl


class ClaimStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    DISPUTED = "DISPUTED"
    UNSUPPORTED = "UNSUPPORTED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class TopicStatus(str, Enum):
    CANDIDATE = "candidate"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_PRODUCTION = "in_production"
    COMPLETED = "completed"
    FAILED = "failed"


class PipelineStage(str, Enum):
    TOPIC = "topic"
    RESEARCH = "research"
    SCRIPT = "script"
    NARRATION = "narration"
    VISUALS = "visuals"
    EDIT = "edit"
    SEO = "seo"
    QUALITY = "quality"
    UPLOAD = "upload"
    ANALYTICS = "analytics"


class Source(BaseModel):
    url: str
    title: str = ""
    publisher: str = ""
    published_date: Optional[str] = None
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)
    excerpt: str = ""
    reliability: float = Field(0.5, ge=0.0, le=1.0)  # heuristic


class Claim(BaseModel):
    id: str
    text: str
    status: ClaimStatus
    sources: list[Source] = []
    notes: str = ""
    last_checked: datetime = Field(default_factory=datetime.utcnow)


class TopicCandidate(BaseModel):
    id: str
    title: str
    summary: str = ""
    keywords: list[str] = []
    opportunity_score: float = 0.0
    score_breakdown: dict[str, float] = {}
    estimated_search_interest: str = "unknown"  # never invent numbers
    competition_level: str = "unknown"
    storytelling_potential: float = 0.0
    evidence_availability: float = 0.0
    production_cost: float = 0.5
    copyright_risk: float = 0.0
    misinformation_risk: float = 0.0
    status: TopicStatus = TopicStatus.CANDIDATE
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = {}


class ResearchDossier(BaseModel):
    topic_id: str
    overview: str
    timeline: list[dict[str, str]] = []
    people: list[str] = []
    locations: list[str] = []
    key_discoveries: list[str] = []
    competing_explanations: list[str] = []
    supporting_evidence: list[str] = []
    contradictory_evidence: list[str] = []
    consensus: str = ""
    unresolved_questions: list[str] = []
    claims: list[Claim] = []
    primary_sources: list[Source] = []
    secondary_sources: list[Source] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ScriptSection(BaseModel):
    name: str  # cold_open, context, mystery, evidence, investigation, turning_point, synthesis, close
    word_count: int = 0
    text: str
    claims_used: list[str] = []
    visual_cues: list[str] = []
    sfx_cues: list[str] = []


class DocumentaryScript(BaseModel):
    topic_id: str
    title_working: str
    target_duration_min: float = 12.0
    word_count: int = 0
    tone: str = "mysterious, intelligent, suspenseful, accessible"
    sections: list[ScriptSection] = []
    full_narration: str = ""
    claim_ids: list[str] = []
    review_status: str = "pending"  # pending | approved | rejected
    created_at: datetime = Field(default_factory=datetime.utcnow)


class VisualPrompt(BaseModel):
    scene_id: str
    section: str
    prompt: str
    aspect_ratio: str = "16:9"
    duration_hint_s: float = 5.0
    style: str = "cinematic dark atmospheric documentary still, film grain, teal grade, haze"
    asset_path: Optional[str] = None


class SEOPack(BaseModel):
    titles: list[str]  # 3 options
    description: str
    tags: list[str]
    chapters: list[dict[str, str]]  # {timestamp, title}
    thumbnail_prompt: str
    pinned_comment: str = ""
    hashtags: list[str] = []


class ProductionJob(BaseModel):
    id: str
    topic_id: str
    stage: PipelineStage
    status: str = "queued"  # queued | running | succeeded | failed | needs_review
    error: Optional[str] = None
    artifacts: dict[str, str] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
