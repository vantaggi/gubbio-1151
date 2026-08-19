#!/usr/bin/env python3
"""
Generatore di GRAFICA SEGNAPOSTO per il QUARTIERE DI SANT'ANDREA (Gubbio 1151).

Produce, in graphics/:

    sant_andrea_ground.bmp   256x256   regular_bg   corridoio, campiello, vicoli, case-torri

NON e' arte definitiva (docs/mappa_del_mondo.md sez. 6): budget zero, nessuno che sappia
disegnare. Ogni tile nasce da una foto quando l'ingrediente esiste in ingredienti/, e da un
ripiego procedurale quando non esiste — cosi' la build resta riproducibile anche per chi clona
il progetto senza le foto, che non sono versionate.

DUE REGOLE, le stesse di tools/make_piazza_art.py:

1. Il suolo e' DERIVATO dalla griglia di collisione: il mirror Python di
   `sant_andrea_tile_type` qui sotto e' un port fedele di
   include/sant_andrea_collision.h, con le STESSE assert sugli STESSI punti notevoli. Due copie
   che divergono in silenzio sono peggio di una sola.
2. Il generatore MISURA e FALLISCE: conteggio colori contro il bpp_mode dichiarato e conteggio
   dei tile unici contro il tetto di 512 (Passo 9 del piano).

    python tools/make_sant_andrea_art.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from make_piazza_art import (TILE, canvas, check_and_write, leggi_indici_bmp4,
                              PALETTE_GROUND, C_WALL, C_WALL_DARK, C_JOINT, C_RAIL,
                              C_STONE, C_ARCH, C_WOOD, C_VOID)   # noqa: E402

# ----------------------------------------------------------------------------------------------
# Mirror di include/sant_andrea_collision.h
# ----------------------------------------------------------------------------------------------

SANT_ANDREA_WIDTH = 32
SANT_ANDREA_HEIGHT = 32

(GROUND, WALL, RAILING, DOOR_CONSOLI, EXIT_SAN_MARTINO, EXIT_PORTA_ROMANA, FOUNTAIN,
 CONSOLI_FACADE, PRETORIO_FACADE, STAIRS, DOOR_PRETORIO, ROAD) = range(12)

CORRIDOIO_FIRST_X, CORRIDOIO_LAST_X, CORRIDOIO_LAST_Y = 14, 17, 9
CAMPIELLO_FIRST_X, CAMPIELLO_LAST_X = 10, 21
CAMPIELLO_FIRST_Y, CAMPIELLO_LAST_Y = 10, 14
VICOLO_SUD_FIRST_X, VICOLO_SUD_LAST_X = 4, 9
VICOLO_SUD_FIRST_Y, VICOLO_SUD_LAST_Y = 11, 12
VICOLO_NORD_FIRST_X, VICOLO_NORD_LAST_X = 22, 27
VICOLO_NORD_FIRST_Y, VICOLO_NORD_LAST_Y = 11, 12
VICOLO_EST_FIRST_X, VICOLO_EST_LAST_X = 14, 15
VICOLO_EST_FIRST_Y, VICOLO_EST_LAST_Y = 15, 24

INGRESSO_DA_SANT_AGOSTINO_X, INGRESSO_DA_SANT_AGOSTINO_Y = 15, 1


def sant_andrea_tile_type(x, y):
    """Mirror di include/sant_andrea_collision.h::sant_andrea_tile_type."""
    if x < 0 or x >= SANT_ANDREA_WIDTH or y < 0 or y >= SANT_ANDREA_HEIGHT:
        return WALL

    if CORRIDOIO_FIRST_X <= x <= CORRIDOIO_LAST_X and y <= CORRIDOIO_LAST_Y:
        return EXIT_SAN_MARTINO if y == 0 else ROAD

    if (CAMPIELLO_FIRST_X <= x <= CAMPIELLO_LAST_X and
            CAMPIELLO_FIRST_Y <= y <= CAMPIELLO_LAST_Y):
        return GROUND

    if (VICOLO_SUD_FIRST_X <= x <= VICOLO_SUD_LAST_X and
            VICOLO_SUD_FIRST_Y <= y <= VICOLO_SUD_LAST_Y):
        return ROAD

    if (VICOLO_NORD_FIRST_X <= x <= VICOLO_NORD_LAST_X and
            VICOLO_NORD_FIRST_Y <= y <= VICOLO_NORD_LAST_Y):
        return ROAD

    if (VICOLO_EST_FIRST_X <= x <= VICOLO_EST_LAST_X and
            VICOLO_EST_FIRST_Y <= y <= VICOLO_EST_LAST_Y):
        return ROAD

    return WALL


# Gli stessi punti notevoli su cui il C++ ha le proprie static_assert.
assert sant_andrea_tile_type(15, 0) == EXIT_SAN_MARTINO
assert sant_andrea_tile_type(15, 1) != WALL   # INGRESSO_DA_SANT_AGOSTINO, calpestabile
assert sant_andrea_tile_type(4, 31) == WALL     # BASSO = EST: chiuso, nessuna uscita
assert sant_andrea_tile_type(0, 16) == WALL     # SINISTRA = SUD: chiuso, nessuna uscita
assert sant_andrea_tile_type(31, 16) == WALL    # DESTRA = NORD: chiuso, nessuna uscita
assert sant_andrea_tile_type(15, 31) != EXIT_SAN_MARTINO   # niente varco a est: non e' un ribaltamento
assert sant_andrea_tile_type(15, 12) == GROUND              # centro del campiello, aperto
assert sant_andrea_tile_type(9, 11) != WALL                 # il vicolo sud aderisce al campiello
assert sant_andrea_tile_type(22, 11) != WALL                # il vicolo nord aderisce al campiello
assert sant_andrea_tile_type(14, 15) != WALL                # il vicolo est aderisce al campiello

# ----------------------------------------------------------------------------------------------
# Budget del Passo 9, in tile unici a 4bpp.
# ----------------------------------------------------------------------------------------------

MAX_TILES_GROUND = 512

# Archi rampanti fra le case: puro effetto VISIVO, disegnato sopra due vicoli. Non hanno una
# rappresentazione propria nella griglia di collisione (che resta ROAD, calpestabile) perche' il
# contratto non prevede un valore di tile per "sopraelevato": il giocatore ci cammina sotto.
ARCHI_RAMPANTI = {(24, 11), (24, 12), (14, 19), (15, 19)}


def draw_ground():
    # Ingrediente fotografico gia' usato per il selciato di Piazza Grande e di Largo del
    # Bargello: e' la stessa citta', quindi la stessa pavimentazione (vedi
    # tools/make_piazza_art.py::draw_bargello).
    cotto, cotto_w, cotto_h = leggi_indici_bmp4("piazza_cotto.bmp")

    w = h = 256   # SANT_ANDREA_WIDTH * TILE == SANT_ANDREA_HEIGHT * TILE == 256: nessun margine
    px = canvas(w, h, C_VOID)

    for ty in range(SANT_ANDREA_HEIGHT):
        for tx in range(SANT_ANDREA_WIDTH):
            kind = sant_andrea_tile_type(tx, ty)
            x0, y0 = tx * TILE, ty * TILE
            arco = (tx, ty) in ARCHI_RAMPANTI

            for y in range(TILE):
                for x in range(TILE):
                    gx, gy = x0 + x, y0 + y

                    if kind == EXIT_SAN_MARTINO:
                        # Il varco verso Sant'Agostino: un passaggio in ombra, come le uscite di
                        # Piazza Grande.
                        c = C_ARCH if (x + y) % 8 else C_WALL_DARK
                    elif kind == ROAD:
                        if arco and y < 3:
                            # L'arco rampante: la sua ombra attraversa il vicolo in alto sullo
                            # schermo, il resto del tile resta ciottolato normale.
                            c = C_ARCH
                        else:
                            # Ciottolato irregolare, stessa formula di via dei Consoli in piazza.
                            c = C_WALL_DARK if (gx * 7 + gy * 13) % 5 else C_RAIL
                            c = C_JOINT if (gx + gy) % 9 == 0 else c
                    elif kind == GROUND:
                        # Il campiello: la stessa pavimentazione fotografata, se c'e'; altrimenti
                        # lastre chiare con le fughe.
                        if cotto:
                            c = cotto[gy % cotto_h][gx % cotto_w]
                        else:
                            c = C_JOINT if (x == 0 or y == 0) else C_STONE
                    else:
                        # Le case-torri: corsi di pietra come i muri di Piazza Grande, ma con
                        # giunti verticali ogni 6 tile a segnare il confine fra una torre e la
                        # successiva, e una finestra stretta ogni due torri — il tratto che
                        # distingue un tessuto di case-torri da un unico muro indistinto.
                        if gx % 6 == 0:
                            c = C_JOINT
                        elif ty % 5 == 2 and (gx % 6) in (2, 3) and 2 <= y <= 5:
                            c = C_ARCH   # finestra stretta della casa-torre
                        elif y % 4 == 3:
                            c = C_WALL_DARK
                        else:
                            c = C_WALL

                    px[gy][gx] = c

    return w, h, px


def main():
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "graphics")
    os.makedirs(out_dir, exist_ok=True)
    print("[sant-andrea-art] generazione degli asset segnaposto del Quartiere di Sant'Andrea")

    w, h, px = draw_ground()
    check_and_write("sant_andrea_ground", w, h, px, PALETTE_GROUND, "regular_bg",
                     MAX_TILES_GROUND)

    print("[sant-andrea-art] fatto. Ritagli fotografici che servirebbero (docs/mappa_del_mondo.md "
          "sez. 6), oggi assenti in ingredienti/: una foto di un VICOLO stretto fra case-torri "
          "del quartiere orientale (inquadratura verticale, senza cavi elettrici in primo piano) "
          "e una foto del FRONTE di una casa-torre eugubina in pietra a corsi, per sostituire la "
          "texture procedurale del tessuto murario senza toccare il C++.")


if __name__ == "__main__":
    main()
