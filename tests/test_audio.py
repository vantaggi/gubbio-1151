"""F7 audio: tools/genera_audio.py, le partiture musica/*.brano e i file generati in audio/.

audio/ e' generata, mai a mano: qui si controlla che sia aggiornata (i byte dei campioni possono
differire di 1 fra macchine diverse per l'arrotondamento dei seni, il resto deve coincidere),
che le partiture tornino (ogni riga lunga quanto la sua sezione, battute dritte), i limiti del GBA
(canali, righe, formato degli effetti) e che i brani delle cutscene durino quanto le cutscene.
"""
import importlib.util
import io
import os
import re
import unittest
import wave

RADICE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def _carica(nome):
    spec = importlib.util.spec_from_file_location(nome, os.path.join(RADICE, "tools", nome + ".py"))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


GA = _carica("genera_audio")

PROVA = """titolo: prova
bpm: 120
battuta: 16
canale a flauto
ordine: A
[A] 16
a: {riga}
"""

# brano -> cutscene (regia/*.regia) di cui e' la colonna sonora
CUTSCENE = {"prologo": "c1_prologo", "undici_bandiere": "c2_undici_bandiere", "pastorale": "c2p_pastorale",
            "presentazione": "c3_ubaldo", "terza_alba": "c4_terza_alba"}


def _wav(byte):
    with wave.open(io.BytesIO(byte)) as w:
        return w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()


