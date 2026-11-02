"""I panorami delle cutscene (F7, pezzo V): Gubbio vista dalla valle, di giorno, all'alba e di notte con
i fuochi del campo nemico nella conca. Ogni piano e' una tela 512x256 (64x32 tile) con la sua palette
di 16 colori della Guida di stile; la notte e' la stessa grafica con le rampe di notte (la trasformata
di stile/dati/palette.json). La citta' e' messa giu' dal censimento: i monumenti dove stanno davvero
(lat e lon proiettate sulla vista da sud-ovest), alla quota della loro area, alti quanto dice
l'altezza (o quanto il loro tipo), le case a riempire il pendio.

Un pittore riceve il momento ("giorno", "alba", "notte") e ritorna (tela, palette, notte).
"""
import csv
import json
import math
import os
import random

from genera_battaglia import Tela
import stendardi as ST

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 512, 256
QUADRO = 112                     # le righe di mappa che si vedono fra le bande
MOMENTI = ("giorno", "alba", "notte")

# --- palette ------------------------------------------------------------------------------------------
PALETTE_CIELO = [("neutri", 0), ("cielo e acqua", 0), ("cielo e acqua", 1), ("cielo e acqua", 2), ("cielo e acqua", 3),
                 ("cielo e acqua", 4), ("oro e bronzo", 1), ("oro e bronzo", 2), ("oro e bronzo", 3),
                 ("vermiglio comunale", 1), ("vermiglio comunale", 3), ("neutri", 0), ("neutri", 1), ("neutri", 2),
                 ("neutri", 4), ("cotto e coppi", 4)]
# panorama: 0 trasparente, poi contorno, pietra, cotto, vermiglio, verde, l'alone e l'oro dei fuochi.
# Le luci non si trasformano: un colore segnato ACCESO resta col tono del giorno anche di notte (i fuochi,
# le finestre accese), cosi' e' il punto di luce della scena. Solo l'alone e l'oro dei panorami lo sono.
ACCESO = "acceso"
PALETTE_PANORAMA = [("neutri", 0), ("neutri", 0), ("pietra calcarea", 1), ("pietra calcarea", 2), ("pietra calcarea", 3),
                    ("pietra calcarea", 4), ("pietra calcarea", 5), ("cotto e coppi", 1), ("cotto e coppi", 2),
                    ("cotto e coppi", 3), ("vermiglio comunale", 2), ("verde dei monti", 0), ("verde dei monti", 1),
                    ("verde dei monti", 2), ("cotto e coppi", 4, ACCESO), ("oro e bronzo", 3, ACCESO)]
CONTORNO, PIETRA_S, PIETRA, PIETRA_M, PIETRA_C, PIETRA_L = 1, 2, 3, 4, 5, 6
COTTO_S, COTTO, COTTO_C, VERMIGLIO = 7, 8, 9, 10
VERDE_S, VERDE_M, VERDE, ALONE, ORO = 11, 12, 13, 14, 15


