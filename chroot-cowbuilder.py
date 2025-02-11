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
    return os.path.join(home_dir, ".chroot-cowbuilder", cow_name)

def run_cowbuilder(operation: str, args: argparse.Namespace):
    cow_name = get_cow_name(args.distribution, args.architecture, args.role)
    base_cow = get_base_cow_path(cow_name)
    bind_mount_dir = get_bind_mount_dir(cow_name)
    os.makedirs(bind_mount_dir, exist_ok=True)

    cowbuilder_args = [
        "sudo", "cowbuilder", operation,
        "--basepath", base_cow,
        "--distribution", args.distribution,
        "--architecture", args.architecture,
        "--bindmounts", bind_mount_dir
    ]

    if args.cowbuilder_args:
        # Remove the leading '--' if present
        if args.cowbuilder_args[0] == '--':
            args.cowbuilder_args = args.cowbuilder_args[1:]
        cowbuilder_args.extend(args.cowbuilder_args)

    logger.info(f"Running cowbuilder with args: {' '.join(cowbuilder_args)}")
    try:
        subprocess.run(cowbuilder_args, check=True)
    except subprocess.CalledProcessError as e:
        raise CowbuilderError(f"Error running cowbuilder {operation}: {e}")

def create(args: argparse.Namespace):
    base_cow = get_base_cow_path(get_cow_name(args.distribution, args.architecture, args.role))
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

    run_cowbuilder("--create", args)
    logger.info(f"Successfully created new chroot environment at {base_cow}")

def update(args: argparse.Namespace):
    base_cow = get_base_cow_path(get_cow_name(args.distribution, args.architecture, args.role))
    if not os.path.exists(base_cow):
        logger.error(f"Base cow does not exist at {base_cow}. Create it first.")
        return
    run_cowbuilder("--update", args)
    logger.info(f"Successfully updated chroot environment at {base_cow}")

def login(args: argparse.Namespace):
    base_cow = get_base_cow_path(get_cow_name(args.distribution, args.architecture, args.role))
    if not os.path.exists(base_cow):
        logger.error(f"Base cow does not exist at {base_cow}. Create it first.")
        return
    run_cowbuilder("--login", args)

def main():
    try:
        check_required_commands()
    except CommandNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    parser = argparse.ArgumentParser(description="chroot-cowbuilder: A tool to simplify chroot environment creation and management using cowbuilder")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Common arguments
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument("--distribution", "-d", required=True, help="Distribution (required)")
    common_parser.add_argument("--architecture", "-a", default="amd64", help="Architecture")
    common_parser.add_argument("--role", "-r", default="", help="Role")
    common_parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    common_parser.add_argument("cowbuilder_args", nargs=argparse.REMAINDER, help="Additional cowbuilder options")

    # Create command
    create_parser = subparsers.add_parser("create", parents=[common_parser], help="Create a new chroot environment")
    create_parser.add_argument("--force", "-f", action="store_true", help="Force creation even if base cow exists")
    create_parser.set_defaults(func=create)

    # Update command
    update_parser = subparsers.add_parser("update", parents=[common_parser], help="Update an existing chroot environment")
    update_parser.set_defaults(func=update)

    # Login command
    login_parser = subparsers.add_parser("login", parents=[common_parser], help="Log in to a chroot environment")
    login_parser.set_defaults(func=login)

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    try:
        args.func(args)
    except CowbuilderError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
