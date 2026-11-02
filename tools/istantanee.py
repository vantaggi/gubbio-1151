#!/usr/bin/env python3
"""Istantanee delle aree: come si vedono nel gioco e com'e' fatta la loro griglia.

    python tools/istantanee.py CARTELLA                      # solo le griglie
    python tools/istantanee.py CARTELLA --rom ROM_ISTANTANEE  # griglie e schermate
    python tools/istantanee.py CARTELLA --fondale piazza_grande  # anche il fondale intero di un'area
                                                    # (ISTANTANEE_SCALA=3 per ingrandirlo)
    python tools/istantanee.py CARTELLA --battaglia ROM_AVVIO_5  # le schermate della battaglia

Griglie (ovunque): per ogni area un PNG di 1 pixel per tile ingrandito x4, dalla griglia finale del
generatore (edifici e dislivello compresi), con suolo, strade, muri, facciate, portoni, varchi e
spawn in colori diversi: griglia_<area>.png.

Schermate (solo Windows, con mGBA 0.10): serve una ROM che parta da sola nel modo istantanee
(src/istantanee.cpp), compilata a parte e poi rimessa com'era:

    touch src/main.cpp && bash build.sh USERFLAGS=-DGUBBIO_AVVIO=2 && cp gubbio1151.gba ROM_ISTANTANEE
    touch src/main.cpp && bash build.sh

Nessun tasto simulato: per ogni riga "Istantanea N" del log di mGBA la finestra viene catturata
(PrintWindow) e salvata come schermata_<area>.png, 240x160.
"""
import glob
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import zlib

RADICE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(RADICE, "tools"))
import genera_mondo as G  # noqa: E402
import pittore_monumenti as PM  # noqa: E402,F401

MGBA = os.environ.get("MGBA", r"C:\Users\cioti\mGBA-0.10.5\mGBA.exe")
ROM = os.path.join(RADICE, "gubbio1151.gba")
INGRANDIMENTO = 4

COLORI = {
    ".": (196, 186, 160),   # suolo
    ",": (168, 108, 74),    # strada
    "S": (220, 214, 196),   # scalinata
    "#": (70, 62, 56),      # muro, tetto, edificio
    "=": (120, 150, 110),   # parapetto
    "C": (236, 226, 200),   # facciata
    "P": (210, 196, 170),   # seconda facciata
    "d": (110, 70, 40),     # portone
    "F": (90, 150, 200),    # fontana
    "I": (20, 20, 20),      # ingresso di un dungeon
    "M": (150, 120, 90),    # muro di contenimento di un gradone
    "V": (40, 30, 40),      # la citta' bassa oltre il parapetto di un belvedere
    "W": (110, 100, 90),    # le mura della citta
    "L": (206, 198, 176),   # lastrico a corsi
    "K": (180, 170, 150),   # corso di pietra del lastrico
    "Z": (214, 196, 150),   # vialetto dei giardini
    "J": (150, 140, 120),   # l'arco di una porta, ci si passa sotto
    "Q": (240, 220, 120),   # lampione
    "O": (60, 110, 160),    # pozzo
    "Y": (60, 120, 60),     # siepe
    "D": (150, 190, 110),   # aiuola
    "N": (120, 170, 90),    # prato
    "b": (226, 216, 190),   # ghiaia degli stradoni
    "r": (80, 140, 70),     # cespuglio
    "u": (30, 80, 40),      # cipresso
    "m": (160, 150, 130),   # muretto a secco
    "h": (170, 150, 120),   # chiostro
    "q": (120, 80, 40),     # panca
    "l": (240, 200, 90),    # candeliere
    "w": (90, 120, 200),    # vetrata
    "p": (200, 200, 190),   # paracarro
    "v": (70, 130, 190),    # vasca
    "c": (200, 120, 90),    # cappelletta
    "k": (140, 140, 130),   # roccia
    "n": (230, 230, 220),   # colonna
    "a": (250, 240, 200),   # altare
    "e": (150, 90, 40),     # cero
    "T": (40, 100, 50),     # albero
    "X": (100, 90, 80),     # torre di una porta
    "R": (170, 160, 140),   # gradinata del Teatro
    "U": (130, 115, 95),    # arcate del Teatro
}
COLORE_VARCO = (230, 60, 60)
COLORE_SPAWN = (40, 90, 230)
COLORE_SPAWN_0 = (250, 210, 40)


