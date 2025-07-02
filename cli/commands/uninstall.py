import os
import shutil
from colorama import Fore, Style
from command_constants import MODULES_DIR

def run(package: str) -> None:
    """
    Uninstall a package from the current watkit project.

    Args:
        package: The name of the package to uninstall.
    """
    package_path = os.path.join(MODULES_DIR, package)

    if not os.path.exists("watkit.json"):
        print(f"{Fore.RED}⛌ not a watkit project (watkit.json not found){Style.RESET_ALL}")
        return

    if not os.path.exists(package_path):
        print(f"{Fore.RED}⛌ package '{package}' is not installed in this project{Style.RESET_ALL}")
        return

    try:
        shutil.rmtree(package_path)
        print(f"{Fore.GREEN}✓ removed package: {package}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}⛌ failed to uninstall {package}: {e}{Style.RESET_ALL}")
