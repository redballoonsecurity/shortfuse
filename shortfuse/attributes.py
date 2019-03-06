from errno import ENOENT, EOPNOTSUPP
from stat import S_IMODE, S_IFMT

from fuse import FuseOSError


class NodeExtraAttributes:
    """
    Store extra attributes for a FUSE node. Modifications are only performed in memory and are not persisted to
    the storage backend.

    Args:
        **kwargs (dict(str, str)): Each key value is added into the attribute dictionary
    """

    def __init__(self, **kwargs):
        self._attributes = kwargs

    def copy(self):
        """
        Create a copy of the attribute object.

        Returns:
            NodeExtraAttributes: The copy of the attribute instance
        """
        return NodeExtraAttributes(**self._attributes)

    def get_attribute(self, name):
        """
        Read an attribute's value.

        Args:
            name (str): The name of the attribute to read.

        Returns:
            str: The attribute value.

        Raises:
            FuseOSError(ENOENT): If the attribute does not exist
        """
        if name not in self._attributes:
            return ''
        return self._attributes[name]

    def get_attribute_names(self):
        """
        Read a list of all attribute names.

        Returns:
            list(str): The list of attribute names
        """
        return self._attributes.keys()

    def set_attribute(self, name, value):
        """
        Set the attribute's value. If the attribute already exist, its value is overwritten.

        Args:
            name (str): The name of the attribute to set
            value (str): The value of the attribute to set

        Returns:
            NodeExtraAttributes: The instance
            
        Raises:
            FuseOSError(EOPNOTSUPP): If the operation has not been overridden by a child implemenetation.
        """
        raise FuseOSError(EOPNOTSUPP)

    def remove_attribute(self, name):
        """
        Remove an attribute.

        Args:
            name (str): The name of the attribute to remove.

        Returns:
            NodeExtraAttributes: The instance

        Raises:
            FuseOSError(EOPNOTSUPP): If the operation has not been overridden by a child implemenetation.
        """
        raise FuseOSError(EOPNOTSUPP)


