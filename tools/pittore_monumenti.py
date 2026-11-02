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
        return PITTORI[mid](w, h, dict(info, faccia=faccia))
    return generico(mid, nome, w, h, faccia, n)


def elementi_mancanti(mid, elementi):
    """Gli elementi richiesti che la tela non ha (vuoto: tutto c'e')."""
    return {k: v for k, v in REQUISITI.get(mid, {}).items() if elementi.get(k, 0) < v}


def facciata_di_lato(t, w, h, lato, tinta, larga=3):
    """Tetto a falde e, sul lato sinistro o destro, la facciata vista di scorcio: una striscia di conci
    larga 'larga' tile. Ritorna (x0, larghezza in pixel) della striscia."""
    t.falde(0, 0, w * 8, h * 8)
    x0 = 0 if lato == "sinistra" else (w - larga) * 8
    t.conci(x0, 0, larga * 8, h * 8, tinta)
    t.rett(x0 + (larga * 8 - 2 if lato == "sinistra" else 0), 0, 2, h * 8, COTTO_CHIARO)
    return x0, larga * 8


def solo_retro(t, w, h, tinta):
    """La facciata guarda in alto: si vedono il tetto e il muro di dietro."""
    t.falde(0, 0, w * 8, (h - 2) * 8)
    t.gronda(0, (h - 2) * 8 - 3, w * 8)
    t.conci(0, (h - 2) * 8, w * 8, 16, tinta)
    t.elementi["retro"] += 1


# --- secondo lotto -----------------------------------------------------------------------------

def rosone(t, cx, cy, r):
    """Il rosone: cerchio di pietra con i raggi."""
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if d <= r:
                raggio = (x - cx) * (y - cy) == 0 or abs(x - cx) == abs(y - cy)
                t.punto(x, y, PIETRA_LUCE if d > r - 1.5 or raggio else CONTORNO)


