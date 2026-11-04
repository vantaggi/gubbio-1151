#!/usr/bin/env python3
"""Le sagome della battaglia (pezzo SAG): i tre protagonisti e i nemici ridisegnati con volume e pose vere.

Le figure di prima (tools/genera_battaglia.py, prima di SAG) erano forme piatte con due pose: ferma e in
azione. Qui ogni figura nasce da uno scheletro (la Guida di stile, scelta 11: testa, collo, bacino, mani,
piedi) messo in posa, e da parti piene (veste, braccia, testa, arma) disegnate sopra lo scheletro. Poi tre
passate, sempre le stesse per tutti:

1. l'ombreggiatura: ogni parte ha tre toni della sua rampa (luce, base, ombra); la luce viene da sinistra
   (Guida, scelta 4): il bordo sinistro e quello in alto di ogni parte prendono la luce, i due pixel del
   bordo destro e l'ultima riga l'ombra;
2. la separazione: dove una parte sta sopra un'altra, la parte di sotto si scurisce lungo il confine (si
   legge il braccio davanti alla veste anche senza una linea nera);
3. il contorno quasi nero intorno alla sagoma (Guida, scelta 5).

Le pose, in quest'ordine in ogni figura (POSE): riposo e respiro (il ciclo di attesa, 2 x 30 vblank come
pose.json), anticipazione, colpo, colpito, potere (le braccia levate: abilita' e oggetti), caduto.

Ogni figura ha la sua palette di 16 colori (16 palette di sprite sul GBA: ne bastano 10), tutti dalla
Guida di stile. I disegni non usano foto ne' derivati: solo forme e la palette.

    python tools/sagome_battaglia.py tavola.png     # la tavola di controllo (serve Pillow)
"""
import math
import os
import sys

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RADICE, "stile"))

POSE = ("riposo", "respiro", "anticipa", "colpo", "colpito", "potere", "caduto")
POSA = {nome: i for i, nome in enumerate(POSE)}

TRASPARENTE, CONTORNO = 0, 1


# --- i materiali: tre toni (ombra, base, luce) da una rampa della Guida -------------------------------
class Materiale:
    def __init__(self, nome, ombra, base, luce):
        self.nome = nome
        self.toni = (ombra, base, luce)       # riferimenti (rampa, tono) della Guida


def palette_di(materiali, extra=()):
    """La palette di una figura: 0 trasparente, 1 contorno, poi i tre toni di ogni materiale, poi i
    colori singoli (emblemi). Un colore gia' presente si riusa (il quasi nero e' il contorno). Torna
    (lista dei riferimenti, {materiale: (i_ombra, i_base, i_luce)}, {singolo: indice})."""
    pal = [("neutri", 0), ("neutri", 0)]

    def posto(rif):
        if rif == ("neutri", 0):
            return CONTORNO
        if rif in pal[2:]:
            return pal.index(rif, 2)
        pal.append(rif)
        return len(pal) - 1

    indici = {m.nome: tuple(posto(r) for r in m.toni) for m in materiali}
    singoli = {nome: posto(rif) for nome, rif in extra}
    if len(pal) > 16:
        raise ValueError(f"palette di {len(pal)} colori: al massimo 16")
    pal += [("neutri", 0)] * (16 - len(pal))
    return pal, indici, singoli


