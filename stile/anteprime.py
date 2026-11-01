"""Tavola di controllo dei dati di stile: tutto quello che sta in stile/dati/, disegnato.
Serve agli occhi, non ai test (che non usano PIL). Richiede Pillow.

    python stile/anteprime.py anteprima.png
"""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stile as S

P = S.carica("palette")
F = S.carica("font")
C = S.carica("cornice")
R = S.carica("ritratti")
PS = S.carica("pose")
L = S.carica("logo")


def rgb(rif, notte=False):
    return S.rgb_di(S.colore(P, rif, notte))


def testo(img, x, y, t, col):
    t = S.normalizza(F, t)
    for ch in t:
        g = F["glifi"][ch]
        for r, riga in enumerate(g):
            for k, v in enumerate(riga):
                if v == "#":
                    img.putpixel((x + k, y + r), col)
        x += len(g[0]) + F["spaziatura"]
    return x


def cornice(img, x, y, colonne, righe):
    pal = [None if c is None else rgb(c) for c in C["colori"]]
    px = S.disegna_mappa(C, S.componi_cornice(C, colonne, righe))
    for yy, riga in enumerate(px):
        for xx, v in enumerate(riga):
            if v:
                img.putpixel((x + xx, y + yy), pal[v])


def cartiglio(img, x, y, colonne):
    pal = [None if c is None else rgb(c) for c in C["colori"]]
    sx, centro = C["regole"]["cartiglio"]
    for riga, vf in ((0, False), (1, True)):
        for k in range(colonne):
            nome, hf = (sx, False) if k == 0 else (sx, True) if k == colonne - 1 else (centro, False)
            t = S.pixel_tile(C, nome, hf, vf)
            for yy in range(8):
                for xx in range(8):
                    if t[yy][xx]:
                        img.putpixel((x + k * 8 + xx, y + riga * 8 + yy), pal[t[yy][xx]])


def ritratto(img, x, y, nome, e):
    px, _ = S.componi_ritratto(R, P, nome, e)
    for yy, riga in enumerate(px):
        for xx, c in enumerate(riga):
            if c is not None:
                img.putpixel((x + xx, y + yy), S.rgb_di(c))


def schermo_dialogo():
    img = Image.new("RGB", (240, 160), rgb(["pietra calcarea", 2]))
    d = C["disposizione"]
    m = d["menu"]
    cornice(img, m["x"], m["y"], m["colonne"], m["righe"])
    for i, voce in enumerate(("Attacca", "Oggetti", "Attendi")):
        testo(img, m["x"] + 16, m["y"] + 7 + i * m["passo_voci"], voce, rgb(C["colori"][1]))
    t = S.pixel_tile(C, "cursore")
    for yy in range(8):
        for xx in range(8):
            if t[yy][xx]:
                img.putpixel((m["x"] + 8 + xx, m["y"] + 8 + yy), rgb(C["colori"][t[yy][xx]]))
    dia = d["dialogo"]
    cornice(img, dia["x"], dia["y"], dia["colonne"], dia["righe"])
    ritratto(img, dia["ritratto"][0], dia["ritratto"][1] + 1, "Ubaldo", "preoccupato")
    cn = d["cartiglio_nome"]
    cartiglio(img, cn["x"], cn["y"] - 4, 5)
    testo(img, cn["x"] + 6, cn["y"] + 1, "Ubaldo", rgb(C["colori"][2]))
    frase = "Undici città marciano su Gubbio. Non abbiate paura: chi può, resti al suo posto."
    for i, r in enumerate(S.a_capo(F, frase, 240 - 52 - 10)[:3]):
        testo(img, 50, dia["y"] + 9 + i * 10, r, rgb(C["colori"][1]))
    return img


