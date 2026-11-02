"""Il motore della storia (F6 parte 1) sulle tabelle del copione v1: tools/genera_storia.py.

I criteri del piano, ognuno con la sua negativa:
- ogni bandiera scritta da una scena e' letta da qualcuno (un'altra scena, le fasi degli NPC, il gioco);
- ogni quest e' completabile (si prende da una bandiera che la storia accende prima della fine, nelle
  aree che esistono);
- nessuna scena e' irraggiungibile (il giro della storia senza camminare le visita tutte).
Lo stesso giro e' provato in C++ a tempo di compilazione (src/autotest_storia.cpp) e sul GBA
(GUBBIO_AVVIO=8, tests/dati/storia_mgba.txt).
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
MONDO_H = open(os.path.join(RADICE, "include", "mondo.h"), encoding="utf-8").read()
AREE_ID = re.findall(r"^    (\w+),$", re.search(r"enum class AreaId : uint8_t\n\{(.*?)\};", MONDO_H, re.S).group(1), re.M)
QUEST_MD = open(os.path.join(RADICE, "copione", "04_quest.md"), encoding="utf-8").read()


def giro(scene):
    """Il gemello Python di storia::gioca_tutta: l'ordine delle scene visitate."""
    accese, fatte, ordine = set(), set(), []
    avanti = True
    while avanti:
        avanti = False
        for area in [None] + AREE_ID:
            for s in scene:
                c = s["codice"]
                if c in fatte or GS.AREE[c] != area:
                    continue
                if not set(s["richieste"]) <= accese or set(s["vietate"]) & accese:
                    continue
                if c in GS.SEGUE and GS.SEGUE[c] not in fatte:
                    continue
                accese |= set(s["imposta"])
                fatte.add(c)
                ordine.append(c)
                avanti = True
                break
            if avanti:
                break
    return ordine, accese


def scritte_non_lette(scene, lette_dal_gioco):
    lette = set(lette_dal_gioco)
    for s in scene:
        lette |= set(s["richieste"]) | set(s["vietate"])
    scritte = {b for s in scene for b in s["imposta"]}
    return sorted(scritte - lette)


def quest_non_completabili(quest, scene):
    ordine, accese = giro(scene)
    posizione = {}
    for i, c in enumerate(ordine):
        for s in scene:
            if s["codice"] == c:
                for b in s["imposta"]:
                    posizione.setdefault(b, i)
    errori = []
    for q in quest:
        if q["da"] not in posizione:
            errori.append(f"{q['id']}: si prende da {q['da']}, che nessuna scena accende")
        elif q["entro"] in posizione and posizione[q["da"]] >= posizione[q["entro"]]:
            errori.append(f"{q['id']}: si prende da {q['da']} dopo la scadenza {q['entro']}")
        for k in ("datore", "obiettivo", "consegna"):
            if q[k] not in AREE_ID:
                errori.append(f"{q['id']}: area {q[k]} sconosciuta")
    return errori


def scene_del_log(log):
    return sorted(re.findall(r"^Scena ([A-Z0-9]+-\d+)$", log, re.M))


class GeneratoAggiornato(unittest.TestCase):

    def test_file_generati_aggiornati(self):
        h, t = GS.genera()
        with open(GS.USCITA_H, encoding="utf-8") as f:
            self.assertEqual(f.read(), h, "eseguire python tools/genera_storia.py --scrivi")
        with open(GS.USCITA_TESTI, encoding="utf-8") as f:
            self.assertEqual(f.read(), t)

    def test_negativa_battuta_cambiata(self):
        scene = copy.deepcopy(SCENE)
        chi, espr, frase, dove = scene[3]["battute"][0]
        scene[3]["battute"][0] = (chi, espr, frase + " Anzi no.", dove)
        with open(GS.USCITA_TESTI, encoding="utf-8") as f:
            self.assertNotEqual(f.read(), GS.testi_del_copione(scene, NPC))


