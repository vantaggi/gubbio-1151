"""Mockup statici (e due GIF) delle cutscene proposte. Solo per discuterne: niente di questo va nel gioco.
Usa la palette, il font, la cornice e i ritratti veri di stile/dati/. Tutto procedurale, nessuna foto.

    python stile/mockup_cutscene.py <cartella_uscita>
"""
import math
import os
import random
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stile as S
import anteprime as A
import json

W, H = 240, 160
BANDA = 24          # bande cinema sopra e sotto: resta un quadro 240x112 (circa 2,14:1)
Z = 3
COAL = json.load(open(os.path.join(os.path.dirname(__file__), "..", "dati", "simboli", "coalizione.json")))


def c(rampa, tono, notte=False):
    return A.rgb([rampa, tono], notte)


NERO = c("legno e cuoio", 0)
CHIARO = c("neutri", 4)
BAYER = [[0, 2], [3, 1]]


def px(img, x, y, col):
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((x, y), col)


def rett(img, x0, y0, x1, y1, col):
    for y in range(max(0, y0), min(img.height, y1)):
        for x in range(max(0, x0), min(img.width, x1)):
            img.putpixel((x, y), col)


def cielo(img, fasce, y0, y1):
    """Gradiente a fasce con retinatura ordinata 2x2 al passaggio (ammessa sui grandi gradienti, scelta 4)."""
    n = len(fasce) - 1
    for y in range(y0, y1):
        t = (y - y0) / max(1, (y1 - y0 - 1)) * n
        i = min(int(t), n - 1)
        f = t - i
        for x in range(img.width):
            col = fasce[i + 1] if f * 4 > BAYER[y % 2][x % 2] + 0.5 else fasce[i]
            img.putpixel((x, y), col)


def profilo(larghezza, base, ampiezze, seme):
    r = random.Random(seme)
    fasi = [r.random() * 6.28 for _ in ampiezze]
    out = []
    for x in range(larghezza):
        v = base
        for k, (a, p) in enumerate(ampiezze):
            v -= a * math.sin(x / p + fasi[k])
        out.append(int(v))
    return out


def riempi_sotto(img, prof, col, col_luce=None, ox=0):
    for x in range(img.width):
        top = prof[(x + ox) % len(prof)]
        for y in range(max(0, top), img.height):
            img.putpixel((x, y), col)
        if col_luce is not None:
            # luce da alto-sinistra: il bordo dei pendii rivolti a sinistra si schiarisce
            prev = prof[(x + ox - 1) % len(prof)]
            if top < prev:
                for y in range(top, min(top + 2, img.height)):
                    img.putpixel((x, y), col_luce)


