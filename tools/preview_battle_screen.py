#!/usr/bin/env python3
"""
Anteprima della schermata di combattimento, composta fuori dall'emulatore.

Compone i 240x160 pixel a partire dagli stessi .bmp di graphics/ e dalle stesse coordinate
usate da src/battle_hud.cpp, con il font 8x8 vero di Butano. Serve a iterare su layout e
grafica senza ricompilare la ROM.

    python tools/preview_battle_screen.py [-o preview.png] [--scale 3]

ATTENZIONE: le costanti di posizione qui sotto RISPECCHIANO quelle di src/battle_hud.cpp.
Se cambiano di la', vanno aggiornate anche qui: e' un'anteprima, non la fonte di verita'.
"""

import argparse
import os
import re

from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
GFX = os.path.join(ROOT, "graphics")
BUTANO_COMMON = os.path.normpath(os.path.join(ROOT, "..", "butano", "common"))

SCREEN_W, SCREEN_H = 240, 160

# --- mirror di src/battle_hud.cpp ---
HERO_FILES = ["ubaldo", "giorgio", "antonio"]
HERO_X = [196, 162, 218]
HERO_Y = [86, 94, 94]
ENEMY_X = [60, 94, 44, 78, 112, 28]
ENEMY_Y = [96, 96, 78, 78, 78, 96]
MENU_X, MENU_Y, MENU_LINE = 8, 118, 10
STATUS_X, STATUS_Y, STATUS_LINE = 84, 118, 12
NUMBERS_X = 133
SHORT = ["Ubaldo", "Giorgio", "Antonio"]
BAR_HP_X, BAR_FER_X = 157, 193
BAR_FRAMES = 17
BAR_FERVOR_OFFSET = 17
TIMELINE_X, TIMELINE_Y, TIMELINE_STEP = 228, 12, 15
# Ordine previsto del round 1: Giorgio 42, Antonio 38, Balestriere 34, Ubaldo 30, Fanti 26.
TIMELINE_ORDER = [1, 2, 4, 0, 3, 3]

# Stato di esempio: il primo round dell'incontro Pattuglia Perugina.
PARTY = [
    ("Sant'Ubaldo", 240, 240, 144, 180),
    ("San Giorgio", 380, 380, 54, 120),
    ("Sant'Antonio", 210, 210, 42, 210),
]
ENEMIES = ["enemy_fante", "enemy_fante", "enemy_balestriere"]
ACTIVE_HERO = 1          # San Giorgio sceglie per primo (Sez. 20B GDD)
SELECTED_COMMAND = 0     # Attacca
TARGET_SLOT = 0
COMMANDS = ["Attacca", "Abilita", "Oggetti", "Fuga"]


def load_rgba(name, transparent_index_0=True):
    img = Image.open(os.path.join(GFX, name + ".bmp"))
    pal = img.convert("P").getpalette()
    rgba = Image.new("RGBA", img.size, (0, 0, 0, 0))
    px, out = img.load(), rgba.load()
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            i = px[x, y]
            if transparent_index_0 and i == 0:
                continue
            out[x, y] = (pal[i * 3], pal[i * 3 + 1], pal[i * 3 + 2], 255)
    return rgba


def load_font():
    """Font sprite 8x8 di Butano: celle impilate da ASCII 32, larghezze nell'header."""
    header = os.path.join(BUTANO_COMMON, "include", "common_variable_8x8_sprite_font.h")
    with open(header, encoding="utf-8") as f:
        text = f.read()
    block = text.split("variable_8x8_sprite_font_character_widths[] = {")[1].split("};")[0]
    widths = [int(m) for m in re.findall(r"^\s*(\d+),", block, re.M)]
    sheet = Image.open(os.path.join(BUTANO_COMMON, "graphics",
                                    "common_variable_8x8_font.bmp")).convert("P")
    return sheet, widths


