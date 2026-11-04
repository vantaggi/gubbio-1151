"""I piani di C6, La visione nel vetro (dentro A1-09, al posto della regia «uno dei vetri chiari si
scurisce»): la bifora del prologo coi vetri chiari (il piano vetrata, gia' in ROM) e un vetro in basso
nella lancetta destra, lo stesso che nell'epilogo prende colore, che si scurisce. Dentro il vetro la gola
di notte disegnata a pannelli di vetro piombati (celle irregolari, non mattoni), la parete con gli archi
dell'acquedotto, la fila degli uomini in ferro che sale col passo e in fondo il gigante col martello;
poi il primo piano del gigante che cala il martello sull'arco (il colpo del motore). Muta: le parole le
dicono subito dopo i tre, nella vista di gioco. Dal mockup approvato (cutscene/v2, CUTM).

Un pittore riceve il momento e ritorna (tela, palette, notte), come in tools/pittore_panorami.py.
"""
import math
import random

from genera_battaglia import Tela
from pennelli import ACCESO, contorna, piombi, poligono

W, H = 512, 256
QUADRO = 112

# il vetro che si scurisce: lo stesso rettangolo del vetro che nell'epilogo prende colore
VETRO_SCURO = (124, 74, 32, 26)


def c6_vetro_scuro(m):
    """La bifora del prologo coi vetri chiari, ma il vetro in basso nella lancetta destra si e'
    scurito e lascia intravedere la gola (le stesse coordinate del vetro che si colora nell'epilogo)."""
    import pittore_panorami as PP          # qui e non in cima: pittore_panorami importa questo modulo
    t = PP.vetrata_disegno("chiari")
    vx, vy, vw, vh = VETRO_SCURO
    for y in range(vy, vy + vh):
        for x in range(vx, vx + vw):
            if PP.nel_vetro(x, y) and t.px[y][x] != PP.V_BUIO:
                t.punto(x, y, PP.V_BLU)
    for y in range(vy, vy + vh):                                                  # le pareti della gola
        for x in range(vx, vx + vw):
            if PP.nel_vetro(x, y) and t.px[y][x] == PP.V_BLU:
                sx = vx + 7 + int(2 * math.sin(y / 3.0))
                dx = vx + vw - 8 + int(2 * math.sin(y / 4.0 + 1))
                if x < sx or x > dx:
                    t.punto(x, y, PP.V_GRIGIO)
    for k in range(3):                                                            # gli archi, appena
        t.rett(vx + 9 + k * 6, vy + 6, 2, 8, PP.V_PIETRA)
    t.rett(vx + 8, vy + 5, 16, 2, PP.V_PIETRA)
    for k in range(4):                                                            # le figure che salgono
        t.rett(vx + 11 + k * 3, vy + 20 - k * 2, 2, 3, PP.V_BUIO)
    return t, PP.PALETTE_VETRATA, False


PALETTE_VISIONE = [("neutri", 0), ("neutri", 0), ("cielo e acqua", 0), ("cielo e acqua", 1), ("cielo e acqua", 2),
                   ("cielo e acqua", 4), ("pietra calcarea", 1), ("pietra calcarea", 3), ("verde dei monti", 2),
                   ("verde dei monti", 4), ("neutri", 2, ACCESO), ("neutri", 3, ACCESO), ("vermiglio comunale", 2, ACCESO),
                   ("neutri", 1, ACCESO), ("cielo e acqua", 1), ("oro e bronzo", 3, ACCESO)]
VI_PIOMBO, VI_NOTTE, VI_BLU, VI_AZZURRO, VI_CHIARO = 1, 2, 3, 4, 5
VI_ROCCIA_S, VI_ROCCIA, VI_VERDE_S, VI_VERDE, VI_FERRO, VI_FERRO_C, VI_ROSSO = 6, 7, 8, 9, 10, 11, 12
VI_GAMBE_A, VI_GAMBE_B, VI_ORO = 13, 14, 15
VI_FERRO_S = 13
# i fanti: il 14 ha il colore della roccia del sentiero (VI_ROCCIA), come in pittore_c2 il 14 ha quello del
# prato; le gambe della posa che non c'e' spariscono nella roccia
PALETTE_VISIONE_FANTI = PALETTE_VISIONE[:13] + [("neutri", 1), ("pietra calcarea", 3), ("oro e bronzo", 3, ACCESO)]


