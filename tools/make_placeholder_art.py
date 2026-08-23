#!/usr/bin/env python3
"""
Generatore di GRAFICA SEGNAPOSTO per Gubbio 1151.

Produce i .bmp a 4bpp (16 colori, indice 0 trasparente) e i .json che Butano si aspetta in
graphics/. Le dimensioni rispettano la Sezione 23A del GDD; le palette seguono la Sezione 14C.

NON e' arte definitiva: sono silhouette leggibili nelle dimensioni corrette, pensate per
sbloccare il rendering. Sostituire un personaggio significa sovrascrivere il suo .bmp con
l'arte vera, senza toccare una riga di C++.

FOGLI DI ANIMAZIONE (Passo 19 del piano). Gli attori di battaglia non sono piu' un disegno
solo: ogni .bmp e' una STRISCIA VERTICALE di fotogrammi, e le pose sono intervalli su quella
striscia. La forma di ogni fotogramma non e' ridisegnata a mano ma derivata da una TABELLA DI
KEYFRAME INTERI (`KEYFRAMES` qui sotto): il disegno resta uno, i fotogrammi sono lo stesso
disegno visto con scarti interi diversi. E' l'unica sorgente di verita': da qui esce il .bmp,
da qui esce `include/battle_anim_table.h`, e da qui legge `tools/preview_battle_screen.py`.

    python tools/make_placeholder_art.py
"""

import collections
import os
import struct

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "graphics")
INC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "include")


# ----------------------------------------------------------------------------------------------
# Scrittura BMP indicizzato a 4 bit
# ----------------------------------------------------------------------------------------------

def write_bmp4(path, width, height, pixels, palette):
    """pixels: lista di righe (dall'alto), ogni riga lista di indici 0-15."""
    assert width % 2 == 0, "larghezza dispari non gestita a 4bpp"
    assert len(palette) <= 16

    pal = list(palette) + [(0, 0, 0)] * (16 - len(palette))
    row_bytes = width // 2
    padding = (4 - row_bytes % 4) % 4

    body = bytearray()
    for y in range(height - 1, -1, -1):          # BMP e' bottom-up
        row = pixels[y]
        for x in range(0, width, 2):
            body.append(((row[x] & 0xF) << 4) | (row[x + 1] & 0xF))
        body.extend(b"\x00" * padding)

    pixel_offset = 14 + 40 + 16 * 4
    header = b"BM" + struct.pack("<IHHI", pixel_offset + len(body), 0, 0, pixel_offset)
    dib = struct.pack("<IiiHHIIiiII", 40, width, height, 1, 4, 0, len(body), 2835, 2835, 16, 0)
    pal_bytes = b"".join(struct.pack("<BBBB", b, g, r, 0) for (r, g, b) in pal)

    with open(path, "wb") as f:
        f.write(header + dib + pal_bytes + bytes(body))


def write_json(path, payload):
    with open(path, "w", encoding="utf-8") as f:
        f.write(payload)


def canvas(w, h, fill=0):
    return [[fill] * w for _ in range(h)]


def rect(px, x0, y0, x1, y1, c):
    for y in range(max(0, y0), min(len(px), y1 + 1)):
        for x in range(max(0, x0), min(len(px[0]), x1 + 1)):
            px[y][x] = c


def disc(px, cx, cy, r, c):
    for y in range(max(0, cy - r), min(len(px), cy + r + 1)):
        for x in range(max(0, cx - r), min(len(px[0]), cx + r + 1)):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                px[y][x] = c


def tri_up(px, cx, base_y, half, height, c):
    """Triangolo isoscele con la punta in alto: la mitra di Sant'Ubaldo."""
    for i in range(height):
        y = base_y - i
        w = max(0, int(half * (1 - i / height)))
        rect(px, cx - w, y, cx + w, y, c)


# ----------------------------------------------------------------------------------------------
# Il vocabolario dell'animazione: quattro interi, nessun numero in virgola mobile
# ----------------------------------------------------------------------------------------------
#
# Un Keyframe non descrive un disegno nuovo: descrive di quanto SPOSTARE le parti del disegno
# base. Percio' i fotogrammi non possono divergere dalla silhouette di partenza, e sostituire
# l'arte vera restera' una sola funzione da riscrivere invece di ventuno immagini.
#
#   dx, dy : scarto dell'intero corpo in pixel (respiro, affondo, contraccolpo, sprofondamento)
#   arm    : estensione dell'arma o del braccio LUNGO LO SGUARDO, in pixel
#   lean   : scorrimento della testa nella direzione dello sguardo (l'inclinazione del busto)
#
# Lo sguardo e' baked in ciascuna draw_*: gli eroi stanno a destra e guardano a sinistra, i
# nemici il contrario (`battle_hud.cpp`: HERO_X 162-218, ENEMY_X 28-112). Nelle tabelle qui
# sotto `arm` e `lean` sono percio' sempre POSITIVI QUANDO SIGNIFICANO "IN AVANTI", quale che
# sia il verso reale sullo schermo.

Keyframe = collections.namedtuple("Keyframe", "dx dy arm lean")

FERMO = Keyframe(0, 0, 0, 0)

# L'ordine e' quello dell'enum `AnimPose` in battle_anim_table.h: cambiarlo qui li cambia
# entrambi, che e' il punto.
POSE_ORDER = ("IDLE", "ATTACK", "CAST", "HURT", "VICTORY", "DEATH")

# Frame di gioco per fotogramma. Un solo numero per posa: la cadenza e' un fatto della POSA
# (un affondo e' rapido, un respiro e' lento), non del personaggio.
POSE_DURATION = {
    "IDLE": 14,        # respiro: 4 fotogrammi x 14 = poco meno di un secondo per ciclo
    "ATTACK": 4,       # l'affondo deve stare dentro il colpo, non seguirlo
    "CAST": 6,
    "HURT": 5,
    "VICTORY": 10,
    "DEATH": 8,
}

