#!/usr/bin/env python3
"""
Generatore di GRAFICA SEGNAPOSTO per PIAZZA GRANDE (Gubbio 1151).

Produce i .bmp a 4bpp e i .json che Butano si aspetta in graphics/:

    piazza_ground.bmp     512x512  regular_bg   suolo, palazzi, ringhiera, fontana
    piazza_sky.bmp        256x256  regular_bg   cielo in parallasse
    overworld_ubaldo.bmp   16x256  sprite       4 direzioni x 4 fotogrammi, 16x16 ciascuno

NON e' arte definitiva. Il suo scopo e' sbloccare il rendering dell'esplorazione, esattamente
come `make_placeholder_art.py` ha sbloccato quello della battaglia.

DUE REGOLE CHE QUESTO GENERATORE APPLICA, e che il piano ha imposto dopo averle viste fallire:

1. Il suolo e' DERIVATO dalla griglia di collisione, non disegnato a mano accanto ad essa.
   Se un muro si sposta in `piazza_grande_collision.h`, si sposta anche il muro disegnato: e'
   impossibile che il giocatore sbatta contro un palazzo che non si vede, o attraversi quello
   che si vede. Il mirror Python di `get_tile_type` qui sotto e' verificato contro gli stessi
   punti notevoli su cui il C++ ha le sue `static_assert`.

2. Il generatore MISURA e FALLISCE: conteggio dei colori contro il `bpp_mode` dichiarato e
   conteggio dei tile unici contro le soglie del Passo 9. Senza il campo `bpp_mode` esplicito,
   `butano_graphics_tool.py` promuove SILENZIOSAMENTE a 8bpp qualunque BMP oltre i 16 colori:
   tile da 32 a 64 byte e, per un background, uso della palette a 256 colori — cioe' tutti e 16
   i banchi, con ground + cielo + HUD che diventa aritmeticamente impossibile.

    python tools/make_piazza_art.py
"""

import os
import struct
import sys

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "graphics")

# ----------------------------------------------------------------------------------------------
# Mirror di include/piazza_grande_collision.h
#
# E' un port fedele, nella stessa forma gia' adottata da tests/test_battle_engine.py per il
# motore di combattimento: il C++ resta la fonte di verita', questo lo rispecchia e gli assert
# in fondo alla funzione impediscono che i due divergano in silenzio.
# ----------------------------------------------------------------------------------------------

PIAZZA_WIDTH = 64
PIAZZA_HEIGHT = 40
TILE = 8

(GROUND, WALL, RAILING, DOOR_CONSOLI, EXIT_SAN_MARTINO, EXIT_PORTA_ROMANA, FOUNTAIN,
 CONSOLI_FACADE, PRETORIO_FACADE, STAIRS) = range(10)


def get_tile_type(x, y):
    if x < 0 or x >= PIAZZA_WIDTH or y < 0 or y >= PIAZZA_HEIGHT:
        return WALL
    if y >= 38:
        return RAILING
    if 34 <= y <= 37 and 24 <= x <= 39:
        return PRETORIO_FACADE
    if y <= 18:
        if y == 18 and x in (32, 33):
            return DOOR_CONSOLI
        if 21 <= x <= 42:
            return CONSOLI_FACADE
        return WALL
    if y == 19 and 29 <= x <= 34:
        return STAIRS
    if x <= 2 and 19 <= y <= 22:
        return EXIT_SAN_MARTINO
    if x >= 61 and 19 <= y <= 22:
        return EXIT_PORTA_ROMANA
    if 23 <= x <= 24 and 24 <= y <= 25:
        return FOUNTAIN
    return GROUND


# Gli stessi punti notevoli su cui il C++ ha le proprie static_assert.
assert get_tile_type(32, 18) == DOOR_CONSOLI
assert get_tile_type(0, 39) == RAILING
assert get_tile_type(32, 30) == GROUND
assert get_tile_type(23, 24) == FOUNTAIN
assert get_tile_type(21, 17) == CONSOLI_FACADE and get_tile_type(20, 17) == WALL
assert get_tile_type(32, 35) == PRETORIO_FACADE
assert get_tile_type(32, 19) == STAIRS

# ----------------------------------------------------------------------------------------------
# Budget del Passo 9, in tile unici a 4bpp. Tetto duro di Butano: 1024 tile per tileset.
# ----------------------------------------------------------------------------------------------

MAX_TILES_GROUND = 512
MAX_TILES_SKY = 128

