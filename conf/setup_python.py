#!/usr/bin/env python3

"""
    DocWrite: setup_python.md # Boot Redistributable Python

    This is a standalone script (one file and no dependencies) to download and setup
    https://github.com/indygreg/python-build-standalone/ redistributable Python.
    But only if it's needed!
"""
from __future__ import annotations

import argparse
import dataclasses
import datetime
import hashlib
import json
import logging
import platform
import re
import shlex
import shutil
import ssl
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib import request


"""DocWrite: setup_python.md # Boot Redistributable Python
Minimal version to used this script is Python v3.9."""
assert sys.version_info >= (3, 9), f'Python version {sys.version_info} is too old!'


DEFAULT_MAJOR_VERSION = '3.12'
GUTHUB_PROJECT = 'indygreg/python-build-standalone'
LASTEST_RELEASE_URL = f'https://raw.githubusercontent.com/{GUTHUB_PROJECT}/latest-release/latest-release.json'
HASH_NAME = 'sha256'


OPTIMIZATION_PRIORITY = ['pgo+lto', 'pgo', 'lto']
TEMP_PREFIX = 'redist_python_'
DOWNLOAD_CHUNK_SIZE = 512 * 1024  # 512 KiB

logger = logging.getLogger(__name__)


def assert_is_dir(path):
    if not isinstance(path, Path):
        path = Path(path)

    if not path.is_dir():
        raise NotADirectoryError(f'Directory does not exists: "{path}"')


def assert_is_file(path):
    if not isinstance(path, Path):
        path = Path(path)

    assert_is_dir(path.parent)

    if not path.is_file():
        raise FileNotFoundError(f'File does not exists: "{path}"')


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


def urlopen(url: str):
    print(f'Fetching {url}', file=sys.stderr)
    """DocWrite: setup_python.md ## Workflow - 4. Download and verify Archive
    All downloads will be done with a secure connection (SSL) and server authentication."""
    context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
    return request.urlopen(url=url, context=context)


def fetch(url: str) -> bytes:
    return urlopen(url).read()


def fetch_json(url: str) -> dict:
    return json.loads(fetch(url))


def download(*, url: str, dst_path: Path, total_size: int, hash_name: str, hash_value: str) -> Path:
    """DocWrite: setup_python.md # Boot Redistributable Python
    The downloaded archive will be verified with the hash checksum.
    """
    filename = Path(url).name
    file_path = dst_path / filename
    logger.debug('Download %s into %s...', url, file_path)

    file_hash = hashlib.new(hash_name)
    response = urlopen(url)
    next_update = time.monotonic() + 1
    with file_path.open('wb') as f:
        while True:
            chunk = response.read(DOWNLOAD_CHUNK_SIZE)
            if not chunk:
                break
            f.write(chunk)
            file_hash.update(chunk)
            if time.monotonic() >= next_update:
                f.flush()
                percent = (file_path.stat().st_size / total_size) * 100
                print(
                    f'\rDownloaded {file_path.stat().st_size} Bytes ({percent:.1f}%)...',
                    file=sys.stderr,
                    end='',
                    flush=True,
                )
                next_update += 1

    file_size = file_path.stat().st_size
    print(f'\rDownloaded {file_size} Bytes (100%)', file=sys.stderr, flush=True)
    assert file_size == total_size, f'Downloaded {file_size=} Bytes is not expected {total_size=} Bytes!'

    file_hash = file_hash.hexdigest()
    logger.debug('Check %s hash...', file_hash)
    assert file_hash == hash_value, f'{file_hash=} != {hash_value=}'
    print(f'{hash_name} checksum verified: {file_hash!r}, ok.', file=sys.stderr)

    return file_path


def removesuffix(text: str, suffix: str) -> str:
    assert text.endswith(suffix), f'{text=} does not end with {suffix=}'
    return text[: -len(suffix)]


def run(args, **kwargs):
    logger.debug('Running: %s (%s)', shlex.join(str(arg) for arg in args), kwargs)
    return subprocess.run(args, **kwargs)


