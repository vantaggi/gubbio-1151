#!/usr/bin/env python3
"""La citta' allo standard grafico (pezzo EDI): case, suolo, ombre, contorni e vita dei fondali.

Lo standard e' /mnt/project-files/stile_dati/STANDARD_GRAFICO.md (le sigle C*, L*, P*, F*, M* qui sotto sono
le sue regole). Il generatore (tools/genera_mondo.py) compone il fondale di un'area con i tile di sempre e le
tele dei monumenti; poi questo modulo lo ridipinge in pixel, sull'area intera, in quest'ordine:

1. le case: i blocchi di muro "#" della citta' si dividono in case. Ogni casa che ha davanti (in basso sullo
   schermo) una via mostra la facciata in piedi, alta fino a 4 tile (M2: la porta e' alta quanto una figura),
   di conci irregolari (F2) con porta, finestre, a volte la porta del morto o la bottega (F5); sopra la
   facciata il tetto di coppi con il colmo, la falda in luce e quella in ombra, la gronda (F1). Le case
   cambiano larghezza, tono del tetto e comignolo (F4). Le collisioni non cambiano: facciata e tetto stanno
   sulle stesse celle solide di prima.
2. il suolo: lastrico, selciato e corsi ridisegnati a pietre irregolari su un motivo di 48 pixel che non
   mostra il tile che si ripete (F3, F4), nei toni medi (C5), con qualche dettaglio sparso (erba fra le
   pietre, una pietra consumata).
3. la vita (F7 e la richiesta di Cioti del 4 nov: la citta' in fermento per l'assedio): stendardi del Comune
   e del quartiere alle finestre, fiaccole, botti, sacchi, casse e fasci di lance appoggiati alle facciate,
   panni stesi e festoni sopra le vie strette. Stanno su celle gia' solide (la facciata) o sono sospesi
   sopra la via: non cambiano dove si cammina.
4. le ombre portate (L4): ogni cosa alta proietta l'ombra a destra e in basso sul suolo, nel tono scuro del
   suolo (C4: mai il nero).
5. il contorno selettivo (P2): il bordo di edifici e alberi verso il suolo prende il tono piu' scuro del
   suo materiale; il quasi nero resta solo nei vani (C4).

I colori sono riferimenti (rampa, tono) della Guida (C1). Alla fine genera_mondo sceglie per ogni tile 8x8 uno
dei BANCHI di 16 colori (la palette dei fondali e' di 4 banchi: 64 colori, una palette per tile come vuole
l'hardware) e lo indicizza.
"""
import math

P, T, V, A, L, O, R, N = ("pietra calcarea", "cotto e coppi", "verde dei monti", "cielo e acqua", "legno e cuoio",
                          "oro e bronzo", "vermiglio comunale", "neutri")
NERO = (N, 0)
FONDO = (N, 0)

# La palette di sempre dei fondali (PALETTE_FONDALI di genera_mondo.py): il banco 0. I pittori di prima la usano
# per indice (1 contorno, 2..5 pietra, 6..9 cotto, 10 e 11 verde, 12 e 13 acqua, 14 e 15 legno).
PALETTE_BASE = [(N, 0), (N, 0), (P, 1), (P, 2), (P, 4), (P, 5), (T, 1), (T, 2), (T, 3), (T, 4), (V, 1), (V, 3),
                (A, 2), (A, 4), (L, 1), (L, 3)]

# --- i banchi della palette dei fondali ----------------------------------------------------------------
# Il banco 0 e' la palette di sempre (PALETTE_FONDALI di genera_mondo.py, che la definisce): ci stanno la gola,
# il monte e tutto quello che non cambia. Gli altri tre li aggiunge questo pezzo.
BANCO_TETTI = [FONDO, NERO, (T, 0), (T, 1), (T, 2), (T, 3), (T, 4), (T, 5), (P, 0), (P, 1), (P, 2), (P, 3), (P, 4),
               (L, 0), (L, 1), (L, 2)]
BANCO_PIETRA = [FONDO, NERO, (P, 0), (P, 1), (P, 2), (P, 3), (P, 4), (P, 5), (L, 0), (L, 1), (L, 2), (O, 1), (O, 2),
                (T, 1), (T, 2), (N, 2)]
BANCO_VITA = [FONDO, NERO, (R, 1), (R, 2), (R, 3), (O, 1), (O, 2), (O, 3), (L, 0), (L, 1), (L, 2), (P, 1),
              (P, 2), (P, 3), (A, 2), (V, 2)]
BANCO_VERDE = [FONDO, NERO, (V, 0), (V, 1), (V, 2), (V, 3), (V, 4), (A, 1), (A, 2), (A, 3), (P, 1), (P, 2), (P, 3),
               (P, 4), (L, 0), (L, 1)]
BANCO_GIARDINO = [FONDO, NERO, (V, 0), (V, 1), (V, 2), (V, 3), (L, 0), (L, 1), (R, 2), (R, 3), (O, 2), (O, 3), (P, 2),
                  (P, 3), (P, 4), (A, 2)]
BANCHI_NUOVI = [BANCO_TETTI, BANCO_PIETRA, BANCO_VITA, BANCO_VERDE, BANCO_GIARDINO]

# I colori dei quartieri (dal Torneo, /mnt/project-files/simboli/): solo dove l'area porta il nome del quartiere.
# Altrove gli stendardi sono quelli del Comune (rosso, il monte a cinque cime d'oro, senza lambello).
QUARTIERE = {"san_martino": (A, 2), "san_pietro": (V, 2), "sant_andrea": (R, 2)}


