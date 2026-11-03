#!/usr/bin/env python3
"""I ritratti del dialogo di Ubaldo, Giorgio, Antonio e Guido (tools/pittore_ritratti.py):
dato allineato al pittore, un ritratto per ogni parlante del copione che usa le espressioni,
solo colori della palette bloccata, luce da sinistra, BMP pronti per grit.

    python -m unittest tests.test_ritratti_eroi
"""
import copy
import os
import sys
import unittest

from _stile import S, RADICE

sys.path.insert(0, os.path.join(RADICE, "tools"))
import pittore_ritratti as PR  # noqa: E402

COPIONE = os.path.join(RADICE, "copione")
GRAPHICS = os.path.join(RADICE, "graphics")


def colori_palette(p):
    return {c for r in p["rampe"] for c in r["giorno"]}


class RitrattiEroi(unittest.TestCase):
    def setUp(self):
        self.rt = S.carica("ritratti")
        self.p = S.carica("palette")

    def test_dato_allineato_al_pittore(self):
        self.assertEqual(PR.dati_attesi(self.rt), self.rt,
                         "stile/dati/ritratti.json non allineato: lanciare tools/pittore_ritratti.py")

    def test_conformi_alla_scelta_10(self):
        self.assertEqual(S.controlla_ritratti(self.rt, self.p), [])

    def test_ogni_parlante_con_espressione_ha_il_ritratto(self):
        parlanti = PR.parlanti_con_espressione(COPIONE)
        self.assertEqual(parlanti, {n.upper() for n in PR.CON_RITRATTO})
        self.assertEqual(PR.controlla_copertura(self.rt, parlanti), [])

    def test_solo_colori_della_palette_bloccata(self):
        ammessi = colori_palette(self.p)
        for nome in PR.CON_RITRATTO:
            for e in self.rt["espressioni"]:
                img, _ = S.componi_ritratto(self.rt, self.p, nome, e)
                usati = {c for r in img for c in r if c is not None}
                self.assertLessEqual(usati, ammessi, f"{nome}/{e}")
                self.assertLessEqual(len(usati), 15, f"{nome}/{e}")

    def test_luce_da_sinistra_negli_strati_nuovi(self):
        self.assertEqual(PR.controlla_luce(PR.STRATI), [])

    def test_quattro_facce_diverse(self):
        calmi = [str(S.componi_ritratto(self.rt, self.p, n, "calmo")[0]) for n in PR.CON_RITRATTO]
        self.assertEqual(len(set(calmi)), 4)

    def test_espressioni_toccano_solo_il_viso(self):
        x0, y0, x1, y1 = self.rt["zona_espressione"]
        for nome in PR.CON_RITRATTO:
            base, _ = S.componi_ritratto(self.rt, self.p, nome, "calmo")
            for e in ("preoccupato", "deciso"):
                img, _ = S.componi_ritratto(self.rt, self.p, nome, e)
                diversi = [(x, y) for y in range(32) for x in range(32) if img[y][x] != base[y][x]]
                self.assertTrue(diversi, f"{nome}/{e} uguale a calmo")
                # il contorno puo' allargarsi di un pixel attorno alla zona del viso
                for x, y in diversi:
                    self.assertTrue(x0 - 1 <= x <= x1 + 1 and y0 - 1 <= y <= y1 + 1, f"{nome}/{e} {x},{y}")

    def test_bmp_per_grit_dei_quattro(self):
        for nome in PR.CON_RITRATTO:
            for est in (".bmp", ".json"):
                self.assertTrue(os.path.exists(os.path.join(GRAPHICS, "ritratto_" + nome.lower() + est)),
                                f"manca ritratto_{nome.lower()}{est}: lanciare stile/genera_bmp.py")

    # --- prove negative ------------------------------------------------------------------

    def test_negativa_dato_ritoccato_a_mano(self):
        g = S.guasta(self.rt)
        g["personaggi"]["Giorgio"]["colori"]["X"] = ["verde dei monti", 2]
        self.assertNotEqual(PR.dati_attesi(g), g)

    def test_negativa_parlante_senza_ritratto(self):
        g = S.guasta(self.rt)
        del g["personaggi"]["Guido"]
        err = PR.controlla_copertura(g, {"UBALDO", "GUIDO"})
        self.assertIn("GUIDO parla con espressione ma non ha ritratto", err)
        self.assertIn("manca il ritratto di Guido", err)

    def test_negativa_colore_fuori_palette(self):
        g = S.guasta(self.rt)
        g["personaggi"]["Antonio"]["colori"]["B"] = ["porpora", 0]
        self.assertTrue(any("fuori palette" in e for e in S.controlla_ritratti(g, self.p)))

    def test_negativa_tono_inventato_in_una_rampa(self):
        g = S.guasta(self.rt)
        g["personaggi"]["Guido"]["colori"]["K"] = ["vermiglio comunale", 7]
        self.assertTrue(any("fuori palette" in e for e in S.controlla_ritratti(g, self.p)))

    def test_negativa_ombra_a_sinistra(self):
        strati = copy.deepcopy(PR.STRATI)
        righe = strati["capelli"]["ciuffo"]
        strati["capelli"]["ciuffo"] = {y: r.replace("C", "x").replace("c", "C").replace("x", "c")
                                       for y, r in righe.items()}
        self.assertTrue(any("ciuffo" in e for e in PR.controlla_luce(strati)))

    def test_negativa_riga_storta(self):
        with self.assertRaises(ValueError):
            PR.maschera({3: "..."})


if __name__ == "__main__":
    unittest.main()
