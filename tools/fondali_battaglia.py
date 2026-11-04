#!/usr/bin/env python3
"""I fondali della battaglia allo standard grafico (/mnt/project-files/stile_dati/STANDARD_GRAFICO.md).

Prima i fondali erano un orizzonte a 76 pixel con il profilo piatto dietro, e le figure delle file alte
stavano in piedi sul cielo o sulle mura. Qui il terreno comincia a 30 pixel: tutte e tre le file poggiano
sul suolo, che scende verso chi guarda con corsi e macchie che crescono (la prospettiva). Il fondo lontano
(mura, monte, palazzo, navata, gola) sta nella fascia alta, con la luce da sinistra (L1), le ombre portate a
destra e in basso (L4), i giunti nel tono d'ombra e mai nel nero (C4, F2), i toni medi sulle superfici grandi
(C5).

Ogni fondale ha la sua palette di 16 colori, tutti della Guida: si dipinge con i riferimenti (rampa, tono) e
la palette nasce da quelli usati. Le voci 0-2 sono sempre quelle del pannello dei comandi (PANNELLO), cosi'
il pannello e' uguale in ogni scontro.

    python tools/fondali_battaglia.py tavola.png      # la tavola dei cinque fondali (serve Pillow)
"""
import os
import random
import sys

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RADICE, "stile"))

W, H = 256, 256
VISTO_W, VISTO_H = 240, 160
PANNELLO_Y = 104
ORIZZONTE = 30                    # da qui in giu' il suolo: tutte e tre le file ci poggiano

NERO = ("neutri", 0)
# le voci fisse del pannello: il fondo nero, il tratteggio, il bordo di pietra
PANNELLO = [NERO, ("legno e cuoio", 1), ("pietra calcarea", 5)]


def r(rampa, tono):
    return (rampa, tono)


PIETRA = [r("pietra calcarea", i) for i in range(6)]
COTTO = [r("cotto e coppi", i) for i in range(6)]
VERDE = [r("verde dei monti", i) for i in range(5)]
CIELO = [r("cielo e acqua", i) for i in range(5)]
LEGNO = [r("legno e cuoio", i) for i in range(4)]
ORO = [r("oro e bronzo", i) for i in range(4)]
VERMIGLIO = [r("vermiglio comunale", i) for i in range(4)]
NEUTRI = [r("neutri", i) for i in range(5)]


