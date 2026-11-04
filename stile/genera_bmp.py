"""Genera i BMP indicizzati a 4bpp che Butano (grit) converte in sprite e sfondi, a partire dai
dati di stile/dati/. Solo libreria standard. Nessun pixel viene da una foto.

    python stile/genera_bmp.py               # scrive graphics/*.bmp e graphics/*.json
    python stile/genera_bmp.py --verifica    # esce con 1 se graphics/ non e' allineata ai dati

Uscite:
  ritratto_<nome>.bmp   sprite 32x96: le 3 espressioni (calmo, preoccupato, deciso) come
                        fotogrammi da 32x32, una palette da 16 per personaggio
  logo.bmp, logo_mono.bmp
                        regular_bg 256x256: il logo a x2 in alto e centrato come nella tavola
                        della scelta 12; il resto e' trasparente
  cornice_dialogo.bmp   regular_bg 256x256: riquadro di dialogo e cartiglio del nome nella
                        disposizione della scelta 9
  cornice_menu.bmp      regular_bg 256x256: riquadro del menu in alto a destra
  titolo_fondo.bmp      regular_bg 256x256: Gubbio al crepuscolo sotto il titolo (mockup 10 di menu/), con la
                        palette di notte (L5); le finestre che tremano hanno il colore segnaposto oro 1

L'indice 0 di ogni palette e' il trasparente (per Butano conta la posizione, non il colore).
I canali a 5 bit si scrivono come v << 3 | v >> 2: grit li riporta a 5 bit con >> 3, quindi
i colori in ROM sono esattamente le parole BGR555 di palette.json.
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stile as S

USCITA = os.path.join(os.path.dirname(S.RADICE), "graphics")
TRASPARENTE = 0x7C1F          # magenta: si vede subito se finisse a schermo per errore
LATO_BG = 256


def a8(v5):
    return (v5 << 3) | (v5 >> 2)


def bmp_4bpp(larghezza, altezza, indici, palette):
    """BMP 4bpp non compresso, righe dal basso, palette di 16 voci BGRA."""
    if len(palette) > 16:
        raise ValueError(f"{len(palette)} colori: un BMP 4bpp ne tiene 16")
    if larghezza % 8 or altezza % 8:
        raise ValueError("misure non multiple di 8")
    palette = list(palette) + [0] * (16 - len(palette))
    passo = ((larghezza * 4 + 31) // 32) * 4
    pixel = bytearray()
    for y in range(altezza - 1, -1, -1):
        riga = bytearray()
        for x in range(0, larghezza, 2):
            a, b = indici[y][x], indici[y][x + 1]
            if not (0 <= a < 16 and 0 <= b < 16):
                raise ValueError("indice fuori da 0..15")
            riga.append((a << 4) | b)
        riga += b"\0" * (passo - len(riga))
        pixel += riga
    tabella = b"".join(bytes((a8((c >> 10) & 31), a8((c >> 5) & 31), a8(c & 31), 0)) for c in palette)
    inizio = 14 + 40 + len(tabella)
    testa = b"BM" + struct.pack("<IHHI", inizio + len(pixel), 0, 0, inizio)
    info = struct.pack("<IiiHHIIiiII", 40, larghezza, altezza, 1, 4, 0, len(pixel), 2835, 2835, 16, 16)
    return testa + info + tabella + bytes(pixel)


def leggi_bmp_4bpp(dati):
    """Inverso di bmp_4bpp: (larghezza, altezza, indici, palette BGR555 a 16 voci)."""
    if dati[:2] != b"BM":
        raise ValueError("non e' un BMP")
    inizio = struct.unpack("<I", dati[10:14])[0]
    larghezza, altezza = struct.unpack("<ii", dati[18:26])
    bpp = struct.unpack("<H", dati[28:30])[0]
    if bpp != 4:
        raise ValueError(f"{bpp}bpp invece di 4")
    palette = []
    for i in range(16):
        b, g, r, _ = dati[54 + 4 * i:58 + 4 * i]
        palette.append((r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10))
    passo = ((larghezza * 4 + 31) // 32) * 4
    indici = []
    for y in range(altezza):
        off = inizio + (altezza - 1 - y) * passo
        riga = []
        for x in range(larghezza):
            byte = dati[off + x // 2]
            riga.append(byte >> 4 if x % 2 == 0 else byte & 15)
        indici.append(riga)
    return larghezza, altezza, indici, palette


def indicizza(colori):
    """Matrice di parole BGR555 (None = trasparente) -> (indici, palette con 0 trasparente)."""
    palette = [TRASPARENTE]
    posto = {}
    indici = []
    for riga in colori:
        r = []
        for c in riga:
            if c is None:
                r.append(0)
                continue
            if c not in posto:
                posto[c] = len(palette)
                palette.append(c)
            r.append(posto[c])
        indici.append(r)
    if len(palette) > 16:
        raise ValueError(f"{len(palette) - 1} colori opachi: un 4bpp ne tiene 15")
    return indici, palette


def vuota(w, h):
    return [[None] * w for _ in range(h)]


def ritratto(nome):
    rt, p = S.carica("ritratti"), S.carica("palette")
    tela = []
    for e in rt["espressioni"]:
        img, _ = S.componi_ritratto(rt, p, nome, e)
        tela += img
    return tela


def logo(monocromatico=False):
    lg, p = S.carica("logo"), S.carica("palette")
    m = S.disegna_logo(lg, lg["testo"], monocromatico)
    z = lg["scala_titolo"]
    tela = vuota(LATO_BG, LATO_BG)
    x0 = (240 - len(m[0]) * z) // 2
    y0 = 12
    for y, riga in enumerate(m):
        for x, ruolo in enumerate(riga):
            if ruolo == ".":
                continue
            c = S.colore(p, lg["colori"][ruolo])
            for dy in range(z):
                for dx in range(z):
                    tela[y0 + y * z + dy][x0 + x * z + dx] = c
    return tela


def _incolla_tile(tela, c, colori, x, y, nome, hf=False, vf=False):
    t = S.pixel_tile(c, nome, hf, vf)
    for yy in range(8):
        for xx in range(8):
            if t[yy][xx]:
                tela[y + yy][x + xx] = colori[t[yy][xx]]


def _incolla_riquadro(tela, c, colori, x0, y0, colonne, righe):
    for ty, riga in enumerate(S.componi_cornice(c, colonne, righe)):
        for tx, (nome, hf, vf) in enumerate(riga):
            _incolla_tile(tela, c, colori, x0 + tx * 8, y0 + ty * 8, nome, hf, vf)


def cornice(quale):
    c, p = S.carica("cornice"), S.carica("palette")
    colori = [None if rif is None else S.colore(p, rif) for rif in c["colori"]]
    d = c["disposizione"]
    tela = vuota(LATO_BG, LATO_BG)
    if quale == "menu":
        m = d["menu"]
        _incolla_riquadro(tela, c, colori, m["x"], m["y"], m["colonne"], m["righe"])
        return tela
    dia = d["dialogo"]
    _incolla_riquadro(tela, c, colori, dia["x"], dia["y"], dia["colonne"], dia["righe"])
    cn = d["cartiglio_nome"]
    sx, centro = c["regole"]["cartiglio"]
    colonne = cn["colonne"]
    for r in range(cn["righe"]):
        for k in range(colonne):
            nome, hf = (sx, False) if k == 0 else (sx, True) if k == colonne - 1 else (centro, False)
            _incolla_tile(tela, c, colori, cn["x"] + k * 8, cn["y"] + r * 8, nome, hf, r == 1)
    return tela


# --- Il fondo del titolo (mockup 10, menu/mockup_menu.py profilo_gubbio): Monte Ingino con la basilica e gli
# stradoni, le case su due file con le finestre accese, il Palazzo dei Consoli col campanile a vela, le mura.
# Luce dall'alto a sinistra (L1), niente contorno nero (P2), cielo a fasce piene (P6). Tutto procedurale.
MONTE = [(70, 160), (96, 140), (118, 126), (138, 116), (156, 108), (170, 102), (182, 98), (192, 96),
         (204, 96), (214, 98), (226, 102), (240, 104), (240, 160)]
STRADONI = [(206, 134), (170, 128), (208, 122), (176, 116), (206, 111), (184, 106), (204, 102), (194, 98)]
CASE_ALTE = [(100, 120, 12), (114, 116, 14), (130, 118, 12), (144, 112, 12), (158, 116, 14)]
CASE = [(36, 128, 18), (54, 124, 14), (68, 130, 20), (88, 126, 16), (104, 132, 18), (122, 128, 14),
        (136, 134, 20), (156, 130, 16), (172, 136, 18), (190, 132, 16), (206, 136, 18), (224, 130, 16)]


def _rett(tela, x0, y0, x1, y1, c):
    for y in range(max(0, y0), min(len(tela), y1 + 1)):
        for x in range(max(0, x0), min(len(tela[0]), x1 + 1)):
            tela[y][x] = c


def _punto(tela, x, y, c):
    if 0 <= y < len(tela) and 0 <= x < len(tela[0]):
        tela[y][x] = c


def _linea(tela, a, b, c):
    """Bresenham, estremi compresi."""
    (x0, y0), (x1, y1) = a, b
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    e = dx + dy
    while True:
        _punto(tela, x0, y0, c)
        if (x0, y0) == (x1, y1):
            return
        e2 = 2 * e
        if e2 >= dy:
            e += dy
            x0 += sx
        if e2 <= dx:
            e += dx
            y0 += sy


def _poligono(tela, punti, c):
    """Pieno a scansione sui centri dei pixel, piu' il contorno (come il poligono pieno di PIL)."""
    ys = [p[1] for p in punti]
    for y in range(min(ys), max(ys) + 1):
        xs = []
        for (xa, ya), (xb, yb) in zip(punti, punti[1:] + punti[:1]):
            if (ya <= y + 0.5) != (yb <= y + 0.5):
                xs.append(xa + (y + 0.5 - ya) * (xb - xa) / (yb - ya))
        xs.sort()
        for a, b in zip(xs[::2], xs[1::2]):
            _rett(tela, int(a + 0.5), y, int(b - 0.5), y, c)
    for a, b in zip(punti, punti[1:] + punti[:1]):
        _linea(tela, a, b, c)


