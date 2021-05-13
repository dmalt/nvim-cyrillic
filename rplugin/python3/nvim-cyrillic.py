import pynvim


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
        line_bytes = self.nvim.current.line.encode("utf-8")
        lo, hi, cursor = self._get_last_input_byte_inds()

        is_ru = self.nvim.request("nvim_get_option", "iminsert")
        line_bytes, cursor_delta = _map_bytes(line_bytes, lo, hi, is_ru)
        self._toggle_language()
        new_cur_line = line_bytes.decode()
        self._replace_line(new_cur_line, cursor, cursor_delta)

    @pynvim.function("MapVisualSelection", sync=True)
    def map_visual(self, args):
        line_bytes = self.nvim.current.line.encode("utf-8")
        lo, hi, cursor = self._get_visual_selection()

        is_ru = self.nvim.request("nvim_get_option", "iminsert")
        line_bytes, cursor_delta = _map_bytes(line_bytes, lo, hi, is_ru)
        new_cur_line = line_bytes.decode()
        self._replace_line(new_cur_line, cursor, cursor_delta)

    def _replace_line(self, text, cursor, cursor_delta):
        self.nvim.current.line = text
        self.nvim.current.window.cursor = [cursor[0], cursor[1] + cursor_delta]

    def _get_visual_selection(self):
        lo = self.nvim.current.buffer.mark("<")[1]
        hi = self.nvim.current.buffer.mark(">")[1]
        cursor = self.nvim.current.window.cursor
        return lo, hi + 1, cursor

    def _get_last_input_byte_inds(self):
        """Get positions of last input start, last input end and cursor

        Positions are specified for byte strings. Neovim stores them like that.
        """
        start_ins_pos = self.nvim.current.buffer.mark("[")
        cursor = self.nvim.current.window.cursor
        if cursor[0] != start_ins_pos[0]:
            # handle linebreaks during input
            start_ins_col = 0
        else:
            start_ins_col = start_ins_pos[1]
        end_ins_col = cursor[1]
        return start_ins_col, end_ins_col, cursor

    def _toggle_language(self):
        is_ru = self.nvim.request("nvim_get_option", "iminsert")
        self.nvim.command(f"set iminsert={int(not is_ru)}")


def _map_bytes(text_bytes, lo, hi, is_ru):
    text_crop = text_bytes[lo:hi].decode("utf-8")
    crop_translate_bytes = _map_text(text_crop, is_ru).encode()
    delta = len(crop_translate_bytes) - (hi - lo)
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
