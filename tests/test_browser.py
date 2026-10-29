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


def test_version():
    pinned = (Path(__file__).parents[1] / ".browser-version").read_text().strip()
    assert lightpanda.version().text == pinned


def test_fetch(url):
    result = lightpanda.fetch(
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
    assert "Hello" in result.text


def test_fetch_multiple_urls(url):
    assert len(lightpanda.fetch([url, url]).json()["results"]) == 2


def test_fetch_http_error(url):
    with pytest.raises(lightpanda.Error) as exc_info:
        lightpanda.fetch(f"{url}/missing", fail_on_http_error=True)
    assert exc_info.value.code == 22


def test_serve(port):
    with lightpanda.serve(
        port=port,
        advertise_host="localhost",
        cdp_max_connections=4,
        cdp_max_pending_connections=4,
        protocol=["cdp", "webdriver"],
        remote_allow_origins="*",
        http_timeout=5000,
    ) as server:
        info = request_json(f"{server.endpoint}/json/version")
        assert info["webSocketDebuggerUrl"] == f"ws://localhost:{port}/"
    assert server.process.poll() is not None


def test_mcp_stdio(port):
    with lightpanda.mcp(http_timeout=5000, cdp_port=port) as mcp:
        assert mcp.request("tools/list")["tools"]
        with pytest.raises(lightpanda.Error, match="Method not found") as exc_info:
            mcp.request("nope")
        assert exc_info.value.code == -32601


def test_mcp_http(port):
    with lightpanda.mcp(host="127.0.0.1", port=port) as mcp:
        request_json(mcp.endpoint, TOOLS_LIST)  # wait until the server is up
        assert mcp.request("tools/list")["tools"]


def test_run(url):
    script = f'''
        const page = new Page();
        await page.goto("{url}");
        console.log(await page.evaluate("document.querySelector('h1').textContent"));
    '''
    assert lightpanda.run(script).text.strip() == "Hello"


def test_agent(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    attachment = tmp_path / "notes.txt"
    attachment.write_text("notes")
    with pytest.raises(lightpanda.Error, match="Missing API key"):
        lightpanda.agent(
            "Say hi",
            provider="openai_compatible",
            model="none",
            base_url="http://127.0.0.1:1/v1",
            url="http://127.0.0.1:1/",
            attach=[str(attachment), str(attachment)],
            effort="low",
            search_engine="keenable",
            system_prompt="Be brief",
            save=str(tmp_path / "script.js"),
            trace=str(tmp_path / "trace.jsonl"),
            trace_results=True,
            verbosity="low",
        )


def test_version_check():
    assert lightpanda.version().text in lightpanda.version(check=True).text
