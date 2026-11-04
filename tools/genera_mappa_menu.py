#!/usr/bin/env python3
"""La mappa della citta' nel menu di pausa (MMA, menu/PROPOSTA.md sez. 3.3; mockup approvato menu/mockup/03_mappa.png,
disegnato da menu/mockup_menu.py: disegna_mappa). Legge mondo/mappa_menu.json (lo schema) e mondo/grafo.json (le
strade e le quote) e scrive:

- include/stile/mappa_menu.h: la palette, i 28x11 tile 4bpp del fondo (prati, monte, mura, Camignano, stradoni, rosa
  dei venti), le aree come nodi, le strade come elenchi di pixel gia' ottolineari, le porte. Strade, porte e nodi li
  disegna il gioco sopra il fondo, perche' dipendono dalle aree viste (src/menu_mappa.cpp);
- testi/mappa_menu.testi: per ogni area la riga della scheda e la quota sopra Piazza Quaranta Martiri.

    python3 tools/genera_mappa_menu.py                 # controlla che i due file siano aggiornati (esce con 1 se no)
    python3 tools/genera_mappa_menu.py --scrivi        # li riscrive
    python3 tools/genera_mappa_menu.py --png FILE      # disegna anche l'anteprima (tutte le aree viste), x3
"""
import json
import os
import sys


RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RADICE, "stile"))
import stile as S  # noqa: E402

DATI = os.path.join(RADICE, "mondo", "mappa_menu.json")
GRAFO = os.path.join(RADICE, "mondo", "grafo.json")
HEADER = os.path.join(RADICE, "include", "stile", "mappa_menu.h")
TESTI = os.path.join(RADICE, "testi", "mappa_menu.testi")

# Il riquadro della mappa dentro la cornice della pagina: tutto l'interno di una cornice 30x13 (8 px di bordo).
X0, Y0, W, H = 8, 8, 224, 88
COLONNE, RIGHE = W // 8, H // 8

# I colori della mappa, tutti della Guida (STANDARD C1); lo 0 e' trasparente.
COLORI = [
    ("k", ("neutri", 0)), ("prato", ("verde dei monti", 4)), ("monte", ("verde dei monti", 3)),
    ("bosco", ("verde dei monti", 2)), ("pietra", ("pietra calcarea", 4)), ("mura", ("pietra calcarea", 1)),
    ("acqua", ("cielo e acqua", 2)), ("salita", ("cotto e coppi", 4)), ("strada", ("cotto e coppi", 2)),
    ("vista", ("oro e bronzo", 3)), ("nebbia", ("neutri", 2)), ("luce", ("neutri", 4)),
    ("porta", ("pietra calcarea", 2)),
]
INDICE = {nome: i + 1 for i, (nome, _) in enumerate(COLORI)}

# Le icone disegnate nel fondo o dal gioco, a lettere come nel mockup (k scuro, S e s pietra, O oro, w luce).
LETTERE = {"k": "k", "S": "porta", "s": "pietra", "O": "vista", "w": "luce"}
PORTA = [".k.k.k..", ".kkkkk..", ".kSsSk..", ".kSSSk..", ".kSkSk..", ".kk.kk..", ".k...k..", "........"]
# la freccia punta alla N, cioe' a destra (il nord, nella mappa ruotata come il gioco)
ROSA = ["....k.....k...k.", "...kOk....kk..k.", "kOOOOkkk..k.k.k.", "kwwwwOOk..k..kk.", "kOOOOkkk..k...k.",
        "...kOk..........", "....k..........."]


class ErroreMappa(Exception):
    pass


