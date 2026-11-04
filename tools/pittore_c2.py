"""I piani di C2, Le undici bandiere (dentro A1-01): l'esercito della coalizione che sale dalla conca,
l'araldo di Perugia a cavallo davanti al Palazzo dei Consoli, la pergamena insanguinata ai piedi di
Ubaldo e il colpo del pastorale sulla pietra (C2P).

Ogni figura e' disegnata alla sua misura (niente pixel ingranditi): i fanti lontani alti 8 px, quelli in
mezzo 12, quelli vicini 18. I fanti hanno due pose: le gambe di una posa nel colore 13, quelle
dell'altra nel 14, e dietro le gambe la fascia del prato nel colore 12; il 14 ha lo stesso colore del
12, e la scena scambia 13 e 14 (src/regia.cpp): le gambe che non ci sono spariscono nel prato. Le
bandiere e le tuniche vengono dagli stendardi dei dati (tools/stendardi.py).

Un pittore riceve il momento e ritorna (tela, palette, notte), come in tools/pittore_panorami.py.
"""
import math
import random

import stendardi as ST
from genera_battaglia import Tela

W, H = 512, 256
QUADRO = 112

# --- l'esercito -----------------------------------------------------------------------------------------
PALETTE_FANTI = [("neutri", 0), ("legno e cuoio", 0), ("vermiglio comunale", 1), ("vermiglio comunale", 2),
                 ("neutri", 4), ("oro e bronzo", 3), ("legno e cuoio", 2), ("cielo e acqua", 1), ("verde dei monti", 1),
                 ("neutri", 1), ("neutri", 2), ("pelle", 1), ("verde dei monti", 2), ("legno e cuoio", 1),
                 ("verde dei monti", 2), ("neutri", 3)]
F_NERO, F_FERRO_S, F_FERRO, F_FERRO_C, F_PELLE = 1, 9, 10, 15, 11
F_PRATO, F_GAMBE_A, F_GAMBE_B, F_ASTA = 12, 13, 14, 6
INDICI_FANTI = {r: i for i, r in reversed(list(enumerate(PALETTE_FANTI))) if i}
CON_PASSO = {"fanti_lontani", "fanti_medi", "fanti_vicini"}

# le tre file: (altezza dei fanti, piedi a y, passo fra due fanti, ogni quanti fanti un alfiere, drappo)
FILE = {"fanti_lontani": (8, 54, 7, 4, 8), "fanti_medi": (12, 80, 10, 4, 10), "fanti_vicini": (18, 110, 15, 3, 12)}


