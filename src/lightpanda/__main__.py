import os
import sys

from ._core import BINARY, Command


def main() -> None:
    cmd = Command(BINARY, *sys.argv[1:])
    os.execve(cmd.binary, cmd.argv, cmd.env)


if __name__ == "__main__":
    main()
