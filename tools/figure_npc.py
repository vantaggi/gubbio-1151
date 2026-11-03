"""Le figure degli NPC (pezzi S e SV2): cinque sagome 16x16 riconoscibili, una per mestiere, con la
palette dei popolani (PALETTE_NEMICI di tools/genera_battaglia.py, la stessa che usa il gioco per gli
NPC). Ogni NPC d'ambiente (copione/03_npc_ambiente.md) prende la figura dal suo nome; ogni amico
(copione/05_npc_amici.md, dati/amici.json) una figura base con il suo accessorio, o una figura nuova
(Gabrione, una testa piu' alto e pelato; Nicoluccio, bambino).

Nel gioco lo sprite e' 16x32: la figura sta nelle 16 righe in basso, sopra resta posto per chi e' piu'
alto e per gli accessori lunghi (l'arco, la trave, il bastone).

Le figure sono di fronte come il giocatore, col contorno scuro; le cifre sono gli indici della palette
in esadecimale ('.' trasparente):
1 contorno, 2-3 pelle, 4-5 vermiglio, 6 bianco, 7 grigio, 8-9 pietra, a-b cuoio, c-d ferro, e oro, f verde.
"""
import re

FIGURE = {
    # la popolana: il fazzoletto bianco in testa, la veste rossa, il grembiule
    "popolana": [
        "......1111......",
        ".....166661.....",
        "....16666661....",
        "....16333361....",
        "....16131361....",
        "....16333361....",
        ".....133331.....",
        "....14444441....",
        "...1446666441...",
        "...1446666441...",
        "...1446666441...",
        "...1446666441...",
        "...1444444441...",
        "..144444444441..",
        "...1111111111...",
        "................",
    ],
    # il frate: il saio col cappuccio, il cordone bianco coi nodi, i sandali
    "frate": [
        "................",
        ".....1aaaa1.....",
        "....1aa33aa1....",
        "...1aa3333aa1...",
        "...1a313313a1...",
        "...1a333333a1...",
        "....1a3333a1....",
        "...1aaaaaaaa1...",
        "..1abaaaaaaba1..",
        "..1abaaaaaaba1..",
        "..1a66666666a1..",
        "...1aaa6aaaa1...",
        "...1aaa6aaaa1...",
        "...1aaaaaaaa1...",
        "....12....21....",
        "....11....11....",
    ],
    # il soldato: il cappello di ferro a tesa larga, la giubba rossa con la croce, la lancia
    "soldato": [
        ".............d..",
        "......1111...d..",
        "....1dddddd1.b..",
        "...1dd7777dd1b..",
        "....13333331.b..",
        "....13133131.b..",
        "....13333331.b..",
        ".....133331..b..",
        "....14444441.b..",
        "...1444664441b..",
        "...1466666641b..",
        "...1444664441b..",
        "....14444441.b..",
        "....1cccccc1.b..",
        "....1c1..1c1.b..",
        "....11....11.b..",
    ],
    # il mercante: il cappuccio rosso a tesa, la veste lunga di cuoio, la cintura d'oro e la borsa
    "mercante": [
        "......5555......",
        ".....555555.....",
        "....15555551....",
        "....13333331....",
        "....13133131....",
        "....13333331....",
        ".....133331.....",
        "....1bbbbbb1....",
        "...1bbbbbbbb1...",
        "...1bbbbbbbb1...",
        "...1eeeeeeee1...",
        "...1bbbbbbe41...",
        "...1bbbbbbb41...",
        "..1bbbbbbbbbb1..",
        "..111111111111..",
        "................",
    ],
    # l'anziano: i capelli grigi, la barba bianca, il mantello di lana, il bastone, curvo
    "anziano": [
        "................",
        "......1111......",
        ".....1dddd1.....",
        "....1d3333d1....",
        "....1d3133d1....",
        "....1d6336d1....",
        ".....166661.....",
        "....18866881....",
        "..a18888888881..",
        "..318888888881..",
        "..a18888888881..",
        "..a18888888881..",
        "..a.1888888881..",
        "..a.188888881...",
        "..a..1a..1a1....",
        "..a..11..111....",
    ],
}
ORDINE = ["popolana", "frate", "soldato", "mercante", "anziano"]
ALTO = 32                       # le righe dello sprite nel gioco (16x32)

