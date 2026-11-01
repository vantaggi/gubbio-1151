# stile/ — la Guida di stile in dati

La [Guida di stile](https://claude.ai/artifact/5Pw6CLTog1JH9u1uvhNmpm) (fase FS) e' la fonte delle
decisioni; questa cartella le traduce in file che i generatori e il gioco leggono.

| Scelta | Dato | Come nasce | Header |
| :-- | :-- | :-- | :-- |
| 3 palette | `dati/palette.json` | `genera.py` da parametri (9 rampe, 42 colori, hue shift 10, notte) | `include/stile/palette.h` |
| 8 font | `dati/font.json` | disegnato a mano come dati (94 glifi, cella 10, maiuscole 7 px) | `include/stile/font.h` |
| 9 interfaccia | `dati/cornice.json` | `genera.py` (tile 8x8 4bpp, 9-slice, cartiglio, cursore, disposizione) | `include/stile/cornice.h` |
| 10 ritratti | `dati/ritratti.json` | maschere di ruoli 32x32 per strato, 3 espressioni | `graphics/ritratto_*.bmp` |
| 11 animazione | `dati/pose.json` | `genera.py` (scheletro 16x32, tempi in vblank) | `include/stile/pose.h` |
| 12 titolo | `dati/logo.json` | capitali lombarde disegnate come dati | `graphics/logo*.bmp` |

Le scelte 1, 2, 4, 5, 6, 7 sono regole, non tabelle: stanno nei controlli (luce da sinistra
su ritratti e tessere, contorno quasi nero automatico, sprite 16x32 con corpo 16x24, nessun
pixel fotografico).

## Flusso

    python stile/genera.py          # dopo aver cambiato i parametri di palette, cornice o pose
    python stile/esporta_cpp.py     # rigenera include/stile/*.h (mai a mano)
    python stile/genera_bmp.py      # rigenera graphics/*.bmp per grit (mai a mano)
    python stile/anteprime.py a.png # tavola di controllo (richiede Pillow)
    python -m unittest discover -s tests -p "test_stile_*.py"

`stile.py` ha una funzione `controlla_*` per ogni dato. I test la chiamano sul dato vero e su
copie guastate apposta (prove negative): ogni controllo ha visto fallire il suo difetto.
I test usano solo la libreria standard, quindi girano anche nella CI devkitARM.
`src/stile_controlli.cpp` ripete i controlli essenziali con `static_assert`: se i dati escono
dalle regole, la ROM non compila.

## Testi del gioco e font

`tests/test_stile_font.py` legge i testi destinati allo schermo (`include/testi*.h`,
`include/dialog*.h`, `testi/**/*.txt`) e le frasi fisse della Guida: ogni carattere usato
deve avere un glifo. Quando nasce il file dei testi, va aggiunto a `TESTI_DEL_GIOCO` se ha un
altro nome.

## BMP per grit

`genera_bmp.py` scrive in `graphics/` BMP indicizzati a 4bpp con il loro `.json`:
`ritratto_<nome>` (sprite 32x32, 3 fotogrammi = calmo, preoccupato, deciso), `logo` e
`logo_mono` (regular_bg 256x256, logo a x2 in alto), `cornice_dialogo` e `cornice_menu`
(regular_bg 256x256 nella disposizione della scelta 9). L'indice 0 e' il trasparente. Per
riquadri di misura variabile si usano invece i tile di `include/stile/cornice.h`.
`tests/test_stile_bmp.py` controlla che i BMP siano allineati ai dati e che i colori riletti
come fa grit (canale >> 3) siano esattamente le parole BGR555 della palette.
