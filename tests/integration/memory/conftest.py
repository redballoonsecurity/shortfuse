import logging
import os

import pytest
from fuse import FUSE

from shortfuse.extra.memory import MemoryFileSystem
from shortfuse.operations import Shortfuse

from shortfuse_test.mount import FuseManager, FuseOS


@pytest.fixture(scope="module")
def fuse(temp_dir_module):
    fuse = FuseManager(mount_memory, temp_dir_module)
    fuse.start()
    yield fuse
    fuse.stop()


def mount_memory(path):
    FUSE(
        Shortfuse(MemoryFileSystem(
            0o777,
            os.geteuid(),
            os.getegid()
        )),
        path,
        raw_fi=True,
        foreground=True,
        entry_timeout=0,
        negative_timeout=0
    )