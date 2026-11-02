#!/usr/bin/env python3
"""Generatore di include/mondo.h: le aree, il grafo dei varchi e i fondali procedurali.

Legge mondo/aree/*.area, il grafo del mondo (mondo/grafo.json, con le funzioni di
tools/mondo_dati.py) e i dati di stile (palette), e scrive in un solo header:
  - le griglie delle aree, una cella per tile, con i varchi numerati per area;
  - il grafo: per ogni varco l'area e lo spawn d'arrivo (o il dungeon, che in F2 e' solo un
    ingresso);
  - i fondali: un'unica serie di tile 8x8 a 4bpp disegnati qui con la palette, la luce da
    sinistra e i contorni della Guida di stile, e per ogni area la mappa di quei tile.

Una sola fonte per il grafo: mondo/grafo.json dice quali aree ci sono, la loro quota, quali archi
le collegano e l'anello; mondo/varchi.json (calcolato da quel grafo) dice su quale lato dello
schermo si apre ogni varco. Un file .area tiene il riferimento, il fattore di compressione, gli
spawn, le uscite e la griglia di fondo (suolo, muri, varchi, elementi decorativi): "uscita A
largo_bargello 2" vuol dire che il varco A della griglia e' l'arco verso il Largo del Bargello, e
che chi arriva da li' compare sullo spawn 2 di quest'area.

Gli edifici non stanno nella griglia: li disegna il generatore da mondo/monumenti.json, cosi' una
misura cambiata nel censimento si propaga da sola. Ogni monumento di tipo "edificio" diventa un
blocco non calpestabile di misure_tile (1 tile = 1,5 m, mai compresso), con l'asse lungo come
asse_lungo_schermo, centrato in riferimento + dall_ancora_tile * fattore (le distanze fra edifici
si comprimono, gli edifici no), piu' l'eventuale "sposta" dichiarato e motivato nella .area. La
facciata va sul lato facciata_lato_schermo (in basso o di fianco: conci di facciata con il
portone; in alto non si vede, e' il retro); gli altri lati sono muro. I tracciati (strade, la gola,
l'acquedotto) e gli SPAZI_APERTI restano calpestabili.

Prima di scrivere controlla il mondo e si rifiuta se trova: un carattere sconosciuto, una riga
di lunghezza sbagliata, un varco senza riga "uscita" o viceversa, uno spawn che non esiste, una
uscita senza arco in grafo.json o un arco senza uscita, un varco che non sta sul bordo indicato da
varchi.json, uno spawn d'arrivo a meno di DISTANZA_MIN_SPAWN_USCITA tile dalla propria uscita o a
meno di DISTANZA_MIN_SPAWN da un altro varco, uno spawn su una cella non calpestabile, un varco
che da uno spawn d'arrivo non si raggiunge camminando. Spawn e camminata li rifa' l'autotest C++
(include/mondo_autotest.h) a tempo di compilazione.

Il dislivello si vede in tre modi, tutti ricavati da quote e lati a monte (non da archi
particolari): scale davanti ai varchi fra aree con quote diverse; gradoni con il muro di
contenimento e l'ombra a valle dove la quota dell'area sale al suo interno (uno ogni
METRI_PER_GRADONE, al massimo GRADONI_MAX, con una scala di passaggio in ogni tratto); belvederi
(parapetto) sul bordo a valle delle aree alte. La salita va sempre verso nord-est, cioe' in basso a
destra: ogni .area dichiara "monte basso" o "monte destra", e un belvedere sta su un lato a valle.

Vie e piazze in proporzione, dalle misure muro a muro di mondo/fonti/misure_osm.json: la .area
nomina la sua via ("via Via dei Consoli") e la sua piazza ("piazza Piazza Grande"). La via deve
essere larga sulla griglia, in mediana, al massimo TOLLERANZA_VIA volte la misura (larghezza mediana
/ 1,5 m, minimo 2 tile; "tolleranza_via" piu' larga solo dove OSM e' incompleto, annotata); una
"strettoia N" vuole almeno un tratto largo N. La piazza sta libera, in scala, intorno al
riferimento; un lato lungo compresso solo con un "fattore_piazza" dichiarato.

Fondali in ROM: per ogni area le celle della mappa BG gia' pronte, che Butano copia senza cicli a
runtime. Fino a LATO_MAPPA_HW (64 tile, la mappa piu' grande dell'hardware) in una mappa di 32 o 64
per lato, a blocchi 32x32 come la VRAM; oltre, e fino a LATO_MAX tile per lato, una big map di
Butano: celle riga per riga in una mappa multipla di 32, e Butano carica solo la parte vicina allo
schermo.

Grafica dei monumenti (tools/pittore_monumenti.py): ogni edificio ha la sua tela in pixel, con la
sola palette dei fondali; ogni area ha il suo set di tile 8x8, deduplicato fra suolo, dislivello e
monumenti, al massimo TILE_MAX_PER_AREA (un BG). Un monumento canonico a cui manca un elemento
richiesto (per esempio i 6 archi del Consoli) e' rifiutato.

Controlli sugli edifici: ognuno compare nella sua area con le misure in tile esatte (un edificio
che esce dalla griglia o che risulta rimpicciolito e' rifiutato), nessuno si sovrappone a un altro o
a un varco, e dopo averli posati ogni varco resta raggiungibile da ogni spawn.

    python tools/genera_mondo.py              # rigenera include/mondo.h
    python tools/genera_mondo.py --controlla  # esce con 1 se include/mondo.h non e' aggiornato
"""
import glob
import json
import os
import sys
from collections import deque

RADICE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(RADICE, "stile"))

import stile as S  # noqa: E402

sys.path.insert(0, os.path.join(RADICE, "tools"))
import mondo_dati as M  # noqa: E402
import pittore_monumenti as PM  # noqa: E402

AREE_GLOB = os.path.join(RADICE, "mondo", "aree", "*.area")
USCITA = os.path.join(RADICE, "include", "mondo.h")

# Destinazioni che non sono aree dell'anello: in F2 esiste solo il loro ingresso.
DUNGEON = {"gola_bottaccione": "AREA_GOLA_BOTTACCIONE"}

# Aree fuori citta': il muro e' il pendio del monte, non un tetto.
AREE_DEL_MONTE = {"monte_ingino", "bottaccione"}

# Uno spawn d'arrivo a 2 tile dal varco rimanda indietro chi tiene premuta la direzione.
DISTANZA_MIN_SPAWN = 3
# Dalla propria uscita, quella da cui si e' entrati, lo spawn sta piu' lontano: si arriva gia'
# dentro l'area, non sulla soglia.
DISTANZA_MIN_SPAWN_USCITA = 6

# Celle della griglia: carattere del file .area -> (nome C++, solida).
CELLE = {
    ".": ("SUOLO", False),
    ",": ("STRADA", False),
    "S": ("SCALINATA", False),
    "F": ("FONTANA", True),
    "d": ("PORTONE", True),        # portone di un edificio: solo visivo, non si attraversa
    "#": ("MURO", True),
    "=": ("PARAPETTO", True),      # affaccio sul vuoto
    "C": ("FACCIATA", True),       # facciata monumentale (Consoli, San Francesco, ...)
    "P": ("FACCIATA_2", True),     # seconda facciata (Pretorio, Bargello, acquedotto, ...)
    "M": ("MURO_CONTENIMENTO", True),  # il gradone: il terreno a monte sta piu' in alto
    "V": ("CITTA_BASSA", True),    # oltre il parapetto di un belvedere: la citta' vista dall'alto
    "W": ("MURA", True),           # le mura della citta', dove l'area tocca il perimetro
}
VARCHI = "ABEGHI"                 # I e' l'ingresso di un dungeon

# Monumenti che il censimento misura come "edificio" ma su cui si cammina: non diventano blocchi.
SPAZI_APERTI = {
    "piazza_grande": "e' la piazza stessa: il suo rettangolo e' il lastricato su cui si cammina",
    "ponte_san_martino": "il ponte sul Camignano si attraversa: e' un pezzo di strada",
}

# Celle che un edificio disegnato dal generatore puo' occupare.
MURO_EDIFICIO, FACCIATA_EDIFICIO, PORTONE_EDIFICIO = "#", "C", "d"
FATTORE_PREDEFINITO = 0.73   # compressione delle distanze del GDD
LATO_MAX = 128               # tile per lato di un'area
LATO_MAPPA_HW = 64           # oltre, il fondale e' una big map
TILE_MAX_PER_AREA = 512      # tile unici di un'area, suolo e monumenti insieme

# Dislivello. La salita va verso nord-est: sullo schermo in basso (est) o a destra (nord).
LATI_A_MONTE = ("basso", "destra")
LATI_A_VALLE = {"basso": "alto", "destra": "sinistra"}
QUOTA_MIN_BELVEDERE = 60       # metri: sotto non c'e' niente da guardare dall'alto
PROFONDITA_BELVEDERE = 3       # senza piazza: vuoto e parapetto nei primi tile dal bordo a valle
METRI_PER_GRADONE = 15
GRADONI_MAX = 3
TOLLERANZA_VIA = 1.5         # una via larga piu' del 50% della misura e' rifiutata
TOLLERANZA_VIA_MAX = 2.0     # dove OSM e' incompleto (quadrante sud-est), annotata nella .area
DISLIVELLO_PER_SCALE = 5       # metri fra le quote di due aree oltre cui il varco ha la scala
PROFONDITA_SCALE = 3           # tile di scala davanti al varco
LARGO_PASSAGGIO = 4            # la scala che attraversa un gradone
PRIMO_VARCO = 16                   # cella = PRIMO_VARCO + indice del varco nell'area

