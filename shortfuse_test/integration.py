import logging
import os
import time
import traceback
from stat import S_IFREG, S_IFMT, S_IFDIR

from shortfuse_test.fixtures import build_random_string

TMP_DIR_PREFIX = "int_test_dir_"
TMP_FILE_PREFIX = "int_test_file_"
LOGGER = logging.getLogger("shortfuse_test.integration")


def failable_test(test_func):
    def test_wrapper(node_path, fuse_os, failure_expected=False, check_parent=False, **kwargs):
        LOGGER.debug("Gathering node stats for potential failure. Include parent = %s" % check_parent)
        parent_path = os.path.dirname(node_path)
        parent_stats = fuse_os.stat(parent_path) if check_parent else None
        node_stats = fuse_os.stat(node_path)
        try:
            test_func(node_path, fuse_os, node_stats=node_stats, **kwargs)
        except Exception as e:
            if failure_expected:
                # Test that the node was not affected in any way
                u_node_stats = fuse_os.stat(node_path)
                u_parent_stats = fuse_os.stat(parent_path)

                assert node_stats == u_node_stats
                if check_parent:
                    assert parent_stats == u_parent_stats

            traceback.print_exc()
            raise e
    return test_wrapper


def test_parent_stat_after_mod(stats, new_stats, diff=1):
    assert stats.st_nlink + diff == new_stats.st_nlink
    assert int(stats.st_atime) <= int(new_stats.st_atime)
    assert int(stats.st_mtime) <= int(new_stats.st_mtime)
    assert int(stats.st_ctime) == int(new_stats.st_ctime)


def test_chmod(node_path, fuse_os, noop=False):
    node_stats = fuse_os.stat(node_path)
    fuse_os.chmod(node_path, 0o111)
    if noop:
        assert node_stats == fuse_os.stat(node_path)
    else:
        test_stat(
            fuse_os.stat(node_path),
            mode=0o111 if not noop else (node_stats.st_mode & 0o777),
            nlink=node_stats.st_nlink,
            node_type=S_IFMT(node_stats.st_mode),
        )
    fuse_os.chmod(node_path, node_stats.st_mode & 0o777)


def test_chown(node_path, fuse_os, noop=False):
    node_stats = fuse_os.stat(node_path)
    fuse_os.chown(node_path, 100, 200)
    if noop:
        assert node_stats == fuse_os.stat(node_path)
    else:
        test_stat(
            fuse_os.stat(node_path),
            uid=100,
            gid=200,
            mode=node_stats.st_mode & 0o777,
            nlink=node_stats.st_nlink,
            node_type=S_IFMT(node_stats.st_mode),
        )
    fuse_os.chown(node_path, os.getuid(), os.getgid())


@failable_test
def test_create(dir_path, fuse_os, node_stats=None):
    parent_stats = node_stats
    file_name = TMP_FILE_PREFIX + build_random_string(10)
    file_path = os.path.join(dir_path, file_name)
    with open(file_path, 'w') as f:
        assert 0 <= f.fileno()

    test_stat(fuse_os.stat(file_path), mode=0o644)
    test_parent_stat_after_mod(parent_stats, fuse_os.stat(dir_path))
    assert file_name in fuse_os.listdir(dir_path)


@failable_test
def test_mkdir(dir_path, fuse_os, node_stats=None, mode=0o711, nlink=2):
    dir_stat = node_stats
    new_dir_name = TMP_DIR_PREFIX + build_random_string(10)
    new_dir_path = os.path.join(dir_path, new_dir_name)
    fuse_os.mkdir(new_dir_path, 0o711)
    test_stat(fuse_os.stat(new_dir_path), node_type=S_IFDIR, mode=mode, nlink=nlink)
    test_parent_stat_after_mod(dir_stat, fuse_os.stat(dir_path))
    assert new_dir_name in fuse_os.listdir(dir_path)


def test_read(file_path, fuse_os, file_content):
    with open(file_path, "r") as file_handle:
        assert file_content == file_handle.read()
        file_handle.seek(5)
        assert file_content[5:] == file_handle.read()
        file_handle.seek(5)
        assert file_content[5:35] == file_handle.read(30)
        assert file_content[35:] == file_handle.read()
        assert '' == file_handle.read()


@failable_test
def test_rmdir(dir_path, fuse_os, node_stats=None):
    dir_name = os.path.basename(dir_path)
    parent_path = os.path.dirname(dir_path)
    parent_stats = fuse_os.stat(parent_path)
    fuse_os.rmdir(dir_path)
    test_parent_stat_after_mod(parent_stats, fuse_os.stat(parent_path), diff=-1)
    assert dir_name not in fuse_os.listdir(parent_path)


def test_stat(
    stats,
    node_type=S_IFREG,
    mode=0o777,
    size=0,
    nlink=1,
    uid=os.getuid(),
    gid=os.getgid()
):
    assert node_type == S_IFMT(stats.st_mode)
    assert mode == (stats.st_mode & 0o777)
    assert uid == stats.st_uid
    assert gid == stats.st_gid
    assert nlink == stats.st_nlink
    if node_type is S_IFREG:
        assert size == stats.st_size


