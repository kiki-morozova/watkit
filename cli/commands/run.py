import os
import json
import re
import subprocess
import shutil
from typing import Dict, List
from colorama import init as colorama_init, Fore, Style
from command_constants import MODULES_DIR

def parse_imports_from_wat(wat_path: str) -> List[Dict[str, str]]:
    """
    Parse the imports from the main WAT file.
    Args:
        wat_path: str - path to the WAT file
    Returns:
        List[Dict[str, str]] - list of imports from the main WAT file
    """
    imports = []
    with open(wat_path, "r") as f:
        for line in f:
            match = re.match(r'\s*\(import\s+"([^"]+)"\s+"([^"]+)"', line)
            if match:
                imports.append({"module": match.group(1), "name": match.group(2)})
    return imports

def validate_modules(imports: List[Dict[str, str]]) -> bool:
    """
    Validate that all modules imported in the main WAT file exist.
    Args:
        imports: List[Dict[str, str]] - list of imports from the main WAT file
    Returns:
        bool - True if all modules exist, False otherwise
    """
    success = True
    for imp in imports:
        mod_path = os.path.join(MODULES_DIR, imp["module"], "dist", "main.wasm")
        if not os.path.exists(mod_path):
            print(f"{Fore.RED}⛌ missing module: {imp['module']} at {mod_path}{Style.RESET_ALL}")
            success = False
    return success

def generate_js_runner(output_path: str, main_module_path: str, imports: List[Dict[str, str]]) -> None:
    """
    Generate a JS runner that imports the WASM modules in preparation for running exported functions.
    Args:
        output_path: str - path to the output JS file
        main_module_path: str - path to the main WAT file
        imports: List[Dict[str, str]] - list of imports from the main WAT file
    """
    modules = {}
    for imp in imports:
        mod = imp["module"]
        modules.setdefault(mod, set()).add(imp["name"])

    with open(output_path, "w") as f:
        f.write("import fs from 'node:fs/promises';\n\n")

        for mod in modules:
            f.write(f"const {mod}Wasm = await fs.readFile('{MODULES_DIR}/{mod}/dist/main.wasm');\n")
            f.write(f"const {mod} = await WebAssembly.instantiate({mod}Wasm);\n\n")

        f.write(f"const mainWasm = await fs.readFile('{main_module_path}');\n")
        f.write("const main = await WebAssembly.instantiate(mainWasm, {\n")
        for i, (mod, funcs) in enumerate(modules.items()):
            exports = ", ".join([f"{fn}: {mod}.instance.exports.{fn}" for fn in funcs])
            comma = "," if i < len(modules) - 1 else ""
            f.write(f"  {mod}: {{ {exports} }}{comma}\n")
        f.write("});\n")

    print(f"{Fore.GREEN}✓ JS runner written to {output_path}{Style.RESET_ALL}")

def compile_wat(src: str, dest: str) -> None:
    """
    Compile the WAT file to a WASM binary.
    Args: 
        src: str - path to the WAT file
        dest: str - path to the output WASM binary
    """
    if not shutil.which("wat2wasm"):
        raise RuntimeError("wat2wasm not found in PATH")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    result = subprocess.run(["wat2wasm", src, "-o", dest], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    print(f"{Fore.GREEN}✓ compiled {src} → {dest}{Style.RESET_ALL}")

def run():
    """
    Compile (if needed) the main WAT file in a package and resolve imports, making a JS runner.
    """
    colorama_init()

    # check if we're in a watkit project
    if not os.path.exists("watkit.json"):
        print(f"{Fore.RED}⛌ watkit.json not found.{Style.RESET_ALL}")
        return

    with open("watkit.json") as f:
        config = json.load(f)

    wat_path = config.get("main", "src/main.wat")
    wasm_path = config.get("output", "dist/main.wasm")
    runner_path = "dist/run.mjs"

    if not os.path.exists(wat_path):
        print(f"{Fore.RED}⛌ source file not found: {wat_path}{Style.RESET_ALL}")
        return

    imports = parse_imports_from_wat(wat_path)

    if not validate_modules(imports):
        print(f"{Fore.RED}⛌ missing module dependencies. aborting.{Style.RESET_ALL}")
        return

    try:
        compile_wat(wat_path, wasm_path)
    except Exception as e:
        print(f"{Fore.RED}⛌ compilation failed: {e}{Style.RESET_ALL}")
        return

    os.makedirs("dist", exist_ok=True)
    generate_js_runner(runner_path, wasm_path, imports)
    print(f"{Fore.GREEN}→ to run: node {runner_path}{Style.RESET_ALL}\n")
