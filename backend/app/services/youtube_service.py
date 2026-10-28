"""YouTube Data API v3 upload + analytics stubs (real when credentials present)."""
from __future__ import annotations
from pathlib import Path
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.schemas import SEOPack

log = get_logger("youtube")


def get_youtube_client():
    """Build authorized YouTube client if OAuth tokens exist."""
    settings = get_settings()
    if not (settings.youtube_client_id and settings.youtube_client_secret and settings.youtube_refresh_token):
        log.warning("youtube_credentials_missing")
        return None
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        creds = Credentials(
            token=None,
            refresh_token=settings.youtube_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.youtube_client_id,
            client_secret=settings.youtube_client_secret,
            scopes=[
                "https://www.googleapis.com/auth/youtube.upload",
                "https://www.googleapis.com/auth/youtube",
                "https://www.googleapis.com/auth/yt-analytics.readonly",
            ],
        )
        return build("youtube", "v3", credentials=creds)
    except Exception as e:
        log.error("youtube_client_failed", error=str(e))
        return None


def upload_video(
    video_path: Path,
    seo: SEOPack,
    privacy: str | None = None,
    schedule_iso: str | None = None,
) -> dict:
    """
    Upload video. Returns {video_id, url} or {error}.
    Does not fake success — real API only when authorized.
    """
    settings = get_settings()
    privacy = privacy or settings.youtube_upload_privacy
    client = get_youtube_client()
    if client is None:
        return {
            "status": "skipped",
            "reason": "YouTube credentials not configured. Set YOUTUBE_* env vars.",
            "would_upload": {
                "title": seo.titles[0],
                "privacy": privacy,
                "path": str(video_path),
            },
        }

    from googleapiclient.http import MediaFileUpload
    body = {
        "snippet": {
            "title": seo.titles[0][:100],
            "description": seo.description[:5000],
            "tags": seo.tags[:30],
            "categoryId": settings.youtube_category_id,
            "defaultLanguage": settings.youtube_default_language,
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": settings.youtube_made_for_kids,
        },
    }
    if schedule_iso and privacy == "private":
        body["status"]["publishAt"] = schedule_iso
        body["status"]["privacyStatus"] = "private"

    media = MediaFileUpload(str(video_path), chunksize=8 * 1024 * 1024, resumable=True)
    request = client.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            log.info("upload_progress", pct=int(status.progress() * 100))
    video_id = response["id"]
    log.info("upload_complete", video_id=video_id)
    return {"status": "uploaded", "video_id": video_id, "url": f"https://youtu.be/{video_id}"}