@failable_test
def test_symlink(dir_path, fuse_os, target, node_stats=None):
    link_name = build_random_string(10)
    link_path = os.path.join(dir_path, link_name)
    fuse_os.symlink(target, link_path)
    raise NotImplemented


def test_truncate(file_path, fuse_os):
    file_content = build_random_string(50)
    with open(file_path, "w+") as file_handle:
        file_handle.write(file_content)

    with open(file_path, "r+") as file_handle:
        file_handle.truncate(70)
        file_handle.seek(0)
        assert file_content + ('\0' * 20) == file_handle.read()
        test_stat(
            fuse_os.stat(file_handle.name),
            mode=0o644,
            node_type=S_IFREG,
            size=70
        )
        file_handle.truncate(20)
        file_handle.seek(0)
        assert file_content[0:20] == file_handle.read()
        test_stat(
            fuse_os.stat(file_handle.name),
            mode=0o644,
            node_type=S_IFREG,
            size=20
        )
        file_handle.truncate(0)
        file_handle.seek(0)
        assert '' == file_handle.read()
        test_stat(
            fuse_os.stat(file_handle.name),
            mode=0o644,
            node_type=S_IFREG,
            size=0
        )


@failable_test
def test_unlink(file_path, fuse_os, node_stats=None):
    file_name = os.path.basename(file_path)
    parent_path = os.path.dirname(file_path)
    parent_stats = fuse_os.stat(parent_path)
    fuse_os.unlink(file_path)
    test_parent_stat_after_mod(parent_stats, fuse_os.stat(parent_path), diff=-1)
    assert file_name not in fuse_os.listdir(parent_path)


def test_utime(node_path, times, fuse_os, noop=True):
    node_stats = fuse_os.stat(node_path)
    fuse_os.utime(node_path, times)
    if noop:
        assert node_stats == fuse_os.stat(node_path)
    else:
        raise NotImplemented


def test_write(file_path, fuse_os):
    with open(file_path, "w+") as file_handle:
        file_content = build_random_string(50)
        file_content_1 = build_random_string(50)

        file_handle.write(file_content)
        file_handle.seek(0)
        assert file_content == file_handle.read()
        test_stat(
            fuse_os.stat(file_handle.name),
            mode=0o644,
            node_type=S_IFREG,
            size=50
        )
        file_handle.seek(5)
        file_handle.write(file_content_1[5:15])
        file_handle.seek(0)
        assert (
            file_content[0:5] +
            file_content_1[5:15] +
            file_content[15:]
        ) == file_handle.read()
        test_stat(
            fuse_os.stat(file_handle.name),
            mode=0o644,
            node_type=S_IFREG,
            size=50
        )
        file_handle.seek(45)
        file_handle.write(file_content_1[40:])
        file_handle.seek(0)
        assert (
           file_content[0:5] +
           file_content_1[5:15] +
           file_content[15:45] +
           file_content_1[40:]
        ) == file_handle.read()
        test_stat(
            fuse_os.stat(file_handle.name),
            mode=0o644,
            node_type=S_IFREG,
            size=55
        )


def test_get_xattr(node_path, fuse_os, noop=False):
    node_stats = fuse_os.stat(node_path)
    key = build_random_string(10)
    assert None == fuse_os.get_xattr(node_path, key)
    value = build_random_string(10)
    fuse_os.set_xattr(node_path, key, value)
    assert node_stats == fuse_os.stat(node_path)
    if noop:
        assert None == fuse_os.get_xattr(node_path, key)
    else:
        assert value == fuse_os.get_xattr(node_path, key)


def test_get_xattrs(node_path, fuse_os, noop=False):
    node_stats = fuse_os.stat(node_path)
    key = build_random_string(10)
    assert node_stats == fuse_os.stat(node_path)
    attrs = fuse_os.get_xattrs(node_path)
    assert 0 <= len(attrs) # Might get some OS specific attributes like 'com.apple.FinderInfo'
    value = build_random_string(10)
    fuse_os.set_xattr(node_path, key, value)

    assert node_stats == fuse_os.stat(node_path)
    u_attrs = fuse_os.get_xattrs(node_path)
    if noop:
        assert len(attrs) == len(u_attrs)
        assert None == u_attrs.get(key)
    else:
        assert len(attrs) + 1 == len(u_attrs)
        assert value == u_attrs.get(key)


def test_set_xattr(node_path, fuse_os, noop=False):
    # We may want some more specialized tests in here but this is fine for a basic test
    test_get_xattr(node_path, fuse_os, noop)


def test_delete_xattr(node_path, fuse_os, noop=False):
    node_stats = fuse_os.stat(node_path)
    key = build_random_string(10)
    assert None == fuse_os.get_xattr(node_path, key)
    value = build_random_string(10)
    fuse_os.set_xattr(node_path, key, value)
    # This may not belong here
    if noop:
        assert None == fuse_os.get_xattr(node_path, key)
    else:
        assert value == fuse_os.get_xattr(node_path, key)
    fuse_os.delete_xattr(node_path, key)
    u_node_stats = fuse_os.stat(node_path)
    assert node_stats == u_node_stats
    assert None == fuse_os.get_xattr(node_path, key)
