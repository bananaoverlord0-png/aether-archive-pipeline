"""Orchestrator: topic → research → script → narration → visuals → edit → SEO → quality."""
from __future__ import annotations
import json
from pathlib import Path
from app.core.config import get_settings
from app.core.logging import get_logger
from app.engines import topic_engine, research_engine, script_engine, narration_engine, visual_engine, seo_engine, quality_gate
from app.models.schemas import TopicCandidate, ScriptSection, DocumentaryScript

log = get_logger("pipeline")


def run_demo_pipeline(topic_title: str | None = None) -> dict:
    """
    Demo end-to-end using seeded topic + handcrafted research notes + script
    (no external LLM/TTS/YouTube keys required). Produces artifacts under data/.
    """
    settings = get_settings()
    data = Path(settings.data_root)
    data.mkdir(parents=True, exist_ok=True)

    # 1. Topic
    candidates = topic_engine.discover_seed_topics()
    topic_engine.save_candidates(candidates)
    if topic_title:
        topic = next((c for c in candidates if topic_title.lower() in c.title.lower()), candidates[0])
    else:
        topic = max(candidates, key=lambda c: c.opportunity_score)
    topic.status = topic_engine.TopicStatus.APPROVED
    log.info("topic_selected", title=topic.title, score=topic.opportunity_score)

    # 2. Research dossier (demo notes — replace with live research in production)
    demo_notes = _demo_research_notes(topic)
    dossier = research_engine.build_dossier_from_research(topic, demo_notes)
    research_engine.save_dossier(dossier)

    # 3. Script (demo cinematic script)
    sections = _demo_script_sections(topic, dossier)
    script = script_engine.assemble_script_from_sections(
        topic, sections, claim_ids=[c.id for c in dossier.claims if c.status.value != "UNSUPPORTED"]
    )
    script_engine.save_script(script)

    # 4. Narration plan
    chunks = narration_engine.plan_narration_chunks(script)
    narration_engine.write_manifest(topic.id, chunks)

    # 5. Visuals
    # inject visual cues into sections for demo
    for sec in script.sections:
        if not sec.visual_cues:
            sec.visual_cues = [f"dark atmospheric {sec.name.replace('_', ' ')} for {topic.title}"]
    prompts = visual_engine.prompts_from_script(script, scenes_per_section=2)
    visual_engine.save_visual_plan(topic.id, prompts)

    # 6. SEO
    pack = seo_engine.generate_seo_pack(topic, script)
    seo_engine.save_seo(topic.id, pack)

    # 7. Quality (script-level; media later)
    q = quality_gate.run_quality_gate(script, dossier)

    summary = {
        "topic_id": topic.id,
        "title": topic.title,
        "opportunity_score": topic.opportunity_score,
        "word_count": script.word_count,
        "estimated_minutes": script.target_duration_min,
        "claims": len(dossier.claims),
        "visual_scenes": len(prompts),
        "seo_titles": pack.titles,
        "quality": q,
        "artifacts": {
            "dossier": f"data/research/{topic.id}_dossier.json",
            "script": f"data/scripts/{topic.id}_script.json",
            "narration": f"data/scripts/{topic.id}_narration.txt",
            "audio_manifest": f"data/audio/{topic.id}_manifest.json",
            "visuals": f"data/visuals/{topic.id}_visual_plan.json",
            "seo": f"data/metadata/{topic.id}_seo.json",
        },
    }
    out = data / "renders" / f"{topic.id}_pipeline_summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    log.info("demo_pipeline_complete", summary=summary)
    return summary


