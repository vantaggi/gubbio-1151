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
                t.punto(fx, fy, ORO if notte and r.random() < 0.3 else CONTORNO)
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
    """La citta' di notte quando 'sorse il fuoco della Fede': il fuoco al posto del drappo in cima alla
    torre dei Consoli."""
    t, palette, _ = gubbio("notte")
    for nome, mx, base, alto, _ in monumenti_dalla_valle():
        if nome == "consoli":
            cima = min(base, QUADRO - 8) - alto
            t.rett(mx - 4, cima - 10, 8, 10, 0)
            fuoco_della_fede(t, mx, cima - 3)
    return t, palette, True


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
PALETTE_PERGAMENA = [("neutri", 0), ("neutri", 0), ("legno e cuoio", 1), ("legno e cuoio", 3), ("oro e bronzo", 2),
                     ("oro e bronzo", 3), ("pelle", 2), ("pelle", 1), ("vermiglio comunale", 1), ("vermiglio comunale", 2),
                     ("neutri", 4), ("verde dei monti", 2), ("cielo e acqua", 2), ("pietra calcarea", 3), ("neutri", 2),
                     ("oro e bronzo", 1)]

# le undici citta' della coalizione (README del copione, Sez. 3 del GDD), dove stanno rispetto a Gubbio
CITTA_COALIZIONE = [("Perugia", 150, 74, True), ("Spoleto", 320, 92, False), ("Foligno", 290, 80, False),
                    ("Assisi", 236, 76, False), ("Spello", 262, 82, False), ("Bettona", 206, 84, False),
                    ("Todi", 176, 98, False), ("Cagli", 214, 22, False), ("Nocera", 316, 58, False),
                    ("Gualdo Tadino", 306, 42, False), ("Fossato", 282, 32, False)]
GUBBIO_SULLA_MAPPA = (238, 46)


def pergamena(momento):
    """La pergamena dell'Umbria medievale: l'inchiostro dei fiumi e dei colli, gli undici stendardi della
    coalizione piantati sui valichi (Perugia il piu' grande, rosso col grifo d'argento coronato d'oro),
    Gubbio al centro col suo drappo rosso e il monte bianco a cinque cime."""
    t = Tela(W, H, 7)
    for y in range(H):
        for x in range(W):
            if (x * 7 + y * 13) % 29 == 0:
                t.punto(x, y, 6)
    t.rett(0, 0, W, 3, 2)
    t.rett(0, 109, W, 3, 2)
    for k in range(6):
        cx = 60 + k * 70
        t.ellisse(cx, 60 + (k % 2) * 20, 18, 7, 13)
    for x in range(40, 480):
        y = int(70 + 14 * math.sin(x / 40.0))
        t.punto(x, y, 12)
    for nome, x, y, grande in CITTA_COALIZIONE:
        alto = 22 if grande else 12
        t.rett(x, y - alto, 1, alto, 2)
        largo = 12 if grande else 7
        t.rett(x + 1, y - alto, largo, alto // 2, 9 if grande else 8)
        if grande:
            t.rett(x + 4, y - alto + 2, 5, 6, 10)
            t.rett(x + 5, y - alto, 3, 2, 5)
        t.ellisse(x, y, 2, 1, 2)
    gx, gy = GUBBIO_SULLA_MAPPA
    t.rett(gx, gy - 12, 1, 12, 2)
    t.rett(gx + 1, gy - 12, 8, 6, 9)
    for k in range(5):
        t.punto(gx + 2 + k, gy - 8 - (k % 2), 10)
        t.punto(gx + 2 + k, gy - 7, 10)
    return t, PALETTE_PERGAMENA, False


PITTORI.update({"vetrata": vetrata, "vetrata_storia": vetrata_storia, "pergamena": pergamena})
