"""Topic discovery & opportunity scoring for Aether Archive."""
from __future__ import annotations
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.schemas import TopicCandidate, TopicStatus

log = get_logger("topic_engine")


# Seed niche seeds for Aether Archive (original, not copied)
NICHE_SEEDS = [
    "lost civilizations unexplained architecture",
    "unsolved archaeological discoveries",
    "deep sea mysterious structures",
    "ancient engineering anomalies",
    "historical events with competing scientific explanations",
    "forgotten scientific instruments",
    "mysterious historical maps",
    "space anomalies historical records",
    "submerged cities evidence",
    "unusual geological formations folklore vs science",
]


def _id_from_title(title: str) -> str:
    return hashlib.sha1(title.lower().encode()).hexdigest()[:12]


def score_topic(
    title: str,
    summary: str = "",
    signals: dict[str, Any] | None = None,
) -> TopicCandidate:
    """
    Calculate configurable opportunity score.
    Never invent search volume or competitor view counts.
    When measurements unavailable, label estimates clearly.
    """
    signals = signals or {}
    breakdown: dict[str, float] = {}

    # Storytelling potential (heuristic from title/summary richness)
    storytelling = min(1.0, 0.4 + 0.1 * len(title.split()) / 5 + 0.2 * (1 if "?" in title else 0))
    if any(w in title.lower() for w in ["mystery", "unexplained", "lost", "ancient", "anomaly"]):
        storytelling = min(1.0, storytelling + 0.2)
    breakdown["storytelling_potential"] = round(storytelling, 3)

    # Evidence availability (caller can override with research pre-check)
    evidence = float(signals.get("evidence_availability", 0.5))
    breakdown["evidence_availability"] = evidence

    # Competition (label only)
    competition = signals.get("competition_level", "unknown")
    competition_score = {"low": 0.8, "medium": 0.5, "high": 0.2, "unknown": 0.45}.get(str(competition).lower(), 0.45)
    breakdown["competition"] = competition_score

    # Audience interest / search demand — never invent numbers
    interest_label = signals.get("estimated_search_interest", "unknown")
    interest_score = {"high": 0.85, "medium": 0.55, "low": 0.25, "unknown": 0.4}.get(str(interest_label).lower(), 0.4)
    breakdown["audience_interest"] = interest_score

    # Click appeal (question / contradiction)
    click = 0.6 if any(c in title for c in ["?", "!", "—"]) else 0.45
    breakdown["click_appeal"] = click

    # Production cost (lower is better for score)
    prod_cost = float(signals.get("production_cost", 0.5))
    breakdown["production_cost"] = 1.0 - prod_cost

    # Risks (lower is better)
    copy_risk = float(signals.get("copyright_risk", 0.1))
    misinfo_risk = float(signals.get("misinformation_risk", 0.2))
    breakdown["copyright_safety"] = 1.0 - copy_risk
    breakdown["misinfo_safety"] = 1.0 - misinfo_risk

    # Relevance to channel
    relevance = 0.7
    for seed in NICHE_SEEDS:
        if any(tok in title.lower() for tok in seed.split()[:3]):
            relevance = 0.9
            break
    breakdown["channel_relevance"] = relevance

    # Weighted aggregate
    weights = {
        "storytelling_potential": 0.18,
        "evidence_availability": 0.18,
        "competition": 0.12,
        "audience_interest": 0.15,
        "click_appeal": 0.10,
        "production_cost": 0.08,
        "copyright_safety": 0.07,
        "misinfo_safety": 0.07,
        "channel_relevance": 0.05,
    }
    score = sum(breakdown[k] * weights[k] for k in weights)

    return TopicCandidate(
        id=_id_from_title(title),
        title=title,
        summary=summary,
        keywords=signals.get("keywords", []),
        opportunity_score=round(score, 4),
        score_breakdown=breakdown,
        estimated_search_interest=str(interest_label),
        competition_level=str(competition),
        storytelling_potential=storytelling,
        evidence_availability=evidence,
        production_cost=prod_cost,
        copyright_risk=copy_risk,
        misinformation_risk=misinfo_risk,
        status=TopicStatus.CANDIDATE,
        metadata={"signals": signals, "scored_at": datetime.utcnow().isoformat()},
    )


def discover_seed_topics() -> list[TopicCandidate]:
    """Generate initial candidates from niche seeds (no invented stats)."""
    seeds = [
        ("The Antikythera Mechanism: Ancient Computer or Something Else?", "2,000-year-old geared device recovered from a shipwreck"),
        ("Yonaguni Monument: Natural Formation or Submerged City?", "Underwater rock formations off Japan with geometric features"),
        ("The Voynich Manuscript: Unreadable Code or Elaborate Hoax?", "15th-century illustrated codex in unknown script"),
        ("Gobekli Tepe: Why Was the World's Oldest Temple Buried?", "11,000-year-old megalithic complex in Turkey"),
        ("The Dyatlov Pass Incident: What the Evidence Actually Shows", "1959 Ural Mountains deaths with competing scientific theories"),
        ("Piri Reis Map: Accurate Ancient Cartography or Coincidence?", "1513 map showing South American coastline details"),
        ("The Tunguska Event: What Exploded Over Siberia in 1908?", "Airburst that flattened 2,000 km² of forest"),
        ("Baigong Pipes: Natural Mineralization or Prehistoric Artifact?", "Mysterious pipe-like structures in Qinghai, China"),
        ("The Taos Hum: Documented Phenomenon Without Consensus Cause", "Low-frequency sound reported by residents of Taos, NM"),
        ("Nazca Lines: Astronomical Calendar, Water Rituals, or Something Else?", "Massive geoglyphs in Peruvian desert"),
    ]
    return [score_topic(t, s) for t, s in seeds]


def save_candidates(candidates: list[TopicCandidate], root: Path | None = None) -> Path:
    settings = get_settings()
    root = root or Path(settings.data_root) / "topics"
    root.mkdir(parents=True, exist_ok=True)
    out = root / f"candidates_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    payload = [c.model_dump(mode="json") for c in candidates]
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    log.info("saved_topic_candidates", path=str(out), count=len(candidates))
    return out


def load_latest_candidates(root: Path | None = None) -> list[TopicCandidate]:
    settings = get_settings()
    root = root or Path(settings.data_root) / "topics"
    files = sorted(root.glob("candidates_*.json"), reverse=True)
    if not files:
        return []
    data = json.loads(files[0].read_text(encoding="utf-8"))
    return [TopicCandidate.model_validate(d) for d in data]
