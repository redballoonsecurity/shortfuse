import logging
import os
import time
import xattr
from multiprocessing import Process, Event
from threading import Thread

EVENT_LOGGER = logging.getLogger("shortfuse_test.mount.event")


class FuseProcessEventManager:
    """
    The fs manager interacts with the root instance Node within a mounted filesystem. It waits for a do event,
    perform the work, clear the do event and set the done event.

    This class should be created along the FUSE filesystem in the child process.
    """
    def __init__(self, fs, do_event, done_event):
        self._fs = fs
        self._do_event = do_event
        self._done_event = done_event
        self._thread = Thread(target=self._run)

    def start(self):
        self._thread.start()

    def _run(self):
        while True:
            # Wait for the parent process to request a flush
            self._do_event.wait()
            # Do the work once notified. Parent process is stuck on waiting for the flushed_event
            self._execute()
            EVENT_LOGGER.debug("Processed an event")
            # Reset the flag until another flush is requested by the parent process
            self._do_event.clear()
            # Notify the parent process that the flush is done. The parent process is responsible for reseting that flag
            self._done_event.set()

    def _execute(self):
        pass


class FuseEventManager:
    def __init__(self):
        self.do_event = Event()
        self.done_event = Event()

    def signal(self):
        self.do_event.set()
        self.done_event.wait()
        self.done_event.clear()


class FuseOS:
    def _callback(self):
        pass

    def _execute_op(self, callback):
        try:
            self._callback()
            result = callback()
            return result
        except Exception as e:
            self._callback()
            raise e

    def chmod(self, path, mode):
        if hasattr(os, 'lchmod'):
            return self._execute_op(lambda: os.lchmod(path, mode))
        return self._execute_op(lambda: os.chmod(path, mode))

    def chown(self, path, uid, gid):
        if hasattr(os, 'lchown'):
            return self._execute_op(lambda: os.lchown(path, uid, gid))
        return self._execute_op(lambda: os.chown(path, uid, gid))

    def delete_xattr(self, path, key):
        def _execute():
            attrs = xattr.xattr(path)
            del attrs[key]
        return self._execute_op(lambda: _execute())

    def get_xattr(self, path, key):
        return self._execute_op(lambda: dict(xattr.xattr(path)).get(key, None))

    def get_xattrs(self, path):
        return self._execute_op(lambda: dict(xattr.xattr(path)))

    def listdir(self, path):
        return self._execute_op(lambda: os.listdir(path))

    def mkdir(self, path, mode):
        return self._execute_op(lambda: os.mkdir(path, mode))

    def open(self, path, mode):
        return self._execute_op(lambda: open(path, mode))

    def readlink(self, path):
        return self._execute_op(lambda: os.readlink(path))

    def rmdir(self, path):
        return self._execute_op(lambda: os.rmdir(path))

    def set_xattr(self, path, key, value):
        def _execute():
            attrs = xattr.xattr(path)
            attrs[key] = value
        return self._execute_op(lambda: _execute())

    def stat(self, path):
        if hasattr(os, 'lstat'):
            return self._execute_op(lambda: os.lstat(path))
        return self._execute_op(lambda: os.stat(path))

    def symlink(self, source, link_name):
        return self._execute_op(lambda: os.symlink(source, link_name))

    def utime(self, path, times):
        return self._execute_op(lambda: os.utime(path, times))

    def unlink(self, path):
        return self._execute_op(lambda: os.unlink(path))


class FuseManager:
    def __init__(self, entry, mount_path, *args):
        self._fuse_process = Process(
            target=entry,
            args=[mount_path] + list(args)
        )
        self.mount_path = mount_path

    def start(self):
        self._fuse_process.start()
        time.sleep(1)

    def stop(self):
        self._fuse_process.terminate()
        self._fuse_process.join()
