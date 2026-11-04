#!/usr/bin/env python3
"""La gente della citta' (pezzo VIVA): NPC, amici, mestieri e passanti ridisegnati allo standard grafico.

Prima (tools/figure_npc.py) gli NPC erano cinque sagome piatte alte 16 pixel, con due toni per materiale e
nessuna posa. Qui ogni persona nasce dallo scheletro della Guida di stile (stile/dati/pose.json, scelta 11:
testa, collo, bacino, mani, piedi in uno sprite 16x32) e da un COSTUME: veste, capelli, copricapo, grembiule,
accessorio del mestiere. Le passate di ombreggiatura, separazione e contorno sono quelle della classe Figura
di tools/sagome_battaglia.py (STANDARD_GRAFICO.md, regole L1, L2, L3, P1), cosi' la gente della mappa sta
allo stesso livello delle sagome della battaglia.

Regole dello standard che valgono qui:
  M1  sprite 16x32, persona alta 22-24 pixel, piedi alla riga 31 (un bambino due terzi, chi e' bassa 2 px meno)
  A5  da fermo il respiro: 2 fotogrammi da 30 vblank, il corpo si abbassa di 1 pixel
  A6  camminata in 3 direzioni (giu', su, destra; sinistra specchiata), 6 fotogrammi da 6 vblank
  A7  chi parla si gira: ogni NPC ha anche la posa di riposo di schiena e di lato
  L4  sotto i piedi un'ombra ellittica 10x3 nel tono d'ombra del suolo (pietra calcarea 1)
  C1  tutti i colori dalle rampe della Guida; una palette sola per tutta la gente (PALETTE_POPOLO), che di
      notte prende le rampe 'notte' (L5)

La palette (16 voci, la stessa per tutti: il GBA ha 16 palette di sprite e in una piazza stanno 15 persone):
  0 trasparente, 1 contorno (neutri 0), 2-4 pelle, 5-7 legno e cuoio 1-3, 8 ombra del suolo (pietra 1),
  9-11 neutri 2-4 (lana, ferro, lino), 12-14 vermiglio 1-3, 15 verde dei monti 2.

    python3 tools/figure_popolo.py tavola.png        # la tavola di controllo (Pillow)
"""
import json
import math
import os
import sys

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RADICE, "tools"))
import sagome_battaglia as SB  # noqa: E402

LATO_W, LATO_H = 16, 32
POSE_JSON = json.load(open(os.path.join(RADICE, "stile", "dati", "pose.json"), encoding="utf-8"))

PALETTE_POPOLO = [
    ("neutri", 0), ("neutri", 0),
    ("pelle", 0), ("pelle", 1), ("pelle", 2),
    ("legno e cuoio", 1), ("legno e cuoio", 2), ("legno e cuoio", 3),
    ("pietra calcarea", 1),
    ("neutri", 2), ("neutri", 3), ("neutri", 4),
    ("vermiglio comunale", 1), ("vermiglio comunale", 2), ("vermiglio comunale", 3),
    ("verde dei monti", 2),
]
OMBRA_SUOLO = 8
# i materiali: (ombra, base, luce) come indici di PALETTE_POPOLO
MATERIALI = {
    "pelle": (2, 3, 4),
    "cuoio": (5, 6, 7),         # legno, cuoio, saio, capelli castani
    "scuro": (5, 5, 6),         # capelli neri e mori, ferro brunito
    "lana": (9, 10, 11),        # lana grezza, ferro, lino
    "grigio": (9, 9, 10),       # ferro, capelli grigi
    "lino": (10, 11, 11),       # bianco: veli, camicie, barbe bianche
    "rosso": (12, 13, 14),      # vermiglio comunale
    "verde": (15, 15, 7),       # il verde dei monti (una voce sola: luce sul cuoio chiaro)
    "biondo": (6, 7, 7),
}
SINGOLI = {"occhio": 1, "oro": 7, "brace": 14, "bianco": 11, "ombra": OMBRA_SUOLO}
DIREZIONI = ("giu", "su", "destra")
FOTOGRAMMI_CAMMINATA = len(POSE_JSON["animazioni"]["camminata"]["fotogrammi"])


def _indici():
    return {nome: t for nome, t in MATERIALI.items()}


# --- lo scheletro dai giunti di pose.json ---------------------------------------------------------------
class Giunti:
    """I giunti di un fotogramma in una direzione, abbassati di 'giu' pixel sopra il bacino (chi e' bassa) e
    rimpiccioliti verso i piedi con 'scala' (il bambino)."""

    def __init__(self, g, giu=0, scala=1.0):
        piedi = POSE_JSON["linea_piedi"]

        def p(nome, sopra=True):
            x, y = g[nome]
            if scala != 1.0:
                y = piedi - (piedi - y) * scala
                x = 8 + (x - 8) * (0.85 + 0.15 * scala)
            if sopra:
                y += giu
            return (x, y)

        self.testa, self.collo, self.bacino = p("testa"), p("collo"), p("bacino")
        self.mano_a, self.mano_b = p("mano_a"), p("mano_b")
        self.piede_a, self.piede_b = p("piede_a", False), p("piede_b", False)
        self.scala = scala


def giunti_di(animazione, fotogramma, direzione, giu=0, scala=1.0):
    f = POSE_JSON["animazioni"][animazione]["fotogrammi"][fotogramma]["giunti"]
    return Giunti(f.get(direzione, f.get("giu", f)), giu, scala)


# --- il costume ----------------------------------------------------------------------------------------
class Costume:
    def __init__(self, veste="cuoio", lunga=False, calze="cuoio", scarpe="scuro", capelli=("cuoio", "corti"),
                 barba=None, grembiule=None, cintura=None, mantello=None, giu=0, scala=1.0, largo=0,
                 accessorio=None, maniche=None):
        self.veste, self.lunga, self.calze, self.scarpe = veste, lunga, calze, scarpe
        self.capelli, self.barba, self.grembiule, self.cintura = capelli, barba, grembiule, cintura
        self.mantello, self.giu, self.scala, self.largo = mantello, giu, scala, largo
        self.accessorio = accessorio
        self.maniche = maniche or veste

    def con(self, **kw):
        c = Costume.__new__(Costume)
        c.__dict__.update(self.__dict__)
        c.__dict__.update(kw)
        if "veste" in kw and "maniche" not in kw:
            c.maniche = kw["veste"]
        return c


