"""Gli stendardi delle cutscene: Gubbio e le undici citta' della coalizione, dai dati.

Le citta' vengono da dati/simboli/coalizione.json (la versione "gioco" di ogni stemma: campo, eventuale
partito o bande, figura e colori della palette bloccata); le figure 8x8 sono quelle della tavola decisa
(scambio/simboli/tavola_coalizione.py, commit a73eb5c), copiate qui senza ridisegnarle. Gubbio viene da
dati/simboli/simboli.json: campo rosso e monte d'argento a cinque cime, senza il lambello (angioino,
dopo il 1266).

Un drappo si disegna su una Tela a indici: chi lo chiama passa la mappa {(rampa, tono): indice} della
sua palette, che deve contenere tutti i colori degli stendardi (COLORI).
"""
import json
import os

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COALIZIONE = json.load(open(os.path.join(RADICE, "dati", "simboli", "coalizione.json"), encoding="utf-8"))["citta"]
SIMBOLI = json.load(open(os.path.join(RADICE, "dati", "simboli", "simboli.json"), encoding="utf-8"))

# '#' = colore della figura, 'o' = secondo colore (dalla tavola della coalizione)
FIGURE = {
    "grifo": ["..##....", ".###.o..", "..####..", ".#####.#", "..#####.", "..####..", ".##..#..", ".#...##."],
    "croce": ["...##...", "...##...", "########", "########", "...##...", "...##...", "...##...", "...##..."],
    "capriolo": [".o....o.", ".o....o.", "...##...", "..####..", ".##..##.", "##....##", "...o....", "...o...."],
    "giglio": ["...#....", "..###...", "#.###.#.", "##.#.##.", ".#####..", "...#....", "..###...", "...#...."],
    "aquila": ["...##...", "#..##..#", "##.##.##", "########", ".######.", "...##...", "..####..", "..#..#.."],
    "torre": ["#.#.#.#.", "#######.", "#######.", "##.#.##.", "#######.", "###.###.", "##...##.", "##...##."],
    "leone": ["..##....", ".###....", "..##.##.", ".#####..", "..####..", ".#####..", ".#...#..", "##...##."],
    # Gubbio: il monte a cinque cime di profilo, la centrale piu' alta (si legge anche a 8 px)
    "monte": ["....#....", "....#....", "..#.#.#..", "#.#####.#", "#########", "#########"],
}

GUBBIO = {"id": "gubbio", "nome": "Gubbio",
          "gioco": {"campo": ["vermiglio comunale", 2], "figura": "monte", "figura_colore": ["neutri", 4]}}
CONTORNO = ("legno e cuoio", 0)


def tutte():
    """Gubbio e poi le undici citta' della coalizione, nell'ordine dei dati."""
    return [GUBBIO] + COALIZIONE


def per_id(ident):
    return next(c for c in tutte() if c["id"] == ident)


def colori(gioco):
    """I colori (rampa, tono) di uno stendardo."""
    out = {tuple(gioco["campo"])}
    for chiave in ("campo_destro", "bande", "figura_colore", "secondo_colore"):
        if gioco.get(chiave):
            out.add(tuple(gioco[chiave]))
    return out


COLORI = sorted({c for citta in tutte() for c in colori(citta["gioco"])} | {CONTORNO})


def indici_o(indici, colore):
    return indici[tuple(colore)]


def drappo(t, x0, y0, gioco, indici, w=10, h=10, scala=1):
    """Il drappo appeso in (x0, y0): il campo (col partito a destra o le bande in diagonale), la figura
    centrata (ingrandita di 'scala'), il contorno scuro. 'indici' mappa (rampa, tono) -> indice."""
    def campo(x, y):
        c = gioco["campo"]
        if gioco.get("campo_destro") and x >= w // 2:
            c = gioco["campo_destro"]
        if gioco.get("bande") and (x - y) % 6 in (0, 1, 2):
            c = gioco["bande"]
        return indici[tuple(c)]

    for y in range(h):
        for x in range(w):
            t.punto(x0 + x, y0 + y, campo(x, y))
    if gioco.get("figura"):
        figura = FIGURE[gioco["figura"]]
        fw, fh = len(figura[0]) * scala, len(figura) * scala
        fx, fy = x0 + (w - fw) // 2, y0 + (h - fh + 1) // 2
        for r, riga in enumerate(figura):
            for k, v in enumerate(riga):
                if v in "#o":
                    c = gioco["figura_colore"] if v == "#" else gioco.get("secondo_colore", gioco["figura_colore"])
                    t.rett(fx + k * scala, fy + r * scala, scala, scala, indici[tuple(c)])
    nero = indici[CONTORNO]
    t.rett(x0 - 1, y0 - 1, w + 2, 1, nero)
    t.rett(x0 - 1, y0 + h, w + 2, 1, nero)
    t.rett(x0 - 1, y0, 1, h, nero)
    t.rett(x0 + w, y0, 1, h, nero)