def fante(t, x, piedi, alto, tunica):
    """Un fante di profilo verso sinistra, alto 'alto': il cappello di ferro, il viso, la tunica coi
    colori della sua citta', la lancia; le gambe nelle due pose (colori 13 e 14)."""
    testa = max(2, alto // 5)
    busto = alto * 2 // 5
    gambe = alto - testa - busto
    largo = max(3, alto // 3)
    y_testa = piedi - alto
    # le gambe: la posa A a forbice (colore 13), la posa B unite (colore 14)
    for k in range(gambe):
        apri = (k * largo) // (2 * gambe) + 1
        t.punto(x - apri // 2, piedi - gambe + k, F_GAMBE_A)
        t.punto(x + largo - 1 + apri // 2 - 1, piedi - gambe + k, F_GAMBE_A)
    for k in range(gambe):
        if (x, piedi - gambe + k) != (x, piedi - gambe):
            t.punto(x + 1, piedi - gambe + k, F_GAMBE_B)
            t.punto(x + largo - 2, piedi - gambe + k, F_GAMBE_B)
    t.rett(x, piedi - gambe, largo, 1, F_NERO)                      # la cintura
    # la tunica e il braccio
    t.rett(x, y_testa + testa, largo, busto, tuple(tunica) in INDICI_FANTI and INDICI_FANTI[tuple(tunica)] or F_FERRO)
    t.rett(x + largo - 1, y_testa + testa, 1, busto, F_NERO if alto >= 12 else F_FERRO_S)
    # la testa e il cappello di ferro a tesa larga
    t.rett(x + largo // 2 - testa // 2, y_testa + 1, testa, testa, F_PELLE)
    t.rett(x + largo // 2 - testa // 2 - 1, y_testa, testa + 2, max(1, testa // 2), F_FERRO)
    if alto >= 12:
        t.punto(x + largo // 2 - testa // 2 - 1, y_testa, F_FERRO_C)
    # la lancia, piu' alta del fante, la punta di ferro
    lx = x - 1
    t.rett(lx, y_testa - alto // 2, 1, alto + alto // 2 - 1, F_ASTA)
    t.rett(lx, y_testa - alto // 2 - max(1, alto // 8), 1, max(1, alto // 8), F_FERRO_C)


def fila(nome):
    """Una fila di fanti sul prato, con gli alfieri delle undici citta' a turno."""
    alto, piedi, passo, ogni, drappo = FILE[nome]
    t = Tela(W, H)
    gambe = alto - max(2, alto // 5) - alto * 2 // 5
    t.rett(0, piedi - gambe, W, gambe + 3, F_PRATO)
    for x in range(0, W, 5):
        t.punto(x + (x // 5) % 3, piedi + 1, F_FERRO_S if alto >= 12 else F_PRATO)
    r = random.Random(len(nome))
    citta = ST.COALIZIONE
    k = 0
    for x in range(4 + (len(nome) % 3) * 3, W - passo, passo):
        c = citta[(k // ogni + len(nome)) % len(citta)]
        base = piedi + r.randint(-1, 0)
        fante(t, x, base, alto, c["gioco"]["campo"])
        if k % ogni == 0:
            # l'alfiere: l'asta alta e il drappo della sua citta'
            ax = x - 1
            cima = base - alto - drappo - alto // 2
            t.rett(ax, cima, 1, base - cima - 2, F_ASTA)
            ST.drappo(t, ax + 1, cima + 1, c["gioco"], INDICI_FANTI, drappo, drappo)
        k += 1
    return t


def fanti_lontani(momento):
    return fila("fanti_lontani"), PALETTE_FANTI, False


def fanti_medi(momento):
    return fila("fanti_medi"), PALETTE_FANTI, False


def fanti_vicini(momento):
    return fila("fanti_vicini"), PALETTE_FANTI, False


# --- la conca vista da Gubbio ---------------------------------------------------------------------------
PALETTE_COLLI = [("neutri", 0), ("neutri", 0), ("cielo e acqua", 2), ("cielo e acqua", 3), ("cielo e acqua", 4),
                 ("neutri", 4), ("verde dei monti", 0), ("verde dei monti", 1), ("verde dei monti", 2),
                 ("verde dei monti", 3), ("verde dei monti", 4), ("pietra calcarea", 2), ("pietra calcarea", 4),
                 ("cotto e coppi", 2), ("pelle", 1), ("legno e cuoio", 1)]


def colli(momento):
    """La conca a sud di Gubbio di mattina: il cielo, i colli lontani a strati sempre piu' chiari, la
    pianura a campi, la strada che sale verso la citta' e un borgo sul colle."""
    t = Tela(W, H, 4)
    for y in range(18):
        for x in range(W):
            t.punto(x, y, 2 if y < 6 or (y < 12 and (x + y) % 2) else 3)
    r = random.Random(4)
    for _ in range(5):
        cx, cy = r.randrange(W), r.randint(10, 26)
        for k in range(4):
            t.ellisse(cx + k * 7, cy - (k % 2) * 2, 8, 3, 5)
    for strato, (y0, ampio, colore) in enumerate(((44, 9, 9), (54, 7, 8), (64, 5, 7))):
        for x in range(W):
            top = int(y0 - ampio * (0.5 + 0.5 * math.sin(x / (40.0 - strato * 8) + strato)))
            for y in range(top, QUADRO):
                t.punto(x, y, colore)
            t.punto(x, top, colore + 1)
    for y in range(66, QUADRO):
        for x in range(W):
            campo = (x // 34 + (y - 66) // 9) % 3
            t.punto(x, y, (7, 8, 9)[campo] if (x + y) % 5 else 6)
    for y in range(66, QUADRO):
        x = int(250 + (y - 66) * 2.2)
        t.rett(x, y, 3 + (y - 66) // 10, 1, 14)
    # un borgo sul colle a destra
    for k, (bx, alto) in enumerate(((400, 8), (409, 11), (418, 7), (426, 9))):
        t.rett(bx, 48 - alto, 8, alto, 12 if k % 2 else 11)
        t.rett(bx, 48 - alto - 1, 8, 1, 13)
    return t, PALETTE_COLLI, False


# --- l'araldo di Perugia ---------------------------------------------------------------------------------
def grifo(t, x, y, colore, secondo):
    """Il grifo di Perugia della tavola (8x8), nel punto (x, y)."""
    for r, riga in enumerate(ST.FIGURE["grifo"]):
        for k, v in enumerate(riga):
            if v == "#":
                t.punto(x + k, y + r, colore)
            elif v == "o":
                t.punto(x + k, y + r, secondo)


def araldo(momento):
    """L'araldo a cavallo, di profilo verso sinistra: il cavallo bruno con la gualdrappa rossa e il grifo
    bianco, il cavaliere col sopravveste di Perugia, l'elmo, la lancia alzata col pennone del grifo."""
    t = Tela(W, H)
    rosso, bianco, oro = INDICI_FANTI[("vermiglio comunale", 1)], INDICI_FANTI[("neutri", 4)], INDICI_FANTI[("oro e bronzo", 3)]
    bruno, bruno_s = F_ASTA, 13                                      # il 13 qui non scambia: niente passo
    cx, suolo = 196, 108
    # le zampe: una anteriore alzata (il passo), le altre a terra
    for zx, alzata in ((cx - 16, True), (cx - 11, False), (cx + 12, False), (cx + 17, False)):
        if alzata:
            t.rett(zx, suolo - 24, 2, 8, bruno_s)
            t.rett(zx - 3, suolo - 17, 4, 2, bruno_s)
        else:
            t.rett(zx, suolo - 24, 3, 22, bruno if zx < cx + 15 else bruno_s)
            t.rett(zx - 1, suolo - 2, 4, 2, F_NERO)
    # il corpo, il collo, la testa, la coda
    t.ellisse(cx, suolo - 32, 22, 10, bruno)
    t.linea(cx - 16, suolo - 36, cx - 25, suolo - 52, bruno, 9)          # il collo, inclinato in avanti
    t.linea(cx - 22, suolo - 56, cx - 21, suolo - 40, bruno_s, 2)        # la criniera
    t.linea(cx - 27, suolo - 54, cx - 37, suolo - 45, bruno, 6)          # la testa, il muso in basso
    t.rett(cx - 40, suolo - 46, 4, 3, bruno_s)                           # il muso
    t.punto(cx - 29, suolo - 54, F_NERO)                                 # l'occhio
    t.rett(cx - 26, suolo - 60, 2, 4, bruno_s)                           # l'orecchio
    for k in range(14):
        t.punto(cx + 22 + k // 3, suolo - 36 + k, bruno_s)
        t.punto(cx + 23 + k // 3, suolo - 36 + k, bruno_s)
    # la gualdrappa rossa col bordo d'oro e il grifo bianco
    t.rett(cx - 14, suolo - 40, 34, 18, rosso)
    t.rett(cx - 14, suolo - 23, 34, 1, oro)
    grifo(t, cx + 2, suolo - 37, bianco, oro)
    # il cavaliere: la gamba, il sopravveste rosso col grifo, il braccio, l'elmo
    t.rett(cx - 4, suolo - 44, 5, 16, F_FERRO)
    t.rett(cx - 6, suolo - 64, 13, 22, rosso)
    grifo(t, cx - 3, suolo - 60, bianco, oro)
    t.rett(cx - 10, suolo - 60, 6, 4, F_FERRO)
    t.rett(cx - 3, suolo - 73, 8, 9, F_FERRO)
    t.rett(cx + 3, suolo - 73, 2, 9, F_FERRO_S)
    t.rett(cx - 3, suolo - 70, 6, 1, F_NERO)                         # la feritoia dell'elmo
    t.rett(cx - 1, suolo - 76, 3, 3, rosso)                          # il cimiero
    # la lancia alzata col pennone del grifo
    t.linea(cx - 9, suolo - 50, cx - 36, suolo - 104, F_ASTA, 2)
    t.trapezio(cx - 44, suolo - 104, suolo - 96, 2, 2, F_FERRO_C)
    for k in range(14):
        alto = 8 - k // 2
        t.rett(cx - 33 + k, suolo - 104 + (8 - alto) // 2 + k // 3, 1, alto, rosso if k < 9 else bianco)
    return t, PALETTE_FANTI, False


# --- il Palazzo dei Consoli dalla piazza -----------------------------------------------------------------
PALETTE_LOGGIATO = [("neutri", 0), ("legno e cuoio", 0), ("cielo e acqua", 3), ("cielo e acqua", 4),
                    ("pietra calcarea", 1), ("pietra calcarea", 2), ("pietra calcarea", 3), ("pietra calcarea", 4),
                    ("pietra calcarea", 5), ("vermiglio comunale", 2), ("neutri", 4), ("legno e cuoio", 2),
                    ("cotto e coppi", 2), ("pietra calcarea", 0), ("oro e bronzo", 3), ("neutri", 2)]
L_CIELO, L_CIELO_C, L_OMBRA, L_PIETRA_S, L_PIETRA, L_PIETRA_M, L_PIETRA_L = 2, 3, 4, 5, 6, 7, 8
L_ROSSO, L_BIANCO, L_ASTA, L_BUIO = 9, 10, 11, 13


def loggiato(momento):
    """Piazza Grande davanti al Palazzo dei Consoli: la facciata di conci chiari coi merli guelfi, le
    bifore, il portale in cima alla scala a ventaglio, il campaniletto a vela; sopra, il drappo di Gubbio
    grande, rosso col monte a cinque cime. In basso il lastricato della piazza."""
    t = Tela(W, H, L_CIELO)
    for y in range(10, 30):
        for x in range(W):
            if (x + y) % 2 and y < 18:
                t.punto(x, y, L_CIELO_C)
            elif y >= 18:
                t.punto(x, y, L_CIELO_C)
    x0, x1, cima = 0, 330, 30
    # la facciata a conci irregolari in tre toni del calcare (F2): i giunti nel tono d'ombra, mai nel
    # nero; lo spigolo destro in ombra, lo zoccolo piu' scuro (L1); i toni medi, il chiaro resta ai
    # bordi in luce (C5)
    r = random.Random(41)
    y = cima
    while y < QUADRO - 6:
        alto = r.choice((5, 6, 6, 7))
        x = x0 - r.randint(0, 10)
        while x < x1:
            largo = r.randint(9, 16)
            tono = r.choice((L_PIETRA, L_PIETRA_M, L_PIETRA_M, L_PIETRA_M))
            t.rett(x, y, largo, alto, tono)
            t.rett(x + 1, y + 1, largo - 2, 1, min(L_PIETRA_L, tono + 1) if r.random() < 0.3 else tono)
            t.rett(x, y, largo, 1, L_PIETRA_S)
            t.rett(x, y, 1, alto, L_PIETRA_S)
            x += largo
        y += alto
    t.rett(x0, QUADRO - 14, x1 - x0, 8, L_PIETRA)                       # lo zoccolo
    t.rett(x0, QUADRO - 14, x1 - x0, 1, L_PIETRA_S)
    t.rett(x1 - 14, cima, 14, QUADRO - cima, L_PIETRA)
    t.rett(x1 - 3, cima, 3, QUADRO - cima, L_PIETRA_S)
    for k in range(x0, x1, 8):                                          # i merli guelfi, luce a sinistra
        t.rett(k, cima - 5, 5, 5, L_PIETRA_M)
        t.rett(k, cima - 5, 1, 5, L_PIETRA_L)
        t.rett(k + 4, cima - 5, 1, 5, L_PIETRA)
    t.rett(x0, cima, x1 - x0, 2, L_PIETRA)                              # l'ombra sotto i merli
    # le bifore della fila alta: la cornice di pietra con la luce sul bordo alto e sinistro, lo strombo
    # d'ombra in alto e a destra dentro il vano (F5)
    def vano(x, y, w, h, arco):
        t.rett(x, y, w, h, L_BUIO)
        t.ellisse(x + w / 2, y, w / 2, arco, L_BUIO)
        t.rett(x + w - 1, y, 1, h, L_PIETRA_S)
        for xx in range(x, x + w):
            for yy in range(int(y - arco), y + 1):
                if t.px[yy][xx] == L_BUIO and t.px[yy - 1][xx] != L_BUIO:
                    t.punto(xx, yy, L_PIETRA_S)
    for bx in range(x0 + 22, x1 - 30, 48):
        t.rett(bx - 1, cima + 7, 16, 22, L_PIETRA)
        t.rett(bx - 1, cima + 7, 16, 1, L_PIETRA_L)
        t.rett(bx - 1, cima + 7, 1, 22, L_PIETRA_L)
        t.rett(bx - 1, cima + 28, 16, 1, L_PIETRA_S)
        for lx in (bx + 1, bx + 8):
            vano(lx, cima + 12, 5, 14, 3)
        t.rett(bx + 6, cima + 10, 2, 16, L_PIETRA_L)
        t.rett(bx + 7, cima + 10, 1, 16, L_PIETRA)
    # il portale ad arco col portone di legno e il battente d'oro, e la scala a ventaglio
    px = 96
    t.rett(px - 14, cima + 40, 28, QUADRO - cima - 54, L_PIETRA)
    t.rett(px - 14, cima + 40, 1, QUADRO - cima - 54, L_PIETRA_L)
    t.ellisse(px, cima + 46, 14, 10, L_PIETRA)
    t.ellisse(px, cima + 46, 10, 7, L_BUIO)
    t.rett(px - 10, cima + 46, 20, QUADRO - cima - 60, L_BUIO)
    t.rett(px - 9, cima + 47, 18, QUADRO - cima - 61, 1)               # il portone (legno scuro)
    t.rett(px, cima + 47, 1, QUADRO - cima - 61, L_BUIO)
    t.rett(px - 3, cima + 56, 2, 2, 14)                                # i battenti d'oro
    t.rett(px + 2, cima + 56, 2, 2, 14)
    t.rett(px + 9, cima + 40, 1, QUADRO - cima - 54, L_PIETRA_S)
    for k in range(5):
        yk = QUADRO - 14 + k * 3
        t.rett(px - 18 - k * 8, yk, 36 + k * 16, 3, L_PIETRA_M)
        t.rett(px - 18 - k * 8, yk, 36 + k * 16, 1, L_PIETRA_L)        # l'alzata in luce, la pedata
        t.rett(px - 18 - k * 8, yk + 2, 36 + k * 16, 1, L_PIETRA)      # in ombra (L4, gradini)
    # il campaniletto a vela e il drappo di Gubbio sull'asta
    vx = x0 + 150
    t.rett(vx, cima - 20, 16, 16, L_PIETRA_M)
    t.trapezio(vx + 8, cima - 26, cima - 20, 2, 16, L_PIETRA_M)
    t.rett(vx, cima - 20, 1, 16, L_PIETRA_L)
    t.rett(vx + 14, cima - 20, 2, 16, L_PIETRA)
    t.rett(vx + 5, cima - 16, 6, 9, L_BUIO)
    t.ellisse(vx + 8, cima - 16, 3, 3, L_BUIO)
    t.rett(vx + 7, cima - 11, 2, 3, 14)                              # la campana
    ax = x0 + 30
    t.rett(ax, 0, 1, cima - 4, L_ASTA)
    ST.drappo(t, ax + 1, 3, ST.GUBBIO["gioco"], {("vermiglio comunale", 2): L_ROSSO, ("neutri", 4): L_BIANCO,
                                                ST.CONTORNO: 1}, 17, 11)
    # il lastricato
    # il lastricato in scorcio: lastre di due toni a file sfalsate, i giunti nel tono d'ombra (F3)
    for y in range(QUADRO - 6, H):
        fila = (y - QUADRO + 6) // 3
        for x in range(W):
            giunto = (y - QUADRO + 6) % 3 == 0 or (x + fila * 7) % 19 == 0
            t.punto(x, y, L_PIETRA_S if giunto else (L_PIETRA if ((x + fila * 7) // 19 + fila) % 3 else L_PIETRA_M))
    return t, PALETTE_LOGGIATO, False


# --- i dettagli: la pergamena a terra e il pastorale ---------------------------------------------------
PALETTE_DETTAGLIO = [("neutri", 0), ("legno e cuoio", 0), ("pietra calcarea", 1), ("pietra calcarea", 2),
                     ("pietra calcarea", 3), ("pietra calcarea", 4), ("pelle", 2), ("pelle", 1), ("legno e cuoio", 1),
                     ("vermiglio comunale", 1), ("vermiglio comunale", 2), ("neutri", 4), ("neutri", 3),
                     ("oro e bronzo", 3), ("oro e bronzo", 2), ("legno e cuoio", 2)]
D_NERO, D_GIUNTO, D_LASTRA_S, D_LASTRA, D_LASTRA_L = 1, 2, 3, 4, 5
D_CARTA, D_CARTA_S, D_INCHIOSTRO, D_SANGUE, D_SIGILLO = 6, 7, 8, 9, 10
D_VESTE, D_VESTE_S, D_ORO, D_ORO_S, D_ASTA = 11, 12, 13, 14, 15


def lastricato(t, r):
    """Le lastre della piazza da vicino: rettangoli di calcare di toni diversi, i giunti scuri."""
    y = 0
    while y < QUADRO:
        alto = r.randint(16, 26)
        x = -r.randint(0, 20)
        while x < W:
            largo = r.randint(28, 48)
            tono = r.choice((D_LASTRA_S, D_LASTRA, D_LASTRA, D_LASTRA_L))
            t.rett(x, y, largo, alto, tono)
            # lo smusso della lastra (L1, L2): il bordo alto e sinistro in luce, quello basso e destro in
            # ombra; il giunto nel tono piu' scuro della pietra, mai nel nero (F2, C4)
            t.rett(x + 1, y + 1, largo - 2, 1, min(D_LASTRA_L, tono + 1))
            t.rett(x + 1, y + 1, 1, alto - 2, min(D_LASTRA_L, tono + 1))
            t.rett(x + 1, y + alto - 2, largo - 2, 1, max(D_LASTRA_S, tono - 1))
            t.rett(x + largo - 2, y + 1, 1, alto - 2, max(D_LASTRA_S, tono - 1))
            t.rett(x, y, largo, 1, D_GIUNTO)
            t.rett(x, y, 1, alto, D_GIUNTO)
            x += largo
        y += alto


def veste(t, x0):
    """L'orlo della veste di Ubaldo, bianca col bordo d'oro, che entra dal bordo."""
    for y in range(QUADRO):
        largo = 26 + y // 3
        t.rett(x0, y, largo, 1, D_VESTE)
        t.rett(x0 + largo - 6, y, 6, 1, D_VESTE_S)
    t.rett(x0, QUADRO - 10, 26 + (QUADRO - 10) // 3, 3, D_ORO)


def pergamena_a_terra(momento):
    """La pergamena di Monaldo gettata sulle lastre ai piedi di Ubaldo: arrotolata a meta', le righe
    d'inchiostro, il sigillo rosso e le macchie di sangue."""
    t = Tela(W, H)
    lastricato(t, random.Random(2))
    cx, cy = 120, 64
    for k in range(60):                                   # l'ombra portata sulle lastre, in basso a destra (L4)
        t.rett(cx - 38 + k, cy - 9 + k // 3, 1, 22, D_GIUNTO)
    t.ellisse(cx + 28, cy + 16, 7, 13, D_GIUNTO)
    t.rett(178, 2, 4, 80, D_GIUNTO)                        # e quella dell'asta
    for k in range(60):
        y = cy - 12 + k // 3
        t.rett(cx - 40 + k, y, 1, 22, D_CARTA)
    for k in range(60):                                   # la carta arrotolata prende la luce in alto
        t.punto(cx - 40 + k, cy - 12 + k // 3, D_LASTRA_L if k % 7 else D_CARTA)
        t.rett(cx - 40 + k, cy + 8 + k // 3, 1, 2, D_CARTA_S)
    for k in range(4):
        t.linea(cx - 32, cy - 4 + k * 4, cx + 10, cy + 10 + k * 4, D_INCHIOSTRO)
    t.ellisse(cx + 26, cy + 14, 7, 13, D_CARTA_S)
    t.ellisse(cx + 26, cy + 14, 4, 9, D_CARTA)
    t.ellisse(cx + 26, cy + 14, 2, 5, D_CARTA_S)
    t.ellisse(cx - 4, cy + 18, 5, 4, D_SIGILLO)
    t.punto(cx - 5, cy + 17, D_SANGUE)
    for sx, sy, rr in ((cx - 24, cy + 2, 3), (cx - 18, cy + 6, 2), (cx + 4, cy - 2, 2), (cx - 30, cy + 24, 3)):
        t.ellisse(sx, sy, rr, rr - 1, D_SANGUE)
    veste(t, 186)
    t.rett(176, 0, 4, 80, D_ASTA)
    t.rett(175, 78, 6, 6, D_ORO)
    return t, PALETTE_DETTAGLIO, False


def pastorale(momento):
    """Il colpo del pastorale: la punta di ferro e d'oro piantata sulla lastra, le crepe che si aprono,
    la polvere; a sinistra l'orlo della veste."""
    t = Tela(W, H)
    lastricato(t, random.Random(9))
    px, suolo = 130, 92
    t.rett(px - 3, 0, 7, suolo - 6, D_ASTA)
    t.rett(px + 2, 0, 2, suolo - 6, D_INCHIOSTRO)
    t.rett(px - 4, suolo - 26, 9, 4, D_ORO)
    t.rett(px - 4, suolo - 24, 9, 1, D_ORO_S)
    t.trapezio(px + 0.5, suolo - 8, suolo, 7, 3, D_ORO)
    r = random.Random(3)
    for angolo in (200, 230, 260, 290, 320, 340, 10):
        a = math.radians(angolo)
        x, y = px, suolo
        for k in range(r.randint(18, 30)):
            x += math.cos(a) * 1.5 + r.uniform(-0.6, 0.6)
            y -= math.sin(a) * 0.6
            t.punto(x, y, D_NERO)
    for _ in range(40):
        a = r.uniform(0, math.pi)
        d = r.uniform(10, 26)
        t.punto(px + math.cos(a) * d * 1.6, suolo - math.sin(a) * d * 0.5 - 4, D_LASTRA_L)
    veste(t, 26)
    return t, PALETTE_DETTAGLIO, False


PITTORI = {"fanti_lontani": fanti_lontani, "fanti_medi": fanti_medi, "fanti_vicini": fanti_vicini, "colli": colli,
           "araldo": araldo, "loggiato": loggiato, "pergamena_a_terra": pergamena_a_terra, "pastorale": pastorale}
