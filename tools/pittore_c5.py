"""I piani di C5, Il risveglio dei Ceri (dentro A1-08, al posto della regia in prosa della cinematica 2):
di notte nella navata, i tre ceri dell'altare si accendono e dalla loro luce salgono i tre Ceri di
legno, due prismi ottagonali con le cornici d'oro e l'attributo in cima (la mitra, l'elmo con la lancia,
la fiamma), nell'ordine voluto da Cioti (4 nov): Ubaldo al centro, Giorgio a destra, Antonio a
sinistra; i tre santi davanti all'altare stanno nello stesso ordine, ognuno sotto il suo Cero. Sono
legno e luce, senza colori propri (il copione e la decisione di Cioti sulle camicie). Girano: le facce
sono strisce nei colori 13 e 14 che il passo scambia, come le gambe dei fanti di C2. La brocca di
maiolica cade e i cocci brillano; alla fine la luce scende sui tre e le armi si accendono. I tre
restano di spalle, in controluce.

Di notte le luci restano accese: le voci ACCESO della palette tengono il tono del giorno (le candele,
i Ceri, l'oro), il resto prende la rampa di notte. Dal mockup approvato (cutscene/v2, CUTM, aggiornato
la mattina del 4 nov con la regola dell'ordine).

Un pittore riceve il momento e ritorna (tela, palette, notte), come in tools/pittore_panorami.py.
"""
import math
import random

from genera_battaglia import Tela
from pennelli import ACCESO, alone, contorna, poligono

W, H = 512, 256
QUADRO = 112

# ======================================================================================================
# la navata di notte
# ======================================================================================================
PALETTE_NAVATA = [("neutri", 0), ("neutri", 0), ("pietra calcarea", 0), ("pietra calcarea", 1),
                  ("pietra calcarea", 2), ("pietra calcarea", 3), ("legno e cuoio", 0), ("legno e cuoio", 1),
                  ("legno e cuoio", 2), ("cielo e acqua", 3), ("cotto e coppi", 3, ACCESO), ("neutri", 4, ACCESO),
                  ("oro e bronzo", 2, ACCESO), ("legno e cuoio", 2, ACCESO), ("legno e cuoio", 3, ACCESO),
                  ("oro e bronzo", 3, ACCESO)]
N_BUIO, N_P0, N_P1, N_P2, N_P3 = 1, 2, 3, 4, 5
N_L0, N_L1, N_L2, N_VETRO, N_ALONE = 6, 7, 8, 9, 10
N_LUCE, N_ORO_S, N_COSTA_A, N_COSTA_B, N_ORO = 11, 12, 13, 14, 15
ALTARE = (70, 170, 80, 98)                # x0, x1, y0 (mensa), y1
CERI_X = (92, 120, 148)                   # Antonio a sinistra, Ubaldo al centro, Giorgio a destra
ATTRIBUTI = ("fiamma", "mitra", "elmo")   # l'ordine voluto da Cioti (4 nov): Ubaldo al centro o davanti,
                                          # Giorgio secondo o a destra, Antonio terzo o a sinistra
SPOSTA = {"ubaldo": 30, "giorgio": 28, "antonio": -58}   # dai disegni qui sotto alla loro posizione


