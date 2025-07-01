import os
import json
import tarfile
from colorama import init as colorama_init, Fore, Style
from command_constants import ALLOWED_TOP_LEVEL, ALLOWED_SRC_EXT

def validate_project() -> dict | None:
    """Ensure watkit.json exists and is readable."""
    if not os.path.exists("watkit.json"):
        print(f"{Fore.RED}⛌ watkit.json not found. are you in a watkit project?{Style.RESET_ALL}")
        return None

    with open("watkit.json") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            print(f"{Fore.RED}⛌ invalid watkit.json format{Style.RESET_ALL}")
            return None

def build_archive_name(name: str, version: str) -> str:
    """
    Build the archive name for the project.
    """
    return os.path.join("dist", f"{name}-{version}.watpkg")

def add_project_files(tar: tarfile.TarFile) -> None:
    """
    Add all allowed top-level files to the archive.
    """
    for filename in ALLOWED_TOP_LEVEL:
        if os.path.exists(filename):
            tar.add(filename)

def add_src_files(tar: tarfile.TarFile) -> None:
    """
    Add all .wat files in the src/ directory to the archive.
    """
    if not os.path.exists("src"):
        return
    for root, _, files in os.walk("src"):
        for file in files:
            if os.path.splitext(file)[1] in ALLOWED_SRC_EXT:
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, start=".")
                tar.add(full_path, arcname=arcname)
            else:
                print(f"{Fore.YELLOW}ⓘ skipping disallowed file in src/: {file}{Style.RESET_ALL}")

def package_project(config: dict) -> None:
    """
    Package the project into a watpkg archive.
    """
    name = config.get("name", "unnamed")
    version = config.get("version", "0.0.0")
    archive_path = build_archive_name(name, version)

    os.makedirs("dist", exist_ok=True)

    print(f"✰creating package: {os.path.basename(archive_path)}✰")

    with tarfile.open(archive_path, "w:gz") as tar:
        add_project_files(tar)
        add_src_files(tar)

    print(f"{Fore.GREEN} ✓ package created at {archive_path}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}→ ready to be uploaded in the future{Style.RESET_ALL}\n")

def run():
    """
    Publish the project to the watkit registry.
    """
    colorama_init()
    config = validate_project()
    if config:
        package_project(config)

