import os
import os.path as op
import subprocess
from time import sleep
from tempfile import mkdtemp

import pytest
from pynvim import attach

import nvim_cyrillic as plug


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
    yield nvim
    nvim.feedkeys(nvim.replace_termcodes("<ESC>:q!<CR>"))
    p.terminate()
    if op.exists(socket):
        os.remove(socket)


def test_map_last_input_single_word_en_ru(nvim):
    string = "hello"
    translation = "руддщ"
    nvim.feedkeys(f"i{string}")
    cursor = nvim.current.window.cursor
    assert cursor[0] == 1
    assert cursor[1] == len(string.encode("utf-8"))
    main = plug.Main(nvim)
    main.map_last_input(args=None)
    buf = nvim.current.buffer
    assert len(buf) == 1
    assert buf[0] == translation


def test_map_last_input_single_word_ru_en(nvim):
    string = "руддщ"
    translation = "hello"
    main = plug.Main(nvim)
    main._toggle_language()
    nvim.feedkeys(f"i{string}")
    cursor = nvim.current.window.cursor
    assert cursor[0] == 1
    assert cursor[1] == len(string.encode("utf-8"))
    main.map_last_input(args=None)
    buf = nvim.current.buffer
    assert len(buf) == 1
    assert buf[0] == translation