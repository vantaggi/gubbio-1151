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

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 512, 256
QUADRO = 112                     # le righe di mappa che si vedono fra le bande
MOMENTI = ("giorno", "alba", "notte")

# --- palette ------------------------------------------------------------------------------------------
PALETTE_CIELO = [("neutri", 0), ("cielo e acqua", 0), ("cielo e acqua", 1), ("cielo e acqua", 2), ("cielo e acqua", 3),
                 ("cielo e acqua", 4), ("oro e bronzo", 1), ("oro e bronzo", 2), ("oro e bronzo", 3),
                 ("vermiglio comunale", 1), ("vermiglio comunale", 3), ("neutri", 0), ("neutri", 1), ("neutri", 2),
                 ("neutri", 4), ("cotto e coppi", 4)]
# panorama: 0 trasparente, poi contorno, pietra, cotto, vermiglio, verde, oro (fuochi, finestre accese)
PALETTE_PANORAMA = [("neutri", 0), ("neutri", 0), ("pietra calcarea", 1), ("pietra calcarea", 2), ("pietra calcarea", 3),
                    ("pietra calcarea", 4), ("pietra calcarea", 5), ("cotto e coppi", 1), ("cotto e coppi", 2),
                    ("cotto e coppi", 3), ("vermiglio comunale", 2), ("verde dei monti", 0), ("verde dei monti", 1),
                    ("verde dei monti", 2), ("verde dei monti", 3), ("oro e bronzo", 3)]
CONTORNO, PIETRA_S, PIETRA, PIETRA_M, PIETRA_C, PIETRA_L = 1, 2, 3, 4, 5, 6
COTTO_S, COTTO, COTTO_C, VERMIGLIO = 7, 8, 9, 10
VERDE_S, VERDE_M, VERDE, VERDE_C, ORO = 11, 12, 13, 14, 15


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


def edificio(t, x, base, alto, tipo, notte):
    largo = {"torre": 14, "palazzo": 18, "chiesa": 16, "porta": 8, "case": 12}[tipo]
    x0 = x - largo // 2
    if tipo == "chiesa":
        t.rett(x0, base - alto + 6, largo, alto - 6, PIETRA_C)
        t.rett(x0 + largo - 4, base - alto + 6, 4, alto - 6, PIETRA)
        t.trapezio(x, base - alto, base - alto + 6, 2, largo + 2, COTTO)
        t.rett(x0 + largo - 3, base - alto - 6, 4, 12, PIETRA_C)
        t.rett(x - 1, base - alto + 9, 3, 3, CONTORNO)
    elif tipo == "torre":
        corpo = alto * 2 // 3
        t.rett(x0, base - corpo, largo, corpo, PIETRA_L)
        t.rett(x0 + largo - 4, base - corpo, 4, corpo, PIETRA_M)
        for k in range(0, largo, 3):
            t.rett(x0 + k, base - corpo - 2, 2, 2, PIETRA_L)
        t.rett(x0 + 2, base - alto, 5, alto - corpo, PIETRA_L)
        t.rett(x0 + 5, base - alto, 2, alto - corpo, PIETRA_M)
        t.rett(x0 + 3, base - alto + 3, 2, 3, CONTORNO)
        for fy in range(base - corpo + 4, base - 3, 7):
            for fx in range(x0 + 2, x0 + largo - 4, 4):
                t.rett(fx, fy, 2, 3, ORO if notte and (fx + fy) % 3 == 0 else CONTORNO)
    elif tipo == "porta":
        t.rett(x0, base - alto, largo, alto, PIETRA_M)
        for k in range(0, largo, 3):
            t.rett(x0 + k, base - alto - 2, 2, 2, PIETRA_M)
        t.rett(x0 + 2, base - 5, 4, 5, CONTORNO)
    else:
        t.rett(x0, base - alto, largo, alto, PIETRA_C)
        t.rett(x0 + largo - 4, base - alto, 4, alto, PIETRA)
        t.rett(x0, base - alto - 2, largo, 2, COTTO)
        for fx in range(x0 + 2, x0 + largo - 4, 4):
            t.rett(fx, base - alto + 4, 2, 3, ORO if notte and fx % 3 == 0 else CONTORNO)


def gubbio(momento):
    """La citta' sul pendio: le case a gradoni, i monumenti del censimento, il drappo rosso sulla torre
    dei Consoli, le mura in basso."""
    t = Tela(W, H)
    notte = momento == "notte"
    r = random.Random(7)
    mura = QUADRO - 8
    # le case: dal basso a sinistra in su verso destra, come sale la citta'
    x = 20
    while x < W - 20:
        w = r.randint(8, 14)
        cima = int(mura - 14 - (x / W) * 26 - r.randint(0, 8))
        t.rett(x, cima, w, mura - cima, PIETRA_M if (x // w) % 2 else PIETRA)
        t.rett(x + w - 2, cima, 2, mura - cima, PIETRA_S)
        t.rett(x, cima - 2, w, 2, COTTO if r.random() < 0.6 else COTTO_C)
        for fy in range(cima + 4, mura - 3, 6):
            for fx in range(x + 2, x + w - 3, 5):
                t.punto(fx, fy, ORO if notte and r.random() < 0.15 else CONTORNO)
        x += w
    for nome, mx, base, alto, tipo in sorted(monumenti_dalla_valle(), key=lambda m: m[2]):
        edificio(t, mx, min(base, mura), alto, tipo, notte)
        if nome == "consoli":
            # il drappo di Gubbio: rosso col monte bianco
            t.rett(mx - 4, min(base, mura) - alto - 10, 1, 10, CONTORNO)
            t.rett(mx - 3, min(base, mura) - alto - 10, 7, 5, VERMIGLIO)
            t.rett(mx - 2, min(base, mura) - alto - 7, 5, 1, PIETRA_L)
    # le mura col camminamento merlato
    t.rett(0, mura, W, 8, PIETRA)
    for k in range(0, W, 4):
        t.rett(k, mura - 2, 2, 2, PIETRA)
    t.rett(0, mura + 6, W, 2, PIETRA_S)
    return t, PALETTE_PANORAMA, notte


# --- la conca col campo nemico ------------------------------------------------------------------------
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
            t.ellisse(x + 8, y - 1, 2, 2, ORO)
            t.punto(x + 8, y - 4, VERMIGLIO)
    return t, PALETTE_PANORAMA, notte


PITTORI = {"cielo": cielo, "monte": monte, "gubbio": gubbio, "campo": campo}
