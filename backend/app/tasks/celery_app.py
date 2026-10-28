from celery import Celery
from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "aether",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)
celery_app.conf.task_routes = {
    "app.tasks.*": {"queue": "aether"},
}
celery_app.conf.task_acks_late = True
celery_app.conf.task_reject_on_worker_lost = True
celery_app.conf.task_default_retry_delay = 30
celery_app.conf.task_max_retries = 3


@celery_app.task(bind=True, name="app.tasks.run_pipeline")
def run_pipeline_task(self, topic: str | None = None):
    from app.engines.pipeline import run_demo_pipeline
    try:
        return run_demo_pipeline(topic_title=topic)
    except Exception as exc:
        raise self.retry(exc=exc)
