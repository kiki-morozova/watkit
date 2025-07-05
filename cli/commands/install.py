import os
import shutil
import json
import requests
from colorama import init as colorama_init, Fore, Style

from command_constants import PKG_DIR
from commands.run_func_utils.import_handler_helpers import resolve_recursive_imports, compile_wat, validate_modules
from commands.run_func_utils.validation_helpers import safe_extract_tar

CONFIG_PATH = os.path.expanduser("~/watkit/config.json")


def load_config():
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except Exception:
        return {}


def fetch_from_registry(url: str, stream=False) -> requests.Response:
    resp = requests.get(url, stream=stream)
    if resp.status_code != 200:
        raise Exception(f"Failed to fetch: {url} → {resp.status_code}")
    return resp


def run(name_with_version: str, seen=None) -> None:
    """
    Install a package from the registry, using LATEST version resolution if necessary.
    """
    colorama_init()
    config = load_config()
    base_url = config.get("registry_url")
    if not base_url:
        print(f"{Fore.RED}✘ Missing 'registry_url' in config.{Style.RESET_ALL}")
        return

    # Parse name and optional version
    if "v" in name_with_version:
        name, version = name_with_version.split("v", 1)
    else:
        name, version = name_with_version, "latest"

    if seen is None:
        seen = set()
    if name_with_version in seen:
        return
    seen.add(name_with_version)

    print(f"\n✰ installing {name}v{version}... ✰")

    try:
        # Step 1: Resolve latest version if needed
        if version == "latest":
            latest_url = f"{base_url}/{name}/LATEST"
            latest_resp = fetch_from_registry(latest_url)
            version = latest_resp.text.strip()
            print(f"{Fore.YELLOW}➜ Resolved {name}vlatest to {version}{Style.RESET_ALL}")

        archive_filename = f"{name}-{version}.watpkg"
        manifest_url = f"{base_url}/{name}/{version}/watkit.json"
        archive_url = f"{base_url}/{name}/{version}/{archive_filename}"

        # Step 2: Download manifest and archive
        manifest = fetch_from_registry(manifest_url).json()
        archive_resp = fetch_from_registry(archive_url, stream=True)

        # Step 3: Save archive locally
        archive_path = os.path.join("/tmp", archive_filename)
        with open(archive_path, "wb") as f:
            for chunk in archive_resp.iter_content(chunk_size=8192):
                f.write(chunk)

        # Step 4: Extract to pkg/modulevversion
        install_path = os.path.join(PKG_DIR, f"{name}v{version}")
        os.makedirs(PKG_DIR, exist_ok=True)

        safe_extract_tar(archive_path, install_path)

        # Step 5: Validate dependencies (but don't recompile since .wasm files are bundled)
        config_path = os.path.join(install_path, "watkit.json")
        with open(config_path) as f:
            manifest = json.load(f)

        # Check if main.wasm already exists (bundled)
        main_wasm_path = os.path.join(install_path, manifest["output"])
        if not os.path.exists(main_wasm_path):
            # Only compile if .wasm files weren't bundled
            print(f"{Fore.YELLOW}➜ Compiling {name} from source...{Style.RESET_ALL}")
            wat_path = os.path.join(install_path, manifest["main"])
            compile_wat(wat_path, main_wasm_path)
        else:
            print(f"{Fore.GREEN}✓ Using bundled compiled files{Style.RESET_ALL}")

        print(f"{Fore.GREEN}✓ installed {name}v{version} → {main_wasm_path}{Style.RESET_ALL}\n")

        # Track successful download
        try:
            # Use localhost server for tracking (since CLI downloads from S3)
            track_url = "http://localhost:8000/track-download"
            requests.post(track_url, params={"name": name, "version": version})
        except Exception as e:
            print(f"{Fore.YELLOW}Warning: Could not track download: {e}{Style.RESET_ALL}")

    except Exception as e:
        print(f"{Fore.RED}⛌ install failed: {e}{Style.RESET_ALL}")
        shutil.rmtree(os.path.join(PKG_DIR, f"{name}v{version}"), ignore_errors=True)
