import os
import json
from colorama import init as colorama_init, Fore, Style

def run(target_dir: str = ".") -> None:
    """
    Initialize a new watkit package in the given directory,
    with a default wat file, config, and readme.
    """
    colorama_init()
    print(f"✰ initializing new watkit package in {target_dir}... ✰")

    if not prepare_directory(target_dir):
        return

    create_project_structure(target_dir)
    create_watkit_config(target_dir)
    create_readme(target_dir)
    create_starter_wat(target_dir)

    print_success(target_dir)

def prepare_directory(target_dir: str) -> bool:
    """
    Create target directory if it doesn't exist and validate overwrite conditions.
    Returns True if it's safe to proceed, False if we should abort.
    """
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    config_path = os.path.join(target_dir, "watkit.json")
    wat_path = os.path.join(target_dir, "src", "main.wat")

    if os.path.exists(config_path):
        print(f"{Fore.YELLOW}ⓘ watkit.json already exists in that folder. aborting to prevent overwrite.{Style.RESET_ALL}")
        return False

    if os.path.exists(wat_path):
        print(f"{Fore.YELLOW}ⓘ src/main.wat already exists. aborting to prevent overwrite.{Style.RESET_ALL}")
        return False

    return True

def create_project_structure(target_dir: str) -> None:
    """
    Create the project structure in the target directory.
    """
    os.makedirs(os.path.join(target_dir, "src"), exist_ok=True)

def create_watkit_config(target_dir: str) -> None:
    """
    Create a watkit.json file in the target directory.
    """
    config = {
        "name": os.path.basename(os.path.abspath(target_dir)),
        "version": "0.1.0",
        "main": "src/main.wat",
        "output": "dist/main.wasm",
        "description": "a new web assembly text format module.",
        "author": "this'll be you :D",
        "license": "MIT"
    }
    path = os.path.join(target_dir, "watkit.json")
    with open(path, "w") as f:
        json.dump(config, f, indent=2)

def create_readme(target_dir: str) -> None:
    """
    Create a README.md file in the target directory.
    """
    name = os.path.basename(os.path.abspath(target_dir))
    readme_path = os.path.join(target_dir, "README.md")
    with open(readme_path, "w") as f:
        f.write(f"# {name}\n\na new web assembly text format module.")


def create_starter_wat(target_dir: str) -> None:
    """
    Create a starter WAT file with a simple add function in the src/ directory.
    """
    wat_code = """(module
  (func (export "add") (param i32 i32) (result i32)
    local.get 0
    local.get 1
    i32.add
  )
)
"""
    wat_path = os.path.join(target_dir, "src", "main.wat")
    with open(wat_path, "w") as f:
        f.write(wat_code)

def print_success(target_dir: str) -> None:
    message = (
        f"{Fore.GREEN}✓ watkit package initialized successfully in {target_dir}.{Style.RESET_ALL}"
        if target_dir != "." else
        f"{Fore.GREEN}✓ watkit package initialized successfully.{Style.RESET_ALL}"
    )
    print(message)
    print(f"{Fore.GREEN}→ edit watkit.json and src/main.wat to get started!!{Style.RESET_ALL}\n")
