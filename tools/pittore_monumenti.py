#!/usr/bin/env python3
"""I monumenti disegnati in pixel, con la sola palette dei fondali (PALETTE_FONDALI di genera_mondo.py).

Ogni edificio posato dal generatore ha la sua tela: larghezza x altezza in tile, 8 pixel per tile,
vista dall'alto in 3/4 come il resto del mondo. La facciata vista di fronte sta sul lato basso
quando facciata_lato_schermo = basso (o quando il monumento ha una facciata da mostrare e il
censimento non da' il lato); sopra c'e' il tetto con la gronda; un fianco, se la facciata e' a
sinistra o a destra, e' la striscia di quel lato. Il generatore taglia la tela in tile 8x8 e li
mette in comune con il suolo dell'area: i moduli ripetuti (conci, coppi, finestre uguali) diventano
lo stesso tile.

Ogni pittore annota gli elementi che disegna (archi, portali, merli...): genera_mondo.py li
confronta con REQUISITI e rifiuta un monumento canonico a cui manca un elemento.

Indici della palette: 1 contorno, 2..5 pietra calcarea dalla piu' scura alla piu' chiara, 6..9
cotto e coppi, 10 e 11 verde, 12 e 13 cielo e acqua, 14 e 15 legno.
"""
from collections import Counter

CONTORNO, PIETRA_SCURA, PIETRA, PIETRA_CHIARA, PIETRA_LUCE = 1, 2, 3, 4, 5
COTTO_SCURO, COTTO, COTTO_CHIARO, COTTO_LUCE = 6, 7, 8, 9
VERDE_SCURO, VERDE = 10, 11
ACQUA_SCURA, ACQUA = 12, 13
LEGNO_SCURO, LEGNO = 14, 15

# Elementi che ogni monumento canonico del primo lotto deve avere sulla tela.
REQUISITI = {
    "consoli": {"finestra_arco": 6, "lesena": 5, "portale_gotico": 1, "bifora": 2, "merlatura": 1,
                "campanile_vela": 1},
    "pretorio": {"retro": 1},
    "bargello": {"portale": 1, "porta_del_morto": 1},
    "san_domenico": {"facciata_incompiuta": 1, "portale": 1},
    "basilica": {"scalinata": 1, "portale": 1},
    "teatro_romano": {"gradinate": 1},
}

# Il lato della facciata quando il censimento non lo da': i monumenti che si riconoscono dal fronte.
FACCIATA_DI_DEFAULT = {"san_domenico": "basso", "basilica": "basso"}

# Tinte della pietra: (conci, giunti, luce). Variano da monumento a monumento.
TINTE = [(PIETRA_CHIARA, PIETRA, PIETRA_LUCE), (PIETRA, PIETRA_SCURA, PIETRA_CHIARA),
         (PIETRA_LUCE, PIETRA_CHIARA, PIETRA_LUCE)]


