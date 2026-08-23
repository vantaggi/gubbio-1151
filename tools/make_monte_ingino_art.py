#!/usr/bin/env python3
"""
Generatore di GRAFICA SEGNAPOSTO per GLI STRADONI DEL MONTE INGINO (Gubbio 1151).

Produce, in graphics/:

    monte_ingino_ground.bmp   512x256   regular_bg   sentiero, tornanti, belvedere, muretti, bosco

NON e' arte definitiva (docs/mappa_del_mondo.md sez. 6): budget zero, nessuno che sappia
disegnare. Nessun ingrediente fotografico esiste oggi per la salita al monte (vedi il messaggio
finale di main() per i ritagli che servirebbero, ed e' un vuoto gia' segnalato in
docs/riferimenti/FONTI.md: "vista dal Monte Ingino verso il basso" e' fra le cose "ancora da
cercare"): tutto il disegno e' procedurale, il ripiego dichiarato che tiene la build riproducibile
anche per chi clona il progetto senza le foto, che non sono versionate.

DUE REGOLE, le stesse di tools/make_piazza_art.py e tools/make_bottaccione_art.py:

1. Il suolo e' DERIVATO dalla griglia di collisione: il mirror Python qui sotto e' un port
   fedele di include/monte_ingino_collision.h, STESSA tabella di tornanti, STESSA
   interpolazione intera (compreso il troncamento verso lo zero della divisione intera con
   segno, che in Python != in C++: vedi `_trunc_div`), STESSE assert sugli STESSI punti
   notevoli — INGRESSO e larghezza del sentiero comprese.
2. Il generatore MISURA e FALLISCE: conteggio colori contro il bpp_mode dichiarato e conteggio
   dei tile unici contro il tetto di 512 (Passo 9 del piano). La texture qui sotto dipende quasi
   ovunque solo dalla posizione LOCALE dentro il tile (8x8) e da un piccolo indice periodico di
   riga/colonna di tile, mai dal pixel assoluto: e' cosi' che un sentiero lungo 64 tile e un bosco
   che ne copre la meta' restano una manciata di tile unici invece di migliaia.

    python tools/make_monte_ingino_art.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from make_piazza_art import (TILE, canvas, check_and_write, leggi_indici_bmp4,
                              PALETTE_GROUND, C_WALL, C_WALL_DARK, C_JOINT, C_RAIL,
                              C_STONE, C_ARCH, C_WOOD, C_VOID)   # noqa: E402

# ----------------------------------------------------------------------------------------------
# Mirror di include/monte_ingino_collision.h
# ----------------------------------------------------------------------------------------------

MONTE_INGINO_WIDTH = 64
MONTE_INGINO_HEIGHT = 32

(GROUND, WALL, RAILING, DOOR_CONSOLI, EXIT_SAN_MARTINO, EXIT_PORTA_ROMANA, FOUNTAIN,
 CONSOLI_FACADE, PRETORIO_FACADE, STAIRS, DOOR_PRETORIO, ROAD) = range(12)

# Colore aggiuntivo della palette condivisa (photo_to_tiles.PALETTE_PIAZZA, importata qui come
# PALETTE_GROUND) che make_piazza_art non nomina perche' non gli serve: indice 12, "vegetazione".
# NON e' una tinta nuova: e' semplicemente il nome che manca all'indice che il bosco di lecci usa.
C_FOREST = 12
C_WATER = 11   # acqua della fontana, stesso indice di piazza_cotto/fontana

PATH_HALF_WIDTH = 2   # 2*2+1 = 5 tile calpestabili per colonna, come nel C++

# STESSA tabella di include/monte_ingino_collision.h::MONTE_INGINO_PATH, x strettamente crescente.
PATH = [
    (0, 15), (12, 15), (18, 4), (28, 4), (34, 27), (44, 27), (50, 24), (63, 24),
]

STAIRS_FIRST_X, STAIRS_LAST_X = 28, 34
BELVEDERE_OVEST_FIRST_X, BELVEDERE_OVEST_LAST_X = 18, 28
BELVEDERE_EST_FIRST_X, BELVEDERE_EST_LAST_X = 34, 44
FONTANILE_X, FONTANILE_Y = 23, 4

VARCO_VALLE_FIRST_Y, VARCO_VALLE_LAST_Y = 13, 17
VARCO_VETTA_FIRST_Y, VARCO_VETTA_LAST_Y = 22, 26

INGRESSO_DA_DUOMO_DUCALE_X, INGRESSO_DA_DUOMO_DUCALE_Y = 8, 15
INGRESSO_DA_BASILICA_X, INGRESSO_DA_BASILICA_Y = 55, 24


def _trunc_div(a, b):
    """Divisione intera che tronca verso lo zero, come in C++ (e non come `//` di Python, che
    arrotonda verso meno infinito). La differenza conta solo quando il numeratore e' negativo —
    cioe' esattamente nei tratti dei tornanti dove il sentiero scende invece di salire — ed e'
    proprio li' che le due griglie divergerebbero in silenzio senza questa funzione."""
    q = abs(a) // abs(b)
    return -q if (a < 0) != (b < 0) else q