def _gambe(f, s, c, direzione):
    bx, by = s.bacino
    if direzione == "destra":
        anche = ((bx - 0.5, by), (bx + 0.5, by))
    else:
        anche = ((bx - 2, by), (bx + 1.5, by))
    for (ax, ay), piede in zip(anche, (s.piede_b, s.piede_a) if direzione == "destra" else (s.piede_a, s.piede_b)):
        f.parte_nuova("gamba", c.calze).arto([(ax, ay), (piede[0], piede[1] - 1.5)], 2)
    f.parte_nuova("scarpa", c.scarpe)
    for x, y in (s.piede_a, s.piede_b):
        if direzione == "destra":
            f.rett(x - 1, y - 1, 3, 2)
        else:
            f.rett(x - 1, y - 1, 2.5, 2)


def _busto(f, s, c, direzione):
    cx, cy = s.collo
    bx, by = s.bacino
    mezzo = (2.6 if direzione == "destra" else 3.8) + c.largo
    if c.lunga:
        orlo = max(s.piede_a[1], s.piede_b[1]) - 1.5
        largo_orlo = (3.6 if direzione == "destra" else 4.8) + c.largo
        punti = [(cx - mezzo, cy), (cx + mezzo, cy), (bx + mezzo, by), (bx + largo_orlo, orlo),
                 (bx - largo_orlo, orlo), (bx - mezzo, by)]
    else:
        orlo = by + 3.5 * s.scala
        largo_orlo = mezzo + 1
        punti = [(cx - mezzo, cy), (cx + mezzo, cy), (bx + largo_orlo, orlo), (bx - largo_orlo, orlo)]
    f.parte_nuova("veste", c.veste).poligono(punti)
    if c.grembiule and direzione != "su":
        g0 = by - 4
        f.parte_nuova("grembiule", c.grembiule).poligono(
            [(bx - 2.5, g0), (bx + 2.5, g0), (bx + 3, orlo - 0.5), (bx - 3, orlo - 0.5)] if direzione == "giu" else
            [(bx + 0.5, g0), (bx + 2.8, g0), (bx + 3.4, orlo - 0.5), (bx + 1, orlo - 0.5)])
    if c.cintura:
        f.dettaglio_rett(bx - mezzo + 0.5, by - 1, 2 * mezzo, 1, c.cintura)
    return orlo


def _braccio(f, s, c, spalla, mano):
    f.parte_nuova("braccio", c.maniche).arto([spalla, mano], 2)
    f.parte_nuova("mano", "pelle").rett(mano[0] - 1, mano[1] - 0.5, 2, 2)


def _testa(f, s, c, direzione):
    tx, ty = s.testa
    r = 3.3 * (0.9 + 0.1 * s.scala)
    f.parte_nuova("testa", "pelle").ellisse(tx, ty, r, r + 0.3)
    if direzione == "destra":
        f.rett(tx + r - 0.4, ty + 0.5, 1, 1)           # il naso
    mat, stile = c.capelli
    # i capelli e i copricapi: dettagli piatti sopra la testa, a meno che non siano un pezzo (velo, cappuccio)
    if stile in ("velo", "cappuccio"):
        punti = [(tx - r - 1, ty + 4), (tx - r - 0.8, ty - 1.5), (tx - 1.5, ty - r - 1.2), (tx + 1.5, ty - r - 1.2),
                 (tx + r + 0.8, ty - 1.5), (tx + r + 1, ty + 4)]
        f.parte_nuova(stile, mat).poligono(punti)
        if direzione != "su":
            # il viso resta scoperto: un ovale di pelle dentro il velo
            f.parte_nuova("viso", "pelle").ellisse(tx + (1 if direzione == "destra" else 0), ty + 0.6, r - 1.1, r - 0.8)
    else:
        for y in range(int(ty - r - 2), int(ty + r + 3)):
            for x in range(int(tx - r - 2), int(tx + r + 2)):
                u, v = (x + 0.5 - tx) / (r + 0.5), (y + 0.5 - ty) / (r + 0.6)
                dentro = u * u + v * v <= 1
                if stile == "calvo":
                    continue
                if stile == "berretto":
                    if dentro and y < ty - 1:
                        f.dettaglio(x, y, (mat, 1 if x > tx - 1 else 2))
                    continue
                if stile == "lunghi":
                    lunghi = abs(x + 0.5 - tx) <= r + 0.6 and ty - 1 <= y <= ty + r + 3.5
                    if direzione == "giu":
                        lunghi = lunghi and abs(x + 0.5 - tx) > r - 1.3
                    elif direzione == "destra":
                        lunghi = lunghi and x + 0.5 < tx - 0.5
                    if (dentro and (y < ty - 1.2 or direzione == "su")) or lunghi:
                        f.dettaglio(x, y, (mat, 1 if (x + y) % 5 else 2))
                    continue
                # corti
                if dentro and (y < ty - 1.4 or direzione == "su" or
                               (direzione == "destra" and x + 0.5 < tx - 0.8) or
                               (direzione == "giu" and abs(x + 0.5 - tx) > r - 0.6 and y < ty + 1)):
                    f.dettaglio(x, y, (mat, 1 if x > tx - 1.5 else 2))
        if stile == "berretto":
            f.dettaglio_rett(tx - r - 0.5, ty - 1.5, 2 * r + 1, 1, (mat, 0))
    if c.barba and direzione != "su":
        x0 = tx - 2 if direzione == "giu" else tx - 0.5
        f.dettaglio_rett(x0, ty + 1.5, 4 if direzione == "giu" else 3, 2, (c.barba, 1))
        f.dettaglio_rett(x0 + 1, ty + 3.5, 2, 1, (c.barba, 0))
    if direzione == "giu":
        f.dettaglio(tx - 1.5, ty + 0.4, "occhio")
        f.dettaglio(tx + 1.0, ty + 0.4, "occhio")
    elif direzione == "destra":
        f.dettaglio(tx + 1.3, ty + 0.4, "occhio")


