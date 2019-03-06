import os
import random
from multiprocessing import Pool

from shortfuse_test.integration import retry_assertion
from shortfuse_test.fixtures import build_random_string


def create_delete_file(filename, content=None, unlink=True):
    """
    Create, then delete a file. It is meant to be called within a multiprocessing Process. The operation is deemed
    successful if the file could be truncated and written to. The ability to remove it at the end is not guaranteed
    since another process could have gotten to it first.

    Args:
        filename (str): The name of the file to create.
        content (str): The content of the file
        unlink (bool): If set to true, the file is deleted after being created.

    Returns:
        bool: True if the operation succeeded, False otherwise.
    """
    try:
        with open(filename, 'w+') as f:
            if content is not None:
                f.write(content)
    except:
        return False
    if not unlink:
        return
    try:
        os.unlink(filename)
    finally:
        return True


def create_delete_dir(dirname, unlink=True):
    """
    Create, then delete a file. It is meant to be called within a multiprocessing Process. The operation is deemed
    successful if the file could be truncated and written to. The ability to remove it at the end is not guaranteed
    since another process could have gotten to it first.

    Args:
        filename (str): The name of the file to create.
        content (str): The content of the file
        unlink (bool): If set to true, the file is deleted after being created.

    Returns:
        bool: True if the operation succeeded, False otherwise.
    """
    try:
        os.mkdir(dirname)
    except:
        return True
    if not unlink:
        return
    try:
        os.rmdir(dirname)
    except:
        return False
    return True


def create_delete_file_test(root_path):
    pool = Pool(8)
    results = []

    file_paths = [os.path.join(root_path, "create_delete_file_%s" % index) for index in range(0, 10)]
    root_stats = os.stat(root_path)
    for iteration in range(0, 10000):
        file_path = file_paths[random.randint(0, len(file_paths) - 1)]
        results.append(pool.apply_async(
            create_delete_file,
            (file_path,)
        ))
    pool.close()
    pool.join()

    u_root_stats = os.stat(root_path)
    retry_assertion(lambda: root_stats.st_nlink == u_root_stats.st_nlink)
    for result in results:
        assert result


def create_file_test(root_path):
    pool = Pool(8)
    results = []

    file_paths = [os.path.join(root_path, "create_delete_file_%s" % index) for index in range(0, 10)]
    file_contents = [build_random_string(1024 * 200) for _ in range(0, 10)]

    root_stats = os.stat(root_path)
    for iteration in range(0, 10000):
        file_path = file_paths[random.randint(0, len(file_paths) - 1)]
        file_content = file_contents[random.randint(0, len(file_contents) - 1)]
        results.append(pool.apply_async(
            create_delete_file,
            (file_path, file_content, False)
        ))
    pool.close()
    pool.join()

    u_root_stats = os.stat(root_path)
    retry_assertion(lambda: root_stats.st_nlink + len(file_paths) == u_root_stats.st_nlink)
    for result in results:
        assert result
    for file_path in file_paths:
        with open(file_path, 'r') as f:
            assert f.read() in file_contents
        os.unlink(file_path)


def create_delete_dir_test(root_path):
    pool = Pool(8)
    results = []

    dir_paths = [os.path.join(root_path, "create_delete_dir_%s" % index) for index in range(0, 10)]
    root_stats = os.stat(root_path)
    for iteration in range(0, 10000):
        file_path = dir_paths[random.randint(0, len(dir_paths) - 1)]
        results.append(pool.apply_async(
            create_delete_dir,
            (file_path,)
        ))
    pool.close()
    pool.join()

    u_root_stats = os.stat(root_path)
    retry_assertion(lambda: root_stats.st_nlink == u_root_stats.st_nlink)
    for result in results:
        assert result
