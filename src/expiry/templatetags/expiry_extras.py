from datetime import time, datetime, timedelta, date, tzinfo
from django import template
from django.utils import timezone
from expiry.models import UserSettings, Item
from group4.settings import TIME_ZONE
import logging

logger = logging.getLogger('views') # todo different log?
register = template.Library()

@register.filter(name='zip')
def zip(a, b):
    return zip(a, b)

@register.filter(name='checked')
def checked(value: UserSettings, label):
    return value

@register.filter
def checker(settings: UserSettings, value):
    if not settings.notification_days:
        return ""
    val = int(value) in settings.notification_days
    return "checked" if val else ""

@register.filter
def required(settings: UserSettings):
    return "required" if settings.notifications else ""

@register.filter
def disabled(settings: UserSettings):

    return "disabled" if not settings.notifications else ""
        
@register.filter
def time_default(user_time: time):
    return user_time.strftime("%H:%M") if user_time else ''
    
@register.filter
def deletion_days(deleted: datetime):
    # if delta is small enough, "just now"
    # otherwise display timestamp of deletion
    threshhold = 10     # seconds
    s = ""
    try:
        now = timezone.now()
        logger.debug('trying delta')
        delta = now - deleted
        logger.debug('trying threshold')
        thresh = deleted + timedelta(seconds=threshhold)    # recent

        logger.debug('trying delta_helper')
        logger.debug(f"expiry: {deleted}, thresh: {thresh}")
        s = (
            f"Just now" if now < thresh 
            else f"{delta_helper(delta)} ago"
        )
    except TypeError as e:
        s = e
    return s

def delta_helper(td: timedelta) -> str:
    hours = td.seconds // 3600
    minutes = (td.seconds % 3600) // 60
    seconds = td.seconds % 60

    logger.debug("hours {}, minutes {}, seconds {}".format(hours, minutes, seconds))
    if minutes < 1:
        return f"{seconds} second{"s" if seconds > 1 else ""}" 
    if hours < 1:
        return f"{minutes} minute{"s" if minutes > 1 else ""}" 
    if td.days < 1:
        return f"{hours} hour{"s" if hours > 1 else ""}" 
    return f"{td.days} day{"s" if td.days > 1 else ""}" 

@register.filter
def delta_days(expiry: date):
    s = ""
    now = timezone.now().date()
    thresh = 1

    if thresh < 0:
        return 'Error: invalid threshold'
    delta = (expiry) - now
    logger.debug(f"delta {delta}")
    # if delta negative, then it has expired
    if delta.days < 0:
        s = f"Expired {abs(delta.days)} day{"s" if abs(delta.days) > 1 else ""} ago"

    # if delta <= thresh, it expires tomorrow
    elif delta.days <= thresh:
        s = f"Expires tomorrow"
    
    # else return delta
    else:
        s = f"{delta.days} day{"s" if delta.days > 1 else ""} left"

    return s

@register.filter
def expired(expiry_date: date, thresh: int):
    thresh = timedelta(days=thresh)
    if not expiry_date:
        return False
    return (expiry_date - thresh) < timezone.now().date()