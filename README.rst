===============
Shortfuse
===============

This module is aims to make it easier to leverage the `fusepy <https://github.com/fusepy/fusepy>` library. It offers the following improvements:

    - Method documentation. While fusepy provide some documentation, a lot of implementation details are lacking.

    - Ease of use. Shortfuse offers many base classes to represent common file system objects and their attributes. These objects take care of representing the tree structure commonly associated with file system. This also opens up opportunities for reducing duplicated logic. A specialized type of file can extend the functionality of a file commonly encountered in your custom file system.

Consider a file system wih the following nodes:

    - ``/`` : The root of the file system

    - ``/dir1`` : A regular directory

    - ``/dir1/file1`` : A regular file

    - ``/dir1/file2`` : A regular file

    - ``/file1`` : A regular file

    - ``/file2`` : A link pointing to /dir1/file4

Shortfuse would use the following objects to represent it:

.. image:: assets/diagram.svg
   :alt: Sample diagram of a shortfuse object relationship

Each arrow in the diagram show a reference from one object to the other. The diagram examplifies the 3 basic classes used to implement a custom file system with shortfuse:

    - :py:class:`~shortfuse.node.DirectoryNode` : A node that supports children and operations such as :py:meth:`~shortfuse.node.DirectoryNode.create_dir` and :py:meth:`~shortfuse.node.DirectoryNode.create_file`.

    - :py:class:`~shortfuse.node.FileNode` : A file node that supports reading/writing through the :py:class:`~shortfuse.node.FileDescriptor` abstraction.

    - :py:class:`~shortfuse.node.LinkNode` : A node that only point to another node. It does not support any operations and other nodes do not.

.. note::

    It is important to remember that all of these classes inherit from the :py:class:`~shortfuse.node.Node` class and some of its operations must be overridden.

When implementing a filesystem using shortfuse, your first step should be to override these classes. By default, most operations they define will result in an ``EPERM`` error to denote that the functionality is not available in the filesystem. Additionally, you may want to override the :py:class:`~shortfuse.attributes.NodeAttributes`, :py:class:`~shortfuse.attributes.NodeExtraAttributes` and :py:class:`~shortfuse.attributes.NodeFSAttributes` classes.

To get you started, a sample in memory filesystem implementation is available in the :py:mod:`shortfuse.extra.memory` package. The reason this package is in the main codebase is that it can be useful when implementing your own filesystem, especially the :py:class:`~shortfuse.extra.memory.MemoryNodeAttributes` and :py:class:`~shortfuse.extra.memory.MemoryNodeExtraAttributes` classes.

Testing
------------

This module also provides a :py:mod:`tests.shortfuse` package that contains utility classes that you may find useful while testing your custom file system. You may want to use the following:

    - :py:class:`tests.shortfuse.mount` : Provides a simple way to start and control a Python subprocess that runs FUSE

    - :py:class:`tests.shortfuse.integration.TestFuse` : Provides basic utilities for your tests such as generating files and random content

    - :py:class:`tests.shortfuse.integration.TestFUSEDirectory` : Define basic tests that a custom filesystem should pass. The inheriting class can determine if the tests should be run or not

    - :py:class:`tests.shortfuse.concurrency.TestFUSEConcurrency` : Define basic concurrency tests that a custom filesystem should pass. The inheriting class can determine if the tests should be run or not


Installation
------------

To install the authproxy server, run:

.. code-block:: bash

    pip install shortfuse
