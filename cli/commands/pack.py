import os
import json
import tarfile
from colorama import init as colorama_init, Fore, Style
from command_constants import ALLOWED_TOP_LEVEL, ALLOWED_SRC_EXT


def validate_project() -> dict | None:
    if not os.path.exists("watkit.json"):
        print(f"{Fore.RED}⛌ watkit.json not found. are you in a watkit project?{Style.RESET_ALL}")
        return None
    try:
        with open("watkit.json") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"{Fore.RED}⛌ invalid watkit.json format{Style.RESET_ALL}")
        return None


def build_archive_name(name: str, version: str) -> str:
    return os.path.join("dist", f"{name}-{version}.watpkg")


def add_project_files(tar: tarfile.TarFile) -> None:
    for filename in ALLOWED_TOP_LEVEL:
        if os.path.exists(filename):
            tar.add(filename)


def add_src_files(tar: tarfile.TarFile) -> None:
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


def add_compiled_files(tar: tarfile.TarFile) -> None:
    """Add compiled .wasm files to the package."""
    if not os.path.exists("dist"):
        return
    for root, _, files in os.walk("dist"):
        for file in files:
            if file.endswith(".wasm"):
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, start=".")
                tar.add(full_path, arcname=arcname)
                print(f"✰ bundling compiled dependency: {arcname} ✰")


def package_project(config: dict, archive_path: str) -> None:
    os.makedirs("dist", exist_ok=True)
    print(f"✰creating package: {os.path.basename(archive_path)}✰")

    with tarfile.open(archive_path, "w:gz") as tar:
        add_project_files(tar)
        add_src_files(tar)
        add_compiled_files(tar)  # Include compiled dependencies

    print(f"{Fore.GREEN}✓ package created at {archive_path}{Style.RESET_ALL}")


def run():
    colorama_init()

    config = validate_project()
    if not config:
        return

    name = config.get("name")
    version = config.get("version")
    if not name or not version:
        print(f"{Fore.RED}⛌ watkit.json must include 'name' and 'version'{Style.RESET_ALL}")
        return

    archive_path = build_archive_name(name, version)
    package_project(config, archive_path)
