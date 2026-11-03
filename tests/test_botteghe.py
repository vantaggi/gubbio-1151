"""SV2b3: le botteghe della storia v2 si riconoscono dalla vista di gioco (insegna grande e oggetti)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import pittore_monumenti as PM  # noqa: E402

MISURE = {"casa_medico": (8, 6, "basso"), "bottega_carradore": (10, 6, "sinistra"), "spezieria": (9, 6, "basso"),
          "taverna": (7, 5, "basso"), "bottega_conti": (8, 5, "destra"), "calcara": (5, 5, "basso"),
          "banco_montano": (4, 2, "basso")}


def colorati(t):
    return sum(1 for riga in t.px for c in riga if c != PM.COTTO)


class Botteghe(unittest.TestCase):
    def test_ogni_bottega_ha_i_suoi_segni(self):
        for mid, (w, h, f) in MISURE.items():
            t = PM.PITTORI[mid](w, h, {"faccia": f})
            self.assertGreaterEqual(t.segni, PM.SEGNI_MINIMI, mid)
            self.assertEqual(t.elementi["insegna_grande"], 1, mid)

    def test_negativa_i_pittori_di_prima(self):
        for mid, (w, h, f) in MISURE.items():
            t = PM.BOTTEGHE_BASE[mid](w, h, {"faccia": f})
            self.assertEqual(getattr(t, "segni", 0), 0, mid)
            self.assertEqual(t.elementi["insegna_grande"], 0, mid)

    def test_i_segni_cambiano_davvero_il_disegno(self):
        for mid, (w, h, f) in MISURE.items():
            prima = PM.BOTTEGHE_BASE[mid](w, h, {"faccia": f}).px
            dopo = PM.PITTORI[mid](w, h, {"faccia": f}).px
            diversi = sum(a != b for ra, rb in zip(prima, dopo) for a, b in zip(ra, rb))
            self.assertGreaterEqual(diversi, PM.SEGNI_MINIMI // 2, mid)

    def test_restano_nei_bordi(self):
        for mid, (w, h, f) in MISURE.items():
            t = PM.PITTORI[mid](w, h, {"faccia": f})
            self.assertEqual((len(t.px), len(t.px[0])), (h * 8, w * 8), mid)


if __name__ == "__main__":
    unittest.main()
