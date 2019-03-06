import os
import sys
import time
from errno import ENOENT, ENOTDIR, ESPIPE
from stat import S_IFMT, S_IMODE, S_IFDIR, S_IFREG
from threading import RLock

from fuse import FuseOSError

from shortfuse.attributes import NodeAttributes, NodeExtraAttributes, NodeFSAttributes
from shortfuse.node import Node, DirectoryNode, FileNode, NodeDescriptor, FileSystem, FileDescriptor, \
    DirectoryDescriptor


class MemoryNodeAttributes(NodeAttributes):
    """
    Implements an in memory :py:class:`~shortfuse.attributes.NodeAttributes`
    """
    def copy(self, **kwargs):
        return MemoryNodeAttributes(**self.merge_attributes(**kwargs))

    def set_mode(self, mode):
        self._attributes['st_mode'] = mode
        return self

    def set_node_type(self, type):
        return self.set_mode(S_IFMT(type) | self.get_permissions())

    def set_permissions(self, mode):
        return self.set_mode(S_IMODE(mode) | self.get_node_type())

    def set_ino(self, ino):
        self._attributes['st_ino'] = ino
        return self

    def set_nlink(self, nlink):
        self._attributes['st_nlink'] = nlink
        return self

    def set_uid(self, uid):
        self._attributes['st_uid'] = uid
        return self

    def set_gid(self, gid):
        self._attributes['st_gid'] = gid
        return self

    def set_size(self, size):
        self._attributes['st_size'] = size
        return self

    def set_access_time(self, access_time):
        self._attributes['st_atime'] = access_time
        return self

    def set_modified_time(self, modified_time):
        self._attributes['st_mtime'] = modified_time
        return self

    def set_created_time(self, created_time):
        self._attributes['st_ctime'] = created_time
        return self


class MemoryNodeExtraAttributes(NodeExtraAttributes):
    """
    Implements an in memory :py:class:`~shortfuse.attributes.NodeExtraAttributes`
    """

    def copy(self):
        return MemoryNodeExtraAttributes(**self._attributes)

    def set_attribute(self, name, value):
        self._attributes[name] = value
        return self

    def remove_attribute(self, name):
        if name not in self._attributes:
            raise FuseOSError(ENOENT)
        del self._attributes[name]
        return self


class MemoryNode(Node):
    """
    Implements an in memory :py:class:`~shortfuse.node.Node`.
    """
    def delete(self):
        self.parent.remove_child(self.name)
        return 0

    def has_access(self, access_mode):
        return 0

    def rename(self, new_path):
        basename, name = os.path.split(new_path)
        parent = self._get_root().get_child(basename)
        if not isinstance(parent, DirectoryNode):
            raise FuseOSError(ENOTDIR)
        parent.add_child(self)
        self.parent.remove_child(self.name)


class MemoryFileDescriptor(FileDescriptor):
    """
    Implements an in memory :py:class:`~shortfuse.node.FileDescriptor`.
    """
    def __init__(self, *args, **kwargs):
        FileDescriptor.__init__(self, *args, **kwargs)
        self._lock = RLock()
        self._content = self.node._content

    def read(self, size, offset):
        content = self._content
        start = min(len(content), offset)
        end = min(len(content), size + offset)
        return content[start:end]

    def write(self, data, offset):
        with self._lock:
            if len(self._content) < offset:
                raise FuseOSError(ESPIPE)
            self._content = self._content[:offset] + data + self._content[offset+len(data):]
            self.attributes.set_size(len(self._content))
            self.attributes.set_modified_time(int(time.time()))
            self.attributes.set_access_time(int(time.time()))
            return len(data)

    def truncate(self, length):
        with self._lock:
            if length == len(self._content):
                return 0
            if length < len(self._content):
                self._content = self._content[:length]
            # Pad the content to reach the desired size
            self._content += b'\0'*(length - len(self._content))
            self.attributes.set_size(len(self._content))
            self.attributes.set_modified_time(int(time.time()))
            self.attributes.set_access_time(int(time.time()))

    def flush(self):
        pass


class MemoryFileNode(MemoryNode, FileNode):
    """
    Implements an in memory :py:class:`~shortfuse.node.FileNode`. See :py:class:`~MemoryNode` for its constructor
    arguments.
    """
    def __init__(self, *args, **kwargs):
        FileNode.__init__(self, *args, **kwargs)
        self._content = b''

    def _create_node_descriptor(self):
        return MemoryFileDescriptor(self)

    def _free_node_descriptor(self, node_descriptor):
        node_descriptor.free()
        self._content = node_descriptor._content
        self.attributes = node_descriptor.attributes
        self.fs_attributes = node_descriptor.fs_attributes
        self.extra_attributes = node_descriptor.extra_attributes


class MemoryDirectoryDescriptor(DirectoryDescriptor):
    """
    Implements an in memory :py:class:`~shortfuse.node.DirectoryDescriptor`.
    """
    def _get_children(self):
        return self.node._children.values()


class MemoryDirectoryNode(MemoryNode, DirectoryNode):
    """
    Implements an in memory :py:class:`~shortfuse.node.DirectoryNode`. See :py:class:`MemoryNode` for its
    constructor arguments.
    """
    def __init__(self, *args, **kwargs):
        DirectoryNode.__init__(self, *args, **kwargs)

    def _create_node(self, NodeClass, type, name, mode, nlink=1):
        node = NodeClass(
            self,
            name,
            attributes=MemoryNodeAttributes(
                mode=(type | mode),
                size=0,
                nlink=nlink,
                uid=self.attributes.get_uid(),
                gid=self.attributes.get_gid(),
                atime=time.time(),
                mtime=time.time(),
                ctime=time.time(),
            ),
            fs_attributes=self.fs_attributes,
            extra_attributes=NodeExtraAttributes()
        )
        self.add_child(node)
        return node

    def _create_node_descriptor(self):
        return MemoryDirectoryDescriptor(self)

    def _free_node_descriptor(self, node_descriptor):
        node_descriptor.free()
        self.attributes = node_descriptor.attributes
        self.fs_attributes = node_descriptor.fs_attributes
        self.extra_attributes = node_descriptor.extra_attributes

    def create_dir(self, name, mode):
        return self._create_node(MemoryDirectoryNode, S_IFDIR, name, mode, 2)

    def create_file(self, name, mode):
        return self._create_node(MemoryFileNode, S_IFREG, name, mode)


class MemoryFileSystem(MemoryDirectoryNode, FileSystem):
    """
    Implements an in memory :py:class:`~shortfuse.FileSystem`.

    Args:
        mode (int): The permission mask for the root directory
        uid (int): The user owner of the root directory
        gid (int): The group owner of the root directory
    """
    def __init__(self, mode, uid, gid):
        MemoryDirectoryNode.__init__(
            self,
            None,
            '/',
            attributes=MemoryNodeAttributes(
                mode=(S_IFDIR | mode),
                nlink=2,
                uid=uid,
                gid=gid,
                atime=time.time(),
                mtime=time.time(),
                ctime=time.time()
            ),
            fs_attributes=NodeFSAttributes(
                bsize=512,
                blocks=sys.maxsize,
                bavail=sys.maxsize
            ),
            extra_attributes=NodeExtraAttributes()
        )
