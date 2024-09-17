#!/usr/bin/env python3

"""
    DocWrite: install_python.md # Install Python Interpreter

    `install_python.py` downloads, builds and installs a Python interpreter, but:
    - **only** if the system Python is not the required major version
    - **only** once (if the required major version is not already build and installed)

    Origin of this script is:
    * https://github.com/jedie/manageprojects/blob/main/manageprojects/install_python.py

    Licensed under GPL-3.0-or-later (Feel free to copy and use it in your project)
"""
from __future__ import annotations

import argparse
import hashlib
import logging
import os
import re
import shlex
import shutil
import ssl
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path


"""DocWrite: install_python.md # Install Python Interpreter
Minimal needed Python version to run the script is: **v3.9**."""
assert sys.version_info >= (3, 9), f'Python version {sys.version_info} is too old!'


DEFAULT_MAJOR_VERSION = '3.11'

"""DocWrite: install_python.md # Install Python Interpreter
Download Python source code from official Python FTP server:
DocWriteMacro: manageprojects.tests.docwrite_macros_install_python.ftp_url"""
PY_FTP_INDEX_URL = 'https://www.python.org/ftp/python/'

"""DocWrite: install_python.md ## Supported Python Versions
The following major Python versions are supported and verified with GPG keys:
DocWriteMacro: manageprojects.tests.docwrite_macros_install_python.supported_python_versions
The GPG keys taken from the official Python download page: https://www.python.org/downloads/"""
GPG_KEY_IDS = {
    # Thomas Wouters (3.12.x and 3.13.x source files and tags):
    '3.13': 'A821E680E5FA6305',
    '3.12': 'A821E680E5FA6305',
    #
    # Pablo Galindo Salgado (3.10.x and 3.11.x source files and tags):
    '3.11': '64E628F8D684696D',
    '3.10': '64E628F8D684696D',
}
GPG_KEY_SERVER = 'hkps://keys.openpgp.org'

"""DocWrite: install_python.md ## Workflow - 3. Check local installed Python
We assume that the `make altinstall` will install local Python interpreter into:
DocWriteMacro: manageprojects.tests.docwrite_macros_install_python.default_install_prefix
See: https://docs.python.org/3/using/configure.html#cmdoption-prefix"""
DEFAULT_INSTALL_PREFIX = '/usr/local'

TEMP_PREFIX = 'setup_python_'

logger = logging.getLogger(__name__)


class TemporaryDirectory:
    """tempfile.TemporaryDirectory in Python 3.9 has no "delete", yet."""

    def __init__(self, prefix, delete: bool):
        self.prefix = prefix
        self.delete = delete

    def __enter__(self) -> Path:
        self.temp_path = Path(tempfile.mkdtemp(prefix=self.prefix))
        return self.temp_path

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.delete:
            shutil.rmtree(self.temp_path, ignore_errors=True)
        if exc_type:
            return False


def fetch(url: str) -> bytes:
    """DocWrite: install_python.md # Install Python Interpreter
    Download only over verified HTTPS connection."""
    context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
    with urllib.request.urlopen(url=url, context=context) as response:
        return response.read()


def get_html_page(url) -> str:
    logger.debug('Getting HTML page from %s', url)
    html = fetch(url).decode('utf-8')
    assert html, 'Failed to get Python FTP index page'
    return html


def extract_versions(*, html, major_version) -> list[str]:
    pattern = rf'href="({re.escape(major_version)}\.[0-9]+)'
    logger.debug('Extracting versions with pattern: %s', pattern)
    versions = re.findall(pattern, html)
    versions.sort(reverse=True)
    logger.debug('Extracted versions: %s', versions)
    return versions


def get_latest_versions(*, html, major_version) -> str:
    latest_versions = extract_versions(html=html, major_version=major_version)[0]
    logger.info('Latest version of Python %s: %s', major_version, latest_versions)
    return latest_versions


def run(args, **kwargs):
    logger.debug('Running: %s (%s)', shlex.join(str(arg) for arg in args), kwargs)
    return subprocess.run(args, **kwargs)


def run_build_step(args, *, step: str, cwd: Path) -> None:
    with tempfile.NamedTemporaryFile(prefix=f'{TEMP_PREFIX}_{step}_', suffix='.txt', delete=False) as temp_file:
        logger.info('Running: %s... Output in %s', shlex.join(str(arg) for arg in args), temp_file.name)
        try:
            subprocess.run(args, stdout=temp_file, stderr=temp_file, check=True, cwd=cwd)
        except subprocess.SubprocessError as err:
            logger.error('Failed to run %s step: %s', step, err)
            run(['tail', temp_file.name])
            raise


