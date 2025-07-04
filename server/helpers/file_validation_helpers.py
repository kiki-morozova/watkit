import tarfile
import os

MAX_FILE_COUNT = 200
MAX_FILE_SIZE = 10 * 1024 * 1024

def is_within_directory(directory: str, target: str) -> bool:
    """Prevent directory traversal"""
    abs_dir = os.path.abspath(directory)
    abs_target = os.path.abspath(target)
    return os.path.commonprefix([abs_dir, abs_target]) == abs_dir

def safe_extract_tar(tar: tarfile.TarFile, path: str) -> None:
    """
    Extract the tar file to the destination directory safely. Checks size and file count.
    """
    members = tar.getmembers()

    if len(members) > MAX_FILE_COUNT:
        raise ValueError("Too many files in archive")

    for member in members:
        if member.size > MAX_FILE_SIZE:
            raise ValueError(f"File too large: {member.name}")

        extracted_path = os.path.join(path, member.name)
        if not is_within_directory(path, extracted_path):
            raise ValueError(f"Unsafe path in archive: {member.name}")

    tar.extractall(path=path)
