from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('expiry/', include('expiry.urls')),  # or keep this
    path('admin/', admin.site.urls),
]
