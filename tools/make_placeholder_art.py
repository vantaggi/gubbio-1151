#!/usr/bin/env python3
"""
Generatore di GRAFICA SEGNAPOSTO per Gubbio 1151.

Produce i .bmp a 4bpp (16 colori, indice 0 trasparente) e i .json che Butano si aspetta in
graphics/. Le dimensioni rispettano la Sezione 23A del GDD; le palette seguono la Sezione 14C.

NON e' arte definitiva: sono silhouette leggibili nelle dimensioni corrette, pensate per
sbloccare il rendering. Sostituire un personaggio significa sovrascrivere il suo .bmp con
l'arte vera, senza toccare una riga di C++.

    python tools/make_placeholder_art.py
"""

import os
import struct

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "graphics")


# ----------------------------------------------------------------------------------------------
# Scrittura BMP indicizzato a 4 bit
# ----------------------------------------------------------------------------------------------

def write_bmp4(path, width, height, pixels, palette):
    """pixels: lista di righe (dall'alto), ogni riga lista di indici 0-15."""
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


def write_json(path, payload):
    with open(path, "w", encoding="utf-8") as f:
        f.write(payload)


def canvas(w, h, fill=0):
    return [[fill] * w for _ in range(h)]


def rect(px, x0, y0, x1, y1, c):
    for y in range(max(0, y0), min(len(px), y1 + 1)):
        for x in range(max(0, x0), min(len(px[0]), x1 + 1)):
            px[y][x] = c


def disc(px, cx, cy, r, c):
    for y in range(max(0, cy - r), min(len(px), cy + r + 1)):
        for x in range(max(0, cx - r), min(len(px[0]), cx + r + 1)):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                px[y][x] = c


def tri_up(px, cx, base_y, half, height, c):
    """Triangolo isoscele con la punta in alto: la mitra di Sant'Ubaldo."""
    for i in range(height):
        y = base_y - i
        w = max(0, int(half * (1 - i / height)))
        rect(px, cx - w, y, cx + w, y, c)


# ----------------------------------------------------------------------------------------------
# Personaggi (Sezione 23A GDD per le misure, Sezione 14C per i colori)
# ----------------------------------------------------------------------------------------------

def make_ubaldo():
    """16x32 - mitra, pastorale, bianco liturgico e oro."""
    P = [(0, 0, 0), (232, 226, 205), (198, 158, 58), (120, 96, 32),
         (245, 240, 228), (150, 140, 118), (90, 80, 62), (60, 52, 40)]
    px = canvas(16, 32)
    rect(px, 5, 14, 10, 30, 1)          # tonaca
    rect(px, 5, 14, 6, 30, 5)           # ombra laterale
    rect(px, 4, 16, 11, 18, 1)          # spalle
    rect(px, 7, 18, 8, 30, 2)           # stola dorata
    disc(px, 7, 11, 3, 4)               # volto
    rect(px, 5, 13, 9, 14, 6)           # collo in ombra
    tri_up(px, 7, 8, 3, 7, 2)           # mitra
    rect(px, 6, 8, 8, 8, 1)             # bordo della mitra
    rect(px, 13, 8, 13, 31, 3)          # pastorale
    rect(px, 12, 6, 14, 8, 2)           # riccio del pastorale
    rect(px, 5, 31, 10, 31, 7)          # base
    return px, P, 16, 32


def make_giorgio():
    """32x32 - lancia, scudo, azzurro cavaliere e acciaio."""
    P = [(0, 0, 0), (74, 122, 190), (44, 78, 132), (176, 186, 200),
         (232, 226, 205), (198, 158, 58), (168, 52, 40), (52, 58, 72)]
    px = canvas(32, 32)
    rect(px, 11, 13, 21, 30, 1)         # corazza
    rect(px, 11, 13, 13, 30, 2)         # ombra
    rect(px, 12, 20, 20, 22, 6)         # fascia rossa
    disc(px, 16, 9, 4, 4)               # volto
    rect(px, 12, 4, 20, 7, 3)           # elmo
    rect(px, 15, 6, 17, 9, 3)           # nasale
    disc(px, 25, 19, 6, 3)              # scudo
    disc(px, 25, 19, 4, 1)
    disc(px, 25, 19, 2, 5)              # borchia
    rect(px, 5, 2, 6, 31, 3)            # lancia
    rect(px, 4, 0, 7, 3, 5)             # punta dorata
    rect(px, 11, 31, 21, 31, 7)
    return px, P, 32, 32