def draw_text(dst, sheet, widths, x, y, text, color=(236, 232, 216)):
    pal = sheet.getpalette()
    src = sheet.load()
    for ch in text:
        code = ord(ch)
        width_idx = code - 32
        if width_idx < 0 or width_idx >= len(widths):
            width_idx = 0
        # Il foglio del font NON contiene la cella dello spazio (e' vuota): le celle partono
        # dal codice 33. Senza questo scarto ogni lettera scivola di uno.
        if code == 32:
            x += widths[0]
            continue
        idx = code - 33
        top = idx * 8
        for cy in range(8):
            for cx in range(8):
                if src[cx, top + cy] != 0:
                    px, py = x + cx, y + cy
                    if 0 <= px < SCREEN_W and 0 <= py < SCREEN_H:
                        dst.putpixel((px, py), color + (255,))
        x += widths[width_idx]
    return x


def paste_centered(dst, sprite, cx, cy):
    dst.alpha_composite(sprite, (cx - sprite.size[0] // 2, cy - sprite.size[1] // 2))


def bar_frame(current, maximum):
    if maximum <= 0:
        return 0
    return max(0, min(BAR_FRAMES - 1, current * (BAR_FRAMES - 1) // maximum))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", default=os.path.join(ROOT, "preview_battle.png"))
    ap.add_argument("--scale", type=int, default=3)
    args = ap.parse_args()

    bg = load_rgba("battle_bg", transparent_index_0=False).crop((0, 0, SCREEN_W, SCREEN_H))
    screen = Image.new("RGBA", (SCREEN_W, SCREEN_H))
    screen.alpha_composite(bg)

    for slot, name in enumerate(ENEMIES):
        paste_centered(screen, load_rgba(name), ENEMY_X[slot], ENEMY_Y[slot])

    for i, name in enumerate(HERO_FILES):
        paste_centered(screen, load_rgba(name), HERO_X[i], HERO_Y[i])

    cursor = load_rgba("target_cursor")
    paste_centered(screen, cursor, ENEMY_X[TARGET_SLOT], ENEMY_Y[TARGET_SLOT] - 28)

    bars = load_rgba("hud_bar")
    for hero in range(3):
        _, hp, max_hp, fer, max_fer = PARTY[hero]
        y = STATUS_Y + hero * STATUS_LINE + 3
        for bx, frame in ((BAR_HP_X, bar_frame(hp, max_hp)),
                          (BAR_FER_X, BAR_FERVOR_OFFSET + bar_frame(fer, max_fer))):
            cell = bars.crop((0, frame * 8, 32, frame * 8 + 8))
            paste_centered(screen, cell, bx + 16, y)

    icons = load_rgba("timeline_icons")
    for i, frame in enumerate(TIMELINE_ORDER):
        cell = icons.crop((0, frame * 16, 16, frame * 16 + 16))
        paste_centered(screen, cell, TIMELINE_X, TIMELINE_Y + i * TIMELINE_STEP)

    sheet, widths = load_font()
    for i, label in enumerate(COMMANDS):
        prefix = "> " if i == SELECTED_COMMAND else "  "
        draw_text(screen, sheet, widths, MENU_X, MENU_Y + i * MENU_LINE, prefix + label)

    for hero, (name, hp, max_hp, fer, max_fer) in enumerate(PARTY):
        mark = ">" if hero == ACTIVE_HERO else " "
        draw_text(screen, sheet, widths, STATUS_X, STATUS_Y + hero * STATUS_LINE, mark + SHORT[hero])
        draw_text(screen, sheet, widths, NUMBERS_X, STATUS_Y + hero * STATUS_LINE,
                  "%d" % hp)

    out = screen.convert("RGB")
    if args.scale > 1:
        out = out.resize((SCREEN_W * args.scale, SCREEN_H * args.scale), Image.NEAREST)
    out.save(args.out)
    print("Anteprima salvata in %s (%dx%d)" % (args.out, out.size[0], out.size[1]))


if __name__ == "__main__":
    main()
