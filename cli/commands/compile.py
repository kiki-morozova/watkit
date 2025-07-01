import subprocess, os, json, shutil, sys
from colorama import init as colorama_init
from colorama import Fore, Style

def run() -> None:
    """
    Compile the main WAT file in a package to a WASM binary.
    """
    colorama_init()
    check_wat2wasm()
    with open("watkit.json") as f:
        config = json.load(f)

    # grab main wat and output path from package config
    src = config["main"]
    dest = config["output"]
    
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    subprocess.run(["wat2wasm", src, "-o", dest], check=True)
    print(f"{Fore.GREEN} ✓ Compiled {src} → {dest}{Style.RESET_ALL}")

def check_wat2wasm() -> None:
    """
    Check if the wat2wasm binary is installed on system.
    If not, print an error message and exit.
    """
    if shutil.which("wat2wasm") is None:
        print(f"\n{Fore.RED}[watkit] ⛌ Missing dependency: `wat2wasm` is not installed or not in your PATH.{Style.RESET_ALL}\n")
        print(f"To install `wat2wasm`, use one of the following methods based on your platform:{Style.RESET_ALL}\n")
        print(f"  • macOS:    brew install wabt")
        print(f"  • Windows:  choco install wabt   (with Chocolatey)")
        print(f"  • Linux:    sudo apt install wabt")
        print(f"  • Manual:   https://github.com/WebAssembly/wabt/releases")
        sys.exit(1)