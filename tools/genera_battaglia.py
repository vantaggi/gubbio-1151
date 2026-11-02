#!/usr/bin/env python3
"""La grafica della battaglia, tutta procedurale: scrive include/battaglia_grafica.h.

- Tre sfondi 32x32 tile (uno per incontro: le mura della citta' per la Pattuglia Perugina, il bosco
  degli stradoni per l'Imboscata, Piazza Grande col Palazzo dei Consoli per il Duello con Corrado):
  cielo a fasce, il profilo lontano, il suolo; tile condivisi e deduplicati.
- Gli sprite dei tre Santi (32x32, due pose: ferma e in azione) e dei nemici (Fante di Perugia,
  Balestriere Pesante, Spia umbra a 32x32, Corrado di Spoleto a 64x64), disegnati con forme semplici.
I colori vengono tutti dalla palette della Guida di stile (stile/dati/palette.json).

    python tools/genera_battaglia.py            # controlla che l'header sia aggiornato
    python tools/genera_battaglia.py --scrivi   # lo riscrive
"""
import os
import sys

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RADICE, "tools"))
sys.path.insert(0, os.path.join(RADICE, "stile"))

import stile as S  # noqa: E402

USCITA = os.path.join(RADICE, "include", "battaglia_grafica.h")
INCONTRI = ("pattuglia", "imboscata", "duello", "rito")
PANNELLO_Y = 104      # da qui in giu' il pannello dei comandi

# --- palette: (rampa, tono) della Guida di stile -------------------------------------------------
PALETTE_SFONDO = [
    ("neutri", 0), ("cielo e acqua", 0), ("cielo e acqua", 1), ("cielo e acqua", 2), ("cielo e acqua", 3),
    ("cielo e acqua", 4), ("pietra calcarea", 1), ("pietra calcarea", 2), ("pietra calcarea", 3),
    ("pietra calcarea", 5), ("verde dei monti", 0), ("verde dei monti", 2), ("verde dei monti", 3),
    ("cotto e coppi", 2), ("cotto e coppi", 4), ("legno e cuoio", 1),
]
PALETTE_SANTI = [
    ("neutri", 0), ("neutri", 0), ("pelle", 0), ("pelle", 2), ("oro e bronzo", 1), ("oro e bronzo", 3),
    ("neutri", 4), ("neutri", 2), ("vermiglio comunale", 1), ("vermiglio comunale", 3), ("cielo e acqua", 2),
    ("cielo e acqua", 4), ("legno e cuoio", 1), ("legno e cuoio", 3), ("pietra calcarea", 5),
    ("pietra calcarea", 2),
]
PALETTE_NEMICI = [
    ("neutri", 0), ("neutri", 0), ("pelle", 0), ("pelle", 2), ("vermiglio comunale", 1),
    ("vermiglio comunale", 3), ("neutri", 4), ("neutri", 2), ("pietra calcarea", 2), ("pietra calcarea", 5),
    ("legno e cuoio", 1), ("legno e cuoio", 3), ("neutri", 1), ("neutri", 3), ("oro e bronzo", 3),
    ("verde dei monti", 0),
]
# indici nominati delle palette degli sprite
C, PELLE_S, PELLE, ORO_S, ORO, BIANCO, GRIGIO = 1, 2, 3, 4, 5, 6, 7
ROSSO_S, ROSSO, AZZURRO, AZZURRO_L, SAIO, SAIO_L, ACCIAIO_L, ACCIAIO = 8, 9, 10, 11, 12, 13, 14, 15
# nemici
N_ROSSO_S, N_ROSSO, N_BIANCO, N_GRIGIO, N_ACCIAIO, N_ACCIAIO_L = 4, 5, 6, 7, 8, 9
N_LEGNO, N_LEGNO_L, N_SCURO, N_MEDIO, N_ORO, N_VERDE = 10, 11, 12, 13, 14, 15


