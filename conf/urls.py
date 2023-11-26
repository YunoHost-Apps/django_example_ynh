"""
    urls.py
    ~~~~~~~

    Look at real examples, here:

     * https://github.com/YunoHost-Apps/django-fritzconnection_ynh/blob/master/conf/urls.py
     * https://github.com/YunoHost-Apps/django-for-runners_ynh/blob/testing/conf/urls.py
     * https://github.com/YunoHost-Apps/pyinventory_ynh/blob/testing/conf/urls.py

"""


from django.conf import settings
from django.urls import include, path
from django.views.generic import RedirectView


if settings.PATH_URL:
    # settings.PATH_URL is __PATH__
    # Prefix all urls with "PATH_URL":
    urlpatterns = [
        path('', RedirectView.as_view(url=f'{settings.PATH_URL}/')),
        path(f'{settings.PATH_URL}/', include('django_example.urls')),
    ]
else:
    # Installed to domain root, without a path prefix
    # Just use the default project urls.py
    from django_example.urls import urlpatterns  # noqa
