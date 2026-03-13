"""preference_site URL Configuration"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("",        include("preference_app.urls")),
]
