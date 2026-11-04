"""Coerenza dei nomi (regola di Cioti, 4 nov 2026: a ogni fusione si controllano i nomi).
- Gli amici parlano nel copione col nome di dati/amici.json, e ogni amico di amici.json esiste nel copione.
- I nomi ritirati (vecchi nomi di gioco e soprannomi veri) non compaiono in copione, testi e dati."""

import json
import re
import unittest
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent

# Vecchi nomi di gioco cambiati da Cioti e soprannomi veri degli amici: nel gioco non devono comparire.
RITIRATI = ["COMPAGNO", "Compagno", "BUBO", "Bubo", "Gabrielone", "Padeletto", "Giamma", "Cumpà", "Endriu",
            "Giordy", "Bubu", "Febbo", "Fagia", "Ciacci", "Massi", "Nicolò"]


def file_del_gioco():
    fs = sorted((RADICE / "copione").glob("0*.md")) + sorted((RADICE / "testi").glob("*.testi"))
    fs += [RADICE / "dati" / "amici.json", RADICE / "include" / "storia.h"]
    return [f for f in fs if f.exists()]


def nomi_ritirati(testo, ritirati=RITIRATI):
    return sorted({n for n in ritirati if re.search(r"(?<![\wÀ-ÿ])" + re.escape(n) + r"(?![\wÀ-ÿ])", testo)})


def parlanti_amici():
    """I nomi in maiuscolo degli NPC amici nel copione: '**Ciaccio**' come intestazione in 05_npc_amici.md."""
    testo = (RADICE / "copione" / "05_npc_amici.md").read_text(encoding="utf-8")
    return testo


class NomiCoerenti(unittest.TestCase):
    def test_nessun_nome_ritirato(self):
        trovati = {f.name: nomi_ritirati(f.read_text(encoding="utf-8")) for f in file_del_gioco()}
        self.assertEqual({k: v for k, v in trovati.items() if v}, {})

    def test_negativa_un_nome_ritirato_viene_trovato(self):
        self.assertEqual(nomi_ritirati("- BUBO: Le carte! E poi il Compagno."), ["BUBO", "Compagno"])
        self.assertEqual(nomi_ritirati("Fino al monte, Renzo."), [])

    def test_ogni_amico_nel_copione(self):
        amici = json.loads((RADICE / "dati" / "amici.json").read_text(encoding="utf-8"))["amici"]
        copione = "\n".join(f.read_text(encoding="utf-8") for f in sorted((RADICE / "copione").glob("0*.md")))
        mancanti = [d["nome"] for d in amici.values() if d["nome"] not in copione]
        self.assertEqual(mancanti, [])
        self.assertGreaterEqual(len(amici), 24)

    def test_negativa_un_amico_che_non_esiste(self):
        copione = parlanti_amici()
        finti = {"X": {"nome": "Bubonio"}, "Y": {"nome": "Ciaccio"}}
        self.assertEqual([d["nome"] for d in finti.values() if d["nome"] not in copione], ["Bubonio"])


if __name__ == "__main__":
    unittest.main()