def png(percorso, larghezza, altezza, pixel):
    """PNG RGB senza dipendenze: pixel e' una lista di righe di tuple (r, g, b)."""
    grezzo = b"".join(b"\x00" + bytes(c for p in riga for c in p) for riga in pixel)

    def blocco(tipo, dati):
        return struct.pack(">I", len(dati)) + tipo + dati + struct.pack(">I", zlib.crc32(tipo + dati) & 0xFFFFFFFF)

    with open(percorso, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(blocco(b"IHDR", struct.pack(">IIBBBBB", larghezza, altezza, 8, 2, 0, 0, 0)))
        f.write(blocco(b"IDAT", zlib.compress(grezzo, 9)))
        f.write(blocco(b"IEND", b""))


def aree_finali():
    """Le aree nell'ordine di include/mondo.h, con edifici, dislivello e tile disegnati."""
    mondo = G.mondo_del_repo()
    aree = [G.leggi_area(n, t) for n, t in G.sorgenti_del_repo()]
    for a in aree:
        G.prepara_area(a, mondo)
        a["tile"], a["indici"], _ = G.disegna_area(a, mondo)
    return G.ordina(aree, G.anello(mondo["grafo"]))


def colore_cella(a, x, y):
    if (x, y) == a["spawn"].get(0):
        return COLORE_SPAWN_0
    if (x, y) in a["spawn"].values():
        return COLORE_SPAWN
    c = a["griglia"][y][x]
    if c in G.VARCHI and c != "I":
        return COLORE_VARCO
    return COLORI[c]


def griglie(cartella):
    for a in aree_finali():
        k = INGRANDIMENTO
        righe = []
        for y in range(a["altezza"]):
            riga = [colore_cella(a, x, y) for x in range(a["larghezza"]) for _ in range(k)]
            righe += [riga] * k
        png(os.path.join(cartella, f"griglia_{a['id']}.png"), a["larghezza"] * k, a["altezza"] * k, righe)
    print(f"[istantanee] {len(aree_finali())} griglie in {cartella}")


def rgb_palette():
    """I 16 colori dei fondali in RGB a 8 bit (dal BGR555 del GBA)."""
    palette = G.S.carica("palette")
    out = []
    for rif in G.PALETTE_FONDALI:
        c = G.S.colore(palette, rif)
        out.append(((c & 31) * 255 // 31, ((c >> 5) & 31) * 255 // 31, ((c >> 10) & 31) * 255 // 31))
    return out


def fondale(cartella, nome, scala=1):
    """Il fondale intero di un'area, con i tile e i colori della ROM: fondale_<area>[_xN].png."""
    colori = rgb_palette()
    a = [x for x in aree_finali() if x["id"] == nome][0]
    w, h = a["larghezza"], a["altezza"]
    righe = []
    for y in range(h * 8):
        riga = []
        for x in range(w * 8):
            tile = a["tile"][a["indici"][(y // 8) * w + x // 8]]
            riga += [colori[tile[y % 8][x % 8]]] * scala
        righe += [riga] * scala
    suffisso = f"_x{scala}" if scala > 1 else ""
    png(os.path.join(cartella, f"fondale_{nome}{suffisso}.png"), w * 8 * scala, h * 8 * scala, righe)


def schermate(cartella, rom, battaglia=False):
    """Schermate dalla ROM compilata con GUBBIO_AVVIO=2: niente tasti simulati (finirebbero nella
    finestra attiva, se mGBA non ha il fuoco). mGBA gira a scala 1; a ogni riga "Istantanea N" del
    log la finestra si cattura con PrintWindow, che non ha bisogno del fuoco, e si tengono le ultime
    160 righe del client (sopra c'e' la barra dei menu)."""
    import ctypes
    from ctypes import wintypes
    user32, gdi32 = ctypes.windll.user32, ctypes.windll.gdi32
    user32.SetProcessDPIAware()

    class BIH(ctypes.Structure):
        _fields_ = [("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG), ("biHeight", wintypes.LONG),
                    ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                    ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG),
                    ("biYPelsPerMeter", wintypes.LONG), ("biClrUsed", wintypes.DWORD), ("biClrImportant", wintypes.DWORD)]

    def finestra(pid):
        trovate = []

        @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        def ciascuna(hwnd, _):
            q = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(q))
            if q.value == pid and user32.IsWindowVisible(hwnd):
                trovate.append(hwnd)
            return True
        user32.EnumWindows(ciascuna, 0)
        return trovate[0] if trovate else None

    def cattura(hwnd, percorso):
        r = wintypes.RECT()
        user32.GetClientRect(hwnd, ctypes.byref(r))
        w, h = r.right, r.bottom
        hdc = user32.GetDC(hwnd)
        mdc = gdi32.CreateCompatibleDC(hdc)
        bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
        gdi32.SelectObject(mdc, bmp)
        user32.PrintWindow(hwnd, mdc, 3)
        bi = BIH()
        bi.biSize, bi.biWidth, bi.biHeight, bi.biPlanes, bi.biBitCount = ctypes.sizeof(BIH), w, -h, 1, 32
        buf = ctypes.create_string_buffer(w * h * 4)
        gdi32.GetDIBits(mdc, bmp, 0, h, buf, ctypes.byref(bi), 0)
        gdi32.DeleteObject(bmp)
        gdi32.DeleteDC(mdc)
        user32.ReleaseDC(hwnd, hdc)
        raw = buf.raw
        x0 = (w - 240) // 2
        righe = [[(raw[(y * w + x) * 4 + 2], raw[(y * w + x) * 4 + 1], raw[(y * w + x) * 4]) for x in range(x0, x0 + 240)]
                 for y in range(h - 160, h)]
        png(percorso, 240, 160, righe)

    nomi = [] if battaglia else [a["id"] for a in aree_finali()]
    con_nome = []
    lavoro = tempfile.mkdtemp(prefix="gubbio-istantanee-")
    copia = os.path.join(lavoro, "rom.gba")
    shutil.copy(rom, copia)
    log = os.path.join(lavoro, "mgba.log")
    proc = subprocess.Popen([MGBA, "-1", "-l", "255", "-C", "logToFile=1", "-C", f"logFile={log}", copia])
    scattate = 0
    try:
        hwnd = None
        for _ in range(100):
            hwnd = finestra(proc.pid)
            if hwnd:
                break
            time.sleep(0.1)
        if not hwnd:
            raise SystemExit("[istantanee] la finestra di mGBA non si apre")
        letto, inizio, finito = 0, time.time(), False
        while time.time() - inizio < 300 and not finito:
            time.sleep(0.05)
            if not os.path.exists(log):
                continue
            with open(log, encoding="utf-8", errors="replace") as f:
                f.seek(letto)
                nuovo = f.read()
                letto = f.tell()
            for riga in nuovo.splitlines():
                if "Istantanea " in riga and "GBA Debug" in riga:
                    # "Istantanea N" (le aree, in ordine) o "Istantanea nome" (la battaglia)
                    parola = riga.split("Istantanea ", 1)[1].split()[0]
                    if not parola.isdigit():
                        cattura(hwnd, os.path.join(cartella, f"schermata_{parola}.png"))
                        con_nome.append(parola)
                    elif scattate < len(nomi):
                        cattura(hwnd, os.path.join(cartella, f"schermata_{nomi[scattate]}.png"))
                        scattate += 1
                if "Istantanee finite" in riga:
                    finito = True
    finally:
        proc.terminate()
    if scattate != len(nomi) or (battaglia and not con_nome):
        raise SystemExit(f"[istantanee] {scattate} schermate per {len(nomi)} aree (log in {log})")
    print(f"[istantanee] {len(nomi) + len(con_nome)} schermate in {cartella}")


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    cartella = argv[0]
    os.makedirs(cartella, exist_ok=True)
    griglie(cartella)
    for nome in [argv[i + 1] for i, v in enumerate(argv) if v == "--fondale"]:
        fondale(cartella, nome, int(os.environ.get("ISTANTANEE_SCALA", "1")))
    if "--rom" in argv:
        schermate(cartella, argv[argv.index("--rom") + 1])
    if "--battaglia" in argv:
        schermate(cartella, argv[argv.index("--battaglia") + 1], battaglia=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
