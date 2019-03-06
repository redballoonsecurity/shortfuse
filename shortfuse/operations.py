import logging
import os
from errno import ENOSYS, ENOTDIR
from fuse import LoggingMixIn, Operations, FuseOSError, EISDIR
from shortfuse.node import LinkNode, DirectoryNode, FileNode

LOGGER = logging.getLogger("shortfuse.operation")


def exception_logger(meth):
    def exception_logger_wrapper(*args, **kwargs):
        try:
            return meth(*args, **kwargs)
        except Exception as e:
            LOGGER.debug("Failed to handle '%s' with args %s, %s" % (meth.__name__, args[1:], kwargs), exc_info=True)
            raise e

    return exception_logger_wrapper


class Shortfuse(LoggingMixIn, Operations):
    """
    Implementation of the FUSE Operations class. It receives commands from the OS and feed them to the
    shortfuse nodes.

    Args:
        root (FileSystemDecorator): The root for the filesystem
    """

    def __init__(self, root):
        self.fd = 0
        self.root = root

    @exception_logger
    def access(self, path, amode):
        """
        Check that the caller has access to the requested node.

        Args:
            path (str): The path to the node
            amode (int): The requested access mode. More details can be found at the
                `manual <http://man7.org/linux/man-pages/man2/access.2.html>`_ page

        Returns:
            int: 0 If the caller has access to the required node.
        """
        return self.root.get_child(path).has_access(amode)

    @exception_logger
    def chmod(self, path, mode):
        """
        Change the file mode bits of the given node. See the `manual <https://linux.die.net/man/1/chmod>`_ page for
        more detailed explanations.

        Args:
            path (str): The path to the node.
            mode (int): An octal number representing the bit pattern for the new mode bits.

        Returns:
            int: 0 if the operation succeeded, negative otherwise

        """
        self.root.get_child(path)\
            .get_attributes()\
            .set_permissions(mode)
        return 0

    @exception_logger
    def chown(self, path, uid, gid):
        """
        Change the owner and group of the given node. See the `manual <https://linux.die.net/man/1/chown>`_ page for
        more detailed explanations.

        Args:
            path (str): The path to the node.
            uid (int): The id of the user that should own the file.
            gid (int): The id of the group that should own the file.

        Returns:
            int: 0 if the operation succeeded, negative otherwise
        """
        self.root.get_child(path)\
            .get_attributes()\
            .set_uid(uid)\
            .set_gid(gid)
        return 0

    @exception_logger
    def create(self, path, mode, file_info=None):
        """
        Create and open a new file. The file handle is set directly on the `file_info` object.

        Args:
            path (str): The path to the new file node
            mode (int): The desired mode bits of the created file
            file_info (FileInfo): The node's file info

        Returns:
            int: 0 if the operation succeeded, negative otherwise
        """
        node_path, blob_name = os.path.split(path)
        node = self.root.get_child(node_path)
        if not isinstance(node, DirectoryNode):
            raise FuseOSError(ENOTDIR)
        file_node = node.create_file(blob_name, mode)
        file_info.fh = file_node.open()
        file_info.direct_io = 1
        return 0

    @exception_logger
    def destroy(self, path):
        """
        Called on filesystem destruction.

        Args:
            path (str): Always '/'

        """
        return self.root.destroy()

    @exception_logger
    def flush(self, path, file_info):
        """
        Flush the file content to the underlying storage.

        Args:
            path (str): The path to the node.
            file_info (FileInfo): The node's file info.

        Returns:
            int: 0 if the operation succeeded, negative otherwise

        """
        node = self.root.get_child(path)
        if not isinstance(node, FileNode):
            raise FuseOSError(EISDIR)
        return node.get_descriptor(file_info.fh)\
            .flush()

    @exception_logger
    def fsync(self, path, datasync, file_info):
        """
        Synchronize the file content.

        Args:
            path (str): The path to the node.
            datasync (int): If non 0, do not sync the metadata
            file_info (FileInfo): The node's file info.

        Returns:
            int: 0 if the operation succeeded, negative otherwise

        """
        node = self.root.get_child(path)
        if not isinstance(node, FileNode):
            raise FuseOSError(EISDIR)
        return node.get_descriptor(file_info.fh)\
            .sync(datasync == 0)

    @exception_logger
    def fsyncdir(self, path, datasync, fh):
        """
        Synchronize the directory content.

        Args:
            path (str): The path to the node.
            datasync (int): If non 0, do not sync the metadata
            fh (int): The directory handle

        Returns:
            int: 0 if the operation succeeded, negative otherwise

        """
        node = self.root.get_child(path)
        if not isinstance(node, DirectoryNode):
            raise FuseOSError(ENOTDIR)
        return node.get_descriptor(fh)\
            .sync(datasync == 0)

    @exception_logger
    def getattr(self, path, file_info=None):
        """
        Get a node's attributes. The returned object should have the following signature::

            {
                 st_mode: int
                 st_ino: int
                 st_nlink: int
                 st_uid: int
                 st_gid: int
                 st_size: int
                 st_atime: int
                 st_mtime: int
                 st_ctime: int
            }

        See :py:class:`NodeAttributes` for more details.

        Args:
            path (str): The path to the node
            file_info (FileInfo): The node's file info

        Returns:
            dict: The node's attributes.

        """
        child = self.root.get_child(path)
        if file_info is not None:
            child = child.get_descriptor(file_info.fh)
        return child.get_attributes()\
            .get_all()

    @exception_logger
    def getxattr(self, path, name, position=0):
        """
        Get a node's extra attribute.

        Args:
            path (str): The path to the node
            name (str): The name of the attribute
            position (int): Unknown

        Returns:
            str: The attribute's value. Default to an empty string if the attribute does not exist.
        """
        return self.root.get_child(path)\
            .get_extra_attributes()\
            .get_attribute(name)

    @exception_logger
    def init(self, path):
        """
        Called on filesystem construction.

        Args:
            path (str): Always '/'

        """
        return self.root.init()

    @exception_logger
    def listxattr(self, path):
        """
        Get a node's list of extra attribute names.

        Args:
            path (str): The path to the node

        Returns:
            list(str): A list of extra attribute names.
        """
        return self.root.get_child(path)\
            .get_extra_attributes()\
            .get_attribute_names()

    @exception_logger
    def mkdir(self, path, mode):
        """
        Create a directory node.

        Args:
            path (str): The path to the new directory node.
            mode (int): The desired mode bits of the created directory

        Returns:
            int: 0 if the operation succeeded, negative otherwise
        """
        node_path, dir_name = os.path.split(path)
        node = self.root.get_child(node_path)
        if not isinstance(node, DirectoryNode):
            raise FuseOSError(ENOTDIR)
        node.create_dir(dir_name, mode)

    @exception_logger
    def open(self, path, file_info):
        """
        Open a file node for reading/writing. The file handle is set directly on the `file_info` object.

        Args:
            path (str): The path to the new file node
            file_info (FileInfo): The node's file info

        Returns:
            int: 0 if the operation succeeded, negative otherwise
        """
        node = self.root.get_child(path)
        if not isinstance(node, FileNode):
            raise FuseOSError(EISDIR)
        file_info.fh = node.open()
        file_info.direct_io = 1

    @exception_logger
    def opendir(self, path):
        """
        Open a directory for reading/writing.

        Args:
            path (str): The path to the directory node

        Returns:
            int: The file handle for the opened directory
        """
        node = self.root.get_child(path)
        if not isinstance(node, DirectoryNode):
            raise FuseOSError(ENOTDIR)
        return node.open()

    @exception_logger
    def read(self, path, size, offset, file_info):
        """
        Read the content of a file node. It may also be called on link nodes.

        Args:
            path (str): The path to the node.
            size (int): The number of bytes to read.
            offset (int): The number of bytes to skip
            file_info (FileInfo): The node's file info

        Returns:
            str: The bytes read from the file.
        """
        node = self.root.get_child(path)
        if not isinstance(node, FileNode):
            raise FuseOSError(EISDIR)
        return node.get_descriptor(file_info.fh)\
            .read(size, offset)

    @exception_logger
    def readdir(self, path, fh):
        """
        Get the list of children names within a directory.

        Args:
            path (str): The path to the directory node
            fh: The file handle for the opened directory

        Returns:
            list(str): The list of children names (including '.' and '..')
        """
        node = self.root.get_child(path)
        if not isinstance(node, DirectoryNode):
            raise FuseOSError(ENOTDIR)
        return node.get_descriptor(fh).get_children_names()

    @exception_logger
    def readlink(self, path):
        """
        Get the target location of a symlink.

        Args:
            path (str): The path to the symlink node.

        Returns:
            str: The path to the target node
        """
        node = self.root.get_child(path)
        if not isinstance(node, LinkNode):
            return node.path
        return node.get_target_path()

    @exception_logger
    def release(self, path, file_info):
        """
        Close a file node.

        Args:
            path (str): The path to the file node
            file_info (FileInfo): The node's file info

        Returns:
            int: 0 if the operation succeeded, negative otherwise
        """
        node = self.root.get_child(path)
        if not isinstance(node, FileNode):
            raise FuseOSError(EISDIR)
        return node.close(file_info.fh)

    @exception_logger
    def releasedir(self, path, fh):
        """
        Close an opened handle for a directory.

        Args:
            path (str): The path to the directory node
            fh (int): The file handle for the opened directory

        Returns:
            int: 0 if the operation succeeded, negative otherwise
        """
        node = self.root.get_child(path)
        if not isinstance(node, DirectoryNode):
            raise FuseOSError(ENOTDIR)
        return node.close(fh)

    @exception_logger
    def removexattr(self, path, name):
        """
        Remove a node's extra attribute.

        Args:
           path (str): The path to the node
           name (str): The name of the attribute

        Returns:
           int: 0 if the operation succeeded, negative otherwise
        """
        self.root.get_child(path)\
            .get_extra_attributes()\
            .remove_attribute(name)

        return 0

    @exception_logger
    def rename(self, old, new):
        """
        Rename a node.

        Args:
            old (str): The path to the node
            new (str): The node's new path

        Returns:
            int: 0 if the operation succeeded, negative otherwise

        """
        return self.root.get_child(old)\
            .rename(new)

    @exception_logger
    def rmdir(self, path):
        """
        Remove a directory node.

        Args:
            path (str): The path to the directory node

        Returns:
            int: 0 if the operation succeeded, negative otherwise
        """
        node = self.root.get_child(path)
        if not isinstance(node, DirectoryNode):
            raise FuseOSError(ENOTDIR)
        node.delete()

    @exception_logger
    def setxattr(self, path, name, value, options, position=0):
        """
        Set extra attributes on the given node.

        Args:
            path (str): The path to the node.
            name (str): The name of the attribute.
            value (str): The value of the attribute.
            options (int): Unknown.
            position (int): Unknown.

        Returns:
            int: 0 if the operation succeeded, negative otherwise
        """
        self.root.get_child(path)\
            .get_extra_attributes()\
            .set_attribute(name, value)
        return 0

    @exception_logger
    def statfs(self, path):
        """
        Returns information about the mounted filesystem. The returned object should have the following signature::

            {
                 f_bsize: int
                 f_frsize: int
                 f_blocks: int
                 f_bfree: int
                 f_bavail: int
                 f_files: int
                 f_ffree: int
                 f_favail: int
                 f_fsid: int
                 f_flag: int
                 f_namemax: int
            }

        See :py:class:`NodeFSAttributes` for more details.

        Args:
            path (str): The pathname of any file within the mounted filesystem

        Returns:
            dict: Information about the mounted filesystem.

        """
        return self.root.get_child(path)\
            .get_fs_attributes()\
            .get_all()

    @exception_logger
    def symlink(self, target, source):
        """
        Create a symbolic link.

        Args:
            target (str): The link's target
            source (str): The link node's location

        Returns:
            int: 0 if the operation succeeded, negative otherwise

        """
        raise FuseOSError(ENOSYS)

    @exception_logger
    def truncate(self, path, length, file_info=None):
        """
        Truncate a file node. It may also be called on link nodes.

        Args:
            path (str): The path to the node.
            length (int): The number of bytes to keep (starting from the beginning of the file).
            file_info (FileInfo): The node's file info.

        Returns:
            int: 0 if the operation succeeded, negative otherwise
        """
        node = self.root.get_child(path)
        if not isinstance(node, FileNode):
            raise FuseOSError(EISDIR)

        fh = node.open() if file_info is None else file_info.fh
        node.get_descriptor(fh)\
            .truncate(length)
        if file_info is None:
            node.close(fh)

    @exception_logger
    def unlink(self, path):
        """
        Delete a file node. It may also be called on link nodes.
        Args:
            path (str): The path to the node

        Returns:
            int: 0 if the operation succeeded, negative otherwise
        """
        node = self.root.get_child(path)
        if isinstance(node, FileNode) or isinstance(node, LinkNode):
            return node.delete()
        raise FuseOSError(EISDIR)

    @exception_logger
    def utimens(self, path, times=None):
        """
        Set the access time and modified time attribute of a node.

        Args:
            path (str): The path to the node.
            times (int, int): A tuple of times. The first item is the access time, the second item is the modified time.

        Returns:
            int: 0 if the operation succeeded, negative otherwise
        """
        self.root.get_child(path)\
            .get_attributes()\
            .set_access_time(times[0])\
            .set_modified_time(times[0])
        return 0

    @exception_logger
    def write(self, path, data, offset, file_info):
        """
        Write to a file node. It may also be called on link nodes.

        Args:
            path (str): The path to the node.
            data (str): The binary data to write to the node.
            offset (int): The number of bytes to skip.
            file_info (FileInfo): The node's file info.

        Returns:
            str: The number of bytes written to the node.
        """
        node = self.root.get_child(path)
        if not isinstance(node, FileNode):
            raise FuseOSError(EISDIR)
        return node.get_descriptor(file_info.fh)\
            .write(data, offset)
