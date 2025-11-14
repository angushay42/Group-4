from django.shortcuts import render, get_object_or_404
from django.template import loader
from django.contrib.auth.models import User
from django.contrib.auth import get_user

import logging

logger = logging.getLogger('views')

def startup(request):
    logger.debug("startup page viewed")
    return render(request, 'expiry/startup.html')

def login_view(request):
    logger.debug("login page viewed")
    if request.method == 'POST':
        logger.debug("post data: {}".format(
            request.POST
        ))
        email = request.POST.get('email')
        password = request.POST.get('password')

        logger.debug("email: {}, password: {}".format(
            email, password
        ))

        if (email == None and password == None):
            logger.debug("no email or password")

        

        #this is where authentication logic needs to go

    return render(request, 'expiry/login.html')

def signup_view(request):
    return render(request, 'expiry/signup.html')

def dashboard(request):
    return render(request, 'expiry/dashboard.html')


