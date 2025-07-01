#!/usr/bin/env python3
import argparse
import sys

from commands.compile import run as compile_command

def main():
    parser = argparse.ArgumentParser(prog="watkit", description="watkit - a wat package manager")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("compile", help="compile .wat to binary .wasm")
    args = parser.parse_args()

    # command routing tree
    if args.command == "compile":
        compile_command()
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