def figura(c, direzione="giu", animazione="riposo", fotogramma=0):
    """Le 32 righe di 16 indici di PALETTE_POPOLO di una persona col costume c."""
    s = giunti_di(animazione, fotogramma, direzione, c.giu, c.scala)
    f = SB.Figura(32, PALETTE_POPOLO, _indici(), SINGOLI)
    cx, cy = s.collo
    if direzione == "destra":
        spalla_a, spalla_b = (cx + 0.5, cy + 1), (cx - 0.5, cy + 1)
    else:
        spalla_a, spalla_b = (cx - 3.5 - c.largo, cy + 1), (cx + 3 + c.largo, cy + 1)
    if c.mantello and direzione == "su":
        pass
    if direzione == "destra":
        _braccio(f, s, c, spalla_b, s.mano_b)            # il braccio dietro, sotto a tutto
    if not c.lunga:
        _gambe(f, s, c, direzione)
    else:
        f.parte_nuova("scarpa", c.scarpe)
        for x, y in (s.piede_a, s.piede_b):
            f.rett(x - 1, y - 1, 2.5, 2)
    if c.accessorio and getattr(c.accessorio, "dietro", False):
        c.accessorio(f, s, direzione)
    _busto(f, s, c, direzione)
    if c.mantello:
        bx, by = s.bacino
        f.parte_nuova("mantello", c.mantello).poligono(
            [(cx - 4.5 - c.largo, cy - 0.5), (cx + 4.5 + c.largo, cy - 0.5), (bx + 5.5, by + 2), (bx - 5.5, by + 2)]
            if direzione != "destra" else [(cx - 3.5, cy - 0.5), (cx + 1.5, cy - 0.5), (bx - 0.5, by + 3), (bx - 4.5, by + 2)])
    if direzione != "destra":
        _braccio(f, s, c, spalla_a, s.mano_a)
        _braccio(f, s, c, spalla_b, s.mano_b)
    _testa(f, s, c, direzione)
    if direzione == "destra":
        _braccio(f, s, c, spalla_a, s.mano_a)
    if c.accessorio and not getattr(c.accessorio, "dietro", False):
        c.accessorio(f, s, direzione)
    out = [riga[:LATO_W] for riga in f.pixel()[:LATO_H]]
    # l'ombra portata sotto i piedi (L4): un'ellisse 10x3 al centro dei piedi, dietro alla figura
    ox = (s.piede_a[0] + s.piede_b[0]) / 2
    for y in (LATO_H - 2, LATO_H - 1):
        for x in range(LATO_W):
            u = (x + 0.5 - ox) / 5.0
            v = (y + 0.5 - (LATO_H - 1.0)) / 1.5
            if u * u + v * v <= 1 and out[y][x] == 0:
                out[y][x] = OMBRA_SUOLO
    return out


# --- gli accessori dei mestieri -------------------------------------------------------------------------
# Ogni accessorio disegna sulla tela nella posa e nella direzione date; si appoggia alle mani (mano_b e' la
# mano a destra dello schermo nella vista di fronte, quella davanti di lato e' mano_a).
def accessorio(dietro=False):
    def deco(fn):
        fn.dietro = dietro
        return fn
    return deco


def _mano(s, direzione):
    return s.mano_a if direzione == "destra" else s.mano_b


def _altra(s, direzione):
    return s.mano_b if direzione == "destra" else s.mano_a


@accessorio()
def martello(f, s, d):
    x, y = _mano(s, d)
    f.parte_nuova("manico", "cuoio").linea(x, y + 1, x + 1, y - 5)
    f.parte_nuova("ferro", "grigio").rett(x - 1, y - 7, 4, 2)


@accessorio()
def vaso(f, s, d):
    x, y = _mano(s, d)
    f.parte_nuova("vaso", "rosso").ellisse(x + 0.5, y - 1, 2.4, 2.6)
    f.parte_nuova("bocca", "rosso").rett(x - 0.5, y - 4.5, 2, 1)


@accessorio()
def bilanciere(f, s, d):
    """l'acquaiolo: il bastone sulle spalle e due secchi"""
    cx, cy = s.collo
    if d == "destra":
        f.parte_nuova("secchio", "grigio").rett(cx - 2, cy + 6, 4, 4)
        return
    f.parte_nuova("bastone", "cuoio").rett(0, cy, 16, 1)
    f.parte_nuova("secchio", "grigio").rett(0, cy + 4, 3, 4)
    f.parte_nuova("secchio", "grigio").rett(13, cy + 4, 3, 4)
    f.parte_nuova("corda", "cuoio").rett(1, cy + 1, 1, 3)
    f.parte_nuova("corda", "cuoio").rett(14, cy + 1, 1, 3)


@accessorio()
def matassa(f, s, d):
    x, y = _mano(s, d)
    f.parte_nuova("matassa", "biondo").ellisse(x, y + 1, 2.2, 2.2)
    f.dettaglio(x, y + 1, ("cuoio", 0))


@accessorio()
def pezza_rossa(f, s, d):
    x, y = _mano(s, d)
    f.parte_nuova("pezza", "rosso").poligono([(x - 2, y - 1), (x + 2, y - 1), (x + 2.5, y + 6), (x - 1.5, y + 6)])


@accessorio()
def pelle_conciata(f, s, d):
    x, y = _altra(s, d)
    f.parte_nuova("pelle", "biondo").poligono([(x - 2, y - 1), (x + 2, y - 2), (x + 2.5, y + 4), (x, y + 5), (x - 2.5, y + 4)])


@accessorio()
def sacco_in_spalla(f, s, d):
    cx, cy = s.collo
    if d == "su":
        f.parte_nuova("sacco", "lana").ellisse(cx + 1, cy + 1, 4, 3)
    elif d == "destra":
        f.parte_nuova("sacco", "lana").ellisse(cx - 2, cy - 1, 3.5, 3)
    else:
        f.parte_nuova("sacco", "lana").ellisse(cx + 3, cy - 1, 3.2, 2.6)
    f.dettaglio(cx + (3 if d == "giu" else -2), cy - 3, ("cuoio", 0))


