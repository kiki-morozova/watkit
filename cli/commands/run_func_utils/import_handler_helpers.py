import os
import re
import shutil
import subprocess
from colorama import Fore, Style

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

def resolve_recursive_imports(wat_path: str, modules_dir: str, seen=None) -> list[dict[str, str]]:
    """
    Resolve all transitive imports from a WAT file, recursively.
    Args:
        wat_path: str - path to the WAT file
        modules_dir: str - path to the modules directory
        seen: set of seen (module, name) pairs to prevent cycles
    Returns:
        List[Dict[str, str]] - all resolved imports
    """
    if seen is None:
        seen = set()

    imports = parse_imports_from_wat(wat_path)
    resolved = []

    for imp in imports:
        key = (imp['module'], imp['name'])
        if key in seen:
            continue
        seen.add(key)
        resolved.append(imp)

        dep_wat = os.path.join(modules_dir, imp["module"], "src", "main.wat")
        if os.path.exists(dep_wat):
            resolved.extend(resolve_recursive_imports(dep_wat, modules_dir, seen))

    return resolved

def discover_bundled_dependencies(package_path: str) -> list[str]:
    """
    Discover bundled .wasm dependencies in an installed package.
    Args:
        package_path: str - path to the installed package directory
    Returns:
        List[str] - list of bundled .wasm file paths relative to package root
    """
    bundled_deps = []
    if os.path.exists(package_path):
        for root, _, files in os.walk(package_path):
            for file in files:
                if file.endswith(".wasm"):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, package_path)
                    bundled_deps.append(rel_path)
    return bundled_deps

def validate_modules(imports: list[dict[str, str]], PKG_DIR: str) -> bool:
    """
    Validate that all package modules imported in the main WAT file exist.
    Args:
        imports: List[Dict[str, str]] - list of imports from the main WAT file
        PKG_DIR: str - path to the modules directory
    Returns:
        bool - True if all package modules exist, False otherwise
    """
    success = True
    for imp in imports:
        module_name = imp["module"]
        # Only validate imports that start with PKG_DIR prefix (package imports)
        if module_name.startswith(PKG_DIR + "/"):
            # Strip PKG_DIR prefix to get the actual package name
            package_name = module_name[len(PKG_DIR + "/"):]
            mod_path = os.path.join(PKG_DIR, package_name, "dist", "main.wasm")
            if not os.path.exists(mod_path):
                print(f"{Fore.RED}⛌ missing module: {imp['module']} at {mod_path}{Style.RESET_ALL}")
                success = False
        # Local imports (like "add1") are not validated here - they should be compiled separately
    return success

def compile_wat(src: str, dest: str) -> None:
    """
    Compile a WAT file to a WASM binary.
    Args:
        src: str - path to the WAT file
        dest: str - path to the output WASM file
    """
    if not shutil.which("wat2wasm"):
        raise RuntimeError("wat2wasm not found in PATH")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    result = subprocess.run(["wat2wasm", src, "-o", dest], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    print(f"{Fore.GREEN}✓ compiled {src} → {dest}{Style.RESET_ALL}")