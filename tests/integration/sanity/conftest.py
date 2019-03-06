import os
import shutil

import pytest


@pytest.fixture(scope="module")
def fuse(temp_dir_module):
    os.chmod(temp_dir_module, 0o777)
    yield temp_dir_module
    shutil.rmtree(temp_dir_module)
