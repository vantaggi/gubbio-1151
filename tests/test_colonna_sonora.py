"""F7c: la colonna sonora nel gioco (musica/colonna_sonora.txt -> tools/genera_colonna_sonora.py ->
include/colonna_sonora.h).

Ogni area ha un brano in ogni fase, ogni brano e ogni effetto citato esiste in audio/, nessun file di audio/
resta orfano, ogni cutscene e ogni evento di battaglia ha la sua riga, il segnale di Fazio sta davanti alla
sua bottega. Ogni regola ha la sua negativa: il generatore deve rifiutare i dati sbagliati.
"""
import importlib.util
import os
import re
import unittest

RADICE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def _carica(nome):
    spec = importlib.util.spec_from_file_location(nome, os.path.join(RADICE, "tools", nome + ".py"))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


GC = _carica("genera_colonna_sonora")


def _sorgenti_cpp():
    out = {}
    for n in sorted(os.listdir(os.path.join(RADICE, "src"))):
        if n.endswith(".cpp"):
            with open(os.path.join(RADICE, "src", n), encoding="utf-8") as f:
                out[n] = f.read()
    return out


class ColonnaSonora(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(GC.DATI, encoding="utf-8") as f:
            cls.testo = f.read()
        cls.dati = GC.leggi_dati(cls.testo)
        cls.gioco = GC.gioco_del_repo()
        cls.audio = GC.audio_del_repo()
        cls.amici = GC.amici_del_repo()
        cls.luoghi = GC.luoghi_del_mondo({(l["area"], l["edificio"]) for l in cls.dati["luoghi"]})

    def genera(self, testo=None, audio=None, gioco=None, luoghi=None):
        return GC.genera(testo if testo is not None else self.testo, gioco or self.gioco, audio or self.audio,
                         luoghi if luoghi is not None else self.luoghi, self.amici)

    def rifiuta(self, testo=None, audio=None, gioco=None, luoghi=None, dice=""):
        with self.assertRaises(GC.ErroreColonna) as e:
            self.genera(testo, audio, gioco, luoghi)
        self.assertIn(dice, str(e.exception))

    def senza_riga(self, inizio):
        righe = [r for r in self.testo.splitlines() if not r.startswith(inizio)]
        self.assertEqual(len(righe), len(self.testo.splitlines()) - 1, inizio)
        return "\n".join(righe)

    # --- l'header -----------------------------------------------------------------------------------
    def test_header_aggiornato(self):
        with open(GC.USCITA, encoding="utf-8") as f:
            self.assertEqual(f.read(), self.genera(), "python tools/genera_colonna_sonora.py --scrivi")

    def test_il_controllo_del_generatore_passa(self):
        self.assertEqual(GC.main([]), 0)

    # --- ogni area ha il suo brano, in ogni fase -----------------------------------------------------
    def test_ogni_area_ha_un_brano_in_ogni_fase(self):
        brani = set(self.audio[0])
        self.assertEqual(sorted(self.dati["aree"]), sorted(self.gioco["aree"]))
        self.assertEqual(len(self.gioco["aree"]), 25)   # le 19 di prima e i 6 interni esplorabili
        for area, riga in self.dati["aree"].items():
            self.assertEqual(len(riga), len(GC.FASI), area)
            for b in riga:
                self.assertIn(b, brani, area)
                self.assertTrue(self.audio[2][b], f"{area}: {b} e' un jingle, l'area resterebbe muta")

    def test_negativa_area_senza_brano(self):
        self.rifiuta(self.senza_riga("area TEATRO_ROMANO"), dice="area TEATRO_ROMANO: senza brano")

    def test_negativa_area_con_una_fase_in_meno(self):
        testo = self.testo.replace("area SAN_PIETRO                 citta        citta        notte",
                                   "area SAN_PIETRO                 citta        notte")
        self.assertNotEqual(testo, self.testo)
        self.rifiuta(testo, dice="SAN_PIETRO")

    def test_negativa_area_inventata(self):
        self.rifiuta(self.testo + "\narea PIAZZA_DEL_MERCATO citta citta notte bandiere\n", dice="PIAZZA_DEL_MERCATO")

    def test_le_fasi_seguono_la_storia(self):
        pg = self.dati["aree"]["PIAZZA_GRANDE"]
        self.assertEqual(dict(zip(GC.FASI, pg)), {"giorno": "citta", "digiuno": "citta", "notte": "notte", "alba": "bandiere"})
        self.assertEqual(self.dati["aree"]["BASILICA_INTERNO"], ["basilica"] * 4)
        for gola in ("BOTTACCIONE", "GOLA_STRISCIA", "GOLA_MIASMI", "GOLA_ARCO", "CONDOTTO"):
            self.assertEqual(self.dati["aree"][gola], ["bottaccione"] * 4, gola)

    # --- ogni brano citato esiste ---------------------------------------------------------------------
    def test_negativa_brano_che_non_esiste(self):
        self.rifiuta(self.testo.replace("cutscene C1   prologo", "cutscene C1   prologo_lungo"), dice="prologo_lungo")
        self.rifiuta(self.testo.replace("vittoria   vittoria", "vittoria   trionfo"), dice="trionfo")

    def test_negativa_effetto_che_non_esiste(self):
        self.rifiuta(self.testo.replace("evento HIT             colpo", "evento HIT             schiaffo"),
                     dice="schiaffo")
        self.rifiuta(self.testo.replace("uso SALVA      salva", "uso SALVA      sigillo"), dice="sigillo")

    def test_negativa_brano_tolto_da_audio(self):
        brani, effetti, anelli = self.audio
        self.rifiuta(audio=([b for b in brani if b != "fazio"], effetti, anelli), dice="'fazio' non c'e' in audio/")

    # --- nessun file di audio/ orfano ----------------------------------------------------------------
    def test_nessun_file_orfano(self):
        brani, effetti, _ = self.audio
        presenti = sorted(os.listdir(os.path.join(RADICE, "audio")))
        self.assertEqual(presenti, sorted([b + ".xm" for b in brani] + [e + ".wav" for e in effetti]))
        self.assertEqual((len(brani), len(effetti)), (19, 13))
        h = self.genera()
        for b in brani:
            self.assertIn(f"Brano::{b.upper()}", h.split("enum class Effetto")[1], f"{b}.xm non e' usato")

    def test_negativa_file_orfano(self):
        brani, effetti, anelli = self.audio
        self.rifiuta(audio=(brani + ["zampogna"], effetti, dict(anelli, zampogna=True)), dice="zampogna.xm")
        self.rifiuta(audio=(brani, effetti + ["tuono"], anelli), dice="tuono.wav")

    def test_negativa_brano_non_piu_usato(self):
        # senza la taverna lo stornello resta orfano
        self.rifiuta(self.senza_riga("luogo taverna"), dice="taverna.xm")
        self.rifiuta(self.testo.replace("cutscene C4   terza_alba     campanone", "cutscene C4   terza_alba"),
                     dice="campanone.wav")

    def test_ogni_uso_degli_effetti_e_nel_codice(self):
        codice = "\n".join(_sorgenti_cpp().values())
        for uso in self.dati["uso"]:
            self.assertRegex(codice, r"Suono::" + uso + r"\b", f"Suono::{uso} non e' usato in src/")
        self.assertNotRegex(codice, r"Suono::FANFARA\b", "negativa: la ricerca trova solo gli usi veri")

    # --- cutscene ---------------------------------------------------------------------------------------
    def test_ogni_cutscene_ha_la_sua_riga(self):
        self.assertEqual(sorted(self.dati["cutscene"]), sorted(self.gioco["cutscene"]))
        attesi = {"C1": "prologo", "C2": "undici_bandiere", "C2P": "pastorale", "C3A": "presentazione",
                  "C3C": "presentazione", "C3G": "presentazione", "C3U": "presentazione", "C4": "terza_alba"}
        for c, b in attesi.items():
            self.assertEqual(self.dati["cutscene"][c][0], b, c)
        self.assertEqual(self.dati["cutscene"]["C4"][1], "campanone")

    def test_coerente_con_i_brani_delle_cutscene_di_test_audio(self):
        test_audio = _carica_test("test_audio")
        codici = {"c1_prologo": "C1", "c2_undici_bandiere": "C2", "c2p_pastorale": "C2P", "c3_ubaldo": "C3U",
                  "c4_terza_alba": "C4"}
        for brano, regia in test_audio.CUTSCENE.items():
            self.assertEqual(self.dati["cutscene"][codici[regia]][0], brano, regia)

    def test_negativa_cutscene_senza_riga(self):
        self.rifiuta(self.senza_riga("cutscene C7S"), dice="cutscene C7S: senza riga")

    def test_negativa_cutscene_inventata(self):
        self.rifiuta(self.testo + "\ncutscene C8 prologo\n", dice="cutscene C8")

    def test_negativa_cutscene_scritta_due_volte(self):
        self.rifiuta(self.testo + "\ncutscene C1 titolo\n", dice="gia' scritta")

    # --- battaglia ----------------------------------------------------------------------------------------
    def test_battaglia_e_duello(self):
        h = self.genera()
        riga = re.search(r"BRANO_INCONTRO\[INCONTRI\] = \{(.*?)\};", h).group(1)
        brani = [b.strip() for b in riga.split(",")]
        self.assertEqual(len(brani), self.gioco["incontri"])
        self.assertEqual(brani[2], "Brano::CORRADO")
        self.assertEqual(brani.count("Brano::CORRADO"), 1)
        self.assertTrue(all(b in ("Brano::BATTAGLIA", "Brano::CORRADO") for b in brani))

    def test_ogni_evento_ha_la_sua_riga(self):
        self.assertEqual(sorted(self.dati["eventi"]), sorted(self.gioco["eventi"]))

    def test_negativa_evento_senza_riga(self):
        self.rifiuta(self.senza_riga("evento DEFEAT"), dice="evento DEFEAT")

    def test_negativa_duello_fuori_dagli_incontri(self):
        self.rifiuta(self.testo.replace("duello     2  corrado", "duello     9  corrado"), dice="duello 9")

    # --- luoghi: la taverna e il segnale di Fazio --------------------------------------------------------
    def test_il_segnale_di_fazio_entrando_in_bottega(self):
        """Con gli interni (pezzo INT) il segnale suona entrando nella bottega dei conti: l'area intera."""
        h = self.genera()
        m = re.search(r"\{ (\d+), (\d+), (\d+), (\d+), (\d+), Brano::FAZIO, Modo::SEGNALE, (\d+) \}", h)
        self.assertIsNotNone(m)
        area, x0, y0, x1, y1, npc = map(int, m.groups())
        self.assertEqual(self.gioco["aree"][area], "BOTTEGA_CONTI_INTERNO")
        self.assertEqual(self.gioco["npc"][npc], ("Fazio", "BOTTEGA_CONTI_INTERNO"))
        _, w, hh = self.luoghi[("BOTTEGA_CONTI_INTERNO", "*")]
        self.assertEqual((x0, y0, x1, y1), (0, 0, w - 1, hh - 1))

    def test_la_taverna_suona_dentro_la_taverna(self):
        h = self.genera()
        m = re.search(r"\{ (\d+), (\d+), (\d+), (\d+), (\d+), Brano::TAVERNA, Modo::FONDO, (-?\d+) \}", h)
        self.assertIsNotNone(m)
        self.assertEqual(self.gioco["aree"][int(m.group(1))], "TAVERNA_INTERNO")

    def test_negativa_luogo_su_un_edificio_di_un_altra_area(self):
        testo = self.testo.replace("luogo fazio    BOTTEGA_CONTI_INTERNO  *", "luogo fazio    SAN_PIETRO  bottega_conti")
        luoghi = dict(self.luoghi)
        self.rifiuta(testo, luoghi=luoghi, dice="SAN_PIETRO non ha l'edificio bottega_conti")

    def test_negativa_amico_in_un_altra_area(self):
        testo = self.testo.replace("0  fazio    segnale  FAZIO", "0  fazio    segnale  PADELLINO")
        self.rifiuta(testo, dice="Padellino non sta in BOTTEGA_CONTI_INTERNO")

    def test_negativa_segnale_uguale_al_brano_dell_area(self):
        testo = self.testo.replace("luogo fazio    BOTTEGA_CONTI_INTERNO  *  0  fazio    segnale",
                                   "luogo fazio    BOTTEGA_CONTI_INTERNO  *  0  citta    segnale")
        self.rifiuta(testo, dice="stesso brano dell'area")

    def test_negativa_riga_sconosciuta(self):
        self.rifiuta(self.testo + "\nvolume 3\n", dice="riga sconosciuta")


def _carica_test(nome):
    spec = importlib.util.spec_from_file_location(nome, os.path.join(RADICE, "tests", nome + ".py"))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


if __name__ == "__main__":
    unittest.main()