@accessorio()
def bastone_pastore(f, s, d):
    x, y = _mano(s, d)
    f.parte_nuova("bastone", "cuoio").linea(x + 1, y - 9, x + 1, min(31, y + 8))
    f.parte_nuova("ricciolo", "cuoio").linea(x + 1, y - 9, x + 3, y - 10)
    f.parte_nuova("ricciolo", "cuoio").punto(x + 3, y - 8)


@accessorio()
def sale(f, s, d):
    x, y = _mano(s, d)
    f.parte_nuova("sacchetto", "lino").ellisse(x, y + 1.5, 2, 2.4)
    f.dettaglio(x - 0.5, y - 0.5, ("cuoio", 0))


@accessorio()
def pala_forno(f, s, d):
    x, y = _mano(s, d)
    f.parte_nuova("manico", "cuoio").linea(x, y + 3, x + 1, y - 8)
    f.parte_nuova("pala", "biondo").rett(x - 0.5, y - 12, 3, 4)


@accessorio()
def scarpa_lesina(f, s, d):
    x, y = _mano(s, d)
    f.parte_nuova("scarpa", "cuoio").rett(x - 2, y - 1, 4, 2)
    f.dettaglio(x + 2, y - 2, ("grigio", 2))


@accessorio()
def penna_foglio(f, s, d):
    x, y = _altra(s, d)
    f.parte_nuova("foglio", "lino").rett(x - 1, y - 3, 4, 5)
    f.dettaglio_linea(x, y - 2, x + 2, y - 2, ("lana", 0))
    f.dettaglio_linea(x, y, x + 2, y, ("lana", 0))
    xm, ym = _mano(s, d)
    f.parte_nuova("penna", "lino").linea(xm, ym, xm + 1, ym - 4)


@accessorio()
def cesta_cavoli(f, s, d):
    x, y = _mano(s, d)
    f.parte_nuova("cesta", "biondo").rett(x - 2.5, y - 1, 5, 3)
    f.parte_nuova("cavoli", "verde").ellisse(x, y - 2, 2.2, 1.4)


@accessorio()
def cesta_in_testa(f, s, d):
    tx, ty = s.testa
    f.parte_nuova("cesta", "biondo").rett(tx - 3.5, ty - 7, 7, 3)
    f.dettaglio_linea(tx - 3, ty - 6, tx + 3, ty - 6, ("cuoio", 0))


@accessorio()
def sacco_carbone(f, s, d):
    cx, cy = s.collo
    if d == "destra":
        f.parte_nuova("sacco", "scuro").ellisse(cx - 2, cy, 3.5, 3)
    else:
        f.parte_nuova("sacco", "scuro").ellisse(cx + 3, cy, 3, 2.6)


@accessorio()
def ascia(f, s, d):
    x, y = _mano(s, d)
    f.parte_nuova("manico", "cuoio").linea(x, y + 1, x, y - 7)
    f.parte_nuova("lama", "grigio").poligono([(x, y - 8), (x + 3.5, y - 9), (x + 3.5, y - 5), (x, y - 6)])


@accessorio(dietro=True)
def faretra(f, s, d):
    cx, cy = s.collo
    x = cx - 4 if d != "su" else cx + 2
    f.parte_nuova("faretra", "cuoio").rett(x, cy - 1, 2.5, 8)
    for k in range(3):
        f.dettaglio(x + k * 0.9, cy - 2, "bianco")


@accessorio()
def fascio_frecce(f, s, d):
    x, y = _mano(s, d)
    f.parte_nuova("frecce", "biondo").rett(x - 1, y - 6, 3, 8)
    f.dettaglio_rett(x - 1, y - 7, 3, 1, "bianco")


@accessorio()
def corda_campana(f, s, d):
    x, y = _mano(s, d)
    f.parte_nuova("corda", "biondo").linea(x, 0, x, y + 2)


@accessorio()
def bordone(f, s, d):
    x, y = _mano(s, d)
    f.parte_nuova("bordone", "cuoio").linea(x + 1, y - 10, x + 1, min(31, y + 8))
    f.parte_nuova("zucca", "biondo").ellisse(x + 1, y - 8, 1.2, 1.3)
    tx, ty = s.testa
    f.parte_nuova("cappello", "cuoio").rett(tx - 5, ty - 3, 10, 1.5)
    f.parte_nuova("cappello", "cuoio").rett(tx - 2.5, ty - 5, 5, 2)


@accessorio()
def pergamena_alta(f, s, d):
    x, y = _mano(s, d)
    f.parte_nuova("pergamena", "lino").rett(x - 1, y - 9, 3, 6)
    f.dettaglio_linea(x, y - 8, x + 1, y - 8, ("rosso", 1))


@accessorio()
def staio(f, s, d):
    x, y = _mano(s, d)
    f.parte_nuova("staio", "cuoio").rett(x - 2, y - 1, 4.5, 4)
    f.dettaglio_rett(x - 2, y - 1, 4.5, 1, "oro")


@accessorio()
def pennello_tavola(f, s, d):
    x, y = _altra(s, d)
    f.parte_nuova("tavola", "biondo").rett(x - 2, y - 3, 4, 5)
    f.dettaglio(x - 1, y - 2, ("rosso", 1))
    f.dettaglio(x, y - 1, ("verde", 1))
    xm, ym = _mano(s, d)
    f.parte_nuova("pennello", "cuoio").linea(xm, ym, xm + 1, ym - 4)


@accessorio()
def ingranaggio(f, s, d):
    x, y = _mano(s, d)
    f.parte_nuova("ruota", "grigio").ellisse(x + 0.5, y - 1, 2.6, 2.6)
    for a in range(0, 360, 60):
        f.punto(x + 0.5 + math.cos(math.radians(a)) * 3.2, y - 1 + math.sin(math.radians(a)) * 3.2)
    f.dettaglio(x + 0.5, y - 1, ("cuoio", 0))


