"""Gli utensili comuni dei pittori delle cutscene C5, C6 e C7 (tools/pittore_c5.py, pittore_c6.py,
pittore_c7.py): il poligono pieno, il contorno, l'alone a scacchiera e i piombi della vetrata.

Lavorano sulla Tela a indici di tools/genera_battaglia.py; non scelgono colori, li ricevono.
"""
import random

ACCESO = "acceso"        # una voce di palette che di notte resta col tono del giorno (tools/pittore_panorami.py)
W, H = 512, 256
QUADRO = 112


def poligono(t, punti, c):
    """Il poligono pieno (regola pari-dispari, campionato a meta' riga)."""
    ys = [p[1] for p in punti]
    for y in range(int(min(ys)), int(max(ys)) + 1):
        xs = []
        n = len(punti)
        for i in range(n):
            (x0, y0), (x1, y1) = punti[i], punti[(i + 1) % n]
            if (y0 <= y + 0.5 < y1) or (y1 <= y + 0.5 < y0):
                xs.append(x0 + (y + 0.5 - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for a, b in zip(xs[::2], xs[1::2]):
            for x in range(int(round(a)), int(round(b))):
                t.punto(x, y, c)


def contorna(t, colore, dentro=lambda c: c != 0):
    """Il contorno: ogni pixel trasparente accanto (in croce) a uno 'dentro' prende 'colore'."""
    pieni = {(x, y) for y in range(t.h) for x in range(t.w) if dentro(t.px[y][x])}
    for (x, y) in pieni:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            u, v = x + dx, y + dy
            if 0 <= u < t.w and 0 <= v < t.h and (u, v) not in pieni and t.px[v][u] == 0:
                t.px[v][u] = colore


def alone(t, cx, cy, rx, ry, interno, esterno, scacchi=True):
    """Un alone ellittico: pieno al centro, all'esterno il bordo a scacchiera."""
    for y in range(int(cy - ry), int(cy + ry) + 1):
        for x in range(int(cx - rx), int(cx + rx) + 1):
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if d < 0.35:
                t.punto(x, y, interno)
            elif d < 1 and (not scacchi or d < 0.7 or (x + y) % 2):
                t.punto(x, y, esterno)


def piombi(t, piombo, griglia=(11, 13), sfasa=0):
    """Stile vetrata: il piombo dove cambia colore e, dentro le forme grandi, pannelli irregolari
    (celle di Voronoi da semi sparsi su una griglia, sfasata per piano): il vetro non e' mai un pezzo
    solo, e non sembra un muro di mattoni. I semi si ripetono ogni 128 px (16 tile), cosi' il disegno
    dei piombi non moltiplica i tile del piano."""
    gx, gy = griglia
    r = random.Random(sfasa * 31 + gx)
    n = 128 // gx
    if n * gx != 128:
        raise ValueError("il passo dei pannelli deve dividere 128")
    base = {(i, j): (r.uniform(0.15, 0.85) * gx, r.uniform(0.15, 0.85) * gy)
            for j in range(-1, QUADRO // gy + 2) for i in range(n)}
    semi = {}
    for j in range(-1, QUADRO // gy + 2):
        for i in range(-1, W // gx + 2):
            ox, oy = base[(i % n, j)]
            semi[(i, j)] = (i * gx + ox, j * gy + oy)

    def cella(x, y):
        i, j = int(x // gx), int(y // gy)
        meglio, quale = 1e9, None
        for dj in (-1, 0, 1):
            for di in (-1, 0, 1):
                k = (i + di, j + dj)
                sx, sy = semi[k]
                d = (x - sx) ** 2 + (y - sy) ** 2
                if d < meglio:
                    meglio, quale = d, k
        return quale
    celle = [[cella(x, y) for x in range(W)] for y in range(QUADRO)]
    px = [riga[:] for riga in t.px]
    for y in range(QUADRO - 1):
        for x in range(W - 1):
            c = px[y][x]
            if not c:
                continue
            bordo = (px[y][x + 1] != c and px[y][x + 1]) or (px[y + 1][x] != c and px[y + 1][x])
            pannello = celle[y][x] != celle[y][x + 1] or celle[y][x] != celle[y + 1][x]
            if bordo or pannello:
                t.punto(x, y, piombo)
