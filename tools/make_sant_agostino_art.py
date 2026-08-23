#!/usr/bin/env python3
"""
Generatore di GRAFICA SEGNAPOSTO per la ZONA DI SANT'AGOSTINO (Gubbio 1151).

Produce, in graphics/:

    sant_agostino_ground.bmp   256x512   regular_bg   strada, slargo, facciata della chiesa

NON e' arte definitiva (docs/mappa_del_mondo.md sez. 6): budget zero, nessuno che sappia
disegnare. Ogni tile nasce da una foto quando l'ingrediente esiste in ingredienti/, e da un
ripiego procedurale quando non esiste -- cosi' la build resta riproducibile anche per chi clona
il progetto senza le foto, che non sono versionate. Oggi in ingredienti/ NON esiste una facciata
della Chiesa di Sant'Agostino: e' interamente procedurale.

DUE REGOLE, le stesse di tools/make_piazza_art.py:

1. Il suolo e' DERIVATO dalla griglia di collisione: il mirror Python di
   `sant_agostino_tile_type` qui sotto e' un port fedele di include/sant_agostino_collision.h,
   con le STESSE assert sugli STESSI punti notevoli. Due copie che divergono in silenzio sono
   peggio di una sola.
2. Il generatore MISURA e FALLISCE: conteggio colori contro il bpp_mode dichiarato e conteggio
   dei tile unici contro il tetto di 512 (Passo 9 del piano).

    python tools/make_sant_agostino_art.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_piazza_art import (TILE, canvas, check_and_write, leggi_indici_bmp4,   # noqa: E402
                              PALETTE_GROUND, C_WALL, C_WALL_DARK, C_JOINT, C_RAIL,
                              C_STONE, C_ARCH, C_WOOD, C_VOID)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "graphics")

# ----------------------------------------------------------------------------------------------
# Mirror di include/sant_agostino_collision.h
# ----------------------------------------------------------------------------------------------

SANT_AGOSTINO_WIDTH = 32
SANT_AGOSTINO_HEIGHT = 64

# Valori di TileType (piazza_grande_collision.h), NON ridefiniti: gli stessi nomi, gli stessi
# numeri. USCITA 4 usa il valore EXIT_SAN_MARTINO (verso via XX Settembre), USCITA 5 usa
# EXIT_PORTA_ROMANA (verso Sant'Andrea) -- riusati, come impone il contratto (sez. 5).
(GROUND, WALL, RAILING, DOOR_CONSOLI, EXIT_SAN_MARTINO, EXIT_PORTA_ROMANA, FOUNTAIN,
 CONSOLI_FACADE, PRETORIO_FACADE, STAIRS, DOOR_PRETORIO, ROAD) = range(12)

ROAD_FIRST_X = 27
NORTH_FRONT_X = 31

CHIESA_FACADE_FIRST_X, CHIESA_FACADE_LAST_X = 9, 18   # 10 tile = 15 m, in scala
CHIESA_FACADE_LAST_Y = 18

SCALINATA_CHIESA_FIRST_X, SCALINATA_CHIESA_LAST_X = 13, 14
SCALINATA_CHIESA_Y = CHIESA_FACADE_LAST_Y + 1   # 19

SLARGO_FIRST_X, SLARGO_LAST_X = 2, ROAD_FIRST_X - 1   # 2..26
SLARGO_FIRST_Y, SLARGO_LAST_Y = SCALINATA_CHIESA_Y, 40   # 19..40

INGRESSO_DA_VIA_XX_SETTEMBRE_X, INGRESSO_DA_VIA_XX_SETTEMBRE_Y = 28, 16
INGRESSO_DA_SANT_ANDREA_X, INGRESSO_DA_SANT_ANDREA_Y = 28, 47


def sant_agostino_tile_type(x, y):
    """Mirror di include/sant_agostino_collision.h::sant_agostino_tile_type. Mappa ruotata con
    l'ovest in alto: alto = imbocco da via XX Settembre, basso = sbocco verso Sant'Andrea,
    destra = strada di passaggio (nord reale), sinistra/centro = slargo e facciata della chiesa."""
    if x < 0 or x >= SANT_AGOSTINO_WIDTH or y < 0 or y >= SANT_AGOSTINO_HEIGHT:
        return WALL

    if x >= NORTH_FRONT_X:
        return WALL

    if x >= ROAD_FIRST_X:
        if y <= 8:
            return EXIT_SAN_MARTINO   # USCITA 4 -> via XX Settembre
        if y >= SANT_AGOSTINO_HEIGHT - 9:
            return EXIT_PORTA_ROMANA   # USCITA 5 -> Sant'Andrea
        return ROAD

    if y <= CHIESA_FACADE_LAST_Y:
        if CHIESA_FACADE_FIRST_X <= x <= CHIESA_FACADE_LAST_X:
            return CONSOLI_FACADE
        return WALL

    if y == SCALINATA_CHIESA_Y and SCALINATA_CHIESA_FIRST_X <= x <= SCALINATA_CHIESA_LAST_X:
        return STAIRS

    if SLARGO_FIRST_Y <= y <= SLARGO_LAST_Y:
        if SLARGO_FIRST_X <= x <= SLARGO_LAST_X:
            return GROUND
        return WALL

    return WALL


# Gli stessi punti notevoli su cui il C++ ha le proprie static_assert.
assert sant_agostino_tile_type(28, 0) == EXIT_SAN_MARTINO
assert sant_agostino_tile_type(28, SANT_AGOSTINO_HEIGHT - 1) == EXIT_PORTA_ROMANA
assert sant_agostino_tile_type(INGRESSO_DA_VIA_XX_SETTEMBRE_X, INGRESSO_DA_VIA_XX_SETTEMBRE_Y) != WALL
assert sant_agostino_tile_type(INGRESSO_DA_SANT_ANDREA_X, INGRESSO_DA_SANT_ANDREA_Y) != WALL
assert sant_agostino_tile_type(0, 25) == WALL          # SINISTRA = SUD: tessuto chiuso
assert sant_agostino_tile_type(31, 25) == WALL         # DESTRA = NORD: fronte oltre la strada
assert sant_agostino_tile_type(13, 10) == CONSOLI_FACADE   # la chiesa sta in ALTO (ovest reale)
assert sant_agostino_tile_type(28, SANT_AGOSTINO_HEIGHT - 1) != EXIT_SAN_MARTINO
assert sant_agostino_tile_type(28, 0) != EXIT_PORTA_ROMANA
assert sant_agostino_tile_type(SCALINATA_CHIESA_FIRST_X, SCALINATA_CHIESA_Y) != WALL
assert sant_agostino_tile_type(14, 30) == GROUND       # centro dello slargo, aperto
assert sant_agostino_tile_type(SLARGO_LAST_X, 30) != WALL   # lo slargo confina con la strada

# ----------------------------------------------------------------------------------------------
# Budget del Passo 9, in tile unici a 4bpp.
# ----------------------------------------------------------------------------------------------

MAX_TILES_GROUND = 512

# Il rosone gotico, sopra il portale: uno dei segni che una facciata a 8 px puo' permettersi
# (docs/riferimenti/FONTI.md), insieme al portale ad arco e ai corsi di pietra chiara.
ROSONE_X = {13, 14}
ROSONE_Y = CHIESA_FACADE_LAST_Y - 7   # a meta' salita della facciata, sopra il portale


def draw_ground():
    # Stesso ingrediente fotografico del selciato gia' usato per Piazza Grande, Largo del
    # Bargello, San Martino, San Pietro e Sant'Andrea: e' la stessa citta'.
    cotto, cotto_w, cotto_h = leggi_indici_bmp4("piazza_cotto.bmp")
    # Nessun ingrediente fotografico per la facciata di Sant'Agostino: e' interamente procedurale
    # (vedi la nota in testa al file e il campo "ritagli_fotografici_richiesti" del rendiconto).
    facciata, facc_w, facc_h = leggi_indici_bmp4("sant_agostino_facciata.bmp")

    w = SANT_AGOSTINO_WIDTH * TILE     # 256
    h = SANT_AGOSTINO_HEIGHT * TILE    # 512
    px = canvas(w, h, C_VOID)

    for ty in range(SANT_AGOSTINO_HEIGHT):
        for tx in range(SANT_AGOSTINO_WIDTH):
            kind = sant_agostino_tile_type(tx, ty)
            x0, y0 = tx * TILE, ty * TILE
            rosone = (tx in ROSONE_X and ty == ROSONE_Y)

            for y in range(TILE):
                for x in range(TILE):
                    gx, gy = x0 + x, y0 + y

                    if kind in (EXIT_SAN_MARTINO, EXIT_PORTA_ROMANA):
                        # Stesso trattamento grafico dei varchi gia' consegnati: un passaggio in
                        # ombra, non un muro pieno.
                        c = C_ARCH if (x + y) % 8 else C_WALL_DARK
                    elif kind == ROAD:
                        # Ciottolato irregolare, stessa formula delle altre vie della citta'.
                        if cotto:
                            c = cotto[gy % cotto_h][gx % cotto_w]
                        else:
                            c = C_WALL_DARK if (gx * 7 + gy * 13) % 5 else C_RAIL
                            c = C_JOINT if (gx + gy) % 9 == 0 else c
                    elif kind == STAIRS:
                        # Gradini: righe alternate chiare e scure, leggibili a 8 px.
                        c = C_WALL if (y % 2 == 0) else C_RAIL
                    elif kind == GROUND:
                        # Lo slargo davanti alla chiesa: la stessa pavimentazione fotografata se
                        # c'e', altrimenti lastre chiare con le fughe.
                        if cotto:
                            c = cotto[gy % cotto_h][gx % cotto_w]
                        else:
                            c = C_JOINT if (x == 0 or y == 0) else C_STONE
                    elif kind == CONSOLI_FACADE:
                        if facciata:
                            # Se un giorno arrivera' l'ingrediente fotografico, si incolla qui,
                            # allineato all'angolo della fascia -- come consoli_facciata in
                            # tools/make_piazza_art.py.
                            fx = gx - CHIESA_FACADE_FIRST_X * TILE
                            fy = gy - 0
                            c = (facciata[fy][fx] if 0 <= fx < facc_w and 0 <= fy < facc_h
                                 else C_WALL)
                        elif ty == SCALINATA_CHIESA_Y - 1 and tx in (13, 14):
                            # Il portale gotico ad arco, appena sopra la scalinata: legno scuro
                            # incorniciato, la stessa idea del portone dei Consoli.
                            c = C_WOOD if 1 <= x <= 6 else C_WALL_DARK
                        elif rosone:
                            # Il rosone: un oculo scuro in un anello di pietra chiara, il segno
                            # che rende la facciata "quella di una chiesa gotica" e non un palazzo.
                            dx, dy = x - 3.5, y - 3.5
                            dist2 = dx * dx + dy * dy
                            if dist2 <= 6:
                                c = C_ARCH
                            elif dist2 <= 11:
                                c = C_RAIL
                            else:
                                c = C_WALL if y % 4 != 3 else C_WALL_DARK
                        elif ty == 0:
                            # Il coronamento, lontano dallo slargo: una cornice scura in sommita',
                            # come le altre facciate maggiori della citta'.
                            c = C_WALL_DARK if y < 2 else C_WALL
                        else:
                            # Corsi di pietra chiara orizzontali: la "pietra chiara" della
                            # descrizione dell'area.
                            c = C_WALL if y % 4 != 3 else C_WALL_DARK
                    else:
                        # Il tessuto edilizio minore che chiude i fianchi della chiesa e il fronte
                        # oltre la strada: corsi di pietra piu' scuri, per restare distinto dal
                        # monumento.
                        c = C_ARCH if (y % 4 == 3) else C_WALL_DARK

                    px[gy][gx] = c

    return w, h, px


def main():
    os.makedirs(OUT, exist_ok=True)
    print("[sant-agostino-art] generazione degli asset segnaposto della Zona di Sant'Agostino")

    w, h, px = draw_ground()
    check_and_write("sant_agostino_ground", w, h, px, PALETTE_GROUND, "regular_bg",
                     MAX_TILES_GROUND)

    print("[sant-agostino-art] fatto. Ritaglio fotografico che servirebbe (docs/mappa_del_mondo.md "
          "sez. 6), oggi assente in ingredienti/: una foto FRONTALE della facciata della Chiesa "
          "di Sant'Agostino (portale gotico e rosone leggibili, senza cavi elettrici ne' auto in "
          "primo piano), per sostituire la texture procedurale senza toccare il C++.")


if __name__ == "__main__":
    main()
