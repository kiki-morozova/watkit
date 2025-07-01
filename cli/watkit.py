#!/usr/bin/env python3
import argparse
import sys

from commands.compile import run as compile_command
from commands.init import run as init_command
from commands.publish import run as publish_command

def main():
    parser = argparse.ArgumentParser(prog="watkit", description="watkit - a wat package manager")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("compile", help="compile .wat to binary .wasm")
    init_parser = subparsers.add_parser("init", help="initialize a new watkit package")
    init_parser.add_argument("folder", nargs="?", default=".", help="directory to create the package in")
    subparsers.add_parser("publish", help="publish the project to the watkit registry")
    args = parser.parse_args()

    # command routing tree
    if args.command == "compile":
        compile_command()
    elif args.command == "init":
        init_command(args.folder)
    elif args.command == "publish":
        publish_command()
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
