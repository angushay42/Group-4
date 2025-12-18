from datetime import time, datetime, timedelta, date
from django import template
from expiry.models import UserSettings, Item

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
def deletion_days(expiry: datetime):
    # if delta is small enough, "just now"
    # otherwise display timestamp of deletion
    s = ""
    try:
        delta = datetime.now() - expiry
        thresh = datetime.now() + timedelta(minutes=1)  # recent
        s = (
            f"Just now" if expiry < thresh 
            else f"{delta_helper(delta)} ago"
        )
    except TypeError:
        # todo
        pass
    return s

def delta_helper(td: timedelta) -> str:
    hours = td.seconds // 3600
    minutes = (td.seconds % 3600) // 60
    seconds = td.seconds % 60

    if minutes < 1:
        return f"{seconds} second{"s" if seconds > 1 else ""}" 
    if hours < 1:
        return f"{minutes} second{"s" if minutes > 1 else ""}" 
    if td.days < 1:
        return f"{hours} second{"s" if hours > 1 else ""}" 
    return f"{td.days} second{"s" if td.days > 1 else ""}" 

@register.filter
def delta_days(expiry: date):
    pass