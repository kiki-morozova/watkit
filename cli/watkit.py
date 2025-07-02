#!/usr/bin/env python3
import argparse
import sys

from commands.compile import run as compile_command
from commands.init import run as init_command
from commands.publish import run as publish_command
from commands.install import run as install_command
from commands.run import run as run_command

def main():
    parser = argparse.ArgumentParser(prog="watkit", description="watkit - a wat package manager")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("compile", help="compile .wat to binary .wasm")

    init_parser = subparsers.add_parser("init", help="initialize a new watkit package")
    init_parser.add_argument("folder", nargs="?", default=".", help="directory to create the package in")

    subparsers.add_parser("publish", help="publish the project to the watkit registry")

    install_parser = subparsers.add_parser("install", help="install a package from the watkit registry")
    install_parser.add_argument("package", help="name of the package to install")

    run_parser = subparsers.add_parser("run", help="compile + resolve imports + emit language runner")
    run_parser.add_argument("-l", "--lang", choices=["js", "rust"], default="js", help="output language (default: js)")

    args = parser.parse_args()

    # command routing tree
    if args.command == "compile":
        compile_command()
    elif args.command == "init":
        init_command(args.folder)
    elif args.command == "publish":
        publish_command()
    elif args.command == "install":
        install_command(args.package)
    elif args.command == "run":
        run_command(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
