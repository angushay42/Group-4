from datetime import time
from django import template
from expiry.models import UserSettings

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
    