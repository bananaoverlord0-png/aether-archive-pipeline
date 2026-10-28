"""SEO pack: titles, description, tags, chapters, thumbnail prompt."""
from __future__ import annotations
import json
from pathlib import Path
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.schemas import DocumentaryScript, SEOPack, TopicCandidate

log = get_logger("seo_engine")


def generate_seo_pack(topic: TopicCandidate, script: DocumentaryScript) -> SEOPack:
    base = topic.title
    titles = [
        base[:70],
        f"What We Actually Know About {base.split(':')[0][:40]}",
        f"The Evidence Behind {base.split(':')[0][:45]}",
    ]
    # chapters from sections
    chapters = []
    # approximate timestamps from word counts @ 140 wpm
    t = 0.0
    for sec in script.sections:
        mins = int(t // 60)
        secs = int(t % 60)
        chapters.append({
            "timestamp": f"{mins}:{secs:02d}",
            "title": sec.name.replace("_", " ").title(),
        })
        t += sec.word_count / 140.0 * 60 if sec.word_count else 30

    description = f"""{script.full_narration[:280]}...

In this Aether Archive documentary we examine the evidence, competing explanations, and unresolved questions surrounding {topic.title}.

Chapters:
""" + "\n".join(f"{c['timestamp']} {c['title']}" for c in chapters) + """

Sources and claims are verified against primary and high-quality secondary materials. Speculation is labeled. Subscribe for more evidence-based mysteries.

#Documentary #History #Mystery #Archaeology #Science
"""

    tags = list({
        "documentary", "mystery", "history", "unexplained", "archaeology",
        "aether archive", "lost civilizations", "ancient mysteries",
        *[k for k in topic.keywords[:8]],
        *topic.title.lower().replace(":", " ").split()[:6],
    })[:25]

    thumb = (
        f"Cinematic YouTube thumbnail for documentary titled '{titles[0]}'. "
        "Dark teal and charcoal grade, bold all-caps hook text under 6 words on left or bottom bar, "
        "one striking mysterious object or location on the right, high contrast, film grain, no faces, "
        "curiosity gap without fake claims."
    )

    return SEOPack(
        titles=titles,
        description=description.strip(),
        tags=tags,
        chapters=chapters,
        thumbnail_prompt=thumb,
        pinned_comment="What do you think the strongest evidence is? Sources in description.",
        hashtags=["#AetherArchive", "#Documentary", "#Mystery", "#History"],
    )


def save_seo(topic_id: str, pack: SEOPack, root: Path | None = None) -> Path:
    settings = get_settings()
    root = root or Path(settings.data_root) / "metadata"
    root.mkdir(parents=True, exist_ok=True)
    out = root / f"{topic_id}_seo.json"
    out.write_text(pack.model_dump_json(indent=2), encoding="utf-8")
    log.info("seo_pack_saved", path=str(out))
    return out
