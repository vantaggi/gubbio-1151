#!/usr/bin/env python3
"""Le griglie delle quattro stanze della gola del Bottaccione (mondo/aree/gola_*.area, condotto.area).

Ogni stanza e' 64x32 e si percorre da sinistra (A, verso valle) a destra (B, verso monte). La via
non e' un rettangolo: segue una curva, si stringe e si allarga, ha uno slargo; sotto (o di traverso)
corre il Camignano, che si passa su un ponticello dove taglia la via. Sulle sponde erba, cespugli,
massi caduti e lecci aggrappati alla rupe. I tratti propri di ogni stanza:

  gola_striscia  la striscia nera del limite K-Pg (x), continua nella rupe sopra la via, e la lapide (i)
  gola_miasmi    le chiazze di nebbia verde (g) sulla via; il torrente taglia la via (ponticello +)
  gola_arco      l'arco di un contrafforte (J coi piloni X) e lo slargo dove stanno i soldati
  condotto       il camminamento stretto sopra gli archi dell'acquedotto (P), la canaletta (~) e, a
                 monte, la diga del Bottaccione (|) col lago dietro

Gli slarghi dove stanno i forzieri sono in SLARGHI (letti da tools/genera_storia.py).

    python tools/disegna_gola.py      # riscrive le griglie nei file .area (il resto del file resta)
"""
import math
import os
import random

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 64, 32
VARCO = range(13, 19)           # le righe dei varchi ai due lati

# lo slargo di ogni stanza: (x, y) della cella libera in mezzo, dove sta un forziere
SLARGHI = {"gola_striscia": (40, 9), "gola_arco": (20, 22)}


def via(x, fase, ampiezza):
    """Il centro e la mezza larghezza della via alla colonna x: curva e respiro diversi per stanza."""
    if x < 4 or x > W - 5:
        return 15.5, 3
    c = 15.5 + ampiezza * math.sin(x / 9.0 + fase)
    m = 2.2 + 1.3 * (0.5 + 0.5 * math.sin(x / 5.0 + fase * 2))
    return c, m


def stanza(nome, fase, ampiezza, torrente, chiusa_a_monte=False):
    r = random.Random(nome)
    g = [["#"] * W for _ in range(H)]
    # il torrente: una fascia ondulata (in basso, o che taglia la via in diagonale)
    for x in range(W):
        ys = torrente(x)
        if ys is None:
            continue
        for y in range(int(ys) - 1, int(ys) + 2):
            if 0 <= y < H:
                g[y][x] = "~"
    # la via con le sponde d'erba
    for x in range(W):
        c, m = via(x, fase, ampiezza)
        alto, basso = (13, 18) if x < 2 or x > W - 3 else (int(round(c - m)), int(round(c + m)))
        for y in range(alto, basso + 1):
            g[y][x] = "+" if g[y][x] == "~" else ","
        if 2 < x < W - 3:
            for y in (alto - 1, basso + 1):
                if 0 <= y < H and g[y][x] == "#":
                    g[y][x] = "."
    # le sponde del torrente
    for x in range(1, W - 1):
        for y in range(1, H - 1):
            if g[y][x] == "#" and any(g[y + dy][x] == "~" for dy in (-1, 1)) and 2 < x < W - 3:
                g[y][x] = "."
    # erba, cespugli, massi e lecci sulle sponde e ai piedi della rupe
    for x in range(3, W - 3):
        for y in range(1, H - 1):
            if g[y][x] == "." and r.random() < 0.12:
                g[y][x] = r.choice("rrk")
            elif g[y][x] == "#" and g[y + 1][x] == "." and r.random() < 0.08:
                g[y][x] = "T"
    if chiusa_a_monte:
        for y in VARCO:
            for x in range(W - 3, W):
                g[y][x] = "#"
    for y in VARCO:
        g[y][0] = g[y][1] = "A"
        if not chiusa_a_monte:
            g[y][W - 2] = g[y][W - 1] = "B"
    return g


