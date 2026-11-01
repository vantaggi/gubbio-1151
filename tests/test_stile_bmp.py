#!/usr/bin/env python3
"""BMP 4bpp per grit generati da stile/genera_bmp.py: allineati ai dati, rileggibili senza
perdite, misure legali per il GBA (stesso controllo di test_assets.py).

    python -m unittest tests.test_stile_bmp
"""
import os
import tempfile
import unittest

from _stile import S, RADICE
import genera_bmp as G
from test_assets import problemi

GRAPHICS = os.path.join(RADICE, "graphics")


class BmpDiStile(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.attesi = G.file_attesi()
        cls.immagini = G.immagini()

    def test_graphics_allineata_ai_dati(self):
        for nome, contenuto in self.attesi.items():
            percorso = os.path.join(GRAPHICS, nome)
            self.assertTrue(os.path.exists(percorso), f"manca {nome}: lanciare stile/genera_bmp.py")
            with open(percorso, "rb") as f:
                self.assertEqual(f.read(), contenuto, f"{nome} non allineato: lanciare stile/genera_bmp.py")

    def test_rilettura_esatta_dei_colori(self):
        # grit porta i canali a 5 bit con >> 3: i colori in ROM devono essere le parole BGR555
        for nome, (colori, _) in self.immagini.items():
            w, h, indici, palette = G.leggi_bmp_4bpp(self.attesi[nome + ".bmp"])
            self.assertEqual((w, h), (len(colori[0]), len(colori)), nome)
            for y in range(h):
                for x in range(w):
                    atteso = colori[y][x]
                    i = indici[y][x]
                    if atteso is None:
                        self.assertEqual(i, 0, f"{nome} {x},{y}: il trasparente deve essere l'indice 0")
                    else:
                        self.assertNotEqual(i, 0, f"{nome} {x},{y}: pixel opaco sull'indice 0")
                        self.assertEqual(palette[i], atteso, f"{nome} {x},{y}")

    def test_misure_e_json_legali_per_butano(self):
        with tempfile.TemporaryDirectory() as d:
            for nome, contenuto in self.attesi.items():
                with open(os.path.join(d, nome), "wb") as f:
                    f.write(contenuto)
            for nome in self.attesi:
                if nome.endswith(".bmp"):
                    self.assertEqual(problemi(os.path.join(d, nome)), [], nome)

    def test_ritratti_tre_fotogrammi_nell_ordine_delle_espressioni(self):
        rt, p = S.carica("ritratti"), S.carica("palette")
        colori, meta = self.immagini["ritratto_ubaldo"]
        self.assertEqual(meta["height"], 32)
        for k, e in enumerate(rt["espressioni"]):
            img, _ = S.componi_ritratto(rt, p, "Ubaldo", e)
            self.assertEqual(colori[32 * k:32 * (k + 1)], img, e)

    def test_disposizione_rispettata(self):
        c = S.carica("cornice")["disposizione"]["dialogo"]
        colori, _ = self.immagini["cornice_dialogo"]
        self.assertIsNone(colori[c["y"] - 1 - 8 - 1][c["x"]])          # sopra il cartiglio: vuoto
        self.assertIsNotNone(colori[c["y"] + 8 * c["righe"] - 1][c["x"] + 8 * c["colonne"] - 1])

    # --- prove negative ------------------------------------------------------------------

    def test_negativa_bmp_ritoccato_a_mano(self):
        nome = "ritratto_ubaldo.bmp"
        rovinato = bytearray(self.attesi[nome])
        rovinato[-1] ^= 0x11
        self.assertNotEqual(bytes(rovinato), G.file_attesi()[nome])

    def test_negativa_troppi_colori(self):
        colori = [[i for i in range(17)] + [None] * 7]
        with self.assertRaises(ValueError):
            G.indicizza(colori)

    def test_negativa_palette_oltre_16(self):
        with self.assertRaises(ValueError):
            G.bmp_4bpp(8, 8, [[0] * 8] * 8, list(range(17)))

    def test_negativa_misura_non_multipla_di_8(self):
        with self.assertRaises(ValueError):
            G.bmp_4bpp(12, 8, [[0] * 12] * 8, [0])

    def test_negativa_rilettura_vede_un_pixel_cambiato(self):
        indici = [[0] * 8 for _ in range(8)]
        indici[3][5] = 2
        _, _, letti, _ = G.leggi_bmp_4bpp(G.bmp_4bpp(8, 8, indici, [G.TRASPARENTE, 1, 2]))
        self.assertEqual(letti, indici)
        indici[3][5] = 1
        self.assertNotEqual(letti, indici)

    def test_negativa_colore_che_perde_bit(self):
        # scrivere il canale a 8 bit con la scala *255//31 darebbe lo stesso risultato; uno
        # scritto male (v << 2) no: la rilettura deve accorgersene
        dati = bytearray(G.bmp_4bpp(8, 8, [[1] * 8] * 8, [G.TRASPARENTE, 0x7FFF]))
        dati[54 + 4] = 31 << 2
        _, _, _, palette = G.leggi_bmp_4bpp(bytes(dati))
        self.assertNotEqual(palette[1], 0x7FFF)

    def test_negativa_sprite_di_misura_illegale(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x.bmp")
            with open(p, "wb") as f:
                f.write(G.bmp_4bpp(24, 24, [[0] * 24] * 24, [0]))
            with open(p[:-4] + ".json", "w") as f:
                f.write('{"type": "sprite", "height": 24, "bpp_mode": "bpp_4"}')
            self.assertTrue(any("OBJ" in m for m in problemi(p)))


if __name__ == "__main__":
    unittest.main()