def titolo_fondo():
    p = S.carica("palette")

    def n(rampa, tono):
        return S.colore(p, [rampa, tono], True)

    def g(rampa, tono):
        return S.colore(p, [rampa, tono])

    tela = vuota(LATO_BG, LATO_BG)
    _rett(tela, 0, 0, 239, 159, g("neutri", 0))
    _rett(tela, 0, 112, 239, 159, n("neutri", 0))
    _rett(tela, 0, 126, 239, 159, n("cielo e acqua", 0))
    _poligono(tela, MONTE, n("verde dei monti", 1))
    for (xa, ya), (xb, yb) in zip(MONTE, MONTE[1:]):
        if xb > xa and yb < ya:
            _linea(tela, (xa, ya), (xb, yb), n("verde dei monti", 3))
    for (xa, ya), (xb, yb) in zip(STRADONI, STRADONI[1:]):
        passi = max(abs(xb - xa), abs(yb - ya))
        for k in range(0, passi, 2):
            _punto(tela, round(xa + (xb - xa) * k / passi), round(ya + (yb - ya) * k / passi), n("verde dei monti", 3))
    _rett(tela, 186, 89, 199, 94, n("pietra calcarea", 3))
    _rett(tela, 186, 89, 187, 94, n("pietra calcarea", 4))
    _rett(tela, 185, 87, 200, 88, n("cotto e coppi", 3))
    _rett(tela, 196, 82, 198, 86, n("pietra calcarea", 3))
    _punto(tela, 197, 81, n("cotto e coppi", 3))
    for x, y, w in CASE_ALTE:
        _rett(tela, x, y, x + w - 1, 130, n("pietra calcarea", 0))
        _rett(tela, x, y, x + 1, 130, n("pietra calcarea", 1))
        _rett(tela, x - 1, y - 2, x + w, y - 1, n("cotto e coppi", 1))
    for i, (x, y, w) in enumerate(CASE):
        _rett(tela, x, y, x + w - 1, 147, n("pietra calcarea", 1))
        _rett(tela, x, y, x + 1, 147, n("pietra calcarea", 2))
        _rett(tela, x - 1, y - 2, x + w, y - 1, n("cotto e coppi", 2))
        if i % 3 != 1:
            # una finestra su quattro trema: ha il colore segnaposto oro 1, che il gioco fa passare da oro 2
            # a oro 1 insieme al lampeggio del cursore (src/titolo.cpp)
            luce = g("oro e bronzo", 1) if i % 4 == 0 else g("oro e bronzo", 2)
            _rett(tela, x + w // 2, y + 5, x + w // 2 + 1, y + 7, luce)
    _rett(tela, 6, 104, 33, 147, n("pietra calcarea", 3))
    _rett(tela, 6, 104, 8, 147, n("pietra calcarea", 4))
    for mx in range(6, 34, 4):
        _rett(tela, mx, 101, mx + 1, 103, n("pietra calcarea", 3))
    _rett(tela, 8, 86, 13, 100, n("pietra calcarea", 3))
    _rett(tela, 8, 86, 8, 100, n("pietra calcarea", 4))
    _rett(tela, 10, 89, 11, 93, n("neutri", 0))
    _rett(tela, 8, 84, 13, 85, n("cotto e coppi", 3))
    for fx in (13, 20, 27):
        _rett(tela, fx, 112, fx + 2, 117, g("oro e bronzo", 2))
        _punto(tela, fx + 1, 111, g("oro e bronzo", 2))
    _rett(tela, 12, 136, 27, 147, n("pietra calcarea", 1))
    _rett(tela, 0, 146, 239, 159, n("pietra calcarea", 0))
    for mx in range(0, 240, 6):
        _rett(tela, mx, 143, mx + 2, 145, n("pietra calcarea", 0))
    return tela


def immagini():
    """nome -> (matrice di colori, meta per Butano)."""
    out = {}
    for nome in S.carica("ritratti")["personaggi"]:
        out["ritratto_" + nome.lower()] = (ritratto(nome), {"type": "sprite", "height": 32, "bpp_mode": "bpp_4"})
    out["logo"] = (logo(), {"type": "regular_bg", "bpp_mode": "bpp_4_auto"})
    out["logo_mono"] = (logo(True), {"type": "regular_bg", "bpp_mode": "bpp_4_auto"})
    out["cornice_dialogo"] = (cornice("dialogo"), {"type": "regular_bg", "bpp_mode": "bpp_4_auto"})
    out["cornice_menu"] = (cornice("menu"), {"type": "regular_bg", "bpp_mode": "bpp_4_auto"})
    out["titolo_fondo"] = (titolo_fondo(), {"type": "regular_bg", "bpp_mode": "bpp_4_auto"})
    return out


def file_attesi():
    """nome file -> contenuto in byte, per ogni BMP e JSON generato."""
    import json
    out = {}
    for nome, (colori, meta) in immagini().items():
        indici, palette = indicizza(colori)
        out[nome + ".bmp"] = bmp_4bpp(len(colori[0]), len(colori), indici, palette)
        out[nome + ".json"] = (json.dumps(meta, indent=4) + "\n").encode("utf-8")
    return out


def main():
    verifica = "--verifica" in sys.argv
    diversi = []
    os.makedirs(USCITA, exist_ok=True)
    for nome, contenuto in file_attesi().items():
        percorso = os.path.join(USCITA, nome)
        if verifica:
            attuale = open(percorso, "rb").read() if os.path.exists(percorso) else b""
            if attuale != contenuto:
                diversi.append(nome)
        else:
            with open(percorso, "wb") as f:
                f.write(contenuto)
    if diversi:
        print("graphics/ non allineata ai dati:", ", ".join(diversi), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
