"""La folla della citta' (pezzo VIVA): mondo/folla.json -> tools/genera_folla.py -> include/folla.h.
Regole: chi passa cammina solo su celle calpestabili, non attraversa gli NPC fermi, al massimo FOLLA_MAX figure per
area e fase, ogni area viva ha gente in ogni fase; figure a standard (A6 per i passanti, 2 fotogrammi per gli animali)."""
import copy
import json
import os
import sys
import unittest

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RADICE, "tools"))
import genera_folla as GF  # noqa: E402
import genera_storia as GS  # noqa: E402
import genera_mondo as G  # noqa: E402
import figure_popolo as FP  # noqa: E402

CORRENTI, PUNTI = GF.calcola()
AREE = GS.aree_del_mondo()
DATI = json.load(open(GF.DATI, encoding="utf-8"))


class Folla(unittest.TestCase):
    def test_header_aggiornato(self):
        self.assertEqual(open(GF.USCITA, encoding="utf-8").read(), GF.header(CORRENTI, PUNTI))

    def test_percorsi_calpestabili(self):
        for c in CORRENTI:
            a = AREE[c["area"]]
            for x, y in c["celle"]:
                self.assertFalse(GS.solida_nel_gioco(a["griglia"][y][x], G), f"{c['area']} {c['chi']} ({x}, {y})")
            for p, q in zip(c["celle"], c["celle"][1:]):
                self.assertEqual(abs(p[0] - q[0]) + abs(p[1] - q[1]), 1, f"{c['area']} {c['chi']}: salto")

    def test_nessuno_cammina_sopra_un_npc(self):
        fermi = GF.posti_fermi()
        for c in CORRENTI:
            for xy in fermi.get(c["area"], []):
                self.assertNotIn(tuple(xy), set(map(tuple, c["celle"])), f"{c['area']} {c['chi']} su {xy}")

    def test_al_massimo_folla_max(self):
        for area in AREE:
            for k, f in enumerate(GF.FASI):
                n = sum(c["quanti"] for c in CORRENTI if c["area"] == area and (c["fasi"] >> k) & 1)
                self.assertLessEqual(n, GF.FOLLA_MAX, f"{area} {f}")

    def test_ogni_area_della_citta_e_viva_in_ogni_fase(self):
        citta = {c["area"] for c in DATI["correnti"]}
        self.assertEqual(len(citta), 10)
        for area in citta:
            for k, f in enumerate(GF.FASI):
                self.assertTrue(any(c["area"] == area and (c["fasi"] >> k) & 1 for c in CORRENTI), f"{area} {f}")

    def test_niente_ceri_ne_divise_fuori_dalla_basilica(self):
        """Regola di Cioti: Ceri e divise solo dentro la basilica; la folla non ne porta."""
        for c in DATI["correnti"]:
            self.assertNotIn("cer", c["chi"])
            self.assertNotIn(c["area"], ("BASILICA", "BASILICA_INTERNO"))

    def test_figure_a_standard(self):
        for nome in FP.PASSANTI:
            self.assertEqual(len(FP.fotogrammi_passante(nome)), 18, nome)
        for nome in FP.ANIMALI:
            a, b = FP.animale(nome, 0), FP.animale(nome, 1)
            self.assertEqual((len(a), len(a[0])), (16, 16), nome)
            self.assertNotEqual(a, b, nome)

    def test_chi_viene_dai_varchi_sparisce(self):
        for c in CORRENTI:
            if c["animale"]:
                self.assertFalse(c["sparisce"])

    def _calcola_con(self, modifica):
        vecchio = GF.DATI
        dati = copy.deepcopy(DATI)
        modifica(dati)
        percorso = os.path.join(os.environ.get("TMPDIR", "/tmp"), "folla_negativa.json")
        json.dump(dati, open(percorso, "w", encoding="utf-8"))
        GF.DATI = percorso
        try:
            GF.calcola()
        finally:
            GF.DATI = vecchio
            os.remove(percorso)

    def test_negativa_troppa_gente(self):
        def piu(d):
            d["correnti"][0]["quanti"] = GF.FOLLA_MAX + 1
        with self.assertRaisesRegex(GF.ErroreFolla, "al massimo"):
            self._calcola_con(piu)

    def test_negativa_ancora_sconosciuta(self):
        def sbagliata(d):
            d["correnti"][1]["da"] = "torre_che_non_c_e"
        with self.assertRaisesRegex(GF.ErroreFolla, "ancora"):
            self._calcola_con(sbagliata)

    def test_negativa_figura_sconosciuta(self):
        def ignoto(d):
            d["correnti"][0]["chi"] = "drago"
        with self.assertRaisesRegex(GF.ErroreFolla, "non e' un passante"):
            self._calcola_con(ignoto)

    def test_negativa_animale_senza_giro(self):
        def senza(d):
            c = next(c for c in d["correnti"] if "giro" in c)
            del c["giro"]
            c["a"] = "varco A"
        with self.assertRaisesRegex(GF.ErroreFolla, "giro"):
            self._calcola_con(senza)


if __name__ == "__main__":
    unittest.main()