def navata(t, luce=0):
    """La navata buia: le volte appena accennate, i pilastri, la finestra alta coi vetri chiari, il
    pavimento a lastre, l'altare. luce 0 spenta, 1 le candele, 2 i Ceri (il bordo verso il centro si
    accende)."""
    t.rett(0, 0, W, QUADRO, N_BUIO)
    r = random.Random(31)                                     # i conci delle navate, appena un filo (F2)
    for y0 in range(0, 98, 9):
        x = -r.randint(0, 20)
        while x < W:
            largo = r.randint(16, 26)
            if x + largo < 50 or x > 190:                     # fuori dall'abside e dall'alone dei Ceri
                t.rett(x, y0, largo - 1, 1, N_P0)
                t.rett(x, y0, 1, 8, N_P0)
            x += largo
    for y in range(QUADRO):                                   # l'abside, appena piu' chiara
        for x in range(56, 184):
            d = abs(x - 120) / 64
            if y > 10 + 18 * (1 - (1 - d * d) ** 0.5) and (d < 0.92 or (x + y) % 2):
                t.punto(x, y, N_P0)
    for x0, spigolo in ((22, 45), (195, 195)):                # i pilastri con l'arco, come solidi (L2)
        t.rett(x0, 0, 24, QUADRO, N_P0)
        verso = -2 if spigolo > x0 else 1                     # la faccia verso l'altare prende la luce
        t.rett(spigolo + verso, 0, 2, QUADRO, N_P1)
        t.rett(spigolo, 0, 1, QUADRO, N_P2 if luce else N_P1)
        for y in range(42, 98, 14):                           # i rocchi: il giunto e il filo di luce sopra
            t.rett(x0 + 2, y, 20, 1, N_BUIO)
            t.rett(x0 + 2, y + 1, 20, 1, N_P1 if luce else N_P0)
        t.rett(x0 - 2, 30, 28, 3, N_P1)
        t.rett(x0 - 2, 30, 28, 1, N_P2)                       # il capitello: la luce sopra, l'ombra sotto
        t.rett(x0, 33, 24, 1, N_BUIO)
    for x in range(22, 219):
        d = (x - 120) / 98
        y = int(12 * (1 - (1 - min(1, d * d)) ** 0.5))
        t.rett(x, y, 1, 2, N_P1)
    for (a, b) in ((108, 118), (122, 132)):                   # la bifora alta, i vetri ancora chiari
        for y in range(8, 40):
            for x in range(a, b):
                c = (a + b) / 2
                if y > 14 or (x + 0.5 - c) ** 2 + (y + 0.5 - 14) ** 2 * 0.6 < 25:
                    t.punto(x, y, N_BUIO if (y % 8 == 0 or x == int(c)) else N_VETRO)
    for y in range(98, QUADRO):                               # il pavimento a lastre, i giunti nel
        t.rett(0, y, W, 1, N_P1)                              # tono d'ombra della pietra (F3, C4)
    for y in (100, 103, 107):
        t.rett(0, y, W, 1, N_P0)
    for k in range(-14, 15):
        x0 = 120 + k * 16
        for y in range(98, QUADRO):
            t.punto(int(x0 + (x0 - 120) * (y - 98) / 18), y, N_P0)
    t.rett(0, 98, W, 1, N_BUIO)                               # l'ombra dello zoccolo sul pavimento
    # l'altare: la mensa in luce, il paliotto in ombra
    x0, x1, y0, y1 = ALTARE
    t.rett(x0 - 2, y0, x1 - x0 + 4, 3, N_P3 if luce else N_P2)
    t.rett(x0, y0 + 3, x1 - x0, y1 - y0 - 3, N_P1)
    t.rett(x0 + 6, y0 + 6, x1 - x0 - 12, y1 - y0 - 9, N_P0)
    t.rett(x0 + 46, y0 + 8, 8, 8, N_P1 if not luce else N_ORO_S)   # la croce del paliotto
    t.rett(x0 + 49, y0 + 6, 2, 12, N_P1 if not luce else N_ORO_S)


