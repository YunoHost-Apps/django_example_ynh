"""
    https://github.com/jedie/manageprojects/blob/main/docs/setup_python.md#include-in-own-projects
"""

from django_yunohost_integration.path_utils import get_project_root
from manageprojects.utilities.include_setup_python import IncludeSetupPythonBaseTestCase


class IncludeSetupPythonTestCase(IncludeSetupPythonBaseTestCase):
    """
    Updates `conf/setup_python.py` from `manageprojects` if needed.
    """

    DESTINATION_PATH = get_project_root() / 'conf' / 'setup_python.py'

    def test_setup_python_is_up2date(self):
        self.auto_update_setup_python()
