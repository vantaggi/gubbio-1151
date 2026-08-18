#!/usr/bin/env python3
"""
Verifica del COPIONE e delle QUEST (Passo 17).

    python tests/test_dialogue_quest.py

Due oracoli:

1. **L'header generato e' allineato al copione.** `include/dialogue_data.h` e' prodotto da
   `tools/dialogue_exporter.py`: se qualcuno modifica il copione e dimentica di rigenerare — o,
   peggio, modifica l'header a mano — il gioco recita un testo diverso da quello in repo. Il
   test rigenera in memoria e confronta.

2. **Il testo sta nel box.** Ogni riga viene rimisurata con le larghezze reali di
   `font_gubbio.h`, e ogni carattere deve esistere nel font. Un carattere non mappato non e' un
   errore di compilazione: e' un `BN_ERROR` a runtime sulla battuta che lo contiene.

Gli invarianti strutturali (intervalli degli script, NPC dentro i muri, ordine delle condizioni
del Podesta') sono verificati dal COMPILATORE con `static_assert` in `dialogue_data.h`,
`npc_registry.h` e `quest_data.h`: non si ripetono qui.
"""

import os
import re
import sys
import unittest

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import dialogue_exporter as exporter          # noqa: E402


class CopioneTest(unittest.TestCase):

    def setUp(self):
        self.larghezze = exporter.carica_larghezze()
        self.header = os.path.join(ROOT, "include", "dialogue_data.h")

    def test_header_generato_e_allineato(self):
        """Il file in repo deve essere quello che l'esportatore produce oggi."""
        self.assertTrue(os.path.exists(self.header), "include/dialogue_data.h non generato")
        prima = open(self.header, encoding="utf-8").read()

        exporter.main()
        dopo = open(self.header, encoding="utf-8").read()

        self.assertEqual(prima, dopo,
                         "dialogue_data.h non e' allineato al copione: "
                         "eseguire python tools/dialogue_exporter.py")

    def test_ogni_riga_sta_nel_box(self):
        for nome, battute in exporter.COPIONE:
            for indice, (_, testo) in enumerate(battute):
                dove = f"{nome}[{indice}]"
                righe = exporter.spezza(exporter.applica_sostituzioni(testo), self.larghezze, dove)

                self.assertLessEqual(len(righe), exporter.MAX_ROWS, f"{dove}: troppe righe")

                for riga in righe:
                    larghezza = exporter.larghezza(riga, self.larghezze, dove)
                    self.assertLessEqual(larghezza, exporter.LARGHEZZA_UTILE_PX,
                                         f"{dove}: riga da {larghezza} px, il box ne regge "
                                         f"{exporter.LARGHEZZA_UTILE_PX}")

    def test_nessun_apostrofo_al_posto_di_un_accento(self):
        """Il font ha le 12 accentate italiane dalla Sessione 12: scrivere "citta'" adesso
        sarebbe una svista, non una necessita'. Le sostituzioni dell'esportatore devono averle
        gia' convertite tutte."""
        sospetti = []

        for nome, battute in exporter.COPIONE:
            for indice, (_, testo) in enumerate(battute):
                convertito = exporter.applica_sostituzioni(testo)

                for parola in re.findall(r"\b\w+'(?=\s|$|[.,!?])", convertito):
                    # L'apostrofo legittimo (l'acqua, dell'estate) precede una lettera; qui si
                    # cercano solo quelli a fine parola, che in italiano sono accenti mancati.
                    if parola[:-1].lower() not in ("po", "un"):
                        sospetti.append(f"{nome}[{indice}]: {parola!r}")

        self.assertFalse(sospetti, "apostrofi a fine parola dove serve un accento: " +
                                   ", ".join(sospetti))

    def test_parlanti_esistenti(self):
        for nome, battute in exporter.COPIONE:
            for indice, (parlante, _) in enumerate(battute):
                self.assertIn(parlante, exporter.SPEAKER,
                              f"{nome}[{indice}]: parlante {parlante!r} non esiste nell'enum Speaker")


class QuestTest(unittest.TestCase):
    """Le quest della Sez. 31A devono essere tutte e cinque nella tabella, con il loro codice."""

    def test_le_cinque_quest_della_sezione_31a(self):
        testo = open(os.path.join(ROOT, "include", "quest_data.h"), encoding="utf-8").read()

        for codice in ("Q-SM01", "Q-SA01", "Q-SP01", "Q-SG01", "Q-CIV01"):
            self.assertIn(codice, testo, f"quest {codice} assente da quest_data.h")

    def test_obiettivi_di_raccolta_conformi_al_gdd(self):
        """Sez. 31A: Q-SM01 vuole 3 blocchi di ferro, Q-SA01 4 radici di elleboro. Sono i due
        numeri per cui `quest_counter` esiste separato da `quest_state`."""
        testo = open(os.path.join(ROOT, "include", "quest_data.h"), encoding="utf-8").read()
        # La RIGA DELLA TABELLA, non il commento che nomina la quest.
        riga_sm01 = next(l for l in testo.splitlines() if l.strip().startswith('{"Q-SM01"'))
        riga_sa01 = next(l for l in testo.splitlines() if l.strip().startswith('{"Q-SA01"'))

        self.assertIn(" 3,", riga_sm01, "Q-SM01 deve chiedere 3 blocchi di ferro")
        self.assertIn(" 4,", riga_sa01, "Q-SA01 deve chiedere 4 radici di elleboro")


if __name__ == "__main__":
    unittest.main(verbosity=2)
