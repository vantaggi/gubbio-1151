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
NOMI = {"ubaldo": "Ubaldo", "giorgio": "Giorgio", "antonio": "Antonio", "corrado": "Corrado di Spoleto"}


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

    def poligono(self, punti, colore=R_SAGOMA):
        """Riempie il poligono (lista di vertici) a scansione di riga: il contorno segue i vertici."""
        ys = [y for _, y in punti]
        for y in range(int(min(ys)), int(max(ys)) + 1):
            yc = y + 0.5
            xs = []
            for (x0, y0), (x1, y1) in zip(punti, punti[1:] + punti[:1]):
                if (y0 <= yc < y1) or (y1 <= yc < y0):
                    xs.append(x0 + (yc - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for a, b in zip(xs[::2], xs[1::2]):
                for x in range(int(round(a)), int(round(b))):
                    self.t.punto(x, y, colore)

    def asta(self, x0, y0, x1, y1, spessore_0, spessore_1=None):
        """Un pezzo dritto (braccio, lama, manico) da (x0, y0) a (x1, y1), largo spessore_0 in partenza
        e spessore_1 in arrivo."""
        spessore_1 = spessore_0 if spessore_1 is None else spessore_1
        dx, dy = x1 - x0, y1 - y0
        n = math.hypot(dx, dy) or 1
        px, py = -dy / n, dx / n
        self.poligono([(x0 + px * spessore_0 / 2, y0 + py * spessore_0 / 2), (x1 + px * spessore_1 / 2, y1 + py * spessore_1 / 2),
                       (x1 - px * spessore_1 / 2, y1 - py * spessore_1 / 2), (x0 - px * spessore_0 / 2, y0 - py * spessore_0 / 2)])

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
    """Il giovane cavaliere, sei teste d'altezza: l'elmo a cono col nasale, la cotta di maglia che si
    allarga ai fianchi con l'orlo frastagliato, le gambe divaricate col peso sulla destra (la sinistra
    piegata al ginocchio), il braccio con spalla e gomito che alza la spada larga con l'elsa e la
    guardia a croce, lo scudo a mandorla avanti sull'altro braccio, il mantello che svolazza in tre pieghe."""
    # il mantello, dietro a tutto
    s.poligono([(154, 37), (170, 33), (184, 38), (180, 44), (192, 50), (186, 56), (196, 64), (184, 64), (188, 74),
                (174, 70), (164, 62)])
    # le gambe: la destra dritta col peso, la sinistra avanti piegata
    s.poligono([(152, 70), (161, 70), (165, 84), (168, 97), (174, 100), (160, 100), (161, 97), (157, 85)])
    s.poligono([(141, 70), (151, 72), (141, 85), (133, 97), (135, 100), (121, 100), (126, 97), (134, 84), (136, 78)])
    # la cotta: spalle, vita, fianchi larghi, l'orlo a denti
    s.poligono([(139, 37), (159, 37), (161, 46), (157, 58), (164, 70), (161, 73), (158, 70), (155, 73), (152, 70),
                (149, 73), (146, 70), (143, 73), (140, 70), (136, 72), (142, 58), (138, 46)])
    s.rett(141, 57, 17, 2, R_SAGOMA)                         # la cintura sporge un poco
    # il collo, la testa, l'elmo a cono col nasale
    s.rett(146, 32, 7, 6, R_SAGOMA)
    s.poligono([(143, 23), (155, 23), (155, 30), (152, 33), (146, 33), (143, 30), (141, 27)])
    s.poligono([(149, 9), (157, 21), (157, 24), (141, 24), (141, 21)])
    s.rett(142, 24, 2, 5, R_SAGOMA)                          # il nasale
    # il braccio della spada: spalla, gomito, mano in alto
    s.asta(142, 40, 131, 36, 7, 5)
    s.asta(131, 36, 127, 24, 5, 4)
    # la spada: il pomo, l'impugnatura, la guardia a croce, la lama larga che si assottiglia
    gx, gy = 126, 22                                          # la mano sulla guardia
    dx, dy = -0.62, -0.78                                     # verso la punta
    s.asta(gx - dx * 6, gy - dy * 6, gx, gy, 3)               # l'impugnatura
    s.ellisse(gx - dx * 7, gy - dy * 7, 2, 2, R_SAGOMA)       # il pomo
    s.asta(gx + dy * 6, gy - dx * 6, gx - dy * 6, gy + dx * 6, 3)    # la guardia a croce
    s.asta(gx + dx * 2, gy + dy * 2, gx + dx * 26, gy + dy * 26, 4, 1)   # la lama
    # lo scudo a mandorla sull'altro braccio, portato avanti: esce dal contorno della cotta
    s.poligono([(122, 46), (137, 43), (140, 55), (131, 75), (123, 59)])


def antonio(s):
    """L'eremita curvo nel saio col cappuccio, la barba lunga, il bastone a tau, il braccio verso la
    fiamma accesa nella mano (il fuoco e' luce, non sagoma); ai piedi il maialino in piedi, di profilo
    verso di lui: il grugno, l'orecchio a punta, quattro zampette, la coda a ricciolo."""
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
    # il maialino, staccato dal saio
    s.ellisse(186, 89, 11, 6, R_SAGOMA)                      # il corpo
    s.ellisse(174, 88, 5, 5, R_SAGOMA)                       # la testa
    s.poligono([(170, 86), (166, 87), (165, 91), (170, 92)])  # il grugno
    s.rett(164, 87, 2, 4, R_SAGOMA)                          # il disco del grugno
    s.poligono([(173, 84), (176, 77), (178, 85)])            # l'orecchio a punta
    for zx in (177, 181, 190, 194):
        s.rett(zx, 94, 2, 6, R_SAGOMA)                       # le quattro zampette
    for x, y in ((197, 88), (198, 87), (199, 86), (200, 86), (201, 87), (201, 88), (200, 89), (199, 88)):
        s.punto(x, y, R_SAGOMA)                              # la coda a ricciolo


def fiamma(t, x, y):
    """La fiamma nella mano di Antonio: il cuore pallido, l'oro, l'alone cotto."""
    t.ellisse(x, y, 5, 8, 6)
    t.ellisse(x, y + 1, 3, 6, R_BORDO)
    t.ellisse(x, y + 2, 1.5, 3, R_CUORE)
    t.rett(x, y - 10, 1, 3, R_BORDO)


def corrado(s):
    """Il Colosso delle Forge in armatura del XII secolo: l'elmo a cilindro (la feritoia la accende il
    bagliore), gli spallacci tondi sovrapposti, la cotta di maglia che scende in una gonna a denti, la
    cintura, le gambe massicce col ginocchio, il mantello strappato dietro e il martello da guerra a
    manico lungo sulla spalla, con la testa a blocco e la punta."""
    # il mantello strappato, dietro
    s.poligono([(170, 34), (190, 44), (198, 66), (200, 92), (195, 86), (191, 97), (186, 88), (181, 98), (177, 84),
                (172, 70)])
    # le gambe col ginocchio
    for x0 in (140, 159):
        s.poligono([(x0, 78), (x0 + 13, 78), (x0 + 14, 86), (x0 + 12, 90), (x0 + 13, 97), (x0 + 16, 100), (x0 - 2, 100),
                    (x0 + 1, 97), (x0, 90), (x0 - 2, 86)])
    # la gonna di maglia a denti e la cintura
    gonna = [(140, 64), (174, 64), (180, 80)]
    for k in range(10):
        gonna.append((180 - k * 5.2, 84 if k % 2 == 0 else 79))
    s.poligono(gonna + [(134, 80)])
    s.rett(137, 61, 40, 4, R_SAGOMA)
    # il busto
    s.poligono([(134, 34), (180, 34), (176, 50), (172, 62), (142, 62), (138, 50)])
    # gli spallacci sovrapposti
    for cx, verso in ((134, -1), (180, 1)):
        s.ellisse(cx, 34, 11, 8, R_SAGOMA)
        s.ellisse(cx + verso * 3, 42, 10, 6, R_SAGOMA)
        s.ellisse(cx + verso * 5, 48, 8, 4, R_SAGOMA)
    # l'elmo a cilindro, il cimiero basso
    s.poligono([(148, 10), (151, 7), (163, 7), (166, 10), (166, 31), (148, 31)])
    s.rett(153, 4, 8, 3, R_SAGOMA)
    # il braccio che regge il martello: spalla, gomito, pugno
    s.asta(130, 44, 124, 60, 9, 8)
    s.asta(124, 60, 134, 70, 8, 7)
    s.ellisse(135, 70, 5, 4, R_SAGOMA)
    # l'altro braccio lungo il fianco
    s.asta(184, 46, 188, 62, 8, 7)
    s.ellisse(188, 65, 4, 4, R_SAGOMA)
    # il martello da guerra: il manico lungo dal pugno oltre la spalla, la testa a blocco con la punta
    s.asta(136, 74, 182, 14, 3)
    hx, hy = 184, 11                                          # dove il manico entra nella testa
    dx, dy = 0.61, -0.79                                      # lungo il manico
    px, py = 0.79, 0.61                                       # di traverso
    s.poligono([(hx + px * 9 - dx * 5, hy + py * 9 - dy * 5), (hx + px * 9 + dx * 5, hy + py * 9 + dy * 5),
                (hx - px * 6 + dx * 4, hy - py * 6 + dy * 4), (hx - px * 15 + dx * 1, hy - py * 15 + dy * 1),
                (hx - px * 6 - dx * 4, hy - py * 6 - dy * 4)])


# La sagoma dei protagonisti e' il controluce della loro figura a colori (figura_luce), pixel per pixel:
# Cioti (5 nov 2026) vedeva una "doppia sagoma", perche' il controluce disegnato a parte aveva un'altra posa
# e un altro profilo della figura che compare subito dopo. Ora lo stacco accende la stessa forma. La fiamma di
# Antonio resta accesa anche nel controluce (il fuoco e' luce, non sagoma).
FIAMMA_ACCESA = {("vermiglio comunale", 2): 6, ("oro e bronzo", 2): R_ORO_S, ("oro e bronzo", 3): R_BORDO}
FIAMMA_X_MAX = 128          # la fiamma sta nella mano tesa, a sinistra del bastone


def sagoma_dalla_luce(chi):
    """I pixel della figura a colori (figura e, per Antonio, il maialino) e quelli della fiamma accesa."""
    tf, palette = figura_luce(chi)
    figura, accesi = set(), {}
    for y, riga in enumerate(tf.px):
        for x, c in enumerate(riga):
            if c:
                figura.add((x, y))
                if chi == "antonio" and x < FIAMMA_X_MAX and palette[c] in FIAMMA_ACCESA:
                    accesi[(x, y)] = FIAMMA_ACCESA[palette[c]]
    return figura, accesi


def ritratto(chi, disegno):
    t = Tela(W, H)
    bagliore(t)
    accesi = {}
    if chi in POSA_LUCE:
        figura, accesi = sagoma_dalla_luce(chi)
    else:
        s = Sagoma()
        disegno(s)
        figura = s.pixel()
    for (x, y) in figura:
        t.punto(x, y, R_SAGOMA)
    bordo_di_luce(t, figura)
    for (x, y), c in accesi.items():
        t.punto(x, y, c)
    if chi == "corrado":
        t.rett(150, 18, 10, 2, 5)                            # la feritoia dell'elmo, accesa dal bagliore
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


# --- la luce (pezzo SAG): dopo la sagoma, lo stacco sul protagonista vero, a colori -----------------
# Cioti (4 nov 2026): le cutscene sono belle ma i protagonisti non si vedono mai. Dopo il controluce
# un secondo fermo immagine: lo stesso bagliore, il cartiglio, e davanti la figura a colori, la stessa
# della battaglia (tools/sagome_battaglia.py) ridisegnata tre volte piu' grande. Guarda a sinistra come
# la sagoma. Due piani: il bagliore col cartiglio (palette del ritratto) e la figura (palette sua).
SCALA_LUCE = 3


def sfondo_luce(chi):
    t = Tela(W, H)
    bagliore(t)
    cartiglio(t, NOMI[chi])
    return t


# La posa a colori ripete il gesto della sagoma: Giorgio con la spada levata, Antonio con la fiamma in mano
# e il maialino ai piedi, Ubaldo col pastorale (giro 4 del loop grafico: prima tutti e tre stavano a riposo e
# lo stacco non somigliava al controluce).
POSA_LUCE = {"ubaldo": "riposo", "giorgio": "potere", "antonio": "colpo"}


def maialino(t, x0, y0, indici):
    """Il maialino di Antonio a colori, di profilo verso sinistra come nella sagoma: il corpo rosa con la luce
    in alto a sinistra, il grugno, l'orecchio, quattro zampette, la coda a ricciolo; il contorno quasi nero."""
    ombra, base, luce = indici
    pieni = {}

    def tinta(x, y, c):
        pieni[(x, y)] = c

    for y in range(-6, 7):                                  # il corpo
        for x in range(-11, 12):
            if (x / 11) ** 2 + (y / 6) ** 2 <= 1:
                tinta(x0 + x, y0 + y, luce if x + y < -6 else (ombra if y > 3 or x > 8 else base))
    for y in range(-5, 6):                                  # la testa
        for x in range(-5, 6):
            if x * x + y * y <= 25:
                tinta(x0 - 12 + x, y0 - 1 + y, luce if x + y < -3 else base)
    for y in range(-2, 3):                                  # il grugno
        for x in range(-4, 0):
            tinta(x0 - 16 + x, y0 + y, base if x > -4 else ombra)
    for k in range(5):                                      # l'orecchio a punta
        for x in range(k // 2 + 1):
            tinta(x0 - 12 + x, y0 - 6 - k, base)
    for zx in (-9, -5, 4, 8):                               # le zampette
        for y in range(5, 11):
            tinta(x0 + zx, y0 + y, ombra if zx > 0 else base)
            tinta(x0 + zx + 1, y0 + y, ombra)
    for x, y in ((12, -1), (13, -2), (14, -3), (15, -3), (16, -2), (16, -1), (15, 0)):
        tinta(x0 + x, y0 + y, base)                          # la coda a ricciolo
    for (x, y), c in pieni.items():
        t.punto(x, y, c)
    for (x, y) in pieni:                                    # il contorno
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in pieni:
                t.punto(x + dx, y + dy, 1)
    t.punto(x0 - 14, y0 - 3, 1)                             # l'occhio
    t.punto(x0 - 19, y0, ombra)                             # la narice


def figura_luce(chi):
    """La figura a colori sul suo piano trasparente, coi piedi sul terreno della sagoma e il centro
    sul bagliore; torna (tela, palette)."""
    import sagome_battaglia as SB
    f = getattr(SB, chi)(POSA_LUCE[chi], SCALA_LUCE)
    px = [list(reversed(r)) for r in f.pixel()]           # a sinistra, come la sagoma
    piedi = max(y for y, r in enumerate(px) if any(r))
    largo = [x for r in px for x, c in enumerate(r) if c]
    centro = (min(largo) + max(largo)) // 2
    t = Tela(W, H)
    ox, oy = CENTRO[0] - centro, SUOLO - 1 - piedi
    for y, riga in enumerate(px):
        for x, c in enumerate(riga):
            if c:
                t.punto(ox + x, oy + y, c)
    if chi == "antonio":
        # il rosa dalla palette di Antonio: l'ombra nel cotto, la base e la luce nella pelle
        rosa = [f.palette.index(rif) for rif in (("cotto e coppi", 3), ("pelle", 1), ("pelle", 2))]
        maialino(t, 190, SUOLO - 12, rosa)
    return t, f.palette


def luce(chi):
    return {f"ritratto_{chi}_sfondo": lambda momento: (sfondo_luce(chi), PALETTE_RITRATTO, False),
            f"ritratto_{chi}_luce": lambda momento: (*figura_luce(chi), False)}


PITTORI = {"ritratto_ubaldo": ritratto_ubaldo, "ritratto_giorgio": ritratto_giorgio,
           "ritratto_antonio": ritratto_antonio, "ritratto_corrado": ritratto_corrado}
for _chi in ("ubaldo", "giorgio", "antonio"):
    PITTORI.update(luce(_chi))
