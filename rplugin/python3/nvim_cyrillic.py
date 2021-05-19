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

rutab = """ЁёАБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдежзийклмнопрстуфхцчшщъыьэюя"№;:?.,"""  # noqa
entab = """~`F<DULT:PBQRKVYJGHCNEA{WXIO}SM">Zf,dult;pbqrkvyjghcnea[wxio]sm'.z@#$^&/?"""  # noqa
# rutab = """ЁёАБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдежзийклмнопрстуфхцчшщъыьэюя"""  # noqa
# entab = """~`F<DULT:PBQRKVYJGHCNEA{WXIO}SM">Zf,dult;pbqrkvyjghcnea[wxio]sm'.z"""  # noqa
ru_en = str.maketrans(rutab, entab)
en_ru = str.maketrans(entab, rutab)


@pynvim.plugin
class Main(object):
    def __init__(self, nvim):
        self.nvim = nvim

    @pynvim.function("MapLastInput", sync=True)
    def map_last_input(self, args):
        # Cursor and mark positions are returned by API as bytes offsets
        # which matters for unicode characters which are encoded by more than
        # one byte per char
        logger.debug("Entering map_last_input")
        logger.debug(f"Current line: '{self.nvim.current.line}'")
        line_bytes = self.nvim.current.line.encode("utf-8")
        lo, hi, cursor = self._get_last_input_byte_inds()

        is_ru = self.nvim.request("nvim_get_option", "iminsert")
        line_bytes, bytes_delta = _map_bytes(line_bytes, lo, hi, is_ru)
        self._toggle_language()
        new_cur_line = line_bytes.decode()
        self._replace_line(new_cur_line)
        self.nvim.current.window.cursor = [cursor[0], cursor[1] + bytes_delta]

    @pynvim.function("MapVisualSelection", sync=True)
    def map_visual(self, args):
        logger.debug(f"Current line: '{self.nvim.current.line}'")
        line_bytes = self.nvim.current.line.encode("utf-8")
        lo, hi, cursor = self._get_visual_selection_byte_inds()

        is_ru = self.nvim.request("nvim_get_option", "iminsert")
        line_bytes, bytes_delta = _map_bytes(line_bytes, lo, hi, is_ru)
        new_cur_line = line_bytes.decode()
        self._replace_line(new_cur_line)
        after_last = hi + bytes_delta
        before_last = after_last - len(
            new_cur_line[after_last - 1 : after_last].encode("utf-8")
        )
        self.nvim.current.window.cursor = [cursor[0], before_last]

    def _replace_line(self, text):
        logger.debug(f"New line: '{text}'")
        self.nvim.current.line = text

    def _get_visual_selection_byte_inds(self):
        lo = self.nvim.current.buffer.mark("<")[1]
        hi = self.nvim.current.buffer.mark(">")[1]
        cursor = self.nvim.current.window.cursor
        logger.debug(f"'<' mark: {lo}, '>' mark: {hi}, Cursor: {cursor}")
        line_bytes = self.nvim.current.line.encode("utf-8")
        # hi mark is set on the last character in visual selection, i.e.
        # the last character will not be included in slice. Therefore we need
        # to forward hi ind by one character respecting its unicode number of
        # bytes; at the end of line hi should be forwarded by 1
        hi_offset = len(line_bytes[hi:].decode()[0].encode("utf-8"))
        if not hi_offset:
            # end of line case
            hi_offset = 1
        logger.debug(f"hi_offset: {hi_offset}")
        return lo, hi + hi_offset, cursor

    def _get_last_input_byte_inds(self):
        """Get positions of last input start, last input end and cursor

        Positions are specified for byte strings. Neovim stores them like that.
        """
        lo_mark = self.nvim.current.buffer.mark("[")
        cursor = self.nvim.current.window.cursor
        if cursor[0] != lo_mark[0]:
            # handle linebreaks during input
            lo = 0
        else:
            lo = lo_mark[1]
        hi = cursor[1]
        logger.debug(
            f"'[' mark: {lo_mark}, lo: {lo}, hi: {hi}, Cursor: {cursor}"
        )
        return lo, hi, cursor

    def _toggle_language(self):
        is_ru = self.nvim.request("nvim_get_option", "iminsert")
        self.nvim.command(f"set iminsert={int(not is_ru)}")


def _map_bytes(text_bytes, lo, hi, is_ru):
    text_crop = text_bytes[lo:hi].decode("utf-8")
    crop_translate_bytes = _map_text(text_crop, is_ru).encode()
    delta = len(crop_translate_bytes) - (hi - lo)
    logger.debug(
        f"Cursor delta:{delta}, new message len: {len(crop_translate_bytes)},"
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