def _demo_research_notes(topic: TopicCandidate) -> dict:
    """Handcrafted demo research for Antikythera-style topics. Production uses live search + LLM."""
    return {
        "overview": (
            f"{topic.title} sits at the intersection of archaeology, astronomy, and the history of technology. "
            "Primary evidence comes from physical artifacts and peer-reviewed analyses rather than folklore."
        ),
        "timeline": [
            {"year": "1900–1901", "event": "Shipwreck recovery off Antikythera island"},
            {"year": "1902", "event": "Gear wheels noticed among recovered objects"},
            {"year": "1950s–1970s", "event": "Early reconstructions and CT-era studies begin"},
            {"year": "2000s–2020s", "event": "High-resolution imaging refines gear counts and inscriptions"},
        ],
        "people": ["Valerios Stais", "Derek de Solla Price", "Michael Wright", "Tony Freeth"],
        "locations": ["Antikythera, Greece", "National Archaeological Museum, Athens"],
        "key_discoveries": [
            "Complex bronze gear train inside a wooden case",
            "Inscriptions related to astronomical cycles",
            "Pointers consistent with calendrical and lunar predictions",
        ],
        "competing_explanations": [
            "Hellenistic astronomical calculator for predicting eclipses and planetary positions",
            "Earlier or parallel technological traditions not yet recovered",
            "Over-interpretation of fragmentary remains (minority view)",
        ],
        "supporting_evidence": [
            "Physical gears and differential-like mechanisms",
            "Inscribed text matching known Metonic and Saros cycles",
            "Independent replications by researchers using CT data",
        ],
        "contradictory_evidence": [
            "No other complete devices of this complexity from the same period have been found",
            "Some gear counts remain debated due to corrosion",
        ],
        "consensus": (
            "Scholarly consensus treats the Antikythera mechanism as a sophisticated Greek astronomical device "
            "of the Hellenistic period. Exact complete function and whether it is unique remain open."
        ),
        "unresolved_questions": [
            "Who built it and for whom?",
            "Were similar devices common but lost to recycling of bronze?",
            "How much of the original case and pointers are missing?",
        ],
        "claims": [
            {
                "text": "The Antikythera mechanism was recovered from a shipwreck off the Greek island of Antikythera around 1900–1901.",
                "status": "VERIFIED",
                "sources": [
                    {"url": "https://www.britannica.com/topic/Antikythera-mechanism", "title": "Britannica — Antikythera mechanism", "publisher": "Encyclopaedia Britannica"},
                    {"url": "https://www.namuseum.gr/", "title": "National Archaeological Museum", "publisher": "Hellenic Ministry of Culture"},
                ],
            },
            {
                "text": "The device contains a complex system of bronze gears used for astronomical calculations.",
                "status": "VERIFIED",
                "sources": [
                    {"url": "https://www.nature.com/", "title": "Nature research coverage of Antikythera studies", "publisher": "Nature"},
                    {"url": "https://www.scientificamerican.com/", "title": "Scientific American reporting on CT analyses", "publisher": "Scientific American"},
                ],
            },
            {
                "text": "No other complete mechanism of equal complexity from the same era has been recovered.",
                "status": "PARTIALLY_VERIFIED",
                "sources": [
                    {"url": "https://www.britannica.com/topic/Antikythera-mechanism", "title": "Britannica", "publisher": "Encyclopaedia Britannica"},
                ],
                "notes": "Absence of evidence is not absolute proof of uniqueness.",
            },
            {
                "text": "The mechanism could predict the positions of all known planets with modern accuracy.",
                "status": "DISPUTED",
                "sources": [],
                "notes": "Planetary modeling is supported for some cycles; full modern accuracy claims exceed consensus.",
            },
        ],
        "primary_sources": [
            {"url": "https://www.namuseum.gr/", "title": "National Archaeological Museum Athens", "publisher": "NAM", "reliability": 0.9},
        ],
        "secondary_sources": [
            {"url": "https://www.britannica.com/topic/Antikythera-mechanism", "title": "Britannica entry", "publisher": "Britannica", "reliability": 0.85},
        ],
    }


