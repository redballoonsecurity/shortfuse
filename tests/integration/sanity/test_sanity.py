import logging
import os
from stat import S_ISDIR

import pytest

from shortfuse_test.integration import create_test, chmod_test, chown_test, mkdir_test, read_test, rmdir_test, \
    unlink_test, truncate_test, write_test

logging.basicConfig(level=logging.DEBUG)


@pytest.mark.usefixtures("fuse")
class TestFS:
    def test_fs_attributes(self, temp_dir_module):
        root_stats = os.stat(temp_dir_module)
        assert S_ISDIR(root_stats.st_mode)
        assert 0o777 == (root_stats.st_mode & 0o777)
        assert os.getuid() == root_stats.st_uid
        assert os.getgid() == root_stats.st_gid
        assert 2 <= root_stats.st_nlink

    def test_create(self, fuse_dir, fuse_os):
        create_test(fuse_dir, fuse_os)

    def test_chmod_dir(self, fuse_dir, fuse_os):
        chmod_test(fuse_dir, fuse_os)

    def test_chmod_file(self, fuse_file, fuse_os):
        chmod_test(fuse_file, fuse_os)

    @pytest.mark.usergroup
    def test_chown_dir(self, fuse_dir, fuse_os, fuse_uid, fuse_gid):
        chown_test(fuse_dir, fuse_os, fuse_uid, fuse_gid)

    @pytest.mark.usergroup
    def test_chown_file(self, fuse_file, fuse_os, fuse_uid, fuse_gid):
        chown_test(fuse_file, fuse_os, fuse_uid, fuse_gid)

    def test_mkdir_in_dir(self, fuse_dir, fuse_os):
        mkdir_test(fuse_dir, fuse_os)

    def test_mkdir_in_file(self, fuse_file, fuse_os):
        with pytest.raises(OSError):
            mkdir_test(fuse_file, fuse_os)

    def test_read(self, fuse_file, fuse_os):
        read_test(fuse_file, fuse_os, "")

    def test_rmdir_dir(self, fuse_dir, fuse_os):
        if fuse_dir.endswith('./'):
            with pytest.raises(OSError):
                rmdir_test(fuse_dir, fuse_os)
        else:
            rmdir_test(fuse_dir, fuse_os)

    def test_rmdir_file(self, fuse_file, fuse_os):
        with pytest.raises(OSError):
            rmdir_test(fuse_file, fuse_os)

    def test_truncate(self, fuse_file_path, fuse_os):
        truncate_test(fuse_file_path, fuse_os)

    def test_unlink_in_dir(self, fuse_dir, fuse_os):
        with pytest.raises(OSError):
            unlink_test(fuse_dir, fuse_os)

    def test_unlink_in_file(self, fuse_file, fuse_os):
        unlink_test(fuse_file, fuse_os)

    def test_write(self, fuse_file_path, fuse_os):
        write_test(fuse_file_path, fuse_os)
