"""Il motore di regia delle cutscene (F7, pezzo U): tools/genera_regia.py e i copioni regia/*.regia.

Le regole della proposta approvata, ognuna con la negativa: nessuna cutscene oltre i 60 s, nelle
bande parla solo il NARRATORE in al massimo 2 righe da 224 px (il contesto NARRATORE di testi.h,
misurato da tools/genera_testi.py), Start salta tutto e A avanza (provati a tempo di compilazione
in src/autotest_regia.cpp, qui si controlla che ci siano), i piani con la palette bloccata.
"""
import importlib.util
import os
import unittest

from _stile import RADICE, S

_spec = importlib.util.spec_from_file_location("genera_regia", os.path.join(RADICE, "tools", "genera_regia.py"))
GR = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(GR)

_spec_t = importlib.util.spec_from_file_location("genera_testi", os.path.join(RADICE, "tools", "genera_testi.py"))
GT = importlib.util.module_from_spec(_spec_t)
_spec_t.loader.exec_module(GT)

PALETTE = S.carica("palette")
PROVA = "cutscene CX | prova\ninquadratura {secondi} | cielo monti | 12\nnarratore {battuta}\n"


class Regia(unittest.TestCase):

    def test_header_aggiornato(self):
        with open(GR.USCITA, encoding="utf-8") as f:
            self.assertEqual(f.read(), GR.genera(GR.sorgenti_del_repo(), PALETTE), "python tools/genera_regia.py --scrivi")

    def test_negativa_header_vecchio(self):
        altri = GR.sorgenti_del_repo() + [("prova.regia", PROVA.format(secondi=3, battuta="R_P_01_00"))]
        with open(GR.USCITA, encoding="utf-8") as f:
            self.assertNotEqual(f.read(), GR.genera(altri, PALETTE))

    def test_ogni_cutscene_entro_il_minuto(self):
        for nome, testo in GR.sorgenti_del_repo():
            c = GR.leggi(nome, testo)
            self.assertLessEqual(sum(i["frame"] for i in c["inquadrature"]), 60 * 60, nome)

    def test_negativa_cutscene_di_61_secondi(self):
        with self.assertRaisesRegex(GR.ErroreRegia, "dura 61 s, il massimo e' 60"):
            GR.genera([("lunga.regia", PROVA.format(secondi=61, battuta="R_P_01_00"))], PALETTE)

    def test_nelle_bande_solo_il_narratore_in_due_righe(self):
        self.assertEqual(GT.CONTESTI["NARRATORE"], (224, 2))
        contesti = GR.contesti_dei_testi()
        for nome, testo in GR.sorgenti_del_repo():
            for i in GR.leggi(nome, testo)["inquadrature"]:
                for b in i["battute"]:
                    self.assertEqual(contesti[b], "NARRATORE", (nome, b))

    def test_negativa_battuta_di_dialogo_nelle_bande(self):
        with self.assertRaisesRegex(GR.ErroreRegia, "non e' una battuta del NARRATORE"):
            GR.genera([("dialogo.regia", PROVA.format(secondi=3, battuta="C_A1_01_01"))], PALETTE)

    def test_negativa_tre_righe_rifiutate(self):
        """Una frase del narratore che non sta in 2 righe da 224 px il generatore dei testi la rifiuta."""
        lunga = "Undici citta' confederate cinsero d'assedio la roccaforte di Gubbio, " * 3
        with self.assertRaisesRegex(GT.ErroreTesti, "il contesto NARRATORE ne ammette 2"):
            GT.genera([("prova.testi", f"X | NARRATORE | {lunga.replace(chr(39), '')}".encode("utf-8"))],
                      S.carica("font"))

    def test_quattro_piani_al_massimo(self):
        with self.assertRaisesRegex(GR.ErroreRegia, "da 1 a 4 piani"):
            GR.leggi("cinque.regia", "cutscene C9 | x\ninquadratura 2 | cielo monti citta prato cielo | 12\n")

    def test_piani_con_la_palette_bloccata(self):
        colori = {c for r in PALETTE["rampe"] for c in r["giorno"]}
        self.assertTrue(all(S.colore(PALETTE, r) in colori for r in GR.PALETTE_SFONDO))
        for nome, pittore in GR.PIANI.items():
            usati = {c for riga in pittore().px for c in riga}
            self.assertTrue(usati <= set(range(16)), nome)

    def test_prove_del_lettore_in_cpp(self):
        autotest = open(os.path.join(RADICE, "src", "autotest_regia.cpp"), encoding="utf-8").read()
        for prova in ("durate_entro_il_minuto()", "dura(0, 0, 0) == 1", "dura(0, 30, -1) < CUTSCENE_DATI[0].frame",
                      "luce_e_stacchi()", "parallasse()", "viste()"):
            self.assertIn("static_assert(" + prova, autotest)


if __name__ == "__main__":
    unittest.main(verbosity=2)
