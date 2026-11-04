"""Il menu di pausa (MPA, MBI): la fila dei compagni segue la regola O1 di Cioti, come la battaglia
(tests/test_scena_battaglia.py, ordine_buono): Antonio a sinistra, Ubaldo al centro, Giorgio a destra."""
import os
import re
import unittest

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGINE = open(os.path.join(RADICE, "include", "menu_pagine.h"), encoding="utf-8").read()
PAUSA = open(os.path.join(RADICE, "src", "menu_pausa.cpp"), encoding="utf-8").read()


def posti(sorgente):
    m = re.search(r"POSTO_IN_FILA\[battaglia::EROI\] = \{ (\d), (\d), (\d) \}", sorgente)
    return [int(x) for x in m.groups()]


def fila_buona(posto):
    ubaldo, giorgio, antonio = 0, 1, 2
    return posto[antonio] < posto[ubaldo] < posto[giorgio] and posto[ubaldo] == 1


class FilaDeiCompagni(unittest.TestCase):
    def test_o1(self):
        self.assertTrue(fila_buona(posti(PAGINE)))

    def test_negativa_ordine_del_codice(self):
        self.assertFalse(fila_buona([0, 1, 2]))

    def test_la_pausa_usa_la_fila(self):
        self.assertIn("GUBBIO_VOCE(POSTO_IN_FILA, e) * COMPAGNO_PASSO", PAUSA)


if __name__ == "__main__":
    unittest.main()