def figura(nome):
    """La sagoma di uno dei tre, nera su una tela vuota, dove l'ha disegnata il mockup (prima dello
    spostamento SPOSTA): Ubaldo con la mitra e il pastorale, Giorgio con l'elmo e la lancia, Antonio
    col cappuccio e la fascina."""
    f = Tela(W, H)
    if nome == "ubaldo":
        poligono(f, [(80, 112), (82, 96), (86, 90), (96, 90), (100, 96), (102, 112)], N_BUIO)
        f.ellisse(91, 87, 5, 5, N_BUIO)
        poligono(f, [(86, 84), (88, 75), (91, 79), (94, 75), (96, 84)], N_BUIO)      # la mitra
        f.rett(104, 70, 2, 42, N_BUIO)                                               # il pastorale
        f.ellisse(106, 69, 3, 3, N_BUIO)
        f.punto(106, 69, 0)
    elif nome == "giorgio":
        poligono(f, [(110, 112), (111, 95), (116, 89), (126, 89), (131, 95), (132, 112)], N_BUIO)
        f.ellisse(121, 85, 5, 5, N_BUIO)
        f.rett(116, 80, 10, 3, N_BUIO)                                               # l'elmo
        f.rett(134, 56, 2, 56, N_BUIO)                                               # la lancia
        poligono(f, [(133, 56), (135, 50), (137, 56)], N_BUIO)
    elif nome == "antonio":
        poligono(f, [(138, 112), (141, 94), (145, 86), (155, 86), (159, 94), (162, 112)], N_BUIO)
        poligono(f, [(144, 88), (146, 79), (150, 76), (154, 79), (156, 88)], N_BUIO)  # il cappuccio
        f.linea(140, 90, 164, 82, N_BUIO, 3)                                         # la fascina
    else:
        raise ValueError(nome)
    return f


