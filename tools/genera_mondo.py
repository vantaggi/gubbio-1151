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
schermo si apre ogni varco. Un file .area tiene solo la griglia, gli spawn e dove stanno le
uscite: "uscita A largo_bargello 2" vuol dire che il varco A della griglia e' l'arco verso il
Largo del Bargello, e che chi arriva da li' compare sullo spawn 2 di quest'area.

Prima di scrivere controlla il mondo e si rifiuta se trova: un carattere sconosciuto, una riga
di lunghezza sbagliata, un varco senza riga "uscita" o viceversa, uno spawn che non esiste, una
uscita senza arco in grafo.json o un arco senza uscita, un varco che non sta sul bordo indicato da
varchi.json, uno spawn d'arrivo a meno di DISTANZA_MIN_SPAWN_USCITA tile dalla propria uscita o a
meno di DISTANZA_MIN_SPAWN da un altro varco, uno spawn su una cella non calpestabile, un varco
che da uno spawn d'arrivo non si raggiunge camminando. Spawn e camminata li rifa' l'autotest C++
(include/mondo_autotest.h) a tempo di compilazione.

Debito aperto (F2): le griglie sono quelle del prototipo, con le sole uscite spostate sul lato
giusto; la scala di 1 tile = 1,5 m dei monumenti (mondo/monumenti.json) non vi e' ancora applicata.

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
    "d": ("PORTONE", False),       # portone solo visivo
    "F": ("FONTANA", True),
    "#": ("MURO", True),
    "=": ("PARAPETTO", True),      # affaccio sul vuoto
    "C": ("FACCIATA", True),       # facciata monumentale (Consoli, San Francesco, ...)
    "P": ("FACCIATA_2", True),     # seconda facciata (Pretorio, Bargello, acquedotto, ...)
}
VARCHI = "ABEGI"
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
    # selciato in cotto a spina di pesce
    blocco = ((x // 4) + (y // 4)) % 2
    posizione = (x % 4 if blocco else y % 4)
    return [9, 8, 8, 7][posizione] if (x + y) % 4 != 3 else 6


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
]
INDICE_TILE = {nome: i for i, (nome, _) in enumerate(TILE_FONDALI)}


def tile_per_cella(griglia, x, y, del_monte=False):
    """Il tile del fondale per la cella (x, y): l'unica regola che decide come si vede il mondo."""
    c = griglia[y][x]
    if c in VARCHI:
        return INDICE_TILE["INGRESSO" if c == "I" else "VARCO"]
    nome = CELLE[c][0]
    if nome == "MURO":
        if del_monte:
            return INDICE_TILE["BOSCO"]
        sotto = griglia[y + 1][x] if y + 1 < len(griglia) else "#"
        # il muro che ha davanti (in basso sullo schermo) uno spazio calpestabile si vede di
        # fronte: e' il muro di sostegno o il fronte cieco; il resto e' tetto visto dall'alto
        return INDICE_TILE["MURO_FRONTE" if not solida(sotto) else "TETTO"]
    return INDICE_TILE[nome]


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
    a = {"file": nome_file, "spawn": {}, "uscite": [], "griglia": []}
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
                    if len(t) != 4:
                        raise ValueError
                    a["uscite"].append((t[1], t[2], int(t[3]), n))
            elif t[0] == "griglia":
                in_griglia = True
            else:
                raise ErroreMondo(f"{nome_file}:{n}: riga '{t[0]}' sconosciuta")
        except (IndexError, ValueError):
            raise ErroreMondo(f"{nome_file}:{n}: riga malformata: {riga}") from None
    for campo in ("id", "etichetta", "larghezza"):
        if campo not in a:
            raise ErroreMondo(f"{nome_file}: manca '{campo}'")
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
            visti = raggiungibili(a, (sx, sy))
            for lettera, _, _, n in a["uscite"]:
                vicini = {(x + dx, y + dy) for x, y in celle_varco(a, lettera)
                          for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))}
                if not vicini & visti:
                    raise ErroreMondo(f"{a['file']}:{n}: il varco '{lettera}' non si raggiunge "
                                      f"camminando dallo spawn {s}")


def anello(grafo):
    """L'anello di grafo.json, senza la ripetizione finale della prima area."""
    return [aid.lower() for aid in grafo["anello"][:-1]]


# --- Uscita C++ -------------------------------------------------------------------------------

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
        "// mondo/varchi.json e stile/dati/palette.json.",
        "// Non modificare a mano: si accede ai dati solo da include/mondo_logica.h.",
        "#ifndef GUBBIO_MONDO_H",
        "#define GUBBIO_MONDO_H",
        "",
        "#include <cstdint>",
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
                mappa.append(tile_per_cella(a["griglia"], x, y, a["id"] in AREE_DEL_MONTE))
        n = a["larghezza"] * a["altezza"]
        nome = a["id"].upper()
        out += [f"inline constexpr uint8_t GRIGLIA_{nome}[{n}] = {{", a_blocchi(celle, 32), "};", "",
                f"inline constexpr uint8_t MAPPA_{nome}[{n}] = {{", a_blocchi(mappa, 32), "};", ""]

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
            f"        GRIGLIA_{nome}, MAPPA_{nome}, {a['larghezza']}, {a['altezza']}, {q[0]}, {q[1]},",
            f"        testi::TestoId::{a['etichetta']}, {len(a['uscite'])},",
            "        { " + ", ".join(varchi) + " },",
            "        { " + ", ".join(f"{{ {x}, {y} }}" for x, y in spawn) + " },",
            "    },",
        ]
    out += ["};", ""]

    out += ["// Fondali: tile 8x8 a 4bpp (un nibble per pixel, pixel di sinistra nei bit bassi).",
            "enum class TileFondale : uint8_t", "{"]
    out += [f"    {nome}," for nome, _ in TILE_FONDALI]
    out += ["};", "",
            f"inline constexpr int TILE_FONDALI = {len(TILE_FONDALI)};",
            "inline constexpr uint32_t TILE_FONDALE[TILE_FONDALI * 8] = {"]
    for nome, funzione in TILE_FONDALI:
        out.append(f"    // {nome.lower()}")
        out.append(a_blocchi(parole_tile(_tile(funzione)), 8, lambda v: f"0x{v:08X}"))
    out += ["};", "",
            "inline constexpr uint16_t PALETTE_FONDALI[16] = {",
            a_blocchi([colore(r) for r in PALETTE_FONDALI], 8, lambda v: f"0x{v:04X}"),
            "};", ""]

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
    return {"grafo": M.carica_grafo(), "varchi": varchi}


def genera(sorgenti, palette_stile, mondo=None):
    """sorgenti: lista di (nome, testo). Ritorna il testo di include/mondo.h."""
    mondo = mondo or mondo_del_repo()
    aree = [leggi_area(nome, testo) for nome, testo in sorgenti]
    controlla(aree, mondo)
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
