from django.urls import path

from . import views

urlpatterns = [
    path("<int:question>/", views.login, name="login")
]