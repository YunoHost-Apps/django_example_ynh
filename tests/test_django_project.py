from axes.models import AccessLog
from bx_django_utils.test_utils.html_assertion import HtmlAssertionMixin
from django.conf import settings
from django.contrib.auth.models import User
from django.test import override_settings
from django.test.testcases import TestCase
from django.urls.base import reverse

from django_yunohost_integration.test_utils import generate_basic_auth


@override_settings(DEBUG=False)
class DjangoYnhTestCase(HtmlAssertionMixin, TestCase):
    def setUp(self):
        super().setUp()

        # Always start a fresh session:
        self.client = self.client_class()

    def test_settings(self):
        assert settings.PATH_URL == 'app_path'

        assert str(settings.FINALPATH).endswith('/local_test/opt_yunohost')
        assert str(settings.PUBLIC_PATH).endswith('/local_test/var_www')
        assert str(settings.LOG_FILE).endswith('/local_test/var_log_django_example_ynh.log')

        assert settings.ROOT_URLCONF == 'urls'

    def test_config_panel_settings(self):
        # config_panel.toml settings, set via tests.conftest.pytest_configure():
        assert settings.DEBUG_ENABLED == '0' and settings.DEBUG is False
        assert settings.LOG_LEVEL == 'INFO'
        assert settings.ADMIN_EMAIL == 'foo-bar@test.tld'
        assert settings.DEFAULT_FROM_EMAIL == 'django_app@test.tld'

    def test_auth(self):
        assert settings.PATH_URL == 'app_path'
        assert reverse('admin:index') == '/app_path/admin/'

        # SecurityMiddleware should redirects all non-HTTPS requests to HTTPS:
        assert settings.SECURE_SSL_REDIRECT is True
        response = self.client.get('/app_path/admin/', secure=False)
        self.assertRedirects(
            response,
            status_code=301,  # permanent redirect
            expected_url='https://testserver/app_path/admin/',
            fetch_redirect_response=False,
        )

        response = self.client.get('/app_path/admin/', secure=True)
        self.assertRedirects(
            response,
            expected_url='/app_path/admin/login/?next=%2Fapp_path%2Fadmin%2F',
            fetch_redirect_response=False,
        )

    def test_create_unknown_user(self):
        assert User.objects.count() == 0

        self.client.cookies['SSOwAuthUser'] = 'test'

        response = self.client.get(
            path='/app_path/admin/',
            HTTP_REMOTE_USER='test',
            HTTP_AUTH_USER='test',
            HTTP_AUTHORIZATION='basic dGVzdDp0ZXN0MTIz',
            secure=True,
        )

        assert User.objects.count() == 1
        user = User.objects.first()
        assert user.username == 'test'
        assert user.is_active is True
        assert user.is_staff is True  # Set by: conf.setup_user.setup_project_user
        assert user.is_superuser is False

        self.assert_html_parts(
            response,
            parts=(
                '<h1 id="site-name"><a href="/app_path/admin/">Django administration</a></h1>',
                '<strong>test</strong>',
            ),
        )

    def test_wrong_auth_user(self):
        assert User.objects.count() == 0
        assert AccessLog.objects.count() == 0

        self.client.cookies['SSOwAuthUser'] = 'test'

        response = self.client.get(
            path='/app_path/admin/',
            HTTP_REMOTE_USER='test',
            HTTP_AUTH_USER='foobar',  # <<< wrong user name
            HTTP_AUTHORIZATION='basic dGVzdDp0ZXN0MTIz',
            secure=True,
        )

        assert User.objects.count() == 1
        user = User.objects.first()
        assert user.username == 'test'
        assert user.is_active is True
        assert user.is_staff is True  # Set by: conf.setup_user.setup_project_user
        assert user.is_superuser is False

        assert AccessLog.objects.count() == 1

        assert response.status_code == 403  # Forbidden

    def test_wrong_cookie(self):
        assert User.objects.count() == 0
        assert AccessLog.objects.count() == 0

        self.client.cookies['SSOwAuthUser'] = 'foobar'  # <<< wrong user name

        response = self.client.get(
            path='/app_path/',
            HTTP_REMOTE_USER='test',
            HTTP_AUTH_USER='test',
            HTTP_AUTHORIZATION='basic dGVzdDp0ZXN0MTIz',
            secure=True,
        )

        assert User.objects.count() == 1
        user = User.objects.first()
        assert user.username == 'test'
        assert user.is_active is True
        assert user.is_staff is True  # Set by: conf.setup_user.setup_project_user
        assert user.is_superuser is False

        assert AccessLog.objects.count() == 1

        assert response.status_code == 403  # Forbidden

    def test_wrong_authorization_user(self):
        assert User.objects.count() == 0

        self.client.cookies['SSOwAuthUser'] = 'test'

        response = self.client.get(
            path='/app_path/',
            HTTP_REMOTE_USER='test',
            HTTP_AUTH_USER='test',
            HTTP_AUTHORIZATION=generate_basic_auth(
                username='foobar',  # <<< wrong user name
                password='test123',
            ),
            secure=True,
        )

        assert User.objects.count() == 1
        user = User.objects.first()
        assert user.username == 'test'
        assert user.is_active is True
        assert user.is_staff is True  # Set by: conf.setup_user.setup_project_user
        assert user.is_superuser is False

        assert AccessLog.objects.count() == 1

        assert response.status_code == 403  # Forbidden
