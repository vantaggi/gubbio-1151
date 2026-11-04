"""F8: gli obiettivi del bilanciamento (docs/bilanciamento.md) con tools/bilanciamento.py."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import bilanciamento as B  # noqa: E402

VECCHIA_ESPERIENZA = [15, 25, 200, 12, 30, 0, 0]  # prima di F8 (i nemici di F10 non c'erano): a Corrado al livello 3


class Bilanciamento(unittest.TestCase):
    def test_livelli_lungo_la_storia(self):
        self.assertEqual(B.livelli_lungo_la_storia(), {0: 1, 1: 3, 3: 4, 4: 5, 2: 5})
        # con le tre quest e tutte le facoltative (le guardie delle fornaci, l'infiltrato): 6, mai 7
        self.assertEqual(B.livelli_lungo_la_storia(con_quest=True)[2], 6)

    def test_negativa_facoltative_troppo_generose(self):
        # se una guardia della fornace desse quanto un Fante (35), con tutto si arriverebbe a Corrado al 7
        xp = B.leggi_tabella("ESPERIENZA_NEMICO")
        xp[5] = 35
        self.assertEqual(B.livelli_lungo_la_storia(xp, con_quest=True)[2], 7)
        self.assertEqual(B.livelli_lungo_la_storia(xp)[2], 5, "senza quest le facoltative non contano")

    def test_negativa_guerrieri_troppo_generosi(self):
        # se i Guerrieri di B-03 dessero 80 ciascuno, senza quest si arriverebbe a Corrado al 6
        xp = B.leggi_tabella("ESPERIENZA_NEMICO")
        xp[5] = 80
        self.assertEqual(B.livelli_lungo_la_storia(xp)[2], 6)

    def test_facoltative_al_livello_piu_basso(self):
        for i, liv in B.LIVELLO_FACOLTATIVI.items():
            for p in ("forte", "medio"):
                v, r = B.misura(i, liv, p, semi=100)
                self.assertGreaterEqual(v, 90, (i, p))
                self.assertTrue(3 <= r <= 6, (i, p, r))

    def test_negativa_vecchia_esperienza(self):
        self.assertEqual(B.livelli_lungo_la_storia(VECCHIA_ESPERIENZA)[2], 3)

    def test_scontri_normali(self):
        for i in (0, 1, 3, 4):
            liv = B.livelli_lungo_la_storia()[i]
            for p in ("forte", "medio"):
                v, r = B.misura(i, liv, p, semi=100, ceri=i in B.DOPO_I_CERI)
                self.assertGreaterEqual(v, 90, (i, p))
                self.assertTrue(3 <= r <= 6, (i, p, r))

    def test_corrado_al_livello_atteso(self):
        """A Corrado si arriva dopo il rito di A1-08: coi Ceri risvegliati (DOPO_I_CERI)."""
        self.assertIn(2, B.DOPO_I_CERI)
        senza = B.misura(2, B.livelli_lungo_la_storia()[2], "medio", ceri=True)[0]
        con = B.misura(2, B.livelli_lungo_la_storia(con_quest=True)[2], "medio", scudo_meno=1, ceri=True)[0]
        self.assertTrue(55 <= senza <= 75, senza)
        self.assertTrue(55 <= con <= 80, con)

    def test_i_ceri_aiutano_poco(self):
        """I Ceri alzano la percentuale di Corrado al livello atteso, ma di poco (non piu' di 5 punti)."""
        liv = B.livelli_lungo_la_storia()[2]
        senza, con = B.misura(2, liv, "medio")[0], B.misura(2, liv, "medio", ceri=True)[0]
        self.assertTrue(0 < con - senza <= 5, (senza, con))

    def test_negativa_ceri_spenti(self):
        """Con FERVORE_CERI a 0 la manopola non fa niente: la differenza misurata sopra viene dai Ceri."""
        vecchio = B.M.FERVORE_CERI
        liv = B.livelli_lungo_la_storia()[2]
        try:
            B.M.FERVORE_CERI = 0
            con = B.misura(2, liv, "medio", ceri=True)
        finally:
            B.M.FERVORE_CERI = vecchio
        self.assertEqual(con, B.misura(2, liv, "medio"))

    def test_negativa_corrado_troppo_presto(self):
        self.assertLess(B.misura(2, 3, "medio")[0], 55)
        self.assertLess(B.misura(2, 3, "medio", ceri=True)[0], 55, "i Ceri non bastano a battere Corrado al 3")

    def test_corrado_non_si_vince_con_un_solo_comando(self):
        for liv in range(1, 9):
            self.assertEqual(B.misura(2, liv, "debole", semi=50)[0], 0, liv)
            self.assertEqual(B.misura(2, liv, "debole", semi=50, ceri=True)[0], 0, liv)

    def test_lo_scudo_in_meno_aiuta(self):
        liv = B.livelli_lungo_la_storia()[2]
        self.assertGreater(B.misura(2, liv, "medio", scudo_meno=1)[0], B.misura(2, liv, "medio")[0])


if __name__ == "__main__":
    unittest.main()
