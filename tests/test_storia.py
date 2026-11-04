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
    """Il gemello Python di storia::gioca_tutta: l'ordine delle scene visitate (la prima pronta nell'ordine
    del copione; ogni menu prende la prima voce)."""
    accese, fatte, ordine = set(), set(), []
    avanti = True
    while avanti:
        avanti = False
        for s in scene:
            c = s["codice"]
            if c in fatte:
                continue
            if not set(s["richieste"]) <= accese or set(s["vietate"]) & accese:
                continue
            if c in GS.SEGUE and GS.SEGUE[c] not in fatte:
                continue
            accese |= set(s["imposta"]) | {GS.TUTTE[b["accende"][0]] for b in s["battute"]
                                          if b["voci"] and b["accende"][0] != GS.NESSUNA}
            fatte.add(c)
            ordine.append(c)
            avanti = True
            break
    return ordine, accese


def scritte_non_lette(scene, lette_dal_gioco):
    lette = set(lette_dal_gioco)
    for s in scene:
        lette |= set(s["richieste"]) | set(s["vietate"])
    scritte = {b for s in scene for b in s["imposta"]}
    return sorted(scritte - lette)


def codice_che_legge():
    """Il codice che legge le bandiere: la logica della storia, la scena, e le tabelle delle quest di storia.h
    (QUEST_V1; e, per le quest giocabili, QUEST_GIOCO, RACCOLTA e INDIZIO; per la gola, FORZIERE; per F10,
    GUARDIA_FORNACE e BATTAGLIA_A_META)."""
    codice = "".join(open(os.path.join(RADICE, p), encoding="utf-8").read()
                     for p in ("include/storia_logica.h", "src/storia_scena.cpp"))
    storia_h = open(GS.USCITA_H, encoding="utf-8").read()
    tabelle = [r"inline constexpr Quest QUEST_V1\[QUEST\] = \{.*?\n\};",
               r"inline constexpr QuestGioco QUEST_GIOCO\[QUEST\] = \{.*?\n\};",
               r"inline constexpr Raccolta RACCOLTA\[RACCOLTE\] = \{.*?\n\};",
               r"inline constexpr Indizio INDIZIO\[INDIZI\] = \{.*?\n\};",
               r"inline constexpr Forziere FORZIERE\[FORZIERI\] = \{.*?\n\};",
               r"inline constexpr GuardiaFornace GUARDIA_FORNACE\[GUARDIE_FORNACE\] = \{.*?\n\};"]
    return codice + "".join(re.search(r, storia_h, re.S).group(0) for r in tabelle)


def righe_da_fare(doc):
    """Le bandiere della prima tabella di docs/bandiere_da_fare.md (quelle che il gioco non legge ancora)."""
    tabella = doc.split("\n## ")[0]
    return re.findall(r"^\| `([A-Z0-9_]+)` \|", tabella, re.M)


def lette_dal_gioco_senza_codice(lette, codice):
    """Le bandiere di LETTE_DAL_GIOCO che il codice non nomina: Bandiera::X per la storia (0-63), il nome per
    quelle delle quest (64-127, costanti di storia.h)."""
    mancano = []
    for b in lette:
        if b in GS.BANDIERE_QUEST:
            if not re.search(r"\b%s\b" % b, codice):
                mancano.append(b)
        elif f"Bandiera::{b}" not in codice:
            mancano.append(b)
    return sorted(mancano)


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
    return sorted(re.findall(r"^Scena ([A-Z0-9]+-\d+[a-z]?)$", log.split("Giro 1\n")[0], re.M))


def griglia_area(nome):
    """Le righe della griglia di mondo/aree/<nome>.area (dopo «griglia», larghe quanto dice «dimensioni»)."""
    testo = open(os.path.join(RADICE, "mondo", "aree", nome + ".area"), encoding="utf-8").read()
    largo = int(re.search(r"^dimensioni (\d+) \d+$", testo, re.M).group(1))
    return [r for r in testo.split("\ngriglia\n", 1)[1].splitlines() if len(r) == largo]


