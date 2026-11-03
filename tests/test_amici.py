"""Gli amici del copione v2 (pezzo SV2b): copione/05_npc_amici.md, dati/amici.json, tools/figure_npc.py.

Ogni amico ha il suo nome a schermo, la sua figura (base piu' accessorio, o una figura nuova), sta nella
sua area vicino all'ancora della scheda, e quelli del borgo di Sant'Agostino hanno il posto in
Sant'Andrea per quando il borgo e' dentro le mura.
"""
import importlib.util
import os
import re
import sys
import unittest

from _stile import RADICE

sys.path.insert(0, os.path.join(RADICE, "tools"))
import figure_npc as FN  # noqa: E402

_spec = importlib.util.spec_from_file_location("genera_storia", os.path.join(RADICE, "tools", "genera_storia.py"))
GS = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(GS)

SCENE, NPC = GS.leggi_copione()
AMICI = [p for p in NPC if p.get("amico")]
STORIA_H = open(GS.USCITA_H, encoding="utf-8").read()
TESTI = open(os.path.join(RADICE, "testi", "copione.testi"), encoding="utf-8").read()


def riga(nome):
    return next(r for r in STORIA_H.splitlines() if r.endswith("// " + nome))


def campi(nome):
    m = re.search(r"\{ int8_t\(mondo::AreaId::(\w+)\), (\d+), (\d+), \{[^}]*\}, \{[^}]*\}, (\d+), (\d+), (\d+), (\d+), (\d+), "
                  r"(true|false) \}", riga(nome))
    return m.groups()


def altezza(righe):
    piene = [i for i, r in enumerate(righe) if r.strip(".")]
    return max(piene) - min(piene) + 1


class Amici(unittest.TestCase):

    def test_ogni_amico_della_scheda_con_nome_e_voce(self):
        self.assertEqual(len(AMICI), len(GS.AMICI))
        for p in AMICI:
            self.assertIn(p["amico"], GS.AMICI)
            self.assertRegex(TESTI, rf"(?m)^{GS.id_parlante(p['amico'])}\s+\| HUD\s+\| {re.escape(GS.AMICI[p['amico']]['nome'])}$")

    def test_negativa_parlante_senza_dati(self):
        finto = {"nome": "Sconosciuto", "frasi": [GS.battuta("SCONOSCIUTO", None, "x", "x")]}
        with self.assertRaisesRegex(GS.ErroreStoria, "senza voce in dati/amici.json"):
            GS.parlante_dell_amico(finto)

    def test_figure_diverse_e_le_due_nuove(self):
        figure = [tuple(GS.figura_dell_npc(p)) for p in AMICI]
        self.assertEqual(len(set(figure)), len(figure))
        base = altezza(FN.figura_composta("mercante", None))
        self.assertGreater(altezza(FN.figura_composta("gabrione", None)), base)
        self.assertLess(altezza(FN.figura_composta("bambino", None)), base)
        gabrione = FN.figura_composta("gabrione", None)
        testa = next(r for r in gabrione if r.strip("."))
        self.assertNotIn("d", testa + gabrione[gabrione.index(testa) + 1])           # pelato: niente cappello

    def test_negativa_l_accessorio_si_vede(self):
        self.assertNotEqual(FN.figura_composta("soldato", "balestra"), FN.figura_composta("soldato", None))

    def test_nella_sua_area_vicino_all_ancora(self):
        sys.path.insert(0, os.path.join(RADICE, "tools"))
        import genera_mondo as G
        mondo = G.mondo_del_repo()
        aree = {}
        for n, t in G.sorgenti_del_repo():
            a = G.leggi_area(n, t)
            G.prepara_area(a, mondo)
            aree[a["id"].upper()] = a
        lontani = []
        for p in AMICI:
            area, tx, ty = campi(p["nome"])[:3]
            self.assertEqual(area, p["area"], p["nome"])
            ancora = GS.AMICI[p["amico"]]["ancora"]
            ax, ay = GS.punto_dell_ancora(aree[area], ancora, G)
            if max(abs(int(tx) - ax), abs(int(ty) - ay)) > 30:
                lontani.append(p["nome"])
        # Masio: la Porta Metauro e' sul bordo, in una striscia stretta (vedi la nota della PR)
        self.assertLessEqual(set(lontani), {"Masio il Romano"})

    def test_quelli_del_borgo_hanno_il_posto_in_sant_andrea(self):
        for p in AMICI:
            borgo = campi(p["nome"])[-1] == "true"
            self.assertEqual(borgo, bool(GS.AMICI[p["amico"]].get("borgo")), p["nome"])
        self.assertEqual(campi("Andreuccio")[-1], "false")                              # resta sempre fuori

    def test_negativa_fuori_dal_borgo_niente_posto(self):
        self.assertEqual(campi("Giordano")[-3:], ("0", "0", "false"))

    def test_le_note_imposta(self):
        rufino = next(p for p in AMICI if p["amico"] == "RUFINO")
        self.assertEqual(GS.TUTTE[rufino["imposta"]], "RUFINO_ASCOLTATO")
        self.assertEqual(rufino["imposta_fasi"], 1 << GS.FASI.index("DIGIUNO"))
        ricciardo = next(p for p in AMICI if p["amico"] == "RICCIARDO")
        self.assertEqual(ricciardo["imposta_fasi"], 7)                                # una qualunque sua battuta

    def test_prova_del_borgo_in_cpp(self):
        codice = open(os.path.join(RADICE, "src", "storia_scena.cpp"), encoding="utf-8").read()
        self.assertIn("n.del_borgo && accesa(g_game_state, Bandiera::BORGO_DENTRO) && fase_npc(g_game_state) != Fase::ULTIMATUM",
                      codice)


if __name__ == "__main__":
    unittest.main(verbosity=2)