# --- Fondali procedurali ----------------------------------------------------------------------
# Palette dei fondali: (rampa, tono) della Guida di stile, dal piu' scuro al piu' chiaro dentro
# ogni rampa. L'indice 0 e' il colore di fondo.
PALETTE_FONDALI = [
    ("neutri", 0),            # 0  fondo
    ("neutri", 0),            # 1  contorno quasi nero
    ("pietra calcarea", 1),   # 2
    ("pietra calcarea", 2),   # 3
    ("pietra calcarea", 4),   # 4
    ("pietra calcarea", 5),   # 5  pietra chiarissima
    ("cotto e coppi", 1),     # 6
    ("cotto e coppi", 2),     # 7
    ("cotto e coppi", 3),     # 8
    ("cotto e coppi", 4),     # 9
    ("verde dei monti", 1),   # 10
    ("verde dei monti", 3),   # 11
    ("cielo e acqua", 2),     # 12
    ("cielo e acqua", 4),     # 13
    ("legno e cuoio", 1),     # 14
    ("legno e cuoio", 3),     # 15
]


def _tile(funzione):
    return [[funzione(x, y) for x in range(8)] for y in range(8)]


def tile_suolo(x, y):
    # lastricato di pietra: lastre 8x4 sfalsate, giunto scuro in basso e a destra, luce da sinistra
    sfalsa = 4 if (y // 4) % 2 else 0
    if y % 4 == 3 or (x + sfalsa) % 8 == 7:
        return 3
    return 5 if (x + sfalsa) % 8 == 0 else 4


def tile_strada(x, y):
    # selciato di pietra: ciottoli 4x4 sfalsati, giunto scuro, luce da sinistra. Non in cotto: a
    # schermo il cotto si confondeva con i coppi dei tetti.
    sfalsa = 2 if (y // 4) % 2 else 0
    gx, gy = (x + sfalsa) % 4, y % 4
    if gx == 3 or gy == 3:
        return 2
    return 4 if gx == 0 else 3


def tile_scalinata(x, y):
    # due gradini per tile: pedata chiara, alzata in ombra
    gradino = y % 4
    base = [5, 4, 4, 2][gradino]
    return base if x > 0 or gradino == 3 else min(base + 1, 5)


def tile_portone(x, y):
    if x in (0, 7) or y == 0:
        return 1
    return 15 if x % 3 == 1 else 14


def tile_fontana(x, y):
    if x in (0, 7) or y in (0, 7):
        return 4 if x == 0 or y == 0 else 2
    return 13 if (x + 2 * y) % 5 == 0 else 12


def tile_tetto(x, y):
    # coppi in cotto visti dall'alto: canali verticali, luce sul fianco sinistro del colmo
    if y % 4 == 3:
        return 6
    return [9, 8, 7, 6][x % 4]


def tile_muro_fronte(x, y):
    # muro di sostegno e fronte cieco: filari di pietra, cimasa chiara, piede in ombra
    if y == 0:
        return 5
    if y == 7:
        return 1
    sfalsa = 2 if (y // 3) % 2 else 0
    if y % 3 == 0 or (x + sfalsa) % 4 == 3:
        return 2
    return 3


def tile_parapetto(x, y):
    # affaccio: muretto basso in alto, oltre il vuoto con il verde lontano
    if y == 0:
        return 5
    if y < 3:
        return 4 if x % 4 else 3
    if y == 3:
        return 1
    return 11 if (x + y) % 3 else 10


def tile_facciata(x, y):
    # conci grandi di pietra chiara, giunti fini: la facciata monumentale vista di fronte
    if y % 4 == 3 or x % 8 == 7:
        return 3
    return 5


def tile_facciata_2(x, y):
    sfalsa = 4 if (y // 4) % 2 else 0
    if y % 4 == 3 or (x + sfalsa) % 8 == 7:
        return 2
    return 4


def tile_varco(x, y):
    # soglia: suolo con due fasce chiare che segnano il passaggio
    if y in (1, 6):
        return 5
    return 4 if (x + y) % 2 else 3


def tile_ingresso(x, y):
    # gradini che scendono nel buio della gola
    return [2, 1, 1, 1][(y + x // 4) % 4] if y < 6 else 1


def tile_bosco(x, y):
    # pendio del monte coperto di bosco: chiome verdi, luce da sinistra, ombre quasi nere
    v = (x * 3 + y * 5 + (x * y) % 3) % 7
    if v == 0:
        return 1
    return 11 if v < 3 and x % 4 < 2 else 10


def tile_muro_contenimento(x, y):
    # muro di contenimento visto dall'alto: cimasa chiara in basso (verso monte), conci, ombra a valle
    if y >= 6:
        return 5
    if y <= 1:
        return 1
    return 2 if (x + (y // 2) * 2) % 4 == 3 or y % 2 == 0 else 3


def tile_suolo_ombra(x, y):
    # il lastricato all'ombra del gradone: stessi giunti, un tono sotto
    return {5: 3, 4: 3, 3: 2}[tile_suolo(x, y)]


def tile_strada_ombra(x, y):
    return {4: 3, 3: 2, 2: 1}[tile_strada(x, y)]


def tile_citta_bassa(x, y):
    # la citta' bassa vista dall'alto: tetti piccoli e scuri, vicoli in ombra
    if x % 4 == 3 or y % 4 == 3:
        return 1
    return 7 if (x % 4) < 2 else 6


def tile_vuoto_ombra(x, y):
    # subito oltre il parapetto: il vuoto in ombra, qualche tetto lontano
    return 6 if (x + y * 3) % 7 == 0 else 1


def tile_tetto_orizzontale(x, y):
    # coppi con i canali orizzontali: il colmo corre nell'altro senso
    if x % 4 == 3:
        return 6
    return [9, 8, 7, 6][y % 4]


def tile_tetto_scuro(x, y):
    # coppi vecchi, piu' scuri
    if y % 4 == 3:
        return 1
    return [8, 7, 6, 6][x % 4]


def tile_comignolo(x, y):
    # un comignolo sul tetto: dado di pietra con l'ombra a destra
    if 2 <= x <= 5 and 1 <= y <= 5:
        return 1 if (x == 5 or y == 5) else (5 if x == 2 else 4)
    return tile_tetto_scuro(x, y)


def tile_cortile(x, y):
    # un piccolo cortile fra le case: terra e verde in ombra
    return 10 if (x * 3 + y) % 5 else 1


def tile_mura(x, y):
    # le mura viste dall'alto: cammino di ronda chiaro, conci, un dente di merlo ogni tile
    if y < 2:
        return 5 if x % 4 < 2 else 1
    sfalsa = 2 if (y // 3) % 2 else 0
    return 2 if y % 3 == 0 or (x + sfalsa) % 4 == 3 else 3


def tile_tetto_falda_luce(x, y):
    # falda di un tetto a capanna, quella in luce
    return 6 if y % 4 == 3 else [9, 9, 8, 7][x % 4]


def tile_tetto_falda_ombra(x, y):
    # l'altra falda, in ombra, con il colmo chiaro in cima
    if y == 0:
        return 9
    return 1 if y % 4 == 3 else [7, 6, 6, 1][x % 4]


def tile_terrazzino(x, y):
    # un terrazzino di cotto con il parapetto
    if x in (0, 7) or y in (0, 7):
        return 4
    return 8 if (x + y) % 2 else 7


def tile_vuoto(x, y):
    return 1


TILE_FONDALI = [
    ("VUOTO", tile_vuoto),
    ("SUOLO", tile_suolo),
    ("STRADA", tile_strada),
    ("SCALINATA", tile_scalinata),
    ("PORTONE", tile_portone),
    ("FONTANA", tile_fontana),
    ("TETTO", tile_tetto),
    ("MURO_FRONTE", tile_muro_fronte),
    ("PARAPETTO", tile_parapetto),
    ("FACCIATA", tile_facciata),
    ("FACCIATA_2", tile_facciata_2),
    ("VARCO", tile_varco),
    ("INGRESSO", tile_ingresso),
    ("BOSCO", tile_bosco),
    ("MURO_CONTENIMENTO", tile_muro_contenimento),
    ("SUOLO_OMBRA", tile_suolo_ombra),
    ("STRADA_OMBRA", tile_strada_ombra),
    ("CITTA_BASSA", tile_citta_bassa),
    ("VUOTO_OMBRA", tile_vuoto_ombra),
    ("TETTO_ORIZZONTALE", tile_tetto_orizzontale),
    ("TETTO_SCURO", tile_tetto_scuro),
    ("COMIGNOLO", tile_comignolo),
    ("CORTILE", tile_cortile),
    ("MURA", tile_mura),
    ("TETTO_FALDA_LUCE", tile_tetto_falda_luce),
    ("TETTO_FALDA_OMBRA", tile_tetto_falda_ombra),
    ("TERRAZZINO", tile_terrazzino),
]
INDICE_TILE = {nome: i for i, (nome, _) in enumerate(TILE_FONDALI)}


def tile_per_cella(griglia, x, y, del_monte=False, monte=None):
    """Il tile del fondale per la cella (x, y): l'unica regola che decide come si vede il mondo.
    monte: il lato a monte dell'area; il suolo subito a valle di un gradone e' in ombra."""
    c = griglia[y][x]
    if c in ".," and monte:
        mx, my = (x, y + 1) if monte == "basso" else (x + 1, y)
        if my < len(griglia) and mx < len(griglia[0]) and griglia[my][mx] == "M":
            return INDICE_TILE["SUOLO_OMBRA" if c == "." else "STRADA_OMBRA"]
    if c in VARCHI:
        return INDICE_TILE["INGRESSO" if c == "I" else "VARCO"]
    nome = CELLE[c][0]
    if nome == "CITTA_BASSA":
        vicine = [griglia[y + dy][x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                  if 0 <= y + dy < len(griglia) and 0 <= x + dx < len(griglia[0])]
        return INDICE_TILE["VUOTO_OMBRA" if "=" in vicine else "CITTA_BASSA"]
    if nome == "MURO":
        if del_monte:
            return INDICE_TILE["BOSCO"]
        sotto = griglia[y + 1][x] if y + 1 < len(griglia) else "#"
        # il muro che ha davanti (in basso sullo schermo) uno spazio calpestabile si vede di
        # fronte: e' il muro di sostegno o il fronte cieco; il resto e' tetto visto dall'alto
        if not solida(sotto):
            return INDICE_TILE["MURO_FRONTE"]
        return INDICE_TILE[tetto_della_casa(x, y)]
    return INDICE_TILE[nome]


VARIANTI_TETTO = 6


def variante_tetto(x, y):
    """La variante del tetto per il blocco 4x4 di case che contiene (x, y): deterministica."""
    bx, by = x // 4, y // 4
    return (bx * 7 + by * 13 + bx * by) % VARIANTI_TETTO


def tetto_della_casa(x, y):
    """Le case non sono tutte uguali: colmo in un senso o nell'altro, coppi scuri con il comignolo,
    un piccolo cortile in mezzo al blocco, falde a capanna, un terrazzino."""
    v = variante_tetto(x, y)
    dx, dy = x % 4, y % 4
    if v == 1:
        return "TETTO_ORIZZONTALE"
    if v == 2:
        return "COMIGNOLO" if (dx, dy) == (2, 1) else "TETTO_SCURO"
    if v == 3 and dx in (1, 2) and dy in (1, 2):
        return "CORTILE"
    if v == 4:
        return "TETTO_FALDA_LUCE" if dy < 2 else "TETTO_FALDA_OMBRA"
    if v == 5:
        return "TERRAZZINO" if (dx, dy) == (1, 2) else ("COMIGNOLO" if (dx, dy) == (3, 0) else "TETTO")
    return "TETTO"


# Lo sprite del giocatore, 16x16: segnaposto procedurale finche' non arrivano le pose.
PALETTE_GIOCATORE = [("neutri", 0), ("neutri", 0), ("pelle", 1), ("pelle", 2),
                     ("vermiglio comunale", 1), ("vermiglio comunale", 2), ("legno e cuoio", 1),
                     ("legno e cuoio", 2)] + [("neutri", 0)] * 8
GIOCATORE = [
    "......1111......",
    ".....177771.....",
    "....17777771....",
    "....13333331....",
    "....13133131....",
    "....13333331....",
    ".....133331.....",
    "....15555551....",
    "...1544444451...",
    "...1544444451...",
    "...1544444451...",
    "....14444441....",
    ".....166661.....",
    ".....16..61.....",
    ".....16..61.....",
    ".....11..11.....",
]


# --- Lettura e controlli ----------------------------------------------------------------------

class ErroreMondo(Exception):
    pass


def solida(c):
    return c not in VARCHI and CELLE[c][1]


def leggi_area(nome_file, testo):
    a = {"file": nome_file, "spawn": {}, "uscite": [], "griglia": [], "sposta": {}, "vicino": {}, "belvedere": [], "largo": {}, "mura": [], "facciata": {},
         "fattore": FATTORE_PREDEFINITO, "riferimento": None}
    in_griglia = False
    for n, riga in enumerate(testo.split("\n"), 1):
        if in_griglia:
            if riga:
                a["griglia"].append((n, riga))
            continue
        if not riga.strip() or riga.startswith("#"):
            continue
        t = riga.split()
        try:
            if t[0] == "id":
                a["id"] = t[1]
            elif t[0] == "etichetta":
                a["etichetta"] = t[1]
            elif t[0] == "dimensioni":
                a["larghezza"], a["altezza"] = int(t[1]), int(t[2])
            elif t[0] == "spawn":
                a["spawn"][int(t[1])] = (int(t[2]), int(t[3]))
            elif t[0] == "uscita":
                if t[2] in DUNGEON:
                    if len(t) != 3:
                        raise ValueError
                    a["uscite"].append((t[1], t[2], None, n))
                else:
                    # "uscita G dest 3 vicino_a B 16": varco e spawn entro 16 tile dal varco B;
                    # "largo 5": la strada che porta al varco e' larga 5 tile (per l'impaginazione)
                    resto = t[4:]
                    while resto:
                        if resto[0] == "vicino_a":
                            a["vicino"][t[1]] = (resto[1], int(resto[2]), n)
                            resto = resto[3:]
                        elif resto[0] == "largo":
                            a["largo"][t[1]] = int(resto[1])
                            resto = resto[2:]
                        else:
                            raise ValueError
                    a["uscite"].append((t[1], t[2], int(t[3]), n))
            elif t[0] in ("via", "piazza"):
                a[t[0]] = (riga.split(None, 1)[1].strip(), n)
            elif t[0] == "fattore_piazza":
                # "fattore_piazza 0.40": lato lungo compresso; "fattore_piazza 0.40 0.85": anche il corto
                a["fattore_piazza"] = (float(t[1]), float(t[2]) if len(t) > 2 else None)
            elif t[0] == "tolleranza_via":
                a["tolleranza_via"] = float(t[1])
                if not TOLLERANZA_VIA <= a["tolleranza_via"] <= TOLLERANZA_VIA_MAX:
                    raise ErroreMondo(f"{nome_file}:{n}: tolleranza_via {t[1]} fuori da "
                                      f"{TOLLERANZA_VIA}..{TOLLERANZA_VIA_MAX}")
            elif t[0] == "strettoia":
                a["strettoia"] = int(t[1])
            elif t[0] == "monte":
                if t[1] not in LATI_A_MONTE:
                    raise ErroreMondo(f"{nome_file}:{n}: lato a monte '{t[1]}': la salita va verso nord-est, "
                                      f"il lato a monte e' basso o destra")
                a["monte"] = t[1]
            elif t[0] == "belvedere":
                a["belvedere"].append((t[1], n))
            elif t[0] == "mura":
                if t[1] not in ("alto", "basso", "sinistra", "destra"):
                    raise ErroreMondo(f"{nome_file}:{n}: lato delle mura '{t[1]}' sconosciuto")
                a["mura"].append(t[1])
            elif t[0] == "facciata":
                if t[2] not in ("alto", "basso", "sinistra", "destra"):
                    raise ErroreMondo(f"{nome_file}:{n}: lato della facciata '{t[2]}' sconosciuto")
                a["facciata"][t[1]] = (t[2], n)
            elif t[0] == "riferimento":
                a["riferimento"] = (int(t[1]), int(t[2]))
            elif t[0] == "fattore":
                a["fattore"] = float(t[1])
                if not 0 < a["fattore"] <= 1:
                    raise ErroreMondo(f"{nome_file}:{n}: fattore {t[1]} fuori da (0, 1]")
            elif t[0] == "sposta":
                a["sposta"][t[1]] = (int(t[2]), int(t[3]))
            elif t[0] == "griglia":
                in_griglia = True
            else:
                raise ErroreMondo(f"{nome_file}:{n}: riga '{t[0]}' sconosciuta")
        except (IndexError, ValueError):
            raise ErroreMondo(f"{nome_file}:{n}: riga malformata: {riga}") from None
    for campo in ("id", "etichetta", "larghezza", "riferimento", "monte"):
        if campo not in a:
            raise ErroreMondo(f"{nome_file}: manca '{campo}'")
    if not (0 < a["larghezza"] <= LATO_MAX and 0 < a["altezza"] <= LATO_MAX):
        raise ErroreMondo(f"{nome_file}: area {a['larghezza']}x{a['altezza']}: il lato massimo e' {LATO_MAX} tile")
    if len(a["griglia"]) != a["altezza"]:
        raise ErroreMondo(f"{nome_file}: {len(a['griglia'])} righe di griglia, ne dichiara {a['altezza']}")
    for n, riga in a["griglia"]:
        if len(riga) != a["larghezza"]:
            raise ErroreMondo(f"{nome_file}:{n}: riga larga {len(riga)}, ne dichiara {a['larghezza']}")
        for c in riga:
            if c not in CELLE and c not in VARCHI:
                raise ErroreMondo(f"{nome_file}:{n}: carattere '{c}' sconosciuto")
    a["griglia"] = [r for _, r in a["griglia"]]
    return a


def faccia_di(a, mid, monumenti):
    """Il lato della facciata: vince il censimento (facciata_lato_schermo); se non lo da', la riga
    "facciata" della .area; se manca anche quella, il default del pittore (o nessuna)."""
    dato = monumenti[mid].get("facciata_lato_schermo")
    scelta = a.get("facciata", {}).get(mid)
    if dato and scelta and scelta[0] != dato:
        raise ErroreMondo(f"{a['file']}:{scelta[1]}: facciata di {mid} a {scelta[0]}, ma il censimento la "
                          f"vuole a {dato}: vince il dato")
    return dato or (scelta[0] if scelta else PM.FACCIATA_DI_DEFAULT.get(mid))


def edifici_attesi(aid, monumenti):
    """{id: (larghezza, altezza)} in tile degli edifici che l'area deve contenere."""
    out = {}
    for mid, m in sorted(monumenti.items()):
        if m["area"].lower() != aid or m["tipo"] != "edificio" or mid in SPAZI_APERTI:
            continue
        lungo, corto = m["misure_tile"]
        out[mid] = (lungo, corto) if m.get("asse_lungo_schermo") == "orizzontale" else (corto, lungo)
    return out


def posa_edifici(a, monumenti):
    """Disegna nella griglia di a gli edifici di monumenti.json. Ritorna i rettangoli posati
    {id: (x, y, larghezza, altezza)}; rifiuta un edificio fuori griglia o sopra un altro, un varco o
    una cella che non sia suolo."""
    g = [list(r) for r in a["griglia"]]
    rx, ry = a["riferimento"]
    for mid in list(a["sposta"]) + list(a.get("facciata", {})):
        if mid not in edifici_attesi(a["id"], monumenti):
            raise ErroreMondo(f"{a['file']}: 'sposta {mid}', ma {mid} non e' un edificio di quest'area")
    posati, occupate = {}, {}
    for mid, (w, h) in edifici_attesi(a["id"], monumenti).items():
        m = monumenti[mid]
        nord, est = m.get("dall_ancora_tile", [0, 0])
        dx, dy = a["sposta"].get(mid, (0, 0))
        x0 = rx + int(round(nord * a["fattore"])) + dx - w // 2
        y0 = ry + int(round(est * a["fattore"])) + dy - h // 2
        if x0 < 0 or y0 < 0 or x0 + w > a["larghezza"] or y0 + h > a["altezza"]:
            raise ErroreMondo(f"{a['file']}: l'edificio {mid} ({w}x{h} tile in {x0}, {y0}) esce dalla "
                              f"griglia {a['larghezza']}x{a['altezza']}")
        faccia = faccia_di(a, mid, monumenti)
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                if (x, y) in occupate:
                    raise ErroreMondo(f"{a['file']}: l'edificio {mid} si sovrappone a {occupate[(x, y)]} "
                                      f"in ({x}, {y})")
                if g[y][x] in VARCHI:
                    raise ErroreMondo(f"{a['file']}: l'edificio {mid} copre il varco '{g[y][x]}' in ({x}, {y})")
                occupate[(x, y)] = mid
                bordo = {"basso": y == y0 + h - 1, "alto": y == y0,
                         "sinistra": x == x0, "destra": x == x0 + w - 1}
                if faccia in ("basso", "sinistra", "destra") and bordo[faccia]:
                    meta = (x0 + w // 2, y0 + h // 2)
                    porta = (abs(x - meta[0]) <= 1 and x != meta[0] + 1) if faccia == "basso" else \
                        (abs(y - meta[1]) <= 1 and y != meta[1] + 1)
                    g[y][x] = PORTONE_EDIFICIO if porta else FACCIATA_EDIFICIO
                else:
                    g[y][x] = MURO_EDIFICIO
        posati[mid] = (x0, y0, w, h)
    a["griglia"] = ["".join(r) for r in g]
    a["edifici"] = posati
    return posati


def quote_dell_area(a, grafo):
    q = [g["quota_m"] for g in grafo["aree"] if g["id"].lower() == a["id"]][0]
    return min(q), max(q)


def rettangolo_piazza(a):
    """(x0, y0, larghezza, altezza) della piazza intorno al riferimento, o None."""
    if "piazza" not in a:
        return None
    with open(os.path.join(RADICE, "mondo", "fonti", "misure_osm.json"), encoding="utf-8") as f:
        misura = json.load(f)["piazze"][a["piazza"][0]]
    w, h = misure_piazza_tile(misura, a.get("fattore_piazza"))
    rx, ry = a["riferimento"]
    return rx - w // 2, ry - h // 2, w, h


def linee_del_belvedere(a, lato):
    """Per ogni linea perpendicolare al lato a valle, dal bordo verso l'interno: le celle che diventano
    citta' bassa e, ultima, quella del parapetto. Con la piazza: sulle linee della piazza, fino al
    primo suolo (il parapetto sta sul bordo della piazza, edifici esclusi). Senza: i primi
    PROFONDITA_BELVEDERE tile, lontano dai varchi."""
    g, w, h = a["griglia"], a["larghezza"], a["altezza"]
    edifici = {(x, y) for (x0, y0, ew, eh) in a.get("edifici", {}).values()
               for x in range(x0, x0 + ew) for y in range(y0, y0 + eh)}
    orizzontale = lato in ("sinistra", "destra")
    lunghezza, profondita = (h, w) if orizzontale else (w, h)

    def cella(k, d):
        d = d if lato in ("sinistra", "alto") else profondita - 1 - d
        return (d, k) if orizzontale else (k, d)

    varchi = {(x, y) for y in range(h) for x in range(w) if g[y][x] in VARCHI}
    piazza = rettangolo_piazza(a)
    out = []
    for k in range(lunghezza):
        linea = []
        if piazza:
            x0, y0, pw, ph = piazza
            if not (y0 <= k < y0 + ph if orizzontale else x0 <= k < x0 + pw):
                continue
            for d in range(profondita):
                x, y = cella(k, d)
                if not solida(g[y][x]) or g[y][x] in VARCHI:
                    break
                linea.append((x, y))
            else:
                continue
            if len(linea) < 2 or linea[-1] in edifici or any(c in varchi for c in linea):
                continue
            # le celle di edificio prima del parapetto restano edificio
            linea = [c for c in linea[:-1] if c not in edifici] + [linea[-1]]
        else:
            linea = [cella(k, d) for d in range(PROFONDITA_BELVEDERE)]
            vicine = {(x + dx, y + dy) for x, y in linea for dx in range(-2, 3) for dy in range(-2, 3)}
            if vicine & varchi or any(c in edifici for c in linea):
                continue
        out.append(linea)
    return out


def errori_belvedere(a):
    """Celle oltre un parapetto (fra il parapetto e il bordo a valle) che sono ancora tetti a quota
    piena: non devono essercene."""
    g = a["griglia"]
    err = []
    for lato, _ in a["belvedere"]:
        passo = {"sinistra": (-1, 0), "destra": (1, 0), "alto": (0, -1), "basso": (0, 1)}[lato]
        for y, r in enumerate(g):
            for x, c in enumerate(r):
                if c != "=":
                    continue
                nx, ny = x + passo[0], y + passo[1]
                while 0 <= nx < a["larghezza"] and 0 <= ny < a["altezza"]:
                    if g[ny][nx] == "#" and (nx, ny) not in {(ex, ey) for (x0, y0, ew, eh) in a.get("edifici", {}).values()
                                                             for ex in range(x0, x0 + ew) for ey in range(y0, y0 + eh)}:
                        err.append((nx, ny))
                        break
                    nx, ny = nx + passo[0], ny + passo[1]
    return err


def numero_gradoni(a, grafo):
    q0, q1 = quote_dell_area(a, grafo)
    return min(GRADONI_MAX, int((q1 - q0) // METRI_PER_GRADONE))


def applica_dislivello(a, grafo):
    """Belvederi, gradoni e scale ai varchi, sulla griglia con gli edifici gia' posati."""
    g = [list(r) for r in a["griglia"]]
    w, h = a["larghezza"], a["altezza"]
    q0, q1 = quote_dell_area(a, grafo)
    edifici = {(x, y) for (x0, y0, ew, eh) in a.get("edifici", {}).values()
               for x in range(x0, x0 + ew) for y in range(y0, y0 + eh)}

    # mura della citta': il bordo dell'area su quel lato, fuori da varchi ed edifici
    for lato in a.get("mura", []):
        celle = {"alto": [(x, 0) for x in range(w)], "basso": [(x, h - 1) for x in range(w)],
                 "sinistra": [(0, y) for y in range(h)], "destra": [(w - 1, y) for y in range(h)]}[lato]
        for x, y in celle:
            if g[y][x] == "#" and (x, y) not in edifici:
                g[y][x] = "W"

    # belvederi: parapetto sul bordo a valle, dove c'e' il muro di bordo
    for lato, n in a["belvedere"]:
        if lato in LATI_A_MONTE:
            raise ErroreMondo(f"{a['file']}:{n}: belvedere sul lato a monte ({lato}): dall'alto si guarda "
                              f"a valle, cioe' {LATI_A_VALLE[a['monte']]} o {LATI_A_VALLE[[l for l in LATI_A_MONTE if l != a['monte']][0]]}")
        if lato not in LATI_A_VALLE.values():
            raise ErroreMondo(f"{a['file']}:{n}: lato del belvedere '{lato}' sconosciuto")
        if (q0 + q1) / 2 < QUOTA_MIN_BELVEDERE:
            raise ErroreMondo(f"{a['file']}:{n}: belvedere a {(q0 + q1) / 2:g} m: un'area sotto "
                              f"{QUOTA_MIN_BELVEDERE} m non ha niente da guardare dall'alto")
        for linea in linee_del_belvedere(a, lato):
            if linea:
                for x, y in linea[:-1]:
                    g[y][x] = "V"
                x, y = linea[-1]
                g[y][x] = "="

    # scale davanti ai varchi verso aree a un'altra quota
    for lettera, dest, _, _ in a["uscite"]:
        if dest in DUNGEON:
            continue
        d0, d1 = [min(x["quota_m"]) if k == 0 else max(x["quota_m"]) for x in grafo["aree"]
                  if x["id"].lower() == dest for k in (0, 1)]
        if max(d0 - q1, q0 - d1, 0) <= DISLIVELLO_PER_SCALE:
            continue
        celle = [(x, y) for y, r in enumerate(g) for x, c in enumerate(r) if c == lettera]
        lati = {"sinistra": (1, 0), "destra": (-1, 0), "alto": (0, 1), "basso": (0, -1)}
        for lato in lati_del_varco({"griglia": ["".join(r) for r in g], "larghezza": w, "altezza": h}, lettera):
            dx, dy = lati[lato]
            for x, y in celle:
                for k in range(1, PROFONDITA_SCALE + 1):
                    nx, ny = x + dx * k, y + dy * k
                    if 0 <= nx < w and 0 <= ny < h and g[ny][nx] in ".,":
                        g[ny][nx] = "S"

    # gradoni: righe (monte basso) o colonne (monte destra) di muro, con una scala in ogni tratto
    n = numero_gradoni(a, grafo)
    lungo = h if a["monte"] == "basso" else w
    vietate = set(a["spawn"].values()) | {(x, y) for y, r in enumerate(g) for x, c in enumerate(r)
                                          if c in VARCHI or c == "S"}
    a["gradoni"] = []
    for k in range(n):
        voluto = lungo * (k + 1) // (n + 1)
        for scarto in sorted(range(-lungo // 4, lungo // 4 + 1), key=abs):
            pos = voluto + scarto
            if not 2 <= pos < lungo - 2:
                continue
            linea = [(x, pos) for x in range(w)] if a["monte"] == "basso" else [(pos, y) for y in range(h)]
            vicine = {(x + dx, y + dy) for x, y in linea for dx in (-2, -1, 0, 1, 2) for dy in (-2, -1, 0, 1, 2)}
            if not vicine & vietate:
                break
        else:
            raise ErroreMondo(f"{a['file']}: non c'e' posto per il gradone {k + 1} di {n}")
        a["gradoni"].append(pos)
        tratto = []
        for cella in linea + [None]:
            if cella is not None and g[cella[1]][cella[0]] in ".,":
                tratto.append(cella)
                continue
            if tratto:
                meta = len(tratto) // 2
                passaggio = set(tratto) if len(tratto) < LARGO_PASSAGGIO + 2 else \
                    set(tratto[meta - LARGO_PASSAGGIO // 2:meta + LARGO_PASSAGGIO // 2])
                for cx, cy in tratto:
                    g[cy][cx] = "S" if (cx, cy) in passaggio else "M"
                tratto = []
    a["griglia"] = ["".join(r) for r in g]


def disegna_area(a, mondo):
    """Il fondale dell'area come tile 8x8: il suolo dai tile procedurali, gli edifici dalle loro
    tele, la Fontana dei Matti dalla sua. Ritorna (tile unici, indice per cella, elementi per
    monumento). Il primo tile e' il vuoto, per le celle fuori dall'area."""
    monumenti = mondo["monumenti"]
    censimento = mondo.get("censimento", {})
    w, h = a["larghezza"], a["altezza"]
    tile_di = {}
    elementi = {}
    for n, (mid, (x0, y0, ew, eh)) in enumerate(sorted(a.get("edifici", {}).items())):
        m = monumenti[mid]
        faccia = faccia_di(a, mid, monumenti)
        altezza = censimento.get(mid, {}).get("altezza_m", "").strip()
        tela = PM.dipingi(mid, m["nome"], ew, eh, faccia, {"altezza_m": float(altezza) if altezza else None}, n)
        elementi[mid] = tela.elementi
        for ty, riga in enumerate(tela.tagli()):
            for tx, pix in enumerate(riga):
                tile_di[(x0 + tx, y0 + ty)] = pix
    fontana = [(x, y) for y in range(h) for x in range(w) if a["griglia"][y][x] == "F"]
    if fontana:
        fx0, fy0 = min(x for x, _ in fontana), min(y for _, y in fontana)
        fw, fh = max(x for x, _ in fontana) - fx0 + 1, max(y for _, y in fontana) - fy0 + 1
        tela = PM.fontana_dei_matti(fw, fh)
        elementi["fontana_matti"] = tela.elementi
        for ty, riga in enumerate(tela.tagli()):
            for tx, pix in enumerate(riga):
                tile_di[(fx0 + tx, fy0 + ty)] = pix
    tile_unici = {tuple(map(tuple, _tile(tile_vuoto))): 0}
    indici = []
    for y in range(h):
        for x in range(w):
            pix = tile_di.get((x, y))
            if pix is None:
                pix = _tile(TILE_FONDALI[tile_per_cella(a["griglia"], x, y, a["id"] in AREE_DEL_MONTE,
                                                        a.get("monte"))][1])
            chiave = tuple(map(tuple, pix))
            indici.append(tile_unici.setdefault(chiave, len(tile_unici)))
    return list(tile_unici), indici, elementi


def controlla_grafica(a, tile_unici, elementi):
    for mid in sorted(a.get("edifici", {})):
        manca = PM.elementi_mancanti(mid, elementi.get(mid, {}))
        if manca:
            raise ErroreMondo(f"{a['file']}: il monumento {mid} non ha " +
                              ", ".join(f"{k} ({elementi.get(mid, {}).get(k, 0)} di {v})" for k, v in sorted(manca.items())))
    if len(tile_unici) > TILE_MAX_PER_AREA:
        raise ErroreMondo(f"{a['file']}: {len(tile_unici)} tile unici, il massimo per un BG e' {TILE_MAX_PER_AREA}")
    for tile in tile_unici:
        for riga in tile:
            for v in riga:
                if not 0 <= v < len(PALETTE_FONDALI):
                    raise ErroreMondo(f"{a['file']}: colore {v} fuori dalla palette dei fondali")


def celle_edifici_calpestabili(a):
    """Celle di un edificio su cui si potrebbe camminare: devono essere nessuna."""
    return sorted((x, y) for (x0, y0, w, h) in a.get("edifici", {}).values()
                  for y in range(y0, y0 + h) for x in range(x0, x0 + w)
                  if not solida(a["griglia"][y][x]) or a["griglia"][y][x] in VARCHI)


def controlla_edifici(a, posati, monumenti):
    """Ogni edificio dell'area c'e', con le misure in tile esatte, e la griglia lo contiene tutto."""
    attesi = edifici_attesi(a["id"], monumenti)
    for mid in sorted(set(attesi) - set(posati)):
        raise ErroreMondo(f"{a['file']}: manca l'edificio {mid}")
    for mid, (x0, y0, w, h) in sorted(posati.items()):
        if mid not in attesi:
            raise ErroreMondo(f"{a['file']}: {mid} non e' un edificio di quest'area")
        if (w, h) != attesi[mid]:
            raise ErroreMondo(f"{a['file']}: l'edificio {mid} e' {w}x{h} tile, il censimento lo vuole "
                              f"{attesi[mid][0]}x{attesi[mid][1]}")
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                if a["griglia"][y][x] not in (MURO_EDIFICIO, FACCIATA_EDIFICIO, PORTONE_EDIFICIO):
                    raise ErroreMondo(f"{a['file']}: l'edificio {mid} non occupa ({x}, {y})")


def celle_varco(a, lettera):
    return [(x, y) for y, r in enumerate(a["griglia"]) for x, c in enumerate(r) if c == lettera]


def raggiungibili(a, inizio):
    g, w, h = a["griglia"], a["larghezza"], a["altezza"]
    visti, coda = {inizio}, deque([inizio])
    while coda:
        x, y = coda.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in visti and not solida(g[ny][nx]):
                visti.add((nx, ny))
                coda.append((nx, ny))
    return visti


def lati_del_varco(a, lettera):
    """I bordi della griglia toccati dal varco ('alto', 'basso', 'sinistra', 'destra')."""
    lati = set()
    for x, y in celle_varco(a, lettera):
        if x == 0:
            lati.add("sinistra")
        if x == a["larghezza"] - 1:
            lati.add("destra")
        if y == 0:
            lati.add("alto")
        if y == a["altezza"] - 1:
            lati.add("basso")
    return lati


def distanza_dal_varco(a, punto, lettera):
    px, py = punto
    return min(max(abs(px - x), abs(py - y)) for x, y in celle_varco(a, lettera))


def controlla(aree, mondo):
    """mondo: {"grafo": grafo.json, "varchi": varchi per area come in mondo/varchi.json}."""
    grafo, lati_attesi = mondo["grafo"], mondo["varchi"]
    per_id = {a["id"]: a for a in aree}
    nel_grafo = {g["id"].lower(): g for g in grafo["aree"]}
    for aid in sorted(set(nel_grafo) - set(per_id)):
        raise ErroreMondo(f"l'area {aid} di grafo.json non ha un file .area")
    for a in aree:
        if a["id"] not in nel_grafo:
            raise ErroreMondo(f"{a['file']}: l'area {a['id']} non e' in grafo.json")

    for a in aree:
        dichiarate = {u[0] for u in a["uscite"]}
        presenti = {c for r in a["griglia"] for c in r if c in VARCHI}
        for lettera in presenti - dichiarate:
            raise ErroreMondo(f"{a['file']}: varco '{lettera}' nella griglia senza riga 'uscita'")
        for lettera, _, _, n in a["uscite"]:
            if lettera not in presenti:
                raise ErroreMondo(f"{a['file']}:{n}: uscita '{lettera}' che non e' nella griglia")

    # (a) ogni uscita e' un arco di grafo.json, e ogni arco ha la sua uscita ai due capi
    archi = {}
    for e in grafo["archi"]:
        archi.setdefault(e["da"].lower(), set()).add(e["a"].lower())
        archi.setdefault(e["a"].lower(), set()).add(e["da"].lower())
    for a in aree:
        verso = [u[1] for u in a["uscite"] if u[1] not in DUNGEON]
        for lettera, dest, _, n in a["uscite"]:
            if dest in DUNGEON:
                if not nel_grafo[a["id"]].get("dungeon"):
                    raise ErroreMondo(f"{a['file']}:{n}: ingresso a {dest}, ma grafo.json non da' "
                                      f"un dungeon all'area {a['id']}")
            elif dest not in archi.get(a["id"], set()):
                raise ErroreMondo(f"{a['file']}:{n}: uscita '{lettera}' verso {dest}, ma grafo.json "
                                  f"non ha l'arco {a['id']}-{dest}")
            elif verso.count(dest) > 1:
                raise ErroreMondo(f"{a['file']}:{n}: due uscite verso {dest}")
        for dest in sorted(archi.get(a["id"], set()) - set(verso)):
            raise ErroreMondo(f"{a['file']}: grafo.json ha l'arco {a['id']}-{dest}, ma l'area non ha "
                              f"l'uscita")

    for a in aree:
        for lettera, dest, spawn, n in a["uscite"]:
            if dest in DUNGEON:
                continue
            # (b) il varco sta sul bordo che varchi.json da' a quell'arco
            atteso = [v["lato"] for v in lati_attesi[a["id"].upper()] if v["verso"] == dest.upper()]
            lati = lati_del_varco(a, lettera)
            if lati != set(atteso):
                trovato = ", ".join(sorted(lati)) or "nessun bordo"
                raise ErroreMondo(f"{a['file']}:{n}: il varco '{lettera}' verso {dest} sta su {trovato}, "
                                  f"varchi.json lo vuole a {atteso[0]}")
            if spawn not in a["spawn"]:
                raise ErroreMondo(f"{a['file']}:{n}: manca lo spawn {spawn}")

    for a in aree:
        varchi = [(x, y) for y, r in enumerate(a["griglia"]) for x, c in enumerate(r) if c in VARCHI]
        arrivi = [(0, None)] + [(u[2], u[0]) for u in a["uscite"] if u[1] not in DUNGEON]
        for s, propria in arrivi:
            if s not in a["spawn"]:
                raise ErroreMondo(f"{a['file']}: manca lo spawn {s}")
            sx, sy = a["spawn"][s]
            if not (0 <= sx < a["larghezza"] and 0 <= sy < a["altezza"]) or solida(a["griglia"][sy][sx])                     or a["griglia"][sy][sx] in VARCHI:
                raise ErroreMondo(f"{a['file']}: lo spawn {s} ({sx}, {sy}) non e' su una cella calpestabile")
            # (c) lontano dalla propria uscita, e comunque non addosso a un altro varco
            if propria is not None:
                distanza = distanza_dal_varco(a, (sx, sy), propria)
                if distanza < DISTANZA_MIN_SPAWN_USCITA:
                    raise ErroreMondo(f"{a['file']}: lo spawn {s} ({sx}, {sy}) e' a {distanza} tile dalla "
                                      f"sua uscita '{propria}', ne servono almeno {DISTANZA_MIN_SPAWN_USCITA}")
            distanza = min(max(abs(sx - x), abs(sy - y)) for x, y in varchi)
            if distanza < DISTANZA_MIN_SPAWN:
                raise ErroreMondo(f"{a['file']}: lo spawn {s} ({sx}, {sy}) e' a {distanza} tile da un varco, "
                                  f"ne servono almeno {DISTANZA_MIN_SPAWN}")
        for s, (sx, sy) in sorted(a["spawn"].items()):
            if not (0 <= sx < a["larghezza"] and 0 <= sy < a["altezza"]) or solida(a["griglia"][sy][sx]) \
                    or a["griglia"][sy][sx] in VARCHI:
                raise ErroreMondo(f"{a['file']}: lo spawn {s} ({sx}, {sy}) non e' su una cella calpestabile")
            visti = raggiungibili(a, (sx, sy))
            for lettera, _, _, n in a["uscite"]:
                vicini = {(x + dx, y + dy) for x, y in celle_varco(a, lettera)
                          for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))}
                if not vicini & visti:
                    raise ErroreMondo(f"{a['file']}:{n}: il varco '{lettera}' non si raggiunge "
                                      f"camminando dallo spawn {s}")


def controlla_vicinanze(a):
    """Il vincolo "vicino_a" di una riga uscita: il varco e il suo spawn d'arrivo stanno entro N tile
    (distanza a scacchiera) dal varco di riferimento. Per le scale laterali che sbucano in una via
    poco prima di Piazza Grande."""
    spawn_di = {u[0]: u[2] for u in a["uscite"]}
    for lettera, (rif, massimo, n) in sorted(a["vicino"].items()):
        if rif not in spawn_di:
            raise ErroreMondo(f"{a['file']}:{n}: '{lettera}' vicino_a '{rif}', ma '{rif}' non e' un'uscita")
        celle_rif = celle_varco(a, rif)
        varco = min(max(abs(x - rx), abs(y - ry)) for x, y in celle_varco(a, lettera) for rx, ry in celle_rif)
        if varco > massimo:
            raise ErroreMondo(f"{a['file']}:{n}: il varco '{lettera}' e' a {varco} tile dal varco '{rif}', "
                              f"ne vuole al massimo {massimo}")
        spawn = distanza_dal_varco(a, a["spawn"][spawn_di[lettera]], rif)
        if spawn > massimo:
            raise ErroreMondo(f"{a['file']}:{n}: lo spawn d'arrivo da '{lettera}' e' a {spawn} tile dal varco "
                              f"'{rif}', ne vuole al massimo {massimo}")


def larghezza_via_tile(misura):
    return max(2, int(round(misura["larghezza_mediana_m"] / 1.5)))


def misure_piazza_tile(misura, fattore=None):
    """(larghezza, altezza) sullo schermo: il lato lungo e' orizzontale se il suo asse punta a
    nord o a sud (destra o sinistra), verticale se a est o a ovest. fattore = (lungo, corto) comprime
    i due lati (None: in scala)."""
    f_lungo, f_corto = fattore or (None, None)
    lungo = int(round(misura["lato_lungo_m"] / 1.5 * (f_lungo or 1)))
    corto = int(round(misura["lato_corto_m"] / 1.5 * (f_corto or 1)))
    if M.lato_schermo(misura["asse_lungo_bussola"]) in ("destra", "sinistra"):
        return lungo, corto
    return corto, lungo


def asse_lungo_area(a):
    return "verticale" if a["altezza"] >= a["larghezza"] else "orizzontale"


def larghezze_lungo_l_asse(a):
    """Per ogni linea perpendicolare all'asse lungo dell'area, il tratto calpestabile piu' lungo."""
    g = a["griglia"]
    linee = g if asse_lungo_area(a) == "verticale" else ["".join(r[x] for r in g) for x in range(a["larghezza"])]
    out = []
    for linea in linee[1:-1]:
        tratti = "".join("x" if not solida(c) and c not in VARCHI else " " for c in linea).split()
        if tratti:
            out.append(max(len(t) for t in tratti))
    return out


def controlla_proporzioni(a, misure):
    if "via" in a:
        nome, n = a["via"]
        misura = misure["vie"].get(nome)
        if not misura or misura["area"].lower() != a["id"] or "larghezza_mediana_m" not in misura:
            raise ErroreMondo(f"{a['file']}:{n}: la via '{nome}' non ha una larghezza misurata per quest'area")
        larga = larghezza_via_tile(misura)
        tolleranza = a.get("tolleranza_via", TOLLERANZA_VIA)
        righe = sorted(larghezze_lungo_l_asse(a))
        mediana = righe[len(righe) // 2]
        if mediana > larga * tolleranza:
            raise ErroreMondo(f"{a['file']}:{n}: {nome} e' larga {mediana} tile sulla griglia, la misura dice "
                              f"{larga} (al massimo {larga * tolleranza:g})")
        if mediana < 2:
            raise ErroreMondo(f"{a['file']}:{n}: {nome} e' larga {mediana} tile: per passare ne servono 2")
        if "strettoia" in a and min(righe) > a["strettoia"]:
            raise ErroreMondo(f"{a['file']}: la strettoia di {a['strettoia']} tile non c'e': il tratto piu' "
                              f"stretto e' {min(righe)}")
    if "piazza" in a:
        nome, n = a["piazza"]
        misura = misure["piazze"].get(nome)
        if not misura:
            raise ErroreMondo(f"{a['file']}:{n}: la piazza '{nome}' non e' fra le misure")
        w, h = misure_piazza_tile(misura, a.get("fattore_piazza"))
        if w > a["larghezza"] - 2 or h > a["altezza"] - 2:
            raise ErroreMondo(f"{a['file']}:{n}: {nome} in scala e' {w}x{h} tile e non sta nella griglia "
                              f"{a['larghezza']}x{a['altezza']}: serve un fattore_piazza")
        rx, ry = a["riferimento"]
        x0, y0 = rx - w // 2, ry - h // 2
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                if not (0 <= x < a["larghezza"] and 0 <= y < a["altezza"]) or \
                        (solida(a["griglia"][y][x]) and a["griglia"][y][x] not in "F"):
                    raise ErroreMondo(f"{a['file']}:{n}: {nome} ({w}x{h} tile intorno al riferimento) non e' "
                                      f"libera in ({x}, {y})")


def anello(grafo):
    """L'anello di grafo.json, senza la ripetizione finale della prima area."""
    return [aid.lower() for aid in grafo["anello"][:-1]]


# --- Uscita C++ -------------------------------------------------------------------------------

def pixel_cartiglio(pezzo):
    """Il pezzo 'sinistro', 'centrale' o 'destro' del cartiglio, 32x16 pixel: pergamena di pietra
    chiara con il bordo scuro, le volute alle estremita'."""
    out = []
    for y in range(16):
        riga = []
        for x in range(32):
            bordo = y in (0, 15) or (pezzo == "sinistro" and x == 0) or (pezzo == "destro" and x == 31)
            dentro = y in (1, 14) or (pezzo == "sinistro" and x == 1) or (pezzo == "destro" and x == 30)
            voluta = (pezzo == "sinistro" and x < 4 and y in (3, 12)) or (pezzo == "destro" and x > 27 and y in (3, 12))
            if bordo or voluta:
                riga.append(1)
            elif dentro:
                riga.append(4)
            else:
                riga.append(5 if (x + y) % 9 else 4)
        out.append(riga)
    return out


def tile_cartiglio():
    """Le parole dei tre pezzi del cartiglio, 8 tile ciascuno (4x2, riga per riga)."""
    pezzi = []
    for pezzo in ("sinistro", "centrale", "destro"):
        px = pixel_cartiglio(pezzo)
        parole = []
        for ty in range(2):
            for tx in range(4):
                parole += parole_tile([r[tx * 8:tx * 8 + 8] for r in px[ty * 8:ty * 8 + 8]])
        pezzi.append(parole)
    return pezzi


def parole_tile(pixel):
    out = []
    for riga in pixel:
        parola = 0
        for x, v in enumerate(riga):
            parola |= v << (4 * x)
        out.append(parola)
    return out


def a_blocchi(valori, per_riga=16, formato=str):
    return "\n".join("    " + ", ".join(formato(v) for v in valori[i:i + per_riga]) + ","
                     for i in range(0, len(valori), per_riga))


def grande(a):
    return a["larghezza"] > LATO_MAPPA_HW or a["altezza"] > LATO_MAPPA_HW


def lati_fondale(a):
    """Lati della mappa BG: 32 o 64 per un'area che sta in 64x64, multipli di 32 per una big map."""
    if grande(a):
        return (-(-a["larghezza"] // 32) * 32, -(-a["altezza"] // 32) * 32)
    return tuple(32 if lato <= 32 else 64 for lato in (a["larghezza"], a["altezza"]))


def celle_fondale(a, mappa):
    """Le celle della mappa BG (indice del tile, palette 0: Butano aggiunge gli scostamenti).
    Big map: riga per riga. Mappa hardware: a blocchi 32x32, nell'ordine della VRAM."""
    gw, gh = lati_fondale(a)
    out = [INDICE_TILE["VUOTO"]] * (gw * gh)
    for y in range(a["altezza"]):
        for x in range(a["larghezza"]):
            if grande(a):
                i = y * gw + x
            else:
                i = (((y // 32) * (gw // 32)) + (x // 32)) * 1024 + (y % 32) * 32 + (x % 32)
            out[i] = mappa[y * a["larghezza"] + x]
    return out


def ordina(aree, giro):
    altre = sorted(a["id"] for a in aree if a["id"] not in giro)
    per_id = {a["id"]: a for a in aree}
    return [per_id[i] for i in giro + altre]


def scrivi_header(aree, grafo, palette_stile):
    giro = anello(grafo)
    quote = {g["id"].lower(): g["quota_m"] for g in grafo["aree"]}
    aree = ordina(aree, giro)
    per_id = {a["id"]: a for a in aree}
    indice = {a["id"]: i for i, a in enumerate(aree)}
    colore = lambda rif: S.colore(palette_stile, rif)  # noqa: E731

    out = [
        "// GENERATO da tools/genera_mondo.py a partire da mondo/aree/*.area, mondo/grafo.json,",
        "// mondo/varchi.json, mondo/monumenti.json e stile/dati/palette.json.",
        "// Non modificare a mano: si accede ai dati solo da include/mondo_logica.h.",
        "#ifndef GUBBIO_MONDO_H",
        "#define GUBBIO_MONDO_H",
        "",
        "#include <cstdint>",
        "",
        "#include \"bn_tile.h\"",
        "",
        "#include \"testi.h\"",
        "",
        "namespace gubbio::mondo",
        "{",
        "",
        "// Orientamento di tutte le aree: alto = ovest, basso = est, sinistra = sud, destra = nord.",
        "// Scala: un tile da 8 px = 1,5 m.",
        "",
        "enum class Cella : uint8_t",
        "{",
    ]
    out += [f"    {nome} = {i}," for i, (nome, _) in enumerate(CELLE.values())]
    out += [
        "};",
        "",
        f"inline constexpr int PRIMO_VARCO = {PRIMO_VARCO};   // cella = PRIMO_VARCO + indice del varco",
        f"inline constexpr int PRIMA_CELLA_SOLIDA = {list(CELLE.values()).index(('FONTANA', True))};",
        f"inline constexpr int DISTANZA_MIN_SPAWN = {DISTANZA_MIN_SPAWN};",
        f"inline constexpr int DISTANZA_MIN_SPAWN_USCITA = {DISTANZA_MIN_SPAWN_USCITA};",
        f"inline constexpr int LATO_MAX = {LATO_MAX};          // tile per lato di un'area",
        f"inline constexpr int SPAWN_PER_AREA = 6;",
        f"inline constexpr int VARCHI_MAX = {len(VARCHI)};",
        "",
        "enum class AreaId : uint8_t",
        "{",
    ]
    out += [f"    {a['id'].upper()}," for a in aree]
    out += [
        "};",
        "",
        f"inline constexpr int AREE_CONTEGGIO = {len(aree)};",
        f"inline constexpr int ANELLO_CONTEGGIO = {len(giro)};",
        "inline constexpr AreaId ANELLO[ANELLO_CONTEGGIO] = {",
        "    " + ", ".join(f"AreaId::{i.upper()}" for i in giro) + ",",
        "};",
        "",
        "inline constexpr int DUNGEON = -1;   // destinazione di un ingresso che in F2 non porta altrove",
        "",
        "struct Punto",
        "{",
        "    uint8_t x;",
        "    uint8_t y;",
        "};",
        "",
        "struct Varco",
        "{",
        "    int8_t destinazione;              // AreaId, oppure DUNGEON",
        "    uint8_t spawn;                    // spawn d'arrivo nell'area di destinazione",
        "    testi::TestoId etichetta;         // per un DUNGEON: il nome mostrato all'ingresso",
        "};",
        "",
        "struct Area",
        "{",
        "    const uint8_t* griglia;           // larghezza * altezza celle",
        "    const uint8_t* mappa;             // larghezza * altezza tile del fondale",
        "    uint8_t larghezza;",
        "    uint8_t altezza;",
        "    const uint16_t* fondale;          // celle della mappa BG (vedi lati_fondale in genera_mondo.py)",
        "    uint8_t larghezza_fondale;",
        "    uint8_t altezza_fondale;",
        "    bool fondale_grande;              // big map (oltre 64 tile): celle riga per riga",
        "    const bn::tile* tile;             // i tile 8x8 dell'area (il primo e' il vuoto)",
        "    uint16_t tile_conteggio;",
        "    int16_t quota_da;                 // metri sopra Piazza Quaranta Martiri",
        "    int16_t quota_a;                  // diversa da quota_da solo per le strade in salita",
        "    testi::TestoId etichetta;",
        "    uint8_t varchi;",
        "    Varco varco[VARCHI_MAX];",
        "    Punto spawn[SPAWN_PER_AREA];",
        "};",
        "",
    ]

    for a in aree:
        lettere = [u[0] for u in a["uscite"]]
        celle = []
        mappa = []
        for y, r in enumerate(a["griglia"]):
            for x, c in enumerate(r):
                if c in VARCHI:
                    celle.append(PRIMO_VARCO + lettere.index(c))
                else:
                    celle.append(list(CELLE).index(c))
                mappa.append(tile_per_cella(a["griglia"], x, y, a["id"] in AREE_DEL_MONTE, a.get("monte")))
        n = a["larghezza"] * a["altezza"]
        nome = a["id"].upper()
        out += [f"inline constexpr uint8_t GRIGLIA_{nome}[{n}] = {{", a_blocchi(celle, 32), "};", "",
                f"inline constexpr uint8_t MAPPA_{nome}[{n}] = {{", a_blocchi(mappa, 32), "};", ""]
        gw, gh = lati_fondale(a)
        fondale = celle_fondale(a, a["indici"])
        out += [f"// {len(a['tile'])} tile unici: suolo, dislivello e monumenti.",
                f"inline constexpr bn::tile TILE_{nome}[{len(a['tile'])}] = {{"]
        out += ["    { { " + ", ".join(f"0x{v:08X}" for v in parole_tile(t)) + " } }," for t in a["tile"]]
        out += ["};", ""]
        out += [f"// Fondale {gw}x{gh}" + (" (big map, riga per riga)" if grande(a) else " (a blocchi 32x32)")
                + ": fuori dall'area tile vuoti.",
                f"inline constexpr uint16_t FONDALE_{nome}[{gw * gh}] = {{", a_blocchi(fondale, 32), "};", ""]

    out += ["inline constexpr Area AREE[AREE_CONTEGGIO] = {"]
    for a in aree:
        nome = a["id"].upper()
        q = quote[a["id"]]
        varchi = []
        for lettera, dest, _, _ in a["uscite"]:
            if dest in DUNGEON:
                varchi.append(f"{{ DUNGEON, 0, testi::TestoId::{DUNGEON[dest]} }}")
            else:
                # si arriva sullo spawn che l'area di destinazione da' alla sua uscita verso di noi
                arrivo = [u[2] for u in per_id[dest]["uscite"] if u[1] == a["id"]][0]
                varchi.append(f"{{ {indice[dest]}, {arrivo}, testi::TestoId::{a['etichetta']} }}")
        while len(varchi) < len(VARCHI):
            varchi.append(f"{{ DUNGEON, 0, testi::TestoId::{a['etichetta']} }}")
        spawn = [a["spawn"].get(i, a["spawn"][0]) for i in range(6)]
        out += [
            f"    {{   // {a['id']}",
            f"        GRIGLIA_{nome}, MAPPA_{nome}, {a['larghezza']}, {a['altezza']},",
            f"        FONDALE_{nome}, {lati_fondale(a)[0]}, {lati_fondale(a)[1]}, {'true' if grande(a) else 'false'}, "
            f"TILE_{nome}, {len(a['tile'])}, {q[0]}, {q[1]},",
            f"        testi::TestoId::{a['etichetta']}, {len(a['uscite'])},",
            "        { " + ", ".join(varchi) + " },",
            "        { " + ", ".join(f"{{ {x}, {y} }}" for x, y in spawn) + " },",
            "    },",
        ]
    out += ["};", ""]

    out += ["// I tipi di tile del suolo, come li usa MAPPA_<AREA> (i tile veri sono in TILE_<AREA>).",
            "enum class TileFondale : uint8_t", "{"]
    out += [f"    {nome}," for nome, _ in TILE_FONDALI]
    out += ["};", "",
            f"inline constexpr int TILE_FONDALI = {len(TILE_FONDALI)};",
            "",
            "inline constexpr uint16_t PALETTE_FONDALI[16] = {",
            a_blocchi([colore(r) for r in PALETTE_FONDALI], 8, lambda v: f"0x{v:04X}"),
            "};", ""]

    out += ["// Il cartiglio dietro il nome dell'area: tre pezzi da 32x16 (sinistro, centrale, destro),",
            "// 8 tile ciascuno in mappatura 1D, con la palette dei fondali.",
            "inline constexpr int TILE_PER_PEZZO_CARTIGLIO = 8;",
            "inline constexpr bn::tile TILE_CARTIGLIO[3 * TILE_PER_PEZZO_CARTIGLIO] = {"]
    for pezzo in tile_cartiglio():
        for k in range(0, len(pezzo), 8):
            out.append("    { { " + ", ".join(f"0x{v:08X}" for v in pezzo[k:k + 8]) + " } },")
    out += ["};", ""]

    pixel = [[int(c, 16) if c != "." else 0 for c in riga] for riga in GIOCATORE]
    tiles = []
    for ty in range(2):
        for tx in range(2):
            tiles += parole_tile([riga[tx * 8:tx * 8 + 8] for riga in pixel[ty * 8:ty * 8 + 8]])
    out += ["// Il giocatore, 16x16 (4 tile in mappatura 1D): segnaposto finche' non arrivano le pose.",
            "inline constexpr uint32_t TILE_GIOCATORE[4 * 8] = {",
            a_blocchi(tiles, 8, lambda v: f"0x{v:08X}"), "};", "",
            "inline constexpr uint16_t PALETTE_GIOCATORE[16] = {",
            a_blocchi([colore(r) for r in PALETTE_GIOCATORE], 8, lambda v: f"0x{v:04X}"),
            "};", "", "}", "", "#endif", ""]
    return "\n".join(out)


def mondo_del_repo():
    """Il grafo (mondo/grafo.json) e i lati dei varchi (mondo/varchi.json) del repo."""
    with open(M.OUT_VARCHI, encoding="utf-8") as f:
        varchi = json.load(f)["varchi"]
    with open(M.OUT_MONUMENTI, encoding="utf-8") as f:
        monumenti = json.load(f)["monumenti"]
    with open(os.path.join(RADICE, "mondo", "fonti", "misure_osm.json"), encoding="utf-8") as f:
        misure = json.load(f)
    return {"grafo": M.carica_grafo(), "varchi": varchi, "monumenti": monumenti, "misure": misure,
            "censimento": M.carica_censimento()}


def genera(sorgenti, palette_stile, mondo=None):
    """sorgenti: lista di (nome, testo). Ritorna il testo di include/mondo.h."""
    mondo = mondo or mondo_del_repo()
    aree = [leggi_area(nome, testo) for nome, testo in sorgenti]
    for a in aree:
        controlla_edifici(a, posa_edifici(a, mondo["monumenti"]), mondo["monumenti"])
        applica_dislivello(a, mondo["grafo"])
    controlla(aree, mondo)
    for a in aree:
        controlla_vicinanze(a)
        controlla_proporzioni(a, mondo["misure"])
        oltre = errori_belvedere(a)
        if oltre:
            raise ErroreMondo(f"{a['file']}: oltre il parapetto del belvedere ci sono tetti a quota piena: {oltre[:4]}")
        calpestabili = celle_edifici_calpestabili(a)
        if calpestabili:
            raise ErroreMondo(f"{a['file']}: celle di edificio calpestabili: {calpestabili[:4]}")
        a["tile"], a["indici"], elementi = disegna_area(a, mondo)
        controlla_grafica(a, a["tile"], elementi)
    return scrivi_header(aree, mondo["grafo"], palette_stile)


def sorgenti_del_repo():
    out = []
    for p in sorted(glob.glob(AREE_GLOB)):
        with open(p, encoding="utf-8") as f:
            out.append((os.path.relpath(p, RADICE).replace(os.sep, "/"), f.read()))
    return out


def main():
    try:
        header = genera(sorgenti_del_repo(), S.carica("palette"))
    except ErroreMondo as e:
        print(f"[mondo] ERRORE: {e}", file=sys.stderr)
        return 1
    if "--controlla" in sys.argv:
        attuale = open(USCITA, encoding="utf-8").read() if os.path.exists(USCITA) else ""
        if attuale != header:
            print("[mondo] include/mondo.h non e' aggiornato: python tools/genera_mondo.py", file=sys.stderr)
            return 1
        print("[mondo] OK: include/mondo.h aggiornato")
        return 0
    with open(USCITA, "w", encoding="utf-8", newline="\n") as f:
        f.write(header)
    print(f"[mondo] scritto {os.path.relpath(USCITA, RADICE)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
