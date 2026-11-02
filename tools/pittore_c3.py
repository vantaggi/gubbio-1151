"""I piani di C3, le presentazioni a fermo immagine (proposta approvata): Ubaldo e Giorgio in A1-01,
Antonio in A1-04, Corrado in B-04. Il personaggio in controluce, una sagoma scura col bordo acceso
dall'oro, davanti a un bagliore caldo che si spegne verso i margini; in basso a sinistra il cartiglio
vermiglio col nome (le due righe le dice il narratore nelle bande, testi/regia.testi).

Le sagome sono disegnate alla loro misura (niente pixel ingranditi). I nomi sono quelli dei cartigli
del copione (tools/genera_storia.py, PARLANTI).
"""
import math

from genera_battaglia import Tela

W, H = 512, 256
QUADRO = 112

PALETTE_RITRATTO = [("neutri", 0), ("neutri", 0), ("legno e cuoio", 0), ("oro e bronzo", 3), ("oro e bronzo", 2),
                    ("cotto e coppi", 5), ("cotto e coppi", 4), ("cotto e coppi", 3), ("vermiglio comunale", 2),
                    ("vermiglio comunale", 1), ("neutri", 4), ("legno e cuoio", 1), ("pelle", 2), ("cotto e coppi", 2),
                    ("vermiglio comunale", 3), ("neutri", 1)]
R_SAGOMA, R_SAGOMA_S, R_BORDO, R_ORO_S = 1, 2, 3, 4
R_CARTIGLIO, R_CARTIGLIO_S, R_NOME, R_FILO, R_CUORE = 8, 9, 10, 11, 12
ANELLI = [(18, 12), (30, 5), (44, 6), (60, 7), (80, 14), (999, 13)]      # (raggio, colore) dal centro
CENTRO = (150, 52)
SUOLO = 100

# il nome nel cartiglio: quello del copione (PARLANTI di tools/genera_storia.py)
NOMI = {"ubaldo": "Sant'Ubaldo", "giorgio": "Giorgio", "antonio": "Antonio", "corrado": "Corrado di Spoleto"}


def bagliore(t):
    """Il controluce: anelli caldi dal centro dietro la figura verso i margini, a scacchiera sui bordi;
    in basso la linea scura del terreno."""
    cx, cy = CENTRO
    for y in range(QUADRO):
        for x in range(W):
            d = math.hypot((x - cx) * 0.8, y - cy)
            for k, (raggio, colore) in enumerate(ANELLI):
                if d < raggio:
                    vicino = k + 1 < len(ANELLI) and raggio - d < 2 and (x + y) % 2
                    t.punto(x, y, ANELLI[k + 1][1] if vicino else colore)
                    break
    for y in range(SUOLO, QUADRO):
        t.rett(0, y, W, 1, R_SAGOMA)


def bordo_di_luce(t, figura):
    """Il bordo acceso: i pixel della figura che toccano lo sfondo dalla parte del bagliore."""
    cx, cy = CENTRO
    accesi = []
    for (x, y) in figura:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in figura and y + dy < SUOLO:
                if math.hypot(x + dx - cx, y + dy - cy) < math.hypot(x - cx, y - cy) + 0.5:
                    accesi.append((x, y))
                    break
    for x, y in accesi:
        t.punto(x, y, R_BORDO)


class Sagoma:
    """Una figura disegnata in un colore solo; alla fine prende il bordo di luce."""

    def __init__(self):
        self.t = Tela(W, H)

    def __getattr__(self, nome):
        return getattr(self.t, nome)

    def pixel(self):
        return {(x, y) for y in range(QUADRO) for x in range(W) if self.t.px[y][x]}


