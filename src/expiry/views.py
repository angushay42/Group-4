from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.http.request import HttpRequest
from django.utils import timezone
from django.db.models import Case, When, IntegerField
from django.forms.models import model_to_dict

from . import forms
from .forms import AddItem
from .models import Item, UserSettings
from group4 import settings as django_settings

import logging
import datetime
import requests
import json

logger = logging.getLogger('views')

SOON_THRESH = 1  # todo


def startup(request: HttpRequest):
    logger.debug("startup page viewed")
    return render(request, 'expiry/startup.html')


def logout_view(request: HttpRequest):
    logout(request)
    return redirect("login")


def login_view(request: HttpRequest):
    code = 200
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        # todo ugly
        if request.POST.get('test_name'):
            logger.debug(f"testname: {request.POST.get('test_name')}")

        form = forms.LogininForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            check = authenticate(
                request,
                username=user.username,
                password=user.password
            )

            login(request, user)
            messages.success(request, "Logged in successfully!")
            return redirect("dashboard")
        else:
            logger.debug(
                f"login form invalid"
            )
            logger.debug(
                f"errors: {form.errors.as_json()}"
            )
            try:
                errors: dict = json.loads(form.errors.as_json())
            except:
                logger.debug(
                    f"error getting errors..."
                )
                ValueError("fatal")

            errors = errors.get('__all__')

            if any("Invalid" in message['message'] for message in errors):
                code = 401
            else:
                code = 400
    else:
        form = forms.LogininForm()
    return render(
        request,
        "expiry/login.html",
        {"login_form": form},
        status=code
    )


def signup_view(request: HttpRequest):
    if request.method == "POST":
        form = forms.RegisterUserForm(request.POST)
        if form.is_valid():
            login(request, form.save())
            return redirect("dashboard")
    else:
        form = forms.RegisterUserForm()
    return render(request, 'expiry/signup.html', {"form": form})


def dashboard(request: HttpRequest):
    
    if not request.user.is_authenticated:  # limits access when not logged in
        return render(request, "login")  # redirect?

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
            'frozen': items.filter(storage_type=Item.FREEZER).count(),
            'total': items.count(),
            'soon': items.filter(expiry_date__lte=expiry_threshold).count(),
        }
    }

    return render(request, 'expiry/dashboard.html', context=context)


def items_list(request: HttpRequest):
    """
    render all items
    take a query parameter to filter by
    error check for query parameters, if a false one given, just ignore it?
    """

    # todo clean input, or make sure dashboard.html sends same string
    filter = request.GET.get('filter')

    if not request.user.is_authenticated:
        return render(request, "login")

    logger.debug(f"items_list getting user and items")
    user = User.objects.get(username=request.user.username)
    items = Item.objects.filter(user=user)

    logger.debug(f"items: {items}")

    context = {'items': list(items)}

    if filter == "frozen":
        # annotate adds extra rows ONLY to QuerySet, shouldn't be
        # too much overhead
        # https://docs.djangoproject.com/en/5.2/topics/db/aggregation/
        # https://docs.djangoproject.com/en/5.2/ref/models/conditional-expressions/
        filtered = items.annotate(
            is_frozen=Case(
                When(storage_type="frozen", then=0),  # 0 is first
                default=1,
                output_field=IntegerField(),  # necessary?
            )
        ).order_by("is_frozen", "expiry_date")

        context['items'] = filtered  # todo safe?
    logger.debug(f"context: {context}")

    return render(request, 'expiry/items.html', context=context)


def settings(request: HttpRequest):
    if not request.user.is_authenticated:
        return render(request, "login")

    user = User.objects.get(username=request.user.username)

    _settings, created = UserSettings.objects.get_or_create(
        user=request.user,
        defaults={
            'notifications': False,
            'dark_mode': False,
            'notification_time': datetime.time(9, 30),
            'notification_days': [],
        }
    )

    logger.debug(
        f"{json.dumps(
            model_to_dict(_settings),
            indent=2,
            default=lambda x: str(x)
        )}"
    )

    if request.method == 'POST':
        form = forms.SettingsForm(request.POST)

        if form.is_valid():
            notif_enabled = form.cleaned_data['notifications']
            notif_time = form.cleaned_data['notification_time']
            notif_days = [int(x) for x in form.cleaned_data['notification_days']]

            if notif_enabled:
                if not (
                        notif_time == _settings.notification_time
                        and notif_days == _settings.notification_days
                ):
                    url = f"http://{django_settings.SCHED_SERVER_URL}:{django_settings.SCHED_SERVER_PORT}"
                    params = {
                        'user': user.username,
                        'time': notif_time,
                        'day_of_week': notif_days
                    }

                    try:
                        response = requests.get(url=url, params=params)
                        if not response.status_code == 200:
                            raise TypeError
                    except:
                        logger.debug("CRITICAL ERROR: Could not connect to Scheduler server")

            _settings.notifications = notif_enabled
            _settings.notification_days = notif_days if notif_enabled else None
            _settings.notification_time = notif_time if notif_enabled else None
            _settings.dark_mode = form.cleaned_data['dark_mode']
            _settings.save()

            messages.success(request, "Settings saved!")
            return redirect('settings')

    else:
        # Pre-populate form with current settings
        notif_days_initial = []
        if _settings.notification_days:
            notif_days_initial = [str(d) for d in _settings.notification_days]

        form = forms.SettingsForm(initial={
            'notifications': _settings.notifications,
            'dark_mode': _settings.dark_mode,
            'notification_time': _settings.notification_time,
            'notification_days': notif_days_initial,
        })

    context = {
        'settings': _settings,
        'form': form
    }

    return render(request, 'expiry/settings.html', context=context)


def add_item_view(request: HttpRequest):
    if not request.user.is_authenticated:  # limits access when not logged in
        return redirect("login")

    if request.method == "POST":
        logger.debug(f"add_item POST requested")
        form = AddItem(request.POST)
        if form.is_valid():
            item_name = form.cleaned_data['item_name']
            item_category = form.cleaned_data['item_category']
            expiry_date = form.cleaned_data['expiry_date']
            quantity = form.cleaned_data['quantity']

            # TODO: Add database saving here
            Item.objects.create(
                user=request.user,
                item_name=item_name,
                expiry_date=expiry_date,
                item_category=item_category,
                quantity=quantity
            )

            messages.success(request, "Item added successfully!")
            return redirect("items")
    else:
        form = AddItem()

    return render(request, "expiry/add_item.html", {"form": form})


def edit_item_view(request: HttpRequest, item_id):
    if not request.user.is_authenticated:
        return redirect("login")

    item = get_object_or_404(Item, id=item_id, user=request.user)

    if request.method == "POST":
        form = AddItem(request.POST)
        if form.is_valid():
            item.item_name = form.cleaned_data["item_name"]
            item.item_category = form.cleaned_data["item_category"]
            item.quantity = form.cleaned_data["quantity"]
            item.expiry_date = form.cleaned_data["expiry_date"]
            item.save()

            return redirect("items")

    else:
        form = AddItem(initial={
            "item_name": item.item_name,
            "item_category": item.item_category,
            "quantity": item.quantity,
            "expiry_date": item.expiry_date,
        })

    return render(request, "expiry/edit_item.html", {
        "form": form,
        "item": item,
    })
