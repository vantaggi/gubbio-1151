"""docs/architettura/ e' la fotografia del codice: grafo dei moduli, matrici, aree e varchi.

Se fallisce dopo una modifica a include, asset o varchi: `python3 tools/grafo_moduli.py` e committare.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import grafo_moduli  # noqa: E402


class Architettura(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a = grafo_moduli.analizza()

    def test_nessun_errore(self):
        self.assertEqual(self.a["errori"], [])

    def test_documenti_aggiornati(self):
        self.assertEqual(grafo_moduli.indietro(self.a), [], "python3 tools/grafo_moduli.py")

    def test_ciclo_trovato(self):
        self.assertEqual(grafo_moduli.cicli({"a": ["b"], "b": ["c"], "c": ["a"], "d": ["a"]}), [["a", "b", "c"]])
        self.assertEqual(grafo_moduli.cicli({"a": ["b"], "b": []}), [])

    def test_generatore_riconosciuto(self):
        self.assertEqual(grafo_moduli.generatore("// GENERATO da tools/genera_mondo.py: non modificare\n"),
                         "tools/genera_mondo.py")
        self.assertIsNone(grafo_moduli.generatore("#ifndef X\n#define X\n"))


if __name__ == "__main__":
    unittest.main()
