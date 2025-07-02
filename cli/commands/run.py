import os
import json
import argparse

from colorama import init as colorama_init, Fore, Style
from command_constants import MODULES_DIR
from commands.run_func_utils.js_handler import generate_js_runner
from commands.run_func_utils.rust_handler import generate_rust_stub
from commands.run_func_utils.import_handler_helpers import resolve_recursive_imports, validate_modules, compile_wat

def run(args: argparse.Namespace) -> None:
    """
    Compile the main WAT file in a package and resolve imports, making a JS, C, or Rust runner.
    Args:
        args: argparse.Namespace - the arguments passed to the run command, specifically the language flag
    """
    colorama_init()

    if not os.path.exists("watkit.json"):
        print(f"{Fore.RED}⛌ watkit.json not found.{Style.RESET_ALL}")
        return

    with open("watkit.json") as f:
        config = json.load(f)

    wat_path = config.get("main", "src/main.wat")
    wasm_path = config.get("output", "dist/main.wasm")
    runner_dir = "dist"
    os.makedirs(runner_dir, exist_ok=True)

    runner_path = {
        "js": os.path.join(runner_dir, "run.mjs"),
        "c": os.path.join(runner_dir, "run.c"),
        "rust": os.path.join(runner_dir, "run.rs")
    }[args.lang]

    if not os.path.exists(wat_path):
        print(f"{Fore.RED}⛌ source file not found: {wat_path}{Style.RESET_ALL}")
        return

    imports = resolve_recursive_imports(wat_path, MODULES_DIR)
    if not validate_modules(imports, MODULES_DIR):
        print(f"{Fore.RED}⛌ missing module dependencies. aborting.{Style.RESET_ALL}")
        return

    try:
        compile_wat(wat_path, wasm_path)
    except Exception as e:
        print(f"{Fore.RED}⛌ compilation failed: {e}{Style.RESET_ALL}")
        return

    if args.lang == "js":
        generate_js_runner(runner_path, wasm_path, imports, MODULES_DIR)
        print(f"{Fore.GREEN}→ to run: node {runner_path}{Style.RESET_ALL}\n")
    elif args.lang == "rust":
        generate_rust_stub(runner_path, wasm_path, imports, MODULES_DIR)
        print(f"{Fore.GREEN}→ compile with: rustc dist/run.rs{Style.RESET_ALL}\n")