# INVARIANTE DI COMPATIBILITA': IDLE deve essere la prima posa e il suo primo fotogramma deve
# essere `FERMO`. `bn::sprite_item::create_sprite(x, y)` di `battle_hud.cpp` usa l'indice
# grafico 0 senza dirlo: se qui entrasse davanti un'altra posa, ogni combattente nascerebbe
# gia' a mezzo affondo. Verificato in Python da _verifica_tabelle() e in C++ da static_assert.
KEYFRAMES = {
    "ubaldo": {
        "IDLE":    [FERMO, Keyframe(0, 1, 0, 0), FERMO, Keyframe(0, -1, 1, 0)],
        "ATTACK":  [Keyframe(2, 0, -1, 0), Keyframe(1, -1, 0, 1),
                    Keyframe(-4, 0, 4, 2), Keyframe(-3, 0, 3, 1), FERMO],
        "CAST":    [Keyframe(0, -1, 1, 0), Keyframe(0, -2, 3, 0), Keyframe(0, -2, 5, 1),
                    Keyframe(0, -1, 3, 0), FERMO],
        "HURT":    [Keyframe(3, 1, -2, -2), Keyframe(4, 0, -2, -3), Keyframe(2, 0, -1, -1)],
        "VICTORY": [Keyframe(0, -2, 3, 0), Keyframe(0, 0, 2, 0),
                    Keyframe(0, -3, 4, 0), Keyframe(0, 0, 2, 0)],
    },
    "giorgio": {
        "IDLE":    [FERMO, Keyframe(0, 1, 0, 0), FERMO, Keyframe(0, -1, 0, 0)],
        "ATTACK":  [Keyframe(3, 0, -2, 0), Keyframe(1, -1, 0, 1),
                    Keyframe(-5, 0, 6, 2), Keyframe(-3, 0, 4, 1), FERMO],
        # Per San Giorgio la posa "CAST" e' il Bastione Azzurro: la guardia che si alza.
        "CAST":    [Keyframe(1, 0, -2, -1), Keyframe(2, -1, -3, -2),
                    Keyframe(2, -1, -3, -2), Keyframe(1, 0, -2, -1)],
        "HURT":    [Keyframe(3, 1, -2, -2), Keyframe(4, 0, -3, -3), Keyframe(2, 0, -1, -1)],
        "VICTORY": [Keyframe(0, -2, 2, 0), Keyframe(0, 0, 1, 0), Keyframe(0, -3, 3, 0)],
    },
    "antonio": {
        "IDLE":    [FERMO, Keyframe(0, 1, 0, 0), FERMO, Keyframe(0, -1, 1, 0)],
        "ATTACK":  [Keyframe(2, 0, -1, 0), Keyframe(1, -1, 1, 1),
                    Keyframe(-3, 0, 3, 2), Keyframe(-2, 0, 2, 1), FERMO],
        "CAST":    [Keyframe(0, -1, 2, 0), Keyframe(0, -2, 4, 0), Keyframe(0, -3, 6, 1),
                    Keyframe(0, -1, 3, 0), FERMO],
        "HURT":    [Keyframe(3, 1, -2, -2), Keyframe(4, 0, -2, -3), Keyframe(2, 0, -1, -1)],
        "VICTORY": [Keyframe(0, -2, 3, 0), Keyframe(0, 0, 2, 0),
                    Keyframe(0, -3, 5, 0), Keyframe(0, 0, 2, 0)],
    },
    "enemy_fante": {
        "IDLE":    [FERMO, Keyframe(0, 1, 0, 0), FERMO, Keyframe(0, -1, 0, 0)],
        "ATTACK":  [Keyframe(-3, 0, -2, 0), Keyframe(4, 0, 5, 2),
                    Keyframe(3, 0, 4, 1), FERMO],
        "HURT":    [Keyframe(-3, 1, -2, -2), Keyframe(-4, 0, -3, -3), Keyframe(-2, 0, -1, -1)],
        "DEATH":   [Keyframe(-2, 4, -3, -3), Keyframe(-3, 10, -5, -5),
                    Keyframe(-3, 20, -6, -6)],
    },
    "enemy_balestriere": {
        "IDLE":    [FERMO, Keyframe(0, 1, 0, 0), FERMO, Keyframe(0, -1, 0, 0)],
        # Il balestriere non affonda: punta, scatta la corda, rincula.
        "ATTACK":  [Keyframe(-1, 0, 2, 1), Keyframe(-1, 0, 3, 1),
                    Keyframe(2, 0, -2, 0), FERMO],
        "HURT":    [Keyframe(-3, 1, -2, -2), Keyframe(-4, 0, -3, -3), Keyframe(-2, 0, -1, -1)],
        "DEATH":   [Keyframe(-2, 4, -3, -3), Keyframe(-3, 10, -5, -5),
                    Keyframe(-3, 20, -6, -6)],
    },
    "enemy_corrado": {
        "IDLE":    [FERMO, Keyframe(0, 1, 0, 0), FERMO, Keyframe(0, -1, 1, 0)],
        "ATTACK":  [Keyframe(-4, -2, -4, -1), Keyframe(-2, -3, -2, 0),
                    Keyframe(6, 2, 8, 3), Keyframe(4, 1, 6, 2), FERMO],
        # La fornace pettorale che si carica: Corrado non lancia, divampa.
        "CAST":    [Keyframe(0, -1, 1, 0), Keyframe(0, -2, 2, 0),
                    Keyframe(0, -2, 3, 0), Keyframe(0, -1, 1, 0)],
        "HURT":    [Keyframe(-4, 2, -3, -2), Keyframe(-6, 1, -4, -3), Keyframe(-3, 0, -2, -1)],
        "DEATH":   [Keyframe(-3, 8, -5, -4), Keyframe(-5, 20, -8, -7),
                    Keyframe(-6, 40, -10, -9)],
    },
}


# ----------------------------------------------------------------------------------------------
# Personaggi (Sezione 23A GDD per le misure, Sezione 14C per i colori)
#
# Ogni draw_* disegna UN fotogramma dentro una tela della misura del fotogramma. Le costanti
# numeriche sono le stesse del disegno monolitico di prima: cio' che e' cambiato e' che ora
# ogni coordinata passa per lo scarto del keyframe.
# ----------------------------------------------------------------------------------------------

PAL_UBALDO = [(0, 0, 0), (232, 226, 205), (198, 158, 58), (120, 96, 32),
              (245, 240, 228), (150, 140, 118), (90, 80, 62), (60, 52, 40)]


