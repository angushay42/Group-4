from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user

from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.validators import EmailValidator, validate_email
from django.core.handlers.wsgi import WSGIRequest
from django.contrib.sessions.models import Session


import logging

logger = logging.getLogger('views')

def startup(request):
    logger.debug("startup page viewed")
    return render(request, 'expiry/startup.html')

def login_view(request: WSGIRequest):
    logger.debug("login page viewed")

    logger.debug("session before checks: {}".format(
        request.session.get_expiry_age()
    ))

    request.session.set_expiry(0) # until browser closed

    if request.method == 'POST':
        # get details
        email = request.POST.get('email')
        password = request.POST.get('password')

        # checks, shouldn't ever happen due to html require
        if (email == None and password == None):
            logger.debug("whoops, no email or password")

        # check if email is potentially valid
        validator = EmailValidator()
        try:
            validator(email)
        except ValidationError as err:
            return render(
                request, 
                'expiry/login.html', 
                {'error': str(err)},
                status=400
            )
        
        # check if user exists in database
        user = authenticate(request, username=email, password=password)
        if user is not None:

            # default is on browser close
            if request.POST.get("remember_me") == "on":  # don't like this 
                logger.debug("remember_me is True")

                request.session.set_expiry(None)

            login(request, user)
            return redirect('dashboard')
        else:
            # doesn't exist, or invalid password
            return render(
                request, 
                'expiry/login.html', {
                    'error': "Invalid email or password"
                },
                status=401
            )
            
        
    
    logger.debug("session after checks: {}".format(
        request.session.get_expiry_age()
    ))

    return render(request, 'expiry/login.html')

def signup_view(request):
    return render(request, 'expiry/signup.html')

def dashboard(request):
    return render(request, 'expiry/dashboard.html')


