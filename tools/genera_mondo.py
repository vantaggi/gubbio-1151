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
import math
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
import pittore_citta as PC  # noqa: E402
import pittore_interni as PI  # noqa: E402

AREE_GLOB = os.path.join(RADICE, "mondo", "aree", "*.area")
USCITA = os.path.join(RADICE, "include", "mondo.h")

# Destinazioni che non sono aree dell'anello: in F2 esiste solo il loro ingresso.
DUNGEON = {"gola_bottaccione": "AREA_GOLA_BOTTACCIONE"}

# Aree fuori citta': il muro e' il pendio del monte, non un tetto.
AREE_DEL_MONTE = {"monte_ingino", "bottaccione"}
# Le stanze del dungeon della gola del Bottaccione: il muro e' la rupe di calcare a strati, e la
# palette e' quella cupa (le rampe di notte: la scelta di stile 1 vale per la notte e per il Bottaccione).
AREE_GOLA = {"gola_striscia", "gola_miasmi", "gola_arco", "condotto"}

# Gli stradoni del Monte Ingino: i dati del percorso (tools/disegna_stradoni.py ne fa la griglia).
STRADONI = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mondo", "stradoni.json")
LUNGHEZZA_MIN_TRATTO = 10   # una colonna di ghiaia piu' lunga e' un tratto, non un tornante

# Uno spawn d'arrivo a 2 tile dal varco rimanda indietro chi tiene premuta la direzione.
DISTANZA_MIN_SPAWN = 3
# Dalla propria uscita, quella da cui si e' entrati, lo spawn sta piu' lontano: si arriva gia'
# dentro l'area, non sulla soglia.
DISTANZA_MIN_SPAWN_USCITA = 6
# Gli arrivi di un'area (0-7): Quaranta Martiri ne ha 7, l'ultimo e' davanti alla bottega del carradore (INT2).
SPAWN_PER_AREA = 8

