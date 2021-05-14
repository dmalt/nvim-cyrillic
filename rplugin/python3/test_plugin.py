# launch nvim with
# NVIM_LISTEN_ADDRESS=/tmp/nvim nvim
import os
import subprocess
from time import sleep

import pytest
from pynvim import attach

import nvim_cyrillic as plug


@pytest.fixture
def nvim():
    os.environ["NVIM_LISTEN_ADDRESS"] = "/tmp/nvim"
    p = subprocess.Popen(
        ["nvim", "--headless", "--clean"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    sleep(1)
    nvim = attach("socket", path=os.environ["NVIM_LISTEN_ADDRESS"])
    yield nvim
    nvim.feedkeys(nvim.replace_termcodes("<ESC>:q!<CR>"))
    p.terminate()
    os.remove("/tmp/nvim")


def test_map_last_input_single_word_en_ru(nvim):
    string = "hello"
    translation = "руддщ"
    nvim.feedkeys(f"i{string}")
    cursor = nvim.current.window.cursor
    assert cursor[0] == 1
    assert cursor[1] == len(string)
    main = plug.Main(nvim)
    main.map_last_input(args=None)
    buf = nvim.current.buffer
    assert len(buf) == 1
    assert buf[0] == translation
