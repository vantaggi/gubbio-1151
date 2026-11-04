"""Le quest della v1 e le regole del copione che il gioco ora legge (include/storia_logica.h):

- ogni quest consegnata da' ESPERIENZA_QUEST (55) a ogni Santo, il numero di docs/bilanciamento.md e di
  tools/bilanciamento.py, e il premio della tabella di copione/04_quest.md;
- la gola del Bottaccione resta raggiungibile dopo B-05 rientrando da Porta Metauro (Q-SA01 non si perde):
  l'arco San Martino-Bottaccione esiste e nessun varco legge lo stato di partita;
- le prove a tempo di compilazione stanno in src/autotest_quest.cpp (consegna, scudo in meno di Corrado,
  digiuno di Ubaldo, la camminata nella gola), src/autotest_oggetti.cpp e src/autotest_battaglia.cpp.
Ogni controllo ha la sua negativa.
"""
import copy
import importlib.util
import json
import os
import re
import sys
import unittest

from _stile import RADICE

_spec = importlib.util.spec_from_file_location("genera_storia", os.path.join(RADICE, "tools", "genera_storia.py"))
GS = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(GS)
sys.path.insert(0, os.path.join(RADICE, "tools"))
import bilanciamento as B  # noqa: E402

QUEST_MD = open(os.path.join(RADICE, "copione", "04_quest.md"), encoding="utf-8").read()
PROGRESSIONE = open(os.path.join(RADICE, "include", "progressione.h"), encoding="utf-8").read()
BILANCIAMENTO_MD = open(os.path.join(RADICE, "docs", "bilanciamento.md"), encoding="utf-8").read()
MONDO_LOGICA = open(os.path.join(RADICE, "include", "mondo_logica.h"), encoding="utf-8").read()
GRAFO = json.load(open(os.path.join(RADICE, "mondo", "grafo.json"), encoding="utf-8"))
AUTOTEST = open(os.path.join(RADICE, "src", "autotest_quest.cpp"), encoding="utf-8").read()
GOLA = ["BOTTACCIONE", "GOLA_STRISCIA", "GOLA_MIASMI", "GOLA_ARCO", "CONDOTTO"]


def premi_sbagliati(quest, testo):
    """Le quest il cui premio (quanti e cosa) non e' nella loro riga della tabella del copione."""
    sbagliate = []
    for q in quest:
        riga = next(r for r in testo.splitlines() if r.startswith(f"| {q['id']} "))
        if f"{q['premio'][1]} {q['nome_premio']}" not in riga.split("|")[5]:
            sbagliate.append(q["id"])
    return sbagliate


def raggiungibili(archi, da, senza=()):
    """Le aree raggiungibili da 'da' sugli archi (in tutti e due i sensi), senza passare per 'senza'."""
    vicini = {}
    for a in archi:
        vicini.setdefault(a["da"], set()).add(a["a"])
        vicini.setdefault(a["a"], set()).add(a["da"])
    viste, coda = {da}, [da]
    while coda:
        x = coda.pop()
        for y in vicini.get(x, ()):
            if y not in viste and y not in senza:
                viste.add(y)
                coda.append(y)
    return viste


class Esperienza(unittest.TestCase):

    def test_cinquantacinque_dappertutto(self):
        self.assertEqual(B.leggi_costante("ESPERIENZA_QUEST"), 55)
        self.assertEqual(B.ESPERIENZA_QUEST, 55)
        self.assertIn("Ogni quest dà **55 punti**", BILANCIAMENTO_MD)
        self.assertIn("assegna_esperienza_fissa(p, progressione::ESPERIENZA_QUEST, saliti)",
                      open(os.path.join(RADICE, "include", "storia_logica.h"), encoding="utf-8").read())

    def test_negativa_esperienza_cambiata(self):
        """Il bilanciamento legge il numero dal C++: se cambia la', cambia anche qui."""
        alterato = PROGRESSIONE.replace("ESPERIENZA_QUEST = 55;", "ESPERIENZA_QUEST = 60;")
        self.assertNotEqual(alterato, PROGRESSIONE)
        self.assertEqual(B.leggi_costante("ESPERIENZA_QUEST", alterato), 60)


class Premi(unittest.TestCase):

    def test_premi_come_nel_copione(self):
        self.assertEqual(premi_sbagliati(GS.QUEST, QUEST_MD), [])
        self.assertEqual([q["consegnata"] for q in GS.QUEST], ["Q_SM01_CONSEGNATA", "Q_SA01_CONSEGNATA", "Q_SP01_CONSEGNATA"])
        for q in GS.QUEST:
            self.assertIn(q["consegnata"], GS.BANDIERE_QUEST)
            self.assertIn(q["consegnata"], GS.LETTE_DAL_GIOCO)

    def test_negativa_premio_diverso(self):
        quest = copy.deepcopy(GS.QUEST)
        quest[1]["premio"] = ("BISCOTTI", 2)
        self.assertEqual(premi_sbagliati(quest, QUEST_MD), ["Q-SA01"])

    def test_tabella_in_storia_h(self):
        storia_h = open(GS.USCITA_H, encoding="utf-8").read()
        self.assertIn('{ "Q-SM01", int8_t(mondo::AreaId::SAN_MARTINO), Bandiera::ULTIMATUM_RICEVUTO, '
                      'Bandiera::ATTO_I_COMPLETATO, Q_SM01_CONSEGNATA, 0, 3 }', storia_h)


