import os
import os.path as op
import subprocess
from pathlib import Path
from tempfile import mkdtemp, mkstemp
from time import sleep

import pytest
from pynvim import attach

import python3.nvim_cyrillic as plug

EN = 0
RU = 1
PACK_DIR = Path(__file__).parent.parent.parent.parent.parent.parent.parent


def update_manifest():
    tempdir = mkdtemp()
    socket = op.join(tempdir, "nvim")
    os.environ["NVIM_LISTEN_ADDRESS"] = socket
    temp_rplugin = mkstemp(suffix=".vim", prefix="rplugin", text=True)
    os.environ["NVIM_RPLUGIN_MANIFEST"] = temp_rplugin[1]
    subprocess.Popen(
        [
            "nvim",
            "--headless",
            "-u",
            "NORC",
            "--cmd",
            f"set packpath+={PACK_DIR}",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    for _ in range(50):
        if op.exists(socket):
            break
        sleep(0.1)
    else:
        raise FileNotFoundError
    nvim = attach("socket", path=os.environ["NVIM_LISTEN_ADDRESS"])
    nvim.command("UpdateRemotePlugins")
    nvim.quit()
    if op.exists(socket):
        os.remove(socket)


update_manifest()


@pytest.fixture
def nvim():
    tempdir = mkdtemp()
    socket = op.join(tempdir, "nvim")
    os.environ["NVIM_LISTEN_ADDRESS"] = socket
    p = subprocess.Popen(
        [
            "nvim",
            "--headless",
            "-u",
            "NORC",
            "--cmd",
            f"set packpath+={PACK_DIR}",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    for _ in range(50):
        if op.exists(socket):
            break
        sleep(0.1)
    else:
        raise FileNotFoundError
    nvim = attach("socket", path=os.environ["NVIM_LISTEN_ADDRESS"])
    nvim.command("set keymap=russian-jcukenwin")
    nvim.command("set iminsert=0")
    yield nvim
    nvim.quit()
    p.terminate()
    if op.exists(socket):
        os.remove(socket)


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
    main = plug.Main(nvim)
    nvim.command(f"set iminsert={lang}")
    nvim.feedkeys("i")
    for c in string:
        nvim.feedkeys(c, "t")
    nvim.feedkeys(nvim.replace_termcodes("<esc>"))
    cursor = nvim.current.window.cursor
    assert cursor[0] == 1
    assert cursor[1] == len(string[:-1].encode("utf-8"))

    nvim.feedkeys(nvim.replace_termcodes("viw<esc>"))
    main.map_visual(args=None)
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
    main = plug.Main(nvim)
    nvim.command(f"set iminsert={lang}")
    nvim.feedkeys(f"i{string}")
    nvim.feedkeys(nvim.replace_termcodes("<esc>"))

    nvim.feedkeys(nvim.replace_termcodes(move))
    main.map_visual(args=None)
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