def M(p):
    """Dallo schema 240x120 ai pixel del riquadro della mappa (0..223, 0..87)."""
    return (p[0] * W // 240, p[1] * H // 120)


def segno(v):
    return (v > 0) - (v < 0)


def ottolineare(punti):
    """STANDARD_GRAFICO P7: ogni tratto diventa un pezzo a 45 gradi e uno dritto, con la piega lontana dai nodi."""
    out = [punti[0]]
    for (xa, ya), (xb, yb) in zip(punti, punti[1:]):
        dx, dy = xb - xa, yb - ya
        m = min(abs(dx), abs(dy))
        rx, ry = dx - segno(dx) * m, dy - segno(dy) * m
        h = (rx // 2, ry // 2)
        for q in ((xa + h[0], ya + h[1]), (xa + h[0] + segno(dx) * m, ya + h[1] + segno(dy) * m), (xb, yb)):
            if q != out[-1]:
                out.append(q)
    return out


def pixel_di(punti):
    out = []
    for (xa, ya), (xb, yb) in zip(punti, punti[1:]):
        n = max(abs(xb - xa), abs(yb - ya))
        for k in range(n):
            out.append((xa + segno(xb - xa) * k, ya + segno(yb - ya) * k))
    out.append(punti[-1])
    return out


def linea(img, punti, colore, spessa=False):
    px = pixel_di(ottolineare(punti))
    for k, (x, y) in enumerate(px):
        if 0 <= x < W and 0 <= y < H:
            img.putpixel((x, y), colore)
        if spessa:
            vx = px[min(k + 1, len(px) - 1)][0] == x and px[max(k - 1, 0)][0] == x
            q = (x + 1, y) if vx else (x, y + 1)
            if 0 <= q[0] < W and 0 <= q[1] < H:
                img.putpixel(q, colore)


def icona(img, x, y, disegno):
    for yy, r in enumerate(disegno):
        for xx, ch in enumerate(r):
            if ch != "." and 0 <= x + xx < W and 0 <= y + yy < H:
                img.putpixel((x + xx, y + yy), INDICE[LETTERE[ch]])


def carica():
    with open(DATI, encoding="utf-8") as f:
        d = json.load(f)
    with open(GRAFO, encoding="utf-8") as f:
        g = json.load(f)
    aree = {a["id"]: a for a in g["aree"]}
    for nodo in d["nodi"]:
        if nodo not in aree:
            raise ErroreMappa("nodo %s: non e' un'area di mondo/grafo.json" % nodo)
        if nodo not in d["righe"]:
            raise ErroreMappa("nodo %s: manca la riga della scheda" % nodo)
    archi = [(a["da"], a["a"]) for a in g["archi"] if a["da"] in d["nodi"] and a["a"] in d["nodi"]]
    return d, aree, archi


def fondo(d):
    """Il fondo della mappa, in indici della palette: quello che non cambia con le aree viste."""
    from PIL import Image, ImageDraw   # qui e non in cima: i test leggono lo schema anche senza Pillow (CI)
    img = Image.new("P", (W, H), INDICE["prato"])
    dr = ImageDraw.Draw(img)
    dr.polygon(ottolineare([M(p) for p in d["monte"]]), fill=INDICE["monte"])
    for y in range(H):
        for x in range(W):
            # il tratteggio del monte, come nel mockup (in coordinate dello schermo)
            if img.getpixel((x, y)) == INDICE["monte"] and (x + X0 + y + Y0) % 6 == 0:
                img.putpixel((x, y), INDICE["bosco"])
    mura = [M(p) for p in d["mura"] + [d["mura"][0]]]
    dr.polygon(ottolineare(mura), fill=INDICE["pietra"])
    linea(img, mura, INDICE["mura"], spessa=True)
    linea(img, [M(p) for p in d["camignano"]], INDICE["acqua"], spessa=True)
    linea(img, [M(p) for p in d["stradoni"]], INDICE["salita"])
    linea(img, [M(p) for p in d["sentiero"]], INDICE["salita"])
    icona(img, W - 18, H - 11, ROSA)
    return img


def disegna_sopra(img, d, archi, viste):
    """Quello che il gioco disegna sopra il fondo (src/menu_mappa.cpp fa lo stesso): strade, porte, nodi."""
    nodi = {k: M(p) for k, p in d["nodi"].items()}
    for a, b in archi:
        piena = a in viste and b in viste
        for k, (x, y) in enumerate(pixel_di(ottolineare([nodi[a], nodi[b]]))):
            if piena or k % 3 == 0:
                img.putpixel((x, y), INDICE["strada"])
    for p in d["porte"].values():
        x, y = M(p)
        icona(img, x - 3, y - 4, PORTA)
    for k, (x, y) in nodi.items():
        for yy in range(-3, 4):
            for xx in range(-3, 4):
                bordo = abs(xx) == 3 or abs(yy) == 3
                img.putpixel((x + xx, y + yy), INDICE["k"] if bordo else INDICE["vista" if k in viste else "nebbia"])
        if k in viste:
            img.putpixel((x - 2, y - 2), INDICE["luce"])


def tile_di(img, tx, ty):
    parole = []
    for r in range(8):
        v = 0
        for p in range(8):
            v |= img.getpixel((tx * 8 + p, ty * 8 + r)) << (4 * p)
        parole.append(v)
    return parole


def quota(area):
    a, b = area["quota_m"]
    f = lambda v: "%+d m" % v if v else "0 m"  # noqa: E731
    return f(a) if a == b else "%+d a %+d m" % (a, b)


def header(d, archi):
    P = S.carica("palette")
    pal = [0] + [S.colore(P, list(rif)) for _, rif in COLORI] + [0] * (15 - len(COLORI))
    img = fondo(d)
    nodi = list(d["nodi"])
    pos = {k: M(p) for k, p in d["nodi"].items()}
    pixel, righe_archi = [], []
    for a, b in archi:
        px = pixel_di(ottolineare([pos[a], pos[b]]))
        righe_archi.append("    { %d, %d, %d, %d },  // %s - %s" % (nodi.index(a), nodi.index(b), len(pixel) // 2, len(px), a, b))
        for x, y in px:
            pixel += [x, y]
    out = ["// GENERATO da tools/genera_mappa_menu.py da mondo/mappa_menu.json e mondo/grafo.json. Non modificare a mano.",
           "#ifndef GUBBIO_STILE_MAPPA_MENU_H", "#define GUBBIO_STILE_MAPPA_MENU_H", "", "#include <cstdint>", "",
           '#include "mondo.h"', '#include "testi.h"', "", "namespace gubbio::stile", "{", "",
           "// I colori della mappa, tutti della Guida (0 trasparente).",
           "inline constexpr uint16_t MAPPA_MENU_PALETTE[16] = {",
           "    " + ", ".join("0x%04X" % c for c in pal), "};", ""]
    for nome, i in INDICE.items():
        out.append("inline constexpr int MAPPA_%s = %d;" % (nome.upper(), i))
    out += ["", "// Il riquadro della mappa: l'angolo in alto a sinistra sullo schermo, i tile del fondo (riga per riga).",
            "inline constexpr int MAPPA_X0 = %d;" % X0, "inline constexpr int MAPPA_Y0 = %d;" % Y0,
            "inline constexpr int MAPPA_COLONNE = %d;" % COLONNE, "inline constexpr int MAPPA_RIGHE = %d;" % RIGHE,
            "inline constexpr uint32_t MAPPA_MENU_TILE[MAPPA_COLONNE * MAPPA_RIGHE * 8] = {"]
    for ty in range(RIGHE):
        for tx in range(COLONNE):
            out.append("    " + ", ".join("0x%08X" % w for w in tile_di(img, tx, ty)) + ",")
    out += ["};", "",
            "// Un'area sulla mappa: il centro del nodo in pixel del riquadro, la riga della scheda e la quota.",
            "struct NodoMappa", "{", "    mondo::AreaId area;", "    uint8_t x;", "    uint8_t y;",
            "    testi::TestoId riga;", "    testi::TestoId quota;",
            "    testi::TestoId libro[2];       // la pagina del libro di Gubbio (testi/libro.testi, MLIB)", "};", "",
            "inline constexpr int NODI_MAPPA = %d;" % len(nodi), "inline constexpr NodoMappa NODO_MAPPA[NODI_MAPPA] = {"]
    for k in nodi:
        x, y = pos[k]
        out.append("    { mondo::AreaId::%s, %d, %d, testi::TestoId::MAPPA_RIGA_%s, testi::TestoId::MAPPA_QUOTA_%s,\n"
                   "      { testi::TestoId::LIBRO_%s_1, testi::TestoId::LIBRO_%s_2 } }," % (k, x, y, k, k, k, k))
    out += ["};", "", "// Una strada fra due nodi (indici in NODO_MAPPA): i suoi pixel in ARCO_PIXEL, a coppie x, y.",
            "struct ArcoMappa", "{", "    uint8_t a;", "    uint8_t b;", "    uint16_t primo;", "    uint16_t quanti;", "};", "",
            "inline constexpr int ARCHI_MAPPA = %d;" % len(archi), "inline constexpr ArcoMappa ARCO_MAPPA[ARCHI_MAPPA] = {"]
    out += righe_archi
    out += ["};", "", "inline constexpr int ARCO_PIXEL_N = %d;" % (len(pixel) // 2),
            "inline constexpr uint8_t ARCO_PIXEL[ARCO_PIXEL_N * 2] = {"]
    for i in range(0, len(pixel), 24):
        out.append("    " + ", ".join(str(v) for v in pixel[i:i + 24]) + ",")
    out += ["};", "", "// Le porte delle mura: l'angolo in alto a sinistra dell'icona, in pixel del riquadro.",
            "struct PortaMappa", "{", "    int16_t x;", "    int16_t y;", "};", "",
            "inline constexpr int PORTE_MAPPA = %d;" % len(d["porte"]), "inline constexpr PortaMappa PORTA_MAPPA[PORTE_MAPPA] = {"]
    for nome, p in d["porte"].items():
        x, y = M(p)
        out.append("    { %d, %d },  // %s" % (x - 3, y - 4, nome))
    out += ["};", "", "// L'icona della porta, una riga per parola: il pixel p nei bit 4p..4p+3 (0 trasparente).",
            "inline constexpr uint32_t PORTA_MAPPA_TILE[8] = {"]
    righe_porta = []
    for r in PORTA:
        v = 0
        for p, ch in enumerate(r):
            if ch != ".":
                v |= INDICE[LETTERE[ch]] << (4 * p)
        righe_porta.append("0x%08X" % v)
    out += ["    " + ", ".join(righe_porta), "};", "", "}", "", "#endif", ""]
    return "\n".join(out)


def testi(d, aree):
    out = ["# GENERATO da tools/genera_mappa_menu.py da mondo/mappa_menu.json e mondo/grafo.json. Non modificare a mano.",
           "# La scheda di ogni area sotto la mappa della pausa (MMA): la riga e la quota sopra Piazza Quaranta Martiri."]
    for k in d["nodi"]:
        out.append("%-25s | AREA    | %s" % ("MAPPA_RIGA_" + k, d["righe"][k]))
        out.append("%-25s | HUD     | %s" % ("MAPPA_QUOTA_" + k, quota(aree[k])))
    return "\n".join(out) + "\n"


def anteprima(d, archi, percorso):
    from PIL import Image
    P = S.carica("palette")
    img = fondo(d)
    disegna_sopra(img, d, archi, set(d["nodi"]))
    rgb = [(0, 0, 0)] + [S.rgb_di(S.colore(P, list(rif))) for _, rif in COLORI]
    flat = [c for t in rgb for c in t] + [0] * (768 - 3 * len(rgb))
    img.putpalette(flat)
    img.convert("RGB").resize((W * 3, H * 3), Image.NEAREST).save(percorso)


def main(argv):
    d, aree, archi = carica()
    h, t = header(d, archi), testi(d, aree)
    if "--png" in argv:
        anteprima(d, archi, argv[argv.index("--png") + 1])
    if "--scrivi" in argv:
        for percorso, testo in ((HEADER, h), (TESTI, t)):
            with open(percorso, "w", encoding="utf-8", newline="\n") as f:
                f.write(testo)
            print("[mappa] scritto", os.path.relpath(percorso, RADICE))
        return 0
    for percorso, testo in ((HEADER, h), (TESTI, t)):
        with open(percorso, encoding="utf-8") as f:
            if f.read() != testo:
                print("[mappa] %s non e' aggiornato: python3 tools/genera_mappa_menu.py --scrivi" %
                      os.path.relpath(percorso, RADICE))
                return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
