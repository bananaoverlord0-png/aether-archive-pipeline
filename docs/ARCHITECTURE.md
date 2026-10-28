# Aether Archive — System Architecture

## Channel Brand

**Name:** Aether Archive  
**Aesthetic:** Dark teal + charcoal grade, film grain, soft atmospheric haze, slow cinematic pans, no faces of real people in primary stills (faceless silhouettes or abstract/architectural preference for mystery topics).  
**Voice:** Calm, intelligent, slightly gravely documentary (Helix / Atlas / Orion).  
**Script rules:**  
- Cold open with verified contradiction or unanswered question  
- Clear labels: [VERIFIED], [DISPUTED], [THEORY], [FOLKLORE], [RECONSTRUCTION]  
- No fabricated quotes or sources  
- 1,200–2,200 words for 8–15 min runtime (~140–150 wpm)  

## Module Map

| Module | Path | Responsibility |
|--------|------|----------------|
| Topic Discovery | `engines/topic_engine.py` | Score & rank candidate topics |
| Research | `engines/research_engine.py` | Dossier + claim verification |
| Script | `engines/script_engine.py` | Cinematic documentary script |
| Narration | `engines/narration_engine.py` | TTS + timing |
| Visuals | `engines/visual_engine.py` | Still prompts + generation + B-roll |
| Editor | `engines/editor_engine.py` | FFmpeg timeline, SFX, subtitles |
| SEO / Thumb | `engines/seo_engine.py` | Titles, desc, tags, chapters, thumb |
| Quality | `engines/quality_gate.py` | Automated checks |
| YouTube | `services/youtube_service.py` | Upload, schedule, analytics |
| Learning | `engines/learning_loop.py` | Performance → future scoring |

## Data Flow

1. Topic candidate stored (`topics` table) → human approve (or auto if flag)  
2. Research task → dossier JSON + claim table  
3. Script task (blocked until claims ≥ threshold VERIFIED/PARTIALLY)  
4. Human review gate (optional)  
5. Narration + Visuals in parallel  
6. Editor assembles → quality gate  
7. SEO pack generated  
8. Upload (private first) → schedule if authorized  
9. Analytics poll after 7/28 days → learning_loop updates weights  

## Claim Verification Statuses

- `VERIFIED` — multiple independent primary/high-quality secondary sources  
- `PARTIALLY_VERIFIED` — supported but incomplete or single-source  
- `DISPUTED` — reputable sources disagree  
- `UNSUPPORTED` — no reliable source found (blocked from final script)  
- `NEEDS_REVIEW` — human required  

## Error Recovery

- Celery tasks: max 3 retries with exponential backoff  
- Dead-letter queue for permanent failures  
- Partial artifacts kept; resume from last successful stage  
- Circuit breakers on external APIs  

## Security

- No secrets in code or logs  
- OAuth tokens rotated via refresh  
- Robots.txt + rate limits honored  
- Copyrighted audio/visuals filtered  