def verbose_check_output(args) -> str:
    completed_process = run(args, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return completed_process.stdout.strip()


def get_platform_parts():
    """DocWrite: setup_python.md ## Workflow - 3. Obtaining optimized Python distribution
    See: https://gregoryszorc.com/docs/python-build-standalone/main/running.html
    """
    parts = [sys.platform]
    abi = 'gnu' if any(platform.libc_ver()) else 'musl'
    logger.debug('Use %r ABI', abi)
    parts.append(abi)

    arch = platform.machine().lower()
    if sys.platform == 'linux' and arch == 'x86_64':
        """DocWrite: setup_python.md ## Workflow - 3. Obtaining optimized Python distribution
        For `x86-64` Linux we check the CPU flags from `/proc/cpuinfo` to determine the best variant."""
        try:
            contents = Path('/proc/cpuinfo').read_text()
        except OSError:
            pass
        else:
            # Based on https://github.com/pypa/hatch/blob/master/src/hatch/python/resolve.py
            # See https://clang.llvm.org/docs/UsersManual.html#x86 for the
            # instructions for each architecture variant and
            # https://github.com/torvalds/linux/blob/master/arch/x86/include/asm/cpufeatures.h
            # for the corresponding Linux flags
            v2_flags = {'cx16', 'lahf_lm', 'popcnt', 'pni', 'sse4_1', 'sse4_2', 'ssse3'}
            v3_flags = {'avx', 'avx2', 'bmi1', 'bmi2', 'f16c', 'fma', 'movbe', 'xsave'} | v2_flags
            v4_flags = {'avx512f', 'avx512bw', 'avx512cd', 'avx512dq', 'avx512vl'} | v3_flags

            cpu_flags = set()
            for line in contents.splitlines():
                key, _, value = line.partition(':')
                if key.strip() == 'flags':
                    cpu_flags |= set(value.strip().split())

            logger.debug('CPU flags: %s', ', '.join(sorted(cpu_flags)))

            missing_v4_flags = v4_flags - cpu_flags
            if not missing_v4_flags:
                arch = 'x86_64_v4'
            else:
                logger.debug('Missing v4 flags: %s', ', '.join(sorted(missing_v4_flags)))
                missing_v3_flags = v3_flags - cpu_flags
                if not missing_v3_flags:
                    arch = 'x86_64_v3'
                else:
                    logger.debug('Missing v3 flags: %s', ', '.join(sorted(missing_v3_flags)))
                    missing_v2_flags = v2_flags - cpu_flags
                    if not missing_v2_flags:
                        arch = 'x86_64_v2'
                    else:
                        logger.debug('Missing v2 flags: %s', ', '.join(sorted(missing_v2_flags)))

    logger.info('Use arch: %r', arch)
    parts.append(arch)
    return parts


def get_best_variant(names):
    """DocWrite: setup_python.md ## Workflow - 3. Obtaining optimized Python distribution
    We choose the optimized variant based on the priority list:
    DocWriteMacro: manageprojects.tests.docwrite_macros_setup_python.optimization_priority
    """
    for optimization in OPTIMIZATION_PRIORITY:
        for name in names:
            if optimization in name:
                return name
    logger.warning('No optimization found in names: %r', names)
    return sorted(names)[0]


def get_python_version(python_bin: str | Path) -> str | None:
    logger.debug('Check %s version', python_bin)
    if output := run([python_bin, '-V'], capture_output=True, text=True).stdout.split():
        full_version = output[-1]
        logger.info('Version of "%s" is: %r', python_bin, full_version)
        return full_version


def check_file_in_path(file_name: str):
    if not shutil.which(file_name):
        logger.error('Executable %r not found in PATH! (Hint: Add ~/.local/bin to PATH)', file_name)
    else:
        logger.info('Executable %r found in PATH, ok.', file_name)


@dataclasses.dataclass
class DownloadInfo:
    url: str
    size: int


def setup_python(
    *,
    major_version: str,
    delete_temp: bool = True,
    force_update: bool = False,
):
    """DocWrite: setup_python.md # Boot Redistributable Python
    The download will be only done, if the system Python is not the same major version as requested
    and if the local Python is not up-to-date.
    """
    logger.info('Requested major Python version: %s', major_version)

    final_file_name = f'python{major_version}'

    existing_version = None
    existing_python_bin = None
    """DocWrite: setup_python.md ## Workflow - 1. Check system Python
    If the system Python is the same major version as the required Python, we skip the download."""
    for try_version in (major_version, '3'):
        filename = f'python{try_version}'
        logger.debug('Checking %s...', filename)
        if python3bin := shutil.which(filename):
            if (full_version := get_python_version(python3bin)) and full_version.startswith(major_version):
                existing_version = full_version
                existing_python_bin = python3bin
                """DocWrite: setup_python.md ## Workflow - 1. Check system Python
                The script just returns the path to the system Python interpreter."""

                if 'local' in python3bin:
                    """DocWrite: setup_python.md ## Workflow - 1. Check system Python
                    A local installed interpreter (e.g. in "~/.local") will be auto updated."""
                    continue

                logger.info('System Python v%s already installed: Return path %r of it.', existing_version, python3bin)
                check_file_in_path(final_file_name)
                return Path(python3bin)
        else:
            logger.debug('%s not found, ok.', filename)

    local_bin_path = Path.home() / '.local' / 'bin' / final_file_name
    # Maybe ~/.local/bin/pythonX.XX is already installed, but ~/.local/bin/ is not in PATH:
    if not existing_python_bin and local_bin_path.is_file():
        if existing_version := get_python_version(local_bin_path):
            assert existing_version.startswith(
                major_version
            ), f'{existing_version=} does not start with {major_version=}'
            existing_python_bin = local_bin_path

    logger.debug('Existing Python version: %s', existing_version)

    """DocWrite: setup_python.md ## Workflow - 4. Download and verify Archive
    We check if we have "zstd" or "gzip" installed for decompression and prefer "zstd" over "gzip"."""
    if shutil.which('zstd'):
        logger.debug('zstd found, ok.')
        compress_program = 'zstd'
        compress_extension = 'zst'
    elif shutil.which('gzip'):
        logger.debug('gzip found, ok.')
        compress_program = 'gzip'
        compress_extension = 'gz'
    else:
        raise FileNotFoundError('"zstd" or "gzip" compress program not found!')

    archive_extension = f'.tar.{compress_extension}'
    archive_hash_extension = f'.tar.{compress_extension}.{HASH_NAME}'

    filters = [archive_extension, *get_platform_parts()]
    logger.debug('Use filters: %s', filters)

    """DocWrite: setup_python.md ## Workflow - 2. Collect latest release data
    We fetch the latest release data from the GitHub API:
    DocWriteMacro: manageprojects.tests.docwrite_macros_setup_python.lastest_release_url"""
    data = fetch_json(LASTEST_RELEASE_URL)
    logger.debug('Latest release data: %r', data)
    tag = data['tag']
    release_url = f'https://api.github.com/repos/{GUTHUB_PROJECT}/releases/tags/{tag}'
    release_data = fetch_json(release_url)
    assets = release_data['assets']

    archive_infos = {}
    hash_urls = {}

    for asset in assets:
        full_name = asset['name']
        if '-debug-' in full_name:
            """DocWrite: setup_python.md ## Workflow - 3. Obtaining optimized Python distribution
            The "debug" build are ignored."""
            continue

        if not full_name.startswith(f'cpython-{major_version}.'):
            # Ignore all other major versions
            continue

        if not all(f in full_name for f in filters):
            # Ignore incompatible assets
            continue

        if full_name.endswith(archive_extension):
            name = removesuffix(full_name, archive_extension)
            archive_infos[name] = DownloadInfo(url=asset['browser_download_url'], size=asset['size'])
        elif full_name.endswith(archive_hash_extension):
            name = removesuffix(full_name, archive_hash_extension)
            hash_urls[name] = asset['browser_download_url']

    assert archive_infos, f'No "{archive_extension}" found in {assets=}'
    assert hash_urls, f'No "{archive_hash_extension}" found in {assets=}'

    assert archive_infos.keys() == hash_urls.keys(), f'{archive_infos.keys()=} != {hash_urls.keys()=}'

    best_variant = get_best_variant(archive_infos.keys())
    logger.debug('Use best variant: %r', best_variant)

    """DocWrite: setup_python.md ## Workflow - 4. Check existing Python
    If the latest Python version is already installed, we skip the download."""
    if existing_python_bin and existing_version:
        # full_name e.g.: cpython-3.13.0rc2+20240909-x86_64_v3-unknown-linux-gnu-pgo-full.tar.zst
        # get full version: 3.13.0rc2
        if match := re.search(r'cpython-(.+?)\+', best_variant):
            full_version = match.group(1)
            logger.debug('Available Python version: %s', full_version)
            if full_version == existing_version:
                logger.info(
                    'Local Python v%s is up-to-date: Return path %r of it.', existing_version, existing_python_bin
                )
                if force_update:
                    logger.info('Force update requested: Continue with download ...')
                else:
                    check_file_in_path(final_file_name)
                    return Path(existing_python_bin)
        else:
            logger.warning('No version found in %r', best_variant)

    local_path = Path.home() / '.local'
    logger.debug('Check "%s" directory', local_path)
    local_path.mkdir(parents=False, exist_ok=True)

    """DocWrite: setup_python.md ## Workflow - 4. Download and verify Archive
    If the latest Python version is already installed, we skip the download."""
    archive_info: DownloadInfo = archive_infos[best_variant]
    logger.debug('Archive info: %s', archive_info)

    hash_url: str = hash_urls[best_variant]
    logger.debug('Hash URL: %s', hash_url)

    # Download checksum file:
    hash_value = fetch(hash_url).decode().strip()
    logger.debug('%s hash value: %s', HASH_NAME, hash_value)

    """DocWrite: setup_python.md ## Workflow - 4. Download and verify Archive
    Download will be done in a temporary directory."""
    with TemporaryDirectory(prefix=TEMP_PREFIX, delete=delete_temp) as temp_path:
        """DocWrite: setup_python.md ## Workflow - 4. Download and verify Archive
        We check the file hash after downloading the archive."""
        archive_temp_path = download(
            url=archive_info.url,
            dst_path=temp_path,
            total_size=archive_info.size,
            hash_name=HASH_NAME,
            hash_value=hash_value,
        )

        # Extract .tar.zstd archive file into temporary directory:
        logger.debug('Extract %s into %s ...', archive_temp_path, temp_path)
        run(
            [
                'tar',
                f'--use-compress-program={compress_program}',
                '--extract',
                '--file',
                archive_temp_path,
                '--directory',
                temp_path,
            ],
            check=True,
        )

        src_path = temp_path / 'python'
        assert_is_dir(src_path)

        """DocWrite: setup_python.md ## Workflow - 6. Setup Python
        There exists two different directory structures:

        * `./python/install/bin/python3`
        * `./python/bin/python3`

        We handle both cases and move all contents to the final destination.
        """
        has_install_dir = (src_path / 'install').is_dir()
        if has_install_dir:
            temp_python_path = src_path / 'install' / 'bin' / 'python3'
        else:
            temp_python_path = src_path / 'bin' / 'python3'
        assert_is_file(temp_python_path)

        python_version_info = verbose_check_output([str(temp_python_path), '-VV']).strip()
        pip_version_into = verbose_check_output([str(temp_python_path), '-m', 'pip', '-VV']).strip()

        """DocWrite: setup_python.md ## Workflow - 5. Add info JSON
        We add the file `info.json` with all relevant information."""
        info_file_path = src_path / 'info.json'
        info = dict(
            download_by=__file__,
            download_dt=datetime.datetime.now().isoformat(),
            download_filters=filters,
            major_version=major_version,
            tag=tag,
            archive_url=archive_info.url,
            hash_url=hash_url,
            archive_hash_name=HASH_NAME,
            archive_hash_value=hash_value,
            python_version_info=python_version_info,
            pip_version_info=pip_version_into,
        )
        info_file_path.write_text(json.dumps(info, indent=4, ensure_ascii=False))

        """DocWrite: setup_python.md ## Workflow - 6. Setup Python
        The extracted Python will be moved to the final destination in `~/.local/pythonX.XX/`."""
        dest_path = Path.home() / '.local' / final_file_name
        logger.debug('Move %s to %s ...', src_path, dest_path)
        if dest_path.exists():
            logger.info('Remove existing %r ...', dest_path)
            shutil.rmtree(dest_path)
        shutil.move(src_path, dest_path)

    if has_install_dir:
        python_home_path = dest_path / 'install'
    else:
        python_home_path = dest_path

    """DocWrite: setup_python.md ## Workflow - 6. Setup Python
    We add a shell script to `~/.local/bin/pythonX.XX` to start the Python interpreter."""
    bin_path = python_home_path / 'bin' / final_file_name
    assert_is_file(bin_path)

    logger.debug('Create %s ...', local_bin_path)
    local_bin_path.parent.mkdir(parents=True, exist_ok=True)
    with local_bin_path.open('w') as f:
        """DocWrite: setup_python.md ## Workflow - 6. Setup Python
        The script set's the correct `PYTHONHOME` environment variable."""
        f.writelines(
            [
                '#!/bin/sh\n',
                f'export PYTHONHOME="{python_home_path}"\n',
                f'exec "{bin_path}" "$@"\n',
            ]
        )
    local_bin_path.chmod(0o777)

    """DocWrite: setup_python.md ## Workflow - 6. Setup Python
    We display version information from Python and pip on `stderr`."""
    print('Installed Python:', verbose_check_output([str(local_bin_path), '-VV']), file=sys.stderr)
    print('Pip info:', verbose_check_output([str(local_bin_path), '-m', 'pip', '-VV']), file=sys.stderr)

    logger.info('Python v%s installed: Return path %r of it.', major_version, local_bin_path)
    check_file_in_path(final_file_name)
    return local_bin_path


def get_parser() -> argparse.ArgumentParser:
    """
    DocWrite: setup_python.md ## CLI
    The CLI interface looks like e.g.:

    DocWriteMacro: manageprojects.tests.docwrite_macros_setup_python.help
    """
    parser = argparse.ArgumentParser(
        description=(
            'Download and setup redistributable Python Interpreter'
            f' from https://github.com/{GUTHUB_PROJECT}/ if needed ;)'
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        'major_version',
        nargs=argparse.OPTIONAL,
        default=DEFAULT_MAJOR_VERSION,
        help='Specify the Python version like: 3.10, 3.11, 3.12, ...',
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
        '--force-update',
        action='store_true',
        help='Update local Python interpreter, even if it is up-to-date',
    )
    return parser


def main(args=None):
    parser = get_parser()
    args = parser.parse_args(args=args)
    verbose2level = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}
    logging.basicConfig(
        level=verbose2level.get(args.verbose, logging.DEBUG),
        format='%(levelname)9s %(message)s',
        stream=sys.stderr,
    )
    logger.debug('Arguments: %s', args)

    return setup_python(
        major_version=args.major_version,
        delete_temp=not args.skip_temp_deletion,
        force_update=args.force_update,
    )


if __name__ == '__main__':
    python_path = main()

    """DocWrite: setup_python.md ## Workflow - 7. print the path
    If no errors occurred, the path to the Python interpreter will be printed to `stdout`.
    So it's usable in shell scripts, like:

    DocWriteMacro: manageprojects.tests.docwrite_macros_setup_python.example_shell_script
    """
    print(python_path)
