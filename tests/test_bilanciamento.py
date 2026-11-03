"""F8: gli obiettivi del bilanciamento (docs/bilanciamento.md) con tools/bilanciamento.py."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import bilanciamento as B  # noqa: E402

VECCHIA_ESPERIENZA = [15, 25, 200, 12, 30]      # prima di F8: a Corrado si arrivava al livello 3


class Bilanciamento(unittest.TestCase):
    def test_livelli_lungo_la_storia(self):
        self.assertEqual(B.livelli_lungo_la_storia(), {0: 1, 1: 3, 3: 4, 2: 5})
        self.assertEqual(B.livelli_lungo_la_storia(con_quest=True)[2], 6)

    def test_negativa_vecchia_esperienza(self):
        self.assertEqual(B.livelli_lungo_la_storia(VECCHIA_ESPERIENZA)[2], 3)

    def test_scontri_normali(self):
        for i in (0, 1, 3):
            liv = B.livelli_lungo_la_storia()[i]
            for p in ("forte", "medio"):
                v, r = B.misura(i, liv, p, semi=100)
                self.assertGreaterEqual(v, 90, (i, p))
                self.assertTrue(3 <= r <= 6, (i, p, r))

    def test_corrado_al_livello_atteso(self):
        senza = B.misura(2, B.livelli_lungo_la_storia()[2], "medio")[0]
        con = B.misura(2, B.livelli_lungo_la_storia(con_quest=True)[2], "medio", scudo_meno=1)[0]
        self.assertTrue(55 <= senza <= 75, senza)
        self.assertTrue(55 <= con <= 80, con)

    def test_negativa_corrado_troppo_presto(self):
        self.assertLess(B.misura(2, 3, "medio")[0], 55)

    def test_corrado_non_si_vince_con_un_solo_comando(self):
        for liv in range(1, 9):
            self.assertEqual(B.misura(2, liv, "debole", semi=50)[0], 0, liv)

    def test_lo_scudo_in_meno_aiuta(self):
        liv = B.livelli_lungo_la_storia()[2]
        self.assertGreater(B.misura(2, liv, "medio", scudo_meno=1)[0], B.misura(2, liv, "medio")[0])


if __name__ == "__main__":
    unittest.main()
