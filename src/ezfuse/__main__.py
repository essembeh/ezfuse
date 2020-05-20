import argparse
import os
import subprocess
import sys
from argparse import ArgumentParser
from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory

from pytput import Style, tput_print

from ezfuse import __title__, __version__

COMMMANDS = (
    ("x", "exit"),
    ("q", "umount and exit"),
    ("o", "xdg-open"),
    ("s", "shell"),
    ("m", "mount"),
    ("u", "umount"),
)


def execute(*command, cwd=None, check_rc=True):
    cmd = list(map(str, command))
    tput_print("[{label:green}] {cmd:yellow}", label="exec", cmd=" ".join(cmd))
    run(cmd, cwd=None if cwd is None else str(cwd), check=check_rc)


def main():
    parser = ArgumentParser(
        prog=__title__, description="Helper to mount temporary folders"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="{0} version {1}".format(__title__, __version__),
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
        nargs=argparse.ONE_OR_MORE,
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
    ) as td:
        mountpoint = Path(td)
    mountpoint.mkdir()
    tput_print(
        "[{label:green}] Using mountpoint {mnt:blue}", label="info", mnt=mountpoint
    )
    # Mount
    try:
        execute(binary, *args.extra_args, mountpoint)
    except BaseException as e:
        print(Style.RED.apply("Error while mounting: {0}".format(e)))
        # In case of error, try to remove the mountpoint
        tput_print(
            "[{label:green}] Remove mountpoint {mnt:blue}", label="info", mnt=mountpoint
        )
        mountpoint.rmdir()
        sys.exit(2)

    mounted = True
    # Question loop
    actions = [a for a, _ in COMMMANDS]
    while True:
        print()
        for cmd, desc in COMMMANDS:
            tput_print("{cmd:bold}: {desc:dim}", cmd=cmd, desc=desc)
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
                tput_print(
                    "[{label:green}] Remove mountpoint {mnt:blue}",
                    label="info",
                    mnt=mountpoint,
                )
                mountpoint.rmdir()
            else:
                tput_print(
                    "[{label:green}] Keeping mountpoint {mnt:blue}",
                    label="info",
                    mnt=mountpoint,
                )
                tput_print(
                    "[{label:green}] To umount it run: {cmd:yellow}",
                    label="info",
                    cmd="fusermount -u -z {0}; rmdir {0}".format(mountpoint),
                )
            sys.exit(0)


if __name__ == "__main__":
    main()
