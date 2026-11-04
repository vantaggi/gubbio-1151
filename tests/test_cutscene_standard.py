"""Le cutscene allo STANDARD_GRAFICO (/mnt/project-files/stile_dati/STANDARD_GRAFICO.md): le regole che si
contano su ogni piano dei copioni di regia, con tools/controlla_cutscene.py. Ognuna ha la sua negativa.

- P3: pochi pixel orfani nei fondali (le luci, i riflessi e le stelle sono esenti);
- L1: le chiome del bosco (pennelli.chioma) hanno la luce in alto a sinistra e l'ombra in basso a destra;
- F2/C4: nella vetrata il quasi nero non e' piu' tutto il muro: intorno alla finestra ci sono i conci.
"""
import importlib.util
import os
import sys
import unittest

from _stile import RADICE

sys.path.insert(0, os.path.join(RADICE, "tools"))
sys.path.insert(0, os.path.join(RADICE, "stile"))

_spec = importlib.util.spec_from_file_location("controlla_cutscene", os.path.join(RADICE, "tools", "controlla_cutscene.py"))
CC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(CC)

from genera_battaglia import Tela  # noqa: E402
import pennelli  # noqa: E402

ORFANI_MAX = 200            # per piano di fondale, sul quadro visibile 512x112: il prima era fino a 3149


class CutsceneStandard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.misure = [CC.misura(p) for p in CC.piani_usati()]

    def test_fondali_senza_pixel_orfani(self):
        for m in self.misure:
            if not m["figura"]:
                self.assertLessEqual(m["orfani"], ORFANI_MAX, f"{m['piano']}: {m['orfani']} pixel orfani (P3)")

    def test_negativa_il_retino_a_puntini_e_orfano(self):
        t = Tela(64, 64, 2)
        for y in range(1, 63, 3):
            for x in range(1, 63, 3):
                t.punto(x, y, 3)
        self.assertGreater(CC.orfani(t.px, {0}), 300)

    def test_negativa_la_scacchiera_non_e_orfana(self):
        t = Tela(32, 32, 2)
        for y in range(32):
            for x in range(32):
                if (x + y) % 2:
                    t.punto(x, y, 3)
        self.assertEqual(CC.orfani(t.px, {0}), 0)

    def chioma(self):
        t = Tela(20, 16)
        pennelli.chioma(t, 9, 7, 5, 4, 3, 2, 1)
        return t

    def test_chioma_luce_in_alto_a_sinistra(self):
        t = self.chioma()
        luce = [(x, y) for y in range(t.h) for x in range(t.w) if t.px[y][x] == 3]
        ombra = [(x, y) for y in range(t.h) for x in range(t.w) if t.px[y][x] == 1]
        self.assertTrue(luce and ombra)
        self.assertLess(sum(x for x, _ in luce) / len(luce), sum(x for x, _ in ombra) / len(ombra))
        self.assertLess(sum(y for _, y in luce) / len(luce), sum(y for _, y in ombra) / len(ombra))

    def test_negativa_chioma_rovesciata(self):
        t = self.chioma()
        for riga in t.px:
            riga.reverse()
        luce = [x for riga in t.px for x, c in enumerate(riga) if c == 3]
        ombra = [x for riga in t.px for x, c in enumerate(riga) if c == 1]
        self.assertGreater(sum(luce) / len(luce), sum(ombra) / len(ombra))

    def test_la_vetrata_ha_i_conci_intorno(self):
        m = next(m for m in self.misure if m["piano"] == "vetrata")
        self.assertLess(m["nero"], 0.7, "il muro intorno alla vetrata e' tutto nero (F2, C4)")


if __name__ == "__main__":
    unittest.main()