# le figure nuove della storia v2, gia' a 32 righe
FIGURE_NUOVE = {
    # Gabrione: una testa piu' alto degli altri, pelato (la luce sulla testa), la veste grigia del pittore
    "gabrione": ["................"] * 11 + [
        ".....1111.......",
        "....133331......",
        "....139331......",
        "....131331......",
        "....133331......",
        ".....1331.......",
        "....177771......",
        "...17777771.....",
        "...17777771.....",
        "...17777771.....",
        "...17d77d71.....",
        "...17777771.....",
        "...17777771.....",
        "....177771......",
        "....177771......",
        "....17..71......",
        "....1a..a1......",
        "....11..11......",
        "................",
        "................",
        "................",
    ],
    # Nicoluccio: un bambino, alto due terzi, i capelli bruni e la tunichetta rossa
    "bambino": ["................"] * 21 + [
        ".....1111.......",
        "....1aaaa1......",
        "....133331......",
        "....131131......",
        ".....1331.......",
        "....144441......",
        "...14444441.....",
        "....144441......",
        "....13..31......",
        "....11..11......",
        "................",
    ],
}


def _a_32(righe):
    return ["................"] * (ALTO - len(righe)) + list(righe)


def _varianti():
    out = {}
    anziano = [r for r in FIGURE["anziano"]]
    # l'anziano senza barba bianca: dove c'era la barba, il viso e la veste
    out["anziano_glabro"] = [r.replace("6", "3") if i in (5, 6) else r for i, r in enumerate(anziano)]
    # il soldato senza elmo, a braccia nude: i capelli al posto del ferro, le maniche di pelle
    soldato = [list(r) for r in FIGURE["soldato"]]
    for y in (1, 2, 3):
        for x in range(16):
            if soldato[y][x] in "d7":
                soldato[y][x] = "a"
    for y in (9, 10, 11):
        for x in (3, 12):
            if soldato[y][x] == "4":
                soldato[y][x] = "3"
        soldato[y][3] = "3"
    out["soldato_nudo"] = ["".join(r) for r in soldato]
    return out


VARIANTI = _varianti()


def griglia_base(base):
    """Le 32 righe di una figura base (o nuova), come liste di caratteri."""
    if base in FIGURE_NUOVE:
        righe = FIGURE_NUOVE[base]
    elif base in VARIANTI:
        righe = _a_32(VARIANTI[base])
    else:
        righe = _a_32(FIGURE[base])
    assert len(righe) == ALTO and all(len(r) == 16 for r in righe), base
    return [list(r) for r in righe]


def _punti(g, punti, c):
    for x, y in punti:
        if 0 <= x < 16 and 0 <= y < ALTO:
            g[y][x] = c


def _rett(g, x0, y0, w, h, c):
    _punti(g, [(x, y) for y in range(y0, y0 + h) for x in range(x0, x0 + w)], c)


# Gli accessori: ognuno disegna sulla griglia di 32 righe (la figura base occupa le righe 16-31: la testa
# 16-22, il busto 23-28, le gambe 29-31; la mano destra intorno a x=12, la sinistra a x=3).
def _arco_lungo(g):
    _punti(g, [(14, y) for y in range(12, 31)], "a")
    _punti(g, [(13, 12), (13, 30), (15, 13), (15, 29)], "a")
    _punti(g, [(12, y) for y in range(13, 30)], "7")


def _salterio(g):
    _rett(g, 8, 24, 5, 3, "b")
    _punti(g, [(9, 25), (11, 25)], "e")


def _viella(g):
    _rett(g, 10, 23, 3, 4, "a")
    _punti(g, [(13, 21), (13, 22), (14, 20)], "a")
    _punti(g, [(11, 24)], "1")


def _borsa_medico(g):
    _rett(g, 12, 26, 3, 3, "a")
    _punti(g, [(13, 25)], "1")


def _fascia_gialla_rossa(g):
    _punti(g, [(5 + k, 23 + k) for k in range(6)], "e")
    _punti(g, [(6 + k, 23 + k) for k in range(5)], "4")


def _pinze_tavoletta(g):
    _punti(g, [(5, 27), (6, 28), (7, 27)], "c")
    _rett(g, 11, 22, 4, 4, "e")
    _punti(g, [(12, 23), (13, 24)], "4")


def _ruota(g):
    for x, y in [(12, 22), (13, 22), (14, 23), (15, 24), (15, 25), (14, 26), (13, 27), (12, 27),
                 (11, 26), (10, 25), (10, 24), (11, 23)]:
        _punti(g, [(x, y)], "c")
    _punti(g, [(12, 24), (13, 25), (12, 25), (13, 24)], "a")


def _secchio_corda(g):
    _rett(g, 12, 27, 3, 3, "c")
    _punti(g, [(12, 26), (14, 26)], "d")
    _punti(g, [(13, y) for y in range(22, 26)], "b")


def _tamburo(g):
    _rett(g, 4, 25, 6, 3, "4")
    _punti(g, [(x, 25) for x in range(4, 10)], "6")
    _punti(g, [(10, 23), (11, 22)], "a")


def _balestra(g):
    _punti(g, [(x, 23) for x in range(1, 13)], "a")
    _punti(g, [(2, 21), (2, 22), (2, 24), (2, 25)], "d")