def slargo(g, x0, y0, rx=3, ry=2):
    for y in range(y0 - ry, y0 + ry + 1):
        for x in range(x0 - rx, x0 + rx + 1):
            if ((x - x0) / (rx + 0.5)) ** 2 + ((y - y0) / (ry + 0.5)) ** 2 <= 1 and g[y][x] in "#.rkT":
                g[y][x] = ","
    # il passaggio fino alla via, in giu' o in su
    passo = 1 if y0 < 15 else -1
    y = y0
    while g[y][x0] != "," or y == y0:
        y += passo
        if g[y][x0] in ",+":
            break
        g[y][x0] = g[y][x0 + 1] = ","


def striscia(g):
    # la striscia nera nella rupe sopra la via, continua da un capo all'altro; la lapide sotto
    for x in range(3, W - 3):
        alto = min(y for y in range(H) if g[y][x] in ",.+rkTg")
        y = max(1, alto - 3)
        g[y][x] = "x"
    g[11][24] = g[11][25] = "i"
    if g[12][24] == "#":
        g[12][24] = g[12][25] = "."


def miasmi(g):
    for cx, rx in ((14, 4), (30, 5), (48, 4)):
        for x in range(cx - rx, cx + rx + 1):
            for y in range(H):
                if g[y][x] == "," and abs(x - cx) + abs(y - 15) * 0.8 <= rx + 1:
                    g[y][x] = "g"


def arco(g):
    for x in range(36, 39):
        for y in range(H):
            if g[y][x] in ",+":
                g[y][x] = "J"
        su = min(y for y in range(H) if g[y][x] == "J") - 1
        giu = max(y for y in range(H) if g[y][x] == "J") + 1
        g[su][x] = g[giu][x] = "X"


def condotto(g):
    # il camminamento stretto: la via ridotta a 3 righe sopra gli archi; la canaletta sopra la via;
    # la diga a monte con il lago dietro
    for x in range(4, W - 3):
        c = 15
        for y in range(H):
            if g[y][x] in ",.rkT+g~":
                g[y][x] = "#"
        for y in range(c - 1, c + 2):
            g[y][x] = ","
        g[c - 2][x] = "~"
        for y in range(c + 2, min(H, c + 12)):
            g[y][x] = "P"
    for x in range(W - 8, W - 5):
        for y in range(4, 28):
            g[y][x] = "|"
    for x in range(W - 5, W):
        for y in range(4, 28):
            g[y][x] = "~"
    # la via arriva alla diga: davanti si allarga un poco (dove sta Corrado)
    for x in range(46, W - 8):
        for y in range(12, 18):
            g[y][x] = ","


TORRENTI = {
    "gola_striscia": lambda x: 25 + 1.5 * math.sin(x / 7.0),
    "gola_miasmi": lambda x: 26 - x * 0.3 if 0 < x < 60 else None,            # taglia la via: il ponticello
    "gola_arco": lambda x: 26 + 1.2 * math.sin(x / 6.0 + 1),
    "condotto": lambda x: None,
}


def griglie():
    out = {}
    g = stanza("gola_striscia", 0.0, 2.5, TORRENTI["gola_striscia"])
    slargo(g, *SLARGHI["gola_striscia"])
    striscia(g)
    out["gola_striscia"] = g
    g = stanza("gola_miasmi", 1.3, 2.0, TORRENTI["gola_miasmi"])
    miasmi(g)
    out["gola_miasmi"] = g
    g = stanza("gola_arco", 2.6, 2.5, TORRENTI["gola_arco"])
    slargo(g, *SLARGHI["gola_arco"])
    arco(g)
    out["gola_arco"] = g
    g = stanza("condotto", 3.9, 1.0, TORRENTI["condotto"], chiusa_a_monte=True)
    condotto(g)
    out["condotto"] = g
    return out


def main():
    for nome, g in griglie().items():
        p = os.path.join(RADICE, "mondo", "aree", nome + ".area")
        testa = open(p, encoding="utf-8").read().split("griglia\n")[0]
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(testa + "griglia\n" + "\n".join("".join(r) for r in g) + "\n")
        print("scritto", os.path.relpath(p, RADICE))


if __name__ == "__main__":
    main()
