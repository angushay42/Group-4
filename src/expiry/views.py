from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.http.request import HttpRequest
from django.utils import timezone
from django.db.models import Case, When, IntegerField

from . import forms
from .forms import AddItem
from .models import Item, UserSettings
from group4.settings import SCHED_SERVER_PORT, SCHED_SERVER_URL

import logging
import datetime
import requests

logger = logging.getLogger('views')

SOON_THRESH = 10 # todo

def startup(request: HttpRequest):
    logger.debug("startup page viewed")
    return render(request, 'expiry/startup.html')

def logout_view(request: HttpRequest):
    logout(request)
    return redirect("login")

def login_view(request: HttpRequest):

    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = forms.LogininForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)
            messages.success(request, "Logged in successfully!")
            return redirect("dashboard")
    else:
        form = forms.LogininForm()
    return render(request, "expiry/login.html", {"login_form" : form})

def signup_view(request: HttpRequest):
    if request.method == "POST":
        form = forms.RegisterUserForm(request.POST)
        if form.is_valid():
            login(request, form.save())
            return redirect("dashboard")
    else:
        form = forms.RegisterUserForm()
    return render(request, 'expiry/signup.html', {"form" : form})

def dashboard(request: HttpRequest):
    """
    tips from docs:
    - instantiate form objects in views
    - form instances have is_valid() method that attaches cleaned_data as an 
    attribute
    - if method=POST, pop the request.POST into the constructor (bind to 
    form data)
    - 
    """

    if not request.user.is_authenticated:   # limits access when not logged in
        return render(request, "login")     # redirect?


    user = User.objects.get(username=request.user.username)  
    items = Item.objects.filter(user=user)
    
    # get total, expires soon, frozen
    expiry_threshold = (
        timezone.now() +
        datetime.timedelta(days=SOON_THRESH)
    )

    context = {
        'items': items, 
        "totals": {
            'frozen': len(items.filter(storage_type=Item.FREEZER)), 
            'total': len(items), 
            'soon': len(items.filter(expiry_date__lte=expiry_threshold)),
        }
    }

    return render(request, 'expiry/dashboard.html', context=context)

def items_list(request: HttpRequest):
    """
    render all items
    take a query parameter to filter by
    error check for query parameters, if a false one given, just ignore it?
    """

    #todo clean input, or make sure dashboard.html sends same string
    filter = request.GET.get('filter')
    

    if not request.user.is_authenticated:
        return render(request, "login")

    user = User.objects.get(username=request.user.username)  
    items = Item.objects.filter(user=user)

    context = {'items': items}

    if filter == "frozen":
        # annotate adds extra rows ONLY to QuerySet, shouldn't be
        # too much overhead
        # https://docs.djangoproject.com/en/5.2/topics/db/aggregation/
        # https://docs.djangoproject.com/en/5.2/ref/models/conditional-expressions/
        filtered = items.annotate(
            is_frozen=Case(
                When(storage_type="frozen", then=0),    # 0 is first
                default=1,
                output_field=IntegerField(),            # necessary?
            )
        ).order_by("is_frozen", "expiry_date")

        context['items'] = filtered # todo safe?

    return render(request, 'expiry/items.html', context=context)
 
def settings(request: HttpRequest):

    if not request.user.is_authenticated:  
        return render(request, "login")
    
    # load user settings
    user = User.objects.get(username=request.user.username)

    # private to avoid overriding 
    _settings: UserSettings = UserSettings.objects.filter(user=user)

    if request.method == 'POST':
        form = forms.SettingsForm(request.POST)

        if form.is_valid():
            if form.cleaned_data['notification_preference'] == False:
                # todo delete jobs
                pass
            else:
                notif_time: datetime.time =\
                    form.cleaned_data['notification_time']
                
                notif_day: int = form.cleaned_data['notification_day']

                if not (
                    notif_time == _settings.notification_time
                    and notif_day == _settings.notification_day
                ):
                    # idea if we add functionality for customising data view,\
                    # we may need to delete old jobs

                    # todo wrap this as a function
                    # make a request to scheduler server
                    url = f"http://{SCHED_SERVER_URL}:{SCHED_SERVER_PORT}"
                    params = {
                        'user': user.name,
                        'time': notif_time, # bug too complex to pass?
                        'day_of_week': notif_day
                    }

                    response = requests.get(
                        url=url,
                        params=params,
                    )
                    # check that response is OK
                    if not response.status_code == 200:
                        # todo create custom exception for this app
                        raise TypeError
                    pass
                
            # save settings
            notif_enabled = form.cleaned_data['notification_preference']
            _settings.notification_enabled = notif_enabled
            _settings.notification_day = notif_day if notif_enabled else None
            _settings.notification_time = notif_time if notif_enabled else None
            _settings.dark_mode = form.cleaned_data['dark_mode']

            _settings.save()

    else:
        form = forms.SettingsForm()

    context = {
        'settings': _settings,
        'form': form
    }

    return render(request,'expiry/settings.html', context=context)

def add_item_view(request: HttpRequest):
    if not request.user.is_authenticated:  # limits access when not logged in
        return redirect("login")

    if request.method == "POST":
        form = AddItem(request.POST)
        if form.is_valid():
            item_name = form.cleaned_data['item_name']
            item_category = form.cleaned_data['item_category']
            expiry_date = form.cleaned_data['expiry_date']
            quantity = form.cleaned_data['quantity']

            # TODO: Add database saving here
            # Item.objects.create(name=item_name, expiry=expiry_date, qty=quantity)

            messages.success(request, "Item added successfully!")
            return redirect("dashboard")
    else:
        form = AddItem()

    return render(request, "expiry/add_item.html", {"form": form})