@accessorio()
def occhiali(f, s, d):
    """le «pietre da leggere» di berillo che il fratello ha molato e legato a un archetto: due lenti chiare"""
    tx, ty = s.testa
    if d == "giu":
        for dx in (-1.5, 1.0):
            f.dettaglio(tx + dx, ty + 0.4, "bianco")
            f.dettaglio(tx + dx - 0.5, ty - 0.4, ("cuoio", 0))
        f.dettaglio(tx - 0.3, ty, ("cuoio", 0))
    elif d == "destra":
        f.dettaglio(tx + 1.3, ty + 0.4, "bianco")
        f.dettaglio_linea(tx - 1, ty, tx + 1, ty, ("cuoio", 0))


def con_occhiali_e_tavola(f, s, d):
    pennello_tavola(f, s, d)
    occhiali(f, s, d)


con_occhiali_e_tavola.dietro = False


@accessorio()
def lancia(f, s, d):
    x, y = _mano(s, d)
    f.parte_nuova("asta", "cuoio").linea(x, y - 14, x, min(31, y + 7))
    f.parte_nuova("punta", "grigio").poligono([(x - 1, y - 14), (x + 1.2, y - 14), (x + 0.2, y - 17)])


@accessorio()
def lanterna(f, s, d):
    x, y = _mano(s, d)
    f.parte_nuova("lanterna", "scuro").rett(x - 1, y + 1, 3, 3)
    f.dettaglio(x, y + 2, "brace")
    f.dettaglio(x + 1, y + 2, "oro")


@accessorio()
def anfora_in_testa(f, s, d):
    tx, ty = s.testa
    f.parte_nuova("anfora", "rosso").ellisse(tx, ty - 6.5, 2.4, 2.6)
    f.parte_nuova("collo", "rosso").rett(tx - 1, ty - 10, 2, 1.5)


@accessorio()
def tamburo(f, s, d):
    bx, by = s.bacino
    f.parte_nuova("tamburo", "rosso").rett(bx - 3, by - 2, 6, 3)
    f.dettaglio_rett(bx - 3, by - 2, 6, 1, "bianco")


# gli accessori degli amici (gli stessi nomi di tools/figure_npc.py, dati/amici.json), ridisegnati sullo scheletro
@accessorio(dietro=True)
def arco_lungo(f, s, d):
    x = 14 if d != "su" else 1
    f.parte_nuova("arco", "cuoio").linea(x, 7, x + 1, 13)
    f.parte_nuova("arco", "cuoio").linea(x + 1, 13, x + 1, 23)
    f.parte_nuova("arco", "cuoio").linea(x + 1, 23, x, 29)
    f.dettaglio_linea(x - 1, 8, x - 1, 28, ("lana", 1))


@accessorio()
def salterio(f, s, d):
    bx, by = s.bacino
    f.parte_nuova("salterio", "biondo").poligono([(bx - 3, by - 5), (bx + 3, by - 5), (bx + 2, by - 1), (bx - 2, by - 1)])
    f.dettaglio_linea(bx - 1, by - 4, bx - 1, by - 2, "oro")
    f.dettaglio_linea(bx + 1, by - 4, bx + 1, by - 2, "oro")


@accessorio()
def viella(f, s, d):
    x, y = _mano(s, d)
    f.parte_nuova("viella", "cuoio").ellisse(x - 1, y - 2, 2, 2.6)
    f.parte_nuova("manico", "cuoio").linea(x, y - 4, x + 2, y - 8)
    f.dettaglio(x - 1, y - 2, ("scuro", 0))


@accessorio()
def borsa_medico(f, s, d):
    x, y = _mano(s, d)
    f.parte_nuova("borsa", "cuoio").rett(x - 1.5, y + 1, 4, 3)
    f.dettaglio(x, y + 1, "oro")


@accessorio()
def fascia_gialla_rossa(f, s, d):
    if d == "su":
        return
    cx, cy = s.collo
    bx, by = s.bacino
    f.dettaglio_linea(cx - 3, cy + 1, bx + 3, by - 1, "oro")
    f.dettaglio_linea(cx - 2, cy + 1, bx + 3, by - 2, ("rosso", 1))


@accessorio()
def pinze_tavoletta(f, s, d):
    x, y = _altra(s, d)
    f.parte_nuova("tavoletta", "biondo").rett(x - 2, y - 3, 4, 4)
    f.dettaglio(x - 1, y - 2, ("rosso", 1))
    xm, ym = _mano(s, d)
    f.parte_nuova("pinze", "grigio").linea(xm, ym, xm + 1, ym + 3)


@accessorio()
def ruota(f, s, d):
    x, y = _mano(s, d)
    f.parte_nuova("ruota", "grigio").ellisse(x + 1, y + 1, 3.2, 3.2)
    f.parte_nuova("mozzo", "cuoio").ellisse(x + 1, y + 1, 1.6, 1.6)


@accessorio()
def secchio_corda(f, s, d):
    x, y = _mano(s, d)
    f.parte_nuova("secchio", "grigio").rett(x - 1.5, y + 1, 3.5, 3)
    f.parte_nuova("corda", "biondo").linea(x, y - 4, x, y)


@accessorio()
def balestra(f, s, d):
    x, y = _mano(s, d)
    f.parte_nuova("teniere", "cuoio").linea(x - 6, y - 1, x + 1, y - 1)
    f.parte_nuova("arco", "grigio").linea(x - 6, y - 4, x - 6, y + 2)


@accessorio()
def carboncino(f, s, d):
    x, y = _mano(s, d)
    f.parte_nuova("carboncino", "scuro").linea(x, y, x + 1, y - 2)


@accessorio()
def tavoletta_cera(f, s, d):
    x, y = _mano(s, d)
    f.parte_nuova("tavoletta", "biondo").rett(x - 2, y - 3, 4, 4)
    f.dettaglio_rett(x - 1, y - 2, 2, 2, ("scuro", 1))


