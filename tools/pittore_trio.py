"""Il piano dei tre sulle mura (pezzo SAG): Antonio, Ubaldo e Giorgio dietro il parapetto, di profilo verso
destra, guardano la conca dove stava il campo della coalizione. Serve a C4, La terza alba: Cioti (4 nov
2026) trovava belle le cutscene ma non vedeva mai i protagonisti.

L'ordine dei tre e' la regola di Cioti: Ubaldo al centro, Giorgio a destra (secondo), Antonio a sinistra
(terzo). Le figure sono quelle della battaglia (tools/sagome_battaglia.py) ridisegnate due volte piu'
grandi; il parapetto e' a sinistra, a destra si vede la conca col campo (il piano 'campo' dietro).

Un piano ha una palette sola: i toni delle tre figure vanno al piu' vicino della PALETTE_TRIO.
"""
import os
import sys

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RADICE, "stile"))

from genera_battaglia import Tela  # noqa: E402
import sagome_battaglia as SB  # noqa: E402
import stile as S  # noqa: E402

W, H = 512, 256
SCALA = 2
PIEDI = 100                       # i piedi dietro il parapetto: si vedono dalla vita in su
PARAPETTO = 86                    # il filo del parapetto
FINE_MURO = 166                   # a destra del muro, la conca
# (figura, centro x): Antonio a sinistra, Ubaldo al centro, Giorgio a destra
TRIO = (("antonio", 34), ("ubaldo", 84), ("giorgio", 134))


def _rgb(rif):
    return S.rgb_di(S.colore(S.carica("palette"), rif))


def figure():
    """Le tre figure: [(griglia di riferimenti (None = vuoto), centro x)]."""
    out = []
    for nome, cx in TRIO:
        f = getattr(SB, nome)("riposo", SCALA)
        px = f.pixel()
        out.append(([[f.palette[c] if c else None for c in r] for r in px], cx))
    return out


# La palette del piano: i toni che servono alle tre figure (scelti a mano fra quelli che usano) e la
# pietra del muro; ogni altro tono delle figure va al piu' vicino di questi (vicino()).
PALETTE_TRIO = [("neutri", 0), ("neutri", 0), ("pietra calcarea", 2), ("pietra calcarea", 3), ("pelle", 1), ("pelle", 2),
                ("neutri", 2), ("neutri", 3), ("neutri", 4), ("oro e bronzo", 2), ("oro e bronzo", 3),
                ("legno e cuoio", 0), ("legno e cuoio", 1), ("legno e cuoio", 2), ("cielo e acqua", 2),
                ("vermiglio comunale", 2)]
MURO, MURO_LUCE = 2, 3
FIGURE_DA = 4                     # dalla voce 4 in poi i toni delle figure


def vicino(rif):
    """L'indice della PALETTE_TRIO piu' vicino (in RGB) a un tono delle figure; il quasi nero e' il contorno."""
    if rif == ("neutri", 0):
        return 1
    if rif in PALETTE_TRIO[FIGURE_DA:]:
        return PALETTE_TRIO.index(rif, FIGURE_DA)
    r = _rgb(rif)
    return min(range(FIGURE_DA, 16), key=lambda i: sum((p - q) ** 2 for p, q in zip(_rgb(PALETTE_TRIO[i]), r)))


def mura_trio(momento):
    figs = figure()
    palette = PALETTE_TRIO
    indice = {}
    t = Tela(W, H)
    for griglia, cx in figs:
        piedi = max(y for y, r in enumerate(griglia) if any(r))
        x0, y0 = cx - len(griglia) // 2, PIEDI - piedi
        for y, r in enumerate(griglia):
            for x, rif in enumerate(r):
                if rif:
                    t.punto(x0 + x, y0 + y, indice.setdefault(rif, vicino(rif)))
    # il parapetto davanti: la pietra a corsi, i merli fra una figura e l'altra, la luce da sinistra
    for y in range(PARAPETTO, H):
        for x in range(0, FINE_MURO):
            corso = (y - PARAPETTO) // 5
            giunto = (y - PARAPETTO) % 5 == 4 or (x + corso * 7) % 14 == 0
            t.punto(x, y, 6 if giunto else (MURO_LUCE if x < 3 else MURO))
    for mx in (-4, 54, 104, 154):
        for y in range(PARAPETTO - 9, PARAPETTO):
            for x in range(mx, mx + 10):
                t.punto(x, y, MURO_LUCE if x == mx else (6 if x == mx + 9 else MURO))
    for x in range(0, FINE_MURO):
        t.punto(x, PARAPETTO, MURO_LUCE)
    for y in range(PARAPETTO - 9, H):
        t.punto(FINE_MURO, y, 1)
    return t, palette, momento == "notte"


PITTORI = {"mura_trio": mura_trio}
