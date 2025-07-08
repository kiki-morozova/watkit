import os
import shutil
import json
import requests
import re
from colorama import init as colorama_init, Fore, Style

from command_constants import PKG_DIR, SERVER_URL
from commands.run_func_utils.import_handler_helpers import compile_wat
from commands.run_func_utils.validation_helpers import safe_extract_tar

CONFIG_PATH = os.path.expanduser("~/.watkit/config.json")

def load_config():
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except Exception:
        return {}


def fetch_from_registry(url: str, stream=False) -> requests.Response:
    """
    Fetch a file from the registry.
    Args:
        url: str - URL to fetch
        stream: bool - whether to stream the response
    Returns:
        requests.Response - response from the registry
    """
    print("url", url)
    resp = requests.get(url, stream=stream)
    if resp.status_code != 200:
        raise Exception(f"Failed to fetch: {url} → {resp.status_code}")
    return resp


def parse_imports_from_wat(wat_path: str) -> list[dict[str, str]]:
    """
    Parse the imports from a WAT file.
    Args:
        wat_path: str - path to the WAT file
    Returns:
        List[Dict[str, str]] - list of imports (module/name pairs)
    """
    imports = []
    with open(wat_path, "r") as f:
        for line in f:
            match = re.match(r'\s*\(import\s+"([^"]+)"\s+"([^"]+)"', line)
            if match:
                imports.append({"module": match.group(1), "name": match.group(2)})
    return imports


def extract_package_dependencies(manifest: dict, install_path: str) -> list[tuple[str, str]]:
    """
    Extract package dependencies from WAT files in the package.
    Args:
        manifest: dict - package manifest
        install_path: str - path where package is installed
    Returns:
        List[Tuple[str, str]] - list of (package_name, version) tuples
    """
    dependencies = []
    
    # Parse main WAT file
    main_wat_path = os.path.join(install_path, manifest["main"])
    if os.path.exists(main_wat_path):
        imports = parse_imports_from_wat(main_wat_path)
        for imp in imports:
            module_name = imp["module"]
            # Check if this is a package import (starts with "pkg/")
            if module_name.startswith("pkg/"):
                # Extract package name and version from "pkg/namevversion"
                pkg_part = module_name[4:]  # Remove "pkg/" prefix
                if "v" in pkg_part:
                    pkg_name, pkg_version = pkg_part.split("v", 1)
                    dependencies.append((pkg_name, pkg_version))
    
    # Also check other WAT files in src directory
    src_dir = os.path.join(install_path, "src")
    if os.path.exists(src_dir):
        for root, _, files in os.walk(src_dir):
            for file in files:
                if file.endswith(".wat"):
                    wat_path = os.path.join(root, file)
                    imports = parse_imports_from_wat(wat_path)
                    for imp in imports:
                        module_name = imp["module"]
                        if module_name.startswith("pkg/"):
                            pkg_part = module_name[4:]
                            if "v" in pkg_part:
                                pkg_name, pkg_version = pkg_part.split("v", 1)
                                dependencies.append((pkg_name, pkg_version))
    
    return list(set(dependencies))  # Remove duplicates


