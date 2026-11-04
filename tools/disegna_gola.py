#!/usr/bin/env python3
"""Le griglie delle quattro stanze della gola del Bottaccione (mondo/aree/gola_*.area, condotto.area).

Ogni stanza e' 64x32 e si percorre da sinistra (A, verso valle) a destra (B, verso monte). La via
non e' un rettangolo: segue una curva, si stringe e si allarga; sotto (o di traverso) corre il
Camignano. Sulle sponde erba, cespugli, massi caduti e lecci aggrappati alla rupe. I tratti propri di
ogni stanza:

  gola_striscia  la striscia nera del limite K-Pg (x): uno strato orizzontale e continuo nella rupe
                 sopra la via, da un capo all'altro della stanza; la lapide (i) ai piedi della rupe;
                 lo slargo del forziere sulla sponda del torrente
  gola_miasmi    il torrente scende ripido e taglia la via: si passa su un ponticello (+) corto; le
                 chiazze di nebbia verde (g), una delle quali sbarra la via da parete a parete, sull'acqua
                 appena passato il ponte (la scena B-02 parte sulla prima nebbia: non si salta)
  gola_arco      l'arco di un contrafforte (J coi piloni X) da parete a parete: e' il riparo da cui si
                 ascoltano i soldati (B-03 parte sotto l'arco); lo slargo del secondo forziere
  condotto       il camminamento stretto sopra gli archi dell'acquedotto (P), la canaletta (~) e, a
                 monte, la diga del Bottaccione (|) col lago dietro

Gli slarghi dei forzieri sono in SLARGHI (li legge tools/genera_storia.py).

    python tools/disegna_gola.py              # riscrive le griglie nei file .area (il resto del file resta)
    python tools/disegna_gola.py --controlla  # controlla che le griglie dei file siano quelle di qui
"""
import math
import os
import random
import sys

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 64, 32
VARCO = range(13, 19)           # le righe dei varchi ai due lati

# lo slargo dei forzieri: (x, y) della cella libera in mezzo, dove sta il forziere
SLARGHI = {"gola_striscia": (40, 21), "gola_arco": (20, 22)}

# la cella che fa partire una scena entrandoci (tools/genera_storia.py, INNESCHI): deve sbarrare la via
SBARRANO = {"gola_miasmi": "g", "gola_arco": "J"}


def via(x, fase, ampiezza):
    """Il centro e la mezza larghezza della via alla colonna x: curva e respiro diversi per stanza."""
    if x < 4 or x > W - 5:
        return 15.5, 3
    c = 15.5 + ampiezza * math.sin(x / 9.0 + fase)
    m = 2.2 + 1.3 * (0.5 + 0.5 * math.sin(x / 5.0 + fase * 2))
    return c, m


def torrente_a_fascia(g, ys_di_x):
    """Il torrente come fascia alta 3 celle intorno a ys_di_x(x); fra due colonne vicine riempie il salto,
    cosi' anche un tratto ripido resta un corso d'acqua continuo."""
    prima = None
    for x in range(W):
        ys = ys_di_x(x)
        if ys is None:
            prima = None
            continue
        y = int(round(ys))
        da, a = (y, y) if prima is None else (min(y, prima), max(y, prima))
        for yy in range(da - 1, a + 2):
            if 0 <= yy < H:
                g[yy][x] = "~"
        prima = y


def stanza(nome, fase, ampiezza, torrente, chiusa_a_monte=False):
    r = random.Random(nome)
    g = [["#"] * W for _ in range(H)]
    if torrente:
        torrente_a_fascia(g, torrente)
    # la via con le sponde d'erba; dove incontra il torrente, il ponticello
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


def slargo(g, x0, y0, rx=3, ry=1):
    """Una radura ovale intorno a (x0, y0) e il passaggio largo due celle fino alla via."""
    for y in range(y0 - ry, y0 + ry + 1):
        for x in range(x0 - rx, x0 + rx + 1):
            if ((x - x0) / (rx + 0.5)) ** 2 + ((y - y0) / (ry + 0.5)) ** 2 <= 1 and g[y][x] in "#.rkT":
                g[y][x] = ","
    passo = 1 if y0 < 15 else -1
    y = y0 + passo * ry
    while True:
        y += passo
        if g[y][x0] in ",+":
            break
        g[y][x0] = g[y][x0 + 1] = ","
    # l'erba intorno alla radura
    for y in range(y0 - ry - 1, y0 + ry + 2):
        for x in range(x0 - rx - 1, x0 + rx + 2):
            if g[y][x] == "#":
                g[y][x] = "."


def alto_della_via(g, x):
    """La prima riga dall'alto che non e' rupe (ne' un leccio aggrappato alla rupe), nella colonna x."""
    return min(y for y in range(H) if g[y][x] not in "#xT")


def striscia(g):
    """La striscia nera: uno strato orizzontale e continuo, due righe sopra il punto piu' alto della via
    (fra la striscia e la via resta sempre almeno una riga di rupe), da un capo all'altro della stanza.
    La lapide ai piedi della rupe, sopra la via, dove la parete e' dritta per due celle."""
    riga = min(alto_della_via(g, x) for x in range(2, W - 2)) - 2
    for x in range(W):
        if g[riga][x] == "#":
            g[riga][x] = "x"
    for x in sorted(range(8, W - 9), key=lambda x: abs(x - 24)):
        a, b = alto_della_via(g, x), alto_della_via(g, x + 1)
        if a == b and a - 1 > riga + 1 and g[a][x] in ".rk" and g[a][x + 1] in ".rk":
            g[a][x] = g[a][x + 1] = "."
            g[a - 1][x] = g[a - 1][x + 1] = "i"
            return riga
    raise ValueError("gola_striscia: nessun posto dritto per la lapide")


