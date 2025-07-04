import os
from colorama import init as colorama_init, Fore, Style

COOKIE_STORAGE_PATH = os.path.expanduser("~/.watkit/cookies.json")

def run() -> None:
    """
    Logs the user out by deleting the saved JWT token.
    """
    colorama_init(autoreset=True)
    if os.path.exists(COOKIE_STORAGE_PATH):
        os.remove(COOKIE_STORAGE_PATH)
        print(f"{Fore.GREEN}✓ Logged out. Token deleted from {COOKIE_STORAGE_PATH}.{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}⇢ No token found. Already logged out.{Style.RESET_ALL}")
