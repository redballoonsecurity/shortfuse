import os
from stat import S_ISDIR

import pytest

from shortfuse_test.integration import test_create, test_chmod, test_chown, test_unlink, test_mkdir, test_rmdir, \
    test_write, test_read, test_truncate


@pytest.mark.usefixtures("fuse")
class TestMemoryFS:
    def test_fs_attributes(self, temp_dir_module):
        root_stats = os.stat(temp_dir_module)
        assert S_ISDIR(root_stats.st_mode)
        assert 0o777 == (root_stats.st_mode & 0o777)
        assert os.getuid() == root_stats.st_uid
        assert os.getgid() == root_stats.st_gid
        assert 2 <= root_stats.st_nlink

    def test_create(self, fuse_dir, fuse_os):
        test_create(fuse_dir, fuse_os)

    def test_chmod_dir(self, fuse_dir, fuse_os):
        test_chmod(fuse_dir, fuse_os)

    def test_chmod_file(self, fuse_file, fuse_os):
        test_chmod(fuse_file, fuse_os)

    def test_chown_dir(self, fuse_dir, fuse_os):
        test_chown(fuse_dir, fuse_os)

    def test_chown_file(self, fuse_file, fuse_os):
        test_chown(fuse_file, fuse_os)

    def test_mkdir_in_dir(self, fuse_dir, fuse_os):
        test_mkdir(fuse_dir, fuse_os)

    def test_mkdir_in_file(self, fuse_file, fuse_os):
        with pytest.raises(OSError):
            test_mkdir(fuse_file, fuse_os)

    def test_read(self, fuse_file_path, fuse_os):
        test_read(fuse_file_path, fuse_os)

    def test_rmdir_dir(self, fuse_dir, fuse_os):
        if fuse_dir.endswith('./'):
            with pytest.raises(OSError):
                test_rmdir(fuse_dir, fuse_os)
        else:
            test_rmdir(fuse_dir, fuse_os)

    def test_rmdir_file(self, fuse_file, fuse_os):
        with pytest.raises(OSError):
            test_rmdir(fuse_file, fuse_os)

    def test_truncate(self, fuse_file_path, fuse_os):
        test_truncate(fuse_file_path, fuse_os)

    def test_unlink_in_dir(self, fuse_dir, fuse_os):
        with pytest.raises(OSError):
            test_unlink(fuse_dir, fuse_os)

    def test_unlink_in_file(self, fuse_file, fuse_os):
        test_unlink(fuse_file, fuse_os)

    def test_write(self, fuse_file_path, fuse_os):
        test_write(fuse_file_path, fuse_os)
