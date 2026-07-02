import logging
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_welcome_email(self, user_email):
    subject = "Добро пожаловать в Blog API!"
    message = (
        "Здравствуйте!\n\n"
        "Спасибо за регистрацию в Blog API.\n"
        "Теперь вы можете создавать посты, редактировать и удалять свои "
        "публикации, а также читать посты других авторов.\n\n"
        "С уважением,\nКоманда Blog API"
    )
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )
        logger.info("Приветственное письмо отправлено на %s", user_email)
    except Exception as exc:
        logger.error("Ошибка отправки письма на %s: %s", user_email, exc)
        raise self.retry(exc=exc)