def _demo_script_sections(topic, dossier) -> list[ScriptSection]:
    """Original demo narration — not copied from any channel."""
    cold = ScriptSection(
        name="cold_open",
        text=(
            "In 1901, divers working a shipwreck off a small Greek island pulled something unexpected from the sea. "
            "Not gold. Not statues. A corroded lump of bronze and wood that, when X-rayed decades later, revealed "
            "a machine of gears more intricate than anything else known from the ancient Mediterranean. "
            "[VERIFIED] The Antikythera mechanism had waited two thousand years on the seafloor. "
            "The question it still asks is simple, and still unfinished: how much of the ancient world have we lost?"
        ),
        visual_cues=["dark underwater wreck silhouette, teal haze", "corroded bronze fragment on museum table, soft side light"],
        sfx_cues=["deep water ambient", "soft metallic resonance"],
        claims_used=["claim1"],
    )
    cold.word_count = len(cold.text.split())

    context = ScriptSection(
        name="context",
        text=(
            "The ship went down near Antikythera, between Crete and the Peloponnese, around the first century BCE. "
            "Salvage in 1900 and 1901 recovered amphorae, statues, and this puzzling mass. "
            "Early observers noticed gear wheels. By the mid-twentieth century, researchers including Derek de Solla Price "
            "began mapping the mechanism's structure. Later CT imaging and international teams refined the gear counts "
            "and read inscriptions that link the device to known astronomical cycles — the Metonic cycle, eclipse prediction, "
            "and calendrical functions. [VERIFIED] It is not folklore. It is hardware."
        ),
        visual_cues=["Aegean map with Antikythera marked", "museum gallery dim lighting, bronze fragments"],
        sfx_cues=["subtle map whoosh", "quiet room tone"],
    )
    context.word_count = len(context.text.split())

    mystery = ScriptSection(
        name="mystery",
        text=(
            "The central mystery is not whether the device exists — it does — but what its existence implies. "
            "If a portable astronomical calculator of this sophistication could be built in the Hellenistic world, "
            "why do we lack others? Was bronze recycled so thoroughly that sister devices vanished? "
            "Or was this nearly unique? [PARTIALLY VERIFIED] No other complete mechanism of equal complexity from that era has been recovered. "
            "Absence of evidence is not proof of uniqueness. It is, however, a real gap in the archaeological record."
        ),
        visual_cues=["empty bronze workshop reconstruction", "timeline of classical inventions fading"],
        sfx_cues=["low drone swell"],
    )
    mystery.word_count = len(mystery.text.split())

    evidence = ScriptSection(
        name="evidence",
        text=(
            "What we can say with confidence rests on physical remains and peer-reviewed analysis. "
            "The mechanism contains a complex bronze gear train inside a wooden case. [VERIFIED] "
            "Inscriptions relate to astronomical cycles. Pointers appear consistent with calendrical and lunar predictions. "
            "Independent teams using CT data have produced compatible reconstructions. "
            "Competing popular claims — that it predicted every planet with modern accuracy, or that it is evidence of lost alien technology — "
            "exceed what the fragments support. Those claims are either [DISPUTED] or fall into folklore. "
            "Aether Archive draws the line at the metal and the math."
        ),
        visual_cues=["CT scan visualization of gears", "inscription close-up with soft light", "reconstruction model turning slowly"],
        sfx_cues=["soft mechanical tick", "paper turn"],
    )
    evidence.word_count = len(evidence.text.split())

    investigation = ScriptSection(
        name="investigation",
        text=(
            "Scholars largely agree this was a Greek astronomical device of the Hellenistic period. "
            "Debate continues on complete function, missing pointers, and the workshop that produced it. "
            "Some argue for earlier technological traditions not yet recovered; others caution against over-reading "
            "corroded fragments. [DISPUTED] Gear counts in damaged regions remain imperfectly known. "
            "What is not serious science is the leap from 'sophisticated gears' to 'impossible for humans of that time.' "
            "The evidence does not require that leap. It requires better recovery of the ancient technical tradition we already know existed in fragments — "
            "astrolabes, armillary spheres, and written mathematical astronomy."
        ),
        visual_cues=["scholarly papers and diagrams montage", "armillary sphere silhouette"],
        sfx_cues=["page turns", "quiet tension bed"],
    )
    investigation.word_count = len(investigation.text.split())

    turning = ScriptSection(
        name="turning_point",
        text=(
            "The turning point for modern understanding came with high-resolution imaging. "
            "What looked like a lump became a readable machine. Inscriptions sharpened. Differential gearing hypotheses "
            "gained support. The device stopped being a curiosity and became a data point in the history of science — "
            "proof that complex analog computation existed in the classical world far earlier than many textbooks once implied."
        ),
        visual_cues=["X-ray to solid model transition", "gear animation slow spin"],
        sfx_cues=["reveal swell"],
    )
    turning.word_count = len(turning.text.split())

    synthesis = ScriptSection(
        name="synthesis",
        text=(
            "What we can say: [VERIFIED] the Antikythera mechanism is a real Hellenistic astronomical calculator recovered from a shipwreck. "
            "It used bronze gears and inscriptions tied to known cycles. "
            "What remains open: the full original configuration, the identity of its makers, and how common such devices once were. "
            "The honest documentary answer is not a closed conspiracy and not a solved puzzle. "
            "It is a partial machine that forces us to raise our estimate of ancient engineering — without inventing what the fragments do not show."
        ),
        visual_cues=["device under museum glass, single spotlight", "Aegean horizon at dusk"],
        sfx_cues=["soft resolve pad"],
    )
    synthesis.word_count = len(synthesis.text.split())

    close = ScriptSection(
        name="close",
        text=(
            "Two thousand years underwater. One set of gears. Dozens of open questions. "
            "Aether Archive exists for cases like this — where the evidence is strong enough to respect, "
            "and incomplete enough to keep asking. If you value mysteries examined with care, stay with us. "
            "The next wreck, the next manuscript, the next anomaly is already waiting. "
            "Evidence first. Speculation labeled. The unknown, on the record."
        ),
        visual_cues=["fade to dark teal end card with Aether Archive mark"],
        sfx_cues=["final soft whoosh", "silence"],
    )
    close.word_count = len(close.text.split())

    return [cold, context, mystery, evidence, investigation, turning, synthesis, close]