class Tela:
    def __init__(self, w, h, fondo=COTTO):
        self.w, self.h = w * 8, h * 8
        self.px = [[fondo] * self.w for _ in range(self.h)]
        self.elementi = Counter()

    def punto(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = c

    def rett(self, x0, y0, w, h, c):
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                self.punto(x, y, c)

    def conci(self, x0, y0, w, h, tinta, passo=8):
        """Muro di conci 8x4 sfalsati, con periodo 8 pixel: si ripete per tile uguali."""
        concio, giunto, luce = tinta
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                sfalsa = 4 if (y // 4) % 2 else 0
                if y % 4 == 3 or (x + sfalsa) % passo == 7:
                    c = giunto
                elif (x + sfalsa) % passo == 0:
                    c = luce
                else:
                    c = concio
                self.punto(x, y, c)

    def coppi(self, x0, y0, w, h, scuro=COTTO_SCURO):
        """Tetto di coppi visto dall'alto: canali verticali, luce a sinistra del colmo."""
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                self.punto(x, y, scuro if y % 4 == 3 else [COTTO_LUCE, COTTO_CHIARO, COTTO, scuro][x % 4])

    def falde(self, x0, y0, w, h):
        """Tetto di un monumento: due falde di coppi con il colmo lungo l'asse lungo, la falda in
        luce piu' chiara; si distingue dai tetti piatti delle case intorno."""
        orizzontale = w >= h
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                if orizzontale:
                    luce = y - y0 < h // 2
                    colmo = abs((y - y0) - h // 2) < 1
                    canale = x % 4
                else:
                    luce = x - x0 < w // 2
                    colmo = abs((x - x0) - w // 2) < 1
                    canale = y % 4
                if colmo:
                    c = COTTO_LUCE
                elif canale == 3:
                    c = COTTO_SCURO
                else:
                    c = (COTTO_LUCE, COTTO_CHIARO, COTTO)[canale] if luce else (COTTO_CHIARO, COTTO, COTTO_SCURO)[canale]
                self.punto(x, y, c)

    def contorno(self):
        """Il bordo dell'edificio, un pixel scuro: lo stacca dalle case."""
        for x in range(self.w):
            self.punto(x, 0, CONTORNO)
        for y in range(self.h):
            self.punto(0, y, CONTORNO)
            self.punto(self.w - 1, y, CONTORNO)

    def gronda(self, x0, y, w):
        """La gronda: il bordo del tetto sopra la facciata, ombra sotto."""
        self.rett(x0, y, w, 2, COTTO_CHIARO)
        self.rett(x0, y + 2, w, 1, CONTORNO)

    def arco(self, x0, y0, w, h, vuoto=CONTORNO, cornice=PIETRA_LUCE):
        """Apertura ad arco a tutto sesto (finestra o portale)."""
        r = w // 2
        for y in range(h):
            for x in range(w):
                dx = x - (w - 1) / 2
                if y < r and dx * dx + (r - y) ** 2 > r * r:
                    continue
                bordo = x in (0, w - 1) or (y < r and dx * dx + (r - y) ** 2 > (r - 1) ** 2)
                self.punto(x0 + x, y0 + y, cornice if bordo else vuoto)

    def arco_acuto(self, x0, y0, w, h, vuoto=LEGNO_SCURO, cornice=PIETRA_LUCE):
        """Arco gotico: due archi che si incontrano in punta."""
        for y in range(h):
            for x in range(w):
                rientro = max(0, (w // 2) - (y * w) // max(1, w)) if y < w // 2 else 0
                if x < rientro or x >= w - rientro:
                    continue
                bordo = x in (rientro, w - 1 - rientro) or y == 0
                self.punto(x0 + x, y0 + y, cornice if bordo else vuoto)

    def merli(self, x0, y0, w, tinta):
        """Merlatura guelfa: denti di 4 pixel ogni 8."""
        concio, giunto, luce = tinta
        for x in range(x0, x0 + w):
            dente = (x - x0) % 8 < 4
            for y in range(y0, y0 + 8):
                if y - y0 < 4 and not dente:
                    continue
                self.punto(x, y, luce if (x - x0) % 8 == 0 else concio)
        self.rett(x0, y0 + 7, w, 1, giunto)

    def tagli(self):
        """La tela in tile 8x8, per righe di tile."""
        return [[[self.px[ty * 8 + y][tx * 8:tx * 8 + 8] for y in range(8)] for tx in range(self.w // 8)]
                for ty in range(self.h // 8)]


def altezza_facciata(h, altezza_m=None, minimo=3):
    """Righe di tile della facciata in 3/4: un terzo dell'altezza vera, entro l'impronta."""
    if altezza_m:
        return max(minimo, min(h - 3, int(round(altezza_m / 1.5 / 3))))
    return max(minimo, min(h - 3, int(round(h * 0.4))))


def tetto_e_facciata(t, w, h, fh, tinta):
    """Tetto a falde sopra, gronda, facciata di conci sotto: la base comune."""
    t.falde(0, 0, w * 8, (h - fh) * 8)
    t.gronda(0, (h - fh) * 8 - 3, w * 8)
    t.conci(0, (h - fh) * 8, w * 8, fh * 8, tinta)


# --- primo lotto -------------------------------------------------------------------------------

def consoli(w, h, info):
    """Palazzo dei Consoli: merlatura, campanile a vela, 6 finestre a tutto sesto a coppie divise da
    lesene, cornice marcapiano, portale gotico fra due bifore."""
    t = Tela(w, h)
    tinta = TINTE[0]
    fh = altezza_facciata(h, info.get("altezza_m"))
    tetto_e_facciata(t, w, h, fh, tinta)
    y0 = (h - fh) * 8
    largo = w * 8
    t.merli(0, y0, largo, tinta)
    t.elementi["merlatura"] += 1
    # campanile a vela sul tetto, verso sinistra: muro con due fornici e i suoi merli
    cx = 24
    t.conci(cx, y0 - 48, 32, 40, tinta)
    t.merli(cx, y0 - 56, 32, tinta)
    t.arco(cx + 4, y0 - 44, 10, 18)
    t.arco(cx + 18, y0 - 44, 10, 18)
    t.elementi["campanile_vela"] += 1
    # lesene: dividono la facciata in tre campate, una coppia di finestre per campata
    for k in range(6):
        x = min((largo * k) // 5 if k < 5 else largo - 4, largo - 4)
        t.rett(x, y0 + 8, 4, fh * 8 - 8, PIETRA_LUCE)
        t.rett(x + 3, y0 + 8, 1, fh * 8 - 8, PIETRA)
    t.elementi["lesena"] += 5
    # piano alto: 6 finestre a tutto sesto, a coppie
    piano = y0 + 14
    alte = max(20, (fh * 8) // 3)
    campata = largo / 3
    for c in range(3):
        mezzo = int(campata * c + campata / 2)
        for k in (-1, 1):
            t.arco(mezzo + (k * 9) - (6 if k < 0 else -3) - 3, piano, 12, alte, CONTORNO)
            t.elementi["finestra_arco"] += 1
    # cornice marcapiano
    terra = piano + alte + 4
    t.rett(0, terra - 3, largo, 3, PIETRA_LUCE)
    t.rett(0, terra, largo, 1, PIETRA_SCURA)
    # piano terra: portale gotico al centro, una bifora per lato
    alto = y0 + fh * 8 - terra - 1
    t.arco_acuto(largo // 2 - 14, terra + 1, 28, alto)
    t.elementi["portale_gotico"] += 1
    for mezzo in (largo // 4, 3 * largo // 4):
        t.arco(mezzo - 11, terra + 6, 10, alto // 2 + 6, CONTORNO)
        t.arco(mezzo + 1, terra + 6, 10, alto // 2 + 6, CONTORNO)
        t.rett(mezzo - 1, terra + 6, 2, alto // 2 + 6, PIETRA_LUCE)
        t.elementi["bifora"] += 1
    t.contorno()
    return t


def pretorio(w, h, info):
    """Pretorio: la facciata guarda a ovest, sullo schermo in alto: se ne vede il retro, tetto e muro."""
    t = Tela(w, h)
    t.falde(0, 0, w * 8, (h - 2) * 8)
    t.gronda(0, (h - 2) * 8 - 3, w * 8)
    t.conci(0, (h - 2) * 8, w * 8, 16, TINTE[1])
    t.elementi["retro"] += 1
    t.contorno()
    return t


def bargello(w, h, info):
    """Bargello: stretto e alto, frontale; il portale e accanto la porta del morto, stretta e rialzata."""
    t = Tela(w, h)
    tinta = TINTE[2]
    fh = max(5, min(h - 2, h * 6 // 10))
    tetto_e_facciata(t, w, h, fh, tinta)
    y0 = (h - fh) * 8
    largo = w * 8
    for k in range(2):
        t.arco(largo // 2 - 17 + k * 22, y0 + 6, 12, 18, CONTORNO)
    base = y0 + fh * 8
    t.arco(largo // 2 - 10, base - 22, 14, 22, LEGNO_SCURO)
    t.elementi["portale"] += 1
    t.arco(largo // 2 + 7, base - 24, 8, 16, LEGNO)
    t.rett(largo // 2 + 7, base - 8, 8, 8, PIETRA_SCURA)
    t.elementi["porta_del_morto"] += 1
    t.contorno()
    return t


def san_domenico(w, h, info):
    """San Domenico: la facciata incompiuta, muratura grezza con il bordo alto irregolare e brani di
    cotto, un portale e l'occhio."""
    t = Tela(w, h)
    tinta = TINTE[1]
    fh = altezza_facciata(h, None, 5)
    tetto_e_facciata(t, w, h, fh, tinta)
    y0 = (h - fh) * 8
    largo = w * 8
    for x in range(largo):
        dente = (x * 7 + (x // 5) * 3) % 11
        for y in range(y0, y0 + dente):
            t.punto(x, y, COTTO)
    for k in range(0, largo, 24):
        t.rett(k + 4, y0 + 16, 8, 8, COTTO_CHIARO)
    t.elementi["facciata_incompiuta"] += 1
    t.arco(largo // 2 - 6, y0 + 12, 12, 12, CONTORNO)
    base = y0 + fh * 8
    t.arco(largo // 2 - 8, base - 22, 16, 22, LEGNO_SCURO)
    t.elementi["portale"] += 1
    t.contorno()
    return t


def basilica(w, h, info):
    """Basilica di Sant'Ubaldo: in basso la scalinata larga, sopra la facciata con il portale."""
    t = Tela(w, h)
    tinta = TINTE[0]
    fh = altezza_facciata(h, None, 6)
    tetto_e_facciata(t, w, h, fh, tinta)
    largo = w * 8
    base = h * 8
    for k in range(4):
        y = base - 16 + k * 4
        t.rett(0, y, largo, 3, PIETRA_LUCE)
        t.rett(0, y + 3, largo, 1, PIETRA)
    t.elementi["scalinata"] += 1
    t.arco(largo // 2 - 8, base - 16 - 26, 16, 26, LEGNO_SCURO)
    t.elementi["portale"] += 1
    t.arco(largo // 2 - 5, (h - fh) * 8 + 8, 10, 10, CONTORNO)
    t.contorno()
    return t


def teatro_romano(w, h, info):
    """Teatro Romano: le gradinate a semicerchio sul prato, aperte verso la scena."""
    t = Tela(w, h, VERDE)
    for y in range(t.h):
        for x in range(t.w):
            if (x * 3 + y * 5) % 13 == 0:
                t.punto(x, y, VERDE_SCURO)
    cx, cy = t.w // 2, t.h - 8
    r_esterno = min(t.w // 2 - 2, t.h - 16)
    r_interno = r_esterno // 3
    for y in range(t.h):
        for x in range(t.w):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if y <= cy and r_interno <= d <= r_esterno:
                anello = int(d) % 6
                t.punto(x, y, PIETRA_LUCE if anello < 3 else (PIETRA if anello < 5 else PIETRA_SCURA))
    t.rett(cx - r_esterno, cy, 2 * r_esterno, 4, PIETRA_SCURA)
    t.elementi["gradinate"] += 1
    return t


# --- gli altri, per ruolo ------------------------------------------------------------------------

def ruolo(nome):
    n = nome.lower()
    if any(p in n for p in ("porta", "torre")):
        return "porta"
    if any(p in n for p in ("chiesa", "san ", "santa ", "sant'", "basilica", "cattedrale", "duomo", "eremo")):
        return "chiesa"
    return "palazzo"


def generico(mid, nome, w, h, faccia, n):
    """Tetto distinto e muro di pietra con la porta; tinta e tetto cambiano con il ruolo."""
    r = ruolo(nome)
    tinta = TINTE[n % len(TINTE)]
    t = Tela(w, h)
    fh = 2 if faccia != "basso" else max(2, min(h - 2, h // 3))
    if r == "porta":
        t.conci(0, 0, w * 8, h * 8, tinta)
        t.merli(0, 0, w * 8, tinta)
        t.elementi["merlatura"] += 1
    elif r == "chiesa":
        # tetto a capanna: due falde, colmo al centro dell'asse lungo
        lungo_orizzontale = w >= h
        for y in range((h - fh) * 8):
            for x in range(w * 8):
                falda = (y < (h - fh) * 4) if lungo_orizzontale else (x < w * 4)
                t.punto(x, y, COTTO_SCURO if y % 4 == 3 else ([COTTO_CHIARO, COTTO] if falda else [COTTO, COTTO_SCURO])[x % 2])
    else:
        t.falde(0, 0, w * 8, (h - fh) * 8)
    if r != "porta":
        t.gronda(0, (h - fh) * 8 - 3, w * 8)
        t.conci(0, (h - fh) * 8, w * 8, fh * 8, tinta)
    if faccia == "basso":
        largo = w * 8
        t.arco(largo // 2 - 5, h * 8 - 14, 10, 14, LEGNO_SCURO)
        t.elementi["porta"] += 1
        if r == "chiesa":
            t.arco(largo // 2 - 4, (h - fh) * 8 + 3, 8, 8, CONTORNO)
    elif faccia in ("sinistra", "destra"):
        x = 0 if faccia == "sinistra" else w * 8 - 8
        t.conci(x, 0, 8, h * 8, tinta)
        for y in range(8, h * 8 - 16, 24):
            t.arco(x + 2, y, 4, 8, CONTORNO)
        t.arco(x + 1, (h * 8) // 2 - 7, 6, 14, LEGNO_SCURO)
        t.elementi["porta"] += 1
    t.elementi["tetto_" + r] += 1
    t.contorno()
    return t


def fontana_dei_matti(w, h):
    """La Fontana dei Matti vista dall'alto: vasca di pietra, acqua, il fusto al centro."""
    t = Tela(w, h, PIETRA)
    cx, cy = t.w / 2 - 0.5, t.h / 2 - 0.5
    r = min(t.w, t.h) / 2
    for y in range(t.h):
        for x in range(t.w):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            c = PIETRA if d > r else (PIETRA_LUCE if d > r - 2 else (ACQUA if (x + y) % 5 else ACQUA_SCURA))
            if d < 3:
                c = PIETRA_CHIARA
            t.punto(x, y, c)
    t.elementi["vasca"] += 1
    return t


PITTORI = {"consoli": consoli, "pretorio": pretorio, "bargello": bargello, "san_domenico": san_domenico,
           "basilica": basilica, "teatro_romano": teatro_romano}


def dipingi(mid, nome, w, h, faccia, info, n):
    """La tela del monumento mid, larga w e alta h tile."""
    if mid in PITTORI:
        return PITTORI[mid](w, h, info)
    return generico(mid, nome, w, h, faccia, n)


def elementi_mancanti(mid, elementi):
    """Gli elementi richiesti che la tela non ha (vuoto: tutto c'e')."""
    return {k: v for k, v in REQUISITI.get(mid, {}).items() if elementi.get(k, 0) < v}
