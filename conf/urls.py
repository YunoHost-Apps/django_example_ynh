from django.conf import settings
from django.conf.urls import static
from django.contrib import admin
from django.urls import path

from django_ynh.views.debug import request_media_debug_view


# settings.PATH_URL is the $YNH_APP_ARG_PATH
# Prefix all urls with "PATH_URL":
urlpatterns = [
    path(f'{settings.PATH_URL}/', admin.site.urls),
]

if settings.SERVE_FILES:
    urlpatterns += static.static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns.append(path(f'{settings.PATH_URL}/debug/', request_media_debug_view))