class Tela:
    """Una tela di riferimenti della Guida (None = non dipinto)."""

    def __init__(self):
        self.px = [[None] * W for _ in range(H)]

    def punto(self, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < VISTO_W and 0 <= y < PANNELLO_Y:
            self.px[y][x] = c

    def leggi(self, x, y):
        if 0 <= x < VISTO_W and 0 <= y < PANNELLO_Y:
            return self.px[y][x]
        return None

    def rett(self, x0, y0, w, h, c):
        for y in range(int(y0), int(y0 + h)):
            for x in range(int(x0), int(x0 + w)):
                self.punto(x, y, c)

    def ellisse(self, cx, cy, rx, ry, c):
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1:
                    self.punto(x, y, c)

    def scurisci(self, x, y, rampa_toni, passi=1):
        """Il pixel prende il tono piu' scuro di 'passi' nella sua rampa (le ombre portate, L4)."""
        c = self.leggi(x, y)
        if c is None or c == NERO:
            return
        rampa, tono = c
        self.punto(x, y, (rampa, max(0, tono - passi)) if rampa != "neutri" else c)


# --- pennelli ------------------------------------------------------------------------------------------
def cielo(t, y0, y1, toni):
    """Il cielo a fasce dal piu' scuro (in alto) al piu' chiaro, col retino solo sul passaggio (P5)."""
    n = len(toni)
    for y in range(y0, y1):
        f = (y - y0) / max(1, y1 - y0) * n
        i = min(n - 1, int(f))
        sopra = f - i > 0.75 and i + 1 < n
        for x in range(VISTO_W):
            t.punto(x, y, toni[i + 1] if sopra and (x + y) % 2 == 0 else toni[i])


def conci(t, x0, y0, w, h, toni, rng, alto=4, largo=(5, 10), luce_sx=True):
    """Un muro a conci irregolari: tre toni (ombra, base, luce), i giunti nel tono d'ombra; lo spigolo
    sinistro in luce e il destro in ombra; ogni concio ha la luce in alto a sinistra (F2)."""
    ombra, base, luce = toni
    y = y0
    corso = 0
    while y < y0 + h:
        hh = min(alto, y0 + h - y)
        x = x0 - (corso % 2) * (largo[0] // 2 + 1)
        while x < x0 + w:
            ll = rng.randint(*largo)
            tono = base if rng.random() < 0.7 else luce
            for yy in range(y, y + hh):
                for xx in range(max(x, x0), min(x + ll, x0 + w)):
                    giunto = yy == y + hh - 1 or xx == x + ll - 1
                    c = ombra if giunto else (luce if (yy == y or xx == x) and tono == base else tono)
                    t.punto(xx, yy, c)
            x += ll
        y += hh
        corso += 1
    for yy in range(y0, y0 + h):
        if luce_sx:
            t.punto(x0, yy, luce)
        t.punto(x0 + w - 1, yy, ombra)


def merli(t, x0, x1, y_base, alto, largo, vuoto, toni):
    """I merli guelfi (squadrati) sopra un muro: la faccia sinistra in luce, la destra in ombra."""
    ombra, base, luce = toni
    x = x0
    while x < x1:
        for yy in range(y_base - alto, y_base):
            for xx in range(x, min(x + largo, x1)):
                t.punto(xx, yy, luce if xx == x or yy == y_base - alto else (ombra if xx == x + largo - 1 else base))
        x += largo + vuoto


def torre(t, x0, y_cima, y_base, w, toni, rng, finestre=True):
    conci(t, x0, y_cima, w, y_base - y_cima, toni, rng, alto=3, largo=(4, 7))
    merli(t, x0 - 1, x0 + w + 1, y_cima, 3, 3, 2, toni)
    if finestre:
        fx = x0 + w // 2 - 1
        t.rett(fx, y_cima + 4, 2, 4, NERO)
        t.punto(fx + 2, y_cima + 4, toni[0])            # lo strombo a destra in ombra (F5)
    # l'ombra della torre sul muro alla sua destra (L4)
    for yy in range(y_cima + 6, y_base):
        for xx in range(x0 + w, x0 + w + 3):
            t.scurisci(xx, yy, None)


def ombra_portata_sotto(t, x0, x1, y, alto):
    """L'ombra di un muro sul suolo: una fascia sotto la base che si accorcia verso sinistra (luce da
    sinistra e dall'alto: l'ombra va a destra e in basso)."""
    for xx in range(x0, x1):
        for yy in range(y, y + alto):
            t.scurisci(xx, yy, None)


def suolo_prospettico(t, y0, y1, toni, rng, pietre=True, ciuffi=None, corsi=True):
    """Il suolo che scende verso chi guarda: corsi di lastre sempre piu' alti, o una terra battuta con
    macchie che crescono. Restano fra il secondo e il quarto tono (C5, F3)."""
    ombra, base, luce = toni
    y = y0
    h = 3
    corso = 0
    while y < y1:
        hh = min(h, y1 - y)
        if corsi:
            largo = 6 + 2 * h
            x = -(corso * 7) % largo
            x -= largo
            while x < VISTO_W:
                tono = base if rng.random() < 0.75 else luce
                ll = largo + rng.randint(-2, 2)
                for yy in range(y, y + hh):
                    for xx in range(x, x + ll):
                        if 0 <= xx < VISTO_W:
                            giunto = yy == y + hh - 1 or xx == x + ll - 1
                            t.punto(xx, yy, ombra if giunto else (luce if (yy == y or xx == x) and tono == base else tono))
                x += ll
        else:
            for yy in range(y, y + hh):
                for xx in range(VISTO_W):
                    t.punto(xx, yy, base)
            # le macchie di terra piu' chiara e piu' scura, larghe quanto la profondita'
            for _ in range(9):
                cx = rng.randint(0, VISTO_W)
                ll = rng.randint(h, 3 * h)
                yy = y + rng.randint(0, max(0, hh - 1))
                for xx in range(cx, cx + ll):
                    t.punto(xx, yy, luce if rng.random() < 0.5 else ombra)
        y += hh
        h += 1 if corso % 2 else 0
        corso += 1
    if ciuffi:
        for _ in range(ciuffi):
            cx, cy = rng.randint(2, VISTO_W - 3), rng.randint(y0 + 2, y1 - 2)
            s = 1 + (cy - y0) // 25
            ciuffo(t, cx, cy, s)


def ciuffo(t, cx, cy, s):
    """Un ciuffo d'erba: tre fili, il piu' chiaro a sinistra, l'ombra sotto a destra."""
    for k, (dx, c) in enumerate(((-1, VERDE[3]), (0, VERDE[2]), (1, VERDE[1]))):
        for dy in range(s + (1 if k == 1 else 0)):
            t.punto(cx + dx * (1 if s < 2 else 2), cy - dy, c)
    t.punto(cx + 1, cy + 1, VERDE[0])


def sasso(t, cx, cy, rx, ry, toni):
    ombra, base, luce = toni
    t.ellisse(cx, cy, rx, ry, base)
    for y in range(int(cy - ry), int(cy + ry) + 1):
        for x in range(int(cx - rx), int(cx + rx) + 1):
            if t.leggi(x, y) == base:
                if x < cx - rx / 3 and y < cy:
                    t.punto(x, y, luce)
                elif x > cx + rx / 3 or y > cy + ry / 2:
                    t.punto(x, y, ombra)
    for x in range(int(cx - rx / 2), int(cx + rx) + 2):        # l'ombra portata a destra
        t.scurisci(x, int(cy + ry) + 1, None)


def chioma(t, cx, cy, rx, ry, rng):
    """Una chioma d'albero: tre toni di verde a grumi, la luce in alto a sinistra."""
    t.ellisse(cx, cy, rx, ry, VERDE[1])
    for _ in range(int(rx * ry / 3)):
        x = cx + rng.uniform(-rx, rx)
        y = cy + rng.uniform(-ry, ry)
        if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 < 0.8:
            luce = (x - cx) / rx + (y - cy) / ry < -0.3
            ombra = (x - cx) / rx + (y - cy) / ry > 0.6
            t.ellisse(x, y, 1.6, 1.2, VERDE[3] if luce else (VERDE[0] if ombra else VERDE[2]))


# --- i cinque fondali ------------------------------------------------------------------------------------
def pattuglia(t, rng):
    """Fuori dalle mura, davanti alla porta: il monte dietro, le mura con le torri, la strada bianca."""
    cielo(t, 0, 16, [CIELO[2], CIELO[3], CIELO[4]])
    # il Monte Ingino dietro le mura, a sinistra piu' alto
    for x in range(VISTO_W):
        cima = 3 + int(9 * (x / VISTO_W) ** 1.4)
        for y in range(cima, 18):
            t.punto(x, y, VERDE[1] if (x + y) % 9 else VERDE[0])
        t.punto(x, cima, VERDE[2])
    conci(t, 0, 13, VISTO_W, ORIZZONTE - 13, (PIETRA[2], PIETRA[3], PIETRA[4]), rng, alto=3, largo=(5, 9))
    merli(t, 0, VISTO_W, 13, 3, 4, 3, (PIETRA[2], PIETRA[3], PIETRA[4]))
    for x0 in (14, 176):
        torre(t, x0, 2, ORIZZONTE, 18, (PIETRA[2], PIETRA[3], PIETRA[4]), rng)
    # la porta: l'arco a tutto sesto, il vano buio, la ghiera chiara
    cx = 112
    for y in range(14, ORIZZONTE):
        for x in range(cx - 10, cx + 11):
            dentro = y > 20 or ((x - cx) / 8.5) ** 2 + ((y - 21) / 7) ** 2 <= 1
            ghiera = (not dentro) and ((x - cx) / 10.5) ** 2 + ((y - 21) / 9) ** 2 <= 1
            if dentro and abs(x - cx) <= 8:
                t.punto(x, y, NERO if x > cx - 6 else LEGNO[0])
            elif ghiera:
                t.punto(x, y, PIETRA[4] if x < cx else PIETRA[3])
    # il suolo: prato con la strada bianca che esce dalla porta e si allarga verso chi guarda
    suolo_prospettico(t, ORIZZONTE, PANNELLO_Y, (VERDE[1], VERDE[2], VERDE[3]), rng, corsi=False, ciuffi=40)
    for y in range(ORIZZONTE, PANNELLO_Y):
        m = 9 + (y - ORIZZONTE) * 0.55
        for x in range(int(cx - m), int(cx + m)):
            bordo = x < cx - m + 2 or x > cx + m - 3
            c = PIETRA[3] if (x * 5 + y * 3) % 11 else PIETRA[2]
            t.punto(x, y, VERDE[1] if bordo and (x + y) % 2 else (PIETRA[2] if bordo else c))
    ombra_portata_sotto(t, 0, VISTO_W, ORIZZONTE, 2)
    for _ in range(7):
        sasso(t, rng.randint(6, VISTO_W - 6), rng.randint(ORIZZONTE + 8, PANNELLO_Y - 4), 2.5, 1.6,
              (PIETRA[1], PIETRA[2], PIETRA[4]))


def imboscata(t, rng):
    """Sul Monte Ingino, a una svolta degli stradoni: i monti lontani, il bosco, la ghiaia della strada."""
    cielo(t, 0, 14, [CIELO[2], CIELO[3], CIELO[4]])
    for x in range(VISTO_W):                         # i monti lontani, azzurrati
        cima = 6 + int(4 * abs(((x / 70.0) % 2) - 1)) + int(3 * abs(((x / 23.0) % 2) - 1))
        for y in range(cima, 20):
            t.punto(x, y, CIELO[1] if y > cima else CIELO[2])
    for x in range(VISTO_W):                         # il bosco sul pendio vicino
        for y in range(16, ORIZZONTE + 2):
            t.punto(x, y, VERDE[0])
    for k in range(22):
        chioma(t, k * 11 + rng.randint(-3, 3), 18 + rng.randint(-2, 4), 7, 5, rng)
    # il suolo: l'erba dei prati e la ghiaia dello stradone in diagonale
    suolo_prospettico(t, ORIZZONTE, PANNELLO_Y, (VERDE[1], VERDE[2], VERDE[3]), rng, corsi=False, ciuffi=35)
    for y in range(ORIZZONTE, PANNELLO_Y):
        p = (y - ORIZZONTE) / (PANNELLO_Y - ORIZZONTE)
        x0 = int(-30 + 150 * p)
        largo = int(70 + 70 * p)
        for x in range(x0, x0 + largo):
            bordo = x - x0 < 2 or x0 + largo - x < 3
            c = LEGNO[2] if (x * 7 + y * 13) % 5 else (LEGNO[3] if (x + y) % 3 else LEGNO[1])
            t.punto(x, y, VERDE[1] if bordo and (x + y) % 2 else (LEGNO[1] if bordo else c))
    ombra_portata_sotto(t, 0, VISTO_W, ORIZZONTE + 2, 2)
    for _ in range(6):
        sasso(t, rng.randint(6, VISTO_W - 6), rng.randint(ORIZZONTE + 8, PANNELLO_Y - 4), 3, 2,
              (PIETRA[1], PIETRA[2], PIETRA[4]))


def duello(t, rng):
    """Piazza Grande: la facciata del Palazzo dei Consoli con le bifore e il portale, il lastrico."""
    cielo(t, 0, 20, [CIELO[2], CIELO[3], CIELO[4]])
    toni = (PIETRA[2], PIETRA[3], PIETRA[4])
    x0, x1 = 40, 200
    conci(t, x0, 4, x1 - x0, ORIZZONTE - 4, toni, rng, alto=3, largo=(6, 11))
    merli(t, x0 - 2, x1 + 2, 4, 3, 4, 3, toni)
    # il campanile a vela a destra, oltre il tetto
    conci(t, 168, 0, 14, 5, toni, rng, alto=2, largo=(3, 5))
    t.rett(173, 0, 4, 3, NERO)
    # le bifore del piano nobile e il cornicione
    for x in range(x0 + 1, x1 - 1):
        t.punto(x, 12, PIETRA[4])
        t.punto(x, 13, PIETRA[2])
    for bx in range(x0 + 10, x1 - 10, 22):
        if abs(bx + 4 - 120) < 12:
            continue
        for k in (0, 5):
            t.rett(bx + k, 6, 3, 5, NERO)
            t.punto(bx + k + 3, 6, PIETRA[2])
        t.punto(bx + 4, 6, PIETRA[4])
    # il portale con la scalinata a ventaglio
    for y in range(14, ORIZZONTE - 3):
        for x in range(114, 127):
            arco = ((x - 120) / 6.5) ** 2 + ((y - 19) / 5) ** 2 <= 1 or y >= 19
            if arco:
                t.punto(x, y, NERO if x > 115 else LEGNO[0])
    for k in range(3):
        y = ORIZZONTE - 3 + k
        for x in range(110 - 3 * k, 131 + 3 * k):
            t.punto(x, y, PIETRA[4] if x < 116 else PIETRA[3])
    # ai lati la citta': i tetti di coppi
    for lato, (a, b) in enumerate(((0, x0), (x1, VISTO_W))):
        for x in range(a, b):
            colmo = 12 + (x * 3) % 7
            for y in range(colmo, ORIZZONTE):
                t.punto(x, y, COTTO[3] if (y - colmo) % 3 else COTTO[2])
            t.punto(x, colmo, COTTO[4])
        for x in range(a, b, 9):
            conci(t, x, 20, 8, ORIZZONTE - 20, toni, rng, alto=3, largo=(4, 6))
            t.rett(x + 3, 23, 2, 3, NERO)
    # il lastrico a corsi
    suolo_prospettico(t, ORIZZONTE, PANNELLO_Y, (PIETRA[2], PIETRA[3], PIETRA[4]), rng)
    ombra_portata_sotto(t, 0, VISTO_W, ORIZZONTE, 3)


def rito(t, rng):
    """Dentro la Basilica: le colonne nella penombra, le finestre alte con la luce che entra da sinistra,
    il pavimento di cotto; le macchie di luce sul pavimento cadono verso destra."""
    for y in range(0, ORIZZONTE + 2):
        for x in range(VISTO_W):
            t.punto(x, y, NEUTRI[1] if (x // 4 + y // 3) % 7 else NEUTRI[2])
    for fx in (30, 110, 190):                    # le finestre alte, la vetrata piu' chiara al centro
        for y in range(3, 18):
            for x in range(fx, fx + 12):
                arco = ((x + 0.5 - fx - 6) / 6) ** 2 + ((y + 0.5 - 9) / 6) ** 2 <= 1 or y >= 9
                if arco:
                    c = CIELO[3] if (x + y) % 4 else ORO[2]
                    t.punto(x, y, CIELO[4] if x < fx + 3 else c)
        t.rett(fx + 5, 3, 2, 15, PIETRA[1])
    for cx in range(0, VISTO_W + 40, 40):        # le colonne: luce a sinistra, ombra a destra
        for y in range(0, ORIZZONTE):
            for x in range(cx, cx + 10):
                t.punto(x, y, PIETRA[3] if x < cx + 2 else (PIETRA[1] if x > cx + 6 else PIETRA[2]))
        t.rett(cx - 1, ORIZZONTE - 3, 12, 3, PIETRA[2])
        t.rett(cx - 1, ORIZZONTE - 3, 2, 3, PIETRA[3])
    # il pavimento: le pianelle di cotto a corsi
    suolo_prospettico(t, ORIZZONTE, PANNELLO_Y, (COTTO[1], COTTO[2], COTTO[3]), rng)
    # le macchie di luce delle finestre, oblique verso destra
    for fx in (30, 110, 190):
        for y in range(ORIZZONTE + 4, PANNELLO_Y):
            d = (y - ORIZZONTE) * 0.6
            for x in range(int(fx + d), int(fx + d + 10 + d / 3)):
                c = t.leggi(x, y)
                if c is not None and c[0] == "cotto e coppi" and (x + y) % 2 == 0:
                    t.punto(x, y, ("cotto e coppi", min(4, c[1] + 1)))


def gola(t, rng):
    """La gola del Bottaccione: le pareti di scaglia a strati rossi e bianchi inclinati, la striscia nera
    del limite fra le ere, il filo di cielo, il greto col torrente."""
    cielo(t, 0, 12, [CIELO[3], CIELO[4]])
    fasce = (COTTO[2], COTTO[3], PIETRA[3], COTTO[2], PIETRA[4], PIETRA[3], COTTO[3], COTTO[1])
    for x in range(VISTO_W):
        cielo_fino = max(0, 12 - abs(x - 120) // 6)
        for y in range(cielo_fino, ORIZZONTE + 4):
            strato = (y + x // 10) // 3
            c = fasce[strato % len(fasce)]
            # luce sulla parete di sinistra, ombra su quella di destra
            if x > 140 and c[1] > 1:
                c = (c[0], c[1] - 1)
            t.punto(x, y, c)
    for x in range(VISTO_W):                        # il limite K-Pg: una riga d'argilla scura
        t.punto(x, 21 - (x // 10) % 3 + x // 40, NEUTRI[1])
    for k in range(10):                             # l'edera
        cx, cy = (k * 47 + 9) % VISTO_W, 22 + (k * 13) % 8
        t.ellisse(cx, cy, 4, 3, VERDE[1])
        t.ellisse(cx - 1, cy - 1, 2, 1, VERDE[2])
    # il greto: ghiaia, e il torrente in diagonale
    suolo_prospettico(t, ORIZZONTE, PANNELLO_Y, (PIETRA[1], PIETRA[2], PIETRA[3]), rng, corsi=False)
    for y in range(ORIZZONTE, PANNELLO_Y):
        p = (y - ORIZZONTE) / (PANNELLO_Y - ORIZZONTE)
        x0 = int(150 - 40 * p)
        for x in range(x0, x0 + 8 + int(14 * p)):
            t.punto(x, y, CIELO[3] if (x + y * 2) % 7 else CIELO[4])
        t.punto(x0 - 1, y, PIETRA[1])
    ombra_portata_sotto(t, 0, VISTO_W, ORIZZONTE + 4, 2)
    for _ in range(12):
        sasso(t, rng.randint(6, VISTO_W - 6), rng.randint(ORIZZONTE + 6, PANNELLO_Y - 4), 3, 2,
              (PIETRA[2], PIETRA[3], PIETRA[4]))


PITTORI = (pattuglia, imboscata, duello, rito, gola)


def pannello(t):
    """Il pannello in basso: fondo scuro tratteggiato e cornice di pietra chiara (voci 0, 1, 2)."""
    for y in range(PANNELLO_Y, VISTO_H):
        for x in range(VISTO_W):
            bordo = y in (PANNELLO_Y, PANNELLO_Y + 1, VISTO_H - 2, VISTO_H - 1) or x in (0, 1, VISTO_W - 2, VISTO_W - 1)
            t.px[y][x] = PANNELLO[2] if bordo else (NERO if (y + x) % 7 else PANNELLO[1])


def fondale(indice):
    """(griglia 256x256 di indici, palette di 16 riferimenti) del fondale 'indice' (0-4)."""
    t = Tela()
    PITTORI[indice](t, random.Random(1151 + indice))
    pannello(t)
    # fuori dallo schermo: sotto il pannello si ripete il suo fondo (il tremito mostra 3 righe in piu'),
    # in fondo alla mappa la prima riga del cielo (il tremito verso il basso), a destra la colonna 239
    for y in range(VISTO_H, W):
        for x in range(VISTO_W):
            t.px[y][x] = t.px[0][x] if y >= 248 else (NERO if (y + x) % 7 else PANNELLO[1])
    for y in range(H):
        for x in range(VISTO_W, W):
            t.px[y][x] = t.px[y][VISTO_W - 1 - (x - VISTO_W)]
    palette = list(PANNELLO)
    uso = {}
    for riga in t.px:
        for c in riga:
            if c is None:
                raise ValueError(f"fondale {indice}: pixel non dipinto")
            uso[c] = uso.get(c, 0) + 1
            if c not in palette:
                palette.append(c)
    # troppi colori: il tono meno usato passa al tono vicino della stessa rampa (le ombre portate e le
    # luci piccole possono cadere su toni che il resto del fondale non usa)
    while len(palette) > 16:
        raro = min(palette[len(PANNELLO):], key=lambda c: uso[c])
        vicini = [c for c in palette if c != raro and c[0] == raro[0]]
        if not vicini:
            break
        sostituto = min(vicini, key=lambda c: abs(c[1] - raro[1]))
        palette.remove(raro)
        uso[sostituto] += uso.pop(raro)
        t.px = [[sostituto if c == raro else c for c in riga] for riga in t.px]
    if len(palette) > 16:
        raise ValueError(f"fondale {PITTORI[indice].__name__}: {len(palette)} colori, al massimo 16")
    palette += [NERO] * (16 - len(palette))
    indice_di = {c: i for i, c in reversed(list(enumerate(palette)))}
    return [[indice_di[c] for c in riga] for riga in t.px], palette


def tavola(percorso):
    from PIL import Image
    import stile as S
    pal = S.carica("palette")
    out = Image.new("RGB", (VISTO_W * 2, (VISTO_H * 2 + 4) * len(PITTORI)), (255, 255, 255))
    for i in range(len(PITTORI)):
        px, palette = fondale(i)
        rgb = [S.rgb_di(S.colore(pal, rif)) for rif in palette]
        im = Image.new("RGB", (VISTO_W, VISTO_H))
        im.putdata([rgb[px[y][x]] for y in range(VISTO_H) for x in range(VISTO_W)])
        out.paste(im.resize((VISTO_W * 2, VISTO_H * 2), Image.NEAREST), (0, i * (VISTO_H * 2 + 4)))
    out.save(percorso)


if __name__ == "__main__":
    tavola(sys.argv[1] if len(sys.argv) > 1 else "fondali.png")
