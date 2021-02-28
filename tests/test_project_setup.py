import os
import shutil
import subprocess
from pathlib import Path

import django_exyunohost_integration


PACKAGE_ROOT = Path(__file__).parent.parent


def assert_file_contains_string(file_path, string):
    with file_path.open('r') as f:
        for line in f:
            if string in line:
                return
    raise AssertionError(f'File {file_path} does not contain {string!r} !')


def test_version():
    version = inventory.__version__

    assert_file_contains_string(file_path=Path(PACKAGE_ROOT, 'pyproject.toml'), string=f'version = "{version}~ynh')
    assert_file_contains_string(file_path=Path(PACKAGE_ROOT, 'pyproject.toml'), string=f'django_example_ynh = "=={version}"')
    assert_file_contains_string(file_path=Path(PACKAGE_ROOT, 'manifest.json'), string=f'"version": "{version}~ynh')


def test_poetry_check():
    poerty_bin = shutil.which('poetry')

    output = subprocess.check_output(
        [poerty_bin, 'check'],
        universal_newlines=True,
        env=os.environ,
        stderr=subprocess.STDOUT,
        cwd=str(PACKAGE_ROOT),
    )
    print(output)
    assert output == 'All set!\n'
