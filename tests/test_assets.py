#!/usr/bin/env python3
"""
Validazione degli asset di graphics/ contro i vincoli hardware del GBA e le regole di Butano.

Prende gli errori che altrimenti compaiono solo come fallimento oscuro di `grit` a build time,
o peggio come sprite storto a schermo, e li rende un test che si legge.

    python tests/test_assets.py
"""

import json
import os
import struct
import unittest

GFX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "graphics")

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


class AssetTest(unittest.TestCase):

    def setUp(self):
        self.root = os.path.normpath(GFX)
        self.bmp = sorted(f for f in os.listdir(self.root) if f.endswith(".bmp"))
        self.assertTrue(self.bmp, "graphics/ non contiene alcun .bmp")

    def test_ogni_bmp_ha_il_suo_json(self):
        for nome in self.bmp:
            atteso = os.path.join(self.root, nome[:-4] + ".json")
            self.assertTrue(os.path.exists(atteso), f"{nome} e' senza .json: grit lo ignorerebbe")

    def test_profondita_a_4_bit(self):
        """Butano vuole BMP indicizzati; 4bpp = 16 colori, il budget di palette del progetto."""
        for nome in self.bmp:
            _, _, bpp = leggi_bmp(os.path.join(self.root, nome))
            self.assertEqual(bpp, 4, f"{nome} e' a {bpp}bpp invece che a 4")

    def test_misure_sprite_legali(self):
        """Uno sprite con misure fuori tabella non e' disegnabile dall'hardware."""
        for nome in self.bmp:
            meta_path = os.path.join(self.root, nome[:-4] + ".json")
            if not os.path.exists(meta_path):
                continue
            meta = json.load(open(meta_path, encoding="utf-8"))
            if meta.get("type") != "sprite":
                continue

            larghezza, altezza, _ = leggi_bmp(os.path.join(self.root, nome))
            # Un foglio a piu' fotogrammi dichiara l'altezza del singolo fotogramma.
            altezza_frame = meta.get("height", altezza)
            self.assertEqual(altezza % altezza_frame, 0,
                             f"{nome}: altezza {altezza} non e' multipla del fotogramma {altezza_frame}")
            self.assertIn((larghezza, altezza_frame), MISURE_OBJ,
                          f"{nome}: {larghezza}x{altezza_frame} non e' una misura OBJ legale")

    def test_misure_background_legali(self):
        for nome in self.bmp:
            meta_path = os.path.join(self.root, nome[:-4] + ".json")
            if not os.path.exists(meta_path):
                continue
            meta = json.load(open(meta_path, encoding="utf-8"))
            if "bg" not in meta.get("type", ""):
                continue
            larghezza, altezza, _ = leggi_bmp(os.path.join(self.root, nome))
            self.assertIn((larghezza, altezza), MISURE_BG,
                          f"{nome}: {larghezza}x{altezza} non e' una misura di background valida")

    def test_bpp_mode_sempre_esplicito(self):
        """Senza `bpp_mode`, `butano_graphics_tool.py` promuove SILENZIOSAMENTE a 8bpp ogni BMP
        con piu' di 16 colori: tile da 32 a 64 byte e, per un background, uso della palette a
        256 colori — cioe' tutti e 16 i banchi. Oggi gli asset sono 4bpp per fortuna (sono
        segnaposto piatti), non per garanzia: il campo va dichiarato, e questo test lo esige."""
        for nome in self.bmp:
            meta_path = os.path.join(self.root, nome[:-4] + ".json")
            if not os.path.exists(meta_path):
                continue
            with open(meta_path, encoding="utf-8") as f:
                meta = json.load(f)
            self.assertIn("bpp_mode", meta,
                          f"{nome[:-4]}.json non dichiara bpp_mode: promozione silenziosa a 8bpp")
            self.assertIn(meta["bpp_mode"], ("bpp_4", "bpp_4_auto", "bpp_8"),
                          f"{nome[:-4]}.json: bpp_mode '{meta['bpp_mode']}' non riconosciuto")

    def test_misure_dei_ceri_conformi_al_gdd(self):
        """Sezione 23A GDD: Giorgio 32x32, Ubaldo e Antonio 16x32. La Sez. 28B li contraddice
        (dice 24x32 / 32x48): finche' la contraddizione non e' sciolta, vale la 23A."""
        attese = {"giorgio.bmp": (32, 32), "ubaldo.bmp": (16, 32), "antonio.bmp": (16, 32)}
        for nome, misura in attese.items():
            percorso = os.path.join(self.root, nome)
            if not os.path.exists(percorso):
                continue
            larghezza, altezza, _ = leggi_bmp(percorso)
            self.assertEqual((larghezza, altezza), misura,
                             f"{nome} non rispetta la Sez. 23A del GDD")


if __name__ == "__main__":
    unittest.main(verbosity=2)
