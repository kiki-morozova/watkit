import os
import json
import tarfile
import requests
from colorama import init as colorama_init, Fore, Style
from command_constants import ALLOWED_TOP_LEVEL, ALLOWED_SRC_EXT

CONFIG_PATH = os.path.expanduser("~/.watkit/config.json")
COOKIE_PATH = os.path.expanduser("~/.watkit/cookies.json")
SERVER_URL = "https://watkit-7omq2a.fly.dev"


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

    print(f"{Fore.GREEN} ✓ package created at {archive_path}{Style.RESET_ALL}")


def load_token() -> str | None:
    if not os.path.exists(COOKIE_PATH):
        print(f"{Fore.RED}✘ Not logged in. Please run `watkit login` first.{Style.RESET_ALL}")
        return None
    try:
        with open(COOKIE_PATH) as f:
            data = json.load(f)
            return data.get("watkit_token")
    except Exception:
        return None


def run():
    colorama_init()

    config = validate_project()
    if not config:
        return

    name = config.get("name")
    version = config.get("version")
    archive_path = build_archive_name(name, version)

    # Step 1: Build .watpkg
    package_project(config, archive_path)

    # Step 2: Load token
    token = load_token()
    if not token:
        print(f"{Fore.RED}✘ Cannot publish without login.{Style.RESET_ALL}")
        return

    # Step 3: Upload to /publish
    with open(archive_path, "rb") as f:
        files = {"watpkg_file": (os.path.basename(archive_path), f)}
        data = {"name": name, "version": version}
        cookies = {"watkit_token": token}

        print(f"{Fore.CYAN}⇨ Uploading package to {SERVER_URL}/publish...{Style.RESET_ALL}")
        try:
            response = requests.post(f"{SERVER_URL}/publish", data=data, files=files, cookies=cookies)
            if response.status_code == 200:
                print(f"{Fore.GREEN}✓ Published {name}v{version} successfully!{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}✘ Publish failed: {response.status_code} {response.text}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}✘ Error publishing: {e}{Style.RESET_ALL}")