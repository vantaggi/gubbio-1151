#!/usr/bin/env python3
"""Scelta 11: scheletro delle pose (camminata 6 x 6 vblank, riposo 2 x 30, attacco in 5 pose).

    python -m unittest tests.test_stile_pose
"""
import unittest

from _stile import S


class Pose(unittest.TestCase):
    def setUp(self):
        self.s = S.carica("pose")

    def test_pose_vere_conformi(self):
        self.assertEqual(S.controlla_pose(self.s), [])

    def test_camminata_dura_600_ms(self):
        f = self.s["animazioni"]["camminata"]["fotogrammi"]
        self.assertEqual(sum(x["vblank"] for x in f) * 1000 // 60, 600)

    # --- prove negative ------------------------------------------------------------------

    def test_negativa_camminata_a_4_fotogrammi(self):
        g = S.guasta(self.s)
        f = g["animazioni"]["camminata"]["fotogrammi"]
        g["animazioni"]["camminata"]["fotogrammi"] = [dict(x, vblank=8) for x in f[:4]]
        self.assertTrue(any(e.startswith("camminata: durate") for e in S.controlla_pose(g)))

    def test_negativa_colpo_lento(self):
        g = S.guasta(self.s)
        g["animazioni"]["attacco"]["fotogrammi"][2]["vblank"] = 10
        err = S.controlla_pose(g)
        self.assertIn("attacco: il colpo deve essere la posa piu' breve", err)

    def test_negativa_sinistra_disegnata(self):
        g = S.guasta(self.s)
        g["direzioni"].append("sinistra")
        self.assertTrue(any("sinistra = destra specchiata" in e for e in S.controlla_pose(g)))

    def test_negativa_personaggio_in_volo(self):
        g = S.guasta(self.s)
        gi = g["animazioni"]["riposo"]["fotogrammi"][0]["giunti"]["destra"]
        gi["piede_a"][1] -= 2
        gi["piede_b"][1] -= 2
        self.assertTrue(any("nessun piede a terra" in e for e in S.controlla_pose(g)))

    def test_negativa_giunto_fuori_sprite(self):
        g = S.guasta(self.s)
        g["animazioni"]["camminata"]["fotogrammi"][0]["giunti"]["giu"]["mano_a"][0] = 16
        self.assertTrue(any("fuori dal corpo" in e for e in S.controlla_pose(g)))

    def test_negativa_scatto_nella_camminata(self):
        g = S.guasta(self.s)
        g["animazioni"]["camminata"]["fotogrammi"][2]["giunti"]["destra"]["piede_b"][0] += 4
        self.assertTrue(any("salto di" in e for e in S.controlla_pose(g)))

    def test_negativa_testa_che_balla(self):
        g = S.guasta(self.s)
        g["animazioni"]["camminata"]["fotogrammi"][1]["giunti"]["su"]["testa"][1] -= 2
        self.assertTrue(any("la testa oscilla" in e for e in S.controlla_pose(g)))

    def test_negativa_colpo_senza_scia(self):
        g = S.guasta(self.s)
        del g["animazioni"]["attacco"]["fotogrammi"][2]["scia"]
        self.assertIn("attacco: il colpo porta la scia", S.controlla_pose(g))


if __name__ == "__main__":
    unittest.main()
