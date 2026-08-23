#!/usr/bin/env python3
"""
Generatore di GRAFICA SEGNAPOSTO per il TEATRO ROMANO (Gubbio 1151).

Produce, in graphics/:

    teatro_romano_ground.bmp   512x256   regular_bg   cavea, gradinate, corridoio, prato aperto

NON e' arte definitiva (docs/mappa_del_mondo.md sez. 6): budget zero, nessuno che sappia
disegnare. Interamente PROCEDURALE, e per una ragione precisa: photo_to_tiles.py ha gia' un
ingrediente "teatro_romano" (MONUMENTI, la ripresa dall'alto del rudere), ma e' convertito sulla
PALETTE_PANORAMA — la palette dello skyline, non quella condivisa di PALETTE_GROUND che questo
script importa. Un BG a 4bpp ha sedici colori per TUTTO cio' che vi sta sopra (vedi il commento
in testa a tools/make_piazza_art.py): rileggere quell'ingrediente sotto PALETTE_GROUND userebbe
gli stessi indici numerici per colori diversi, e la cavea comparirebbe con le tinte sbagliate
senza che nessun controllo automatico se ne accorga. RITAGLIO FOTOGRAFICO CHE SERVIREBBE (non
ancora in ingredienti/, docs/mappa_del_mondo.md sez. 6): una nuova conversione della stessa foto
sorgente ("13-Gubbio-Teatro-Romano-02-696x464.jpg"), stavolta contro PALETTE_PIAZZA/solo_indici
come consoli_facciata e basilica_facciata, dimensionata 46x4 tile per il solo fronte della cavea
— non e' compito di quest'area toccare tools/photo_to_tiles.py, che appartiene ad altri.

DUE REGOLE, le stesse di tools/make_piazza_art.py:

1. Il suolo e' DERIVATO dalla griglia di collisione: il mirror Python di `teatro_romano_tile_type`
   qui sotto e' un port fedele di include/teatro_romano_collision.h, con le STESSE assert sugli
   STESSI punti notevoli. Due copie che divergono in silenzio sono peggio di una sola.
2. Il generatore MISURA e FALLISCE: conteggio colori contro il bpp_mode dichiarato e conteggio
   dei tile unici contro il tetto di 512 (Passo 9 del piano).

    python tools/make_teatro_romano_art.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_piazza_art import (TILE, canvas, check_and_write, leggi_indici_bmp4,   # noqa: E402
                              PALETTE_GROUND, C_WALL, C_WALL_DARK, C_JOINT, C_RAIL,
                              C_STONE, C_ARCH, C_WOOD, C_VOID)

# L'erba, fra i gradoni e nel prato aperto: indice 12 di photo_to_tiles.PALETTE_PIAZZA
# ("vegetazione"), non esposto fra i nomi importati sopra ma parte della STESSA palette
# condivisa — non un colore nuovo, solo un indice della tavolozza che gli altri generatori non
# hanno ancora avuto motivo di nominare.
C_VEG = 12

# ----------------------------------------------------------------------------------------------
# Mirror di include/teatro_romano_collision.h
# ----------------------------------------------------------------------------------------------

TEATRO_ROMANO_WIDTH = 64
TEATRO_ROMANO_HEIGHT = 32

(GROUND, WALL, RAILING, DOOR_CONSOLI, EXIT_SAN_MARTINO, EXIT_PORTA_ROMANA, FOUNTAIN,
 CONSOLI_FACADE, PRETORIO_FACADE, STAIRS, DOOR_PRETORIO, ROAD) = range(12)

CAVEA_FIRST_X, CAVEA_LAST_X = 9, 54       # 46 tile: 70 m in scala
CAVEA_FACADE_LAST_Y = 3

GRADINATE_FIRST_X, GRADINATE_LAST_X = 11, 52
GRADINATE_LAST_Y = 13

CORRIDOIO_FIRST_Y = GRADINATE_LAST_Y + 1   # 14
CORRIDOIO_LAST_Y = 16
ARCO_PASSO = 8
ARCO_PILONE_LARGH = 2

EXIT_SAN_MARTINO_FIRST_Y, EXIT_SAN_MARTINO_LAST_Y = 24, 25

# Sei tile dal proprio varco (docs/mappa_del_mondo.md sez. 5), come in teatro_romano_collision.h.
INGRESSO_DA_SAN_MARTINO_X, INGRESSO_DA_SAN_MARTINO_Y = 55, 24


def teatro_romano_tile_type(x, y):
    """Mirror di include/teatro_romano_collision.h::teatro_romano_tile_type."""
    if x < 0 or x >= TEATRO_ROMANO_WIDTH or y < 0 or y >= TEATRO_ROMANO_HEIGHT:
        return WALL

    if x == TEATRO_ROMANO_WIDTH - 1 and EXIT_SAN_MARTINO_FIRST_Y <= y <= EXIT_SAN_MARTINO_LAST_Y:
        return EXIT_SAN_MARTINO

    if x == TEATRO_ROMANO_WIDTH - 1:
        return WALL

    if y <= CORRIDOIO_LAST_Y:
        if x < CAVEA_FIRST_X or x > CAVEA_LAST_X:
            return WALL

        if y <= CAVEA_FACADE_LAST_Y:
            return CONSOLI_FACADE

        if y <= GRADINATE_LAST_Y:
            return STAIRS if GRADINATE_FIRST_X <= x <= GRADINATE_LAST_X else WALL

        fase = (x - CAVEA_FIRST_X) % ARCO_PASSO
        return WALL if fase < ARCO_PILONE_LARGH else ROAD

    return GROUND


# Gli stessi punti notevoli su cui il C++ ha le proprie static_assert.
assert teatro_romano_tile_type(32, 1) == CONSOLI_FACADE                          # ALTO = OVEST
assert teatro_romano_tile_type(32, TEATRO_ROMANO_HEIGHT - 1) == GROUND           # BASSO = EST
assert teatro_romano_tile_type(0, 20) == GROUND                                  # SINISTRA = SUD
assert teatro_romano_tile_type(TEATRO_ROMANO_WIDTH - 1, 20) == WALL              # DESTRA = NORD
assert (teatro_romano_tile_type(0, 20) !=
        teatro_romano_tile_type(TEATRO_ROMANO_WIDTH - 1, 20))                    # niente ribaltamento
assert (teatro_romano_tile_type(32, 1) !=
        teatro_romano_tile_type(32, TEATRO_ROMANO_HEIGHT - 1))
assert teatro_romano_tile_type(TEATRO_ROMANO_WIDTH - 1, EXIT_SAN_MARTINO_FIRST_Y) == EXIT_SAN_MARTINO
assert teatro_romano_tile_type(INGRESSO_DA_SAN_MARTINO_X, INGRESSO_DA_SAN_MARTINO_Y) != WALL
# Almeno sei tile dal proprio varco, altrimenti si rimbalza all'infinito fra le due aree.
assert (TEATRO_ROMANO_WIDTH - 1) - INGRESSO_DA_SAN_MARTINO_X >= 6
# Il fronte della cavea: 70 m = 46 tile (city_reference.h::LANDMARKS, tolleranza di un tile).
assert sum(1 for x in range(TEATRO_ROMANO_WIDTH)
           if teatro_romano_tile_type(x, 1) == CONSOLI_FACADE) == 46

# ----------------------------------------------------------------------------------------------
# Budget del Passo 9, in tile unici a 4bpp.
# ----------------------------------------------------------------------------------------------

MAX_TILES_GROUND = 512


def draw_ground():
    # 512x256: TEATRO_ROMANO_WIDTH * TILE == 512, TEATRO_ROMANO_HEIGHT * TILE == 256. Un solo
    # blocco BG, misura legale (docs/mappa_del_mondo.md sez. 5: solo 256 o 512 px per lato).
    w, h = TEATRO_ROMANO_WIDTH * TILE, TEATRO_ROMANO_HEIGHT * TILE
    px = canvas(w, h, C_VOID)

    for ty in range(TEATRO_ROMANO_HEIGHT):
        for tx in range(TEATRO_ROMANO_WIDTH):
            kind = teatro_romano_tile_type(tx, ty)
            x0, y0 = tx * TILE, ty * TILE

            for y in range(TILE):
                for x in range(TILE):
                    gx, gy = x0 + x, y0 + y

                    if kind == CONSOLI_FACADE:
                        # La cavea: blocchi calcarei a corsi orizzontali, come i palazzi delle
                        # altre aree quando manca la foto (nessun ingrediente per questa, vedi
                        # la nota in testa al file).
                        c = C_WALL if (y % 4 != 3) else C_WALL_DARK
                    elif kind == STAIRS:
                        # Le gradinate: due righe di pietra (chiara e scura) e una di erba, che
                        # cresce fra un gradone e l'altro.
                        fase = y % 4
                        if fase == 3:
                            c = C_VEG
                        elif fase == 2:
                            c = C_WALL_DARK
                        else:
                            c = C_WALL
                    elif kind == ROAD:
                        # Il pavimento del corridoio anulare: lo stesso ciottolato delle vie
                        # gia' consegnate, e' la stessa citta'.
                        c = C_WALL_DARK if ((gx * 7 + gy * 13) % 5) else C_RAIL
                        c = C_JOINT if (gx + gy) % 9 == 0 else c
                    elif kind == WALL and CORRIDOIO_FIRST_Y <= ty <= CORRIDOIO_LAST_Y:
                        # I piloni del corridoio, in parte crollati: muratura voltata con la
                        # natura che ha gia' cominciato a riprendersi la rovina.
                        c = C_VEG if (x + y) % 5 == 0 else (
                            C_ARCH if y % 4 == 3 else C_WALL_DARK)
                    elif kind == WALL:
                        # Il resto: fianchi del rudere fuori dal suo fronte, e il bordo nord
                        # chiuso oltre l'unico varco. Muratura a corsi, come le altre aree.
                        c = C_ARCH if (y % 4 == 3) else C_WALL_DARK
                    elif kind == EXIT_SAN_MARTINO:
                        c = C_ARCH if (x + y) % 8 else C_WALL_DARK
                    elif kind == GROUND:
                        # Prato aperto: fuori le mura, il tessuto edilizio finisce e comincia
                        # l'erba. A differenza del cotto della piazza, qui domina il verde.
                        c = C_VEG if (gx * 3 + gy * 5) % 4 else C_WALL_DARK
                    else:
                        c = C_STONE

                    px[gy][gx] = c

    return w, h, px


def main():
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "graphics")
    os.makedirs(out_dir, exist_ok=True)
    print("[teatro-romano-art] generazione degli asset segnaposto del Teatro Romano")

    w, h, px = draw_ground()
    check_and_write("teatro_romano_ground", w, h, px, PALETTE_GROUND, "regular_bg",
                     MAX_TILES_GROUND)

    print("[teatro-romano-art] fatto. NON e' arte definitiva: il ritaglio fotografico che "
          "servirebbe e' descritto in testa a questo file. C_WOOD e' importato per coerenza "
          "con gli altri generatori ma non e' ancora usato qui: il rudere non ha portoni.")


if __name__ == "__main__":
    main()
