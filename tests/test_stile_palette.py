#!/usr/bin/env python3
"""Scelta 3: palette maestra in BGR555, notte come cambio di palette.

    python -m unittest tests.test_stile_palette
"""
import unittest

from _stile import S


class Palette(unittest.TestCase):
    def setUp(self):
        self.p = S.carica("palette")

    def test_palette_vera_conforme(self):
        self.assertEqual(S.controlla_palette(self.p), [])

    def test_42_colori_in_9_rampe(self):
        self.assertEqual(len(self.p["rampe"]), 9)
        self.assertEqual(sum(len(r["giorno"]) for r in self.p["rampe"]), 42)

    # --- prove negative: rimettere il difetto, il controllo deve accorgersene ---------------

    def test_negativa_colore_ritoccato_a_mano(self):
        g = S.guasta(self.p)
        g["rampe"][0]["giorno"][2] ^= 1
        self.assertIn("rampe di giorno non allineate ai parametri: rigenerare con genera.py",
                      S.controlla_palette(g))

    def test_negativa_parola_fuori_da_15_bit(self):
        g = S.guasta(self.p)
        g["rampe"][1]["notte"][0] = 0x8000
        self.assertTrue(any("non e' una parola BGR555" in e for e in S.controlla_palette(g)))

    def test_negativa_rampe_dritte(self):
        g = S.guasta(self.p)
        g["parametri"]["hue_shift_per_tono"] = 0
        g["rampe"] = S.calcola_palette(g["parametri"])
        self.assertIn("hue shifting diverso dai 10 gradi per tono della scelta 3", S.controlla_palette(g))

    def test_negativa_luce_che_non_cresce(self):
        # il difetto trovato nella palette della tavola: i due toni scuri del vermiglio
        # avevano la stessa luminosita' (55 e 53) con luce_min 0,30
        g = S.guasta(self.p)
        g["parametri"]["rampe"][2]["luce_min"] = 0.30
        g["rampe"] = S.calcola_palette(g["parametri"])
        self.assertIn("vermiglio comunale: la luminosita' non cresce lungo la rampa", S.controlla_palette(g))

    def test_negativa_notte_piu_chiara(self):
        g = S.guasta(self.p)
        g["parametri"]["notte"]["luce"] = 1.4
        g["rampe"] = S.calcola_palette(g["parametri"])
        self.assertTrue(any("notturno non piu' scuro" in e for e in S.controlla_palette(g)))


if __name__ == "__main__":
    unittest.main()
