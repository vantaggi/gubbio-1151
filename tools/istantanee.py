#!/usr/bin/env python3
"""Istantanee delle aree: come si vedono nel gioco e com'e' fatta la loro griglia.

    python tools/istantanee.py CARTELLA             # griglie e schermate
    python tools/istantanee.py CARTELLA --griglie   # solo le griglie, senza emulatore

Griglie (ovunque): per ogni area un PNG di 1 pixel per tile ingrandito x4, dalla griglia finale del
generatore (edifici di monumenti.json compresi), con suolo, strade, muri, facciate, portoni, varchi e
spawn in colori diversi: griglia_<area>.png.

Schermate (solo Windows, con mGBA 0.10): avvia la ROM gubbio1151.gba tenendo premuto R, che la mette
nel modo istantanee (src/istantanee.cpp): ogni area sullo spawn 0, una dopo l'altra. Per ogni riga
"Istantanea N" del log di mGBA preme il tasto dello scatto (F12, la scorciatoia predefinita di mGBA)
e alla fine rinomina i PNG 240x160 come schermata_<area>.png. Il tasto R e' quello della tastiera
configurata in mGBA: MGBA_TASTO_R (codice virtuale Windows, predefinito 0x45, la E).
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
    """Le aree nell'ordine di include/mondo.h, con gli edifici posati."""
    mondo = G.mondo_del_repo()
    aree = [G.leggi_area(n, t) for n, t in G.sorgenti_del_repo()]
    for a in aree:
        G.posa_edifici(a, mondo["monumenti"])
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


def schermate(cartella):
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    tasto_r = int(os.environ.get("MGBA_TASTO_R", "0x45"), 16)
    F12 = 0x7B

    def premi(vk, giu=True):
        user32.keybd_event(vk, 0, 0 if giu else 2, 0)

    def finestra(pid):
        trovate = []

        @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        def ciascuna(hwnd, _):
            p = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
            if p.value == pid and user32.IsWindowVisible(hwnd):
                trovate.append(hwnd)
            return True
        user32.EnumWindows(ciascuna, 0)
        return trovate[0] if trovate else None

    nomi = [a["id"] for a in aree_finali()]
    lavoro = tempfile.mkdtemp(prefix="gubbio-istantanee-")
    rom = os.path.join(lavoro, "rom.gba")
    shutil.copy(ROM, rom)
    log = os.path.join(lavoro, "mgba.log")
    proc = subprocess.Popen([MGBA, "-l", "255", "-C", "logToFile=1", "-C", f"logFile={log}",
                             "-C", f"screenshotPath={lavoro}", rom])
    try:
        hwnd = None
        for _ in range(100):
            hwnd = finestra(proc.pid)
            if hwnd:
                break
            time.sleep(0.1)
        if not hwnd:
            raise SystemExit("[istantanee] la finestra di mGBA non si apre")
        user32.SetForegroundWindow(hwnd)
        premi(tasto_r)
        # R si rilascia dopo l'avvio, ma il log si legge da subito: la prima area arriva presto.
        scattate, letto, inizio, r_premuto = 0, 0, time.time(), True
        while time.time() - inizio < 300:
            time.sleep(0.05)
            if r_premuto and time.time() - inizio > 1.5:
                premi(tasto_r, False)
                r_premuto = False
            if not os.path.exists(log):
                continue
            with open(log, encoding="utf-8", errors="replace") as f:
                f.seek(letto)
                nuovo = f.read()
                letto = f.tell()
            for riga in nuovo.splitlines():
                if "Istantanea " in riga and "GBA Debug" in riga:
                    user32.SetForegroundWindow(hwnd)
                    premi(F12)
                    time.sleep(0.05)
                    premi(F12, False)
                    scattate += 1
                if "Istantanee finite" in riga:
                    break
            else:
                continue
            break
        time.sleep(1)
    finally:
        proc.terminate()
    scatti = sorted(glob.glob(os.path.join(lavoro, "*.png")), key=os.path.getmtime)
    if len(scatti) != len(nomi):
        raise SystemExit(f"[istantanee] {len(scatti)} scatti per {len(nomi)} aree (log in {log})")
    for percorso, nome in zip(scatti, nomi):
        shutil.move(percorso, os.path.join(cartella, f"schermata_{nome}.png"))
    print(f"[istantanee] {len(nomi)} schermate in {cartella}")


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    cartella = argv[0]
    os.makedirs(cartella, exist_ok=True)
    griglie(cartella)
    if "--griglie" not in argv:
        schermate(cartella)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
