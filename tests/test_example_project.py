from bx_django_utils.test_utils.html_assertion import HtmlAssertionMixin
from django.conf import settings
from django.test.testcases import TestCase
from django.urls.base import reverse

from example_project import __version__


class ExampleProjectTestCase(HtmlAssertionMixin, TestCase):
    def test_urls(self):
        assert settings.PATH_URL == 'app_path'
        assert reverse('admin:index') == '/app_path/admin/'
        assert reverse('debug-view') == '/app_path/'

        ###############################################################################
        # Test as anonymous user

        response = self.client.get(
            path='/app_path/',
            secure=True,
        )
        self.assert_html_parts(
            response,
            parts=(
                f'<h2>YunoHost Django Example Project v{__version__}</h2>',
                '<a href="/app_path/admin/">Django Admin</a>',
                '<tr><td>User:</td><td>AnonymousUser</td></tr>',
                '<tr><td>META:</td><td><pre><code>&#x27;&#x27;</code></pre></td></tr>',
            ),
        )

        ###############################################################################
        # Test as SSO user

        self.client.cookies['SSOwAuthUser'] = 'test'

        response = self.client.get(
            path='/app_path/',
            HTTP_REMOTE_USER='test',
            HTTP_AUTH_USER='test',
            HTTP_AUTHORIZATION='basic dGVzdDp0ZXN0MTIz',
            secure=True,
        )
        self.assert_html_parts(
            response,
            parts=(
                f'<h2>YunoHost Django Example Project v{__version__}</h2>',
                '<a href="/app_path/admin/">Django Admin</a>',
                '<tr><td>User:</td><td>test</td></tr>',
                '&#x27;HTTP_COOKIE&#x27;: &#x27;SSOwAuthUser=test&#x27;',
            ),
        )