def draw_ubaldo(px, kf):
    """16x32 - mitra, pastorale, bianco liturgico e oro. Guarda a SINISTRA."""
    dx, dy, arm, lean = kf.dx, kf.dy, kf.arm, kf.lean
    hx = dx - lean                       # la testa scorre in avanti, cioe' verso sinistra
    rect(px, 5 + dx, 14 + dy, 10 + dx, 30 + dy, 1)          # tonaca
    rect(px, 5 + dx, 14 + dy, 6 + dx, 30 + dy, 5)           # ombra laterale
    rect(px, 4 + dx, 16 + dy, 11 + dx, 18 + dy, 1)          # spalle
    rect(px, 7 + dx, 18 + dy, 8 + dx, 30 + dy, 2)           # stola dorata
    disc(px, 7 + hx, 11 + dy, 3, 4)                         # volto
    rect(px, 5 + dx, 13 + dy, 9 + dx, 14 + dy, 6)           # collo in ombra
    tri_up(px, 7 + hx, 8 + dy, 3, 7, 2)                     # mitra
    rect(px, 6 + hx, 8 + dy, 8 + hx, 8 + dy, 1)             # bordo della mitra
    rect(px, 13 + dx, 8 + dy - arm, 13 + dx, 31 + dy, 3)    # pastorale, che si alza con `arm`
    rect(px, 12 + dx, 6 + dy - arm, 14 + dx, 8 + dy - arm, 2)   # riccio del pastorale
    rect(px, 5 + dx, 31 + dy, 10 + dx, 31 + dy, 7)          # base


PAL_GIORGIO = [(0, 0, 0), (74, 122, 190), (44, 78, 132), (176, 186, 200),
               (232, 226, 205), (198, 158, 58), (168, 52, 40), (52, 58, 72)]


def draw_giorgio(px, kf):
    """32x32 - lancia, scudo, azzurro cavaliere e acciaio. Guarda a SINISTRA."""
    dx, dy, arm, lean = kf.dx, kf.dy, kf.arm, kf.lean
    hx = dx - lean
    ax = dx - arm                        # la lancia e' a sinistra: estenderla e' andare a -x
    rect(px, 11 + dx, 13 + dy, 21 + dx, 30 + dy, 1)         # corazza
    rect(px, 11 + dx, 13 + dy, 13 + dx, 30 + dy, 2)         # ombra
    rect(px, 12 + dx, 20 + dy, 20 + dx, 22 + dy, 6)         # fascia rossa
    disc(px, 16 + hx, 9 + dy, 4, 4)                         # volto
    rect(px, 12 + hx, 4 + dy, 20 + hx, 7 + dy, 3)           # elmo
    rect(px, 15 + hx, 6 + dy, 17 + hx, 9 + dy, 3)           # nasale
    disc(px, 25 + dx, 19 + dy, 6, 3)                        # scudo
    disc(px, 25 + dx, 19 + dy, 4, 1)
    disc(px, 25 + dx, 19 + dy, 2, 5)                        # borchia
    rect(px, 5 + ax, 2 + dy, 6 + ax, 31 + dy, 3)            # lancia
    rect(px, 4 + ax, 0 + dy, 7 + ax, 3 + dy, 5)             # punta dorata
    rect(px, 11 + dx, 31 + dy, 21 + dx, 31 + dy, 7)


PAL_ANTONIO = [(0, 0, 0), (46, 42, 40), (28, 26, 26), (222, 118, 40),
               (240, 190, 90), (196, 176, 150), (96, 72, 48), (150, 60, 24)]


def draw_antonio(px, kf):
    """16x32 - saio nero, bastone a tau, fiamma. Guarda a SINISTRA."""
    dx, dy, arm, lean = kf.dx, kf.dy, kf.arm, kf.lean
    hx = dx - lean
    rect(px, 4 + dx, 11 + dy, 11 + dx, 30 + dy, 1)          # saio
    rect(px, 4 + dx, 11 + dy, 5 + dx, 30 + dy, 2)
    rect(px, 6 + hx, 8 + dy, 10 + hx, 13 + dy, 2)           # cappuccio
    disc(px, 8 + hx, 11 + dy, 2, 5)                         # volto in ombra
    rect(px, 2 + dx, 8 + dy - arm, 3 + dx, 31 + dy, 6)      # bastone, sollevato da `arm`
    rect(px, 0 + dx, 8 + dy - arm, 5 + dx, 9 + dy - arm, 6)     # traversa del tau
    disc(px, 2 + dx, 5 + dy - arm, 2, 3)                    # fiamma
    disc(px, 2 + dx, 4 + dy - arm, 1, 4)
    rect(px, 6 + dx, 24 + dy, 9 + dx, 26 + dy, 7)           # cintura
    rect(px, 4 + dx, 31 + dy, 11 + dx, 31 + dy, 2)


PAL_FANTE = [(0, 0, 0), (150, 44, 40), (104, 30, 28), (160, 168, 178),
             (206, 178, 150), (70, 62, 58), (110, 88, 54), (40, 36, 34)]


def draw_fante(px, kf):
    """32x32 - fante di Perugia, rosso e lancia corta. Guarda a DESTRA."""
    dx, dy, arm, lean = kf.dx, kf.dy, kf.arm, kf.lean
    hx = dx + lean                       # i nemici guardano a destra: avanti e' +x
    ax = dx + arm
    rect(px, 11 + dx, 13 + dy, 21 + dx, 30 + dy, 1)
    rect(px, 19 + dx, 13 + dy, 21 + dx, 30 + dy, 2)
    disc(px, 16 + hx, 9 + dy, 4, 4)
    rect(px, 12 + hx, 4 + dy, 20 + hx, 8 + dy, 3)           # elmo
    rect(px, 26 + ax, 3 + dy, 27 + ax, 31 + dy, 6)          # asta
    rect(px, 25 + ax, 0 + dy, 28 + ax, 4 + dy, 3)           # punta
    rect(px, 12 + dx, 19 + dy, 20 + dx, 21 + dy, 5)         # cintura
    rect(px, 11 + dx, 31 + dy, 21 + dx, 31 + dy, 7)


