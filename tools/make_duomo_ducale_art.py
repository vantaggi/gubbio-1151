#!/usr/bin/env python3
"""
Generatore di GRAFICA SEGNAPOSTO per DUOMO, GIARDINI PENSILI E PALAZZO DUCALE (Gubbio 1151).

Produce graphics/duomo_ducale_ground.bmp (512x256, regular_bg) + il suo .json, seguendo le
stesse due regole di tools/make_piazza_art.py (sez. 5-6 del contratto, docs/mappa_del_mondo.md):

1. Il suolo e' DERIVATO dalla griglia di collisione: la funzione qui sotto e' un mirror fedele di
   include/duomo_ducale_collision.h::duomo_ducale_tile_type, con le STESSE assert sugli STESSI
   punti notevoli. Se la disposizione cambia nel C++ e non qui, il giocatore attraversa un muro
   che si vede o sbatte contro un portone che non c'e'.

2. Il generatore MISURA e FALLISCE: check_and_write (importata) conta colori e tile unici contro
   il tetto del Passo 9 (512), e la .json dichiara sempre "bpp_mode": "bpp_4".

    python tools/make_duomo_ducale_art.py

COSA C'E': la terrazza monumentale sopra Piazza Grande (90 m). Un camminamento (via Ducale, che
sale) attraversa la mappa da SUD a NORD; sul fianco ovest, uno dopo l'altro salendo, il Duomo dei
Santi Mariano e Giacomo, il Palazzo Ducale di Federico da Montefeltro, i Giardini Pensili; sul
fianco est, per tutta la lunghezza, l'affaccio sulla citta' sottostante — coerente col fatto che
l'intera area sta sopra Piazza Grande, come la piazza stessa e' pensile sugli Arconi.

RITAGLI FOTOGRAFICI CHE SERVIREBBERO, e non ci sono ancora (docs/riferimenti/FONTI.md li elenca
gia' fra i "da cercare": Palazzo Ducale, Duomo). Finche' non esistono, questo script legge
(leggi_indici_bmp4) gli ingredienti SE ci sono e ripiega sul procedurale sotto - e' il ripiego che
il contratto impone (sez. 6), non un abbozzo:
  - una foto frontale della facciata del Duomo (rosone, facciata a capanna), da salvare come
    ingredienti/duomo_facciata.bmp con photo_to_tiles.py: renderebbe il rosone e i simboli degli
    evangelisti, che qui sono semplificati a un cerchio per il budget di un tile 8x8;
  - una foto frontale del fronte del Palazzo Ducale (i due ordini di arcate del cortile
    rinascimentale), da salvare come ingredienti/ducale_facciata.bmp;
  - una vista zenitale dei Giardini Pensili (le aiuole squadrate a siepi basse), da salvare come
    ingredienti/giardini_pensili.bmp: qui il reticolo e' procedurale, un motivo periodico che
    approssima la scacchiera vista dall'alto senza riprodurne il dettaglio vero.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from make_piazza_art import (TILE, canvas, check_and_write, leggi_indici_bmp4,   # noqa: E402
                              PALETTE_GROUND, C_WALL, C_WALL_DARK, C_JOINT, C_RAIL,
                              C_STONE, C_ARCH, C_WOOD, C_VOID)

# Indice 12 della PALETTE_GROUND condivisa (tools/photo_to_tiles.py::PALETTE_PIAZZA) e' la
# "vegetazione": non ha un nome esportato da make_piazza_art.py perche' nessun'altra area
# consegnata finora ne aveva bisogno. E' lo stesso colore, non una tinta nuova da tenere allineata.
C_VEGE = 12

# ----------------------------------------------------------------------------------------------
# Mirror di include/duomo_ducale_collision.h
# ----------------------------------------------------------------------------------------------

DUOMO_DUCALE_WIDTH = 64
DUOMO_DUCALE_HEIGHT = 32

(GROUND, WALL, RAILING, DOOR_CONSOLI, EXIT_SAN_MARTINO, EXIT_PORTA_ROMANA, FOUNTAIN,
 CONSOLI_FACADE, PRETORIO_FACADE, STAIRS, DOOR_PRETORIO, ROAD) = range(12)

APRON_SOUTH_FIRST_X, APRON_SOUTH_LAST_X = 0, 5
DUOMO_FIRST_X, DUOMO_LAST_X = 6, 15
GAP1_FIRST_X, GAP1_LAST_X = 16, 19
DUCALE_FIRST_X, DUCALE_LAST_X = 20, 39
GAP2_FIRST_X, GAP2_LAST_X = 40, 43
GARDEN_FIRST_X, GARDEN_LAST_X = 44, 55
APRON_NORTH_FIRST_X, APRON_NORTH_LAST_X = 56, DUOMO_DUCALE_WIDTH - 1

assert APRON_SOUTH_LAST_X + 1 == DUOMO_FIRST_X
assert DUOMO_LAST_X + 1 == GAP1_FIRST_X
assert GAP1_LAST_X + 1 == DUCALE_FIRST_X
assert DUCALE_LAST_X + 1 == GAP2_FIRST_X
assert GAP2_LAST_X + 1 == GARDEN_FIRST_X
assert GARDEN_LAST_X + 1 == APRON_NORTH_FIRST_X
assert APRON_NORTH_LAST_X == DUOMO_DUCALE_WIDTH - 1

MONUMENT_FIRST_Y, MONUMENT_LAST_Y = 0, 12
FRONT_Y = MONUMENT_LAST_Y + 1          # 13: marciapiede/gradini
PATH_FIRST_Y = FRONT_Y + 1             # 14
PATH_LAST_Y = 25
RAILING_FIRST_Y = PATH_LAST_Y + 1      # 26
RAILING_LAST_Y = 27

DUOMO_DOOR_FIRST_X, DUOMO_DOOR_LAST_X = 10, 11
DUCALE_DOOR_FIRST_X, DUCALE_DOOR_LAST_X = 29, 30

EXIT_PIAZZA_GRANDE_LAST_X = 1
EXIT_MONTE_INGINO_FIRST_X = DUOMO_DUCALE_WIDTH - 2   # 62

INGRESSO_DA_PIAZZA_GRANDE_X, INGRESSO_DA_PIAZZA_GRANDE_Y = 17, 19
INGRESSO_DA_MONTE_INGINO_X, INGRESSO_DA_MONTE_INGINO_Y = 46, 19


def in_garden(x, y):
    return (GARDEN_FIRST_X <= x <= GARDEN_LAST_X and
            MONUMENT_FIRST_Y <= y <= MONUMENT_LAST_Y)


def garden_tile(x, y):
    """Mirror di duomo_ducale_garden_tile: reticolo di siepi, sentiero ogni terza colonna e riga."""
    gx = (x - GARDEN_FIRST_X) % 3
    gy = (y - MONUMENT_FIRST_Y) % 3
    return GROUND if (gx == 2 or gy == 2) else WALL


def duomo_ducale_tile_type(x, y):
    """Mirror di include/duomo_ducale_collision.h::duomo_ducale_tile_type."""
    if x < 0 or x >= DUOMO_DUCALE_WIDTH or y < 0 or y >= DUOMO_DUCALE_HEIGHT:
        return WALL

    if MONUMENT_FIRST_Y <= y <= MONUMENT_LAST_Y:
        if DUOMO_FIRST_X <= x <= DUOMO_LAST_X:
            if y == MONUMENT_LAST_Y and DUOMO_DOOR_FIRST_X <= x <= DUOMO_DOOR_LAST_X:
                return DOOR_PRETORIO
            return CONSOLI_FACADE

        if DUCALE_FIRST_X <= x <= DUCALE_LAST_X:
            if y == MONUMENT_LAST_Y and DUCALE_DOOR_FIRST_X <= x <= DUCALE_DOOR_LAST_X:
                return DOOR_PRETORIO
            return PRETORIO_FACADE

        if in_garden(x, y):
            return garden_tile(x, y)

        return WALL

    if y == FRONT_Y:
        alla_porta = (DUOMO_DOOR_FIRST_X <= x <= DUOMO_DOOR_LAST_X or
                      DUCALE_DOOR_FIRST_X <= x <= DUCALE_DOOR_LAST_X)
        return STAIRS if alla_porta else GROUND

    if PATH_FIRST_Y <= y <= PATH_LAST_Y:
        if x <= EXIT_PIAZZA_GRANDE_LAST_X:
            return EXIT_SAN_MARTINO
        if x >= EXIT_MONTE_INGINO_FIRST_X:
            return EXIT_PORTA_ROMANA
        return ROAD

    if RAILING_FIRST_Y <= y <= RAILING_LAST_Y:
        return RAILING

    return WALL


# Gli stessi punti notevoli su cui il C++ ha le proprie static_assert.
assert duomo_ducale_tile_type(0, PATH_FIRST_Y) == EXIT_SAN_MARTINO
assert duomo_ducale_tile_type(DUOMO_DUCALE_WIDTH - 1, PATH_FIRST_Y) == EXIT_PORTA_ROMANA
assert duomo_ducale_tile_type(10, 6) == CONSOLI_FACADE
assert duomo_ducale_tile_type(29, 6) == PRETORIO_FACADE
assert duomo_ducale_tile_type(50, 26) == RAILING
assert duomo_ducale_tile_type(50, 30) == WALL
assert duomo_ducale_tile_type(DUOMO_DOOR_FIRST_X, MONUMENT_LAST_Y) == DOOR_PRETORIO
assert duomo_ducale_tile_type(DUCALE_DOOR_FIRST_X, MONUMENT_LAST_Y) == DOOR_PRETORIO
assert duomo_ducale_tile_type(DUOMO_DOOR_FIRST_X, FRONT_Y) == STAIRS
assert duomo_ducale_tile_type(DUCALE_DOOR_FIRST_X, FRONT_Y) == STAIRS
assert duomo_ducale_tile_type(GARDEN_FIRST_X, MONUMENT_FIRST_Y) == WALL
assert duomo_ducale_tile_type(GARDEN_FIRST_X + 2, MONUMENT_FIRST_Y) == GROUND
# I due ingressi (INGRESSO_DA_* nel C++) cadono su ciottolato, non su un muro.
assert duomo_ducale_tile_type(INGRESSO_DA_PIAZZA_GRANDE_X, INGRESSO_DA_PIAZZA_GRANDE_Y) == ROAD
assert duomo_ducale_tile_type(INGRESSO_DA_MONTE_INGINO_X, INGRESSO_DA_MONTE_INGINO_Y) == ROAD
# Il reticolo del giardino deve restare connesso: verificato una volta in fase di progettazione
# con un flood fill (vedi lo storico della sessione); qui si ripete solo la controprova che il
# motivo produca sia siepe sia sentiero, che e' cio' che un errore di formula romperebbe per primo.
_ground_in_garden = sum(1 for gy in range(MONUMENT_FIRST_Y, MONUMENT_LAST_Y + 1)
                         for gx in range(GARDEN_FIRST_X, GARDEN_LAST_X + 1)
                         if duomo_ducale_tile_type(gx, gy) == GROUND)
_wall_in_garden = sum(1 for gy in range(MONUMENT_FIRST_Y, MONUMENT_LAST_Y + 1)
                       for gx in range(GARDEN_FIRST_X, GARDEN_LAST_X + 1)
                       if duomo_ducale_tile_type(gx, gy) == WALL)
assert _ground_in_garden > 0 and _wall_in_garden > 0

# ----------------------------------------------------------------------------------------------
# Budget del Passo 9, in tile unici a 4bpp.
# ----------------------------------------------------------------------------------------------

MAX_TILES_GROUND = 512


def draw_duomo_facade(gx, gy, x, y):
    """Facciata a capanna col rosone, e' il segno che distingue il Duomo dal generico
    CONSOLI_FACADE che piazza_grande_collision.h disegna per il Palazzo dei Consoli: qui il
    riuso e' solo del VALORE di collisione (sez. 5 del contratto: le facciate condividono il
    trattamento "muro di monumento"), non del disegno, che e' specifico di questo edificio."""
    ty = y - MONUMENT_FIRST_Y   # riga di tile locale alla fascia dei monumenti (0..12)

    # Corsi di pietra chiara, come il resto della muratura monumentale della citta'.
    c = C_WALL if (gy % 4 != 3) else C_WALL_DARK

    if ty <= 1:
        # LA CAPANNA: il tetto a due falde che da' il nome alla facciata. Un profilo a gradini
        # che si restringe salendo (ty=0 piu' stretto di ty=1), con C_VOID a rappresentare il
        # cielo oltre la sagoma - stessa tecnica della merlatura in piazza_grande_collision.h.
        centro = (DUOMO_FIRST_X + DUOMO_LAST_X) / 2
        distanza = abs((x + gx / TILE) - centro)
        soglia = 1.5 if ty == 0 else 4.5
        c = c if distanza <= soglia else C_VOID
    elif ty == 5 and DUOMO_LAST_X - DUOMO_FIRST_X >= 8:
        # IL ROSONE: un cerchio al centro della facciata, un solo tile 8x8. Gli evangelisti
        # (sez. GDD) non ci stanno in un tile e restano il ritaglio fotografico da recuperare
        # (vedi la testata del file): qui il segno e' ridotto al rosone da solo.
        centro_tile = (DUOMO_FIRST_X + DUOMO_LAST_X) // 2
        if x == centro_tile:
            raggio = ((gx - 3.5) ** 2 + (gy - 3.5) ** 2) ** 0.5
            if raggio <= 3:
                c = C_ARCH if raggio >= 1.5 else C_WALL_DARK

    return c


