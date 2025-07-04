#!/usr/bin/env python3
import os, json, requests, argparse
from colorama import init as colorama_init, Fore, Style

CONFIG_PATH = os.path.expanduser("~/watkit/config.json")
from command_constants import SEARCH_API_URL

def run(args):
    colorama_init()
    by = "name" if args.name else "author"
    print(f"{Fore.CYAN}⇨ Searching {by} for '{args.query}'...{Style.RESET_ALL}")

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
        print(f"{Fore.RED}✘ Search failed: {e}{Style.RESET_ALL}")
