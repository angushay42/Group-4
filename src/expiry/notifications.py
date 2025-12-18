from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import timezone
from django.template.loader import render_to_string
from apscheduler.events import EVENT_JOB_ERROR

from expiry.models import Item

import logging

User = get_user_model()
logger = logging.getLogger('jobs')  # todo new log


# bug template does not exist
def send_notification(user_id: int):
    # get user

    try:
        user = User.objects.get(id=user_id)
    except TypeError as e:
        logger.debug(f"ERROR sending notification: {e}")
        return
    
    thresh = timezone.now() + timezone.timedelta(days=7)

    # get items
    # filter by <= 7 days
    items = Item.objects.filter(user=user, expiry_date__lte=thresh).order_by("-expiry_date")

    context = {
        "user": user,
        "items": items,
    }

    subject = render_to_string('emails/notification.txt', context=context)

    html = render_to_string('emails/notification.html', context=context)

    # format email
    # send email
    send_mail(
        subject=subject,
        message=html,
        from_email=None,
        recipient_list=[user.email],
    )