class NodeAttributes:
    """
    Represent a node's attributes. See the `manual <http://man7.org/linux/man-pages/man2/stat.2.html>`_ page for a
    more detailed explanation on the meaning of each attribute. No attribute is set by default, they must be either
    provided to the constructor.

    Args:
        mode (int): The file type and mode
        ino (int): The Inode number
        nlink (int): The number of hard links
        uid (int): The user ID of the owner
        gid (int): The group ID of the owner
        size (int): The total size of the node, in bytes
        atime (int): The time of last access
        mtime (int): The time of last modification
        ctime (int): The time of last status change
    """

    def __init__(
            self,
            **kwargs
    ):
        self._attributes = dict()
        for key, value in kwargs.items():
            if not key.startswith("st_"):
                key = 'st_' + key
            self._attributes[key] = value

    def copy(self, **kwargs):
        """
        Create a copy of the attribute object.

        Args:
            **kwargs dict(): See the arguments for the :py:class:`NodeAttributes` constructor.

        Returns:
            NodeAttributes: The copy of the attribute instance
        """
        return NodeAttributes(**self.merge_attributes(**kwargs))

    def merge_attributes(self, **kwargs):
        """
        Merge attributes from the node with the provided arguments.

        Args:
            **kwargs: See the arguments for the :py:meth:`NodeAttributes.copy` constructor.

        Returns:
            dict(str, int): The merged attributes
        """
        updated_attributes = {key[3:]: value for key, value in self._attributes.items()}
        updated_attributes.update(kwargs)
        return updated_attributes

    def get_all(self):
        """
        Get all attributes for the node.

        Returns:
            dict(str, int): The node's attributes. The key correspond to the standard unix name for each attribute.
        """
        return self._attributes

    def set_mode(self, mode):
        """
        Set the node type and mode

        Args:
            mode (int): The file type and mode

        Returns:
            NodeAttributes: The instance

        Raises:
            FuseOSError(EOPNOTSUPP): If the operation has not been overridden by a child implemenetation.
        """
        raise FuseOSError(EOPNOTSUPP)

    def get_mode(self, default_value=None):
        """
        Get the file type and mode.

        Args:
            default_value (int): The default value if the attribute does not exist.

        Returns:
            int: The file type and mode

        """
        return self._attributes.get('st_mode', default_value)

    def set_node_type(self, type):
        """
        Set the node type

        Args:
            type: S_IFDIR | S_IFCHR | S_IFBLK | S_IFREG | S_IFIFO | S_IFLNK | S_IFSOCK: The node type

        Returns:
            NodeAttributes: The instance

        """
        return self.set_mode(S_IFMT(type) | self.get_permissions())

    def get_node_type(self):
        """
        Get the node type

        Returns:
            S_IFDIR | S_IFCHR | S_IFBLK | S_IFREG | S_IFIFO | S_IFLNK | S_IFSOCK: The node type

        """
        return S_IFMT(self.get_mode(0))

    def set_permissions(self, mode):
        """
        Get the node's permissions.

        Args:
            mode: The node's permissions (ie 0o777)

        Returns:
            NodeAttributes: The instance

        """
        return self.set_mode(S_IMODE(mode) | self.get_node_type())

    def get_permissions(self):
        """
        Get the node's permissions.

        Returns:
            int: The node permission

        """
        return S_IMODE(self.get_mode(0))

    def set_ino(self, ino):
        """
        Set the inode number

        Args:
            ino (int): The inode number

        Returns:
            NodeAttributes: The instance

        Raises:
            FuseOSError(EOPNOTSUPP): If the operation has not been overridden by a child implemenetation.
        """
        raise FuseOSError(EOPNOTSUPP)

    def set_nlink(self, nlink):
        """
        Set the number of hard links to the node

        Args:
            nlink (int): The number of hard links to the node

        Returns:
            NodeAttributes: The instance

        Raises:
            FuseOSError(EOPNOTSUPP): If the operation has not been overridden by a child implemenetation.
        """
        raise FuseOSError(EOPNOTSUPP)

    def get_nlink(self, default_value=None):
        """
        Get the number of hard links to the node

        Args:
            default_value (int): The default value if the attribute does not exist.

        Returns:
            int: The number of hard links to the node

        """
        return self._attributes.get('st_nlink', default_value)

    def set_uid(self, uid):
        """
        Set the user ID of the owner

        Args:
            uid (int): The user ID of the owner

        Returns:
            NodeAttributes: The instance

        Raises:
            FuseOSError(EOPNOTSUPP): If the operation has not been overridden by a child implemenetation.
        """
        raise FuseOSError(EOPNOTSUPP)

    def get_uid(self, default_value=None):
        """
        Get the user owner ID

        Args:
            default_value (int): The default value if the attribute does not exist.

        Returns:
            int: The user owner ID

        """
        return self._attributes.get('st_uid', default_value)

    def set_gid(self, gid):
        """
        Set the group ID of the owner

        Args:
            gid (int): The group ID of the owner

        Returns:
            NodeAttributes: The instance

        Raises:
            FuseOSError(EOPNOTSUPP): If the operation has not been overridden by a child implemenetation.
        """
        raise FuseOSError(EOPNOTSUPP)

    def get_gid(self, default_value=None):
        """
        Get the group owner ID

        Args:
            default_value (int): The default value if the attribute does not exist.

        Returns:
            int: The group owner ID

        """
        return self._attributes.get('st_gid', default_value)

    def set_size(self, size):
        """
        Set the size of the node, in bytes.

        Args:
            size (int): The node size, in bytes.

        Returns:
            NodeAttributes: The instance

        Raises:
            FuseOSError(EOPNOTSUPP): If the operation has not been overridden by a child implemenetation.
        """
        raise FuseOSError(EOPNOTSUPP)

    def get_size(self, default_value=None):
        """
        Get the node size

        Args:
           default_value (int): The default value if the attribute does not exist.

        Returns:
           int: The node size

        """
        return self._attributes.get('st_size', default_value)

    def set_access_time(self, access_time):
        """
        Set access time of the node.

        Args:
            access_time (int): The access time of the node

        Returns:
            NodeAttributes: The instance

        Raises:
            FuseOSError(EOPNOTSUPP): If the operation has not been overridden by a child implemenetation.
        """
        raise FuseOSError(EOPNOTSUPP)

    def set_modified_time(self, modified_time):
        """
        Set modified time of the node

        Args:
            modified_time (int): The modified time of the node

        Returns:
            NodeAttributes: The instance

        Raises:
            FuseOSError(EOPNOTSUPP): If the operation has not been overridden by a child implemenetation.
        """
        raise FuseOSError(EOPNOTSUPP)

    def set_created_time(self, created_time):
        """
        Set the created time of the node

        Args:
            created_time (int): The created time of the node

        Returns:
            NodeAttributes: The instance

        Raises:
            FuseOSError(EOPNOTSUPP): If the operation has not been overridden by a child implemenetation.
        """
        raise FuseOSError(EOPNOTSUPP)


class NodeFSAttributes:
    """
    Represent a node's filesystem attributes. See the `manual <http://man7.org/linux/man-pages/man3/statvfs.3.html>`_
    page for a more detailed explanation on the meaning of each attribute. No attribute is set by default, they must
    be either provided to the constructor or the base :py:class:`NodeAttributes` instance.

    Args:
        bsize (int): The optimal transfer block size
        frsize (int): The fragment size
        blocks (int): The total number of data blocks in the filesystem
        bfree (int):  The number of free blocks in the filesystem
        bavail (int): The number of free blocks available to the unprivileged user
        files (int): The total number of inodes in the file system
        ffree (int): The number of free inodes in the filesystem
        favail (int): The number of free inodes available to the unprivileged user
        fsid (int): The filesystem id
        flags (int): The mount flags of the filesystem
        namemax (int): The maximum length of file name
    """

    def __init__(
        self,
        bsize=0,
        frsize=0,
        blocks=0,
        bfree=0,
        bavail=0,
        files=0,
        ffree=0,
        favail=0,
        fsid=0,
        flags=0,
        namemax=0
    ):
        self._attributes = dict(
            f_bsize=bsize,
            f_frsize=frsize,
            f_blocks=blocks,
            f_bfree=bfree,
            f_bavail=bavail,
            f_files=files,
            f_ffree=ffree,
            f_favail=favail,
            f_fsid=fsid,
            f_flags=flags,
            f_namemax=namemax
        )

    def copy(self):
        """
        Create a copy of the attribute object.

        Returns:
            NodeFSAttributes: The copy of the attribute instance
        """
        attributes = {}
        for key, value in self._attributes.items():
            attributes[key[2:]] = value
        return NodeFSAttributes(**attributes)

    def get_all(self):
        """
        Get all the filesystem attributes for the node.

        Returns:
            dict(str, int): The node's filesystem attributes. The key correspond to the standard unix name for each
                attribute.
        """
        return self._attributes
