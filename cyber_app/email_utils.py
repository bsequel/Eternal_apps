from django.core.mail import send_mail
from django.conf import settings


def notify_admin(subject, message):
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin[1] for admin in settings.ADMINS],
            fail_silently=False
        )
    except Exception as e:
        print(f"❌ Failed to send error email: {e}")
