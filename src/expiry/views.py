from django.shortcuts import render, get_object_or_404
from django.template import loader


from .models import Question

def login(request):
    template = loader.get_template("expiry/login.html")
    context = {"Login" : template}
    return render(request, "expiry/login.html", context)

def detail(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    return render(request, "polls/detail.html", {"question": question})