def ceri_dell_altare(logica):
    """La tabella CERO_ALTARE di storia_logica.h: [(area, tx, ty)]."""
    corpo = re.search(r"CERO_ALTARE\[CERI_ALTARE\] = \{(.*?)\n\};", logica, re.S).group(1)
    return [(a, int(x), int(y)) for a, x, y in re.findall(r"AreaId::(\w+)\), (\d+), (\d+) \}", corpo)]


def errori_ceri(ceri, griglie):
    """Ogni cero della tabella sta nell'interno della Basilica, sulla cella in alto a sinistra di un blocco 2x4 di
    'e'; ogni blocco di 'e' ha il suo cero; nessun'altra area ha celle 'e' (regola di Cioti)."""
    err = []
    for area, tx, ty in ceri:
        if area != "BASILICA_INTERNO":
            err.append(f"cero fuori dalla Basilica: {area}")
            continue
        g = griglie["basilica_interno"]
        blocco = [g[ty + dy][tx + dx] for dy in range(4) for dx in range(2) if ty + dy < len(g) and tx + dx < len(g[0])]
        if blocco != ["e"] * 8 or (tx > 0 and g[ty][tx - 1] == "e") or (ty > 0 and g[ty - 1][tx] == "e"):
            err.append(f"({tx}, {ty}) non e' l'angolo di un cero")
    celle = sum(r.count("e") for r in griglie["basilica_interno"])
    if celle != 8 * len([c for c in ceri if c[0] == "BASILICA_INTERNO"]):
        err.append(f"{celle} celle di ceri per {len(ceri)} ceri in tabella")
    for nome, g in griglie.items():
        if nome != "basilica_interno" and any("e" in r for r in g):
            err.append(f"ceri fuori dalla Basilica: {nome}")
    return err


class CeriDellaBasilica(unittest.TestCase):
    """F10: con CERI_RISVEGLIATI una fiamma sopra ognuno dei tre ceri dell'altare (CERO_ALTARE)."""

    def setUp(self):
        self.logica = open(os.path.join(RADICE, "include", "storia_logica.h"), encoding="utf-8").read()
        nomi = [f[:-5] for f in os.listdir(os.path.join(RADICE, "mondo", "aree")) if f.endswith(".area")]
        self.griglie = {n: griglia_area(n) for n in nomi}

    def test_i_tre_ceri_sulla_griglia(self):
        ceri = ceri_dell_altare(self.logica)
        self.assertEqual(len(ceri), 3)
        self.assertEqual(errori_ceri(ceri, self.griglie), [])

    def test_negativa_cero_spostato(self):
        ceri = ceri_dell_altare(self.logica)
        ceri[1] = (ceri[1][0], ceri[1][1] + 1, ceri[1][2])
        self.assertEqual(len(errori_ceri(ceri, self.griglie)), 1)

    def test_negativa_cero_fuori_dalla_basilica(self):
        ceri = ceri_dell_altare(self.logica)
        ceri[0] = ("BASILICA", ceri[0][1], ceri[0][2])
        self.assertIn("cero fuori dalla Basilica: BASILICA", errori_ceri(ceri, self.griglie))
        griglie = dict(self.griglie)
        griglie["piazza_grande"] = griglie["piazza_grande"][:1] + ["e" + r[1:] for r in griglie["piazza_grande"][1:2]]
        self.assertIn("ceri fuori dalla Basilica: piazza_grande", errori_ceri(ceri_dell_altare(self.logica), griglie))

    def test_la_fiamma_coi_colori_della_palette(self):
        """La fiamma usa solo il contorno, il vermiglio, l'oro e il bianco della palette dei popolani."""
        fiamma = GS.FN.FIGURE_RACCOLTE["fiamma_cero"]
        self.assertEqual(set("".join(fiamma)) - {"."}, {"1", "5", "e", "6"})
        self.assertIn("inline constexpr int FIGURA_FIAMMA_CERO = 4;", open(GS.USCITA_H, encoding="utf-8").read())

    def test_la_scena_mette_le_fiamme(self):
        scena = open(os.path.join(RADICE, "src", "storia_scena.cpp"), encoding="utf-8").read()
        self.assertIn("k < CERI_ALTARE && ceri_accesi(g_game_state)", scena)
        self.assertIn("crea_raccolta(palette, FIGURA_FIAMMA_CERO)", scena)


