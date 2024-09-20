#!/usr/bin/env python3

import argparse
import hashlib
import logging
import os
import subprocess
import sys
from typing import List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CommandNotFoundError(Exception):
    pass

class CowbuilderError(Exception):
    pass

def check_required_commands():
    commands = ["sudo", "/usr/sbin/cowbuilder"]
    for cmd in commands:
        try:
            subprocess.run(["which", cmd], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError:
            raise CommandNotFoundError(f"Required command not found: {cmd}")

def get_cow_name(distribution: str, architecture: str, role: Optional[str]) -> str:
    if not role:
        hash_input = f"{distribution}-{architecture}".encode('utf-8')
        role = hashlib.sha512(hash_input).hexdigest()[:10]
    return f"{distribution}-{architecture}-{role}"

def get_base_cow_path(cow_name: str) -> str:
    return os.path.join("/var/cache/pbuilder", f"{cow_name}.cow")

def get_bind_mount_dir(cow_name: str) -> str:
    home_dir = os.path.expanduser("~")
    return os.path.join(home_dir, ".cowbuilder-aide", cow_name)

def run_cowbuilder(operation: str, args: argparse.Namespace, base_cow: str, distribution: str, architecture: str):
    cow_name = get_cow_name(distribution, architecture, args.role)
    bind_mount_dir = get_bind_mount_dir(cow_name)
    os.makedirs(bind_mount_dir, exist_ok=True)

    cowbuilder_args = [
        "sudo", "cowbuilder", operation,
        "--basepath", base_cow,
        "--distribution", distribution,
        "--architecture", architecture,
        "--bindmounts", bind_mount_dir
    ]

    cowbuilder_args.extend(args.additional_options)

    logger.info(f"Running cowbuilder with args: {' '.join(cowbuilder_args)}")
    try:
        subprocess.run(cowbuilder_args, check=True)
    except subprocess.CalledProcessError as e:
        raise CowbuilderError(f"Error running cowbuilder {operation}: {e}")

def create(args: argparse.Namespace):
    cow_name = get_cow_name(args.distribution, args.architecture, args.role)
    base_cow = get_base_cow_path(cow_name)

    if os.path.exists(base_cow) and not args.force:
        logger.warning(f"Base cow already exists at {base_cow}. Use --force to overwrite.")
        return

    if os.path.exists(base_cow):
        logger.info(f"Force flag set. Removing existing base cow at {base_cow}.")
        try:
            subprocess.run(["sudo", "rm", "-rf", base_cow], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error removing existing base cow: {e}")
            return

    run_cowbuilder("--create", args, base_cow, args.distribution, args.architecture)
    logger.info(f"Successfully created new chroot environment at {base_cow}")

def update(args: argparse.Namespace):
    cow_name = get_cow_name(args.distribution, args.architecture, args.role)
    base_cow = get_base_cow_path(cow_name)
    if not os.path.exists(base_cow):
        logger.error(f"Base cow does not exist at {base_cow}. Create it first.")
        return
    run_cowbuilder("--update", args, base_cow, args.distribution, args.architecture)
    logger.info(f"Successfully updated chroot environment at {base_cow}")

def login(args: argparse.Namespace):
    cow_name = get_cow_name(args.distribution, args.architecture, args.role)
    base_cow = get_base_cow_path(cow_name)
    if not os.path.exists(base_cow):
        logger.error(f"Base cow does not exist at {base_cow}. Create it first.")
        return
    run_cowbuilder("--login", args, base_cow, args.distribution, args.architecture)

def main():
    try:
        check_required_commands()
    except CommandNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    parser = argparse.ArgumentParser(description="cowbuilder-aide: A tool to simplify chroot environment creation and management using cowbuilder")

    subparsers = parser.add_subparsers(title="commands", dest="command", required=True)

    # Common parser for shared arguments
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument("--distribution", "-d", required=True, help="Distribution (required)")
    common_parser.add_argument("--architecture", "-a", default="amd64", help="Architecture")
    common_parser.add_argument("--role", "-r", default="", help="Role")
    common_parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    common_parser.add_argument("additional_options", nargs="*", help="Additional cowbuilder options")

    # Create subparser
    create_parser = subparsers.add_parser("create", help="Create a new chroot environment", parents=[common_parser])
    create_parser.add_argument("--force", "-f", action="store_true", help="Force creation even if base cow exists")

    # Update subparser
    update_parser = subparsers.add_parser("update", help="Update an existing chroot environment", parents=[common_parser])

    # Login subparser
    login_parser = subparsers.add_parser("login", help="Log in to a chroot environment", parents=[common_parser])

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    try:
        if args.command == "create":
            create(args)
        elif args.command == "update":
            update(args)
        elif args.command == "login":
            login(args)
    except CowbuilderError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
