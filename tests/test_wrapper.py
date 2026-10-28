import pytest

import lightpanda


def test_build_cmd():
    cmd = lightpanda.build_cmd(
        "fetch", "url", strip_mode=["js", "css"], with_base=True, with_frames=False, dump=None
    )
    assert cmd == [lightpanda.BINARY, "fetch", "url", "--strip-mode", "js", "--strip-mode", "css", "--with-base"]


def test_response_json():
    assert lightpanda.Response(b'{"a": "<b>"}').json() == {"a": "<b>"}
    assert lightpanda.Response(b"<pre>{&quot;a&quot;: &quot;&lt;b&gt;&quot;}</pre>").json() == {"a": "<b>"}


def test_response_text_replaces_invalid_utf8():
    assert lightpanda.Response(b"\xff").text == "�"


def test_serve_rejects_removed_timeout():
    with pytest.raises(TypeError, match="timeout"):
        lightpanda.serve(timeout=10)
