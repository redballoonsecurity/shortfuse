import pytest

from shortfuse_test.concurrency import create_delete_file_test, create_file_test, create_delete_dir_test


@pytest.mark.usefixtures("fuse")
class TestMemoryFSConcurrency:

    def test_create_delete_file(self, temp_dir_module):
        create_delete_file_test(temp_dir_module)

    def test_create_file(self, temp_dir_module):
        create_file_test(temp_dir_module)

    def test_create_delete_dir(self, temp_dir_module):
        create_delete_dir_test(temp_dir_module)
