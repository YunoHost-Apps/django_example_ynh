from axes.models import AccessLog
from bx_py_utils.test_utils.html_assertion import HtmlAssertionMixin
from django.conf import settings
from django.contrib.auth.models import User
from django.test import override_settings
from django.test.testcases import TestCase
from django.urls import NoReverseMatch
from django.urls.base import reverse
from django_ynh.test_utils import generate_basic_auth
from django_ynh.views import request_media_debug_view

import inventory


@override_settings(DEBUG=False)
class DjangoYnhTestCase(HtmlAssertionMixin, TestCase):
    def setUp(self):
        super().setUp()

        # Always start a fresh session:
        self.client = self.client_class()

    def test_settings(self):
        assert settings.PATH_URL == 'app_path'

        assert str(settings.FINAL_HOME_PATH).endswith('/local_test/opt_yunohost')
        assert str(settings.FINAL_WWW_PATH).endswith('/local_test/var_www')
        assert str(settings.LOG_FILE).endswith('/local_test/var_log_django_example_ynh.log')

        assert settings.ROOT_URLCONF == 'urls'

    def test_urls(self):
        assert reverse('admin:index') == '/app_path/'

        # The django_ynh debug view should not be avaiable:
        with self.assertRaises(NoReverseMatch):
            reverse(request_media_debug_view)

        # Serve user uploads via django_tools.serve_media_app:
        assert settings.MEDIA_URL == '/app_path/media/'
        assert reverse('serve_media_app:serve-media', kwargs={'user_token': 'token', 'path': 'foo/bar/'}) == (
            '/app_path/media/token/foo/bar/'
        )

    def test_auth(self):
        response = self.client.get('/app_path/')
        self.assertRedirects(response, expected_url='/app_path/login/?next=/app_path/')

    def test_create_unknown_user(self):
        assert User.objects.count() == 0

        self.client.cookies['SSOwAuthUser'] = 'test'

        response = self.client.get(
            path='/app_path/',
            HTTP_REMOTE_USER='test',
            HTTP_AUTH_USER='test',
            HTTP_AUTHORIZATION='basic dGVzdDp0ZXN0MTIz',
        )

        assert User.objects.count() == 1
        user = User.objects.first()
        assert user.username == 'test'
        assert user.is_active is True
        assert user.is_staff is True  # Set by: conf.django_ynh_demo_urls.setup_user_handler
        assert user.is_superuser is False

        self.assert_html_parts(
            response,
            parts=(
                f'<title>Site administration | PyInventory v{inventory.__version__}</title>',
                '<strong>test</strong>',
            ),
        )

    def test_wrong_auth_user(self):
        assert User.objects.count() == 0
        assert AccessLog.objects.count() == 0

        self.client.cookies['SSOwAuthUser'] = 'test'

        response = self.client.get(
            path='/app_path/',
            HTTP_REMOTE_USER='test',
            HTTP_AUTH_USER='foobar',  # <<< wrong user name
            HTTP_AUTHORIZATION='basic dGVzdDp0ZXN0MTIz',
        )

        assert User.objects.count() == 1
        user = User.objects.first()
        assert user.username == 'test'
        assert user.is_active is True
        assert user.is_staff is True  # Set by: conf.django_ynh_demo_urls.setup_user_handler
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
        )

        assert User.objects.count() == 1
        user = User.objects.first()
        assert user.username == 'test'
        assert user.is_active is True
        assert user.is_staff is True  # Set by: conf.django_ynh_demo_urls.setup_user_handler
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
            HTTP_AUTHORIZATION=generate_basic_auth(username='foobar', password='test123'),  # <<< wrong user name
        )

        assert User.objects.count() == 1
        user = User.objects.first()
        assert user.username == 'test'
        assert user.is_active is True
        assert user.is_staff is True  # Set by: conf.django_ynh_demo_urls.setup_user_handler
        assert user.is_superuser is False

        assert AccessLog.objects.count() == 1

        assert response.status_code == 403  # Forbidden
