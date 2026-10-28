# Deployment

## Local (Docker)

```bash
cp .env.example .env
# edit secrets
docker compose -f docker/docker-compose.yml up -d --build
# API: http://localhost:8000/docs
# Dashboard: http://localhost:3000 (after npm install in frontend)
```

## Production notes

1. Use managed Postgres + Redis + S3  
2. Store OAuth refresh tokens in a secrets manager (not .env on disk)  
3. Enable `REQUIRE_HUMAN_REVIEW=true` until trusted  
4. Start with `YOUTUBE_UPLOAD_PRIVACY=private`  
5. Wire Celery Flower or Prometheus for observability  
6. Respect YouTube API quotas and robots.txt on research crawls  

## CLI without Docker

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATA_ROOT=../data
python -m app.cli discover
python -m app.cli run --topic Antikythera --mode demo
```
