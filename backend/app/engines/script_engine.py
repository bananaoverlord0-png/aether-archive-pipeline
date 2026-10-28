"""Original cinematic documentary script generator for Aether Archive."""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.schemas import (
    DocumentaryScript, ResearchDossier, ScriptSection, TopicCandidate, ClaimStatus,
)

log = get_logger("script_engine")

SECTION_ORDER = [
    "cold_open",
    "context",
    "mystery",
    "evidence",
    "investigation",
    "turning_point",
    "synthesis",
    "close",
]

SECTION_GUIDANCE = {
    "cold_open": "Begin with a compelling verified fact, unresolved contradiction, or precise question. No misleading clickbait. 80–150 words.",
    "context": "Location, period, original discovery or scientific background. Ground the viewer. 150–250 words.",
    "mystery": "State the central question and why it matters. 100–180 words.",
    "evidence": "Strongest documented facts, records, discoveries. Attach claim IDs. 250–400 words.",
    "investigation": "Competing explanations, theories, weaknesses in evidence. Label statuses. 250–400 words.",
    "turning_point": "Important discovery, contradiction, or shift in understanding. 120–200 words.",
    "synthesis": "What can be said with confidence, what remains open. 150–250 words.",
    "close": "Satisfying but honest conclusion; invite curiosity without false certainty. 80–150 words.",
}


def build_script_prompt(topic: TopicCandidate, dossier: ResearchDossier) -> str:
    """Prompt template for LLM script generation. Used by adapters."""
    claims_block = "\n".join(
        f"- [{c.status.value}] {c.text} (id={c.id})"
        for c in dossier.claims
        if c.status != ClaimStatus.UNSUPPORTED
    )
    return f"""You are the documentary scriptwriter for Aether Archive — a dark, atmospheric, cinematic channel about unexplained mysteries, lost civilizations, and evidence-based historical enigmas.

RULES:
- Original writing only. Do not copy other creators.
- Never present speculation as established fact.
- Label clearly: [VERIFIED], [DISPUTED], [THEORY], [FOLKLORE], [RECONSTRUCTION].
- Every factual claim must map to a claim id from the dossier.
- Do not invent sources, quotes, dates, or evidence.
- Tone: mysterious, intelligent, suspenseful, accessible.
- Target: 1,400–2,000 words total (~10–13 minutes at 140 wpm).
- English.

TOPIC: {topic.title}
OVERVIEW: {dossier.overview}
CONSENSUS: {dossier.consensus}
UNRESOLVED: {'; '.join(dossier.unresolved_questions)}

CLAIMS AVAILABLE:
{claims_block}

COMPETING EXPLANATIONS:
{chr(10).join('- ' + e for e in dossier.competing_explanations)}

Write the full narration script section by section with these headers:
## COLD_OPEN
## CONTEXT
## MYSTERY
## EVIDENCE
## INVESTIGATION
## TURNING_POINT
## SYNTHESIS
## CLOSE

After each section, add a short list of visual_cues and sfx_cues in brackets.
At the end, list claim_ids used.
"""


def assemble_script_from_sections(
    topic: TopicCandidate,
    sections: list[ScriptSection],
    claim_ids: list[str] | None = None,
) -> DocumentaryScript:
    full = "\n\n".join(s.text for s in sections)
    wc = len(full.split())
    return DocumentaryScript(
        topic_id=topic.id,
        title_working=topic.title,
        target_duration_min=round(wc / 140, 1),
        word_count=wc,
        sections=sections,
        full_narration=full,
        claim_ids=claim_ids or [],
        review_status="pending",
    )


def save_script(script: DocumentaryScript, root: Path | None = None) -> Path:
    settings = get_settings()
    root = root or Path(settings.data_root) / "scripts"
    root.mkdir(parents=True, exist_ok=True)
    out = root / f"{script.topic_id}_script.json"
    out.write_text(script.model_dump_json(indent=2), encoding="utf-8")
    # Also plain text for TTS
    txt = root / f"{script.topic_id}_narration.txt"
    txt.write_text(script.full_narration, encoding="utf-8")
    log.info("saved_script", path=str(out), words=script.word_count)
    return out


def load_script(topic_id: str, root: Path | None = None) -> DocumentaryScript | None:
    settings = get_settings()
    root = root or Path(settings.data_root) / "scripts"
    path = root / f"{topic_id}_script.json"
    if not path.exists():
        return None
    return DocumentaryScript.model_validate_json(path.read_text(encoding="utf-8"))