def make_antonio():
    """16x32 - saio nero, bastone a tau, fiamma."""
    P = [(0, 0, 0), (46, 42, 40), (28, 26, 26), (222, 118, 40),
         (240, 190, 90), (196, 176, 150), (96, 72, 48), (150, 60, 24)]
    px = canvas(16, 32)
    rect(px, 4, 11, 11, 30, 1)          # saio
    rect(px, 4, 11, 5, 30, 2)
    rect(px, 6, 8, 10, 13, 2)           # cappuccio
    disc(px, 8, 11, 2, 5)               # volto in ombra
    rect(px, 2, 8, 3, 31, 6)            # bastone
    rect(px, 0, 8, 5, 9, 6)             # traversa del tau
    disc(px, 2, 5, 2, 3)                # fiamma
    disc(px, 2, 4, 1, 4)
    rect(px, 6, 24, 9, 26, 7)           # cintura
    rect(px, 4, 31, 11, 31, 2)
    return px, P, 16, 32


def make_fante():
    """32x32 - fante di Perugia, rosso e lancia corta."""
    P = [(0, 0, 0), (150, 44, 40), (104, 30, 28), (160, 168, 178),
         (206, 178, 150), (70, 62, 58), (110, 88, 54), (40, 36, 34)]
    px = canvas(32, 32)
    rect(px, 11, 13, 21, 30, 1)
    rect(px, 19, 13, 21, 30, 2)
    disc(px, 16, 9, 4, 4)
    rect(px, 12, 4, 20, 8, 3)           # elmo
    rect(px, 26, 3, 27, 31, 6)          # asta
    rect(px, 25, 0, 28, 4, 3)           # punta
    rect(px, 12, 19, 20, 21, 5)         # cintura
    rect(px, 11, 31, 21, 31, 7)
    return px, P, 32, 32


def make_balestriere():
    """32x32 - balestriere pesante, cuoio e acciaio."""
    P = [(0, 0, 0), (96, 84, 62), (68, 58, 44), (170, 178, 188),
         (206, 178, 150), (58, 52, 46), (128, 108, 72), (36, 34, 32)]
    px = canvas(32, 32)
    rect(px, 10, 13, 20, 30, 1)
    rect(px, 18, 13, 20, 30, 2)
    disc(px, 15, 9, 4, 4)
    rect(px, 11, 4, 19, 8, 3)
    rect(px, 22, 14, 30, 16, 6)         # fusto della balestra
    rect(px, 25, 10, 26, 21, 3)         # arco
    rect(px, 24, 11, 27, 12, 3)
    rect(px, 10, 31, 20, 31, 7)
    return px, P, 32, 32


def make_corrado():
    """64x64 - Corrado di Spoleto: il colosso delle forge (Sez. 14B.3: boss 64x64)."""
    P = [(0, 0, 0), (86, 92, 104), (56, 62, 74), (150, 158, 172),
         (198, 96, 40), (232, 150, 60), (38, 42, 52), (120, 84, 44)]
    px = canvas(64, 64)
    rect(px, 18, 22, 44, 60, 1)         # corazza massiccia
    rect(px, 18, 22, 24, 60, 2)
    rect(px, 24, 34, 38, 44, 4)         # fornace pettorale
    rect(px, 27, 37, 35, 41, 5)
    disc(px, 31, 16, 8, 3)              # elmo
    rect(px, 21, 8, 41, 20, 1)
    rect(px, 21, 8, 41, 11, 2)
    rect(px, 25, 16, 37, 19, 6)         # feritoia
    rect(px, 50, 10, 55, 58, 7)         # manico del martello
    rect(px, 44, 4, 62, 20, 1)          # testa del martello
    rect(px, 44, 4, 62, 8, 3)
    rect(px, 18, 61, 44, 63, 6)
    return px, P, 64, 64


