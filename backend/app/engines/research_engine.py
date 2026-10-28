"""Research dossier builder + claim verification for Aether Archive."""
from __future__ import annotations
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.schemas import (
    Claim, ClaimStatus, ResearchDossier, Source, TopicCandidate,
)

log = get_logger("research_engine")


# Preferred source domains (higher reliability weight)
HIGH_RELIABILITY = [
    "nature.com", "science.org", "sciencedirect.com", "nih.gov", "nasa.gov",
    "smithsonianmag.com", "britannica.com", "archaeology.org", "jstor.org",
    "who.int", "usgs.gov", "noaa.gov", "edu", "gov", "ac.uk",
]


def _claim_id(text: str) -> str:
    return hashlib.sha1(text.encode()).hexdigest()[:10]


def reliability_for_url(url: str) -> float:
    u = url.lower()
    for d in HIGH_RELIABILITY:
        if d in u:
            return 0.85 if d not in ("edu", "gov", "ac.uk") else 0.9
    if any(x in u for x in ["wikipedia.org", "bbc.com", "reuters.com", "nytimes.com", "theguardian.com"]):
        return 0.7
    return 0.45


def build_dossier_from_research(
    topic: TopicCandidate,
    research_notes: dict[str, Any],
) -> ResearchDossier:
    """
    Build a structured dossier from gathered research notes.
    research_notes is expected to be produced by a researcher agent or human.
    """
    claims: list[Claim] = []
    for c in research_notes.get("claims", []):
        sources = []
        for s in c.get("sources", []):
            sources.append(Source(
                url=s.get("url", ""),
                title=s.get("title", ""),
                publisher=s.get("publisher", ""),
                published_date=s.get("published_date"),
                excerpt=s.get("excerpt", ""),
                reliability=s.get("reliability") or reliability_for_url(s.get("url", "")),
            ))
        status = ClaimStatus(c.get("status", "NEEDS_REVIEW"))
        # Strict mode: single low-reliability source → PARTIALLY or NEEDS_REVIEW
        if status == ClaimStatus.VERIFIED and len(sources) < 2:
            status = ClaimStatus.PARTIALLY_VERIFIED
        claims.append(Claim(
            id=c.get("id") or _claim_id(c["text"]),
            text=c["text"],
            status=status,
            sources=sources,
            notes=c.get("notes", ""),
        ))

    primary = [Source(**s) if isinstance(s, dict) else s for s in research_notes.get("primary_sources", [])]
    secondary = [Source(**s) if isinstance(s, dict) else s for s in research_notes.get("secondary_sources", [])]

    dossier = ResearchDossier(
        topic_id=topic.id,
        overview=research_notes.get("overview", topic.summary),
        timeline=research_notes.get("timeline", []),
        people=research_notes.get("people", []),
        locations=research_notes.get("locations", []),
        key_discoveries=research_notes.get("key_discoveries", []),
        competing_explanations=research_notes.get("competing_explanations", []),
        supporting_evidence=research_notes.get("supporting_evidence", []),
        contradictory_evidence=research_notes.get("contradictory_evidence", []),
        consensus=research_notes.get("consensus", ""),
        unresolved_questions=research_notes.get("unresolved_questions", []),
        claims=claims,
        primary_sources=primary,
        secondary_sources=secondary,
    )
    return dossier


def verify_claims_strict(dossier: ResearchDossier) -> list[Claim]:
    """Return claims that are safe for final script (VERIFIED or PARTIALLY)."""
    settings = get_settings()
    safe = []
    for c in dossier.claims:
        if c.status in (ClaimStatus.VERIFIED, ClaimStatus.PARTIALLY_VERIFIED):
            safe.append(c)
        elif c.status == ClaimStatus.DISPUTED:
            # Allowed only if script labels the dispute
            safe.append(c)
        else:
            log.warning("claim_blocked", claim_id=c.id, status=c.status.value, text=c.text[:80])
    return safe


def save_dossier(dossier: ResearchDossier, root: Path | None = None) -> Path:
    settings = get_settings()
    root = root or Path(settings.data_root) / "research"
    root.mkdir(parents=True, exist_ok=True)
    out = root / f"{dossier.topic_id}_dossier.json"
    out.write_text(dossier.model_dump_json(indent=2), encoding="utf-8")
    log.info("saved_dossier", path=str(out), claims=len(dossier.claims))
    return out


def load_dossier(topic_id: str, root: Path | None = None) -> ResearchDossier | None:
    settings = get_settings()
    root = root or Path(settings.data_root) / "research"
    path = root / f"{topic_id}_dossier.json"
    if not path.exists():
        return None
    return ResearchDossier.model_validate_json(path.read_text(encoding="utf-8"))
