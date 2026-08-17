#!/usr/bin/env python3
"""
Anteprima di PIAZZA GRANDE fuori dall'emulatore.

Compone i 240x160 che la GBA mostrerebbe con la camera in una data posizione, sovrapponendo
al suolo il riquadro di collisione del giocatore. Serve a iterare su layout e arte senza
avviare mGBA, come `preview_battle_screen.py` fa per la battaglia.

    python tools/preview_piazza.py                # camera sullo spawn di default
    python tools/preview_piazza.py 44 172         # camera su una posizione in pixel

ATTENZIONE, e' un'ANTEPRIMA e non una cattura: ricompone gli stessi dati che la ROM usa
(`piazza_ground.bmp` e il mirror di `get_tile_type`), ma non passa dall'hardware. Non mostra
il parallasse del cielo, che dipende dalla camera a runtime.
"""

import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GRAPHICS = os.path.join(HERE, "..", "graphics")

sys.path.insert(0, HERE)
from make_piazza_art import (  # noqa: E402  (import dopo sys.path, voluto)
    PIAZZA_WIDTH, PIAZZA_HEIGHT, TILE, get_tile_type, write_bmp4, canvas, PALETTE_GROUND)

SCREEN_W, SCREEN_H = 240, 160
CAMERA_MARGIN_X, CAMERA_MARGIN_Y = 120, 80

# Devono restare uguali a include/overworld_player.h.
HITBOX_HALF_WIDTH = 6
HITBOX_HEIGHT = 8


def read_bmp4(path):
    with open(path, "rb") as f:
        data = f.read()

    pixel_offset = struct.unpack_from("<I", data, 10)[0]
    width, height = struct.unpack_from("<ii", data, 18)
    bpp = struct.unpack_from("<H", data, 28)[0]
    assert bpp == 4, f"{path}: atteso 4bpp, trovato {bpp}"

    row_bytes = width // 2
    padding = (4 - row_bytes % 4) % 4
    px = []
    for y in range(height - 1, -1, -1):          # BMP e' bottom-up
        start = pixel_offset + (height - 1 - y) * (row_bytes + padding)
        riga = []
        for b in data[start:start + row_bytes]:
            riga.append(b >> 4)
            riga.append(b & 0xF)
        px.append(riga)
    px.reverse()
    return width, height, px


def clamp(v, lo, hi):
    return lo if v < lo else (hi if v > hi else v)


def main():
    if len(sys.argv) >= 3:
        px_x, py_y = int(sys.argv[1]), int(sys.argv[2])
    else:
        px_x, py_y = 32 * TILE + TILE // 2, 30 * TILE + TILE // 2

    ground_path = os.path.join(GRAPHICS, "piazza_ground.bmp")
    if not os.path.exists(ground_path):
        sys.exit("[preview] manca graphics/piazza_ground.bmp: eseguire prima make_piazza_art.py")

    _, _, ground = read_bmp4(ground_path)

    # Stesso clamping di ExplorationScene::_update_camera.
    cam_x = clamp(px_x, CAMERA_MARGIN_X, PIAZZA_WIDTH * TILE - CAMERA_MARGIN_X)
    cam_y = clamp(py_y, CAMERA_MARGIN_Y, PIAZZA_HEIGHT * TILE - CAMERA_MARGIN_Y)
    origin_x = cam_x - SCREEN_W // 2
    origin_y = cam_y - SCREEN_H // 2

    out = canvas(SCREEN_W, SCREEN_H, 0)
    for y in range(SCREEN_H):
        for x in range(SCREEN_W):
            sx, sy = origin_x + x, origin_y + y
            if 0 <= sx < PIAZZA_WIDTH * TILE and 0 <= sy < PIAZZA_HEIGHT * TILE:
                out[y][x] = ground[sy][sx]

    # Riquadro di collisione del giocatore, in rosso vivo (indice 11 della palette del suolo).
    for x in range(px_x - HITBOX_HALF_WIDTH, px_x + HITBOX_HALF_WIDTH):
        for y in (py_y - HITBOX_HEIGHT + 1, py_y):
            sx, sy = x - origin_x, y - origin_y
            if 0 <= sx < SCREEN_W and 0 <= sy < SCREEN_H:
                out[sy][sx] = 11

    dest = os.path.join(HERE, "..", "preview_piazza.bmp")
    write_bmp4(dest, SCREEN_W, SCREEN_H, out, PALETTE_GROUND)

    tile = get_tile_type(px_x // TILE, py_y // TILE)
    print(f"[preview] giocatore ({px_x},{py_y}) su tile {px_x // TILE},{py_y // TILE} "
          f"di tipo {tile}")
    print(f"[preview] camera ({cam_x},{cam_y}) — scritto {os.path.normpath(dest)}")


if __name__ == "__main__":
    main()
