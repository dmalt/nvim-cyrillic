import os
import os.path as op
import subprocess
from contextlib import contextmanager
from pathlib import Path
from tempfile import mkdtemp, mkstemp
from time import sleep

import pytest
from pynvim import attach


EN, RU = 0, 1
PACK_DIR = Path(__file__).parent.parent.parent.parent.parent.parent.parent
NVIM_CMD = [
    "nvim", "--headless", "-u", "NORC", "--cmd", f"set packpath+={PACK_DIR}"
]


def update_rplugin_manifest():
    temp_rplugin = mkstemp(suffix=".vim", prefix="rplugin", text=True)
    os.environ["NVIM_RPLUGIN_MANIFEST"] = temp_rplugin[1]
    with spawn_nvim() as nvim:
        nvim.command("UpdateRemotePlugins")
    return temp_rplugin


@contextmanager
def spawn_nvim(timeout=1000):
    tempdir = mkdtemp()
    socket = op.join(tempdir, "nvim")
    os.environ["NVIM_LISTEN_ADDRESS"] = socket
    process = subprocess.Popen(
        NVIM_CMD, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    for _ in range(timeout):
        if op.exists(socket):
            break
        sleep(0.001)
    else:
        raise FileNotFoundError(f"No socket file at {socket}")
    nvim = attach("socket", path=os.environ["NVIM_LISTEN_ADDRESS"])
    try:
        yield nvim
    finally:
        nvim.quit()
        process.terminate()
        if op.exists(socket):
            os.remove(socket)


@pytest.fixture(scope="module")
def rplugin_manifest():
    temp_rplugin = update_rplugin_manifest()
    yield temp_rplugin[1]
    os.remove(temp_rplugin[1])


@pytest.fixture
def nvim(rplugin_manifest):
    with spawn_nvim() as nvim:
        nvim.command("set keymap=russian-jcukenwin")
        nvim.command("set iminsert=0")
        yield nvim


@pytest.mark.parametrize(
    "string,transl,lang",
    [
        ("", "", RU),
        ("", "", EN),
        ("hello", "руддщ", EN),
        ("руддщ", "hello", RU),
        ("Мама мыла раму", "Vfvf vskf hfve", RU),
        ("№", "#", RU),
        ("  №", "  #", RU),
        ("  №", "  №", EN),
    ],
)
def test_map_last_input(nvim, string, transl, lang):
    # check if current language is english
    nvim.command(f"set iminsert={lang}")
    nvim.feedkeys("i")
    for c in string:
        nvim.feedkeys(c)

    assert nvim.current.window.cursor[0] == 1
    assert nvim.current.window.cursor[1] == len(string.encode("utf-8"))

    # nvim.feedkeys(nvim.replace_termcodes(r"<c-\><c-o>"), "t")
    nvim.command("call MapLastInput()")

    assert len(nvim.current.buffer) == 1
    assert nvim.current.buffer[0] == transl
    # check if language is switched
    assert nvim.request("nvim_get_option", "iminsert") == int(not lang)

    assert nvim.current.window.cursor[0] == 1
    assert nvim.current.window.cursor[1] == len(transl.encode("utf-8"))


@pytest.mark.parametrize(
    "string,transl,lang",
    [
        ("hello", "руддщ", EN),
        ("руддщ", "hello", RU),
        ("руддщ руддщ", "руддщ hello", RU),
    ],
)
def test_map_visual_word_ru_en(nvim, string, transl, lang):
    nvim.command(f"set iminsert={lang}")
    nvim.feedkeys("i")
    for c in string:
        nvim.feedkeys(c, "t")
    nvim.feedkeys(nvim.replace_termcodes("<esc>"))
    cursor = nvim.current.window.cursor
    assert cursor[0] == 1
    assert cursor[1] == len(string[:-1].encode("utf-8"))

    nvim.feedkeys(nvim.replace_termcodes("viw<esc>"))
    nvim.command("call MapVisualSelection()")
    buf = nvim.current.buffer
    assert len(buf) == 1
    assert buf[0] == transl

    assert nvim.current.window.cursor[0] == 1
    assert nvim.current.window.cursor[1] == len(transl[:-1].encode("utf-8"))


@pytest.mark.parametrize(
    "string,transl,lang,move, targ",
    [
        ("hellopal", "heддщpal", EN, "02lv2l<esc>", 4),
        ("руддщзфд", "руlloзфд", RU, "02lv2l<esc>", 4),
    ],
)
def test_map_visual_middle_of_word(nvim, string, transl, lang, move, targ):
    nvim.command(f"set iminsert={lang}")
    nvim.feedkeys(f"i{string}")
    nvim.feedkeys(nvim.replace_termcodes("<esc>"))

    nvim.feedkeys(nvim.replace_termcodes(move))
    nvim.command("call MapVisualSelection()")
    buf = nvim.current.buffer
    assert len(buf) == 1
    assert buf[0] == transl

    assert nvim.current.window.cursor[0] == 1
    assert nvim.current.window.cursor[1] == len(transl[:targ].encode("utf-8"))


@pytest.mark.parametrize(
    "string,transl,lang,move,targ",
    [
        ("Научный текст \\куа", "Научный текст \\ref", RU, "", 18),
        ("Мама мыла раму \\куа", "Мама мыла раму \\reа", RU, "<Left>", 18),
        ("Quick brown pfqxbr", "Quick brown зайчик", EN, "", 18),
        (
            "Quick cbybq bunny",
            "Quick синий bunny",
            EN,
            "<C-Left><Left>",
            11,
        ),
        (
            "Something",
            "Something",
            EN,
            "<esc>0lla",
            3,
        ),
        (
            "Smth",
            "elseSmth",
            EN,
            "<esc>Ielse<Right><Right>",
            6,
        ),
    ],
)
def test_map_last_input_word(nvim, string, transl, lang, move, targ):
    nvim.command(f"set iminsert={lang}")
    nvim.feedkeys("i")
    for c in string:
        nvim.feedkeys(c)
    nvim.feedkeys(nvim.replace_termcodes(move), options="t")

    nvim.command("call MapLastInputWord()")
    buf = nvim.current.buffer
    assert len(buf) == 1
    assert buf[0] == transl

    assert nvim.current.window.cursor[0] == 1
    assert nvim.current.window.cursor[1] == len(transl[:targ].encode("utf-8"))


@pytest.mark.parametrize(
    "string,transl, lang", [("Something", "Ыщьуерштп", EN)]
)
def test_map_last_input_word_triggered_twice(nvim, string, transl, lang):
    nvim.command(f"set iminsert={lang}")
    nvim.feedkeys("i")
    for c in string:
        nvim.feedkeys(c)

    nvim.command("call MapLastInputWord()")
    assert len(nvim.current.buffer) == 1
    assert nvim.current.buffer[0] == transl
    nvim.command("call MapLastInputWord()")

    assert len(nvim.current.buffer) == 1
    assert nvim.current.buffer[0] == string

    assert nvim.current.window.cursor[0] == 1
    assert nvim.current.window.cursor[1] == len(string.encode("utf-8"))
