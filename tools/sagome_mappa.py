#!/usr/bin/env python3
"""Il giocatore sulla mappa (giro 5 del loop grafico): Ubaldo, 16x32, in quattro direzioni.

Prima era un segnaposto 16x16 di una sola posa che si specchiava. Qui Ubaldo e' alto 23 pixel coi piedi alla
riga 31 (STANDARD_GRAFICO M1), con l'ombra 10x3 sotto i piedi (L4) come la gente di tools/figure_popolo.py, e
cammina coi tempi di stile/dati/pose.json (A6): 6 fotogrammi da 6 vblank, il corpo che sale di un pixel nei
passaggi; da fermo respira (A5, 2 x 30 vblank). Giu', su e destra sono disegnate, sinistra e' la destra
specchiata (pose.json, "specchiate").

Le figure si dipingono con la Figura di tools/sagome_battaglia.py: parti piene, luce da sinistra, separazione e
contorno automatici (L1, L3, P1). La tela e' 32x32 e se ne tengono le 16 colonne centrali.

    python tools/sagome_mappa.py tavola.png      # la tavola di controllo (serve Pillow)
"""
import os
import sys

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RADICE, "tools"))
sys.path.insert(0, os.path.join(RADICE, "stile"))

import sagome_battaglia as SB  # noqa: E402

M = SB.Materiale
DIREZIONI = ("giu", "su", "destra")
# i fotogrammi di ogni direzione, in quest'ordine: i 6 della camminata, poi riposo e respiro
FOTOGRAMMI = 8
CAMMINATA = 6
RIPOSO, RESPIRO = 6, 7
VBLANK_PASSO = 6           # pose.json: camminata, 6 vblank a fotogramma
VBLANK_CORSA = 4           # la corsa: gli stessi fotogrammi piu' svelti (STANDARD A6)
VBLANK_RESPIRO = 30
LARGO, ALTO = 16, 32
OMBRA = ("pietra calcarea", 1)

BIANCO = M("bianco", ("neutri", 3), ("neutri", 4), ("pietra calcarea", 5))
ORO = M("oro", ("oro e bronzo", 1), ("oro e bronzo", 2), ("oro e bronzo", 3))
CAMICE = M("camice", ("neutri", 1), ("neutri", 2), ("neutri", 3))
CAPELLI = M("capelli", ("neutri", 2), ("neutri", 3), ("neutri", 4))
SCARPE = M("scarpe", ("legno e cuoio", 0), ("legno e cuoio", 1), ("legno e cuoio", 1))
PALETTE, INDICI, SINGOLI = SB.palette_di([SB.PELLE, BIANCO, ORO, CAMICE, CAPELLI, SCARPE],
                                         [SB.OCCHIO, ("ombra", OMBRA), ("rosso", ("vermiglio comunale", 2))])


def passo(f):
    """Il passo del fotogramma f della camminata: (piede avanti: -1 sinistro, 1 destro, 0 nessuno; su di 1 px)."""
    return ((-1, 0), (-1, 1), (0, 0), (1, 0), (1, 1), (0, 0))[f]


def _tela():
    return SB.Figura(32, PALETTE, INDICI, SINGOLI)


# Le coordinate: la tela e' 32x32, la figura sta fra le colonne 8 e 23 (X0) coi piedi alla riga 31.
X0 = 8