def c6_cielo(m):
    """Il cielo del vetro: notte blu a pannelli, la luna in alto a sinistra (la luce del vetro)."""
    t = Tela(W, H, VI_NOTTE)
    for y in range(QUADRO):
        for x in range(W):
            if y > 34 or (y > 26 and (x + y) % 2):
                t.punto(x, y, VI_BLU)
            if y > 70 or (y > 62 and (x + y) % 2):
                t.punto(x, y, VI_AZZURRO)
    for x0 in range(0, W, 128):
        t.ellisse(x0 + 30, 14, 7, 7, VI_CHIARO)
    piombi(t, VI_PIOMBO, (16, 14), sfasa=1)
    return t, PALETTE_VISIONE, True


def c6_parete(m):
    """La parete lontana della gola con gli archi dell'acquedotto che corrono a mezza costa."""
    t = Tela(W, H)
    for x in range(W):
        top = 26 + int(10 * math.sin(x / 37.0) + 4 * math.sin(x / 11.0 + 2))
        for y in range(top, QUADRO):
            t.punto(x, y, VI_ROCCIA_S)
    for x in range(0, W, 24):                                                     # l'acquedotto
        t.rett(x, 50, 24, 4, VI_ROCCIA)
        t.rett(x + 2, 54, 4, 30, VI_ROCCIA)
        for y in range(54, 62):
            for xx in range(x + 6, x + 24):
                if (xx + 0.5 - (x + 15)) ** 2 + (y + 0.5 - 63) ** 2 > 80:
                    t.punto(xx, y, VI_ROCCIA)
    piombi(t, VI_PIOMBO, (16, 13), sfasa=3)
    return t, PALETTE_VISIONE, True


def c6_sentiero(m):
    """In basso il sentiero sul fondo della gola, i massi, i ciuffi verdi; a tratti la parete vicina."""
    t = Tela(W, H)
    for x in range(W):
        for y in range(92 + int(2 * math.sin(x / 19.0)), QUADRO):
            t.punto(x, y, VI_ROCCIA if y < 98 else VI_ROCCIA_S)
    r = random.Random(6)
    for _ in range(14):
        cx = r.randrange(W)
        t.ellisse(cx, 93, r.randint(5, 9), r.randint(3, 5), VI_VERDE if r.random() < 0.5 else VI_VERDE_S)
    for x0 in (60, 300):                                                          # la parete vicina
        poligono(t, [(x0, QUADRO), (x0 + 4, 40), (x0 + 16, 0), (x0 + 40, 0), (x0 + 46, QUADRO)], VI_ROCCIA_S)
    piombi(t, VI_PIOMBO, (16, 12), sfasa=5)
    return t, PALETTE_VISIONE, True


def uomo_di_ferro(t, x, base, gigante=False):
    """Un fante in ferro che va a sinistra: elmo, corpo, scudo; le gambe di una posa nel 13 e
    dell'altra nel 14 (il passo le alterna). Il gigante (Corrado) e' alto il doppio, col martello."""
    k = 2 if gigante else 1
    t.rett(x, base - 14 * k, 5 * k, 4 * k, VI_FERRO_C)                        # elmo
    t.rett(x - k, base - 10 * k, 7 * k, 6 * k, VI_FERRO)                      # corpo
    t.rett(x - 2 * k, base - 9 * k, 3 * k, 5 * k, VI_ROSSO)                   # lo scudo
    t.rett(x, base - 4 * k, k, 4 * k, VI_GAMBE_A)
    t.rett(x + 3 * k, base - 4 * k, k, 4 * k, VI_GAMBE_A)
    t.rett(x + k, base - 4 * k, k, 4 * k, VI_GAMBE_B)
    t.rett(x + 2 * k, base - 4 * k, k, 4 * k, VI_GAMBE_B)
    if gigante:
        t.linea(x + 10, base - 18, x + 18, base - 34, VI_FERRO_C, 2)          # il manico
        t.rett(x + 13, base - 40, 10, 7, VI_FERRO)                            # il martello
        t.rett(x + 13, base - 40, 10, 2, VI_FERRO_C)
    else:
        t.linea(x + 5, base - 9, x - 3, base - 22, VI_FERRO_C)                # la lancia
        t.punto(x - 3, base - 23, VI_CHIARO)


