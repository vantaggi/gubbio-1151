#!/usr/bin/env python3
"""
Generatore di GRAFICA SEGNAPOSTO per il Quartiere di San Martino (Gubbio 1151).

Produce graphics/san_martino_ground.bmp (256x512, regular_bg) + la .json che lo accompagna.

Come impone docs/mappa_del_mondo.md sez. 5: il suolo e' DERIVATO dal mirror di
`san_martino_tile_type` qui sotto, non disegnato a mano accanto alla griglia. Il mirror e'
verificato con gli STESSI assert, sugli STESSI punti notevoli, della `san_martino_tile_type` in
include/san_martino_collision.h — due copie che divergono in silenzio sono peggio di una sola.

    python tools/make_san_martino_art.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_piazza_art import (TILE, canvas, check_and_write, leggi_indici_bmp4,   # noqa: E402
                              PALETTE_GROUND, C_WALL, C_WALL_DARK, C_JOINT, C_RAIL,
                              C_STONE, C_ARCH, C_WOOD, C_VOID)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "graphics")

# ----------------------------------------------------------------------------------------------
# Mirror di include/san_martino_collision.h
# ----------------------------------------------------------------------------------------------

SAN_MARTINO_WIDTH = 32
SAN_MARTINO_HEIGHT = 40

# Valori di TileType (piazza_grande_collision.h), NON ridefiniti: gli stessi nomi, gli stessi
# numeri. USCITA_BARGELLO usa il valore 4 (EXIT_SAN_MARTINO), PORTA_SANTA_LUCIA il valore 3
# (DOOR_CONSOLI, riusato: e' il valore piu' vicino concettualmente a "una porta" fra i tre che
# is_transition() in piazza_grande_collision.h riconosce davvero — vedi la nota in testa
# all'header C++), USCITA_PQM il valore 5 (EXIT_PORTA_ROMANA).
(GROUND, WALL, RAILING, DOOR_CONSOLI, EXIT_SAN_MARTINO, EXIT_PORTA_ROMANA, FOUNTAIN,
 CONSOLI_FACADE, PRETORIO_FACADE, STAIRS, DOOR_PRETORIO, ROAD, EXIT_TERZA, EXIT_QUARTA) = range(14)

CORSO_FIRST_X, CORSO_LAST_X = 14, 17

RAMO_PQM_FIRST_X, RAMO_PQM_LAST_X = 0, CORSO_LAST_X
RAMO_PQM_FIRST_Y, RAMO_PQM_LAST_Y = 24, 27

CAMPIELLO_FIRST_X, CAMPIELLO_LAST_X = 10, 21
CAMPIELLO_FIRST_Y, CAMPIELLO_LAST_Y = 18, 23

EXIT_BARGELLO_FIRST_Y, EXIT_BARGELLO_LAST_Y = 0, 1
EXIT_PORTA_SANTA_LUCIA_FIRST_Y = SAN_MARTINO_HEIGHT - 2
EXIT_PORTA_SANTA_LUCIA_LAST_Y = SAN_MARTINO_HEIGHT - 1
EXIT_PQM_FIRST_X, EXIT_PQM_LAST_X = 0, 1

STAIRS_BARGELLO_FIRST_Y, STAIRS_BARGELLO_LAST_Y = 4, 6
STAIRS_PQM_FIRST_X, STAIRS_PQM_LAST_X = 4, 6

RAILING_FIRST_Y, RAILING_LAST_Y = 8, 12


def san_martino_tile_type(x, y):
    """Mirror di include/san_martino_collision.h. Mappa ruotata con l'ovest in alto: alto = uscita
    verso il Bargello (a monte), basso = Porta di Santa Lucia, sinistra = uscita verso Piazza
    Quaranta Martiri (a valle, sud reale), destra = case (nord reale, nessun varco)."""
    if x < 0 or x >= SAN_MARTINO_WIDTH or y < 0 or y >= SAN_MARTINO_HEIGHT:
        return WALL

    in_corso = CORSO_FIRST_X <= x <= CORSO_LAST_X
    in_ramo_pqm = (RAMO_PQM_FIRST_Y <= y <= RAMO_PQM_LAST_Y and
                   RAMO_PQM_FIRST_X <= x <= RAMO_PQM_LAST_X)

    if in_corso and EXIT_BARGELLO_FIRST_Y <= y <= EXIT_BARGELLO_LAST_Y:
        return EXIT_SAN_MARTINO
    if in_corso and EXIT_PORTA_SANTA_LUCIA_FIRST_Y <= y <= EXIT_PORTA_SANTA_LUCIA_LAST_Y:
        return DOOR_CONSOLI
    if in_ramo_pqm and EXIT_PQM_FIRST_X <= x <= EXIT_PQM_LAST_X:
        return EXIT_PORTA_ROMANA

    if in_corso and STAIRS_BARGELLO_FIRST_Y <= y <= STAIRS_BARGELLO_LAST_Y:
        return STAIRS
    if in_ramo_pqm and STAIRS_PQM_FIRST_X <= x <= STAIRS_PQM_LAST_X:
        return STAIRS

    if in_corso or in_ramo_pqm:
        return ROAD

    if (CAMPIELLO_FIRST_X <= x <= CAMPIELLO_LAST_X and
            CAMPIELLO_FIRST_Y <= y <= CAMPIELLO_LAST_Y):
        return GROUND

    if x == 0 and RAILING_FIRST_Y <= y <= RAILING_LAST_Y:
        return RAILING

    return WALL


# Gli stessi punti notevoli su cui il C++ ha le proprie static_assert.
assert san_martino_tile_type(15, 0) == EXIT_SAN_MARTINO
assert san_martino_tile_type(15, SAN_MARTINO_HEIGHT - 1) == DOOR_CONSOLI
assert san_martino_tile_type(0, RAMO_PQM_FIRST_Y) == EXIT_PORTA_ROMANA
assert san_martino_tile_type(0, 10) == RAILING
assert san_martino_tile_type(SAN_MARTINO_WIDTH - 1, 10) == WALL
assert san_martino_tile_type(0, 10) != san_martino_tile_type(SAN_MARTINO_WIDTH - 1, 10)
assert san_martino_tile_type(15, 0) != san_martino_tile_type(15, SAN_MARTINO_HEIGHT - 1)

MAX_TILES_GROUND = 512

# ----------------------------------------------------------------------------------------------
# Disegno del suolo: 256x512, il quartiere occupa 256x320 e il resto resta C_VOID (come Largo del
# Bargello: canvas legale, area logica piu' piccola).
# ----------------------------------------------------------------------------------------------

def draw_ground():
    cotto, cotto_w, cotto_h = leggi_indici_bmp4("piazza_cotto.bmp")
    porta, porta_w, porta_h = leggi_indici_bmp4("san_martino_porta.bmp")

    w, h = 256, 512
    px = canvas(w, h, C_VOID)

    for ty in range(SAN_MARTINO_HEIGHT):
        for tx in range(SAN_MARTINO_WIDTH):
            kind = san_martino_tile_type(tx, ty)
            x0, y0 = tx * TILE, ty * TILE

            for y in range(TILE):
                for x in range(TILE):
                    gx, gy = x0 + x, y0 + y

                    if kind == ROAD:
                        # Stesso ciottolato delle altre vie: e' la stessa citta'.
                        c = C_WALL_DARK if (gx * 7 + gy * 13) % 5 else C_RAIL
                        c = C_JOINT if (gx + gy) % 9 == 0 else c
                    elif kind == STAIRS:
                        c = C_WALL if (y % 2 == 0) else C_RAIL
                    elif kind == GROUND:
                        # Il campiello: selciato in cotto se l'ingrediente c'e', altrimenti una
                        # scacchiera di pietra come il ripiego procedurale della piazza.
                        if cotto:
                            c = cotto[gy % cotto_h][gx % cotto_w]
                        else:
                            base = C_STONE if (tx + ty) % 2 == 0 else C_WALL
                            c = C_JOINT if (x == 0 or y == 0) else base
                    elif kind == RAILING:
                        c = C_RAIL if y < 4 else C_WALL_DARK
                    elif kind in (DOOR_CONSOLI, EXIT_SAN_MARTINO, EXIT_PORTA_ROMANA):
                        # Le tre uscite, disegnate come varchi voltati: e' anche cosi' che la
                        # Porta di Santa Lucia (valore riusato DOOR_CONSOLI) deve leggersi, un
                        # arco nelle mura, non un buco nel nulla.
                        if kind == DOOR_CONSOLI and porta:
                            # La Porta di Santa Lucia fotografata, se il ritaglio esiste. Vedi
                            # docs/riferimenti/FONTI.md per il ritaglio richiesto: la porta ad
                            # arco vista di fronte, con le mura che proseguono ai due lati.
                            fx = gx - CORSO_FIRST_X * TILE
                            fy = gy - EXIT_PORTA_SANTA_LUCIA_FIRST_Y * TILE
                            c = (porta[fy][fx] if 0 <= fx < porta_w and 0 <= fy < porta_h
                                 else C_ARCH)
                        else:
                            c = C_ARCH if (x + y) % 8 else C_WALL_DARK
                    elif kind == WALL:
                        # Tessuto edilizio minore: corsi di pietra orizzontali, come le vie gia'
                        # consegnate. La fascia che fiancheggia la Porta di Santa Lucia condivide
                        # la stessa trama: sono le mura che "proseguono ai suoi lati".
                        c = C_WALL if (y % 4 != 3) else C_WALL_DARK
                    else:
                        c = C_STONE

                    px[gy][gx] = c

    return w, h, px


def main():
    os.makedirs(OUT, exist_ok=True)
    print("[san-martino-art] generazione degli asset segnaposto del Quartiere di San Martino")

    w, h, px = draw_ground()
    check_and_write("san_martino_ground", w, h, px, PALETTE_GROUND, "regular_bg",
                     MAX_TILES_GROUND)

    print("[san-martino-art] fatto. NON e' arte definitiva: il ritaglio fotografico che manca "
          "e' 'san_martino_porta.bmp' (ingredienti/), la Porta di Santa Lucia vista di fronte.")


if __name__ == "__main__":
    main()
