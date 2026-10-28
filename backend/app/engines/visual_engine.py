"""Visual prompt generation for Aether Archive cinematic stills."""
from __future__ import annotations
import json
from pathlib import Path
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.schemas import DocumentaryScript, VisualPrompt

log = get_logger("visual_engine")

STYLE_LOCK = (
    "cinematic dark atmospheric documentary still, 16:9, cold teal and charcoal color grade, "
    "soft film grain, atmospheric haze, volumetric light, no readable modern logos, "
    "no real-person faces, photoreal or hyper-real architectural and landscape focus"
)


def prompts_from_script(script: DocumentaryScript, scenes_per_section: int = 2) -> list[VisualPrompt]:
    """Create visual prompts from section visual_cues or generic section maps."""
    prompts: list[VisualPrompt] = []
    for sec in script.sections:
        cues = sec.visual_cues or [f"atmospheric scene for {sec.name.replace('_', ' ')} of {script.title_working}"]
        for i, cue in enumerate(cues[:scenes_per_section]):
            scene_id = f"{script.topic_id}_{sec.name}_{i+1:02d}"
            full_prompt = f"{cue}. {STYLE_LOCK}."
            prompts.append(VisualPrompt(
                scene_id=scene_id,
                section=sec.name,
                prompt=full_prompt,
                aspect_ratio="16:9",
                duration_hint_s=5.0 if sec.name != "cold_open" else 4.0,
            ))
    return prompts


def save_visual_plan(topic_id: str, prompts: list[VisualPrompt], root: Path | None = None) -> Path:
    settings = get_settings()
    root = root or Path(settings.data_root) / "visuals"
    root.mkdir(parents=True, exist_ok=True)
    out = root / f"{topic_id}_visual_plan.json"
    payload = [p.model_dump() for p in prompts]
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    # human-readable prompts.md
    md = root / f"{topic_id}_prompts.md"
    lines = [f"# Visual prompts — {topic_id}\n"]
    for p in prompts:
        lines.append(f"## {p.scene_id}\n")
        lines.append(f"**Section:** {p.section}\n")
        lines.append(f"```\n{p.prompt}\n```\n")
    md.write_text("\n".join(lines), encoding="utf-8")
    log.info("visual_plan_saved", path=str(out), scenes=len(prompts))
    return out
