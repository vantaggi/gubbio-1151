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
PROVA = "cutscene CX | prova\ninquadratura {secondi} | cielo_prova monti | 12\nnarratore {battuta}\n"


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
        giorno = {c for r in PALETTE["rampe"] for c in r["giorno"]}
        notte = {c for r in PALETTE["rampe"] for c in r["notte"]}
        for nome, pittore in GR.PIANI.items():
            for momento in GR.PP.MOMENTI:
                tela, palette, di_notte = pittore(momento)
                self.assertEqual(len(palette), 16, nome)
                colori = {S.colore(PALETTE, r, di_notte) for r in palette}
                self.assertTrue(colori <= (notte if di_notte else giorno), (nome, momento))
                self.assertTrue({c for riga in tela.px for c in riga} <= set(range(16)), nome)


class Panorami(unittest.TestCase):
    """Pezzo V: Gubbio vista dalla valle (tools/pittore_panorami.py), dal censimento."""

    def test_monumenti_dal_censimento(self):
        m = {nome: (x, base, alto) for nome, x, base, alto, _ in GR.PP.monumenti_dalla_valle()}
        for nome in ("consoli", "duomo", "san_francesco", "san_pietro", "sant_agostino", "san_domenico"):
            self.assertIn(nome, m)
        # vista da sud-ovest: San Domenico (a nord-ovest) a sinistra di Sant'Agostino (a sud-est)
        self.assertLess(m["san_domenico"][0], m["sant_agostino"][0])
        # la torre dei Consoli (60 m) e' il monumento piu' alto
        self.assertEqual(max(m, key=lambda k: m[k][2]), "consoli")
        # il Duomo (109 m) sta piu' in alto sul pendio di San Francesco (0 m)
        self.assertLess(m["duomo"][1], m["san_francesco"][1])

    def test_negativa_monumento_inventato(self):
        self.assertNotIn("torre_inventata", {n for n, _, _, _, _ in GR.PP.monumenti_dalla_valle()})

    def test_la_notte_e_la_trasformata(self):
        for nome in ("cielo", "monte", "gubbio", "campo"):
            _, palette, notte = GR.PIANI[nome]("notte")
            _, palette_g, giorno_notte = GR.PIANI[nome]("giorno")
            self.assertTrue(notte)
            self.assertFalse(giorno_notte)
            self.assertNotEqual([S.colore(PALETTE, r, True) for r in palette], [S.colore(PALETTE, r) for r in palette_g])

    def test_i_fuochi_del_campo_di_notte(self):
        def fuochi(momento):
            tela, _, _ = GR.PP.campo(momento)
            return sum(r.count(GR.PP.ORO) for r in tela.px)
        self.assertGreater(fuochi("notte"), 50)
        self.assertEqual(fuochi("giorno"), 0)

    def test_i_panorami_nel_budget(self):
        dipinti = GR.dipingi_piani(["cielo:notte", "monte:notte", "gubbio:notte", "campo:notte"])
        tile = sum(len(v[0]) for v in dipinti.values())
        self.assertLessEqual(max(len(v[0]) for v in dipinti.values()), GR.TILE_MAX_PER_PIANO)
        self.assertLess(tile * 32 + 4 * 2048 * 2, 64 * 1024, "tile e mappe di un'inquadratura nella VRAM dei BG")

    def test_prove_del_lettore_in_cpp(self):
        autotest = open(os.path.join(RADICE, "src", "autotest_regia.cpp"), encoding="utf-8").read()
        for prova in ("durate_entro_il_minuto()", "dura(0, 0, 0) == 1", "dura(0, 30, -1) < CUTSCENE_DATI[0].frame",
                      "luce_e_stacchi()", "parallasse()", "viste()"):
            self.assertIn("static_assert(" + prova, autotest)


if __name__ == "__main__":
    unittest.main(verbosity=2)