def eroi(t, luce, armi=False):
    """I tre, di spalle in basso, guardano l'altare, ognuno sotto il suo Cero (Antonio a sinistra,
    Ubaldo al centro, Giorgio a destra). Sagome scure col filo acceso in alto."""
    figure = [(figura(n), SPOSTA[n]) for n in ("ubaldo", "giorgio", "antonio")]
    filo = {0: N_P1, 1: N_ALONE, 2: N_LUCE}[luce]
    for f, dx in figure:
        for y in range(QUADRO):
            for x in range(W):
                if f.px[y][x]:
                    t.punto(x + dx, y, N_BUIO)
                    if y > 0 and not f.px[y - 1][x] and (x + y) % 3:
                        t.punto(x + dx, y, filo)
    if armi:
        # i doni dei Ceri: la verga risplende, la lancia d'oro, il fuoco si alza
        du, dg, da = SPOSTA["ubaldo"], SPOSTA["giorgio"], SPOSTA["antonio"]
        t.rett(104 + du, 70, 2, 30, N_ORO)
        t.ellisse(106 + du, 69, 3, 3, N_ORO)
        t.punto(106 + du, 69, N_BUIO)
        t.rett(134 + dg, 56, 2, 40, N_ORO)
        poligono(t, [(133 + dg, 56), (135 + dg, 50), (137 + dg, 56)], N_LUCE)
        for k in range(14):
            w = max(1, int(4 * math.sin(math.pi * (k + 1) / 15)))
            t.rett(166 + da - w // 2 - (k % 3 == 0), 84 - k * 2, w, 2, N_ORO if k % 2 else N_ALONE)
        t.ellisse(166 + da, 86, 3, 3, N_LUCE)


def candele(t, accese):
    for cx in CERI_X:
        t.rett(cx - 4, 77, 8, 3, N_ORO_S if accese else N_L1)            # il candeliere
        t.rett(cx - 1, 74, 2, 3, N_ORO_S if accese else N_L1)
        t.rett(cx - 2, 52, 4, 22, N_P3 if accese else N_P1)               # la candela
        t.rett(cx + 1, 52, 1, 22, N_P2 if accese else N_P0)
        t.punto(cx, 51, N_BUIO)
        if accese:
            t.rett(cx - 1, 46, 2, 5, N_ORO)
            t.punto(cx, 45, N_LUCE)
            t.punto(cx, 47, N_LUCE)


def cero(t, cx, base, attributo, emerso=1.0):
    """Un Cero: due prismi ottagonali di legno uno sopra l'altro, appena rastremati verso l'alto, la
    vita stretta, le cornici d'oro, l'attributo in cima. Le facce visibili sono strisce verticali nei
    colori 13 e 14 (il passo le scambia: il Cero gira). emerso: quanto e' salito da dietro l'altare."""
    alto = 76
    cima = base - int(alto * emerso)
    prismi = ((cima + 12, cima + 42), (cima + 46, cima + 78))
    for n, (y0, y1) in enumerate(prismi):
        for y in range(y0, y1):
            f = (y - y0) / (y1 - y0)
            mezzo = 5 + n + int(1.5 * f)                                  # piu' largo in basso
            for x in range(cx - mezzo, cx + mezzo + 1):
                faccia = (x - (cx - mezzo)) * 4 // (2 * mezzo + 1)
                c = N_COSTA_A if faccia % 2 == 0 else N_COSTA_B
                if x == cx - mezzo:
                    c = N_LUCE                                       # lo spigolo verso la luce
                elif x == cx + mezzo:
                    c = N_L0
                t.punto(x, y, c)
            t.punto(cx - mezzo - 1, y, N_BUIO)
            t.punto(cx + mezzo + 1, y, N_BUIO)
        for y in (y0, y1 - 1):                                           # le cornici
            t.rett(cx - 7 - n, y, 15 + 2 * n, 1, N_ORO)
        t.rett(cx - 7 - n, y0 + 1, 15 + 2 * n, 1, N_BUIO)
    t.rett(cx - 2, prismi[0][1], 5, 4, N_L2)                             # la vita
    t.rett(cx - 1, cima + 7, 3, 5, N_L2)                                 # il pomo sotto l'attributo
    if attributo == "mitra":
        poligono(t, [(cx - 5, cima + 8), (cx - 4, cima), (cx, cima + 3), (cx + 4, cima), (cx + 5, cima + 8)], N_ORO)
        t.rett(cx - 4, cima + 6, 9, 1, N_LUCE)
        t.rett(cx, cima + 2, 1, 6, N_ORO_S)
    elif attributo == "elmo":
        t.ellisse(cx, cima + 5, 4, 4, N_ORO)
        t.rett(cx - 4, cima + 5, 9, 3, N_ORO)
        t.rett(cx - 2, cima + 5, 5, 1, N_BUIO)
        t.rett(cx + 6, cima - 8, 1, 18, N_LUCE)                          # la lancia
        poligono(t, [(cx + 5, cima - 8), (cx + 6.5, cima - 12), (cx + 8, cima - 8)], N_LUCE)
    else:
        for k in range(11):
            w = max(1, int(5 * math.sin(math.pi * (k + 1) / 12)))
            t.rett(cx - w // 2 + (1 if k in (6, 7, 8) else 0), cima + 9 - k, w, 1, N_ORO if k > 3 else N_ALONE)
        t.rett(cx - 1, cima + 5, 2, 3, N_LUCE)


def colonne_di_luce(t, larghe=False):
    for cx in CERI_X:
        w = 7 if larghe else 4
        for y in range(0, 78):
            for x in range(cx - w, cx + w + 1):
                if abs(x - cx) < w // 2 or (x + y) % 2:
                    if t.px[y][x] in (N_BUIO, N_P0, N_P1, N_P2, N_VETRO):
                        t.punto(x, y, N_ALONE if abs(x - cx) > 1 else N_LUCE)


def c5_navata(m):
    t = Tela(W, H)
    navata(t, 0)
    candele(t, False)
    eroi(t, 0)
    return t, PALETTE_NAVATA, True


def c5_accese(m):
    t = Tela(W, H)
    navata(t, 1)
    for cx in CERI_X:
        alone(t, cx, 48, 12, 10, N_ORO_S, N_ALONE)
    candele(t, True)
    colonne_di_luce(t)
    eroi(t, 1)
    return t, PALETTE_NAVATA, True


def c5_sorgono(m):
    t = Tela(W, H)
    navata(t, 2)
    alone(t, 120, 60, 70, 46, N_ORO_S, N_ALONE)
    colonne_di_luce(t, larghe=True)
    for cx, a in zip(CERI_X, ATTRIBUTI):
        cero(t, cx, ALTARE[2] + 6, a, emerso=0.55)
    x0, x1, y0, y1 = ALTARE                       # l'altare davanti ai Ceri che salgono
    t.rett(x0 - 2, y0, x1 - x0 + 4, 3, N_P3)
    t.rett(x0, y0 + 3, x1 - x0, y1 - y0 - 3, N_P1)
    t.rett(x0 + 6, y0 + 6, x1 - x0 - 12, y1 - y0 - 9, N_P0)
    eroi(t, 2)
    return t, PALETTE_NAVATA, True


def c5_ceri(m):
    t = Tela(W, H)
    navata(t, 2)
    alone(t, 120, 46, 76, 50, N_ORO_S, N_ALONE)
    for cx, a in zip(CERI_X, ATTRIBUTI):
        cero(t, cx, ALTARE[2] + 6, a)
    x0, x1, y0, y1 = ALTARE
    t.rett(x0 - 2, y0, x1 - x0 + 4, 3, N_P3)
    t.rett(x0, y0 + 3, x1 - x0, y1 - y0 - 3, N_P1)
    t.rett(x0 + 6, y0 + 6, x1 - x0 - 12, y1 - y0 - 9, N_P0)
    t.rett(x0 + 46, y0 + 8, 8, 8, N_ORO_S)
    t.rett(x0 + 49, y0 + 6, 2, 12, N_ORO_S)
    eroi(t, 2)
    return t, PALETTE_NAVATA, True


def c5_raggi(m):
    """Il piano davanti, sopra c5_ceri: in cima a ogni Cero l'attributo manda una scintilla, sopra
    ciascun santo scende una pioggia di luce e le armi si accendono. Il resto e' trasparente."""
    t = Tela(W, H)
    r = random.Random(21)
    for cx, sx in zip(CERI_X, (92, 121, 149)):
        for d in range(2, 7):                                         # la scintilla dell'attributo
            for dx, dy in ((d, 0), (-d, 0), (0, d), (0, -d)):
                t.punto(cx + dx, ALTARE[2] + 6 - 76 + 4 + dy, N_LUCE if d < 4 else N_ORO)
        for _ in range(40):                                           # la pioggia di luce sul santo
            x = int(r.gauss(sx, 4))
            y = int(r.uniform(14, 84))
            t.punto(x, y, N_ORO if r.random() < 0.6 else N_LUCE)
    eroi(t, 2, armi=True)
    for y in range(QUADRO):
        for x in range(W):
            if t.px[y][x] in (N_BUIO, N_P1):
                t.px[y][x] = 0
            elif t.px[y][x] == N_LUCE and y > 84:
                t.px[y][x] = N_ORO                                     # il filo dei santi diventa d'oro
    return t, PALETTE_NAVATA, True


PALETTE_BROCCA = [("neutri", 0), ("neutri", 0), ("pietra calcarea", 0), ("pietra calcarea", 1),
                  ("pietra calcarea", 2), ("pietra calcarea", 4), ("neutri", 4, ACCESO), ("neutri", 3, ACCESO),
                  ("cielo e acqua", 1, ACCESO), ("cielo e acqua", 2, ACCESO), ("verde dei monti", 2, ACCESO),
                  ("vermiglio comunale", 2, ACCESO), ("oro e bronzo", 2, ACCESO), ("cotto e coppi", 4, ACCESO),
                  ("oro e bronzo", 1, ACCESO), ("oro e bronzo", 3, ACCESO)]
B_BUIO, B_P0, B_P1, B_P2, B_P4, B_BIANCO, B_BIANCO_S = 1, 2, 3, 4, 5, 6, 7
B_BLU, B_AZZURRO, B_VERDE, B_RUBINO, B_ORO_S, B_ALONE, B_LUSTRO_S, B_ORO = 8, 9, 10, 11, 12, 13, 14, 15


def disegna_brocca(t, ox, oy):
    """La brocca di maiolica di Gubbio: il corpo bianco con le fasce blu e verdi, il lustro d'oro e di
    rubino, l'ansa e il beccuccio. 28x40 a partire da (ox, oy)."""
    for y in range(40):
        for x in range(28):
            if y < 8:
                w = 4 + (8 - y) // 3                                     # il collo che si apre
            else:
                w = int(12 * math.sin(math.pi * (y - 4) / 40)) + 2
            if abs(x - 14) <= w:
                c = B_BIANCO if x - 14 < w // 2 else B_BIANCO_S
                if y in (12, 13, 30, 31):
                    c = B_BLU
                elif 17 <= y <= 25:
                    c = B_ORO if (x + y // 2) % 6 < 3 else B_RUBINO
                    if abs(x - 14) == w:
                        c = B_LUSTRO_S
                elif y in (14, 28):
                    c = B_VERDE
                t.punto(ox + x, oy + y, c)
    t.rett(ox + 6, oy, 16, 2, B_BLU)
    poligono(t, [(ox + 4, oy + 1), (ox - 2, oy - 2), (ox + 5, oy + 4)], B_BIANCO)   # il beccuccio
    for k in range(14):                                                           # l'ansa
        a = math.pi * k / 13
        t.rett(ox + 26 + int(5 * math.sin(a)), oy + 4 + int(10 * (1 - math.cos(a))), 2, 2, B_BIANCO_S)
    contorna(t, B_BUIO)


def piano_altare(t):
    t.rett(0, 0, W, QUADRO, B_BUIO)
    for y in range(QUADRO):                                                      # il bagliore dei Ceri
        for x in range(W):
            d = math.hypot((x - 40) * 0.7, y + 10)
            if d < 50:
                t.punto(x, y, B_P1 if d < 34 or (x + y) % 2 else B_P0)
            elif d < 80:
                t.punto(x, y, B_P0 if d < 70 or (x + y) % 2 else B_BUIO)
    t.rett(0, 70, W, 4, B_P4)                                                    # la mensa dell'altare
    t.rett(0, 74, W, 1, B_P2)
    t.rett(0, 75, W, QUADRO - 75, B_P0)
    for x in range(0, W, 23):
        t.rett(x, 75, 1, QUADRO - 75, B_BUIO)


def c5_brocca(m):
    t = Tela(W, H)
    piano_altare(t)
    b = Tela(W, H)
    disegna_brocca(b, 40, 20)
    # la brocca inclinata sul bordo della mensa: ruotata a 25 gradi col piede sullo spigolo
    a = math.radians(25)
    px0, py0 = 54, 61
    for y in range(QUADRO):
        for x in range(W):
            u = (x - 128) * math.cos(a) + (y - 69) * math.sin(a) + px0
            v = -(x - 128) * math.sin(a) + (y - 69) * math.cos(a) + py0
            ui, vi = int(round(u)), int(round(v))
            if 0 <= ui < W and 0 <= vi < H and b.px[vi][ui]:
                t.punto(x, y, b.px[vi][ui])
    return t, PALETTE_BROCCA, True


def c5_cocci(m):
    t = Tela(W, H)
    piano_altare(t)
    r = random.Random(12)
    colori = [B_BIANCO, B_BIANCO_S, B_BLU, B_ORO, B_VERDE, B_RUBINO, B_BIANCO]
    for _ in range(26):                                                           # i cocci sul pavimento
        cx, cy = r.gauss(124, 34), r.uniform(84, 108)
        s = r.uniform(2, 6)
        pts = [(cx + s * math.cos(k * 2.1 + r.random()), cy + 0.6 * s * math.sin(k * 2.1 + r.random())) for k in range(3)]
        poligono(t, pts, r.choice(colori))
    for _ in range(12):                                                           # i cocci brillano
        cx, cy = int(r.gauss(124, 30)), int(r.uniform(82, 106))
        for d in range(1, 4):
            for dx, dy in ((d, 0), (-d, 0), (0, d), (0, -d)):
                t.punto(cx + dx, cy + dy, B_ORO if d < 3 else B_ALONE)
        t.punto(cx, cy, B_BIANCO)
    return t, PALETTE_BROCCA, True


# i Ceri girano: le facce nei colori 13 e 14 si scambiano (src/regia.cpp)
CON_PASSO = {"c5_ceri"}
PITTORI = {"c5_navata": c5_navata, "c5_accese": c5_accese, "c5_sorgono": c5_sorgono, "c5_ceri": c5_ceri,
           "c5_raggi": c5_raggi, "c5_brocca": c5_brocca, "c5_cocci": c5_cocci}