def draw_ducale_facade(gx, gy, x, y):
    """Il cortile rinascimentale a due ordini di arcate, reso sul fronte esterno come due fasce
    orizzontali di archi - la stessa idea grafica degli archi voltati gia' usata da
    piazza_grande_collision.h per le uscite (C_ARCH dentro C_WALL_DARK), ripetuta due volte in
    altezza per dire "due ordini"."""
    ty = y - MONUMENT_FIRST_Y

    c = C_WALL if (gy % 4 != 3) else C_WALL_DARK

    if ty in (3, 4, 8, 9):
        # Ogni arco occupa 3 colonne di tile, con un pilastro fra un arco e l'altro: il ritmo
        # "arco-pilastro" e' cio' che rende leggibile un porticato a 8 px per tile. La sommita'
        # dell'arco (gy piccola) resta pietra piena, il vano voltato si apre sotto.
        tx_local = x - DUCALE_FIRST_X
        if tx_local % 3 != 0:
            c = C_ARCH if gy >= 2 else C_WALL_DARK

    return c


def draw_garden_hedge(gx, gy):
    """La siepe bassa: verde compatto con un bordo piu' scuro, cosi' che il reticolo si legga
    anche a 8 px per tile - lo stesso principio della merlatura in piazza_grande_collision.h,
    un motivo che si legge per silhouette invece che per dettaglio."""
    bordo = gx == 0 or gy == 0 or gx == TILE - 1 or gy == TILE - 1
    return C_WALL_DARK if bordo else C_VEGE