# --- la tela a parti ---------------------------------------------------------------------------------
class Figura:
    """Una tela dove ogni pixel ricorda la parte che l'ha dipinto (per ombreggiare e separare) e, alla
    fine, l'indice di palette."""

    def __init__(self, lato, palette, indici, singoli, k=1):
        """k: la scala (1 in battaglia; 2 o 3 per le cutscene). Le coordinate dei disegni restano quelle
        dello sprite 32x32: la tela le moltiplica per k e riempie i pixel alla sua misura, cosi' le
        forme si ridisegnano piu' grandi (niente pixel ingranditi) e il contorno resta di un pixel."""
        self.k = k
        lato = int(lato * k)
        self.w = self.h = lato
        self.parte = [[None] * lato for _ in range(lato)]
        self.materiale = {}
        self.ordine = []
        self.palette, self.indici, self.singoli = palette, indici, singoli
        self.dettagli = []          # (x, y, indice) dipinti dopo l'ombreggiatura
        self.corrente = None

    # le parti
    def parte_nuova(self, nome, materiale):
        nome = f"{nome}#{len(self.ordine)}"
        self.ordine.append(nome)
        self.materiale[nome] = materiale
        self.corrente = nome
        return self

    def _fine(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.parte[y][x] = self.corrente

    def punto(self, x, y):
        """Un pixel dello sprite 32x32: a scala k, un quadrato di k pixel."""
        k = self.k
        x, y = int(math.floor(x)), int(math.floor(y))
        for yy in range(y * k, y * k + k):
            for xx in range(x * k, x * k + k):
                self._fine(xx, yy)

    def rett(self, x0, y0, w, h):
        k = self.k
        for y in range(int(round(y0 * k)), int(round((y0 + h) * k))):
            for x in range(int(round(x0 * k)), int(round((x0 + w) * k))):
                self._fine(x, y)

    def ellisse(self, cx, cy, rx, ry):
        k = self.k
        cx, cy, rx, ry = cx * k, cy * k, rx * k, ry * k
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1:
                    self._fine(x, y)

    def poligono(self, punti):
        punti = [(x * self.k, y * self.k) for x, y in punti]
        ys = [p[1] for p in punti]
        for y in range(int(min(ys)), int(max(ys)) + 1):
            xs = []
            for i in range(len(punti)):
                (x0, y0), (x1, y1) = punti[i], punti[(i + 1) % len(punti)]
                if (y0 <= y + 0.5 < y1) or (y1 <= y + 0.5 < y0):
                    xs.append(x0 + (y + 0.5 - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for a, b in zip(xs[::2], xs[1::2]):
                for x in range(int(round(a)), int(round(b))):
                    self._fine(x, y)

    def linea(self, x0, y0, x1, y1, spessore=1):
        k = self.k
        if k > 1:
            # alla scala k la linea si ridisegna fine, spessa k volte
            x0, y0, x1, y1, spessore = x0 * k + (k - 1) / 2, y0 * k + (k - 1) / 2, x1 * k + (k - 1) / 2, y1 * k + (k - 1) / 2, spessore * k
        n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
        for i in range(n + 1):
            t = i / max(n, 1)
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            if spessore == 1:
                self._fine(int(math.floor(x + 0.5)), int(math.floor(y + 0.5)))
            else:
                r = spessore / 2
                for yy in range(int(math.floor(y - r + 0.5)), int(math.floor(y + r + 0.5))):
                    for xx in range(int(math.floor(x - r + 0.5)), int(math.floor(x + r + 0.5))):
                        self._fine(xx, yy)

    def arto(self, punti, spessore):
        for a, b in zip(punti, punti[1:]):
            self.linea(a[0], a[1], b[0], b[1], spessore)

    # i dettagli piatti (occhi, emblemi): sopra l'ombreggiatura
    def dettaglio(self, x, y, colore):
        """colore: un materiale con tono ('oro', 2) o un colore singolo ('occhio'). A scala k, un quadrato."""
        k = self.k
        x, y = int(math.floor(x)), int(math.floor(y))
        for yy in range(y * k, y * k + k):
            for xx in range(x * k, x * k + k):
                self.dettagli.append((xx, yy, colore))

    def dettaglio_rett(self, x0, y0, w, h, colore):
        for y in range(int(round(y0)), int(round(y0 + h))):
            for x in range(int(round(x0)), int(round(x0 + w))):
                self.dettaglio(x, y, colore)

    def dettaglio_linea(self, x0, y0, x1, y1, colore):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for k in range(n + 1):
            t = k / n
            self.dettaglio(x0 + (x1 - x0) * t + 0.5, y0 + (y1 - y0) * t + 0.5, colore)

    def indice(self, colore):
        if isinstance(colore, tuple):
            return self.indici[colore[0]][colore[1]]
        return self.singoli[colore]

    # le tre passate
    def pixel(self):
        w, h = self.w, self.h
        P = self.parte
        livello = {nome: i for i, nome in enumerate(self.ordine)}
        out = [[TRASPARENTE] * w for _ in range(h)]

        def stessa(x, y, p):
            return 0 <= x < w and 0 <= y < h and P[y][x] == p

        for y in range(h):
            for x in range(w):
                p = P[y][x]
                if p is None:
                    continue
                ombra, base, luce = self.indici[self.materiale[p]]
                tono = base
                # l'ombra: i due pixel del bordo destro (uno se la parte e' sottile) e l'ultima riga
                largo = sum(1 for k in range(-3, 4) if stessa(x + k, y, p)) >= 5
                if not stessa(x + 1, y, p) or (largo and not stessa(x + 2, y, p)) or not stessa(x, y + 1, p):
                    tono = ombra
                # la luce da sinistra e dall'alto
                elif not stessa(x - 1, y, p) or not stessa(x, y - 1, p):
                    tono = luce
                # la separazione: sotto a una parte dipinta dopo, la parte si scurisce lungo il confine
                for dx, dy in ((1, 0), (-1, 0), (0, -1), (0, 1)):
                    u, v = x + dx, y + dy
                    if 0 <= u < w and 0 <= v < h and P[v][u] is not None and livello[P[v][u]] > livello[p]:
                        tono = ombra
                out[y][x] = tono
        for x, y, colore in self.dettagli:
            if 0 <= x < w and 0 <= y < h:
                out[y][x] = self.indice(colore)
        # il contorno quasi nero: ogni pixel vuoto accanto (in croce) a uno pieno
        pieni = {(x, y) for y in range(h) for x in range(w) if out[y][x]}
        for (x, y) in pieni:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                u, v = x + dx, y + dy
                if 0 <= u < w and 0 <= v < h and (u, v) not in pieni and out[v][u] == 0:
                    out[v][u] = CONTORNO
        return out


# --- la posa: lo scheletro di una figura che guarda a destra -----------------------------------------
class Posa:
    """Lo scheletro in una posa. Le coordinate sono quelle dello sprite 32x32 (o del suo lato, scalate);
    'avanti' sposta il busto (positivo verso il nemico), 'giu' abbassa tutto il corpo sopra le gambe."""

    def __init__(self, nome, avanti=0, giu=0, testa_avanti=0, testa_giu=0, braccio="basso", gambe="ferme",
                 occhi="aperti"):
        self.nome = nome
        self.avanti, self.giu = avanti, giu
        self.testa_avanti, self.testa_giu = testa_avanti, testa_giu
        self.braccio, self.gambe, self.occhi = braccio, gambe, occhi


POSE_BASE = {
    "riposo": Posa("riposo"),
    "respiro": Posa("respiro", giu=1),
    "anticipa": Posa("anticipa", avanti=-2, giu=1, testa_avanti=-1, braccio="dietro", gambe="raccolte"),
    "colpo": Posa("colpo", avanti=3, giu=1, testa_avanti=1, braccio="avanti", gambe="affondo"),
    "colpito": Posa("colpito", avanti=-3, testa_avanti=-2, testa_giu=-1, braccio="basso", gambe="raccolte",
                    occhi="chiusi"),
    "potere": Posa("potere", avanti=0, giu=0, testa_giu=-1, braccio="alto", gambe="ferme"),
    "caduto": Posa("caduto", avanti=2, giu=8, testa_avanti=2, testa_giu=2, braccio="giu", gambe="ginocchio",
                   occhi="chiusi"),
}


class Scheletro:
    """I giunti di una figura umana di tre teste in 32 pixel, alta 'alto' pixel, coi piedi alla riga
    'piedi' e il centro a 'cx'."""

    def __init__(self, posa, cx=13, piedi=30, testa_r=3.6):
        p = posa
        self.posa = p
        self.cx, self.piedi = cx, piedi
        g = p.giu
        self.bacino = (cx + p.avanti * 0.5, 22 + g)
        self.collo = (cx + p.avanti, 15 + g)
        self.testa = (cx + 1 + p.avanti + p.testa_avanti, 10.5 + g + p.testa_giu)
        self.testa_r = testa_r
        self.spalla_a = (self.collo[0] + 1, self.collo[1] + 1.5)        # il braccio davanti (verso chi guarda)
        self.spalla_b = (self.collo[0] - 2, self.collo[1] + 1.5)        # il braccio dietro
        # i piedi: a = davanti (verso il nemico), b = dietro
        apertura = {"ferme": (3, -3), "raccolte": (2, -4), "affondo": (6, -5), "ginocchio": (5, -4)}[p.gambe]
        self.piede_a = (cx + apertura[0], piedi)
        self.piede_b = (cx + apertura[1], piedi)
        sx, sy = self.spalla_a
        self.mano_a, self.gomito_a = {
            "basso": ((sx + 4, sy + 6), (sx + 2, sy + 4)),
            "dietro": ((sx - 4, sy - 3), (sx - 2, sy + 2)),
            "avanti": ((sx + 9, sy + 1), (sx + 5, sy + 1)),
            "alto": ((sx + 4, sy - 9), (sx + 3, sy - 4)),
            "giu": ((sx + 3, sy + 8), (sx + 2, sy + 4)),
        }[p.braccio]
        bx, by = self.spalla_b
        self.mano_b = {
            "basso": (bx - 1, by + 7), "dietro": (bx - 2, by + 6), "avanti": (bx - 3, by + 5),
            "alto": (bx - 2, by - 8), "giu": (bx, by + 8),
        }[p.braccio]


def veste_lunga(f, s, materiale, orlo_largo=7):
    """La veste fino ai piedi (vescovo, eremita): un trapezio dalle spalle all'orlo che segue i piedi."""
    cx, y_orlo = s.cx, s.piedi - 1
    c = s.collo
    if s.posa.gambe == "ginocchio":
        y_orlo = s.piedi - 1
        punti = [(c[0] - 4, c[1]), (c[0] + 4, c[1]), (s.piede_a[0] + 4, y_orlo), (s.piede_b[0] - 4, y_orlo)]
    else:
        sinistra = min(s.piede_b[0] - 3, cx - orlo_largo + 1)
        destra = max(s.piede_a[0] + 3, cx + orlo_largo - 1)
        punti = [(c[0] - 4, c[1]), (c[0] + 4, c[1]), (s.bacino[0] + 5, s.bacino[1]), (destra, y_orlo),
                 (sinistra, y_orlo), (s.bacino[0] - 5, s.bacino[1])]
    f.parte_nuova("veste", materiale).poligono(punti)
    return punti


def piedi_sotto(f, s, materiale):
    f.parte_nuova("piede", materiale)
    for (x, y) in (s.piede_b, s.piede_a):
        f.rett(x - 1, y - 1, 3, 2)


def gambe(f, s, calze, scarpe):
    """Le gambe fasciate del soldato: dal bacino ai piedi, il ginocchio un po' avanti."""
    bx, by = s.bacino
    for piede, dx in ((s.piede_b, -1), (s.piede_a, 1)):
        ginocchio = ((bx + dx + piede[0]) / 2 + 1, (by + piede[1]) / 2)
        if s.posa.gambe == "ginocchio" and dx > 0:
            ginocchio = (bx + 5, s.piedi - 1)
        f.parte_nuova("gamba", calze).arto([(bx + dx, by), ginocchio, (piede[0], piede[1] - 2)], 3)
    f.parte_nuova("scarpa", scarpe)
    for piede in (s.piede_b, s.piede_a):
        f.rett(piede[0] - 1, piede[1] - 1, 4, 2)


def testa(f, s, pelle, capelli=None, barba=None, rx=None):
    """La testa di tre quarti verso destra: il viso a destra, la nuca a sinistra; l'occhio e' un dettaglio."""
    tx, ty = s.testa
    r = rx or s.testa_r
    f.parte_nuova("testa", pelle).ellisse(tx, ty, r, r + 0.4)
    f.rett(tx + r - 0.5, ty + 0.5, 1, 1)     # il naso
    if capelli:
        f.parte_nuova("capelli", capelli).poligono([(tx - r - 0.3, ty + 1.5), (tx - r - 0.3, ty - 1.5),
                                                   (tx - 1, ty - r - 0.6), (tx + r, ty - r), (tx + r + 0.3, ty - 1.2),
                                                   (tx + 0.5, ty - 1.6), (tx - 0.5, ty + 2.5)])
    if barba:
        f.parte_nuova("barba", barba).poligono([(tx - 1, ty + 1), (tx + r + 0.4, ty + 1.2), (tx + r - 0.6, ty + 3.6),
                                               (tx + 1, ty + r + 1.6), (tx - 0.6, ty + 3)])
    occhio(f, s)


def occhio(f, s, dx=1.5):
    tx, ty = s.testa
    if s.posa.occhi == "chiusi":
        f.dettaglio(tx + dx, ty, "occhio")
        f.dettaglio(tx + dx + 1, ty, "occhio")
    else:
        f.dettaglio(tx + dx + 0.5, ty - 0.6, "occhio")
        f.dettaglio(tx + dx + 0.5, ty + 0.4, "occhio")


def braccio_a(f, s, manica, pelle):
    f.parte_nuova("braccio", manica).arto([s.spalla_a, s.gomito_a, s.mano_a], 3)
    f.parte_nuova("mano", pelle).rett(s.mano_a[0] - 1, s.mano_a[1] - 1, 2, 2)


def braccio_b(f, s, manica, pelle):
    f.parte_nuova("braccio", manica).arto([s.spalla_b, s.mano_b], 3)
    f.parte_nuova("mano", pelle).rett(s.mano_b[0] - 1, s.mano_b[1] - 1, 2, 2)


def angolo_arma(s):
    """Dove punta l'arma della mano davanti, in gradi (0 = verso il nemico, 90 = in alto)."""
    return {"basso": 75, "dietro": 135, "avanti": 10, "alto": 88, "giu": -60}[s.posa.braccio]


def dalla_mano(s, lunghezza, dietro=0, angolo=None):
    a = math.radians(angolo_arma(s) if angolo is None else angolo)
    hx, hy = s.mano_a
    return ((hx - math.cos(a) * dietro, hy + math.sin(a) * dietro),
            (hx + math.cos(a) * lunghezza, hy - math.sin(a) * lunghezza))


# --- le figure ---------------------------------------------------------------------------------------
M = Materiale
PELLE = M("pelle", ("pelle", 1), ("pelle", 2), ("pelle", 2))
OCCHIO = ("occhio", ("neutri", 0))


def ubaldo(nome_posa, k=1):
    """Ubaldo, vescovo: la mitria bianca bordata d'oro, il piviale bianco con lo stolone d'oro, il camice
    grigio sotto, la barba grigia, il pastorale d'oro col ricciolo."""
    BIANCO = M("bianco", ("neutri", 3), ("neutri", 4), ("pietra calcarea", 5))
    ORO = M("oro", ("oro e bronzo", 1), ("oro e bronzo", 2), ("oro e bronzo", 3))
    CAMICE = M("camice", ("neutri", 1), ("neutri", 2), ("neutri", 3))
    pal, ind, sing = palette_di([PELLE, BIANCO, ORO, CAMICE], [OCCHIO, ("rosso", ("vermiglio comunale", 2))])
    f = Figura(32, pal, ind, sing, k)
    s = Scheletro(POSE_BASE[nome_posa])
    braccio_b(f, s, "bianco", "pelle")
    veste_lunga(f, s, "camice")
    # il piviale: il mantello a campana sopra il camice, aperto davanti
    c, b = s.collo, s.bacino
    f.parte_nuova("piviale", "bianco").poligono([(c[0] - 4.5, c[1] - 0.5), (c[0] + 3.5, c[1] - 0.5),
                                               (b[0] + 3, b[1] + 2), (b[0] + 2, s.piedi - 4),
                                               (b[0] - 7, s.piedi - 3), (b[0] - 5, b[1])])
    f.dettaglio_linea(c[0] + 2, c[1] + 1, b[0] + 2, s.piedi - 5, ("oro", 2))      # lo stolone d'oro
    f.dettaglio_linea(c[0] + 1, c[1] + 1, b[0] + 1, s.piedi - 5, ("oro", 1))
    testa(f, s, "pelle", barba="camice")
    # la mitria: due punte bianche, la fascia e la croce d'oro
    tx, ty = s.testa
    f.parte_nuova("mitria", "bianco").poligono([(tx - 3.6, ty - 2), (tx + 3.6, ty - 2), (tx + 2.6, ty - 7.5),
                                              (tx + 0.4, ty - 9.5), (tx - 1.6, ty - 7.5), (tx - 3.8, ty - 5)])
    f.dettaglio_rett(tx - 3, ty - 3, 7, 1, ("oro", 2))
    f.dettaglio_linea(tx + 0.5, ty - 8, tx + 0.5, ty - 3.5, ("oro", 1))
    f.dettaglio_rett(tx - 0.5, ty - 6, 3, 1, ("oro", 1))
    # il pastorale nella mano davanti: in riposo dritto, nel colpo puntato sul nemico
    angolo = {"basso": 92, "dietro": 115, "avanti": 35, "alto": 90, "giu": 200}[s.posa.braccio]
    basso, alto = dalla_mano(s, 13, dietro=9, angolo=angolo)
    f.parte_nuova("asta", "oro").linea(basso[0], basso[1], alto[0], alto[1], 1)
    a = math.radians(angolo)
    rx, ry = alto[0] + math.cos(a) * 2.5, alto[1] - math.sin(a) * 2.5
    f.parte_nuova("ricciolo", "oro")
    for k in range(10):         # il ricciolo, una spirale che si chiude verso il nemico
        t = k / 9 * math.pi * 1.6
        f.punto(rx + math.cos(a - math.pi / 2 + t) * 2.4 + 0.5, ry - math.sin(a - math.pi / 2 + t) * 2.4 + 0.5)
    braccio_a(f, s, "bianco", "pelle")
    return f


def giorgio(nome_posa, k=1):
    """Giorgio, giovane cavaliere: il ciuffo biondo, la cotta di maglia, la sopravveste bianca con la croce
    rossa, lo scudo azzurro a goccia, la spada."""
    FERRO = M("ferro", ("neutri", 1), ("neutri", 2), ("neutri", 3))
    BIANCO = M("bianco", ("neutri", 3), ("neutri", 4), ("pietra calcarea", 5))
    AZZURRO = M("azzurro", ("cielo e acqua", 1), ("cielo e acqua", 2), ("cielo e acqua", 3))
    pal, ind, sing = palette_di([PELLE, FERRO, BIANCO, AZZURRO], [OCCHIO, ("rosso", ("vermiglio comunale", 2)),
                                                                 ("biondo", ("oro e bronzo", 3)),
                                                                 ("biondo_s", ("pelle", 0))])
    f = Figura(32, pal, ind, sing, k)
    s = Scheletro(POSE_BASE[nome_posa])
    # lo scudo, sul braccio dietro: una goccia azzurra con la croce bianca
    mb = s.mano_b
    sx, sy = mb[0] - 1, mb[1] - 2
    if s.posa.braccio == "alto":
        sx, sy = s.spalla_b[0] - 2, s.spalla_b[1] + 3
    gambe(f, s, "ferro", "ferro")
    c, b = s.collo, s.bacino
    f.parte_nuova("cotta", "ferro").poligono([(c[0] - 4, c[1]), (c[0] + 4, c[1]), (b[0] + 4, b[1] + 3),
                                             (b[0] - 4, b[1] + 3)])
    f.parte_nuova("sopravveste", "bianco").poligono([(c[0] - 3, c[1] + 1), (c[0] + 3, c[1] + 1),
                                                    (b[0] + 5, b[1] + 4), (b[0] - 5, b[1] + 4)])
    # la croce rossa sul petto
    f.dettaglio_linea(c[0] + 0.5, c[1] + 2, b[0] + 0.5, b[1] + 2, "rosso")
    f.dettaglio_linea(c[0] - 2, c[1] + 4.5, c[0] + 3, c[1] + 4.5, "rosso")
    f.dettaglio_rett(b[0] - 4, b[1] - 0.5, 9, 1, ("ferro", 0))      # la cintura
    testa(f, s, "pelle")
    tx, ty = s.testa
    r = s.testa_r
    for y in range(int(ty - r - 2), int(ty + 3)):         # i capelli: la calotta e la nuca, il viso libero
        for x in range(int(tx - r - 1), int(tx + r + 1)):
            dentro = ((x + 0.5 - tx) / (r + 0.6)) ** 2 + ((y + 0.5 - ty) / (r + 1)) ** 2 <= 1
            if dentro and (y < ty - 1.5 or x < tx - 0.5 - (y - ty) * 0.3):
                f.dettaglio(x, y, "biondo_s" if x < tx - 2.5 and y > ty - 2 else "biondo")
    f.dettaglio(tx + r - 0.2, ty - 2.5, "biondo")        # il ciuffo sulla fronte
    occhio(f, s)
    f.parte_nuova("scudo", "azzurro").poligono([(sx - 4, sy - 3), (sx + 3, sy - 3), (sx + 3, sy + 3),
                                              (sx - 0.5, sy + 8), (sx - 4, sy + 3)])
    f.dettaglio_linea(sx - 1, sy - 2, sx - 1, sy + 5, ("bianco", 2))
    f.dettaglio_linea(sx - 3, sy, sx + 1, sy, ("bianco", 2))
    # la spada nella mano davanti
    angolo = {"basso": 70, "dietro": 160, "avanti": 5, "alto": 90, "giu": -50}[s.posa.braccio]
    elsa, punta = dalla_mano(s, 12, dietro=1, angolo=angolo)
    f.parte_nuova("lama", "bianco").linea(s.mano_a[0], s.mano_a[1], punta[0], punta[1], 1)
    a = math.radians(angolo)
    gx, gy = math.sin(a) * 2, math.cos(a) * 2
    f.parte_nuova("guardia", "ferro").linea(s.mano_a[0] - gx + math.cos(a), s.mano_a[1] - gy - math.sin(a),
                                            s.mano_a[0] + gx + math.cos(a), s.mano_a[1] + gy - math.sin(a), 1)
    braccio_a(f, s, "ferro", "pelle")
    return f


def antonio(nome_posa, k=1):
    """Antonio, eremita: il saio bruno col cappuccio, la barba bianca lunga, il bastone a tau col
    campanello; nel colpo e nel potere la fiamma in mano."""
    SAIO = M("saio", ("legno e cuoio", 0), ("legno e cuoio", 1), ("legno e cuoio", 2))
    BIANCO = M("bianco", ("neutri", 3), ("neutri", 4), ("pietra calcarea", 5))
    FUOCO = M("fuoco", ("vermiglio comunale", 2), ("oro e bronzo", 2), ("oro e bronzo", 3))
    pal, ind, sing = palette_di([PELLE, SAIO, BIANCO, FUOCO], [OCCHIO, ("corda", ("legno e cuoio", 3)),
                                                              ("bastone", ("cotto e coppi", 3))])
    f = Figura(32, pal, ind, sing, k)
    s = Scheletro(POSE_BASE[nome_posa])
    # il bastone a tau nella mano dietro, piantato a terra
    mb = s.mano_b
    f.parte_nuova("bastone", "saio")
    braccio_b(f, s, "saio", "pelle")
    veste_lunga(f, s, "saio", orlo_largo=6)
    c, b = s.collo, s.bacino
    f.dettaglio_rett(b[0] - 4, b[1] - 1, 9, 1, "corda")          # il cordone
    f.dettaglio_linea(b[0] + 2, b[1], b[0] + 3, b[1] + 5, "corda")
    testa(f, s, "pelle", barba="bianco")
    tx, ty = s.testa
    # il cappuccio: copre la nuca e la fronte, il viso resta fuori a destra
    f.parte_nuova("cappuccio", "saio").poligono([(tx - 4.6, ty + 3.5), (tx - 4.8, ty - 1.5), (tx - 2, ty - 4.8),
                                                (tx + 2, ty - 4.8), (tx + 3.6, ty - 2.2), (tx + 0.6, ty - 2),
                                                (tx - 0.8, ty + 0.5), (tx - 0.6, ty + 4.2)])
    occhio(f, s)
    f.dettaglio_rett(tx + 0.6, ty - 1.6, 3, 1, ("bianco", 1))        # le sopracciglia bianche
    # il tau: un'asta col traverso e il campanello
    x0 = mb[0] - 1
    f.parte_nuova("tau", "saio").linea(x0, s.piedi - 1, x0, mb[1] - 10, 1)
    f.parte_nuova("tau_t", "saio").rett(x0 - 2, mb[1] - 11, 5, 1)
    f.dettaglio(x0, mb[1] - 11, "bastone")
    f.dettaglio_linea(x0, s.piedi - 1, x0, mb[1] - 9, "bastone")
    f.parte_nuova("campanello", "fuoco").rett(x0 + 2, mb[1] - 10, 2, 2)
    braccio_a(f, s, "saio", "pelle")
    if s.posa.braccio in ("avanti", "alto"):
        hx, hy = s.mano_a
        f.parte_nuova("fiamma", "fuoco").poligono([(hx - 2, hy - 1), (hx + 2.5, hy - 1), (hx + 1.5, hy - 5),
                                                  (hx + 0.5, hy - 8), (hx - 1, hy - 4)])
    return f


# --- i nemici: si disegnano verso destra e si specchiano --------------------------------------------
def soldato_base(f, s, tunica, calze, scarpe, pelle="pelle"):
    gambe(f, s, calze, scarpe)
    c, b = s.collo, s.bacino
    f.parte_nuova("tunica", tunica).poligono([(c[0] - 4, c[1]), (c[0] + 4, c[1]), (b[0] + 5, b[1] + 3),
                                             (b[0] - 5, b[1] + 3)])
    testa(f, s, pelle)


def fante(nome_posa, k=1):
    """Fante di Perugia: la tunica rossa e bianca a quarti, l'elmo a coppo col nasale, la lancia."""
    ROSSO = M("rosso", ("vermiglio comunale", 1), ("vermiglio comunale", 2), ("vermiglio comunale", 3))
    FERRO = M("ferro", ("neutri", 1), ("neutri", 2), ("neutri", 3))
    LEGNO = M("legno", ("legno e cuoio", 0), ("legno e cuoio", 1), ("legno e cuoio", 2))
    BIANCO = M("bianco", ("neutri", 3), ("neutri", 4), ("pietra calcarea", 5))
    pal, ind, sing = palette_di([PELLE, ROSSO, FERRO, LEGNO, BIANCO], [OCCHIO])
    f = Figura(32, pal, ind, sing, k)
    s = Scheletro(POSE_BASE[nome_posa])
    braccio_b(f, s, "rosso", "pelle")
    soldato_base(f, s, "rosso", "legno", "legno")
    c, b = s.collo, s.bacino
    # la tunica a quarti: bianco in alto dietro e in basso davanti
    f.parte_nuova("quarto", "bianco").poligono([(c[0] - 4, c[1]), (c[0], c[1]), (c[0] + 0.5 * (b[0] - c[0]), c[1] + 4),
                                              (c[0] - 4.5, c[1] + 4)])
    f.parte_nuova("quarto", "bianco").poligono([(b[0], b[1] - 2), (b[0] + 4.6, b[1] - 2), (b[0] + 5, b[1] + 3),
                                              (b[0], b[1] + 3)])
    tx, ty = s.testa
    f.parte_nuova("elmo", "ferro").poligono([(tx - 4, ty - 0.5), (tx - 3.5, ty - 3.5), (tx - 1, ty - 5),
                                            (tx + 2, ty - 4.5), (tx + 4, ty - 2), (tx + 4, ty - 0.8)])
    f.parte_nuova("nasale", "ferro").rett(tx + 2.5, ty - 1, 1, 3)
    angolo = {"basso": 95, "dietro": 175, "avanti": 2, "alto": 80, "giu": 200}[s.posa.braccio]
    calcio, punta = dalla_mano(s, 13, dietro=12, angolo=angolo)
    f.parte_nuova("asta", "legno").linea(calcio[0], calcio[1], punta[0], punta[1], 1)
    a = math.radians(angolo)
    f.parte_nuova("punta", "ferro").linea(punta[0], punta[1], punta[0] + math.cos(a) * 3, punta[1] - math.sin(a) * 3, 2)
    braccio_a(f, s, "rosso", "pelle")
    return f


def balestriere(nome_posa, k=1):
    """Balestriere pesante: la cervelliera, il gambeson imbottito color cuoio, la balestra puntata."""
    CUOIO = M("cuoio", ("legno e cuoio", 1), ("legno e cuoio", 2), ("legno e cuoio", 3))
    FERRO = M("ferro", ("neutri", 1), ("neutri", 2), ("neutri", 3))
    ROSSO = M("rosso", ("vermiglio comunale", 1), ("vermiglio comunale", 2), ("vermiglio comunale", 3))
    pal, ind, sing = palette_di([PELLE, CUOIO, FERRO, ROSSO], [OCCHIO, ("legno", ("legno e cuoio", 0))])
    f = Figura(32, pal, ind, sing, k)
    s = Scheletro(POSE_BASE[nome_posa])
    braccio_b(f, s, "cuoio", "pelle")
    soldato_base(f, s, "cuoio", "rosso", "ferro")
    c, b = s.collo, s.bacino
    for y in range(int(c[1]) + 2, int(b[1]) + 3, 2):          # le cuciture dell'imbottitura
        f.dettaglio_linea(c[0] - 3, y, c[0] + 2, y, ("cuoio", 0))
    f.dettaglio_rett(b[0] - 4, b[1], 9, 1, "legno")
    tx, ty = s.testa
    f.parte_nuova("cervelliera", "ferro").poligono([(tx - 5, ty - 1), (tx - 3, ty - 4.5), (tx + 2, ty - 4.5),
                                                  (tx + 5, ty - 1)])
    # la balestra: il fusto nella mano davanti, l'arco di traverso in punta
    angolo = {"basso": -20, "dietro": 30, "avanti": 0, "alto": 50, "giu": -70}[s.posa.braccio]
    fondo, punta = dalla_mano(s, 6, dietro=5, angolo=angolo)
    f.parte_nuova("fusto", "cuoio").linea(fondo[0], fondo[1], punta[0], punta[1], 2)
    a = math.radians(angolo)
    nx, ny = math.sin(a) * 5, math.cos(a) * 5
    f.parte_nuova("arco", "ferro").arto([(punta[0] - nx - math.cos(a) * 2, punta[1] - ny + math.sin(a) * 2),
                                        punta, (punta[0] + nx - math.cos(a) * 2, punta[1] + ny + math.sin(a) * 2)], 1)
    braccio_a(f, s, "cuoio", "pelle")
    return f


def spia(nome_posa, k=1):
    """Spia umbra: il mantello verde scuro col cappuccio a punta, il viso in ombra, il pugnale."""
    VERDE = M("verde", ("verde dei monti", 0), ("verde dei monti", 1), ("verde dei monti", 2))
    SCURO = M("scuro", ("neutri", 0), ("neutri", 1), ("neutri", 2))
    FERRO = M("ferro", ("neutri", 2), ("neutri", 3), ("neutri", 4))
    pal, ind, sing = palette_di([PELLE, VERDE, SCURO, FERRO], [("occhio", ("oro e bronzo", 3))])
    f = Figura(32, pal, ind, sing, k)
    s = Scheletro(POSE_BASE[nome_posa])
    braccio_b(f, s, "verde", "pelle")
    gambe(f, s, "scuro", "scuro")
    c, b = s.collo, s.bacino
    f.parte_nuova("mantello", "verde").poligono([(c[0] - 4, c[1] - 1), (c[0] + 3, c[1] - 1), (b[0] + 5, s.piedi - 5),
                                                (b[0] - 1, s.piedi - 3), (b[0] - 8, s.piedi - 2)])
    tx, ty = s.testa
    f.parte_nuova("cappuccio", "verde").poligono([(tx - 4.5, ty + 3), (tx - 4.5, ty - 2), (tx - 3, ty - 6.5),
                                                 (tx + 1.5, ty - 4.5), (tx + 4, ty - 1.5), (tx + 4, ty + 3)])
    f.parte_nuova("viso", "scuro").poligono([(tx, ty - 1.5), (tx + 3.5, ty - 1.5), (tx + 3.5, ty + 2.5), (tx, ty + 2.5)])
    occhio(f, s)
    angolo = {"basso": -45, "dietro": 120, "avanti": 0, "alto": 70, "giu": -80}[s.posa.braccio]
    _, punta = dalla_mano(s, 5, angolo=angolo)
    f.parte_nuova("pugnale", "ferro").linea(s.mano_a[0], s.mano_a[1], punta[0], punta[1], 1)
    braccio_a(f, s, "verde", "pelle")
    return f


def guerriero(nome_posa, k=1):
    """Guerriero della Roccia di Spoleto: la corazza di ferro a fasce, l'elmo tondo col nasale, lo scudo
    lungo con la fascia rossa, il piccone da guerra."""
    FERRO = M("ferro", ("neutri", 1), ("neutri", 2), ("neutri", 3))
    ROSSO = M("rosso", ("vermiglio comunale", 1), ("vermiglio comunale", 2), ("vermiglio comunale", 3))
    LEGNO = M("legno", ("legno e cuoio", 0), ("legno e cuoio", 1), ("legno e cuoio", 2))
    PIETRA = M("pietra", ("pietra calcarea", 1), ("pietra calcarea", 2), ("pietra calcarea", 3))
    pal, ind, sing = palette_di([PELLE, FERRO, ROSSO, LEGNO], [OCCHIO, ("fascia", ("neutri", 1))])
    f = Figura(32, pal, ind, sing, k)
    s = Scheletro(POSE_BASE[nome_posa])
    gambe(f, s, "legno", "ferro")
    c, b = s.collo, s.bacino
    f.parte_nuova("corazza", "ferro").poligono([(c[0] - 5, c[1] - 0.5), (c[0] + 5, c[1] - 0.5), (b[0] + 5, b[1] + 3),
                                               (b[0] - 5, b[1] + 3)])
    for y in range(int(c[1]) + 3, int(b[1]) + 3, 3):
        f.dettaglio_linea(c[0] - 4, y, c[0] + 4, y, "fascia")
    testa(f, s, "pelle")
    tx, ty = s.testa
    f.parte_nuova("elmo", "ferro").poligono([(tx - 4.2, ty + 1), (tx - 4, ty - 3), (tx - 1, ty - 5), (tx + 2.5, ty - 4.5),
                                            (tx + 4.3, ty - 1.5), (tx + 4.3, ty - 0.5)])
    f.parte_nuova("nasale", "ferro").rett(tx + 2.5, ty - 1, 1, 3)
    mb = s.mano_b
    f.parte_nuova("scudo", "rosso").rett(mb[0] - 4, mb[1] - 7, 6, 13)
    f.dettaglio_linea(mb[0] - 2, mb[1] - 6, mb[0] - 2, mb[1] + 5, "fascia")
    angolo = {"basso": 80, "dietro": 140, "avanti": 15, "alto": 95, "giu": -60}[s.posa.braccio]
    fondo, cima = dalla_mano(s, 9, dietro=3, angolo=angolo)
    f.parte_nuova("manico", "legno").linea(fondo[0], fondo[1], cima[0], cima[1], 1)
    a = math.radians(angolo)
    nx, ny = math.sin(a) * 4, math.cos(a) * 4
    f.parte_nuova("piccone", "ferro").arto([(cima[0] - nx * 0.6, cima[1] - ny * 0.6), cima, (cima[0] + nx, cima[1] + ny)], 2)
    braccio_a(f, s, "ferro", "pelle")
    del PIETRA
    return f


def infiltrato(nome_posa, k=1):
    """L'infiltrato delle Logge: vestito da pellegrino (il cappello a tesa larga con la conchiglia, il
    mantello, il bordone); in azione il pugnale esce dal mantello."""
    MANTELLO = M("mantello", ("legno e cuoio", 1), ("legno e cuoio", 2), ("legno e cuoio", 3))
    CAPPELLO = M("cappello", ("legno e cuoio", 0), ("legno e cuoio", 1), ("legno e cuoio", 2))
    FERRO = M("ferro", ("neutri", 2), ("neutri", 3), ("neutri", 4))
    pal, ind, sing = palette_di([PELLE, MANTELLO, CAPPELLO, FERRO], [OCCHIO, ("conchiglia", ("pietra calcarea", 5)),
                                                                    ("zucca", ("oro e bronzo", 2))])
    f = Figura(32, pal, ind, sing, k)
    s = Scheletro(POSE_BASE[nome_posa])
    mb = s.mano_b
    f.parte_nuova("bordone", "cappello").linea(mb[0] - 1, s.piedi - 1, mb[0] - 1, mb[1] - 13, 1)
    f.dettaglio_rett(mb[0] - 2, mb[1] - 10, 2, 2, "zucca")
    braccio_b(f, s, "mantello", "pelle")
    gambe(f, s, "cappello", "cappello")
    veste_lunga(f, s, "mantello", orlo_largo=6)
    testa(f, s, "pelle", barba="cappello")
    tx, ty = s.testa
    f.parte_nuova("cappello", "cappello").ellisse(tx, ty - 3, 7, 1.6)
    f.parte_nuova("cupola", "cappello").ellisse(tx - 0.5, ty - 4.5, 3.4, 2.2)
    f.dettaglio_rett(tx - 1, ty - 5, 2, 2, "conchiglia")
    if s.posa.braccio in ("avanti", "alto", "dietro"):
        angolo = {"dietro": 130, "avanti": 0, "alto": 70}[s.posa.braccio]
        _, punta = dalla_mano(s, 5, angolo=angolo)
        f.parte_nuova("pugnale", "ferro").linea(s.mano_a[0], s.mano_a[1], punta[0], punta[1], 1)
        braccio_a(f, s, "mantello", "pelle")
    return f


def spettro(nome_posa):
    """Spettro del Dubbio: un velo grigio che fluttua (nessun piede a terra), sfrangiato in basso, due occhi
    vuoti; nel colpo le mani lunghe si allungano. Non ha scheletro: ondeggia."""
    VELO = M("velo", ("neutri", 1), ("neutri", 2), ("neutri", 3))
    OMBRA = M("ombra", ("neutri", 0), ("neutri", 0), ("neutri", 1))
    LUCE = M("luce", ("cielo e acqua", 2), ("cielo e acqua", 3), ("cielo e acqua", 4))
    pal, ind, sing = palette_di([VELO, OMBRA, LUCE], [("occhio", ("cielo e acqua", 4))])
    f = Figura(32, pal, ind, sing)
    p = POSE_BASE[nome_posa]
    alto = 4 + p.giu - (1 if p.braccio == "alto" else 0) + (4 if p.gambe == "ginocchio" else 0)
    av = p.avanti
    f.parte_nuova("velo", "velo").poligono([(13 + av, alto), (19 + av, alto + 2), (21 + av, alto + 10), (23, 27),
                                          (5, 27), (8 + av * 0.5, alto + 10), (9 + av, alto + 2)])
    f.parte_nuova("viso", "ombra").ellisse(16 + av, alto + 6, 3.5, 4)
    if p.occhi == "aperti":
        f.dettaglio(15 + av, alto + 5, "occhio")
        f.dettaglio(18 + av, alto + 5, "occhio")
    else:
        f.dettaglio_rett(15 + av, alto + 6, 4, 1, "occhio")
    for k, x in enumerate(range(5, 24, 3)):                     # le frange, sfasate fra le pose
        lun = 2 + (k + POSA[nome_posa]) % 3
        f.parte_nuova("frangia", "velo").rett(x, 27, 2, lun)
    if p.braccio in ("avanti", "alto", "dietro"):
        mano = {"avanti": (30, alto + 10), "alto": (24, alto - 2), "dietro": (12, alto + 4)}[p.braccio]
        f.parte_nuova("braccio", "velo").arto([(18 + av, alto + 9), mano], 2)
        f.parte_nuova("dita", "luce").rett(mano[0] - 1, mano[1] - 1, 2, 2)
    return f


def corrado(nome_posa):
    """Corrado di Spoleto, 64x64: il colosso in armatura scura, l'elmo chiuso col cimiero rosso, lo scudo
    rosso con la fascia d'oro, il martello d'assedio. E' lo scheletro di 32 disegnato al doppio."""
    FERRO = M("ferro", ("neutri", 1), ("neutri", 2), ("neutri", 3))
    ROSSO = M("rosso", ("vermiglio comunale", 1), ("vermiglio comunale", 2), ("vermiglio comunale", 3))
    ORO = M("oro", ("oro e bronzo", 1), ("oro e bronzo", 2), ("oro e bronzo", 3))
    LEGNO = M("legno", ("legno e cuoio", 0), ("legno e cuoio", 1), ("legno e cuoio", 2))
    pal, ind, sing = palette_di([FERRO, ROSSO, ORO, LEGNO], [("occhio", ("vermiglio comunale", 3)),
                                                           ("buio", ("neutri", 0))])
    f = Figura(64, pal, ind, sing)
    p = POSE_BASE[nome_posa]
    s = Scheletro(p)
    k = 2.15      # piu' del doppio dello scheletro di 32: e' un colosso

    def X(v):
        return (v - 13) * k + 24

    def Y(v):
        return 62 - (30 - v) * k

    c = (X(s.collo[0]), Y(s.collo[1]) - 2)
    b = (X(s.bacino[0]), Y(s.bacino[1]))
    pa, pb = (X(s.piede_a[0]), 62), (X(s.piede_b[0]), 62)
    # il braccio dietro con lo scudo
    mb = (X(s.mano_b[0]), Y(s.mano_b[1]))
    f.parte_nuova("braccio_b", "ferro").arto([(X(s.spalla_b[0]), Y(s.spalla_b[1])), mb], 7)
    # le gambe e gli schinieri
    for piede, dx in ((pb, -3), (pa, 3)):
        ginocchio = ((b[0] + dx + piede[0]) / 2 + 2, (b[1] + piede[1]) / 2)
        if p.gambe == "ginocchio" and dx > 0:
            ginocchio = (b[0] + 10, 61)
        f.parte_nuova("gamba", "ferro").arto([(b[0] + dx, b[1]), ginocchio, (piede[0], piede[1] - 3)], 7)
        f.parte_nuova("piede", "ferro").rett(piede[0] - 3, piede[1] - 4, 8, 4)
    # il corpo: spalle larghissime
    f.parte_nuova("corpo", "ferro").poligono([(c[0] - 12, c[1] + 1), (c[0] + 11, c[1] + 1), (b[0] + 10, b[1] + 4),
                                            (b[0] - 10, b[1] + 4)])
    f.parte_nuova("spallaccio", "ferro").ellisse(c[0] + 7, c[1] + 4, 6, 5)
    f.parte_nuova("gonnella", "rosso").poligono([(b[0] - 10, b[1] + 1), (b[0] + 10, b[1] + 1), (b[0] + 12, b[1] + 10),
                                               (b[0] - 12, b[1] + 10)])
    f.dettaglio_rett(b[0] - 10, b[1], 21, 2, ("oro", 2))         # la cintura
    f.dettaglio_rett(b[0] - 1, b[1], 3, 2, ("oro", 1))
    # l'elmo chiuso, la feritoia rossa che brilla, il cimiero
    tx, ty = X(s.testa[0]), Y(s.testa[1])
    f.parte_nuova("elmo", "ferro").poligono([(tx - 8, ty + 7), (tx - 8, ty - 5), (tx - 4, ty - 9), (tx + 5, ty - 9),
                                           (tx + 8, ty - 5), (tx + 8, ty + 7)])
    f.dettaglio_rett(tx - 1, ty - 1, 9, 2, "buio")
    if p.occhi == "aperti":
        f.dettaglio_rett(tx + 4, ty - 1, 2, 1, "occhio")
    for yy in range(int(ty + 3), int(ty + 7), 2):
        f.dettaglio_rett(tx + 3, yy, 4, 1, "buio")
    f.parte_nuova("cimiero", "rosso").poligono([(tx - 2, ty - 9), (tx + 2, ty - 9), (tx - 1, ty - 17), (tx - 9, ty - 12)])
    # lo scudo a mandorla
    f.parte_nuova("scudo", "rosso").poligono([(mb[0] - 9, mb[1] - 12), (mb[0] + 5, mb[1] - 12), (mb[0] + 5, mb[1] + 4),
                                            (mb[0] - 2, mb[1] + 14), (mb[0] - 9, mb[1] + 4)])
    f.dettaglio_rett(mb[0] - 3, mb[1] - 11, 3, 22, ("oro", 2))
    f.dettaglio_rett(mb[0] - 8, mb[1] - 4, 13, 3, ("oro", 2))
    # il martello nella mano davanti
    ma = (X(s.mano_a[0]), Y(s.mano_a[1]))
    angolo = {"basso": -78, "dietro": 135, "avanti": 25, "alto": 92, "giu": -60}[p.braccio]
    a = math.radians(angolo)
    lungo = 9 if p.braccio == "avanti" else 14
    fondo = (ma[0] - math.cos(a) * 6, ma[1] + math.sin(a) * 6)
    cima = (ma[0] + math.cos(a) * lungo, ma[1] - math.sin(a) * lungo)
    f.parte_nuova("manico", "legno").linea(fondo[0], fondo[1], cima[0], cima[1], 3)
    nx, ny = math.sin(a), math.cos(a)
    testa_m = [(cima[0] - nx * 7 - math.cos(a) * 3, cima[1] - ny * 7 + math.sin(a) * 3),
               (cima[0] + nx * 7 - math.cos(a) * 3, cima[1] + ny * 7 + math.sin(a) * 3),
               (cima[0] + nx * 7 + math.cos(a) * 4, cima[1] + ny * 7 - math.sin(a) * 4),
               (cima[0] - nx * 7 + math.cos(a) * 4, cima[1] - ny * 7 - math.sin(a) * 4)]
    f.parte_nuova("mazza", "ferro").poligono(testa_m)
    f.parte_nuova("braccio_a", "ferro").arto([(X(s.spalla_a[0]), Y(s.spalla_a[1])), (X(s.gomito_a[0]), Y(s.gomito_a[1])),
                                             ma], 7)
    f.parte_nuova("guanto", "ferro").rett(ma[0] - 3, ma[1] - 3, 6, 6)
    return f


SANTI = (("UBALDO", ubaldo), ("GIORGIO", giorgio), ("ANTONIO", antonio))
NEMICI = (("FANTE", fante), ("BALESTRIERE", balestriere), ("CORRADO", corrado), ("SPIA", spia),
          ("SPETTRO", spettro), ("GUERRIERO", guerriero), ("INFILTRATO", infiltrato))


def pose_di(pittore, nemico):
    """Le pose di una figura come righe di indici, specchiate se e' un nemico (guarda a sinistra)."""
    out = []
    for nome in POSE:
        f = pittore(nome)
        px = f.pixel()
        if nemico:
            px = [list(reversed(r)) for r in px]
        out.append((f.palette, px))
    return out


# --- gli effetti: 32x32, quattro fotogrammi ciascuno, una palette sola -----------------------------
# Nell'ordine di Effetto in include/animazione_battaglia.h (NESSUNO escluso). Disegnati verso destra:
# quando colpisce un nemico la scena li specchia.
PALETTE_EFFETTI = [("neutri", 0), ("neutri", 0), ("pietra calcarea", 5), ("oro e bronzo", 3), ("oro e bronzo", 2),
                   ("oro e bronzo", 1), ("cotto e coppi", 4), ("vermiglio comunale", 2), ("vermiglio comunale", 1),
                   ("cielo e acqua", 4), ("cielo e acqua", 3), ("cielo e acqua", 2), ("neutri", 3), ("neutri", 2),
                   ("pietra calcarea", 3), ("pietra calcarea", 2)]
E_BIANCO, E_GIALLO, E_ORO, E_ORO_S, E_ARANCIO, E_ROSSO, E_ROSSO_S = 2, 3, 4, 5, 6, 7, 8
E_CELESTE, E_AZZURRO, E_BLU, E_GRIGIO_L, E_GRIGIO, E_POLVERE_L, E_POLVERE = 9, 10, 11, 12, 13, 14, 15
FOTOGRAMMI_EFFETTO = 4


def _tela():
    return [[0] * 32 for _ in range(32)]


def _punto(t, x, y, c):
    x, y = int(math.floor(x)), int(math.floor(y))
    if 0 <= x < 32 and 0 <= y < 32:
        t[y][x] = c


def _anello(t, cx, cy, rx, ry, c, spessore=1.0, scacchi=False):
    for y in range(32):
        for x in range(32):
            d = math.hypot((x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry)
            if abs(d - 1) * min(rx, ry) < spessore / 2 + 0.25 and (not scacchi or (x + y) % 2 == 0):
                t[y][x] = c


def _disco(t, cx, cy, r, c, scacchi=False):
    for y in range(32):
        for x in range(32):
            if math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= r and (not scacchi or (x + y) % 2 == 0):
                t[y][x] = c


def scia(k):
    """Il fendente: una mezzaluna dall'alto a destra verso il basso, bianca col filo celeste, che si
    assottiglia e si sgrana."""
    t = _tela()
    inizio, fine = [(-100, -60), (-100, 30), (-60, 60), (-10, 70)][k]
    spessore = [2.5, 4.5, 3, 1.5][k]
    for g in range(inizio, fine):
        a = math.radians(g)
        for r10 in range(0, int(spessore * 10)):
            r = 12 - r10 / 10
            x, y = 14 + math.cos(a) * r, 16 + math.sin(a) * r
            colore = E_CELESTE if r10 < 6 else E_BIANCO
            if k == 3 and (int(x) + int(y)) % 2:
                continue
            _punto(t, x, y, colore if k < 2 or r10 < 12 else E_AZZURRO)
    return t


def scintilla(k):
    """L'impatto: un lampo a croce, la stella a otto punte, i punti che volano via."""
    t = _tela()
    cx, cy = 16, 16
    if k == 0:
        for d in range(-3, 4):
            _punto(t, cx + d, cy, E_BIANCO)
            _punto(t, cx, cy + d, E_BIANCO)
        _disco(t, cx + 0.5, cy + 0.5, 1.2, E_GIALLO)
    elif k == 1:
        for i in range(8):
            a = math.radians(i * 45 + 22.5)
            lun = 9 if i % 2 == 0 else 6
            for r in range(lun):
                _punto(t, cx + 0.5 + math.cos(a) * r, cy + 0.5 + math.sin(a) * r, E_GIALLO if r > 3 else E_BIANCO)
        _disco(t, cx + 0.5, cy + 0.5, 2.5, E_BIANCO)
    else:
        r = 9 if k == 2 else 12
        for i in range(8):
            a = math.radians(i * 45 + 22.5)
            c = E_GIALLO if k == 2 else E_ORO
            _punto(t, cx + 0.5 + math.cos(a) * r, cy + 0.5 + math.sin(a) * r, c)
            if k == 2:
                _punto(t, cx + 0.5 + math.cos(a) * (r - 1), cy + 0.5 + math.sin(a) * (r - 1), E_BIANCO)
    return t


def raggio(k):
    """Il Giudizio della Verga: la colonna di luce che cade sul bersaglio, si allarga e si spegne;
    scintille d'oro ai lati."""
    t = _tela()
    largo = [2, 8, 6, 3][k]
    for y in range(32):
        if k == 0 and y > 20:
            break
        for x in range(16 - largo // 2 - 1, 16 + (largo + 1) // 2 + 1):
            bordo = x < 16 - largo // 2 or x >= 16 + (largo + 1) // 2
            if k == 3 and (x + y) % 2:
                continue
            t[y][x] = E_GIALLO if bordo else (E_BIANCO if abs(x - 15.5) < largo / 3 else E_GIALLO)
    if k in (1, 2):
        _anello(t, 16, 29, 9 + 2 * k, 2.5, E_ORO)
        for i, (x, y) in enumerate(((7, 10), (24, 14), (9, 22), (23, 5))):
            if (i + k) % 2 == 0:
                _punto(t, x, y, E_BIANCO)
                _punto(t, x - 1, y, E_GIALLO)
                _punto(t, x + 1, y, E_GIALLO)
                _punto(t, x, y - 1, E_GIALLO)
                _punto(t, x, y + 1, E_GIALLO)
    return t


def fiamma(k):
    """Il fuoco: tre lingue che salgono dal basso, sfasate fra i fotogrammi (il ciclo e' di quattro)."""
    t = _tela()
    for i, (x0, alto) in enumerate(((10, 14), (16, 20), (22, 12))):
        h = alto + [0, 3, -2, 1][(k + i) % 4]
        for y in range(31 - h, 31):
            v = (y - (31 - h)) / h            # 0 in punta, 1 alla base
            mezza = 1 + v * 3.5
            sbanda = math.sin((y + k * 3 + i * 5) * 0.6) * (1 - v) * 1.5
            for x in range(int(x0 - mezza + sbanda), int(x0 + mezza + sbanda) + 1):
                d = abs(x - x0 - sbanda) / mezza
                c = E_ROSSO if d > 0.7 or v < 0.15 else (E_ARANCIO if d > 0.4 or v < 0.35 else E_GIALLO)
                _punto(t, x, y, c)
    for i in range(3):                       # le faville
        _punto(t, 8 + i * 7 + k * 2 % 5, 12 - k * 3 + i * 2, E_GIALLO)
    return t


def aura(k):
    """Il Fervore: due anelli d'oro che salgono dai piedi, le scintille che salgono con loro."""
    t = _tela()
    for j in range(2):
        y = 28 - ((k * 6 + j * 12) % 24)
        r = 10 - (28 - y) * 0.15
        _anello(t, 16, y, r, 2.2, E_GIALLO if j == 0 else E_ORO, scacchi=(k == 3))
    for i in range(5):
        x = 6 + i * 5
        y = 26 - ((k * 5 + i * 7) % 26)
        _punto(t, x, y, E_BIANCO)
        _punto(t, x, y + 1, E_GIALLO)
    return t


def scudo(k):
    """L'alone azzurro del Muro e del Bastione: si apre, pulsa, si sgrana."""
    t = _tela()
    r = [8, 13, 12, 13][k]
    _anello(t, 16, 16, r * 0.75, r, E_AZZURRO, spessore=2, scacchi=(k == 3))
    _anello(t, 16, 16, r * 0.75 - 1.5, r - 1.5, E_CELESTE, spessore=1, scacchi=(k >= 2))
    if k in (1, 2):
        for dy in (-5, 0, 5):
            _punto(t, 16 + r * 0.75 - 1, 16 + dy, E_BIANCO)
    return t


def schegge(k):
    """Lo scudo che si rompe: schegge di ferro e di vermiglio che volano via dal centro."""
    t = _tela()
    for i in range(7):
        a = math.radians(i * 51 + 10)
        r = 3 + k * 4
        x, y = 16 + math.cos(a) * r, 16 + math.sin(a) * r + k * k * 0.6
        c = (E_GRIGIO_L, E_ROSSO, E_GRIGIO)[i % 3]
        _punto(t, x, y, c)
        _punto(t, x + 1, y, c)
        if k < 2:
            _punto(t, x, y + 1, c)
    if k == 0:
        _disco(t, 16.5, 16.5, 3, E_BIANCO)
    return t


def polvere(k):
    """La polvere del passo e della caduta: due sbuffi bassi che crescono e si sgranano."""
    t = _tela()
    for cx in (9, 22):
        r = 1.5 + k * 1.2
        _disco(t, cx + 0.5, 29 - k * 0.5, r, E_POLVERE_L, scacchi=(k >= 2))
        if k < 3:
            _disco(t, cx - 0.5, 29.5 - k * 0.5, r * 0.6, E_POLVERE, scacchi=(k >= 2))
    return t


def dardo(k):
    """Il verrettone della balestra in volo, verso destra (a sinistra lo specchia il gioco): la punta di ferro,
    l'asta, le alette vermiglie; dietro, due fili d'aria che si allungano e si accorciano (k)."""
    t = _tela()
    y = 15
    for x in range(10, 23):                     # l'asta: luce sopra, ombra sotto
        _punto(t, x, y, E_POLVERE_L)
        _punto(t, x, y + 1, E_POLVERE)
    for x, dy in ((23, 0), (24, 0), (25, 0), (23, -1), (23, 2), (24, 1)):
        _punto(t, x, y + dy, E_GRIGIO_L if dy <= 0 else E_GRIGIO)
    _punto(t, 26, y, E_BIANCO)
    for x in (9, 10, 11):                       # le alette
        _punto(t, x, y - 1, E_ROSSO)
        _punto(t, x, y + 2, E_ROSSO_S)
    contorna_effetto(t)
    scia = 3 + (k % 2) * 3 + k // 2
    for x in range(8 - scia, 8):                # i fili d'aria, senza contorno: sono aria
        if (x + k) % 2 == 0:
            _punto(t, x, y - 2, E_BIANCO)
        _punto(t, x + 1, y + 3, E_GRIGIO_L if (x + k) % 3 else 0)
    return t


def contorna_effetto(t, colore=CONTORNO):
    """Gli effetti di luce non hanno contorno (sono luce); le schegge e la polvere si'."""
    pieni = {(x, y) for y in range(32) for x in range(32) if t[y][x]}
    for (x, y) in pieni:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            u, v = x + dx, y + dy
            if 0 <= u < 32 and 0 <= v < 32 and (u, v) not in pieni:
                t[v][u] = colore
    return t


EFFETTI = (("SCIA", scia), ("SCINTILLA", scintilla), ("RAGGIO", raggio), ("FIAMMA", fiamma), ("AURA", aura),
           ("SCUDO", scudo), ("SCHEGGE", lambda k: contorna_effetto(schegge(k))), ("POLVERE", polvere), ("DARDO", dardo))


def effetti():
    """Tutti i fotogrammi degli effetti, in ordine: effetto per effetto, quattro fotogrammi ciascuno."""
    return [pittore(k) for _, pittore in EFFETTI for k in range(FOTOGRAMMI_EFFETTO)]


# --- i lampi: una palette intera dello stesso colore (il contorno resta) -----------------------------
LAMPI = (("BIANCO", ("pietra calcarea", 5), ("neutri", 3)), ("FUOCO", ("vermiglio comunale", 3), ("vermiglio comunale", 2)),
         ("LUCE", ("oro e bronzo", 3), ("oro e bronzo", 2)))


def palette_lampo(chiaro, scuro):
    """Il lampo: tutta la figura del colore chiaro, il contorno del colore scuro (si legge ancora la sagoma)."""
    return [("neutri", 0), scuro] + [chiaro] * 14


# --- la tavola di controllo --------------------------------------------------------------------------
def tavola(percorso, scala=4):
    from PIL import Image, ImageDraw
    import stile as S
    pal_stile = S.carica("palette")
    gruppi = [(n, p, False) for n, p in SANTI] + [(n, p, True) for n, p in NEMICI]
    colonne = len(POSE)
    cella = 64 * scala + 8
    im = Image.new("RGB", (colonne * cella + 120, len(gruppi) * cella + 30), (232, 226, 210))
    d = ImageDraw.Draw(im)
    for j, nome in enumerate(POSE):
        d.text((120 + j * cella + 4, 8), nome, fill=(40, 30, 30))
    for i, (nome, pittore, nemico) in enumerate(gruppi):
        d.text((6, 30 + i * cella + 20), nome.lower(), fill=(40, 30, 30))
        for j, (pal, px) in enumerate(pose_di(pittore, nemico)):
            colori = [S.rgb_di(S.colore(pal_stile, r)) for r in pal]
            for y, riga in enumerate(px):
                for x, c in enumerate(riga):
                    if c:
                        x0, y0 = 120 + j * cella + x * scala, 30 + i * cella + y * scala
                        d.rectangle([x0, y0, x0 + scala - 1, y0 + scala - 1], fill=colori[c])
    im.save(percorso)


if __name__ == "__main__":
    tavola(sys.argv[1] if len(sys.argv) > 1 else "tavola_sagome.png")
