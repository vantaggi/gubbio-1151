"""I piani di C7, le presentazioni dei luoghi: due cartoline brevi, solo al primo ingresso.

C7S, Gli Stradoni del Monte (A1-07): il fianco del Monte Ingino nel pomeriggio che si fa sera (il cielo
di C4, gia' in ROM), i nove stradoni di ghiaia a zigzag, le tre cappellette al 3o, 6o e 7o tornante, la
Basilica col campanile in cima, i tre piccolissimi all'imbocco del primo stradone, davanti le fronde dei
lecci; poi il primo piano di una cappelletta col lumino acceso e sotto la valle coi tetti di Gubbio.

C7B, La gola del Bottaccione (B-01): una lama di cielo, la parete lontana cupa, la parete vicina a strati
inclinati di Scaglia rosata e grigia con, una volta sola, la riga scura sottile e l'argilla chiara sopra,
il condotto di pietra sugli archetti, il Camignano coi massi; poi il primo piano della parete.

Di giorno, senza luci accese. Dal mockup approvato (cutscene/v2, CUTM).

Un pittore riceve il momento e ritorna (tela, palette, notte), come in tools/pittore_panorami.py.
"""
import math
import random

from genera_battaglia import Tela
from pennelli import contorna, poligono

W, H = 512, 256
QUADRO = 112
SW = 240                           # lo schermo: i primi piani fermi si vedono da x=0 a 240

# ======================================================================================================
# C7S · Gli Stradoni del Monte
# ======================================================================================================
PALETTE_STRADONI = [("neutri", 0), ("neutri", 0), ("verde dei monti", 0), ("verde dei monti", 1),
                    ("verde dei monti", 2), ("verde dei monti", 3), ("pietra calcarea", 2), ("pietra calcarea", 4),
                    ("pietra calcarea", 5), ("cotto e coppi", 2), ("cotto e coppi", 3), ("legno e cuoio", 1),
                    ("neutri", 4), ("oro e bronzo", 3), ("vermiglio comunale", 2), ("cielo e acqua", 2)]
ST_C, ST_V0, ST_V1, ST_V2, ST_V3, ST_P2, ST_GHIAIA, ST_GHIAIA_L = 1, 2, 3, 4, 5, 6, 7, 8
ST_COTTO_S, ST_COTTO, ST_LEGNO, ST_BIANCO, ST_ORO, ST_ROSSO, ST_AZZURRO = 9, 10, 11, 12, 13, 14, 15
CAPPELLE = {3: "Sant'Ubaldo", 6: "San Giorgio", 7: "Sant'Antonio"}


def tornanti():
    """I nove stradoni a zigzag sul fianco del monte, dal basso: [(x0, y0, x1, y1)], tornante a ogni
    capo. Salgono verso destra e restringono: in cima la Basilica."""
    out = []
    y = 106
    for k in range(9):
        sx = 40 + k * 17
        dx = sx + 96
        a, b = (sx, dx) if k % 2 == 0 else (dx, sx + 17)
        out.append((a, y, b, y - 10))
        y -= 10
    return out


