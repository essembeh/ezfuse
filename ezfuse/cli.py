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

from colorama import Fore, Style

from . import __title__, __version__

COMMMANDS = (
    ("x", "exit"),
    ("q", "umount and exit"),
    ("o", "xdg-open"),
    ("s", "shell"),
    ("m", "mount"),
    ("u", "umount"),
)


def execute(*command, cwd: Path = None, check_rc: bool = True):
    """
    execute a command using a subprocess
    """
    command = list(map(str, command))
    command_txt = " ".join(map(shlex.quote, command))
    print(f"[exec] {command_txt}")
    subprocess.run(command, cwd=str(cwd) if cwd else None, check=check_rc)


def run():
    """
    command line entrypoint
    """
    parser = ArgumentParser(
        prog=__title__, description="Helper to mount temporary folders"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"{__title__} version {__version__}",
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
        if prog == __title__ or not prog.startswith("ez"):
            raise ValueError("Cannot find fuse mount binary")
        binary = prog[2:]
    # Test mount binary
    if not args.force:
        subprocess.check_call(
            [binary, "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    # Create mountpoint
    mountpoint = None
    parent_folder = Path.cwd() if args.pwd else Path.home()
    with TemporaryDirectory(
        prefix="ezmount-{0}-".format(binary), dir=str(parent_folder)
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
                action = input("[{0}] ".format("/".join(actions))).strip().lower()
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
            execute(os.getenv("SHELL", "bash"), cwd=mountpoint, check_rc=False)

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
