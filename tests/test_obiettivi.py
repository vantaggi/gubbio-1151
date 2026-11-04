"""MOB: le righe OBIETTIVO del copione diventano la tabella OBIETTIVO[] di include/storia.h, con l'area meta
(menu/PROPOSTA.md sez. 5): il Luogo della prima scena che segue nel copione, oppure «(area: ID)» scritta a mano in
fondo alla riga. L'annotazione non va mai a schermo. Prove negative: un'annotazione su una riga che non e'
OBIETTIVO, un'area che il mondo non ha, un obiettivo senza scene dopo e senza annotazione.
"""
import importlib.util
import os
import re
import sys
import unittest

from _stile import RADICE

sys.path.insert(0, os.path.join(RADICE, "tools"))
import genera_storia as GS  # noqa: E402

_spec = importlib.util.spec_from_file_location("verifica_copione", os.path.join(RADICE, "copione", "verifica_copione.py"))
VC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(VC)


def leggi(*parti):
    with open(os.path.join(RADICE, *parti), encoding="utf-8") as f:
        return f.read()


SCENE, _NPC = GS.leggi_copione()
QUEST = GS.leggi_le_quest()
RIGHE = GS.obiettivi(SCENE, QUEST)
STORIA_H = leggi("include", "storia.h")


class Tabella(unittest.TestCase):

    def test_nove_della_cronaca_e_tre_degli_incarichi(self):
        self.assertEqual(sum(1 for r in RIGHE if r["quest"] < 0), 9)
        self.assertEqual(sorted(r["quest"] for r in RIGHE if r["quest"] >= 0), [0, 1, 2])
        self.assertIn(f"inline constexpr int OBIETTIVI = {len(RIGHE)};", STORIA_H)

    def test_le_righe_del_header(self):
        for r in RIGHE:
            self.assertIn(f"{{ testi::TestoId::{r['testo']}, int8_t(mondo::AreaId::{r['area']}), {r['quest']}, {r['scena']} }},",
                          STORIA_H)

    def test_meta_dalla_scena_che_segue(self):
        codici = [s["codice"] for s in SCENE]
        mete = {SCENE[r["scena"]]["codice"]: r["area"] for r in RIGHE if r["quest"] < 0}
        # scritte a mano: A1-01 (la scena dopo e' via dei Consoli, facoltativa), A1-05 (il borgo, facoltativo)
        self.assertEqual(mete["A1-01"], "TEATRO_ROMANO")
        self.assertEqual(mete["A1-05"], "DUOMO_DUCALE")
        # le altre: il Luogo (AREE) della prima scena dopo con un'area
        for codice in ("A1-03", "A1-04", "A1-07", "A1-09", "B-04", "B-05"):
            dopo = next(c for c in codici[codici.index(codice) + 1:] if GS.AREE[c])
            self.assertEqual(mete[codice], GS.AREE[dopo], codice)

    def test_meta_degli_incarichi(self):
        for r in RIGHE:
            if r["quest"] >= 0:
                self.assertEqual(r["area"], GS.QUEST[r["quest"]]["obiettivo"])

    def test_l_annotazione_non_va_a_schermo(self):
        self.assertIn("(area: TEATRO_ROMANO)", leggi("copione", "01_atto_I.md"))
        for testo in (leggi("testi", "copione.testi"), leggi("include", "testi.h"), STORIA_H):
            self.assertNotIn("(area:", testo)
        frasi = [r["frase"] for r in RIGHE]
        self.assertIn("Raggiungi il Teatro Romano, fuori dalle mura di San Martino.", frasi)

    def test_verifica_copione_misura_senza_annotazione(self):
        p = os.path.join(RADICE, "copione", "01_atto_I.md")
        obiettivi = [t for _, chi, _, t in VC.battute(p) if chi == "OBIETTIVO"]
        self.assertIn("Sali al Monte Ingino passando dal Duomo.", obiettivi)
        self.assertFalse(any("(area:" in t for t in obiettivi))


class Negative(unittest.TestCase):

    def test_annotazione_su_una_riga_che_non_e_obiettivo(self):
        with self.assertRaises(GS.ErroreStoria):
            GS.battuta("SISTEMA", None, "Premi A. (area: PIAZZA_GRANDE)", "prova:1")
        b = GS.battuta("OBIETTIVO", None, "Vai. (area: PIAZZA_GRANDE)", "prova:1")
        self.assertEqual((b["frase"], b["meta"]), ("Vai.", "PIAZZA_GRANDE"))

    def test_area_che_il_mondo_non_ha(self):
        scene = [dict(s) for s in SCENE]
        k = next(i for i, s in enumerate(scene) if s["codice"] == "A1-03")
        battute = list(scene[k]["battute"])
        j = next(i for i, b in enumerate(battute) if b["chi"] == "OBIETTIVO")
        battute[j] = GS.battuta("OBIETTIVO", None, "Vai. (area: TEATRO_GRECO)", "prova:1")
        scene[k]["battute"] = battute
        with self.assertRaisesRegex(GS.ErroreStoria, "TEATRO_GRECO"):
            GS.obiettivi(scene, QUEST)

    def test_obiettivo_nell_ultima_scena_senza_annotazione(self):
        scene = [dict(s) for s in SCENE]
        scene[-1]["battute"] = list(scene[-1]["battute"]) + [GS.battuta("OBIETTIVO", None, "Guarda.", "prova:1")]
        with self.assertRaisesRegex(GS.ErroreStoria, "senza area meta"):
            GS.obiettivi(scene, QUEST)
        scene[-1]["battute"][-1] = GS.battuta("OBIETTIVO", None, "Guarda. (area: BASILICA)", "prova:1")
        self.assertEqual(GS.obiettivi(scene, QUEST)[-4]["area"], "BASILICA")

    def test_il_cartiglio_nel_gioco(self):
        self.assertTrue(re.search(r"^ETICHETTA_OBIETTIVO\s*\| HUD\s*\| Obiettivo$", leggi("testi", "partita.testi"), re.M))
        self.assertIn("segna_obiettivo(g_game_state, b);", leggi("src", "storia_scena.cpp"))
        self.assertIn("storia::dopo_il_caricamento(gubbio::g_game_state);", leggi("src", "main.cpp"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
