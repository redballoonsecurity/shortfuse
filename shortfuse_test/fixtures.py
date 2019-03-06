import random
import string
import tempfile

import pytest


def build_random_string(length):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))


@pytest.fixture
def random_string(length):
    return build_random_string(length)


@pytest.fixture(scope="module")
def temp_dir_module():
    return tempfile.mkdtemp(prefix="shortfuse")


@pytest.fixture
def temp_file(file_path):
    file_content = build_random_string(50)
    with open(file_path, "w+") as file_handle:
        file_handle.write(file_content)