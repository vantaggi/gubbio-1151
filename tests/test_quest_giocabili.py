"""Le quest giocabili (SV2c): Q-SM01, Q-SA01 e Q-SP01 si prendono, si compiono sulla mappa e si consegnano.

- le bandiere nuove (quest presa, un bit per pezzo dell'obiettivo) stanno nell'intervallo quest 64-127 di
  GameState::quest: nessun campo nuovo, il salvataggio resta v3; i pezzi di una quest sono consecutivi;
- ogni oggetto da raccogliere sta nell'area che dice il copione, su una cella dove il gioco cammina
  (MIASMA compreso, che nel gioco blocca), raggiungibile dallo spawn 0; le radici della gola si raggiungono
  dalla citta' anche dopo B-05, da Porta Metauro;
- ogni datore ha proposta, attesa, consegna e una battuta di dopo in ogni fase in cui la quest si puo'
  consegnare; le righe di raccolta hanno le guardie giuste; gli indizi sono di Lucia, del Venditore e di
  Giordano;
- il gioco chiama davvero la consegna, la raccolta, gli indizi e la Rosa (src/storia_scena.cpp), e le
  bandiere nuove sono in LETTE_DAL_GIOCO e in ACCESE_DAL_GIOCO di tools/grafo_trama.py.
La camminata con la collisione vera e il giro completo di ogni quest sono a tempo di compilazione in
src/autotest_quest.cpp. Ogni controllo qui ha la sua negativa.
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
import genera_mondo as G  # noqa: E402
import grafo_trama as GT  # noqa: E402

STORIA_H = open(GS.USCITA_H, encoding="utf-8").read()
SCENA_CPP = open(os.path.join(RADICE, "src", "storia_scena.cpp"), encoding="utf-8").read()
SAVE_H = open(os.path.join(RADICE, "include", "save_data.h"), encoding="utf-8").read()
QUEST_MD = open(os.path.join(RADICE, "copione", "04_quest.md"), encoding="utf-8").read()
GRAFO = json.load(open(os.path.join(RADICE, "mondo", "grafo.json"), encoding="utf-8"))
AREE = GS.aree_del_mondo()
NUOVE = ["Q_SM01_PRESA", "Q_SA01_PRESA", "Q_SP01_PRESA", "FERRO_1", "FERRO_2", "FERRO_3", "ELLEBORO_1", "ELLEBORO_2",
         "ELLEBORO_3", "ELLEBORO_4", "ROSA_RIPRESA"]
INDIZI = ["INDIZIO_LUCIA", "INDIZIO_VENDITORE", "INDIZIO_FONTANIERE"]


def fuori_intervallo(bandiere_quest):
    """Le bandiere delle quest che escono da 64-127 (GameState::quest ha 8 byte)."""
    return [b for i, b in enumerate(bandiere_quest) if not 64 <= GS.PRIMA_QUEST + i < 128]


def pezzi_non_consecutivi(quest):
    return [q["id"] for q in quest
            if [GS.indice(b) for b in q["pezzi"]] != list(range(GS.indice(q["pezzi"][0]), GS.indice(q["pezzi"][0]) + len(q["pezzi"])))]


def raccolte_di_storia_h(testo):
    """[(area, tx, ty, quest, bandiera)] dalla tabella RACCOLTA di storia.h."""
    blocco = re.search(r"inline constexpr Raccolta RACCOLTA\[RACCOLTE\] = \{(.*?)\n\};", testo, re.S).group(1)
    return [(a, int(x), int(y), int(q), b) for a, x, y, q, b in
            re.findall(r"\{ int8_t\(mondo::AreaId::([A-Z_]+)\), (\d+), (\d+), (\d+), ([A-Z_0-9]+), \d+ \}", blocco)]


def raccolte_sbagliate(raccolte):
    """Gli oggetti fuori posto: area che il copione non dice, cella solida per il gioco o varco, non raggiungibile
    dallo spawn 0 dell'area."""
    sbagliate = []
    for area, x, y, q, b in raccolte:
        a = AREE[area]
        c = a["griglia"][y][x] if 0 <= y < a["altezza"] and 0 <= x < a["larghezza"] else "#"
        if area not in GS.AREE_DELLE_RACCOLTE.get(GS.QUEST[q]["id"], set()):
            sbagliate.append((b, "area"))
        elif GS.solida_nel_gioco(c, G) or c in G.VARCHI:
            sbagliate.append((b, "cella"))
        elif (x, y) not in GS.raggiungibili_da(a, *a["spawn"][0], G):
            sbagliate.append((b, "irraggiungibile"))
    return sbagliate


