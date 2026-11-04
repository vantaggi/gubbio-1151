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

import pittore_citta as PC

PALETTE_RIF = PC.PALETTE_BASE      # indice di sempre -> (rampa, tono)

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
        """Muro di conci irregolari (STANDARD_GRAFICO F2, pezzo EDI): il motivo del muro di
        tools/pittore_citta.py a coordinate della tela, file di 3-4 pixel e conci di 5-10, il giunto nel tono
        d'ombra; la tinta sceglie il motivo chiaro (pietra luce o chiara) o quello medio."""
        nome = "muro_chiaro" if tinta[0] in (PIETRA_CHIARA, PIETRA_LUCE) else "muro"
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                self.punto(x, y, PC.colore_suolo(nome, x, y))

    def coppi(self, x0, y0, w, h, scuro=COTTO_SCURO):
        """Tetto di coppi visto dall'alto: canali verticali, luce a sinistra del colmo."""
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                self.punto(x, y, scuro if y % 4 == 3 else [COTTO_LUCE, COTTO_CHIARO, COTTO, scuro][x % 4])

    def falde(self, x0, y0, w, h):
        """Tetto di un monumento: due falde di coppi con il colmo lungo l'asse lungo (F1, il pennello dei tetti di
        tools/pittore_citta.py), piu' chiaro delle case intorno perche' il monumento e' piu' alto."""
        if w <= 0 or h <= 0:
            return
        PC.dipingi_tetto(self, x0, x0 + w - 1, y0, y0 + h - 1, 3, w * 31 + h, gronda=False, verticale=w < h)

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            v = self.px[y][x]
            return PALETTE_RIF[v] if isinstance(v, int) else v
        return None

    def contorno(self):
        """Il bordo del monumento non e' piu' una riga nera (STANDARD_GRAFICO P2): lo fa il contorno selettivo di
        tools/pittore_citta.py, nel tono scuro del materiale, dove il monumento tocca il suolo o le case."""
        self.elementi["contorno"] += 1

    def gronda(self, x0, y, w):
        """La gronda: il bordo del tetto, un tono scuro, e sotto l'ombra sul muro (L4), mai nera (C4)."""
        self.rett(x0, y, w, 1, ("cotto e coppi", 2))
        self.rett(x0, y + 1, w, 1, ("cotto e coppi", 0))
        self.rett(x0, y + 2, w, 2, ("pietra calcarea", 1))

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


