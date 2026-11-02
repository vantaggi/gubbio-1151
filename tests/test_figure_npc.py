"""Le figure degli NPC d'ambiente (pezzo S): tools/figure_npc.py e la tabella FIGURA_NPC di storia.h.

Cinque figure 16x16 diverse fra loro e dal giocatore, con la palette dei popolani; ogni NPC del copione
prende la figura dal mestiere scritto nel suo nome, e tutte e cinque si usano.
"""
import importlib.util
import os
import sys
import unittest

from _stile import RADICE

sys.path.insert(0, os.path.join(RADICE, "tools"))
import figure_npc as FN  # noqa: E402

_spec = importlib.util.spec_from_file_location("genera_storia", os.path.join(RADICE, "tools", "genera_storia.py"))
GS = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(GS)
_spec_m = importlib.util.spec_from_file_location("genera_mondo", os.path.join(RADICE, "tools", "genera_mondo.py"))
GM = importlib.util.module_from_spec(_spec_m)
_spec_m.loader.exec_module(GM)

_, NPC = GS.leggi_copione()


def sagoma(righe):
    return tuple(tuple(c != "." for c in r) for r in righe)


class FigureNpc(unittest.TestCase):

    def test_cinque_figure_16x16_con_la_palette(self):
        self.assertEqual(sorted(FN.FIGURE), sorted(FN.ORDINE))
        self.assertEqual(len(FN.ORDINE), 5)
        for nome, righe in FN.FIGURE.items():
            self.assertEqual(len(righe), 16, nome)
            self.assertTrue(all(len(r) == 16 for r in righe), nome)
            self.assertTrue(set("".join(righe)) <= set(".0123456789abcdef"), nome)
            self.assertIn("1", "".join(righe), nome)                      # il contorno

    def test_figure_diverse_fra_loro_e_dal_giocatore(self):
        """Ogni figura si riconosce gia' dalla sagoma (il contorno), non solo dai colori."""
        sagome = {sagoma(r) for r in FN.FIGURE.values()}
        self.assertEqual(len(sagome), 5)
        self.assertNotIn(sagoma(GM.GIOCATORE), sagome)

    def test_negativa_due_figure_con_la_stessa_sagoma(self):
        doppie = [FN.FIGURE["popolana"], [r.replace("4", "a") for r in FN.FIGURE["popolana"]]]
        self.assertEqual(len({sagoma(r) for r in doppie}), 1)

    def test_ogni_npc_ha_la_figura_del_suo_mestiere(self):
        figure = {p["nome"]: FN.figura_di(p["nome"]) for p in NPC}
        self.assertEqual(set(figure.values()), set(FN.ORDINE))
        self.assertEqual(figure["Popolana"], "popolana")
        self.assertEqual(figure["Frate agostiniano"], "frate")
        self.assertEqual(figure["Canonico"], "frate")
        self.assertEqual(figure["Cecco il Balestriere"], "soldato")
        self.assertEqual(figure["Sentinella di Porta Romana"], "soldato")
        self.assertEqual(figure["Merciaio"], "mercante")
        self.assertEqual(figure["Vecchio sulla scalinata"], "anziano")

    def test_negativa_nome_senza_mestiere(self):
        with self.assertRaisesRegex(ValueError, "nessuna figura"):
            FN.figura_di("Un tale")

    def test_la_tabella_del_gioco(self):
        h = open(os.path.join(RADICE, "include", "storia.h"), encoding="utf-8").read()
        self.assertIn(f"inline constexpr int FIGURE_NPC = {len(FN.ORDINE)};", h)
        for p in NPC:
            riga = next(r for r in h.splitlines() if r.endswith("// " + p["nome"]))
            self.assertTrue(riga.rstrip().split("//")[0].rstrip().endswith(f", {FN.ORDINE.index(FN.figura_di(p['nome']))} }},"),
                            p["nome"])
        parole = FN.parole("frate")
        self.assertIn(", ".join(f"0x{v:08X}" for v in parole[:8]), h)

    def test_negativa_parole_di_un_altra_figura(self):
        self.assertNotEqual(FN.parole("frate"), FN.parole("soldato"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
