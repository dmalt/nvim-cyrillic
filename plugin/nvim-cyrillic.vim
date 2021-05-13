" ----- Handle cyrillic input --------- "
set keymap=russian-jcukenwin
set iminsert=0
set imsearch=0
highlight lCursor guifg=None guibg=Cyan
" ------------------------------------- "

" function MapLayoutAndRestPos()
"     let vv=winsaveview()
"     exec MapLayout()
"     call winrestview(vv)
" endfunction

function MyMapLayout()
    " let vv=winsaveview()
    call MapLayout()

    " call winrestview(vv)
    " normal m]
endfunction

inoremap <c-k> <c-\><c-o>:call MyMapLayout()<CR>

" inoremap <c-u> <Esc>ua
inoremap <c-space> <c-^>
nnoremap <c-space> a<c-^><Esc>
cnoremap <c-space> <c-^>
