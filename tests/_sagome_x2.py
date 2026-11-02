"""Le sagome di C3 com'erano in X2, a blocchi: le negative dei test di X3 (tests/test_regia.py). Non
servono al gioco, solo a provare che la misura dei dettagli le distingue dalle nuove."""
import math  # noqa: F401

R_SAGOMA = 1
SUOLO = 100


def giorgio_a_blocchi(s):
    """Il giovane cavaliere in avanti: la spada alzata, lo scudo a mandorla, il mantello nel vento, i
    capelli senza elmo."""
    cx = 150
    s.linea(cx - 4, 72, cx - 14, SUOLO - 1, R_SAGOMA, 6)    # le gambe
    s.linea(cx + 4, 72, cx + 14, SUOLO - 1, R_SAGOMA, 6)
    s.trapezio(cx, 40, 76, 16, 22, R_SAGOMA)                 # la tunica
    s.ellisse(cx, 30, 7, 8, R_SAGOMA)
    for k in range(4):
        s.linea(cx + 2 + k, 22 + k, cx + 9 + k * 2, 18 + k * 3, R_SAGOMA)   # i capelli al vento
    s.linea(cx - 7, 44, cx - 20, 30, R_SAGOMA, 4)            # il braccio alzato
    s.linea(cx - 21, 30, cx - 42, 2, R_SAGOMA, 2)            # la lama
    s.linea(cx - 27, 26, cx - 16, 34, R_SAGOMA, 2)           # l'elsa
    s.trapezio(cx + 15, 44, 74, 16, 2, R_SAGOMA)             # lo scudo a mandorla
    for k in range(30):
        s.rett(cx + 6, 40 + k, 6 + k, 1, R_SAGOMA)           # il mantello
    return s.t

def corrado_a_blocchi(s):
    """Il Colosso delle Forge: il doppio di un uomo, l'elmo chiuso con la feritoia accesa, gli spallacci,
    il martello enorme sulla spalla."""
    cx = 156
    s.rett(cx - 18, 72, 13, SUOLO - 72, R_SAGOMA)            # le gambe
    s.rett(cx + 5, 72, 13, SUOLO - 72, R_SAGOMA)
    s.trapezio(cx, 30, 76, 50, 38, R_SAGOMA)                 # il busto corazzato
    s.ellisse(cx - 24, 34, 9, 7, R_SAGOMA)                   # gli spallacci
    s.ellisse(cx + 24, 34, 9, 7, R_SAGOMA)
    s.rett(cx - 8, 10, 17, 22, R_SAGOMA)                     # l'elmo
    s.trapezio(cx, 6, 11, 8, 17, R_SAGOMA)
    s.linea(cx - 30, 62, cx + 22, 12, R_SAGOMA, 4)           # il manico del martello
    s.rett(cx + 14, 2, 24, 16, R_SAGOMA)                     # la testa del martello
    s.rett(cx + 12, 5, 2, 10, R_SAGOMA)
    s.linea(cx - 24, 38, cx - 30, 60, R_SAGOMA, 8)           # il braccio che regge il manico
    s.ellisse(cx - 30, 62, 5, 4, R_SAGOMA)                   # il pugno
    return s.t

def antonio_a_blocchi(s):
    """L'eremita curvo nel saio col cappuccio, la barba lunga, il bastone a tau, la fiamma accesa nella
    mano (il fuoco e' luce, non sagoma) e il maialino ai piedi."""
    cx = 146
    for y in range(36, SUOLO):
        largo = 20 + (y - 36) * 14 // 64
        s.rett(cx - largo // 2 + (100 - y) // 16, y, largo, 1, R_SAGOMA)
    s.ellisse(cx + 2, 30, 9, 9, R_SAGOMA)                    # il cappuccio
    s.trapezio(cx + 10, 26, 40, 2, 6, R_SAGOMA)
    s.trapezio(cx - 5, 34, 52, 8, 3, R_SAGOMA)               # la barba
    s.rett(cx - 24, 22, 3, SUOLO - 22, R_SAGOMA)             # il bastone a tau
    s.rett(cx - 29, 20, 13, 3, R_SAGOMA)
    s.linea(cx - 4, 50, cx - 16, 58, R_SAGOMA, 4)            # il braccio verso la fiamma
    s.ellisse(cx + 30, 92, 12, 7, R_SAGOMA)                  # il maialino
    s.rett(cx + 16, 90, 5, 4, R_SAGOMA)
    s.rett(cx + 22, 84, 3, 3, R_SAGOMA)
    for gx in (cx + 22, cx + 27, cx + 34, cx + 38):
        s.rett(gx, 97, 2, 3, R_SAGOMA)
    s.rett(cx + 42, 88, 2, 2, R_SAGOMA)
    t = s.t
    return t