PAL_BALESTRIERE = [(0, 0, 0), (96, 84, 62), (68, 58, 44), (170, 178, 188),
                   (206, 178, 150), (58, 52, 46), (128, 108, 72), (36, 34, 32)]


def draw_balestriere(px, kf):
    """32x32 - balestriere pesante, cuoio e acciaio. Guarda a DESTRA."""
    dx, dy, arm, lean = kf.dx, kf.dy, kf.arm, kf.lean
    hx = dx + lean
    ax = dx + arm
    rect(px, 10 + dx, 13 + dy, 20 + dx, 30 + dy, 1)
    rect(px, 18 + dx, 13 + dy, 20 + dx, 30 + dy, 2)
    disc(px, 15 + hx, 9 + dy, 4, 4)
    rect(px, 11 + hx, 4 + dy, 19 + hx, 8 + dy, 3)
    rect(px, 22 + ax, 14 + dy, 30 + ax, 16 + dy, 6)         # fusto della balestra
    rect(px, 25 + ax, 10 + dy, 26 + ax, 21 + dy, 3)         # arco
    rect(px, 24 + ax, 11 + dy, 27 + ax, 12 + dy, 3)
    rect(px, 10 + dx, 31 + dy, 20 + dx, 31 + dy, 7)


PAL_CORRADO = [(0, 0, 0), (86, 92, 104), (56, 62, 74), (150, 158, 172),
               (198, 96, 40), (232, 150, 60), (38, 42, 52), (120, 84, 44)]


def draw_corrado(px, kf):
    """64x64 - Corrado di Spoleto: il colosso delle forge (Sez. 14B.3: boss 64x64)."""
    dx, dy, arm, lean = kf.dx, kf.dy, kf.arm, kf.lean
    hx = dx + lean
    ax = dx + arm
    rect(px, 18 + dx, 22 + dy, 44 + dx, 60 + dy, 1)         # corazza massiccia
    rect(px, 18 + dx, 22 + dy, 24 + dx, 60 + dy, 2)
    # La fornace pettorale divampa con `arm`: e' l'unico dettaglio che cambia MISURA e non
    # solo posizione, ed e' cio' che rende leggibile la posa CAST di un boss che non gesticola.
    rect(px, 24 + dx - arm, 34 + dy, 38 + dx + arm, 44 + dy, 4)
    rect(px, 27 + dx, 37 + dy, 35 + dx, 41 + dy, 5)
    disc(px, 31 + hx, 16 + dy, 8, 3)                        # elmo
    rect(px, 21 + hx, 8 + dy, 41 + hx, 20 + dy, 1)
    rect(px, 21 + hx, 8 + dy, 41 + hx, 11 + dy, 2)
    rect(px, 25 + hx, 16 + dy, 37 + hx, 19 + dy, 6)         # feritoia
    rect(px, 50 + ax, 10 + dy, 55 + ax, 58 + dy, 7)         # manico del martello
    rect(px, 44 + ax, 4 + dy, 62 + ax, 20 + dy, 1)          # testa del martello
    rect(px, 44 + ax, 4 + dy, 62 + ax, 8 + dy, 3)
    rect(px, 18 + dx, 61 + dy, 44 + dx, 63 + dy, 6)


# ----------------------------------------------------------------------------------------------
# Gli attori di battaglia, e le misure di foglio che il Passo 19 del piano impone
# ----------------------------------------------------------------------------------------------

Actor = collections.namedtuple("Actor", "name enum draw palette width frame_height sheet_height")

# `sheet_height` NON e' calcolata: e' copiata dal piano (Passo 19: ubaldo 16x672, giorgio
# 32x608, antonio 16x672, nemici 32x448, corrado 64x1216). Serve proprio a fallire quando la
# tabella dei keyframe e il piano divergono, invece di generare in silenzio un foglio diverso.
ACTORS = [
    Actor("ubaldo",            "UBALDO",            draw_ubaldo,      PAL_UBALDO,      16, 32, 672),
    Actor("giorgio",           "GIORGIO",           draw_giorgio,     PAL_GIORGIO,     32, 32, 608),
    Actor("antonio",           "ANTONIO",           draw_antonio,     PAL_ANTONIO,     16, 32, 672),
    Actor("enemy_fante",       "ENEMY_FANTE",       draw_fante,       PAL_FANTE,       32, 32, 448),
    Actor("enemy_balestriere", "ENEMY_BALESTRIERE", draw_balestriere, PAL_BALESTRIERE, 32, 32, 448),
    Actor("enemy_corrado",     "ENEMY_CORRADO",     draw_corrado,     PAL_CORRADO,     64, 64, 1216),
]

# Misure OBJ legali del GBA. Un foglio la cui misura di FOTOGRAMMA non e' qui dentro non e'
# disegnabile dall'hardware: e' la stessa tabella di tests/test_assets.py, ripetuta qui perche'
# il generatore deve rifiutarsi di produrre il file, non lasciarlo scoprire al test.
MISURE_OBJ = {(8, 8), (16, 16), (32, 32), (64, 64),
              (16, 8), (32, 8), (32, 16), (64, 32),
              (8, 16), (8, 32), (16, 32), (32, 64)}

# Tetto dei fotogrammi di una singola posa. Il Passo 21 del piano dimensiona l'animatore su
# `bn::sprite_animate_action<6>`, uno solo, cached, per l'unico attore animato per volta.
MAX_CLIP_FRAMES = 6


def clips(actor):
    """(posa, primo_fotogramma, conteggio) per le sole pose che l'attore possiede."""
    out = []
    first = 0
    for pose in POSE_ORDER:
        frames = KEYFRAMES[actor.name].get(pose)
        if not frames:
            continue
        out.append((pose, first, len(frames)))
        first += len(frames)
    return out


def total_frames(actor):
    return sum(count for _, _, count in clips(actor))


def build_sheet(actor):
    """Il foglio: le pose in fila, nell'ordine di POSE_ORDER, una striscia verticale sola."""
    cells = []
    for pose in POSE_ORDER:
        for kf in KEYFRAMES[actor.name].get(pose, ()):
            cell = canvas(actor.width, actor.frame_height)
            actor.draw(cell, kf)
            cells.append(cell)

    px = canvas(actor.width, actor.frame_height * len(cells))
    for i, cell in enumerate(cells):
        for y in range(actor.frame_height):
            px[i * actor.frame_height + y] = cell[y]
    return px, list(actor.palette), actor.width, actor.frame_height * len(cells)