# ----------------------------------------------------------------------------------------------
# Palette (Sez. 14C GDD come intenzione d'arte: pietra calcarea del Monte Ingino, cotto, bronzo)
# ----------------------------------------------------------------------------------------------

C_VOID = 0        # fuori mappa / trasparente per gli sprite
C_STONE = 1       # lastricato chiaro
C_STONE_ALT = 2   # lastricato, seconda tinta
C_JOINT = 3       # fuga fra le lastre
C_WALL = 4        # muratura dei palazzi
C_WALL_DARK = 5   # ombra della muratura
C_WOOD = 6        # portone dei Consoli
C_RAIL = 7        # parapetto panoramico
C_WATER = 8       # Fontana dei Matti
C_ARCH = 9        # varchi laterali
C_SKIN = 10
C_ROBE = 11
C_ROBE_DARK = 12
C_GOLD = 13
C_SKY_HI = 14
C_SKY_LO = 15

# Le tinte vere della citta', lette dalle fotografie d'insieme (vedi docs/riferimenti/FONTI.md):
# pietra calcarea quasi bianca per i palazzi, COTTO ROSSO per la pavimentazione della piazza —
# che la Sez. 23 GDD chiama "spina di pesce rossa" e che il segnaposto rendeva in grigio-beige.
PALETTE_GROUND = [
    (0, 0, 0),          # 0  fuori mappa
    (166, 86, 58),      # 1  cotto della pavimentazione
    (148, 74, 50),      # 2  cotto, seconda tinta
    (112, 56, 40),      # 3  fuga fra le lastre
    (226, 220, 206),    # 4  pietra calcarea dei palazzi, quasi bianca
    (168, 160, 146),    # 5  ombra della pietra
    (110, 72, 40),      # 6  legno del portone
    (150, 140, 120),    # 7  parapetto
    (64, 118, 152),     # 8  acqua
    (96, 88, 78),       # 9  varco
    (222, 180, 140),    # 10 (riservati allo sprite, tenuti allineati)
    (150, 40, 40),
    (100, 26, 26),
    (206, 172, 74),
    (120, 160, 200),
    (78, 118, 168),
]

PALETTE_SKY = [
    (0, 0, 0),
    (150, 186, 220), (136, 174, 212), (122, 162, 204), (110, 150, 196),
    (98, 138, 188), (88, 128, 180), (78, 118, 172), (70, 108, 164),
    (210, 214, 220), (196, 202, 212), (182, 190, 204), (168, 178, 196),
    (154, 166, 188), (140, 154, 180), (126, 142, 172),
]

PALETTE_HERO = [
    (0, 0, 0),          # 0 trasparente
    (222, 180, 140),    # 1 incarnato
    (180, 140, 104),    # 2 incarnato in ombra
    (240, 240, 235),    # 3 saio chiaro (Sant'Ubaldo, Sez. 5 GDD)
    (206, 206, 198),
    (168, 168, 160),
    (120, 120, 114),
    (206, 172, 74),     # 7 mitra e pastorale
    (150, 120, 40),
    (70, 60, 40),       # 9 contorno
    (40, 34, 24),
    (110, 72, 40),
    (86, 56, 30),
    (150, 40, 40),
    (100, 26, 26),
    (255, 255, 255),
]


# ----------------------------------------------------------------------------------------------
# BMP indicizzato a 4 bit (stesso formato di make_placeholder_art.py)
# ----------------------------------------------------------------------------------------------

def write_bmp4(path, width, height, pixels, palette):
    assert width % 2 == 0, "larghezza dispari non gestita a 4bpp"
    assert len(palette) <= 16

    pal = list(palette) + [(0, 0, 0)] * (16 - len(palette))
    row_bytes = width // 2
    padding = (4 - row_bytes % 4) % 4

    body = bytearray()
    for y in range(height - 1, -1, -1):          # BMP e' bottom-up
        row = pixels[y]
        for x in range(0, width, 2):
            body.append(((row[x] & 0xF) << 4) | (row[x + 1] & 0xF))
        body.extend(b"\x00" * padding)

    pixel_offset = 14 + 40 + 16 * 4
    header = b"BM" + struct.pack("<IHHI", pixel_offset + len(body), 0, 0, pixel_offset)
    dib = struct.pack("<IiiHHIIiiII", 40, width, height, 1, 4, 0, len(body), 2835, 2835, 16, 0)
    pal_bytes = b"".join(struct.pack("<BBBB", b, g, r, 0) for (r, g, b) in pal)

    with open(path, "wb") as f:
        f.write(header + dib + pal_bytes + bytes(body))


