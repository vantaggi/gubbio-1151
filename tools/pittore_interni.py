#!/usr/bin/env python3
"""Gli interni esplorabili (pezzi INT1 e INT2, thread «Progettare edifici esplorabili», 4 nov 2026).

Sei stanze: la taverna del corso e la spezieria con l'ospizio (San Pietro), la bottega dei conti e dei congegni
(Sant'Agostino), la bottega del carradore (Quaranta Martiri), la casa del medico (San Martino), la sala dei
Consoli (Piazza Grande). Ogni stanza e' scritta qui una volta sola, come disposizione di arredi in celle da
16 px, e da questa nascono sia il fondale dell'area (genera_mondo.ridipingi la passa a dipingi()) sia la
griglia della .area (scrivi_aree()): collisioni e disegno non possono divergere (test_interni).

Regole dello STANDARD_GRAFICO.md che valgono qui:
- F6: pavimento di cotto/lastre/assi, muro di fondo in piedi alto 3 celle con finestre a sinistra, arredi con
  ombra portata, uscita in basso con soglia chiara e tappeto;
- L1: ogni solido ha luce sul bordo sinistro e alto, ombra sui due pixel a destra e sull'ultima riga;
- L3: dove un pezzo sta davanti a un muro, il muro si scurisce di un tono lungo il confine;
- L4: ombra portata a destra e in basso (1/4 dell'altezza, 2-8 px);
- P2: gli arredi hanno il bordo nel tono piu' scuro del materiale, il quasi nero solo nei vani;
- C5: le superfici grandi nei toni medi della rampa; M6: oggetti in 3/4 frontale (il carro di fianco).

Nel gioco i colori sono riferimenti (rampa, tono) della Guida (C1): genera_mondo sceglie poi per ogni tile 8x8
il banco di 16 colori (pittore_citta.BANCHI_NUOVI piu' BANCO_INTERNI qui sotto: legno a quattro toni, cotto e
pietra, cosi' pavimenti e arredi restano nei toni medi, C5). Il ferro e il lino passano alla pietra; per le tavole di anteprima (main) i colori sono RGB e ci sono anche le figure.

    python3 tools/pittore_interni.py --aree           # riscrive mondo/aree/*_interno.area
    python3 tools/pittore_interni.py --tavole DIR     # le anteprime PNG (serve Pillow)
"""
import json
import os
import random
import sys


REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(REPO, "stile"), os.path.join(REPO, "tools")]
import stile  # noqa: E402
try:
    import sagome_mappa as SM  # noqa: E402  (il giocatore nuovo, ripartenza e2954fe)
except ImportError:
    SM = None
try:
    import figure_popolo as FP  # noqa: E402  (la gente a standard M1, thread «città viva»)
except ImportError:
    FP = None

PAL = json.load(open(os.path.join(REPO, "stile", "dati", "palette.json")))
NOTTE = False
GIOCO = True          # True: riferimenti (rampa, tono) per il fondale; False: RGB per le tavole

# Il banco degli interni (il settimo della palette dei fondali, in coda a pittore_citta.BANCHI_NUOVI): i colori
# che le stanze usano di piu', tutti insieme. Assi e banconi hanno i quattro toni del legno; i neutri restano il
# quasi nero e il 2 degli altri banchi, il ferro e il lino passano alla pietra, il bronzo scuro al legno
# scuro, il blu piu' scuro al tono sopra.
L_, T_, P_, O_, N_ = "legno e cuoio", "cotto e coppi", "pietra calcarea", "oro e bronzo", "neutri"
BANCO_INTERNI = [(N_, 0), (N_, 0), (L_, 0), (L_, 1), (L_, 2), (L_, 3), (T_, 1), (T_, 2), (T_, 3), (T_, 4),
                 (P_, 1), (P_, 2), (P_, 3), (P_, 4), (P_, 5), (O_, 2)]
NEL_BANCO = {("neutri", 1): ("pietra calcarea", 1), ("neutri", 3): ("pietra calcarea", 4),
             ("neutri", 4): ("pietra calcarea", 5), ("oro e bronzo", 0): ("legno e cuoio", 0),
             ("cielo e acqua", 0): ("cielo e acqua", 1)}


def C(rampa, tono):
    if GIOCO:
        return NEL_BANCO.get((rampa, tono), (rampa, tono))
    return stile.rgb_di(stile.colore(PAL, (rampa, tono), NOTTE))


NERO = lambda: C("neutri", 0)  # noqa: E731
CELLA = 16
SCHERMO = (240, 160)


class Mat:
    """Un materiale a tre toni (C3) piu' il bordo (P2: il tono piu' scuro del materiale)."""
    def __init__(self, rampa, ombra, base, luce, bordo=None):
        self.r, self.t = rampa, (ombra, base, luce)
        self.b = ombra - 1 if bordo is None else bordo

    @property
    def ombra(self): return C(self.r, self.t[0])
    @property
    def base(self): return C(self.r, self.t[1])
    @property
    def luce(self): return C(self.r, self.t[2])
    @property
    def bordo(self): return C(self.r, max(self.b, 0))


LEGNO = Mat("legno e cuoio", 1, 2, 3, 0)
LEGNO_SCURO = Mat("legno e cuoio", 0, 1, 2, 0)
PIETRA = Mat("pietra calcarea", 2, 3, 4, 1)
PIETRA_SCURA = Mat("pietra calcarea", 1, 2, 3, 0)
COTTO = Mat("cotto e coppi", 2, 3, 4, 1)
ROSSO = Mat("vermiglio comunale", 1, 2, 3, 0)
ORO = Mat("oro e bronzo", 1, 2, 3, 0)
FERRO = Mat("neutri", 1, 2, 3, 0)
BIANCO = Mat("neutri", 2, 3, 4, 1)
VERDE = Mat("verde dei monti", 1, 2, 3, 0)
CIELO = Mat("cielo e acqua", 1, 2, 3, 0)
PAGLIA = Mat("oro e bronzo", 0, 1, 2, 0)


