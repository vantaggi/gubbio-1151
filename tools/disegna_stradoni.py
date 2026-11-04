#!/usr/bin/env python3
"""Gli stradoni del Monte Ingino: da mondo/stradoni.json scrive mondo/aree/monte_ingino.area.

Nord in alto (4 nov 2026): il percorso sale a zig-zag verso l'alto, verso la cima: 9 tratti
orizzontali di ghiaia (b), alternati verso destra e verso sinistra, cuciti da tornanti. In basso a
sinistra Porta Sant'Ubaldo con i due varchi verso la citta' (A da via Sant'Ubaldo, a sinistra; E da
via Appennino, in basso); in alto l'arrivo alla Basilica (B). Ai lati bosco (#), con lecci e
roverelle (T) e rocce (k) sulle scarpate; le cappellette (c) stanno nel gomito dei loro tornanti.
Il lato a valle (a sinistra) e' un belvedere sulla citta'. Il disegno si fa coricato (W x H, salita
a destra) e ruota() lo gira.

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
X0, PASSO = 6, 14      # colonna del primo tratto e distanza fra un tratto e il successivo
Y_INIZIO = 2           # il primo tratto parte dall'arco di Porta Sant'Ubaldo
LATO_CAPPELLETTA = 3
GOMITO = 2             # tile di ghiaia in piu' nel gomito interno di un tornante: la curva tonda


def caso(x, y, seme=0):
    """Un numero fisso in [0, 1) per la cella: lo stesso caso di genera_mondo.pseudo."""
    h = (x * 374761393 + y * 668265263 + seme * 2246822519) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65536.0


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
            # la curva: il gomito interno si allarga in tondo verso i due tratti
            dentro = fascia[0] - 1 if giu else fascia[1] + 1
            passo = -1 if giu else 1
            for k in range(GOMITO):
                for xx in (x + LARGO + k, x_dopo - 1 - k):
                    for j in range(GOMITO - k):
                        g[dentro + passo * j][xx] = "b"
            # il muretto a secco sul lato esterno del tornante, e gli spigoli di fuori smussati
            fuori = fascia[1] + 1 if giu else fascia[0] - 1
            for xx in range(x + 1, x_dopo + LARGO - 1):
                if 0 < fuori < H - 1:
                    g[fuori][xx] = "m"
            for xx in (x, x_dopo + LARGO - 1):
                g[fascia[1] if giu else fascia[0]][xx] = "m"
    # l'arrivo: dall'ultimo tratto al bordo destro, verso la Basilica
    x, y_da, y_a = righe[-1]
    y0 = y_a - LARGO + 1 if y_a > y_da else y_a     # la fascia d'arrivo sta dentro la fine del tratto
    ghiaia(x, y0, W - 3, y0 + LARGO - 1)
    for y in range(y0, y0 + LARGO):
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
    # i paracarri sul lato a valle (sinistra) dei tratti, uno ogni 4 tile
    for x, y_da, y_a in righe:
        for y in range(min(y_da, y_a) + 2, max(y_da, y_a) - 1, 4):
            if g[y][x - 1] == "#":
                g[y][x - 1] = "p"
    # il bosco: alberi e cespugli a macchie, rocce affioranti, mai in fila e mai addosso ai varchi
    piantati = set()
    # (non nelle prime righe: li' c'e' il belvedere sulla citta')
    for y, x in sorted(((y, x) for y in range(4, H - 1) for x in range(1, W - 1)), key=lambda c: caso(c[1], c[0], 4)):
        if g[y][x] != "#":
            continue
        vicino = [g[y + dy][x + dx] for dx in (-2, -1, 0, 1, 2) for dy in (-2, -1, 0, 1, 2)
                  if 0 <= y + dy < H and 0 <= x + dx < W]
        if any(c in "ABEc" for c in vicino) or any((x + i, y + j) in piantati for i in (-1, 0, 1) for j in (-1, 0, 1)):
            continue
        macchia = caso(x // 6, y // 6, 5)
        sul_bordo = "b" in vicino
        r = caso(x, y, 6)
        quattro = [(x + i, y + j) for i in range(2) for j in range(2)]
        if not sul_bordo and macchia > 0.3 and r < 0.85 and \
                all(g[v][u] == "#" and (u, v) not in piantati for u, v in quattro):
            # nel folto: chiome di 2x2 una accanto all'altra, la macchia di bosco
            for u, v in quattro:
                g[v][u] = "T"
            piantati.update(quattro)
        elif r < (0.30 if sul_bordo else 0.06) * (0.5 + macchia):
            g[y][x] = "u" if caso(x, y, 7) < 0.2 and g[y + 1][x] == "#" else ("r" if caso(x, y, 7) < 0.5 else "k")
            if g[y][x] == "u":
                g[y + 1][x] = "u"
                piantati.add((x, y + 1))
            piantati.add((x, y))
        elif r > 0.985 or (sul_bordo and r > 0.94):
            g[y][x] = "k"
            piantati.add((x, y))
    spawn = {
        1: (X0 + 1, 8),                        # da via Sant'Ubaldo, sotto la porta
        3: (X0 + 1, y_e + LARGO + 4),          # da via Appennino
        # dalla Basilica, all'arrivo, sull'ultimo tratto
        2: (righe[-1][0] + 1, y_a - 6 if y_a > righe[-1][1] else y_a + LARGO + 2),
    }
    # lo spawn iniziale guarda la cappelletta di Sant'Ubaldo dal suo tornante
    x, x_dopo, (f0, f1), giu = tornanti[dati["cappellette"][0]["tornante"] - 1]
    spawn[0] = ((x + LARGO + x_dopo) // 2, f0 + 1)
    return g, spawn


def ruota(g, spawn):
    """Nord in alto (4 nov 2026): il disegno si fa coricato, con la salita verso destra, e si gira di 90
    gradi in senso antiorario. I tratti diventano orizzontali e il percorso sale verso l'alto; il
    cipresso (1x2, in piedi) si rimette in piedi."""
    w, h = len(g[0]), len(g)
    r = [[g[x][w - 1 - y] for x in range(h)] for y in range(w)]
    for y in range(w):
        for x in range(h - 1):
            if r[y][x] == "u" and r[y][x + 1] == "u":
                r[y][x + 1] = "#"
                if y + 1 < w and r[y + 1][x] == "#":
                    r[y + 1][x] = "u"
                else:
                    r[y][x] = "r"
    return r, {k: (y, w - 1 - x) for k, (x, y) in spawn.items()}


def testo(dati):
    g, spawn = ruota(*disegna(dati))
    righe = [
        "# Generato da tools/disegna_stradoni.py da mondo/stradoni.json: non modificare a mano.",
        "# Gli stradoni: 9 tratti di ghiaia a zig-zag da Porta Sant'Ubaldo alla Basilica, le",
        "# cappellette ai tornanti 3, 6 e 7, il bosco ai lati, il belvedere sulla citta' a valle.",
        "id monte_ingino",
        "etichetta AREA_MONTE_INGINO",
        f"dimensioni {H} {W}",
        "monte alto",
        "belvedere sinistra",
        "stradoni",
        f"riferimento {H // 2} {W // 2 - 1}",
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