class Tabelle(unittest.TestCase):

    def test_le_scene_del_copione(self):
        self.assertEqual(len(SCENE), 19)
        self.assertEqual(sum(len(s["battute"]) for s in SCENE), 181)
        self.assertEqual(len(NPC), 13)

    def test_ogni_bandiera_scritta_e_letta(self):
        self.assertEqual(scritte_non_lette(SCENE, GS.LETTE_DAL_GIOCO), [])

    def test_negativa_bandiera_scritta_e_mai_letta(self):
        scene = copy.deepcopy(SCENE)
        scene[-1]["imposta"] = scene[-1]["imposta"] + ["MIASMI_VISTI"]
        self.assertEqual(scritte_non_lette(scene, {k: v for k, v in GS.LETTE_DAL_GIOCO.items() if k != "MIASMI_VISTI"}),
                         ["MIASMI_VISTI"])

    def test_nessuna_scena_irraggiungibile(self):
        ordine, accese = giro(SCENE)
        self.assertEqual(sorted(ordine), sorted(s["codice"] for s in SCENE))
        self.assertEqual(ordine[0], "P-00")
        self.assertEqual(ordine[-1], "E-02")
        self.assertIn("CRONACA_V1_FINITA", accese)

    def test_negativa_scena_irraggiungibile(self):
        scene = copy.deepcopy(SCENE)
        scena = next(s for s in scene if s["codice"] == "A1-06")
        scena["richieste"] = scena["richieste"] + ["CRONACA_V1_FINITA"]
        ordine, _ = giro(scene)
        self.assertNotIn("A1-06", ordine)

    def test_ogni_quest_completabile(self):
        self.assertEqual(quest_non_completabili(GS.QUEST, SCENE), [])

    def test_negativa_quest_che_non_si_prende(self):
        quest = copy.deepcopy(GS.QUEST)
        quest[0]["da"] = "SIGILLO_SPEZZATO"
        self.assertTrue(quest_non_completabili(quest, SCENE))

    def test_quest_come_nel_copione(self):
        """La tabella QUEST del generatore dice le stesse bandiere di partenza della tabella di 04_quest.md."""
        for q in GS.QUEST:
            riga = next(r for r in QUEST_MD.splitlines() if r.startswith(f"| {q['id']} "))
            self.assertIn(f"da `{q['da']}`", riga, q["id"])

    def test_npc_per_fase(self):
        for p in NPC:
            self.assertTrue(p["frasi"], p["nome"])
            self.assertTrue(all(f in GS.FASI for f, _, _, _ in p["frasi"]))
        storia_h = open(GS.USCITA_H, encoding="utf-8").read()
        self.assertIn("inline constexpr int NPC = 13;", storia_h)

    def test_la_storia_sul_gba(self):
        """La ROM GUBBIO_AVVIO=8 ha recitato ogni scena, dalla prima ai titoli di coda (log in tests/dati)."""
        log = open(os.path.join(RADICE, "tests", "dati", "storia_mgba.txt"), encoding="utf-8").read()
        self.assertEqual(scene_del_log(log), sorted(s["codice"] for s in SCENE))
        self.assertIn("Storia: 19 scene visitate su 19, 0 mancanti, titoli di coda raggiunti", log)
        self.assertIn("Cutscene P-01 (segnaposto)", log)

    def test_negativa_log_con_una_scena_in_meno(self):
        log = open(os.path.join(RADICE, "tests", "dati", "storia_mgba.txt"), encoding="utf-8").read()
        self.assertNotEqual(scene_del_log(log.replace("Scena A1-06\n", "")), sorted(s["codice"] for s in SCENE))

    def test_il_prologo_giocabile_sul_gba(self):
        """La ROM GUBBIO_AVVIO=9: l'ultimatum, la postierla, la Pattuglia che compare al Teatro solo ora,
        la battaglia (col pilota) che salva Antonio, il gruppo di tre, la Pattuglia che sparisce."""
        log = open(os.path.join(RADICE, "tests", "dati", "prologo_mgba.txt"), encoding="utf-8").read()
        self.assertEqual(re.findall(r"^Scena (\S+)$", log, re.M), ["P-00", "P-01", "P-02", "A1-01", "A1-03", "A1-04"])
        self.assertIn("Prologo: Giorgio nel gruppo si, Pattuglia sulla mappa si, Antonio salvato si, gruppo 7, "
                      "Pattuglia sulla mappa dopo sparita", log)

    def test_negativa_prologo_senza_antonio(self):
        log = open(os.path.join(RADICE, "tests", "dati", "prologo_mgba.txt"), encoding="utf-8").read()
        self.assertNotIn("Prologo: Giorgio nel gruppo si, Pattuglia sulla mappa si, Antonio salvato si",
                         log.replace("Antonio salvato si", "Antonio salvato NO"))

    def test_prove_in_cpp(self):
        autotest = open(os.path.join(RADICE, "src", "autotest_storia.cpp"), encoding="utf-8").read()
        for prova in ("tutta_la_storia()", "visitate_con_la_tabella_guasta() < SCENE", "fasi()",
                      "pattuglia_quando_serve()", "gruppo_della_storia()", "! agisce(0b001, battaglia::GIORGIO)",
                      "agisce(0b111, battaglia::GIORGIO)"):
            self.assertIn("static_assert(" + prova, autotest)


if __name__ == "__main__":
    unittest.main(verbosity=2)
