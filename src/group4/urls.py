from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('expiry/', include('expiry.urls')), 
    path('admin/', admin.site.urls),
]
