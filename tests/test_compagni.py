"""I compagni in fila sulla mappa (tools/sagome_compagni.py -> include/compagni.h): l'header e' aggiornato, le figure
hanno il formato del giocatore (16x32, 3 direzioni x 8 fotogrammi, i piedi alla riga 31 con l'ombra) e il motore
li tiene sulle orme di Ubaldo."""
import os
import sys
import unittest

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RADICE, "tools"))
import sagome_compagni as SC  # noqa: E402
import sagome_mappa as SM  # noqa: E402


class Compagni(unittest.TestCase):
    def test_header_aggiornato(self):
        self.assertEqual(open(SC.USCITA, encoding="utf-8").read(), SC.header())

    def test_formato_del_giocatore(self):
        for chi in SC.COMPAGNI:
            fot = SC.fotogrammi(chi)
            self.assertEqual(len(fot), len(SM.DIREZIONI) * SM.FOTOGRAMMI, chi)
            for i, g in enumerate(fot):
                self.assertEqual((len(g), len(g[0])), (32, 16), f"{chi} {i}")
                self.assertTrue(any(g[31]), f"{chi} {i}: niente alla riga 31 (M1)")
                self.assertIn(SC.SINGOLI[chi]["ombra"], g[31], f"{chi} {i}: senza ombra (L4)")

    def test_palette_da_16(self):
        for chi in SC.COMPAGNI:
            self.assertEqual(len(SC.PALETTE[chi]), 16, chi)

    def test_la_fila_e_nella_storia(self):
        storia = open(os.path.join(RADICE, "src", "storia_scena.cpp"), encoding="utf-8").read()
        self.assertIn("imposta_compagni", storia)
        self.assertIn("GIORGIO_NEL_GRUPPO", storia)


if __name__ == "__main__":
    unittest.main()