def c6_fanti(m):
    t = Tela(W, H)
    # la fila sul fondo della gola. Il 14 ha il colore della roccia del sentiero (c6_sentiero), come
    # in pittore_c2 il 14 ha quello del prato: le gambe della posa che non c'e' spariscono
    for i, x in enumerate(range(20, 420, 22)):
        uomo_di_ferro(t, x + (i % 2) * 3, 97 - (i % 2))
    uomo_di_ferro(t, 450, 99, gigante=True)
    contorna(t, VI_PIOMBO)
    return t, PALETTE_VISIONE_FANTI, True


def c6_corrado(m):
    """Il primo piano nel vetro: il gigante di ferro col martello sull'arco dell'acquedotto; il colpo
    del motore (lampo e scossa a 0,5 s) e' il martello che cade, le crepe ci sono gia'."""
    t = Tela(W, H, VI_NOTTE)
    for y in range(QUADRO):
        for x in range(W):
            if y > 50 or (y > 42 and (x + y) % 2):
                t.punto(x, y, VI_BLU)
    t.ellisse(36, 20, 9, 9, VI_CHIARO)
    t.rett(140, 30, 110, 12, VI_ROCCIA)                                           # l'arco
    for (a, b) in ((140, 156), (196, 212)):
        t.rett(a, 42, b - a, 70, VI_ROCCIA)
    for y in range(42, 70):
        for x in range(156, 196):
            if (x + 0.5 - 176) ** 2 + (y + 0.5 - 70) ** 2 > 400:
                t.punto(x, y, VI_ROCCIA)
    t.rett(156, 30, 1, 82, VI_ROCCIA_S)
    for k, (dx, dy) in enumerate(((0, 0), (-4, 5), (3, 9), (-2, 14), (5, 18))):    # le crepe
        t.linea(146 + dx, 32 + dy, 148 + dx + (k % 2) * 4, 38 + dy, VI_PIOMBO)
    poligono(t, [(70, 112), (74, 64), (86, 50), (112, 50), (122, 64), (126, 112)], VI_FERRO_S)
    poligono(t, [(98, 50), (112, 50), (122, 64), (126, 112), (108, 112)], VI_FERRO)
    t.ellisse(98, 40, 11, 12, VI_FERRO)                                           # l'elmo
    t.ellisse(94, 36, 5, 5, VI_FERRO_C)
    t.rett(90, 40, 16, 3, VI_PIOMBO)                                              # la feritoia
    poligono(t, [(80, 72), (76, 100), (98, 106), (100, 74)], VI_ROSSO)            # lo scudo
    t.linea(118, 58, 138, 40, VI_FERRO, 5)                                        # il braccio
    poligono(t, [(130, 24), (148, 28), (144, 48), (126, 44)], VI_FERRO)           # il martello
    poligono(t, [(130, 24), (148, 28), (147, 32), (129, 29)], VI_FERRO_C)
    for d in range(3, 12, 2):                                                     # le schegge
        for a in (-0.9, -0.4, 0.1, 0.6, 1.1):
            t.punto(150 + d * math.cos(a), 36 + d * math.sin(a), VI_ORO)
    piombi(t, VI_PIOMBO, (16, 15), sfasa=2)
    return t, PALETTE_VISIONE, True


# la fila in ferro sale: le gambe nei colori 13 e 14 si scambiano (src/regia.cpp)
CON_PASSO = {"c6_fanti"}
PITTORI = {"c6_vetro_scuro": c6_vetro_scuro, "c6_cielo": c6_cielo, "c6_parete": c6_parete,
           "c6_sentiero": c6_sentiero, "c6_fanti": c6_fanti, "c6_corrado": c6_corrado}
