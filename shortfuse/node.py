import logging
import os
import time
import traceback
from errno import ENOENT, EEXIST, EPERM, EBADF
from threading import RLock

from fuse import FuseOSError

from shortfuse.attributes import NodeAttributes, NodeExtraAttributes, NodeFSAttributes

SEPARATOR = '/'
DEFAULT_CHILDREN = ['.', '..']


class NodeDescriptor:
    """
    A handle to an opened node.

    Args:
        id (int): The id of the node handle
        node (Node): The node that the handle represents

    Attributes:
        node (Node): The node that the handle represents
        attributes (:py:class:`~shortfuse.attributes.NodeAttributes`): Attributes for the node
        fs_attributes (:py:class:`~shortfuse.attributes.NodeFSAttributes`): The filesystem attributes for the node
        extra_attributes (:py:class:`~shortfuse.attributes.NodeExtraAttributes`): Extra attributes for the node
    """
    def __init__(self, node):
        self.node = node
        self.attributes = node.attributes.copy()
        self.fs_attributes = node.fs_attributes.copy()
        self.extra_attributes = node.extra_attributes.copy()

    def sync(self, sync_metadata=True):
        """
        Synchronize the node content.

        Args:
            sync_metadata (bool): If false, do not sync the metadata

        Returns:
            int: 0 If the caller has access to the required node.
        """
        return 0

    def free(self):
        """
        Close all resources associated with the file descriptor. It means they are no longer any opened handles for
        the node.
        """
        pass


