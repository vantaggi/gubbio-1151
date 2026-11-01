#!/usr/bin/env python3
"""
Validazione degli asset di graphics/ contro i vincoli hardware del GBA e le regole di Butano.
Ripreso dal prototipo (prototipo-v0), senza i controlli legati ai suoi asset (Ceri, font).

Prende gli errori che altrimenti compaiono come fallimento oscuro di `grit` a build time, o
come sprite storto a schermo, e li rende un test che si legge. In F0 graphics/ non ha ancora
asset del progetto: per questo il controllo e' provato anche su BMP costruiti apposta, che
devono essere respinti. Un controllo che non ha mai visto un errore non sa di funzionare.

    python tests/test_assets.py
"""

import json
import os
import struct
import tempfile
import unittest

GFX = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "graphics"))

# Misure OBJ legali del GBA: fuori da queste l'hardware non sa disegnare uno sprite.
MISURE_OBJ = {(8, 8), (16, 16), (32, 32), (64, 64),
              (16, 8), (32, 8), (32, 16), (64, 32),
              (8, 16), (8, 32), (16, 32), (32, 64)}

# Misure legali per un background regolare in Butano.
MISURE_BG = {(256, 256), (256, 512), (512, 256), (512, 512)}


def leggi_bmp(percorso):
    with open(percorso, "rb") as f:
        d = f.read(54)
    larghezza, altezza = struct.unpack("<ii", d[18:26])
    bpp = struct.unpack("<H", d[28:30])[0]
    return larghezza, abs(altezza), bpp


def problemi(percorso_bmp):
    """Elenco dei problemi di un BMP e del suo .json; vuoto se l'asset e' valido."""
    nome = os.path.basename(percorso_bmp)
    meta_path = percorso_bmp[:-4] + ".json"
    if not os.path.exists(meta_path):
        return [f"{nome} e' senza .json: grit lo ignorerebbe"]

    with open(meta_path, encoding="utf-8") as f:
        meta = json.load(f)
    larghezza, altezza, bpp = leggi_bmp(percorso_bmp)
    trovati = []

    # 4bpp = 16 colori, il budget di palette del progetto.
    if bpp != 4:
        trovati.append(f"{nome} e' a {bpp}bpp invece che a 4")

    # Senza bpp_mode Butano promuove in silenzio a 8bpp ogni BMP con piu' di 16 colori.
    if meta.get("bpp_mode") not in ("bpp_4", "bpp_4_auto", "bpp_8"):
        trovati.append(f"{nome}: bpp_mode assente o non riconosciuto")

    tipo = meta.get("type", "")
    if tipo == "sprite":
        if "height" not in meta:
            trovati.append(f"{nome}: sprite senza height dichiarata")
        altezza_frame = meta.get("height", altezza)
        if altezza % altezza_frame:
            trovati.append(f"{nome}: altezza {altezza} non multipla del fotogramma {altezza_frame}")
        if (larghezza, altezza_frame) not in MISURE_OBJ:
            trovati.append(f"{nome}: {larghezza}x{altezza_frame} non e' una misura OBJ legale")
    elif "bg" in tipo:
        if (larghezza, altezza) not in MISURE_BG:
            trovati.append(f"{nome}: {larghezza}x{altezza} non e' una misura di background valida")

    return trovati


def scrivi_bmp(percorso, larghezza, altezza, bpp, meta=None):
    """BMP minimo: basta l'intestazione, che e' l'unica parte che il controllo legge."""
    intestazione = (b"BM" + struct.pack("<IHHI", 54, 0, 0, 54) +
                    struct.pack("<IiiHHIIiiII", 40, larghezza, altezza, 1, bpp, 0, 0, 0, 0, 0, 0))
    with open(percorso, "wb") as f:
        f.write(intestazione)
    if meta is not None:
        with open(percorso[:-4] + ".json", "w", encoding="utf-8") as f:
            json.dump(meta, f)


class AssetDelProgettoTest(unittest.TestCase):

    def test_ogni_asset_di_graphics_e_valido(self):
        bmp = sorted(f for f in os.listdir(GFX) if f.endswith(".bmp")) if os.path.isdir(GFX) else []
        for nome in bmp:
            self.assertEqual(problemi(os.path.join(GFX, nome)), [])


class IlControlloSaFallireTest(unittest.TestCase):

    def setUp(self):
        self.cartella = tempfile.TemporaryDirectory()
        self.addCleanup(self.cartella.cleanup)

    def bmp(self, nome, *args, **kwargs):
        percorso = os.path.join(self.cartella.name, nome)
        scrivi_bmp(percorso, *args, **kwargs)
        return percorso

    def test_asset_valido_accettato(self):
        p = self.bmp("ok.bmp", 16, 32, 4, {"type": "sprite", "height": 16, "bpp_mode": "bpp_4"})
        self.assertEqual(problemi(p), [])

    def test_senza_json(self):
        self.assertIn("senza .json", problemi(self.bmp("a.bmp", 16, 16, 4))[0])

    def test_8bpp(self):
        p = self.bmp("b.bmp", 16, 16, 8, {"type": "sprite", "height": 16, "bpp_mode": "bpp_4"})
        self.assertTrue(any("8bpp" in m for m in problemi(p)))

    def test_bpp_mode_assente(self):
        p = self.bmp("c.bmp", 16, 16, 4, {"type": "sprite", "height": 16})
        self.assertTrue(any("bpp_mode" in m for m in problemi(p)))

    def test_sprite_di_misura_illegale(self):
        p = self.bmp("d.bmp", 24, 24, 4, {"type": "sprite", "height": 24, "bpp_mode": "bpp_4"})
        self.assertTrue(any("OBJ" in m for m in problemi(p)))

    def test_sprite_senza_height(self):
        p = self.bmp("e.bmp", 16, 16, 4, {"type": "sprite", "bpp_mode": "bpp_4"})
        self.assertTrue(any("height" in m for m in problemi(p)))

    def test_background_di_misura_illegale(self):
        p = self.bmp("f.bmp", 240, 160, 4, {"type": "regular_bg", "bpp_mode": "bpp_4"})
        self.assertTrue(any("background" in m for m in problemi(p)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