def giu(f):
    """Di fronte: la mitria con la croce, il viso con la barba corta, il piviale aperto con lo stolone, il
    camice grigio sotto, il pastorale nella destra (a sinistra di chi guarda)."""
    t = _tela()
    if f < CAMMINATA:
        piede, su = passo(f)
    else:
        piede, su = 0, (1 if f == RESPIRO else 0)
    dy = -su if f < CAMMINATA else su            # la camminata sale nei passaggi, il respiro abbassa
    c = X0 + 8                                   # il centro della figura
    # i piedi sotto l'orlo: quello avanti sporge di un pixel in basso
    t.parte_nuova("scarpe", "scarpe")
    for lato in (-1, 1):
        t.rett(c - 3 + (lato > 0) * 4, 30 + (1 if piede == lato else 0) - (1 if piede == -lato else 0), 2, 1)
    # il camice fino ai piedi
    t.parte_nuova("camice", "camice").poligono([(c - 4, 20 + dy), (c + 4, 20 + dy), (c + 5, 30), (c - 5, 30)])
    # il piviale: dalle spalle a campana, aperto al centro; l'orlo ondeggia verso il piede che avanza
    o = piede
    t.parte_nuova("piviale_s", "bianco").poligono([(c - 1, 17 + dy), (c - 4, 17 + dy), (c - 6 + o, 29 + dy // 2),
                                                 (c - 1 + o, 29 + dy // 2)])
    t.parte_nuova("piviale_d", "bianco").poligono([(c, 17 + dy), (c + 4, 17 + dy), (c + 6 + o, 29 + dy // 2),
                                                 (c + 1 + o, 29 + dy // 2)])
    t.dettaglio_linea(c - 1, 18 + dy, c - 2 + o, 28 + dy // 2, ("oro", 2))   # lo stolone d'oro
    t.dettaglio_linea(c + 1, 18 + dy, c + 2 + o, 28 + dy // 2, ("oro", 1))
    # le mani giunte davanti al petto: la sinistra regge il pastorale
    t.parte_nuova("mano", "pelle").rett(c - 6, 21 + dy, 2, 2)
    # il pastorale d'oro: l'asta e il riccio in cima
    t.parte_nuova("pastorale", "oro")
    for y in range(8 + dy, 31):
        t.punto(c - 6, y)
    for x, y in ((-6, 7), (-6, 6), (-5, 5), (-4, 5), (-3, 6), (-3, 7), (-4, 8)):
        t.punto(c + x, y + dy)
    # la testa: il viso, la barba corta canuta sotto la bocca, gli occhi
    t.parte_nuova("testa", "pelle").ellisse(c + 0.5, 14 + dy, 3, 3.2)
    t.parte_nuova("barba", "camice").poligono([(c - 2.4, 15.6 + dy), (c + 3.4, 15.6 + dy), (c + 2.4, 17.6 + dy),
                                             (c - 1.4, 17.6 + dy)])
    t.dettaglio(c - 1, 13 + dy, "occhio")
    t.dettaglio(c + 2, 13 + dy, "occhio")
    t.dettaglio(c + 0.5, 15 + dy, ("pelle", 0))
    # la mitria: due punte bianche, la fascia e la croce d'oro
    t.parte_nuova("mitria", "bianco").poligono([(c - 3, 11.5 + dy), (c + 4, 11.5 + dy), (c + 3, 7 + dy),
                                              (c + 0.5, 4.5 + dy), (c - 2, 7 + dy)])
    t.dettaglio_rett(c - 2, 10 + dy, 6, 1, ("oro", 2))
    t.dettaglio_linea(c + 0.5, 6 + dy, c + 0.5, 9 + dy, ("oro", 1))
    return t


def su(f):
    """Di schiena: le infule della mitria che pendono, la nuca canuta, il piviale con il cappuccio a scudo
    d'oro, il pastorale che sporge a sinistra."""
    t = _tela()
    if f < CAMMINATA:
        piede, sale = passo(f)
    else:
        piede, sale = 0, (1 if f == RESPIRO else 0)
    dy = -sale if f < CAMMINATA else sale
    c = X0 + 8
    t.parte_nuova("scarpe", "scarpe")
    for lato in (-1, 1):
        t.rett(c - 3 + (lato > 0) * 4, 30 - (1 if piede == lato else 0), 2, 1)
    t.parte_nuova("pastorale", "oro")
    for y in range(8 + dy, 31):
        t.punto(c + 6, y)
    for x, y in ((6, 7), (6, 6), (5, 5), (4, 5), (3, 6), (3, 7), (4, 8)):
        t.punto(c + x, y + dy)
    o = piede
    t.parte_nuova("piviale", "bianco").poligono([(c - 4, 17 + dy), (c + 4, 17 + dy), (c + 6 + o, 30), (c - 6 + o, 30)])
    # il cappuccio a scudo sulle spalle, d'oro, e lo stolone che scende al centro
    t.parte_nuova("scudo", "oro").poligono([(c - 3, 17.5 + dy), (c + 4, 17.5 + dy), (c + 0.5, 22.5 + dy)])
    t.dettaglio_linea(c + 0.5, 22 + dy, c + 0.5 + o, 29, ("oro", 1))
    # la nuca canuta: capelli bianchi sotto la mitria (non grigio scuro, che di schiena faceva una macchia),
    # e una striscia di collo fra i capelli e il piviale
    t.parte_nuova("collo", "pelle").rett(c - 1, 15 + dy, 4, 2)
    t.parte_nuova("testa", "bianco").ellisse(c + 0.5, 13.4 + dy, 3, 2.6)
    t.parte_nuova("mitria", "bianco").poligono([(c - 3, 11.5 + dy), (c + 4, 11.5 + dy), (c + 3, 7 + dy),
                                              (c + 0.5, 4.5 + dy), (c - 2, 7 + dy)])
    t.dettaglio_rett(c - 2, 10 + dy, 6, 1, ("oro", 2))
    # le infule sulla nuca: due nastri d'oro chiaro di un pixel, senza ombra (un pezzo ombreggiato
    # incorniciava la nuca di bruno e la testa si leggeva come un elmo)
    t.dettaglio_linea(c - 1, 12 + dy, c - 1, 17 + dy, ("oro", 2))
    t.dettaglio_linea(c + 2, 12 + dy, c + 2, 17 + dy, ("oro", 2))
    return t


def destra(f):
    """Di profilo verso destra: la mitria, il viso con la barba, il piviale che si apre col passo, il
    pastorale avanti nella mano."""
    t = _tela()
    if f < CAMMINATA:
        piede, sale = passo(f)
    else:
        piede, sale = 0, (1 if f == RESPIRO else 0)
    dy = -sale if f < CAMMINATA else sale
    c = X0 + 7
    apre = abs(piede) * 2                                                   # le gambe a forbice nei contatti
    t.parte_nuova("scarpe", "scarpe")
    t.rett(c - 2 - apre, 30, 3, 1)
    t.rett(c + 1 + apre, 30, 3, 1)
    t.parte_nuova("camice", "camice").poligono([(c - 3, 21 + dy), (c + 3, 21 + dy), (c + 3 + apre, 30), (c - 3 - apre, 30)])
    t.parte_nuova("piviale", "bianco").poligono([(c - 2, 16 + dy), (c + 3, 16 + dy), (c + 4, 21 + dy), (c + 2 + apre // 2, 29),
                                               (c - 5 - apre // 2, 29), (c - 4, 21 + dy)])
    t.dettaglio_linea(c + 2, 17 + dy, c + 1 + apre // 2, 28, ("oro", 2))      # lo stolone sul davanti
    # il braccio avanti col pastorale
    t.parte_nuova("braccio", "bianco").arto([(c + 1, 18 + dy), (c + 3, 21 + dy), (c + 5, 21 + dy)], 2)
    t.parte_nuova("mano", "pelle").rett(c + 5, 20 + dy, 2, 2)
    t.parte_nuova("pastorale", "oro")
    for y in range(8 + dy, 31):
        t.punto(c + 6 + (1 if y > 24 and piede else 0), y)
    for x, y in ((6, 7), (6, 6), (7, 5), (8, 5), (9, 6), (9, 7), (8, 8)):
        t.punto(c + x, y + dy)
    t.parte_nuova("testa", "pelle").ellisse(c + 1, 14 + dy, 2.8, 3.2)
    t.rett(c + 3.5, 14 + dy, 1, 1)                                            # il naso
    t.parte_nuova("barba", "camice").poligono([(c, 15.6 + dy), (c + 3.4, 15.8 + dy), (c + 2.4, 17.6 + dy), (c + 0.6, 17.6 + dy)])
    t.dettaglio(c + 2, 13 + dy, "occhio")
    t.parte_nuova("mitria", "bianco").poligono([(c - 2, 11.5 + dy), (c + 4, 11.5 + dy), (c + 3, 7 + dy),
                                              (c + 1, 4.5 + dy), (c - 1, 7 + dy)])
    t.dettaglio_rett(c - 1, 10 + dy, 5, 1, ("oro", 2))
    return t


PITTORI = {"giu": giu, "su": su, "destra": destra}


def fotogramma(direzione, f):
    """La griglia 16x32 di indici del fotogramma f (0-7) della direzione, con l'ombra sotto i piedi."""
    px = PITTORI[direzione](f).pixel()
    griglia = [riga[X0:X0 + LARGO] for riga in px]
    ombra = SINGOLI["ombra"]
    for y in (30, 31):
        for x in range(3, 13):
            if griglia[y][x] == 0 and (y == 31 or 4 <= x <= 11):
                griglia[y][x] = ombra
    for x in range(4, 12):
        if griglia[31][x] == 0:
            griglia[31][x] = ombra
    return griglia


def fotogrammi():
    """Tutti i fotogrammi, direzione per direzione (giu, su, destra), 8 ciascuna."""
    return [fotogramma(d, f) for d in DIREZIONI for f in range(FOTOGRAMMI)]


def tavola(percorso):
    from PIL import Image
    import stile as S
    pal = S.carica("palette")
    rgb = [S.rgb_di(S.colore(pal, r)) for r in PALETTE]
    sfondo = S.rgb_di(S.colore(pal, ("pietra calcarea", 3)))
    out = Image.new("RGB", (FOTOGRAMMI * 20, len(DIREZIONI) * 36), sfondo)
    for i, g in enumerate(fotogrammi()):
        for y, riga in enumerate(g):
            for x, c in enumerate(riga):
                if c:
                    out.putpixel(((i % FOTOGRAMMI) * 20 + 2 + x, (i // FOTOGRAMMI) * 36 + 2 + y), rgb[c])
    out.resize((out.width * 4, out.height * 4), Image.NEAREST).save(percorso)


if __name__ == "__main__":
    tavola(sys.argv[1] if len(sys.argv) > 1 else "giocatore.png")
