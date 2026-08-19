#!/usr/bin/env python3
"""
Generatore di GRAFICA SEGNAPOSTO per VIA XX SETTEMBRE (Gubbio 1151).

Produce, in graphics/:

    via_xx_settembre_ground.bmp   256x512   regular_bg   carreggiata, scalinata, case a schiera

NON e' arte definitiva (docs/mappa_del_mondo.md sez. 6): budget zero, nessuno che sappia
disegnare. Ogni tile nasce da una foto quando l'ingrediente esiste in ingredienti/, e da un
ripiego procedurale quando non esiste — cosi' la build resta riproducibile anche per chi clona
il progetto senza le foto, che non sono versionate.

DUE REGOLE, le stesse di tools/make_piazza_art.py:

1. Il suolo e' DERIVATO dalla griglia di collisione: il mirror Python di
   `via_xx_settembre_tile_type` qui sotto e' un port fedele di
   include/via_xx_settembre_collision.h, con le STESSE assert sugli STESSI punti notevoli. Due
   copie che divergono in silenzio sono peggio di una sola.
2. Il generatore MISURA e FALLISCE: conteggio colori contro il bpp_mode dichiarato e conteggio
   dei tile unici contro il tetto di 512 (Passo 9 del piano).

    python tools/make_via_xx_settembre_art.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from make_piazza_art import (TILE, canvas, check_and_write, leggi_indici_bmp4,
                              PALETTE_GROUND, C_WALL, C_WALL_DARK, C_JOINT, C_RAIL,
                              C_STONE, C_ARCH, C_WOOD, C_VOID)   # noqa: E402

# ----------------------------------------------------------------------------------------------
# Mirror di include/via_xx_settembre_collision.h
# ----------------------------------------------------------------------------------------------

VIA_XX_SETTEMBRE_WIDTH = 32
VIA_XX_SETTEMBRE_HEIGHT = 64

(GROUND, WALL, RAILING, DOOR_CONSOLI, EXIT_SAN_MARTINO, EXIT_PORTA_ROMANA, FOUNTAIN,
 CONSOLI_FACADE, PRETORIO_FACADE, STAIRS, DOOR_PRETORIO, ROAD) = range(12)

ROAD_FIRST_X, ROAD_LAST_X = 13, 18
STAIRS_FIRST_Y, STAIRS_LAST_Y = 30, 35

INGRESSO_DA_PIAZZA_GRANDE_X, INGRESSO_DA_PIAZZA_GRANDE_Y = 15, 1
INGRESSO_DA_SANT_AGOSTINO_X, INGRESSO_DA_SANT_AGOSTINO_Y = 16, VIA_XX_SETTEMBRE_HEIGHT - 2


def via_xx_settembre_tile_type(x, y):
    """Mirror di include/via_xx_settembre_collision.h::via_xx_settembre_tile_type."""
    if x < 0 or x >= VIA_XX_SETTEMBRE_WIDTH or y < 0 or y >= VIA_XX_SETTEMBRE_HEIGHT:
        return WALL

    if x < ROAD_FIRST_X or x > ROAD_LAST_X:
        return WALL

    if y == 0:
        return EXIT_SAN_MARTINO   # USCITA 4 -> Piazza Grande

    if y == VIA_XX_SETTEMBRE_HEIGHT - 1:
        return EXIT_PORTA_ROMANA   # USCITA 5 -> Sant'Agostino

    if STAIRS_FIRST_Y <= y <= STAIRS_LAST_Y:
        return STAIRS

    return ROAD


# Gli stessi punti notevoli su cui il C++ ha le proprie static_assert.
assert via_xx_settembre_tile_type(15, 0) == EXIT_SAN_MARTINO
assert via_xx_settembre_tile_type(16, VIA_XX_SETTEMBRE_HEIGHT - 1) == EXIT_PORTA_ROMANA
assert via_xx_settembre_tile_type(15, 1) != WALL   # INGRESSO_DA_PIAZZA_GRANDE, calpestabile
assert via_xx_settembre_tile_type(16, VIA_XX_SETTEMBRE_HEIGHT - 2) != WALL  # idem, Sant'Agostino
assert via_xx_settembre_tile_type(0, 20) == WALL     # SINISTRA = SUD: case a schiera
assert via_xx_settembre_tile_type(VIA_XX_SETTEMBRE_WIDTH - 1, 20) == WALL   # DESTRA = NORD
assert via_xx_settembre_tile_type(15, VIA_XX_SETTEMBRE_HEIGHT - 1) != EXIT_SAN_MARTINO
assert via_xx_settembre_tile_type(16, 0) != EXIT_PORTA_ROMANA
assert via_xx_settembre_tile_type(ROAD_FIRST_X, STAIRS_FIRST_Y) != WALL
assert via_xx_settembre_tile_type(ROAD_LAST_X, STAIRS_LAST_Y) != WALL

# ----------------------------------------------------------------------------------------------
# Budget del Passo 9, in tile unici a 4bpp.
# ----------------------------------------------------------------------------------------------

MAX_TILES_GROUND = 512

# Porte delle botteghe al piano terra, decorazione pura: non hanno una rappresentazione propria
# nella griglia di collisione (restano WALL, non calpestabili — sono facciate, non ingressi
# funzionanti). Una ogni tre tile lungo entrambi i fianchi, per rompere la monotonia del muro.
BOTTEGA_PASSO_Y = 3


def draw_ground():
    # Stesso ingrediente fotografico del ciottolato gia' usato per Piazza Grande, Largo del
    # Bargello e Sant'Andrea: e' la stessa citta', quindi la stessa pavimentazione.
    cotto, cotto_w, cotto_h = leggi_indici_bmp4("piazza_cotto.bmp")

    w = VIA_XX_SETTEMBRE_WIDTH * TILE     # 256
    h = VIA_XX_SETTEMBRE_HEIGHT * TILE    # 512
    px = canvas(w, h, C_VOID)

    for ty in range(VIA_XX_SETTEMBRE_HEIGHT):
        for tx in range(VIA_XX_SETTEMBRE_WIDTH):
            kind = via_xx_settembre_tile_type(tx, ty)
            x0, y0 = tx * TILE, ty * TILE
            # Una bottega ogni BOTTEGA_PASSO_Y righe di tile, sul primo tile utile di ciascun
            # fianco: e' un tratto puramente visivo, non tocca la collisione.
            bottega = (ty % BOTTEGA_PASSO_Y == 1)

            for y in range(TILE):
                for x in range(TILE):
                    gx, gy = x0 + x, y0 + y

                    if kind in (EXIT_SAN_MARTINO, EXIT_PORTA_ROMANA):
                        # Stesso trattamento grafico dei varchi di Piazza Grande: un passaggio
                        # in ombra, non un muro pieno.
                        c = C_ARCH if (x + y) % 8 else C_WALL_DARK
                    elif kind == STAIRS:
                        # Gradini: righe alternate chiare e scure, leggibili a 8 px.
                        c = C_WALL if (y % 2 == 0) else C_RAIL
                    elif kind == ROAD:
                        # Ciottolato irregolare, stessa formula delle altre vie della citta'.
                        if cotto:
                            c = cotto[gy % cotto_h][gx % cotto_w]
                        else:
                            c = C_WALL_DARK if (gx * 7 + gy * 13) % 5 else C_RAIL
                            c = C_JOINT if (gx + gy) % 9 == 0 else c
                    else:
                        # Le case a schiera: corsi di pietra come il tessuto minore di Sant'Andrea,
                        # con una porta di bottega in legno sul tile piu' vicino alla carreggiata.
                        vicino_alla_strada = (tx == ROAD_FIRST_X - 1 or tx == ROAD_LAST_X + 1)
                        if bottega and vicino_alla_strada and 2 <= x <= 5 and y >= 2:
                            c = C_WOOD
                        elif gx % 6 == 0:
                            c = C_JOINT
                        elif y % 4 == 3:
                            c = C_WALL_DARK
                        else:
                            c = C_WALL

                    px[gy][gx] = c

    return w, h, px


def main():
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "graphics")
    os.makedirs(out_dir, exist_ok=True)
    print("[via-xx-settembre-art] generazione degli asset segnaposto di Via XX Settembre")

    w, h, px = draw_ground()
    check_and_write("via_xx_settembre_ground", w, h, px, PALETTE_GROUND, "regular_bg",
                     MAX_TILES_GROUND)

    print("[via-xx-settembre-art] fatto. Ritagli fotografici che servirebbero "
          "(docs/mappa_del_mondo.md sez. 6), oggi assenti in ingredienti/: una foto di una "
          "CASA A SCHIERA eugubina in pietra calcarea con bottega al piano terra (inquadratura "
          "frontale, senza cavi elettrici), per sostituire la texture procedurale del fianco "
          "stradale senza toccare il C++.")


if __name__ == "__main__":
    main()