def run(name_with_version: str, seen=None) -> None:
    """
    Install a package from the registry, using LATEST version resolution if necessary.
    Handles recursive dependencies automatically.
    Args:
        name_with_version: str - name and version of the package to install
        seen: set - set of already installed packages
    Returns:
        None
    """
    colorama_init()
    config = load_config()
    base_url = config.get("registry_url")
    if not base_url:
        print(f"{Fore.RED}✘ Missing 'registry_url' in config.{Style.RESET_ALL}")
        return

    # Convert S3 static website URL to S3 REST API URL
    if "s3-website" in base_url:
        # Convert from: https://watkit-registry.s3-website-us-east-1.amazonaws.com
        # To: https://watkit-registry.s3.us-east-1.amazonaws.com
        base_url = base_url.replace("s3-website-", "s3.")

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

    # Track installed dependencies for cleanup on failure
    installed_deps = []
    
    try:
        # resolve latest version if none specified
        if version == "latest":
            latest_url = f"{base_url}/{name}/LATEST"
            latest_resp = fetch_from_registry(latest_url)
            version = latest_resp.text.strip()
            print(f"{Fore.YELLOW}➜ Resolved {name}vlatest to {version}{Style.RESET_ALL}")
   
        archive_filename = f"{name}-{version}.watpkg"
        manifest_url = f"{base_url}/{name}/{version}/watkit.json"
        archive_url = f"{base_url}/{name}/{version}/{archive_filename}"

        # grab manifest + archive
        manifest = fetch_from_registry(manifest_url).json()
        archive_resp = fetch_from_registry(archive_url, stream=True)

        # save archive locally in a tmp dir
        archive_path = os.path.join("/tmp", archive_filename)
        with open(archive_path, "wb") as f:
            for chunk in archive_resp.iter_content(chunk_size=8192):
                f.write(chunk)

        # extract to pkg/modulevversion
        install_path = os.path.join(PKG_DIR, f"{name}v{version}")
        os.makedirs(PKG_DIR, exist_ok=True)

        safe_extract_tar(archive_path, install_path)

        # extract dependencies recursively
        dependencies = extract_package_dependencies(manifest, install_path)
        for dep_name, dep_version in dependencies:
            dep_name_with_version = f"{dep_name}v{dep_version}"
            if dep_name_with_version not in seen:
                print(f"{Fore.CYAN}➜ Installing dependency: {dep_name_with_version}{Style.RESET_ALL}")
                try:
                    run(dep_name_with_version, seen)
                    installed_deps.append(dep_name_with_version)
                except Exception as e:
                    print(f"{Fore.RED}⛌ Failed to install dependency {dep_name_with_version}: {e}{Style.RESET_ALL}")
                    # clean up any partial installs
                    for installed_dep in installed_deps:
                        dep_install_path = os.path.join(PKG_DIR, installed_dep)
                        if os.path.exists(dep_install_path):
                            shutil.rmtree(dep_install_path)
                            print(f"{Fore.YELLOW}➜ Cleaned up failed dependency: {installed_dep}{Style.RESET_ALL}")
                    # clean up the main package
                    if os.path.exists(install_path):
                        shutil.rmtree(install_path)
                    raise Exception(f"Dependency installation failed: {e}")

        # validate dependencies (but don't recompile)
        config_path = os.path.join(install_path, "watkit.json")
        with open(config_path) as f:
            manifest = json.load(f)

        # check if main.wasm already exists (bundled)
        main_wasm_path = os.path.join(install_path, manifest["output"])
        if not os.path.exists(main_wasm_path):
            # compile if .wasm files weren't bundled
            print(f"{Fore.YELLOW}➜ Compiling {name} from source...{Style.RESET_ALL}")
            wat_path = os.path.join(install_path, manifest["main"])
            compile_wat(wat_path, main_wasm_path)
        else:
            print(f"{Fore.GREEN}✓ Using bundled compiled files{Style.RESET_ALL}")

        print(f"{Fore.GREEN}✓ installed {name}v{version} → {main_wasm_path}{Style.RESET_ALL}\n")

        # track successful download for *website metrics ooo shiny*
        try:
            # use watkit server for tracking (since CLI downloads from S3)
            track_url = f"{SERVER_URL}/track-download"
            requests.post(track_url, params={"name": name, "version": version})
        except Exception as e:
            print(f"{Fore.YELLOW}Warning: Could not track download: {e}{Style.RESET_ALL}")

    except Exception as e:
        print(f"{Fore.RED}⛌ install failed: {e}{Style.RESET_ALL}")
        # clean up the main package and any installed dependencies
        shutil.rmtree(os.path.join(PKG_DIR, f"{name}v{version}"), ignore_errors=True)
        for installed_dep in installed_deps:
            dep_install_path = os.path.join(PKG_DIR, installed_dep)
            shutil.rmtree(dep_install_path, ignore_errors=True)
        raise  # Re-raise the exception to propagate the error
