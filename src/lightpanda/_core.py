import html
import json
import os
import subprocess
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ._errors import Error

BINARY = str(Path(__file__).parent / "bin" / "lightpanda")


@dataclass
class Option:
    flag: str
    value: Any

    def __iter__(self):
        values = self.value
        if not isinstance(values, (list, tuple)):
            values = [values]
        for value in values:
            if value is not None:
                yield from (self.flag, str(value))


@dataclass
class Flag:
    flag: str
    set: bool | None = True

    def __iter__(self):
        if self.set:
            yield self.flag


class Command:
    def __init__(self, binary: str, *args: str, **kwargs: Any) -> None:
        self.binary = binary
        self.args = args
        self.kwargs = kwargs

    @property
    def argv(self) -> list[str]:
        cmd = [self.binary, *self.args]
        for key, value in self.kwargs.items():
            flag = "--" + key.replace("_", "-")
            if isinstance(value, bool):
                cmd += Flag(flag, value)
            else:
                cmd += Option(flag, value)
        return cmd

    @property
    def env(self) -> dict[str, str]:
        return {"LIGHTPANDA_DISABLE_TELEMETRY": "true", **os.environ}


@dataclass
class Result:
    stdout: bytes
    stderr: bytes = b""

    def __str__(self) -> str:
        return self.text

    @property
    def text(self) -> str:
        return self.stdout.decode("utf-8", errors="replace").strip("\n")

    @property
    def bytes(self) -> bytes:
        return self.stdout

    def json(self) -> Any:
        text = self.text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # JSON documents are rendered by the browser as <pre>{...}</pre>
            if "<pre>" not in text:
                raise
            return json.loads(html.unescape(text.split("<pre>")[1].split("</pre>")[0]))


class Server:
    def __init__(self, process: subprocess.Popen, endpoint: str | None = None) -> None:
        self.process = process
        self.endpoint = endpoint

    def stop(self, timeout: float = 5) -> None:
        self.process.terminate()
        try:
            self.process.wait(timeout)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()

    def __enter__(self):
        return self

    def __exit__(self, *exc: object) -> None:
        self.stop()


class CDP(Server):
    pass


class MCP(Server):
    def request(self, method: str, params: dict[str, Any] | None = None) -> Any:
        message = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}).encode()
        if self.endpoint:
            req = urllib.request.Request(self.endpoint, message, {"Content-Type": "application/json"})
            with urllib.request.urlopen(req) as resp:
                response = json.load(resp)
        else:
            assert self.process.stdin and self.process.stdout
            self.process.stdin.write(message + b"\n")
            self.process.stdin.flush()
            line = self.process.stdout.readline()
            if not line:
                raise Error("MCP server exited")
            response = json.loads(line)
        if "error" in response:
            raise Error(response["error"]["message"], response["error"]["code"])
        return response["result"]
