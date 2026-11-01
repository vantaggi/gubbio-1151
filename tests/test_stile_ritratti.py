#!/usr/bin/env python3
"""Scelta 10: ritratti 32x32 a strati, 3 espressioni che cambiano solo sopracciglia e bocca.

    python -m unittest tests.test_stile_ritratti
"""
import unittest

from _stile import S


class Ritratti(unittest.TestCase):
    def setUp(self):
        self.r = S.carica("ritratti")
        self.p = S.carica("palette")

    def test_ritratti_veri_conformi(self):
        self.assertEqual(S.controlla_ritratti(self.r, self.p), [])

    def test_ogni_personaggio_ha_tre_espressioni_32x32(self):
        for nome in self.r["personaggi"]:
            for e in self.r["espressioni"]:
                img, _ = S.componi_ritratto(self.r, self.p, nome, e)
                self.assertEqual((len(img), len(img[0])), (32, 32))

    # --- prove negative ------------------------------------------------------------------

    def test_negativa_espressione_che_tocca_la_veste(self):
        g = S.guasta(self.r)
        m = g["strati"]["bocca"]["deciso"]
        m[29] = m[29][:5] + "n" + m[29][6:]
        self.assertTrue(any("fuori dalla zona del viso" in e for e in S.controlla_ritratti(g, self.p)))

    def test_negativa_espressioni_identiche(self):
        g = S.guasta(self.r)
        for s in ("sopracciglia", "bocca"):
            g["strati"][s]["deciso"] = g["strati"][s]["calmo"]
        self.assertTrue(any("due espressioni identiche" in e for e in S.controlla_ritratti(g, self.p)))

    def test_negativa_ombra_dal_lato_della_luce(self):
        g = S.guasta(self.r)
        p = g["personaggi"]["Giovane"]["colori"]
        p["V"], p["v"] = p["v"], p["V"]
        self.assertTrue(any("non e' piu' scura" in e for e in S.controlla_ritratti(g, self.p)))

    def test_negativa_ombra_disegnata_a_sinistra(self):
        g = S.guasta(self.r)
        m = g["strati"]["veste"]["tunica"]
        g["strati"]["veste"]["tunica"] = [r.replace("V", "x").replace("v", "V").replace("x", "v") for r in m]
        self.assertTrue(any("non sta a destra" in e for e in S.controlla_ritratti(g, self.p)))

    def test_negativa_bocca_fuori_dal_viso(self):
        g = S.guasta(self.r)
        m = g["strati"]["bocca"]["calmo"]
        m[27] = m[27][:5] + "b" + m[27][6:]
        self.assertTrue(any("fuori dalla zona del viso" in e for e in S.controlla_ritratti(g, self.p)))

    def test_negativa_colore_fuori_palette(self):
        g = S.guasta(self.r)
        g["personaggi"]["Soldato"]["colori"]["V"] = ["porpora", 1]
        self.assertTrue(any("fuori palette" in e for e in S.controlla_ritratti(g, self.p)))

    def test_negativa_strato_non_32x32(self):
        g = S.guasta(self.r)
        g["strati"]["occhi"]["base"] = g["strati"]["occhi"]["base"][:31]
        self.assertIn("strato occhi/base: non e' 32x32", S.controlla_ritratti(g, self.p))

    def test_negativa_quarta_espressione_nella_veste(self):
        g = S.guasta(self.r)
        g["strati_espressione"].append("veste")
        self.assertIn("le espressioni devono cambiare solo sopracciglia e bocca",
                      S.controlla_ritratti(g, self.p))

    def test_negativa_troppi_colori_per_4bpp(self):
        g = S.guasta(self.r)
        m = g["strati"]["veste"]["tunica"]
        extra = {}
        for i, (rampa, tono) in enumerate([("cielo e acqua", t) for t in range(5)] +
                                         [("cotto e coppi", t) for t in range(4)]):
            extra[chr(ord("0") + i)] = [rampa, tono]
        g["ruoli_fissi"].update(extra)
        m[27] = "...012345678" + m[27][12:]
        self.assertTrue(any("uno sprite 4bpp ne tiene 15" in e for e in S.controlla_ritratti(g, self.p)))

    def test_negativa_ruolo_senza_colore(self):
        g = S.guasta(self.r)
        del g["personaggi"]["Giovane"]["colori"]["C"]
        self.assertTrue(any("ruoli di colore senza valore ['C']" in e for e in S.controlla_ritratti(g, self.p)))


if __name__ == "__main__":
    unittest.main()