def h32(*v):
    """Un caso fisso dai numeri dati, in [0, 1)."""
    x = 2166136261
    for n in v:
        x = ((x ^ (int(n) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    x ^= x >> 15
    x = (x * 2246822519) & 0xFFFFFFFF
    x ^= x >> 13
    return (x & 0xFFFFFF) / float(1 << 24)


def scuro(c, n=1):
    """Lo stesso materiale, n toni piu' scuro (mai sotto il primo tono della rampa: il nero non e' un'ombra)."""
    rampa, tono = c
    if c == NERO:
        return c
    return (rampa, max(0, tono - n))


def chiaro(c, n=1, massimo=5):
    rampa, tono = c
    if c == NERO:
        return c
    limite = {P: 5, T: 5, V: 4, A: 4, L: 3, O: 3, R: 3, N: 4}.get(rampa, 3)
    return (rampa, min(limite, massimo, tono + n))


# --- la tela dell'area -----------------------------------------------------------------------------------
class Quadro:
    """L'area intera in pixel: un riferimento di colore per pixel e, per ogni pixel, che cosa e'.

    tipo: "suolo" (ci si cammina), "casa", "tetto", "edificio" (monumenti, porte, mura), "verde" (alberi,
    siepi), "basso" (muretti, vasche, panche), "acqua", "vuoto"."""

    def __init__(self, w, h):
        self.w, self.h = w * 8, h * 8
        self.px = [[FONDO] * self.w for _ in range(self.h)]
        self.tipo = [["vuoto"] * self.w for _ in range(self.h)]
        self.alto = [[0] * self.w for _ in range(self.h)]   # l'altezza in pixel che proietta l'ombra
        self.livello = {}                                     # (x, y) di un tetto -> quanto e' alto (0..2)
        self.elementi = {}

    def livella(self, x0, x1, y0, y1, livello):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.livello[(x, y)] = livello

    def conta(self, nome, n=1):
        self.elementi[nome] = self.elementi.get(nome, 0) + n

    def punto(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = c

    def rett(self, x0, y0, w, h, c):
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                self.punto(x, y, c)

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[y][x]
        return None


# --- il suolo (F3, F4, C5) ---------------------------------------------------------------------------------
MOTIVO = 48   # il motivo del suolo si ripete ogni 48 pixel = 3 celle da 16: mai due celle uguali di fila


def _motivo_lastre(lato, alte, lunghe, toni, giunto, seme, largo=None):
    """Lastre posate a file su un toro largo x lato (largo = lato se non e' dato) (F3): ogni fila alta 'alte'
    pixel (scelte a caso), lastre lunghe 'lunghe' (min, max), sfalsate; il giunto a destra e in basso nel tono
    d'ombra (L1), lo spigolo in alto a sinistra un tono piu' chiaro (contorni morbidi), il corpo in uno dei
    toni medi (C5)."""
    largo = largo or lato
    out = [[None] * largo for _ in range(lato)]
    file, y = [], 0
    while y < lato:
        a = alte[int(h32(seme, y, 1) * len(alte))]
        if lato - y - a < min(alte) and lato - y != a:
            a = lato - y
        file.append((y, a))
        y += a
    for f, (y0, a) in enumerate(file):
        x0 = int(h32(seme, f, 2) * lunghe[1])
        tagli, x = [x0], x0
        while True:
            x += lunghe[0] + int(h32(seme, f, len(tagli), 3) * (lunghe[1] - lunghe[0] + 1))
            if x >= x0 + largo - 2:
                break
            tagli.append(x)
        tagli.append(x0 + largo)
        for k in range(len(tagli) - 1):
            corpo = toni[int(h32(seme, f, k, 4) * len(toni))]
            for yy in range(y0, y0 + a):
                for xx in range(tagli[k], tagli[k + 1]):
                    if yy == y0 + a - 1 or xx == tagli[k + 1] - 1:
                        c = giunto
                    elif yy == y0 or xx == tagli[k]:
                        c = chiaro(corpo, 1, 4)
                    else:
                        c = corpo
                    out[yy % lato][xx % largo] = c
    return out


_MOTIVI = {}


def motivo(nome):
    if nome not in _MOTIVI:
        if nome == "lastrico":      # le lastre grandi delle piazze
            m = _motivo_lastre(32, (8, 8, 8, 8), (12, 22), [(P, 3), (P, 3), (P, 3), (P, 2)], (P, 1), 11)
        elif nome == "suolo":       # il lastricato dei larghi
            m = _motivo_lastre(32, (6, 6, 5, 7), (7, 13), [(P, 3), (P, 2), (P, 2)], (P, 1), 12)
        elif nome == "strada":      # il selciato delle vie: pietre piccole a file strette
            m = _motivo_lastre(32, (4, 4, 4, 4), (4, 7), [(P, 2), (P, 2), (P, 3)], (P, 1), 13)
        elif nome == "muro_chiaro":  # i conci dei monumenti di calcare chiaro
            m = _motivo_lastre(8, (4, 4), (6, 12), [(P, 4), (P, 4), (P, 3)], (P, 2), 16, largo=16)
        elif nome == "muro":        # i conci delle facciate (F2): file di 3-4 pixel, conci 5-10
            m = _motivo_lastre(8, (4, 4), (8, 8), [(P, 3), (P, 3), (P, 2)], (P, 1), 14, largo=8)
        elif nome == "muro_secco":  # il muretto a secco del monte: pietre piccole e irregolari
            m = _motivo_lastre(8, (3, 3, 2), (3, 6), [(P, 3), (P, 2), (P, 3)], (P, 1), 17, largo=16)
        elif nome == "muro_scuro":
            m = _motivo_lastre(8, (4, 4), (8, 8), [(P, 2), (P, 2), (P, 3)], (P, 1), 15, largo=8)
        else:
            raise KeyError(nome)
        _MOTIVI[nome] = m
    return _MOTIVI[nome]


def colore_suolo(nome, x, y):
    m = motivo(nome)
    return m[y % len(m)][x % len(m[0])]


# I dettagli sparsi del suolo (F7): pochi, a caso fisso, ognuno 2-6 pixel.
def _ciuffo(q, x, y):
    for dx, dy, c in ((1, 0, (V, 2)), (0, 1, (V, 0)), (2, 1, (V, 2)), (1, 1, (V, 0))):
        q.punto(x + dx, y + dy, c)


def _pietra_consumata(q, x, y):
    for dy in range(2):
        for dx in range(4):
            q.punto(x + dx, y + dy, (P, 4) if dy == 0 else (P, 3))
    q.punto(x + 4, y + 1, (P, 1))


def _pozzanghera(q, x, y):
    for dy in range(3):
        for dx in range(6 - (dy == 2) * 2):
            q.punto(x + dx + (dy == 2), y + dy, (N, 2) if (dx + dy) % 3 else (P, 4))


DETTAGLI_SUOLO = (_ciuffo, _pietra_consumata, _ciuffo, _pozzanghera)


# --- le case (M2, F1, F2, F5) -------------------------------------------------------------------------------
ALTEZZA_FACCIATA_MAX = 5   # tile: 40 pixel, la porta alta 28 (il giocatore e' alto 22-24, M2) e il piano di sopra


class Casa:
    def __init__(self, x0, x1, yb, fh, n):
        self.x0, self.x1, self.yb, self.fh, self.n = x0, x1, yb, fh, n
        self.tetto = (2, 3, 3, 3, 3, 3, 3, 3, 4, 4)[int(h32(n, 7) * 10)]   # il tono base dei coppi
        self.comignolo = h32(n, 8) < 0.45
        self.bottega = (x1 - x0 + 1) >= 3 and h32(n, 9) < 0.35
        self.morto = not self.bottega and (x1 - x0 + 1) >= 3 and h32(n, 10) < 0.3
        self.pietra = 3 if h32(n, 11) < 0.65 else 2                 # il tono dei conci: 3 o 2


def _segmenti(xs):
    """Le corse di x consecutive."""
    out, corsa = [], []
    for x in sorted(xs):
        if corsa and x != corsa[-1] + 1:
            out.append(corsa)
            corsa = []
        corsa.append(x)
    if corsa:
        out.append(corsa)
    return out


def dividi_in_case(griglia, case_celle, calpestabile):
    """Le case con facciata: per ogni riga, le celle di casa con una cella calpestabile sotto, divise in case
    larghe 2-5 tile. La facciata e' alta quanto lo permette la colonna di case sopra (lasciando almeno una
    riga di tetto), al massimo ALTEZZA_FACCIATA_MAX, uguale per tutta la casa."""
    hgt = len(griglia)
    sotto_via = {}
    for (x, y) in case_celle:
        if y + 1 < hgt and calpestabile(x, y + 1):
            sotto_via.setdefault(y, []).append(x)
    case = []
    n = 0
    for y in sorted(sotto_via):
        for corsa in _segmenti(sotto_via[y]):
            i = 0
            while i < len(corsa):
                resto = len(corsa) - i
                larga = 2 + int(h32(corsa[i], y, 5) * 4)          # 2..5
                if resto - larga == 1:
                    larga += 1
                larga = min(larga, resto)
                xs = corsa[i:i + larga]
                colonna = []
                for x in xs:
                    k = 0
                    while (x, y - k) in case_celle:
                        k += 1
                    colonna.append(k)
                fh = max(1, min(ALTEZZA_FACCIATA_MAX, min(colonna) - 1))
                case.append(Casa(xs[0], xs[-1], y, fh, n))
                n += 1
                i += larga
    return case


def dipingi_tetto(q, px0, px1, py0, py1, tono, n, luce_sx=True, gronda=True, verticale=None):
    """Un tetto di coppi visto in 3/4 (F1). Colmo orizzontale (il tetto lungo la via): la falda lontana in alto,
    stretta e un tono piu' scura (guarda a nord), il colmo chiaro, la falda vicina nel tono base, la gronda
    d'ombra in basso. Colmo verticale (le case strette e profonde): la falda sinistra in luce, la destra un
    tono sotto. Coppi a canali di 4 pixel, file sfalsate, tre toni; il bordo sinistro prende la luce, i due
    pixel a destra l'ombra (L1). Ritorna la riga (o la colonna) del colmo."""
    alto, largo = py1 - py0 + 1, px1 - px0 + 1
    if verticale is None:
        verticale = False
    # il colmo cade sempre alla stessa riga dentro il suo tile (i tile dei tetti si ripetono: la ROM risparmia)
    colmo = (px0 + (largo // 16) * 8 + 3) if verticale else (py0 + ((alto // 8 - 1) // 3) * 8 + 2)
    for y in range(py0, py1 + 1):
        for x in range(px0, px1 + 1):
            if verticale:
                lontana = x > colmo
                u, v = (y - py0), (x - px0)
            else:
                lontana = y < colmo
                u, v = (x - px0), (y - py0)
            base = tono - (1 if lontana else 0)
            fila = (v + (2 if (u // 4) % 2 else 0)) % 4
            canale = u % 4
            c = (T, base)
            if canale == 0:
                c = (T, base + 1)
            elif canale == 3 or fila == 3:
                c = (T, base - 1)
            if (x if verticale else y) == colmo:
                c = (T, min(5, tono + 1))
            elif (x if verticale else y) == colmo + 1:
                c = (T, tono - 2)
            if x == px0 and luce_sx:
                c = chiaro(c, 1)
            if x >= px1 - 1:
                c = scuro(c, 1)
            if gronda and y == py1:
                c = (T, max(0, tono - 3))
            elif gronda and y == py1 - 1:
                c = (T, max(1, tono - 2))
            q.punto(x, y, c)
    return colmo


def _conci(q, x0, y0, x1, y1, tono, seme):
    """Muro di conci irregolari (F2) dal motivo del muro, a coordinate assolute (i tile si ripetono e la ROM
    risparmia): file alte 3-4 pixel, conci lunghi 5-10, due toni, il giunto nel tono d'ombra."""
    nome = "muro" if tono >= 3 else "muro_scuro"
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            q.punto(x, y, colore_suolo(nome, x, y))


def _vano_arco(q, x0, y0, w, h, dentro, stipite=(P, 4), strombo=(P, 1)):
    """Un vano con l'arco a tutto sesto (F5): lo stipite chiaro a sinistra e in alto, lo strombo d'ombra a
    destra e in alto dentro il vano, l'interno nel colore dato. Ritorna le righe interne."""
    r = w / 2.0
    for y in range(h):
        for x in range(w):
            dx = x + 0.5 - r
            yy = y + 0.5
            if yy < r and dx * dx + (r - yy) ** 2 > r * r:
                continue
            bordo = x == 0 or x == w - 1 or (yy < r and dx * dx + (r - yy) ** 2 > (r - 1.2) ** 2)
            if bordo:
                c = stipite if x < w / 2 else (P, 2)
            elif x == w - 2 or (yy < r + 1 and dx * dx + (r - yy - 1) ** 2 > (r - 2.2) ** 2):
                c = strombo
            else:
                c = dentro(x, y)
            q.punto(x0 + x, y0 + y, c)


def _porta(q, x0, ybase, w, h, seme):
    """La porta di casa: battenti di legno a tavole, la maniglia di bronzo (F5), la soglia chiara."""
    def legno(x, y):
        if x % 3 == 0:
            return (L, 0)
        return (L, 1) if x < w // 2 else (L, 1 if y % 7 else 0)
    _vano_arco(q, x0, ybase - h, w, h, legno)
    mx = x0 + w // 2 + 1
    q.punto(mx, ybase - h // 2 + 1, (O, 2))
    q.punto(mx, ybase - h // 2 + 2, (O, 1))
    q.rett(x0, ybase - 1, w, 1, (P, 4))
    q.conta("porta")


def _porta_del_morto(q, x0, ybase, h):
    """La porta del morto: stretta, rialzata, murata. A Gubbio la si riconosce accanto al portone."""
    alta = h - 6
    _vano_arco(q, x0, ybase - 6 - alta, 5, alta, lambda x, y: (P, 2) if (y // 3) % 2 else (P, 1))
    q.conta("porta_del_morto")


def _finestra(q, x0, y0, w, h, seme, imposte, chiusa=False):
    """Finestra ad arco col davanzale e la sua ombra; a volte con le imposte di legno o il vaso di fiori.
    chiusa: scuri di legno serrati, per le finestrelle basse che, nere, sembrerebbero porte (M2)."""
    if chiusa:
        _vano_arco(q, x0, y0, w, h, lambda x, y: (L, 0) if x == w // 2 else (L, 1))
    else:
        _vano_arco(q, x0, y0, w, h, lambda x, y: NERO)
    q.rett(x0 - 1, y0 + h, w + 2, 1, (P, 4))
    q.rett(x0, y0 + h + 1, w + 1, 1, (P, 1))
    if imposte:
        colore = (L, 1) if h32(seme, 1) < 0.6 else (L, 2)
        q.rett(x0 - 2, y0 + 2, 2, h - 2, colore)
        q.rett(x0 + w, y0 + 2, 2, h - 2, scuro(colore) if colore[0] == L else colore)
        q.punto(x0 - 2, y0 + 2, chiaro(colore) if colore[0] == L else colore)
    q.conta("finestra")


def _bottega(q, x0, ybase, w, h, seme):
    """La bottega al piano terra: un arco largo chiuso dalle imposte di legno con la sbarra, davanti il banco."""
    def dentro(x, y):
        # le imposte chiuse, a tavole verticali (solo dove si entra il vano e' aperto e luminoso: dipingi_ingressi)
        if y >= h - 6:
            return (L, 0)
        tavola = (x // 3) % 2
        if x % 3 == 2:
            return (L, 0)
        return (L, 2) if tavola == 0 and x < w // 2 else (L, 1)
    _vano_arco(q, x0, ybase - h, w, h, dentro)
    # la sbarra di ferro che tiene chiuse le imposte
    q.rett(x0 + 2, ybase - h // 2 - 1, w - 4, 1, (L, 0))
    # il banco
    q.rett(x0 - 1, ybase - 6, w + 2, 2, (L, 2))
    q.rett(x0 - 1, ybase - 4, w + 2, 3, (L, 1))
    q.rett(x0 + w, ybase - 4, 1, 3, (L, 0))
    q.conta("bottega")


def dipingi_casa(q, casa, w_celle):
    """La facciata in piedi della casa: conci, gronda d'ombra, spigoli, zoccolo, porta e finestre."""
    X0, X1 = casa.x0 * 8, casa.x1 * 8 + 7
    Y1 = casa.yb * 8 + 7
    Y0 = (casa.yb - casa.fh + 1) * 8
    _conci(q, X0, Y0, X1, Y1, casa.pietra, casa.n * 31 + 7)
    # la gronda proietta l'ombra sulla facciata (L4): due righe in alto
    for y in range(Y0, min(Y0 + 2, Y1 + 1)):
        for x in range(X0, X1 + 1):
            q.punto(x, y, (P, 1) if y == Y0 else scuro(q.get(x, y)))
    # lo spigolo sinistro in luce, il destro in ombra (F2, L1); lo zoccolo piu' scuro
    for y in range(Y0 + 2, Y1 + 1):
        q.punto(X0, y, (P, 4))
        q.punto(X1, y, (P, 1))
        q.punto(X1 - 1, y, scuro(q.get(X1 - 1, y)))
    for y in range(Y1 - 2, Y1 + 1):
        for x in range(X0 + 1, X1 - 1):
            c = q.get(x, y)
            q.punto(x, y, (P, 1) if c == (P, 1) else (P, 2))
    larga = X1 - X0 + 1
    alta = Y1 - Y0 + 1
    if alta < 16:
        # facciata bassa: solo una finestrella
        if larga >= 12:
            _finestra(q, X0 + larga // 2 - 2, Y0 + 3, 5, max(4, alta - 8), casa.n, False, chiusa=True)
        return
    # il piano terra: porta (o bottega) e, se c'e' posto, la porta del morto
    hp = min(28, alta - 4)       # M2: porte e botteghe di almeno 26 pixel dove la facciata e' alta 4-5 tile
    if casa.bottega:
        wb = min(larga - 6, 18)
        bx = X0 + 8 * int(h32(casa.n, 12) * max(1, (larga - wb) // 8)) + 3
        _bottega(q, bx, Y1, wb, hp, casa.n)
        porta_x, porta_w = bx, wb
    else:
        pw = 10 if larga >= 20 else 8
        posti = max(1, larga - pw - 6)
        px = X0 + 8 * int(h32(casa.n, 13) * max(1, posti // 8)) + (3 if pw == 10 else 4)
        _porta(q, px, Y1, pw, hp, casa.n)
        porta_x, porta_w = px, pw
        if casa.morto and px - X0 >= 9:
            _porta_del_morto(q, px - 7, Y1, hp)
        elif casa.morto and X1 - (px + pw) >= 9:
            _porta_del_morto(q, px + pw + 2, Y1, hp)
    # le finestre: al piano di sopra se la facciata e' alta 5 tile, accanto alla porta se c'e' posto
    if alta >= 40:
        k = max(1, (larga - 4) // 12)
        passo = larga / (k + 1)
        for i in range(k):
            fx = (int(X0 + passo * (i + 1)) // 8) * 8 + 1
            _finestra(q, fx, Y0 + 3, 6, 7, casa.n * 5 + i, h32(casa.n, i, 14) < 0.5)
            casa_finestre = getattr(casa, "finestre", [])
            casa_finestre.append((fx, Y0 + 3))
            casa.finestre = casa_finestre
    else:
        for fx in (X0 + 1, X1 - 14):
            if fx + 6 < porta_x - 1 or fx > porta_x + porta_w + 1:
                _finestra(q, fx, Y0 + 4, 6, 7, casa.n * 3 + fx, False)
                casa.finestre = getattr(casa, "finestre", []) + [(fx, Y0 + 4)]
    casa.porta = (porta_x, porta_w)


# --- la vita (F7, Cioti 4 nov: la citta' in fermento) -----------------------------------------------------
def _stendardo(q, x, y, colore, comune):
    """Uno stendardo appeso sotto una finestra: l'asta di legno, il drappo che finisce a coda di rondine.
    Il Comune: rosso col monte d'oro (il monte a cinque cime, ridotto a tre punte di un pixel a questa
    misura); il quartiere: il suo colore con la banda chiara."""
    q.rett(x - 1, y, 7, 1, (L, 1))
    for yy in range(1, 12):
        for xx in range(5):
            if yy >= 10 and xx == 2:
                continue
            if yy == 11 and xx in (1, 3):
                continue
            c = colore
            if xx == 0:
                c = chiaro(colore, 1, 3)
            elif xx == 4:
                c = scuro(colore, 1)
            q.punto(x + xx, y + yy, c)
    if comune:
        for xx, yy in ((1, 6), (2, 5), (3, 6), (1, 7), (2, 7), (3, 7), (2, 6)):
            q.punto(x + xx, y + yy, (O, 2) if yy < 7 else (O, 1))
    else:
        q.rett(x + 1, y + 3, 3, 1, (O, 2))
    q.conta("stendardo")


def _fiaccola(q, x, y):
    """La fiaccola nel suo anello di ferro sul muro, accesa: si prepara la notte di guardia."""
    q.punto(x, y + 4, (L, 0))
    q.punto(x + 1, y + 4, (L, 0))
    q.rett(x + 1, y + 2, 1, 2, (L, 1))
    q.punto(x + 1, y, (R, 3))
    q.punto(x, y + 1, (O, 2))
    q.punto(x + 1, y + 1, (O, 3))
    q.punto(x + 2, y + 1, (R, 2))
    q.conta("fiaccola")


def _botte(q, x, ybase):
    """Una botte in piedi (M6): in cima il fondo visto dall'alto, un'ellisse alta un terzo della larghezza con il
    cerchio di ferro; sotto il corpo panciuto di doghe, la luce a sinistra, due cerchi di ferro."""
    for yy in range(10):
        if yy < 3:
            larga = (5, 7, 5)[yy]
        else:
            larga = 7 if 4 <= yy <= 8 else 6
        x0 = x + (7 - larga) // 2
        for xx in range(larga):
            if yy < 3:
                c = (L, 0) if yy in (0, 2) or xx in (0, larga - 1) else (L, 2)
            else:
                c = (L, 2) if xx == 0 else ((L, 0) if xx >= larga - 2 else (L, 1))
                if yy in (4, 8):
                    c = (P, 1) if xx else (P, 2)
            q.punto(x0 + xx, ybase - 10 + yy, c)
    q.conta("botte")


def _sacco(q, x, ybase):
    """Un sacco di grano chiuso: la bocca legata in cima, la tela chiara, la luce a sinistra."""
    for yy in range(7):
        larga = [2, 4, 5, 6, 6, 6, 5][yy]
        x0 = x + (6 - larga) // 2
        for xx in range(larga):
            q.punto(x0 + xx, ybase - 7 + yy, (P, 3) if xx < larga - 2 else (P, 2))
    q.punto(x + 2, ybase - 6, (L, 0))
    q.punto(x + 3, ybase - 6, (L, 0))
    q.conta("sacco")


def _cassa(q, x, ybase):
    """Una cassa (M6): il coperchio visto dall'alto in cima (3 pixel, piu' chiaro), la faccia davanti intera con
    le assi e la traversa, l'ombra a destra."""
    q.rett(x, ybase - 9, 8, 3, (L, 2))
    q.rett(x, ybase - 7, 8, 1, (L, 1))
    q.rett(x, ybase - 6, 8, 6, (L, 1))
    q.rett(x, ybase - 6, 8, 1, (L, 0))
    q.rett(x, ybase - 3, 8, 1, (L, 0))
    q.rett(x + 6, ybase - 9, 2, 9, (L, 0))
    q.conta("cassa")


def _lance(q, x, ybase):
    """Un fascio di lance appoggiato al muro: le aste di legno, le punte di ferro."""
    for k in range(3):
        xx = x + k * 2
        q.rett(xx, ybase - 18, 1, 18, (L, 1) if k != 2 else (L, 0))
        q.punto(xx, ybase - 20, (P, 3))
        q.punto(xx, ybase - 19, (P, 2))
    q.rett(x - 1, ybase - 8, 7, 1, (L, 0))
    q.conta("lance")


def _ombra_a_terra(q, x0, ybase, w):
    """La piccola ombra di un oggetto basso sul suolo davanti (L4: 1-2 pixel)."""
    for x in range(x0 + 1, x0 + w + 1):
        c = q.get(x, ybase + 1)
        if c and q.tipo[ybase + 1][x] == "suolo":
            q.punto(x, ybase + 1, scuro(c, 1))


def vita_delle_case(q, case, aid, seme_area):
    """Stendardi alle finestre alte, fiaccole, e alla base delle facciate botti, sacchi, casse e lance."""
    colore_q = QUARTIERE.get(aid)
    for casa in case:
        X0, X1 = casa.x0 * 8, casa.x1 * 8 + 7
        Y1 = casa.yb * 8 + 7
        finestre = getattr(casa, "finestre", [])
        porta = getattr(casa, "porta", None)
        Y0 = (casa.yb - casa.fh + 1) * 8
        if casa.fh >= 3 and h32(casa.n, 21, seme_area) < 0.6:
            # lo stendardo appeso sotto la gronda, in un tratto di muro libero (non sopra la porta, M6/I3)
            occupati = [(porta[0] - 2, porta[0] + porta[1] + 1)] if porta else []
            liberi = [x for x in range(X0 + 2, X1 - 6, 8) if all(x + 6 < a or x > b for a, b in occupati)]
            if liberi:
                comune = colore_q is None or h32(casa.n, 22) < 0.5
                fx = liberi[int(h32(casa.n, 27) * len(liberi))]
                _stendardo(q, fx, Y0 + 2, (R, 2) if comune else colore_q, comune)
        if casa.fh >= 3 and porta and h32(casa.n, 23, seme_area) < 0.35:
            px, pw = porta
            fx = px + pw + 2 if px + pw + 5 < X1 else px - 4
            _fiaccola(q, fx, Y1 - 20)
        # alla base: un oggetto per casa, in un angolo libero
        if casa.fh >= 2 and porta:
            px, pw = porta
            liberi = [x for x in (X0 + 2, X1 - 9) if x + 8 < px - 1 or x > px + pw + 1]
            if liberi and h32(casa.n, 24, seme_area) < 0.7:
                x = liberi[int(h32(casa.n, 25) * len(liberi))]
                scelta = int(h32(casa.n, 26, seme_area) * 4)
                [_botte, _sacco, _cassa, _lance][scelta](q, x, Y1)
                _ombra_a_terra(q, x, Y1, 8)


def panni_stesi(q, griglia, calpestabile, case_celle, aid):
    """Sopra le vie strette che scendono sullo schermo, da un tetto all'altro: una corda con i panni o un festone
    di bandierine. Sono sospesi: non tolgono niente a dove si cammina. La loro ombra cade piu' in basso a destra
    (L4), sul selciato."""
    hgt, wid = len(griglia), len(griglia[0])
    fatte = 0
    gia = []          # le file che hanno gia' una corda (una ogni 7 righe al piu')
    for y in range(2, hgt - 2):
        for x in range(1, wid - 2):
            if (x - 1, y) not in case_celle or not calpestabile(x, y):
                continue
            k = x
            while k < wid and calpestabile(k, y):
                k += 1
            if k >= wid or (k, y) not in case_celle or not 2 <= k - x <= 6:
                continue
            if h32(x, y, 31, len(aid)) > 0.1 or any(abs(y - yy) < 7 for yy in gia):
                continue
            gia.append(y)
            festone = h32(x, y, 32) < 0.5
            _corda(q, x * 8 - 2, k * 8 + 1, y * 8 + 1, festone, aid, x + y)
            fatte += 1
            q.conta("panni" if not festone else "festone")
    return fatte


def _corda(q, px0, px1, py, festone, aid, seme):
    """La corda che pende un poco al centro; i panni (lino chiaro, una tovaglia a strisce, una camicia) o le
    bandierine del Comune e del quartiere; ogni cosa con il bordo destro e la riga in basso un tono sotto (L1)
    e l'ombra che cade 3 pixel a destra e 7 sotto, sul suolo."""
    cose = []
    for xx in range(px0, px1 + 1):
        t = (xx - px0) / max(1, px1 - px0)
        yy = py + int(round(math.sin(t * math.pi) * 3))
        cose.append((xx, yy, (L, 0)))
    passo = 6 if festone else 9
    for i, xx in enumerate(range(px0 + 4, px1 - 5, passo)):
        t = (xx - px0) / max(1, px1 - px0)
        yy = py + int(round(math.sin(t * math.pi) * 3)) + 1
        if festone:
            colori = [(R, 2), (O, 2), QUARTIERE.get(aid, (R, 3))]
            c = colori[i % 3]
            for dy in range(5):
                for dx in range(dy // 2, 5 - dy // 2):
                    cose.append((xx + dx, yy + dy, scuro(c) if dx == 4 - dy // 2 else c))
        else:
            c = [(P, 4), (P, 4), (A, 2), (R, 2), (O, 2)][int(h32(seme, i, 33) * 5)]
            alto = 5 + int(h32(seme, i, 34) * 3)
            for dy in range(alto):
                for dx in range(5):
                    cc = c
                    if c == (R, 2) and dx % 2:
                        cc = (P, 4)
                    if dx == 4 or dy == alto - 1:
                        cc = scuro(cc) if cc[0] != P else (P, 2)
                    cose.append((xx + dx, yy + dy, cc))
    for (xx, yy, c) in cose:
        sx, sy = xx + 3, yy + 7
        if 0 <= sx < q.w and 0 <= sy < q.h and q.tipo[sy][sx] == "suolo":
            v = q.px[sy][sx]
            q.px[sy][sx] = (P, 0) if v[1] <= 1 else (P, 1)
    for (xx, yy, c) in cose:
        q.punto(xx, yy, c)




# --- ombre portate e contorno selettivo -------------------------------------------------------------------
def ombre_portate(q, larghezza=4):
    """L4: chi e' alto proietta sul suolo l'ombra a destra e in basso, larga fino a 'larghezza' pixel con
    l'angolo a 45 gradi (P7); sul suolo il tono scende di uno (C4: il tono scuro del suolo, mai il nero)."""
    da_scurire = set()
    for y in range(q.h):
        for x in range(q.w):
            a = q.alto[y][x]
            if not a:
                continue
            w = max(1, min(larghezza, a // 4))
            for k in range(1, w + 1):
                xx, yy = x + k, y + k
                if xx < q.w and yy < q.h and q.tipo[yy][xx] == "suolo":
                    da_scurire.add((xx, yy))
                xx, yy = x + k, y
                if xx < q.w and q.tipo[yy][xx] == "suolo":
                    da_scurire.add((xx, yy))
    for (x, y) in da_scurire:
        c = q.px[y][x]
        if c[0] in (P, N):
            # il tono d'ombra del suolo: il corpo delle pietre scende al tono 1, i giunti allo 0
            q.px[y][x] = (P, 0) if c[1] <= 1 else (P, 1)
        elif c != NERO:
            q.px[y][x] = scuro(c, 1)


def cortili(libere, w, h):
    """I cortili e gli orti chiusi fra le case: blocchi 2x2 nella massa di tetti senza facciata, circondati da
    tetti su tutti i lati (si capisce che non ci si entra), al piu' uno ogni ~150 celle di massa, a caso fisso."""
    out = []
    preso = set()
    for (x, y) in sorted(libere, key=lambda c: (c[1], c[0])):
        if h32(x, y, 73) > 0.012:
            continue
        blocco = [(x + dx, y + dy) for dy in range(2) for dx in range(2)]
        anello = [(x + dx, y + dy) for dy in range(-1, 3) for dx in range(-1, 3)]
        if all(c in libere and c not in preso for c in anello):
            out.append((x, y))
            preso.update((x + dx, y + dy) for dy in range(-3, 5) for dx in range(-3, 5))
    return out


def dipingi_cortile(q, x, y, n):
    """Un orto chiuso 16x16 visto dall'alto: la terra e l'erba, un alberello (o il pozzo), l'ombra dei tetti che
    lo chiudono in alto e a sinistra (L4)."""
    X0, Y0 = x * 8, y * 8
    for yy in range(16):
        for xx in range(16):
            c = (V, 2) if (xx * 3 + yy * 5 + (xx * yy) % 4) % 7 else (V, 1)
            if (xx + 2 * yy) % 11 == 0:
                c = (V, 3)
            if yy < 3 or xx < 3:
                c = (V, 0) if c != (V, 3) else (V, 1)
            q.punto(X0 + xx, Y0 + yy, c)
    if h32(n, 74) < 0.6:
        # l'alberello: la chioma tonda in tre toni, la luce in alto a sinistra, l'ombra a destra e in basso
        cx, cy = X0 + 9, Y0 + 8
        for yy in range(-5, 6):
            for xx in range(-5, 6):
                d = xx * xx + yy * yy
                if d <= 22:
                    c = (V, 3) if xx + yy < -3 else ((V, 1) if xx + yy > 3 else (V, 2))
                    q.punto(cx + xx, cy + yy, c)
                elif d <= 30 and xx > 0 and yy > 0:
                    q.punto(cx + xx + 1, cy + yy + 1, (V, 0))
    else:
        # il pozzo: la vera di pietra, l'acqua scura
        for yy in range(6):
            for xx in range(6):
                bordo = xx in (0, 5) or yy in (0, 5)
                q.punto(X0 + 6 + xx, Y0 + 6 + yy, ((P, 4) if xx == 0 or yy == 0 else (P, 2)) if bordo else (A, 1))
        q.rett(X0 + 12, Y0 + 7, 1, 6, (V, 0))
    q.conta("cortile")


def ombre_dei_tetti(q):
    """L4 fra i tetti: una casa piu' alta proietta sul tetto piu' basso accanto l'ombra a destra e in basso, 3
    pixel per ogni piano di differenza. E' quello che fa leggere le case una per una."""
    da_scurire = set()
    for (x, y), l in q.livello.items():
        if l == 0:
            continue
        for k in range(1, 4):
            for xx, yy in ((x + k, y + k), (x + k, y), (x, y + k)):
                l2 = q.livello.get((xx, yy))
                if l2 is not None and l2 < l and q.tipo[yy][xx] == "tetto":
                    da_scurire.add((xx, yy))
    for (x, y) in da_scurire:
        q.px[y][x] = scuro(q.px[y][x], 1)


def contorno_selettivo(q):
    """P2: dove un edificio, una casa o un albero tocca il suolo, il suo pixel di bordo prende il tono piu'
    scuro del suo materiale (a destra e in basso) o un tono sotto (a sinistra e in alto). Il quasi nero che
    stava sul bordo esterno dei monumenti diventa il tono scuro della pietra; quello dei vani resta (C4)."""
    nuovi = {}
    for y in range(q.h):
        for x in range(q.w):
            if q.tipo[y][x] not in ("casa", "tetto", "edificio"):
                continue
            tipo = q.tipo[y][x]
            vicini = {(dx, dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                      if 0 <= x + dx < q.w and 0 <= y + dy < q.h and (q.tipo[y + dy][x + dx] == "suolo" or
                      (tipo == "edificio" and q.tipo[y + dy][x + dx] in ("casa", "tetto")))}
            if not vicini:
                continue
            c = q.px[y][x]
            if c == NERO:
                # il vecchio contorno nero di un monumento: diventa la pietra scura
                c = (P, 1)
            if (1, 0) in vicini or (0, 1) in vicini:
                nuovi[(x, y)] = (c[0], 0) if c[0] in (P, T, L, V) else scuro(c, 1)
            else:
                nuovi[(x, y)] = scuro(c, 1)
    for (x, y), c in nuovi.items():
        q.px[y][x] = c


# --- il verde: prati, vialetti, siepi, aiuole, alberi (L1, L4, P2, F3) ------------------------------------
def _motivo_prato():
    """L'erba su 32x32: il verde base, ciuffi chiari di due pixel in verticale, punti scuri radi, pochi fiori."""
    m = [[(V, 2)] * 32 for _ in range(32)]
    for i in range(70):
        x, y = int(h32(i, 81) * 32), int(h32(i, 82) * 32)
        m[y][x] = (V, 3)
        m[(y + 1) % 32][x] = (V, 3) if i % 3 else (V, 2)
        m[(y + 2) % 32][(x + 1) % 32] = (V, 1)
    for i in range(30):
        x, y = int(h32(i, 83) * 32), int(h32(i, 84) * 32)
        m[y][x] = (V, 1)
    for i in range(5):
        x, y = int(h32(i, 85) * 32), int(h32(i, 86) * 32)
        m[y][x] = (P, 4) if i % 2 else (O, 2)
    return m


def _motivo_ghiaia():
    """La ghiaia dei vialetti: sassolini chiari e medi su un fondo di pietra, nessuna riga che si ripete."""
    m = [[(P, 3)] * 32 for _ in range(32)]
    for i in range(160):
        x, y = int(h32(i, 87) * 32), int(h32(i, 88) * 32)
        m[y][x] = (P, 4) if i % 3 else (P, 2)
        if i % 5 == 0:
            m[y][(x + 1) % 32] = (P, 2)
    return m


_MOTIVI_VERDI = {}


def colore_verde(nome, x, y):
    if nome not in _MOTIVI_VERDI:
        _MOTIVI_VERDI[nome] = _motivo_prato() if nome == "prato" else _motivo_ghiaia()
    return _MOTIVI_VERDI[nome][y % 32][x % 32]


def dipingi_siepe(q, x, y, griglia):
    """La siepe di bosso in 3/4: il piano di sopra a ciuffi (due toni chiari), la faccia davanti un tono sotto e piu'
    in basso il piede scuro, solo dove sotto non continua la siepe."""
    X0, Y0 = x * 8, y * 8
    sotto = y + 1 < len(griglia) and griglia[y + 1][x] == "Y"
    for yy in range(8):
        for xx in range(8):
            X, Y = X0 + xx, Y0 + yy
            sopra = (V, 3) if ((X % 8) * 3 + (Y % 8) * 5) % 7 < 2 else (V, 2)
            if sotto or yy < 4:
                c = sopra
            elif yy < 7:
                c = (V, 1) if (X % 8 + Y % 8) % 5 else (V, 2)
            else:
                c = (V, 0)
            q.punto(X, Y, c)


def dipingi_aiuola(q, x, y):
    """Il prato fiorito dentro le siepi: l'erba del prato, e a macchie rade i ciuffi di fiori rossi, gialli e
    bianchi (2x2 pixel con la foglia sotto), su un motivo di 32 pixel."""
    X0, Y0 = x * 8, y * 8
    for yy in range(8):
        for xx in range(8):
            X, Y = X0 + xx, Y0 + yy
            c = colore_verde("prato", X, Y)
            k = h32((X % 32) // 3, (Y % 32) // 3, 89)
            if k < 0.04 and X % 3 < 2 and Y % 3 < 2:
                c = ((R, 2), (O, 2), (P, 4), (R, 3))[int(h32((X % 32) // 3, (Y % 32) // 3, 90) * 4)]
            elif k < 0.04 and Y % 3 == 2:
                c = (V, 1)
            q.punto(X, Y, c)


def dipingi_albero(q, x0, y0, aw, ah, c, seme):
    """Gli alberi in 3/4 (L1, L2, P2): la chioma a grumi (leccio tondo, roverella piu' aperta, cipresso a fiamma,
    cespuglio basso), tre toni con la luce in alto a sinistra e l'ombra in basso a destra, il bordo nel tono piu'
    scuro del verde (non nero); il tronco sotto la chioma; l'ombra portata la fa ombre_portate (L4)."""
    X0, Y0, W, H = x0 * 8, y0 * 8, aw * 8, ah * 8
    if c == "u" and ah == 2:
        # il cipresso: fiamma stretta, alta 16
        cx = X0 + 4
        for yy in range(16):
            r = 1 + min(yy, 13 - yy if yy < 13 else 0) * 0.28 if yy < 14 else 0
            for xx in range(-3, 4):
                if abs(xx + 0.5 - 0.5) <= r:
                    lato = xx + 0.5 - 0.5
                    t = (V, 3) if lato < -r * 0.3 else ((V, 1) if lato > r * 0.4 else (V, 2))
                    if abs(lato) > r - 1:
                        t = (V, 0) if lato > 0 else (V, 1)
                    if (yy * 3 + xx) % 5 == 0 and t == (V, 2):
                        t = (V, 1)
                    q.punto(cx + xx, Y0 + yy, t)
        q.rett(cx, Y0 + 14, 1, 2, (L, 1))
        return
    cx, cy = X0 + W / 2 - 0.5, Y0 + H / 2 - (1.5 if H >= 16 else 0.5)
    r = (W / 2 - 1) if W >= 16 else 3.2
    if c == "r":
        r = 2.8
        cy = Y0 + 4.5
    grumi = [(cx + r * 0.45 * math.cos(k * 2.1 + seme), cy + r * 0.4 * math.sin(k * 2.1 + seme), r * 0.62)
             for k in range(5)] + [(cx, cy, r * 0.75)]
    dentro = set()
    for yy in range(int(cy - r - 2), int(cy + r + 3)):
        for xx in range(int(cx - r - 2), int(cx + r + 3)):
            for gx, gy, gr in grumi:
                if (xx - gx) ** 2 + (yy - gy) ** 2 <= gr * gr:
                    dentro.add((xx, yy))
                    break
    if W >= 16 and c == "T":
        # il tronco sotto la chioma, la luce a sinistra
        for yy in range(int(cy + r * 0.6), Y0 + H):
            q.punto(int(cx), yy, (L, 1))
            q.punto(int(cx) + 1, yy, (L, 0))
    # solo la chioma (e il tronco) e' alta e getta ombra: il resto delle celle dell'albero e' suolo, cosi'
    # l'ombra portata ha la forma della chioma e non quella quadrata delle celle (L4)
    for yy in range(Y0, min(q.h, Y0 + H)):
        for xx in range(X0, min(q.w, X0 + W)):
            if (xx, yy) not in dentro and q.tipo[yy][xx] == "verde":
                q.tipo[yy][xx] = "suolo"
                q.alto[yy][xx] = 0
    for (xx, yy) in dentro:
        # il grumo piu' vicino decide la luce: la parte alta a sinistra di ogni grumo e' chiara (L2)
        gx, gy, gr = min(grumi, key=lambda g: (xx - g[0]) ** 2 + (yy - g[1]) ** 2 - g[2] ** 2)
        d = (xx - gx) + (yy - gy)
        t = (V, 3) if d < -gr * 0.5 else ((V, 1) if d > gr * 0.45 else (V, 2))
        if d < -gr * 0.9 and (xx + yy) % 2 == 0:
            t = (V, 4)
        bordo = any(v not in dentro for v in ((xx + 1, yy), (xx - 1, yy), (xx, yy + 1), (xx, yy - 1)))
        if bordo:
            t = (V, 0) if (xx > cx or yy > cy) else (V, 1)
        q.punto(xx, yy, t)


# --- scale, soglie, lampioni, fontane (F2, F3, M6) --------------------------------------------------------
def dipingi_scala(q, x, y, griglia):
    """Una scala vista in 3/4: due gradini per tile, la pedata nel tono medio con lo spigolo chiaro in alto, l'alzata
    un tono sotto, la riga d'ombra sotto lo spigolo (C5: niente bianco su grandi superfici). Il bordo sinistro della
    rampa prende la luce, il destro l'ombra (L1)."""
    X0, Y0 = x * 8, y * 8
    sx = x > 0 and griglia[y][x - 1] == "S"
    dx = x + 1 < len(griglia[0]) and griglia[y][x + 1] == "S"
    for yy in range(8):
        for xx in range(8):
            r = yy % 4
            c = ((P, 4), (P, 3), (P, 3), (P, 1))[r]
            if r == 2 and (X0 + xx) % 9 == 0:
                c = (P, 2)
            if not sx and xx == 0:
                c = chiaro(c, 1)
            if not dx and xx >= 6:
                c = scuro(c, 1)
            q.punto(X0 + xx, Y0 + yy, c)


def dipingi_soglia(q, x, y):
    """La soglia di un varco: il selciato con due filari di pietra chiara che segnano il passaggio (come prima, ma nei
    toni del suolo, C5)."""
    X0, Y0 = x * 8, y * 8
    for yy in range(8):
        for xx in range(8):
            c = colore_suolo("strada", X0 + xx, Y0 + yy)
            if yy in (1, 6):
                c = (P, 4) if xx % 4 else (P, 3)
            elif yy in (2, 7):
                c = (P, 1)
            q.punto(X0 + xx, Y0 + yy, c)


def dipingi_lampione(q, x, y):
    """Il braciere su un'asta di ferro (M6: di fronte, la base orizzontale sul suolo): la ciotola con il fuoco
    acceso, l'asta, il piede di pietra. Nel 1151 la piazza la illuminano i bracieri."""
    X0, Y0 = x * 8, y * 8
    for yy in range(8):
        for xx in range(8):
            q.punto(X0 + xx, Y0 + yy, colore_suolo("suolo", X0 + xx, Y0 + yy))
    q.rett(X0 + 2, Y0 + 7, 4, 1, (P, 1))
    q.rett(X0 + 2, Y0 + 6, 4, 1, (P, 3))
    q.rett(X0 + 3, Y0 + 3, 1, 3, (L, 0))
    q.rett(X0 + 4, Y0 + 3, 1, 3, (L, 0))
    q.rett(X0 + 1, Y0 + 2, 6, 1, (L, 0))
    q.rett(X0 + 2, Y0 + 1, 4, 1, (R, 2))
    q.punto(X0 + 3, Y0, (O, 3))
    q.punto(X0 + 4, Y0, (O, 2))
    q.punto(X0 + 2, Y0 + 1, (O, 2))
    q.conta("braciere")


def _ottagono(u, v):
    """La 'distanza' di un ottagono regolare (1 sul bordo), al quadrato come quella dell'ellisse."""
    au, av = abs(u), abs(v)
    return max(au, av, (au + av) * 0.76) ** 2


def dipingi_fontana(q, x0, y0, w, h):
    """La Fontana dei Matti in 3/4 (M6): la vasca tonda vista dall'alto e' un'ellisse schiacciata a due terzi, con
    l'orlo chiaro in alto a sinistra, la parete davanti in piedi (3 pixel, piu' scura) e l'acqua con i riflessi;
    in mezzo il fusto con la tazza e lo zampillo."""
    X0, Y0, W, H = x0 * 8, y0 * 8, w * 8, h * 8
    for yy in range(H):
        for xx in range(W):
            q.punto(X0 + xx, Y0 + yy, colore_suolo("suolo", X0 + xx, Y0 + yy))
    cx, cy = X0 + W / 2 - 0.5, Y0 + H / 2 - 2
    rx, ry = W / 2 - 1, (H / 2 - 2) * 0.85
    for yy in range(Y0, Y0 + H):
        for xx in range(X0, X0 + W):
            # giro 2 della fedelta' (5 nov 2026): la vasca vera e' ottagonale, non tonda
            d = _ottagono((xx - cx) / rx, (yy - cy) / ry)
            sotto = _ottagono((xx - cx) / rx, (yy - cy - 3) / ry)
            if d <= 1:
                if d > 0.72:
                    c = (P, 4) if (xx < cx or yy < cy) else (P, 3)
                else:
                    c = (A, 2) if (xx * 2 + yy * 3) % 7 else (A, 3)
                    if d < 0.15:
                        c = (A, 3)
                q.punto(xx, yy, c)
            elif sotto <= 1 and yy > cy:
                q.punto(xx, yy, (P, 2) if xx < cx else (P, 1))
    # il fusto, la tazza e lo zampillo: il fusto sale sopra l'orlo, cosi' la sagoma si legge anche piccola
    fx, ct = int(cx), max(Y0 + 2, int(cy) - 9)
    q.rett(fx - 1, ct + 2, 3, int(cy) + 3 - ct - 2, (P, 3))
    q.rett(fx - 1, ct + 2, 1, int(cy) + 3 - ct - 2, (P, 4))
    q.rett(fx + 1, ct + 2, 1, int(cy) + 3 - ct - 2, (P, 2))
    q.rett(fx - 3, ct, 7, 2, (P, 4))
    q.rett(fx - 3, ct + 1, 7, 1, (P, 2))
    q.punto(fx, ct - 2, (A, 4))
    q.punto(fx, ct - 1, (A, 3))
    for k in (-4, 4):
        for yy in range(ct + 2, int(cy) + 1, 2):
            q.punto(fx + k, yy, (A, 4))
    q.conta("fontana")


# --- belvedere e mura -------------------------------------------------------------------------------------
def _tettino(m, x0, y0, w, h, tono, W, H):
    """Un tetto lontano della citta' bassa: a capanna col colmo lungo il lato lungo; la falda verso la luce (in alto
    o a sinistra) un tono sopra, quella in ombra un tono sotto, il colmo chiaro (L1, L2)."""
    orizzontale = w >= h
    for yy in range(y0, y0 + h):
        for xx in range(x0, x0 + w):
            if orizzontale:
                u, colmo = yy - y0, (h - 1) // 2
            else:
                u, colmo = xx - x0, (w - 1) // 2
            c = (T, tono + 1) if u == colmo else ((T, tono) if u < colmo else (T, tono - 1))
            m[yy % H][xx % W] = c


def _motivo_citta_bassa():
    """La citta' bassa vista dal belvedere, lontana e in basso (C5, prospettiva aerea): isolati irregolari di case
    piccole coi tetti a capanna girati di qua e di la' (il colmo sul lato lungo), qualche cortile, i vicoli di
    pietra velata di foschia con l'ombra delle case a destra e in basso (L4). Contrasto basso, niente nero: e'
    sfondo. Solo cotto e pietra (un banco solo). Motivo di 48 x 32 pixel."""
    W, H = 48, 32
    m = [[(P, 3)] * W for _ in range(H)]
    for by in range(4):
        for bx in range(4):
            x0, y0 = bx * 12 + (by % 2) * 6, by * 8
            # l'isolato: 11 x 7 pixel, il vicolo di un pixel a destra e sotto
            n = 1 + int(h32(bx, by, 101) * 3)
            tagli = sorted({0, 11} | {2 + int(h32(bx, by, k, 102) * 8) for k in range(n - 1)})
            for k in range(len(tagli) - 1):
                xa, xb = tagli[k], tagli[k + 1]
                if xb - xa < 3:
                    continue
                if h32(bx, by, k, 103) < 0.07:
                    # un cortile: la pietra chiara chiusa fra i tetti
                    continue
                alto = 7 if h32(bx, by, k, 104) < 0.7 else 6
                tono = 3 if h32(bx, by, k, 106) < 0.55 else 2
                _tettino(m, x0 + xa, y0 + 7 - alto, xb - xa - (1 if xb < 11 else 0), alto, tono, W, H)
                # l'ombra della casa sulla pietra a destra e sotto
                for yy in range(y0 + 7 - alto, y0 + 8):
                    m[yy % H][(x0 + xb - (1 if xb < 11 else 0)) % W] = (P, 2)
                for xx in range(x0 + xa + 1, x0 + xb):
                    m[(y0 + 7) % H][xx % W] = (P, 2)
    return m


_CB = []


def colore_citta_bassa(x, y):
    if not _CB:
        _CB.append(_motivo_citta_bassa())
    m = _CB[0]
    return m[y % len(m)][x % len(m[0])]


def dipingi_citta_bassa(q, x, y, griglia):
    """Una cella di citta' bassa: il motivo, e accanto al muretto del belvedere la sua faccia esterna che scende
    (conci in ombra, 4 pixel) con l'ombra che cade sui tetti (2 pixel): si capisce che c'e' il salto (P2, L4)."""
    X0, Y0 = x * 8, y * 8
    h, w = len(griglia), len(griglia[0])
    muro = [(dx, dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
            if 0 <= x + dx < w and 0 <= y + dy < h and griglia[y + dy][x + dx] == "="]
    for yy in range(8):
        for xx in range(8):
            X, Y = X0 + xx, Y0 + yy
            c = colore_citta_bassa(X, Y)
            for dx, dy in muro:
                d = (7 - xx) if dx == 1 else (xx if dx == -1 else ((7 - yy) if dy == 1 else yy))
                if d < 4:
                    c = colore_suolo("muro_scuro", X, Y)
                    if d == 3:
                        c = (P, 0)
                elif d < 6:
                    c = scuro(c, 1)
            q.punto(X, Y, c)


def dipingi_parapetto(q, x, y, griglia, calpestabile):
    """Il muretto del belvedere visto dall'alto: la cimasa chiara dal lato della piazza, i conci della faccia
    esterna che scende verso la citta' bassa, il piede in ombra (L1: la luce da sinistra e dall'alto)."""
    X0, Y0 = x * 8, y * 8
    lati = [(dx, dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if calpestabile(x + dx, y + dy)]
    dx, dy = lati[0] if lati else (1, 0)
    for yy in range(8):
        for xx in range(8):
            # u: distanza dal lato della piazza (0) al lato del vuoto (7)
            u = (7 - xx) if dx == 1 else (xx if dx == -1 else ((7 - yy) if dy == 1 else yy))
            v = yy if dx else xx
            if u <= 2:
                c = (P, 4) if u == 0 else (P, 3)
                if (v + (u * 3)) % 8 == 7:
                    c = (P, 2)
            elif u <= 5:
                c = colore_suolo("muro", X0 + xx, Y0 + yy)
            elif u == 6:
                c = (P, 1)
            else:
                c = (P, 0)
            q.punto(X0 + xx, Y0 + yy, c)


def dipingi_mura(q, x, y, griglia, calpestabile):
    """Le mura viste dall'alto: il cammino di ronda di lastre, i merli guelfi (quadrati) sul lato verso fuori con la
    luce in alto a sinistra e l'ombra a destra e in basso, il muro esterno che cade in ombra."""
    X0, Y0 = x * 8, y * 8
    h, w = len(griglia), len(griglia[0])
    fuori = [(dx, dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
             if not (0 <= x + dx < w and 0 <= y + dy < h) or (griglia[y + dy][x + dx] not in "W" and
                                                              not calpestabile(x + dx, y + dy))]
    dx, dy = fuori[0] if fuori else (0, -1)
    for yy in range(8):
        for xx in range(8):
            X, Y = X0 + xx, Y0 + yy
            u = xx if dx == 1 else ((7 - xx) if dx == -1 else (yy if dy == 1 else 7 - yy))   # 7 = verso fuori
            v = Y if dx else X
            c = colore_suolo("suolo", X, Y)
            if u >= 5:
                dente = (v % 8) < 4
                if dente:
                    c = (P, 4) if (u == 5 or v % 8 == 0) else ((P, 2) if v % 8 == 3 else (P, 3))
                else:
                    c = (P, 1) if u == 5 else (P, 2)
                if u == 7:
                    c = (P, 1) if dente else (P, 0)
            elif u == 4:
                c = (P, 1)
            q.punto(X, Y, c)


# --- il Monte Ingino: stradoni, muretti, paracarri, rocce (F3, C5, L1, M6) --------------------------------
def _motivo_breccia():
    """La ghiaia degli stradoni su 32x32: il fondo di pietra nel tono medio (C5: niente bianco su grandi superfici),
    sassolini chiari con l'ombra in basso a destra, qualche sasso scuro, nessuna riga che si ripete."""
    m = [[(P, 3)] * 32 for _ in range(32)]
    for i in range(140):
        x, y = int(h32(i, 111) * 32), int(h32(i, 112) * 32)
        if i % 4 == 0:
            m[y][x] = (P, 2)
        else:
            m[y][x] = (P, 4)
            m[(y + 1) % 32][(x + 1) % 32] = (P, 2)
    for i in range(90):
        x, y = int(h32(i, 113) * 32), int(h32(i, 114) * 32)
        if m[y][x] == (P, 3):
            m[y][x] = (P, 2)
    return m


_BR = []


def colore_breccia(x, y):
    if not _BR:
        _BR.append(_motivo_breccia())
    return _BR[0][y % 32][x % 32]


def dipingi_breccia(q, x, y, griglia):
    """Una cella di stradone: la ghiaia; lungo i tratti dritti i due solchi delle ruote (un tono sotto, a 2 pixel
    dai bordi della carreggiata); sul bordo verso il bosco l'erba che invade la ghiaia a ciuffi (2 pixel)."""
    X0, Y0 = x * 8, y * 8
    h, w = len(griglia), len(griglia[0])

    def b(xx, yy):
        return 0 <= xx < w and 0 <= yy < h and griglia[yy][xx] in "b,SAEBGJ"
    verticale = b(x, y - 1) and b(x, y + 1)
    orizzontale = b(x - 1, y) and b(x + 1, y)
    bosco = {(dx, dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
             if 0 <= x + dx < w and 0 <= y + dy < h and griglia[y + dy][x + dx] in "#Tr"}
    for yy in range(8):
        for xx in range(8):
            X, Y = X0 + xx, Y0 + yy
            c = colore_breccia(X, Y)
            # i solchi di carreggiata, nel verso della strada
            solco = (verticale and not orizzontale and xx in (2, 5) and h32(xx, (Y % 32) // 4, 115) < 0.85) or \
                (orizzontale and not verticale and yy in (2, 5) and h32(yy, (X % 32) // 4, 116) < 0.85)
            if solco:
                c = (P, 2)       # un tono sotto la ghiaia, non di piu': l'ombra portata ci scende ancora di uno
            for dx, dy in bosco:
                d = (7 - xx) if dx == 1 else (xx if dx == -1 else ((7 - yy) if dy == 1 else yy))
                v = Y if dx else X
                ciuffo = h32(v % 16, dx, dy, 117)
                if d == 0 or (d == 1 and ciuffo < 0.6) or (d == 2 and ciuffo < 0.2):
                    c = (V, 2) if (v + d) % 3 else (V, 1)
            q.punto(X, Y, c)


def dipingi_muretto(q, x, y, griglia):
    """Il muretto a secco sul lato a valle dei tornanti, visto in 3/4: la cresta di pietre chiare in alto, la faccia
    di pietre irregolari un tono sotto coi giunti scuri, il piede in ombra (L1, F2)."""
    X0, Y0 = x * 8, y * 8
    sotto = y + 1 < len(griglia) and griglia[y + 1][x] in "mM"
    sopra = y > 0 and griglia[y - 1][x] in "mM"
    for yy in range(8):
        for xx in range(8):
            X, Y = X0 + xx, Y0 + yy
            pietra = colore_suolo("muro_secco", X, Y)
            if not sopra and yy < 3:
                c = chiaro(pietra, 1, 4)                     # la cresta in luce
            elif not sotto and yy == 7:
                c = (P, 1)                                   # il piede in ombra (il banco del verde: P1-P4)
            else:
                c = pietra
            q.punto(X, Y, c)
            q.tipo[Y][X] = "basso"
            q.alto[Y][X] = 6


def dipingi_paracarro(q, x, y, sotto):
    """Un paracarro di pietra in 3/4 (M6): il cappello tondo chiaro sopra, il fusto con la luce a sinistra e l'ombra
    a destra, l'ombra portata sul suolo la fa ombre_portate. 'sotto' dipinge il suolo della cella."""
    X0, Y0 = x * 8, y * 8
    for yy in range(8):
        for xx in range(8):
            q.punto(X0 + xx, Y0 + yy, sotto(X0 + xx, Y0 + yy))
            q.tipo[Y0 + yy][X0 + xx] = "suolo"
            q.alto[Y0 + yy][X0 + xx] = 0
    # il cappello: ellisse 4x2 (si vede da sopra)
    for xx, yy, c in ((3, 1, (P, 4)), (4, 1, (P, 4)), (2, 2, (P, 4)), (3, 2, (P, 4)), (4, 2, (P, 4)), (5, 2, (P, 3))):
        q.punto(X0 + xx, Y0 + yy, c)
    # il fusto: 4 pixel di larghezza, la luce a sinistra
    for yy in range(3, 7):
        for xx, c in ((2, (P, 3)), (3, (P, 3)), (4, (P, 2)), (5, (P, 1))):
            q.punto(X0 + xx, Y0 + yy, c)
    for xx in range(2, 6):
        q.punto(X0 + xx, Y0 + 7, (P, 1))
    for yy in range(1, 8):
        for xx in range(2, 6):
            q.tipo[Y0 + yy][X0 + xx] = "basso"
            q.alto[Y0 + yy][X0 + xx] = 6
    q.conta("paracarro")


def dipingi_roccia(q, x, y, seme):
    """Un masso di calcare sulla scarpata (L1, L2): un grumo tondo e irregolare, la faccia in alto a sinistra chiara,
    la massa nel tono medio, il lato in basso a destra in ombra con il bordo un tono sotto (mai nero), una crepa."""
    X0, Y0 = x * 8, y * 8
    for yy in range(8):
        for xx in range(8):
            # il sottobosco intorno al masso: un motivo di 8 pixel (i tile dei massi si ripetono)
            q.punto(X0 + xx, Y0 + yy, (V, 1) if (xx * 3 + yy * 5) % 7 == 0 else (V, 2))
            q.tipo[Y0 + yy][X0 + xx] = "suolo"
            q.alto[Y0 + yy][X0 + xx] = 0
    cx, cy = X0 + 3.5 + (h32(seme, 118) - 0.5), Y0 + 4.2
    rx, ry = 3.4, 2.9
    dentro = set()
    for yy in range(Y0, Y0 + 8):
        for xx in range(X0, X0 + 8):
            u, v = (xx - cx) / rx, (yy - cy) / ry
            bozzo = 0.12 * math.sin(math.atan2(v, u) * 3 + seme)
            if u * u + v * v <= (1 + bozzo) ** 2:
                dentro.add((xx, yy))
    for (xx, yy) in dentro:
        d = (xx - cx) / rx + (yy - cy) / ry
        c = (P, 4) if d < -0.7 else ((P, 3) if d < 0.4 else (P, 2))
        if any(v not in dentro for v in ((xx + 1, yy), (xx, yy + 1))):
            c = (P, 1)
        q.punto(xx, yy, c)
        q.tipo[yy][xx] = "basso"
        q.alto[yy][xx] = 6
    crepa = int(cx) + 1
    for yy in (int(cy) - 1, int(cy)):
        if (crepa, yy) in dentro:
            q.punto(crepa, yy, (P, 1))
    q.conta("roccia")


# --- gli ingressi (Cioti 4 nov sera: in citta' non si capisce dove sono le porte) ---------------------------
# Un solo disegno per le porte dove si entra, diverso da tutto il resto: il vano APERTO con la luce calda di
# dentro (l'unico vano luminoso della citta': le botteghe delle case hanno le imposte chiuse), le ante aperte
# contro gli stipiti, gli stipiti e l'arco di pietra chiara, la soglia, la pozza di luce sul selciato davanti e
# la lanterna appesa alla mensola. Colori del banco VITA (nero, ocra, legno, pietra 1-3) per il vano e del banco
# PIETRA per il selciato: la luce resta calda anche di notte (le rampe O e R del banco 3 non cambiano).
def _luce_dentro(u, v, alto):
    """Il colore del vano aperto: u in 0..1 da sinistra a destra, v pixel dal fondo (0 = soglia). In fondo il
    pavimento illuminato, piu' su il buio."""
    if v <= 2:
        return (O, 3) if 0.3 <= u <= 0.7 else (O, 2)
    if v <= 6:
        return (O, 2) if 0.25 <= u <= 0.75 else (O, 1)
    if v <= 9:
        return (O, 1) if 0.35 <= u <= 0.65 else (L, 0)
    return NERO


def _lanterna(q, x, y):
    """La lanterna appesa alla mensola di ferro (M6: la gabbia vista di fronte col tettuccio sopra): accesa."""
    q.rett(x, y, 4, 1, (L, 0))           # la mensola
    q.punto(x + 3, y + 1, (L, 0))
    q.rett(x + 2, y + 2, 3, 1, (L, 0))   # il tettuccio
    q.punto(x + 2, y + 3, (L, 0))
    q.punto(x + 3, y + 3, (O, 3))
    q.punto(x + 4, y + 3, (L, 0))
    q.punto(x + 2, y + 4, (L, 0))
    q.punto(x + 3, y + 4, (O, 2))
    q.punto(x + 4, y + 4, (L, 0))
    q.rett(x + 2, y + 5, 3, 1, (L, 0))


def dipingi_ingresso_frontale(q, x0, x1, ybase, alto=28):
    """L'ingresso su una facciata che guarda in basso: il vano di (x1 - x0) pixel per 'alto', ad arco, aperto."""
    w = x1 - x0
    r = w / 2.0
    top = ybase - alto + 1
    for yy in range(top, ybase + 1):
        for xx in range(x0, x1):
            dx = xx - x0 + 0.5 - r
            dy = yy - top + 0.5
            d2 = dx * dx + (r - dy) ** 2 if dy < r else dx * dx
            fuori = dy < r and d2 > r * r
            if fuori:
                continue
            bordo = xx - x0 < 2 or x1 - 1 - xx < 2 or (dy < r and d2 > (r - 2) ** 2)
            v = ybase - yy
            if bordo:
                # stipiti e ghiera di pietra chiara: luce a sinistra, ombra a destra (L1); la chiave in cima
                sinistra = xx - x0 < w / 2
                c = (P, 3) if sinistra else (P, 2)
                if dy < r and ((xx - x0) // 3) % 2 and abs(dx) > 2:
                    c = (P, 2) if sinistra else (P, 1)
                if abs(dx) < 1.5 and dy < 2.5:
                    c = (P, 3)
            else:
                u = (xx - x0 - 2) / max(1, w - 5)
                c = _luce_dentro(u, v, alto)
                # le ante aperte verso dentro, contro gli stipiti: 2 pixel di legno per parte
                if xx - x0 in (2, 3) and v < alto - r:
                    c = (L, 2) if xx - x0 == 2 else (L, 1)
                elif x1 - 1 - xx in (2, 3) and v < alto - r:
                    c = (L, 0) if x1 - 1 - xx == 2 else (L, 1)
            q.punto(xx, yy, c)
    # la soglia: un gradino di pietra
    q.rett(x0, ybase, w, 1, (P, 3))
    _lanterna(q, x1 - 2, top + 2)
    q.conta("ingresso")


def pozza_di_luce(q, x0, x1, y0, verso=(0, 1), lungo=6):
    """La luce che esce dal vano e schiarisce il selciato davanti (un tono, a ventaglio): si vede da lontano."""
    for k in range(lungo):
        allarga = k // 2
        for t in range(-allarga, (x1 - x0) + allarga):
            if verso[1]:
                xx, yy = x0 + t, y0 + k * verso[1]
            else:
                xx, yy = y0 + k * verso[0], x0 + t
            if 0 <= xx < q.w and 0 <= yy < q.h and q.tipo[yy][xx] == "suolo":
                bordo = t in (-allarga, (x1 - x0) + allarga - 1)
                if bordo and k > 1:
                    continue
                c = q.px[yy][xx]
                if c[0] == P:
                    q.px[yy][xx] = (P, min(4, c[1] + 1))


def dipingi_ingresso_laterale(q, x, y0, y1, verso):
    """L'ingresso su un fianco (le celle del varco in colonna): si vede di scorcio dall'alto. Dentro la colonna
    di celle, dal lato della strada: la spalla di pietra in alto e in basso, il vano aperto con la luce verso
    l'esterno, l'anta aperta; 'verso' e' +1 se la strada sta a destra, -1 a sinistra."""
    X0 = x * 8
    for yy in range(y0, y1):
        for k in range(8):
            xx = X0 + (k if verso > 0 else 7 - k)       # k = 7 sul lato della strada
            v = yy - y0
            if v < 3 or y1 - 1 - yy < 2:
                c = (P, 3) if v < 3 and v != 2 else (P, 1)   # architrave chiaro in alto, spalla in ombra in basso
            elif k < 2:
                c = NERO
            else:
                u = (y1 - 1 - yy) / max(1, y1 - y0 - 5)      # piu' luce verso la strada e verso il basso
                c = (O, 3) if k >= 6 and 0.2 < u < 0.8 else ((O, 2) if k >= 4 else (O, 1))
                if v in (3, 4) and k >= 3:
                    c = (L, 1) if v == 3 else (L, 0)         # l'anta aperta contro l'architrave
            q.punto(xx, yy, c)
    lx = X0 + 8 if verso > 0 else X0 - 5
    _lanterna(q, lx, y0 - 2)
    q.conta("ingresso")


def accendi_portale(q, x0, x1, ybase, cerca=48):
    """Il portale gia' disegnato sopra le celle del varco (il vano buio o le ante di legno, collegati alla soglia):
    lo si apre e lo si accende con la luce di dentro, tenendone la forma. Falso se non c'e' o e' piu' basso di 22."""
    def vano(c):
        return c == NERO or c[0] in (L, N) and c[1] <= 1 or c == ("neutri", 0)
    semi = []
    fondo = ybase
    for yb in range(ybase - 1, ybase - 21, -1):           # il fondo del vano puo' stare in cima ai gradini (Basilica: 16 px)
        semi = [(xx, yb) for xx in range(x0, x1) if vano(q.px[yb][xx])]
        if len(semi) >= 4:
            ybase = yb + 1
            break
    dentro, coda = set(semi), list(semi)
    while coda:
        xx, yy = coda.pop()
        for nx, ny in ((xx + 1, yy), (xx - 1, yy), (xx, yy - 1)):
            if (nx, ny) not in dentro and x0 - 8 <= nx < x1 + 8 and ybase - cerca <= ny <= ybase and vano(q.px[ny][nx]):
                dentro.add((nx, ny))
                coda.append((nx, ny))
    if not dentro:
        return False
    top = min(y for _, y in dentro)
    if ybase - top < 21:
        return False
    sx, dx = min(x for x, _ in dentro), max(x for x, _ in dentro)
    larga = dx - sx + 1
    for (xx, yy) in dentro:
        v = ybase - 1 - yy
        u = (xx - sx) / max(1, larga - 1)
        c = _luce_dentro(u, v, ybase - top)
        if xx - sx in (0, 1) and v < (ybase - top) * 0.7:
            c = (L, 2) if xx - sx == 0 else (L, 1)
        elif dx - xx in (0, 1) and v < (ybase - top) * 0.7:
            c = (L, 0) if dx - xx == 0 else (L, 1)
        q.px[yy][xx] = c
    # fra il portale e le celle del varco ci sono i gradini: si continuano quelli di fianco, senza riquadri
    for yy in range(ybase + 1, fondo + 1):
        for xx in range(x0, x1):
            q.px[yy][xx] = q.px[yy][x0 - 3]
    q.rett(sx, ybase, larga, 1, (P, 3))
    _lanterna(q, dx + 1, top + 3)
    q.conta("ingresso")
    return True


# Le botteghe e le case dove si entra hanno ognuna la sua tenda sopra l'ingresso, a strisce col colore del
# mestiere: da lontano si riconoscono (Cioti 4 nov sera: «gli edifici da fuori sono anonimi»). I monumenti
# (Consoli, Basilica) si riconoscono gia' dalla facciata e non la hanno.
TENDE = {"taverna": (R, 2), "spezieria": (V, 2), "casa_medico": (A, 2), "bottega_conti": (O, 2),
         "bottega_carradore": (R, 1)}


def dipingi_tenda(q, x0, x1, y, colore):
    """La tenda a strisce sopra la porta in 3/4: il telo che scende verso chi guarda (strisce verticali di 2 pixel,
    il colore del mestiere e la tela chiara), l'orlo a festoni, l'ombra sul muro sotto (L4)."""
    alto = 7
    for yy in range(y, y + alto):
        for xx in range(x0, x1):
            k = (xx - x0) // 3
            c = colore if k % 2 == 0 else (O, 1)
            if yy == y:
                c = (L, 0)                                       # il bastone in alto
            elif yy >= y + alto - 2:
                c = scuro(c, 1) if c[0] != O else (O, 1)        # l'orlo, piu' in ombra (la tenda scende verso chi guarda)
            if yy == y + alto - 1 and (xx - x0) % 3 == 1:
                continue                                         # i festoni
            q.punto(xx, yy, c)
    # l'ombra della tenda sul muro e sul vano, due righe sotto l'orlo (L4)
    for xx in range(x0 + 1, x1 + 1):
        for yy in (y + alto, y + alto + 1):
            if 0 <= xx < q.w and yy < q.h:
                c = q.px[yy][xx]
                if c[0] == P:
                    q.px[yy][xx] = scuro(c, 1)
                elif c[0] == O:
                    q.px[yy][xx] = (O, max(1, c[1] - 1))
    q.conta("tenda")


def dipingi_ingressi(q, a, griglia):
    """Ogni ingresso dell'area (riga 'ingresso'), col disegno giusto per il lato su cui sta."""
    h, w = len(griglia), len(griglia[0])
    for lettera in sorted(a.get("ingressi", {})):
        celle = [(x, y) for y in range(h) for x in range(w) if griglia[y][x] == lettera]
        if not celle:
            continue
        xs, ys = sorted({x for x, _ in celle}), sorted({y for _, y in celle})
        if len(ys) == 1:
            y = ys[0]
            x0, x1 = xs[0] * 8, (xs[-1] + 1) * 8
            ybase = y * 8 + 7
            # sotto il vano c'e' la strada: la soglia guarda in basso. Se il pittore del monumento ha gia' il suo
            # portale (Consoli, Basilica, chiese), si accende quello; se no si disegna il vano dello standard.
            if not accendi_portale(q, x0, x1, ybase):
                dipingi_ingresso_frontale(q, x0, x1, ybase)
            tenda = TENDE.get(a["ingressi"][lettera])
            if tenda:
                dipingi_tenda(q, x0 - 6, x1 + 6, ybase - 29, tenda)
            pozza_di_luce(q, x0, x1, ybase + 1, (0, 1))
        else:
            x = xs[0]
            destra = x + 1 < w and not _solida_cella(griglia[ys[0]][x + 1])
            verso = 1 if destra else -1
            y0, y1 = ys[0] * 8, (ys[-1] + 1) * 8
            dipingi_ingresso_laterale(q, x, y0, y1, verso)
            tenda = TENDE.get(a["ingressi"][lettera])
            if tenda:
                # di fianco la tenda sporge sulla strada: un telo stretto sopra il vano
                tx = x * 8 + 8 if verso > 0 else x * 8 - 6
                dipingi_tenda(q, tx, tx + 6, y0 - 1, tenda)
            pozza_di_luce(q, y0, y1, x * 8 + 8 if verso > 0 else x * 8 - 1, (verso, 0))


def _solida_cella(c):
    import genera_mondo as G
    return G.solida(c)
