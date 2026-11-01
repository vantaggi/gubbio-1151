#!/usr/bin/env python3
"""Scelta 12: logo 'GUBBIO 1151' in capitali lombarde, oro a due toni con riflesso e contorno.

    python -m unittest tests.test_stile_logo
"""
import unittest

from _stile import S


class Logo(unittest.TestCase):
    def setUp(self):
        self.l = S.carica("logo")
        self.p = S.carica("palette")

    def test_logo_vero_conforme(self):
        self.assertEqual(S.controlla_logo(self.l, self.p), [])

    def test_sottotitolo_nel_font_nostro(self):
        self.assertEqual(S.caratteri_mancanti(S.carica("font"), self.l["sottotitolo"]), [])

    # --- prove negative ------------------------------------------------------------------

    def test_negativa_lettera_mancante(self):
        g = S.guasta(self.l)
        del g["glifi"]["B"]
        self.assertIn("manca la lettera lombarda 'B'", S.controlla_logo(g, self.p))

    def test_negativa_logo_troppo_largo(self):
        g = S.guasta(self.l)
        g["scala_titolo"] = 3
        self.assertTrue(any("non sta nei 240" in e for e in S.controlla_logo(g, self.p)))

    def test_negativa_contorno_nero_puro(self):
        g = S.guasta(self.l)
        g["colori"]["contorno"] = ["neutri", 0]
        self.assertTrue(any("quasi nero" in e for e in S.controlla_logo(g, self.p)))

    def test_negativa_oro_preso_da_altra_rampa(self):
        g = S.guasta(self.l)
        g["colori"]["basso"] = ["cotto e coppi", 3]
        self.assertTrue(any("oro e bronzo" in e for e in S.controlla_logo(g, self.p)))

    def test_negativa_lettere_di_altezze_diverse(self):
        g = S.guasta(self.l)
        g["glifi"]["I"] = g["glifi"]["I"][:11]
        self.assertIn("lettere di altezze diverse", S.controlla_logo(g, self.p))


if __name__ == "__main__":
    unittest.main()
