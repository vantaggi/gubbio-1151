#!/usr/bin/env python3
"""Gli stradoni del Monte Ingino: da mondo/stradoni.json scrive mondo/aree/monte_ingino.area.

Il percorso sale a zig-zag verso destra, come la salita del resto del mondo: 8 tratti verticali di
ghiaia (b), alternati in giu' e in su, cuciti da tornanti orizzontali. In alto a sinistra Porta
Sant'Ubaldo con i due varchi verso la citta' (A da via Sant'Ubaldo, E da via Appennino); in alto a
destra l'arrivo alla Basilica (B). Ai lati bosco (#), con lecci e roverelle (T) e rocce (k) sulle
scarpate; le cappellette (c) stanno nel gomito dei loro tornanti. Il lato a valle (in alto) e' un
belvedere sulla citta'.

    python tools/disegna_stradoni.py            # controlla che il file sia aggiornato
    python tools/disegna_stradoni.py --scrivi   # lo riscrive
"""
import json
import os
import sys

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATI = os.path.join(RADICE, "mondo", "stradoni.json")
AREA = os.path.join(RADICE, "mondo", "aree", "monte_ingino.area")

W, H = 128, 64
LARGO = 4              # tile di ghiaia per tratto
X0, PASSO = 6, 16      # colonna del primo tratto e distanza fra un tratto e il successivo
Y_INIZIO = 2           # il primo tratto parte dall'arco di Porta Sant'Ubaldo
LATO_CAPPELLETTA = 3


def colonne(n):
    return [X0 + k * PASSO for k in range(n)]


def percorso(tratti):
    """[(x, y_da, y_a)] per tratto, nell'ordine dal basso: i dispari scendono, i pari risalgono."""
    out, y = [], Y_INIZIO
    for k, (x, lunghezza) in enumerate(zip(colonne(len(tratti)), tratti)):
        if k % 2 == 0:
            y_da, y_a = y, y + lunghezza - 1
        else:
            y_da, y_a = y, y - lunghezza + 1
        if not (Y_INIZIO <= min(y_da, y_a) and max(y_da, y_a) <= H - 3):
            raise SystemExit(f"[stradoni] il tratto {k + 1} esce dall'area: righe {y_da}..{y_a}")
        out.append((x, y_da, y_a))
        y = y_a
    return out


def disegna(dati):
    tratti = dati["tratti"]
    g = [["#"] * W for _ in range(H)]
    righe = percorso(tratti)

    def ghiaia(x0, y0, x1, y1):
        for y in range(min(y0, y1), max(y0, y1) + 1):
            for x in range(min(x0, x1), max(x0, x1) + 1):
                g[y][x] = "b"

    tornanti = []
    for k, (x, y_da, y_a) in enumerate(righe):
        ghiaia(x, y_da, x + LARGO - 1, y_a)
        if k + 1 < len(righe):
            # il tornante: una fascia larga quanto il tratto, all'estremo dove il tratto finisce
            giu = y_a > y_da
            fascia = (y_a - LARGO + 1, y_a) if giu else (y_a, y_a + LARGO - 1)
            x_dopo = righe[k + 1][0]
            ghiaia(x, fascia[0], x_dopo + LARGO - 1, fascia[1])
            tornanti.append((x, x_dopo, fascia, giu))
    # l'arrivo: dall'ultimo tratto al bordo destro, verso la Basilica
    x, _, y_a = righe[-1]
    ghiaia(x, y_a, W - 3, y_a + LARGO - 1)
    for y in range(y_a, y_a + LARGO):
        g[y][W - 2] = g[y][W - 1] = "B"
    # Porta Sant'Ubaldo: A in alto sul primo tratto, E a sinistra con il suo raccordo
    for x in range(X0, X0 + LARGO):
        g[0][x] = g[1][x] = "A"
    y_e = 10
    ghiaia(2, y_e, X0 - 1, y_e + LARGO - 1)
    for y in range(y_e, y_e + LARGO):
        g[y][0] = g[y][1] = "E"
    # le cappellette nel gomito dei loro tornanti, attaccate alla fascia
    for c in dati["cappellette"]:
        x, x_dopo, (f0, f1), giu = tornanti[c["tornante"] - 1]
        cx = (x + LARGO + x_dopo) // 2 - LATO_CAPPELLETTA // 2
        cy = f0 - LATO_CAPPELLETTA if giu else f1 + 1
        for y in range(cy, cy + LATO_CAPPELLETTA):
            for xx in range(cx, cx + LATO_CAPPELLETTA):
                g[y][xx] = "c"
    # scarpate: lecci, roverelle e rocce accanto alla ghiaia, mai addosso ai varchi
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            if g[y][x] != "#":
                continue
            accanto = [g[y + dy][x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            vicino = [g[y + dy][x + dx] for dx in (-2, -1, 0, 1, 2) for dy in (-2, -1, 0, 1, 2)
                      if 0 <= y + dy < H and 0 <= x + dx < W]
            if "b" not in accanto or any(c in "ABEc" for c in vicino):
                continue
            if (x * 7 + y * 13) % 5 == 0:
                g[y][x] = "T"
            elif (x * 5 + y * 3) % 11 == 0:
                g[y][x] = "k"
    spawn = {
        1: (X0 + 1, 8),                        # da via Sant'Ubaldo, sotto la porta
        3: (X0 + 1, y_e + LARGO + 4),          # da via Appennino
        2: (righe[-1][0] + 1, y_a + LARGO + 2),  # dalla Basilica, all'arrivo
    }
    # lo spawn iniziale guarda la cappelletta di Sant'Ubaldo dal suo tornante
    x, x_dopo, (f0, f1), giu = tornanti[dati["cappellette"][0]["tornante"] - 1]
    spawn[0] = ((x + LARGO + x_dopo) // 2, f0 + 1)
    return g, spawn


def testo(dati):
    g, spawn = disegna(dati)
    righe = [
        "# Generato da tools/disegna_stradoni.py da mondo/stradoni.json: non modificare a mano.",
        "# Gli stradoni: 8 tratti di ghiaia a zig-zag da Porta Sant'Ubaldo alla Basilica, le",
        "# cappellette ai tornanti 3, 6 e 7, il bosco ai lati, il belvedere sulla citta' a valle.",
        "id monte_ingino",
        "etichetta AREA_MONTE_INGINO",
        f"dimensioni {W} {H}",
        "monte destra",
        "belvedere alto",
        "stradoni",
        f"riferimento {W // 2} {H // 2}",
        "fattore 0.73",
    ]
    righe += [f"spawn {k} {x} {y}" for k, (x, y) in sorted(spawn.items())]
    righe += ["uscita A duomo_ducale 1", "uscita B basilica 2", "uscita E sant_andrea 3", "griglia"]
    righe += ["".join(r) for r in g]
    return "\n".join(righe) + "\n"


def main(argv):
    with open(DATI, encoding="utf-8") as f:
        dati = json.load(f)
    nuovo = testo(dati)
    vecchio = open(AREA, encoding="utf-8").read() if os.path.exists(AREA) else ""
    if "--scrivi" in argv:
        with open(AREA, "w", encoding="utf-8", newline="\n") as f:
            f.write(nuovo)
        print(f"[stradoni] scritto {os.path.relpath(AREA, RADICE)}")
        return 0
    if nuovo != vecchio:
        print("[stradoni] mondo/aree/monte_ingino.area da rigenerare con --scrivi")
        return 1
    print("[stradoni] aggiornato")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