def cartiglio(t, nome):
    """Il cartiglio vermiglio col nome, arrotolato alle due estremita'."""
    import pittore_panorami as PP
    largo = PP.larghezza(nome) + 16
    x0, y0, alto = 14, 76, 18
    t.rett(x0, y0, largo, alto, R_CARTIGLIO)
    t.rett(x0, y0 + alto - 2, largo, 2, R_CARTIGLIO_S)
    t.rett(x0, y0 - 1, largo, 1, R_FILO)
    t.rett(x0, y0 + alto, largo, 1, R_FILO)
    for ex in (x0 - 3, x0 + largo):
        t.ellisse(ex + 1.5, y0 + alto / 2, 3, alto / 2 + 1, R_FILO)
        t.ellisse(ex + 1.5, y0 + alto / 2, 2, alto / 2, R_CARTIGLIO_S)
        t.rett(ex + 1, y0 + 2, 1, alto - 4, R_FILO)
    PP.scrivi(t, x0 + 8, y0 + 4, nome, R_NOME)
    return (x0, y0, largo, alto)


def ubaldo(s):
    """Il vescovo di profilo verso sinistra: la mitra a due punte con le infule, la testa canuta con la
    barba corta, il piviale largo, il pastorale col riccio in cima."""
    cx = 152
    s.trapezio(cx, 40, SUOLO, 26, 46, R_SAGOMA)
    s.ellisse(cx, 46, 15, 7, R_SAGOMA)                       # le spalle sotto il piviale
    s.ellisse(cx - 2, 32, 7, 8, R_SAGOMA)
    s.rett(cx - 11, 32, 3, 2, R_SAGOMA)                      # il naso
    s.trapezio(cx - 5, 38, 46, 8, 5, R_SAGOMA)               # la barba
    s.trapezio(cx - 2, 10, 26, 2, 14, R_SAGOMA)              # la mitra
    s.rett(cx + 4, 25, 2, 18, R_SAGOMA)                      # le infule
    s.rett(cx + 7, 25, 2, 15, R_SAGOMA)
    s.rett(cx - 26, 52, 14, 5, R_SAGOMA)                     # il braccio
    s.rett(cx - 26, 16, 3, SUOLO - 16, R_SAGOMA)             # il pastorale
    for a in range(0, 300, 6):
        r = math.radians(a + 150)
        s.rett(cx - 21 + 6 * math.cos(r), 12 + 6 * math.sin(r), 2, 2, R_SAGOMA)
    t = s.t
    t.rett(cx - 2, 10, 1, 5, 0)                              # la fessura fra le due punte della mitra
    return t


def giorgio(s):
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


def antonio(s):
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


def fiamma(t, x, y):
    """La fiamma nella mano di Antonio: il cuore pallido, l'oro, l'alone cotto."""
    t.ellisse(x, y, 5, 8, 6)
    t.ellisse(x, y + 1, 3, 6, R_BORDO)
    t.ellisse(x, y + 2, 1.5, 3, R_CUORE)
    t.rett(x, y - 10, 1, 3, R_BORDO)


def corrado(s):
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


def ritratto(chi, disegno):
    t = Tela(W, H)
    bagliore(t)
    s = Sagoma()
    disegno(s)
    figura = s.pixel()
    for (x, y) in figura:
        t.punto(x, y, R_SAGOMA)
    bordo_di_luce(t, figura)
    if chi == "corrado":
        t.rett(150, 18, 10, 2, 5)                            # la feritoia dell'elmo, accesa dal bagliore
    if chi == "antonio":
        fiamma(t, 126, 52)
    cartiglio(t, NOMI[chi])
    return t


def ritratto_ubaldo(momento):
    return ritratto("ubaldo", ubaldo), PALETTE_RITRATTO, False


def ritratto_giorgio(momento):
    return ritratto("giorgio", giorgio), PALETTE_RITRATTO, False


def ritratto_antonio(momento):
    return ritratto("antonio", antonio), PALETTE_RITRATTO, False


def ritratto_corrado(momento):
    return ritratto("corrado", corrado), PALETTE_RITRATTO, False


PITTORI = {"ritratto_ubaldo": ritratto_ubaldo, "ritratto_giorgio": ritratto_giorgio,
           "ritratto_antonio": ritratto_antonio, "ritratto_corrado": ritratto_corrado}