def miasmi(g):
    """Le chiazze di nebbia: due sulla via, e una che la sbarra da parete a parete appena passato il ponte,
    bassa sull'acqua del Camignano (la regia di B-02)."""
    for cx, rx in ((14, 4), (50, 4)):
        for x in range(cx - rx, cx + rx + 1):
            for y in range(H):
                if g[y][x] == "," and abs(x - cx) + abs(y - 15.5) * 0.8 <= rx + 1:
                    g[y][x] = "g"
    ponte = [x for x in range(W) if any(g[y][x] == "+" for y in range(H))]
    for x in range(max(ponte) + 1, max(ponte) + 5):
        for y in range(H):
            if g[y][x] == ",":
                g[y][x] = "g"


def arco(g):
    """L'arco del contrafforte, tre colonne da parete a parete sulla via; i piloni salgono nella rupe sopra
    e scendono sotto la via, fino alle sponde."""
    for x in range(36, 39):
        for y in range(H):
            if g[y][x] in ",+":
                g[y][x] = "J"
        su = min(y for y in range(H) if g[y][x] == "J")
        giu = max(y for y in range(H) if g[y][x] == "J")
        for y in list(range(su - 3, su)) + list(range(giu + 1, giu + 3)):
            if g[y][x] in "#.rkT":
                g[y][x] = "X"


def condotto(g):
    """Il camminamento stretto: la via ridotta a 3 righe sopra gli archi; la canaletta sopra la via; la
    diga a monte con il lago dietro; davanti alla diga la via si allarga un poco (dove sta Corrado)."""
    for x in range(4, W - 3):
        c = 15
        for y in range(H):
            if g[y][x] in ",.rkT+g~":
                g[y][x] = "#"
        for y in range(c - 1, c + 2):
            g[y][x] = ","
        g[c - 2][x] = "~"
        for y in range(c + 2, c + 10):
            g[y][x] = "P"
    for x in range(W - 8, W - 5):
        for y in range(4, 28):
            g[y][x] = "|"
    for x in range(W - 5, W):
        for y in range(4, 28):
            g[y][x] = "~"
    for x in range(46, W - 8):
        for y in range(12, 18):
            g[y][x] = ","
    # l'erba ai piedi della rupe sopra lo slargo e il masso caduto
    for x in range(47, W - 9):
        if g[11][x] == "#":
            g[11][x] = "."
    g[11][49] = "k"


TORRENTI = {
    "gola_striscia": lambda x: 25 + 1.5 * math.sin(x / 7.0),
    # il torrente scende dal monte (in alto a destra), taglia la via di traverso e corre in basso a valle
    "gola_miasmi": lambda x: 26 + math.sin(x / 5.0) if x < 25 else (7 + math.sin(x / 6.0) if x > 33
                                                                      else 26 - (x - 25) * 19 / 8),
    "gola_arco": lambda x: 26 + 1.2 * math.sin(x / 6.0 + 1),
    "condotto": None,
}


def griglie():
    out = {}
    g = stanza("gola_striscia", 0.0, 1.2, TORRENTI["gola_striscia"])     # la via corre dritta sotto la striscia
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


def percorso_senza(g, vietata):
    """Si va dal varco A al varco B senza mai entrare in una cella 'vietata'? (passi di una cella, le celle
    calpestabili della gola: suolo, via, ponte, nebbia, arco, varchi)."""
    libere = set(".,+gJAB") - set(vietata)
    partenze = [(0, y) for y in range(H) if g[y][0] == "A"]
    viste, coda = set(partenze), list(partenze)
    while coda:
        x, y = coda.pop()
        if g[y][x] == "B":
            return True
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < W and 0 <= ny < H and (nx, ny) not in viste and g[ny][nx] in libere:
                viste.add((nx, ny))
                coda.append((nx, ny))
    return False


def testo_griglia(g):
    return "\n".join("".join(r) for r in g) + "\n"


def main(argv):
    diverse = []
    for nome, g in griglie().items():
        if nome in SBARRANO and percorso_senza(g, SBARRANO[nome]):
            print(f"[gola] ERRORE: in {nome} si passa da A a B senza «{SBARRANO[nome]}»", file=sys.stderr)
            return 1
        p = os.path.join(RADICE, "mondo", "aree", nome + ".area")
        testa, _, vecchia = open(p, encoding="utf-8").read().partition("griglia\n")
        if "--controlla" in argv:
            if vecchia != testo_griglia(g):
                diverse.append(nome)
            continue
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(testa + "griglia\n" + testo_griglia(g))
        print("[gola] scritto", os.path.relpath(p, RADICE))
    if diverse:
        print(f"[gola] griglie non aggiornate: {', '.join(diverse)} (python tools/disegna_gola.py)", file=sys.stderr)
        return 1
    if "--controlla" in argv:
        print("[gola] OK: le griglie delle quattro stanze sono aggiornate")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
