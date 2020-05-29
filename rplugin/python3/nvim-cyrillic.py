"""Change last input word
If the last input is characters going after
previous input without it, change only the last input
and leave the preceding text intact.

"""
import pynvim


# rutab = """ЁёАБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдежзийклмнопрстуфхцчшщъыьэюя"№;:?.,"""  # noqa
# entab = """~`F<DULT:PBQRKVYJGHCNEA{WXIO}SM">Zf,dult;pbqrkvyjghcnea[wxio]sm'.z@#$^&/?"""  # noqa
rutab = """ЁёАБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдежзийклмнопрстуфхцчшщъыьэюя"""  # noqa
entab = """~`F<DULT:PBQRKVYJGHCNEA{WXIO}SM">Zf,dult;pbqrkvyjghcnea[wxio]sm'.z"""  # noqa
ru_en = str.maketrans(rutab, entab)
en_ru = str.maketrans(entab, rutab)


@pynvim.plugin
class Main(object):
    def __init__(self, nvim):
        self.nvim = nvim

    @pynvim.function("MapLayout", sync=True)
    def map_layout(self, args):
        cur_line = self.nvim.current.line
        # Cursor and mark positions are returned by API as bytes offsets
        # which matters for unicode characters which are encoded by more than
        # one byte per char
        cur_line_bytes = cur_line.encode("utf-8")
        start_ins_pos = self.nvim.current.buffer.mark("[")
        cursor = self.nvim.current.window.cursor

        if cursor[0] != start_ins_pos[0]:
            # handle linebreaks during input
            start_ins_col = 0
        else:
            start_ins_col = start_ins_pos[1]
        end_ins_col = cursor[1]

        last_input_bytes = cur_line_bytes[start_ins_col:end_ins_col]
        last_input = last_input_bytes.decode("utf-8")
        is_ru = self.nvim.request("nvim_get_option", "iminsert")
        if is_ru:
            self.nvim.command("set iminsert=0")  # change input language
            last_input_translate = last_input.translate(ru_en)
        else:
            self.nvim.command("set iminsert=1")  # change input language
            last_input_translate = last_input.translate(en_ru)

        last_input_translate_bytes = last_input_translate.encode()

        new_cur_line_bytes = (
            cur_line_bytes[:start_ins_col]
            + last_input_translate_bytes
            + cur_line_bytes[end_ins_col:]
        )
        new_cur_line = new_cur_line_bytes.decode()
        self.nvim.current.line = new_cur_line
        cursor_delta = len(last_input_translate_bytes) - len(last_input_bytes)
        self.nvim.current.window.cursor = [cursor[0], cursor[1] + cursor_delta]


if __name__ == "__main__":
    # launch nvim with
    # NVIM_LISTEN_ADDRESS=/tmp/nvim nvim
    from pynvim import attach

    nvim = attach("socket", path="/tmp/nvim")
    buffer = nvim.current.buffer
    buffer[0]
