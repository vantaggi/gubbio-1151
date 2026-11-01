#!/usr/bin/env python3
"""Scelta 9: cornice a vetrata in tile 8x8, composta a 9-slice.

    python -m unittest tests.test_stile_cornice
"""
import unittest

from _stile import S


class Cornice(unittest.TestCase):
    def setUp(self):
        self.c = S.carica("cornice")
        self.p = S.carica("palette")

    def test_cornice_vera_conforme(self):
        self.assertEqual(S.controlla_cornice(self.c, self.p), [])

    def test_angoli_con_flip_hardware(self):
        m = S.componi_cornice(self.c, 30, 7)
        self.assertEqual([m[0][0], m[0][-1], m[-1][0], m[-1][-1]],
                         [("angolo", False, False), ("angolo", True, False),
                          ("angolo", False, True), ("angolo", True, True)])

    def test_disposizione_sullo_schermo(self):
        d = self.c["disposizione"]
        for nome in ("dialogo", "menu"):
            r = d[nome]
            self.assertEqual(r["x"] % 8 + r["y"] % 8, 0, f"{nome} non allineato ai tile")
            self.assertLessEqual(r["x"] + 8 * r["colonne"], 240, nome)
            self.assertLessEqual(r["y"] + 8 * r["righe"], 160, nome)
        dia = d["dialogo"]
        self.assertEqual(dia["y"] + 8 * dia["righe"], 160, "il dialogo sta in basso")
        self.assertEqual(dia["colonne"], 30, "il dialogo prende tutta la larghezza")
        self.assertGreaterEqual(d["menu"]["x"], 120, "il menu sta a destra")
        self.assertLess(d["menu"]["y"], 80, "il menu sta in alto")
        # 3 righe di testo a interlinea 10 nel vano interno del dialogo
        self.assertGreaterEqual((dia["righe"] - 2) * 8, dia["righe_testo_max"] * 10)
        menu = d["menu"]
        self.assertGreaterEqual((menu["righe"] - 2) * 8, menu["voci_max"] * menu["passo_voci"])

    def test_negativa_menu_troppo_basso(self):
        g = S.guasta(self.c)
        g["disposizione"]["menu"]["righe"] = 5
        menu = g["disposizione"]["menu"]
        self.assertLess((menu["righe"] - 2) * 8, menu["voci_max"] * menu["passo_voci"])

    def test_meno_di_tre_tile_rifiutato(self):
        with self.assertRaises(ValueError):
            S.componi_cornice(self.c, 2, 5)

    # --- prove negative ------------------------------------------------------------------

    def test_negativa_piombo_interrotto(self):
        g = S.guasta(self.c)
        g["tile"]["oriz_1"][0] = "11131111"
        self.assertTrue(any("piombo esterno interrotto" in e for e in S.controlla_cornice(g, self.p)))

    def test_negativa_filo_interno_interrotto(self):
        g = S.guasta(self.c)
        g["tile"]["vert_0"][3] = "16666662"
        self.assertTrue(any("filo di piombo interno" in e for e in S.controlla_cornice(g, self.p)))

    def test_negativa_riflesso_dalla_parte_sbagliata(self):
        g = S.guasta(self.c)
        t = g["tile"]["oriz_0"]
        t[2] = t[1]
        t[6] = "3333323" + "1"
        self.assertTrue(any("riflesso non in alto a sinistra" in e for e in S.controlla_cornice(g, self.p)))

    def test_negativa_fondo_trasparente(self):
        g = S.guasta(self.c)
        g["tile"]["centro"][4] = "22220222"
        err = S.controlla_cornice(g, self.p)
        self.assertTrue(any("fondo interno non uniforme" in e for e in err))
        self.assertTrue(any("pixel trasparenti" in e for e in err))

    def test_negativa_colore_fuori_palette(self):
        g = S.guasta(self.c)
        g["colori"][4] = ["oro e bronzo", 9]
        self.assertTrue(any("non e' nella palette" in e for e in S.controlla_cornice(g, self.p)))

    def test_negativa_indice_senza_colore(self):
        g = S.guasta(self.c)
        g["tile"]["centro"][0] = "2222222f"
        self.assertTrue(any("usa l'indice 15" in e for e in S.controlla_cornice(g, self.p)))

    def test_negativa_tessere_vicine_uguali(self):
        g = S.guasta(self.c)
        g["regole"]["lato_orizzontale"] = ["oriz_0", "oriz_0", "oriz_2"]
        self.assertIn("lato_orizzontale: due tessere vicine dello stesso colore",
                      S.controlla_cornice(g, self.p))


if __name__ == "__main__":
    unittest.main()
