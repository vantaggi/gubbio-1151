#!/usr/bin/env python3
"""
Generatore di GRAFICA SEGNAPOSTO per la BASILICA DI SANT'UBALDO (Gubbio 1151).

Produce, in graphics/:

    basilica_ground.bmp   512x256   regular_bg   roccia, facciata, scalinata, spiazzo, parapetto

NON e' arte definitiva (docs/mappa_del_mondo.md sez. 6): budget zero, nessuno che sappia
disegnare. La facciata nasce dalla foto in ingredienti/basilica_facciata.bmp quando c'e', e da
un ripiego procedurale quando manca — cosi' la build resta riproducibile anche per chi clona il
progetto senza le foto, che non sono versionate.

DUE REGOLE, le stesse di tools/make_piazza_art.py:

1. Il suolo e' DERIVATO dalla griglia di collisione: il mirror Python di `basilica_tile_type`
   qui sotto e' un port fedele di include/basilica_collision.h, con le STESSE assert sugli
   STESSI punti notevoli. Due copie che divergono in silenzio sono peggio di una sola.
2. Il generatore MISURA e FALLISCE: conteggio colori contro il bpp_mode dichiarato e conteggio
   dei tile unici contro il tetto di 512 (Passo 9 del piano).

    python tools/make_basilica_art.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from make_piazza_art import (TILE, canvas, check_and_write, leggi_indici_bmp4,
                              PALETTE_GROUND, C_WALL, C_WALL_DARK, C_JOINT, C_RAIL,
                              C_STONE, C_ARCH, C_WOOD, C_VOID)   # noqa: E402

# ----------------------------------------------------------------------------------------------
# Mirror di include/basilica_collision.h
# ----------------------------------------------------------------------------------------------

BASILICA_WIDTH = 64
BASILICA_HEIGHT = 32

(GROUND, WALL, RAILING, DOOR_CONSOLI, EXIT_SAN_MARTINO, EXIT_PORTA_ROMANA, FOUNTAIN,
 CONSOLI_FACADE, PRETORIO_FACADE, STAIRS, DOOR_PRETORIO, ROAD) = range(12)

ROCCIA_LAST_Y = 1

FACADE_FIRST_Y = ROCCIA_LAST_Y + 1        # 2
FACADE_LAST_Y = FACADE_FIRST_Y + 19       # 21: 20 righe, come la foto
FACADE_FIRST_X, FACADE_LAST_X = 15, 48    # 34 tile

PORTONE_X0, PORTONE_X1 = 31, 32

STAIRS_Y = FACADE_LAST_Y + 1              # 22
STAIRS_FIRST_X, STAIRS_LAST_X = 28, 35

RAILING_FIRST_Y = BASILICA_HEIGHT - 2     # 30

VARCO_SUD_LAST_X = 1
VARCO_SUD_FIRST_Y, VARCO_SUD_LAST_Y = 23, 25

VARCO_NORD_FIRST_X = BASILICA_WIDTH - 2   # 62
VARCO_NORD_FIRST_Y, VARCO_NORD_LAST_Y = 27, 29

# Sei tile dal proprio varco (docs/mappa_del_mondo.md sez. 5), come in basilica_collision.h.
INGRESSO_DA_MONTE_INGINO_X, INGRESSO_DA_MONTE_INGINO_Y = 8, 24
INGRESSO_DA_BOTTACCIONE_X, INGRESSO_DA_BOTTACCIONE_Y = 56, 28


def basilica_tile_type(x, y):
    """Mirror di include/basilica_collision.h::basilica_tile_type."""
    if x < 0 or x >= BASILICA_WIDTH or y < 0 or y >= BASILICA_HEIGHT:
        return WALL

    if y <= ROCCIA_LAST_Y:
        return WALL

    if y <= FACADE_LAST_Y:
        if y == FACADE_LAST_Y and x in (PORTONE_X0, PORTONE_X1):
            return DOOR_PRETORIO
        if FACADE_FIRST_X <= x <= FACADE_LAST_X:
            return CONSOLI_FACADE
        return WALL

    if y == STAIRS_Y:
        return STAIRS if STAIRS_FIRST_X <= x <= STAIRS_LAST_X else GROUND

    if y >= RAILING_FIRST_Y:
        return RAILING

    if x <= VARCO_SUD_LAST_X:
        return EXIT_SAN_MARTINO if VARCO_SUD_FIRST_Y <= y <= VARCO_SUD_LAST_Y else WALL

    if x >= VARCO_NORD_FIRST_X:
        return EXIT_PORTA_ROMANA if VARCO_NORD_FIRST_Y <= y <= VARCO_NORD_LAST_Y else WALL

    return GROUND


# Gli stessi punti notevoli su cui il C++ ha le proprie static_assert.
assert basilica_tile_type(31, 10) == CONSOLI_FACADE            # ALTO = OVEST: la facciata
assert basilica_tile_type(31, BASILICA_HEIGHT - 1) == RAILING  # BASSO = EST: il parapetto
assert basilica_tile_type(0, VARCO_SUD_FIRST_Y) == EXIT_SAN_MARTINO      # SINISTRA = SUD
assert basilica_tile_type(BASILICA_WIDTH - 1, VARCO_NORD_FIRST_Y) == EXIT_PORTA_ROMANA  # DESTRA = NORD
assert (basilica_tile_type(0, VARCO_SUD_FIRST_Y) !=
        basilica_tile_type(BASILICA_WIDTH - 1, VARCO_NORD_FIRST_Y))      # niente ribaltamento
assert basilica_tile_type(INGRESSO_DA_MONTE_INGINO_X, INGRESSO_DA_MONTE_INGINO_Y) != WALL
assert basilica_tile_type(INGRESSO_DA_BOTTACCIONE_X, INGRESSO_DA_BOTTACCIONE_Y) != WALL
# Almeno sei tile dal proprio varco, altrimenti si rimbalza all'infinito fra le due aree.
assert INGRESSO_DA_MONTE_INGINO_X - VARCO_SUD_LAST_X >= 6
assert VARCO_NORD_FIRST_X - INGRESSO_DA_BOTTACCIONE_X >= 6
assert basilica_tile_type(PORTONE_X0, STAIRS_Y) == STAIRS       # la scalinata aderisce al portone
assert basilica_tile_type(31, 26) == GROUND                     # centro dello spiazzo, aperto
assert sum(1 for x in range(BASILICA_WIDTH)
           if basilica_tile_type(x, FACADE_FIRST_Y) == CONSOLI_FACADE) == 34   # 50 m = 34 tile

# ----------------------------------------------------------------------------------------------
# Budget del Passo 9, in tile unici a 4bpp.
# ----------------------------------------------------------------------------------------------

MAX_TILES_GROUND = 512


# La facciata fotografata, alla massima fusione ammessa da photo_to_tiles.py, non scende sotto
# 586 tile unici su 680 celle (docs/riferimenti/FONTI.md: e' una foto vera, non ha ripetizione).
# Da sola sfora gia' il tetto di 512 di quest'area: e' il difetto gia' descritto nel piano
# ("la Basilica ne ha prodotti 607"). SEMPLIFICARE il disegno (docs/mappa_del_mondo.md sez. 5)
# qui vuol dire ridurre la RISOLUZIONE con cui la si incolla: si campiona un pixel ogni
# FACADE_DOWNSAMPLE e lo si ripete sul blocco, cosi' molti tile diventano identici invece di
# essere ciascuno un frammento unico di pietra. 4 e' il piu' piccolo valore che rientra nel
# tetto (misurato: 404 tile totali) e che allinea sui bordi di tile (8 e' multiplo di 4): un
# valore che non divide 8 sfaserebbe il campionamento a ogni tile, PEGGIORANDO la ripetizione
# invece di aiutarla (misurato: 3 e 5 restano oltre 600).
FACADE_DOWNSAMPLE = 4


def draw_ground():
    # La facciata vera, se c'e': 272x160 px, cioe' 34x20 tile, esattamente le misure che la
    # scala impone (city_reference.h::LANDMARKS). Il selciato riusa lo stesso ingrediente di
    # Piazza Grande e di Largo del Bargello: e' la stessa citta'.
    facciata, facc_w, facc_h = leggi_indici_bmp4("basilica_facciata.bmp")
    cotto, cotto_w, cotto_h = leggi_indici_bmp4("piazza_cotto.bmp")

    # 512x256: BASILICA_WIDTH * TILE == 512, BASILICA_HEIGHT * TILE == 256. Entrambe misure
    # legali di un BG regolare (256 o 512, mai una via di mezzo): un solo blocco BG, nessun
    # margine da riempire come i 512x512 di Piazza Grande.
    w, h = BASILICA_WIDTH * TILE, BASILICA_HEIGHT * TILE
    px = canvas(w, h, C_VOID)

    for ty in range(BASILICA_HEIGHT):
        for tx in range(BASILICA_WIDTH):
            kind = basilica_tile_type(tx, ty)
            x0, y0 = tx * TILE, ty * TILE

            for y in range(TILE):
                for x in range(TILE):
                    gx, gy = x0 + x, y0 + y

                    if kind == CONSOLI_FACADE and facciata:
                        # La facciata fotografata combacia con la fascia della griglia: origine
                        # dell'immagine nell'angolo (FACADE_FIRST_X, FACADE_FIRST_Y), non un
                        # numero scritto a mano altrove. Campionata a bassa risoluzione: vedi
                        # FACADE_DOWNSAMPLE qui sopra.
                        fx = gx - FACADE_FIRST_X * TILE
                        fy = gy - FACADE_FIRST_Y * TILE
                        fx = (fx // FACADE_DOWNSAMPLE) * FACADE_DOWNSAMPLE
                        fy = (fy // FACADE_DOWNSAMPLE) * FACADE_DOWNSAMPLE
                        c = (facciata[fy][fx] if 0 <= fx < facc_w and 0 <= fy < facc_h
                             else C_WALL)
                    elif kind == CONSOLI_FACADE:
                        # Ripiego procedurale: pietra calcarea chiara a corsi orizzontali, come
                        # il Palazzo dei Consoli quando manca la foto.
                        c = C_WALL if (y % 4 != 3) else C_WALL_DARK
                    elif kind == WALL and ty <= ROCCIA_LAST_Y:
                        # La roccia della vetta: non e' muratura a corsi, e' pietra viva, quindi
                        # una trama irregolare invece delle fasce ordinate del resto della mappa.
                        c = C_WALL_DARK if ((gx * 3 + gy * 5) % 7 < 3) else C_ARCH
                    elif kind == WALL:
                        # Il fianco roccioso oltre la facciata, e le pareti dei varchi laterali:
                        # stessa muratura a corsi di piazza_grande_collision.h.
                        c = C_ARCH if (y % 4 == 3) else C_WALL_DARK
                    elif kind == DOOR_PRETORIO:
                        c = C_WOOD if 1 <= x <= 6 else C_WALL_DARK
                    elif kind == STAIRS:
                        # Gradini: righe alternate chiare e scure, il segno che si legge a 8 px.
                        c = C_WALL if (y % 2 == 0) else C_RAIL
                    elif kind == RAILING:
                        c = C_RAIL if y < 4 else C_WALL_DARK
                    elif kind in (EXIT_SAN_MARTINO, EXIT_PORTA_ROMANA):
                        c = C_ARCH if (x + y) % 8 else C_WALL_DARK
                    elif kind == GROUND:
                        # Il selciato davanti alla basilica e lo spiazzo panoramico: la stessa
                        # pavimentazione fotografata, se c'e'; altrimenti lastre chiare.
                        if cotto:
                            c = cotto[gy % cotto_h][gx % cotto_w]
                        else:
                            c = C_JOINT if (x == 0 or y == 0) else C_STONE
                    else:
                        c = C_WALL_DARK

                    px[gy][gx] = c

    return w, h, px


def main():
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "graphics")
    os.makedirs(out_dir, exist_ok=True)
    print("[basilica-art] generazione degli asset segnaposto della Basilica di Sant'Ubaldo")

    w, h, px = draw_ground()
    check_and_write("basilica_ground", w, h, px, PALETTE_GROUND, "regular_bg", MAX_TILES_GROUND)

    print("[basilica-art] fatto. Ritagli fotografici che servirebbero (docs/mappa_del_mondo.md "
          "sez. 6), oggi assenti o non ancora usati in ingredienti/: la vista dallo spiazzo "
          "panoramico sulla citta' e la piana, per il fondale oltre il parapetto (oggi tinta "
          "piatta), e un primo piano della roccia della vetta per sostituire la trama "
          "procedurale senza toccare il C++.")


if __name__ == "__main__":
    main()
