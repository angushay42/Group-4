from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")

def login(request):
    template = loader.get_template("expiry/login.html")
    context = {}
    return template.render(context, request)
    context = {}
    return render(request, "expiry/login.html", context)