def raggiungibili(archi, da, senza=()):
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


def fasi_senza_dopo(quest, letto):
    """Le (quest, fase) in cui la quest si puo' consegnare ma il datore, dopo, non ha niente da dire."""
    mancano = []
    for q in quest:
        prima = GS.FASI.index("DIGIUNO") if q["da"] == "CITTA_IN_DIGIUNO" else 0
        for f in GS.FASI[prima:]:
            if not letto[q["id"]]["dopo"][f]:
                mancano.append((q["id"], f))
    return mancano


def chiamate_mancanti(codice):
    """Le chiamate che rendono le quest giocabili e che la scena del gioco non fa."""
    attese = ["consegna_quest(g_game_state", "prendi_quest(g_game_state", "raccogli(g_game_state",
              "trova_indizio(g_game_state", "riprendi_la_rosa(g_game_state", "raccolta_toccata(g_game_state",
              "infiltrato_presente(g_game_state", "indizio_dell_npc(g_game_state"]
    return [c for c in attese if c not in codice]


class Bandiere(unittest.TestCase):

    def test_nell_intervallo_quest(self):
        self.assertEqual(fuori_intervallo(GS.BANDIERE_QUEST), [])
        for b in NUOVE:
            self.assertIn(b, GS.BANDIERE_QUEST)
            self.assertIn(f"inline constexpr uint8_t {b} = {GS.indice(b)};", STORIA_H)
        self.assertIn("inline constexpr uint16_t VERSIONE = 3;", SAVE_H)
        self.assertEqual(pezzi_non_consecutivi(GS.QUEST), [])

    def test_negativa_troppe_bandiere(self):
        # oggi le bandiere delle quest sono 24 (64-87): la quarantesima in piu' cade a 128
        self.assertEqual(len(GS.BANDIERE_QUEST), 24)
        self.assertEqual(fuori_intervallo(GS.BANDIERE_QUEST + [f"X{i}" for i in range(64)])[:1], ["X40"])

    def test_negativa_pezzi_sparsi(self):
        quest = copy.deepcopy(GS.QUEST)
        quest[1]["pezzi"] = ["ELLEBORO_1", "ELLEBORO_3"]
        self.assertEqual(pezzi_non_consecutivi(quest), ["Q-SA01"])

    def test_lette_e_accese(self):
        for b in NUOVE + INDIZI:
            self.assertIn(b, GS.LETTE_DAL_GIOCO, b)
            self.assertIn(b, GT.ACCESE_DAL_GIOCO, b)

    def test_negativa_bandiera_senza_lettore(self):
        lette = dict(GS.LETTE_DAL_GIOCO)
        del lette["ELLEBORO_3"]
        self.assertEqual([b for b in NUOVE if b not in lette], ["ELLEBORO_3"])