# ----------------------------------------------------------------------------------------------
# Fondale d'assedio + pannello HUD (Sezione 14B.3 GDD)
# ----------------------------------------------------------------------------------------------

def make_battle_bg():
    """256x256; l'area visibile e' 240x160. Righe 0-111 scena, 112-159 pannello HUD."""
    P = [
        (18, 20, 34),    # 0 cielo alto
        (30, 32, 52),    # 1 cielo medio
        (48, 46, 68),    # 2 cielo basso / foschia
        (34, 32, 46),    # 3 monte lontano
        (24, 24, 36),    # 4 monte vicino
        (66, 62, 80),    # 5 nebbia
        (44, 40, 38),    # 6 terreno
        (58, 52, 46),    # 7 terreno chiaro
        (14, 15, 12),    # 8 pannello HUD
        (26, 28, 22),    # 9 pannello HUD chiaro
        (138, 110, 44),  # 10 bordo bronzo
        (90, 72, 30),    # 11 bordo bronzo scuro
        (10, 11, 9),     # 12 nero pannello
        (72, 78, 66),    # 13 divisorio
        (0, 0, 0), (0, 0, 0),
    ]
    W, H = 256, 256
    px = canvas(W, H, 0)

    for y in range(0, 112):                       # cielo a fasce
        c = 0 if y < 26 else 1 if y < 58 else 2
        rect(px, 0, y, W - 1, y, c)

    for x in range(W):                            # profilo del Monte Ingino
        h = 74 - int(26 * abs(((x + 40) % 200) / 100.0 - 1.0) ** 1.4)
        rect(px, x, h, x, 99, 3)
        h2 = 86 - int(16 * abs(((x + 130) % 150) / 75.0 - 1.0) ** 1.2)
        rect(px, x, h2, x, 99, 4)

    for y in range(86, 100):                      # banco di nebbia, a chiazze
        for x in range(W):
            n = (x * 7 + y * 13) % 23
            if n < 6 - abs(y - 93):
                px[y][x] = 5

    rect(px, 0, 100, W - 1, 111, 6)               # terreno
    for x in range(0, W, 7):
        rect(px, x, 104, x + 2, 105, 7)

    rect(px, 0, 112, W - 1, 159, 8)               # pannello HUD
    rect(px, 0, 112, W - 1, 113, 10)              # bordo bronzo superiore
    rect(px, 0, 114, W - 1, 114, 11)
    rect(px, 2, 117, 78, 157, 12)                 # riquadro menu comandi (80px)
    rect(px, 82, 117, 253, 157, 12)               # riquadro stato party
    rect(px, 80, 117, 80, 157, 13)                # divisorio
    return px, P, W, H


def make_bar():
    """32x8, 34 fotogrammi: 0-16 barra HP (cremisi), 17-33 barra Fervore (oro).

    Due set distinti invece dello scaling affine, che consumerebbe gli slot affine del GBA.
    """
    P = [(0, 0, 0), (34, 32, 28), (70, 74, 64), (176, 52, 44),
         (226, 96, 76), (206, 160, 52), (244, 214, 120), (12, 13, 11)]
    W, FRAME_H, HALF = 32, 8, 17
    px = canvas(W, FRAME_H * HALF * 2)
    for setno, (body, light) in enumerate(((3, 4), (5, 6))):
        for f in range(HALF):
            top = (setno * HALF + f) * FRAME_H
            rect(px, 0, top, W - 1, top + FRAME_H - 1, 1)          # fondo
            rect(px, 0, top, W - 1, top, 7)                        # cornice
            rect(px, 0, top + FRAME_H - 1, W - 1, top + FRAME_H - 1, 7)
            filled = (W - 2) * f // (HALF - 1)
            if filled:
                rect(px, 1, top + 1, filled, top + FRAME_H - 2, body)
                rect(px, 1, top + 1, filled, top + 2, light)       # lumeggiatura
    return px, P, W, FRAME_H * HALF * 2


