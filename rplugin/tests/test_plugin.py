import os
import os.path as op
import subprocess
from tempfile import mkdtemp
from time import sleep

import pytest
from pynvim import attach

import python3.nvim_cyrillic as plug

EN = 0
RU = 1


@pytest.fixture
def nvim():

    tempdir = mkdtemp()
    socket = op.join(tempdir, "nvim")
    os.environ["NVIM_LISTEN_ADDRESS"] = socket
    p = subprocess.Popen(
        ["nvim", "--headless", "--clean"],
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
    nvim.feedkeys(nvim.replace_termcodes("<ESC>:q!<CR>"))
    p.terminate()
    if op.exists(socket):
        os.remove(socket)


@pytest.mark.parametrize(
    "string,translation,lang",
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
def test_map_last_input(nvim, string, translation, lang):
    # check if current language is english
    nvim.command(f"set iminsert={lang}")
    nvim.feedkeys(f"i{string}")

    assert nvim.current.window.cursor[0] == 1
    assert nvim.current.window.cursor[1] == len(string.encode("utf-8"))

    main = plug.Main(nvim)
    main.map_last_input(args=None)

    assert len(nvim.current.buffer) == 1
    assert nvim.current.buffer[0] == translation
    # check if language is switched
    assert nvim.request("nvim_get_option", "iminsert") == int(not lang)

    assert nvim.current.window.cursor[0] == 1
    assert nvim.current.window.cursor[1] == len(translation.encode("utf-8"))


@pytest.mark.parametrize(
    "string,translation,lang",
    [
        ("hello", "руддщ", EN),
        ("руддщ", "hello", RU),
    ],
)
def test_map_visual_word_ru_en(nvim, string, translation, lang):
    main = plug.Main(nvim)
    nvim.command(f"set iminsert={lang}")
    nvim.feedkeys(f"i{string}")
    nvim.feedkeys(nvim.replace_termcodes("<esc>"))
    cursor = nvim.current.window.cursor
    assert cursor[0] == 1
    assert cursor[1] == len(string[:-1].encode("utf-8"))

    nvim.feedkeys(nvim.replace_termcodes("viw<esc>"))
    main.map_visual(args=None)
    buf = nvim.current.buffer
    assert len(buf) == 1
    assert buf[0] == translation

    assert nvim.current.window.cursor[0] == 1
    assert nvim.current.window.cursor[1] == len(
        translation[:-1].encode("utf-8")
    )