@accessorio()
def libro(f, s, d):
    x, y = _altra(s, d)
    f.parte_nuova("libro", "rosso").rett(x - 1, y - 2, 4, 3)
    f.dettaglio_linea(x, y - 1, x + 2, y - 1, "bianco")


@accessorio()
def rotolo(f, s, d):
    x, y = _mano(s, d)
    f.parte_nuova("rotolo", "lino").rett(x - 2, y - 1, 4, 2)
    f.dettaglio(x - 2, y - 1, ("cuoio", 1))


@accessorio()
def ciotola(f, s, d):
    x, y = _altra(s, d)
    f.parte_nuova("ciotola", "cuoio").poligono([(x - 2, y - 1), (x + 3, y - 1), (x + 2, y + 1), (x - 1, y + 1)])
    f.dettaglio(x, y - 1, "bianco")


@accessorio()
def fiasco_grembiule(f, s, d):
    x, y = _mano(s, d)
    f.parte_nuova("fiasco", "verde").ellisse(x, y + 2, 1.8, 2)
    f.parte_nuova("collo", "biondo").rett(x - 0.5, y - 1, 1, 1.5)


@accessorio()
def tavoliere(f, s, d):
    x, y = _mano(s, d)
    f.parte_nuova("tavoliere", "biondo").rett(x - 2, y - 3, 4, 5)
    for k in range(3):
        f.dettaglio(x - 1 + (k % 2) * 2, y - 2 + k, ("scuro", 0))


@accessorio()
def chiave(f, s, d):
    x, y = _mano(s, d)
    f.parte_nuova("chiave", "grigio").linea(x, y - 6, x, y + 2)
    f.parte_nuova("anello", "grigio").ellisse(x, y - 7, 1.5, 1.5)
    f.parte_nuova("ingegno", "grigio").rett(x, y + 1, 2, 1)


@accessorio()
def tavoletta_conti(f, s, d):
    x, y = _altra(s, d)
    f.parte_nuova("tavoletta", "biondo").rett(x - 1, y - 2, 4, 3)
    f.dettaglio(x, y - 1, ("scuro", 0))
    f.dettaglio(x + 2, y - 1, ("scuro", 0))


@accessorio()
def lanterna_bastone(f, s, d):
    x, y = _altra(s, d)
    f.parte_nuova("bastone", "cuoio").linea(x, y - 9, x, min(31, y + 8))
    lanterna(f, s, d)


@accessorio()
def trave(f, s, d):
    cx, cy = s.collo
    if d == "destra":
        f.parte_nuova("trave", "biondo").rett(cx - 2, cy - 2, 4, 3)
    else:
        f.parte_nuova("trave", "biondo").rett(0, cy - 2, 16, 2)
        f.dettaglio_linea(1, cy - 2, 14, cy - 2, ("cuoio", 1))


@accessorio()
def scudo_monte(f, s, d):
    x, y = _altra(s, d)
    f.parte_nuova("scudo", "rosso").poligono([(x - 3, y - 4), (x + 2, y - 4), (x + 2, y + 1), (x - 0.5, y + 3), (x - 3, y + 1)])
    f.dettaglio(x - 1, y - 2, "bianco")
    f.dettaglio_rett(x - 2, y - 1, 3, 1, "bianco")


ACCESSORI_AMICI = {n: globals()[n] for n in (
    "arco_lungo", "salterio", "viella", "borsa_medico", "fascia_gialla_rossa", "pinze_tavoletta", "ruota",
    "secchio_corda", "tamburo", "balestra", "carboncino", "tavoletta_cera", "libro", "rotolo", "ciotola",
    "fiasco_grembiule", "tavoliere", "chiave", "tavoletta_conti", "lanterna_bastone", "trave", "scudo_monte")}


# --- i costumi ------------------------------------------------------------------------------------------
POPOLANO = Costume(veste="cuoio", calze="lana", scarpe="scuro", capelli=("cuoio", "corti"), cintura=("cuoio", 0))
POPOLANA = Costume(veste="rosso", lunga=True, capelli=("lino", "velo"), grembiule="lino")
FRATE = Costume(veste="cuoio", lunga=True, capelli=("cuoio", "cappuccio"), cintura="bianco")
SOLDATO = Costume(veste="rosso", calze="lana", scarpe="scuro", capelli=("grigio", "berretto"), cintura=("cuoio", 0))
MERCANTE = Costume(veste="rosso", lunga=True, capelli=("rosso", "berretto"), cintura="oro", maniche="rosso")
ANZIANO = Costume(veste="lana", lunga=True, capelli=("lino", "corti"), barba="lino", cintura=("cuoio", 0))

