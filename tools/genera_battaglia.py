#!/usr/bin/env python3
"""La grafica della battaglia, tutta procedurale: scrive include/battaglia_grafica.h.

- Tre sfondi 32x32 tile (uno per incontro: le mura della citta' per la Pattuglia Perugina, il bosco
  degli stradoni per l'Imboscata, Piazza Grande col Palazzo dei Consoli per il Duello con Corrado):
  cielo a fasce, il profilo lontano, il suolo; tile condivisi e deduplicati.
- Gli sprite dei tre protagonisti e dei nemici (32x32, Corrado di Spoleto 64x64) con sette pose e una
  palette ciascuno, gli effetti e i lampi: li disegna tools/sagome_battaglia.py (pezzo SAG).
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
import sagome_battaglia as SB  # noqa: E402

USCITA = os.path.join(RADICE, "include", "battaglia_grafica.h")
INCONTRI = ("pattuglia", "imboscata", "duello", "rito", "guerrieri", "fornace", "infiltrato")
# Gli incontri che riusano lo sfondo di un altro (nessun tile in piu'): la guardia della fornace al Teatro Romano,
# appena fuori dalle mura, ha le mura della Pattuglia; l'infiltrato sotto le Logge, in citta', la piazza del
# Palazzo dei Consoli del Duello. I Guerrieri della Roccia (B-03) hanno la gola del Bottaccione.
SFONDO_DI = {5: 0, 6: 2}
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


# --- le figure: in tools/sagome_battaglia.py (pezzo SAG) -------------------------------------------
# I Santi e i nemici di prima (forme piatte, due pose) sono stati ridisegnati con lo scheletro della
# Guida (scelta 11), l'ombreggiatura con la luce da sinistra e sette pose; qui resta la freccia.


def freccia(azione):
    """Il cursore del bersaglio, 16x16: una freccia d'oro che punta in giu'; nella seconda posa e'
    due pixel piu' in basso, cosi' alternando le pose dondola."""
    t = Tela(16, 16)
    y0 = 3 if azione else 1
    t.trapezio(8, y0 + 5, y0 + 11, 10, 1, ORO)
    t.rett(6, y0, 4, 6, ORO)
    t.rett(7, y0 + 1, 1, 6, BIANCO)
    return t.contorno()


SANTI, NEMICI = SB.SANTI, SB.NEMICI
ALTRI = (("FRECCIA", freccia),)


# --- gli sfondi ------------------------------------------------------------------------------------
def sfondo(incontro):
    """Lo sfondo 256x256 (si vedono i primi 240x160): cielo, profilo lontano, suolo."""
    incontro = SFONDO_DI.get(incontro, incontro)
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
    elif incontro == 4:
        # la gola del Bottaccione sotto l'arco: le due pareti di scaglia a fasce, rossa e bianca, che lasciano un
        # filo di cielo; la striscia nera del limite K-Pg che corre da una parete all'altra; l'edera
        fasce = (13, 13, 8, 14, 14, 14, 9, 9, 7, 13, 8, 8)    # strati di spessore diverso, 4 righe l'uno
        for x in range(256):
            colonna = x // 8                        # il bordo delle pareti a gradini di un tile
            cielo = max(0, 30 - 3 * abs(colonna - 16) + (colonna * 5) % 3 * 2)
            for y in range(cielo, orizzonte):
                t.punto(x, y, fasce[(y // 4) % len(fasce)])
        t.rett(0, 50, 256, 3, 0)                    # la striscia nera
        for y in range(36, orizzonte, 6):           # le fratture della roccia, a tile
            for x in range(4 + (y // 6) % 2 * 8, 256, 16):
                t.rett(x, y, 1, 3, 6)
        for k in range(9):                          # l'edera sulle pareti
            cx, cy = (k * 61 + 12) % 256, 58 + (k * 23) % 14
            t.ellisse(cx, cy, 5, 4, 10)
            t.ellisse(cx + 2, cy - 1, 2, 2, 11)
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
            if incontro in (1, 4):
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
def tile_di(px):
    """I tile 8x8 di una griglia di indici, riga per riga di tile (l'ordine degli sprite)."""
    lato = len(px)
    return [[px[ty * 8 + y][tx * 8:tx * 8 + 8] for y in range(8)] for ty in range(lato // 8) for tx in range(lato // 8)]


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
    # le sagome (pezzo SAG, tools/sagome_battaglia.py): ogni figura con la sua palette e le sue pose
    out += [f"inline constexpr int POSE_PER_FIGURA = {len(SB.POSE)};", ""]
    for gruppo, nemico in ((SB.SANTI, False), (SB.NEMICI, True)):
        for nome, pittore in gruppo:
            pose = SB.pose_di(pittore, nemico)
            lato = len(pose[0][1])
            pal = pose[0][0]
            tile_posa = (lato // 8) ** 2
            parole_tile = [parola for _, px in pose for t_ in tile_di(px) for parola in parole(t_)]
            out += [f"inline constexpr uint16_t PALETTE_{nome}[16] = {{",
                    blocchi([colore(r) for r in pal], 8, lambda v: f"0x{v:04X}"), "};",
                    f"inline constexpr int LATO_{nome} = {lato};",
                    f"inline constexpr int TILE_PER_POSA_{nome} = {tile_posa};",
                    f"inline constexpr bn::tile SPRITE_{nome}[{len(SB.POSE) * tile_posa}] = {{"]
            out += ["    { { " + ", ".join(f"0x{v:08X}" for v in parole_tile[k:k + 8]) + " } },"
                    for k in range(0, len(parole_tile), 8)]
            out += ["};", ""]
    # gli effetti: 32x32, FOTOGRAMMI_EFFETTO ciascuno, nell'ordine di animazione::Effetto
    fot = SB.effetti()
    parole_tile = [parola for px in fot for t_ in tile_di(px) for parola in parole(t_)]
    out += ["inline constexpr uint16_t PALETTE_EFFETTI[16] = {",
            blocchi([colore(r) for r in SB.PALETTE_EFFETTI], 8, lambda v: f"0x{v:04X}"), "};",
            f"inline constexpr int EFFETTI_FOTOGRAMMI = {len(fot)};",
            f"inline constexpr bn::tile SPRITE_EFFETTI[{len(fot) * 16}] = {{"]
    out += ["    { { " + ", ".join(f"0x{v:08X}" for v in parole_tile[k:k + 8]) + " } },"
            for k in range(0, len(parole_tile), 8)]
    out += ["};", ""]
    # i lampi, nell'ordine di animazione::Lampo (NESSUNO escluso)
    for nome, chiaro, scuro in SB.LAMPI:
        out += [f"inline constexpr uint16_t PALETTE_LAMPO_{nome}[16] = {{",
                blocchi([colore(r) for r in SB.palette_lampo(chiaro, scuro)], 8, lambda v: f"0x{v:04X}"), "};", ""]
    for nome, pittore in ALTRI:
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
