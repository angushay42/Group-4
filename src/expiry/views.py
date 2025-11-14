from django.shortcuts import render, get_object_or_404
from django.template import loader
from django.contrib.auth.models import User
from django.contrib.auth import get_user

def startup(request):
    return render(request, 'expiry/startup.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        #this is where authentication logic needs to go

    return render(request, 'expiry/login.html')

def signup_view(request):
    return render(request, 'expiry/signup.html')

def dashboard(request):
    return render(request, 'expiry/dashboard.html')