def _verifica_tabelle():
    """Le stesse invarianti che il .h generato ripete come static_assert.

    Il mirror non e' un vezzo: senza, la tabella C++ potrebbe restare valida mentre il .bmp da
    cui dipende e' gia' sbagliato, e nessuno dei due lo direbbe.
    """
    for actor in ACTORS:
        pose_presenti = [p for p in KEYFRAMES[actor.name] if p not in POSE_ORDER]
        assert not pose_presenti, \
            "%s dichiara pose che AnimPose non conosce: %s" % (actor.name, pose_presenti)

        elenco = clips(actor)
        assert elenco, "%s non ha nemmeno una posa" % actor.name

        # 1. Compatibilita' con create_sprite(x, y), che usa l'indice grafico 0 e basta.
        pose0, first0, count0 = elenco[0]
        assert pose0 == "IDLE" and first0 == 0 and count0 > 0, \
            "%s: l'indice 0 non e' IDLE frame 0, ogni sprite creato da create_sprite(x,y) " \
            "nascerebbe nella posa sbagliata" % actor.name
        assert KEYFRAMES[actor.name]["IDLE"][0] == FERMO, \
            "%s: IDLE fotogramma 0 non e' il disegno fermo, quindi il gioco parte gia' " \
            "a mezzo movimento" % actor.name

        # 2. Le pose sono contigue: nessun buco, nessuna sovrapposizione, nessuna coda morta.
        atteso = 0
        for pose, first, count in elenco:
            assert first == atteso, \
                "%s posa %s: primo fotogramma %d invece di %d, il foglio ha un buco" % (
                    actor.name, pose, first, atteso)
            assert count <= MAX_CLIP_FRAMES, \
                "%s posa %s: %d fotogrammi, oltre i %d di bn::sprite_animate_action del " \
                "Passo 21" % (actor.name, pose, count, MAX_CLIP_FRAMES)
            atteso += count
        assert atteso == total_frames(actor)

        # 3. Il foglio e' esattamente quello che il Passo 19 del piano prescrive.
        altezza = total_frames(actor) * actor.frame_height
        assert altezza == actor.sheet_height, \
            "%s: il foglio verrebbe %dx%d invece di %dx%d prescritto dal Passo 19 del piano" % (
                actor.name, actor.width, altezza, actor.width, actor.sheet_height)

        # 4. Il FOTOGRAMMA, non il foglio, deve essere una misura OBJ legale.
        assert (actor.width, actor.frame_height) in MISURE_OBJ, \
            "%s: il fotogramma %dx%d non e' una misura OBJ del GBA" % (
                actor.name, actor.width, actor.frame_height)
        assert altezza % actor.frame_height == 0


# ----------------------------------------------------------------------------------------------
# include/battle_anim_table.h, generato dalla tabella qui sopra
# ----------------------------------------------------------------------------------------------