def bande(img, testo=None, testo2=None, alto=None):
    rett(img, 0, 0, W, BANDA, NERO)
    rett(img, 0, H - BANDA, W, H, NERO)
    if alto:
        A.testo(img, 8, 7, alto, c("oro e bronzo", 3))
    righe = [t for t in (testo, testo2) if t]
    for i, t in enumerate(righe):
        larg = S.larghezza_testo(A.F, S.normalizza(A.F, t))
        A.testo(img, (W - larg) // 2, H - BANDA + 3 + i * 10, t, CHIARO)


# ---------------------------------------------------------------- panorama di Gubbio dalla valle

def strato_citta(larghezza, notte=False):
    """Profilo della città ai piedi del monte: case, Palazzo dei Consoli con la torre, mura. Sfondo trasparente."""
    img = Image.new("RGBA", (larghezza, H), (0, 0, 0, 0))
    r = random.Random(7)
    mura_y = 112
    pietra = [c("pietra calcarea", i, notte) for i in range(6)]
    coppi = [c("cotto e coppi", i, notte) for i in range(6)]
    # case a gradoni sul pendio: più in alto verso destra (la città sale verso il monte)
    x = 0
    while x < larghezza:
        w = r.randint(9, 16)
        sal = int(14 * (x / larghezza))
        top = mura_y - r.randint(8, 16) - sal
        rett(img, x, top, x + w, mura_y, pietra[3])
        rett(img, x + w - 3, top, x + w, mura_y, pietra[2])           # lato in ombra a destra
        for k in range(w):
            px(img, x + k, top - 1, coppi[3])
            px(img, x + k, top - 2, coppi[2] if k % 3 else coppi[1])
        for fy in range(top + 4, mura_y - 3, 6):                        # finestrine
            for fx in range(x + 2, x + w - 3, 5):
                px(img, fx, fy, pietra[0])
                px(img, fx, fy + 1, pietra[0])
        x += w
    # Palazzo dei Consoli: blocco alto e torre (40 m di fronte, 60 m con la torre: compressione libera per il cinema)
    px0 = int(larghezza * 0.42)
    rett(img, px0, 66, px0 + 34, mura_y, pietra[4])
    rett(img, px0 + 26, 66, px0 + 34, mura_y, pietra[2])
    for k in range(0, 34, 3):                                            # merli guelfi
        rett(img, px0 + k, 63, px0 + k + 2, 66, pietra[4] if k < 26 else pietra[2])
    for fy in (74, 86):                                                  # bifore
        for fx in range(px0 + 4, px0 + 24, 7):
            rett(img, fx, fy, fx + 3, fy + 5, pietra[0])
    rett(img, px0 + 4, 40, px0 + 12, 66, pietra[4])                      # torre campanaria
    rett(img, px0 + 10, 40, px0 + 12, 66, pietra[2])
    rett(img, px0 + 6, 44, px0 + 10, 50, pietra[0])                      # cella del Campanone
    for k in range(0, 8, 3):
        rett(img, px0 + 4 + k, 37, px0 + 6 + k, 40, pietra[4])
    # drappo di Gubbio sulla torre: rosso con monte bianco
    rett(img, px0 + 7, 29, px0 + 8, 40, NERO)
    rett(img, px0 + 8, 29, px0 + 15, 34, c("vermiglio comunale", 2, notte))
    for k in range(5):
        px(img, px0 + 9 + k, 33 - (1 if k % 2 == 0 else 0), CHIARO)
        px(img, px0 + 9 + k, 33, CHIARO)
    # mura con camminamento merlato
    rett(img, 0, mura_y, larghezza, mura_y + 10, pietra[2])
    for k in range(0, larghezza, 4):
        rett(img, k, mura_y - 2, k + 2, mura_y, pietra[2])
    rett(img, 0, mura_y + 8, larghezza, mura_y + 10, pietra[1])
    return img


def strato_monte(larghezza, notte=False):
    img = Image.new("RGBA", (larghezza, H), (0, 0, 0, 0))
    prof = []
    cima = int(larghezza * 0.55)
    for x in range(larghezza):
        d = abs(x - cima) / (larghezza * 0.42)
        prof.append(int(38 + 62 * min(1, d ** 1.25) + 2 * math.sin(x / 5.0)))
    riempi_sotto(img, prof, c("verde dei monti", 1, notte), c("verde dei monti", 2, notte))
    # stradoni a zigzag, appena accennati
    for k in range(9):
        y = 92 - k * 5
        x0 = cima - 40 + (k % 2) * 30
        for xx in range(x0, x0 + 30):
            if prof[min(larghezza - 1, xx)] < y:
                px(img, xx, y, c("verde dei monti", 2, notte))
    # basilica in vetta, piccola, con campanile
    b = cima - 8
    rett(img, b, 34, b + 16, 40, c("pietra calcarea", 3, notte))
    rett(img, b + 12, 27, b + 16, 40, c("pietra calcarea", 3, notte))
    rett(img, b, 33, b + 12, 34, c("cotto e coppi", 2, notte))
    return img


PROF_LONTANI = profilo(480, 78, [(6, 23), (3, 9)], 3)


def strato_lontani(larghezza, notte=False):
    img = Image.new("RGBA", (larghezza, H), (0, 0, 0, 0))
    riempi_sotto(img, PROF_LONTANI, c("cielo e acqua", 1, notte))
    return img


def strato_campi(larghezza, notte=False):
    img = Image.new("RGBA", (larghezza, H), (0, 0, 0, 0))
    r = random.Random(11)
    rett(img, 0, 122, larghezza, H, c("verde dei monti", 2, notte))
    for y in range(122, H, 3):
        for x in range(larghezza):
            if (x + y * 3) % 7 == 0:
                px(img, x, y, c("verde dei monti", 3, notte))
    for _ in range(larghezza // 22):                                     # cipressi in primo piano
        x = r.randint(0, larghezza)
        h = r.randint(16, 26)
        for yy in range(h):
            half = max(1, int(3 * math.sin(math.pi * (yy + 2) / (h + 2))))
            for xx in range(-half, half + 1):
                px(img, x + xx, 128 - h + yy, c("verde dei monti", 0, notte) if xx > 0 else c("verde dei monti", 1, notte))
    return img


def panorama(ox=0, fuochi=0, alba=True):
    img = Image.new("RGB", (W, H))
    if alba:
        fasce = [c("cielo e acqua", 2), c("cielo e acqua", 3), c("cielo e acqua", 4), c("oro e bronzo", 3), c("cotto e coppi", 5)]
    else:
        fasce = [c("cielo e acqua", 0, True), c("cielo e acqua", 1, True), c("cielo e acqua", 2, True), c("cotto e coppi", 2, True)]
    cielo(img, fasce, BANDA, 96)
    notte = not alba
    # parallasse: ogni strato scorre a una velocità diversa (BG3 lento, BG0 veloce)
    for k, (strato, vel) in enumerate(((STRATI[notte][0], 0.25), (STRATI[notte][1], 0.5), (STRATI[notte][2], 0.75), (STRATI[notte][3], 1.0))):
        x = int(ox * vel) % strato.width
        img.paste(strato.crop((x, 0, x + W, H)), (0, 0), strato.crop((x, 0, x + W, H)))
    # fuochi del campo nemico nella conca, sotto le mura: sprite 1x2 che lampeggiano, con le tende
    rr = random.Random(5)
    for i in range(fuochi):
        wx = rr.randint(0, 479)
        fx = (wx - ox) % 480
        if fx >= W:
            continue
        fy = rr.randint(126, 134)
        for k in range(-2, 3):
            for j in range(0, 3 - abs(k)):
                px(img, fx + 4 + k, fy - j, c("pietra calcarea", 1, notte))
        col = c("oro e bronzo", 3) if (i + ox // 4) % 3 else c("cotto e coppi", 5)
        px(img, fx, fy, col)
        px(img, fx, fy - 1, c("cotto e coppi", 4))
    return img


def prepara_strati():
    larghezza = 480
    out = {}
    for notte in (False, True):
        out[notte] = (strato_lontani(larghezza, notte), strato_monte(larghezza, notte),
                      strato_citta(larghezza, notte), strato_campi(larghezza, notte))
    return out


STRATI = None

# ---------------------------------------------------------------- l'esercito

def drappo(img, x, y, citta, w=7, h=11, onda=0):
    g = citta["gioco"]
    campo = c(*g["campo"])
    for yy in range(h):
        for xx in range(w):
            dy = int(math.sin((xx + onda) / 2.0))
            col = campo
            if "campo_destro" in g and xx >= w // 2:
                col = c(*g["campo_destro"])
            if "bande" in g and (xx + yy) % 4 < 2:
                col = c(*g["bande"])
            px(img, x + xx, y + yy + dy, col)
    fig = g.get("figura")
    if fig:
        fc = c(*g["figura_colore"])
        cx, cy = x + w // 2, y + h // 2
        forme = {
            "croce": [(0, -2), (0, -1), (0, 0), (0, 1), (0, 2), (-1, 0), (1, 0)],
            "grifo": [(0, -2), (1, -2), (-1, -1), (0, -1), (0, 0), (1, 0), (-1, 1), (1, 1), (0, 2)],
            "torre": [(-1, -2), (1, -2), (-1, -1), (0, -1), (1, -1), (-1, 0), (0, 0), (1, 0), (-1, 1), (1, 1)],
            "aquila": [(-2, -1), (2, -1), (-1, 0), (0, 0), (1, 0), (0, -1), (0, 1), (0, 2)],
            "giglio": [(0, -2), (-1, -1), (0, -1), (1, -1), (0, 0), (-1, 1), (0, 1), (1, 1)],
            "leone": [(-1, -2), (0, -1), (1, -1), (-1, 0), (0, 0), (1, 0), (-1, 1), (1, 1)],
            "capriolo": [(0, -1), (-1, 0), (1, 0), (-2, 1), (2, 1)],
        }
        for dx, dy in forme.get(fig, []):
            px(img, cx + dx, cy + dy + int(math.sin((cx - x + dx + onda) / 2.0)), fc)
    for yy in range(-2, h + 14):                                        # asta
        px(img, x - 1, y + yy, NERO)


def fante(img, x, y, col, col_ombra, passo):
    """Sagoma 5x12 di fante con lancia: è un tile di BG ripetuto, non uno sprite."""
    rett(img, x + 1, y, x + 4, y + 3, col)                                # elmo
    rett(img, x, y + 3, x + 5, y + 8, col)                                # corpo e scudo
    rett(img, x + 3, y + 3, x + 5, y + 8, col_ombra)
    a, b = (0, 3) if passo else (1, 2)
    rett(img, x + a, y + 8, x + a + 1, y + 12, col)
    rett(img, x + b, y + 8, x + b + 1, y + 12, col)
    for k in range(-8, 6):                                                # lancia
        px(img, x + 4, y + k, NERO)
    px(img, x + 4, y - 9, CHIARO)


def esercito(t=0):
    img = Image.new("RGB", (W, H))
    cielo(img, [c("cielo e acqua", 3), c("cielo e acqua", 4), c("neutri", 4)], BANDA, 80)
    riempi_sotto(img, profilo(W + 400, 70, [(5, 17), (2, 6)], 21), c("cielo e acqua", 1), ox=t // 4)
    riempi_sotto(img, profilo(W + 400, 84, [(4, 29), (2, 8)], 22), c("verde dei monti", 2), c("verde dei monti", 3), ox=t // 2)
    # tre file di fanti a velocità diverse: la profondità la dà la parallasse, non il numero di sprite
    file = ((88, 6, c("verde dei monti", 1), c("verde dei monti", 0), 0.5),
            (100, 7, c("legno e cuoio", 1), c("legno e cuoio", 0), 0.75),
            (114, 8, c("legno e cuoio", 2), c("legno e cuoio", 1), 1.0))
    for i, (y, passo_x, col, om, vel) in enumerate(file):
        rett(img, 0, y + 11, W, H, c("verde dei monti", 2 - i // 2))
        sh = int(t * vel)
        for x in range(-passo_x * 2, W + passo_x, passo_x):
            fante(img, x + sh % passo_x, y, col, om, ((x // passo_x) + t // 4) % 2)
    # gli stendardi delle undici città sopra le file: sprite, con l'onda a 2 fotogrammi
    citta = [cc for cc in COAL["citta"] if cc["id"] != "perugia"]
    for i, cc in enumerate(citta):
        drappo(img, 14 + i * 22 + int(t * 0.75) % 22 - 11, 70 + (i % 2) * 6, cc, onda=(t // 6 + i) % 2)
    per = COAL["citta"][0]
    drappo(img, 150 + int(t * 1.0) % 40 - 20, 52, per, w=13, h=19, onda=(t // 6) % 2)
    rett(img, 0, 128, W, H, c("verde dei monti", 1))
    return img


# ---------------------------------------------------------------- presentazione di un personaggio

def presentazione():
    img = Image.new("RGB", (W, H))
    cielo(img, [c("cielo e acqua", 0, True), c("cotto e coppi", 1), c("cotto e coppi", 3), c("oro e bronzo", 3)], BANDA, 120)
    pietra = [c("pietra calcarea", i, True) for i in range(6)]
    # arcate del Teatro Romano in controluce (due ordini)
    for ordine, (y0, y1, passo, lar) in enumerate(((54, 92, 30, 18), (92, 136, 34, 22))):
        rett(img, 0, y0, W, y1, pietra[1])
        for x in range(-10, W, passo):
            for yy in range(y0 + 6, y1):
                for xx in range(lar):
                    dx = xx - lar / 2
                    if yy > y0 + 6 + lar / 2 or dx * dx + (yy - (y0 + 6 + lar / 2)) ** 2 < (lar / 2) ** 2:
                        bg = img.getpixel((x + xx, yy)) if 0 <= x + xx < W else None
                        if bg is not None:
                            px(img, x + xx, yy, c("cotto e coppi", 2) if ordine else c("cotto e coppi", 1))
    rett(img, 0, 128, W, H, pietra[0])
    # bagliore del fuoco dietro la figura: due fasce piene, retinatura solo sul bordo
    cx, cy = 70, 118
    for y in range(BANDA, H - BANDA):
        for x in range(0, 150):
            d = math.hypot(x - cx, (y - cy) * 1.3)
            if d < 22:
                img.putpixel((x, y), c("oro e bronzo", 3))
            elif d < 34:
                img.putpixel((x, y), c("oro e bronzo", 2))
            elif d < 44 or (d < 48 and BAYER[y % 2][x % 2] < 2):
                img.putpixel((x, y), c("cotto e coppi", 3))
    # Antonio in controluce: cappuccio, spalle, saio a campana, fascina. Alla sua risoluzione, niente pixel ingranditi
    sag = NERO
    mask = set()
    for y in range(0, 58):
        if y < 12:
            half = int(5 * math.sin(math.pi * (y + 1) / 14)) + 1     # cappuccio
            off = -1
        elif y < 18:
            half, off = 5 + (y - 12) // 2, 0                           # spalle
        else:
            half, off = 8 + (y - 18) // 6, 0                           # saio
        for x in range(-half, half + 1):
            mask.add((cx + x + off, 70 + y))
    for k in range(30):                                                # fascina sulla spalla sinistra
        for j in range(4):
            mask.add((cx - 20 + k, 78 - k // 3 + j))
    for (x, y) in mask:
        px(img, x, y, sag)
    for (x, y) in mask:                                                # filo di luce del fuoco sul bordo
        if (x + 1, y) not in mask and x > cx and y > 72 or (x, y - 1) not in mask and y < 84:
            px(img, x, y, c("cotto e coppi", 4))
    # fiammella nella mano
    for (dx, dy, t) in ((17, 100, 3), (17, 99, 3), (18, 98, 2), (16, 98, 2), (17, 97, 3), (17, 96, 2)):
        px(img, cx + dx, dy, c("oro e bronzo", t))
    bande(img)
    # cartiglio del nome come nell'interfaccia, più ampio
    A.cartiglio(img, 140, 70, 8)
    A.testo(img, 152, 75, "ANTONIO", c("neutri", 4))
    A.testo(img, 142, 92, "Eremita e piromante.", CHIARO)
    A.testo(img, 142, 102, "La città lo lasciò", c("neutri", 3))
    A.testo(img, 142, 112, "fuori dalle porte.", c("neutri", 3))
    return img


# ---------------------------------------------------------------- dettaglio: il pastorale sulla pietra

def dettaglio(lampo=True):
    img = Image.new("RGB", (W, H))
    pietra = [c("pietra calcarea", i) for i in range(6)]
    r = random.Random(4)
    rett(img, 0, BANDA, W, 92, c("neutri", 4))                          # orlo della veste di Ubaldo
    rett(img, 0, 80, W, 92, c("neutri", 3))
    rett(img, 0, 86, W, 89, c("oro e bronzo", 2))                         # bordura d'oro
    for x in range(0, W, 6):
        px(img, x + 2, 87, c("oro e bronzo", 3))
    for x in range(20, W, 34):                                            # pieghe della veste
        rett(img, x, BANDA, x + 3, 86, c("neutri", 3))
        rett(img, x + 3, BANDA, x + 4, 86, c("neutri", 2))
    rett(img, 0, 92, W, H - BANDA, pietra[3])                             # selciato in prospettiva
    for i, y in enumerate((92, 97, 104, 113, 124)):
        rett(img, 0, y, W, y + 1, pietra[1])
    for k in range(-12, 13):
        x0 = 120 + k * 12
        for y in range(92, H - BANDA):
            px(img, int(x0 + (x0 - 120) * (y - 92) / 24), y, pietra[1])
    for _ in range(200):
        px(img, r.randint(0, W), r.randint(93, H - BANDA), pietra[2])
    # il piede del pastorale: legno e puntale di bronzo
    cx = 120
    rett(img, cx - 3, BANDA, cx + 3, 104, c("legno e cuoio", 2))
    rett(img, cx + 1, BANDA, cx + 3, 104, c("legno e cuoio", 1))
    rett(img, cx - 3, 84, cx + 3, 90, c("oro e bronzo", 2))
    rett(img, cx - 4, 98, cx + 4, 108, c("oro e bronzo", 2))
    rett(img, cx + 1, 98, cx + 4, 108, c("oro e bronzo", 1))
    rett(img, cx - 3, 98, cx - 2, 108, c("oro e bronzo", 3))
    # crepa e schegge
    for k in range(18):
        px(img, cx - 6 - k, 109 + k // 3, pietra[0])
        px(img, cx + 6 + k, 108 + k // 4, pietra[0])
    if lampo:
        for a in range(0, 360, 30):
            for d in range(10, 22):
                px(img, cx + int(d * math.cos(math.radians(a))), 108 + int(d * 0.5 * math.sin(math.radians(a))), CHIARO)
    bande(img, alto="Piazza Grande. Il primo giorno.")
    return img


# ---------------------------------------------------------------- la visione nella vetrata

def vetrata():
    img = Image.new("RGB", (W, H))
    rett(img, 0, 0, W, H, c("pietra calcarea", 0, True))
    x0, y0, w, h = 70, BANDA + 2, 100, H - 2 * BANDA - 4
    piombo = NERO
    chiari = [c("neutri", 3), c("neutri", 4), c("cielo e acqua", 4), c("pietra calcarea", 5)]
    r = random.Random(9)
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            dx = x - (x0 + w / 2)
            if y < y0 + w / 2 and dx * dx + (y - (y0 + w / 2)) ** 2 > (w / 2) ** 2:
                continue
            img.putpixel((x, y), chiari[((x - x0) // 12 + (y - y0) // 14 + r.randint(0, 0)) % 4])
            if (x - x0) % 12 == 0 or (y - y0) % 14 == 0:
                img.putpixel((x, y), piombo)
    # il vetro della visione: una finestra hardware mostra dentro un altro BG che scorre
    vx, vy, vw, vh = x0 + 24, y0 + 56, 48, 42
    cielo_v = Image.new("RGB", (vw, vh))
    cielo(cielo_v, [c("cielo e acqua", 0, True), c("cielo e acqua", 1, True)], 0, vh)
    for x in range(vw):                                                   # pareti della gola
        lx = 10 + int(4 * math.sin(x / 3.0)) if x < 18 else None
        for y in range(vh):
            if x < 12 + int(3 * math.sin(y / 4.0)) or x > vw - 12 + int(3 * math.sin(y / 5.0)):
                cielo_v.putpixel((x, y), c("pietra calcarea", 1, True))
    for k in range(4):                                                    # archi dell'acquedotto
        rett(cielo_v, 6 + k * 10, 8, 8 + k * 10, 22, c("pietra calcarea", 3, True))
    rett(cielo_v, 4, 6, vw - 4, 9, c("pietra calcarea", 3, True))
    for k in range(5):                                                    # uomini in ferro che salgono
        fx, fy = 16 + k * 4, 36 - k * 3
        rett(cielo_v, fx, fy, fx + 2, fy + 4, c("neutri", 2))
    rett(cielo_v, 34, 18, 39, 28, c("neutri", 1))                         # Corrado, il doppio di un uomo
    rett(cielo_v, 38, 14, 40, 19, c("legno e cuoio", 1))
    rett(cielo_v, 37, 12, 42, 15, c("neutri", 2))                         # martello
    img.paste(cielo_v, (vx, vy))
    for x in range(vx - 1, vx + vw + 1):
        px(img, x, vy - 1, c("oro e bronzo", 3)); px(img, x, vy + vh, c("oro e bronzo", 3))
    for y in range(vy - 1, vy + vh + 1):
        px(img, vx - 1, y, c("oro e bronzo", 3)); px(img, vx + vw, y, c("oro e bronzo", 3))
    # fasci di luce dalla vetrata: blending sul BG della navata
    for y in range(y0 + h, H - BANDA):
        for x in range(x0 - 20, x0 + w + 20):
            if (x + y) % 3 == 0 and abs((x - 120) - (y - 120) * 0.4) < 48:
                px(img, x, y, c("pietra calcarea", 2, True))
    bande(img, "Uomini in ferro salgono la gola,", "verso gli archi dell'acquedotto.")
    return img


def ingrandisci(img):
    return img.resize((img.width * Z, img.height * Z), Image.NEAREST)


def main(cartella):
    global STRATI
    os.makedirs(cartella, exist_ok=True)
    STRATI = prepara_strati()
    pan = panorama(ox=60, fuochi=0)
    bande(pan, "Nel maggio del 1151, l'invidia e la sete di dominio", "spezzarono la pace dei colli.")
    ingrandisci(pan).save(os.path.join(cartella, "c1_panorama_alba.png"))
    sera = panorama(ox=200, fuochi=40, alba=False)
    bande(sera, "Undici città confederate cinsero d'assedio", "la roccaforte di Gubbio.")
    ingrandisci(sera).save(os.path.join(cartella, "c1_panorama_fuochi.png"))
    es = esercito(0)
    bande(es, "Spoleto e Foligno. Assisi, Spello e Bettona.", "Todi e Cagli.")
    ingrandisci(es).save(os.path.join(cartella, "c2_esercito.png"))
    ingrandisci(presentazione()).save(os.path.join(cartella, "c3_presentazione_antonio.png"))
    ingrandisci(dettaglio()).save(os.path.join(cartella, "c4_dettaglio_pastorale.png"))
    ingrandisci(vetrata()).save(os.path.join(cartella, "c5_visione_vetrata.png"))
    # GIF: carrellata con parallasse (4 strati a velocità 1/4, 1/2, 3/4, 1)
    fot = []
    for i in range(0, 240, 1):
        f = panorama(ox=i, fuochi=min(40, max(0, (i - 120) // 2)))
        bande(f, "Nel maggio del 1151, l'invidia e la sete di dominio" if i < 120 else "Undici città confederate cinsero d'assedio",
              "spezzarono la pace dei colli." if i < 120 else "la roccaforte di Gubbio.")
        fot.append(ingrandisci(f).convert("P", palette=Image.ADAPTIVE, colors=64))
    fot[0].save(os.path.join(cartella, "c1_carrellata.gif"), save_all=True, append_images=fot[1:], duration=80, loop=0)
    fot = []
    for t in range(0, 96, 2):
        f = esercito(t)
        bande(f, "Spoleto e Foligno. Assisi, Spello e Bettona.", "Todi e Cagli.")
        fot.append(ingrandisci(f).convert("P", palette=Image.ADAPTIVE, colors=64))
    fot[0].save(os.path.join(cartella, "c2_esercito.gif"), save_all=True, append_images=fot[1:], duration=66, loop=0)


if __name__ == "__main__":
    main(sys.argv[1])
