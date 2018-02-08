
" The VimL/VimScript code is included in this sample plugin to demonstrate the
" two different approaches but it is not required you use VimL. Feel free to
" delete this code and proceed without it.

" ----- Handle cyrillic input --------- "
set keymap=russian-jcukenwin
set iminsert=0
set imsearch=0
highlight lCursor guifg=None guibg=Cyan
setlocal spell spelllang=ru_yo,en_us
setlocal spell spelllang=ru_ru,en_us

syntax spell toplevel
" ------------------------------------- "

function MapLayoutAndRestPos()
    let vv=winsaveview()
    exec MapLayout()
    call winrestview(vv)
endfunction

inoremap <c-k> <c-\><c-o>:call MapLayoutAndRestPos()<CR><c-^><esc>
inoremap <c-space> <c-^>
nnoremap <c-space> a<c-^><Esc>