def tavola(percorso):
    Z = 3
    out = Image.new("RGB", (240 * Z * 2 + 48, 1500), (245, 243, 238))
    dr = ImageDraw.Draw(out)
    out.paste(schermo_dialogo().resize((240 * Z, 160 * Z), Image.NEAREST), (16, 16))
    # palette giorno / notte
    x0, y0 = 240 * Z + 32, 16
    for i, r in enumerate(P["rampe"]):
        for j, (g, n) in enumerate(zip(r["giorno"], r["notte"])):
            dr.rectangle([x0 + j * 30, y0 + i * 32, x0 + j * 30 + 27, y0 + i * 32 + 27], fill=S.rgb_di(g))
            dr.rectangle([x0 + 200 + j * 30, y0 + i * 32, x0 + 200 + j * 30 + 27, y0 + i * 32 + 27], fill=S.rgb_di(n))
    # font intero
    fimg = Image.new("RGB", (240, 64), rgb(["neutri", 4]))
    righe = ["ABCDEFGHIJKLMNOPQRSTUVWXYZ ÀÈÉÌÒÙ", "abcdefghijklmnopqrstuvwxyz àèéìòù",
             "0123456789 .,;:!?'\"«»-—()/%+*… ’", "È l'anno 1151. «Chi può, resti al suo posto.»"]
    for i, r in enumerate(righe):
        testo(fimg, 4, 3 + i * 15, r, rgb(["legno e cuoio", 0]))
    out.paste(fimg.resize((240 * Z, 64 * Z), Image.NEAREST), (16, 160 * Z + 32))
    # ritratti 3x3
    rimg = Image.new("RGB", (3 * 36, 3 * 36), rgb(["cielo e acqua", 3]))
    for j, n in enumerate(R["personaggi"]):
        for i, e in enumerate(R["espressioni"]):
            ritratto(rimg, 2 + i * 36, 2 + j * 36, n, e)
    out.paste(rimg.resize((108 * 4, 108 * 4), Image.NEAREST), (x0, 330))
    # pose: scheletri
    y = 160 * Z + 64 * Z + 56
    pimg = Image.new("RGB", (240, 110), rgb(["pietra calcarea", 3]))
    pd = ImageDraw.Draw(pimg)
    col = rgb(["legno e cuoio", 0])
    k = 0
    for nome in ("camminata", "attacco"):
        for d in ("destra", "giu"):
            for f in PS["animazioni"][nome]["fotogrammi"]:
                g = f["giunti"][d]
                ox, oy = 4 + (k % 12) * 19, 4 + (k // 12) * 36
                pd.rectangle([ox, oy, ox + 15, oy + 31], outline=rgb(["pietra calcarea", 1]))
                for a, b in (("testa", "collo"), ("collo", "bacino"), ("collo", "mano_a"), ("collo", "mano_b"),
                             ("bacino", "piede_a"), ("bacino", "piede_b")):
                    pd.line([(ox + g[a][0], oy + g[a][1]), (ox + g[b][0], oy + g[b][1])], fill=col)
                pd.ellipse([ox + g["testa"][0] - 2, oy + g["testa"][1] - 3, ox + g["testa"][0] + 2,
                            oy + g["testa"][1] + 2], outline=col)
                k += 1
    out.paste(pimg.resize((240 * Z, 110 * Z), Image.NEAREST), (16, y))
    # logo e versione monocromatica
    ruoli = {"luce": rgb(L["colori"]["luce"]), "alto": rgb(L["colori"]["alto"]),
             "basso": rgb(L["colori"]["basso"]), "contorno": rgb(L["colori"]["contorno"]),
             "pieno": rgb(L["colori"]["pieno"])}
    for i, mono in enumerate((False, True)):
        m = S.disegna_logo(L, L["testo"], mono)
        limg = Image.new("RGB", (len(m[0]), len(m)), rgb(["cielo e acqua", 1]))
        for yy, riga in enumerate(m):
            for xx, v in enumerate(riga):
                if v != ".":
                    limg.putpixel((xx, yy), ruoli[v])
        out.paste(limg.resize((limg.width * 6, limg.height * 6), Image.NEAREST), (x0, 800 + i * 100))
    out = out.crop((0, 0, out.width, y + 110 * Z + 16))
    out.save(percorso)


if __name__ == "__main__":
    tavola(sys.argv[1])
