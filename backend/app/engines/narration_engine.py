"""Narration / TTS orchestration for Aether Archive."""
from __future__ import annotations
import json
from pathlib import Path
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.schemas import DocumentaryScript

log = get_logger("narration_engine")


def plan_narration_chunks(script: DocumentaryScript, max_chars: int = 4500) -> list[dict]:
    """Split full narration into TTS-friendly chunks by section."""
    chunks = []
    for sec in script.sections:
        text = sec.text.strip()
        if not text:
            continue
        if len(text) <= max_chars:
            chunks.append({"section": sec.name, "text": text})
        else:
            # naive paragraph split
            paras = text.split("\n\n")
            buf = ""
            idx = 0
            for p in paras:
                if len(buf) + len(p) + 2 > max_chars and buf:
                    chunks.append({"section": f"{sec.name}_{idx}", "text": buf.strip()})
                    idx += 1
                    buf = p
                else:
                    buf = (buf + "\n\n" + p).strip()
            if buf:
                chunks.append({"section": f"{sec.name}_{idx}", "text": buf.strip()})
    return chunks


def narration_manifest_path(topic_id: str, root: Path | None = None) -> Path:
    settings = get_settings()
    root = root or Path(settings.data_root) / "audio"
    root.mkdir(parents=True, exist_ok=True)
    return root / f"{topic_id}_manifest.json"


def write_manifest(topic_id: str, chunks: list[dict], voice_id: str | None = None) -> Path:
    settings = get_settings()
    voice_id = voice_id or settings.voice_default_id
    manifest = {
        "topic_id": topic_id,
        "provider": settings.tts_provider,
        "voice_id": voice_id,
        "chunks": [
            {
                **c,
                "audio_file": f"{topic_id}_{i:02d}_{c['section']}.mp3",
                "status": "pending",
            }
            for i, c in enumerate(chunks)
        ],
    }
    path = narration_manifest_path(topic_id)
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    log.info("narration_manifest_written", path=str(path), chunks=len(chunks))
    return path


# Note: actual TTS is invoked via connected Voice tool or external API adapters
# in services/tts_adapters.py — this engine only prepares and tracks.
