import os
import time
import json
import httpx
from colorama import init as colorama_init, Fore, Style

colorama_init(autoreset=True)

CONFIG_PATH = os.path.expanduser("~/watkit/config.json")
COOKIE_PATH = os.path.expanduser("~/.watkit/cookies.json")
GITHUB_DEVICE_CODE_URL = "https://github.com/login/device/code"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_API = "https://api.github.com/user"

def load_config():
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"{Fore.RED}✘ Missing or invalid config file at {CONFIG_PATH}{Style.RESET_ALL}")
        return {}

def save_token(token):
    os.makedirs(os.path.dirname(COOKIE_PATH), exist_ok=True)
    with open(COOKIE_PATH, "w") as f:
        json.dump({"watkit_token": token}, f)
    print(f"{Fore.GREEN}✓ Token saved to {COOKIE_PATH}{Style.RESET_ALL}")

def run():
    config = load_config()
    client_id = config.get("github_client_id")
    if not client_id:
        print(f"{Fore.RED}✘ GitHub client ID not found in config.{Style.RESET_ALL}")
        return

    print(f"{Fore.CYAN}↪ Starting login using GitHub device flow...{Style.RESET_ALL}")

    # Step 1: Get device and user codes
    resp = httpx.post(GITHUB_DEVICE_CODE_URL, data={
        "client_id": client_id,
        "scope": "read:user"
    }, headers={"Accept": "application/json"})
    resp.raise_for_status()
    data = resp.json()

    user_code = data["user_code"]
    verification_uri = data["verification_uri"]
    device_code = data["device_code"]
    interval = data.get("interval", 5)

    print(f"\n{Fore.YELLOW}⇨ Visit this URL to authorize: {Fore.BLUE}{verification_uri}")
    print(f"{Fore.YELLOW}⇨ And enter this code: {Fore.GREEN}{user_code}{Style.RESET_ALL}")

    # Step 2: Poll for access token
    print(f"{Fore.CYAN}⌛ Waiting for authorization...{Style.RESET_ALL}")
    while True:
        time.sleep(interval)
        poll_resp = httpx.post(GITHUB_TOKEN_URL, data={
            "client_id": client_id,
            "device_code": device_code,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
        }, headers={"Accept": "application/json"})

        poll_data = poll_resp.json()
        if "access_token" in poll_data:
            access_token = poll_data["access_token"]
            break
        elif poll_data.get("error") == "authorization_pending":
            continue
        elif poll_data.get("error") == "slow_down":
            interval += 2
        else:
            print(f"{Fore.RED}✘ Login failed: {poll_data.get('error_description')}{Style.RESET_ALL}")
            return

    # Step 3: Exchange for watkit token
    server = config.get("server_url", "https://watkit.dev")
    exchange_resp = httpx.post(f"{server}/auth/exchange", json={
        "access_token": access_token
    })
    if exchange_resp.status_code != 200:
        print(f"{Fore.RED}✘ Failed to exchange token: {exchange_resp.text}{Style.RESET_ALL}")
        return

    watkit_token = exchange_resp.json().get("watkit_token")
    if not watkit_token:
        print(f"{Fore.RED}✘ Server did not return a watkit token.{Style.RESET_ALL}")
        return

    save_token(watkit_token)
    print(f"{Fore.GREEN}✓ Logged in and token saved!{Style.RESET_ALL}")
