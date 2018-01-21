"""Change last input word
If the last input is characters going after
previous input without it, change only the last input
and leave the preceeding text intact.

"""
import neovim
@neovim.plugin
class Main(object):
    def __init__(self, nvim):
        self.nvim = nvim

    @neovim.function('MapLayout')
    def map_layout(self, args, sync=True):
        cur_shift = {'Ё':1, 'ё':1, 'А':1, 'Б':1, 'В':1,
                     'Г':1, 'Д':1, 'Е':1, 'Ж':1, 'З':1,
                     'И':1, 'Й':1, 'К':1, 'Л':1, 'М':1,
                     'Н':1, 'О':1, 'П':1, 'Р':1, 'С':1,
                     'Т':1, 'У':1, 'Ф':1, 'Х':1, 'Ц':1,
                     'Ч':1, 'Ш':1, 'Щ':1, 'Ъ':1, 'Ы':1,
                     'Ь':1, 'Э':1, 'Ю':1, 'Я':1, 'а':1,
                     'б':1, 'в':1, 'г':1, 'д':1, 'е':1,
                     'ж':1, 'з':1, 'и':1, 'й':1, 'к':1,
                     'л':1, 'м':1, 'н':1, 'о':1, 'п':1,
                     'р':1, 'с':1, 'т':1, 'у':1, 'ф':1,
                     'х':1, 'ц':1, 'ч':1, 'ш':1, 'щ':1,
                     'ъ':1, 'ы':1, 'ь':1, 'э':1, 'ю':1,
                     'я':1, '"':0, '№':2, ';':1, ':':0,
                     '?':0, '.':0, ',':0, ' ':0, '\\':0
                    }
        self.nvim.command('normal `]')
        cur_line = list(self.nvim.current.line)

        shift_pos = dict()
        shift_pos[0] = 0
        for ii, char in enumerate(cur_line):
            if char in cur_shift:
                shift_pos[ii + 1] = shift_pos[ii] + 1 + cur_shift[char]
            else:
                shift_pos[ii + 1] = shift_pos[ii] + 1

        shift_pos_inv = dict([[v, k] for k, v in shift_pos.items()])

        last_ins_pos = self.nvim.current.buffer.mark('[')

        cursor = self.nvim.current.window.cursor
        if cursor[0] != last_ins_pos[0]:
            last_ins_pos[1] = 0

        cur_col = shift_pos_inv[cursor[1]]
        # cur_col_inv = shift_pos[cur_col - 1]
        # cur_col = shift_pos_inv[cur_col_inv]
        last_ins_pos = shift_pos_inv[last_ins_pos[1]]

        if cur_col == last_ins_pos + 1:
            return

        if cur_col != len(cur_line) - 1:
            cur_col -= 1

        for ii, char in enumerate(cur_line[:cur_col + 1][::-1]):
            # Skip trailing spaces
            if not char.isspace():
                break

        for jj, char in enumerate(cur_line[:cur_col - ii + 1][::-1]):
            if last_ins_pos > cur_col - ii - jj:
                break
            if not char.isspace():
                cur_line[cur_col - ii - jj] = self.map_char(char)
            else:
                break

        self.nvim.current.line = ''.join(cur_line)
        cur_line_new = self.nvim.current.line
        shift_pos_new = dict()
        shift_pos_new[0] = 0
        for ii, char in enumerate(cur_line_new):
            if char in cur_shift:
                shift_pos_new[ii + 1] = shift_pos_new[ii] + 1 + cur_shift[char]
            else:
                shift_pos_new[ii + 1] = shift_pos_new[ii] + 1
        self.nvim.current.window.cursor = (cursor[0], shift_pos_new[cur_col])
        self.nvim.feedkeys('a')

    def map_char(self, char):
        map_en_ru = {'~': 'Ё', '`': 'ё', 'F': 'А', '<': 'Б', 'D': 'В',
                     'U': 'Г', 'L': 'Д', 'T': 'Е', ':': 'Ж', 'P': 'З',
                     'B': 'И', 'Q': 'Й', 'R': 'К', 'K': 'Л', 'V': 'М',
                     'Y': 'Н', 'J': 'О', 'G': 'П', 'H': 'Р', 'C': 'С',
                     'N': 'Т', 'E': 'У', 'A': 'Ф', '{': 'Х', 'W': 'Ц',
                     'X': 'Ч', 'I': 'Ш', 'O': 'Щ', '}': 'Ъ', 'S': 'Ы',
                     'M': 'Ь', '"': 'Э', '>': 'Ю', 'Z': 'Я', 'f': 'а',
                     ',': 'б', 'd': 'в', 'u': 'г', 'l': 'д', 't': 'е',
                     ';': 'ж', 'p': 'з', 'b': 'и', 'q': 'й', 'r': 'к',
                     'k': 'л', 'v': 'м', 'y': 'н', 'j': 'о', 'g': 'п',
                     'h': 'р', 'c': 'с', 'n': 'т', 'e': 'у', 'a': 'ф',
                     '[': 'х', 'w': 'ц', 'x': 'ч', 'i': 'ш', 'o': 'щ',
                     ']': 'ъ', 's': 'ы', 'm': 'ь', "'": 'э', '.': 'ю',
                     'z': 'я', '@': '"', '#': '№', '$': ';', '^': ':',
                     '&': '?', '/': '.', '?': ',', ' ':' ', '\\':'\\',
                    }
        map_ru_en = dict([[v, k] for k, v in map_en_ru.items()])
        layout_mapping = map_en_ru.copy()
        layout_mapping.update(map_ru_en)
        if char.isprintable():
            return layout_mapping[char]
        return char
