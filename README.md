# Gubbio 1151

Gioco per Game Boy Advance in C++20 con [Butano](https://github.com/GValiente/butano).
Codice con licenza MIT (`LICENSE`), contenuti CC BY-NC 4.0 (`LICENSE-CONTENUTI`), asset di terzi
in `CREDITI.md`.

## Compilare

    git submodule update --init
    bash build.sh

`build.sh` confronta Butano e devkitARM con `toolchain.lock` e si ferma se non coincidono, poi
compila, passa il gate zero-heap (`tools/check_zero_heap.sh`) e stampa lo SHA-256 della ROM.
I test: `python tools/check_no_skip.py` e `python -m unittest discover -s tests`.

## Quale ROM fa fede

**La ROM ufficiale e' l'artifact `gubbio1151-rom` della CI** (`.github/workflows/build.yml`),
compilata nell'immagine `devkitpro/devkitarm` bloccata per digest in `toolchain.lock`. Run dopo
run da' la stessa ROM, byte per byte. Per giocare la ROM di una fase si scarica quella.

La build sul PC Windows serve solo per provare. Ha lo stesso gcc 16.1.0 e le stesse librerie C
(libc, libm, crt0 e libsysbase hanno lo stesso SHA-256), ma `libgcc.a` e `libstdc++.a` della
distribuzione Windows sono diverse. Il risultato e' una ROM della stessa lunghezza, con le
sezioni delle stesse dimensioni, ma con alcune funzioni di maxmod in IWRAM in un altro ordine,
quindi con un altro SHA-256. Non dipende da percorsi o date: la ROM non ne contiene, e una build
con `-ffile-prefix-map` da' lo stesso SHA-256 di prima. `build.sh` lo ricorda con un avviso.

Criterio di F0 riscritto di conseguenza: lo SHA-256 della ROM e' stabile tra le run della CI, e
la ROM della CI si avvia in mGBA.
