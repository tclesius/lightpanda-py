import functools
import subprocess
from collections.abc import Callable
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


class Error(Exception):
    def __init__(self, message: str | bytes, code: int | None = None) -> None:
        if isinstance(message, bytes):
            message = message.decode(errors="replace").strip()
        super().__init__(message)
        self.code = code


def reraise(func: Callable[P, R]) -> Callable[P, R]:
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return func(*args, **kwargs)
        except subprocess.CalledProcessError as e:
            raise Error(e.stderr, e.returncode) from e

    return wrapper
