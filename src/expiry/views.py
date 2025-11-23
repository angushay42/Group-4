from django.contrib.auth.forms import (
    UserChangeForm, UserCreationForm, AuthenticationForm
)
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.validators import EmailValidator, validate_email
from django.core.handlers.wsgi import WSGIRequest
from django.contrib.sessions.models import Session

from . import forms     # relative import, unsure if safe? (probs fine)
from django.contrib import messages

import logging



logger = logging.getLogger('views')

def startup(request):
    logger.debug("startup page viewed")
    return render(request, 'expiry/startup.html')

def logout_view(request):
    logout(request)
    return redirect("login")

def login_view(request):

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

def signup_view(request):
    if request.method == "POST":
        form = forms.RegisterUserForm(request.POST)
        if form.is_valid():
            login(request,form.save())
            return redirect("dashboard")
    else:
        form = forms.RegisterUserForm()
    return render(request, 'expiry/signup.html', {"form" : form})

def dashboard(request):
    """
    tips from docs:
    - instantiate form objects in views
    - form instances have is_valid() method that attaches cleaned_data as an 
    attribute
    - if method=POST, pop the request.POST into the constructor (bind to 
    form data)
    - 
    """

    # TODO:
    # if user has any expiries, load them
    # otherwise, load some "you have no items" default value


    if not request.user.is_authenticated:   # limits access when not logged in
        return render(request, "login")     # redirect?
    else:
        return render(request, 'expiry/dashboard.html')


