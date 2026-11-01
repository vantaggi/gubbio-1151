#!/usr/bin/env python3
"""Il copione v1 (copione/*.md) passa il suo controllo: caratteri del font e al massimo 3 righe.

Prova negativa: una copia del copione con una battuta guasta deve essere rifiutata.

    python -m unittest tests.test_copione
"""
import contextlib
import importlib.util
import io
import os
import shutil
import tempfile
import unittest

from _stile import RADICE

COPIONE = os.path.join(RADICE, "copione")


def esegui(cartella):
    """Carica verifica_copione.py dalla cartella data e ne esegue main(); (codice, stampa)."""
    cwd = os.getcwd()
    spec = importlib.util.spec_from_file_location("verifica_copione_" + str(abs(hash(cartella))),
                                                  os.path.join(cartella, "verifica_copione.py"))
    mod = importlib.util.module_from_spec(spec)
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            spec.loader.exec_module(mod)
            codice = mod.main()
    finally:
        os.chdir(cwd)
    return codice, out.getvalue()


class Copione(unittest.TestCase):

    def test_copione_valido(self):
        codice, testo = esegui(COPIONE)
        self.assertEqual(codice, 0, testo)
        self.assertIn(" 0 errori", testo)

    def test_battuta_guasta_presa(self):
        with tempfile.TemporaryDirectory() as tmp:
            copia = os.path.join(tmp, "copione")
            shutil.copytree(COPIONE, copia)
            with open(os.path.join(copia, "01_atto_I.md"), "a", encoding="utf-8") as f:
                f.write("\n- UBALDO (furioso): Señor.\n")
                f.write("- GIORGIO (deciso): " + "parola " * 60 + "\n")
            codice, testo = esegui(copia)
        self.assertEqual(codice, 1)
        self.assertIn("espressione sconosciuta", testo)
        self.assertIn("caratteri fuori dal font", testo)
        self.assertIn("righe (GIORGIO)", testo)


if __name__ == "__main__":
    unittest.main()
