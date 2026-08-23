#!/usr/bin/env python3
"""
Generatore di GRAFICA SEGNAPOSTO per PIAZZA QUARANTA MARTIRI (Gubbio 1151).

Produce graphics/piazza_quaranta_martiri_ground.bmp (512x512, regular_bg) + la .json che lo
accompagna: il punto piu' basso della citta' (quota 0 m, docs/mappa_del_mondo.md sez. 2), la
grande piazza d'ingresso con la Loggia dei Tiratori e la Chiesa di San Francesco sul fianco SUD,
i giardini al centro, e le tre uscite verso San Martino, Piazza Grande e San Pietro.

Come impone docs/mappa_del_mondo.md sez. 5: il suolo e' DERIVATO dal mirror di
`piazza_quaranta_martiri_tile_type` qui sotto, non disegnato a mano accanto alla griglia. Il
mirror e' verificato con gli STESSI assert, sugli STESSI punti notevoli, della funzione C++ in
include/piazza_quaranta_martiri_collision.h -- due copie che divergono in silenzio sono peggio
di una sola.

    python tools/make_piazza_quaranta_martiri_art.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_piazza_art import (TILE, canvas, check_and_write, leggi_indici_bmp4,   # noqa: E402
                              PALETTE_GROUND, C_WALL, C_WALL_DARK, C_JOINT, C_RAIL,
                              C_STONE, C_ARCH, C_WOOD, C_VOID)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "graphics")

# Indice 12 della palette condivisa (photo_to_tiles.PALETTE_PIAZZA): "vegetazione". E' il colore
# dei giardini al centro della piazza, che sono prato aperto e non selciato -- l'unico punto di
# tutta quest'area che non condivide la tinta di cotto/pietra delle altre.
C_GRASS = 12

# ----------------------------------------------------------------------------------------------
# Mirror di include/piazza_quaranta_martiri_collision.h::piazza_quaranta_martiri_tile_type
# ----------------------------------------------------------------------------------------------

PQM_WIDTH = 64
PQM_HEIGHT = 64

# Gli stessi nomi e numeri di TileType (piazza_grande_collision.h), NON ridefiniti. EXIT_SAN_
# MARTINO (4) e' riusato per l'uscita verso San Martino, EXIT_PORTA_ROMANA (5) per quella verso
# Piazza Grande, FOUNTAIN (6) per quella verso San Pietro -- l'assegnazione data all'area, la
# stessa dell'header C++.
(GROUND, WALL, RAILING, DOOR_CONSOLI, EXIT_SAN_MARTINO, EXIT_PORTA_ROMANA, FOUNTAIN,
 CONSOLI_FACADE, PRETORIO_FACADE, STAIRS, DOOR_PRETORIO, ROAD, EXIT_TERZA, EXIT_QUARTA) = range(14)

EXIT_SAN_MARTINO_FIRST_X, EXIT_SAN_MARTINO_LAST_X = 28, 35
EXIT_SAN_MARTINO_FIRST_Y, EXIT_SAN_MARTINO_LAST_Y = 0, 1

EXIT_PIAZZA_GRANDE_FIRST_X, EXIT_PIAZZA_GRANDE_LAST_X = PQM_WIDTH - 2, PQM_WIDTH - 1
EXIT_PIAZZA_GRANDE_FIRST_Y, EXIT_PIAZZA_GRANDE_LAST_Y = 28, 35

EXIT_SAN_PIETRO_FIRST_X, EXIT_SAN_PIETRO_LAST_X = 28, 35
EXIT_SAN_PIETRO_FIRST_Y, EXIT_SAN_PIETRO_LAST_Y = PQM_HEIGHT - 2, PQM_HEIGHT - 1

LOGGIA_FIRST_X, LOGGIA_LAST_X = 2, 5
LOGGIA_FIRST_Y, LOGGIA_LAST_Y = 8, 47

SAN_FRANCESCO_FIRST_X, SAN_FRANCESCO_LAST_X = 2, 15
SAN_FRANCESCO_FIRST_Y, SAN_FRANCESCO_LAST_Y = 48, 61

PERIMETRO_THICK = 2

GIARDINO_FIRST_X, GIARDINO_LAST_X = 22, 47
GIARDINO_FIRST_Y, GIARDINO_LAST_Y = 16, 49


def piazza_quaranta_martiri_tile_type(x, y):
    """Mirror di include/piazza_quaranta_martiri_collision.h. Mappa ruotata con l'ovest in alto:
    alto = uscita verso San Martino, basso = uscita verso San Pietro, sinistra = Loggia dei
    Tiratori e Chiesa di San Francesco (sud reale), destra = uscita verso Piazza Grande (nord
    reale)."""
    if x < 0 or x >= PQM_WIDTH or y < 0 or y >= PQM_HEIGHT:
        return WALL

    if (EXIT_SAN_MARTINO_FIRST_Y <= y <= EXIT_SAN_MARTINO_LAST_Y and
            EXIT_SAN_MARTINO_FIRST_X <= x <= EXIT_SAN_MARTINO_LAST_X):
        return EXIT_SAN_MARTINO

    if (EXIT_PIAZZA_GRANDE_FIRST_X <= x <= EXIT_PIAZZA_GRANDE_LAST_X and
            EXIT_PIAZZA_GRANDE_FIRST_Y <= y <= EXIT_PIAZZA_GRANDE_LAST_Y):
        return EXIT_PORTA_ROMANA

    if (EXIT_SAN_PIETRO_FIRST_Y <= y <= EXIT_SAN_PIETRO_LAST_Y and
            EXIT_SAN_PIETRO_FIRST_X <= x <= EXIT_SAN_PIETRO_LAST_X):
        return FOUNTAIN

    if (LOGGIA_FIRST_X <= x <= LOGGIA_LAST_X and LOGGIA_FIRST_Y <= y <= LOGGIA_LAST_Y):
        return CONSOLI_FACADE

    if (SAN_FRANCESCO_FIRST_X <= x <= SAN_FRANCESCO_LAST_X and
            SAN_FRANCESCO_FIRST_Y <= y <= SAN_FRANCESCO_LAST_Y):
        return PRETORIO_FACADE

    if (x < PERIMETRO_THICK or y < PERIMETRO_THICK or
            x > PQM_WIDTH - 1 - PERIMETRO_THICK or y > PQM_HEIGHT - 1 - PERIMETRO_THICK):
        return WALL

    if (GIARDINO_FIRST_X <= x <= GIARDINO_LAST_X and GIARDINO_FIRST_Y <= y <= GIARDINO_LAST_Y):
        return GROUND

    return ROAD


# Gli stessi punti notevoli su cui il C++ ha le proprie static_assert.
assert piazza_quaranta_martiri_tile_type(31, 0) == EXIT_SAN_MARTINO
assert piazza_quaranta_martiri_tile_type(63, 31) == EXIT_PORTA_ROMANA
assert piazza_quaranta_martiri_tile_type(31, 63) == FOUNTAIN
assert piazza_quaranta_martiri_tile_type(3, 20) == CONSOLI_FACADE     # Loggia dei Tiratori
assert piazza_quaranta_martiri_tile_type(3, 55) == PRETORIO_FACADE    # Chiesa di San Francesco
assert piazza_quaranta_martiri_tile_type(34, 32) == GROUND            # centro dei giardini
assert piazza_quaranta_martiri_tile_type(31, 0) != piazza_quaranta_martiri_tile_type(31, 63)
assert piazza_quaranta_martiri_tile_type(31, 2) not in (WALL, CONSOLI_FACADE, PRETORIO_FACADE)
assert piazza_quaranta_martiri_tile_type(61, 31) not in (WALL, CONSOLI_FACADE, PRETORIO_FACADE)
assert piazza_quaranta_martiri_tile_type(31, 61) not in (WALL, CONSOLI_FACADE, PRETORIO_FACADE)

# ----------------------------------------------------------------------------------------------
# Budget del Passo 9, in tile unici a 4bpp. Tetto duro: 512 per tileset.
# ----------------------------------------------------------------------------------------------

MAX_TILES_GROUND = 512


def draw_ground():
    # L'ingrediente fotografico gia' usato per il selciato di tutte le altre aree: e' la stessa
    # citta'. Nessun ritaglio fotografico esiste ancora per la Loggia dei Tiratori o per San
    # Francesco (vedi la nota in fondo al file): entrambe restano interamente procedurali.
    cotto, cotto_w, cotto_h = leggi_indici_bmp4("piazza_cotto.bmp")

    w = h = 512   # PQM_WIDTH * TILE == PQM_HEIGHT * TILE == 512: nessun margine, come 512x512.
    px = canvas(w, h, C_VOID)

    for ty in range(PQM_HEIGHT):
        for tx in range(PQM_WIDTH):
            kind = piazza_quaranta_martiri_tile_type(tx, ty)
            x0, y0 = tx * TILE, ty * TILE

            # Coordinate LOCALI dentro i due monumenti, usate per tenere basso il numero di tile
            # unici (Passo 9): un disegno che variasse su ogni singola tile del monumento, invece
            # che periodicamente, costerebbe centinaia di tile unici da solo.
            loggia_depth = tx - LOGGIA_FIRST_X          # 0..3, profondita' del portico
            loggia_row = ty - LOGGIA_FIRST_Y            # 0.., posizione lungo la lunghezza
            sf_dx = tx - SAN_FRANCESCO_FIRST_X           # 0..13
            sf_dy = ty - SAN_FRANCESCO_FIRST_Y           # 0..13

            for y in range(TILE):
                for x in range(TILE):
                    gx, gy = x0 + x, y0 + y

                    if kind == ROAD:
                        # Il grande selciato aperto della piazza: stesso acciottolato delle vie
                        # gia' consegnate, e' la stessa citta'.
                        c = C_WALL_DARK if (gx * 7 + gy * 13) % 5 else C_RAIL
                        c = C_JOINT if (gx + gy) % 9 == 0 else c
                    elif kind == GROUND:
                        # I giardini al centro: prato, non selciato. Un leggero scacchiera fra
                        # tile adiacenti basta a rompere la piattezza senza costare tile unici.
                        c = C_GRASS if (tx + ty) % 2 == 0 else C_ARCH
                    elif kind in (EXIT_SAN_MARTINO, EXIT_PORTA_ROMANA, FOUNTAIN):
                        # Le tre uscite: varchi in ombra, come quelle di Piazza Grande e delle
                        # altre aree gia' consegnate.
                        c = C_ARCH if (x + y) % 8 else C_WALL_DARK
                    elif kind == CONSOLI_FACADE:
                        # LOGGIA DEI TIRATORI: portico ad arcate su pilastri. Il lato rivolto alla
                        # piazza (la tile piu' profonda, loggia_depth == 3) alterna arcata aperta
                        # e pilastro ogni 5 tile lungo la lunghezza; il resto del portico, verso
                        # il muro di fondo, resta pietra chiara a corsi.
                        if loggia_depth == LOGGIA_LAST_X - LOGGIA_FIRST_X and loggia_row % 5 < 3:
                            c = C_ARCH if y >= 2 else C_WALL_DARK   # arcata: vano scuro sotto l'imposta
                        else:
                            c = C_WALL if y % 4 != 3 else C_WALL_DARK   # pietra a corsi
                    elif kind == PRETORIO_FACADE:
                        # CHIESA DI SAN FRANCESCO: fronte a corsi di pietra, con due segni che la
                        # distinguono da un palazzo civico -- il campanile (angolo verso Piazza
                        # Grande, cioe' verso il corso, alto) e l'abside poligonale (angolo
                        # opposto, verso il muro di fondo).
                        if sf_dx >= 11 and sf_dy <= 2:
                            # Campanile: fasce verticali strette, il segno di una torre.
                            c = C_WALL_DARK if x % 3 == 0 else C_WALL
                        elif sf_dx <= 2 and sf_dy <= 2:
                            # Abside poligonale: un taglio diagonale invece dello spigolo retto.
                            c = C_ARCH if (x + y) < 4 else C_WALL
                        else:
                            c = C_WALL if y % 4 != 3 else C_WALL_DARK
                    else:   # WALL: tessuto minore che chiude il perimetro
                        c = C_WALL if y % 4 != 3 else C_WALL_DARK

                    px[gy][gx] = c

    return w, h, px


def main():
    os.makedirs(OUT, exist_ok=True)
    print("[piazza-quaranta-martiri-art] generazione degli asset segnaposto di Piazza Quaranta "
          "Martiri")

    w, h, px = draw_ground()
    check_and_write("piazza_quaranta_martiri_ground", w, h, px, PALETTE_GROUND, "regular_bg",
                     MAX_TILES_GROUND)

    print("[piazza-quaranta-martiri-art] fatto. NON e' arte definitiva: i ritagli fotografici "
          "che servirebbero (docs/mappa_del_mondo.md sez. 6), oggi assenti in ingredienti/, sono "
          "una foto FRONTALE della Loggia dei Tiratori (le arcate su pilastri, senza auto in "
          "sosta davanti) e una foto della Chiesa di San Francesco che mostri insieme il "
          "campanile e l'abside poligonale.")


if __name__ == "__main__":
    main()
