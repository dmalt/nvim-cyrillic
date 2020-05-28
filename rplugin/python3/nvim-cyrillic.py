"""Change last input word
If the last input is characters going after
previous input without it, change only the last input
and leave the preceding text intact.

"""
# a $jks$j
# a asjkkj
import neovim


@neovim.plugin
class Main(object):
    def __init__(self, nvim):
        self.nvim = nvim

    @neovim.function("MapLayout")
    def map_layout(self, args, sync=True):
        # Move cursor to where the last input ends
        # self.nvim.command("normal `]")
        cur_line = self.nvim.current.line
        # Cursor and mark positions are returned by API as bytes offsets
        # which matters for unicode characters which are encoded by more than
        # one byte per char
        cur_line_bytes = cur_line.encode()
        last_ins_pos = self.nvim.current.buffer.mark("[")
        cursor = self.nvim.current.window.cursor

        if cursor[0] != last_ins_pos[0]:
            # handle linebreaks during input
            last_ins_pos[1] = 0
        cursor_col = cursor[1]

        last_input_bytes = cur_line_bytes[last_ins_pos:cursor_col]
        last_input = last_input_bytes.decode()
        last_input_translate = "".join([self.map_char(c) for c in last_input])
        last_input_translate_bytes = last_input_translate.encode()

        new_cur_line_bytes = (
            cur_line_bytes[:last_ins_pos]
            + last_input_translate_bytes
            + cur_line_bytes[cursor_col:]
        )
        new_cur_line = new_cur_line_bytes.decode()
        self.nvim.current.line = new_cur_line
        self.nvim.current.window.cursor = [
            cursor[0],
            cursor[1]
            + len(last_input_translate_bytes)
            - len(last_input_bytes),
        ]

        # if cursor_col < last_ins_pos:
        #     return

        # if cur_col != len(cur_line) - 1:
        #     cur_col -= 1

        # # set ii to index of last nonspace character
        # for ii, char in enumerate(cur_line[: cur_col + 1][::-1]):
        #     # Skip trailing spaces
        #     if not char.isspace():
        #         break

        # for jj, char in enumerate(cur_line[: cur_col - ii + 1][::-1]):
        #     if last_ins_pos > cur_col - ii - jj:
        #         # we reached the start of previous input
        #         break
        #     if not char.isspace():
        #         cur_line[cur_col - ii - jj] = self.map_char(char)
        #     else:
        #         # translate only the last word
        #         break
        # self.nvim.current.line = "".join(cur_line)

        # -------- insert translated string and calc new cursor pos -------- #
        # cur_line_new = self.nvim.current.line
        # shift_pos_new = dict()
        # shift_pos_new[0] = 0
        # for ii, char in enumerate(cur_line_new):
        #     if char in cur_shift:
        #         shift_pos_new[ii + 1] = shift_pos_new[ii] + 1 + cur_shift[char]
        #     else:
        #         shift_pos_new[ii + 1] = shift_pos_new[ii] + 1
        # self.nvim.current.window.cursor = (cursor[0], shift_pos_new[cur_col])
        # self.nvim.feedkeys("a")
        # ------------------------------------------------------------------ #

    def map_char(self, char):
        map_en_ru = {
            "~": "Ё",
            "`": "ё",
            "F": "А",
            "<": "Б",
            "D": "В",
            "U": "Г",
            "L": "Д",
            "T": "Е",
            ":": "Ж",
            "P": "З",
            "B": "И",
            "Q": "Й",
            "R": "К",
            "K": "Л",
            "V": "М",
            "Y": "Н",
            "J": "О",
            "G": "П",
            "H": "Р",
            "C": "С",
            "N": "Т",
            "E": "У",
            "A": "Ф",
            "{": "Х",
            "W": "Ц",
            "X": "Ч",
            "I": "Ш",
            "O": "Щ",
            "}": "Ъ",
            "S": "Ы",
            "M": "Ь",
            '"': "Э",
            ">": "Ю",
            "Z": "Я",
            "f": "а",
            ",": "б",
            "d": "в",
            "u": "г",
            "l": "д",
            "t": "е",
            ";": "ж",
            "p": "з",
            "b": "и",
            "q": "й",
            "r": "к",
            "k": "л",
            "v": "м",
            "y": "н",
            "j": "о",
            "g": "п",
            "h": "р",
            "c": "с",
            "n": "т",
            "e": "у",
            "a": "ф",
            "[": "х",
            "w": "ц",
            "x": "ч",
            "i": "ш",
            "o": "щ",
            "]": "ъ",
            "s": "ы",
            "m": "ь",
            "'": "э",
            ".": "ю",
            "z": "я",
            "@": '"',
            "#": "№",
            "$": ";",
            "^": ":",
            "&": "?",
            "/": ".",
            "?": ",",
            " ": " ",
            "\\": "\\",
        }
        map_ru_en = dict([[v, k] for k, v in map_en_ru.items()])
        layout_mapping = map_en_ru.copy()
        layout_mapping.update(map_ru_en)
        if char.isprintable() and (char in layout_mapping):
            return layout_mapping[char]
        return char


if __name__ == "__main__":
    # launch nvim with
    # NVIM_LISTEN_ADDRESS=/tmp/nvim nvim
    from pynvim import attach

    nvim = attach("socket", path="/tmp/nvim")
    buffer = nvim.current.buffer
    buffer[0]