class Node:
    """
    A fuse file system node.

    Args:
        parent (DirectoryNode): The parent node.
        name (str): The basename of the node
        attributes (NodeAttributes): Attributes for the node
        fs_attributes (NodeFSAttributes): The filesystem attributes for the node
        extra_attributes (NodeExtraAttributes): Extra attributes for the node

    Attributes:
        path (str): The node's full path.
        parent (:py:class:`DirectoryNode`): The parent node.
        name (str): The node's basename.
        attributes (:py:class:`~shortfuse.attributes.NodeAttributes`): Attributes for the node
        fs_attributes (:py:class:`~shortfuse.attributes.NodeFSAttributes`): The filesystem attributes for the node
        extra_attributes (:py:class:`~shortfuse.attributes.NodeExtraAttributes`): Extra attributes for the node

    """
    def __init__(self, parent, name, attributes, fs_attributes, extra_attributes):
        self.path = name if parent is None else os.path.join(parent.path, name)
        self.parent = parent
        self.name = name
        self.attributes = attributes
        self.fs_attributes = fs_attributes
        self.extra_attributes = extra_attributes

        self._descriptors_lock = RLock()
        self._next_node_descriptor = 1
        self._descriptor = None
        self._node_descriptors = set()

    def _get_root(self):
        """
        Retrieve the root node of the file system.

        Returns:
            DirectoryNode: The root node of the file system
        """
        root = self
        while root.parent is not None:
            root = root.parent
        return root

    def open(self):
        """
        Open the node for reading/writing.

        Returns:
            int: The unique identifier for the file handle.

        Raises:
            FuseOSError(EPERM): If the :py:meth:`~Node._create_node_descriptor` method is not overriden.
        """
        with self._descriptors_lock:
            nd = self._next_node_descriptor
            if not self._descriptor:
                self._descriptor = self._create_node_descriptor()
            self._node_descriptors.add(nd)
            self._next_node_descriptor += 1
            return nd

    def _create_node_descriptor(self):
        """
        Instantiate a new :py:class:`NodeDescriptor` in response to an ``open`` request. Calls to this method are
        thread-safe. Note that they are only ever one :py:class:`NodeDescriptor` per :py:class:`Node`.

        Returns:
            NodeDescriptor: The node descriptor
        """
        raise FuseOSError(EPERM)

    def close(self, file_handle):
        """
        Close the file handle for the node.

        Args:
            file_handle (int): The unique identifier for the file handle.

        Returns:
            int: 0 if the operation succeeded, negative otherwise
        """
        with self._descriptors_lock:
            node_descriptor = self.get_descriptor(file_handle)
            self._node_descriptors.remove(file_handle)
            if len(self._node_descriptors) == 0:
                self._free_node_descriptor(node_descriptor)
                self._descriptor = None
            return 0

    def _free_node_descriptor(self, node_descriptor):
        """
        Close a file handle to for this node's descriptor. The implementation call :py:meth:`NodeDescriptor.free` and
        synchronize the attributes. Calls to this method are thread-safe.

        Args:
            node_descriptor (NodeDescriptor): The node descriptor to be closed.

        Returns:
            int: 0 if the operation succeeded, negative otherwise
        """
        raise FuseOSError(EPERM)

    def delete(self):
        """
        Delete the node from the file system. It requires bookkeeping on the parent directory.

        Returns:
            int: 0 if the operation succeeded, negative otherwise

        Raises:
            FuseOSError(EPERM): If the operation is not overwritten by a child class.
        """
        raise FuseOSError(EPERM)

    def has_access(self, access_mode):
        """
        Check that the caller has access to the requested node.

        Args:
            access_mode (int): The requested access mode. More details can be found at the
                `manual <http://man7.org/linux/man-pages/man2/access.2.html>`_ page

        Returns:
            int: 0 If the caller has access to the required node.
        """
        raise FuseOSError(EPERM)

    def rename(self, new_path):
        """
        Rename a node.

        Args:
            new_path (str): The node's new path

        Returns:
            int: 0 if the operation succeeded, negative otherwise

        """
        raise FuseOSError(EPERM)

    def get_descriptor(self, node_handle):
        """
        Get the node descriptor for the corresponding handle.

        Args:
            node_handle (int): The handle ID.

        Returns:
            NodeDescriptor: The node descriptor

        Raises:
            FuseOSError(ENOENT): If the node descriptor does not exist.
        """
        if node_handle not in self._node_descriptors:
            raise FuseOSError(EBADF)
        return self._descriptor

    def get_attributes(self):
        """
        Get the node's attributes. If a descriptor is present, the attributes are read from there.
        Returns:
            NodeAttributes: The node's attributes.
        """
        with self._descriptors_lock:
            if self._descriptor:
                return self._descriptor.attributes
            return self.attributes

    def get_extra_attributes(self):
        """
        Get the node's extra attributes. If a descriptor is present, the attributes are read from there.
        Returns:
            NodeExtraAttributes: The node's extra attributes.
        """
        with self._descriptors_lock:
            if self._descriptor:
                return self._descriptor.extra_attributes
            return self.extra_attributes

    def get_fs_attributes(self):
        """
        Get the node's fs attributes. If a descriptor is present, the attributes are read from there.
        Returns:
            NodeFSAttributes: The node's fs attributes.
        """
        with self._descriptors_lock:
            if self._descriptor:
                return self._descriptor.fs_attributes
            return self.fs_attributes


class FileDescriptor(NodeDescriptor):
    """
    A file descriptor. See :py:class:`NodeDescriptor` for more details.
    """

    def read(self, size, offset):
        """
        Read data from the file. See the `read <http://man7.org/linux/man-pages/man2/read.2.html>` documentation for
        more details on the implementation requirements.

        Args:
            size (int): The number of bytes to read.
            offset (int): The number of bytes to skip.

        Returns:
            str: The bytes read.

        Raises:
            FuseOSError(EPERM): If the operation is not overwritten by a child class.
        """
        raise FuseOSError(EPERM)

    def write(self, data, offset):
        """
        Write data to the file. See the `write <http://man7.org/linux/man-pages/man2/write.2.html>` documentation for
        more details on the implementation requirements.

        Args:
            data (str): The bytes to write
            offset (int): The offset at which to start writing bytes.

        Returns:
            int: The number of bytes written.

        Raises:
            FuseOSError(EPERM): If the operation is not overwritten by a child class.
        """
        raise FuseOSError(EPERM)

    def truncate(self, length):
        """
        Truncate the file content. See the `truncate <http://man7.org/linux/man-pages/man2/truncate.2.html>`
        documentation for more details on the implementation requirements.

        Args:
            length (int): The number of bytes to keep (from the beginning of the file)

        Returns:
            int: 0 if the operation succeeded, negative otherwise

        Raises:
            FuseOSError(EPERM): If the operation is not overwritten by a child class.
        """
        raise FuseOSError(EPERM)

    def flush(self):
        """
        Flush the content of the file to the underlying storage.

        Returns:
            int: 0 if the operation succeeded, negative otherwise

        Raises:
            FuseOSError(EPERM): If the operation is not overwritten by a child class.
        """
        raise FuseOSError(EPERM)