COSTUMI = {
    # le figure base degli NPC d'ambiente (copione/03_npc_ambiente.md)
    "popolana": POPOLANA,
    "frate": FRATE,
    "soldato": SOLDATO.con(accessorio=lancia),
    "mercante": MERCANTE,
    "anziano": ANZIANO,
    "anziano_glabro": ANZIANO.con(barba=None, capelli=("grigio", "corti")),
    "soldato_nudo": POPOLANO.con(veste="lana", maniche="pelle"),
    "gabrione": POPOLANO.con(veste="lana", lunga=True, capelli=("cuoio", "calvo"), giu=-2),
    "bambino": POPOLANO.con(veste="rosso", scala=0.68),
    # i mestieri (copione/06_npc_mestieri.md)
    "banditore": MERCANTE.con(veste="rosso", mantello="lana", accessorio=pergamena_alta),
    "misuratore": POPOLANO.con(veste="lana", lunga=True, capelli=("grigio", "berretto"), accessorio=staio),
    "fabbro": POPOLANO.con(veste="scuro", maniche="pelle", grembiule="cuoio", capelli=("scuro", "corti"),
                           barba="scuro", accessorio=martello),
    "vasaia": POPOLANA.con(veste="cuoio", grembiule="lana", capelli=("lana", "velo"), accessorio=vaso),
    "acquaiolo": POPOLANO.con(veste="lana", accessorio=bilanciere),
    "funaio": POPOLANO.con(veste="biondo", capelli=("cuoio", "corti"), accessorio=matassa),
    "tintore": POPOLANO.con(veste="lana", maniche="rosso", grembiule="rosso", accessorio=pezza_rossa),
    "conciatore": POPOLANO.con(veste="cuoio", maniche="pelle", grembiule="scuro", capelli=("scuro", "corti"),
                               accessorio=pelle_conciata),
    "mugnaio": POPOLANO.con(veste="lino", capelli=("lino", "berretto"), accessorio=sacco_in_spalla),
    "lanaiolo": POPOLANO.con(veste="lana", lunga=True, capelli=("cuoio", "berretto"), accessorio=matassa),
    "pastore": POPOLANO.con(veste="lana", mantello="cuoio", capelli=("scuro", "corti"), barba="scuro",
                            accessorio=bastone_pastore),
    "macellaio": POPOLANO.con(veste="rosso", grembiule="lino", capelli=("cuoio", "corti"), largo=0.6, accessorio=sale),
    "fornaia": POPOLANA.con(veste="lana", grembiule="lino", capelli=("lino", "velo"), accessorio=pala_forno),
    "calzolaio": POPOLANO.con(veste="verde", grembiule="cuoio", capelli=("grigio", "calvo"), accessorio=scarpa_lesina),
    "notaio": MERCANTE.con(veste="scuro", capelli=("scuro", "berretto"), accessorio=penna_foglio),
    "ortolana": POPOLANA.con(veste="verde", grembiule="lana", capelli=("cuoio", "velo"), accessorio=cesta_cavoli),
    "carbonaio": POPOLANO.con(veste="scuro", calze="scuro", capelli=("scuro", "corti"), barba="scuro",
                              accessorio=sacco_carbone),
    "carpentiere": POPOLANO.con(veste="biondo", capelli=("cuoio", "corti"), accessorio=ascia),
    "frecciaio": POPOLANO.con(veste="verde", capelli=("biondo", "corti"), accessorio=fascio_frecce),
    "campanaro": FRATE.con(veste="lana", capelli=("lana", "cappuccio"), accessorio=corda_campana),
    "pellegrino": POPOLANO.con(veste="cuoio", lunga=True, mantello="lana", capelli=("cuoio", "corti"),
                               barba="cuoio", accessorio=bordone),
    # i fratelli di Ciotto (copione/05_npc_amici.md): Milia, bassa e mora, coi capelli lunghi e le sue lenti;
    # Michelino col berretto verde e l'ingranaggio
    "milia": POPOLANA.con(veste="verde", grembiule=None, capelli=("scuro", "lunghi"), giu=2,
                          accessorio=con_occhiali_e_tavola),
    "michelino": POPOLANO.con(veste="lana", capelli=("verde", "berretto"), cintura=("cuoio", 0), accessorio=ingranaggio),
    # i passanti (src/folla.cpp): camminano in tre direzioni
    "portatore": POPOLANO.con(accessorio=sacco_in_spalla),
    "portatrice": POPOLANA.con(veste="lana", grembiule=None, accessorio=cesta_in_testa),
    "acquaiola": POPOLANA.con(veste="cuoio", grembiule="lino", accessorio=anfora_in_testa),
    "fante": SOLDATO.con(accessorio=lancia),
    "ragazzo": POPOLANO.con(veste="verde", scala=0.72),
    "penitente": FRATE.con(veste="lana", capelli=("lana", "cappuccio")),
    "ronda": SOLDATO.con(mantello="cuoio", accessorio=lanterna),
}
PASSANTI = ("portatore", "portatrice", "acquaiola", "fante", "ragazzo", "penitente", "ronda", "frate")


# --- gli animali: 16x16, disegnati a mano, due fotogrammi ------------------------------------------------
# cifre: indici di PALETTE_POPOLO in esadecimale, '.' trasparente
ANIMALI = {
    "gallina": [
        ["................", "................", "................", "................",
         "................", ".........1d1....", "........1dbb1...", "........1bbb17..",
         "..11...1bbbb11..", ".1bb111bbbbb1...", ".1abbbbbabbb1...", "..1aabbbaab1....",
         "...11aaaa11.....", ".....1771.......", ".....7..7.......", "....88888888...."],
        ["................", "................", "................", "................",
         "................", "................", "................", "..11............",
         ".1bb1....1d1....", ".1abb1111bb1....", "..1aabbbbbbb17..", "..1aaaaaabbb11..",
         "...11aaaa11.....", ".....1771.......", ".....7..7.......", "....88888888...."],
    ],
    "gatto": [
        ["................", "................", "................", "................",
         "................", "................", "...1.1..........", "..1515.......1..",
         "..15551.....161.", "..1515161...161.", "..155551..1551..", "...15556111561..",
         "...155555555561.", "...1551551551...", "....11.11.11....", "...8888888888..."],
        ["................", "................", "................", "................",
         "................", "................", "...1.1..........", "..1515..........",
         "..15551.......1.", "..1515161....161", "..155551...1561.", "...15556111561..",
         "...155555555561.", "...1551551551...", "....11.11.11....", "...8888888888..."],
    ],
    "cane": [
        ["................", "................", "................", "................",
         "................", "................", "..11............", ".1661...........",
         ".16661.......1..", "1666671......161", ".1166661111116..", "...16666666661..",
         "...16666666661..", "...161161161161.", "...11.11.11.11..", "..888888888888.."],
        ["................", "................", "................", "................",
         "................", "................", "..11............", ".1661........1..",
         ".16661......161.", "1666671.....161.", ".1166661111161..", "...16666666661..",
         "...16666666661..", "..161.1611.161..", "..11..11...11...", "..888888888888.."],
    ],
    "piccione": [
        ["................", "................", "................", "................",
         "................", "................", "................", "................",
         "................", "........111.....", ".......1a9a1....", "..111.1aaa917...",
         ".1999199aa91....", "..1999999a1.....", "...11d1d11......", ".....8888......."],
        ["................", "................", "................", "................",
         "..1.......1.....", ".1a1.....1a1....", ".1aa1...1aa1....", "..1aa1.1aa1.....",
         "...1aa1aa1......", "....1aaa9a1.....", "....1999917.....", ".....1991.......",
         "......11........", "................", "................", "................"],
    ],
    "pecora": [
        ["................", "................", "................", "................",
         "................", "................", "....1111111.....", "...1bbbbbbb1....",
         "..1bbababbbb111.", "..1bbbbbbbbb1331", "..1abbbbbbab1331", "...1aaaaaaa1.11.",
         "....1.1..1.1....", "....1.1..1.1....", "....11...11.....", "...8888888888..."],
        ["................", "................", "................", "................",
         "................", "................", "....1111111.....", "...1bbbbbbb1....",
         "..1bbababbbb1...", "..1bbbbbbbbb111.", "..1abbbbbbab1331", "...1aaaaaaa11331",
         "....1.1..1.1.11.", "...1..1..1..1...", "...11.....11....", "...8888888888..."],
    ],
}


