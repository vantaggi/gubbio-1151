"""Il motore della storia v2 (pezzo SV2): le varianti del copione v2 lette da tools/genera_storia.py.

Le scelte (un menu a due voci nella vista di gioco, mai nelle bande) e i blocchi «voce» che accendono la
loro bandiera; "Se `BANDIERA`:" e "Altrimenti:"; "al posto della battuta di"; "Se almeno due indizi:";
le condizioni con "né ... né"; le righe "(se BANDIERA)" degli NPC, che vincono dall'alto; la SCELTA di
B-05 che non conta; le bandiere 64-127 nelle quest; la frase nuova del narratore in C1.
"""
import copy
import importlib.util
import os
import re
import unittest

from _stile import RADICE

_spec = importlib.util.spec_from_file_location("genera_storia", os.path.join(RADICE, "tools", "genera_storia.py"))
GS = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(GS)

SCENE, NPC = GS.leggi_copione()
PER_CODICE = {s["codice"]: s for s in SCENE}
TESTI = open(os.path.join(RADICE, "testi", "copione.testi"), encoding="utf-8").read()
STORIA_H = open(GS.USCITA_H, encoding="utf-8").read()


def recita(scena, accese, voce):
    """Il gemello Python di recita_battute: le battute che si dicono con quelle bandiere e quella voce."""
    dette, scelta = [], -1
    for b in scena["battute"]:
        if not vale(b["guardia"], accese, scelta):
            continue
        if b["voci"]:
            scelta = voce
            if b["accende"][voce] != GS.NESSUNA:
                accese = accese | {GS.TUTTE[b["accende"][voce]]}
            continue
        dette.append(b["frase"])
    return dette, accese


def vale(g, accese, scelta):
    tipo, a, b, c = g
    if tipo == "SEMPRE":
        return True
    if tipo in ("BANDIERA", "VARIANTE_BANDIERA"):
        return GS.TUTTE[a] in accese
    if tipo in ("NON_BANDIERA", "VARIANTE_NON_BANDIERA"):
        return GS.TUTTE[a] not in accese
    if tipo == "SCELTA":
        return scelta == a
    if tipo == "ALMENO_DUE":
        return sum(GS.TUTTE[x] in accese for x in (a, b, c)) >= 2
    raise AssertionError(tipo)