class FileNode(Node):
    """
    A node representing a file. Data can be read from and written to this node.

    Args:
        parent (DirectoryNode): The parent node.
        name (str): The basename of the node
        attributes (NodeAttributes): Attributes for the node
        fs_attributes (NodeFSAttributes): The filesystem attributes for the node
        extra_attributes (NodeExtraAttributes): Extra attributes for the node
    """
    def __init__(
        self,
        parent,
        name,
        attributes,
        fs_attributes,
        extra_attributes,
    ):
        Node.__init__(
            self,
            parent,
            name,
            attributes=attributes,
            fs_attributes=fs_attributes,
            extra_attributes=extra_attributes,
        )

    def get_descriptor(self, node_handle):
        """
        Get the node descriptor for the corresponding handle.

        Args:
            node_handle (int): The handle ID.

        Returns:
            FileDescriptor: The node descriptor

        Raises:
            FuseOSError(ENOENT): If the node descriptor does not exist.
        """
        return Node.get_descriptor(self, node_handle)


class LinkNode(Node):
    """
    A node representing a :py:class:`File` node. It has the same signature as :py:class:`File` node but all
    calls are forwarded to the target.

    Args:
        parent (DirectoryNode): The parent node.
        name (str): The basename of the node.
        target (Node): The node that the link points to.
        attributes (NodeAttributes): Attributes for the node
        fs_attributes (NodeFSAttributes): The filesystem attributes for the node
        extra_attributes (NodeExtraAttributes): Extra attributes for the node

    Attributes:
        target (:py:class:`FileNode`): The file node that the link points to.
    """
    def __init__(
        self,
        parent,
        name,
        target,
        attributes,
        fs_attributes,
        extra_attributes
    ):
        Node.__init__(
            self,
            parent,
            name,
            attributes=attributes,
            fs_attributes=fs_attributes,
            extra_attributes=extra_attributes
        )
        self.target = target
        self.target.attributes.set_nlink(self.target.attributes.get_nlink() + 1)

    def get_target_path(self):
        """
        Get the node targeted by the link.

        Returns:
            str: The path to the target node.
        """
        return os.path.relpath(self.target.path, self.parent.path)


class DirectoryDescriptor(NodeDescriptor):
    """
    A directory descriptor. See :py:class:`NodeDescriptor` for more details.
    """

    def get_children_names(self):
        """
        Get the list of children names in this directory.

        Returns:
            list(str): The list of children names (including '.' and '..')
        """
        children_name = sorted([bindb_file.name for bindb_file in self._get_children()])
        return DEFAULT_CHILDREN + children_name


    def _get_children(self):
        """
        Get an unordered list of children node for the directory

        Returns:
            list(Node): The children nodes
        """
        raise FuseOSError(EPERM)


