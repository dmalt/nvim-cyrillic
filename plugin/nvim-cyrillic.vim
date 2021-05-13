" ----- Handle cyrillic input --------- "
set keymap=russian-jcukenwin
set iminsert=0
set imsearch=0
highlight lCursor guifg=None guibg=Cyan
" ------------------------------------- "

inoremap <c-k> <c-\><c-o>:call MapLastInput()<CR>
vnoremap <c-k> :call MapVisualSelection()<CR>

" inoremap <c-u> <Esc>ua
" Switch language with <c-space>
inoremap <c-space> <c-^>
nnoremap <c-space> a<c-^><Esc>
cnoremap <c-space> <c-^>
