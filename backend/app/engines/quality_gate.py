"""Automated quality checks before upload."""
from __future__ import annotations
from pathlib import Path
from app.core.logging import get_logger
from app.models.schemas import DocumentaryScript, ResearchDossier, ClaimStatus

log = get_logger("quality_gate")


def check_script_claims(script: DocumentaryScript, dossier: ResearchDossier) -> list[str]:
    issues = []
    claim_map = {c.id: c for c in dossier.claims}
    for cid in script.claim_ids:
        c = claim_map.get(cid)
        if not c:
            issues.append(f"Unknown claim id in script: {cid}")
        elif c.status == ClaimStatus.UNSUPPORTED:
            issues.append(f"UNSUPPORTED claim used: {cid}")
        elif c.status == ClaimStatus.NEEDS_REVIEW:
            issues.append(f"NEEDS_REVIEW claim used without resolution: {cid}")
    if script.word_count < 800:
        issues.append(f"Script too short: {script.word_count} words")
    if script.word_count > 2800:
        issues.append(f"Script too long: {script.word_count} words")
    return issues


def check_media_files(audio: Path | None, video: Path | None, min_audio_s: float = 60) -> list[str]:
    issues = []
    if audio is None or not audio.exists():
        issues.append("Missing narration audio")
    if video is None or not video.exists():
        issues.append("Missing rendered video")
    return issues


def run_quality_gate(
    script: DocumentaryScript,
    dossier: ResearchDossier,
    audio: Path | None = None,
    video: Path | None = None,
) -> dict:
    issues = []
    issues.extend(check_script_claims(script, dossier))
    issues.extend(check_media_files(audio, video))
    passed = len(issues) == 0
    result = {"passed": passed, "issues": issues}
    log.info("quality_gate", passed=passed, issue_count=len(issues))
    return result
