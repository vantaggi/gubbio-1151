#!/usr/bin/env python3
"""Istantanee delle aree: come si vedono nel gioco e com'e' fatta la loro griglia.

    python tools/istantanee.py CARTELLA                      # solo le griglie
    python tools/istantanee.py CARTELLA --rom ROM_ISTANTANEE  # griglie e schermate

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
    """Le aree nell'ordine di include/mondo.h, con gli edifici posati e il dislivello."""
    mondo = G.mondo_del_repo()
    aree = [G.leggi_area(n, t) for n, t in G.sorgenti_del_repo()]
    for a in aree:
        G.posa_edifici(a, mondo["monumenti"])
        G.applica_dislivello(a, mondo["grafo"])
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


def schermate(cartella, rom):
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

    nomi = [a["id"] for a in aree_finali()]
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
                if "Istantanea " in riga and "GBA Debug" in riga and scattate < len(nomi):
                    cattura(hwnd, os.path.join(cartella, f"schermata_{nomi[scattate]}.png"))
                    scattate += 1
                if "Istantanee finite" in riga:
                    finito = True
    finally:
        proc.terminate()
    if scattate != len(nomi):
        raise SystemExit(f"[istantanee] {scattate} schermate per {len(nomi)} aree (log in {log})")
    print(f"[istantanee] {len(nomi)} schermate in {cartella}")


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    cartella = argv[0]
    os.makedirs(cartella, exist_ok=True)
    griglie(cartella)
    if "--rom" in argv:
        schermate(cartella, argv[argv.index("--rom") + 1])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