def animale(nome, fotogramma):
    return [[int(ch, 16) if ch != "." else 0 for ch in riga] for riga in ANIMALI[nome][fotogramma]]


# Le tinte delle vesti: chi ha la stessa figura base non veste uguale. La tinta viene dal nome, sempre la stessa
# (crc32), cosi' una piazza non e' tutta vermiglia (i soldati della milizia restano rossi).
TINTE = {
    "mercante": ("rosso", "cuoio", "verde", "scuro", "lana", "biondo"),
    "popolana": ("rosso", "cuoio", "verde", "lana", "biondo"),
    "anziano": ("lana", "cuoio", "scuro"),
    "anziano_glabro": ("lana", "cuoio", "scuro", "verde"),
}
BERRETTI = ("rosso", "scuro", "verde", "cuoio")


def costume_npc(base, accessorio=None, nome=None):
    """Il costume di un NPC dal nome della sua figura (base), dall'accessorio degli amici (o None) e dal nome
    (la tinta della veste)."""
    import zlib
    c = COSTUMI[base]
    if nome and base in TINTE:
        h = zlib.crc32(nome.encode("utf-8"))
        veste = TINTE[base][h % len(TINTE[base])]
        c = c.con(veste=veste)
        if base == "mercante":
            c = c.con(capelli=(BERRETTI[(h >> 8) % len(BERRETTI)], "berretto"))
    if accessorio:
        c = c.con(accessorio=ACCESSORI_AMICI[accessorio])
    return c


# --- uscita ---------------------------------------------------------------------------------------------
def fotogrammi_npc(base, accessorio=None, nome=None):
    """Le quattro pose di un NPC fermo: riposo e respiro di fronte (A5), riposo di schiena e di lato (A7)."""
    c = costume_npc(base, accessorio, nome)
    return [figura(c, "giu", "riposo", 0), figura(c, "giu", "riposo", 1),
            figura(c, "su", "riposo", 0), figura(c, "destra", "riposo", 0)]


def fotogrammi_passante(nome):
    """I 18 fotogrammi della camminata (A6): giu', su, destra, 6 ciascuno."""
    c = COSTUMI[nome]
    return [figura(c, d, "camminata", k) for d in DIREZIONI for k in range(FOTOGRAMMI_CAMMINATA)]


def parole(px):
    """Le tile 8x8 (mappatura 1D, righe di tile) di una tela in parole da 32 bit, 4 bit per pixel."""
    h, w = len(px), len(px[0])
    out = []
    for ty in range(h // 8):
        for tx in range(w // 8):
            for r in range(8):
                v = 0
                for c in range(8):
                    v |= (px[ty * 8 + r][tx * 8 + c] & 15) << (4 * c)
                out.append(v)
    return out


def rgb(rif, versione="giorno"):
    sys.path.insert(0, os.path.join(RADICE, "stile"))
    rampe = {r["nome"]: r for r in json.load(open(os.path.join(RADICE, "stile", "dati", "palette.json"),
                                                   encoding="utf-8"))["rampe"]}
    v = rampe[rif[0]][versione][rif[1]]
    return ((v & 31) * 255 // 31, ((v >> 5) & 31) * 255 // 31, ((v >> 10) & 31) * 255 // 31)


def colori(versione="giorno"):
    return [rgb(r, versione) for r in PALETTE_POPOLO]


def bgr555(versione="giorno"):
    rampe = {r["nome"]: r for r in json.load(open(os.path.join(RADICE, "stile", "dati", "palette.json"),
                                                   encoding="utf-8"))["rampe"]}
    return [rampe[n][versione][t] for n, t in PALETTE_POPOLO]


def tavola(percorso, scala=4):
    from PIL import Image, ImageDraw
    pal = colori()
    nomi = list(COSTUMI)
    colonne = 4 + FOTOGRAMMI_CAMMINATA
    W = colonne * (LATO_W + 4) + 120
    H = len(nomi) * (LATO_H + 4) + 10 + 24
    img = Image.new("RGB", (W, H), (196, 186, 160))
    d = ImageDraw.Draw(img)
    for i, nome in enumerate(nomi):
        y0 = 4 + i * (LATO_H + 4)
        d.text((2, y0 + 10), nome, fill=(40, 30, 30))
        pose = fotogrammi_npc(nome) + [figura(COSTUMI[nome], "destra", "camminata", k)
                                       for k in range(FOTOGRAMMI_CAMMINATA)]
        for j, px in enumerate(pose):
            x0 = 120 + j * (LATO_W + 4)
            for y in range(LATO_H):
                for x in range(LATO_W):
                    if px[y][x]:
                        img.putpixel((x0 + x, y0 + y), pal[px[y][x]])
    y0 = H - 22
    for j, nome in enumerate(ANIMALI):
        for k in range(2):
            px = animale(nome, k)
            x0 = 120 + (j * 2 + k) * 20
            for y in range(16):
                for x in range(16):
                    if px[y][x]:
                        img.putpixel((x0 + x, y0 + y), pal[px[y][x]])
    img = img.resize((W * scala, H * scala), Image.NEAREST)
    img.save(percorso)


if __name__ == "__main__":
    tavola(sys.argv[1] if len(sys.argv) > 1 else "tavola_popolo.png")
