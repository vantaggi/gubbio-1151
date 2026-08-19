#!/usr/bin/env python3
"""
Generatore di GRAFICA SEGNAPOSTO per VIA DEI CONSOLI (Gubbio 1151).

Produce graphics/via_dei_consoli_ground.bmp (256x512, regular_bg) + il suo .json, seguendo le
stesse due regole di tools/make_piazza_art.py:

1. Il suolo e' DERIVATO dalla griglia di collisione: la funzione qui sotto e' un mirror fedele di
   include/via_dei_consoli_collision.h::via_dei_consoli_tile_type, con le STESSE assert sugli
   STESSI punti notevoli. Se la disposizione cambia nel C++ e non qui, il giocatore attraversa un
   muro che si vede o sbatte contro un ciottolato che non c'e'.

2. Il generatore MISURA e FALLISCE: check_and_write (importata) conta colori e tile unici contro
   il tetto del Passo 9, e la .json dichiara sempre "bpp_mode": "bpp_4".

    python tools/make_via_dei_consoli_art.py

COSA C'E': la strada che scende da Piazza Grande (70 m) a Largo del Bargello (45 m), stretta e
ripida. Il dislivello si mostra nei soli tre modi che docs/mappa_del_mondo.md sez. 2 ammette:
quattro bande di scalinata, due bande di muro di sostegno dove la sede stradale si stringe, un
affaccio (parapetto) a meta' percorso sul lato nord. Le case sui due lati portano, disegnate in
procedurale, le cosiddette "porte del morto": portine strette, rialzate da terra (non toccano la
riga di base del tile) e murate - un dettaglio della texture del muro, non un nuovo valore di tile.

RITAGLIO FOTOGRAFICO CHE SERVIREBBE, e non c'e' ancora. docs/riferimenti/FONTI.md elenca
`riferimenti/Gubbio,_via_dei_consoli,_01.JPG` ("la fascia sotto la piazza, muri di contenimento"):
guardata per scrivere questo file, mostra il lato destro della via in piena luce - conci di pietra
chiara, arcate murate a piano terra, finestre incorniciate ai piani sopra - con la torre del
Bargello/Pretorio in fondo alla prospettiva. Il ritaglio utile sarebbe la sola fascia del piano
terra (arcate e portoni, non le finestre superiori: a 8 px per tile non si leggono, come gia'
osservato per le bifore dei Consoli), salvata come ingredienti/via_dei_consoli_facciata.bmp con
photo_to_tiles.py. Finche' non esiste, questo script legge (leggi_indici_bmp4) e usa quel file SE
c'e' - il ripiego procedurale sotto e' cio' che tiene la build riproducibile senza le foto, che
non sono versionate (contratto, sez. 6).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from make_piazza_art import (TILE, canvas, check_and_write, leggi_indici_bmp4,   # noqa: E402
                              PALETTE_GROUND, C_WALL, C_WALL_DARK, C_JOINT, C_RAIL,
                              C_STONE, C_ARCH, C_WOOD, C_VOID)

# ----------------------------------------------------------------------------------------------
# Mirror di include/via_dei_consoli_collision.h
# ----------------------------------------------------------------------------------------------

VIA_DEI_CONSOLI_WIDTH = 16
VIA_DEI_CONSOLI_HEIGHT = 64

(GROUND, WALL, RAILING, DOOR_CONSOLI, EXIT_SAN_MARTINO, EXIT_PORTA_ROMANA, FOUNTAIN,
 CONSOLI_FACADE, PRETORIO_FACADE, STAIRS, DOOR_PRETORIO, ROAD) = range(12)

EXIT_PIAZZA_FIRST_Y, EXIT_PIAZZA_LAST_Y = 0, 1
EXIT_PIAZZA_FIRST_X, EXIT_PIAZZA_LAST_X = 6, 9

EXIT_BARGELLO_FIRST_Y = VIA_DEI_CONSOLI_HEIGHT - 2
EXIT_BARGELLO_LAST_Y = VIA_DEI_CONSOLI_HEIGHT - 1
EXIT_BARGELLO_FIRST_X, EXIT_BARGELLO_LAST_X = 6, 9

SIDE_WALL_THICK = 2
BUTTRESS_THICK = 4

BUTTRESS_A_FIRST_Y, BUTTRESS_A_LAST_Y = 18, 20
BUTTRESS_B_FIRST_Y, BUTTRESS_B_LAST_Y = 46, 48

STAIRS_BANDS = ((10, 12), (24, 26), (38, 40), (52, 54))

AFFACCIO_FIRST_Y, AFFACCIO_LAST_Y = 32, 34


def via_dei_consoli_tile_type(x, y):
    """Mirror di include/via_dei_consoli_collision.h::via_dei_consoli_tile_type."""
    if x < 0 or x >= VIA_DEI_CONSOLI_WIDTH or y < 0 or y >= VIA_DEI_CONSOLI_HEIGHT:
        return WALL

    if (EXIT_PIAZZA_FIRST_Y <= y <= EXIT_PIAZZA_LAST_Y and
            EXIT_PIAZZA_FIRST_X <= x <= EXIT_PIAZZA_LAST_X):
        return EXIT_SAN_MARTINO      # riusato: qui vale "verso Piazza Grande"

    if (EXIT_BARGELLO_FIRST_Y <= y <= EXIT_BARGELLO_LAST_Y and
            EXIT_BARGELLO_FIRST_X <= x <= EXIT_BARGELLO_LAST_X):
        return EXIT_PORTA_ROMANA     # riusato: qui vale "verso Largo del Bargello"

    thick = SIDE_WALL_THICK
    if (BUTTRESS_A_FIRST_Y <= y <= BUTTRESS_A_LAST_Y or
            BUTTRESS_B_FIRST_Y <= y <= BUTTRESS_B_LAST_Y):
        thick = BUTTRESS_THICK

    if x < thick:
        return WALL

    if x >= VIA_DEI_CONSOLI_WIDTH - thick:
        if AFFACCIO_FIRST_Y <= y <= AFFACCIO_LAST_Y:
            return RAILING
        return WALL

    if any(a <= y <= b for a, b in STAIRS_BANDS):
        return STAIRS

    return ROAD


# Gli stessi punti notevoli su cui il C++ ha le proprie static_assert.
assert via_dei_consoli_tile_type(7, 0) == EXIT_SAN_MARTINO
assert via_dei_consoli_tile_type(7, VIA_DEI_CONSOLI_HEIGHT - 1) == EXIT_PORTA_ROMANA
assert via_dei_consoli_tile_type(0, 33) == WALL
assert via_dei_consoli_tile_type(VIA_DEI_CONSOLI_WIDTH - 1, 33) == RAILING
assert via_dei_consoli_tile_type(0, 33) != via_dei_consoli_tile_type(VIA_DEI_CONSOLI_WIDTH - 1, 33)
# I due ingressi (VIA_DEI_CONSOLI_INGRESSO_DA_* nel C++) cadono su sede stradale, non su un muro.
assert via_dei_consoli_tile_type(7, 3) == ROAD
assert via_dei_consoli_tile_type(7, 60) == ROAD

# ----------------------------------------------------------------------------------------------
# Budget del Passo 9, in tile unici a 4bpp.
# ----------------------------------------------------------------------------------------------

MAX_TILES_GROUND = 512

# Le "porte del morto": una colonna sola (quella che tocca la strada, sul lato SUD), a intervalli
# lungo la discesa. Scelte lontano da uscite, scalinate e muri di sostegno, cosi' restano un
# dettaglio della casa e non si sovrappongono a un'altra regola.
DOOR_COLUMN = 1
DOOR_TY = (5, 15, 29, 43, 57)


def draw_ground():
    # L'INGREDIENTE FOTOGRAFICO, se c'e'. Vedi il ritaglio descritto in testa al file: finche'
    # ingredienti/via_dei_consoli_facciata.bmp non esiste, leggi_indici_bmp4 ritorna None e si
    # procede in procedurale - e' il ripiego che il contratto impone (sez. 6), non un abbozzo.
    facciata, facc_w, facc_h = leggi_indici_bmp4("via_dei_consoli_facciata.bmp")

    # 256x512: le misure BMP legali sono solo 256 o 512 per lato. La via e' larga 16 tile (128
    # px): meta' del canvas resta C_VOID e non viene mai inquadrata, la camera e' clampata a
    # VIA_DEI_CONSOLI_WIDTH_PX prima - esattamente come per la fascia oltre y=320 in piazza_ground.
    w, h = 256, 512
    px = canvas(w, h, C_VOID)

    for ty in range(VIA_DEI_CONSOLI_HEIGHT):
        for tx in range(VIA_DEI_CONSOLI_WIDTH):
            kind = via_dei_consoli_tile_type(tx, ty)
            x0, y0 = tx * TILE, ty * TILE

            for y in range(TILE):
                for x in range(TILE):
                    gx, gy = x0 + x, y0 + y

                    if kind == ROAD:
                        # Ciottolato, la stessa formula di piazza_ground per la via a nord: e'
                        # la stessa citta', deve avere la stessa strada.
                        c = C_WALL_DARK if (gx * 7 + gy * 13) % 5 else C_RAIL
                        c = C_JOINT if (gx + gy) % 9 == 0 else c
                    elif kind == STAIRS:
                        # Gradini: righe alternate chiare e scure, leggibili a 8 px.
                        c = C_WALL if (y % 2 == 0) else C_RAIL
                    elif kind == RAILING:
                        # L'affaccio: un parapetto basso, con il vuoto oltre.
                        c = C_RAIL if y < 4 else C_WALL_DARK
                    elif kind == WALL:
                        is_door = (tx == DOOR_COLUMN and ty in DOOR_TY and
                                   1 <= y <= 5 and 2 <= x <= 5)

                        if is_door:
                            # Rialzata da terra: il battente non scende fino all'ultima riga
                            # del tile (y=6,7 restano pietra), che e' cio' che dice "porta del
                            # morto" invece di "portone a raso strada".
                            c = C_WALL_DARK if (x in (2, 5) or y == 1) else C_WOOD
                        elif facciata:
                            c = facciata[gy % facc_h][gx % facc_w]
                        else:
                            # Pietra calcarea chiara a corsi orizzontali (FONTI.md: "quasi
                            # bianca"), la stessa formula delle facciate canoniche di piazza_art -
                            # non la formula di WALL li', che e' scura perche' li' descrive
                            # edificato minore sullo sfondo, non il soggetto principale della via.
                            c = C_WALL if (y % 4 != 3) else C_WALL_DARK
                    elif kind in (EXIT_SAN_MARTINO, EXIT_PORTA_ROMANA):
                        c = C_ARCH if (x + y) % 8 else C_WALL_DARK
                    else:
                        c = C_STONE

                    px[gy][gx] = c

    return w, h, px


def main():
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "graphics")
    os.makedirs(out, exist_ok=True)
    print("[via-dei-consoli-art] generazione degli asset segnaposto di Via dei Consoli")

    w, h, px = draw_ground()
    check_and_write("via_dei_consoli_ground", w, h, px, PALETTE_GROUND, "regular_bg",
                     MAX_TILES_GROUND)

    print("[via-dei-consoli-art] fatto. NON e' arte definitiva: sostituire il .bmp mantenendo "
          "misure e 16 colori, senza toccare il C++.")


if __name__ == "__main__":
    main()
