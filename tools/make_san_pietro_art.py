#!/usr/bin/env python3
"""
Generatore di GRAFICA SEGNAPOSTO per il Quartiere di San Pietro (Gubbio 1151).

Produce graphics/san_pietro_ground.bmp (512x512, regular_bg) + la .json che lo accompagna.

Come impone docs/mappa_del_mondo.md sez. 5: il suolo e' DERIVATO dal mirror di
`san_pietro_tile_type` qui sotto, non disegnato a mano accanto alla griglia. Il mirror e'
verificato con gli STESSI assert, sugli STESSI punti notevoli, della `san_pietro_tile_type` in
include/san_pietro_collision.h — due copie che divergono in silenzio sono peggio di una sola.

RITAGLIO FOTOGRAFICO CHE SERVIREBBE (docs sez. 6), non ancora in ingredienti/: la facciata della
Chiesa di San Pietro, romanica con rimaneggiamenti successivi, inquadrata frontale e ritagliata
stretta al fronte dell'edificio (niente cielo, niente cavi, niente strada). Finche' non esiste,
questo generatore disegna la facciata in procedurale — vedi leggi_indici_bmp4() piu' sotto, che
ritorna None se il file manca e lascia il ripiego fare il suo lavoro.

    python tools/make_san_pietro_art.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_piazza_art import (TILE, canvas, check_and_write, leggi_indici_bmp4,   # noqa: E402
                              PALETTE_GROUND, C_WALL, C_WALL_DARK, C_JOINT, C_RAIL,
                              C_STONE, C_ARCH, C_WOOD, C_VOID)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "graphics")

# ----------------------------------------------------------------------------------------------
# Mirror di include/san_pietro_collision.h::san_pietro_tile_type — stessa forma, stesse assert
# sugli stessi punti notevoli, per la stessa ragione gia' scritta li'.
# ----------------------------------------------------------------------------------------------

SAN_PIETRO_WIDTH = 64
SAN_PIETRO_HEIGHT = 64

# Valori di TileType (piazza_grande_collision.h), NON ridefiniti: gli stessi nomi, gli stessi
# numeri. L'uscita verso Piazza Quaranta Martiri usa il valore 4 (EXIT_SAN_MARTINO); la facciata
# della chiesa riusa CONSOLI_FACADE(7), il portone DOOR_PRETORIO(10) — esattamente come fa il C++,
# e per la stessa ragione documentata li'.
(GROUND, WALL, RAILING, DOOR_CONSOLI, EXIT_SAN_MARTINO, EXIT_PORTA_ROMANA, FOUNTAIN,
 CONSOLI_FACADE, PRETORIO_FACADE, STAIRS, DOOR_PRETORIO, ROAD) = range(12)

EXIT_PQM_FIRST_X, EXIT_PQM_LAST_X = 28, 35
EXIT_PQM_FIRST_Y, EXIT_PQM_LAST_Y = 0, 1

VIA_FIRST_X, VIA_LAST_X = 30, 33
VIA_FIRST_Y, VIA_LAST_Y = 0, 34

STAIRS_INGRESSO_FIRST_Y, STAIRS_INGRESSO_LAST_Y = 4, 5

VICOLO_FIRST_X, VICOLO_LAST_X = 5, 58
VICOLO_FIRST_Y, VICOLO_LAST_Y = 15, 18

CAMPIELLO_FIRST_X, CAMPIELLO_LAST_X = 6, 14
CAMPIELLO_FIRST_Y, CAMPIELLO_LAST_Y = 13, 20

PIAZZETTA_FIRST_X, PIAZZETTA_LAST_X = 20, 43
PIAZZETTA_FIRST_Y, PIAZZETTA_LAST_Y = 24, 34

STAIRS_CHIESA_FIRST_X, STAIRS_CHIESA_LAST_X = 28, 35
STAIRS_CHIESA_FIRST_Y, STAIRS_CHIESA_LAST_Y = 35, 37

CHIESA_FIRST_X, CHIESA_LAST_X = 24, 39
CHIESA_FIRST_Y, CHIESA_LAST_Y = 38, 58
CHIESA_DOOR_FIRST_X, CHIESA_DOOR_LAST_X = 31, 32

RAILING_LAST_X = 1
RAILING_FIRST_Y, RAILING_LAST_Y = CHIESA_FIRST_Y, CHIESA_LAST_Y


def get_tile_type(x, y):
    """Mirror di include/san_pietro_collision.h::san_pietro_tile_type."""
    if x < 0 or x >= SAN_PIETRO_WIDTH or y < 0 or y >= SAN_PIETRO_HEIGHT:
        return WALL

    if EXIT_PQM_FIRST_Y <= y <= EXIT_PQM_LAST_Y and EXIT_PQM_FIRST_X <= x <= EXIT_PQM_LAST_X:
        return EXIT_SAN_MARTINO

    in_via = (VIA_FIRST_X <= x <= VIA_LAST_X and VIA_FIRST_Y <= y <= VIA_LAST_Y)

    if in_via and STAIRS_INGRESSO_FIRST_Y <= y <= STAIRS_INGRESSO_LAST_Y:
        return STAIRS

    if CHIESA_FIRST_X <= x <= CHIESA_LAST_X and CHIESA_FIRST_Y <= y <= CHIESA_LAST_Y:
        if y == CHIESA_FIRST_Y and CHIESA_DOOR_FIRST_X <= x <= CHIESA_DOOR_LAST_X:
            return DOOR_PRETORIO
        return CONSOLI_FACADE

    if (STAIRS_CHIESA_FIRST_Y <= y <= STAIRS_CHIESA_LAST_Y and
            STAIRS_CHIESA_FIRST_X <= x <= STAIRS_CHIESA_LAST_X):
        return STAIRS

    if in_via:
        return ROAD

    if VICOLO_FIRST_Y <= y <= VICOLO_LAST_Y and VICOLO_FIRST_X <= x <= VICOLO_LAST_X:
        return ROAD

    if (PIAZZETTA_FIRST_X <= x <= PIAZZETTA_LAST_X and
            PIAZZETTA_FIRST_Y <= y <= PIAZZETTA_LAST_Y):
        return GROUND

    if (CAMPIELLO_FIRST_X <= x <= CAMPIELLO_LAST_X and
            CAMPIELLO_FIRST_Y <= y <= CAMPIELLO_LAST_Y):
        return GROUND

    if x <= RAILING_LAST_X and RAILING_FIRST_Y <= y <= RAILING_LAST_Y:
        return RAILING

    return WALL


# Gli stessi punti notevoli su cui il C++ ha le proprie static_assert.
assert get_tile_type(31, 0) == EXIT_SAN_MARTINO
assert get_tile_type(31, 50) == CONSOLI_FACADE
assert get_tile_type(1, 45) == RAILING
assert get_tile_type(62, 45) == WALL
assert get_tile_type(31, 9) == ROAD            # l'ingresso da Piazza Quaranta Martiri
assert get_tile_type(31, 38) == DOOR_PRETORIO  # il portone, al centro del fronte
assert get_tile_type(22, 29) == GROUND         # il centro della piazzetta, fuori dalla via

# ----------------------------------------------------------------------------------------------
# Budget del Passo 9: 512 tile unici per tileset a 4bpp (docs/mappa_del_mondo.md sez. 5).
# ----------------------------------------------------------------------------------------------

MAX_TILES_GROUND = 512


def draw_san_pietro():
    """512x512: la griglia (64x64 tile) riempie l'intero canvas, come Piazza Quaranta Martiri."""
    w = h = 512
    px = canvas(w, h, C_VOID)

    # Gli ASSET FOTOGRAFICI, se ci sono. Il ripiego procedurale resta cio' che tiene la build
    # riproducibile per chi clona il progetto senza le foto (docs sez. 6).
    cotto, cotto_w, cotto_h = leggi_indici_bmp4("piazza_cotto.bmp")
    facciata, facc_w, facc_h = leggi_indici_bmp4("san_pietro_facciata.bmp")

    for ty in range(SAN_PIETRO_HEIGHT):
        for tx in range(SAN_PIETRO_WIDTH):
            kind = get_tile_type(tx, ty)
            x0, y0 = tx * TILE, ty * TILE

            for y in range(TILE):
                for x in range(TILE):
                    gx, gy = x0 + x, y0 + y

                    if kind == ROAD:
                        # Ciottolato: lo stesso trattamento delle altre vie gia' autorate.
                        c = C_WALL_DARK if (gx * 7 + gy * 13) % 5 else C_RAIL
                        c = C_JOINT if (gx + gy) % 9 == 0 else c
                    elif kind == GROUND:
                        if cotto:
                            # Il selciato e' lo stesso della piazza: e' la stessa citta' (gia'
                            # fatto per Largo del Bargello).
                            c = cotto[gy % cotto_h][gx % cotto_w]
                        else:
                            c = C_JOINT if (x == 0 or y == 0) else C_STONE
                    elif kind == STAIRS:
                        # Gradini: righe alternate chiare e scure, leggibili a 8 px.
                        c = C_WALL if (y % 2 == 0) else C_RAIL
                    elif kind == CONSOLI_FACADE:
                        # La facciata romanica rimaneggiata: pietra a corsi, con una cornice
                        # scura sopra il portone e lesene d'angolo — quel che un tile 8x8 concede.
                        c = C_WALL if (y % 4 != 3) else C_WALL_DARK

                        if facciata:
                            fx = gx - CHIESA_FIRST_X * TILE
                            fy = gy - CHIESA_FIRST_Y * TILE
                            if 0 <= fx < facc_w and 0 <= fy < facc_h:
                                c = facciata[fy][fx]
                        else:
                            if ty == CHIESA_FIRST_Y:
                                c = C_WALL_DARK   # cornice sopra il portone
                            elif tx in (CHIESA_FIRST_X, CHIESA_LAST_X):
                                c = C_WALL_DARK if x in (0, 7) else C_WALL   # lesene d'angolo
                    elif kind == DOOR_PRETORIO:
                        c = C_WOOD if 1 <= x <= 6 else C_WALL_DARK
                    elif kind == EXIT_SAN_MARTINO:
                        c = C_ARCH if (x + y) % 8 else C_WALL_DARK
                    elif kind == RAILING:
                        c = C_RAIL if y < 4 else C_WALL_DARK
                    else:   # WALL: tessuto edilizio minore
                        c = C_ARCH if (y % 4 == 3) else C_WALL_DARK

                    px[gy][gx] = c

    return w, h, px


def main():
    os.makedirs(OUT, exist_ok=True)
    print("[san-pietro-art] generazione degli asset segnaposto del Quartiere di San Pietro")

    w, h, px = draw_san_pietro()
    check_and_write("san_pietro_ground", w, h, px, PALETTE_GROUND, "regular_bg", MAX_TILES_GROUND)

    print("[san-pietro-art] fatto. NON e' arte definitiva: sostituire il .bmp mantenendo misure "
          "e 16 colori, senza toccare il C++.")


if __name__ == "__main__":
    main()
