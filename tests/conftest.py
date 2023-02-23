"""
    Special pytest init:

        - Build a "local_test" YunoHost installation
        - init Django with this local test installation

    So the pytests will run against this local test installation
"""
import os
import sys
from pathlib import Path

import django
from django_yunohost_integration.local_test import create_local_test


BASE_PATH = Path(__file__).parent.parent

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'


def pytest_configure():
    print('Compile YunoHost files...')
    final_path = create_local_test(
        django_settings_path=BASE_PATH / 'conf' / 'settings.py',
        destination=BASE_PATH / 'local_test',
        runserver=False,
        extra_replacements={
            '__DEBUG_ENABLED__': '0',
            '__LOG_LEVEL__': 'INFO',
            '__ADMIN_EMAIL__': 'foo-bar@test.tld',
            '__DEFAULT_FROM_EMAIL__': 'django_app@test.tld',
        },
    )
    print('Local test files created here:')
    print(f'"{final_path}"')

    os.chdir(final_path)
    final_home_str = str(final_path)
    if final_home_str not in sys.path:
        sys.path.insert(0, final_home_str)

    django.setup()
