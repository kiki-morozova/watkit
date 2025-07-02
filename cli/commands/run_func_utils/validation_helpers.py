from colorama import Fore, Style
import tarfile
import os
import json

from command_constants import REQUIRED_FIELDS, ALLOWED_OPTIONAL_FIELDS

def safe_extract_tar(tar_path: str, dest: str) -> None:
    """
    Extract the tar file to the destination directory safely.
    """
    with tarfile.open(tar_path, "r:gz") as tar:
        for member in tar.getmembers():
            member_path = os.path.join(dest, member.name)
            if not is_within_directory(dest, member_path):
                raise Exception(f"{Fore.RED}⛌ unsafe file path in archive: {member.name}{Style.RESET_ALL}")
        tar.extractall(dest)


def is_within_directory(directory: str, target: str) -> bool:
    """
    Check if the target path is within the given base directory.
    """
    abs_directory = os.path.abspath(directory)
    abs_target = os.path.abspath(target)
    return os.path.commonpath([abs_directory]) == os.path.commonpath([abs_directory, abs_target])


def validate_config(path: str) -> dict:
    """
    Validate the watkit.json configuration file.
    """
    with open(path) as f:
        config = json.load(f)

    missing = REQUIRED_FIELDS - config.keys()
    if missing:
        raise ValueError(f"{Fore.RED}⛌ watkit.json missing required fields: {', '.join(missing)}{Style.RESET_ALL}")

    unknown = set(config.keys()) - (REQUIRED_FIELDS | ALLOWED_OPTIONAL_FIELDS)
    if unknown:
        raise ValueError(f"{Fore.RED}⛌ watkit.json contains unknown fields: {', '.join(unknown)}{Style.RESET_ALL}")

    return config