class GeneratoAggiornato(unittest.TestCase):

    def test_file_generati_aggiornati(self):
        h, t = GS.genera()
        with open(GS.USCITA_H, encoding="utf-8") as f:
            self.assertEqual(f.read(), h, "eseguire python tools/genera_storia.py --scrivi")
        with open(GS.USCITA_TESTI, encoding="utf-8") as f:
            self.assertEqual(f.read(), t)

    def test_negativa_battuta_cambiata(self):
        scene = copy.deepcopy(SCENE)
        scene[3]["battute"][0]["frase"] = scene[3]["battute"][0]["frase"] + " Anzi no."
        with open(GS.USCITA_TESTI, encoding="utf-8") as f:
            self.assertNotEqual(f.read(), GS.testi_del_copione(scene, NPC))


class Tabelle(unittest.TestCase):

    def test_le_scene_del_copione(self):
        self.assertEqual(len(SCENE), 20)
        self.assertEqual(sum(len(s["battute"]) for s in SCENE), 229)
        self.assertEqual(len(NPC), 14 + 24)                 # gli NPC d'ambiente (con Fra' Matteo, revisione) e gli amici

    def test_ogni_bandiera_scritta_e_letta(self):
        """Letta da una scena, dal gioco (LETTE_DAL_GIOCO, ognuna col suo punto nel codice) o in elenco
        in docs/bandiere_da_fare.md con quel che dovra' fare."""
        self.assertEqual(scritte_non_lette(SCENE, set(GS.LETTE_DAL_GIOCO) | set(GS.DA_FARE)), [])
        doc = open(os.path.join(RADICE, "docs", "bandiere_da_fare.md"), encoding="utf-8").read()
        for b in GS.DA_FARE:
            self.assertIn(f"| `{b}` |", doc, b)
        self.assertEqual(lette_dal_gioco_senza_codice(GS.LETTE_DAL_GIOCO, codice_che_legge()), [])

    def test_negativa_letta_dal_gioco_senza_codice(self):
        """Una bandiera dichiarata letta dal gioco che il codice non nomina viene segnalata (della storia e quest)."""
        codice = codice_che_legge().replace("Bandiera::CRONACA_V1_FINITA", "Bandiera::X")
        codice = re.sub(r"\bRUFINO_ASCOLTATO\b", "RUFINO", codice)
        self.assertEqual(lette_dal_gioco_senza_codice(GS.LETTE_DAL_GIOCO, codice), ["CRONACA_V1_FINITA", "RUFINO_ASCOLTATO"])

    def test_nessuna_bandiera_da_fare(self):
        """F10: CERI_RISVEGLIATI era l'ultima; ora il gioco le legge tutte e la tabella del documento e' vuota."""
        self.assertEqual(GS.DA_FARE, [])
        doc = open(os.path.join(RADICE, "docs", "bandiere_da_fare.md"), encoding="utf-8").read()
        self.assertEqual(righe_da_fare(doc), [])

    def test_negativa_bandiera_da_fare_senza_documento(self):
        doc = open(os.path.join(RADICE, "docs", "bandiere_da_fare.md"), encoding="utf-8").read()
        self.assertNotIn("CERI_RISVEGLIATI", righe_da_fare(doc))
        riga = "| `CERI_RISVEGLIATI` | A1-08 | x | y |\n"
        self.assertEqual(righe_da_fare(doc.replace("| :-- | :-- | :-- | :-- |\n", "| :-- | :-- | :-- | :-- |\n" + riga, 1)),
                         ["CERI_RISVEGLIATI"])

    def test_negativa_ceri_senza_codice(self):
        """CERI_RISVEGLIATI e' letta dal gioco solo se il codice la nomina (storia::ceri_accesi())."""
        codice = codice_che_legge().replace("Bandiera::CERI_RISVEGLIATI", "Bandiera::X")
        self.assertEqual(lette_dal_gioco_senza_codice(GS.LETTE_DAL_GIOCO, codice), ["CERI_RISVEGLIATI"])

    def test_negativa_bandiera_scritta_e_mai_letta(self):
        """Togliendo CERI_RISVEGLIATI da quelle lette dal gioco, resta scritta e mai letta; togliendo
        MIASMI_VISTI (T2), lo stesso."""
        lette = set(GS.LETTE_DAL_GIOCO) - {"CERI_RISVEGLIATI"}
        self.assertEqual(scritte_non_lette(SCENE, lette | set(GS.DA_FARE)), ["CERI_RISVEGLIATI"])
        lette = set(GS.LETTE_DAL_GIOCO) - {"MIASMI_VISTI"}
        self.assertEqual(scritte_non_lette(SCENE, lette | set(GS.DA_FARE)), ["MIASMI_VISTI"])

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
            self.assertTrue(all(b["fase"] in GS.FASI for b in p["frasi"]))
        storia_h = open(GS.USCITA_H, encoding="utf-8").read()
        self.assertIn(f"inline constexpr int NPC = {len(NPC)};", storia_h)

    def test_la_storia_sul_gba(self):
        """La ROM GUBBIO_AVVIO=8 ha recitato ogni scena, dalla prima ai titoli di coda (log in tests/dati)."""
        log = open(os.path.join(RADICE, "tests", "dati", "storia_mgba.txt"), encoding="utf-8").read()
        self.assertEqual(scene_del_log(log), sorted(s["codice"] for s in SCENE))
        self.assertIn("Storia: 20 scene visitate su 20, 0 mancanti, titoli di coda raggiunti", log)
        # due giri: ogni menu prende la prima voce, poi la seconda; ogni scena in tutti e due
        primo, secondo = log.split("Giro 1\n")
        self.assertEqual(sorted(re.findall(r"^Scena (\S+)$", secondo, re.M)), sorted(s["codice"] for s in SCENE))
        self.assertIn("Giro 0: 20 scene, borgo dentro, esule prigioniero, giustizia offerta", primo)
        self.assertIn("Giro 1: 20 scene, borgo fuori, esule liberato, giustizia no", secondo)
        # quattro menu per giro: D1, D2, D3 e la conferma dell'alba di B-05 (ALBA_CONFERMATA, REVa)
        self.assertEqual(primo.count("Scelta 0"), 4)
        self.assertEqual(secondo.count("Scelta 1"), 4)
        self.assertIn("Cutscene C1 finita", log)
        self.assertIn("Cutscene P-02 dentro la precedente", log)
        self.assertIn("Cutscene C4 finita", log)

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


