"""Coerenza dei nomi (regola di Cioti, 4 nov 2026: a ogni fusione si controllano i nomi).
- Gli amici parlano nel copione col nome di dati/amici.json, e ogni amico di amici.json esiste nel copione.
- I nomi ritirati (vecchi nomi di gioco e soprannomi veri) non compaiono in copione, testi e dati.
- Allineamento del 4 nov 2026: nemmeno nei documenti e nei dati del repo (docs/, README, mondo/, dati/), salvo
  la nota storica «prima «Bubo»»; il README del copione elenca ogni amico e ogni mestiere dei dati; la verifica del
  copione conosce ogni parlante (prima Milia, Michelino e i mestieri restavano fuori dal controllo)."""

import importlib.util
import json
import os
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


def documenti_del_repo():
    """I documenti e i dati che non vanno a schermo ma che si leggono: anche qui valgono i nomi di oggi."""
    fs = sorted((RADICE / "docs").glob("*.md")) + [RADICE / n for n in ("README.md", "CREDITI.md")]
    fs += [RADICE / "copione" / "README.md", RADICE / "musica" / "LEGGIMI.md", RADICE / "stile" / "LEGGIMI.md"]
    fs += sorted((RADICE / "mondo").rglob("*.json")) + sorted((RADICE / "dati").rglob("*.json"))
    fs += sorted((RADICE / "stile" / "dati").glob("*.json"))
    return [f for f in fs if f.exists()]


NOTA_STORICA = re.compile(r"(?:prima|non) «[^»]+»")


def nomi_ritirati_nei_documenti(testo):
    """Come nomi_ritirati, ma la nota storica («prima «Compagno»», «non «Bubo»») e' ammessa."""
    return nomi_ritirati(NOTA_STORICA.sub("", testo))


RIGA_PARLANTE = re.compile(r"^- (?:(?:ULTIMATUM|DIGIUNO|NOTTE)(?: \(se (?:non )?[A-Z_0-9]+\))?: )?([A-Z][A-Z']*(?: [A-Z][A-Z']*)?)"
                           r"(?: \([a-z]+\))?: ")


def parlanti_del_copione():
    nomi = set()
    for f in sorted((RADICE / "copione").glob("0*.md")):
        for riga in f.read_text(encoding="utf-8").splitlines():
            m = RIGA_PARLANTE.match(riga)
            if m and not m.group(1).startswith("IN BATTAGLIA"):
                nomi.add(m.group(1))
    return nomi


def verifica_copione():
    spec = importlib.util.spec_from_file_location("verifica_copione", RADICE / "copione" / "verifica_copione.py")
    modulo = importlib.util.module_from_spec(spec)
    cwd = os.getcwd()
    try:
        spec.loader.exec_module(modulo)
    finally:
        os.chdir(cwd)
    return modulo


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


    def test_documenti_e_dati_senza_nomi_ritirati(self):
        trovati = {str(f.relative_to(RADICE)): nomi_ritirati_nei_documenti(f.read_text(encoding="utf-8"))
                   for f in documenti_del_repo()}
        self.assertEqual({k: v for k, v in trovati.items() if v}, {})
        self.assertGreater(len(documenti_del_repo()), 15)

    def test_negativa_nota_storica_ammessa_il_resto_no(self):
        self.assertEqual(nomi_ritirati_nei_documenti("Il medico è Vanni (prima «Compagno»)."), [])
        self.assertEqual(nomi_ritirati_nei_documenti("Il custode delle carte, Bubo, sta nella pieve."), ["Bubo"])

    def test_il_readme_del_copione_elenca_amici_e_mestieri(self):
        readme = (RADICE / "copione" / "README.md").read_text(encoding="utf-8")
        amici = json.loads((RADICE / "dati" / "amici.json").read_text(encoding="utf-8"))["amici"]
        mestieri = json.loads((RADICE / "dati" / "mestieri.json").read_text(encoding="utf-8"))["mestieri"]
        self.assertEqual([d["nome"] for d in amici.values() if d["nome"] not in readme], [])
        self.assertEqual([m for m in mestieri if (m[0].lower() + m[1:]) not in readme and m not in readme], [])
        self.assertIn("06_npc_mestieri.md", readme)

    def test_la_verifica_del_copione_conosce_ogni_parlante(self):
        parlanti = parlanti_del_copione()
        self.assertGreater(len(parlanti), 80)
        self.assertEqual(sorted(parlanti - verifica_copione().PARLANTI), [])

    def test_negativa_un_parlante_nuovo_si_vede(self):
        self.assertTrue({"MILIA", "BANDITORE", "UBALDO"} <= parlanti_del_copione())
        self.assertNotIn("PARLANTE_FINTO", verifica_copione().PARLANTI)


if __name__ == "__main__":
    unittest.main()
