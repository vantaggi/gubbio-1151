#!/usr/bin/env python3
"""Registro dei crediti (CREDITI.md): ogni asset di terzi ha la sua riga, e ogni riga punta a file
che esistono davvero. Un dato che cita una fonte esterna senza riga nel registro fa fallire.

    python -m unittest tests.test_crediti
"""
import glob
import json
import os
import re
import unittest

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def righe_registro(testo):
    """Le righe della tabella del registro (salta intestazione e separatore)."""
    righe = [r for r in testo.splitlines() if r.startswith("|")]
    return [r for r in righe[2:] if not set(r) <= set("|:- ")]


def file_citati(riga):
    """I percorsi fra backtick nella prima colonna di una riga del registro."""
    prima = riga.split("|")[1]
    return [p for p in re.findall(r"`([^`]+)`", prima) if "/" in p]


def controlla(testo, radice=RADICE):
    err = []
    righe = righe_registro(testo)
    if not righe:
        err.append("registro vuoto")
    citati = set()
    for r in righe:
        celle = [c.strip() for c in r.strip().strip("|").split("|")]
        if len(celle) != 5:
            err.append(f"riga con {len(celle)} colonne invece di 5: {r[:60]}")
            continue
        if not all(celle):
            err.append(f"riga con una colonna vuota: {r[:60]}")
        for p in file_citati(r):
            citati.add(p.rstrip("/"))
            if not os.path.exists(os.path.join(radice, p)):
                err.append(f"il registro cita '{p}', che non esiste")
    # ogni dato JSON che dichiara una fonte esterna deve avere la sua riga
    for f in sorted(glob.glob(os.path.join(radice, "dati", "**", "*.json"), recursive=True)):
        rel = os.path.relpath(f, radice).replace(os.sep, "/")
        with open(f, encoding="utf-8") as h:
            nota = str(json.load(h).get("_nota", "")) if f.endswith(".json") else ""
        if re.search(r"wikipedia|araldicacivica|openstreetmap|osm\b|fonte", nota, re.I) and rel not in citati:
            err.append(f"'{rel}' cita una fonte esterna ma non ha una riga in CREDITI.md")
    return err


class Crediti(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(RADICE, "CREDITI.md"), encoding="utf-8") as f:
            self.testo = f.read()

    def test_registro_vero_conforme(self):
        self.assertEqual(controlla(self.testo), [])

    def test_licenze_dei_contenuti_presenti(self):
        for nome in ("LICENSE", "LICENSE-CONTENUTI"):
            self.assertTrue(os.path.exists(os.path.join(RADICE, nome)), nome)

    # --- prove negative ------------------------------------------------------------------

    def test_negativa_file_inesistente(self):
        guasto = self.testo + "| `dati/non_esiste.json` | x | x | x | x |\n"
        self.assertIn("il registro cita 'dati/non_esiste.json', che non esiste", controlla(guasto))

    def test_negativa_dato_senza_riga(self):
        guasto = "\n".join(r for r in self.testo.splitlines() if "mappa_umbria" not in r)
        self.assertIn("'dati/mappa_umbria.json' cita una fonte esterna ma non ha una riga in CREDITI.md",
                      controlla(guasto))

    def test_negativa_colonna_vuota(self):
        guasto = self.testo + "| `CREDITI.md` |  | x | x | x |\n"
        self.assertTrue(any("colonna vuota" in e for e in controlla(guasto)))

    def test_negativa_registro_vuoto(self):
        self.assertIn("registro vuoto", controlla("# Crediti\n"))


if __name__ == "__main__":
    unittest.main()
