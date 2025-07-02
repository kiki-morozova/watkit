import os
import shutil
from colorama import init as colorama_init, Fore, Style

from command_constants import MODULES_DIR, LOCAL_REGISTRY, REQUIRED_FIELDS, ALLOWED_OPTIONAL_FIELDS
from commands.run_func_utils.import_handler_helpers import (
    resolve_recursive_imports,
    compile_wat
)
from commands.run_func_utils.validation_helpers import safe_extract_tar, validate_config


def run(package_name: str, seen=None) -> None:
    """
    Install a package from the local registry, resolving dependencies recursively.
    """
    colorama_init()

    if seen is None:
        seen = set()
    if package_name in seen:
        return
    seen.add(package_name)

    print(f"\n✰ installing {package_name}... ✰")
    archive_name = f"{package_name}.watpkg"
    archive_path = os.path.join("/tmp", archive_name)
    registry_path = os.path.join(os.path.dirname(__file__), "..", LOCAL_REGISTRY)
    module_path = os.path.join(MODULES_DIR, package_name)

    local_source = os.path.join(registry_path, archive_name)
    if not os.path.exists(local_source):
        print(f"{Fore.RED}⛌ package not found in local registry: {archive_name}{Style.RESET_ALL}")
        return
    shutil.copyfile(local_source, archive_path)

    os.makedirs(MODULES_DIR, exist_ok=True)

    try:
        safe_extract_tar(archive_path, module_path)
        config_path = os.path.join(module_path, "watkit.json")
        config = validate_config(config_path)

        wat_path = os.path.join(module_path, config["main"])
        dependencies = resolve_recursive_imports(wat_path, MODULES_DIR)
        for dep in dependencies:
            run(dep["module"], seen=seen)

        compile_wat(wat_path, os.path.join(module_path, config["output"]))

    except Exception as e:
        print(f"{Fore.RED}⛌ install failed: {e}{Style.RESET_ALL}")
        shutil.rmtree(module_path, ignore_errors=True)
        return

    print(f"{Fore.GREEN}✓ installed {package_name} → {config['output']}{Style.RESET_ALL}\n")