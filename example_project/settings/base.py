"""
    Django Project settings
"""
import os as __os


ENV_TYPE = __os.environ.get('ENV_TYPE', None)


INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'axes',  # https://github.com/jazzband/django-axes
    'django_yunohost_integration.apps.YunohostIntegrationConfig',
    #
    'bx_django_utils.admin_extra_views.apps.AdminExtraViewsAppConfig',
    'bx_django_utils.admin_extra_views.admin_config.CustomAdminConfig',
]