def get_python_version(python_bin: str | Path) -> str | None:
    logger.debug('Check %s version', python_bin)
    if output := run([python_bin, '-V'], capture_output=True, text=True).stdout.split():
        full_version = output[-1]
        logger.info('Version of "%s" is: %r', python_bin, full_version)
        return full_version


def download2temp(*, temp_path: Path, base_url: str, filename: str) -> Path:
    url = f'{base_url}/{filename}'
    dst_path = temp_path / filename
    logger.info('Downloading %s into %s...', url, dst_path)
    dst_path.write_bytes(fetch(url))
    logger.info('Downloaded %s is %d Bytes', filename, dst_path.stat().st_size)
    return dst_path


def verify_download(*, major_version: str, tar_file_path: Path, asc_file_path: Path, delete_temp: bool):
    """DocWrite: install_python.md ## Workflow - 5. Verify download
    The sha256 hash downloaded tar archive will logged.
    If `gpg` is available, the signature will be verified.
    """
    hash_obj = hashlib.sha256(tar_file_path.read_bytes())
    logger.info('Downloaded sha256: %s', hash_obj.hexdigest())

    """DocWrite: install_python.md # Install Python Interpreter
    The Downloaded tar archive will be verified with the GPG signature, if `gpg` is available."""
    if gpg_bin := shutil.which('gpg'):
        logger.debug('Verifying signature with %s...', gpg_bin)
        assert major_version in GPG_KEY_IDS, f'No GPG key ID for Python {major_version}'
        gpg_key_id = GPG_KEY_IDS[major_version]
        with TemporaryDirectory(prefix='install-python-gpg-', delete=delete_temp) as temp_path:
            """DocWrite: install_python.md ## Workflow - 5. Verify download
            We set the `GNUPGHOME` environment variable to a temporary directory."""
            env = {'GNUPGHOME': str(temp_path)}
            run([gpg_bin, '--keyserver', GPG_KEY_SERVER, '--recv-keys', gpg_key_id], check=True, env=env)
            run([gpg_bin, '--verify', asc_file_path, tar_file_path], check=True, env=env)
            run(['gpgconf', '--kill', 'all'], check=True, env=env)
    else:
        logger.warning('No GPG verification possible! (gpg not found)')