def emit_anim_table():
    L = []
    a = L.append
    a("#ifndef BATTLE_ANIM_TABLE_H")
    a("#define BATTLE_ANIM_TABLE_H")
    a("")
    a("// GENERATO DA tools/make_placeholder_art.py - non modificare a mano.")
    a("//")
    a("// Dove stanno le pose dentro i fogli di graphics/*.bmp. La tabella e' derivata dalle")
    a("// STESSE liste di keyframe da cui escono i .bmp: e' l'unico modo perche' un ritocco")
    a("// all'animazione non possa lasciare indietro gli indici che il C++ usa per pescarla.")
    a("//")
    a("// I fogli sono strisce verticali: l'indice grafico di Butano scorre dall'alto al basso,")
    a("// un fotogramma per cella. Non costano VRAM: `create_sprite` copia in OBJ VRAM il solo")
    a("// fotogramma richiesto, il resto resta in ROM.")
    a("")
    a("#include <stdint.h>")
    a("")
    a("namespace gubbio")
    a("{")
    a("")
    a("enum class AnimActor : uint8_t")
    a("{")
    for i, actor in enumerate(ACTORS):
        a("    %s = %d,       // graphics/%s.bmp, %dx%d" % (
            actor.enum, i, actor.name, actor.width, actor.sheet_height))
    a("};")
    a("")
    a("inline constexpr int ANIM_ACTOR_COUNT = %d;" % len(ACTORS))
    a("")
    a("// L'ordine e' quello di POSE_ORDER nel generatore, ed e' anche l'ordine in cui le pose")
    a("// si succedono dentro il foglio. Non tutti gli attori hanno tutte le pose: gli eroi non")
    a("// hanno DEATH (svengono, non muoiono - Sez. 20B), i nemici non hanno VICTORY.")
    a("enum class AnimPose : uint8_t")
    a("{")
    for i, pose in enumerate(POSE_ORDER):
        a("    %s = %d," % (pose, i))
    a("};")
    a("")
    a("inline constexpr int ANIM_POSE_COUNT = %d;" % len(POSE_ORDER))
    a("")
    a("// Una posa assente ha frame_count == 0: chiederla e' un errore del chiamante, non un")
    a("// caso da disegnare. Usare anim_has_pose() prima.")
    a("struct AnimClip")
    a("{")
    a("    uint16_t first_frame;")
    a("    uint8_t frame_count;")
    a("    uint8_t frame_duration;    // frame di gioco per fotogramma")
    a("};")
    a("")
    a("struct AnimSheet")
    a("{")
    a("    uint16_t width;")
    a("    uint16_t frame_height;")
    a("    uint16_t total_frames;")
    a("};")
    a("")
    a("inline constexpr AnimSheet ANIM_SHEETS[ANIM_ACTOR_COUNT] = {")
    for actor in ACTORS:
        a("    { %d, %d, %d },    // %s" % (
            actor.width, actor.frame_height, total_frames(actor), actor.name))
    a("};")
    a("")
    a("inline constexpr AnimClip ANIM_CLIPS[ANIM_ACTOR_COUNT][ANIM_POSE_COUNT] = {")
    for actor in ACTORS:
        mappa = {pose: (first, count) for pose, first, count in clips(actor)}
        voci = []
        for pose in POSE_ORDER:
            first, count = mappa.get(pose, (0, 0))
            durata = POSE_DURATION[pose] if count else 0
            voci.append("{ %d, %d, %d }" % (first, count, durata))
        a("    // %s" % actor.name)
        a("    { %s }," % ", ".join(voci))
    a("};")
    a("")
    a("[[nodiscard]] constexpr const AnimClip& anim_clip(AnimActor actor, AnimPose pose)")
    a("{")
    a("    return ANIM_CLIPS[int(actor)][int(pose)];")
    a("}")
    a("")
    a("[[nodiscard]] constexpr bool anim_has_pose(AnimActor actor, AnimPose pose)")
    a("{")
    a("    return ANIM_CLIPS[int(actor)][int(pose)].frame_count > 0;")
    a("}")
    a("")
    a("// Indice grafico da passare a bn::sprite::set_item / set_tiles.")
    a("[[nodiscard]] constexpr int anim_graphics_index(AnimActor actor, AnimPose pose, int frame)")
    a("{")
    a("    return int(ANIM_CLIPS[int(actor)][int(pose)].first_frame) + frame;")
    a("}")
    a("")
    a("// Durata totale della posa in frame di gioco: quanto deve attendere il temporizzatore")
    a("// dello stato PLAY_ROUND_ANIMATIONS del Passo 20 prima di passare all'evento dopo.")
    a("[[nodiscard]] constexpr int anim_pose_duration(AnimActor actor, AnimPose pose)")
    a("{")
    a("    const AnimClip& clip = ANIM_CLIPS[int(actor)][int(pose)];")
    a("    return int(clip.frame_count) * int(clip.frame_duration);")
    a("}")
    a("")
    a("// Le pose in fila senza buchi ne' sovrapposizioni, e la fila che copre tutto il foglio.")
    a("// Un buco qui significa fotogrammi in ROM che nessuna posa nomina; una sovrapposizione")
    a("// significa due pose che si contendono le stesse celle.")
    a("[[nodiscard]] constexpr bool anim_clips_are_contiguous(int actor)")
    a("{")
    a("    int next = 0;")
    a("")
    a("    for(int pose = 0; pose < ANIM_POSE_COUNT; ++pose)")
    a("    {")
    a("        const AnimClip& clip = ANIM_CLIPS[actor][pose];")
    a("")
    a("        if(clip.frame_count == 0)")
    a("        {")
    a("            if(clip.first_frame != 0 || clip.frame_duration != 0)")
    a("            {")
    a("                return false;      // posa assente ma descrittore non azzerato")
    a("            }")
    a("")
    a("            continue;")
    a("        }")
    a("")
    a("        if(int(clip.first_frame) != next)")
    a("        {")
    a("            return false;")
    a("        }")
    a("")
    a("        next += int(clip.frame_count);")
    a("    }")
    a("")
    a("    return next == int(ANIM_SHEETS[actor].total_frames);")
    a("}")
    a("")
    a("// Misure OBJ legali del GBA, applicate al FOTOGRAMMA e non al foglio.")
    a("[[nodiscard]] constexpr bool anim_frame_size_is_legal(int width, int height)")
    a("{")
    a("    return (width == 8  && (height == 8 || height == 16 || height == 32)) ||")
    a("           (width == 16 && (height == 8 || height == 16 || height == 32)) ||")
    a("           (width == 32 && (height == 8 || height == 16 || height == 32 || height == 64)) ||")
    a("           (width == 64 && (height == 32 || height == 64));")
    a("}")
    a("")
    a("// -------------------------------------------------------------------------------------")
    a("// Le invarianti. Sono le stesse di _verifica_tabelle() in tools/make_placeholder_art.py:")
    a("// se una delle due sponde cede, il foglio .bmp e questa tabella hanno gia' divergiuto.")
    a("// -------------------------------------------------------------------------------------")
    a("")
    for i, actor in enumerate(ACTORS):
        a("// --- %s ---" % actor.name)
        a('static_assert(ANIM_CLIPS[%d][int(AnimPose::IDLE)].first_frame == 0 &&' % i)
        a('              ANIM_CLIPS[%d][int(AnimPose::IDLE)].frame_count > 0,' % i)
        a('              "%s: l\'indice grafico 0 non e\' IDLE fotogramma 0. '
          'battle_hud.cpp crea gli sprite con create_sprite(x, y), che usa l\'indice 0 senza '
          'dirlo: ogni combattente nascerebbe nella posa sbagliata.");' % actor.name)
        a('static_assert(anim_clips_are_contiguous(%d),' % i)
        a('              "%s: le pose non coprono il foglio senza buchi. '
          'Il .bmp e questa tabella non descrivono piu' % actor.name +
          "' lo stesso file.\");")
        a('static_assert(int(ANIM_SHEETS[%d].total_frames) * int(ANIM_SHEETS[%d].frame_height) '
          '== %d,' % (i, i, actor.sheet_height))
        a('              "%s: il foglio non e\' alto %d px come prescrive il Passo 19 del '
          'piano.");' % (actor.name, actor.sheet_height))
        a('static_assert(anim_frame_size_is_legal(ANIM_SHEETS[%d].width, '
          'ANIM_SHEETS[%d].frame_height),' % (i, i))
        a('              "%s: il fotogramma non e\' una misura OBJ del GBA, l\'hardware non '
          'saprebbe disegnarlo.");' % actor.name)
        a("")

    a("// Nessuna posa oltre i fotogrammi che l'animatore del Passo 21 puo' tenere: uno solo,")
    a("// cached, bn::sprite_animate_action<%d>, per l'unico attore animato per volta." % MAX_CLIP_FRAMES)
    a("inline constexpr int ANIM_MAX_CLIP_FRAMES = %d;" % MAX_CLIP_FRAMES)
    a("")
    a("[[nodiscard]] constexpr bool anim_clips_fit_animator()")
    a("{")
    a("    for(int actor = 0; actor < ANIM_ACTOR_COUNT; ++actor)")
    a("    {")
    a("        for(int pose = 0; pose < ANIM_POSE_COUNT; ++pose)")
    a("        {")
    a("            if(int(ANIM_CLIPS[actor][pose].frame_count) > ANIM_MAX_CLIP_FRAMES)")
    a("            {")
    a("                return false;")
    a("            }")
    a("        }")
    a("    }")
    a("")
    a("    return true;")
    a("}")
    a("")
    a('static_assert(anim_clips_fit_animator(),')
    a('              "una posa supera i fotogrammi di bn::sprite_animate_action<%d>: '
      'l\'animatore del Passo 21 non potrebbe riprodurla senza allargare il tetto VRAM di ~3 KB '
      'gia\' calcolato nel piano.");' % MAX_CLIP_FRAMES)
    a("")
    a("// -------------------------------------------------------------------------------------")
    a("// Fogli a fotogrammi che NON sono attori: barre e gettoni della timeline. Stanno qui")
    a("// perche' sono le costanti che src/battle_hud.cpp e tools/preview_battle_screen.py")
    a("// duplicavano a mano - il difetto dichiarato nella Sessione 05 che il Passo 19 chiude.")
    a("// -------------------------------------------------------------------------------------")
    a("")
    a("inline constexpr int HUD_BAR_FRAMES = %d;" % BAR_HALF)
    a("inline constexpr int HUD_BAR_FERVOR_OFFSET = %d;   // secondo set, in oro" % BAR_HALF)
    a("inline constexpr int HUD_BAR_WIDTH = %d;" % BAR_W)
    a("inline constexpr int HUD_BAR_FRAME_HEIGHT = %d;" % BAR_FRAME_H)
    a("inline constexpr int TIMELINE_ICON_COUNT = %d;" % len(TIMELINE_FACES))
    a("inline constexpr int TIMELINE_ICON_SIZE = %d;" % TIMELINE_SIZE)
    a("")
    a('static_assert(HUD_BAR_FERVOR_OFFSET == HUD_BAR_FRAMES,')
    a('              "il set Fervore non comincia dove finisce quello HP: le barre d\'oro '
      'mostrerebbero valori di HP.");')
    a('static_assert(anim_frame_size_is_legal(HUD_BAR_WIDTH, HUD_BAR_FRAME_HEIGHT) &&')
    a('              anim_frame_size_is_legal(TIMELINE_ICON_SIZE, TIMELINE_ICON_SIZE),')
    a('              "barra o gettone fuori dalle misure OBJ del GBA.");')
    a("")
    a("}")
    a("")
    a("#endif")
    a("")
    return "\n".join(L)