class Tela:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = [[NERO()] * w for _ in range(h)]
        self.ombra_suolo = {}      # colore del suolo -> il suo tono d'ombra (L4)

    def p(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = c

    def r(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.p(xx, yy, c)

    def get(self, x, y):
        return self.px[y][x] if 0 <= x < self.w and 0 <= y < self.h else None

    def ombra(self, x, y, w, h, alto=None):
        """L4: ombra portata a destra e in basso, larga 1/4 dell'altezza visibile (2-8 px)."""
        s = max(2, min(8, (alto or h) // 4))
        for yy in range(y + s, y + h + s):
            for xx in range(x + s, x + w + s):
                if xx >= x + w or yy >= y + h:
                    c = self.get(xx, yy)
                    if c in self.ombra_suolo:
                        self.p(xx, yy, self.ombra_suolo[c])

    def solido(self, x, y, w, h, m, contorno=None, ombra=True):
        """Un solido a tre toni con la luce da sinistra e dall'alto (L1)."""
        if ombra:
            self.ombra(x, y, w, h)
        self.r(x, y, w, h, m.base)
        self.r(x, y, w, 1, m.luce)
        self.r(x, y, 1, h, m.luce)
        self.r(x + w - 2, y + 1, 2, h - 1, m.ombra)
        self.r(x + 1, y + h - 1, w - 1, 1, m.ombra)
        bordo = contorno or m.bordo
        for xx in range(x - 1, x + w + 1):
            self.p(xx, y - 1, bordo)
            self.p(xx, y + h, bordo)
        for yy in range(y, y + h):
            self.p(x - 1, yy, bordo)
            self.p(x + w, yy, bordo)

    def ellisse(self, cx, cy, rx, ry, c):
        for yy in range(cy - ry, cy + ry + 1):
            for xx in range(cx - rx, cx + rx + 1):
                if ((xx - cx) / max(rx, .5)) ** 2 + ((yy - cy) / max(ry, .5)) ** 2 <= 1.0:
                    self.p(xx, yy, c)

    def png(self, nome, k=3):
        from PIL import Image
        img = Image.new("RGB", (self.w, self.h))
        img.putdata([c for riga in self.px for c in riga])
        img.resize((self.w * k, self.h * k), Image.NEAREST).save(nome)
        return img


# --- suoli ------------------------------------------------------------------------------------------
def pavimento_cotto(t, x0, y0, w, h, seme):
    """Mattoni 12x6 a file sfalsate a caso con seme fisso (F3/F4): quasi tutti nel tono 3 del cotto, uno su
    cinque nel tono 4; giunti nel tono d'ombra 2, solo in basso e a destra di ogni mattone (C5)."""
    rnd = random.Random(seme)
    giunto, base, chiaro = C("cotto e coppi", 2), C("cotto e coppi", 3), C("cotto e coppi", 4)
    for yy in range(y0, y0 + h, 6):
        sfasa = rnd.randint(0, 11)
        for xx in range(x0 - sfasa, x0 + w, 12):
            c = chiaro if rnd.random() < 0.2 else base
            for dy in range(6):
                for dx in range(12):
                    X, Y = xx + dx, yy + dy
                    if x0 <= X < x0 + w and y0 <= Y < y0 + h:
                        t.p(X, Y, giunto if dy == 5 or dx == 11 else c)
    t.ombra_suolo.update({base: giunto, chiaro: giunto, giunto: C("cotto e coppi", 1)})


def pavimento_assi(t, x0, y0, w, h, seme):
    """Assi di legno per lungo (bottega del carradore), giunti nel tono 1, nodi rari."""
    rnd = random.Random(seme)
    giunto, toni = C("legno e cuoio", 1), [C("legno e cuoio", 2), C("legno e cuoio", 2), C("legno e cuoio", 2)]
    for xx in range(x0, x0 + w, 6):
        y = y0
        while y < y0 + h:
            lun = rnd.randint(20, 40)
            c = rnd.choice(toni)
            for Y in range(y, min(y + lun, y0 + h)):
                for dx in range(6):
                    if xx + dx < x0 + w:
                        nodo = dx == 2 and (Y * 7 + xx) % 23 == 0
                        t.p(xx + dx, Y, giunto if dx == 5 or Y == y + lun - 1 or nodo else c)
            y += lun
    t.ombra_suolo.update({toni[0]: C("legno e cuoio", 1), toni[2]: C("legno e cuoio", 1), giunto: C("legno e cuoio", 0)})


def pavimento_lastre(t, x0, y0, w, h, seme):
    """Lastre di pietra 16x12 irregolari (Palazzo dei Consoli), toni 2-4, giunti morbidi nel tono 2."""
    rnd = random.Random(seme)
    giunto, toni = C("pietra calcarea", 2), [C("pietra calcarea", 3), C("pietra calcarea", 3), C("pietra calcarea", 4)]
    for yy in range(y0, y0 + h, 12):
        sfasa = rnd.randint(0, 10)
        for xx in range(x0 - sfasa, x0 + w, 16):
            c = toni[2] if rnd.random() < 0.2 else toni[0]
            for dy in range(12):
                for dx in range(16):
                    X, Y = xx + dx, yy + dy
                    if x0 <= X < x0 + w and y0 <= Y < y0 + h:
                        bordo = (dy == 11 and dx % 3 != 1) or (dx == 15 and dy % 3 != 1)   # giunti morbidi
                        t.p(X, Y, giunto if bordo else c)
    t.ombra_suolo.update({toni[0]: C("pietra calcarea", 2), toni[2]: C("pietra calcarea", 2),
                          giunto: C("pietra calcarea", 1)})


def luce_finestra(t, fx, fw, y0, h, x_max):
    """La luce che entra dalla finestra a sinistra: una lama in diagonale verso destra-basso (L1),
    i mattoni schiariscono di un tono (solo dove tocca: L5 vale anche di giorno)."""
    piu = {C("cotto e coppi", 3): C("cotto e coppi", 4), C("pietra calcarea", 3): C("pietra calcarea", 4),
           C("legno e cuoio", 2): C("legno e cuoio", 3) if False else C("legno e cuoio", 2)}
    for dy in range(h):
        for dx in range(fw - 2):
            X, Y = fx + 1 + dx + dy // 2, y0 + dy
            if X < x_max:
                c = t.get(X, Y)
                if c in piu:
                    t.p(X, Y, piu[c])


# --- la scatola della stanza ------------------------------------------------------------------------
class Stanza:
    """Una stanza di cw x ch celle, centrata nello schermo 240x160 (il resto e' buio, come in ogni
    interno da GBA). Le prime 3 righe di celle sono il muro di fondo in piedi (F6)."""
    def __init__(self, nome, cw, ch, suolo="cotto", seme=1, muro="intonaco", uscita=2):
        self.nome, self.cw, self.ch = nome, cw, ch
        W, H = max(SCHERMO[0], cw * CELLA + 16), max(SCHERMO[1], ch * CELLA + 16)
        self.t = Tela(W, H)
        self.x0, self.y0 = (W - cw * CELLA) // 2, (H - ch * CELLA) // 2
        self.solide = [[False] * cw for _ in range(ch)]
        self.marchi = [["L"] * cw for _ in range(ch)]
        self.oggetti = []          # (y_piedi, funzione) per disegnare in ordine di profondita'
        self.uscita = uscita
        X, Y, w, h = self.x0, self.y0, cw * CELLA, ch * CELLA
        fondo = 3 * CELLA
        {"cotto": pavimento_cotto, "assi": pavimento_assi, "lastre": pavimento_lastre}[suolo](
            self.t, X, Y + fondo, w, h - fondo, seme)
        self.muro_di_fondo(X, Y, w, fondo, muro, seme)
        for cy in range(3):
            for cx in range(cw):
                self.segna(cx, cy, "#")
        # i muri laterali e quello in basso visti dall'alto: la testa del muro, 4 px, luce a sinistra
        cap = PIETRA_SCURA
        self.t.r(X - 4, Y, 4, h + 4, cap.base)
        self.t.r(X - 4, Y, 1, h + 4, cap.luce)
        self.t.r(X + w, Y, 4, h + 4, cap.base)
        self.t.r(X + w + 3, Y, 1, h + 4, cap.ombra)
        mezzo = cw // 2
        ux0, ux1 = X + (mezzo - uscita // 2) * CELLA, X + (mezzo - uscita // 2 + uscita) * CELLA
        for xx in range(X - 4, X + w + 4):
            if not ux0 <= xx < ux1:
                self.t.r(xx, Y + h, 1, 4, cap.base)
                self.t.p(xx, Y + h, cap.luce)
        # la soglia chiara e il tappeto davanti all'uscita (F6)
        self.t.r(ux0, Y + h, ux1 - ux0, 4, C("pietra calcarea", 4))
        self.t.r(ux0, Y + h + 3, ux1 - ux0, 1, C("pietra calcarea", 3))
        self.tappeto(ux0 + 2, Y + h - 12, ux1 - ux0 - 4, 10)
        for i in range(uscita):
            self.marchi[ch - 1][mezzo - uscita // 2 + i] = "A"

    def segna(self, cx, cy, c="#"):
        if 0 <= cx < self.cw and 0 <= cy < self.ch:
            self.solide[cy][cx] = True
            self.marchi[cy][cx] = c

    def px(self, cx, cy):
        return self.x0 + cx * CELLA, self.y0 + cy * CELLA

    def muro_di_fondo(self, X, Y, w, h, muro, seme):
        t = self.t
        rnd = random.Random(seme + 7)
        # le travi del soffitto in alto (il buio sopra la stanza)
        t.r(X, Y, w, 5, C("legno e cuoio", 0))
        for xx in range(X, X + w, 24):
            t.r(xx, Y, 6, 6, C("legno e cuoio", 1))
            t.r(xx, Y, 1, 6, C("legno e cuoio", 2))
        if muro == "pietra":
            # conci irregolari in 2-3 toni, giunti nel tono d'ombra (F2)
            for yy in range(Y + 6, Y + h - 6, 7):
                xx = X - rnd.randint(0, 9)
                while xx < X + w:
                    lw = rnd.randint(9, 16)
                    c = C("pietra calcarea", rnd.choice((3, 3, 4)))
                    for dy in range(7):
                        for dx in range(lw):
                            if X <= xx + dx < X + w and yy + dy < Y + h - 6:
                                g = dy == 6 or dx == lw - 1
                                t.p(xx + dx, yy + dy, C("pietra calcarea", 2) if g else c)
                    xx += lw
        else:
            # intonaco chiaro a macchie larghe (toni medi, C5)
            t.r(X, Y + 6, w, h - 12, C("pietra calcarea", 4))
            for _ in range(w * h // 90):
                mx, my = rnd.randrange(X, X + w - 6), rnd.randrange(Y + 7, Y + h - 14)
                t.r(mx, my, rnd.randint(3, 7), rnd.randint(2, 3), C("pietra calcarea", 3))
        # lo zoccolo piu' scuro (F2) e la riga d'ombra al piede del muro (dove il muro incontra il pavimento)
        t.r(X, Y + h - 6, w, 5, C("pietra calcarea", 2))
        t.r(X, Y + h - 6, w, 1, C("pietra calcarea", 3))
        t.r(X, Y + h - 1, w, 1, C("pietra calcarea", 1))
        # lo spigolo a sinistra illuminato, a destra in ombra
        t.r(X, Y + 6, 1, h - 7, C("pietra calcarea", 5 if muro != "pietra" else 4))
        t.r(X + w - 2, Y + 6, 2, h - 7, C("pietra calcarea", 2))

    def finestra(self, cx, larga=1, notte=False):
        """Una finestra nel muro di fondo (F5): strombo d'ombra a destra e in alto, cielo dentro,
        e la lama di luce sul pavimento verso destra-basso."""
        t = self.t
        x, y = self.px(cx, 0)
        x += 3
        w, h = larga * CELLA - 6, 22
        y += 10
        t.r(x - 1, y - 1, w + 2, h + 2, C("pietra calcarea", 2))
        t.r(x, y, w, h, C("cielo e acqua", 3) if not notte else C("cielo e acqua", 0))
        t.r(x, y, w, h // 3, C("cielo e acqua", 4) if not notte else C("cielo e acqua", 1))
        t.r(x + w - 2, y, 2, h, C("cielo e acqua", 2) if not notte else NERO())   # strombo a destra
        t.r(x, y, w, 2, C("cielo e acqua", 2) if not notte else NERO())           # e in alto
        t.r(x + w // 2 - 1, y, 1, h, C("legno e cuoio", 1))                          # il montante
        t.r(x - 2, y + h + 1, w + 4, 2, C("pietra calcarea", 4))                     # il davanzale
        t.r(x - 2, y + h + 2, w + 4, 1, C("pietra calcarea", 2))
        if not notte:
            luce_finestra(t, x, w, self.y0 + 3 * CELLA, 3 * CELLA, self.x0 + self.cw * CELLA)

    def tappeto(self, x, y, w, h):
        t = self.t
        t.r(x, y, w, h, C("vermiglio comunale", 1))
        t.r(x + 1, y + 1, w - 2, h - 2, C("vermiglio comunale", 2))
        for xx in range(x + 3, x + w - 3, 4):
            t.p(xx, y + h // 2, C("oro e bronzo", 2))
        t.r(x, y, w, 1, C("vermiglio comunale", 3))

    def metti(self, y_piedi, f):
        self.oggetti.append((y_piedi, f))

    def disegna(self):
        for _, f in sorted(self.oggetti, key=lambda o: o[0]):
            f()
        return self.t

    def griglia(self):
        """La bozza .area: ogni cella da 16 px diventa 2x2 tile da 8 px."""
        righe = []
        for riga in self.marchi:
            r = "#" + "".join(c * 2 for c in riga) + "#"
            righe += [r, r]
        ultima = righe[-1]
        righe.append("".join("A" if c == "A" else "#" for c in ultima))
        righe[-2] = righe[-2].replace("A", "L")
        righe[-3] = righe[-3].replace("A", "L")
        return righe


# --- figure (NPC e giocatore) ----------------------------------------------------------------------
PAL_NPC = [("neutri", 0), ("neutri", 0), ("pelle", 0), ("pelle", 2), ("vermiglio comunale", 1),
           ("vermiglio comunale", 3), ("neutri", 4), ("neutri", 2), ("pietra calcarea", 2), ("pietra calcarea", 5),
           ("legno e cuoio", 1), ("legno e cuoio", 3), ("neutri", 1), ("neutri", 3), ("oro e bronzo", 3),
           ("verde dei monti", 0)]       # = PALETTE_NEMICI di tools/genera_battaglia.py
GIOCATORE = ["......1111......", ".....177771.....", "....17777771....", "....13333331....",
             "....13133131....", "....13333331....", ".....133331.....", "....15555551....",
             "...1544444451...", "...1544444451...", "...1544444451...", "....14444441....",
             ".....166661.....", ".....16..61.....", ".....16..61.....", ".....11..11....."]
PAL_GIOC = [("neutri", 0), ("neutri", 0), ("pelle", 1), ("pelle", 2), ("vermiglio comunale", 1),
            ("vermiglio comunale", 2), ("legno e cuoio", 1), ("legno e cuoio", 2), ("neutri", 4)]


def _fumetto(t, bx, by):
    """I2: il fumetto a tre puntini, uguale per persone, cartelli e cose."""
    t.r(bx, by, 9, 7, NERO())
    t.r(bx + 1, by + 1, 7, 5, C("neutri", 4))
    t.p(bx + 2, by + 7, NERO()); t.p(bx + 3, by + 7, NERO()); t.p(bx + 2, by + 8, NERO())
    t.p(bx + 2, by + 6, C("neutri", 4))
    for k in (2, 4, 6):
        t.p(bx + k, by + 3, NERO())


def figura(st, cx, cy, base=None, acc=None, giocatore=False, fumetto=False, dx=0, dy=0, nome=None):
    """Una figura 16x32 coi piedi nella cella (cx, cy): l'ellisse d'ombra 10x3 (L4), poi lo sprite. Solo nelle
    tavole: nel gioco le persone sono sprite e il loro posto lo sceglie genera_storia."""
    if GIOCO:
        return
    x, y = st.px(cx, cy)
    x, y = x + dx, y + dy

    def f():
        t = st.t
        piedi = y + 15
        for (dx_, w_, dy_) in ((-3, 6, -1), (-5, 10, 0), (-3, 6, 1)):      # ellisse 10x3 (L4)
            for xx in range(x + 8 + dx_, x + 8 + dx_ + w_):
                c = t.get(xx, piedi + dy_)
                t.p(xx, piedi + dy_, t.ombra_suolo.get(c, c))
        if giocatore and SM is not None:
            # Ubaldo 16x32 di tools/sagome_mappa.py (camminata A6), di spalle verso il fondo della stanza
            g = SM.fotogramma("su", 0)
            ombra_i = SM.SINGOLI["ombra"]
            for ry, riga in enumerate(g):
                for rx, i in enumerate(riga):
                    if i and i != ombra_i:
                        t.p(x + rx, y - 16 + ry, C(*SM.PALETTE[i]))
            return
        if not giocatore and FP is not None:
            g = FP.figura(FP.costume_npc(base, acc, nome), "giu")
            for ry, riga in enumerate(g):
                for rx, i in enumerate(riga):
                    if i and i != FP.OMBRA_SUOLO:
                        t.p(x + rx, y - 16 + ry, C(*FP.PALETTE_POPOLO[i]))
            if fumetto:
                cima = next(i for i, r in enumerate(g) if any(r))
                _fumetto(t, x + 4, y - 16 + cima - 10)
            return
        if giocatore:
            righe, pal, oy = GIOCATORE, PAL_GIOC, y
        else:
            righe, pal, oy = FN.figura_composta(base, acc), PAL_NPC, y - 16
        for ry, riga in enumerate(righe):
            for rx, ch in enumerate(riga):
                if ch != ".":
                    i = int(ch, 16)
                    t.p(x + rx, oy + ry, C(*pal[i]))
        if fumetto:
            bx, by = x + 4, oy + (0 if giocatore else 12) - 10
            if not giocatore:
                # la cima della figura nelle 32 righe: sopra la testa
                cima = next(i for i, r in enumerate(righe) if r.strip("."))
                by = oy + cima - 10
            t.r(bx, by, 9, 7, NERO())
            t.r(bx + 1, by + 1, 7, 5, C("neutri", 4))
            t.p(bx + 2, by + 7, NERO()); t.p(bx + 3, by + 7, NERO()); t.p(bx + 2, by + 8, NERO())
            t.p(bx + 2, by + 6, C("neutri", 4))
            for k in (2, 4, 6):
                t.p(bx + k, by + 3, NERO())
    st.metti(y + 15, f)
    if not giocatore:
        st.segna(cx, cy, "N")


# --- arredi -----------------------------------------------------------------------------------------
def tavolo(st, cx, cy, cw, ch=1, oggetti=()):
    x, y = st.px(cx, cy)
    w, h = cw * CELLA - 2, ch * CELLA - 6

    def f():
        t = st.t
        t.solido(x + 1, y + 2, w, h, LEGNO)
        # le gambe davanti (si vedono sotto il piano)
        for gx in (x + 2, x + w - 3):
            t.r(gx, y + 2 + h, 2, 4, LEGNO.ombra)
            t.p(gx, y + 2 + h, LEGNO.base)
        for (ox, oy, tipo) in oggetti:
            OGGETTI[tipo](t, x + ox, y + oy)
    st.metti(y + h + 6, f)
    for i in range(cw):
        for j in range(ch):
            st.segna(cx + i, cy + j, "t")


def panca(st, cx, cy, cw):
    x, y = st.px(cx, cy)

    def f():
        st.t.solido(x + 1, y + 8, cw * CELLA - 2, 5, LEGNO)
    st.metti(y + 13, f)
    for i in range(cw):
        st.segna(cx + i, cy, "q")


def sgabello(st, cx, cy, rovesciato=False, dx=4, dy=6):
    x, y = st.px(cx, cy)
    x, y = x + dx, y + dy

    def f():
        t = st.t
        if rovesciato:
            t.solido(x, y + 2, 8, 4, LEGNO)
            for gx in (x + 1, x + 5):
                t.r(gx, y - 2, 2, 4, LEGNO.ombra)
        else:
            t.solido(x, y, 8, 4, LEGNO)
            t.r(x + 1, y + 4, 1, 3, LEGNO.ombra)
            t.r(x + 6, y + 4, 1, 3, LEGNO.ombra)
    st.metti(y + 7, f)


def botte(st, cx, cy, dx=0, dy=0):
    """Una botte in piedi vista di 3/4: il coperchio ellittico in alto, il corpo panciuto, due cerchi."""
    x, y = st.px(cx, cy)
    x, y = x + 1 + dx, y - 4 + dy

    def f():
        t = st.t
        t.ombra(x + 1, y + 2, 13, 17)
        prof = (2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2)      # la pancia: rientra in alto e in basso
        for i, r in enumerate(prof):
            yy = y + 3 + i
            t.r(x + r, yy, 14 - 2 * r, 1, LEGNO.base)
            t.r(x + r, yy, 2, 1, LEGNO.luce)
            t.r(x + 12 - r, yy, 2, 1, LEGNO.ombra)
            t.p(x + r - 1, yy, LEGNO.bordo); t.p(x + 14 - r, yy, LEGNO.bordo)
        t.r(x + 2, y + 19, 10, 1, LEGNO.bordo)
        for dv in (5, 9):                                          # le doghe
            t.r(x + dv, y + 6, 1, 12, LEGNO.ombra)
        t.ellisse(x + 7, y + 3, 6, 2, LEGNO.bordo)                 # il coperchio
        t.ellisse(x + 7, y + 3, 5, 1, LEGNO.luce)
        t.r(x + 5, y + 3, 4, 1, LEGNO.base)
        for hy, r in ((y + 6, 1), (y + 14, 1)):                    # i cerchi di bronzo
            t.r(x + r, hy, 14 - 2 * r, 2, ORO.base)
            t.r(x + r, hy, 2, 2, ORO.luce)
            t.r(x + 12 - r, hy, 2, 2, ORO.ombra)
        t.p(x + 7, y + 11, NERO())                                 # la cannella
        t.p(x + 8, y + 11, ORO.base)
    st.metti(y + 19, f)
    st.segna(cx, cy, "b")


def banco(st, cx, cy, cw, oggetti=()):
    """Il banco di vendita: un solido lungo, alto, col piano chiaro."""
    x, y = st.px(cx, cy)
    w = cw * CELLA - 2

    def f():
        t = st.t
        t.solido(x + 1, y - 2, w, 16, LEGNO_SCURO)
        t.r(x + 1, y - 2, w, 4, LEGNO.luce)
        t.r(x + 1, y + 2, w, 1, LEGNO.ombra)
        for px_ in range(x + 6, x + w - 4, 10):  # le doghe del fronte
            t.r(px_, y + 4, 1, 9, LEGNO_SCURO.ombra)
        for (ox, oy, tipo) in oggetti:
            OGGETTI[tipo](t, x + ox, y + oy)
    st.metti(y + 14, f)
    for i in range(cw):
        st.segna(cx + i, cy, "B")


def scaffale_a_muro(st, cx, cw, cosa="fiaschi", righe=2, cy=1):
    """Mensole contro il muro di fondo, con gli oggetti sopra (si esaminano)."""
    x, y = st.px(cx, cy)
    t = st.t
    w = cw * CELLA - 4
    t.r(x + 2 + 2, y + 2 + 2, w, righe * 12, C("pietra calcarea", 2))   # L3: il muro si scurisce dietro
    for r in range(righe):
        my = y + 2 + r * 12 + 9
        t.r(x + 2, my, w, 3, LEGNO.base)
        t.r(x + 2, my, w, 1, LEGNO.luce)
        t.r(x + 2, my + 3, w, 1, LEGNO.bordo)
        for i, ox in enumerate(range(x + 4, x + w - 2, 6)):
            OGGETTI[cosa](t, ox, my - 1, i + r)


def camino(st, cx, cw=2):
    x, y = st.px(cx, 0)
    t = st.t
    w = cw * CELLA - 4
    # la cappa di pietra in piedi contro il muro, il focolare, il fuoco e il paiolo
    t.solido(x + 2, y + 6, w, 30, PIETRA, ombra=False)
    t.r(x + 6, y + 26, w - 8, 14, NERO())                  # il vano del focolare (C4: buio vero)
    t.r(x + 4, y + 24, w - 4, 2, PIETRA.ombra)             # l'architrave
    for i, (fx, fh) in enumerate(((x + 10, 6), (x + 13, 9), (x + 16, 7), (x + 19, 5))):
        t.r(fx, y + 40 - fh, 3, fh, C("vermiglio comunale", 2))
        t.r(fx + 1, y + 41 - fh + 2, 1, fh - 3, C("oro e bronzo", 3))
    t.r(x + 9, y + 37, w - 14, 3, C("legno e cuoio", 1))   # i ciocchi
    t.ellisse(x + 2 + w // 2, y + 30, 5, 3, C("neutri", 1)) # il paiolo
    t.r(x + 2 + w // 2 - 4, y + 28, 8, 1, C("neutri", 2))
    t.r(x + 2 + w // 2, y + 24, 1, 5, C("neutri", 1))       # la catena
    for i in range(cw):
        st.segna(cx + i, 3, "f")


def ruota(t, x, y, r=7, m=LEGNO):
    """Una ruota vista di fronte: cerchione di ferro, raggi di legno, mozzo."""
    for yy in range(y - r, y + r + 1):
        for xx in range(x - r, x + r + 1):
            d = ((xx - x) ** 2 + (yy - y) ** 2) ** .5
            if r - 1.2 <= d <= r + .3:
                t.p(xx, yy, C("neutri", 3) if xx < x and yy < y else C("neutri", 1))
            elif r - 2.4 <= d < r - 1.2:
                t.p(xx, yy, m.luce if xx < x else m.base)
    for dx_, dy_ in ((1, 0), (0, 1), (1, 1), (1, -1)):
        for s in range(-r + 2, r - 1):
            t.p(x + dx_ * s, y + dy_ * s, m.base)
    t.r(x - 1, y - 1, 3, 3, m.ombra)
    t.p(x - 1, y - 1, m.luce)


def ruota_a_muro(st, cx, dy=18):
    x, y = st.px(cx, 0)
    t = st.t
    t.ellisse(x + 10, y + dy + 2, 7, 7, C("pietra calcarea", 3))   # L3/L4: ombra sul muro a destra-basso
    ruota_in_piedi(t, x + 8, y + dy, 8, 8)


def ruota_in_piedi(t, cx, cy, rx, ry):
    """Una ruota di carro in piedi, vista di fronte in 3/4: cerchione di ferro (luce a sinistra-alto, ombra
    a destra-basso), corona di legno, sei raggi, mozzo di ferro. Contorno quasi nero: si interagisce (P1)."""
    def dentro(x, y, a, b):
        return ((x - cx) / a) ** 2 + ((y - cy) / b) ** 2 <= 1.0
    for y in range(cy - ry - 1, cy + ry + 2):
        for x in range(cx - rx - 1, cx + rx + 2):
            if not dentro(x, y, rx + .5, ry + .5):
                continue
            if not dentro(x, y, rx - .5, ry - .5):
                t.p(x, y, NERO())                                      # contorno
            elif not dentro(x, y, rx - 1.6, ry - 1.6):
                luce = (x - cx) * 0.8 + (y - cy) < 0
                t.p(x, y, C("neutri", 3) if luce else C("neutri", 2))  # cerchione di ferro
            elif not dentro(x, y, rx - 3.2, ry - 3.2):
                luce = (x - cx) * 0.8 + (y - cy) < 0
                t.p(x, y, LEGNO.luce if luce else LEGNO.base)          # corona di legno
            else:
                t.p(x, y, LEGNO.bordo)                                 # il vuoto fra i raggi
    import math
    for k in range(6):                                                 # sei raggi
        ang = k * math.pi / 3 + math.pi / 6
        for s_ in range(1, 20):
            f = s_ / 20
            x = round(cx + math.cos(ang) * (rx - 3) * f)
            y = round(cy + math.sin(ang) * (ry - 3) * f)
            if dentro(x, y, rx - 3.2, ry - 3.2):
                t.p(x, y, LEGNO.luce if math.cos(ang) < 0 else LEGNO.base)
    t.r(cx - 1, cy - 1, 3, 3, C("neutri", 1))                          # mozzo
    t.p(cx - 1, cy - 1, C("neutri", 3))


def carro(st, cx, cy):
    """Il carro di Rufino in lavorazione, con la regola M6 (proposta del thread degli esterni): lato lungo
    parallelo allo schermo, faccia davanti intera, piano di sopra schiacciato a 1/3 della profondita',
    niente fianchi ne' diagonali, ruote come ellissi strette, base sul suolo con l'ombra a destra-basso.
    Le «ali»: le due sponde aperte all'infuori, quella dietro alzata contro il muro, quella davanti
    abbassata verso chi guarda."""
    x, y = st.px(cx, cy)
    L = 60                          # lunghezza del cassone
    sopra = 8                       # profondita' 24 px, schiacciata a 1/3
    fronte = 12                     # la faccia davanti del cassone
    suolo = y + 30                  # dove poggiano le ruote

    def f():
        t = st.t
        top = suolo - 10 - fronte - sopra
        t.ombra(x + 2, top + sopra, L, fronte + 10, alto=24)
        # la sponda di dietro aperta: una tavola che sale all'indietro sopra il piano (ala)
        for i in range(6):
            t.r(x + 2 - i // 2, top - 6 + i, L - 4 + i, 1, LEGNO.luce if i < 2 else LEGNO.base)
        t.r(x + 1 - 3, top - 7, L - 2 + 3, 1, LEGNO.bordo)
        # il piano di sopra (assi per lungo), schiacciato
        PIANALE = Mat("legno e cuoio", 2, 3, 3, 0)
        t.r(x, top, L, sopra, PIANALE.base)
        t.r(x, top, L, 1, PIANALE.luce)
        for k in range(top + 3, top + sopra, 3):
            t.r(x + 1, k, L - 2, 1, PIANALE.ombra)
        # una ruota nuova distesa sul piano: ellisse schiacciata a 1/3
        t.ellisse(x + 18, top + 4, 8, 3, C("neutri", 1))
        t.ellisse(x + 18, top + 4, 6, 2, LEGNO.base)
        t.r(x + 17, top + 3, 2, 2, LEGNO.ombra)
        # la faccia davanti del cassone, intera
        t.solido(x, top + sopra, L, fronte, LEGNO, ombra=False)
        for k in range(x + 10, x + L - 4, 10):
            t.r(k, top + sopra + 1, 1, fronte - 2, LEGNO.ombra)
        # la sponda davanti aperta verso il basso (ala): una tavola chiara che sporge dal bordo
        t.r(x + 4, top + sopra + fronte, L - 8, 3, PIANALE.base)
        t.r(x + 4, top + sopra + fronte, L - 8, 1, PIANALE.luce)
        t.r(x + 3, top + sopra + fronte + 3, L - 6, 1, LEGNO.bordo)
        # le ruote: in piedi davanti al cassone, ellissi appena piu' alte che larghe (M6 c), poggiate al suolo
        for rx in (x + 13, x + L - 13):
            ruota_in_piedi(t, rx, suolo - 10, 8, 10)
        # la stanga: viene avanti a destra, appoggiata al suolo su un cavalletto
        t.r(x + L, top + sopra + 4, 22, 2, LEGNO.base)
        t.r(x + L, top + sopra + 4, 22, 1, LEGNO.luce)
        t.r(x + L, top + sopra + 6, 22, 1, LEGNO.bordo)
        t.r(x + L + 18, top + sopra + 7, 2, suolo - (top + sopra + 7), LEGNO.ombra)
        t.ombra(x + L, top + sopra + 4, 22, 3, alto=8)
    st.metti(suolo, f)
    for i in range(5):
        for j in range(2):
            st.segna(cx + i, cy + j, "k")


def letto(st, cx, cy, coperta=ROSSO):
    """Un pagliericcio dell'ospizio: paglia, coperta, il cuscino bianco in alto."""
    x, y = st.px(cx, cy)

    def f():
        t = st.t
        t.solido(x + 2, y + 2, 28, 14, PAGLIA)
        t.solido(x + 3, y + 3, 6, 11, BIANCO, ombra=False)
        t.solido(x + 11, y + 3, 18, 12, coperta, ombra=False)
        for i in range(x + 13, x + 28, 4):
            t.p(i, y + 8, coperta.luce)
    st.metti(y + 16, f)
    st.segna(cx, cy, "l")
    st.segna(cx + 1, cy, "l")


def stemma(st, cx, dy=8):
    """Lo stemma della citta': scudo rosso col monte bianco a cinque cime (senza lambello)."""
    x, y = st.px(cx, 0)
    t = st.t
    x, y = x + 3, y + dy
    t.r(x + 1, y + 1, 12, 16, C("pietra calcarea", 2))   # L3 sul muro
    t.r(x - 1, y - 1, 12, 15, NERO())
    t.r(x, y, 10, 11, ROSSO.base)
    for i in range(4):
        t.r(x + i + 1, y + 11 + i, 8 - 2 * i, 1, ROSSO.base)
    t.r(x, y, 1, 11, ROSSO.luce)
    t.r(x + 8, y, 2, 11, ROSSO.ombra)
    # il monte: cinque cime (tre in alto, due piu' basse ai lati), bianco
    bianco = C("neutri", 4)
    for (mx, my) in ((x + 2, y + 5), (x + 4, y + 3), (x + 6, y + 5)):
        t.r(mx, my, 2, 2, bianco)
    t.r(x + 1, y + 7, 8, 2, bianco)
    t.r(x + 3, y + 5, 4, 2, bianco)
    t.p(x + 1, y + 6, bianco); t.p(x + 8, y + 6, bianco)


def torcia(st, cx, dy=16):
    x, y = st.px(cx, 0)
    t = st.t
    x += 7
    t.r(x, y + dy, 2, 8, C("neutri", 1))
    t.r(x - 1, y + dy - 4, 4, 4, C("vermiglio comunale", 2))
    t.r(x, y + dy - 6, 2, 3, C("oro e bronzo", 3))
    t.p(x, y + dy - 7, C("oro e bronzo", 3))


def chiarina(st, cx, dy=12):
    """La chiarina di Fazio appesa al muro: la tromba lunga d'ottone col pennoncello rosso col monte."""
    x, y = st.px(cx, 0)
    t = st.t
    x, y = x + 2, y + dy
    t.r(x + 1, y + 1, 26, 2, C("pietra calcarea", 3))
    t.r(x, y, 24, 2, ORO.base)
    t.r(x, y, 24, 1, ORO.luce)
    t.r(x + 23, y - 2, 3, 6, ORO.base)
    t.r(x + 25, y - 2, 1, 6, ORO.ombra)
    t.p(x + 5, y, ORO.luce if False else C("oro e bronzo", 3))
    t.r(x + 6, y + 2, 10, 7, ROSSO.base)
    t.r(x + 6, y + 2, 1, 7, ROSSO.luce)
    t.r(x + 9, y + 4, 4, 1, C("neutri", 4))
    t.r(x + 8, y + 5, 6, 2, C("neutri", 4))


def rastrelliera_chiavi(st, cx, dy=10):
    x, y = st.px(cx, 0)
    t = st.t
    x += 2
    t.r(x + 1, y + dy + 1, 28, 3, C("pietra calcarea", 3))
    t.r(x, y + dy, 28, 3, LEGNO.base)
    t.r(x, y + dy, 28, 1, LEGNO.luce)
    for i, kx in enumerate(range(x + 2, x + 26, 5)):
        ky = y + dy + 3
        lun = 6 + (i % 2) * 3
        t.r(kx, ky, 1, lun, ORO.base)
        t.r(kx - 1, ky + lun, 3, 2, ORO.luce if i % 2 else ORO.base)
        t.r(kx + 1, ky + lun - 2, 1, 1, ORO.ombra)


def disegni_appesi(st, cx, dy=10):
    """I disegni a carboncino di Gabrione appesi al muro: fogli chiari con segni scuri."""
    x, y = st.px(cx, 0)
    t = st.t
    for i, (ox, oy) in enumerate(((2, dy), (14, dy + 4), (24, dy - 1))):
        t.r(x + ox + 1, y + oy + 1, 9, 11, C("pietra calcarea", 3))
        t.r(x + ox, y + oy, 9, 11, C("neutri", 4))
        t.r(x + ox + 8, y + oy, 1, 11, C("neutri", 3))
        for k in range(3):
            t.r(x + ox + 2, y + oy + 3 + k * 2 + (i % 2), 4 + (k + i) % 3, 1, C("neutri", 1))
        t.p(x + ox + 4, y + oy, C("neutri", 1))


def leggio(st, cx, cy):
    x, y = st.px(cx, cy)

    def f():
        t = st.t
        t.solido(x + 4, y - 2, 9, 7, LEGNO)
        t.r(x + 5, y - 1, 7, 4, C("neutri", 4))     # il libro aperto
        t.r(x + 8, y - 1, 1, 4, C("neutri", 3))
        t.r(x + 7, y + 5, 3, 9, LEGNO.ombra)
        t.r(x + 5, y + 13, 7, 2, LEGNO.base)
    st.metti(y + 15, f)
    st.segna(cx, cy, "g")


def scranno(st, cx, cy):
    """Il seggio alto dei consoli: lo schienale si vede contro la tavola."""
    x, y = st.px(cx, cy)

    def f():
        t = st.t
        t.solido(x + 3, y - 10, 10, 14, LEGNO_SCURO)
        t.r(x + 5, y - 8, 6, 2, ROSSO.base)
        t.solido(x + 2, y + 4, 12, 6, LEGNO)
    st.metti(y + 10, f)
    st.segna(cx, cy, "s")


def colonna(st, cx, cy):
    x, y = st.px(cx, cy)

    def f():
        t = st.t
        t.ombra(x + 3, y - 18, 10, 34, alto=34)
        t.solido(x + 3, y - 18, 10, 34, PIETRA, ombra=False)
        t.r(x + 2, y - 20, 12, 3, PIETRA.luce)
        t.r(x + 2, y + 14, 12, 3, PIETRA.base)
    st.metti(y + 16, f)
    st.segna(cx, cy, "n")


def giara(st, cx, cy, dx=3, dy=0):
    x, y = st.px(cx, cy)
    x, y = x + dx, y + dy

    def f():
        t = st.t
        t.ombra(x, y, 10, 14)
        t.ellisse(x + 5, y + 8, 5, 6, COTTO.base)
        t.ellisse(x + 4, y + 6, 2, 3, COTTO.luce)
        for yy in range(y + 3, y + 15):
            t.p(x + 9, yy, COTTO.ombra)
        t.r(x + 3, y, 5, 3, COTTO.ombra)
        t.r(x + 3, y, 5, 1, COTTO.luce)
    st.metti(y + 14, f)
    st.segna(cx, cy, "j")


# --- piccoli oggetti (sopra tavoli, banchi, mensole) ------------------------------------------------
def o_fiasco(t, x, y, i=0):
    t.r(x, y - 5, 4, 5, C("verde dei monti", 2) if i % 2 else C("oro e bronzo", 1))
    t.p(x, y - 5, C("verde dei monti", 3) if i % 2 else C("oro e bronzo", 2))
    t.r(x + 1, y - 7, 2, 2, C("legno e cuoio", 2))


def o_albarello(t, x, y, i=0):
    """Il vaso da spezieria: bianco con la fascia azzurra (maiolica arcaica)."""
    t.r(x, y - 6, 4, 6, C("neutri", 4))
    t.r(x + 3, y - 6, 1, 6, C("neutri", 3))
    t.r(x, y - 4, 4, 2, C("cielo e acqua", 2) if i % 3 else C("verde dei monti", 2))
    t.r(x, y - 7, 4, 1, C("legno e cuoio", 1))


def o_libro(t, x, y, i=0):
    c = (C("vermiglio comunale", 1), C("legno e cuoio", 1), C("verde dei monti", 1))[i % 3]
    t.r(x, y - 7, 3, 7, c)
    t.r(x, y - 7, 1, 7, C("oro e bronzo", 2))


def o_boccale(t, x, y, i=0):
    t.r(x, y, 3, 4, C("cotto e coppi", 3))
    t.r(x, y, 1, 4, C("cotto e coppi", 4))
    t.p(x + 3, y + 1, C("cotto e coppi", 2))


def o_tavoliere(t, x, y, i=0):
    for yy in range(4):
        for xx in range(6):
            t.r(x + xx * 2, y + yy * 2, 2, 2, C("neutri", 4) if (xx + yy) % 2 else C("legno e cuoio", 0))
    t.p(x + 3, y + 2, C("vermiglio comunale", 2))
    t.p(x + 7, y + 4, C("neutri", 1))


def o_abaco(t, x, y, i=0):
    t.r(x, y, 14, 8, C("legno e cuoio", 0))
    for r in range(3):
        t.r(x + 1, y + 1 + r * 2 + 1, 12, 1, C("neutri", 2))
        for b in range((r * 2 + 3) % 5 + 1):
            t.p(x + 2 + b * 2, y + 2 + r * 2, C("vermiglio comunale", 2) if r != 1 else C("oro e bronzo", 2))


def o_mortaio(t, x, y, i=0):
    t.ellisse(x + 3, y + 3, 4, 2, C("pietra calcarea", 4))
    t.r(x, y + 3, 7, 3, C("pietra calcarea", 3))
    t.r(x + 5, y + 3, 2, 3, C("pietra calcarea", 2))
    t.r(x + 3, y + 1, 2, 2, C("pietra calcarea", 1))
    t.r(x + 4, y - 4, 1, 5, C("legno e cuoio", 2))


def o_bilancia(t, x, y, i=0):
    t.r(x + 5, y - 6, 1, 8, C("oro e bronzo", 1))
    t.r(x, y - 6, 11, 1, C("oro e bronzo", 2))
    t.r(x, y - 3, 3, 1, C("oro e bronzo", 2))
    t.r(x + 8, y - 4, 3, 1, C("oro e bronzo", 2))


def o_rotoli(t, x, y, i=0):
    for k in range(3):
        t.r(x + k * 3, y + (k % 2), 2, 6, C("neutri", 4))
        t.p(x + k * 3 + 1, y + (k % 2), C("neutri", 3))


def o_pane(t, x, y, i=0):
    t.ellisse(x + 3, y + 2, 3, 2, C("oro e bronzo", 1))
    t.r(x + 1, y + 1, 3, 1, C("oro e bronzo", 2))


def o_attrezzi(t, x, y, i=0):
    t.r(x, y, 10, 1, C("neutri", 2))           # la sega
    for k in range(0, 10, 2):
        t.p(x + k, y + 1, C("neutri", 1))
    t.r(x + 12, y - 2, 1, 5, C("legno e cuoio", 1))   # il martello
    t.r(x + 11, y - 3, 4, 2, C("neutri", 2))


def o_serratura(t, x, y, i=0):
    t.r(x, y, 6, 5, C("neutri", 1))
    t.r(x, y, 6, 1, C("neutri", 2))
    t.r(x + 2, y + 2, 1, 2, C("neutri", 0))


def o_ciotola(t, x, y, i=0):
    t.ellisse(x + 3, y + 1, 3, 1, C("legno e cuoio", 3))
    t.r(x + 1, y + 2, 5, 2, C("legno e cuoio", 2))


OGGETTI = {"fiaschi": o_fiasco, "albarelli": o_albarello, "libri": o_libro, "boccale": o_boccale,
           "tavoliere": o_tavoliere, "abaco": o_abaco, "mortaio": o_mortaio, "bilancia": o_bilancia,
           "rotoli": o_rotoli, "pane": o_pane, "attrezzi": o_attrezzi, "serratura": o_serratura,
           "ciotola": o_ciotola, "fiasco": o_fiasco}


def esamina(st, cx, cy):
    """Una cella da esaminare (cartello, oggetto sul banco, stemma): 'e' nella griglia."""
    if 0 <= cy < st.ch:
        st.marchi[cy][cx] = "e"


# --- le stanze --------------------------------------------------------------------------------------
def taverna(variante="giorno"):
    """La taverna del corso, di Padellino (San Pietro): il banco con le botti, il camino, tre tavoli.
    Nel DIGIUNO i tavoli sono vuoti e le panche stanno capovolte sopra (l'ordine di Ubaldo, A1-05)."""
    st = Stanza("taverna", 14, 9, "cotto", seme=3)
    st.finestra(1); st.finestra(3)
    scaffale_a_muro(st, 5, 2, "fiaschi")
    camino(st, 8)
    esamina(st, 8, 3)
    # il banco a destra con Padellino dietro e le botti contro il muro
    banco(st, 10, 5, 3, oggetti=((4, -2, "boccale"), (14, -3, "fiasco"), (26, -2, "pane")))
    botte(st, 11, 3); botte(st, 12, 3); botte(st, 13, 4)
    figura(st, 11, 4, "mercante", "fiasco_grembiule", fumetto=True, nome="Padellino")       # Padellino
    pieno = variante == "giorno"
    for (tx, ty) in ((1, 4), (5, 5), (1, 7)):
        tavolo(st, tx, ty, 2, oggetti=((5, 1, "boccale"), (18, 0, "pane")) if pieno else ())
        if pieno:
            panca(st, tx, ty + 1, 2)
        else:
            for k in range(2):
                sgabello(st, tx + k, ty, rovesciato=True, dy=-2)
    if pieno:
        figura(st, 1, 5, "anziano")            # un avventore
        figura(st, 6, 6, "popolana", dx=-4)    # un'avventrice
    figura(st, 7, 7, giocatore=True)
    giara(st, 13, 6)
    return st


def bottega_conti(variante="giorno"):
    """La bottega dei conti e dei congegni (Sant'Agostino): Fazio, Lauretta, Ciotto e Nicoluccio.
    A muro le chiavi e le serrature, la chiarina; il banco dei conti con l'abaco; il tavoliere di Ciotto.
    NOTTE con BORGO_FUORI: «la bottega l'hanno rovesciata» (sgabelli a terra, serrature sparse)."""
    st = Stanza("bottega_conti", 12, 8, "cotto", seme=5)
    st.finestra(1)
    rastrelliera_chiavi(st, 3)
    rastrelliera_chiavi(st, 5, dy=26)
    chiarina(st, 7, dy=16)
    esamina(st, 7, 3)
    scaffale_a_muro(st, 9, 2, "libri", righe=2)
    rovesciata = variante == "rovesciata"
    banco(st, 1, 4, 3, oggetti=() if rovesciata else ((6, -2, "abaco"), (32, 0, "rotoli")))
    tavolo(st, 7, 5, 2, oggetti=() if rovesciata else ((9, 1, "tavoliere"),))
    if rovesciata:
        sgabello(st, 6, 5, rovesciato=True); sgabello(st, 9, 6, rovesciato=True); sgabello(st, 3, 6, rovesciato=True)
        for (ox, oy) in ((2, 6), (5, 3), (10, 5), (4, 5)):
            x, y = st.px(ox, oy)
            st.metti(y + 10, lambda x=x, y=y: o_serratura(st.t, x + 5, y + 8))
        figura(st, 8, 3, "mercante", "chiave", fumetto=True, nome="Fazio")              # Fazio solo, di notte
    else:
        sgabello(st, 6, 5); sgabello(st, 9, 5)
        figura(st, 2, 3, "popolana", "tavoletta_conti", fumetto=True, nome="Lauretta")     # Lauretta dietro il banco
        figura(st, 3, 5, "bambino", None, dx=-6, nome="Nicoluccio")                       # Nicoluccio accanto alla madre
        figura(st, 9, 6, "mercante", "tavoliere", nome="Ciotto")                          # Ciotto al tavoliere
        figura(st, 10, 4, "mercante", "chiave", nome="Fazio")                            # Fazio
    figura(st, 6, 7, giocatore=True)
    giara(st, 11, 7)
    return st


def bottega_carradore(variante="giorno"):
    """La bottega del carradore (Quaranta Martiri), di Mastro Rufino: pavimento d'assi, il carro in mezzo
    con le sponde «ad ali», le ruote appese, il banco con gli attrezzi, il portone largo (3 celle)."""
    st = Stanza("bottega_carradore", 14, 9, "assi", seme=9, muro="pietra", uscita=3)
    st.finestra(1)
    for cx in (3, 4, 5):
        ruota_a_muro(st, cx, dy=20 if cx % 2 else 14)
    scaffale_a_muro(st, 10, 3, "attrezzi" if False else "fiaschi", righe=1, cy=1)
    banco(st, 9, 4, 4, oggetti=((4, -1, "attrezzi"), (40, -3, "boccale")))
    carro(st, 2, 5)
    esamina(st, 4, 7)
    figura(st, 8, 6, "mercante", "ruota", fumetto=True, nome="Rufino")                    # Rufino
    # i trucioli sul pavimento, legno chiaro (F7)
    rnd = random.Random(4)
    for _ in range(40):
        x, y = st.px(rnd.randint(1, 12), rnd.randint(4, 8))
        st.t.r(x + rnd.randint(0, 12), y + rnd.randint(0, 12), 2, 1, C("legno e cuoio", 3))
    botte(st, 12, 7); botte(st, 13, 7, dx=-2, dy=3)
    figura(st, 7, 8, giocatore=True)
    return st


def spezieria(variante="giorno"):
    """Spezieria e ospizio (San Pietro), di Gabrione e Valenza. A sinistra la spezieria: gli albarelli,
    il banco col mortaio e la bilancia, i disegni a carboncino. A destra l'ospizio: tre pagliericci.
    Valenza cura (PV e ferite della gola) e lo dice: e' il posto dove ci si rimette in piedi."""
    st = Stanza("spezieria", 14, 9, "cotto", seme=11)
    st.finestra(1)
    scaffale_a_muro(st, 2, 3, "albarelli", righe=2)
    disegni_appesi(st, 5)
    esamina(st, 5, 3)
    banco(st, 1, 5, 4, oggetti=((8, -3, "mortaio"), (30, -1, "bilancia"), (50, -2, "albarelli")))
    figura(st, 2, 4, "gabrione", "carboncino", fumetto=True, nome="Gabrione")
    # il tramezzo con l'arco fra spezieria e ospizio
    for cy in (3, 4):
        st.segna(7, cy, "#")
    colonna(st, 7, 4)
    st.finestra(10, larga=2)
    for i, cy in enumerate((3, 5, 7)):
        letto(st, 11, cy, coperta=(ROSSO, CIELO, VERDE)[i])
    figura(st, 9, 5, "popolana", "ciotola", fumetto=True, nome="Valenza")                  # Valenza
    figura(st, 6, 7, giocatore=True)
    giara(st, 13, 8); giara(st, 5, 7)
    return st


def casa_medico(variante="giorno"):
    """La casa del medico (San Martino), di Vanni: i libri, i rotoli sugli assedi, il letto per i feriti."""
    st = Stanza("casa_medico", 12, 8, "cotto", seme=13)
    st.finestra(1)
    scaffale_a_muro(st, 3, 3, "libri", righe=2)
    scaffale_a_muro(st, 7, 2, "albarelli", righe=1)
    tavolo(st, 3, 5, 3, oggetti=((4, 0, "rotoli"), (28, 1, "ciotola"), (38, -1, "libri")))
    esamina(st, 4, 4)
    letto(st, 9, 4, coperta=CIELO)
    leggio(st, 1, 4)
    figura(st, 6, 5, "anziano", "borsa_medico", fumetto=True, nome="Vanni")              # Vanni
    figura(st, 6, 7, giocatore=True)
    return st


def sala_consoli(variante="giorno"):
    """La sala grande del Palazzo dei Consoli (Piazza Grande): lastre, muro di pietra con lo stemma e
    le torce, la tavola lunga dei consoli con gli scranni, il leggio del notaio. Riusata nell'Atto II (A2-10)."""
    st = Stanza("sala_consoli", 15, 10, "lastre", seme=17, muro="pietra")
    st.finestra(1); st.finestra(3)
    stemma(st, 7)
    esamina(st, 7, 3)
    torcia(st, 5); torcia(st, 9)
    for cx in (5, 7, 9):
        scranno(st, cx, 4)
    tavolo(st, 4, 5, 7, oggetti=((10, 1, "rotoli"), (52, 0, "libri"), (80, 1, "rotoli")))
    leggio(st, 12, 4)
    esamina(st, 12, 5)
    panca(st, 1, 4, 2); panca(st, 1, 8, 2); panca(st, 12, 8, 2)
    colonna(st, 3, 7); colonna(st, 11, 7)
    figura(st, 12, 5, "notaio", None, fumetto=True, nome="Notaio del Comune")  # il notaio dei consoli (NPC d'ambiente)
    figura(st, 13, 3, "soldato", None)                     # la guardia
    figura(st, 7, 8, giocatore=True)
    return st


STANZE = {"taverna": taverna, "bottega_conti": bottega_conti, "bottega_carradore": bottega_carradore,
          "spezieria": spezieria, "casa_medico": casa_medico, "sala_consoli": sala_consoli}
VARIANTI = {"taverna": ("giorno", "digiuno"), "bottega_conti": ("giorno", "rovesciata")}


# --- nel gioco ---------------------------------------------------------------------------------------
# stanza -> (id dell'area, area di fuori, monumento col portone, lettera del varco fuori, spawn fuori)
INTERNI = {
    "taverna": ("taverna_interno", "san_pietro", "taverna", "E", 3),
    "spezieria": ("spezieria_interno", "san_pietro", "spezieria", "G", 4),
    "bottega_conti": ("bottega_conti_interno", "sant_agostino", "bottega_conti", "E", 3),
    "bottega_carradore": ("carradore_interno", "piazza_quaranta_martiri", "bottega_carradore", "I", 6),
    "casa_medico": ("casa_medico_interno", "san_martino", "casa_medico", "H", 5),
    "sala_consoli": ("sala_consoli", "piazza_grande", "consoli", "E", 4),
}
STANZA_DELL_AREA = {v[0]: k for k, v in INTERNI.items()}


def stanza_di_gioco(nome):
    """La stanza disegnata coi riferimenti (rampa, tono), senza figure."""
    global GIOCO, NOTTE
    GIOCO, NOTTE = True, False
    st = STANZE[nome]("giorno")
    st.disegna()
    return st


def griglia_di_gioco(st):
    """La griglia dell'area in tile da 8 px: dentro la stanza le celle da 16 px (libere 'L', solide '#'),
    fuori il buio solido; sotto l'uscita la soglia calpestabile e, sull'ultima riga, il varco 'A'."""
    tw, th = st.t.w // 8, st.t.h // 8
    stanza_basso = st.y0 + st.ch * CELLA
    uscita = [cx for cx in range(st.cw) if st.marchi[st.ch - 1][cx] == "A"]
    righe = []
    for ty in range(th):
        r = []
        for tx in range(tw):
            x, y = tx * 8, ty * 8
            cx, cy = (x - st.x0) // CELLA, (y - st.y0) // CELLA
            dentro = st.x0 <= x < st.x0 + st.cw * CELLA and st.y0 <= y < stanza_basso
            if dentro:
                r.append("#" if st.solide[cy][cx] else "L")
            elif y >= stanza_basso and st.x0 <= x < st.x0 + st.cw * CELLA and cx in uscita:
                r.append("A" if ty == th - 1 else "L")
            else:
                r.append("#")
        righe.append("".join(r))
    return righe


def spawn_di_gioco(st):
    """Dove si arriva entrando: sopra l'uscita, almeno 6 tile dal varco 'A' (regola di genera_mondo),
    sulla prima cella libera della colonna dell'uscita o delle vicine."""
    g = griglia_di_gioco(st)
    uscita = [cx for cx in range(st.cw) if st.marchi[st.ch - 1][cx] == "A"]
    x0 = (st.x0 + uscita[0] * CELLA + len(uscita) * CELLA // 2) // 8
    varco = len(g) - 1
    for y in range(varco - 6, 0, -1):
        for dx in (0, -1, 1, -2, 2, -3, 3):
            x = x0 + dx
            if all(g[yy][xx] == "L" for yy in (y - 1, y, y + 1) for xx in (x - 1, x, x + 1)):
                return x, y
    raise ValueError(f"nessuna cella libera per lo spawn in {st}")


def testo_area(nome):
    aid, fuori, mid, _, spawn_fuori = INTERNI[nome]
    st = stanza_di_gioco(nome)
    g = griglia_di_gioco(st)
    sx, sy = spawn_di_gioco(st)
    doc = (STANZE[nome].__doc__ or "").strip().splitlines()
    righe = ["# GENERATO da tools/pittore_interni.py --aree: non modificare a mano (la stanza e' scritta li').",
             *("# " + d.strip() for d in doc),
             f"id {aid}", f"etichetta AREA_{aid.upper()}", f"dimensioni {len(g[0])} {len(g)}", "monte basso",
             "interno", f"riferimento {len(g[0]) // 2} {len(g) // 2}", "fattore 0.73",
             f"spawn 0 {sx} {sy}", f"spawn 1 {sx} {sy}", f"uscita A {fuori} 1", "griglia", *g]
    return "\n".join(righe) + "\n"


def scrivi_aree():
    for nome, (aid, *_r) in INTERNI.items():
        with open(os.path.join(REPO, "mondo", "aree", aid + ".area"), "w", encoding="utf-8") as f:
            f.write(testo_area(nome))


def dipinge(area_id):
    return area_id in STANZA_DELL_AREA


def dipingi(q, a):
    """Il fondale dell'interno nel Quadro di genera_mondo (riferimenti (rampa, tono) per pixel)."""
    st = stanza_di_gioco(STANZA_DELL_AREA[a["id"]])
    if (st.t.w, st.t.h) != (q.w, q.h):
        raise ValueError(f"{a['id']}: la stanza e' {st.t.w}x{st.t.h} px, l'area {q.w}x{q.h}: rifare --aree")
    for y in range(q.h):
        for x in range(q.w):
            q.px[y][x] = st.t.px[y][x]
    return q


def tavole(uscita):
    """Le anteprime RGB con le figure (come i mockup di /mnt/project-files/interni/)."""
    global GIOCO, NOTTE
    GIOCO = False
    os.makedirs(uscita, exist_ok=True)
    fatte = []
    for nome, f in STANZE.items():
        for var in VARIANTI.get(nome, ("giorno",)):
            NOTTE = var == "rovesciata"
            st = f(var)
            file = os.path.join(uscita, f"{nome}_{var}.png")
            st.disegna().png(file)
            fatte.append(file)
    GIOCO, NOTTE = True, False
    return fatte


def main(argv):
    if argv[:1] == ["--aree"]:
        scrivi_aree()
    elif argv[:1] == ["--tavole"] and len(argv) == 2:
        print("\n".join(tavole(argv[1])))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
