import logging
from celery import shared_task

logger = logging.getLogger("celery_beat")

@shared_task
def log_periodic_message():
    message = "✅ Периодическая задача Celery Beat выполнена успешно"
    logger.info(message)
    print(message)
    return message