def c7_monte(m):
    t = Tela(W, H)
    def cresta(x):
        return int(2 + 0.0016 * (x - 300) ** 2 + 2 * math.sin(x / 9.0))
    for x in range(W):                                                            # il fianco del monte
        top = cresta(x)
        for y in range(max(0, top), QUADRO):
            t.punto(x, y, ST_V1 if (x * 5 + y * 3) % 13 else ST_V0)
        if top >= 0:
            t.punto(x, top, ST_V3)
    r = random.Random(17)
    for _ in range(260):                                                          # il bosco a macchie
        cx, cy = r.randrange(W), r.randrange(4, QUADRO)
        if cy > cresta(cx) + 3:
            t.ellisse(cx, cy, 3, 2, ST_V2 if r.random() < 0.55 else ST_V0)
            t.punto(cx - 1, cy - 1, ST_V3)
    gir = tornanti()
    for k, (x0, y0, x1, y1) in enumerate(gir):                                    # gli stradoni di ghiaia
        n = abs(x1 - x0)
        for i in range(n + 1):
            x = x0 + (x1 - x0) * i / n
            y = y0 + (y1 - y0) * i / n
            if y < cresta(int(x)) + 4:
                continue                                                  # niente strade nel cielo
            t.rett(x, y - 1, 1, 3, ST_GHIAIA)
            t.punto(x, y - 1, ST_GHIAIA_L)
            t.punto(x, y + 2, ST_V0)
        if k + 1 < len(gir):                                                      # il tornante
            for a in range(0, 11):
                ang = math.pi * a / 10
                lato = 1 if x1 > x0 else -1
                hx, hy = x1 + lato * 5 * math.sin(ang), y1 - 5 + 5 * math.cos(ang) - 1
                if hy > cresta(int(hx)) + 4:
                    t.rett(hx, hy, 2, 3, ST_GHIAIA)
        if k + 1 in CAPPELLE:                                                     # la cappelletta
            cx, cy = int(x1) + (6 if x1 > x0 else -8), int(y1) - 1
            t.rett(cx - 3, cy - 7, 7, 7, ST_BIANCO)
            t.rett(cx + 2, cy - 7, 2, 7, ST_P2)
            poligono(t, [(cx - 4, cy - 7), (cx, cy - 10), (cx + 5, cy - 7)], ST_COTTO)
            t.rett(cx - 1, cy - 5, 2, 4, ST_C)
            t.punto(cx, cy - 3, ST_ORO)
    # la Basilica in cima, col campanile, sopra l'ultimo stradone
    bx, by = 222, 22
    t.rett(bx, by - 9, 30, 10, ST_BIANCO)
    t.rett(bx + 24, by - 9, 6, 10, ST_P2)
    poligono(t, [(bx - 1, by - 9), (bx + 15, by - 15), (bx + 31, by - 9)], ST_COTTO)
    t.rett(bx + 32, by - 20, 6, 21, ST_BIANCO)
    t.rett(bx + 36, by - 20, 2, 21, ST_P2)
    poligono(t, [(bx + 31, by - 20), (bx + 35, by - 25), (bx + 39, by - 20)], ST_COTTO)
    for k in range(4):
        t.rett(bx + 3 + k * 6, by - 5, 3, 4, ST_C)
    # i tre all'imbocco del primo stradone, piccoli: la mitra bianca, l'elmo, il saio
    for i, (c1, c2) in enumerate(((ST_BIANCO, ST_ORO), (ST_P2, ST_ROSSO), (ST_LEGNO, ST_LEGNO))):
        x = 44 + i * 6
        t.rett(x, 99, 3, 6, c1)
        t.rett(x, 97, 3, 2, c2)
        t.punto(x + 1, 96, ST_C)
    return t, PALETTE_STRADONI, False


