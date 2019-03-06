import os
import shutil

import pytest

from shortfuse_test.fixtures import build_random_string
from shortfuse_test.mount import FuseOS

pytest_plugins = "shortfuse_test.fixtures",


@pytest.fixture(scope="module")
def fuse_os():
    return FuseOS()


@pytest.fixture(params=["./", "./deep/path"])
def fuse_dir(temp_dir_module, request):
    if request.param == "./":
        yield os.path.join(temp_dir_module, request.param)
        return
    dir_path = os.path.join(temp_dir_module, request.param, build_random_string(10))
    os.makedirs(dir_path)
    yield  dir_path
    if os.path.isdir(dir_path):
        shutil.rmtree(dir_path)


@pytest.fixture
def fuse_file_path(fuse_dir):
    return os.path.join(fuse_dir, build_random_string(10))


@pytest.fixture
def fuse_file(fuse_file_path):
    with open(fuse_file_path, 'w'):
        pass
    yield fuse_file_path
    if os.path.isfile(fuse_file_path):
        os.unlink(fuse_file_path)


@pytest.fixture
def fuse_file_handle(fuse_dir):
    file_path = os.path.join(fuse_dir, build_random_string(10))
    with open(file_path, 'w+') as f:
        yield f
    if os.path.isfile(file_path):
        os.unlink(file_path)