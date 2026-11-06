# Gubbio 1151

Gioco per Game Boy Advance in C++20 con [Butano](https://github.com/GValiente/butano).
Codice con licenza MIT (`LICENSE`), contenuti CC BY-NC 4.0 (`LICENSE-CONTENUTI`), asset di terzi
in `CREDITI.md`.

## Compilare

    git submodule update --init
    bash build.sh

`build.sh` confronta Butano e devkitARM con `toolchain.lock` e si ferma se non coincidono, poi
compila, passa il gate zero-heap (`tools/check_zero_heap.sh`) e stampa lo SHA-256 della ROM.
I test: `python tools/check_no_skip.py` e `python -m unittest discover -s tests` (tutti, in serie).
Mentre si lavora c'e' il giro corto, vedi [docs/prove.md](docs/prove.md):

    python3 tools/prove.py            # solo i test toccati dalla modifica, in parallelo (+ mGBA se cambia la ROM)
    python3 tools/prove.py --tutte    # tutto, in parallelo: prima di fondere

## Architettura

[docs/architettura/ARCHITETTURA.md](docs/architettura/ARCHITETTURA.md): grafo dei moduli, matrice degli include,
matrice degli asset, aree e varchi. Sono generati dal codice con `python3 tools/grafo_moduli.py` e
`tests/test_architettura.py` fallisce se restano indietro. Lo stato della revisione a loop e' in
[LOOP_PROGRESS.md](LOOP_PROGRESS.md). La ROM si compila con zero avvisi (`-Werror` nel Makefile).

## Metodo di lavoro della serie

[docs/metodo/](docs/metodo/README.md): registro delle decisioni, lezioni imparate e percorso per fare da zero
il prossimo gioco della serie. Ogni decisione e ogni rifacimento si registrano li' nella stessa fusione che
li applica; `python3 tools/controlla_metodo.py` (e `tests/test_metodo.py`) controlla che il registro sia in
ordine.

## Regole di sviluppo GBA

Chi scrive codice C++ per il gioco (persone e thread di Claude) segue
[docs/regole_sviluppo_gba.md](docs/regole_sviluppo_gba.md): niente float, contenitori `bn::`, tabelle
`constexpr`, testo ridisegnato solo quando cambia, scene distrutte prima della successiva, campi delle struct
dal piu' grande al piu' piccolo, niente divisioni software nel ciclo di ogni frame, pannello di debug con
L+Select. Le regole sono controllate in automatico: `tools/controlla_regole_gba.py` (sul sorgente, nei test),
`tools/controlla_divisioni.py` (sulla ROM, in `build.sh`), `tools/controlla_struct.py` (l'ordine dei campi,
nella CI).

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
