import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "blog_api.settings")

app = Celery("blog_api")


app.config_from_object("django.conf:settings", namespace="CELERY")


app.autodiscover_tasks()


app.conf.beat_schedule = {
    "log-message-every-5-minutes": {
        "task": "blog_api.tasks.log_periodic_message",
        "schedule": crontab(minute="*/5"),
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
