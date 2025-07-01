import os
import json
import sys
from colorama import init as colorama_init
from colorama import Fore, Style

def run(target_dir: str = ".") -> None:
    """
    Initialize a new watkit package in the given directory,
    with a default wat file, config, and readme.
    """
    colorama_init()
    print(f"✰ initializing new watkit package in {target_dir}... ✰")

    # make target directory if it doesn't exist
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    # check if package already exists
    elif os.path.exists(os.path.join(target_dir, "watkit.json")):
        print(f"{Fore.YELLOW}ⓘ watkit.json already exists in that folder. aborting to prevent overwrite.{Style.RESET_ALL}")
        return
    
    if os.path.exists(os.path.join(target_dir, "src", "main.wat")):
        print(f"{Fore.YELLOW}ⓘ src/main.wat already exists. aborting to prevent overwrite.{Style.RESET_ALL}")
        return

    os.makedirs(os.path.join(target_dir, "src"), exist_ok=True)
    
    # Create watkit.json
    config = {
        "name": os.path.basename(os.path.abspath(target_dir)),
        "version": "0.1.0",
        "main": "src/main.wat",
        "output": "dist/main.wasm",
        "description": "a new web assembly text format module.",
        "author": "this'll be you :D",
        "license": "MIT"
    }
    with open(os.path.join(target_dir, "watkit.json"), "w") as f:
        json.dump(config, f, indent=2)

    # Create README.md
    with open(os.path.join(target_dir, "README.md"), "w") as f:
        f.write(f"# {config['name']}\n\na new web assembly text format module.")

    # Create starter WAT file
    wat_code = """(module
  (func (export "add") (param i32 i32) (result i32)
    local.get 0
    local.get 1
    i32.add
  )
)
"""
    with open(os.path.join(target_dir, "src", "main.wat"), "w") as f:
        f.write(wat_code)

    if (target_dir != "."):
        print(f"{Fore.GREEN}✓ watkit package initialized successfully in {target_dir}.{Style.RESET_ALL}")
    else:
        print(f"{Fore.GREEN}✓ watkit package initialized successfully.{Style.RESET_ALL}")
    print(f"{Fore.GREEN}→ edit watkit.json and src/main.wat to get started!!{Style.RESET_ALL}\n")