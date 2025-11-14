from django.shortcuts import render, get_object_or_404
from django.template import loader
from django.contrib.auth.models import User
from django.contrib.auth import get_user

from .models import Question

def login(request):
    if 'username' in request.POST and 'password' in request.POST:
        print("yippee!")
        pass    # do stuff with details

    template = loader.get_template("expiry/login.html")
    context = {"Login" : template}

    return render(request, "expiry/login.html", context)



def detail(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    return render(request, "polls/detail.html", {"question": question})