class Audio(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.uscita = GA.genera_tutto()
        cls.brani = {n: GA.leggi_brano(n, t) for n, t in GA.sorgenti_del_repo()}

    def test_audio_aggiornata(self):
        presenti = sorted(f for f in os.listdir(GA.CARTELLA_AUDIO) if f.endswith((".xm", ".wav")))
        self.assertEqual(presenti, sorted(self.uscita), "python tools/genera_audio.py --scrivi")
        for nome, atteso in self.uscita.items():
            with open(os.path.join(GA.CARTELLA_AUDIO, nome), "rb") as f:
                reale = f.read()
            if reale == atteso:
                continue
            if nome.endswith(".wav"):
                self.assertEqual(_wav(reale), _wav(atteso), nome)
                self.assertLessEqual(_scarto(_wav_dati(atteso), _wav_dati(reale)), 1, nome)
                continue
            a, r = GA.leggi_xm(atteso), GA.leggi_xm(reale)
            self.assertEqual(a["pattern"], r["pattern"], f"{nome}: python tools/genera_audio.py --scrivi")
            self.assertEqual(a["ordine"], r["ordine"], nome)
            for sa, sr in zip(a["strumenti"], r["strumenti"]):
                self.assertEqual(sa["intestazione"], sr["intestazione"], nome)
                for (ca, ta), (cr, tr) in zip(sa["campioni"], sr["campioni"]):
                    self.assertEqual(ta, tr, nome)
                    self.assertEqual(len(ca), len(cr), nome)
                    self.assertLessEqual(_scarto(ca, cr), 1, nome)

    def test_xm_si_rilegge_tutto(self):
        for nome, dati in self.uscita.items():
            if nome.endswith(".xm"):
                x = GA.leggi_xm(dati)
                self.assertEqual(x["flag"] & 1, 1, "tabella lineare")
                self.assertLessEqual(x["canali"], 16, nome)
                self.assertEqual(x["canali"] % 2, 0, nome)
                for righe, _ in x["pattern"]:
                    self.assertLessEqual(righe, GA.MAX_RIGHE)

    def test_canali_entro_il_limite(self):
        for nome, b in self.brani.items():
            self.assertLessEqual(len(b["canali"]), GA.MAX_CANALI, nome)

    def test_negativa_troppi_canali(self):
        canali = "".join(f"canale c{i} flauto\n" for i in range(GA.MAX_CANALI + 1))
        with self.assertRaisesRegex(GA.ErroreMusica, "canali, il massimo"):
            GA.leggi_brano("troppi", "bpm: 120\n" + canali + "ordine: A\n[A] 4\nc0: C4:4\n")

    def test_negativa_riga_corta(self):
        with self.assertRaisesRegex(GA.ErroreMusica, "12 righe invece di 16"):
            GA.leggi_brano("prova", PROVA.format(riga="C4:4 D4:4 E4:4"))

    def test_negativa_battuta_storta(self):
        with self.assertRaisesRegex(GA.ErroreMusica, "battuta storta"):
            GA.leggi_brano("prova", PROVA.format(riga="C4:6 | D4:10"))

    def test_negativa_gettone_sconosciuto(self):
        with self.assertRaisesRegex(GA.ErroreMusica, "gettone non valido 'H4:16'"):
            GA.leggi_brano("prova", PROVA.format(riga="H4:16"))

    def test_negativa_strumento_sconosciuto(self):
        with self.assertRaisesRegex(GA.ErroreMusica, "strumento sconosciuto"):
            GA.leggi_brano("prova", PROVA.replace("flauto", "pianoforte").format(riga="C4:16"))

    def test_diesis_non_e_un_commento(self):
        b = GA.leggi_brano("prova", PROVA.format(riga="F#4:16  # commento"))
        self.assertEqual(b["sezioni"]["A"]["eventi"]["a"][0][2], GA.midi("F#4"))

    def test_gruppi_macro_e_trasposizione(self):
        testo = PROVA.replace("ordine", "def m: C4:2 D4:2\nordine").format(riga="($m)*2 $m+12 r:4")
        ev = GA.leggi_brano("prova", testo)["sezioni"]["A"]["eventi"]["a"]
        self.assertEqual([n for (_, t, n, _) in ev if t == "nota"], [60, 62, 60, 62, 72, 74])

    def test_intonazione(self):
        """Il C-4 del modulo e' il Do centrale: frequenza di lettura = f_campione * Do4 / f0."""
        for st in GA.strumenti().values():
            rel, fine = GA._intonazione(st)
            letta = 8363 * 2 ** ((rel + fine / 128) / 12)
            self.assertAlmostEqual(letta / (st.freq * GA.DO4 / st.f0), 1.0, delta=0.0005, msg=st.nome)

    def test_loop_dentro_il_campione(self):
        for st in GA.strumenti().values():
            if st.loop:
                inizio, lun = st.loop
                self.assertGreater(lun, 0, st.nome)
                self.assertLessEqual(inizio + lun, len(st.dati), st.nome)

    def test_effetti_nel_formato_di_butano(self):
        """8 bit, mono, 22050 Hz (consigliato da Butano), al massimo 3 secondi."""
        for nome, dati in self.uscita.items():
            if nome.endswith(".wav"):
                canali, larghezza, freq, n = _wav(dati)
                self.assertEqual((canali, larghezza, freq), (1, 1, GA.SFX_FREQ), nome)
                self.assertLessEqual(n / freq, 3.0, nome)

    def test_nomi_validi_per_butano(self):
        basi = [os.path.splitext(n)[0] for n in self.uscita]
        self.assertEqual(len(basi), len(set(basi)), "un brano e un effetto con lo stesso nome")
        for b in basi:
            self.assertRegex(b, r"^[a-z][a-z0-9_]*$")

    def test_brani_delle_cutscene_lunghi_quanto_le_cutscene(self):
        GR = _carica("genera_regia")
        durate = {os.path.splitext(os.path.basename(n))[0]: sum(i["frame"] for i in GR.leggi(n, t)["inquadrature"]) / 60
                  for n, t in GR.sorgenti_del_repo()}
        for brano, cut in CUTSCENE.items():
            b = self.brani[brano]
            self.assertIsNotNone(b["durata_attesa"], brano)
            self.assertLess(abs(GA.durata_brano(b) - durate[cut]), 1.6, (brano, cut, GA.durata_brano(b), durate[cut]))

    def test_jingle_non_tornano_da_capo(self):
        for nome in ("vittoria", "sconfitta", "presentazione", "pastorale"):
            self.assertFalse(self.brani[nome]["anello"], nome)
            self.assertLess(GA.durata_brano(self.brani[nome]), 13, nome)

    def test_tema_di_gubbio_ritorna(self):
        """Il filo musicale del gioco: il Tema torna nel titolo, nella basilica, nel prologo,
        nella terza alba e nella canzone dei titoli."""
        for nome in ("titolo", "basilica", "prologo", "terza_alba", "canzone_di_flaviano"):
            with open(os.path.join(GA.CARTELLA_BRANI, nome + ".brano"), encoding="utf-8") as f:
                self.assertRegex(f.read(), r"\$tema1", nome)

    def test_deterministico(self):
        self.assertEqual(GA.genera_tutto(), self.uscita)


def _scarto(a, b):
    return max((abs(x - y) for x, y in zip(a, b)), default=0)


def _wav_dati(byte):
    with wave.open(io.BytesIO(byte)) as w:
        return w.readframes(w.getnframes())


if __name__ == "__main__":
    unittest.main()
