"""Gli edifici della storia v2 (pezzo SV2b2): le botteghe e le case delle schede degli amici, nel
censimento come edifici inventati (ruolo storia_v2), posati nelle loro aree su isolati di case con la via
davanti, disegnati dal pittore coi segni del mestiere; gli amici che ci lavorano stanno davanti.
"""
import csv
import importlib.util
import os
import sys
import unittest

from _stile import RADICE

sys.path.insert(0, os.path.join(RADICE, "tools"))
import genera_mondo as G  # noqa: E402
import pittore_monumenti as PM  # noqa: E402

_spec = importlib.util.spec_from_file_location("genera_storia", os.path.join(RADICE, "tools", "genera_storia.py"))
GS = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(GS)

EDIFICI = {"casa_medico": ("san_martino", "insegna"), "bottega_carradore": ("piazza_quaranta_martiri", "ruote"),
           "spezieria": ("san_pietro", "portico"), "taverna": ("san_pietro", "frasca"),
           "bottega_conti": ("sant_agostino", "congegno"), "calcara": ("sant_agostino", "bocca"),
           "banco_montano": ("via_dei_consoli", "tenda")}
CENSIMENTO = {r["id"]: r for r in csv.DictReader(open(os.path.join(RADICE, "mondo", "fonti", "censimento_osm.csv"),
                                                      encoding="utf-8"))}


def aree_preparate():
    mondo = G.mondo_del_repo()
    out = {}
    for n, t in G.sorgenti_del_repo():
        a = G.leggi_area(n, t)
        G.prepara_area(a, mondo)
        out[a["id"]] = a
    return out


class Edifici(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.aree = aree_preparate()

    def test_nel_censimento_come_inventati(self):
        for mid, (area, _) in EDIFICI.items():
            r = CENSIMENTO[mid]
            self.assertEqual((r["area"], r["ruolo"], r["osm_stato"]), (area, "storia_v2", "inventato"), mid)
        self.assertNotIn("mulino", " ".join(CENSIMENTO))                     # il carradore al posto del mulino

    def test_posati_su_case_con_la_via_davanti(self):
        for mid, (area, _) in EDIFICI.items():
            a = self.aree[area]
            self.assertIn(mid, a["edifici"], mid)
            x0, y0, w, h = a["edifici"][mid]
            sorgente = next(G.leggi_area(n, t) for n, t in G.sorgenti_del_repo() if n.endswith(f"/{area}.area")
                            or n.endswith(f"\\{area}.area") or n == f"{area}.area")
            celle = [sorgente["griglia"][y][x] for y in range(y0, y0 + h) for x in range(x0, x0 + w)]
            ammessi = set("#.NrTuk") if mid == "calcara" else {"#"}
            self.assertTrue(set(celle) <= ammessi, mid)
            intorno = [sorgente["griglia"][y][x] for y in range(max(0, y0 - 1), min(a["altezza"], y0 + h + 1))
                       for x in range(max(0, x0 - 1), min(a["larghezza"], x0 + w + 1))]
            self.assertTrue(any(not G.solida(c) for c in intorno), mid)

    def test_negativa_un_edificio_sulla_via_si_vede(self):
        g = ["#####", "#,,,#", "#####"]
        self.assertFalse({g[1][x] for x in range(1, 4)} <= {"#"})

    def test_i_segni_del_mestiere(self):
        for mid, (_, segno) in EDIFICI.items():
            t = PM.dipingi(mid, CENSIMENTO[mid]["nome"], 8, 6, "basso", {}, 0)
            self.assertGreater(t.elementi[segno], 0, mid)

    def test_negativa_una_casa_qualunque_non_ha_il_segno(self):
        t = PM.generico("x", "Casa qualunque", 8, 6, "basso", 0)
        self.assertEqual(t.elementi["ruote"] + t.elementi["frasca"] + t.elementi["tenda"], 0)

    def test_gli_amici_davanti_alla_loro_bottega(self):
        for chi, amico in GS.AMICI.items():
            tipo, _, nome = amico["ancora"].partition(" ")
            if tipo != "edificio":
                continue
            area = EDIFICI[nome][0]
            a = self.aree[area]
            punto = GS.punto_dell_ancora(a, amico["ancora"], G)
            x0, y0, w, h = a["edifici"][nome]
            self.assertLessEqual(max(abs(punto[0] - (x0 + w // 2)), abs(punto[1] - (y0 + h))), 2, chi)

    def test_negativa_senza_bottega_l_ancora_e_l_ingresso(self):
        a = dict(self.aree["san_pietro"], edifici={})
        self.assertEqual(GS.punto_dell_ancora(a, "edificio spezieria", G), a["spawn"][0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
