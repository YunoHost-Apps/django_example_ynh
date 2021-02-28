from django.conf import settings
from django.contrib import admin
from django.urls import path

from django_yunohost_integration.views import request_media_debug_view


# settings.PATH_URL is the $YNH_APP_ARG_PATH
# Prefix all urls with "PATH_URL":
urlpatterns = [
    path(f'{settings.PATH_URL}/', admin.site.urls),
    path(f'{settings.PATH_URL}/debug/', request_media_debug_view),
]