def install_python(
    major_version: str,
    *,
    write_check: bool = True,
    delete_temp: bool = True,
) -> Path:
    logger.info('Requested major Python version: %s', major_version)

    """DocWrite: install_python.md ## Workflow
    The setup process is as follows:"""

    """DocWrite: install_python.md ## Workflow - 1. Check system Python
    If the system Python is the same major version as the required Python, we skip the installation."""
    for try_version in (major_version, '3'):
        filename = f'python{try_version}'
        logger.debug('Checking %s...', filename)
        if python3bin := shutil.which(filename):
            if (full_version := get_python_version(python3bin)) and full_version.startswith(major_version):
                logger.info('Python version already installed: Return path %r of it.', python3bin)
                """DocWrite: install_python.md ## Workflow - 1. Check system Python
                The script just returns the path to the system Python interpreter."""
                return Path(python3bin)

    """DocWrite: install_python.md ## Workflow - 2. Get latest Python release
    We fetch the latest Python release from the Python FTP server, from:
    DocWriteMacro: manageprojects.tests.docwrite_macros_install_python.ftp_url"""
    # Get latest full version number of Python from Python FTP:
    py_required_version = get_latest_versions(
        html=get_html_page(PY_FTP_INDEX_URL),
        major_version=major_version,
    )

    local_bin_path = Path(DEFAULT_INSTALL_PREFIX) / 'bin'

    """DocWrite: install_python.md ## Workflow - 3. Check local installed Python
    The script checks if the latest release already build and installed."""
    local_python_path = local_bin_path / f'python{major_version}'
    if local_python_path.exists() and get_python_version(local_python_path) == py_required_version:
        logger.info('Local Python is up-to-date')
        """DocWrite: install_python.md ## Workflow - 3. Check local installed Python
        If the local Python is up-to-date, the script exist and returns the path this local interpreter."""
        return local_python_path

    """DocWrite: install_python.md ## Workflow - 4. Download Python sources
    Before we start building Python, check if we have write permissions.
    The check can be skipped via CLI argument."""
    if write_check and not os.access(local_bin_path, os.W_OK):
        raise PermissionError(f'No write permission to {local_bin_path} (Hint: Call with "sudo" ?!)')

    """DocWrite: install_python.md ## Workflow - 4. Download Python sources
    The download will be done in a temporary directory. The directory will be deleted after the installation.
    This can be skipped via CLI argument. The directory will be prefixed with:
    DocWriteMacro: manageprojects.tests.docwrite_macros_install_python.temp_prefix"""
    with TemporaryDirectory(prefix=TEMP_PREFIX, delete=delete_temp) as temp_path:
        base_url = f'{PY_FTP_INDEX_URL}{py_required_version}'

        tar_filename = f'Python-{py_required_version}.tar.xz'
        asc_filename = f'{tar_filename}.asc'
        asc_file_path = download2temp(
            temp_path=temp_path,
            base_url=base_url,
            filename=asc_filename,
        )
        tar_file_path = download2temp(
            temp_path=temp_path,
            base_url=base_url,
            filename=tar_filename,
        )
        verify_download(
            major_version=major_version,
            tar_file_path=tar_file_path,
            asc_file_path=asc_file_path,
            delete_temp=delete_temp,
        )

        tar_bin = shutil.which('tar')
        logger.debug('Extracting %s with ...', tar_file_path)
        run([tar_bin, 'xf', tar_file_path], check=True, cwd=temp_path)
        extracted_dir = temp_path / f'Python-{py_required_version}'

        logger.info('Building Python %s (may take a while)...', py_required_version)

        """DocWrite: install_python.md ## Workflow - 6. Build and install Python
        If the verify passed, the script will start the build process."""
        run_build_step(
            ['./configure', '--enable-optimizations'],
            step='configure',
            cwd=extracted_dir,
        )
        run_build_step(
            ['make', f'-j{os.cpu_count()}'],
            step='make',
            cwd=extracted_dir,
        )

        """DocWrite: install_python.md ## Workflow - 6. Build and install Python
        The installation will be done with `make altinstall`."""
        run_build_step(
            ['make', 'altinstall'],
            step='install',
            cwd=extracted_dir,
        )

    logger.info('Python %s installed to %s', py_required_version, local_python_path)

    local_python_version = get_python_version(local_python_path)
    assert local_python_version == py_required_version, f'{local_python_version} is not {py_required_version}'

    return local_python_path


def get_parser() -> argparse.ArgumentParser:
    """
    DocWrite: install_python.md ## CLI
    The CLI interface looks like e.g.:
    ```shell
    $ python3 install_python.py --help

    DocWriteMacro: manageprojects.tests.docwrite_macros_install_python.help
    ```
    """
    parser = argparse.ArgumentParser(
        description='Install Python Interpreter',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        'major_version',
        nargs=argparse.OPTIONAL,
        default=DEFAULT_MAJOR_VERSION,
        choices=sorted(GPG_KEY_IDS.keys()),
        help='Specify the Python version',
    )
    parser.add_argument(
        '-v',
        '--verbose',
        action='count',
        default=0,
        help='Increase verbosity level (can be used multiple times, e.g.: -vv)',
    )
    parser.add_argument(
        '--skip-temp-deletion',
        action='store_true',
        help='Skip deletion of temporary files',
    )
    parser.add_argument(
        '--skip-write-check',
        action='store_true',
        help='Skip the test for write permission to /usr/local/bin',
    )
    return parser


def main() -> Path:
    parser = get_parser()
    args = parser.parse_args()
    verbose2level = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}
    logging.basicConfig(
        level=verbose2level.get(args.verbose, logging.DEBUG),
        format='%(levelname)9s %(message)s',
        stream=sys.stderr,
    )
    logger.debug('Arguments: %s', args)
    return install_python(
        major_version=args.major_version,
        write_check=not args.skip_write_check,
        delete_temp=not args.skip_temp_deletion,
    )


if __name__ == '__main__':
    python_path = main()

    """DocWrite: install_python.md ## Workflow - 7. print the path
    If no errors occurred, the path to the Python interpreter will be printed to `stdout`.
    So it's usable in shell scripts, like:
    DocWriteMacro: manageprojects.tests.docwrite_macros_install_python.example_shell_script
    """
    print(python_path)
