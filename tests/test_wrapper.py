import lightpanda


def test_command_argv():
    cmd = lightpanda.Command(
        lightpanda.BINARY, "fetch", "url", strip_mode=["js", "css"], with_base=True, with_frames=False, dump=None,
        user_agent="x", json=True, obey_robots=False,
    )
    assert cmd.argv == [
        lightpanda.BINARY, "fetch", "url", "--strip-mode", "js", "--strip-mode", "css", "--with-base",
        "--user-agent", "x", "--json",
    ]


def test_result_json():
    assert lightpanda.Result(b'{"a": "<b>"}').json() == {"a": "<b>"}
    assert lightpanda.Result(b"<pre>{&quot;a&quot;: &quot;&lt;b&gt;&quot;}</pre>").json() == {"a": "<b>"}


def test_result_str():
    assert str(lightpanda.Result(b"hello\n")) == "hello"


def test_result_text_strips_only_newlines():
    assert lightpanda.Result(b"\n  x  \n").text == "  x  "


def test_result_text_replaces_invalid_utf8():
    assert lightpanda.Result(b"\xff").text == "�"
