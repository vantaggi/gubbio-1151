"""Tavola 240x160 (x3) dei drappi delle undici citta' della coalizione, dalla palette bloccata.
Dati in coalizione.json. Richiede Pillow e stile_dati accanto.

    python tavola_coalizione.py tavola_coalizione.png
"""
import json
import os
import sys

from PIL import Image

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(QUI, "..", "stile_dati", "stile"))
import stile as S  # noqa: E402

P = S.carica("palette")
F = S.carica("font")
D = json.load(open(os.path.join(QUI, "coalizione.json"), encoding="utf-8"))


def c(rif):
    return S.rgb_di(S.colore(P, list(rif)))


def tono(rif, d):
    n = len(next(r for r in P["rampe"] if r["nome"] == rif[0])["giorno"])
    return c([rif[0], max(0, min(n - 1, rif[1] + d))])


NERO = c(["legno e cuoio", 0])
img = Image.new("RGB", (240, 160), c(["pietra calcarea", 5]))
px = img.putpixel

# '#' = colore della figura, 'o' = secondo colore
FIGURE = {
    "grifo": ["..##....", ".###.o..", "..####..", ".#####.#", "..#####.", "..####..", ".##..#..", ".#...##."],
    "croce": ["...##...", "...##...", "########", "########", "...##...", "...##...", "...##...", "...##..."],
    "capriolo": [".o....o.", ".o....o.", "...##...", "..####..", ".##..##.", "##....##", "...o....", "...o...."],
    "giglio": ["...#....", "..###...", "#.###.#.", "##.#.##.", ".#####..", "...#....", "..###...", "...#...."],
    "aquila": ["...##...", "#..##..#", "##.##.##", "########", ".######.", "...##...", "..####..", "..#..#.."],
    "torre": ["#.#.#.#.", "#######.", "#######.", "##.#.##.", "#######.", "###.###.", "##...##.", "##...##."],
    "leone": ["..##....", ".###....", "..##.##.", ".#####..", "..####..", ".#####..", ".#...#..", "##...##."],
}


def testo(x, y, t, col):
    for ch in S.normalizza(F, t):
        g = F["glifi"][ch]
        for r, riga in enumerate(g):
            for k, v in enumerate(riga):
                if v == "#":
                    px((x + k, y + r), col)
        x += len(g[0]) + F["spaziatura"]


def centrato(cx, y, t, col):
    testo(cx - S.larghezza_testo(F, S.normalizza(F, t)) // 2, y, t, col)


def drappo(x0, y0, g, w=14, h=26):
    def dentro(x, y):
        if not (0 <= x < w and 0 <= y < h):
            return False
        if y >= h - 4:
            return abs(x - (w - 1) / 2) > (y - (h - 5)) * (w / 8)
        return True
    for y in range(h):
        for x in range(w):
            if not dentro(x, y):
                continue
            campo = g["campo_destro"] if g.get("campo_destro") and x >= w // 2 else g["campo"]
            if g.get("bande") and (x - y) % 8 in (0, 1, 2):
                campo = g["bande"]
            col = tono(campo, 1) if x < 2 else tono(campo, -1) if x >= w - 2 else c(campo)
            px((x0 + x, y0 + y), col)
    for y in range(-1, h + 1):
        for x in range(-1, w + 1):
            if not dentro(x, y) and any(dentro(x + a, y + b) for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px((x0 + x, y0 + y), NERO)
    for xx in range(x0 - 2, x0 + w + 2):
        for yy in (y0 - 2, y0 - 1):
            px((xx, yy), c(["legno e cuoio", 2]))
    if g.get("figura"):
        fx = x0 + 3 if not g.get("campo_destro") else x0 + 1
        for r, riga in enumerate(FIGURE[g["figura"]]):
            for k, v in enumerate(riga):
                if v == "#":
                    px((fx + k, y0 + 6 + r), c(g["figura_colore"]))
                elif v == "o":
                    px((fx + k, y0 + 6 + r), c(g.get("secondo_colore", g["figura_colore"])))


centrato(120, 2, "La coalizione delle undici citta'", NERO)
for i, cit in enumerate(D["citta"]):
    riga, col = divmod(i, 6)
    x = 12 + col * 38 + (19 if riga else 0)
    y = 22 + riga * 64
    drappo(x, y, cit["gioco"])
    centrato(x + 7, y + 30, cit["nome"].split()[0], NERO)
centrato(120, 148, "Tutto dalla palette bloccata", c(["pietra calcarea", 1]))

out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(QUI, "tavola_coalizione.png")
img.resize((720, 480), Image.NEAREST).save(out)
print("scritta", out)
