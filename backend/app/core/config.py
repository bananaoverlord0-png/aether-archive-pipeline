from functools import lru_cache
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    app_secret_key: str = "dev-secret"
    log_level: str = "INFO"
    data_root: str = "./data"

    database_url: str = "postgresql+asyncpg://aether:aether@localhost:5432/aether_archive"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "aether-archive"
    s3_region: str = "us-east-1"

    llm_default_provider: Literal["anthropic", "openai", "grok"] = "anthropic"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    grok_api_key: str = ""
    llm_script_model: str = "claude-sonnet-4-20250514"
    llm_research_model: str = "claude-sonnet-4-20250514"

    serper_api_key: str = ""
    tavily_api_key: str = ""

    tts_provider: Literal["voice", "elevenlabs", "fish", "openai"] = "voice"
    voice_default_id: str = "helix"
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""
    fish_audio_api_key: str = ""
    fish_audio_reference_id: str = ""

    image_provider: str = "grok_imagine"
    pexels_api_key: str = ""

    ffmpeg_path: str = "ffmpeg"
    ffprobe_path: str = "ffprobe"
    default_resolution: str = "1920x1080"
    default_fps: int = 30
    default_target_duration_min: int = 8
    default_target_duration_max: int = 15

    youtube_client_id: str = ""
    youtube_client_secret: str = ""
    youtube_refresh_token: str = ""
    youtube_channel_id: str = ""
    youtube_upload_privacy: str = "private"
    youtube_category_id: str = "27"
    youtube_default_language: str = "en"
    youtube_made_for_kids: bool = False
    youtube_analytics_enabled: bool = False

    auto_topic_selection: bool = False
    auto_script_approve: bool = False
    auto_upload: bool = False
    auto_schedule: bool = False
    require_human_review: bool = True
    claim_verification_strict: bool = True

    max_concurrent_renders: int = 2
    research_rate_limit_per_min: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()