class Raccolte(unittest.TestCase):

    def test_al_loro_posto(self):
        raccolte = raccolte_di_storia_h(STORIA_H)
        self.assertEqual(len(raccolte), len(GS.RACCOLTE))
        self.assertEqual([b for *_, b in raccolte], [r["bandiera"] for r in GS.RACCOLTE])
        self.assertEqual(raccolte_sbagliate(raccolte), [])
        # ogni pezzo sulla mappa una volta sola, e solo per le quest con oggetti da raccogliere
        for q in GS.QUEST:
            sulla_mappa = sorted(b for *_, b in raccolte if b in q["pezzi"])
            self.assertEqual(sulla_mappa, sorted(q["pezzi"]) if q["id"] in GS.AREE_DELLE_RACCOLTE else [], q["id"])

    def test_negativa_nel_muro(self):
        raccolte = raccolte_di_storia_h(STORIA_H)
        area, x, y, q, b = raccolte[0]
        self.assertEqual(raccolte_sbagliate([(area, 30, 30, q, b)]), [(b, "cella")])     # la cavea del Teatro

    def test_negativa_area_sbagliata(self):
        raccolte = raccolte_di_storia_h(STORIA_H)
        area, x, y, q, b = raccolte[0]
        self.assertEqual(raccolte_sbagliate([("TEATRO_ROMANO", x, y, 1, "ELLEBORO_1")]), [("ELLEBORO_1", "area")])

    def test_negativa_nei_miasmi(self):
        """Il MIASMA nella .area e' calpestabile, ma nel gioco (mondo::solida) blocca: li' non si raccoglie."""
        a = AREE["GOLA_MIASMI"]
        x, y = next((x, y) for y, r in enumerate(a["griglia"]) for x, c in enumerate(r) if c == "g")
        self.assertFalse(G.solida("g"))
        self.assertEqual(raccolte_sbagliate([("GOLA_MIASMI", x, y, 1, "ELLEBORO_3")]), [("ELLEBORO_3", "cella")])

    def test_la_gola_dopo_b05(self):
        """Le radici stanno nelle stanze della gola, che dalla citta' si raggiungono da Porta Metauro senza
        ripassare dal monte: dopo B-05 si raccolgono ancora."""
        aree = {area for area, *_ in raccolte_di_storia_h(STORIA_H) if area in GS.AREE_DELLE_RACCOLTE["Q-SA01"]}
        self.assertEqual(aree, GS.AREE_DELLE_RACCOLTE["Q-SA01"])
        self.assertTrue(aree <= raggiungibili(GRAFO["archi"], "SAN_MARTINO", senza={"BASILICA", "MONTE_INGINO"}))

    def test_negativa_gola_senza_porta_metauro(self):
        archi = [a for a in GRAFO["archi"] if {a["da"], a["a"]} != {"SAN_MARTINO", "BOTTACCIONE"}]
        self.assertFalse(GS.AREE_DELLE_RACCOLTE["Q-SA01"] <= raggiungibili(archi, "SAN_MARTINO", senza={"BASILICA", "MONTE_INGINO"}))

    def test_negativa_nessun_posto(self):
        """Un oggetto accanto a un simbolo che nell'area non c'e' non trova posto: il generatore si ferma."""
        with self.assertRaises(GS.ErroreStoria):
            GS.posti_delle_raccolte([dict(GS.RACCOLTE[0], vicino="~")], {})


