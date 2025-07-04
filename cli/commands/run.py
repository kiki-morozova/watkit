import os
import json
import argparse
from colorama import init as colorama_init, Fore, Style

from command_constants import PKG_DIR
from commands.run_func_utils.js_handler import generate_js_runner
from commands.run_func_utils.rust_handler import generate_rust_stub
from commands.run_func_utils.import_handler_helpers import (
    resolve_recursive_imports,
    validate_modules,
    compile_wat,
    discover_bundled_dependencies
)

def run(args: argparse.Namespace) -> None:
    colorama_init()

    if not os.path.exists("watkit.json"):
        print(f"{Fore.RED}⛌ watkit.json not found.{Style.RESET_ALL}")
        return

    try:
        with open("watkit.json") as f:
            config = json.load(f)
    except json.JSONDecodeError:
        print(f"{Fore.RED}⛌ invalid watkit.json format{Style.RESET_ALL}")
        return

    wat_path = config.get("main", "src/main.wat")
    wasm_path = config.get("output", "dist/main.wasm")

    if not os.path.exists(wat_path):
        print(f"{Fore.RED}⛌ source file not found: {wat_path}{Style.RESET_ALL}")
        return

    print(f"✰ compiling {wat_path} → {wasm_path} ✰")

    try:
        imports = resolve_recursive_imports(wat_path, PKG_DIR)
        if not validate_modules(imports, PKG_DIR):
            print(f"{Fore.RED}⛌ missing dependencies in pkg/. Try installing with `watkit install <package>`{Style.RESET_ALL}")
            return

        compile_wat(wat_path, wasm_path)

        # Build module path map: mod name → path/to/pkg/<module>/dist/main.wasm
        module_paths = {}
        for imp in imports:
            mod = imp["module"]
            # Handle package imports (those starting with PKG_DIR prefix)
            if mod.startswith(PKG_DIR + "/"):
                # Strip PKG_DIR prefix if present in module name
                if mod.startswith(PKG_DIR + "/"):
                    mod_name = mod[len(PKG_DIR + "/"):]  # Remove PKG_DIR prefix
                else:
                    mod_name = mod
                
                mod_path = os.path.join(PKG_DIR, mod_name, "dist", "main.wasm")
                module_paths[mod] = mod_path
                
                # Discover bundled dependencies from this package
                package_path = os.path.join(PKG_DIR, mod_name)
                bundled_deps = discover_bundled_dependencies(package_path)
                for dep in bundled_deps:
                    if dep != "dist/main.wasm":  # Skip the main module itself
                        # Extract the dependency name (e.g., "dist/add1.wasm" -> "add1")
                        dep_name = os.path.splitext(os.path.basename(dep))[0]
                        dep_path = os.path.join(package_path, dep)
                        module_paths[dep_name] = dep_path
                        print(f"✰ discovered bundled dependency: {dep_name} → {dep_path} ✰")
            else:
                # Handle local imports (like "add1")
                local_wat_path = f"src/{mod}.wat"
                local_wasm_path = f"dist/{mod}.wasm"
                
                if os.path.exists(local_wat_path):
                    print(f"✰ compiling local import {local_wat_path} → {local_wasm_path} ✰")
                    compile_wat(local_wat_path, local_wasm_path)
                    module_paths[mod] = local_wasm_path
                else:
                    print(f"{Fore.RED}⛌ local import not found: {local_wat_path}{Style.RESET_ALL}")
                    return

        runner_dir = "dist"
        os.makedirs(runner_dir, exist_ok=True)
        runner_path = os.path.join(runner_dir, {
            "js": "run.mjs",
            "rust": "run.rs"
        }[args.lang])

        if args.lang == "js":
            generate_js_runner(runner_path, wasm_path, imports, module_paths)
            print(f"{Fore.GREEN}→ to run: node {runner_path}{Style.RESET_ALL}\n")
        elif args.lang == "rust":
            generate_rust_stub(runner_path, wasm_path, imports, module_paths)
            print(f"{Fore.GREEN}→ compile with: rustc {runner_path}{Style.RESET_ALL}\n")
        else:
            print(f"{Fore.RED}⛌ unsupported language: {args.lang}{Style.RESET_ALL}")

    except Exception as e:
        print(f"{Fore.RED}⛌ build failed: {e}{Style.RESET_ALL}")
