"""
ezfuse - Quickly mount fuse filesystems in temporary directories
"""

import argparse
import os
import shlex
import subprocess
import sys
from argparse import ArgumentParser
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, Optional

from colorama import Fore, Style

from . import __description__, __version__

COMMMANDS = (
    ("q", "umount and exit"),
    ("x", "exit (and keep mountpoint)"),
    ("o", "xdg-open"),
    ("s", "shell"),
    ("m", "mount"),
    ("u", "umount"),
)


def execute(
    *command,
    cwd: Optional[Path] = None,
    check_rc: bool = True,
    extra_env: Optional[Dict[str, Any]] = None,
):
    """
    execute a command using a subprocess
    """
    command = [str(x) for x in command]
    command_txt = " ".join(map(shlex.quote, command))
    print(f"[exec] {command_txt}")
    env = dict(os.environ)
    if isinstance(extra_env, dict):
        env.update(extra_env)
    subprocess.run(command, cwd=str(cwd) if cwd else None, check=check_rc, env=env)


def run():
    """
    command line entrypoint
    """
    parser = ArgumentParser(description=__description__)
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s version {__version__}",
    )
    parser.add_argument(
        "-t",
        "--type",
        action="store",
        help="type of filesystem, which is also the binary to use to mount it",
    )
    parser.add_argument(
        "--force", action="store_true", help="force type without testing binary before"
    )
    parser.add_argument(
        "--pwd",
        action="store_true",
        help="create temporary folder in current directory, default is home folder",
    )
    parser.add_argument(
        "extra_args",
        nargs=argparse.REMAINDER,
        help="arguments to pass to the mount command",
    )
    args = parser.parse_args()

    # Get mount binary
    binary = args.type
    if binary is None:
        prog = Path(sys.argv[0]).name
        if prog == "ezfuse":
            parser.error("missing -t|--type argument")
        if not prog.startswith("ez"):
            raise ValueError(f"Cannot infer fuse type from {prog}")
        binary = prog[2:]
    # Test mount binary
    if not args.force:
        subprocess.check_call(
            [binary, "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    # Create mountpoint
    mountpoint = None
    parent_folder = Path.cwd() if args.pwd else Path.home()
    with TemporaryDirectory(
        prefix=f"ezmount-{binary}-", dir=str(parent_folder)
    ) as tempdir:
        mountpoint = Path(tempdir)
    mountpoint.mkdir()
    print(
        f"[{Fore.GREEN}info{Fore.RESET}] Using mountpoint {Fore.BLUE}{mountpoint}{Fore.RESET}",
    )
    # Mount
    try:
        execute(binary, *args.extra_args, mountpoint)
    except BaseException as e:  # pylint: disable=broad-except,invalid-name
        print(f"{Fore.RED}Error while mounting: {e}{Fore.RESET}")
        # In case of error, try to remove the mountpoint
        print(
            f"[{Fore.GREEN}info{Fore.RESET}] Remove mountpoint {Fore.BLUE}{mountpoint}{Fore.RESET}"
        )
        mountpoint.rmdir()
        sys.exit(2)

    mounted = True
    # Question loop
    actions = [a for a, _ in COMMMANDS]
    while True:
        print()
        for cmd, desc in COMMMANDS:
            print(
                f"{Style.BRIGHT}{cmd}{Style.RESET_ALL}: {Style.DIM}{desc}{Style.RESET_ALL}"
            )
        action = None
        while action not in actions:
            try:
                action = input(f"[{'/'.join(actions)}] ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                action = "x"
        print()

        # Mount/Umount
        if action in ("q", "u"):
            if mounted:
                execute("fusermount", "-u", "-z", mountpoint)
                mounted = False
        elif action in ("m", "o", "s"):
            if not mounted:
                execute(binary, *args.extra_args, mountpoint)
                mounted = True

        # Action open/shell
        if action == "o":
            execute("xdg-open", mountpoint)
        elif action == "s":
            execute(
                os.getenv("SHELL", "bash"),
                cwd=mountpoint,
                check_rc=False,
                extra_env={"EZMNT": str(mountpoint)},
            )

        # Handle end of loop to quit
        if action in ("x", "q"):
            if not mounted:
                print(
                    f"[{Fore.GREEN}info{Fore.RESET}] Remove mountpoint {Fore.BLUE}{mountpoint}{Fore.RESET}",
                )
                mountpoint.rmdir()
            else:
                print(
                    f"[{Fore.GREEN}info{Fore.RESET}] Keeping mountpoint {Fore.BLUE}{mountpoint}{Fore.RESET}"
                )
                umount_cmd = f"fusermount -u -z {mountpoint}; rmdir {mountpoint}"
                print(
                    f"[{Fore.GREEN}info{Fore.RESET}] To umount it run: {Fore.YELLOW}{umount_cmd}{Fore.RESET}"
                )
            sys.exit(0)