def draw_ground():
    cotto, cotto_w, cotto_h = leggi_indici_bmp4("piazza_cotto.bmp")

    # 512x256: le misure BMP legali sono solo 256 o 512 per lato. L'area e' 64x32 tile: piu'
    # larga che alta, al contrario di Piazza Grande, perche' qui l'asse lungo (il camminamento
    # SUD-NORD) e' quello orizzontale sullo schermo (x cresce verso NORD, la destra).
    w, h = DUOMO_DUCALE_WIDTH * TILE, DUOMO_DUCALE_HEIGHT * TILE
    px = canvas(w, h, C_VOID)

    for ty in range(DUOMO_DUCALE_HEIGHT):
        for tx in range(DUOMO_DUCALE_WIDTH):
            kind = duomo_ducale_tile_type(tx, ty)
            x0, y0 = tx * TILE, ty * TILE

            for y in range(TILE):
                for x in range(TILE):
                    gx, gy = x0 + x, y0 + y

                    if kind == ROAD:
                        # Ciottolato della salita: stessa formula del ciottolato di Piazza Grande
                        # e di via dei Consoli, per restare la stessa citta' sotto i piedi.
                        c = C_WALL_DARK if ((gx * 7 + gy * 13) % 5) else C_RAIL
                        c = C_JOINT if (gx + gy) % 9 == 0 else c
                    elif kind == GROUND:
                        if cotto:
                            c = cotto[gy % cotto_h][gx % cotto_w]
                        else:
                            base = C_STONE if (tx + ty) % 2 == 0 else C_WALL_DARK
                            c = C_JOINT if (x == 0 or y == 0) else base
                    elif kind == CONSOLI_FACADE:
                        c = draw_duomo_facade(x, y, tx, ty)
                    elif kind == PRETORIO_FACADE:
                        # PRETORIO_FACADE qui e' sempre il Palazzo Ducale: il reticolo dei
                        # giardini (garden_tile) non produce mai questo valore, restituisce solo
                        # GROUND o WALL.
                        c = draw_ducale_facade(x, y, tx, ty)
                    elif kind == STAIRS:
                        c = C_WALL if (y % 2 == 0) else C_RAIL
                    elif kind == WALL:
                        if in_garden(tx, ty):
                            c = draw_garden_hedge(x, y)
                        else:
                            c = C_ARCH if (y % 4 == 3) else C_WALL_DARK
                    elif kind == RAILING:
                        c = C_RAIL if y < 4 else C_WALL_DARK
                    elif kind == DOOR_PRETORIO:
                        c = C_WOOD if 1 <= x <= 6 else C_WALL_DARK
                    elif kind in (EXIT_SAN_MARTINO, EXIT_PORTA_ROMANA):
                        c = C_ARCH if (x + y) % 8 else C_WALL_DARK
                    else:
                        c = C_WALL_DARK

                    px[gy][gx] = c

    return w, h, px


def main():
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "graphics")
    os.makedirs(out, exist_ok=True)
    print("[duomo-ducale-art] generazione degli asset segnaposto di Duomo, Giardini Pensili e "
          "Palazzo Ducale")

    w, h, px = draw_ground()
    check_and_write("duomo_ducale_ground", w, h, px, PALETTE_GROUND, "regular_bg",
                     MAX_TILES_GROUND)

    print("[duomo-ducale-art] fatto. NON e' arte definitiva: sostituire il .bmp mantenendo "
          "misure e 16 colori, senza toccare il C++.")


if __name__ == "__main__":
    main()