class Scelte(unittest.TestCase):

    def test_quattro_dilemmi_con_le_loro_bandiere(self):
        """D1 (A1-05b), D2 (B-03), D4 (E-01) nelle scene, D3 (la popolana) negli NPC; ogni voce col suo blocco."""
        attese = {"A1-05b": ("BORGO_DENTRO", "BORGO_FUORI"), "B-03": ("ESULE_PRIGIONIERO", "ESULE_LIBERATO"),
                  "E-01": ("GIUSTIZIA_OFFERTA", None)}
        for codice, bandiere in attese.items():
            scelte = [b for b in PER_CODICE[codice]["battute"] if b["voci"]]
            self.assertEqual(len(scelte), 1, codice)
            accende = tuple(GS.TUTTE[a] if a != GS.NESSUNA else None for a in scelte[0]["accende"])
            self.assertEqual(accende, bandiere, codice)
        popolana = next(p for p in NPC if p["nome"] == "Popolana")
        d3 = [b for b in popolana["frasi"] if b["voci"]][0]
        self.assertEqual(GS.TUTTE[d3["accende"][0]], "PANE_DATO")
        self.assertEqual(d3["consuma"], GS.OGGETTO_CRESCIA)
        self.assertEqual(d3["guardia"][0], "OGGETTO_E_NON_BANDIERA")

    def test_ogni_voce_recita_solo_il_suo_blocco(self):
        s = PER_CODICE["A1-05b"]
        dentro, accese_d = recita(s, set(), 0)
        fuori, accese_f = recita(s, set(), 1)
        self.assertIn("Aprite. Nessuno resta fuori, stanotte. Il grano lo divideremo.", dentro)
        self.assertNotIn("Restate nel borgo. La milizia vi guarda, e Dio con lei.", dentro)
        self.assertIn("Restate nel borgo. La milizia vi guarda, e Dio con lei.", fuori)
        self.assertIn("BORGO_DENTRO", accese_d)
        self.assertIn("BORGO_FUORI", accese_f)

    def test_negativa_voce_che_non_c_e(self):
        testo = "## A1-05b · prova\n\n- SCELTA: Apri / Chiudi\n\nSe «Brucia tutto» (`BORGO_DENTRO`):\n\n- UBALDO: No.\n"
        with self.assertRaisesRegex(GS.ErroreStoria, "non e' una voce"):
            GS.leggi_scene([("prova.md", testo)])

    def test_e01_la_voce_corta_trova_il_suo_blocco(self):
        """Il menu dice «Giustizia agli esuli», il blocco «Offri giustizia agli esuli»: e' la stessa voce."""
        s = PER_CODICE["E-01"]
        offerta, accese = recita(s, set(), 0)
        self.assertIn("GIUSTIZIA_OFFERTA", accese)
        self.assertIn("Hai aperto una porta, vescovo. Non è servito. Ma l'hanno vista.", offerta)
        chiuse, accese = recita(s, set(), 1)
        self.assertNotIn("GIUSTIZIA_OFFERTA", accese)
        self.assertIn("Anche tu hai chiuso una porta, stamattina. Ricordatelo.", chiuse)
        self.assertNotIn("Anche tu hai chiuso una porta, stamattina. Ricordatelo.", offerta)

    def test_la_scelta_di_b05_accende_alba_confermata(self):
        """«Sì, è ora» di B-05 accende ALBA_CONFERMATA, che E-01 richiede (prima la scelta si buttava)."""
        scelte = [b for b in PER_CODICE["B-05"]["battute"] if b["voci"]]
        self.assertEqual(len(scelte), 1)
        self.assertEqual(GS.TUTTE[scelte[0]["accende"][0]], "ALBA_CONFERMATA")
        self.assertEqual(scelte[0]["accende"][1], GS.NESSUNA)
        self.assertIn("ALBA_CONFERMATA", PER_CODICE["E-01"]["richieste"])
        _, accese = recita(PER_CODICE["B-05"], set(), 1)
        self.assertNotIn("ALBA_CONFERMATA", accese)

    def test_negativa_una_scelta_senza_blocchi_resta_se_ha_i_blocchi(self):
        battute = [GS.battuta("SCELTA", None, "A / B", "x"), GS.battuta("UBALDO", None, "si", "x", ("SCELTA", 0, 0, 0))]
        battute[0]["voci"] = ("A", "B")
        self.assertEqual(len(GS.togli_scelte_senza_blocchi(battute)), 2)

    def test_le_voci_nella_vista_di_gioco_non_nelle_bande(self):
        """Le voci sono testi SCELTA (100 px, una riga) e nessuna scena con una scelta e' una cutscene."""
        for s in SCENE:
            for k, b in enumerate(s["battute"]):
                if b["voci"]:
                    self.assertNotIn(s["codice"], GS.CUTSCENE, s["codice"])
                    for j in (0, 1):
                        self.assertRegex(TESTI, rf"(?m)^{GS.id_voce(GS.id_battuta(s['codice'], k), j)}\s+\| SCELTA ")


class Varianti(unittest.TestCase):

    def test_b01_al_posto_della_battuta_di_giorgio(self):
        s = PER_CODICE["B-01"]
        senza, _ = recita(s, set(), 0)
        con, _ = recita(s, {"INDIZIO_ROCCIA"}, 0)
        self.assertIn("Berto dice un sacco di cose.", senza)
        self.assertNotIn("Giambono diceva lo stesso. Due che dicono la stessa cosa...", senza)
        self.assertIn("Giambono diceva lo stesso. Due che dicono la stessa cosa...", con)
        self.assertNotIn("Berto dice un sacco di cose.", con)
        self.assertEqual(len(senza), len(con))

    def test_b04_righe_di_battaglia_fuori_dal_dialogo(self):
        """Le righe "- IN BATTAGLIA (evento): ..." di B-04 si mettono da parte: non si recitano prima dello scontro."""
        s = PER_CODICE["B-04"]
        self.assertEqual(len(s["in_battaglia"]), 7)
        self.assertEqual(s["in_battaglia"][0][0], "turno 1, Scudo di Forgia")
        frasi = [b["frase"] for b in s["battute"]]
        for _, b in s["in_battaglia"]:
            self.assertNotIn(b["frase"], frasi)
        self.assertEqual(s["in_battaglia"][2][1]["chi"], "ANTONIO")
        self.assertEqual(s["in_battaglia"][2][1]["espr"], "deciso")

    def test_negativa_riga_di_battaglia_con_parlante_sconosciuto(self):
        testo = "## B-04 · prova\n\n- UBALDO: Si.\n- IN BATTAGLIA (turno 1): NESSUNO: No.\n"
        with self.assertRaises(GS.ErroreStoria):
            GS.leggi_scene([("prova.md", testo)])

    def test_a109_almeno_due_indizi(self):
        s = PER_CODICE["A1-09"]
        frase = "Quello che ci hanno detto in città... tutte le voci portano all'acqua."
        self.assertIn(frase, recita(s, {"INDIZIO_CARTA", "INDIZIO_ACQUA"}, 0)[0])
        self.assertNotIn(frase, recita(s, {"INDIZIO_CARTA"}, 0)[0])

    def test_condizione_ne_ne(self):
        s = PER_CODICE["A1-05b"]
        self.assertEqual(s["richieste"], ["CITTA_IN_DIGIUNO"])
        self.assertEqual(sorted(s["vietate"]), ["BORGO_DENTRO", "BORGO_FUORI"])
        self.assertNotIn("BORGO_DENTRO", s["imposta"])

    def test_negativa_bandiera_che_non_esiste(self):
        testo = "## A1-05b · prova\n\n- UBALDO: Si.\n\nSe `BANDIERA_INVENTATA`:\n\n- UBALDO: No.\n"
        with self.assertRaises(ValueError):
            GS.leggi_scene([("prova.md", testo)])


