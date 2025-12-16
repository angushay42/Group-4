from .models import UserSettings
import datetime as dt

def user_settings(request):

    if request.user.is_authenticated:
        user_settings, created = UserSettings.objects.get_or_create(
            user=request.user,
            defaults={
                'notifications': False,
                'dark_mode': False,
                'notification_time': dt.time(9,30),
                'notification_days': 0,
            }
        )
        return {
            'dark_mode': user_settings.dark_mode,
            'user_settings': user_settings,
        }

    return {
        'dark_mode': False,
        'user_settings': None,
    }