class DirectoryNode(Node):
    """
    A node representing a directory. Nodes can be added to/removed from directories.

    Args:
        parent (DirectoryNode): The parent node.
        name (str): The basename of the node
        attributes (NodeAttributes): Attributes for the node
        fs_attributes (NodeFSAttributes): The filesystem attributes for the node
        extra_attributes (NodeExtraAttributes): Extra attributes for the node
    """
    def __init__(
        self,
        parent,
        name,
        attributes,
        fs_attributes,
        extra_attributes
    ):
        Node.__init__(
            self,
            parent,
            name,
            attributes=attributes,
            fs_attributes=fs_attributes,
            extra_attributes=extra_attributes,
        )
        self._children = {}
        self._children_locks = RLock()

    def create_dir(self, name, mode):
        """
        Create a directory node.

        Args:
            name (str): The basename of the directory
            mode (int): The desired mode bits of the created directory.

        Returns:
            DirectoryNode: The created directory node

        Raises:
            FuseOSError(EPERM): If the operation is not overwritten by a child class.
        """
        raise FuseOSError(EPERM)

    def create_file(self, name, mode):
        """
        Create a file node.

        Args:
            name (str): The basename of the file
            mode (int): The desired mode bits of the created file.

        Returns:
            FileNode: The created file node

        Raises:
            FuseOSError(EPERM): If the operation is not overwritten by a child class.
        """
        raise FuseOSError(EPERM)

    def get_child(self, path):
        """
        Get a child :py:class:`Node`. The child may be nested in other :py:class:`Directory`.

        Args:
            path (str): The relative to the child node

        Returns:
            Node: The child node

        Raises:
            FuseOSError(ENOENT): If the child does not exist
        """
        if path is None:
            logging.error("Empty path provided in get_child for directory %s" % self.path)
            traceback.print_stack()
            raise FuseOSError(ENOENT)
        bindb_file = self
        for part in path.split(SEPARATOR):
            if not part:
                continue
            if not isinstance(bindb_file, DirectoryNode):
                logging.error("Expected a directory in %s" % bindb_file.path)
                traceback.print_stack()
                raise FuseOSError(ENOENT)
            bindb_file = bindb_file.get_direct_child(part)
        return bindb_file

    def replace_child(self, new_child):
        """
        Replace a child :py:class:`Node` by another :py:class:`Node`.

        Args:
            new_child (Node): The new child to add

        Raises:
            FuseOSError(ENOENT): If the new child's name does not match the name of the previous child.
        """
        with self._children_locks:
            if new_child.name not in self._children:
                logging.error("The child %s to replace does not exist in directory %s" % (new_child.name, self.path))
                raise FuseOSError(ENOENT)
            self._children[new_child.name] = new_child
            self.attributes.set_access_time(int(time.time()))
            self.attributes.set_modified_time(int(time.time()))

    def get_direct_child(self, name):
        """
        Get a direct child node.

        Args:
            name (str): The name of the node.

        Returns:
            Node: The child node.

        Raises:
            FuseOSError(ENOENT): If the child does not exist
        """
        with self._children_locks:
            if name not in self._children:
                raise FuseOSError(ENOENT)
            return self._children[name]

    def has_direct_child(self, name):
        """
        Determine if the :py:class:`Directory` contains the provided child.

        Args:
            name (str): The name of the child :py:class:`Node`

        Returns:
            bool: True if the child exist.

        """
        return name in self._children

    def add_child(self, node):
        """
        Add a child node and update the node's attributes accordingly.

        Args:
            node (Node): The node to be added.

        Raises:
            FuseOSError(EEXIST): If the child already exist
        """
        with self._children_locks:
            self._add_child(node)
            self.get_attributes().set_nlink(self.attributes.get_nlink() + 1)
            self.get_attributes().set_access_time(int(time.time()))
            self.get_attributes().set_modified_time(int(time.time()))

    def _add_child(self, node):
        """
        Add a child node without updating the node's attributes.

        Args:
            node (Node): The node to be added.

        Raises:
            FuseOSError(EEXIST): If the child already exist
        """
        with self._children_locks:
            if node.name in self._children:
                logging.error("The child %s already exist in %s" % (node.name, self.path))
                raise FuseOSError(EEXIST)
            self._children[node.name] = node

    def remove_child(self, name):
        """
        Remove a child node.

        Args:
            name (str): The name of the child.

        Raises:
            FuseOSError(ENOENT): If the child does not exist
        """
        with self._children_locks:
            if name not in self._children:
                raise FuseOSError(ENOENT)
            self.get_attributes().set_nlink(self.attributes.get_nlink() - 1)
            self.get_attributes().set_access_time(int(time.time()))
            self.get_attributes().set_modified_time(int(time.time()))
            del self._children[name]


class FileSystem:
    """
    A node representing a root filesystem. The implementation should also inherit from the :py:class:DirectoryNode
    class.
    """

    def init(self):
        """ Called on filesystem construction. """
        pass

    def destroy(self):
        """ Called on filesystem destruction. """
        pass
