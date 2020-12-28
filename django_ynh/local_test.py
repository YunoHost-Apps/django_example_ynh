"""
    Create a YunoHost package local test
"""
import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path

from django_ynh.path_utils import assert_is_dir, assert_is_file
from django_ynh.test_utils import generate_basic_auth


def verbose_check_call(command, verbose=True, **kwargs):
    """ 'verbose' version of subprocess.check_call() """
    if verbose:
        print('_' * 100)
        msg = f'Call: {command!r}'
        verbose_kwargs = ', '.join(f'{k}={v!r}' for k, v in sorted(kwargs.items()))
        if verbose_kwargs:
            msg += f' (kwargs: {verbose_kwargs})'
        print(f'{msg}\n', flush=True)

    env = os.environ.copy()
    env['PYTHONUNBUFFERED'] = '1'

    popenargs = shlex.split(command)
    subprocess.check_call(popenargs, universal_newlines=True, env=env, **kwargs)


def call_manage_py(final_home_path, args):
    verbose_check_call(
        command=f'{sys.executable} manage.py {args}',
        cwd=final_home_path,
    )


def copy_patch(src_file, replaces, final_home_path):
    dst_file = final_home_path / src_file.name
    print(f'{src_file} -> {dst_file}')

    with src_file.open('r') as f:
        content = f.read()

    if replaces:
        for old, new in replaces.items():
            if old in content:
                print(f' * Replace "{old}" -> "{new}"')
                content = content.replace(old, new)

    with dst_file.open('w') as f:
        f.write(content)


def create_local_test(django_settings_path, destination, runserver=False):
    assert_is_file(django_settings_path)

    django_settings_name = django_settings_path.stem

    conf_path = django_settings_path.parent

    assert isinstance(destination, Path)
    destination = destination.resolve()
    if not destination.is_dir():
        destination.mkdir(parents=False)

    assert_is_dir(destination)

    final_home_path = destination / 'opt_yunohost'
    final_www_path = destination / 'var_www'
    log_file = destination / 'var_log_django_ynh.log'

    REPLACES = {
        '__FINAL_HOME_PATH__': str(final_home_path),
        '__FINAL_WWW_PATH__': str(final_www_path),
        '__LOG_FILE__': str(destination / 'var_log_django_ynh.log'),
        '__PATH_URL__': 'app_path',
        '__DOMAIN__': '127.0.0.1',
        'django.db.backends.postgresql': 'django.db.backends.sqlite3',
        "'NAME': '__APP__',": f"'NAME': '{destination / 'test_db.sqlite'}',",
        'django_redis.cache.RedisCache': 'django.core.cache.backends.dummy.DummyCache',
        # Just use the default logging setup from django_ynh project:
        'LOGGING = {': 'HACKED_DEACTIVATED_LOGGING = {',
    }

    for p in (final_home_path, final_www_path):
        if p.is_dir():
            print(f'Already exists: "{p}", ok.')
        else:
            p.mkdir(parents=True, exist_ok=True)

    log_file.touch(exist_ok=True)

    for src_file in conf_path.glob('*.py'):
        copy_patch(src_file=src_file, replaces=REPLACES, final_home_path=final_home_path)

    with Path(final_home_path / 'local_settings.py').open('w') as f:
        f.write('# Only for local test run\n')
        f.write('SERVE_FILES = True  # used in src/inventory_project/urls.py\n')
        f.write('AUTH_PASSWORD_VALIDATORS = []  # accept all passwords\n')

    # call "local_test/manage.py" via subprocess:
    call_manage_py(final_home_path, 'check --deploy')
    if runserver:
        call_manage_py(final_home_path, 'migrate --no-input')
        call_manage_py(final_home_path, 'collectstatic --no-input')

        verbose_check_call(
            command=(
                f'{sys.executable} -m django_ynh.create_superuser'
                f' --ds="{django_settings_name}" --username="test" --password="test123"'
            ),
            cwd=final_home_path,
        )

        os.environ['DJANGO_SETTINGS_MODULE'] = django_settings_name

        # All environment variables are passed to Django's "runnserver" ;)
        # "Simulate" SSOwat authentication, by set "http headers"
        # Still missing is the 'SSOwAuthUser' cookie,
        # but this is ignored, if settings.DEBUG=True ;)
        os.environ['HTTP_AUTH_USER'] = 'test'
        os.environ['HTTP_REMOTE_USER'] = 'test'

        os.environ['HTTP_AUTHORIZATION'] = generate_basic_auth(username='test', password='test123')

        try:
            call_manage_py(final_home_path, 'runserver --nostatic')
        except KeyboardInterrupt:
            print('\nBye ;)')

    return final_home_path


def cli():
    parser = argparse.ArgumentParser(description='Generate a YunoHost package local test')

    parser.add_argument(
        '--django_settings_path',
        action='store',
        metavar='path',
        help='Path to YunoHost package settings.py file (in "conf" directory)',
    )
    parser.add_argument(
        '--destination',
        action='store',
        metavar='path',
        help='Destination directory for the local test files',
    )
    parser.add_argument(
        '--runserver',
        action='store',
        type=bool,
        default=False,
        help='Start Django "runserver" after local test file creation?',
    )
    args = parser.parse_args()

    create_local_test(
        django_settings_path=Path(args.django_settings_path),
        destination=Path(args.destination),
        runserver=args.runserver,
    )


if __name__ == '__main__':
    cli()
