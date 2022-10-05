from bx_django_utils.admin_extra_views.registry import extra_view_registry
from django.contrib import admin
from django.urls import include, path

from example_project.views import DebugView


urlpatterns = [
    path('', DebugView.as_view(), name='debug-view'),
    path('admin/', include(extra_view_registry.get_urls())),
    path('admin/', admin.site.urls),
]
