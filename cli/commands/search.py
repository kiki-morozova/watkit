#!/usr/bin/env python3
import os, json, requests, argparse, re
from colorama import init as colorama_init, Fore, Style

CONFIG_PATH = os.path.expanduser("~/watkit/config.json")
from command_constants import SEARCH_API_URL

def validate_query(query: str) -> None:
    """Validate that query only contains alphanumeric characters, hyphens, and underscores."""
    if not re.match(r'^[a-zA-Z0-9_-]+$', query):
        raise ValueError("oooo someone's being sneaky with their query! it must only contain alphanumeric characters, hyphens (-), and underscores (_)")

def run(args):
    colorama_init()

    try:
        validate_query(args.query)
    except ValueError as e:
        print(f"{Fore.RED}✘ invalid query: {e}{Style.RESET_ALL}")
        return
    
    by = "name" if args.name else "author"
    print(f"{Fore.CYAN}⇨ searching {by} for '{args.query}'...{Style.RESET_ALL}")

    try:
        resp = requests.get(f"{SEARCH_API_URL}/search", params={"q": args.query, "by": by})
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if not results:
            print(f"{Fore.YELLOW}ⓘ No matches found.{Style.RESET_ALL}")
            return
        for pkg in results:
            versions = ", ".join(pkg["versions"])
            print(f"{Fore.GREEN}{pkg['name']}{Style.RESET_ALL}"
                  f" (author: {pkg.get('author') or 'unknown'}) → latest: {pkg['latest']}  versions: {versions}")
    except Exception as e:
        print(f"{Fore.RED}✘ search failed: {e}{Style.RESET_ALL}")