# --- tela a indici ---------------------------------------------------------------------------------
class Tela:
    def __init__(self, w, h, fondo=0):
        self.w, self.h = w, h
        self.px = [[fondo] * w for _ in range(h)]

    def punto(self, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = c

    def rett(self, x0, y0, w, h, c):
        for y in range(int(y0), int(y0 + h)):
            for x in range(int(x0), int(x0 + w)):
                self.punto(x, y, c)

    def ellisse(self, cx, cy, rx, ry, c):
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1:
                    self.punto(x, y, c)

    def linea(self, x0, y0, x1, y1, c, spessore=1):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for k in range(n + 1):
            t = k / max(n, 1)
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            self.rett(x - spessore // 2, y - spessore // 2, spessore, spessore, c)

    def trapezio(self, cx, y0, y1, w0, w1, c):
        for y in range(int(y0), int(y1)):
            t = (y - y0) / max(y1 - y0 - 1, 1)
            m = (w0 + (w1 - w0) * t) / 2
            self.rett(cx - m, y, 2 * m, 1, c)

    def contorno(self, colore=C):
        """Il contorno scuro intorno alla figura: ogni pixel trasparente accanto a uno pieno."""
        pieni = {(x, y) for y in range(self.h) for x in range(self.w) if self.px[y][x]}
        for y in range(self.h):
            for x in range(self.w):
                if not self.px[y][x] and any((x + dx, y + dy) in pieni for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    self.px[y][x] = colore
        return self

    def specchia(self):
        self.px = [list(reversed(r)) for r in self.px]
        return self

    def tile(self):
        """I tile 8x8 nell'ordine degli sprite (riga per riga di tile)."""
        out = []
        for ty in range(self.h // 8):
            for tx in range(self.w // 8):
                out.append([self.px[ty * 8 + y][tx * 8:tx * 8 + 8] for y in range(8)])
        return out


# --- i Santi (guardano a destra) -------------------------------------------------------------------
def corpo_santo(t, veste, veste_l, azione):
    t.trapezio(15, 13, 30, 8, 16, veste)            # la veste che si allarga
    t.rett(15, 14, 2, 15, veste_l)                  # la piega di luce
    t.rett(9, 29, 14, 2, veste)
    t.ellisse(15.5, 9.5, 3.6, 3.8, PELLE)           # la testa
    t.rett(17, 9, 1, 1, C)                          # l'occhio, verso destra
    t.rett(12, 11, 2, 2, PELLE_S)
    braccio_y = 15 if azione else 18
    t.rett(17, braccio_y, 6, 3, veste)
    t.rett(22, braccio_y, 2, 3, PELLE)
    return braccio_y


def ubaldo(azione):
    """Sant'Ubaldo vescovo: cappa bianca e oro, la mitria, il pastorale."""
    t = Tela(32, 32)
    y = corpo_santo(t, BIANCO, ORO, azione)
    t.rett(11, 20, 10, 2, ORO)                      # il bordo d'oro della cappa
    t.trapezio(15.5, 1, 7, 3, 7, BIANCO)            # la mitria
    t.rett(15, 1, 1, 6, ORO)
    t.rett(12, 6, 8, 1, ORO)
    x = 24 if not azione else 26
    t.linea(x, y - 12 if azione else y - 10, x, 30, ORO_S, 1)   # il pastorale
    t.ellisse(x - 1, y - 13 if azione else y - 11, 2.5, 2.5, ORO)
    t.punto(x - 1, y - 13 if azione else y - 11, 0)
    return t.contorno()


def giorgio(azione):
    """San Giorgio cavaliere: armatura, la sopravveste bianca con la croce rossa, scudo e spada."""
    t = Tela(32, 32)
    y = corpo_santo(t, ACCIAIO, ACCIAIO_L, azione)
    t.rett(12, 15, 7, 9, BIANCO)                    # la sopravveste
    t.rett(15, 15, 1, 9, ROSSO)
    t.rett(12, 18, 7, 1, ROSSO)
    t.ellisse(15.5, 7.5, 4, 3, ACCIAIO)             # l'elmo
    t.rett(15, 3, 2, 3, ROSSO)                      # il pennacchio
    t.ellisse(9, 20, 4, 5, AZZURRO)                 # lo scudo, a sinistra
    t.rett(8, 17, 2, 7, BIANCO)
    t.rett(7, 19, 5, 2, BIANCO)
    if azione:
        t.linea(23, y + 1, 31, y - 7, ACCIAIO_L, 2)   # la spada alta
    else:
        t.linea(23, y + 1, 29, y + 9, ACCIAIO_L, 2)
    return t.contorno()


def antonio(azione):
    """Sant'Antonio abate: il saio col cappuccio, il bastone a tau col campanello, la fiamma."""
    t = Tela(32, 32)
    y = corpo_santo(t, SAIO, SAIO_L, azione)
    t.ellisse(14.5, 8, 4.6, 4.8, SAIO)              # il cappuccio
    t.ellisse(16, 9.5, 3, 3.4, PELLE)
    t.rett(17, 9, 1, 1, C)
    t.rett(14, 12, 3, 2, BIANCO)                    # la barba
    t.linea(25, y - 9, 25, 30, SAIO_L, 1)           # il tau
    t.rett(23, y - 9, 5, 1, SAIO_L)
    t.ellisse(27.5, y - 6, 1.5, 1.5, ORO)           # il campanello
    if azione:
        t.ellisse(28, y - 3, 2.5, 3.5, ROSSO)       # la fiamma in mano
        t.ellisse(28, y - 2, 1.4, 2, ORO)
    return t.contorno()


# --- i nemici (guardano a sinistra: si disegnano a destra e si specchiano) -------------------------
def soldato(t, tunica, tunica_l, azione):
    t.trapezio(15, 13, 29, 9, 13, tunica)
    t.rett(15, 14, 2, 14, tunica_l)
    t.rett(10, 28, 4, 3, N_SCURO)
    t.rett(17, 28, 4, 3, N_SCURO)
    t.ellisse(15.5, 9.5, 3.6, 3.8, 3)
    t.rett(17, 9, 1, 1, C)
    braccio = 15 if azione else 18
    t.rett(17, braccio, 6, 3, tunica)
    t.rett(22, braccio, 2, 3, 3)
    return braccio


def fante(azione):
    """Fante di Perugia: elmo, la tunica rossa e bianca del grifo, la lancia."""
    t = Tela(32, 32)
    b = soldato(t, N_ROSSO_S, N_BIANCO, azione)
    t.rett(12, 14, 4, 13, N_ROSSO)
    t.ellisse(15.5, 7, 4, 2.6, N_ACCIAIO)
    t.rett(11, 8, 9, 1, N_ACCIAIO_L)
    if azione:
        t.linea(14, b + 1, 31, b - 1, N_LEGNO_L, 1)
        t.linea(29, b - 2, 31, b - 1, N_ACCIAIO_L, 2)
    else:
        t.linea(24, 2, 24, 30, N_LEGNO_L, 1)
        t.rett(23, 0, 3, 3, N_ACCIAIO_L)
    return t.contorno().specchia()


def balestriere(azione):
    """Balestriere Pesante: corazza, il cappello di ferro, la balestra di legno."""
    t = Tela(32, 32)
    b = soldato(t, N_ACCIAIO, N_ACCIAIO_L, azione)
    t.rett(11, 14, 9, 4, N_ROSSO)
    t.ellisse(15.5, 7, 5.5, 2.2, N_ACCIAIO)
    t.rett(14, 4, 3, 3, N_ACCIAIO)
    x = 24 if not azione else 26
    t.rett(x - 6, b - 1, 10, 2, N_LEGNO)            # il fusto
    t.linea(x + 3, b - 6, x + 3, b + 5, N_LEGNO_L, 1)  # l'arco
    t.linea(x + 3, b - 6, x - 2, b, N_GRIGIO, 1)    # la corda
    t.linea(x + 3, b + 5, x - 2, b, N_GRIGIO, 1)
    return t.contorno().specchia()


def spia(azione):
    """Spia umbra: il mantello scuro col cappuccio, il pugnale."""
    t = Tela(32, 32)
    b = soldato(t, N_SCURO, N_MEDIO, azione)
    t.trapezio(14, 12, 30, 10, 18, N_VERDE)         # il mantello
    t.ellisse(15, 8.5, 4.8, 5, N_SCURO)             # il cappuccio
    t.ellisse(16.5, 10, 2.6, 2.8, 3)
    t.rett(17, 10, 1, 1, C)
    if azione:
        t.linea(22, b, 30, b - 4, N_ACCIAIO_L, 1)
    else:
        t.linea(22, b + 1, 26, b + 4, N_ACCIAIO_L, 1)
    return t.contorno().specchia()


def spettro(azione):
    """Spettro del Dubbio: un velo grigio e sfrangiato che fluttua, due occhi vuoti, le mani che si
    allungano (in azione)."""
    t = Tela(32, 32)
    alto = 3 if azione else 5
    t.ellisse(15.5, alto + 8, 7, 8, N_MEDIO)
    t.trapezio(15.5, alto + 8, 30, 14, 20, N_MEDIO)
    for x in range(6, 26, 4):
        t.rett(x, 28, 2, 3 if (x // 4) % 2 else 1, 0)
    t.rett(9, alto + 12, 14, 10, N_GRIGIO)
    t.ellisse(12.5, alto + 8, 1.6, 2.2, N_SCURO)
    t.ellisse(18.5, alto + 8, 1.6, 2.2, N_SCURO)
    if azione:
        t.linea(23, alto + 14, 31, alto + 10, N_GRIGIO, 2)
    return t.contorno().specchia()


def corrado(azione):
    """Corrado di Spoleto, 64x64: armatura scura, l'elmo col cimiero, lo scudo, il martello d'assedio."""
    t = Tela(64, 64)
    t.trapezio(30, 24, 58, 18, 30, N_ACCIAIO)       # il corpo corazzato
    t.rett(29, 26, 4, 30, N_ACCIAIO_L)
    t.rett(20, 34, 22, 3, N_ORO)                    # la cintura
    t.rett(19, 58, 9, 6, N_SCURO)
    t.rett(34, 58, 9, 6, N_SCURO)
    t.ellisse(31, 17, 8, 8.5, N_ACCIAIO)            # l'elmo
    t.rett(26, 16, 14, 2, N_SCURO)                  # la feritoia
    t.trapezio(31, 3, 10, 3, 9, N_ROSSO)            # il cimiero
    t.ellisse(15, 40, 9, 12, N_ROSSO_S)             # lo scudo, a sinistra
    t.rett(14, 30, 3, 20, N_ORO)
    t.rett(8, 38, 15, 3, N_ORO)
    braccio = 28 if azione else 36
    t.rett(36, braccio, 13, 6, N_ACCIAIO)
    if azione:
        t.linea(48, braccio + 2, 58, 4, N_LEGNO, 3)     # il martello alzato
        t.rett(52, 0, 12, 9, N_ACCIAIO_L)
    else:
        t.linea(48, braccio + 2, 56, 60, N_LEGNO, 3)
        t.rett(51, 54, 12, 9, N_ACCIAIO_L)
    return t.contorno().specchia()


def freccia(azione):
    """Il cursore del bersaglio, 16x16: una freccia d'oro che punta in giu'; nella seconda posa e'
    due pixel piu' in basso, cosi' alternando le pose dondola."""
    t = Tela(16, 16)
    y0 = 3 if azione else 1
    t.trapezio(8, y0 + 5, y0 + 11, 10, 1, ORO)
    t.rett(6, y0, 4, 6, ORO)
    t.rett(7, y0 + 1, 1, 6, BIANCO)
    return t.contorno()


SANTI = (("UBALDO", ubaldo), ("GIORGIO", giorgio), ("ANTONIO", antonio))
NEMICI = (("FANTE", fante), ("BALESTRIERE", balestriere), ("CORRADO", corrado), ("SPIA", spia),
          ("SPETTRO", spettro))
ALTRI = (("FRECCIA", freccia),)


# --- gli sfondi ------------------------------------------------------------------------------------
def sfondo(incontro):
    """Lo sfondo 256x256 (si vedono i primi 240x160): cielo, profilo lontano, suolo."""
    t = Tela(256, 256, 1)
    orizzonte = 76
    for y in range(orizzonte):
        banda = min(4, y // 14)
        for x in range(256):
            # fasce del cielo con il passaggio a scacchiera fra una e l'altra
            sopra = y % 14 < 2 and (x + y) % 2 == 0 and banda > 0
            t.punto(x, y, 1 + (banda - 1 if sopra else banda))
    if incontro == 0:
        # le mura con le torri merlate, la porta in mezzo
        t.rett(0, 54, 256, orizzonte - 54, 7)
        for x in range(0, 256, 6):
            t.rett(x, 50, 3, 4, 7)
        for x0 in (20, 96, 170, 230):
            t.rett(x0, 34, 18, orizzonte - 34, 8)
            for x in range(x0, x0 + 18, 5):
                t.rett(x, 30, 3, 4, 8)
            t.rett(x0 + 7, 44, 3, 6, 0)
        t.ellisse(128, 72, 12, 16, 15)
        for y in range(54, orizzonte, 6):
            t.rett(0, y, 256, 1, 6)
    elif incontro == 1:
        # il monte: il bosco a macchie sul pendio, gli stradoni chiari
        for x in range(256):
            cima = 30 + int(14 * abs(((x / 256.0) * 2) % 2 - 1))
            for y in range(cima, orizzonte):
                t.punto(x, y, 11 if (x * 7 + y * 3) % 5 else 12)
        for k in range(26):
            cx, cy = (k * 41) % 256, 40 + (k * 17) % 34
            t.ellisse(cx, cy, 6, 5, 10)
        for y in range(46, orizzonte, 12):
            t.rett(0, y, 256, 2, 9)
    elif incontro == 3:
        # dentro la Basilica: le colonne della navata nella penombra, la vetrata in fondo
        t.rett(0, 0, 256, orizzonte, 1)
        for x0 in range(10, 256, 46):
            t.rett(x0, 8, 14, orizzonte - 8, 7)
            t.rett(x0 + 10, 8, 4, orizzonte - 8, 6)
        t.rett(104, 6, 48, 46, 0)
        for y in range(8, 50, 6):
            for x in range(106, 150, 6):
                t.rett(x, y, 5, 5, 3 if (x + y) % 12 else 13)
    else:
        # Piazza Grande: il Palazzo dei Consoli con la torre, e la citta' bassa
        t.rett(0, 58, 256, orizzonte - 58, 13)
        for x in range(0, 256, 9):
            t.rett(x, 56, 6, 3, 14)
        t.rett(70, 22, 116, orizzonte - 22, 8)
        for x in range(72, 186, 6):
            t.rett(x, 18, 3, 4, 8)
        t.rett(150, 4, 18, 20, 8)
        for x in range(150, 168, 5):
            t.rett(x, 1, 3, 3, 8)
        for x in range(80, 180, 16):
            t.rett(x, 32, 6, 10, 0)
            t.rett(x, 48, 6, 10, 0)
        t.rett(124, 60, 10, 16, 15)
    # il suolo: ghiaia o lastre a corsi sfalsati, allineato ai tile (pochi tile diversi)
    for y in range(orizzonte, 256):
        for x in range(256):
            if incontro == 1:
                c = 9 if (x * 3 + y * 5) % 7 else 8
            else:
                riga = y // 8
                sfalsa = 8 if riga % 2 else 0
                c = 6 if y % 8 == 7 or (x + sfalsa) % 16 == 15 else (8 if ((x + sfalsa) // 16 + riga) % 3 else 7)
            t.punto(x, y, c)
    # fuori dallo schermo (oltre 240x160) si ripete il suolo
    for y in range(160, 256):
        for x in range(256):
            t.px[y][x] = t.px[96 + (y % 8)][x % 16 + 16 * ((y // 8) % 2)]
    # il pannello in basso (da y=104): fondo scuro e cornice di pietra chiara, per i comandi,
    # gli indizi e l'esito
    for y in range(PANNELLO_Y, 160):
        for x in range(240):
            bordo = y in (PANNELLO_Y, PANNELLO_Y + 1, 158, 159) or x in (0, 1, 238, 239)
            t.px[y][x] = 9 if bordo else (0 if (y + x) % 7 else 15)
    for y in range(256):
        for x in range(240, 256):
            t.px[y][x] = t.px[y][x - 16]
    return t


def tile_e_mappe():
    tile, mappe = {}, []
    for i in range(len(INCONTRI)):
        t = sfondo(i)
        mappa = []
        for ty in range(32):
            for tx in range(32):
                chiave = tuple(tuple(t.px[ty * 8 + y][tx * 8:tx * 8 + 8]) for y in range(8))
                mappa.append(tile.setdefault(chiave, len(tile)))
        mappe.append(mappa)
    return list(tile), mappe


# --- l'header ----------------------------------------------------------------------------------------
def parole(pixel):
    out = []
    for riga in pixel:
        v = 0
        for x, c in enumerate(riga):
            v |= c << (4 * x)
        out.append(v)
    return out


def blocchi(valori, per_riga, formato):
    return "\n".join("    " + ", ".join(formato(v) for v in valori[i:i + per_riga]) + ","
                     for i in range(0, len(valori), per_riga))


def genera(palette_stile):
    colore = lambda rif: S.colore(palette_stile, rif)  # noqa: E731
    tile, mappe = tile_e_mappe()
    if len(tile) > 512:
        raise SystemExit(f"[battaglia] {len(tile)} tile di sfondo: il massimo e' 512")
    out = ["// GENERATO da tools/genera_battaglia.py: la grafica procedurale della battaglia.",
           "// Non modificare a mano.",
           "#ifndef GUBBIO_BATTAGLIA_GRAFICA_H", "#define GUBBIO_BATTAGLIA_GRAFICA_H", "",
           "#include <cstdint>", "", "#include \"bn_tile.h\"", "",
           "namespace gubbio::battaglia::grafica", "{", ""]
    for nome, pal in (("SFONDO", PALETTE_SFONDO), ("SANTI", PALETTE_SANTI), ("NEMICI", PALETTE_NEMICI)):
        out += [f"inline constexpr uint16_t PALETTE_{nome}[16] = {{",
                blocchi([colore(r) for r in pal], 8, lambda v: f"0x{v:04X}"), "};", ""]
    out += [f"inline constexpr int TILE_SFONDO_CONTEGGIO = {len(tile)};",
            "inline constexpr bn::tile TILE_SFONDO[TILE_SFONDO_CONTEGGIO] = {"]
    out += ["    { { " + ", ".join(f"0x{v:08X}" for v in parole(t)) + " } }," for t in tile]
    out += ["};", "", f"inline constexpr uint16_t SFONDO[{len(INCONTRI)}][1024] = {{"]
    for m in mappe:
        out += ["    {", blocchi(m, 32, str).replace("\n    ", "\n        ").replace("    ", "        ", 1), "    },"]
    out += ["};", ""]
    for gruppo in (SANTI, NEMICI, ALTRI):
        for nome, pittore in gruppo:
            pose = [pittore(False), pittore(True)]
            lato = pose[0].w
            tiles = [parola for p in pose for t_ in p.tile() for parola in parole(t_)]
            out += [f"inline constexpr int LATO_{nome} = {lato};",
                    f"inline constexpr int TILE_PER_POSA_{nome} = {len(pose[0].tile())};",
                    f"inline constexpr bn::tile SPRITE_{nome}[{2 * len(pose[0].tile())}] = {{"]
            out += ["    { { " + ", ".join(f"0x{v:08X}" for v in tiles[k:k + 8]) + " } },"
                    for k in range(0, len(tiles), 8)]
            out += ["};", ""]
    out += ["}", "", "#endif", ""]
    return "\n".join(out)


def main(argv):
    nuovo = genera(S.carica("palette"))
    vecchio = open(USCITA, encoding="utf-8").read() if os.path.exists(USCITA) else ""
    if "--scrivi" in argv:
        with open(USCITA, "w", encoding="utf-8", newline="\n") as f:
            f.write(nuovo)
        print(f"[battaglia] scritto {os.path.relpath(USCITA, RADICE)}")
        return 0
    if nuovo != vecchio:
        print("[battaglia] include/battaglia_grafica.h da rigenerare con --scrivi")
        return 1
    print("[battaglia] aggiornato")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