# Celle della griglia: carattere del file .area -> (nome C++, solida). L'ordine conta: il gioco
# (mondo::solida in include/mondo_logica.h) dice solida ogni cella da PRIMA_CELLA_SOLIDA in su, quindi
# tutte le calpestabili stanno prima di FONTANA (controlla_ordine_celle).
CELLE = {
    ".": ("SUOLO", False),
    ",": ("STRADA", False),
    "S": ("SCALINATA", False),
    "L": ("LASTRICO", False),      # il lastricato a lastre di una piazza
    "K": ("CORSO", False),         # i corsi di pietra che disegnano il lastricato
    "Z": ("VIALETTO", False),      # i vialetti dei giardini
    "J": ("ARCO", False),          # sotto l'arco di una porta della citta': si passa
    "N": ("PRATO", False),         # il prato fuori le mura ("prato" nella .area)
    "b": ("BRECCIA", False),       # la ghiaia degli stradoni del Monte Ingino
    "g": ("MIASMA", False),        # la nebbia verde dei miasmi sulla via: ci si cammina (e si perdono PV)
    "+": ("PONTE", False),         # il ponticello sul torrente della gola
    "F": ("FONTANA", True),
    "d": ("PORTONE", True),        # portone di un edificio: solo visivo, non si attraversa
    "#": ("MURO", True),
    "=": ("PARAPETTO", True),      # affaccio sul vuoto
    "C": ("FACCIATA", True),       # facciata monumentale (Consoli, San Francesco, ...)
    "P": ("FACCIATA_2", True),     # seconda facciata (Pretorio, Bargello, acquedotto, ...)
    "M": ("MURO_CONTENIMENTO", True),  # il gradone: il terreno a monte sta piu' in alto
    "V": ("CITTA_BASSA", True),    # oltre il parapetto di un belvedere: la citta' vista dall'alto
    "W": ("MURA", True),           # le mura della citta', dove l'area tocca il perimetro
    "Q": ("LAMPIONE", True),
    "O": ("POZZO", True),
    "Y": ("SIEPE", True),          # le siepi intorno alle aiuole dei giardini
    "D": ("AIUOLA", True),         # l'aiuola fiorita dentro la siepe
    "T": ("ALBERO", True),
    "X": ("TORRE", True),          # i piloni della torre di una porta, ai lati dell'arco
    "R": ("GRADINATA", True),      # la cavea del Teatro Romano
    "U": ("ARCATA", True),         # l'anello esterno di arcate del Teatro
    "r": ("CESPUGLIO", True),      # un cespuglio basso, nel prato e ai margini del bosco
    "u": ("CIPRESSO", True),       # un cipresso, alto e stretto: 1x2 tile
    "v": ("VASCA", True),          # la vasca all'incrocio dei vialetti dei giardini
    "m": ("MURETTO", True),        # muretto a secco sul lato esterno dei tornanti
    "p": ("PARACARRO", True),      # i paracarri sul lato a valle degli stradoni
    "h": ("CHIOSTRO", True),       # il chiostro accanto a una chiesa, col loggiato e il pozzo
    "q": ("PANCA", True),          # le panche di legno di un interno
    "l": ("CANDELIERE", True),     # un candeliere accanto all'altare
    "w": ("VETRATA", True),        # una vetrata nel muro di un interno
    "c": ("CAPPELLETTA", True),    # le cappellette ai tornanti degli stradoni
    "k": ("ROCCIA", True),         # le rocce sulle scarpate del monte
    "n": ("COLONNA", True),        # le colonne fra le navate di un interno
    "a": ("ALTARE", True),         # l'altare, con l'urna del santo
    "e": ("CERO", True),           # un cero esposto
    "~": ("ACQUA", True),          # il torrente (il Camignano nella gola): non si attraversa
    "x": ("STRISCIA_NERA", True),  # la rupe con la striscia nera del limite K-Pg (Bottaccione)
    "i": ("LAPIDE", True),         # la lapide che segna il limite K-Pg
    "|": ("DIGA", True),           # la diga del Bottaccione, in fondo alla gola
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
TILE_MAX_PER_AREA = 1024     # tile unici di un area, suolo e monumenti insieme: il massimo di Butano per un BG (pezzo EDI)

# Dislivello. La salita va verso nord-est: sullo schermo in basso (est) o a destra (nord).
LATI_A_MONTE = ("alto", "destra")      # nord in alto: la salita verso nord-est e' in alto o a destra
LATI_A_VALLE = {"alto": "basso", "destra": "sinistra"}
LATI_DEGLI_INTERNI = ("basso",)         # un interno non e' orientato: resta come era disegnato
QUOTA_MIN_BELVEDERE = 60       # metri: sotto non c'e' niente da guardare dall'alto
PROFONDITA_BELVEDERE = 3       # senza piazza: vuoto e parapetto nei primi tile dal bordo a valle
METRI_PER_GRADONE = 15
GRADONI_MAX = 3
TOLLERANZA_VIA = 1.5         # una via larga piu' del 50% della misura e' rifiutata
TOLLERANZA_VIA_MAX = 2.0     # dove OSM e' incompleto (quadrante sud-est), annotata nella .area
DISLIVELLO_PER_SCALE = 5       # metri fra le quote di due aree oltre cui il varco ha la scala
PROFONDITA_SCALE = 3           # tile di scala davanti al varco
LARGO_PASSAGGIO = 4            # la scala che attraversa un gradone
PRIMO_VARCO = 64                   # cella = PRIMO_VARCO + indice del varco nell'area
if len(CELLE) >= PRIMO_VARCO:
    raise SystemExit(f"[mondo] {len(CELLE)} tipi di cella: PRIMO_VARCO ({PRIMO_VARCO}) va alzato")

# --- Fondali procedurali ----------------------------------------------------------------------
# Palette dei fondali: (rampa, tono) della Guida di stile, dal piu' scuro al piu' chiaro dentro
# ogni rampa. L'indice 0 e' il colore di fondo.
PALETTE_FONDALI = PC.PALETTE_BASE   # il banco 0: (rampa, tono) della Guida, vedi tools/pittore_citta.py


def banchi_fondali(palette_stile, cupa=False, notte=False):
    """I banchi della palette dei fondali in BGR555 (pezzo EDI): di giorno; cupa (la gola: il banco 0 e' la
    palette cupa, gli altri le rampe di notte); notte (la citta' dopo il rientro da Porta Metauro: tutte le
    rampe di notte, ma oro e vermiglio del banco della vita restano caldi, perche' sono fiaccole e drappi
    alla luce delle fiaccole, L5)."""
    import pittore_citta as _PC
    out = []
    for b, banco in enumerate(BANCHI_FONDALI):
        if b == 0 and cupa:
            out.append([S.colore(palette_stile, r, True) for r in palette_cupa(palette_stile)])
            continue
        scura = cupa or notte
        out.append([S.colore(palette_stile, r, scura and not (b == 3 and r[0] in (_PC.O, _PC.R))) for r in banco])
    return out


def palette_cupa(palette_stile):
    """La palette cupa della gola: le rampe di notte, ma un tono piu' chiare (oltre il contorno), cosi'
    si legge come le notti delle cutscene. Dentro una rampa due voci non finiscono mai sullo stesso tono:
    dalla piu' chiara in giu', ognuna sale di uno solo se resta sotto quella sopra (la pietra chiarissima
    e la chiara restano distinte: la scaglia bianca ha due toni)."""
    toni = {r["nome"]: len(r["notte"]) for r in palette_stile["rampe"]}
    out = list(PALETTE_FONDALI)
    sopra = {}
    for i in sorted(range(2, len(out)), key=lambda i: -out[i][1]):
        rampa, tono = out[i]
        limite = sopra.get(rampa, toni[rampa]) - 1
        out[i] = (rampa, min(tono + 1, limite))
        sopra[rampa] = out[i][1]
    return out


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


def tile_lastrico(x, y):
    # lastre grandi di pietra chiara, giunti sottili sfalsati
    sfalsa = 4 if (y // 8) % 2 else 0
    if y % 8 == 7 or (x + sfalsa) % 8 == 7:
        return 3
    return 5 if (x + y) % 11 == 0 else 4


def tile_corso(x, y):
    # un corso di pietra piu' scura, a conci stretti, che taglia il lastricato
    if y in (0, 7):
        return 2
    return 3 if x % 4 == 3 else 2 if (x + y) % 5 == 0 else 3


def tile_vialetto(x, y):
    # ghiaia dei vialetti, chiara e minuta
    return 4 if (x * 3 + y * 7) % 5 else 5


def tile_arco(x, y):
    # sotto l'arco della porta: l'ombra della volta, il selciato che continua
    if y < 3:
        return 1
    return 3 if (x + y) % 4 else 2


def tile_lampione(x, y):
    # un lampione visto dall'alto: piede di pietra, lanterna chiara al centro
    if 2 <= x <= 5 and 2 <= y <= 5:
        return 13 if 3 <= x <= 4 and 3 <= y <= 4 else 1
    return tile_lastrico(x, y)


def tile_pozzo(x, y):
    return 2 if x in (0, 7) or y in (0, 7) else (12 if (x + y) % 3 else 13)


def tile_siepe(x, y):
    # siepe di bosso tagliata, fitta e scura, qualche foglia in luce
    return 11 if (x * 5 + y * 3) % 7 == 0 else 10


def tile_aiuola(x, y):
    # l'aiuola: erba chiara con i fiori sparsi
    if (x * 3 + y * 5) % 9 == 0:
        return 4
    return 11


def tile_albero(x, y):
    # chioma tonda vista dall'alto col contorno scuro, luce a sinistra in alto, l'erba intorno
    d = (x - 3.5) ** 2 + (y - 3.5) ** 2
    if d > 14:
        return 11
    if d > 9:
        return 1
    return 11 if x < 4 and y < 4 else 10


def tile_roverella(x, y):
    # roverella: chioma chiara e sfrangiata, a lobi
    d = (x - 3.5) ** 2 + (y - 3.5) ** 2 + (2 if (x + y) % 3 == 0 else 0)
    if d > 15:
        return 11
    return 1 if d > 11 else (11 if (x * 3 + y) % 4 == 0 else 10)


def tile_cipresso(x, y):
    # cipresso visto dall'alto: un fuso stretto e scuro con l'ombra lunga a destra
    if abs(x - 3.5) <= 1.5 and 0 < y < 7:
        return 1 if x == 5 else 10
    if x == 6 and 2 < y < 8:
        return 1
    return 11


def tile_cespuglio(x, y):
    # un cespuglio basso: due ciuffi tondi
    d1 = (x - 2.5) ** 2 + (y - 4.5) ** 2
    d2 = (x - 5) ** 2 + (y - 3) ** 2
    if min(d1, d2) > 6:
        return 11
    return 1 if min(d1, d2) > 4 else 10


def tile_vasca(x, y):
    return 4 if x in (0, 7) or y in (0, 7) else (13 if (x + y) % 4 else 12)


def tile_aiuola_2(x, y):
    # l'aiuola fiorita piu' fitta, fiori chiari e color mattone
    if (x * 5 + y * 3) % 7 == 0:
        return 9
    if (x * 3 + y * 5) % 11 == 0:
        return 5
    return 11


def tile_lastrico_2(x, y):
    sfalsa = 4 if (y // 8) % 2 else 0
    if y % 8 == 7 or (x + sfalsa) % 8 == 7:
        return 3
    return 5


def tile_lastrico_3(x, y):
    sfalsa = 4 if (y // 8) % 2 else 0
    if y % 8 == 7 or (x + sfalsa) % 8 == 7:
        return 2
    return 3 if (x * 3 + y * 5) % 13 == 0 else 4


def tile_prato(x, y):
    # prato rasato, qualche ciuffo piu' scuro
    return 10 if (x * 3 + y * 5 + (x * y) % 3) % 11 == 0 else 11


def tile_torre(x, y):
    return 3 if (x + (y // 3) * 2) % 4 == 3 or y % 3 == 0 else 4


def tile_gradinata(x, y):
    return 5 if y % 4 < 2 else 3


def tile_arcata(x, y):
    return 1 if 2 <= x <= 5 and y >= 3 else 4


def tile_breccia(x, y):
    # ghiaia chiara e battuta, sassi sparsi
    if (x * 5 + y * 3) % 7 == 0:
        return 3
    return 5 if (x * 3 + y * 7) % 4 else 4


def tile_breccia_2(x, y):
    # ghiaia piu' scura, battuta dalle ruote
    if (x * 3 + y * 5) % 6 == 0:
        return 2
    return 4 if (x + y * 3) % 5 else 3


def tile_breccia_solco(x, y):
    # i due solchi delle ruote nella ghiaia
    if x in (1, 6):
        return 3
    return 5 if (x * 3 + y * 7) % 4 else 4


def tile_muretto(x, y):
    # muretto a secco: pietre irregolari, giunti scuri
    if y in (0, 7):
        return 2
    return 2 if (x + (y // 3) * 3) % 5 == 4 or y % 3 == 0 else (3 if (x + y) % 4 else 4)


def tile_paracarro(x, y):
    # un paracarro di pietra tondo nell'erba del bosco
    d = (x - 3.5) ** 2 + (y - 3.5) ** 2
    if d > 7:
        return 10
    return 5 if x + y < 7 else 3


def tile_chiostro(x, y):
    return 3 if y in (0, 7) else 4


def tile_panca(x, y):
    # una panca di legno vista dall'alto: seduta e schienale, l'ombra sotto
    if y in (1, 2):
        return 14
    if 3 <= y <= 5:
        return 15
    return 2 if y == 6 else 4


def tile_candeliere(x, y):
    # il candeliere: piede tondo e la fiamma
    d = (x - 3.5) ** 2 + (y - 4.5) ** 2
    if 3 <= x <= 4 and y <= 2:
        return 9 if y < 2 else 5
    return 14 if d <= 5 else 4


def tile_vetrata(x, y):
    # una vetrata a sesto acuto nel muro: vetri colorati fra i piombi
    if x in (0, 7) or y == 7:
        return 3
    if x in (1, 6) or (y == 0 and x in (2, 5)):
        return 4
    return 1 if (x + y) % 3 == 0 else (13 if (x * y) % 2 else 9)


def tile_cappelletta(x, y):
    return 2 if y < 3 else 4


def tile_roccia(x, y):
    # un masso calcareo nel bosco: luce in alto a sinistra, ombra in basso
    d = (x - 3.5) ** 2 + (y - 4) ** 2
    if d > 13:
        return 10
    return 5 if x + y < 6 else (3 if x + y < 10 else 2)


def tile_miasma(x, y):
    # la nebbia verde bassa sul selciato: fitta, a fiocchi di due verdi, le pietre si vedono appena
    if (x * 3 + y * 5) % 4 == 0 or (x + 2 * y) % 5 == 0:
        return 11
    if (x + y) % 2 == 0:
        return 10
    return tile_strada(x, y)


def _strati(x, y, rossa):
    """La scaglia: strati orizzontali di spessore diverso (il giunto ondeggia), rossa o bianca."""
    giunto_1 = 2 + (1 if 3 <= x <= 5 else 0)
    giunto_2 = 6 - (1 if x <= 1 else 0)
    if y in (giunto_1, giunto_2):
        return 6 if rossa else 3
    if rossa:
        return 8 if y < giunto_1 else (7 if (x + y) % 5 else 9)
    return 5 if y < giunto_1 else (4 if (x * 3 + y) % 7 else 9)


def tile_rupe(x, y):
    # la rupe della gola: la scaglia rossa a strati irregolari
    return _strati(x, y, True)


def tile_rupe_bianca(x, y):
    # la scaglia bianca, piu' chiara, con un velo rosato fra gli strati
    return _strati(x, y, False)


def tile_rupe_frattura(x, y):
    # una frattura verticale che scende a zig-zag nella scaglia
    if x == 3 + (y // 3) % 2:
        return 1
    if x == 4 + (y // 3) % 2:
        return 6
    return _strati(x, y, True)


def tile_rupe_piede(x, y):
    # il piede della rupe sopra la via: il muschio e l'ombra in basso
    if y >= 6:
        return 1 if y == 7 and x % 3 == 0 else 14
    if y >= 4:
        return 11 if (x + y) % 2 else 10
    return _strati(x, y, True)


def tile_edera(x, y):
    # l'edera aggrappata alla rupe: grappoli di foglie su due verdi, i rami scuri
    if (x * 2 + y * 3) % 5 < 2:
        return 11 if (x + y) % 3 else 10
    if (x + y * 2) % 7 == 0:
        return 1
    return _strati(x, y, x % 2 == 0)


def _banda_nera(x, y, spessore):
    """Il limite K-Pg: la scaglia rossa sopra, l'orlo d'argilla, la banda nera continua, la bianca chiara
    sotto (cosi' la banda si stacca anche nella palette cupa)."""
    if y < 2:
        return 8 if (x + y) % 5 else 7
    if y == 2:
        return 14
    if y < 3 + spessore:
        return 1
    if y == 3 + spessore:
        return 14
    return 5 if (x * 3 + y) % 7 else 4


def tile_striscia_nera(x, y):
    # la banda nera, tre pixel
    return _banda_nera(x, y, 3)


def tile_striscia_nera_2(x, y):
    # dove la banda si gonfia: quattro pixel, l'argilla che cola in un punto
    if y == 7 and x in (2, 3):
        return 14
    return _banda_nera(x, y, 4 if 1 <= x <= 5 else 3)


def tile_lapide(x, y):
    # la lapide che segna il limite: cornice scura, pietra chiara, le righe incise
    if x in (0, 7) or y in (0, 7):
        return 2
    return 3 if y in (2, 4) and 1 < x < 6 else 5


def tile_ghiaia(x, y):
    # la ghiaia della via, nell'ombra della gola: un tono sotto la scaglia bianca, coi sassi chiari
    if (x * 5 + y * 3) % 7 == 0:
        return 4
    return 3 if (x * 3 + y * 7) % 4 else 2


def tile_ghiaia_2(x, y):
    # la stessa ghiaia con sassi piu' grossi e l'ombra sotto a destra
    if (x, y) in ((2, 2), (5, 5), (6, 1), (3, 2), (6, 5)):
        return 2
    if (x, y) in ((1, 2), (2, 1), (4, 5), (5, 4), (5, 1)):
        return 4
    return 3 if (x + y * 3) % 5 else 2


def tile_terra(x, y):
    # la terra battuta, coi sassolini
    if (x * 7 + y * 5) % 11 == 0:
        return 4
    return 15 if (x + y * 2) % 5 else 14


def tile_erba(x, y):
    # la sponda: terra e ciuffi d'erba
    if (x + y * 3) % 6 in (0, 1) and y % 3 != 2:
        return 11 if x % 2 else 10
    return 15 if (x * 2 + y) % 4 else 14


def tile_erba_2(x, y):
    # la sponda piu' fitta: felci a ventaglio
    if abs(x - 3.5) + (7 - y) * 0.6 < 4 and (x + y) % 2 == 0:
        return 11
    if (x * 3 + y) % 4 == 0:
        return 10
    return 15 if (x + y) % 3 else 14


def tile_acqua(x, y):
    # l'acqua del Camignano: increspature chiare sfalsate (i colori 12 e 13 si scambiano: i riflessi)
    return 13 if y % 4 == 1 and (x + (y // 4) * 3) % 6 < 2 else 12


def tile_acqua_sassi(x, y):
    # i sassi nel torrente, con la luce in alto a sinistra
    for cx, cy in ((2, 2), (5, 5)):
        d = (x - cx) ** 2 + (y - cy) ** 2
        if d <= 2:
            return 5 if x <= cx and y <= cy else 3
        if d <= 3:
            return 2
    return tile_acqua(x, y)


def tile_acqua_schiuma(x, y):
    # le rapide: creste bianche corte lungo la corrente
    if y % 4 == 1 and (x + (y // 4) * 4) % 8 < 3:
        return 5
    if y % 4 == 2 and (x + (y // 4) * 4 + 1) % 8 < 4:
        return 13
    return 12


def tile_canaletta(x, y):
    # la canaletta dell'acquedotto: il labbro di pietra sopra e sotto, l'acqua che corre
    if y == 0:
        return 3
    if y == 7:
        return 2
    return 13 if y == 3 and (x + 2) % 6 < 3 else 12


def tile_ponte(x, y):
    # il ponticello di legno: le assi di traverso alla via, la luce a sinistra, il giunto scuro
    if x % 3 == 2:
        return 14
    if (x // 3 * 3 + y) % 7 == 0:
        return 15
    return 9 if x % 3 == 0 else 15


def tile_ponte_sponda(x, y):
    # il corrimano del ponticello a monte: un tronco scuro, sotto le assi
    if y <= 1:
        return 1 if y == 0 else 14
    return tile_ponte(x, y)


def tile_ponte_sponda_giu(x, y):
    # il corrimano a valle, coi pioli che scendono nell'acqua
    if y >= 6:
        return 14 if y == 6 else 1
    return tile_ponte(x, y)


def _conci(x, y, scarto=0):
    """Pietra squadrata a corsi di 4 pixel, i giunti sfalsati."""
    if y % 4 == 3 or (x + (y // 4) * 4 + scarto) % 8 == 7:
        return 2
    return 4 if (x + y) % 6 else 3


def tile_diga(x, y):
    # la cresta della diga del Bottaccione: grandi conci
    return _conci(x, y)


def tile_diga_luce(x, y):
    # il fianco della diga verso valle, nella luce
    return 5 if x <= 1 else _conci(x, y)


def tile_diga_ombra(x, y):
    # il fianco verso il lago: la pietra bagnata, scura
    if x >= 6:
        return 1 if x == 7 else 12
    return _conci(x, y)


def tile_contrafforte(x, y):
    # il pilone del contrafforte: conci, la luce a sinistra
    if x == 0:
        return 5
    if x == 7:
        return 1
    return _conci(x, y, 3)


def _arco_gola(x, y, lato):
    """L'arco del contrafforte visto dall'alto: i conci della ghiera di traverso, la luce da sinistra."""
    if lato < 0 and x <= 1:
        return 5 if x == 1 else 2
    if lato > 0 and x >= 6:
        return 3 if x == 6 else 1
    if y % 4 == 0 and (x + (y // 4) * 3) % 6 != 0:
        return 3
    if (x + (y // 4) * 3) % 6 == 0:
        return 3
    return 4 if (x + y) % 7 else 5


def tile_arco_gola(x, y):
    return _arco_gola(x, y, 0)


def tile_arco_gola_s(x, y):
    return _arco_gola(x, y, -1)


def tile_arco_gola_d(x, y):
    return _arco_gola(x, y, 1)


def tile_acquedotto_cornice(x, y):
    # la cornice in cima all'acquedotto, sotto il camminamento: il bordo in luce, i conci sotto
    if y < 2:
        return 5
    if y == 2:
        return 1
    return 2 if y == 7 or (x + (y > 4) * 4) % 8 == 0 else 4


def tile_acquedotto_pilastro(x, y):
    # un pilastro dell'acquedotto: conci, luce a sinistra, ombra a destra
    if x == 0:
        return 2
    if x == 7:
        return 1
    if y % 4 == 3:
        return 2
    return 4 if x < 4 else 3


def tile_acquedotto_base(x, y):
    # il piede del pilastro: si allarga e affonda nell'acqua
    if y >= 6:
        return 1 if (x + y) % 2 else 12
    return tile_acquedotto_pilastro(x, y)


def _lontano(x, y, profondita):
    """Quel che si vede sotto un arco: la rupe in fondo, scura, poi il bosco, in fondo il torrente."""
    if profondita <= 1:
        return 1 if (x + y) % 3 else 14
    if profondita <= 3:
        return 6 if (y + x // 4) % 4 else 1
    if profondita <= 5:
        return 10 if (x * 3 + y * 5) % 7 < 3 else 6
    return 12 if (x + y) % 4 else 1


def _curva_arco(u):
    """L'intradosso dell'arco largo 24 pixel (tre tile): pixel dall'alto della prima riga d'archi."""
    return 1 + 12 - math.sqrt(max(0.0, 144 - (u - 11.5) ** 2))


def _tile_arco_acquedotto(colonna, riga):
    """La tile (colonna 0-2 dentro l'arco, riga 0-1 sotto la cornice) dell'arco dell'acquedotto."""
    def tile(x, y):
        u, v = colonna * 8 + x, riga * 8 + y
        curva = _curva_arco(u)
        if v < curva - 2:
            return 2 if (v % 4 == 3 or (u + v // 4 * 3) % 6 == 0) else 4
        if v < curva:
            return 2 if v < curva - 1 else 1
        return _lontano(x, y, riga)
    return tile


def _tile_lontano(profondita):
    def tile(x, y):
        return _lontano(x, y, profondita)
    return tile


def tile_colonna(x, y):
    # il fusto di una colonna visto dall'alto: tondo chiaro, ombra a destra
    d = (x - 3.5) ** 2 + (y - 3.5) ** 2
    if d > 10:
        return 4
    return 5 if x < 4 else 3


def tile_altare(x, y):
    return 2 if y in (0, 7) else 5


def tile_cero(x, y):
    return 2 if x in (2, 5) else 4


def tile_muro_interno(x, y):
    # la parete di una chiesa vista dall'alto: conci chiari e grossi
    if y % 4 == 3 or (x + (y // 4) * 4) % 8 == 7:
        return 3
    return 4


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
    ("LASTRICO", tile_lastrico),
    ("CORSO", tile_corso),
    ("VIALETTO", tile_vialetto),
    ("ARCO", tile_arco),
    ("LAMPIONE", tile_lampione),
    ("POZZO", tile_pozzo),
    ("SIEPE", tile_siepe),
    ("AIUOLA", tile_aiuola),
    ("PRATO", tile_prato),
    ("ALBERO", tile_albero),
    ("TORRE", tile_torre),
    ("GRADINATA", tile_gradinata),
    ("ARCATA", tile_arcata),
    ("ROVERELLA", tile_roverella),
    ("CIPRESSO", tile_cipresso),
    ("CESPUGLIO", tile_cespuglio),
    ("VASCA", tile_vasca),
    ("AIUOLA_2", tile_aiuola_2),
    ("LASTRICO_2", tile_lastrico_2),
    ("LASTRICO_3", tile_lastrico_3),
    ("BRECCIA", tile_breccia),
    ("CAPPELLETTA", tile_cappelletta),
    ("CHIOSTRO", tile_chiostro),
    ("PANCA", tile_panca),
    ("CANDELIERE", tile_candeliere),
    ("VETRATA", tile_vetrata),
    ("BRECCIA_2", tile_breccia_2),
    ("BRECCIA_SOLCO", tile_breccia_solco),
    ("MURETTO", tile_muretto),
    ("PARACARRO", tile_paracarro),
    ("ROCCIA", tile_roccia),
    ("COLONNA", tile_colonna),
    ("ALTARE", tile_altare),
    ("CERO", tile_cero),
    ("MURO_INTERNO", tile_muro_interno),
    ("RUPE", tile_rupe),
    ("STRISCIA_NERA", tile_striscia_nera),
    ("ACQUA", tile_acqua),
    ("MIASMA", tile_miasma),
    ("RUPE_BIANCA", tile_rupe_bianca),
    ("RUPE_FRATTURA", tile_rupe_frattura),
    ("RUPE_PIEDE", tile_rupe_piede),
    ("EDERA", tile_edera),
    ("STRISCIA_NERA_2", tile_striscia_nera_2),
    ("LAPIDE", tile_lapide),
    ("GHIAIA", tile_ghiaia),
    ("GHIAIA_2", tile_ghiaia_2),
    ("TERRA", tile_terra),
    ("ERBA", tile_erba),
    ("ERBA_2", tile_erba_2),
    ("ACQUA_SASSI", tile_acqua_sassi),
    ("ACQUA_SCHIUMA", tile_acqua_schiuma),
    ("CANALETTA", tile_canaletta),
    ("PONTE", tile_ponte),
    ("PONTE_SPONDA", tile_ponte_sponda),
    ("PONTE_SPONDA_GIU", tile_ponte_sponda_giu),
    ("DIGA", tile_diga),
    ("DIGA_LUCE", tile_diga_luce),
    ("DIGA_OMBRA", tile_diga_ombra),
    ("CONTRAFFORTE", tile_contrafforte),
    ("ARCO_GOLA", tile_arco_gola),
    ("ARCO_GOLA_S", tile_arco_gola_s),
    ("ARCO_GOLA_D", tile_arco_gola_d),
    ("ACQUEDOTTO_CORNICE", tile_acquedotto_cornice),
    ("ACQUEDOTTO_PILASTRO", tile_acquedotto_pilastro),
    ("ACQUEDOTTO_BASE", tile_acquedotto_base),
] + [(f"ACQUEDOTTO_ARCO_{c}{r}", _tile_arco_acquedotto(c, r)) for r in range(2) for c in range(3)] + [
    (f"ACQUEDOTTO_LONTANO_{p}", _tile_lontano(p)) for p in range(2, 8)
]
INDICE_TILE = {nome: i for i, (nome, _) in enumerate(TILE_FONDALI)}


CALPESTABILI_GOLA = ".,+gJ" + VARCHI


def tile_della_gola(griglia, x, y, c):
    """Il tile di una cella nelle stanze della gola, o None per quello di sempre."""
    alt, larg = len(griglia), len(griglia[0])

    def g(xx, yy):
        return griglia[yy][xx] if 0 <= xx < larg and 0 <= yy < alt else "#"

    caso = pseudo(x, y, 21)
    if c == "#":
        if g(x, y + 1) in CALPESTABILI_GOLA:
            return "RUPE_PIEDE"
        vicino_alla_via = any(g(x, y + k) in CALPESTABILI_GOLA for k in (1, 2, 3))
        if caso < (0.22 if vicino_alla_via else 0.05):
            return "EDERA"
        if caso < (0.28 if vicino_alla_via else 0.11):
            return "RUPE_FRATTURA"
        # gli strati: fasce di un tile e mezzo che salgono piano verso monte, rosse e bianche alternate (una
        # bianca ogni tre, qualcuna in piu' a caso fisso); sopra la striscia nera la scaglia e' quasi tutta
        # rossa, sotto le bianche sono due su tre
        striscia = next((yy for yy in range(alt) if g(x, yy) == "x"), None)
        fascia = (2 * y + x // 7) // 3
        if striscia is not None and y < striscia:
            bianca = fascia % 5 == 0
        elif striscia is not None:
            bianca = fascia % 3 != 1
        else:
            bianca = fascia % 3 == 0 or pseudo(fascia, 0, 31) < 0.15
        return "RUPE_BIANCA" if bianca else "RUPE"
    if c == "x":
        return "STRISCIA_NERA_2" if pseudo(x // 3, y, 25) < 0.3 else "STRISCIA_NERA"
    if c == ",":
        sponda = any(g(x + dx, y + dy) == "." for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if (sponda and caso < 0.45) or pseudo(x // 3, y // 2, 22) < 0.12:
            return "TERRA"
        return "GHIAIA_2" if pseudo(x, y, 24) < 0.4 else "GHIAIA"
    if c == ".":
        return "ERBA_2" if caso < 0.3 else "ERBA"
    if c == "~":
        if g(x, y - 1) != "~" and g(x, y + 1) != "~":
            return "CANALETTA"
        if caso < 0.08:
            return "ACQUA_SASSI"
        if pseudo(x // 3, y, 23) < 0.18:
            return "ACQUA_SCHIUMA"
        return "ACQUA"
    if c == "+":
        if g(x, y - 1) != "+":
            return "PONTE_SPONDA"
        return "PONTE_SPONDA_GIU" if g(x, y + 1) != "+" else "PONTE"
    if c == "J":
        if g(x - 1, y) != "J":
            return "ARCO_GOLA_S"
        return "ARCO_GOLA_D" if g(x + 1, y) != "J" else "ARCO_GOLA"
    if c == "X":
        return "CONTRAFFORTE"
    if c == "|":
        if g(x - 1, y) != "|":
            return "DIGA_LUCE"
        return "DIGA_OMBRA" if g(x + 1, y) != "|" else "DIGA"
    if c == "P":
        # gli archi dell'acquedotto, larghi tre tile fra pilastri di uno: la cornice in cima, la ghiera
        # nelle due righe sotto, poi quel che si vede sotto l'arco
        riga = 0
        while g(x, y - riga - 1) == "P":
            riga += 1
        ultima = g(x, y + 1) != "P"
        if riga == 0:
            return "ACQUEDOTTO_CORNICE"
        if x % 4 == 0:
            return "ACQUEDOTTO_BASE" if ultima else "ACQUEDOTTO_PILASTRO"
        if riga <= 2:
            return f"ACQUEDOTTO_ARCO_{x % 4 - 1}{riga - 1}"
        return f"ACQUEDOTTO_LONTANO_{7 if ultima else min(riga, 6)}"
    return None


def del_monte(a):
    """Come si vede il muro dell'area: "gola" la rupe del dungeon, True il bosco del monte, False i tetti."""
    return "gola" if a["id"] in AREE_GOLA else a["id"] in AREE_DEL_MONTE


def tile_per_cella(griglia, x, y, del_monte=False, monte=None):
    """Il tile del fondale per la cella (x, y): l'unica regola che decide come si vede il mondo.
    monte: il lato a monte dell'area; il suolo subito a valle di un gradone e' in ombra."""
    c = griglia[y][x]
    if c in ".," and monte:
        mx, my = {"alto": (x, y - 1), "basso": (x, y + 1)}.get(monte, (x + 1, y))
        if 0 <= my < len(griglia) and mx < len(griglia[0]) and griglia[my][mx] == "M":
            return INDICE_TILE["SUOLO_OMBRA" if c == "." else "STRADA_OMBRA"]
    if c in VARCHI:
        return INDICE_TILE["INGRESSO" if c == "I" else "VARCO"]
    nome = CELLE[c][0]
    if nome == "CITTA_BASSA":
        vicine = [griglia[y + dy][x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                  if 0 <= y + dy < len(griglia) and 0 <= x + dx < len(griglia[0])]
        return INDICE_TILE["VUOTO_OMBRA" if "=" in vicine else "CITTA_BASSA"]
    if del_monte == "gola":
        gola = tile_della_gola(griglia, x, y, c)
        if gola:
            return INDICE_TILE[gola]
    if nome == "MURO":
        if del_monte:
            return INDICE_TILE["BOSCO"]
        sotto = griglia[y + 1][x] if y + 1 < len(griglia) else "#"
        # il muro che ha davanti (in basso sullo schermo) uno spazio calpestabile si vede di
        # fronte: e' il muro di sostegno o il fronte cieco; il resto e' tetto visto dall'alto
        if not solida(sotto):
            return INDICE_TILE["MURO_FRONTE"]
        return INDICE_TILE[tetto_della_casa(x, y)]
    if nome == "ALBERO":
        # un albero piccolo (quel che avanza delle chiome 2x2): leccio o roverella, a caso fisso
        return INDICE_TILE["ROVERELLA" if pseudo(x, y, 5) < 0.4 else "ALBERO"]
    if nome == "LASTRICO":
        # lastre di tre toni, a gruppi di 2x2 tile
        return INDICE_TILE[("LASTRICO", "LASTRICO_2", "LASTRICO_3")[int(pseudo(x // 2, y // 2, 6) * 3)]]
    if nome == "BRECCIA":
        # la ghiaia a due toni, e i solchi delle ruote lungo i tratti
        su = y > 0 and griglia[y - 1][x] == "b"
        giu = y + 1 < len(griglia) and griglia[y + 1][x] == "b"
        if su and giu and pseudo(x, y // 5, 9) < 0.25:
            return INDICE_TILE["BRECCIA_SOLCO"]
        return INDICE_TILE["BRECCIA_2" if pseudo(x // 2, y // 2, 10) < 0.4 else "BRECCIA"]
    if nome == "AIUOLA" and pseudo(x // 3, y // 3, 8) < 0.5:
        return INDICE_TILE["AIUOLA_2"]
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


# Lo sprite del giocatore: Ubaldo 16x32 in quattro direzioni (tools/sagome_mappa.py, giro 5 del loop grafico).
import sagome_mappa as SM  # noqa: E402

PALETTE_GIOCATORE = SM.PALETTE


# --- Lettura e controlli ----------------------------------------------------------------------

class ErroreMondo(Exception):
    pass


def solida(c):
    return c not in VARCHI and CELLE[c][1]


def controlla_ordine_celle(celle=None):
    """Le celle calpestabili tutte prima della prima solida: cosi' il gioco, che confronta l'indice con
    PRIMA_CELLA_SOLIDA, vede solida la stessa cella che la .area dice solida (il MIASMA, a indice 42,
    bloccava la via)."""
    celle = CELLE if celle is None else celle
    valori = list(celle.values())
    prima = next(i for i, (_, s) in enumerate(valori) if s)
    dopo = [nome for nome, s in valori[prima:] if not s]
    if dopo:
        raise ErroreMondo(f"celle calpestabili dopo {valori[prima][0]} (il gioco le vedrebbe solide): {', '.join(dopo)}")


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
                if not 0 <= int(t[1]) < SPAWN_PER_AREA:
                    raise ErroreMondo(f"{nome_file}:{n}: spawn {t[1]} oltre SPAWN_PER_AREA ({SPAWN_PER_AREA})")
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
                if t[1] not in LATI_A_MONTE + LATI_DEGLI_INTERNI:
                    raise ErroreMondo(f"{nome_file}:{n}: lato a monte '{t[1]}' sconosciuto")
                a["monte"] = t[1]
                a["riga_monte"] = n
            elif t[0] == "belvedere":
                a["belvedere"].append((t[1], n))
            elif t[0] == "giardini":
                a["giardini"] = True
            elif t[0] == "prato":
                a["prato"] = True
            elif t[0] == "alberi":
                a["alberi"] = float(t[1])
                if len(t) > 2:
                    a["alberi_margine"] = int(t[2])
            elif t[0] == "sagrato":
                a["sagrato"] = int(t[1])
            elif t[0] == "a_mano":
                a["a_mano"] = True
            elif t[0] == "stradoni":
                a["stradoni"] = True
            elif t[0] == "interno":
                a["interno"] = True
            elif t[0] == "ingresso":
                a.setdefault("ingressi", {})[t[1]] = t[2]
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
    if a["monte"] not in LATI_A_MONTE and not a.get("interno"):
        raise ErroreMondo(f"{nome_file}:{a['riga_monte']}: lato a monte '{a['monte']}': la salita va verso "
                          f"nord-est, il lato a monte e' alto o destra")
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
        # nord in alto: x = est, y = -nord (il centro in basso a destra se il lato e' pari)
        x0 = rx + int(round(est * a["fattore"])) + dx - w // 2
        y0 = ry - int(round(nord * a["fattore"])) + dy - (h - 1) // 2
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
    for mid in FORME:
        if mid in posati:
            stampa_teatro(a, posati[mid])
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
    return rx - w // 2, ry - (h - 1) // 2, w, h


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


# Monumenti che non sono un blocco rettangolare: il generatore ne stampa la forma nella griglia.
FORME = {"teatro_romano": "cavea a semicerchio, anello di arcate, orchestra e scena"}


def geometria_teatro(x0, y0, w, h):
    """Centro e raggi del Teatro nel suo rettangolo: il diametro sul lato lungo. Col nord in alto (4 nov
    2026) il lato lungo e' orizzontale: la scena sul bordo basso, la cavea che sale verso l'alto, come la
    si vede arrivando; su un rettangolo alto la scena a sinistra e la cavea che si apre a destra.
    Ritorna (cx, cy, r, r_int, orizzontale)."""
    if w > h:
        cx, cy = x0 + w / 2 - 0.5, y0 + h - 3
        r = min(h - 3, w / 2 - 1)
        return cx, cy, r, r / 3, True
    cx, cy = x0 + 2, y0 + h / 2 - 0.5
    r = min(w - 3, h / 2 - 1)
    return cx, cy, r, r / 3, False


def stampa_teatro(a, rett):
    """La forma del Teatro Romano nella griglia: scena (P), orchestra (lastrico), gradinate (R) e anello
    di arcate (U) in un semicerchio; il resto del rettangolo resta prato calpestabile."""
    x0, y0, w, h = rett
    cx, cy, r, r_int, orizz = geometria_teatro(x0, y0, w, h)
    g = [list(riga) for riga in a["griglia"]]
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            # lungo: la coordinata lungo il diametro; fuori: oltre il diametro, dalla parte della scena
            lungo, fuori = (x - cx, y > cy) if orizz else (y - cy, x < cx)
            if fuori:
                g[y][x] = "P" if abs(lungo) <= r else "."
            elif d <= r_int:
                g[y][x] = "L"
            elif d <= r - 1.5:
                g[y][x] = "R"
            elif d <= r:
                g[y][x] = "U"
            else:
                g[y][x] = "."
    a["griglia"] = ["".join(riga) for riga in g]


def errori_semicerchio(a, rett):
    """La cavea e' un semicerchio: su ogni linea parallela alla scena... cioe' su ogni riga (scena a
    sinistra) o colonna (scena in basso), la gradinata arriva fino al raggio (con un tile di tolleranza)."""
    x0, y0, w, h = rett
    cx, cy, r, _, orizz = geometria_teatro(x0, y0, w, h)
    err = []
    linee = range(x0, x0 + w) if orizz else range(y0, y0 + h)
    for k in linee:
        if orizz:
            cavea = [y for y in range(y0, y0 + h) if a["griglia"][y][k] in "RU"]
            scarto, trovato = k - cx, (cy - min(cavea)) if cavea else 0
        else:
            cavea = [x for x in range(x0, x0 + w) if a["griglia"][k][x] in "RU"]
            scarto, trovato = k - cy, (max(cavea) - cx) if cavea else 0
        if abs(scarto) > r:
            if cavea:
                err.append((k, "cavea fuori dal semicerchio"))
            continue
        atteso = (r * r - scarto ** 2) ** 0.5
        if abs(trovato - atteso) > 1.5:
            err.append((k, round(trovato, 1), round(atteso, 1)))
    return err


def pseudo(x, y, seme=0):
    """Un numero fisso in [0, 1) per la cella (x, y): il caso con il seme, sempre uguale."""
    h = (x * 374761393 + y * 668265263 + seme * 2246822519) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65536.0


def rumore(x, y, seme=0, passo=9):
    """Rumore a valori, liscio su 'passo' tile: le macchie fitte e le radure."""
    gx, gy = x / passo, y / passo
    x0, y0 = int(gx), int(gy)
    fx, fy = gx - x0, gy - y0
    a, b = pseudo(x0, y0, seme), pseudo(x0 + 1, y0, seme)
    c, d = pseudo(x0, y0 + 1, seme), pseudo(x0 + 1, y0 + 1, seme)
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def semina(posti, densita, raggio, seme):
    """Alberi mai in griglia: fra i posti buoni, in un ordine a caso fisso, si pianta dove il rumore
    lo vuole (macchie e radure) e nessun altro albero sta entro 'raggio' tile."""
    piantati = set()
    for x, y in sorted(posti, key=lambda c: pseudo(c[0], c[1], seme)):
        if pseudo(x, y, seme + 1) > densita * 3 * rumore(x, y, seme + 2) ** 2:
            continue
        if any((x + i, y + j) in piantati for i in range(-raggio, raggio + 1) for j in range(-raggio, raggio + 1)):
            continue
        piantati.add((x, y))
    return piantati


def piantagione(g, posti, densita, raggio, seme, cespugli=0.3, cipressi=0.2):
    """Pianta nei posti scelti da semina(): chiome di 2x2 tile (T: lecci e roverelle), cipressi di
    1x2 (u) e cespugli bassi (r). Un albero grande ha bisogno di tutti i suoi posti liberi."""
    posti = set(posti)
    for x, y in semina(posti, densita, max(raggio, 2), seme):
        tipo = pseudo(x, y, seme + 3)
        if tipo < cespugli:
            g[y][x] = "r"
        elif tipo < cespugli + cipressi and (x, y + 1) in posti:
            g[y][x] = g[y + 1][x] = "u"
        elif {(x + 1, y), (x, y + 1), (x + 1, y + 1)} <= posti:
            for i in range(2):
                for j in range(2):
                    g[y + j][x + i] = "T"
        else:
            g[y][x] = "r"


def alberi_dell_area(griglia):
    """Gli alberi della griglia: [(x, y, larghezza, altezza, cella)]. Le chiome T si leggono a blocchi
    di 2x2 (da sinistra a destra, dall'alto), quel che avanza e' un albero piccolo da un tile; i
    cipressi u a coppie verticali; i cespugli r da soli."""
    out, presi = [], set()
    h, w = len(griglia), len(griglia[0])
    for y in range(h):
        for x in range(w):
            c = griglia[y][x]
            if (x, y) in presi or c not in "Tur":
                continue
            if c == "T" and x + 1 < w and y + 1 < h and all(
                    griglia[y + j][x + i] == "T" and (x + i, y + j) not in presi for i in range(2) for j in range(2)):
                celle = [(x + i, y + j) for i in range(2) for j in range(2)]
                out.append((x, y, 2, 2, "T"))
            elif c == "u" and y + 1 < h and griglia[y + 1][x] == "u" and (x, y + 1) not in presi:
                celle = [(x, y), (x, y + 1)]
                out.append((x, y, 1, 2, "u"))
            else:
                celle = [(x, y)]
                out.append((x, y, 1, 1, c))
            presi.update(celle)
    return out


def decora_piazza(a):
    """Il lastricato di una piazza: lastre e corsi di pietra ogni 5 tile, i lampioni agli angoli, un
    pozzo; nei giardini ("giardini" nella .area) aiuole, siepi, alberi e vialetti al centro."""
    g = [list(riga) for riga in a["griglia"]]
    if a.get("sagrato"):
        # il sagrato lastricato intorno agli edifici, largo quanto dice la riga "sagrato"
        d = a["sagrato"]
        for x0, y0, ew, eh in a.get("edifici", {}).values():
            for y in range(max(0, y0 - d), min(a["altezza"], y0 + eh + d)):
                for x in range(max(0, x0 - d), min(a["larghezza"], x0 + ew + d)):
                    if g[y][x] == ".":
                        g[y][x] = "L"
    if a.get("prato"):
        # il prato e qualche albero sparso, lontano da varchi, spawn e costruzioni
        g = [["N" if c == "." else c for c in riga] for riga in g]
        fermi = set(a["spawn"].values())
        posti = [(x, y) for y in range(2, a["altezza"] - 2) for x in range(2, a["larghezza"] - 2)
                 if all(g[y + j][x + i] == "N" for i in range(-2, 3) for j in range(-2, 3))
                 and all(max(abs(x - sx), abs(y - sy)) > 3 for sx, sy in fermi)
                 and (not a.get("alberi_margine") or min(x, y, a["larghezza"] - 1 - x, a["altezza"] - 1 - y)
                      < a["alberi_margine"])]
        piantagione(g, posti, a.get("alberi", 0.5), 1, sum(map(ord, a["id"])))
        a["griglia"] = ["".join(riga) for riga in g]
    piazza = rettangolo_piazza(a)
    if not piazza:
        return
    x0, y0, pw, ph = piazza
    g = [list(riga) for riga in a["griglia"]]
    spawn = set(a["spawn"].values())

    def libera(x, y):
        return 0 <= x < a["larghezza"] and 0 <= y < a["altezza"] and g[y][x] == "."

    def corsi(inizio, lunghezza, seme):
        # i corsi di pietra a passo irregolare (7-11 tile), non a scacchiera
        out, k = set(), inizio + 3
        while k < inizio + lunghezza - 2:
            out.add(k)
            k += 7 + int(pseudo(k, seme, 11) * 5)
        return out

    corsi_x, corsi_y = corsi(x0, pw, 1), corsi(y0, ph, 2)
    for y in range(y0, y0 + ph):
        for x in range(x0, x0 + pw):
            if libera(x, y):
                g[y][x] = "K" if x in corsi_x or y in corsi_y else "L"
    if a.get("giardini"):
        gx0, gy0, gx1, gy1 = x0 + 4, y0 + 4, x0 + pw - 4, y0 + ph - 4
        mx, my = (gx0 + gx1) // 2, (gy0 + gy1) // 2
        for y in range(gy0, gy1):
            for x in range(gx0, gx1):
                if g[y][x] not in "LK":
                    continue
                vialetto = abs(x - mx) <= 1 or abs(y - my) <= 1 or x in (gx0, gx1 - 1) or y in (gy0, gy1 - 1)
                if vialetto or (x, y) in spawn:
                    g[y][x] = "Z"
                    continue
                # l'aiuola fra i vialetti: siepe sul bordo, fiori dentro (gli alberi dopo, a caso)
                bordo = any(abs(x + dx - mx) <= 1 or abs(y + dy - my) <= 1 or x + dx in (gx0, gx1 - 1)
                            or y + dy in (gy0, gy1 - 1) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                g[y][x] = "Y" if bordo else "D"
        # gli alberi nelle aiuole, mai in fila, e la vasca all'incrocio dei vialetti con il giro intorno
        aiuole = [(x, y) for y in range(gy0, gy1) for x in range(gx0, gx1) if g[y][x] == "D"]
        piantagione(g, aiuole, 0.2, 1, 7, cespugli=0.2)
        for y in range(my - 4, my + 5):
            for x in range(mx - 4, mx + 5):
                d = max(abs(x - mx), abs(y - my))
                g[y][x] = "v" if d <= 2 else ("Z" if d <= 4 and g[y][x] in "YDTr" else g[y][x])
    else:
        for x, y in ((x0 + 1, y0 + 1), (x0 + pw - 2, y0 + 1), (x0 + 1, y0 + ph - 2), (x0 + pw - 2, y0 + ph - 2)):
            if g[y][x] in "LK" and all(max(abs(x - sx), abs(y - sy)) > 1 for sx, sy in spawn):
                g[y][x] = "Q"
        for dx, dy in ((pw // 4, ph // 3), (pw // 4, 2 * ph // 3), (3 * pw // 4, ph // 3)):
            px, py = x0 + dx, y0 + dy
            celle = [(px + i, py + j) for i in range(2) for j in range(2)]
            intorno = [(x + i, y + j) for x, y in celle for i in (-1, 0, 1) for j in (-1, 0, 1)]
            if all(0 <= x < a["larghezza"] and 0 <= y < a["altezza"] and g[y][x] in "LK" for x, y in intorno) and \
                    all(max(abs(x - sx), abs(y - sy)) > 2 for x, y in celle for sx, sy in spawn):
                for x, y in celle:
                    g[y][x] = "O"
                break
    a["griglia"] = ["".join(riga) for riga in g]


def porte_dell_area(a, grafo):
    """[(lettera del varco, nome della porta)] per i varchi dell'area che passano da una porta."""
    out = []
    for e in grafo["archi"]:
        if not e.get("porta"):
            continue
        for qui, la in ((e["da"], e["a"]), (e["a"], e["da"])):
            if qui.lower() == a["id"]:
                for lettera, dest, _, _ in a["uscite"]:
                    if dest == la.lower():
                        out.append((lettera, e["porta"]))
    return sorted(out)


def errori_cinta(grafo):
    """Ogni arco fra un'area dentro le mura e una fuori passa da una porta."""
    fuori = {x["id"] for x in grafo["aree"] if x.get("fuori_le_mura")}
    return [f"{e['da']}-{e['a']}: esce dalle mura senza porta" for e in grafo["archi"]
            if (e["da"] in fuori) != (e["a"] in fuori) and not e.get("porta")]


PROFONDITA_TORRE = 5   # tile: la torre e' profonda, il passaggio sotto l'arco e' lungo 3 tile
LATO_PILONE = 3        # tile di muro per lato: con un varco di 4 la torre e' larga 10


def geometria_porta(a, lettera):
    """La torre della porta intorno al varco: (lato, celle dei piloni, celle sotto l'arco)."""
    celle = celle_varco(a, lettera)
    lato = sorted(lati_del_varco(a, lettera))[0]
    lungo = [x for x, _ in celle] if lato in ("alto", "basso") else [y for _, y in celle]
    p0, p1 = min(lungo), max(lungo)

    def cella(u, prof):
        return {"alto": (u, prof), "basso": (u, a["altezza"] - 1 - prof),
                "sinistra": (prof, u), "destra": (a["larghezza"] - 1 - prof, u)}[lato]
    piloni = [cella(u, prof) for prof in range(PROFONDITA_TORRE)
              for u in list(range(p0 - LATO_PILONE, p0)) + list(range(p1 + 1, p1 + 1 + LATO_PILONE))]
    arco = [cella(u, prof) for prof in range(2, PROFONDITA_TORRE) for u in range(p0, p1 + 1)]
    return lato, piloni, arco


def costruisci_porte(a, grafo):
    """Le porte della citta': la torre di pietra a cavallo del varco, i piloni ai lati e l'arco
    calpestabile davanti al varco. Rifiuta una porta che non ha posto."""
    g = [list(riga) for riga in a["griglia"]]
    edifici = {(x, y) for (x0, y0, ew, eh) in a.get("edifici", {}).values()
               for x in range(x0, x0 + ew) for y in range(y0, y0 + eh)}
    a["porte"] = {}
    for lettera, nome in porte_dell_area(a, grafo):
        if not celle_varco(a, lettera):
            continue  # il varco che manca lo segnala controlla()
        lato, piloni, arco = geometria_porta(a, lettera)
        for x, y in piloni + arco:
            if not (0 <= x < a["larghezza"] and 0 <= y < a["altezza"]) or (x, y) in edifici or g[y][x] in VARCHI:
                raise ErroreMondo(f"{a['file']}: non c'e' posto per {nome} intorno al varco '{lettera}' in ({x}, {y})")
        for x, y in piloni:
            g[y][x] = "X"
        for x, y in arco:
            # l'arco copre la strada (fora la cinta, toglie un albero): un passaggio murato resta murato (e il varco non si raggiunge)
            if not solida(g[y][x]) or g[y][x] in "WTru":
                g[y][x] = "J"
        a["porte"][lettera] = (nome, lato, piloni, arco)
    a["griglia"] = ["".join(riga) for riga in g]


def errori_porte(a, grafo):
    """Ogni varco con una porta passa sotto il suo arco: davanti al varco c'e' l'arco, ai lati i piloni."""
    err = []
    for lettera, nome in porte_dell_area(a, grafo):
        if lettera not in a.get("porte", {}):
            err.append(f"{nome}: manca la torre al varco '{lettera}'")
            continue
        _, piloni, arco = geometria_porta(a, lettera)
        if any(a["griglia"][y][x] != "J" for x, y in arco):
            err.append(f"{nome}: il varco '{lettera}' non passa sotto l'arco")
        if any(a["griglia"][y][x] != "X" for x, y in piloni):
            err.append(f"{nome}: la torre del varco '{lettera}' e' incompleta")
    return err


def finestra_dello_spawn(a):
    """Le celle che lo schermo (30x20 tile) mostra dallo spawn 0: la camera segue e si ferma ai bordi."""
    sx, sy = a["spawn"][0]
    w, h = a["larghezza"], a["altezza"]
    x0 = 0 if w <= 30 else min(max(sx - 15, 0), w - 30)
    y0 = 0 if h <= 20 else min(max(sy - 10, 0), h - 20)
    return [(x, y) for y in range(y0, min(h, y0 + 20)) for x in range(x0, min(w, x0 + 30))]


def composizione(a):
    """(elementi riconoscibili, quota di pavimento nudo) nella schermata dello spawn: monumenti,
    parapetto, porte, mura, giardini, pozzi e fontane; nudo e' il suolo semplice o il prato, senza disegno."""
    celle = finestra_dello_spawn(a)
    # conta solo quel che si legge: non le prime 3 righe (il cartiglio del nome) ne' l'ultima colonna
    # per lato, e un monumento vale se se ne vedono almeno 6 celle
    xs, ys = sorted({x for x, _ in celle}), sorted({y for _, y in celle})
    leggibili = [(x, y) for x, y in celle if y >= ys[0] + 3 and xs[0] < x < xs[-1]]
    visti = set()
    for mid, (x0, y0, ew, eh) in a.get("edifici", {}).items():
        if sum(1 for x, y in leggibili if x0 <= x < x0 + ew and y0 <= y < y0 + eh) >= 6:
            visti.add(mid)
    segni = {"u": "alberi", "h": "chiostro", "q": "panche", "l": "candelieri", "w": "vetrate", "m": "muretti", "p": "muretti", "v": "vasca", "r": "alberi", "c": "cappelletta", "a": "altare", "e": "ceri", "n": "colonne", "=": "parapetto", "X": "porta", "Y": "giardini", "T": "alberi", "D": "giardini", "O": "pozzo",
             "F": "fontana", "Q": "lampioni", "R": "teatro_romano", "U": "teatro_romano", "W": "mura"}
    for x, y in leggibili:
        c = a["griglia"][y][x]
        if c in segni:
            visti.add(segni[c])
    nudo = sum(1 for x, y in celle if a["griglia"][y][x] in ".N")
    return visti, nudo / len(celle)


def blocchi(griglia, lettera):
    """Le macchie (4-connesse) di celle 'lettera' della griglia, come insiemi di celle."""
    viste, out = set(), []
    for y, r in enumerate(griglia):
        for x, c in enumerate(r):
            if c != lettera or (x, y) in viste:
                continue
            blocco, coda = set(), deque([(x, y)])
            viste.add((x, y))
            while coda:
                cx, cy = coda.popleft()
                blocco.add((cx, cy))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= ny < len(griglia) and 0 <= nx < len(griglia[0]) and griglia[ny][nx] == lettera \
                            and (nx, ny) not in viste:
                        viste.add((nx, ny))
                        coda.append((nx, ny))
            out.append(blocco)
    return out


def coricata(a):
    """Gli stradoni col nord in alto salgono verso l'alto a tratti orizzontali: per contarli la griglia si
    gira di 90 gradi in senso orario, come la disegna tools/disegna_stradoni.py (tratti in colonna,
    salita verso destra)."""
    g, w, h = a["griglia"], a["larghezza"], a["altezza"]
    if h <= w:
        return a
    return dict(a, griglia=["".join(g[h - 1 - x][y] for x in range(h)) for y in range(w)], larghezza=h, altezza=w)


def tratti_degli_stradoni(a):
    """Letti dalla griglia (coricata): i tratti (colonne di ghiaia lunghe almeno LUNGHEZZA_MIN_TRATTO,
    unite fra colonne vicine) dal primo all'ultimo, ognuno come (x0, x1, y0, y1)."""
    a = coricata(a)
    g, w, h = a["griglia"], a["larghezza"], a["altezza"]
    via = "bJ"
    colonne = []
    for x in range(w):
        y = 0
        while y < h:
            if g[y][x] in via:
                y0 = y
                while y < h and g[y][x] in via:
                    y += 1
                if y - y0 >= LUNGHEZZA_MIN_TRATTO:
                    colonne.append((x, y0, y - 1))
            else:
                y += 1
    tratti = []
    for x, y0, y1 in colonne:
        if tratti and tratti[-1][1] == x - 1 and tratti[-1][2] <= y1 and y0 <= tratti[-1][3]:
            t = tratti[-1]
            tratti[-1] = (t[0], x, min(t[2], y0), max(t[3], y1))
        else:
            tratti.append((x, x, y0, y1))
    return tratti


def tornanti_degli_stradoni(a, tratti):
    """Il tornante n (dal basso, da 1) e' la ghiaia orizzontale fra il tratto n e il successivo:
    le celle di ghiaia fra le due colonne, all'estremo comune (sulla griglia coricata)."""
    g = coricata(a)["griglia"]
    out = []
    for (ax0, ax1, ay0, ay1), (bx0, bx1, by0, by1) in zip(tratti, tratti[1:]):
        celle = {(x, y) for y in range(max(ay0, by0), min(ay1, by1) + 1) for x in range(ax1 + 1, bx0)
                 if g[y][x] == "b"}
        out.append(celle)
    return out


def errori_stradoni(a, dati):
    """Gli stradoni della griglia contro mondo/stradoni.json: quanti tratti e quanto lunghi, ogni
    tornante che c'e', ogni cappelletta nel gomito del suo tornante."""
    err = []
    tratti = tratti_degli_stradoni(a)
    lunghezze = [t[3] - t[2] + 1 for t in tratti]
    if lunghezze != dati["tratti"]:
        err.append(f"tratti {lunghezze}, i dati ne vogliono {dati['tratti']}")
        return err
    tornanti = tornanti_degli_stradoni(a, tratti)
    for n, celle in enumerate(tornanti, 1):
        if not celle:
            err.append(f"manca il tornante {n}")
    capp = blocchi(coricata(a)["griglia"], "c")
    if len(capp) != len(dati["cappellette"]):
        err.append(f"{len(capp)} cappellette, i dati ne vogliono {len(dati['cappellette'])}")
    trovate = []
    for blocco in capp:
        accanto = {(x + dx, y + dy) for x, y in blocco for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))}
        trovate.append(sorted(n for n, celle in enumerate(tornanti, 1) if accanto & celle))
    for c in dati["cappellette"]:
        if [c["tornante"]] not in trovate:
            err.append(f"{c['nome']}: non e' al tornante {c['tornante']} (cappellette ai tornanti {trovate})")
    return err


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
    if a.get("stradoni") or a.get("interno"):
        return 0  # il dislivello lo fanno i tornanti; dentro una chiesa non ce n'e'
    q0, q1 = quote_dell_area(a, grafo)
    return min(GRADONI_MAX, int((q1 - q0) // METRI_PER_GRADONE))


def applica_dislivello(a, grafo):
    """Belvederi, gradoni e scale ai varchi, sulla griglia con gli edifici gia' posati."""
    g = [list(r) for r in a["griglia"]]
    w, h = a["larghezza"], a["altezza"]
    q0, q1 = quote_dell_area(a, grafo)
    edifici = {(x, y) for (x0, y0, ew, eh) in a.get("edifici", {}).values()
               for x in range(x0, x0 + ew) for y in range(y0, y0 + eh)}

    # mura della citta': il bordo dell'area su quel lato, fuori da varchi ed edifici; nel prato fuori
    # le mura si vede tutto lo spessore della cinta, profonda quanto la torre di una porta
    spessore = 3 if a.get("prato") else 1
    for lato in a.get("mura", []):
        celle = {"alto": [(x, p) for x in range(w) for p in range(spessore)],
                 "basso": [(x, h - 1 - p) for x in range(w) for p in range(spessore)],
                 "sinistra": [(p, y) for y in range(h) for p in range(spessore)],
                 "destra": [(w - 1 - p, y) for y in range(h) for p in range(spessore)]}[lato]
        for x, y in celle:
            if g[y][x] in "#N" and (x, y) not in edifici:
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

    # gradoni: righe (monte alto) o colonne (monte destra) di muro, con una scala in ogni tratto
    n = numero_gradoni(a, grafo)
    lungo = h if a["monte"] == "alto" else w
    vietate = set(a["spawn"].values()) | {(x, y) for y, r in enumerate(g) for x, c in enumerate(r)
                                          if c in VARCHI or c == "S"}
    a["gradoni"] = []
    for k in range(n):
        voluto = lungo * (k + 1) // (n + 1)
        for scarto in sorted(range(-lungo // 4, lungo // 4 + 1), key=abs):
            pos = voluto + scarto
            if not 2 <= pos < lungo - 2:
                continue
            linea = [(x, pos) for x in range(w)] if a["monte"] == "alto" else [(pos, y) for y in range(h)]
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
    for lettera, (nome, lato, piloni, arco) in a.get("porte", {}).items():
        celle = piloni + arco
        x0, y0 = min(x for x, _ in celle), min(y for _, y in celle)
        pw, ph = max(x for x, _ in celle) - x0 + 1, max(y for _, y in celle) - y0 + 1
        tela = PM.porta_della_citta(pw, ph, lato)
        elementi["porta:" + nome] = tela.elementi
        for ty, riga in enumerate(tela.tagli()):
            for tx, pix in enumerate(riga):
                if (x0 + tx, y0 + ty) in celle:
                    tile_di[(x0 + tx, y0 + ty)] = pix
    pozzo = [(x, y) for y in range(h) for x in range(w) if a["griglia"][y][x] == "O"]
    if pozzo:
        px0, py0 = min(x for x, _ in pozzo), min(y for _, y in pozzo)
        tela = PM.pozzo(2, 2)
        for ty, riga in enumerate(tela.tagli()):
            for tx, pix in enumerate(riga):
                if (px0 + tx, py0 + ty) in pozzo:
                    tile_di[(px0 + tx, py0 + ty)] = pix
    for lettera, pittore in (("c", PM.cappelletta), ("a", PM.altare), ("e", PM.cero), ("n", PM.pilastro),
                             ("h", PM.chiostro)):
        for blocco in blocchi(a["griglia"], lettera):
            bx0, by0 = min(x for x, _ in blocco), min(y for _, y in blocco)
            bw, bh = max(x for x, _ in blocco) - bx0 + 1, max(y for _, y in blocco) - by0 + 1
            tela = pittore(bw, bh)
            elementi.setdefault(lettera, {})
            for k, v in tela.elementi.items():
                elementi[lettera][k] = elementi[lettera].get(k, 0) + v
            for ty, riga in enumerate(tela.tagli()):
                for tx, pix in enumerate(riga):
                    if (bx0 + tx, by0 + ty) in blocco:
                        tile_di[(bx0 + tx, by0 + ty)] = pix
    # gli alberi grandi: le chiome 2x2 (leccio o roverella) e i cipressi 1x2, con l'ombra
    fondo = PM.VERDE_SCURO if a["id"] in AREE_DEL_MONTE else PM.VERDE
    for x0, y0, aw, ah, c in alberi_dell_area(a["griglia"]):
        if (aw, ah) == (1, 1):
            continue
        tela = PM.chioma("roverella" if pseudo(x0, y0, 5) < 0.4 else "leccio", fondo) if c == "T" else PM.cipresso(fondo)
        for ty, riga in enumerate(tela.tagli()):
            for tx, pix in enumerate(riga):
                tile_di[(x0 + tx, y0 + ty)] = pix
    celle = {}
    for y in range(h):
        for x in range(w):
            pix = tile_di.get((x, y))
            if pix is None:
                indice = tile_per_cella(a["griglia"], x, y, del_monte(a), a.get("monte"))
                if a.get("interno") and TILE_FONDALI[indice][0] not in ("MURO_FRONTE",) and a["griglia"][y][x] == "#":
                    indice = INDICE_TILE["MURO_INTERNO"]
                pix = _tile(TILE_FONDALI[indice][1])
            celle[(x, y)] = pix
    # lo standard grafico (pezzo EDI, tools/pittore_citta.py): case, suolo, vita, ombre e contorni, in pixel
    quadro = ridipingi(a, celle, tile_di, mondo, elementi)
    tile_unici = {(0, tuple(map(tuple, _tile(tile_vuoto)))): 0}
    indici, giri = [], []
    for y in range(h):
        for x in range(w):
            if quadro is None:
                banco, pix = 0, celle[(x, y)]
            else:
                banco, pix = indicizza_tile(quadro, x, y, a)
            t = tuple(map(tuple, pix))
            # un tile uguale a uno gia' preso, specchiato, si riusa con i bit di specchio della cella (10 e 11):
            # la cavea del Teatro e' simmetrica, molti bordi pure
            for giro, chiave in ((0, t), (2, t[::-1]), (1, tuple(r[::-1] for r in t)), (3, tuple(r[::-1] for r in t[::-1]))):
                if (banco, chiave) in tile_unici:
                    indici.append(tile_unici[(banco, chiave)])
                    giri.append(giro)
                    break
            else:
                indici.append(tile_unici.setdefault((banco, t), len(tile_unici)))
                giri.append(0)
    a["banchi"] = [b for b, _ in tile_unici]
    a["specchi"] = giri
    return [t for _, t in tile_unici], indici, elementi


# --- Lo standard grafico sui fondali (pezzo EDI) -----------------------------------------------------
# La palette dei fondali ha 5 banchi da 16 colori: il banco 0 e' PALETTE_FONDALI (la gola e il monte ci
# restano interi), gli altri tre li definisce tools/pittore_citta.py. Ogni tile usa un banco solo.
BANCHI_FONDALI = [PALETTE_FONDALI] + PC.BANCHI_NUOVI + [PI.BANCO_INTERNI]   # il settimo: gli interni (pezzo INT1)

# Le celle e come proiettano l'ombra (L4): (tipo del pixel, altezza in pixel).
TIPO_CELLA = {
    "T": ("verde", 20), "u": ("verde", 24), "r": ("verde", 6), "Y": ("basso", 6), "D": ("basso", 3),
    "v": ("basso", 4), "m": ("basso", 6), "p": ("basso", 5), "Q": ("basso", 12), "O": ("basso", 8),
    "=": ("basso", 4), "M": ("basso", 8), "F": ("basso", 6), "q": ("basso", 3), "W": ("edificio", 24),
    "X": ("edificio", 32), "R": ("edificio", 8), "U": ("edificio", 16), "C": ("edificio", 24),
    "P": ("edificio", 24), "d": ("edificio", 24), "c": ("edificio", 12), "k": ("basso", 6), "h": ("edificio", 12),
}
SUOLI_RIDIPINTI = {".": "suolo", ",": "strada", "L": "lastrico", "K": "corso"}


def area_di_citta(a):
    """Le aree che il pittore della citta' ridipinge tutte: non la gola (palette cupa), non gli interni (sono del
    pezzo degli edifici esplorabili), non il monte (bosco e ghiaia restano quelli di sempre, con le ombre)."""
    return not a.get("interno") and a["id"] not in AREE_GOLA and a["id"] not in AREE_DEL_MONTE


def ridipingi_monte(q, g, w, h):
    """Il Monte allo standard: la ghiaia degli stradoni coi solchi e l'erba ai bordi, i muretti a secco in 3/4, i
    paracarri e i massi (M6). Il bosco e gli alberi restano quelli di sempre, con le ombre portate."""
    for y in range(h):
        for x in range(w):
            c = g[y][x]
            if c in "b,":
                # la ghiaia degli stradoni e la strada bianca del Bottaccione
                PC.dipingi_breccia(q, x, y, g)
            elif c in "mM":
                PC.dipingi_muretto(q, x, y, g)
            elif c == "S":
                PC.dipingi_scala(q, x, y, g)
    for y in range(h):
        for x in range(w):
            c = g[y][x]
            if c == "p":
                # il paracarro sta nell'erba del ciglio, non sulla ghiaia: la strada resta della sua larghezza
                PC.dipingi_paracarro(q, x, y, lambda X, Y: (PC.V, 1) if (X * 3 + Y * 5) % 7 == 0 else (PC.V, 2))
            elif c == "k":
                PC.dipingi_roccia(q, x, y, (x * 7 + y * 3) % 3)


def ridipingi(a, celle, tile_di, mondo, elementi):
    """Il fondale dell'area in pixel, ridipinto allo standard. Le stanze della gola e gli interni si convertono
    soltanto (la gola ha la sua palette cupa; gli interni sono del pezzo degli edifici esplorabili)."""
    g = a["griglia"]
    w, h = a["larghezza"], a["altezza"]
    q = PC.Quadro(w, h)
    for (x, y), pix in celle.items():
        for yy in range(8):
            for xx in range(8):
                v = pix[yy][xx]
                q.px[y * 8 + yy][x * 8 + xx] = PALETTE_FONDALI[v] if isinstance(v, int) else v
    citta = area_di_citta(a)
    if a.get("interno") and PI.dipinge(a["id"]):
        return PI.dipingi(q, a)           # gli interni esplorabili: la stanza intera da tools/pittore_interni.py
    if a["id"] in AREE_GOLA or a.get("interno"):
        return q
    occupate = {}
    for mid, (x0, y0, ew, eh) in a.get("edifici", {}).items():
        for y in range(y0, y0 + eh):
            for x in range(x0, x0 + ew):
                occupate[(x, y)] = mid
    for _, (nome, lato, piloni, arco) in a.get("porte", {}).items():
        for c in piloni:
            occupate[c] = "porta:" + nome
    calpestabile = lambda x, y: 0 <= y < h and 0 <= x < w and not solida(g[y][x])  # noqa: E731
    case_celle = set()
    for y in range(h):
        for x in range(w):
            c = g[y][x]
            if not solida(c):
                tipo, alto = "suolo", 0
            elif (x, y) in occupate:
                tipo, alto = "edificio", 32
            elif c == "#" and citta:
                tipo, alto = "tetto", 32
                case_celle.add((x, y))
            elif c == "#":
                tipo, alto = "verde", 16       # il bosco del monte
            elif c in "~":
                tipo, alto = "acqua", 0
            elif c == "V":
                tipo, alto = "vuoto", 0
            else:
                tipo, alto = TIPO_CELLA.get(c, ("basso", 4))
            if (x, y) in tile_di and tipo == "verde":
                alto = 20
            for yy in range(y * 8, y * 8 + 8):
                for xx in range(x * 8, x * 8 + 8):
                    q.tipo[yy][xx] = tipo
                    q.alto[yy][xx] = alto
    if citta:
        # 1. il suolo
        for y in range(h):
            for x in range(w):
                nome = SUOLI_RIDIPINTI.get(g[y][x])
                if not nome:
                    continue
                ombra = TILE_FONDALI[tile_per_cella(g, x, y, del_monte(a), a.get("monte"))][0].endswith("_OMBRA")
                for yy in range(y * 8, y * 8 + 8):
                    for xx in range(x * 8, x * 8 + 8):
                        if nome == "corso":
                            # i corsi: lastre lunghe 16x8, il giunto nel tono d'ombra del lastrico (F3)
                            giunto = yy % 8 == 7 or (xx + (8 if (yy // 8) % 2 else 0)) % 16 == 15
                            c = (PC.P, 1) if giunto else ((PC.P, 3) if (xx % 16 == 0 or yy % 8 == 0) else (PC.P, 2))
                        else:
                            c = PC.colore_suolo(nome, xx, yy)
                        q.px[yy][xx] = PC.scuro(c, 1) if ombra else c
                if PC.h32(x, y, 41, w) < 0.02:
                    dettaglio = PC.DETTAGLI_SUOLO[int(PC.h32(x, y, 42) * len(PC.DETTAGLI_SUOLO))]
                    dettaglio(q, x * 8 + 2, y * 8 + 3)
                    q.conta("dettaglio_suolo")
        # scale, soglie, bracieri, fontana
        for y in range(h):
            for x in range(w):
                c = g[y][x]
                if c == "S":
                    PC.dipingi_scala(q, x, y, g)
                elif c in VARCHI and c != "I":
                    PC.dipingi_soglia(q, x, y)
                elif c == "Q":
                    PC.dipingi_lampione(q, x, y)
                elif c == "V":
                    PC.dipingi_citta_bassa(q, x, y, g)
                elif c == "=":
                    PC.dipingi_parapetto(q, x, y, g, calpestabile)
                elif c == "W" and (x, y) not in occupate:
                    PC.dipingi_mura(q, x, y, g, calpestabile)
        fontana = [(x, y) for y in range(h) for x in range(w) if g[y][x] == "F"]
        if fontana:
            fx0, fy0 = min(x for x, _ in fontana), min(y for _, y in fontana)
            PC.dipingi_fontana(q, fx0, fy0, max(x for x, _ in fontana) - fx0 + 1, max(y for _, y in fontana) - fy0 + 1)
        # il verde dei giardini
        for y in range(h):
            for x in range(w):
                c = g[y][x]
                if c in "NZ":
                    for yy in range(y * 8, y * 8 + 8):
                        for xx in range(x * 8, x * 8 + 8):
                            q.px[yy][xx] = PC.colore_verde("prato" if c == "N" else "ghiaia", xx, yy)
                elif c == "Y":
                    PC.dipingi_siepe(q, x, y, g)
                elif c == "D":
                    PC.dipingi_aiuola(q, x, y)
        # 2. le case: prima tutti i tetti, poi le facciate
        case = PC.dividi_in_case(g, case_celle, calpestabile)
        coperte = set()
        for casa in case:
            fondo_tetto = casa.yb - casa.fh
            cima = fondo_tetto
            profondo = 3 + int(PC.h32(casa.n, 55) * 4)
            while cima - 1 >= 0 and cima - 1 > fondo_tetto - profondo and \
                    all((x, cima - 1) in case_celle and (x, cima - 1) not in coperte for x in range(casa.x0, casa.x1 + 1)):
                cima -= 1
            if fondo_tetto >= cima and all((x, fondo_tetto) in case_celle for x in range(casa.x0, casa.x1 + 1)):
                PC.dipingi_tetto(q, casa.x0 * 8, casa.x1 * 8 + 7, cima * 8, fondo_tetto * 8 + 7, casa.tetto, casa.n)
                q.livella(casa.x0 * 8, casa.x1 * 8 + 7, cima * 8, fondo_tetto * 8 + 7, 1)
                if casa.comignolo and fondo_tetto - cima >= 1:
                    _comignolo(q, (casa.x0 + int(PC.h32(casa.n, 50) * (casa.x1 - casa.x0 + 1))) * 8 + 2, cima * 8 + 1)
                for y in range(cima, fondo_tetto + 1):
                    for x in range(casa.x0, casa.x1 + 1):
                        coperte.add((x, y))
            for y in range(casa.yb - casa.fh + 1, casa.yb + 1):
                for x in range(casa.x0, casa.x1 + 1):
                    coperte.add((x, y))
        # i tetti che restano (le case dietro, i retro sulle vie in alto): rettangoli larghi 3-6, alti fino a 5
        n = len(case)
        # i cortili e gli orti chiusi fra le case: rompono la massa dei tetti. Restano celle solide.
        libere = case_celle - coperte
        for k, (x, y) in enumerate(PC.cortili(libere, w, h)):
            PC.dipingi_cortile(q, x, y, k)
            for c in ((x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)):
                coperte.add(c)
                for yy in range(c[1] * 8, c[1] * 8 + 8):
                    for xx in range(c[0] * 8, c[0] * 8 + 8):
                        q.tipo[yy][xx] = "verde"
        resto = sorted(case_celle - coperte, key=lambda c: (c[1], c[0]))
        for (x, y) in resto:
            if (x, y) in coperte:
                continue
            larga = 4 + int(PC.h32(x, y, 51) * 5)
            x1 = x
            while x1 + 1 < x + larga and (x1 + 1, y) in case_celle and (x1 + 1, y) not in coperte:
                x1 += 1
            y1 = y
            profondo = 4 + int(PC.h32(x, y, 56) * 4)
            while y1 + 1 < y + profondo and all((k, y1 + 1) in case_celle and (k, y1 + 1) not in coperte for k in range(x, x1 + 1)):
                y1 += 1
            sotto_via = any(calpestabile(k, y1 + 1) for k in range(x, x1 + 1))
            tono = 2 if PC.h32(x, y, 52) < 0.12 else 3     # i tetti di riempimento: due toni (M2: i tile servono alle facciate)
            PC.dipingi_tetto(q, x * 8, x1 * 8 + 7, y * 8, y1 * 8 + 7, tono, n, gronda=sotto_via or y1 - y >= 1)
            q.livella(x * 8, x1 * 8 + 7, y * 8, y1 * 8 + 7, int(PC.h32(x, y, 58) < 0.45))
            if y1 - y >= 1 and PC.h32(x, y, 53) < 0.3:
                _comignolo(q, (x + int(PC.h32(x, y, 54) * (x1 - x + 1))) * 8 + 2, y * 8 + 1)
            n += 1
            for yy in range(y, y1 + 1):
                for xx in range(x, x1 + 1):
                    coperte.add((xx, yy))
        for casa in case:
            PC.dipingi_casa(q, casa, w)
            for y in range(casa.yb - casa.fh + 1, casa.yb + 1):
                for x in range(casa.x0, casa.x1 + 1):
                    for yy in range(y * 8, y * 8 + 8):
                        for xx in range(x * 8, x * 8 + 8):
                            q.tipo[yy][xx] = "casa"
        PC.ombre_dei_tetti(q)
        # 3. la vita
        PC.vita_delle_case(q, case, a["id"], len(a["id"]))
        PC.panni_stesi(q, g, calpestabile, case_celle, a["id"])
    if a["id"] in AREE_DEL_MONTE:
        ridipingi_monte(q, g, w, h)
    # gli alberi, in citta' e sul monte: sul suolo che c'e' sotto (prato, lastrico, bosco)
    for k, (x0, y0, aw, ah, c) in enumerate(alberi_dell_area(g)):
        for y in range(y0, y0 + ah):
            for x in range(x0, x0 + aw):
                fondo = "prato" if not citta or any(g[yy][xx] in "NDYZ" for yy in (y - 1, y, y + 1) for xx in (x - 1, x, x + 1)
                                                    if 0 <= yy < h and 0 <= xx < w) else None
                for yy in range(y * 8, y * 8 + 8):
                    for xx in range(x * 8, x * 8 + 8):
                        if fondo:
                            # sotto la chioma l'erba e' in ombra e senza fiori: un motivo di 8 pixel (i tile
                            # dell'albero si ripetono uguali dovunque stia)
                            q.px[yy][xx] = PC.colore_verde("prato", xx, yy) if citta else \
                                ((PC.V, 1) if (xx * 3 + yy * 5) % 7 == 0 else (PC.V, 2))
                        elif citta:
                            q.px[yy][xx] = (PC.P, 2) if xx % 8 == 7 or yy % 8 == 7 else (PC.P, 3)
        if citta or fondo:
            PC.dipingi_albero(q, x0, y0, aw, ah, c, k % 3)
    # 4. ombre portate e 5. contorno selettivo
    PC.ombre_portate(q)
    if citta:
        PC.contorno_selettivo(q)
    PI.apri_portali(q, a)                 # i portoni da cui si entra negli interni: aperti, col vano buio
    elementi["citta"] = dict(q.elementi)
    return q


def _comignolo(q, x, y):
    """Il comignolo: un dado di pietra con la bocca scura in cima, la luce a sinistra e l'ombra portata sul tetto
    a destra e in basso (L4)."""
    for yy in range(6):
        for xx in range(4):
            c = (PC.P, 3)
            if xx == 0:
                c = (PC.P, 4)
            elif xx == 3:
                c = (PC.P, 1)
            if yy == 0:
                c = (PC.P, 2) if 0 < xx < 3 else (PC.P, 1)
            if yy == 1 and 0 < xx < 3:
                c = PC.NERO
            q.punto(x + xx, y + yy, c)
    for k in range(1, 3):
        for yy in range(2 + k, 6 + k):
            c = q.get(x + 3 + k, y + yy)
            if c:
                q.punto(x + 3 + k, y + yy, PC.scuro(c, 1))


_RGB = {}


def _rgb(rif):
    if rif not in _RGB:
        if "palette" not in _RGB:
            _RGB["palette"] = S.carica("palette")
        v = S.colore(_RGB["palette"], rif)
        _RGB[rif] = ((v & 31), (v >> 5) & 31, (v >> 10) & 31)
    return _RGB[rif]


def _distanza(r1, r2):
    a, b = _rgb(r1), _rgb(r2)
    return (a[0] - b[0]) ** 2 * 3 + (a[1] - b[1]) ** 2 * 4 + (a[2] - b[2]) ** 2 * 2


COMPROMESSI = {}


def indicizza_tile(q, x, y, a):
    """Il tile (x, y) del quadro: il primo banco che ha tutti i suoi colori, o quello che lo tradisce meno (il
    colore mancante prende il piu' vicino del banco; i compromessi si contano in COMPROMESSI)."""
    pix = [q.px[y * 8 + yy][x * 8:x * 8 + 8] for yy in range(8)]
    colori = {c for r in pix for c in r}
    migliore = None
    for b, banco in enumerate(BANCHI_FONDALI):
        mancano = [c for c in colori if c not in banco[1:]]
        if not mancano:
            migliore = (0, b, {})
            break
        mappa = {c: min(banco[1:], key=lambda k: _distanza(c, k)) for c in mancano}
        costo = sum(_distanza(c, m) for c, m in mappa.items())
        if migliore is None or costo < migliore[0]:
            migliore = (costo, b, mappa)
    costo, b, mappa = migliore
    if mappa:
        COMPROMESSI.setdefault(a["id"], []).append((x, y, costo))
    banco = BANCHI_FONDALI[b]
    indice = {c: banco.index(c, 1) for c in banco[1:]}
    return b, [[indice[mappa.get(c, c)] for c in r] for r in pix]


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
    return sorted((x, y) for mid, (x0, y0, w, h) in a.get("edifici", {}).items() if mid not in FORME
                  for y in range(y0, y0 + h) for x in range(x0, x0 + w)
                  if (not solida(a["griglia"][y][x]) or a["griglia"][y][x] in VARCHI)
                  and a["griglia"][y][x] not in a.get("ingressi", {}))


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
        if mid in FORME:
            if errori_semicerchio(a, (x0, y0, w, h)):
                raise ErroreMondo(f"{a['file']}: la cavea di {mid} non e' un semicerchio: "
                                  f"{errori_semicerchio(a, (x0, y0, w, h))[:3]}")
            continue
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
            if atteso == ["dentro"]:
                if lati or lettera not in a.get("ingressi", {}):
                    raise ErroreMondo(f"{a['file']}:{n}: il varco '{lettera}' verso {dest} e' un portale: "
                                      f"va su un edificio con la riga 'ingresso', non sul bordo")
            elif lati != set(atteso):
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
    # un'area quadrata conta come orizzontale (col nord in alto le vie lunghe corrono di traverso)
    return "verticale" if a["altezza"] > a["larghezza"] else "orizzontale"


def larghezze_lungo_l_asse(a, asse=None):
    """Per ogni linea perpendicolare all'asse lungo dell'area (o all'asse dato), il tratto calpestabile piu'
    lungo."""
    g = a["griglia"]
    asse = asse or asse_lungo_area(a)
    linee = g if asse == "verticale" else ["".join(r[x] for r in g) for x in range(a["larghezza"])]
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
        # la strettoia puo' correre per lungo o di traverso (la stradina fra il Duomo e il Ducale)
        stretta = min(min(righe), min(larghezze_lungo_l_asse(a, "orizzontale" if asse_lungo_area(a) == "verticale"
                                                             else "verticale") or [99]))
        if "strettoia" in a and stretta > a["strettoia"]:
            raise ErroreMondo(f"{a['file']}: la strettoia di {a['strettoia']} tile non c'e': il tratto piu' "
                              f"stretto e' {stretta}")
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
        x0, y0 = rx - w // 2, ry - (h - 1) // 2
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                if not (0 <= x < a["larghezza"] and 0 <= y < a["altezza"]) or \
                        (solida(a["griglia"][y][x]) and a["griglia"][y][x] not in "FQOYTDrvu"):
                    raise ErroreMondo(f"{a['file']}:{n}: {nome} ({w}x{h} tile intorno al riferimento) non e' "
                                      f"libera in ({x}, {y})")


def anello(grafo):
    """L'anello di grafo.json, senza la ripetizione finale della prima area."""
    return [aid.lower() for aid in grafo["anello"][:-1]]


# --- Uscita C++ -------------------------------------------------------------------------------

def pixel_cartiglio(pezzo):
    """Il pezzo 'sinistro', 'centrale' o 'destro' del cartiglio, 32x16 pixel: pergamena di pietra
    scura (il nome e' chiaro con l'ombra scura: su una pergamena chiara si perdeva), bordo chiaro
    con il filo scuro, le volute alle estremita'."""
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
                riga.append(2 if (x + y) % 9 else 3)
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


# Gli interni esplorabili (pezzo INT2) vanno in coda, dopo le 19 aree di prima e in quest'ordine: i salvataggi
# tengono l'indice dell'area (AreaId) e la nebbia della mappa ha un bit per area all'aperto (indici sotto 24).
AREE_IN_CODA = ["taverna_interno", "spezieria_interno", "bottega_conti_interno", "carradore_interno",
                "casa_medico_interno", "sala_consoli"]


def ordina(aree, giro):
    coda = [i for i in AREE_IN_CODA if i in {a["id"] for a in aree}]
    altre = sorted(a["id"] for a in aree if a["id"] not in giro and a["id"] not in coda)
    per_id = {a["id"]: a for a in aree}
    return [per_id[i] for i in giro + altre + coda]


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
        f"inline constexpr int PRIMA_CELLA_SOLIDA = {[s for _, s in CELLE.values()].index(True)};",
        f"inline constexpr int DISTANZA_MIN_SPAWN = {DISTANZA_MIN_SPAWN};",
        f"inline constexpr int DISTANZA_MIN_SPAWN_USCITA = {DISTANZA_MIN_SPAWN_USCITA};",
        f"inline constexpr int LATO_MAX = {LATO_MAX};          // tile per lato di un'area",
        f"inline constexpr int SPAWN_PER_AREA = {SPAWN_PER_AREA};",
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
        "    bool interno;                     // un interno ('interno' nel .area): fuori dalla nebbia della mappa",
        "    bool cupa;                        // le stanze della gola: la palette cupa (PALETTE_FONDALI_CUPA)",
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
                mappa.append(tile_per_cella(a["griglia"], x, y, del_monte(a), a.get("monte")))
        n = a["larghezza"] * a["altezza"]
        nome = a["id"].upper()
        out += [f"inline constexpr uint8_t GRIGLIA_{nome}[{n}] = {{", a_blocchi(celle, 32), "};", "",
                f"inline constexpr uint8_t MAPPA_{nome}[{n}] = {{", a_blocchi(mappa, 32), "};", ""]
        gw, gh = lati_fondale(a)
        fondale = celle_fondale(a, [i | (a["specchi"][k] << 10) | (a["banchi"][i] << 12)
                                    for k, i in enumerate(a["indici"])])
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
        spawn = [a["spawn"].get(i, a["spawn"][0]) for i in range(SPAWN_PER_AREA)]
        out += [
            f"    {{   // {a['id']}",
            f"        GRIGLIA_{nome}, MAPPA_{nome}, {a['larghezza']}, {a['altezza']},",
            f"        FONDALE_{nome}, {lati_fondale(a)[0]}, {lati_fondale(a)[1]}, {'true' if grande(a) else 'false'}, "
            f"TILE_{nome}, {len(a['tile'])}, {q[0]}, {q[1]},",
            f"        testi::TestoId::{a['etichetta']}, {len(a['uscite'])},",
            "        { " + ", ".join(varchi) + " },",
            "        { " + ", ".join(f"{{ {x}, {y} }}" for x, y in spawn) + " },",
            f"        {'true' if a.get('interno') else 'false'},",
            f"        {'true' if a['id'] in AREE_GOLA else 'false'},",
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
            "};", "",
            "// La palette cupa delle stanze della gola (Area::cupa): le stesse voci con le rampe di notte.",
            "inline constexpr uint16_t PALETTE_FONDALI_CUPA[16] = {",
            a_blocchi([S.colore(palette_stile, r, True) for r in palette_cupa(palette_stile)], 8, lambda v: f"0x{v:04X}"),
            "};", "",
            "// I banchi della palette dei fondali (pezzo EDI, tools/pittore_citta.py): il banco 0 e' PALETTE_FONDALI,",
            "// gli altri sono tetti, pietra, vita, verde e giardino. La cella del fondale porta il banco nei bit 12-15.",
            f"inline constexpr int BANCHI_FONDALI = {len(BANCHI_FONDALI)};", ""]
    for nome, kw in (("", {}), ("_CUPA", {"cupa": True}), ("_NOTTE", {"notte": True})):
        parole = [v for banco in banchi_fondali(palette_stile, **kw) for v in banco]
        out += [f"inline constexpr uint16_t PALETTE_FONDALI_BANCHI{nome}[BANCHI_FONDALI * 16] = {{",
                a_blocchi(parole, 8, lambda v: f"0x{v:04X}"), "};", ""]

    out += ["// Il cartiglio dietro il nome dell'area: tre pezzi da 32x16 (sinistro, centrale, destro),",
            "// 8 tile ciascuno in mappatura 1D, con la palette dei fondali.",
            "inline constexpr int TILE_PER_PEZZO_CARTIGLIO = 8;",
            "inline constexpr bn::tile TILE_CARTIGLIO[3 * TILE_PER_PEZZO_CARTIGLIO] = {"]
    for pezzo in tile_cartiglio():
        for k in range(0, len(pezzo), 8):
            out.append("    { { " + ", ".join(f"0x{v:08X}" for v in pezzo[k:k + 8]) + " } },")
    out += ["};", ""]

    tiles = []
    for griglia in SM.fotogrammi():
        for ty in range(4):
            for tx in range(2):
                tiles += parole_tile([riga[tx * 8:tx * 8 + 8] for riga in griglia[ty * 8:ty * 8 + 8]])
    fot = len(SM.DIREZIONI) * SM.FOTOGRAMMI
    out += ["// Il giocatore (tools/sagome_mappa.py): Ubaldo 16x32 (8 tile in mappatura 1D a fotogramma), le",
            "// direzioni giu', su, destra (sinistra = destra specchiata), 8 fotogrammi l'una: 6 di camminata, riposo,",
            "// respiro. L'ombra sotto i piedi e' nel disegno.",
            f"inline constexpr int GIOCATORE_DIREZIONI = {len(SM.DIREZIONI)};",
            f"inline constexpr int GIOCATORE_FOTOGRAMMI = {SM.FOTOGRAMMI};",
            f"inline constexpr int GIOCATORE_CAMMINATA = {SM.CAMMINATA};",
            f"inline constexpr int GIOCATORE_RIPOSO = {SM.RIPOSO};",
            f"inline constexpr int GIOCATORE_RESPIRO = {SM.RESPIRO};",
            f"inline constexpr int GIOCATORE_VBLANK_PASSO = {SM.VBLANK_PASSO};",
            f"inline constexpr int GIOCATORE_VBLANK_CORSA = {SM.VBLANK_CORSA};",
            f"inline constexpr int GIOCATORE_VBLANK_RESPIRO = {SM.VBLANK_RESPIRO};",
            f"inline constexpr uint32_t TILE_GIOCATORE[{fot} * 8 * 8] = {{",
            a_blocchi(tiles, 8, lambda v: f"0x{v:08X}"), "};", "",
            "inline constexpr uint16_t PALETTE_GIOCATORE[16] = {",
            a_blocchi([colore(r) for r in PALETTE_GIOCATORE], 8, lambda v: f"0x{v:04X}"),
            "};", "",
            "// di notte (STANDARD L5) il giocatore prende le rampe di notte, come i fondali e la gente",
            "inline constexpr uint16_t PALETTE_GIOCATORE_NOTTE[16] = {",
            a_blocchi([S.colore(palette_stile, r, True) for r in PALETTE_GIOCATORE], 8, lambda v: f"0x{v:04X}"),
            "};", "",
            "// Il segnale d'interazione (STANDARD I2, tools/sagome_mappa.py): un tile 8x8 con la palette del",
            "// giocatore; oscilla di un pixel ogni FUMETTO_OSCILLA vblank.",
            f"inline constexpr int FUMETTO_OSCILLA = {SM.FUMETTO_OSCILLA};",
            "inline constexpr uint32_t TILE_FUMETTO[8] = {",
            a_blocchi(parole_tile(SM.fumetto()), 8, lambda v: f"0x{v:08X}"), "};", "", "}", "", "#endif", ""]
    return "\n".join(out)


def mondo_del_repo():
    """Il grafo (mondo/grafo.json) e i lati dei varchi (mondo/varchi.json) del repo."""
    with open(M.OUT_VARCHI, encoding="utf-8") as f:
        varchi = json.load(f)["varchi"]
    with open(M.OUT_MONUMENTI, encoding="utf-8") as f:
        monumenti = json.load(f)["monumenti"]
    with open(os.path.join(RADICE, "mondo", "fonti", "misure_osm.json"), encoding="utf-8") as f:
        misure = json.load(f)
    with open(STRADONI, encoding="utf-8") as f:
        stradoni = json.load(f)
    return {"grafo": M.carica_grafo(), "varchi": varchi, "monumenti": monumenti, "misure": misure,
            "censimento": M.carica_censimento(), "stradoni": stradoni}


def apri_ingressi(a):
    """"ingresso E basilica": il portone dell'edificio diventa il varco E, che porta dentro."""
    g = [list(r) for r in a["griglia"]]
    for lettera, mid in a.get("ingressi", {}).items():
        if mid not in a.get("edifici", {}):
            raise ErroreMondo(f"{a['file']}: ingresso '{lettera}' su {mid}, che non e' un edificio dell'area")
        x0, y0, w, h = a["edifici"][mid]
        portone = [(x, y) for y in range(y0, y0 + h) for x in range(x0, x0 + w) if g[y][x] == PORTONE_EDIFICIO]
        if not portone:
            raise ErroreMondo(f"{a['file']}: ingresso '{lettera}': {mid} non ha un portone")
        for x, y in portone:
            g[y][x] = lettera
    a["griglia"] = ["".join(r) for r in g]


def prepara_area(a, mondo):
    """L'area come la vede il gioco: edifici posati e controllati, decoro della piazza, dislivello,
    porte della citta'."""
    controlla_edifici(a, posa_edifici(a, mondo["monumenti"]), mondo["monumenti"])
    apri_ingressi(a)
    decora_piazza(a)
    applica_dislivello(a, mondo["grafo"])
    costruisci_porte(a, mondo["grafo"])


def genera(sorgenti, palette_stile, mondo=None):
    """sorgenti: lista di (nome, testo). Ritorna il testo di include/mondo.h."""
    mondo = mondo or mondo_del_repo()
    controlla_ordine_celle()
    aree = [leggi_area(nome, testo) for nome, testo in sorgenti]
    cinta = errori_cinta(mondo["grafo"])
    if cinta:
        raise ErroreMondo("mondo/grafo.json: " + "; ".join(cinta))
    for a in aree:
        prepara_area(a, mondo)
    controlla(aree, mondo)
    for a in aree:
        controlla_vicinanze(a)
        controlla_proporzioni(a, mondo["misure"])
        oltre = errori_belvedere(a)
        if oltre:
            raise ErroreMondo(f"{a['file']}: oltre il parapetto del belvedere ci sono tetti a quota piena: {oltre[:4]}")
        if a.get("stradoni"):
            stradoni = errori_stradoni(a, mondo["stradoni"])
            if stradoni:
                raise ErroreMondo(f"{a['file']}: gli stradoni non tornano: " + "; ".join(stradoni))
        porte = errori_porte(a, mondo["grafo"])
        if porte:
            raise ErroreMondo(f"{a['file']}: " + "; ".join(porte))
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
