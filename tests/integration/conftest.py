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
    yield dir_path
    if os.path.isdir(dir_path):
        shutil.rmtree(dir_path)


def pytest_addoption(parser):
    parser.addoption("--uid", type=int, default=None, help="User ID for tests changing file permissions.")
    parser.addoption("--gid", type=int, default=None, help="Group ID for tests changing file permissions.")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--uid") is None or config.getoption("--gid") is None:
        skip_uid_gid = pytest.mark.skip(reason="Need to provide a --uid and --gid to test changing ownership.")
        for item in items:
            if "usergroup" in item.keywords:
                item.add_marker(skip_uid_gid)


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


@pytest.fixture
def fuse_uid(request):
    return request.config.getoption("--uid")


@pytest.fixture
def fuse_gid(request):
    return request.config.getoption("--gid")