class Npc(unittest.TestCase):

    def test_le_varianti_stanno_sopra_e_vincono_dall_alto(self):
        """Nella tabella del gioco le righe "(se BANDIERA)" di una fase vengono prima delle altre."""
        popolana = next(p for p in NPC if p["nome"].startswith("Popolana"))
        notte = [b for b in popolana["frasi"] if b["fase"] == "NOTTE"]
        self.assertEqual(notte[0]["guardia"][0], "VARIANTE_BANDIERA")
        self.assertEqual(GS.TUTTE[notte[0]["guardia"][1]], "PANE_DATO")
        self.assertEqual(notte[1]["guardia"], GS.SEMPRE)

    def test_negativa_riga_senza_variante(self):
        b = GS.battuta("GUIDO", None, "x", "x")
        self.assertFalse(b["guardia"][0].startswith("VARIANTE"))

    def test_se_non(self):
        cecco = next(p for p in NPC if p["nome"].startswith("Cecco"))
        varianti = [b for b in cecco["frasi"] if b["guardia"][0].startswith("VARIANTE")]
        self.assertEqual([GS.TUTTE[b["guardia"][1]] for b in varianti], ["ESULE_LIBERATO", "INDIZIO_ROCCIA"])  # NOTTE: il ragazzo di B-03 lasciato andare


class Bandiere(unittest.TestCase):

    def test_storia_e_quest(self):
        for b in ("BORGO_DENTRO", "BORGO_FUORI", "ESULE_PRIGIONIERO", "ESULE_LIBERATO", "GIUSTIZIA_OFFERTA"):
            self.assertLess(GS.TUTTE.index(b), 64, b)
        for b in ("INDIZIO_CARTA", "INDIZIO_ACQUA", "INDIZIO_ROCCIA", "RICCIARDO_ASCOLTATO", "RUFINO_ASCOLTATO", "PANE_DATO"):
            self.assertGreaterEqual(GS.TUTTE.index(b), 64, b)
            self.assertIn(f"inline constexpr uint8_t {b} = {GS.TUTTE.index(b)};", STORIA_H)
        self.assertLessEqual(len(GS.BANDIERE), 64)
        self.assertLessEqual(len(GS.TUTTE), 128)

    def test_negativa_quest_nell_intervallo_della_storia(self):
        self.assertNotIn("INDIZIO_CARTA", GS.BANDIERE)

    def test_nel_salvataggio(self):
        gs = open(os.path.join(RADICE, "include", "game_state.h"), encoding="utf-8").read()
        self.assertIn("uint8_t quest[8];", gs)
        self.assertIn("VERSIONE = 3;", open(os.path.join(RADICE, "include", "save_data.h"), encoding="utf-8").read())


class C1(unittest.TestCase):

    def test_la_frase_nuova_del_narratore(self):
        frase = "Nel 1151, vecchi torti e nuove ambizioni spezzarono la pace dei colli."
        self.assertRegex(TESTI, rf"(?m)^R_P_02_00\s+\| NARRATORE \| {re.escape(frase)}$")
        regia = open(os.path.join(RADICE, "regia", "c1_prologo.regia"), encoding="utf-8").read()
        self.assertIn("narratore R_P_02_00", regia)

    def test_negativa_la_frase_vecchia_non_c_e_piu(self):
        self.assertNotIn("l'invidia e la sete di dominio", TESTI)


class ProveInCpp(unittest.TestCase):

    def test_prove_a_tempo_di_compilazione(self):
        autotest = open(os.path.join(RADICE, "src", "autotest_storia.cpp"), encoding="utf-8").read()
        for prova in ("guardie()", "! guardie_guaste()", "borgo_dimenticato()", "scelte_di_tutta_la_storia(0)",
                      "scelte_di_tutta_la_storia(1)"):
            self.assertIn("static_assert(" + prova, autotest)


if __name__ == "__main__":
    unittest.main(verbosity=2)
