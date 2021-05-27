import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import pynvim

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = RotatingFileHandler(
    Path(__file__).parent.parent / "logs" / "nvim_cyrillic.log",
    maxBytes=1e6,
    backupCount=1,
)
file_handler.setFormatter(
    logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%m/%d/%Y %I:%M:%S %p",
    )
)
logger.addHandler(file_handler)

RUTAB = """ЁёАБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдежзийклмнопрстуфхцчшщъыьэюя"№;:?.,"""  # noqa
ENTAB = """~`F<DULT:PBQRKVYJGHCNEA{WXIO}SM">Zf,dult;pbqrkvyjghcnea[wxio]sm'.z@#$^&/?"""  # noqa
RU_EN = str.maketrans(RUTAB, ENTAB)
EN_RU = str.maketrans(ENTAB, RUTAB)


@pynvim.plugin
class Main(object):
    def __init__(self, nvim):
        self.nvim = NvimWrapper(nvim)
        self.input_start = self.input_end = None
        self.prev_limits = []

    @pynvim.function("MapLastInput", sync=True)
    def map_last_input(self, args):
        self.map_insert(lambda : self.nvim.get_cursor()[1] - self.input_start)

    @pynvim.function("MapLastInputWord", sync=True)
    def map_last_input_word(self, args):
        self.map_insert(self.get_last_word_nchars)

    @pynvim.autocmd("InsertEnter", sync=True)
    def on_insert_enter(self):
        if self.prev_limits:
            self.input_start, self.input_end = self.prev_limits.pop()
        else:
            self.input_start = self.input_end = self.nvim.get_cursor()[1]

    @pynvim.autocmd("TextChangedI", sync=True)
    def on_text_changed_i(self):
        cursor_col = self.nvim.get_cursor()[1]
        if cursor_col > self.input_end + 1 or cursor_col <= self.input_start:
            self.input_start = cursor_col
        self.input_end = cursor_col

    @pynvim.function("MapVisualSelection", sync=True)
    def map_visual(self, args):
        lo = self.nvim.get_left_visual_mark()
        hi = self.nvim.get_right_visual_mark() + 1
        mapped_text = self.nvim.map_text(self.nvim.get_line()[lo : hi])
        self.nvim.feedkeys(f"`<{hi - lo}s{mapped_text}")
        self.nvim.feedkeys("<esc>", replace_termcodes=True)

    def map_insert(self, nchars_getter):
        if self.input_start < self.nvim.get_cursor()[1] <= self.input_end:
            self.prev_limits.append([self.input_start, self.input_end])
            self.nvim.map_nchars_back(nchars_getter())
        self.nvim.toggle_language()

    def get_last_word_nchars(self):
        line = self.nvim.get_line()
        for i in reversed(range(self.input_start, self.nvim.get_cursor()[1])):
            if i and line[i - 1].isspace():
                break
        return self.nvim.get_cursor()[1] - i


class NvimWrapper(object):
    def __init__(self, nvim):
        self.nvim = nvim

    def feedkeys(self, keys, replace_termcodes=False):
        keys = self.nvim.replace_termcodes(keys) if replace_termcodes else keys
        self.nvim.feedkeys(keys)

    def map_nchars_back(self, n_chars):
        cursor_col = self.get_cursor()[1]
        crop = self.get_line()[cursor_col - n_chars : cursor_col]
        crop_mapped = self.map_text(crop)
        self.feedkeys("<BS>" * n_chars, replace_termcodes=True)
        self.feedkeys(crop_mapped)

    def get_left_visual_mark(self):
        return self.byte_2_char(self.nvim.current.buffer.mark("<")[1])

    def get_right_visual_mark(self):
        return self.byte_2_char(self.nvim.current.buffer.mark(">")[1])

    def get_cursor(self):
        cursor_row, cursor_col = self.nvim.current.window.cursor
        return [cursor_row, self.byte_2_char(cursor_col)]

    def get_line(self):
        return self.nvim.current.line

    def get_layout(self):
        return self.nvim.request("nvim_get_option", "iminsert")

    def toggle_language(self):
        self.nvim.command(f"set iminsert={int(not self.get_layout())}")

    def map_text(self, text):
        """Translate characters and switch language"""
        is_ru = self.get_layout()
        return text.translate(RU_EN) if is_ru else text.translate(EN_RU)

    def byte_2_char(self, col_byte):
        return len(self.get_line().encode()[:col_byte].decode())


if __name__ == "__main__":
    # launch nvim with
    # NVIM_LISTEN_ADDRESS=/tmp/nvim nvim
    from pynvim import attach
    nvim = attach("socket", path="/tmp/nvim")