# --- cielo --------------------------------------------------------------------------------------------
def cielo(momento):
    """Il cielo a fasce con il passaggio a scacchiera: azzurro di giorno, oro e rosso all'alba, la
    notte stellata (la rampa di notte)."""
    fasce = {"giorno": [3, 3, 4, 4, 5], "alba": [2, 3, 10, 7, 8], "notte": [11, 12, 12, 13, 13]}[momento]
    t = Tela(W, H, fasce[0])
    passo = QUADRO // len(fasce)
    for y in range(H):
        i = min(len(fasce) - 1, y // passo)
        for x in range(W):
            sopra = y % passo < 2 and (x + y) % 2 == 0 and i > 0
            t.punto(x, y, fasce[i - 1] if sopra else fasce[i])
    if momento == "notte":
        r = random.Random(3)
        for _ in range(70):
            t.punto(r.randrange(W), r.randrange(QUADRO - 40), 14)
    if momento == "alba":
        t.ellisse(380, QUADRO - 26, 10, 10, 8)
    return t, PALETTE_CIELO, momento == "notte"


# --- il Monte Ingino con la Basilica ------------------------------------------------------------------
def monte(momento):
    """Il Monte Ingino dietro la citta': il profilo con la cima a destra, il bosco a macchie, la Basilica
    e la Rocca in cima (dal censimento: la Basilica a 380 m sopra Quaranta Martiri)."""
    t = Tela(W, H)
    r = random.Random(11)
    cima = 330
    for x in range(W):
        d = abs(x - cima) / 260.0
        top = int(14 + 50 * d * d + 3 * math.sin(x / 13.0))
        for y in range(top, QUADRO):
            t.punto(x, y, VERDE_S if (x * 7 + y * 3) % 11 else VERDE_M)
        if x > 0:
            # la luce da sinistra sul fianco che sale
            if top < 14 + 50 * (abs(x - 1 - cima) / 260.0) ** 2:
                t.punto(x, top, VERDE)
    for _ in range(160):
        cx, cy = r.randrange(W), r.randrange(30, QUADRO)
        d = abs(cx - cima) / 260.0
        if cy > 18 + 50 * d * d:
            t.ellisse(cx, cy, 3, 2, VERDE_M if r.random() < 0.6 else VERDE)
    # la Basilica in cima, un po' sotto la vetta, col campanile; la Rocca piu' su
    bx, by = cima - 30, 30
    t.rett(bx, by - 8, 18, 9, PIETRA_C)
    t.rett(bx + 14, by - 8, 4, 9, PIETRA)
    t.trapezio(bx + 9, by - 12, by - 8, 4, 20, COTTO)
    t.rett(bx + 18, by - 16, 4, 17, PIETRA_C)
    t.rett(bx + 18, by - 18, 4, 2, COTTO)
    t.rett(cima - 2, 10, 10, 6, PIETRA_M)
    for k in range(0, 10, 3):
        t.rett(cima - 2 + k, 8, 2, 2, PIETRA_M)
    if momento == "notte":
        t.rett(bx + 6, by - 5, 2, 2, ORO)
    return t, PALETTE_PANORAMA, momento == "notte"


# --- Gubbio dal censimento ----------------------------------------------------------------------------
TIPI = {"consoli": ("torre", 60), "pretorio": ("palazzo", 28), "ducale": ("palazzo", 24), "bargello": ("torre", 30),
        "capitano_popolo": ("torre", 26), "duomo": ("chiesa", 30), "san_francesco": ("chiesa", 34),
        "san_pietro": ("chiesa", 28), "sant_agostino": ("chiesa", 26), "san_domenico": ("chiesa", 30),
        "san_marziale": ("chiesa", 18), "santa_maria_nuova": ("chiesa", 16), "porta_metauro": ("porta", 18),
        "porta_romana": ("porta", 18), "porta_san_pietro": ("porta", 16), "loggia_tiratori": ("palazzo", 14),
        "ranghiasci": ("palazzo", 22), "case_consoli": ("case", 12), "santa_maria_laici": ("chiesa", 16)}


def monumenti_dalla_valle():
    """[(id, x, base, altezza, tipo)] in pixel di mappa: vista da sud-ovest, la destra verso sud-est."""
    grafo = json.load(open(os.path.join(RADICE, "mondo", "grafo.json"), encoding="utf-8"))
    quota = {a["id"].lower(): sum(a["quota_m"]) / 2 for a in grafo["aree"]}
    righe = list(csv.DictReader(open(os.path.join(RADICE, "mondo", "fonti", "censimento_osm.csv"), encoding="utf-8")))
    punti = []
    for r in righe:
        if r["id"] not in TIPI or not r["lat"]:
            continue
        lat, lon = float(r["lat"]), float(r["lon"])
        est = (lon - 12.578) * 111320 * math.cos(math.radians(43.353))
        nord = (lat - 43.353) * 110540
        destra = (est - nord) / math.sqrt(2)                 # verso sud-est
        tipo, alto = TIPI[r["id"]]
        alto = float(r["altezza_m"]) if r["altezza_m"] else alto
        punti.append((r["id"], destra, quota.get(r["area"], 0), alto, tipo))
    xs = [p[1] for p in punti]
    x0, x1 = min(xs), max(xs)
    out = []
    for nome, destra, q, alto, tipo in punti:
        x = int(40 + (destra - x0) / (x1 - x0) * (W - 80))
        base = int(QUADRO - 8 - q * 0.42)                    # la citta' sale verso il monte
        out.append((nome, x, base, max(6, int(alto * 0.6)), tipo))
    return out


def finestra(t, x, y, tipo, notte, r):
    """Una finestra di tipo diverso: feritoia, quadrata, alta, ad arco o bifora. Di notte qualcuna e'
    accesa (l'oro, che non si trasforma)."""
    c = ORO if notte and r.random() < 0.3 else CONTORNO
    if tipo == "feritoia":
        t.rett(x, y, 1, 3, c)
    elif tipo == "quadrata":
        t.rett(x, y, 2, 2, c)
    elif tipo == "alta":
        t.rett(x, y, 2, 4, c)
    elif tipo == "arco":
        t.rett(x, y + 1, 3, 4, c)
        t.punto(x + 1, y, c)
    else:                                       # bifora: due luci ad arco e la colonnina in mezzo
        t.rett(x, y + 1, 1, 3, c)
        t.rett(x + 2, y + 1, 1, 3, c)
        t.punto(x, y, c)
        t.punto(x + 2, y, c)


def tetto(t, x0, y, largo, falde=False):
    """Il tetto a coppi: la fila dei coppi a righe, la gronda che fa ombra sul muro sotto."""
    if falde:
        t.trapezio(x0 + largo // 2, y - 3, y, largo - 4, largo + 2, COTTO)
    t.rett(x0 - 1, y, largo + 2, 2, COTTO)
    for k in range(x0 - 1, x0 + largo + 1, 2):
        t.punto(k, y, COTTO_C)
    t.rett(x0, y + 2, largo, 1, PIETRA_S)


def casa(t, x0, base, largo, alto, notte, r, torre=False):
    """Una casa del pendio: il muro in uno dei toni del calcare, il fianco destro in ombra, i marcapiani,
    le finestre diverse per piano (non in griglia), il tetto a coppi o i merli se e' una torre."""
    tono = r.choice((PIETRA, PIETRA_M, PIETRA_M, PIETRA_C))
    cima = base - alto
    t.rett(x0, cima, largo, alto, tono)
    t.rett(x0 + largo - 2, cima, 2, alto, max(PIETRA_S, tono - 1))
    for y in range(cima + 7, base - 2, 7):
        if alto > 11:
            t.rett(x0, y, largo - 2, 1, min(PIETRA_L, tono + 1))     # il marcapiano
    if torre:
        for k in range(0, largo, 3):
            t.rett(x0 + k, cima - 2, 2, 2, tono)
    else:
        tetto(t, x0, cima - 2, largo, falde=r.random() < 0.4)
    for y in range(cima + 3, base - 3, 7):
        x = x0 + 1 + r.randint(0, 2)
        while x < x0 + largo - 4:
            if r.random() < 0.75:
                tipo = "feritoia" if torre else r.choice(("quadrata", "alta", "alta", "arco", "bifora"))
                finestra(t, x, y + r.randint(0, 1), tipo, notte, r)
            x += r.randint(4, 6)
    if not torre and r.random() < 0.5 and largo > 8:
        porta = x0 + r.randint(1, largo - 5)
        t.rett(porta, base - 4, 3, 4, CONTORNO)
        t.punto(porta + 1, base - 5, CONTORNO)


def palazzo_dei_consoli(t, x, base, alto, notte, fuoco):
    """Il Palazzo dei Consoli visto dalla valle: il corpo alto di calcare chiaro, i merli guelfi, il
    campaniletto a vela in cima a sinistra, la fila delle bifore in alto, le finestre ad arco sotto, i
    grandi archi alla base (la loggia sul pendio). In cima, il drappo di Gubbio o il fuoco della Fede."""
    largo = 24
    x0 = x - largo // 2
    cima = base - alto + 8
    t.rett(x0, cima, largo, base - cima, PIETRA_L)
    t.rett(x0 + largo - 5, cima, 5, base - cima, PIETRA_M)
    for k in range(0, largo, 3):
        t.rett(x0 + k, cima - 2, 2, 2, PIETRA_L if k < largo - 5 else PIETRA_M)
    t.rett(x0, cima + 2, largo, 1, PIETRA_C)
    for k in range(3):
        finestra(t, x0 + 2 + k * 6, cima + 4, "bifora", notte, random.Random(k))
    for k in range(3):
        finestra(t, x0 + 3 + k * 6, cima + 12, "arco", notte, random.Random(k + 5))
    t.rett(x0, base - 9, largo, 1, PIETRA_C)
    for k in range(4):
        ax = x0 + 1 + k * 6
        t.rett(ax, base - 7, 4, 7, CONTORNO)
        t.rett(ax + 1, base - 8, 2, 1, CONTORNO)
    # il campaniletto a vela: un muro sottile con l'arco della campana
    vx = x0 + 2
    t.rett(vx, cima - 9, 5, 7, PIETRA_L)
    t.rett(vx + 4, cima - 9, 1, 7, PIETRA_M)
    t.rett(vx + 1, cima - 11, 3, 2, PIETRA_L)
    t.punto(vx + 2, cima - 12, PIETRA_L)
    t.rett(vx + 2, cima - 7, 1, 2, CONTORNO)
    if fuoco:
        fuoco_della_fede(t, x + 4, cima - 5)
    else:
        t.rett(x + 3, cima - 13, 1, 11, CONTORNO)
        ST.drappo(t, x + 4, cima - 13, ST.GUBBIO["gioco"], {("vermiglio comunale", 2): VERMIGLIO,
                                                           ("neutri", 4): PIETRA_L, ST.CONTORNO: CONTORNO}, 15, 9)


def chiesa(t, x, base, alto, notte, r):
    """Una chiesa: la facciata a capanna col portale, il rosone, il tetto a coppi, il campanile a lato
    con la cella a bifora e la cuspide."""
    largo = 16
    x0 = x - largo // 2
    cima = base - alto + 8
    t.rett(x0, cima, largo, base - cima, PIETRA_C)
    t.rett(x0 + largo - 3, cima, 3, base - cima, PIETRA)
    t.trapezio(x, cima - 6, cima, 2, largo + 2, COTTO)
    t.trapezio(x, cima - 5, cima - 1, 1, largo - 2, PIETRA_C)
    t.punto(x, cima - 3, CONTORNO)                                       # l'oculo del timpano
    t.ellisse(x - 0.5, cima + 5, 2.2, 2.2, CONTORNO)                     # il rosone
    t.punto(x - 1, cima + 4, PIETRA_L)
    t.rett(x - 2, base - 6, 4, 6, CONTORNO)                              # il portale
    t.rett(x - 1, base - 7, 2, 1, CONTORNO)
    cx = x0 + largo + 1
    t.rett(cx, cima - 10, 5, base - cima + 10, PIETRA_C)
    t.rett(cx + 4, cima - 10, 1, base - cima + 10, PIETRA)
    finestra(t, cx + 1, cima - 7, "bifora", notte, r)
    t.trapezio(cx + 2, cima - 15, cima - 10, 1, 6, COTTO)


def torre(t, x, base, alto, notte, r):
    """Una torre civica: alta e stretta, i merli guelfi, le feritoie a quote diverse, la faccia destra in
    ombra."""
    largo = 9
    x0 = x - largo // 2
    t.rett(x0, base - alto, largo, alto, PIETRA_C)
    t.rett(x0 + largo - 3, base - alto, 3, alto, PIETRA)
    for k in range(0, largo, 3):
        t.rett(x0 + k, base - alto - 2, 2, 2, PIETRA_C)
    t.rett(x0, base - alto + 3, largo, 1, PIETRA_L)
    for y in range(base - alto + 6, base - 4, 6):
        finestra(t, x0 + 2 + r.randint(0, 2), y + r.randint(0, 2), "feritoia", notte, r)


def porta_urbica(t, x, base, alto):
    """Una porta delle mura: la torre-porta coi merli e il fornice ad arco."""
    largo = 12
    x0 = x - largo // 2
    t.rett(x0, base - alto, largo, alto, PIETRA_M)
    t.rett(x0 + largo - 3, base - alto, 3, alto, PIETRA)
    for k in range(0, largo, 3):
        t.rett(x0 + k, base - alto - 2, 2, 2, PIETRA_M)
    t.rett(x0 + 3, base - 7, 5, 7, CONTORNO)
    t.rett(x0 + 4, base - 8, 3, 1, CONTORNO)


def edificio(t, nome, x, base, alto, tipo, notte, r, fuoco=False):
    if nome == "consoli":
        palazzo_dei_consoli(t, x, base, alto, notte, fuoco)
    elif tipo == "chiesa":
        chiesa(t, x, base, alto, notte, r)
    elif tipo == "torre":
        torre(t, x, base, alto, notte, r)
    elif tipo == "porta":
        return                                  # le porte stanno sulle mura (gubbio_disegno)
    else:
        casa(t, x - 9, base, 18, alto, notte, r)


def gubbio_disegno(momento, fuoco=False):
    t = Tela(W, H)
    notte = momento == "notte"
    r = random.Random(7)
    mura = QUADRO - 8
    # le case a gradoni: file parallele al pendio, quelle piu' in alto dietro; la citta' sale verso il
    # monte (a destra) e ogni fila ha case di larghezza, altezza e tono diversi, qualche torre
    for fila in range(4, -1, -1):
        x = 16 + fila * 5
        while x < W - 16:
            largo = r.randint(7, 15)
            sale = (x / W) * 28
            base = int(mura - fila * 8 - sale + r.randint(0, 1))
            torre_g = r.random() < 0.08
            alto = r.randint(16, 24) if torre_g else r.randint(9, 15)
            casa(t, x, base, 6 if torre_g else largo, alto, notte, r, torre=torre_g)
            x += (6 if torre_g else largo) + r.randint(0, 1)
    for nome, mx, base, alto, tipo in sorted(monumenti_dalla_valle(), key=lambda m: m[2]):
        edificio(t, nome, mx, min(base, mura), alto, tipo, notte, r, fuoco)
    # le mura col camminamento a merli guelfi, le torri di cinta
    t.rett(0, mura, W, 8, PIETRA)
    t.rett(0, mura + 6, W, 2, PIETRA_S)
    t.rett(0, mura + 1, W, 1, PIETRA_M)
    for k in range(0, W, 4):
        t.rett(k, mura - 2, 2, 2, PIETRA)
    for k in range(30, W, 96):
        t.rett(k, mura - 6, 7, 14, PIETRA_M)
        t.rett(k + 5, mura - 6, 2, 14, PIETRA)
        for m in range(0, 7, 3):
            t.rett(k + m, mura - 8, 2, 2, PIETRA_M)
    for nome, mx, base, alto, tipo in monumenti_dalla_valle():
        if tipo == "porta":
            porta_urbica(t, mx, mura + 8, 18)
    return t


def gubbio(momento):
    """La citta' sul pendio: le case a gradoni, i monumenti del censimento, il Palazzo dei Consoli col
    drappo di Gubbio, le mura merlate con le porte."""
    return gubbio_disegno(momento), PALETTE_PANORAMA, momento == "notte"


# --- la conca col campo nemico ------------------------------------------------------------------------
def fuoco(t, x, y):
    """Un fuoco del campo, il punto di luce della notte: il cuore 3x3 oro caldo, l'alone acceso di un
    pixel e un bagliore vermiglio a scacchiera intorno. Il tremolio lo fa la scena alternando il colore
    ORO (src/regia.cpp)."""
    for dx in range(-3, 6):
        for dy in range(-3, 6):
            if (dx + dy) % 2 == 0 and ((dx - 1) / 4.5) ** 2 + ((dy - 1) / 4.5) ** 2 <= 1:
                t.punto(x + dx, y + dy, VERMIGLIO)
    t.rett(x - 1, y - 1, 5, 5, ALONE)
    t.rett(x, y, 3, 3, ORO)
    t.punto(x + 1, y - 2, ORO)


def campo(momento):
    """La conca davanti alle mura: i campi, le tende della coalizione e, di notte, i fuochi."""
    t = Tela(W, H)
    notte = momento == "notte"
    r = random.Random(5)
    for y in range(QUADRO - 14, H):
        for x in range(W):
            t.punto(x, y, VERDE_M if (x // 24 + y // 4) % 3 else VERDE_S)
    for k in range(22):
        x = 12 + k * 23 + r.randint(-4, 4)
        y = QUADRO - 6 + r.randint(-4, 2)
        t.trapezio(x, y - 7, y, 1, 11, PIETRA_C if k % 3 else VERMIGLIO)
        t.rett(x, y - 9, 1, 3, CONTORNO)
        if notte and k % 2 == 0:
            fuoco(t, x + 9, y - 3)
    return t, PALETTE_PANORAMA, notte


def fuoco_della_fede(t, x, y):
    """Il fuoco acceso in cima alla torre dei Consoli: una fiamma alta 8 px col cuore oro 3x5, l'alone
    cotto e un bagliore vermiglio largo; si legge da lontano e trema come i fuochi del campo."""
    for dy in range(-12, 6):
        for dx in range(-9, 10):
            if (dx + dy) % 2 == 0 and (dx / 9) ** 2 + (dy / 10) ** 2 <= 1:
                t.punto(x + dx, y + dy, VERMIGLIO)
    t.ellisse(x + 0.5, y - 1, 4, 6, ALONE)
    t.rett(x - 1, y - 4, 3, 5, ORO)
    t.rett(x, y - 7, 1, 3, ORO)
    t.rett(x - 3, y + 2, 7, 1, CONTORNO)          # il braciere


def gubbio_fede(momento):
    """La citta' di notte quando 'sorse il fuoco della Fede': il fuoco al posto del drappo in cima al
    Palazzo dei Consoli."""
    return gubbio_disegno("notte", fuoco=True), PALETTE_PANORAMA, True


PITTORI = {"cielo": cielo, "monte": monte, "gubbio": gubbio, "campo": campo, "gubbio_fede": gubbio_fede}


# --- la vetrata della Basilica ------------------------------------------------------------------------
PALETTE_VETRATA = [("neutri", 0), ("neutri", 0), ("pietra calcarea", 0), ("pietra calcarea", 1), ("pietra calcarea", 3),
                   ("pietra calcarea", 5), ("cielo e acqua", 3), ("cielo e acqua", 4), ("neutri", 4),
                   ("vermiglio comunale", 2), ("oro e bronzo", 3), ("verde dei monti", 2), ("cielo e acqua", 1),
                   ("legno e cuoio", 2), ("pelle", 2), ("neutri", 2)]
V_BUIO, V_PILASTRO, V_SPIGOLO, V_PIETRA, V_PIETRA_L = 1, 2, 3, 4, 5
V_CHIARO, V_CHIARO_L, V_BIANCO, V_ROSSO, V_ORO, V_VERDE, V_BLU, V_LEGNO, V_PELLE, V_GRIGIO = range(6, 16)
VETRI_CHIARI = {V_CHIARO, V_CHIARO_L}
# la bifora, centrata nel quadro (la mappa si vede da x=0 a 240): due lancette e un oculo sotto un arco
# acuto, l'imposta degli archi a y=65 (arco grande) e 70 (lancette), il davanzale a y=100
V_CENTRO, V_LARGA, V_SOGLIA = 120, 80, 100
LANCETTE = ((82, 118), (122, 158))
OCULO = (120, 34, 9)


def ogiva(x, y, x0, x1, imposta, raggio):
    """Dentro un arco acuto da x0 a x1 con l'imposta a y=imposta (sotto, il rettangolo fino al davanzale)?"""
    if not x0 <= x < x1 or y >= V_SOGLIA:
        return False
    if y >= imposta:
        return True
    return (x + 0.5 - (x0 + raggio)) ** 2 + (y + 0.5 - imposta) ** 2 <= raggio ** 2 and \
        (x + 0.5 - (x1 - raggio)) ** 2 + (y + 0.5 - imposta) ** 2 <= raggio ** 2


def nel_vetro(x, y):
    if any(ogiva(x, y, a, b, 70, 27) for a, b in LANCETTE):
        return True
    cx, cy, r = OCULO
    return (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r


def nella_finestra(x, y, bordo=0):
    return ogiva(x, y, V_CENTRO - V_LARGA // 2 - bordo, V_CENTRO + V_LARGA // 2 + bordo, 65, 60 + bordo)


def figure_della_storia(t):
    """La vetrata come la vede chi la guarda oggi: a sinistra i soldati in rotta e uno stendardo
    spezzato, a destra il vescovo con le braccia aperte, nell'oculo la luce. Figure semplici a pezzi di
    vetro: il colore cambia, il piombo segue il bordo."""
    for y in range(0, V_SOGLIA):
        for x in range(V_CENTRO - V_LARGA // 2, V_CENTRO + V_LARGA // 2):
            if nel_vetro(x, y):
                t.punto(x, y, V_BLU if (x // 6 + y // 8) % 2 else V_CHIARO)
    # la terra verde in fondo alle lancette
    for a, b in LANCETTE:
        t.rett(a, 90, b - a, 10, V_VERDE)
    # sinistra: lo stendardo spezzato (asta di legno rotta, drappo rosso a terra) e tre soldati in fuga
    t.linea(86, 88, 96, 58, V_LEGNO, 2)
    t.linea(97, 56, 104, 50, V_LEGNO, 2)
    t.trapezio(92, 74, 86, 12, 4, V_ROSSO)
    for k, (sx, sy) in enumerate(((100, 78), (108, 72), (91, 64))):
        t.rett(sx, sy, 5, 9, V_ROSSO if k % 2 == 0 else V_LEGNO)    # il corpo, chino nella corsa
        t.rett(sx + 1, sy - 4, 4, 4, V_GRIGIO)                      # l'elmo
        t.linea(sx + 5, sy + 2, sx + 9, sy + 6, V_GRIGIO)           # la lancia abbassata
        t.rett(sx, sy + 9, 2, 4, V_LEGNO)
        t.rett(sx + 3, sy + 9, 2, 3, V_LEGNO)
    # destra: il vescovo con le braccia aperte, la mitra d'oro e il pastorale
    t.rett(136, 64, 9, 26, V_BIANCO)
    t.trapezio(140, 70, 90, 9, 14, V_BIANCO)
    t.rett(124, 66, 12, 4, V_BIANCO)
    t.rett(145, 66, 12, 4, V_BIANCO)
    t.rett(124, 64, 3, 3, V_PELLE)
    t.rett(154, 64, 3, 3, V_PELLE)
    t.rett(137, 56, 7, 7, V_PELLE)
    t.trapezio(140, 46, 56, 2, 8, V_ORO)
    t.rett(152, 48, 2, 42, V_ORO)
    t.rett(150, 46, 4, 3, V_ORO)
    t.rett(138, 72, 5, 14, V_ORO)                               # la stola
    # l'oculo: la luce
    cx, cy, r = OCULO
    t.ellisse(cx, cy, r, r, V_ORO)
    t.ellisse(cx, cy, r - 4, r - 4, V_BIANCO)


def vetrata_disegno(vetri):
    """La bifora gotica nell'interno buio della Basilica: i pilastri e l'arco appena accennati, la luce
    che entra di sbieco, la cornice di pietra, i piombi neri. vetri: "chiari" (il prologo), "uno" (un
    solo vetro ha preso colore, l'epilogo), "storia" (la vetrata come la si vede oggi)."""
    t = Tela(W, H, V_BUIO)
    # i pilastri ai lati e l'arco della navata, lo spigolo verso la finestra preso dalla luce
    for px0, spigolo in ((14, 42), (196, 196)):
        t.rett(px0, 0, 30, QUADRO, V_PILASTRO)
        t.rett(spigolo, 0, 2, QUADRO, V_SPIGOLO)
    for x in range(14, 226):
        y = int(14 - 14 * (1 - ((x - 120) / 106) ** 2) ** 0.5) if abs(x - 120) < 106 else 14
        t.rett(x, y, 1, 3, V_PILASTRO)
    # la luce che entra: fasci a scacchiera che scendono a destra dalla finestra fino al pavimento
    for y in range(V_SOGLIA - 30, QUADRO):
        for x in range(V_CENTRO - 30, 196):
            fascio = (x - V_CENTRO - (y - V_SOGLIA + 30) * 1.1) % 26 < 8
            if fascio and not nella_finestra(x, y, 5) and (x + y) % 2 == 0:
                t.punto(x, y, V_PILASTRO)
    # la cornice di pietra (4 px, il bordo in alto a sinistra in luce) e il timpano fra le lancette
    for y in range(QUADRO):
        for x in range(V_CENTRO - V_LARGA, V_CENTRO + V_LARGA):
            if nella_finestra(x, y, 4) and not nella_finestra(x, y, 0):
                t.punto(x, y, V_PIETRA_L if x < V_CENTRO and not nella_finestra(x + 1, y + 1, 4) else V_PIETRA)
            elif nella_finestra(x, y):
                t.punto(x, y, V_PIETRA)
    t.rett(V_CENTRO - V_LARGA // 2 - 6, V_SOGLIA, V_LARGA + 12, 3, V_PIETRA_L)
    t.rett(V_CENTRO - V_LARGA // 2 - 6, V_SOGLIA + 3, V_LARGA + 12, 1, V_PILASTRO)
    # i vetri
    if vetri == "storia":
        figure_della_storia(t)
    else:
        for y in range(V_SOGLIA):
            for x in range(V_CENTRO - V_LARGA // 2, V_CENTRO + V_LARGA // 2):
                if nel_vetro(x, y):
                    luce = (x - 82) + (y - 30) // 2 < 40
                    t.punto(x, y, V_CHIARO_L if luce and (x + y) % 3 else V_CHIARO)
        if vetri == "uno":
            # il vetro del Bottaccione, in basso nella lancetta destra: il gigante di ferro sopra gli
            # archi dell'acquedotto, sotto tre uomini coi ceri
            vx, vy, vw, vh = 124, 74, 32, 26
            t.rett(vx, vy, vw, vh, V_BLU)
            for k in range(3):
                t.rett(vx + 2 + k * 10, vy + vh - 9, 6, 7, V_LEGNO)
            t.rett(vx + 2, vy + vh - 13, vw - 4, 4, V_PIETRA)
            t.rett(vx + vw // 2 - 3, vy + 2, 6, 9, V_GRIGIO)
            for k in range(3):
                t.rett(vx + 4 + k * 10, vy + vh - 4, 3, 4, V_ROSSO)
                t.punto(vx + 5 + k * 10, vy + vh - 5, V_ORO)
            t.rett(vx, vy + vh - 2, vw, 2, V_VERDE)
    # i piombi: lungo i bordi fra un colore e l'altro, piu' le traverse di ferro ogni 12 px e, nei vetri
    # chiari, i montanti ogni 9 px
    vetro = [[nel_vetro(x, y) for x in range(W)] for y in range(QUADRO)]
    colore = [r[:] for r in t.px[:QUADRO]]
    for y in range(QUADRO - 1):
        for x in range(W - 1):
            if not vetro[y][x]:
                continue
            bordo = any(vetro[v][u] and colore[v][u] != colore[y][x] and not {colore[v][u], colore[y][x]} <= VETRI_CHIARI
                        for u, v in ((x + 1, y), (x, y + 1)))
            if bordo or y % 12 == 0 or (vetri != "storia" and (x - 82) % 9 == 0 and y > 46):
                t.punto(x, y, V_BUIO)
    # il piombo di contorno: il primo pixel di pietra intorno a ogni vetro
    for y in range(1, QUADRO - 1):
        for x in range(1, W - 1):
            if not vetro[y][x] and nella_finestra(x, y) and any(vetro[v][u] for u, v in
                                                               ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))):
                t.punto(x, y, V_BUIO)
    return t


def vetrata(momento):
    """La vetrata della Basilica: nel prologo (giorno) i vetri tutti chiari, all'epilogo (alba) uno solo
    ha preso colore."""
    return vetrata_disegno("uno" if momento == "alba" else "chiari"), PALETTE_VETRATA, False


def vetrata_storia(momento):
    """La vetrata a colori, come la vede chi la guarda oggi (la prima inquadratura del prologo)."""
    return vetrata_disegno("storia"), PALETTE_VETRATA, False


# --- la pergamena dell'Umbria con gli stendardi -------------------------------------------------------
import sys as _sys  # noqa: E402

_sys.path.insert(0, os.path.join(RADICE, "stile"))
import stile as _S  # noqa: E402

FONT = _S.carica("font")
MAPPA = json.load(open(os.path.join(RADICE, "dati", "mappa_umbria.json"), encoding="utf-8"))
TESTI = os.path.join(RADICE, "testi", "copione.testi")

PALETTE_PERGAMENA = [("neutri", 0), ("legno e cuoio", 0), ("legno e cuoio", 1), ("legno e cuoio", 2), ("pelle", 2),
                     ("pelle", 1), ("pelle", 0), ("vermiglio comunale", 1), ("vermiglio comunale", 2), ("neutri", 4),
                     ("oro e bronzo", 3), ("cielo e acqua", 1), ("verde dei monti", 1), ("cielo e acqua", 2),
                     ("oro e bronzo", 2), ("legno e cuoio", 3)]
P_INCHIOSTRO, P_ASTA, P_CARTA, P_CARTA_S, P_RILIEVO = 2, 3, 4, 5, 6
P_ORO, P_FIUME, P_LAGO, P_ALONE = 10, 11, 13, 14
INDICI_PERGAMENA = {r: i for i, r in reversed(list(enumerate(PALETTE_PERGAMENA))) if i}

# la proiezione: nord in alto, la stessa scala in orizzontale e in verticale (px per km), il quadro
# fra le bande e' 240x112 e la mappa ci sta tutta (non scorre)
PX_PER_KM = 1.05
KM_PER_GRADO_LAT = 111.2
KM_PER_GRADO_LON = 111.2 * math.cos(math.radians(43.15))
ORIGINE = (43.55, 12.57, 126, 8)          # lat, lon -> x, y: Cagli in cima, Gubbio a x=126
BANDIERA = 10                             # i drappi della coalizione sulla mappa, 10x10
COLONNA_OVEST, COLONNA_EST = 66, 164
DIVISORIO_LON = 12.63                     # a ovest di qui il drappo va nella colonna di sinistra


def proietta(lat, lon):
    la0, lo0, x0, y0 = ORIGINE
    return (x0 + (lon - lo0) * KM_PER_GRADO_LON * PX_PER_KM, y0 + (la0 - lat) * KM_PER_GRADO_LAT * PX_PER_KM)


def scrivi(t, x, y, testo, colore):
    for ch in _S.normalizza(FONT, testo):
        g = FONT["glifi"][ch]
        for r, riga in enumerate(g):
            for k, v in enumerate(riga):
                if v == "#":
                    t.punto(x + k, y + r, colore)
        x += len(g[0]) + FONT["spaziatura"]


def larghezza(testo):
    return _S.larghezza_testo(FONT, _S.normalizza(FONT, testo))


def battuta(ident):
    for riga in open(TESTI, encoding="utf-8"):
        if riga.startswith(ident + " "):
            return riga.split("|", 2)[2].strip()
    raise KeyError(ident)


def nominate(battute):
    """{id: come la chiama il narratore} delle citta' della coalizione nominate in quelle battute (il
    nome piu' lungo, a parole intere dall'inizio, che compare nel testo: 'Fossato', 'Gualdo Tadino')."""
    testo = " ".join(battuta(b) for b in battute)
    out = {}
    for c in ST.COALIZIONE:
        parole = c["nome"].split()
        for n in range(len(parole), 0, -1):
            if " ".join(parole[:n]) in testo:
                out[c["id"]] = " ".join(parole[:n])
                break
    return out


def posti_delle_bandiere():
    """{id: (x_drappo, y_drappo, x_citta, y_citta)} delle undici citta': il punto dov'e' la citta' e il
    drappo nella colonna di ovest o di est, all'altezza della citta' o spinto quanto basta perche' i
    drappi non si tocchino."""
    out = {}
    for colonna, ovest in ((COLONNA_OVEST, True), (COLONNA_EST, False)):
        qui = sorted((proietta(*MAPPA["citta"][c["id"]])[1], c["id"]) for c in ST.COALIZIONE
                     if (MAPPA["citta"][c["id"]][1] < DIVISORIO_LON) == ovest)
        ys = [y - BANDIERA // 2 for y, _ in qui]
        passo = BANDIERA + 3
        for i in range(1, len(ys)):
            ys[i] = max(ys[i], ys[i - 1] + passo)
        ys[-1] = min(ys[-1], QUADRO - 6 - BANDIERA)
        for i in range(len(ys) - 2, -1, -1):
            ys[i] = min(ys[i], ys[i + 1] - passo)
        for (_, ident), y in zip(qui, ys):
            cx, cy = proietta(*MAPPA["citta"][ident])
            out[ident] = (colonna, int(y), int(round(cx)), int(round(cy)))
    return out


def linea_geo(t, punti, colore, tratteggio=0):
    xy = [proietta(*p) for p in punti]
    k = 0
    for (x0, y0), (x1, y1) in zip(xy, xy[1:]):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n):
            if not tratteggio or (k // tratteggio) % 2 == 0:
                t.punto(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n), colore)
            k += 1


def collina(t, x, y, largo, alto):
    """Un monte a tratto di penna: il pendio in ombra a destra (la luce viene da sinistra)."""
    for dy in range(alto):
        m = largo * (dy + 1) // (2 * alto)
        t.rett(x - m, y - alto + dy, 2 * m + 1, 1, P_RILIEVO if dy else P_INCHIOSTRO)
        t.punto(x - m, y - alto + dy, P_INCHIOSTRO)
        t.punto(x + m, y - alto + dy, P_INCHIOSTRO)


def pergamena_con(battute):
    """La pergamena dell'Umbria: nord in alto e una scala sola (dati/mappa_umbria.json), l'Appennino a
    est, il Monte Ingino dietro Gubbio, il Tevere, il Chiascio, il Topino e il Trasimeno, le strade che
    portano a Gubbio. Gli undici stendardi (tools/stendardi.py) stanno in due colonne con un filo fino
    alla loro citta'; il nome compare accanto quando il narratore lo dice (le battute date). Gubbio e'
    segnata d'oro, col suo drappo piu' grande."""
    t = Tela(W, H, P_CARTA)
    for y in range(H):
        for x in range(W):
            if (x % 8, y % 8) in ((3, 5), (7, 1)):
                t.punto(x, y, P_CARTA_S)
    t.rett(0, 0, W, 2, P_INCHIOSTRO)
    t.rett(0, QUADRO - 2, W, 2, P_INCHIOSTRO)
    # l'Appennino: colline lungo il crinale, il Monte Ingino dietro Gubbio
    xy = [proietta(*p) for p in MAPPA["appennino"]]
    for (x0, y0), (x1, y1) in zip(xy, xy[1:]):
        n = int(abs(y1 - y0) // 7) + 1
        for i in range(n):
            collina(t, int(x0 + (x1 - x0) * i / n) + (i % 2) * 3, int(y0 + (y1 - y0) * i / n), 9, 5)
    ix, iy = proietta(*MAPPA["luoghi"]["monte_ingino"])
    collina(t, int(ix), int(iy) + 1, 11, 6)
    # il Trasimeno, i fiumi, le strade
    lx, ly = proietta(*MAPPA["luoghi"]["trasimeno"])
    t.ellisse(lx, ly, 9, 6, P_FIUME)
    t.ellisse(lx, ly, 8, 5, P_LAGO)
    for corso in MAPPA["fiumi"].values():
        linea_geo(t, corso, P_FIUME)
    for strada in MAPPA["strade"].values():
        linea_geo(t, strada, P_INCHIOSTRO, tratteggio=2)
    sx, sy = proietta(*MAPPA["luoghi"]["scheggia"])
    t.rett(int(sx) - 1, int(sy), 3, 1, P_INCHIOSTRO)          # il passo della Scheggia
    # gli stendardi della coalizione, il filo fino alla citta' e il nome se e' stato detto
    nomi = nominate(battute)
    for ident, (fx, fy, cx, cy) in posti_delle_bandiere().items():
        ovest = fx == COLONNA_OVEST
        asta = fx + BANDIERA + 1 if ovest else fx - 2
        t.rett(asta, fy - 2, 1, BANDIERA + 5, P_ASTA)
        ax, ay = asta, fy + BANDIERA + 2
        n = max(abs(cx - ax), abs(cy - ay), 1)
        for i in range(0, n, 2):
            t.punto(round(ax + (cx - ax) * i / n), round(ay + (cy - ay) * i / n), P_INCHIOSTRO)
        t.rett(cx - 1, cy - 1, 3, 3, ST.indici_o(INDICI_PERGAMENA, ST.CONTORNO))
        ST.drappo(t, fx, fy, ST.per_id(ident)["gioco"], INDICI_PERGAMENA, BANDIERA, BANDIERA)
        if ident in nomi:
            nome = nomi[ident]
            scrivi(t, fx - 4 - larghezza(nome) if ovest else fx + BANDIERA + 4, fy, nome, 1)
    # Gubbio: il punto d'oro, il drappo grande col monte a cinque cime, il nome sempre scritto
    gx, gy = (int(round(v)) for v in proietta(*MAPPA["citta"]["gubbio"]))
    t.ellisse(gx + 0.5, gy + 0.5, 4, 4, P_ALONE)
    t.ellisse(gx + 0.5, gy + 0.5, 3, 3, P_ORO)
    t.rett(gx - 1, gy - 1, 3, 3, 1)
    t.rett(gx - 5, gy - 22, 1, 20, P_ASTA)
    ST.drappo(t, gx - 23, gy - 22, ST.GUBBIO["gioco"], INDICI_PERGAMENA, 17, 11)
    scrivi(t, gx - 6 - larghezza("Gubbio"), gy - 3, "Gubbio", 1)
    return t


def pergamena(momento):
    """La pergamena all'inizio della guerra: gli stendardi, nessun nome ancora."""
    return pergamena_con([]), PALETTE_PERGAMENA, False


def pergamena_nomi1(momento):
    """... con i nomi detti in 'Spoleto e Foligno. Assisi, Spello e Bettona. Todi e Cagli.'"""
    return pergamena_con(["R_P_02_01"]), PALETTE_PERGAMENA, False


def pergamena_nomi2(momento):
    """... e con quelli di 'Nocera, Gualdo Tadino e Fossato. E sopra tutte, Perugia.'"""
    return pergamena_con(["R_P_02_01", "R_P_02_02"]), PALETTE_PERGAMENA, False


PITTORI.update({"vetrata": vetrata, "vetrata_storia": vetrata_storia, "pergamena": pergamena,
                "pergamena_nomi1": pergamena_nomi1, "pergamena_nomi2": pergamena_nomi2})

# i piani di C2, Le undici bandiere (tools/pittore_c2.py); i fanti hanno il passo (due pose)
import pittore_c2 as C2  # noqa: E402

PITTORI.update(C2.PITTORI)
CON_PASSO = C2.CON_PASSO

# i piani di C3, le presentazioni a fermo immagine (tools/pittore_c3.py)
import pittore_c3 as C3  # noqa: E402

PITTORI.update(C3.PITTORI)
