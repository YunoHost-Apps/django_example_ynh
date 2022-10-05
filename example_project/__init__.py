try:
    from importlib.metadata import version  # New in Python 3.8
except ImportError:
    from pkg_resources import get_distribution  # from setuptools, deprecated

    __version__ = get_distribution('django_example_ynh').version
else:
    __version__ = version('django_example_ynh')
