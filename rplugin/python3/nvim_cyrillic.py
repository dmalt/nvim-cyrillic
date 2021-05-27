import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import pynvim

# TODO
# 1) Refactor insert-mode mapping so they delete characters manually
#    with feedkeys("<BS>") and then reinsert them also with feedkeys.
#    This way I won't have to worry about the cursor position and last input
#    marks which are being distorted when the character encoding length changes
# 2) Refactor visual-mode mapping
# 3) Take care of multiline modes, doing nothing when the user tries to invoke
#    mapping in those modes.

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

rutab = """ЁёАБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдежзийклмнопрстуфхцчшщъыьэюя"№;:?.,"""  # noqa
entab = """~`F<DULT:PBQRKVYJGHCNEA{WXIO}SM">Zf,dult;pbqrkvyjghcnea[wxio]sm'.z@#$^&/?"""  # noqa
ru_en = str.maketrans(rutab, entab)
en_ru = str.maketrans(entab, rutab)


def _byte_2_char(text, col_byte):
    return len(text.encode()[:col_byte].decode())


def _char_2_byte(text, col_char):
    return len(text[:col_char].encode())


@pynvim.plugin
class Main(object):
    def __init__(self, nvim):
        self.nvim = nvim
        self.input_start = None
        self.input_end = None
        self.prev_limits = []

    @pynvim.function("MapLastInput", sync=True)
    def map_last_input(self, args):
        logger.debug("Mapping last input")
        self._map_insert(self._get_input_nchars)

    @pynvim.function("MapLastInputWord", sync=True)
    def map_last_input_word(self, args):
        logger.debug("Mapping last input word")
        self._map_insert(self._get_last_word_nchars)

    @pynvim.autocmd("InsertEnter", sync=True)
    def on_insert_enter(self):
        if self.prev_limits:
            self.input_start, self.input_end = self.prev_limits.pop()
            logger.debug(
                "Restoring to previous position:"
                f" start: {self.input_start}, end:{self.input_end}"
            )
            return
        self.input_start = self.input_end = self._get_cursor()[1]
        logger.debug(
            f"Entering insert mode. start:{self.input_start},"
            f" end:{self.input_end}"
        )

    @pynvim.autocmd("TextChangedI", sync=True)
    def on_text_changed_i(self):
        cursor_col = self._get_cursor()[1]

        if cursor_col == self.input_end + 1:
            self.input_end = cursor_col
        elif cursor_col > self.input_end + 1 or cursor_col <= self.input_start:
            self.input_start = self.input_end = cursor_col
        elif self.input_start < cursor_col < self.input_end:
            self.input_end = cursor_col
        logger.debug(
            f"on_text_changed: cursor:{cursor_col},"
            f" end: {self.input_end}, start:{self.input_start}"
        )

    def _get_cursor(self):
        line = self._get_line()
        cursor_row, cursor_col = self.nvim.current.window.cursor
        return [cursor_row, _byte_2_char(line, cursor_col)]

    def _get_line(self):
        return self.nvim.current.line

    def _map_insert(self, nchars_getter):
        logger.debug("In _map_insert")
        # Assert the cursor is between `[ and `] marks
        cursor_col = self._get_cursor()[1]
        left = self.input_start
        right = self.input_end
        logger.debug(
            f"_map_insert: left:{left}, right:{right}, cursor:{cursor_col}"
        )
        if not (left < cursor_col <= right):
            logger.debug(
                f"Bad cursor or marks position: cursor col:{cursor_col}"
            )
            self._toggle_language()
            return
        # Get the number of chars to map back from cursor with nchars_getter
        n_chars = nchars_getter()
        logger.debug(f"Removing {n_chars} backwards")
        self._map_chars_backwards_insert_mode(n_chars)
        logger.debug(f"{self.nvim.current.line}")
        self._toggle_language()

    def _get_input_nchars(self):
        # convert cursor position from byte ind to char ind
        cursor_col = self._get_cursor()[1]
        # convert `[ position from byte ind to char ind
        left_mark = self.input_start
        # return the difference
        return cursor_col - left_mark

    def _get_last_word_nchars(self):
        line = self.nvim.current.line
        # convert cursor position from byte ind to char ind
        cursor_col = self._get_cursor()[1]
        # convert `[ position from byte ind to char ind
        # get the index where I need to stop
        for i in range(cursor_col - 1, self.input_start - 1, -1):
            if line[i].isspace():
                i += 1
                break
        # return the difference
        return cursor_col - i

    def _map_chars_backwards_insert_mode(self, n_chars):
        # Crop the to-be-replaced line and map it to alt layout
        line = self._get_line()
        cursor_col = self._get_cursor()[1]
        crop = line[cursor_col - n_chars : cursor_col]
        logger.debug(f"mapping {cursor_col}, {crop}")
        crop_mapped = _map_text(crop, self._get_layout())
        # Delete this line with <BS>
        input_start_save = self.input_start
        logger.debug(f"saving start:{input_start_save}")
        self.nvim.feedkeys(self.nvim.replace_termcodes("<BS>" * n_chars))

        # Retype the cropped text in an alternative layout
        logger.debug(f"mapping to {crop_mapped}")
        self.nvim.feedkeys(crop_mapped)
        self.input_start = input_start_save
        self.input_end = self._get_cursor()[1]
        self.prev_limits.append([self.input_start, self.input_end])
        logger.debug(
            f"restoring start:{self.input_start}, end:{self.input_end}"
        )

    def _get_layout(self):
        return self.nvim.request("nvim_get_option", "iminsert")

    @pynvim.function("MapVisualSelection", sync=True)
    def map_visual(self, args):
        logger.debug(f"Current line: '{self.nvim.current.line}'")
        line_bytes = self.nvim.current.line.encode()
        lo, hi, cursor = self._get_visual_selection_byte_inds()

        is_ru = self.nvim.request("nvim_get_option", "iminsert")
        line_bytes, bytes_delta = _map_bytes(line_bytes, lo, hi, is_ru)
        new_cur_line = line_bytes.decode()
        self._replace_line(new_cur_line)
        after_last = hi + bytes_delta
        before_last = after_last - len(
            line_bytes[:after_last].decode()[-1].encode()
        )
        logger.debug(f"Before last: {before_last}, after last: {after_last}")
        self.nvim.current.window.cursor = [cursor[0], before_last]

    def _replace_line(self, text):
        logger.debug(f"New line: '{text}'")
        self.nvim.current.line = text

    def _get_visual_selection_byte_inds(self):
        lo = self.nvim.current.buffer.mark("<")[1]
        hi = self.nvim.current.buffer.mark(">")[1]
        cursor = self.nvim.current.window.cursor
        logger.debug(f"'<' mark: {lo}, '>' mark: {hi}, Cursor: {cursor}")
        line_bytes = self.nvim.current.line.encode()
        # hi mark is set on the last character in visual selection, i.e.
        # the last character will not be included in slice. Therefore we need
        # to forward hi ind by one character respecting its unicode number of
        # bytes; at the end of line hi should be forwarded by 1
        hi_offset = len(line_bytes[hi:].decode()[0].encode())
        if not hi_offset:
            # end of line case
            hi_offset = 1
        logger.debug(f"hi_offset: {hi_offset}")
        return lo, hi + hi_offset, cursor

    def _toggle_language(self):
        is_ru = self.nvim.request("nvim_get_option", "iminsert")
        self.nvim.command(f"set iminsert={int(not is_ru)}")


def _map_bytes(text_bytes, lo, hi, is_ru):
    text_crop = text_bytes[lo:hi].decode()
    crop_translate_bytes = _map_text(text_crop, is_ru).encode()
    delta = len(crop_translate_bytes) - (hi - lo)
    logger.debug(
        f"Bytes delta:{delta}, new message len: {len(crop_translate_bytes)},"
        f" hi: {hi}, lo: {lo}"
    )
    return text_bytes[:lo] + crop_translate_bytes + text_bytes[hi:], delta


def _map_text(text, is_ru):
    """Translate characters and switch language"""
    if is_ru:
        text_translate = text.translate(ru_en)
    else:
        text_translate = text.translate(en_ru)
    return text_translate


if __name__ == "__main__":
    # launch nvim with
    # NVIM_LISTEN_ADDRESS=/tmp/nvim nvim
    from pynvim import attach

    nvim = attach("socket", path="/tmp/nvim")
    buffer = nvim.current.buffer
    buffer[0]
