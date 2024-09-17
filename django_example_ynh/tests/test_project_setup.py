import tomllib

from bx_django_utils.filename import clean_filename
from bx_py_utils.path import assert_is_dir, assert_is_file
from django.test.testcases import TestCase
from django_tools.unittest_utils.project_setup import check_editor_config
from django_yunohost_integration.path_utils import get_project_root
from django_example import __version__ as upstream_version

from django_example_ynh import __version__ as ynh_pkg_version


def assert_file_contains_string(file_path, string):
    with file_path.open('r') as f:
        for line in f:
            if string in line:
                return
    raise AssertionError(f'File {file_path} does not contain {string!r} !')


class ProjectSetupTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        manifest_path = get_project_root() / 'manifest.toml'
        assert_is_file(manifest_path)

        cls.manifest_cfg = tomllib.loads(manifest_path.read_text(encoding='UTF-8'))

    def test_version(self):
        assert ynh_pkg_version.startswith(
            upstream_version
        ), f'{ynh_pkg_version=} does not start with {upstream_version=}'
        self.assertIn('+ynh', ynh_pkg_version)

        # pyproject.toml needs a PEP 440 conform version and used "+ynh"
        # the YunoHost syntax is: "~ynh", just "convert this:
        manifest_version = ynh_pkg_version.replace('+', '~')
        self.assertEqual(self.manifest_cfg['version'], manifest_version)

    def test_screenshot_filenames(self):
        """
        https://forum.yunohost.org/t/yunohost-bot-cant-handle-spaces-in-screenshots/19483
        """
        screenshot_path = get_project_root() / 'doc' / 'screenshots'
        assert_is_dir(screenshot_path)
        renamed = []
        for file_path in screenshot_path.iterdir():
            file_name = file_path.name
            if file_name.startswith('.'):
                continue
            cleaned_name = clean_filename(file_name)
            if cleaned_name != file_name:
                new_path = file_path.with_name(cleaned_name)
                file_path.rename(new_path)
                renamed.append(f'{file_name!r} renamed to {cleaned_name!r}')
        assert not renamed, f'Bad screenshots file names found: {", ".join(renamed)}'

    def test_check_editor_config(self):
        check_editor_config(package_root=get_project_root())

    def test_manifest_toml(self):
        self.assertEqual(self.manifest_cfg['packaging_format'], 2)
        self.assertEqual(
            set(self.manifest_cfg['install'].keys()),
            {
                'update_python',
                'admin',
                'admin_email',
                'debug_enabled',
                'default_from_email',
                'domain',
                'init_main_permission',
                'log_level',
                'path',
            },
        )
        self.assertEqual(
            set(self.manifest_cfg['resources'].keys()),
            {
                'apt',
                'data_dir',
                'database',
                'install_dir',
                'permissions',
                'ports',
                'system_user',
            },
        )