def _carboncino(g):
    _punti(g, [(12, 27), (12, 28)], "1")


def _tavoletta_cera(g):
    _rett(g, 10, 23, 4, 4, "e")
    _punti(g, [(14, 22), (14, 23)], "d")


def _libro(g):
    _rett(g, 6, 24, 4, 3, "a")
    _punti(g, [(7, 25), (8, 25)], "6")


def _rotolo(g):
    _rett(g, 11, 24, 3, 2, "9")
    _punti(g, [(11, 24), (13, 25)], "d")


def _ciotola(g):
    _rett(g, 6, 24, 4, 2, "b")
    _punti(g, [(7, 24), (8, 24)], "6")


def _fiasco_grembiule(g):
    for y in range(24, 29):
        for x in range(5, 11):
            if g[y][x] == "b":
                g[y][x] = "6"
    _rett(g, 12, 26, 3, 3, "f")
    _punti(g, [(13, 25)], "a")


def _tavoliere(g):
    _rett(g, 11, 23, 4, 5, "b")
    _punti(g, [(11, 23), (13, 23), (12, 24), (14, 24), (11, 25), (13, 25), (12, 26), (14, 26)], "c")


def _chiave(g):
    _punti(g, [(12, 23), (12, 24), (12, 25), (12, 26), (13, 26)], "d")
    _rett(g, 11, 21, 3, 2, "d")


def _tavoletta_conti(g):
    _rett(g, 7, 24, 4, 3, "b")
    _punti(g, [(8, 25), (9, 25)], "1")


def _lanterna_bastone(g):
    _punti(g, [(2, y) for y in range(14, 31)], "a")
    _rett(g, 12, 25, 2, 3, "e")
    _punti(g, [(12, 24), (13, 24)], "1")


def _trave(g):
    _rett(g, 0, 17, 16, 2, "b")
    _punti(g, [(x, 18) for x in range(0, 16, 3)], "a")


def _scudo_monte(g):
    _rett(g, 1, 23, 5, 6, "4")
    _punti(g, [(3, 24), (2, 25), (3, 25), (4, 25), (2, 26), (3, 26), (4, 26)], "6")
    _punti(g, [(1, 28), (5, 28)], "1")


ACCESSORI = {"arco_lungo": _arco_lungo, "salterio": _salterio, "viella": _viella, "borsa_medico": _borsa_medico,
             "fascia_gialla_rossa": _fascia_gialla_rossa, "pinze_tavoletta": _pinze_tavoletta, "ruota": _ruota,
             "secchio_corda": _secchio_corda, "tamburo": _tamburo, "balestra": _balestra, "carboncino": _carboncino,
             "tavoletta_cera": _tavoletta_cera, "libro": _libro, "rotolo": _rotolo, "ciotola": _ciotola,
             "fiasco_grembiule": _fiasco_grembiule, "tavoliere": _tavoliere, "chiave": _chiave,
             "tavoletta_conti": _tavoletta_conti, "lanterna_bastone": _lanterna_bastone, "trave": _trave,
             "scudo_monte": _scudo_monte}


def figura_composta(base, accessorio):
    """La figura di 32 righe: la base con l'accessorio disegnato sopra."""
    g = griglia_base(base)
    if accessorio:
        ACCESSORI[accessorio](g)
    return ["".join(r) for r in g]

# il mestiere dal nome dell'NPC nel copione
MESTIERI = [(r"Popolana|Lavandaia|Tessitrice", "popolana"), (r"Fra'|Frate|Canonico", "frate"),
            (r"Balestriere|Sentinella", "soldato"), (r"console|Merciaio|Venditore", "mercante"),
            (r"Vecchio|Mastro|Tagliapietre", "anziano")]


def figura_di(nome):
    """La figura di un NPC dal suo nome nel copione; un nome che non dice il mestiere e' un errore."""
    for schema, figura in MESTIERI:
        if re.search(schema, nome):
            return figura
    raise ValueError(f"NPC '{nome}': nessuna figura per questo nome (tools/figure_npc.py, MESTIERI)")


def pixel(figura):
    """Le 32 righe di una figura: un nome di FIGURE o una figura composta (lista di 32 righe)."""
    righe = _a_32(FIGURE[figura]) if isinstance(figura, str) else figura
    return [[int(c, 16) if c != "." else 0 for c in riga] for riga in righe]


def parole(figura):
    """Le 8 tile 8x8 (16x32 in mappatura 1D) in parole da 32 bit, 4 bit per pixel."""
    px = pixel(figura)
    out = []
    for ty in range(ALTO // 8):
        for tx in range(2):
            for riga in px[ty * 8:ty * 8 + 8]:
                parola = 0
                for x, v in enumerate(riga[tx * 8:tx * 8 + 8]):
                    parola |= v << (4 * x)
                out.append(parola)
    return out
