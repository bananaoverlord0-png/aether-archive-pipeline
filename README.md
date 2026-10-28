# Aether Archive — Fully Automated YouTube Documentary Pipeline

**Original channel identity:** Aether Archive  
**Tagline:** *Where evidence meets the unknown.*  
**Niche:** Unexplained mysteries • Lost civilizations • Strange historical events • Unsolved archaeological discoveries • Unusual scientific phenomena • Forgotten historical stories • Mysterious locations • Ancient engineering • Deep-sea discoveries • Space mysteries • Evidence-based examination of historical conspiracies

Dark, atmospheric, cinematic documentary aesthetic. Intelligent, suspenseful, accessible. Never presents speculation as fact. Clearly labels VERIFIED / DISPUTED / THEORY / FOLKLORE.

## What This System Does

End-to-end automation that turns a topic idea into a publication-ready YouTube video:

1. **Topic Discovery** — scores opportunity from trends, competition, storytelling potential, evidence availability
2. **Research & Fact-Checking** — builds source-linked dossiers with claim verification statuses
3. **Original Script Generation** — cinematic 8–15 min documentary structure (cold open → context → mystery → evidence → investigation → turning point → synthesis → close)
4. **Narration** — configurable TTS (Voice / ElevenLabs / Fish Audio adapters)
5. **Visuals** — AI stills + motion prompts + stock search adapters (Grok Imagine, Higgsfield, Runway, Pexels)
6. **Assembly** — FFmpeg-based timeline editor with atmospheric SFX beds, chapters, subtitles
7. **Thumbnails & SEO** — titles, descriptions, tags, chapters, thumbnail generation
8. **Quality Gates** — automated checks before upload
9. **YouTube Upload & Schedule** — Data API v3 + Analytics feedback loop
10. **Learning Loop** — performance data updates opportunity scoring and style preferences

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Next.js    │────▶│   FastAPI    │────▶│  PostgreSQL │
│  Dashboard  │     │   Backend    │     │  + Redis    │
└─────────────┘     └──────┬───────┘     └─────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         Celery Workers  S3 Storage  External APIs
         (research,      (renders,   (YouTube, TTS,
          script, TTS,    assets)     Image Gen,
          render)                     Search)
```

Modular engines live under `backend/app/engines/`.  
Provider adapters under `backend/app/services/`.  
All secrets via environment variables (see `.env.example`).

## Quick Start (Local Demo)

```bash
cp .env.example .env
# fill keys you have
docker compose -f docker/docker-compose.yml up -d
cd backend && pip install -r requirements.txt
python -m app.cli run --topic "The Antikythera Mechanism" --mode demo
```

For a full production deploy see `docs/DEPLOYMENT.md`.

## Design Principles

- **No fabrication** of sources, quotes, or evidence
- **Claim provenance** required for every factual statement
- **Human-in-the-loop** gates by default (topic approval, script review)
- **Recoverable tasks** with retries and dead-letter queues
- **Observable** (structured logs + Prometheus-ready metrics)
- **Copyright-safe** visual & audio sourcing
- **Original brand** — never clones another creator’s scripts, thumbs, or voice

## License

MIT — build responsibly. Do not use for misinformation or non-consensual content.