def path_center_y(x):
    """Mirror di monte_ingino_path_center_y: interpolazione lineare intera fra i punti di PATH."""
    for i in range(len(PATH) - 1):
        x0, y0 = PATH[i]
        x1, y1 = PATH[i + 1]

        if x <= x1 or i + 2 == len(PATH):
            return y0 + _trunc_div((y1 - y0) * (x - x0), x1 - x0)

    return PATH[-1][1]   # irraggiungibile: x resta 0..63


def monte_ingino_tile_type(x, y):
    """Mirror di include/monte_ingino_collision.h::monte_ingino_tile_type."""
    if x < 0 or x >= MONTE_INGINO_WIDTH or y < 0 or y >= MONTE_INGINO_HEIGHT:
        return WALL

    if x == 0:
        if VARCO_VALLE_FIRST_Y <= y <= VARCO_VALLE_LAST_Y:
            return EXIT_SAN_MARTINO      # valore 4: USCITA verso Duomo/Ducale
        return WALL

    if x == MONTE_INGINO_WIDTH - 1:
        if VARCO_VETTA_FIRST_Y <= y <= VARCO_VETTA_LAST_Y:
            return EXIT_PORTA_ROMANA     # valore 5: USCITA verso la Basilica
        return WALL

    if x == FONTANILE_X and y == FONTANILE_Y:
        return FOUNTAIN

    centro = path_center_y(x)
    distanza = abs(y - centro)

    if distanza <= PATH_HALF_WIDTH:
        if STAIRS_FIRST_X <= x <= STAIRS_LAST_X:
            return STAIRS
        return GROUND

    if BELVEDERE_OVEST_FIRST_X <= x <= BELVEDERE_OVEST_LAST_X and y < centro:
        return RAILING

    if BELVEDERE_EST_FIRST_X <= x <= BELVEDERE_EST_LAST_X and y > centro:
        return RAILING

    return WALL


# Gli stessi punti notevoli su cui il C++ ha le proprie static_assert.
assert [p[0] for p in PATH] == sorted(p[0] for p in PATH) and len(set(p[0] for p in PATH)) == len(PATH), \
    "i punti dei tornanti devono avere x strettamente crescente"
assert monte_ingino_tile_type(0, 15) == EXIT_SAN_MARTINO
assert monte_ingino_tile_type(MONTE_INGINO_WIDTH - 1, 24) == EXIT_PORTA_ROMANA
assert monte_ingino_tile_type(23, 0) == RAILING             # ALTO SCHERMO = OVEST: primo belvedere
assert monte_ingino_tile_type(38, 31) == RAILING            # BASSO SCHERMO = EST: secondo belvedere
assert monte_ingino_tile_type(INGRESSO_DA_DUOMO_DUCALE_X, INGRESSO_DA_DUOMO_DUCALE_Y) not in (WALL, RAILING)
assert monte_ingino_tile_type(INGRESSO_DA_BASILICA_X, INGRESSO_DA_BASILICA_Y) not in (WALL, RAILING)
assert INGRESSO_DA_DUOMO_DUCALE_X - 0 >= 6, "l'ingresso deve stare almeno sei tile dal proprio varco"
assert (MONTE_INGINO_WIDTH - 1) - INGRESSO_DA_BASILICA_X >= 6, \
    "l'ingresso deve stare almeno sei tile dal proprio varco"
for _x in range(MONTE_INGINO_WIDTH):
    _larghezza = sum(1 for _y in range(MONTE_INGINO_HEIGHT)
                      if monte_ingino_tile_type(_x, _y) not in (WALL, RAILING, PRETORIO_FACADE,
                                                                 CONSOLI_FACADE))
    assert _larghezza == 2 * PATH_HALF_WIDTH + 1, \
        f"colonna {_x}: il sentiero non e' largo {2 * PATH_HALF_WIDTH + 1} tile"

# ----------------------------------------------------------------------------------------------
# Budget del Passo 9, in tile unici a 4bpp.
# ----------------------------------------------------------------------------------------------