def duomo(w, h, info):
    """Duomo: facciata semplice con il portale a sesto acuto e il rosone sopra. La facciata guarda la
    via in salita: di fronte in basso, o di scorcio a sinistra o a destra."""
    t = Tela(w, h)
    tinta = TINTE[1]
    faccia = info.get("faccia", "basso")
    if faccia == "alto":
        solo_retro(t, w, h, tinta)
        t.contorno()
        return t
    if faccia in ("sinistra", "destra"):
        x0, larga = facciata_di_lato(t, w, h, faccia, tinta)
        mezzo = h * 8 // 2
        t.arco_acuto(x0 + larga // 2 - 8, mezzo, 16, 24)
        rosone(t, x0 + larga // 2, mezzo - 14, 7)
    else:
        fh = altezza_facciata(h, None, 6)
        tetto_e_facciata(t, w, h, fh, tinta)
        largo, base = w * 8, h * 8
        t.arco_acuto(largo // 2 - 10, base - 28, 20, 28)
        rosone(t, largo // 2, (h - fh) * 8 + 14, 8)
    t.elementi["portale_acuto"] += 1
    t.elementi["rosone"] += 1
    t.contorno()
    return t


def ducale(w, h, info):
    """Palazzo Ducale: dall'alto il cortile rinascimentale, con il portico su quattro lati."""
    t = Tela(w, h)
    t.falde(0, 0, w * 8, (h - 2) * 8)
    t.gronda(0, (h - 2) * 8 - 3, w * 8)
    t.conci(0, (h - 2) * 8, w * 8, 16, TINTE[2])
    cw, ch = (w * 8) * 2 // 5, (h * 8) * 2 // 5
    cx0, cy0 = (w * 8 - cw) // 2, (h * 8 - ch) // 2
    t.rett(cx0 - 3, cy0 - 3, cw + 6, ch + 6, CONTORNO)
    t.conci(cx0, cy0, cw, ch, (PIETRA_LUCE, PIETRA_CHIARA, PIETRA_LUCE))
    for x in range(cx0, cx0 + cw - 6, 8):
        t.arco(x + 1, cy0, 6, 6, PIETRA_SCURA)
        t.arco(x + 1, cy0 + ch - 6, 6, 6, PIETRA_SCURA)
    for y in range(cy0 + 8, cy0 + ch - 8, 8):
        t.arco(cx0, y, 6, 6, PIETRA_SCURA)
        t.arco(cx0 + cw - 6, y, 6, 6, PIETRA_SCURA)
    t.elementi["cortile"] += 1
    t.contorno()
    return t


def san_francesco(w, h, info):
    """San Francesco: la facciata guarda in alto, se ne vede il retro: il tetto a capanna e l'abside
    semicircolare, verso est (in basso)."""
    t = Tela(w, h)
    t.falde(0, 0, w * 8, h * 8 - 16)
    raggio = min(w * 8 // 3, 20)
    cx, cy = w * 8 // 2, h * 8 - 16
    t.rett(0, cy, w * 8, 16, COTTO)
    t.conci(0, cy, w * 8, 16, TINTE[0])
    for y in range(cy - raggio, cy + 1):
        for x in range(cx - raggio, cx + raggio + 1):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if d <= raggio:
                spicchio = int((x - cx + raggio) / 4) % 2
                t.punto(x, y, CONTORNO if d > raggio - 1 else (COTTO_CHIARO if spicchio else COTTO))
    t.elementi["abside"] += 1
    t.elementi["retro"] += 1
    t.contorno()
    return t


def loggia_tiratori(w, h, info):
    """Loggia dei Tiratori della Lana: sopra il colonnato, la loggia con le sue arcate; il fianco
    destro e' il lato che si vede."""
    t = Tela(w, h)
    t.falde(0, 0, w * 8, (h - 4) * 8)
    t.gronda(0, (h - 4) * 8 - 3, w * 8)
    y0 = (h - 4) * 8
    t.conci(0, y0, w * 8, 32, TINTE[0])
    for x in range(2, w * 8 - 12, 12):
        t.arco(x, y0 + 2, 10, 14, LEGNO_SCURO)
        t.elementi["arcata"] += 1
    t.rett(0, y0 + 17, w * 8, 2, PIETRA_LUCE)
    x = w * 8 - 8
    t.conci(x, 0, 8, h * 8, TINTE[0])
    t.arco(x + 1, (h * 8) // 2 - 7, 6, 14, LEGNO_SCURO)
    t.elementi["fianco"] += 1
    t.contorno()
    return t


def sant_agostino(w, h, info):
    """Sant'Agostino: facciata semplice a capanna, portale e occhio; se guarda in alto (a ovest, verso
    il piazzale) se ne vede il retro."""
    t = Tela(w, h)
    if info.get("faccia", "basso") == "alto":
        solo_retro(t, w, h, TINTE[2])
        t.contorno()
        return t
    fh = altezza_facciata(h, None, 5)
    tetto_e_facciata(t, w, h, fh, TINTE[2])
    largo, base = w * 8, h * 8
    t.arco(largo // 2 - 7, base - 22, 14, 22, LEGNO_SCURO)
    t.elementi["portale"] += 1
    t.arco(largo // 2 - 4, (h - fh) * 8 + 8, 8, 8, CONTORNO)
    t.contorno()
    return t


def san_pietro(w, h, info):
    """San Pietro: la facciata dell'abbazia con le arcate cieche e il portale, verso la piazza: di
    fronte in basso o di scorcio a sinistra o a destra."""
    t = Tela(w, h)
    faccia = info.get("faccia", "basso")
    if faccia in ("sinistra", "destra"):
        x0, larga = facciata_di_lato(t, w, h, faccia, TINTE[1])
        passo = h * 8 // 6
        for k in range(1, 6):
            if k == 3:
                t.arco(x0 + 3, k * passo, larga - 6, passo, LEGNO_SCURO)
                t.elementi["portale"] += 1
            else:
                t.arco(x0 + 5, k * passo + 2, larga - 10, passo - 4, PIETRA_SCURA)
                t.elementi["arcata_cieca"] += 1
        t.contorno()
        return t
    fh = altezza_facciata(h, None, 6)
    tetto_e_facciata(t, w, h, fh, TINTE[1])
    largo, base = w * 8, h * 8
    passo = largo // 5
    for k in range(5):
        if k == 2:
            continue
        t.arco(k * passo + 3, base - 26, passo - 6, 22, PIETRA_SCURA)
        t.elementi["arcata_cieca"] += 1
    t.arco(2 * passo + 1, base - 30, passo - 2, 30, LEGNO_SCURO)
    t.elementi["portale"] += 1
    t.contorno()
    return t


def porta(w, h, info):
    """Una porta delle mura: torre di conci con i merli e il fornice ad arco."""
    t = Tela(w, h, PIETRA)
    tinta = TINTE[1]
    t.conci(0, 0, w * 8, h * 8, tinta)
    t.merli(0, 0, w * 8, tinta)
    t.elementi["merlatura"] += 1
    largo, alto = w * 8, h * 8
    if largo >= alto:
        t.arco(largo // 2 - 6, alto - 16, 12, 16, CONTORNO)
    else:
        t.arco(largo // 2 - min(6, largo // 2 - 1), alto // 2 - 8, min(12, largo - 2), 16, CONTORNO)
    t.elementi["fornice"] += 1
    t.contorno()
    return t


PITTORI.update({"duomo": duomo, "ducale": ducale, "san_francesco": san_francesco,
                "loggia_tiratori": loggia_tiratori, "sant_agostino": sant_agostino, "san_pietro": san_pietro,
                "porta_metauro": porta, "porta_romana": porta})
REQUISITI.update({
    "duomo": {"portale_acuto": 1, "rosone": 1},
    "ducale": {"cortile": 1},
    "san_francesco": {"abside": 1, "retro": 1},
    "loggia_tiratori": {"arcata": 6, "fianco": 1},
    "sant_agostino": {"portale": 1},
    "san_pietro": {"portale": 1, "arcata_cieca": 4},
    "porta_metauro": {"merlatura": 1, "fornice": 1},
    "porta_romana": {"merlatura": 1, "fornice": 1},
})
FACCIATA_DI_DEFAULT.update({"duomo": "basso", "sant_agostino": "basso", "san_pietro": "basso"})


# --- terzo lotto -------------------------------------------------------------------------------

def san_marziale(w, h, info):
    """San Marziale (in origine Sant'Andrea): chiesetta romanica, tetto a capanna, campanile a vela e
    portale."""
    t = Tela(w, h)
    fh = altezza_facciata(h, None, 4)
    tetto_e_facciata(t, w, h, fh, TINTE[0])
    largo, base = w * 8, h * 8
    t.conci(largo // 2 - 8, (h - fh) * 8 - 20, 16, 18, TINTE[0])
    t.arco(largo // 2 - 4, (h - fh) * 8 - 17, 8, 10)
    t.elementi["campanile_vela"] += 1
    t.arco(largo // 2 - 6, base - 18, 12, 18, LEGNO_SCURO)
    t.elementi["portale"] += 1
    t.contorno()
    return t


def santa_maria_nuova(w, h, info):
    """Santa Maria Nuova: chiesa semplice, tetto a capanna, portale ad arco e una monofora."""
    t = Tela(w, h)
    fh = altezza_facciata(h, None, 4)
    tetto_e_facciata(t, w, h, fh, TINTE[1])
    largo, base = w * 8, h * 8
    t.arco(largo // 2 - 6, base - 18, 12, 18, LEGNO_SCURO)
    t.elementi["portale"] += 1
    t.arco(largo // 2 - 2, (h - fh) * 8 + 5, 4, 10, CONTORNO)
    t.elementi["monofora"] += 1
    t.contorno()
    return t


def capitano_popolo(w, h, info):
    """Palazzo del Capitano del Popolo: blocco gotico di pietra, merlato, con le finestre ad arco
    acuto e il portale."""
    t = Tela(w, h)
    tinta = TINTE[1]
    fh = altezza_facciata(h, None, 4)
    tetto_e_facciata(t, w, h, fh, tinta)
    y0 = (h - fh) * 8
    largo, base = w * 8, h * 8
    t.merli(0, y0, largo, tinta)
    t.elementi["merlatura"] += 1
    for k in range(3):
        t.arco_acuto(8 + k * (largo - 16) // 3, y0 + 10, 8, 12, CONTORNO)
        t.elementi["finestra_acuta"] += 1
    t.arco(largo // 2 - 6, base - 16, 12, 16, LEGNO_SCURO)
    t.elementi["portale"] += 1
    t.contorno()
    return t


def ranghiasci(w, h, info):
    """Palazzo Ranghiasci-Brancaleoni: la facciata neoclassica guarda a sud, cioe' a sinistra: una
    lunga fila regolare di finestre rettangolari e il portone al centro."""
    t = Tela(w, h)
    faccia = info.get("faccia") if info.get("faccia") in ("sinistra", "destra") else "sinistra"
    x0, larga = facciata_di_lato(t, w, h, faccia, TINTE[2], 2)
    for y in range(8, h * 8 - 8, 12):
        t.rett(x0 + 4, y, larga - 8, 7, CONTORNO)
        t.rett(x0 + 4, y + 7, larga - 8, 1, PIETRA_LUCE)
        t.elementi["finestra_regolare"] += 1
    t.rett(x0 + 2, h * 8 // 2 - 8, larga - 4, 16, LEGNO_SCURO)
    t.elementi["portone"] += 1
    t.contorno()
    return t


def sant_ambrogio(w, h, info):
    """Eremo di Sant'Ambrogio: muri di pietra addossati alla roccia della gola, tetto basso, la
    cappella con la porta."""
    t = Tela(w, h, PIETRA_SCURA)
    for y in range(t.h):
        for x in range(t.w):
            if (x * 5 + y * 3) % 9 == 0:
                t.punto(x, y, CONTORNO)
    fh = max(2, h // 3)
    t.falde(8, 8, w * 8 - 16, (h - fh) * 8 - 8)
    t.elementi["roccia"] += 1
    t.conci(8, (h - fh) * 8, w * 8 - 16, fh * 8, TINTE[1])
    t.arco(w * 4 - 5, h * 8 - 14, 10, 14, LEGNO_SCURO)
    t.elementi["porta"] += 1
    t.contorno()
    return t


PITTORI.update({"san_marziale": san_marziale, "santa_maria_nuova": santa_maria_nuova,
                "capitano_popolo": capitano_popolo, "ranghiasci": ranghiasci, "sant_ambrogio": sant_ambrogio})
REQUISITI.update({
    "san_marziale": {"campanile_vela": 1, "portale": 1},
    "santa_maria_nuova": {"portale": 1, "monofora": 1},
    "capitano_popolo": {"merlatura": 1, "finestra_acuta": 3, "portale": 1},
    "ranghiasci": {"finestra_regolare": 10, "portone": 1},
    "sant_ambrogio": {"roccia": 1, "porta": 1},
    # la facciata di Sant'Agostino guarda a ovest, in alto: se ne vede il retro
    "sant_agostino": {"retro": 1},
})
FACCIATA_DI_DEFAULT.update({"san_marziale": "basso", "santa_maria_nuova": "basso", "capitano_popolo": "basso",
                            "sant_ambrogio": "basso"})


# --- la citta': porte, pozzi, Teatro con la sua forma, ritocchi ai monumenti delle piazze ---------

def porta_della_citta(w, h, lato):
    """Una porta della citta' vista dall'alto: la torre di conci a cavallo del varco, con i merli sul
    lato di fuori e l'arco sopra il passaggio. w x h tile nell'orientamento dello schermo; il lato e'
    quello del varco (il fuori)."""
    lungo = w if lato in ("alto", "basso") else h
    base = Tela(lungo, 3, PIETRA)
    tinta = TINTE[1]
    base.conci(0, 0, lungo * 8, 24, tinta)
    # i merli sul bordo di fuori (riga 2 nel riferimento canonico, quello del varco in basso)
    for x in range(lungo * 8):
        if (x // 4) % 2 == 0:
            base.rett(x, 20, 1, 4, PIETRA_LUCE)
    base.rett(0, 19, lungo * 8, 1, CONTORNO)
    base.elementi["merlatura"] += 1
    # l'arco: sopra il passaggio (fra i piloni da 2 tile), nella riga verso dentro
    largo = (lungo - 4) * 8
    for x in range(largo):
        for y in range(8):
            dx = (x - largo / 2 + 0.5) / (largo / 2)
            curva = int(6 * (1 - dx * dx) ** 0.5)
            px = 16 + x
            if y >= 7 - curva:
                base.punto(px, y, CONTORNO if y > 7 - curva else PIETRA_LUCE)
            else:
                base.punto(px, y, PIETRA_CHIARA)
    base.elementi["arco"] += 1
    t = Tela(w, h, PIETRA)
    t.elementi = base.elementi
    for y in range(3 * 8):
        for x in range(lungo * 8):
            c = base.px[y][x]
            if lato == "basso":
                t.punto(x, y, c)
            elif lato == "alto":
                t.punto(x, 23 - y, c)
            elif lato == "sinistra":
                t.punto(23 - y, x, c)
            else:
                t.punto(y, x, c)
    return t


def pozzo(w, h):
    """Un pozzo di pietra visto dall'alto: la vera tonda, l'acqua scura, la carrucola."""
    t = Tela(w, h, PIETRA)
    cx, cy = t.w / 2 - 0.5, t.h / 2 - 0.5
    for y in range(t.h):
        for x in range(t.w):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if d <= t.w / 2 - 1:
                t.punto(x, y, PIETRA_LUCE if d > t.w / 2 - 4 else ACQUA_SCURA)
    t.rett(1, int(cy), t.w - 2, 2, LEGNO)
    t.elementi["pozzo"] += 1
    return t


def teatro_romano(w, h, info):
    """Teatro Romano, con la stessa forma della griglia (geometria_teatro di genera_mondo.py): scena
    sul bordo sinistro, orchestra a semicerchio, gradinate concentriche, l'anello esterno di arcate di
    pietra, il prato intorno. Si dipinge tile per tile con pochi motivi, cosi' i tile unici restano
    pochi anche con la cavea grande."""
    t = Tela(w, h, VERDE)
    cx, cy = 2.0, h / 2 - 0.5
    r = min(w - 3, h / 2 - 1)
    r_int = r / 3

    def prato(x0, y0):
        for y in range(8):
            for x in range(8):
                t.punto(x0 + x, y0 + y, VERDE_SCURO if (x * 3 + y * 5) % 13 == 0 else VERDE)

    for ty in range(h):
        for tx in range(w):
            x0, y0 = tx * 8, ty * 8
            d = ((tx - cx) ** 2 + (ty - cy) ** 2) ** 0.5
            if tx < cx:
                if abs(ty - cy) <= r:
                    # la fronte della scena: conci con le nicchie a tile alterni
                    for y in range(8):
                        for x in range(8):
                            t.punto(x0 + x, y0 + y, PIETRA_CHIARA if x < 6 else PIETRA)
                    if ty % 3 == 0:
                        t.rett(x0 + 2, y0 + 2, 3, 5, CONTORNO)
                else:
                    prato(x0, y0)
            elif d <= r_int:
                for y in range(8):
                    for x in range(8):
                        t.punto(x0 + x, y0 + y, PIETRA_CHIARA if (x + y) % 9 == 0 else PIETRA_LUCE)
            elif d <= r - 1.5:
                # un gradino per anello: alzata chiara e pedata in ombra, alternati
                chiaro = int(d) % 2 == 0
                for y in range(8):
                    for x in range(8):
                        t.punto(x0 + x, y0 + y, (PIETRA_LUCE if chiaro else PIETRA) if (x + y) % 8 < 5
                                else PIETRA_SCURA)
            elif d <= r:
                # l'anello di arcate: un arco per tile
                for y in range(8):
                    for x in range(8):
                        t.punto(x0 + x, y0 + y, PIETRA)
                t.rett(x0 + 2, y0 + 3, 4, 5, CONTORNO)
                t.rett(x0 + 3, y0 + 2, 2, 1, CONTORNO)
            else:
                prato(x0, y0)
    t.elementi["gradinate"] += 1
    t.elementi["arcate"] += 1
    t.elementi["scena"] += 1
    return t


def san_francesco(w, h, info):
    """San Francesco: la facciata guarda la piazza (in alto), con il portale, il rosone e il campanile
    al fianco; il tetto a capanna e, in fondo, l'abside semicircolare."""
    t = Tela(w, h)
    t.falde(0, 24, w * 8, h * 8 - 40)
    t.conci(0, 0, w * 8, 24, TINTE[0])
    t.rett(0, 22, w * 8, 2, COTTO_CHIARO)
    largo = w * 8
    t.arco(largo // 2 - 6, 6, 12, 18, LEGNO_SCURO)
    t.elementi["portale"] += 1
    rosone(t, largo // 2, 4, 3)
    t.elementi["facciata"] += 1
    # il campanile, a destra della facciata, alto sopra il tetto
    t.conci(largo - 24, 0, 20, 48, TINTE[1])
    t.merli(largo - 24, 0, 20, TINTE[1])
    t.arco(largo - 18, 14, 8, 10)
    t.elementi["campanile"] += 1
    raggio = min(largo // 3, 20)
    cx, cy = largo // 2, h * 8 - 16
    t.conci(0, cy, largo, 16, TINTE[0])
    for y in range(cy - raggio, cy + 1):
        for x in range(cx - raggio, cx + raggio + 1):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if d <= raggio:
                spicchio = int((x - cx + raggio) / 4) % 2
                t.punto(x, y, CONTORNO if d > raggio - 1 else (COTTO_CHIARO if spicchio else COTTO))
    t.elementi["abside"] += 1
    t.contorno()
    return t


def loggia_tiratori(w, h, info):
    """Loggia dei Tiratori della Lana: in basso il portico dell'antico ospedale di Santa Maria della
    Misericordia, sopra la lunga loggia di legno dove si stendevano i panni; il fianco destro e' il
    lato che si vede."""
    t = Tela(w, h)
    t.falde(0, 0, w * 8, (h - 6) * 8)
    t.gronda(0, (h - 6) * 8 - 3, w * 8)
    y0 = (h - 6) * 8
    t.conci(0, y0, w * 8, 48, TINTE[0])
    # la loggia: pilastrini di legno e il vuoto del loggiato
    for x in range(2, w * 8 - 8, 8):
        t.rett(x, y0 + 2, 6, 14, CONTORNO)
        t.rett(x + 6, y0 + 2, 2, 14, LEGNO)
        t.elementi["arcata"] += 1
    t.rett(0, y0 + 16, w * 8, 3, LEGNO)
    # l'ospedale sotto: portico ad archi di pietra
    for x in range(4, w * 8 - 16, 16):
        t.arco(x, y0 + 22, 12, 24, PIETRA_SCURA)
    t.elementi["ospedale"] += 1
    x = w * 8 - 8
    t.conci(x, 0, 8, h * 8, TINTE[0])
    t.arco(x + 1, (h * 8) // 2 - 7, 6, 14, LEGNO_SCURO)
    t.elementi["fianco"] += 1
    t.contorno()
    return t


_san_pietro_base = san_pietro


def san_pietro(w, h, info):
    """San Pietro: la facciata con le arcate cieche romaniche e il portale verso la piazza, e il
    campanile sul fianco."""
    t = _san_pietro_base(w, h, info)
    largo = w * 8
    x0 = largo - 28
    t.conci(x0, 8, 20, 40, TINTE[1])
    t.merli(x0, 0, 20, TINTE[1])
    t.arco(x0 + 6, 16, 8, 12)
    t.elementi["campanile"] += 1
    t.contorno()
    return t


PITTORI.update({"teatro_romano": teatro_romano, "san_francesco": san_francesco,
                "loggia_tiratori": loggia_tiratori, "san_pietro": san_pietro})
REQUISITI.update({
    "teatro_romano": {"gradinate": 1, "arcate": 1, "scena": 1},
    "san_francesco": {"facciata": 1, "portale": 1, "campanile": 1, "abside": 1},
    "loggia_tiratori": {"arcata": 6, "ospedale": 1, "fianco": 1},
    "san_pietro": {"portale": 1, "arcata_cieca": 4, "campanile": 1},
})


# --- il Monte e la Basilica: cappellette, chiostro, interno -----------------------------------------

def cappelletta(w, h):
    """Una cappelletta degli stradoni vista dall'alto: il tettuccio di coppi a capanna, la fronte di
    pietra con l'arco dell'edicola e la croce sul colmo."""
    t = Tela(w, h)
    t.falde(0, 0, w * 8, h * 8 - 10)
    t.conci(0, h * 8 - 10, w * 8, 10, TINTE[0])
    t.arco(w * 4 - 4, h * 8 - 10, 8, 10, CONTORNO)
    t.rett(w * 4 - 1, 1, 2, 6, PIETRA_LUCE)
    t.rett(w * 4 - 3, 3, 6, 2, PIETRA_LUCE)
    t.elementi["edicola"] += 1
    t.elementi["croce"] += 1
    t.contorno()
    return t


def altare(w, h):
    """L'altare maggiore con l'urna di vetro del santo sopra: mensa di marmo, l'urna al centro."""
    t = Tela(w, h, PIETRA_LUCE)
    t.rett(0, 0, w * 8, 2, PIETRA)
    t.rett(0, h * 8 - 2, w * 8, 2, PIETRA_SCURA)
    x0, largo = w * 2, w * 4
    t.rett(x0, 3, largo, h * 8 - 7, CONTORNO)
    t.rett(x0 + 1, 4, largo - 2, h * 8 - 9, ACQUA)
    t.rett(x0 + 3, h * 4 - 2, largo - 6, 3, COTTO_LUCE)
    t.elementi["mensa"] += 1
    t.elementi["urna"] += 1
    return t


def cero(w, h):
    """Un cero esposto, visto dall'alto: i due prismi di legno sovrapposti e, in cima, il santo."""
    t = Tela(w, h, PIETRA_CHIARA)
    largo = w * 8
    for y in range(4, h * 8 - 2):
        banda = (y // 6) % 2
        t.rett(largo // 2 - 5, y, 10, 1, LEGNO if banda else LEGNO_SCURO)
    t.rett(largo // 2 - 5, h * 4 - 1, 10, 2, CONTORNO)
    t.rett(largo // 2 - 2, 0, 4, 5, COTTO_LUCE)
    t.rett(largo // 2 - 1, 1, 2, 2, PIETRA_LUCE)
    t.elementi["prismi"] += 1
    t.elementi["santo"] += 1
    return t


def basilica(w, h, info):
    """Basilica di Sant'Ubaldo: in alto la chiesa (tetto e campanile), al centro il chiostro col
    loggiato su colonne e il pozzo, in basso la fronte con il portale e la scalinata d'ingresso."""
    t = Tela(w, h)
    largo, alto = w * 8, h * 8
    fronte = 6 * 8                   # la fronte e la scalinata
    chiostro = min(14 * 8, alto - fronte - 10 * 8)
    y_chiostro = alto - fronte - chiostro
    # la chiesa: tetto a capanna, il campanile in alto a destra
    t.falde(0, 0, largo, y_chiostro)
    t.gronda(0, y_chiostro - 3, largo)
    t.conci(largo - 32, 0, 24, 40, TINTE[1])
    t.merli(largo - 32, 0, 24, TINTE[1])
    t.arco(largo - 25, 14, 10, 14)
    t.elementi["campanile"] += 1
    # il chiostro: cortile lastricato, il loggiato di colonne tutto intorno, il pozzo al centro
    t.rett(0, y_chiostro, largo, chiostro, PIETRA)
    t.rett(10, y_chiostro + 10, largo - 20, chiostro - 20, PIETRA_LUCE)
    for x in range(12, largo - 12, 8):
        for y in (y_chiostro + 6, y_chiostro + chiostro - 8):
            t.rett(x, y, 3, 3, PIETRA_CHIARA)
            t.punto(x + 2, y + 2, CONTORNO)
    for y in range(y_chiostro + 14, y_chiostro + chiostro - 12, 8):
        for x in (6, largo - 9):
            t.rett(x, y, 3, 3, PIETRA_CHIARA)
            t.punto(x + 2, y + 2, CONTORNO)
    t.elementi["loggiato"] += 1
    cx, cy = largo // 2, y_chiostro + chiostro // 2
    for y in range(cy - 6, cy + 7):
        for x in range(cx - 6, cx + 7):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if d <= 6:
                t.punto(x, y, PIETRA_CHIARA if d > 3.5 else ACQUA_SCURA)
    t.rett(cx - 6, cy, 13, 1, LEGNO)
    t.elementi["chiostro"] += 1
    t.elementi["pozzo"] += 1
    # la fronte con il portale e, sotto, la scalinata
    y0 = alto - fronte
    t.conci(0, y0, largo, fronte - 16, TINTE[0])
    t.arco(largo // 2 - 8, y0 + 4, 16, fronte - 20, LEGNO_SCURO)
    t.elementi["portale"] += 1
    for k in range(4):
        y = alto - 16 + k * 4
        t.rett(0, y, largo, 3, PIETRA_LUCE)
        t.rett(0, y + 3, largo, 1, PIETRA)
    t.elementi["scalinata"] += 1
    t.contorno()
    return t


PITTORI["basilica"] = basilica
REQUISITI.update({"basilica": {"scalinata": 1, "portale": 1, "chiostro": 1, "loggiato": 1, "pozzo": 1,
                               "campanile": 1}})