def make_cursor():
    """16x16 - cursore di selezione bersaglio: cuneo bronzeo."""
    P = [(0, 0, 0), (222, 178, 72), (150, 112, 34), (250, 228, 160)]
    px = canvas(16, 16)
    for i in range(8):
        rect(px, 4 + i, 3 + i, 11 - i, 3 + i, 1)
    for i in range(8):
        rect(px, 4 + i, 3 + i, 4 + i, 3 + i, 3)
        rect(px, 11 - i, 3 + i, 11 - i, 3 + i, 2)
    return px, P, 16, 16


# ----------------------------------------------------------------------------------------------

def make_timeline_icons():
    """16x16 x6 - gettoni della timeline (Sez. 20A GDD): 0-2 i Ceri, 3-5 i nemici."""
    P = [(0, 0, 0), (18, 20, 16), (232, 226, 205), (198, 158, 58),
         (74, 122, 190), (222, 118, 40), (150, 44, 40), (96, 84, 62),
         (150, 158, 172), (110, 116, 128)]
    faces = [(2, 3), (4, 8), (1, 5), (6, 2), (7, 8), (8, 5)]
    px = canvas(16, 16 * len(faces))
    for i, (body, mark) in enumerate(faces):
        top = i * 16
        rect(px, 1, top + 1, 14, top + 14, 1)          # cornice scura
        rect(px, 2, top + 2, 13, top + 13, body)
        disc(px, 7, top + 7, 3, mark)                  # contrassegno
        rect(px, 2, top + 2, 13, top + 2, mark)        # lumeggiatura superiore
    return px, P, 16, 16 * len(faces)


SPRITES = [
    ("timeline_icons", make_timeline_icons, 16),
    ("ubaldo", make_ubaldo, None),
    ("giorgio", make_giorgio, None),
    ("antonio", make_antonio, None),
    ("enemy_fante", make_fante, None),
    ("enemy_balestriere", make_balestriere, None),
    ("enemy_corrado", make_corrado, None),
    ("hud_bar", make_bar, 8),          # altezza del singolo fotogramma
    ("target_cursor", make_cursor, None),
]


def main():
    out = os.path.normpath(OUT)
    os.makedirs(out, exist_ok=True)

    for name, fn, frame_h in SPRITES:
        px, pal, w, h = fn()
        write_bmp4(os.path.join(out, name + ".bmp"), w, h, px, pal)
        # `bpp_mode` esplicito, sempre: senza, butano_graphics_tool.py promuove in silenzio a
        # 8bpp ogni BMP oltre i 16 colori, raddoppiando la VRAM per tile e — per un background —
        # occupando tutti e 16 i banchi di palette. Preteso da tests/test_assets.py.
        meta = '{\n    "type": "sprite",\n    "bpp_mode": "bpp_4"'
        if frame_h:
            meta += ',\n    "height": %d' % frame_h
        meta += '\n}\n'
        write_json(os.path.join(out, name + ".json"), meta)
        print("  sprite  %-20s %dx%d" % (name, w, h))

    px, pal, w, h = make_battle_bg()
    write_bmp4(os.path.join(out, "battle_bg.bmp"), w, h, px, pal)
    write_json(os.path.join(out, "battle_bg.json"),
               '{\n    "type": "regular_bg",\n    "bpp_mode": "bpp_4"\n}\n')
    print("  bg      %-20s %dx%d" % ("battle_bg", w, h))

    print("\nGrafica segnaposto generata in %s" % out)


if __name__ == "__main__":
    main()
