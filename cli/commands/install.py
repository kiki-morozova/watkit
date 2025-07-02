import os
import json
import tarfile
import shutil
import subprocess
from colorama import init as colorama_init
from colorama import Fore, Style
from command_constants import MODULES_DIR, LOCAL_REGISTRY, REQUIRED_FIELDS, ALLOWED_OPTIONAL_FIELDS

def run(package_name: str) -> None:
    """
    Install a package from the local registry.
    """
    colorama_init()

    print(f"\n✰ installing {package_name}... ✰")
    archive_name = f"{package_name}.watpkg"
    archive_path = os.path.join("/tmp", archive_name)
    registry_path = os.path.join(os.path.dirname(__file__), "..", LOCAL_REGISTRY)
    module_path = os.path.join(MODULES_DIR, package_name)

    # Simulate fetch from local registry
    local_source = os.path.join(registry_path, archive_name)
    if not os.path.exists(local_source):
        print(f"{Fore.RED}⛌ package not found in local registry: {archive_name}{Style.RESET_ALL}")
        return
    shutil.copyfile(local_source, archive_path)

    os.makedirs(MODULES_DIR, exist_ok=True)

    try:
        safe_extract_tar(archive_path, module_path)
        config = validate_config(os.path.join(module_path, "watkit.json"))
        compile_wat(os.path.join(module_path, config["main"]),
                    os.path.join(module_path, config["output"]))
    except Exception as e:
        print(f"{Fore.RED}⛌ install failed: {e}{Style.RESET_ALL}")
        shutil.rmtree(module_path, ignore_errors=True)
        return

    print(f"{Fore.GREEN}✓ installed {package_name} → {config['output']}{Style.RESET_ALL}\n")

def safe_extract_tar(tar_path: str, dest: str) -> None:
    """
    Extract the tar file to the destination directory.
    """
    with tarfile.open(tar_path, "r:gz") as tar:
        for member in tar.getmembers():
            member_path = os.path.join(dest, member.name)
            if not is_within_directory(dest, member_path):
                raise Exception(f"{Fore.RED}⛌ unsafe file path in archive: {member.name}{Style.RESET_ALL}")
        
        tar.extractall(dest)

def is_within_directory(directory: str, target: str) -> bool:
    """
    Check if the target is within the base directory.
    """
    abs_directory = os.path.abspath(directory)
    abs_target = os.path.abspath(target)
    return os.path.commonpath([abs_directory]) == os.path.commonpath([abs_directory, abs_target])

def validate_config(path: str) -> dict:
    """
    Validate the watkit.json file.
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

def compile_wat(src: str, dest: str) -> None:
    """
    Compile the WAT file to a WASM binary.
    """
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    result = subprocess.run(["wat2wasm", src, "-o", dest],
                            capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    print(f"{Fore.GREEN}✓ compiled {src} → {dest}{Style.RESET_ALL}")
