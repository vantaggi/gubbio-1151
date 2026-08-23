#!/usr/bin/env python3
"""
Generatore di GRAFICA SEGNAPOSTO per STRADA E GOLA DEL BOTTACCIONE (Gubbio 1151).

Produce, in graphics/:

    bottaccione_ground.bmp   256x512   regular_bg   camminamento, parapetto, roccia, vuoto

NON e' arte definitiva (docs/mappa_del_mondo.md sez. 6): budget zero, nessuno che sappia
disegnare. Nessun ingrediente fotografico esiste oggi per questa gola (vedi il messaggio finale
di main() per i ritagli che servirebbero): tutto il disegno e' procedurale, ed e' il ripiego
dichiarato che tiene la build riproducibile anche per chi clona il progetto senza le foto, che
non sono versionate.

DUE REGOLE, le stesse di tools/make_piazza_art.py:

1. Il suolo e' DERIVATO dalla griglia di collisione: il mirror Python di
   `bottaccione_tile_type` qui sotto e' un port fedele di include/bottaccione_collision.h, con
   le STESSE assert sugli STESSI punti notevoli — INGRESSO compresi, perche' qui il vincolo dei
   "sei tile dal proprio varco" e' cio' che tiene il giocatore dal rimbalzare all'infinito fra
   Bottaccione e i suoi due vicini.
2. Il generatore MISURA e FALLISCE: conteggio colori contro il bpp_mode dichiarato e conteggio
   dei tile unici contro il tetto di 512 (Passo 9 del piano). Un corridoio stretto e lungo come
   questo rischia il tetto piu' di una piazza aperta se il disegno usasse la posizione ASSOLUTA
   in pixel: qui sotto la trama dipende quasi ovunque solo dalla posizione LOCALE dentro il tile
   (8x8) e dall'indice di riga/colonna del tile, mai dal pixel assoluto, cosi' la stessa parete
   ripetuta per 64 file di tile resta una manciata di tile unici invece di sessantaquattro.

    python tools/make_bottaccione_art.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from make_piazza_art import (TILE, canvas, check_and_write, leggi_indici_bmp4,
                              PALETTE_GROUND, C_WALL, C_WALL_DARK, C_JOINT, C_RAIL,
                              C_STONE, C_ARCH, C_WOOD, C_VOID)   # noqa: E402

# ----------------------------------------------------------------------------------------------
# Mirror di include/bottaccione_collision.h
# ----------------------------------------------------------------------------------------------

BOTTACCIONE_WIDTH = 32
BOTTACCIONE_HEIGHT = 64

(GROUND, WALL, RAILING, DOOR_CONSOLI, EXIT_SAN_MARTINO, EXIT_PORTA_ROMANA, FOUNTAIN,
 CONSOLI_FACADE, PRETORIO_FACADE, STAIRS, DOOR_PRETORIO, ROAD) = range(12)

RAILING_X = 9
CAMMINAMENTO_FIRST_X, CAMMINAMENTO_LAST_X = 10, 11
ROCCIA_X = 12

INGRESSO_DA_BASILICA_X, INGRESSO_DA_BASILICA_Y = CAMMINAMENTO_FIRST_X, 6
INGRESSO_DA_SAN_MARTINO_X = CAMMINAMENTO_FIRST_X
INGRESSO_DA_SAN_MARTINO_Y = BOTTACCIONE_HEIGHT - 7


def bottaccione_tile_type(x, y):
    """Mirror di include/bottaccione_collision.h::bottaccione_tile_type."""
    if x < 0 or x >= BOTTACCIONE_WIDTH or y < 0 or y >= BOTTACCIONE_HEIGHT:
        return WALL

    if CAMMINAMENTO_FIRST_X <= x <= CAMMINAMENTO_LAST_X:
        if y == 0:
            return EXIT_SAN_MARTINO      # valore 4: USCITA verso la Basilica
        if y == BOTTACCIONE_HEIGHT - 1:
            return EXIT_PORTA_ROMANA     # valore 5: USCITA verso San Martino
        return ROAD

    if x == RAILING_X:
        return RAILING

    if x == ROCCIA_X:
        return PRETORIO_FACADE

    return WALL


# Gli stessi punti notevoli su cui il C++ ha le proprie static_assert, INGRESSO compresi: qui e'
# dove si romperebbe l'assert se qualcuno riportasse per errore l'INGRESSO a un passo dal varco.
assert bottaccione_tile_type(CAMMINAMENTO_FIRST_X, 0) == EXIT_SAN_MARTINO
assert bottaccione_tile_type(CAMMINAMENTO_FIRST_X, BOTTACCIONE_HEIGHT - 1) == EXIT_PORTA_ROMANA
assert bottaccione_tile_type(RAILING_X, 32) == RAILING            # SINISTRA = SUD: il vuoto
assert bottaccione_tile_type(ROCCIA_X, 32) == PRETORIO_FACADE     # DESTRA = NORD: la roccia
assert bottaccione_tile_type(INGRESSO_DA_BASILICA_X, INGRESSO_DA_BASILICA_Y) != WALL
assert bottaccione_tile_type(INGRESSO_DA_SAN_MARTINO_X, INGRESSO_DA_SAN_MARTINO_Y) != WALL
assert INGRESSO_DA_BASILICA_Y >= 6, "l'ingresso deve stare almeno sei tile dal proprio varco"
assert (BOTTACCIONE_HEIGHT - 1) - INGRESSO_DA_SAN_MARTINO_Y >= 6, \
    "l'ingresso deve stare almeno sei tile dal proprio varco"
for _y in range(BOTTACCIONE_HEIGHT):
    _larghezza = sum(1 for _x in range(BOTTACCIONE_WIDTH)
                      if bottaccione_tile_type(_x, _y) not in (WALL, RAILING, PRETORIO_FACADE))
    assert _larghezza == 2, f"riga {_y}: il camminamento non e' largo 2 tile"

# ----------------------------------------------------------------------------------------------
# Budget del Passo 9, in tile unici a 4bpp.
# ----------------------------------------------------------------------------------------------

MAX_TILES_GROUND = 512

# Ogni quante file di tile appare la vena di roccia scura K-T, sulle pareti ai due lati del
# camminamento: puro effetto visivo (docs/riferimenti/FONTI.md, Alvarez 1980), non ha un valore
# proprio nella griglia di collisione — resta WALL o PRETORIO_FACADE come tutta la parete.
KT_BAND_PERIOD = 21
KT_BAND_OFFSET = 10

# Ogni quante file appare la campata dell'arco sotto il camminamento (Sez. 22 GDD: "camminamento
# stretto su arcate"): anche questo e' solo visivo, il camminamento resta ROAD ovunque.
ARCO_PERIOD = 6
ARCO_OFFSET = 3


def draw_ground():
    w, h = BOTTACCIONE_WIDTH * TILE, BOTTACCIONE_HEIGHT * TILE   # 256x512
    px = canvas(w, h, C_VOID)

    for ty in range(BOTTACCIONE_HEIGHT):
        for tx in range(BOTTACCIONE_WIDTH):
            kind = bottaccione_tile_type(tx, ty)
            x0, y0 = tx * TILE, ty * TILE
            kt_band = (ty % KT_BAND_PERIOD == KT_BAND_OFFSET)
            arco = (ty % ARCO_PERIOD == ARCO_OFFSET)

            for y in range(TILE):
                for x in range(TILE):
                    if kind in (EXIT_SAN_MARTINO, EXIT_PORTA_ROMANA):
                        # Il varco, in ombra: stesso trattamento delle uscite in tutte le aree.
                        c = C_ARCH if (x + y) % 8 else C_WALL_DARK
                    elif kind == ROAD:
                        # Il camminamento su arcate: lastricato semplice, con una campata scura
                        # ogni ARCO_PERIOD file a suggerire l'arco che lo regge da sotto.
                        if arco and y < 3:
                            c = C_ARCH
                        else:
                            c = C_JOINT if x == 0 else C_STONE
                    elif kind == RAILING:
                        # Il parapetto sul vuoto: identico a quello di Piazza Grande e Basilica.
                        c = C_RAIL if y < 4 else C_WALL_DARK
                    elif kind == PRETORIO_FACADE:
                        # La roccia viva addossata al camminamento: muratura a corsi con la vena
                        # K-T scura quando la riga di tile cade nella banda.
                        if kt_band:
                            c = C_JOINT if 3 <= y <= 4 else C_WALL_DARK
                        else:
                            c = C_WALL if (y % 4 != 3) else C_WALL_DARK
                    elif tx < RAILING_X:
                        # Il vuoto della gola oltre il parapetto: sfuma verso il nero quanto piu'
                        # ci si allontana dal camminamento, senza dipendere dal pixel assoluto.
                        profondita = RAILING_X - tx
                        if profondita > 4:
                            c = C_VOID
                        else:
                            c = C_WALL_DARK if (x + y) % 5 == 0 else C_VOID
                    else:
                        # Il corpo del monte oltre la roccia viva: pietra calcarea scura, un poco
                        # piu' chiara vicino al camminamento e piu' cupa in profondita', con la
                        # stessa vena K-T della fascia di roccia.
                        profondita = tx - ROCCIA_X
                        ombra = C_WALL_DARK if profondita % 2 == 0 else C_ARCH
                        if kt_band:
                            c = C_JOINT if 3 <= y <= 4 else ombra
                        else:
                            c = C_WALL if (y % 4 != 3) else ombra

                    px[y0 + y][x0 + x] = c

    return w, h, px


def main():
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "graphics")
    os.makedirs(out_dir, exist_ok=True)
    print("[bottaccione-art] generazione degli asset segnaposto della Gola del Bottaccione")

    w, h, px = draw_ground()
    check_and_write("bottaccione_ground", w, h, px, PALETTE_GROUND, "regular_bg",
                     MAX_TILES_GROUND)

    print("[bottaccione-art] fatto. Ritagli fotografici che servirebbero (docs/mappa_del_mondo.md "
          "sez. 6), oggi assenti in ingredienti/: una foto del CAMMINAMENTO dell'acquedotto preso "
          "lungo l'asse (per sostituire il lastricato procedurale con le arcate vere) e una foto "
          "della PARETE della gola che mostri la vena scura K-T (Alvarez, 1980) per sostituire la "
          "banda procedurale con quella reale, senza toccare il C++.")


if __name__ == "__main__":
    main()
