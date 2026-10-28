import json
import time
import urllib.request
from pathlib import Path

import pytest

import lightpanda

TOOLS_LIST = b'{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'


def request_json(url, data=None, timeout=10):
    req = urllib.request.Request(
        url, data, {"Content-Type": "application/json", "Accept": "application/json"}
    )
    deadline = time.monotonic() + timeout
    while True:
        try:
            with urllib.request.urlopen(req) as resp:
                return json.load(resp)
        except OSError:
            if time.monotonic() > deadline:
                raise
            time.sleep(0.1)


@pytest.fixture
def spawn():
    procs = []

    def track(proc):
        procs.append(proc)
        return proc

    yield track
    for proc in procs:
        proc.kill()
        proc.wait()


def test_version():
    pinned = (Path(__file__).parents[1] / ".browser-version").read_text().strip()
    assert lightpanda.version() == pinned


def test_fetch(url):
    response = lightpanda.fetch(
        url,
        dump="markdown",
        strip_mode=["js", "css"],
        with_base=True,
        with_frames=True,
        dump_selector="h1",
        dump_max_bytes=1000,
        wait_ms=5000,
        wait_until="load",
        wait_selector="h1",
        wait_script="true",
        inject_script=["1", "2"],
        terminate_ms=5000,
        fail_on_http_error=True,
        http_timeout=5000,
    )
    assert "Hello" in response.text


def test_fetch_multiple_urls(url):
    assert len(lightpanda.fetch([url, url]).json()["results"]) == 2


def test_fetch_http_error(url):
    with pytest.raises(lightpanda.LightpandaError) as exc_info:
        lightpanda.fetch(f"{url}/missing", fail_on_http_error=True)
    assert isinstance(exc_info.value, RuntimeError)
    assert exc_info.value.returncode == 22


def test_serve(spawn, port):
    spawn(
        lightpanda.serve(
            port=port,
            advertise_host="localhost",
            cdp_max_connections=4,
            cdp_max_pending_connections=4,
            protocol=["cdp", "webdriver"],
            remote_allow_origins="*",
            http_timeout=5000,
        )
    )
    info = request_json(f"http://127.0.0.1:{port}/json/version")
    assert info["webSocketDebuggerUrl"] == f"ws://localhost:{port}/"


def test_mcp_stdio(spawn, port):
    proc = spawn(lightpanda.mcp(http_timeout=5000, cdp_port=port))
    proc.stdin.write(TOOLS_LIST + b"\n")
    proc.stdin.flush()
    assert json.loads(proc.stdout.readline())["result"]["tools"]


def test_mcp_http(spawn, port):
    spawn(lightpanda.mcp(host="127.0.0.1", port=port))
    assert request_json(f"http://127.0.0.1:{port}/mcp", TOOLS_LIST)["result"]["tools"]


def test_run(url):
    script = f'''
        const page = new Page();
        await page.goto("{url}");
        console.log(await page.evaluate("document.querySelector('h1').textContent"));
    '''
    assert lightpanda.run(script).text.strip() == "Hello"