# ----------------------------------------------------------------------------------------------
# Fondale d'assedio + pannello HUD (Sezione 14B.3 GDD)
# ----------------------------------------------------------------------------------------------

def make_battle_bg():
    """256x256; l'area visibile e' 240x160. Righe 0-111 scena, 112-159 pannello HUD."""
    P = [
        (18, 20, 34),    # 0 cielo alto
        (30, 32, 52),    # 1 cielo medio
        (48, 46, 68),    # 2 cielo basso / foschia
        (34, 32, 46),    # 3 monte lontano
        (24, 24, 36),    # 4 monte vicino
        (66, 62, 80),    # 5 nebbia
        (44, 40, 38),    # 6 terreno
        (58, 52, 46),    # 7 terreno chiaro
        (14, 15, 12),    # 8 pannello HUD
        (26, 28, 22),    # 9 pannello HUD chiaro
        (138, 110, 44),  # 10 bordo bronzo
        (90, 72, 30),    # 11 bordo bronzo scuro
        (10, 11, 9),     # 12 nero pannello
        (72, 78, 66),    # 13 divisorio
        (0, 0, 0), (0, 0, 0),
    ]
    W, H = 256, 256
    px = canvas(W, H, 0)

    for y in range(0, 112):                       # cielo a fasce
        c = 0 if y < 26 else 1 if y < 58 else 2
        rect(px, 0, y, W - 1, y, c)

    # LA CITTA' VERA, se c'e'. `tools/photo_to_tiles.py` converte la fotografia dello skyline
    # sulla palette qui sopra: il profilo procedurale che segue resta come ripiego per chi clona
    # il progetto senza le foto, che non sono versionate.
    import os as _os
    _ingr = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "ingredienti",
                          "skyline_assedio.bmp")
    _skyline = None

    if _os.path.exists(_ingr):
        import struct as _st
        _d = open(_ingr, "rb").read()
        _off = _st.unpack_from("<I", _d, 10)[0]
        _w, _h = _st.unpack_from("<ii", _d, 18)
        _rb = _w // 2
        _pad = (4 - _rb % 4) % 4
        _righe = []

        for _y in range(_h):
            _st0 = _off + _y * (_rb + _pad)
            _r = []
            for _b in _d[_st0:_st0 + _rb]:
                _r.append(_b >> 4)
                _r.append(_b & 0x0F)
            _righe.append(_r)

        _righe.reverse()
        _skyline = _righe

        for _y in range(min(_h, 96)):
            for _x in range(min(_w, W)):
                px[16 + _y][_x] = _righe[_y][_x]

    for x in range(W) if not _skyline else range(0):    # profilo del Monte Ingino
        h = 74 - int(26 * abs(((x + 40) % 200) / 100.0 - 1.0) ** 1.4)
        rect(px, x, h, x, 99, 3)
        h2 = 86 - int(16 * abs(((x + 130) % 150) / 75.0 - 1.0) ** 1.2)
        rect(px, x, h2, x, 99, 4)

    for y in range(86, 100):                      # banco di nebbia, a chiazze
        for x in range(W):
            n = (x * 7 + y * 13) % 23
            if n < 6 - abs(y - 93):
                px[y][x] = 5

    rect(px, 0, 100, W - 1, 111, 6)               # terreno
    for x in range(0, W, 7):
        rect(px, x, 104, x + 2, 105, 7)

    rect(px, 0, 112, W - 1, 159, 8)               # pannello HUD
    rect(px, 0, 112, W - 1, 113, 10)              # bordo bronzo superiore
    rect(px, 0, 114, W - 1, 114, 11)
    rect(px, 2, 117, 78, 157, 12)                 # riquadro menu comandi (80px)
    rect(px, 82, 117, 253, 157, 12)               # riquadro stato party
    rect(px, 80, 117, 80, 157, 13)                # divisorio
    return px, P, W, H


