################################################################################
################################################################################

# Please do not modify this file, it will be reset at the next update.
# You can edit the file __FINAL_HOME_PATH__/local_settings.py and add/modify the settings you need.
# The parameters you add in local_settings.py will overwrite these,
# but you can use the options and documentation in this file to find out what can be done.

################################################################################
################################################################################

from pathlib import Path as __Path

from django_ynh.secret_key import get_or_create_secret as __get_or_create_secret
from inventory_project.settings.base import *  # noqa


DEBUG = False  # Don't turn DEBUG on in production!

# -----------------------------------------------------------------------------

FINAL_HOME_PATH = __Path('__FINAL_HOME_PATH__')  # /opt/yunohost/$app
assert FINAL_HOME_PATH.is_dir(), f'Directory not exists: {FINAL_HOME_PATH}'

FINAL_WWW_PATH = __Path('__FINAL_WWW_PATH__')  # /var/www/$app
assert FINAL_WWW_PATH.is_dir(), f'Directory not exists: {FINAL_WWW_PATH}'

LOG_FILE = __Path('__LOG_FILE__')  # /var/log/$app/django_example_ynh.log
assert LOG_FILE.is_file(), f'File not exists: {LOG_FILE}'

PATH_URL = '__PATH_URL__'  # $YNH_APP_ARG_PATH
PATH_URL = PATH_URL.strip('/')

# -----------------------------------------------------------------------------

ROOT_URLCONF = 'urls'  # /opt/yunohost/django_example_ynh/ynh_urls.py

# Function that will be called to finalize a user profile:
YNH_SETUP_USER = 'setup_user.setup_project_user'

SECRET_KEY = __get_or_create_secret(FINAL_HOME_PATH / 'secret.txt')  # /opt/yunohost/$app/secret.txt

INSTALLED_APPS.append('django_ynh')

MIDDLEWARE.insert(
    MIDDLEWARE.index('django.contrib.auth.middleware.AuthenticationMiddleware') + 1,
    # login a user via HTTP_REMOTE_USER header from SSOwat:
    'django_ynh.sso_auth.auth_middleware.SSOwatRemoteUserMiddleware',
)

# Keep ModelBackend around for per-user permissions and superuser
AUTHENTICATION_BACKENDS = (
    'axes.backends.AxesBackend',  # AxesBackend should be the first backend!
    #
    # Authenticate via SSO and nginx 'HTTP_REMOTE_USER' header:
    'django_ynh.sso_auth.auth_backend.SSOwatUserBackend',
    #
    # Fallback to normal Django model backend:
    'django.contrib.auth.backends.ModelBackend',
)

LOGIN_REDIRECT_URL = None
LOGIN_URL = '/yunohost/sso/'
LOGOUT_REDIRECT_URL = '/yunohost/sso/'
# /yunohost/sso/?action=logout

# -----------------------------------------------------------------------------


ADMINS = (('__ADMIN__', '__ADMINMAIL__'),)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': '__APP__',
        'USER': '__APP__',
        'PASSWORD': '__DB_PWD__',
        'HOST': '127.0.0.1',
        'PORT': '5432',  # Default Postgres Port
        'CONN_MAX_AGE': 600,
    }
}

# Title of site to use
SITE_TITLE = '__APP__'

# Site domain
SITE_DOMAIN = '__DOMAIN__'

# Subject of emails includes site title
EMAIL_SUBJECT_PREFIX = f'[{SITE_TITLE}] '


# E-mail address that error messages come from.
SERVER_EMAIL = 'noreply@__DOMAIN__'

# Default email address to use for various automated correspondence from
# the site managers. Used for registration emails.
DEFAULT_FROM_EMAIL = '__ADMINMAIL__'

# List of URLs your site is supposed to serve
ALLOWED_HOSTS = ['__DOMAIN__']

# _____________________________________________________________________________
# Configuration for caching
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/__REDIS_DB__',
        # If redis is running on same host as PyInventory, you might
        # want to use unix sockets instead:
        # 'LOCATION': 'unix:///var/run/redis/redis.sock?db=1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': '__APP__',
    },
}

# _____________________________________________________________________________
# Static files (CSS, JavaScript, Images)

if PATH_URL:
    STATIC_URL = f'/{PATH_URL}/static/'
    MEDIA_URL = f'/{PATH_URL}/media/'
else:
    # Installed to domain root, without a path prefix?
    STATIC_URL = '/static/'
    MEDIA_URL = '/media/'

STATIC_ROOT = str(FINAL_WWW_PATH / 'static')
MEDIA_ROOT = str(FINAL_WWW_PATH / 'media')

# _____________________________________________________________________________
# django-ckeditor

CKEDITOR_BASEPATH = STATIC_URL + 'ckeditor/ckeditor/'

# _____________________________________________________________________________
# Django-dbbackup

DBBACKUP_STORAGE_OPTIONS['location'] = str(FINAL_HOME_PATH / 'backups')

# -----------------------------------------------------------------------------

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '{asctime} {levelname} {name} {module}.{funcName} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'formatter': 'verbose',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        },
        'log_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.WatchedFileHandler',
            'formatter': 'verbose',
            'filename': str(LOG_FILE),
        },
    },
    'loggers': {
        '': {'handlers': ['log_file', 'mail_admins'], 'level': 'INFO', 'propagate': False},
        'django': {'handlers': ['log_file', 'mail_admins'], 'level': 'INFO', 'propagate': False},
        'axes': {'handlers': ['log_file', 'mail_admins'], 'level': 'WARNING', 'propagate': False},
        'django_tools': {'handlers': ['log_file', 'mail_admins'], 'level': 'INFO', 'propagate': False},
        'django_ynh': {'handlers': ['log_file', 'mail_admins'], 'level': 'INFO', 'propagate': False},
        'inventory': {'handlers': ['log_file', 'mail_admins'], 'level': 'INFO', 'propagate': False},
    },
}

# -----------------------------------------------------------------------------

try:
    from local_settings import *  # noqa
except ImportError:
    pass