class GolaDopoB05(unittest.TestCase):

    def test_da_porta_metauro_alla_gola(self):
        """L'arco San Martino-Bottaccione passa da Porta Metauro; dalla citta' si arriva al Condotto senza
        ripassare dalla Basilica (dopo B-05 non c'e' un'altra discesa)."""
        arco = [a for a in GRAFO["archi"] if {a["da"], a["a"]} == {"SAN_MARTINO", "BOTTACCIONE"}]
        self.assertEqual(len(arco), 1)
        self.assertEqual(arco[0].get("porta"), "Porta Metauro")
        self.assertTrue(set(GOLA) <= raggiungibili(GRAFO["archi"], "SAN_MARTINO", senza={"BASILICA", "MONTE_INGINO"}))

    def test_negativa_senza_porta_metauro(self):
        archi = [a for a in GRAFO["archi"] if {a["da"], a["a"]} != {"SAN_MARTINO", "BOTTACCIONE"}]
        self.assertFalse(set(GOLA) <= raggiungibili(archi, "SAN_MARTINO", senza={"BASILICA", "MONTE_INGINO"}))

    def test_i_varchi_non_leggono_la_partita(self):
        """Nessun varco dipende dalla storia: la logica del mondo non conosce lo stato di partita."""
        self.assertEqual(varchi_con_condizioni(MONDO_LOGICA), [])

    def test_negativa_varco_con_condizione(self):
        alterato = MONDO_LOGICA.replace("constexpr Evento controlla_varco(Esploratore& e)",
                                        "constexpr Evento controlla_varco(Esploratore& e, const GameState& p)")
        self.assertEqual(varchi_con_condizioni(alterato), ["GameState"])

    def test_la_camminata_a_tempo_di_compilazione(self):
        for prova in ("static_assert(cammina(DA_PORTA_METAURO, 11)", "static_assert(! cammina(SCORCIATOIA, 2)",
                      "static_assert(gola_dopo_il_rientro()", "static_assert(condotto_prima_di_b04()"):
            self.assertIn(prova, AUTOTEST)


def varchi_con_condizioni(testo):
    return [p for p in ("GameState", "storia::", "accesa(") if p in testo]


PROVE = {
    "src/autotest_quest.cpp": ["static_assert(consegna_buona(0) && consegna_buona(1) && consegna_buona(2)",
                               "static_assert(digiuno_di_ubaldo()", "static_assert(scudi(false, false, INCONTRO_DI_CORRADO) == 0",
                               "static_assert(livello_a_corrado(0) == 5 && livello_a_corrado(3) == 6"],
    "src/autotest_oggetti.cpp": ["static_assert(crescia_al_primo_round(UBALDO, GIORGIO, UBALDO_A_DIGIUNO) == -1"],
    "src/autotest_battaglia.cpp": ["static_assert(verifica_scudo_in_meno() == 100", "static_assert(verifica_ceri() == 200"],
    # la scena passa le due regole alla battaglia
    "src/scena_battaglia.cpp": ["g_scena.ricomincia(incontro, seme, false, eroi, presenti, scudi_in_meno, a_digiuno, partita ? partita->ferite : nullptr,\n                       ceri);",
                                "storia::scudi_in_meno(*partita, incontro)", "storia::a_digiuno(*partita)",
                                "storia::ceri_accesi(*partita)"],
}


def prove_mancanti(testi):
    return [(f, p) for f, prove in PROVE.items() for p in prove if p not in testi[f]]


class ProveInCpp(unittest.TestCase):

    def setUp(self):
        self.testi = {f: open(os.path.join(RADICE, f), encoding="utf-8").read() for f in PROVE}

    def test_le_prove_ci_sono(self):
        self.assertEqual(prove_mancanti(self.testi), [])

    def test_negativa_regola_non_passata(self):
        """Una scena che non passa le regole alla battaglia viene segnalata."""
        self.testi["src/scena_battaglia.cpp"] = self.testi["src/scena_battaglia.cpp"].replace(
            "presenti, scudi_in_meno, a_digiuno, partita ? partita->ferite : nullptr,\n                       ceri);", "presenti);")
        self.assertEqual(prove_mancanti(self.testi), [("src/scena_battaglia.cpp", PROVE["src/scena_battaglia.cpp"][0])])


if __name__ == "__main__":
    unittest.main()