def canvas(w, h, fill=0):
    return [[fill] * w for _ in range(h)]


def count_unique_tiles(pixels, width, height):
    """Tile 8x8 distinti, che e' l'unita' in cui il GBA misura la VRAM."""
    seen = set()
    for ty in range(height // 8):
        for tx in range(width // 8):
            block = tuple(tuple(pixels[ty * 8 + y][tx * 8: tx * 8 + 8]) for y in range(8))
            seen.add(block)
    return len(seen)


def check_and_write(name, width, height, pixels, palette, kind, max_tiles, extra_json=""):
    used = {c for row in pixels for c in row}
    if max(used) > 15:
        sys.exit(f"[piazza-art] {name}: indice colore {max(used)} oltre i 15 ammessi a 4bpp")

    tiles = count_unique_tiles(pixels, width, height)
    if max_tiles is not None and tiles > max_tiles:
        sys.exit(f"[piazza-art] {name}: {tiles} tile unici, oltre la soglia {max_tiles} "
                 f"del budget VRAM (Passo 9)")

    write_bmp4(os.path.join(OUT, name + ".bmp"), width, height, pixels, palette)

    with open(os.path.join(OUT, name + ".json"), "w", encoding="utf-8") as f:
        f.write('{\n    "type": "%s",\n    "bpp_mode": "bpp_4"%s\n}\n' % (kind, extra_json))

    print(f"  {name:18s} {width:4d}x{height:<4d}  {len(used):2d} colori  {tiles:4d} tile unici"
          + (f"  (tetto {max_tiles})" if max_tiles else ""))


# ----------------------------------------------------------------------------------------------
# 1. Suolo della piazza: 512x512, derivato dalla griglia di collisione
# ----------------------------------------------------------------------------------------------

def draw_ground():
    # 512x512 e non 512x320: le dimensioni legali di un BG regolare sono multipli di 256
    # (butano_graphics_tool.py), e un 512x256 farebbe ricomparire in cima la fascia sud della
    # ringhiera per wrap hardware. Le righe oltre y=320 non sono mai inquadrate: la camera e'
    # clampata prima.
    w, h = 512, 512
    px = canvas(w, h, C_VOID)

    for ty in range(PIAZZA_HEIGHT):
        for tx in range(PIAZZA_WIDTH):
            kind = get_tile_type(tx, ty)
            x0, y0 = tx * TILE, ty * TILE

            for y in range(TILE):
                for x in range(TILE):
                    if kind == GROUND:
                        # Lastricato: due tinte a scacchi con la fuga sui bordi della lastra.
                        base = C_STONE if (tx + ty) % 2 == 0 else C_STONE_ALT
                        c = C_JOINT if (x == 0 or y == 0) else base
                    elif kind in (CONSOLI_FACADE, PRETORIO_FACADE):
                        # Pietra calcarea chiara con i corsi orizzontali: e' cosi' che i due
                        # palazzi si staccano dal tessuto edilizio minore, che resta piu' scuro.
                        c = C_WALL if (y % 4 != 3) else C_WALL_DARK
                    elif kind == STAIRS:
                        # Gradini: righe alternate chiare e scure, il segno che si legge a 8 px.
                        c = C_WALL if (y % 2 == 0) else C_RAIL
                    elif kind == WALL:
                        # Muratura a corsi orizzontali, con la base in ombra.
                        c = C_ARCH if (y % 4 == 3 or ty == 18) else C_WALL_DARK
                    elif kind == RAILING:
                        c = C_RAIL if y < 4 else C_WALL_DARK
                    elif kind == DOOR_CONSOLI:
                        c = C_WOOD if 1 <= x <= 6 else C_WALL_DARK
                    elif kind in (EXIT_SAN_MARTINO, EXIT_PORTA_ROMANA):
                        c = C_ARCH if (x + y) % 8 else C_WALL_DARK
                    else:  # FOUNTAIN
                        c = C_WATER if 1 <= x <= 6 and 1 <= y <= 6 else C_RAIL
                    px[y0 + y][x0 + x] = c

    return w, h, px


# ----------------------------------------------------------------------------------------------
# 2. Cielo in parallasse: 256x256
# ----------------------------------------------------------------------------------------------

def draw_sky():
    w, h = 256, 256
    px = canvas(w, h, 1)

    for y in range(h):
        # Gradiente a 8 fasce: una fascia per riga di tile costerebbe 32 tile unici invece di 8.
        band = 1 + min(7, (y * 8) // h)
        for x in range(w):
            px[y][x] = band

    # Qualche banco di nebbia sul Monte Ingino, in tinte chiare: forme larghe e a bordi netti,
    # perche' un dithering costerebbe tile unici senza aggiungere leggibilita' a un segnaposto.
    for (cx, cy, rw, rh) in ((40, 60, 34, 8), (150, 40, 46, 6), (96, 110, 28, 6),
                             (210, 90, 30, 8)):
        for y in range(max(0, cy - rh), min(h, cy + rh)):
            for x in range(max(0, cx - rw), min(w, cx + rw)):
                px[y][x] = 9 + ((y - cy + rh) * 3) // (2 * rh)

    return w, h, px


# ----------------------------------------------------------------------------------------------
# 3. Sprite dell'eroe nell'overworld: 16x16 per fotogramma, 4 direzioni x 4 fotogrammi
# ----------------------------------------------------------------------------------------------

DIRECTIONS = ("giu", "su", "sinistra", "destra")
FRAMES_PER_DIRECTION = 4


def draw_hero_frame(px, y0, direction, frame):
    """Sant'Ubaldo visto dall'alto: saio chiaro, mitra dorata, pastorale."""
    # Oscillazione del passo: fotogrammi 1 e 3 alzano un piede, 0 e 2 sono la posa neutra.
    step = (0, 1, 0, -1)[frame]

    def put(x, y, c):
        if 0 <= x < 16 and 0 <= y < 16:
            px[y0 + y][x] = c

    # Mitra (Sez. 5 GDD: il vescovo la porta anche in marcia)
    for y in range(1, 4):
        for x in range(6, 10):
            put(x, y, C_GOLD if y > 1 else 8)

    # Testa
    for y in range(4, 7):
        for x in range(6, 10):
            put(x, y, 1 if direction != "su" else 2)

    # Saio
    for y in range(7, 13):
        for x in range(5, 11):
            put(x, y, 3 if (y + x) % 5 else 4)

    # Braccia e pastorale, orientati secondo la direzione
    if direction == "sinistra":
        for y in range(6, 12):
            put(4, y, C_GOLD)
        for y in range(8, 11):
            put(10, y, 5)
    elif direction == "destra":
        for y in range(6, 12):
            put(11, y, C_GOLD)
        for y in range(8, 11):
            put(5, y, 5)
    else:
        for y in range(6, 12):
            put(12 if direction == "giu" else 3, y, C_GOLD)

    # Piedi, con l'oscillazione del passo
    for x in range(5, 8):
        put(x, 13 + max(0, step), 9)
    for x in range(9, 12):
        put(x, 13 + max(0, -step), 9)

    # Contorno inferiore, perche' la silhouette resti leggibile sul lastricato chiaro
    for x in range(5, 11):
        put(x, 14, 10)


def draw_hero():
    w = 16
    h = 16 * len(DIRECTIONS) * FRAMES_PER_DIRECTION      # 16x256
    px = canvas(w, h, 0)

    index = 0
    for direction in DIRECTIONS:
        for frame in range(FRAMES_PER_DIRECTION):
            draw_hero_frame(px, index * 16, direction, frame)
            index += 1

    return w, h, px


def main():
    os.makedirs(OUT, exist_ok=True)
    print("[piazza-art] generazione degli asset segnaposto di Piazza Grande")

    w, h, px = draw_ground()
    check_and_write("piazza_ground", w, h, px, PALETTE_GROUND, "regular_bg", MAX_TILES_GROUND)

    w, h, px = draw_sky()
    check_and_write("piazza_sky", w, h, px, PALETTE_SKY, "regular_bg", MAX_TILES_SKY)

    w, h, px = draw_hero()
    # `height` NON e' facoltativo: senza, un foglio 16x256 viene letto come UN unico sprite
    # 16x256, che non e' una misura OBJ esistente sul GBA, e la build muore con
    # "Invalid sprite height". Emesso qui insieme al .bmp, mai scritto a mano.
    check_and_write("overworld_ubaldo", w, h, px, PALETTE_HERO, "sprite", None,
                    ',\n    "height": 16')

    print("[piazza-art] fatto. NON e' arte definitiva: sostituire i .bmp mantenendo misure e "
          "16 colori, senza toccare il C++.")


if __name__ == "__main__":
    main()