def c7_fronde(m):
    """Davanti, agli angoli, le fronde dei lecci in ombra: incorniciano e danno la profondita'."""
    t = Tela(W, H)
    r = random.Random(4)
    for (x0, y0, n) in ((0, 0, 70), (246, 118, 50), (330, 0, 60), (500, 112, 40)):
        for _ in range(n):
            cx, cy = x0 + r.gauss(0, 16), y0 + r.gauss(0, 12)
            t.ellisse(cx, cy, r.randint(3, 6), r.randint(2, 4), ST_V0)
        for _ in range(n // 2):
            cx, cy = x0 + r.gauss(0, 14), y0 + r.gauss(0, 10)
            t.ellisse(cx - 1, cy - 1, 2, 1, ST_V1)
    contorna(t, ST_C)
    return t, PALETTE_STRADONI, False


def c7_cappella(m):
    """Il primo piano di una cappelletta al tornante: la ghiaia che gira, il muretto a secco, sotto
    la valle e i tetti di Gubbio."""
    t = Tela(W, H)
    for y in range(QUADRO):
        for x in range(W):
            if y < 26 or (y < 30 and (x + y) % 2):
                t.punto(x, y, ST_AZZURRO)
            elif y < 40:
                t.punto(x, y, ST_V2)
            else:
                t.punto(x, y, ST_V1)
    r = random.Random(5)
    for k in range(60):                                                           # i tetti giu' a valle
        x, y = r.randrange(0, 130), r.randrange(42, 60)
        t.rett(x, y, r.randint(3, 6), 2, ST_COTTO)
        t.rett(x, y + 2, 3, 1, ST_P2)
    poligono(t, [(0, 112), (0, 80), (60, 72), (140, 70), (240, 78), (240, 112)], ST_GHIAIA)
    for _ in range(400):
        x, y = r.randrange(240), r.randrange(72, 112)
        if t.px[y][x] == ST_GHIAIA:
            t.punto(x, y, ST_GHIAIA_L if r.random() < 0.5 else ST_P2)
    for x in range(0, 140, 7):                                                    # il muretto
        t.rett(x, 64 + x // 40, 6, 4, ST_P2)
        t.rett(x, 64 + x // 40, 6, 1, ST_GHIAIA_L)
    cx = 150
    t.rett(cx, 26, 40, 48, ST_BIANCO)
    t.rett(cx + 32, 26, 8, 48, ST_P2)
    poligono(t, [(cx - 4, 27), (cx + 20, 12), (cx + 44, 27)], ST_COTTO)
    poligono(t, [(cx + 20, 12), (cx + 44, 27), (cx + 36, 27)], ST_COTTO_S)
    t.rett(cx + 8, 38, 16, 24, ST_C)
    t.ellisse(cx + 16, 38, 8, 6, ST_C)
    t.rett(cx + 14, 50, 4, 8, ST_ORO)                                             # il lumino
    t.rett(cx + 15, 47, 2, 3, ST_BIANCO)
    t.rett(cx + 15, 6, 2, 7, ST_C)
    t.rett(cx + 13, 8, 6, 2, ST_C)
    contorna(t, ST_C, lambda c: c in (ST_BIANCO, ST_P2, ST_COTTO, ST_COTTO_S))
    for i in range(3):                                                            # i cipressi dietro
        x = 206 + i * 12
        for yy in range(30):
            w = max(1, int(4 * math.sin(math.pi * (yy + 2) / 32)))
            t.rett(x - w, 44 + yy, 2 * w, 1, ST_V0)
    return t, PALETTE_STRADONI, False


# ======================================================================================================
# C7B · La gola del Bottaccione
# ======================================================================================================
PALETTE_GOLA = [("neutri", 0), ("neutri", 0), ("cielo e acqua", 1), ("cielo e acqua", 2), ("pietra calcarea", 1),
                ("pietra calcarea", 2), ("pietra calcarea", 3), ("cotto e coppi", 1), ("cotto e coppi", 2),
                ("cotto e coppi", 3), ("legno e cuoio", 0), ("verde dei monti", 0), ("verde dei monti", 1),
                ("cielo e acqua", 0), ("cielo e acqua", 1), ("pietra calcarea", 4)]
G_C, G_CIELO_S, G_CIELO, G_P1, G_P2, G_P3 = 1, 2, 3, 4, 5, 6
G_ROSA_S, G_ROSA, G_ROSA_C, G_NERA, G_V0, G_V1, G_ACQUA, G_ACQUA_C, G_P4 = 7, 8, 9, 10, 11, 12, 13, 14, 15


def strati(x, y, pendenza=0.18, scala=1.0):
    """Gli strati della Scaglia, inclinati e di spessore vario: rosati e grigi; la striscia nera,
    sottile, una volta sola."""
    s = (y + x * pendenza) / scala
    onda = 1.6 * math.sin(s / 7.0) + 0.8 * math.sin(s / 2.3)
    v = s + onda
    if 58 <= s < 59.6:
        return G_NERA
    if 59.6 <= s < 60.4:
        return G_P4                                                  # l'argilla chiara sopra la riga
    k = int(v // 3.4)
    return (G_ROSA_S, G_P2, G_ROSA, G_P1, G_ROSA_S, G_ROSA_C, G_P2)[k % 7]


def c7_gola_fondo(m):
    """Il fondo: una lama di cielo in alto e la parete lontana, cupa, che sale fuori dal quadro."""
    t = Tela(W, H, G_CIELO_S)
    for y in range(QUADRO):
        for x in range(W):
            if y > 6 or (y > 3 and (x + y) % 2):
                t.punto(x, y, G_CIELO)
    for x in range(W):
        top = 10 + int(6 * math.sin(x / 23.0) + 3 * math.sin(x / 7.0))
        for y in range(top, QUADRO):
            t.punto(x, y, G_P1 if (y // 5 + x // 60) % 5 else G_ROSA_S)
    return t, PALETTE_GOLA, False


def c7_gola_parete(m):
    """La parete vicina, ripida, a strati con la striscia nera; a mezza costa il condotto, il canale
    di pietra sugli archetti che porta l'acqua a Gubbio."""
    t = Tela(W, H)
    utile = 336                     # 8 s a 12 px/s per 3/4: oltre x=312 il piano non si vede mai
    for x in range(utile):
        top = 16 + int(10 * math.sin(x / 41.0) + 4 * math.sin(x / 13.0 + 1))
        bot = 92 + int(3 * math.sin(x / 17.0))
        for y in range(top, bot):
            t.punto(x, y, strati(x, y))
        t.punto(x, top, G_P4)
    for x in range(0, utile, 14):                                                     # il condotto
        t.rett(x, 70, 14, 4, G_P3)
        t.rett(x, 70, 14, 1, G_P4)
        t.rett(x, 74, 14, 1, G_C)
        t.rett(x + 1, 75, 3, 10, G_P2)
        t.rett(x + 3, 75, 1, 10, G_P1)
    r = random.Random(8)
    for _ in range(30):                                                           # ciuffi aggrappati
        cx, cy = r.randrange(utile), r.randrange(24, 88)
        if t.px[cy][cx]:
            t.ellisse(cx, cy, 3, 2, G_V1 if r.random() < 0.5 else G_V0)
    return t, PALETTE_GOLA, False


def c7_gola_torrente(m):
    """Il Camignano sul fondo, coi massi; davanti, agli angoli, edera e rovi in ombra."""
    t = Tela(W, H)
    for x in range(W):
        for y in range(94 + int(2 * math.sin(x / 17.0)), QUADRO):
            t.punto(x, y, G_ACQUA if (x // 6 + y * 2) % 7 else G_ACQUA_C)
    r = random.Random(9)
    for _ in range(18):
        cx = r.randrange(W)
        cy = 100 + r.randint(0, 8)
        t.ellisse(cx, cy, r.randint(4, 8), r.randint(2, 3), G_P2)
        t.rett(cx - 3, cy - 2, 4, 1, G_P3)
    for (x0, y0, n) in ((0, 0, 50), (150, 116, 30), (300, 0, 40)):
        for _ in range(n):
            t.ellisse(x0 + r.gauss(0, 14), y0 + r.gauss(0, 10), r.randint(3, 5), r.randint(2, 3), G_V0)
    contorna(t, G_C)
    return t, PALETTE_GOLA, False


def c7_striscia(m):
    """Il primo piano della parete: gli strati rosati e grigi, la riga scura e l'argilla chiara sopra,
    le crepe, i licheni."""
    t = Tela(W, H)
    for y in range(QUADRO):
        for x in range(SW):
            t.punto(x, y, strati(x * 0.5, y * 0.5 + 20, 0.22))
    r = random.Random(3)
    for _ in range(500):                                                          # la grana della pietra
        x, y = r.randrange(SW), r.randrange(QUADRO)
        if t.px[y][x] not in (G_NERA, G_P4):
            t.punto(x, y, G_P1 if r.random() < 0.6 else G_ROSA_C)
    for _ in range(6):                                                            # le crepe
        x, y = r.randrange(SW), r.randrange(QUADRO)
        for k in range(14):
            t.punto(x, y, G_C)
            x += r.choice((0, 1))
            y += 1
    for _ in range(7):
        t.ellisse(r.randrange(SW), r.randrange(QUADRO), 4, 2, G_V1)
    return t, PALETTE_GOLA, False


PITTORI = {"c7_monte": c7_monte, "c7_fronde": c7_fronde, "c7_cappella": c7_cappella,
           "c7_gola_fondo": c7_gola_fondo, "c7_gola_parete": c7_gola_parete,
           "c7_gola_torrente": c7_gola_torrente, "c7_striscia": c7_striscia}
