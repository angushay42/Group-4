from django.contrib.auth.forms import UserChangeForm, UserCreationForm, AuthenticationForm
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.validators import EmailValidator, validate_email
from django.core.handlers.wsgi import WSGIRequest
from django.contrib.sessions.models import Session


import logging

logger = logging.getLogger('views')

def startup(request):
    logger.debug("startup page viewed")
    return render(request, 'expiry/startup.html')

def logout_view(request):
    logout(request)
    return render(request, "expiry/login.html")

def login_view(request: WSGIRequest):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect("expiry/dashboard.html")
    else:
        form = AuthenticationForm()
    return render(request, "expiry/login.html", {"form" : form})

def signup_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            login(request,form.save())
            return redirect("expiry:dashboard")
    else:
        form = UserCreationForm()
    return render(request, 'expiry/signup.html', {"form" : form})


def dashboard(request):
    if not request.user.is_authenticated:    #limits access when not logged in
        return render(request, "expiry/login.html")
    else:
        return render(request, 'expiry/dashboard.html')


