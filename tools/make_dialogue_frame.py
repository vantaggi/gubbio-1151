#!/usr/bin/env python3
"""
Cornice della finestra di dialogo (Sez. 25 GDD) come background regolare per BG0.

    python tools/make_dialogue_frame.py

Produce `graphics/dialogue_frame.{bmp,json}`: un BG 256x256 di cui e' dipinta la sola fascia
bassa, y 108-159, che e' dove il GDD colloca l'interfaccia inferiore.

PERCHE' UN BG E NON DEGLI SPRITE. Il testo su GBA e' fatto di sprite (OAM) e il tetto vero non
sono i tile ma le 128 allocazioni distinte di `BN_CFG_SPRITE_TILES_MAX_ITEMS`: una cornice fatta
di sprite ne mangerebbe una decina per non disegnare nulla che cambi mai. Su BG0 costa un blocco
di mappa e pochi tile ripetuti, e lascia l'intero budget OAM al testo.

Il fondo e' un blocco pieno di colore scuro: la "semitrasparenza" della Sez. 25 sul GBA e'
alpha blending (registri BLDCNT/BLDALPHA), che si attiva a runtime sul layer e non si dipinge
nell'immagine.
"""

import os
import struct

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "graphics")

W = H = 256
BOX_TOP = 108          # prima riga della cornice
BOX_BOTTOM = 159       # ultima riga visibile dello schermo
BOX_LEFT = 4
BOX_RIGHT = 235        # 240 - 5: lo schermo e' largo 240 anche se il BG e' 256

C_VUOTO = 0            # trasparente: si vede la mappa sotto
C_FONDO = 1
C_BORDO = 2
C_LUCE = 3             # lumeggiatura interna del bordo
C_FORMELLA = 4         # motivo geometrico delle formelle di Palazzo dei Consoli

PALETTE = [
    (0, 0, 0),          # 0 trasparente
    (20, 16, 28),       # 1 fondo scuro del box
    (206, 172, 74),     # 2 bordo dorato
    (128, 104, 44),     # 3 ombra del bordo
    (94, 76, 36),       # 4 formelle
    (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0),
    (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0),
]


def write_bmp4(path, width, height, pixels, palette):
    row_bytes = width // 2
    padding = (4 - row_bytes % 4) % 4
    body = bytearray()
    for y in range(height - 1, -1, -1):
        row = pixels[y]
        for x in range(0, width, 2):
            body.append(((row[x] & 0xF) << 4) | (row[x + 1] & 0xF))
        body.extend(b"\x00" * padding)

    off = 14 + 40 + 16 * 4
    header = b"BM" + struct.pack("<IHHI", off + len(body), 0, 0, off)
    dib = struct.pack("<IiiHHIIiiII", 40, width, height, 1, 4, 0, len(body), 2835, 2835, 16, 0)
    pal = b"".join(struct.pack("<BBBB", b, g, r, 0) for (r, g, b) in palette)
    open(path, "wb").write(header + dib + pal + bytes(body))


def main():
    px = [[C_VUOTO] * W for _ in range(H)]

    for y in range(BOX_TOP, BOX_BOTTOM + 1):
        for x in range(BOX_LEFT, BOX_RIGHT + 1):
            sul_bordo_v = y in (BOX_TOP, BOX_TOP + 1, BOX_BOTTOM - 1, BOX_BOTTOM)
            sul_bordo_o = x in (BOX_LEFT, BOX_LEFT + 1, BOX_RIGHT - 1, BOX_RIGHT)

            if sul_bordo_v or sul_bordo_o:
                px[y][x] = C_BORDO
            elif y in (BOX_TOP + 2, BOX_BOTTOM - 2) or x in (BOX_LEFT + 2, BOX_RIGHT - 2):
                px[y][x] = C_LUCE
            else:
                px[y][x] = C_FONDO

    # Formelle di Palazzo dei Consoli: rombi regolari lungo il bordo superiore. Il motivo ha
    # passo 16 px, cioe' due tile: cosi' la riga di tile si ripete e costa 1 tile unico, non 15.
    for cx in range(BOX_LEFT + 8, BOX_RIGHT - 6, 16):
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                if abs(dx) + abs(dy) <= 3 and 0 <= cx + dx < W:
                    px[BOX_TOP + 4 + dy][cx + dx] = C_FORMELLA if abs(dx) + abs(dy) == 3 else C_LUCE

    write_bmp4(os.path.join(OUT, "dialogue_frame.bmp"), W, H, px, PALETTE)
    with open(os.path.join(OUT, "dialogue_frame.json"), "w", encoding="utf-8") as f:
        f.write('{\n    "type": "regular_bg",\n    "bpp_mode": "bpp_4"\n}\n')

    unici = len({tuple(tuple(px[ty * 8 + y][tx * 8: tx * 8 + 8]) for y in range(8))
                 for ty in range(H // 8) for tx in range(W // 8)})
    colori = len({c for r in px for c in r})
    print(f"[cornice] dialogue_frame  {W}x{H}  {colori} colori  {unici} tile unici")
    if unici > 64:
        raise SystemExit(f"[cornice] {unici} tile unici: oltre il budget di 64 per l'interfaccia")


if __name__ == "__main__":
    main()