BAR_W, BAR_FRAME_H, BAR_HALF = 32, 8, 17


def make_bar():
    """32x8, 34 fotogrammi: 0-16 barra HP (cremisi), 17-33 barra Fervore (oro).

    Due set distinti invece dello scaling affine, che consumerebbe gli slot affine del GBA.
    """
    P = [(0, 0, 0), (34, 32, 28), (70, 74, 64), (176, 52, 44),
         (226, 96, 76), (206, 160, 52), (244, 214, 120), (12, 13, 11)]
    W, FRAME_H, HALF = BAR_W, BAR_FRAME_H, BAR_HALF
    px = canvas(W, FRAME_H * HALF * 2)
    for setno, (body, light) in enumerate(((3, 4), (5, 6))):
        for f in range(HALF):
            top = (setno * HALF + f) * FRAME_H
            rect(px, 0, top, W - 1, top + FRAME_H - 1, 1)          # fondo
            rect(px, 0, top, W - 1, top, 7)                        # cornice
            rect(px, 0, top + FRAME_H - 1, W - 1, top + FRAME_H - 1, 7)
            filled = (W - 2) * f // (HALF - 1)
            if filled:
                rect(px, 1, top + 1, filled, top + FRAME_H - 2, body)
                rect(px, 1, top + 1, filled, top + 2, light)       # lumeggiatura
    return px, P, W, FRAME_H * HALF * 2


CURSOR_SIZE = 16


def make_cursor():
    """16x16 - cursore di selezione bersaglio: cuneo bronzeo."""
    P = [(0, 0, 0), (222, 178, 72), (150, 112, 34), (250, 228, 160)]
    px = canvas(CURSOR_SIZE, CURSOR_SIZE)
    for i in range(8):
        rect(px, 4 + i, 3 + i, 11 - i, 3 + i, 1)
    for i in range(8):
        rect(px, 4 + i, 3 + i, 4 + i, 3 + i, 3)
        rect(px, 11 - i, 3 + i, 11 - i, 3 + i, 2)
    return px, P, CURSOR_SIZE, CURSOR_SIZE


# ----------------------------------------------------------------------------------------------

TIMELINE_SIZE = 16
TIMELINE_FACES = [(2, 3), (4, 8), (1, 5), (6, 2), (7, 8), (8, 5)]


def make_timeline_icons():
    """16x16 x6 - gettoni della timeline (Sez. 20A GDD): 0-2 i Ceri, 3-5 i nemici."""
    P = [(0, 0, 0), (18, 20, 16), (232, 226, 205), (198, 158, 58),
         (74, 122, 190), (222, 118, 40), (150, 44, 40), (96, 84, 62),
         (150, 158, 172), (110, 116, 128)]
    faces = TIMELINE_FACES
    px = canvas(TIMELINE_SIZE, TIMELINE_SIZE * len(faces))
    for i, (body, mark) in enumerate(faces):
        top = i * TIMELINE_SIZE
        rect(px, 1, top + 1, 14, top + 14, 1)          # cornice scura
        rect(px, 2, top + 2, 13, top + 13, body)
        disc(px, 7, top + 7, 3, mark)                  # contrassegno
        rect(px, 2, top + 2, 13, top + 2, mark)        # lumeggiatura superiore
    return px, P, TIMELINE_SIZE, TIMELINE_SIZE * len(faces)


# Sprite che non sono attori di battaglia. `height` e' SEMPRE dichiarata, anche quando il foglio
# ha un fotogramma solo: senza, il .json non dice a nessuno quale sia la misura OBJ, e un foglio
# a piu' fotogrammi diventa una misura illegale nell'istante in cui qualcuno lo allunga.
SPRITES = [
    ("timeline_icons", make_timeline_icons, TIMELINE_SIZE),
    ("hud_bar", make_bar, BAR_FRAME_H),
    ("target_cursor", make_cursor, CURSOR_SIZE),
]


def sprite_json(frame_h):
    # `bpp_mode` esplicito, sempre: senza, butano_graphics_tool.py promuove in silenzio a
    # 8bpp ogni BMP oltre i 16 colori, raddoppiando la VRAM per tile e — per un background —
    # occupando tutti e 16 i banchi di palette. Preteso da tests/test_assets.py.
    return ('{\n    "type": "sprite",\n    "bpp_mode": "bpp_4",\n'
            '    "height": %d\n}\n' % frame_h)


def main():
    _verifica_tabelle()

    out = os.path.normpath(OUT)
    os.makedirs(out, exist_ok=True)

    for actor in ACTORS:
        px, pal, w, h = build_sheet(actor)
        write_bmp4(os.path.join(out, actor.name + ".bmp"), w, h, px, pal)
        write_json(os.path.join(out, actor.name + ".json"), sprite_json(actor.frame_height))
        pose_txt = " ".join("%s:%d" % (pose, count) for pose, _, count in clips(actor))
        print("  attore  %-20s %dx%d  (%d fotogrammi da %dx%d)  %s" % (
            actor.name, w, h, total_frames(actor), actor.width, actor.frame_height, pose_txt))

    for name, fn, frame_h in SPRITES:
        px, pal, w, h = fn()
        write_bmp4(os.path.join(out, name + ".bmp"), w, h, px, pal)
        write_json(os.path.join(out, name + ".json"), sprite_json(frame_h))
        print("  sprite  %-20s %dx%d" % (name, w, h))

    px, pal, w, h = make_battle_bg()
    write_bmp4(os.path.join(out, "battle_bg.bmp"), w, h, px, pal)
    write_json(os.path.join(out, "battle_bg.json"),
               '{\n    "type": "regular_bg",\n    "bpp_mode": "bpp_4"\n}\n')
    print("  bg      %-20s %dx%d" % ("battle_bg", w, h))

    header = os.path.normpath(os.path.join(INC, "battle_anim_table.h"))
    write_json(header, emit_anim_table())
    print("  header  %s" % header)

    print("\nGrafica segnaposto generata in %s" % out)


if __name__ == "__main__":
    main()
