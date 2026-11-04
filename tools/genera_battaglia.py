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
import sagome_battaglia as SB
import fondali_battaglia as FB  # noqa: E402

USCITA = os.path.join(RADICE, "include", "battaglia_grafica.h")
INCONTRI = ("pattuglia", "imboscata", "duello", "rito", "guerrieri", "fornace", "infiltrato")
# Gli incontri che riusano lo sfondo di un altro (nessun tile in piu'): la guardia della fornace al Teatro Romano,
# appena fuori dalle mura, ha le mura della Pattuglia; l'infiltrato sotto le Logge, in citta', la piazza del
# Palazzo dei Consoli del Duello. I Guerrieri della Roccia (B-03) hanno la gola del Bottaccione.
SFONDO_DI = {5: 0, 6: 2}
PANNELLO_Y = 104      # da qui in giu' il pannello dei comandi
TILE_SFONDO_MAX = 480  # i tile di un fondale nella VRAM degli sfondi, con quelli del testo

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
# --- i fondali: in tools/fondali_battaglia.py (standard grafico, giro 2 del loop grafico) -------------
FONDALE_DI = tuple(SFONDO_DI.get(i, i) for i in range(len(INCONTRI)))     # incontro -> fondale (0-4)


def sfondo(incontro):
    """La griglia 256x256 di indici dello sfondo di un incontro (si vedono i primi 240x160); la palette e'
    quella del suo fondale (palette_sfondo)."""
    t = Tela(256, 256)
    t.px = FB.fondale(SFONDO_DI.get(incontro, incontro))[0]
    return t


def palette_sfondo(incontro):
    return FB.fondale(SFONDO_DI.get(incontro, incontro))[1]


def tile_e_mappe():
    """Per ogni fondale i suoi tile (senza doppioni) e la sua mappa 32x32: [(tile, mappa)]."""
    out = []
    for k in range(len(FB.PITTORI)):
        px = FB.fondale(k)[0]
        tile, mappa = {}, []
        for ty in range(32):
            for tx in range(32):
                chiave = tuple(tuple(px[ty * 8 + y][tx * 8:tx * 8 + 8]) for y in range(8))
                mappa.append(tile.setdefault(chiave, len(tile)))
        out.append((list(tile), mappa))
    return out


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
    fondali = tile_e_mappe()
    for k, (tile, _) in enumerate(fondali):
        if len(tile) > TILE_SFONDO_MAX:
            raise SystemExit(f"[battaglia] fondale {k}: {len(tile)} tile, il massimo e' {TILE_SFONDO_MAX}")
    out = ["// GENERATO da tools/genera_battaglia.py: la grafica procedurale della battaglia.",
           "// Non modificare a mano.",
           "#ifndef GUBBIO_BATTAGLIA_GRAFICA_H", "#define GUBBIO_BATTAGLIA_GRAFICA_H", "",
           "#include <cstdint>", "", "#include \"bn_tile.h\"", "",
           "namespace gubbio::battaglia::grafica", "{", ""]
    for nome, pal in (("SANTI", PALETTE_SANTI), ("NEMICI", PALETTE_NEMICI)):
        out += [f"inline constexpr uint16_t PALETTE_{nome}[16] = {{",
                blocchi([colore(r) for r in pal], 8, lambda v: f"0x{v:04X}"), "};", ""]
    # i fondali (tools/fondali_battaglia.py): per ognuno la palette, i tile e la mappa; l'incontro sceglie il suo
    out += [f"inline constexpr int FONDALI = {len(fondali)};",
            f"inline constexpr int FONDALE_DI[{len(INCONTRI)}] = {{ " + ", ".join(map(str, FONDALE_DI)) + " };",
            "inline constexpr uint16_t PALETTE_SFONDO[FONDALI][16] = {"]
    for k in range(len(fondali)):
        out += ["    {", blocchi([colore(r) for r in FB.fondale(k)[1]], 8, lambda v: f"0x{v:04X}").replace("    ", "        ", 1)
                .replace("\n    ", "\n        "), "    },"]
    out += ["};", ""]
    for k, (tile, _) in enumerate(fondali):
        out += [f"inline constexpr bn::tile TILE_SFONDO_{k}[{len(tile)}] = {{"]
        out += ["    { { " + ", ".join(f"0x{v:08X}" for v in parole(t)) + " } }," for t in tile]
        out += ["};", ""]
    out += ["inline constexpr const bn::tile* TILE_SFONDO[FONDALI] = { " +
            ", ".join(f"TILE_SFONDO_{k}" for k in range(len(fondali))) + " };",
            "inline constexpr int TILE_SFONDO_CONTEGGIO[FONDALI] = { " +
            ", ".join(str(len(t)) for t, _ in fondali) + " };", "",
            "inline constexpr uint16_t SFONDO[FONDALI][1024] = {"]
    for _, m in fondali:
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