def portale_in_scala(t, cx, base, cima_libera, largo=16, alto=28):
    """M2: il portale frontale in scala col giocatore (alto 22-24 pixel): 28 pixel, o fin dove la facciata lo
    lascia (sotto finestre e occhi, 'cima_libera'), largo 2 celle (16 pixel, quanto il portale aperto degli
    interni). Ritorna l'altezza; i test vogliono almeno 26."""
    hp = max(8, min(alto, base - cima_libera))
    if abs(cx - t.w / 2) <= 8:
        # il portale al centro sta sulle due celle 'd' del generatore (w//2 - 1 e w//2): li' si entra
        cx = (t.w // 16) * 8
    t.arco(cx - largo // 2, base - hp, largo, hp, LEGNO_SCURO)
    return hp


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
    fh = max(min(6, h - 2), min(h - 2, h * 6 // 10))
    tetto_e_facciata(t, w, h, fh, tinta)
    y0 = (h - fh) * 8
    largo = w * 8
    for k in range(2):
        t.arco(largo // 2 - 17 + k * 22, y0 + 4, 12, 14, CONTORNO)
    base = y0 + fh * 8
    portale_in_scala(t, largo // 2 - 4, base, y0 + 20)
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
    portale_in_scala(t, largo // 2, base, y0 + 26)
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
    # M2: la facciata frontale alta almeno 4 tile, perche' il portone sia di 26-28 pixel
    fh = 2 if faccia != "basso" else max(2, min(h - 1, max(4, h // 3)))
    if r == "porta":
        t.conci(0, 0, w * 8, h * 8, tinta)
        t.merli(0, 0, w * 8, tinta)
        t.elementi["merlatura"] += 1
    elif r == "chiesa":
        # tetto a capanna: due falde, colmo al centro dell'asse lungo
        lungo_orizzontale = w >= h
        PC.dipingi_tetto(t, 0, w * 8 - 1, 0, (h - fh) * 8 - 1, 3, w * 7 + h, gronda=False,
                         verticale=not lungo_orizzontale)
    else:
        t.falde(0, 0, w * 8, (h - fh) * 8)
    if r != "porta":
        t.gronda(0, (h - fh) * 8 - 3, w * 8)
        t.conci(0, (h - fh) * 8, w * 8, fh * 8, tinta)
    if faccia == "basso":
        largo = w * 8
        # M2: il portone in scala col giocatore (alto 22-24): 28 pixel, o quanto la facciata permette
        ap = portale_in_scala(t, largo // 2, h * 8, (h - fh) * 8 + 4, largo=16 if largo >= 24 else 10)
        t.elementi["porta"] += 1
        if r == "chiesa" and fh * 8 - ap >= 12:
            # la finestra sopra il portone, se c'e' posto
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
    # il muro di scorcio: verso sinistra prende la luce (L1), verso destra sta in ombra; la gronda lo separa
    # dal tetto con un tono scuro, non nero (C4, L3)
    if lato == "sinistra":
        for y in range(h * 8):
            t.punto(x0, y, ("pietra calcarea", 5))
        t.rett(x0 + larga * 8 - 2, 0, 1, h * 8, ("cotto e coppi", 2))
        t.rett(x0 + larga * 8 - 1, 0, 1, h * 8, ("cotto e coppi", 0))
    else:
        for y in range(h * 8):
            for x in range(x0, x0 + larga * 8):
                c = t.get(x, y)
                if c and c[0] == "pietra calcarea":
                    t.punto(x, y, ("pietra calcarea", max(1, c[1] - 1)))
        t.rett(x0, 0, 1, h * 8, ("cotto e coppi", 0))
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
    """Palazzo Ducale: dall'alto il cortile rinascimentale, con il portico su quattro lati. Con la
    facciata di lato (sinistra o destra) si vede di scorcio il fronte sulla stradina del Duomo:
    le finestre regolari a cornice di pietra e il portale."""
    t = Tela(w, h)
    faccia = info.get("faccia")
    spostamento = 0
    if faccia in ("sinistra", "destra"):
        x0, larga = facciata_di_lato(t, w, h, faccia, TINTE[2])
        for y in range(12, h * 8 - 12, 14):
            t.rett(x0 + larga // 2 - 4, y - 1, 8, 10, PIETRA_LUCE)
            t.rett(x0 + larga // 2 - 3, y, 6, 8, CONTORNO)
        t.arco(x0 + larga // 2 - 5, h * 4 - 8, 10, 16, LEGNO_SCURO)
        t.elementi["facciata"] += 1
        spostamento = (larga // 2) * (1 if faccia == "sinistra" else -1)
    else:
        t.falde(0, 0, w * 8, (h - 2) * 8)
        t.gronda(0, (h - 2) * 8 - 3, w * 8)
        t.conci(0, (h - 2) * 8, w * 8, 16, TINTE[2])
    cw, ch = (w * 8) * 2 // 5, (h * 8) * 2 // 5
    cx0, cy0 = (w * 8 - cw) // 2 + spostamento, (h * 8 - ch) // 2
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
    portale_in_scala(t, largo // 2, base, (h - fh) * 8 + 18)
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
    portale_in_scala(t, largo // 2, base, (h - fh) * 8 + 4)
    t.elementi["portale"] += 1
    t.contorno()
    return t


def santa_maria_nuova(w, h, info):
    """Santa Maria Nuova: chiesa semplice, tetto a capanna, portale ad arco e una monofora."""
    t = Tela(w, h)
    fh = altezza_facciata(h, None, 4)
    tetto_e_facciata(t, w, h, fh, TINTE[1])
    largo, base = w * 8, h * 8
    portale_in_scala(t, largo // 2, base, (h - fh) * 8 + 17)
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
    fh = altezza_facciata(h, None, min(6, h - 2))
    tetto_e_facciata(t, w, h, fh, tinta)
    y0 = (h - fh) * 8
    largo, base = w * 8, h * 8
    t.merli(0, y0, largo, tinta)
    t.elementi["merlatura"] += 1
    for k in range(3):
        t.arco_acuto(8 + k * (largo - 16) // 3, y0 + 8, 8, 10, CONTORNO)
        t.elementi["finestra_acuta"] += 1
    portale_in_scala(t, largo // 2, base, y0 + 20)
    t.elementi["portale"] += 1
    t.contorno()
    return t


def ranghiasci(w, h, info):
    """Palazzo Ranghiasci-Brancaleoni: la facciata neoclassica guarda a sud, cioe' a sinistra: una
    lunga fila regolare di finestre rettangolari e il portone al centro."""
    t = Tela(w, h)
    faccia = info.get("faccia") if info.get("faccia") in ("sinistra", "destra") else "sinistra"
    x0, larga = facciata_di_lato(t, w, h, faccia, TINTE[2], 2)
    # di scorcio le finestre sono strette (M2, F5): il vano scuro, lo stipite in luce, il davanzale e la sua ombra
    for y in range(8, h * 8 - 8, 14):
        if abs(y + 4 - h * 4) < 14:
            continue
        for fx in (x0 + 4, x0 + larga - 8):
            t.rett(fx, y, 3, 8, CONTORNO)
            t.rett(fx - 1, y, 1, 8, PIETRA_LUCE)
            t.rett(fx + 2, y + 1, 1, 7, ("legno e cuoio", 0))
            t.rett(fx - 1, y + 8, 5, 1, PIETRA_LUCE)
            t.rett(fx, y + 9, 4, 1, ("pietra calcarea", 1))
            t.elementi["finestra_regolare"] += 1
    t.rett(x0 + 3, h * 8 // 2 - 8, larga - 6, 16, LEGNO_SCURO)
    t.rett(x0 + 2, h * 8 // 2 - 9, 1, 17, PIETRA_LUCE)
    t.rett(x0 + 3, h * 8 // 2 - 9, larga - 6, 1, PIETRA_LUCE)
    t.punto(x0 + larga // 2, h * 8 // 2, ("oro e bronzo", 2))
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
    portale_in_scala(t, w * 4, h * 8, (h - fh) * 8 + 4)
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
    """Teatro Romano, con la stessa forma della griglia (geometria_teatro di genera_mondo.py): scena sul bordo
    sinistro, orchestra a semicerchio, gradinate concentriche, l'anello esterno di arcate di pietra, il prato
    intorno. Allo standard (pezzo EDI): i gradini sono anelli veri di 5 pixel, ognuno con lo spigolo chiaro, la
    pedata nel tono medio e l'alzata d'ombra (F2, C5); l'anello delle arcate ha i fornici scuri con l'arco (F5);
    la scena e' un muro di conci con le nicchie; il prato e' quello dei giardini."""
    t = Tela(w, h, VERDE)
    cx, cy = 2.0 * 8 + 4, h * 4 - 0.5     # centro fra due righe di pixel: la cavea e' simmetrica (tile specchiati)
    r = min(w - 3, h / 2 - 1)
    r_int = r / 3
    R, RI, RA = (r - 1.5) * 8 + 4, r_int * 8 + 4, r * 8 + 4
    import math as _m
    for y in range(h * 8):
        for x in range(w * 8):
            ty, tx = y // 8, x // 8
            d_t = ((tx - 2.0) ** 2 + (ty - (h / 2 - 0.5)) ** 2) ** 0.5
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if tx < 2.0:
                if abs(ty - (h / 2 - 0.5)) <= r:
                    c = PC.colore_suolo("muro_chiaro", x, y)
                    if ty % 3 == 0 and 2 <= x % 8 <= 5 and 1 <= y % 8 <= 7:
                        c = ("pietra calcarea", 1) if x % 8 == 5 or y % 8 == 1 else CONTORNO
                    if x % 16 == 15:
                        c = ("pietra calcarea", 1)
                else:
                    c = PC.colore_verde("prato", x, y)
            elif d <= RI:
                c = PC.colore_suolo("lastrico", x, y)
            elif d <= R:
                k = (d - RI) % 5
                c = ("pietra calcarea", 4) if k < 1 else (("pietra calcarea", 3) if k < 4 else ("pietra calcarea", 1))
                if k >= 1 and k < 4 and (int(d) * 7 + int(abs(_m.atan2(y - cy, x - cx)) * 40)) % 23 == 0:
                    c = ("pietra calcarea", 2)
            elif d <= RA:
                ang = abs(_m.atan2(y - cy, x - cx))
                u = (ang * RA) % 12
                k = d - (r - 1.5) * 8
                c = ("pietra calcarea", 2)
                if 3 <= u <= 9 and k > 3:
                    c = CONTORNO if 4 <= u <= 8 and k > 5 else ("pietra calcarea", 1)
                if k <= 2:
                    c = ("pietra calcarea", 4) if k <= 1 else ("pietra calcarea", 3)
            else:
                c = PC.colore_verde("prato", x, y)
            t.punto(x, y, c)
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
    t = Tela(w, h, VERDE)
    largo, alto = w * 8, h * 8
    # il tetto a capanna di coppi, col colmo in mezzo e la croce di pietra sopra
    t.falde(2, 0, largo - 4, alto - 12)
    t.rett(largo // 2 - 1, 1, 2, 7, PIETRA_LUCE)
    t.rett(largo // 2 - 3, 3, 6, 2, PIETRA_LUCE)
    t.punto(largo // 2, 8, CONTORNO)
    # la fronte bianca con l'arco dell'edicola, l'immagine del santo dentro
    t.conci(2, alto - 12, largo - 4, 8, TINTE[0])
    t.arco(largo // 2 - 4, alto - 12, 8, 8, CONTORNO)
    t.rett(largo // 2 - 1, alto - 9, 2, 3, COTTO_LUCE)
    # il gradino davanti
    t.rett(4, alto - 4, largo - 8, 3, PIETRA_LUCE)
    t.rett(4, alto - 1, largo - 8, 1, PIETRA)
    t.elementi["edicola"] += 1
    t.elementi["croce"] += 1
    t.elementi["gradino"] += 1
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
    """Un cero esposto, visto dall'alto in tre quarti: il supporto di legno (la barella), i due prismi
    ottagonali sovrapposti e, in cima, la statuina del santo."""
    t = Tela(w, h, PIETRA_CHIARA)
    largo, alto = w * 8, h * 8
    cx = largo // 2
    t.rett(1, alto - 6, largo - 2, 4, LEGNO_SCURO)
    t.rett(1, alto - 2, largo - 2, 1, CONTORNO)
    for y in range(8, alto - 6):
        banda = ((y - 8) // ((alto - 14) // 2)) % 2
        meta = 5 if (y - 8) % ((alto - 14) // 2) in (0, 1) else 6
        t.rett(cx - meta, y, 2 * meta, 1, LEGNO if banda else COTTO_LUCE)
        t.punto(cx - meta, y, CONTORNO)
        t.punto(cx + meta - 1, y, CONTORNO)
    t.rett(cx - 3, 1, 6, 7, COTTO)
    t.rett(cx - 2, 0, 4, 3, PIETRA_LUCE)
    t.punto(cx - 1, 1, CONTORNO)
    t.elementi["supporto"] += 1
    t.elementi["prismi"] += 1
    t.elementi["santo"] += 1
    return t


def basilica(w, h, info):
    """Basilica di Sant'Ubaldo: il tetto a capanna della chiesa, il campanile alto in cima a destra
    con la sua ombra lunga, la facciata con il portale a vista e, sotto, la scalinata. Il chiostro
    sta accanto, a sinistra (cella h, pittore chiostro)."""
    t = Tela(w, h)
    largo, alto = w * 8, h * 8
    facciata = 9 * 8
    t.falde(0, 0, largo, alto - facciata)
    t.gronda(0, alto - facciata - 3, largo)
    # il campanile: alto, a conci, la cella delle campane, la cuspide e l'ombra sul tetto
    cx0, cw, ch = largo - 34, 26, 64
    t.rett(cx0 - 6, 8, 6, ch, COTTO_SCURO)
    t.conci(cx0, 0, cw, ch, TINTE[1])
    t.merli(cx0, 0, cw, TINTE[1])
    for k in range(2):
        t.arco(cx0 + 4 + k * 10, 14, 8, 14)
    t.rett(cx0 + 4, 36, cw - 8, 2, PIETRA_LUCE)
    t.arco(cx0 + 8, 42, 10, 12, CONTORNO)
    t.elementi["campanile"] += 1
    # la facciata: conci chiari, il rosone, il portale grande in cima alla scalinata
    y0 = alto - facciata
    t.conci(0, y0, largo, facciata - 16, TINTE[0])
    t.rett(0, y0, largo, 2, PIETRA_LUCE)
    rosone(t, largo // 2, y0 + 12, 6)
    t.arco(largo // 2 - 10, y0 + 24, 20, facciata - 40, LEGNO_SCURO)
    t.rett(largo // 2 - 1, y0 + 30, 2, facciata - 46, LEGNO)
    t.elementi["facciata"] += 1
    t.elementi["portale"] += 1
    for k in range(4):
        y = alto - 16 + k * 4
        t.rett(0, y, largo, 3, PIETRA_LUCE)
        t.rett(0, y + 3, largo, 1, PIETRA)
    t.elementi["scalinata"] += 1
    t.contorno()
    return t


def chiostro(w, h):
    """Il chiostro della Basilica visto dall'alto: il tetto del loggiato tutto intorno, le colonne
    sul giardino, il pozzo al centro del prato."""
    t = Tela(w, h)
    largo, alto = w * 8, h * 8
    t.falde(0, 0, largo, alto)
    gx0, gy0, gx1, gy1 = 16, 16, largo - 16, alto - 16
    t.rett(gx0 - 6, gy0 - 6, gx1 - gx0 + 12, gy1 - gy0 + 12, PIETRA)
    t.rett(gx0, gy0, gx1 - gx0, gy1 - gy0, VERDE)
    for x in range(gx0 - 4, gx1 + 4, 7):
        for y in (gy0 - 4, gy1 + 1):
            t.rett(x, y, 3, 3, PIETRA_LUCE)
            t.punto(x + 2, y + 2, CONTORNO)
    for y in range(gy0 + 3, gy1, 7):
        for x in (gx0 - 4, gx1 + 1):
            t.rett(x, y, 3, 3, PIETRA_LUCE)
            t.punto(x + 2, y + 2, CONTORNO)
    t.elementi["loggiato"] += 1
    cx, cy = largo // 2, alto // 2
    for y in range(cy - 7, cy + 8):
        for x in range(cx - 7, cx + 8):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if d <= 7:
                t.punto(x, y, PIETRA_LUCE if d > 4 else ACQUA_SCURA)
    t.rett(cx - 7, cy, 15, 1, LEGNO)
    t.rett(gx0 + 2, cy - 1, cx - 9 - gx0, 2, PIETRA_CHIARA)
    t.rett(cx + 8, cy - 1, gx1 - cx - 10, 2, PIETRA_CHIARA)
    t.elementi["pozzo"] += 1
    t.elementi["giardino"] += 1
    t.contorno()
    return t


def pilastro(w, h):
    """Un pilastro della navata visto dall'alto: la base quadrata e il fusto a fascio con l'ombra."""
    t = Tela(w, h, PIETRA_CHIARA)
    largo, alto = w * 8, h * 8
    t.rett(1, 1, largo - 2, alto - 2, PIETRA)
    t.rett(3, 3, largo - 6, alto - 6, PIETRA_LUCE)
    t.rett(largo - 4, 4, 2, alto - 6, PIETRA_SCURA)
    t.rett(4, alto - 4, largo - 6, 2, PIETRA_SCURA)
    t.elementi["base"] += 1
    t.elementi["fusto"] += 1
    return t


PITTORI["basilica"] = basilica
REQUISITI.update({"basilica": {"scalinata": 1, "portale": 1, "facciata": 1, "campanile": 1}})




# --- alberi grandi ----------------------------------------------------------------------------------

def chioma(tipo, fondo=VERDE):
    """Una chioma di 2x2 tile vista dall'alto: il leccio scuro e compatto, la roverella chiara a lobi;
    la luce in alto a sinistra, l'ombra che cade in basso a destra sul terreno."""
    t = Tela(2, 2, fondo)
    cx, cy, r = 7.0, 7.0, 6.6
    for y in range(16):
        for x in range(16):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            ombra = ((x - cx - 2) ** 2 + (y - cy - 2) ** 2) ** 0.5
            lobi = 0.9 * ((x * 5 + y * 3) % 4 == 0) if tipo == "roverella" else 0
            if d <= r - lobi:
                luce = (x - cx) + (y - cy) < -3
                if tipo == "roverella":
                    c = VERDE if luce or (x * 3 + y * 5) % 7 == 0 else VERDE_SCURO
                else:
                    c = VERDE if luce and (x + y) % 3 == 0 else VERDE_SCURO
                if d > r - 1.2 - lobi and not luce:
                    c = CONTORNO
                t.punto(x, y, c)
            elif ombra <= r:
                t.punto(x, y, CONTORNO)
    t.elementi["chioma"] += 1
    return t


def cipresso(fondo=VERDE):
    """Un cipresso di 1x2 tile: il fuso scuro e stretto, la punta in alto, l'ombra lunga a destra."""
    t = Tela(1, 2, fondo)
    for y in range(16):
        meta = 1 if y < 3 else (2 if y < 6 or y > 13 else 3)
        for x in range(8):
            if abs(x - 3.5) <= meta - 0.5:
                t.punto(x, y, VERDE if x < 3 and y % 3 == 0 else VERDE_SCURO)
            elif x == int(3.5 + meta) and y > 2:
                t.punto(x, y, CONTORNO)
    t.elementi["cipresso"] += 1
    return t


# --- gli edifici della storia v2 (le schede degli amici, copione/05_npc_amici.md) ----------------------
def _cerchio(t, cx, cy, r, c, pieno=True):
    for y in range(int(cy - r) - 1, int(cy + r) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            d = ((x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2) ** 0.5
            if (d <= r if pieno else abs(d - r) < 0.7):
                t.punto(x, y, c)


def _facciata(w, h, faccia):
    """Il rettangolo (x, y, larghezza, altezza) in pixel della facciata che si vede."""
    fh = max(2, min(h - 2, h // 3))
    if faccia == "basso":
        return 0, (h - fh) * 8, w * 8, fh * 8
    if faccia == "destra":
        return w * 8 - 8, 0, 8, h * 8
    return 0, 0, 8, h * 8


def _ruota(t, cx, cy, r):
    _cerchio(t, cx, cy, r, LEGNO_SCURO, pieno=False)
    for dx, dy in ((0, 1), (1, 0), (1, 1), (1, -1)):
        for k in range(-r + 1, r):
            t.punto(cx + dx * k, cy + dy * k, LEGNO)
    t.punto(cx, cy, CONTORNO)


def casa_medico(w, h, info):
    """La casa del medico a San Martino: una casa di pietra col portone e, accanto, l'insegna col vaso
    delle urine, il segno del medico medievale."""
    t = generico("casa_medico", "Casa del medico", w, h, info["faccia"], 1)
    x, y, fw, fh = _facciata(w, h, info["faccia"])
    sx, sy = x + fw // 2 + 8, y + 3
    t.rett(sx - 1, sy, 9, 1, LEGNO_SCURO)
    t.rett(sx, sy + 1, 7, 7, LEGNO)
    _cerchio(t, sx + 3.5, sy + 5, 2, ACQUA)
    t.rett(sx + 3, sy + 1, 1, 2, ACQUA)
    t.elementi["insegna"] += 1
    t.contorno()
    return t


def bottega_carradore(w, h, info):
    """La bottega del carradore a Quaranta Martiri: il portone largo da cui escono i carri, le ruote
    cerchiate di ferro appoggiate al muro, il carro."""
    t = generico("bottega_carradore", "Bottega del carradore", w, h, info["faccia"], 3)
    x, y, fw, fh = _facciata(w, h, info["faccia"])
    if fw > fh:
        t.rett(x + fw // 2 - 8, y + fh - 14, 16, 14, LEGNO_SCURO)
        for k, cx in enumerate((x + 6, x + fw - 7)):
            _ruota(t, cx, y + fh - 6, 4)
    else:
        t.rett(x + 1, y + fh // 2 - 8, 6, 16, LEGNO_SCURO)
        for cy in (y + 6, y + fh - 7):
            _ruota(t, x + 4, cy, 3)
    # il carro sul tetto del cortile: il pianale e due ruote
    t.rett(8, 6, 18, 5, LEGNO)
    t.rett(8, 6, 18, 1, LEGNO_SCURO)
    _ruota(t, 11, 13, 3)
    _ruota(t, 23, 13, 3)
    t.elementi["ruote"] += 1
    t.contorno()
    return t


def spezieria(w, h, info):
    """La spezieria con l'ospizio a San Pietro: la vetrina coi vasi colorati sugli scaffali e, a destra,
    il portico ad archi dell'ospizio dove si curano i malati."""
    t = generico("spezieria", "Spezieria e ospizio", w, h, info["faccia"], 2)
    x, y, fw, fh = _facciata(w, h, info["faccia"])
    vx, vy = x + 4, y + 3
    t.rett(vx, vy, fw // 2 - 8, 10, LEGNO_SCURO)
    for r in range(2):
        t.rett(vx, vy + 4 + r * 5, fw // 2 - 8, 1, LEGNO)
        for k in range(vx + 1, vx + fw // 2 - 9, 3):
            t.punto(k, vy + 3 + r * 5, (ACQUA, COTTO_LUCE, VERDE, PIETRA_LUCE)[(k + r) % 4])
            t.punto(k, vy + 2 + r * 5, (ACQUA, COTTO_LUCE, VERDE, PIETRA_LUCE)[(k + r) % 4])
    for k in range(2):
        # il portico dell'ospizio: muro di fondo in ombra e parapetto chiaro, non un vano nero (custode
        # visivo, 4 nov: il nero aperto e' riservato alle porte vere)
        ax, ay = x + fw // 2 + 4 + k * 12, y + fh - 14
        t.arco(ax, ay, 10, 14, PIETRA_SCURA)
        t.rett(ax + 1, ay + 9, 8, 1, PIETRA_LUCE)
        t.rett(ax + 1, ay + 10, 8, 4, PIETRA_CHIARA)
        t.rett(ax + 4, ay + 10, 2, 4, PIETRA)
    t.elementi["vasi"] += 1
    t.elementi["portico"] += 1
    t.contorno()
    return t


def taverna(w, h, info):
    """La taverna del corso a San Pietro, di Padellino: la frasca verde appesa sopra la porta (il segno
    dell'osteria) e la botte accanto."""
    t = generico("taverna", "Taverna del corso", w, h, info["faccia"], 4)
    x, y, fw, fh = _facciata(w, h, info["faccia"])
    fx, fy = x + fw // 2 + 7, y + 2
    t.rett(fx, fy, 1, 3, LEGNO_SCURO)
    _cerchio(t, fx + 0.5, fy + 6, 3, VERDE)
    _cerchio(t, fx - 1, fy + 5, 1.5, VERDE_SCURO)
    _cerchio(t, x + 7, y + fh - 5, 4, LEGNO)
    t.rett(x + 3, y + fh - 6, 9, 1, LEGNO_SCURO)
    t.rett(x + 3, y + fh - 3, 9, 1, LEGNO_SCURO)
    t.elementi["frasca"] += 1
    t.contorno()
    return t


def bottega_conti(w, h, info):
    """La bottega dei conti e dei congegni a Sant'Agostino, di Fazio e Lauretta: la porta e l'insegna con
    la ruota dentata di un congegno."""
    t = generico("bottega_conti", "Bottega dei conti e dei congegni", w, h, info["faccia"], 5)
    x, y, fw, fh = _facciata(w, h, info["faccia"])
    cx, cy = (x + fw // 2, y + 6) if fw > fh else (x + 4, y + fh // 2 - 14)
    _cerchio(t, cx, cy, 3.2, PIETRA_LUCE)
    for dx, dy in ((0, -4), (0, 4), (-4, 0), (4, 0), (3, 3), (-3, -3), (3, -3), (-3, 3)):
        t.punto(cx + dx, cy + dy, PIETRA_LUCE)
    t.punto(cx, cy, CONTORNO)
    t.elementi["congegno"] += 1
    t.contorno()
    return t


def calcara(w, h, info):
    """La calcara fuori Porta Romana, di Ragnetto: il forno tondo di pietre a secco dove si cuoce il
    calcare, la bocca accesa in basso e il fumo chiaro dalla cima."""
    t = Tela(w, h)
    cx, cy, r = w * 4, h * 4 + 2, min(w, h) * 4 - 2
    _cerchio(t, cx, cy, r, PIETRA)
    for y in range(int(cy - r), int(cy + r)):
        for x in range(int(cx - r), int(cx + r)):
            if t.px[y][x] == PIETRA and (x // 3 + y // 2) % 4 == 0:
                t.punto(x, y, PIETRA_SCURA)
            elif t.px[y][x] == PIETRA and x < cx - 2 and y < cy - 2 and (x + y) % 5 == 0:
                t.punto(x, y, PIETRA_CHIARA)
    _cerchio(t, cx, cy - r // 3, r // 3, CONTORNO)
    for k in range(5):
        t.punto(cx - 2 + k, cy - r // 3 - 3 - k, PIETRA_LUCE)
    t.arco(cx - 4, cy + r - 9, 8, 9, COTTO_LUCE)
    t.rett(cx - 2, cy + r - 5, 4, 4, COTTO_CHIARO)
    t.elementi["bocca"] += 1
    t.contorno()
    return t


def banco_montano(w, h, info):
    """Il banco di Montano sotto le case di via dei Consoli: la tenda a strisce, il tavolo con le pinze del
    cavadenti e una tavoletta dipinta."""
    t = Tela(w, h)
    for x in range(w * 8):
        for y in range(6):
            t.punto(x, y, COTTO_CHIARO if (x // 4) % 2 else PIETRA_LUCE)
    for x in range(0, w * 8, 4):
        t.punto(x, 6, COTTO_SCURO)
    t.rett(1, 6, 1, h * 8 - 6, LEGNO_SCURO)
    t.rett(w * 8 - 2, 6, 1, h * 8 - 6, LEGNO_SCURO)
    t.rett(2, 10, w * 8 - 4, 4, LEGNO)
    t.rett(5, 8, 7, 5, PIETRA_LUCE)
    t.rett(6, 9, 5, 3, ACQUA)
    t.punto(8, 10, VERDE)
    t.rett(18, 9, 4, 1, PIETRA_SCURA)
    t.punto(21, 8, PIETRA_SCURA)
    t.elementi["tenda"] += 1
    t.contorno()
    return t


PITTORI.update({"casa_medico": casa_medico, "bottega_carradore": bottega_carradore, "spezieria": spezieria,
                "taverna": taverna, "bottega_conti": bottega_conti, "calcara": calcara, "banco_montano": banco_montano})


# --- le botteghe leggibili (SV2b3): insegne grandi e oggetti davanti alla porta -------------------------
# Nei fondali 1 tile = 8 px: i segni del mestiere di SV2b2 erano di 3-7 px e dalla vista di gioco le
# botteghe sembravano case qualsiasi. Qui ogni bottega riceve un'insegna appesa di 14x12 px sul bordo
# del tetto, con un'icona che si legge da lontano, e due o tre oggetti a misura di personaggio (8-12 px)
# sulla facciata, accanto alla porta. tests/test_mondo.py (Botteghe) conta i pixel dei segni.
SEGNI_MINIMI = 60          # pixel di insegna e oggetti che ogni bottega deve avere almeno


def _insegna(t, x, y, icona):
    """Il cartello appeso: staffa di ferro, tavola di legno incorniciata, l'icona dentro (10x8)."""
    t.rett(x + 6, y, 2, 2, CONTORNO)
    t.rett(x, y + 2, 14, 12, CONTORNO)
    t.rett(x + 1, y + 3, 12, 10, LEGNO)
    icona(t, x + 2, y + 4)
    t.segni += 14 * 12


def _icona_vaso(t, x, y):          # il medico: l'ampolla
    t.rett(x + 4, y, 2, 3, PIETRA_LUCE)
    _cerchio(t, x + 5, y + 5, 3, ACQUA)
    t.punto(x + 4, y + 4, PIETRA_LUCE)


def _icona_ruota(t, x, y):         # il carradore
    _ruota(t, x + 5, y + 4, 4)


def _icona_mortaio(t, x, y):       # la spezieria: mortaio e pestello
    t.rett(x + 1, y + 4, 8, 4, PIETRA_LUCE)
    t.rett(x + 2, y + 7, 6, 1, PIETRA)
    t.rett(x + 6, y, 1, 5, LEGNO_SCURO)
    t.rett(x + 5, y, 3, 1, LEGNO_SCURO)


def _icona_frasca(t, x, y):        # la taverna: la frasca e il fiasco
    _cerchio(t, x + 3, y + 3, 3, VERDE)
    t.punto(x + 2, y + 2, VERDE_SCURO)
    t.rett(x + 7, y + 2, 2, 2, PIETRA_LUCE)
    t.rett(x + 6, y + 4, 4, 4, VERDE_SCURO)


def _icona_abaco(t, x, y):         # i conti: l'abaco
    t.rett(x, y, 10, 8, LEGNO_SCURO)
    t.rett(x + 1, y + 1, 8, 6, LEGNO)
    for r in range(3):
        t.rett(x + 1, y + 2 + r * 2, 8, 1, PIETRA_SCURA)
        for k in range(r % 2, 4, 1):
            t.punto(x + 2 + k * 2 - r % 2, y + 2 + r * 2, COTTO_LUCE)


def _icona_dente(t, x, y):         # Montano: il dente e la cornice
    t.rett(x, y, 10, 8, COTTO_CHIARO)
    t.rett(x + 3, y + 1, 4, 4, PIETRA_LUCE)
    t.punto(x + 3, y + 5, PIETRA_LUCE)
    t.punto(x + 6, y + 5, PIETRA_LUCE)
    t.punto(x + 3, y + 6, PIETRA_LUCE)
    t.punto(x + 6, y + 6, PIETRA_LUCE)


def _botte(t, x, y):
    t.rett(x, y, 8, 10, LEGNO)
    t.rett(x, y + 2, 8, 1, LEGNO_SCURO)
    t.rett(x, y + 7, 8, 1, LEGNO_SCURO)
    t.rett(x + 3, y + 4, 2, 2, LEGNO_SCURO)
    t.segni += 80


def _vaso_erbe(t, x, y):
    t.rett(x + 1, y + 4, 6, 6, COTTO_LUCE)
    t.rett(x + 1, y + 4, 6, 1, COTTO_SCURO)
    _cerchio(t, x + 4, y + 2, 2.5, VERDE)
    t.segni += 50


def _panca(t, x, y, w):
    t.rett(x, y, w, 2, LEGNO)
    t.rett(x + 1, y + 2, 1, 3, LEGNO_SCURO)
    t.rett(x + w - 2, y + 2, 1, 3, LEGNO_SCURO)
    t.segni += w * 2


def _fumo(t, x, y):
    for k, (dx, r) in enumerate(((0, 2.5), (2, 3), (-1, 3.5), (2, 4))):
        _cerchio(t, x + dx, y - k * 5, r, PIETRA_LUCE if k % 2 else PIETRA_CHIARA)
    t.segni += 120


def _con_segni(pittore, icona, oggetti):
    def disegna(w, h, info):
        t = pittore(w, h, info)
        t.segni = 0
        x, y, fw, fh = _facciata(w, h, info["faccia"])
        # l'insegna pende dal bordo del tetto, sopra la facciata e lontana dalla porta
        if info["faccia"] == "basso":
            _insegna(t, max(1, w * 8 - 18), max(0, y - 6), icona)
        elif info["faccia"] == "sinistra":
            _insegna(t, 1, max(0, h * 4 - 22), icona)
        else:
            _insegna(t, w * 8 - 15, max(0, h * 4 - 22), icona)
        oggetti(t, w, h, info["faccia"], x, y, fw, fh)
        t.elementi["insegna_grande"] += 1
        t.contorno()
        return t
    disegna.__doc__ = pittore.__doc__
    return disegna


def _ogg_medico(t, w, h, faccia, x, y, fw, fh):
    # la porta del medico e' di un altro colore (cotto chiaro), con la panca per chi aspetta
    t.arco(w * 4 - 5, h * 8 - 14, 10, 14, COTTO_LUCE)
    t.segni += 60
    _panca(t, 3, h * 8 - 6, 12)


def _ogg_carradore(t, w, h, faccia, x, y, fw, fh):
    for k in range(3):
        _ruota(t, x + 4, y + 12 + k * 12, 5)
    t.segni += 3 * 40


def _ogg_spezieria(t, w, h, faccia, x, y, fw, fh):
    t.arco(x + fw // 2 - 14, h * 8 - 14, 10, 14, ACQUA_SCURA)
    for k in range(3):
        _vaso_erbe(t, x + 3 + k * 9, h * 8 - 10)


def _ogg_taverna(t, w, h, faccia, x, y, fw, fh):
    _botte(t, x + 2, h * 8 - 11)
    _botte(t, x + 11, h * 8 - 11)
    _panca(t, w * 8 - 16, h * 8 - 6, 14)


def _ogg_conti(t, w, h, faccia, x, y, fw, fh):
    # la bilancia appesa accanto alla porta
    bx = x - 1 if faccia == "destra" else x + 1
    t.rett(bx + 3, y + 8, 1, 8, CONTORNO)
    t.rett(bx, y + 9, 7, 1, CONTORNO)
    t.rett(bx, y + 10, 2, 2, PIETRA_LUCE)
    t.rett(bx + 5, y + 10, 2, 2, PIETRA_LUCE)
    _vaso_erbe(t, bx, h * 8 - 12)
    t.segni += 30


def _ogg_calcara(t, w, h, faccia, x, y, fw, fh):
    _fumo(t, w * 4, h * 4 - 4)
    for k in range(2):
        t.rett(2 + k * 7, h * 8 - 8, 6, 6, PIETRA_LUCE)
        t.rett(2 + k * 7, h * 8 - 8, 6, 1, PIETRA)
    t.segni += 72


def _ogg_montano(t, w, h, faccia, x, y, fw, fh):
    # lo sgabello e la tavoletta dipinta grande appoggiata al banco
    t.rett(w * 8 - 10, h * 8 - 6, 6, 2, LEGNO)
    t.rett(w * 8 - 9, h * 8 - 4, 1, 3, LEGNO_SCURO)
    t.rett(w * 8 - 6, h * 8 - 4, 1, 3, LEGNO_SCURO)
    t.segni += 20


BOTTEGHE = {"casa_medico": (_icona_vaso, _ogg_medico), "bottega_carradore": (_icona_ruota, _ogg_carradore),
            "spezieria": (_icona_mortaio, _ogg_spezieria), "taverna": (_icona_frasca, _ogg_taverna),
            "bottega_conti": (_icona_abaco, _ogg_conti), "calcara": (_icona_frasca, _ogg_calcara),
            "banco_montano": (_icona_dente, _ogg_montano)}
BOTTEGHE["calcara"] = (None, _ogg_calcara)
BOTTEGHE_BASE = {m: PITTORI[m] for m in BOTTEGHE}     # i pittori di SV2b2, per le negative
for _mid, (_icona, _ogg) in BOTTEGHE.items():
    if _icona is None:
        _base = PITTORI[_mid]

        def _solo_oggetti(w, h, info, _base=_base, _ogg=_ogg):
            t = _base(w, h, info)
            t.segni = 0
            x, y, fw, fh = _facciata(w, h, info["faccia"])
            _ogg(t, w, h, info["faccia"], x, y, fw, fh)
            t.elementi["insegna_grande"] += 1
            t.contorno()
            return t
        PITTORI[_mid] = _solo_oggetti
    else:
        PITTORI[_mid] = _con_segni(PITTORI[_mid], _icona, _ogg)
