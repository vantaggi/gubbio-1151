"""MTUT: le righe SISTEMA che insegnano i comandi (menu/PROPOSTA.md sez. 3.8): A parla, B corre, Start apre la
pausa, Select ricorda la meta. Stanno alla fine di A1-01, prima dell'obiettivo, quando il giocatore prende Ubaldo
per la prima volta (P-01 e P-02 sono la cutscene C1, che recita solo il narratore). Prova negativa: senza una
delle quattro righe il controllo se ne accorge.
"""
import os
import sys
import unittest

from _stile import RADICE

sys.path.insert(0, os.path.join(RADICE, "tools"))
import genera_storia as GS  # noqa: E402

TASTI = ("A", "B", "Start", "Select")


def righe_dei_comandi(battute):
    """Le righe SISTEMA che nominano un tasto, nell'ordine: {tasto: indice della battuta}."""
    trovate = {}
    for k, b in enumerate(battute):
        if b["chi"] != "SISTEMA":
            continue
        parole = b["frase"].replace(";", " ").replace(":", " ").replace(".", " ").split()
        for t in TASTI:
            if t in parole and t not in trovate:
                trovate[t] = k
    return trovate


def a1_01():
    scene, _ = GS.leggi_copione()
    return next(s for s in scene if s["codice"] == "A1-01")


class Comandi(unittest.TestCase):

    def test_quattro_tasti_prima_dell_obiettivo(self):
        s = a1_01()
        trovate = righe_dei_comandi(s["battute"])
        self.assertEqual(set(trovate), set(TASTI))
        obiettivo = next(k for k, b in enumerate(s["battute"]) if b["chi"] == "OBIETTIVO")
        self.assertTrue(all(k < obiettivo for k in trovate.values()))
        # nell'ordine della proposta: A, B, Start, Select
        self.assertEqual(sorted(trovate, key=trovate.get), list(TASTI))

    def test_dette_nel_gioco(self):
        # le righe sono battute della scena (SCENA/BATTUTA in storia.h), non note di regia
        with open(os.path.join(RADICE, "testi", "copione.testi"), encoding="utf-8") as f:
            testi = f.read()
        self.assertIn("Select ricorda l'obiettivo e indica il varco da prendere.", testi)
        self.assertIn("Start apre la pausa: da lì si salva la partita.", testi)

    def test_negativa_una_riga_mancante(self):
        battute = [b for b in a1_01()["battute"] if not b["frase"].startswith("Select")]
        self.assertNotIn("Select", righe_dei_comandi(battute))


if __name__ == "__main__":
    unittest.main(verbosity=2)