MAX_TILES_GROUND = 512


def draw_ground():
    w, h = MONTE_INGINO_WIDTH * TILE, MONTE_INGINO_HEIGHT * TILE   # 512x256
    px = canvas(w, h, C_VOID)

    fontana, font_w, font_h = leggi_indici_bmp4("fontana.bmp")

    for ty in range(MONTE_INGINO_HEIGHT):
        for tx in range(MONTE_INGINO_WIDTH):
            kind = monte_ingino_tile_type(tx, ty)
            x0, y0 = tx * TILE, ty * TILE
            centro_tx = path_center_y(tx)
            distanza_tx = abs(ty - centro_tx)

            for y in range(TILE):
                for x in range(TILE):
                    if kind == GROUND:
                        # Sterrato: terra battuta, due tinte di cotto (le piu' vicine al marrone
                        # che la palette condivisa offra) alternate per tile, con la fuga scura
                        # a segnare il bordo di ogni lastra come nel selciato di piazza.
                        base = C_STONE if (tx + ty) % 2 == 0 else C_WALL_DARK
                        c = C_JOINT if (x == 0 or y == 0) else base
                    elif kind == STAIRS:
                        # I gradini del tornante ripido: righe alternate chiare e scure, lo
                        # stesso segno leggibile a 8 px usato in Piazza Grande.
                        c = C_WALL if (y % 2 == 0) else C_RAIL
                    elif kind == RAILING:
                        # Il parapetto dei due belvedere: identico a quello di Piazza Grande,
                        # Bottaccione e Basilica.
                        c = C_RAIL if y < 4 else C_WALL_DARK
                    elif kind in (EXIT_SAN_MARTINO, EXIT_PORTA_ROMANA):
                        c = C_ARCH if (x + y) % 8 else C_WALL_DARK
                    elif kind == FOUNTAIN:
                        if fontana:
                            # Riusa l'ingrediente della Fontana dei Matti, ritagliato: non e' lo
                            # stesso monumento, ma e' la stessa pietra e la stessa acqua, ed e'
                            # meglio del cerchio procedurale se la foto esiste.
                            c = fontana[y % font_h][x % font_w]
                        else:
                            # Un piccolo fontanile di sosta: vasca d'acqua con la cornice in
                            # pietra, in un solo tile 8x8.
                            dentro = 2 <= x <= 5 and 2 <= y <= 5
                            c = C_WATER if dentro else C_WALL
                    elif kind == WALL:
                        # Vicino al sentiero (fino a due tile oltre il bordo): muretto a secco di
                        # contenimento, pietra a corsi come in tutte le altre aree. Piu' lontano:
                        # il bosco di lecci che riempie il resto della mappa.
                        if distanza_tx <= PATH_HALF_WIDTH + 2:
                            c = C_ARCH if (y % 4 == 3) else C_WALL_DARK
                        else:
                            # Chiazze di chioma, di dimensione e fase diverse da tile a tile (un
                            # piccolo indice periodico su tx/ty, mai il pixel assoluto), cosi' il
                            # bosco non e' un tappeto uniforme ma resta una manciata di tile unici.
                            fase = (tx * 3 + ty * 5) % 4
                            chioma = ((x - fase) % 4 < 2) == ((y + fase) % 4 < 2)
                            c = C_FOREST if chioma else C_ARCH
                    else:
                        c = C_WALL_DARK

                    px[y0 + y][x0 + x] = c

    return w, h, px


def main():
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "graphics")
    os.makedirs(out_dir, exist_ok=True)
    print("[monte-ingino-art] generazione degli asset segnaposto degli Stradoni del Monte Ingino")

    w, h, px = draw_ground()
    check_and_write("monte_ingino_ground", w, h, px, PALETTE_GROUND, "regular_bg",
                     MAX_TILES_GROUND)

    print("[monte-ingino-art] fatto. Ritagli fotografici che servirebbero (docs/mappa_del_mondo.md "
          "sez. 6), oggi assenti in ingredienti/ e gia' segnalati come mancanti in "
          "docs/riferimenti/FONTI.md: uno STERRATO di montagna con muretti a secco ai lati, per "
          "sostituire il selciato in cotto riadattato; un BOSCO DI LECCI ripreso da vicino, per "
          "sostituire le chiazze di chioma procedurali; e la VISTA DAL MONTE INGINO VERSO IL "
          "BASSO (struttura a terrazze) da mettere oltre i due parapetti, senza toccare il C++.")


if __name__ == "__main__":
    main()
