import pytest

from shortfuse_test.concurrency import test_create_delete_file, test_create_file, test_create_delete_dir


@pytest.mark.usefixtures("fuse")
class TestMemoryFSConcurrency:
    def test_create_delete_file(self, temp_dir_module):
        test_create_delete_file(temp_dir_module)

    def test_create_file(self, temp_dir_module):
        test_create_file(temp_dir_module)

    def test_create_delete_dir(self, temp_dir_module):
        test_create_delete_dir(temp_dir_module)