class Battute(unittest.TestCase):

    def setUp(self):
        self.letto = GS.leggi_quest(QUEST_MD)

    def test_ogni_momento_del_datore(self):
        for q in GS.QUEST:
            d = self.letto[q["id"]]
            for k in ("proposta", "attesa", "consegna"):
                self.assertTrue(d[k], (q["id"], k))
        self.assertEqual([self.letto[q["id"]]["datore"] for q in GS.QUEST], ["Mastro Raniero", "Monna Agnese", "Fra' Bernardo"])
        self.assertEqual(fasi_senza_dopo(GS.QUEST, self.letto), [])

    def test_negativa_dopo_mancante(self):
        testo = QUEST_MD.replace("- ULTIMATUM: RANIERO: La fornace è accesa. Spoleto si tenga pure il suo passo.\n", "")
        self.assertEqual(fasi_senza_dopo(GS.QUEST, GS.leggi_quest(testo)), [("Q-SM01", "ULTIMATUM")])

    def test_negativa_attesa_mancante(self):
        testo = re.sub(r"### Attesa \(presa, meno di 4 radici\)\n\n- AGNESE: [^\n]*\n", "", QUEST_MD)
        with self.assertRaisesRegex(GS.ErroreStoria, "Q-SA01 senza attesa"):
            GS.leggi_quest(testo)

    def test_righe_di_raccolta(self):
        """Q-SM01: le tre righe di SISTEMA una per blocco, Antonio al primo se e' nel gruppo. Q-SA01: SISTEMA a
        ogni radice, Antonio alla prima, Ubaldo alla prima senza la quest presa."""
        ferro = [b["guardia"] for b in self.letto["Q-SM01"]["raccolta"]]
        self.assertEqual(ferro, [("CONTEGGIO", 0, 1, GS.NESSUNA), ("CONTEGGIO", 0, 2, GS.NESSUNA), ("CONTEGGIO", 0, 3, GS.NESSUNA),
                                 ("CONTEGGIO", 0, 1, GS.indice("ANTONIO_NEL_GRUPPO"))])
        erbe = [(b["chi"], b["guardia"]) for b in self.letto["Q-SA01"]["raccolta"]]
        self.assertEqual(erbe, [("SISTEMA", GS.SEMPRE), ("ANTONIO", ("CONTEGGIO", 1, 1, GS.NESSUNA)),
                                ("UBALDO", ("CONTEGGIO_E_NON_BANDIERA", 1, 1, GS.indice("Q_SA01_PRESA")))])

    def test_negativa_antonio_a_ogni_radice(self):
        """Senza la riga «Alla prima radice, una volta sola:» Antonio parlerebbe a ogni radice."""
        testo = QUEST_MD.replace("Alla prima radice, una volta sola:\n\n", "")
        erbe = [(b["chi"], b["guardia"]) for b in GS.leggi_quest(testo)["Q-SA01"]["raccolta"]]
        self.assertEqual(erbe[1], ("ANTONIO", GS.SEMPRE))

    def test_la_consegna_dopo_il_condotto(self):
        agnese = [b["guardia"] for b in self.letto["Q-SA01"]["consegna"]]
        self.assertEqual(agnese[-1], ("BANDIERA", GS.indice("CONDOTTO_SALVO"), 0, 0))
        self.assertTrue(all(g == GS.SEMPRE for g in agnese[:-1]))

    def test_gli_indizi(self):
        _, npc = GS.leggi_copione()
        d = self.letto["Q-SP01"]
        self.assertEqual([i["bandiera"] for i in d["indizi"]], INDIZI)
        nomi = [npc[GS.npc_dell_indizio(i, npc)]["nome"] for i in d["indizi"]]
        self.assertTrue(nomi[0].startswith("Lucia") and nomi[1].startswith("Venditore") and nomi[2] == "Giordano", nomi)
        self.assertTrue(d["completi"] and d["infiltrato_prima"] and d["infiltrato_dopo"])
        self.assertIn("Hai ripreso la Rosa", d["infiltrato_dopo"][-1]["frase"])

    def test_negativa_indizio_di_nessuno(self):
        _, npc = GS.leggi_copione()
        finto = {"nome": "Nessuno", "bandiera": "INDIZIO_LUCIA", "frasi": [GS.battuta("TIZIO", None, "Ciao.", "x")]}
        with self.assertRaisesRegex(GS.ErroreStoria, "non ha un solo NPC"):
            GS.npc_dell_indizio(finto, npc)

    def test_negativa_sezione_sconosciuta(self):
        with self.assertRaisesRegex(GS.ErroreStoria, "sezione «Ricompensa»"):
            GS.leggi_quest(QUEST_MD.replace("### Attesa (presa, meno di 3 blocchi)", "### Ricompensa"))


class NelGioco(unittest.TestCase):

    def test_la_scena_chiama_la_logica(self):
        self.assertEqual(chiamate_mancanti(SCENA_CPP), [])

    def test_negativa_consegna_mai_chiamata(self):
        alterato = SCENA_CPP.replace("consegna_quest(g_game_state", "consegna_finta(g_game_state")
        self.assertEqual(chiamate_mancanti(alterato), ["consegna_quest(g_game_state"])

    def test_le_tabelle_in_storia_h(self):
        self.assertIn("inline constexpr QuestGioco QUEST_GIOCO[QUEST] = {", STORIA_H)
        self.assertIn(f"inline constexpr int RACCOLTE = {len(GS.RACCOLTE)};", STORIA_H)
        self.assertIn("inline constexpr Infiltrato INFILTRATO = { int8_t(mondo::AreaId::PIAZZA_QUARANTA_MARTIRI)", STORIA_H)
        self.assertIn("    { Q_SM01_PRESA, 80, 3, int8_t(mondo::AreaId::SAN_MARTINO)", STORIA_H)


if __name__ == "__main__":
    unittest.main()
