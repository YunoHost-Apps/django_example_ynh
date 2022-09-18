import os
import shutil
import subprocess
from pathlib import Path

import tomli
from django_tools.unittest_utils.project_setup import check_editor_config


PACKAGE_ROOT = Path(__file__).parent.parent


def assert_file_contains_string(file_path, string):
    with file_path.open('r') as f:
        for line in f:
            if string in line:
                return
    raise AssertionError(f'File {file_path} does not contain {string!r} !')


def test_version():
    pyproject_toml_path = Path(PACKAGE_ROOT, 'pyproject.toml')
    pyproject_toml = tomli.loads(pyproject_toml_path.read_text(encoding='UTF-8'))
    version = pyproject_toml['tool']['poetry']['version']
    assert '~ynh' not in version
    assert version[0].isdigit()

    assert_file_contains_string(
        file_path=Path(PACKAGE_ROOT, 'manifest.json'),
        string=f'"version": "{version}~ynh',
    )


def test_poetry_check():
    poerty_bin = shutil.which('poetry')

    output = subprocess.check_output(
        [poerty_bin, 'check'],
        text=True,
        env=os.environ,
        stderr=subprocess.STDOUT,
        cwd=str(PACKAGE_ROOT),
    )
    print(output)
    assert output == 'All set!\n'


def test_check_editor_config():
    check_editor_config(package_root=PACKAGE_ROOT)