class Inserti(unittest.TestCase):
    """Le cutscene dentro le scene (pezzo X): C2 prima che parli l'araldo, C2P prima che risponda Ubaldo."""

    def parlante(self, codice, k):
        return next(s for s in SCENE if s["codice"] == codice)["battute"][k][0]

    def test_c2_prima_dell_araldo_e_c2p_prima_di_ubaldo(self):
        self.assertEqual({k: c for k, c in GS.INSERTI["A1-01"].items() if c.startswith("C2")}, {4: "C2", 8: "C2P"})
        self.assertEqual(self.parlante("A1-01", 4), "ARALDO")
        self.assertNotEqual(self.parlante("A1-01", 3), "ARALDO")
        self.assertEqual(self.parlante("A1-01", 8), "UBALDO")
        self.assertEqual(self.parlante("A1-01", 7), "ARALDO")
        h = open(os.path.join(RADICE, "include", "storia.h"), encoding="utf-8").read()
        prima = sum(len(s["battute"]) for s in SCENE[:[s["codice"] for s in SCENE].index("A1-01")])
        self.assertIn(f"{{ {prima + 4}, {GS.codici_regia().index('C2')}, 0 }},", h)

    def test_sul_gba_c2_e_c2p_dentro_a1_01(self):
        """Nei log di mGBA (storia intera e prologo giocabile) C2 e poi C2P si recitano dentro A1-01,
        prima della scena dopo."""
        for nome in ("storia_mgba.txt", "prologo_mgba.txt"):
            righe = open(os.path.join(RADICE, "tests", "dati", nome), encoding="utf-8").read().splitlines()
            righe = [r for r in righe if not r.startswith("Istantanea ")]   # le foto del banco non contano
            a = righe.index("Scena A1-01")
            dopo = [r for r in righe[a + 1:] if not r.startswith("Cutscene C3")]
            self.assertEqual(dopo[:4], ["Cutscene C2", "Cutscene C2 finita", "Cutscene C2P", "Cutscene C2P finita"], nome)
            self.assertTrue(dopo[4].startswith("Scena "), nome)
            self.assertEqual(righe[a + 1:a + 5], ["Cutscene C3U", "Cutscene C3U finita", "Cutscene C3G", "Cutscene C3G finita"], nome)

    def test_negativa_log_senza_c2(self):
        righe = open(os.path.join(RADICE, "tests", "dati", "storia_mgba.txt"), encoding="utf-8").read().splitlines()
        senza = [r for r in righe if not r.startswith("Cutscene C2") and not r.startswith("Cutscene C3")]
        a = senza.index("Scena A1-01")
        self.assertNotEqual(senza[a + 1:a + 5], ["Cutscene C2", "Cutscene C2 finita", "Cutscene C2P", "Cutscene C2P finita"])

    def prima_volta(self, codice, chi):
        return next(k for k, b in enumerate(next(s for s in SCENE if s["codice"] == codice)["battute"]) if b[0] == chi)

    def test_presentazioni_prima_che_il_personaggio_parli(self):
        """C3 entra prima della prima battuta del personaggio nella sua scena; Ubaldo, che c'e' gia' dalla
        prima scena, dopo il cartello della piazza e prima di ogni altra voce."""
        self.assertEqual(GS.INSERTI["A1-01"][self.prima_volta("A1-01", "GIORGIO")], "C3G")
        self.assertEqual(GS.INSERTI["A1-04"][self.prima_volta("A1-04", "ANTONIO")], "C3A")
        self.assertEqual(GS.INSERTI["B-04"][self.prima_volta("B-04", "CORRADO")], "C3C")
        a101 = next(s for s in SCENE if s["codice"] == "A1-01")["battute"]
        self.assertEqual(GS.INSERTI["A1-01"][1], "C3U")
        self.assertNotIn(a101[0][0], GS.PARLANTI)
        self.assertIn(a101[1][0], GS.PARLANTI)

    def test_negativa_presentazione_dopo_la_prima_battuta(self):
        self.assertNotEqual(self.prima_volta("A1-04", "ANTONIO") + 1, [k for k, c in GS.INSERTI["A1-04"].items() if c == "C3A"][0])

    def test_c5_c6_c7_dove_dicono_le_schede(self):
        """F10: C5 prima del narratore di A1-08 (che la cutscene dice nelle bande: copre 1), C6 in A1-09 dopo
        lo scambio dei due indizi e prima che Ubaldo nomini il Bottaccione, C7S e C7B all'inizio di A1-07 e
        B-01; in storia.h col numero di battute coperte."""
        self.assertEqual(GS.INSERTI["A1-08"], {9: "C5"})
        self.assertEqual(self.parlante("A1-08", 9), "NARRATORE")
        self.assertEqual(self.parlante("A1-08", 8), "UBALDO")
        a109 = next(s for s in SCENE if s["codice"] == "A1-09")["battute"]
        self.assertEqual(GS.INSERTI["A1-09"], {3: "C6"})
        self.assertTrue(all(b["guardia"][0] == "ALMENO_DUE" for b in a109[:3]))
        self.assertEqual(a109[3]["guardia"][0], "SEMPRE")
        self.assertIn("Bottaccione", a109[3][2])
        self.assertEqual(GS.INSERTI["A1-07"], {0: "C7S"})
        self.assertEqual(GS.INSERTI["B-01"], {0: "C7B"})
        h = open(os.path.join(RADICE, "include", "storia.h"), encoding="utf-8").read()
        codici = [s["codice"] for s in SCENE]
        for scena, k, cut, copre in (("A1-08", 9, "C5", 1), ("A1-09", 3, "C6", 0), ("A1-07", 0, "C7S", 0), ("B-01", 0, "C7B", 0)):
            prima = sum(len(s["battute"]) for s in SCENE[:codici.index(scena)])
            self.assertIn(f"{{ {prima + k}, {GS.codici_regia().index(cut)}, {copre} }},", h, cut)
        self.assertEqual(GS.coperte(next(s for s in SCENE if s["codice"] == "A1-08"), 9, "C5"), 1)

    def test_negativa_c5_fuori_posto(self):
        """C5 dice nelle bande la battuta 9 di A1-08: inserita prima della 8 la si sentirebbe in anticipo."""
        vecchi = GS.INSERTI
        try:
            GS.INSERTI = {"A1-08": {8: "C5"}}
            with self.assertRaisesRegex(ValueError, "non vengono subito dopo l'inserto"):
                GS.genera()
            GS.INSERTI = {"A1-08": {10: "C5"}}
            with self.assertRaisesRegex(ValueError, "non vengono subito dopo l'inserto"):
                GS.genera()
        finally:
            GS.INSERTI = vecchi

    def test_negativa_inserto_su_una_battuta_gia_detta(self):
        """Un inserto su una battuta che la cutscene prima ha gia' detto nelle bande e' rifiutato."""
        vecchi, vecchia = GS.INSERTI, GS.narratore_della_regia
        try:
            GS.narratore_della_regia = lambda c: ["R_A1_08_09", "R_A1_08_10"] if c == "C5" else []
            GS.INSERTI = {"A1-08": {9: "C5", 10: "C3U"}}
            with self.assertRaisesRegex(ValueError, "l'ha gia' detta la cutscene prima"):
                GS.genera()
        finally:
            GS.INSERTI, GS.narratore_della_regia = vecchi, vecchia

    def test_le_battute_coperte_non_si_ripetono(self):
        """Nel lettore: dopo una cutscene recitata le battute coperte si saltano; una cutscene gia' vista
        (la scena rigiocata dopo una battaglia persa) le lascia alla vista di gioco."""
        cpp = open(os.path.join(RADICE, "src", "storia_scena.cpp"), encoding="utf-8").read()
        self.assertRegex(cpp, r"if\(recita_regia\(n\.regia[^)]*\)\)\s*\{\s*da \+= n\.copre;")
        self.assertIn("return false;", cpp[cpp.index("bool Storia::recita_regia"):cpp.index("bool Storia::recita(")])

    def test_negativa_lettore_che_ripete(self):
        cpp = open(os.path.join(RADICE, "src", "storia_scena.cpp"), encoding="utf-8").read()
        senza = cpp.replace("da += n.copre;", "")
        self.assertNotRegex(senza, r"if\(recita_regia\(n\.regia[^)]*\)\)\s*\{\s*da \+= n\.copre;")

    def test_negativa_inserto_su_una_battuta_che_non_c_e(self):
        vecchi = GS.INSERTI
        try:
            GS.INSERTI = {"A1-01": {99: "C2"}}
            with self.assertRaisesRegex(ValueError, "battuta o cutscene che non c'e'"):
                GS.genera()
            GS.INSERTI = {"A1-01": {4: "C7"}}
            with self.assertRaisesRegex(ValueError, "battuta o cutscene che non c'e'"):
                GS.genera()
        finally:
            GS.INSERTI = vecchi


    # F10, C7S all'ingresso degli Stradoni: la cartolina parte entrando nel Monte Ingino, non toccando l'Imboscata.
    def test_c7s_all_ingresso_del_monte(self):
        self.assertEqual(GS.ALL_INGRESSO, {"A1-07": "C7S"})
        self.assertEqual(GS.AREE["A1-07"], "MONTE_INGINO")
        h = open(os.path.join(RADICE, "include", "storia.h"), encoding="utf-8").read()
        codici = [s["codice"] for s in SCENE]
        self.assertIn(f"{{ {codici.index('A1-07')}, {GS.codici_regia().index('C7S')} }},", h)
        self.assertIn("inline constexpr int INGRESSI = 1;", h)

    def test_negativa_ingresso_senza_inserto_o_che_copre(self):
        """Una cartolina all'ingresso senza l'inserto alla battuta 0, che copre il narratore della scena, su una
        scena a schermo intero o con una cutscene che non c'e' e' rifiutata."""
        vecchi, vecchia = GS.ALL_INGRESSO, GS.coperte
        try:
            GS.ALL_INGRESSO = {"A1-07": "C7B"}
            with self.assertRaisesRegex(ValueError, "manca l'inserto alla battuta 0"):
                GS.genera()
            GS.ALL_INGRESSO = {"P-00": "C7S"}
            with self.assertRaisesRegex(ValueError, "a schermo intero"):
                GS.genera()
            GS.ALL_INGRESSO = {"A1-07": "C99"}
            with self.assertRaisesRegex(ValueError, "scena o cutscene che non c'e'"):
                GS.genera()
            GS.ALL_INGRESSO = {"A1-07": "C7S"}
            GS.coperte = lambda scena, k, codice: 1 if codice == "C7S" else vecchia(scena, k, codice)
            with self.assertRaisesRegex(ValueError, "copre battute del narratore"):
                GS.genera()
        finally:
            GS.ALL_INGRESSO, GS.coperte = vecchi, vecchia

    def _ordine_in_aggiorna(self, cpp):
        corpo = cpp[cpp.index("bool Storia::aggiorna"):]
        return corpo.index("cutscene_all_ingresso(") < corpo.index("pronta_qui(g_game_state")

    def test_c7s_prima_delle_scene_e_dei_nemici(self):
        """In Storia::aggiorna la cartolina viene prima delle scene; nel giro del gioco la storia si aggiorna
        prima dei nemici sulla mappa: C7S parte prima del contatto con l'Imboscata."""
        cpp = open(os.path.join(RADICE, "src", "storia_scena.cpp"), encoding="utf-8").read()
        self.assertTrue(self._ordine_in_aggiorna(cpp))
        self.assertRegex(cpp, r"recita_regia\(cartolina, &esplorazione")
        main = open(os.path.join(RADICE, "src", "main.cpp"), encoding="utf-8").read()
        self.assertLess(main.index("storia.aggiorna(esplorazione, palette)"), main.index("scontri.aggiorna(esplorazione, palette)"))

    def test_negativa_cartolina_dopo_le_scene(self):
        cpp = open(os.path.join(RADICE, "src", "storia_scena.cpp"), encoding="utf-8").read()
        corpo = cpp[cpp.index("bool Storia::aggiorna"):]
        a = corpo.index("    int cartolina")
        b = corpo.index("    // la cella sotto i piedi")
        blocco = corpo[a:b]
        spostato = corpo[:a] + corpo[b:]
        c = spostato.index("    if(k >= 0)")
        spostato = spostato[:c] + blocco + spostato[c:]
        self.assertFalse(self._ordine_in_aggiorna("bool Storia::aggiorna" + spostato[len("bool Storia::aggiorna"):]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
