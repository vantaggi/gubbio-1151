"""I tre protagonisti senza «San»/«Sant'» (Cioti, 4 nov 2026): nel 1151 Ubaldo, Giorgio e Antonio non
sono ancora santi. Il titolo resta solo nei nomi dei luoghi (Basilica, cappellette, chiese, quartieri)."""

import re
import unittest
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
SANTO = re.compile(r"\b(?:San|Sant'|S\.)\s?(?:Ubaldo|Giorgio|Antonio)\b")
# luoghi: dove il titolo resta
LUOGO = re.compile(r"(?:Basilica|[Cc]appell\w*|[Cc]hiesa|[Pp]orta|[Qq]uartiere|[Vv]ia|[Pp]iazza)\s+(?:di\s+)?$")


def nomi_sbagliati(righe):
    """Le righe (chiave, testo) che chiamano santo un protagonista fuori da un nome di luogo."""
    errori = []
    for chiave, testo in righe:
        if chiave.startswith("AREA_"):
            continue
        for m in SANTO.finditer(testo):
            if not LUOGO.search(testo[:m.start()]):
                errori.append((chiave, testo))
    return errori


def righe_dei_testi():
    for f in sorted((RADICE / "testi").glob("*.testi")):
        if f.name == "prova.testi":     # le frasi di prova del font, non del gioco
            continue
        for riga in f.read_text(encoding="utf-8").splitlines():
            parti = [p.strip() for p in riga.split("|")]
            if len(parti) >= 3 and not riga.lstrip().startswith("#"):
                yield parti[0], "|".join(parti[2:])


class NomiSenzaSanto(unittest.TestCase):
    def test_nessun_protagonista_chiamato_santo(self):
        self.assertEqual(nomi_sbagliati(righe_dei_testi()), [])

    def test_ci_sono_testi_da_controllare(self):
        self.assertGreater(len(list(righe_dei_testi())), 300)

    def test_negativa_il_titolo_viene_trovato(self):
        self.assertEqual(len(nomi_sbagliati([("BATT_X", "Sant'Ubaldo sale di livello!"),
                                              ("D", "Lo dice San Giorgio."),
                                              ("D", "Il Fuoco di Sant'Antonio")])), 3)

    def test_i_luoghi_restano(self):
        self.assertEqual(nomi_sbagliati([("D", "Alla Basilica di Sant'Ubaldo."),
                                         ("D", "La cappella di San Giorgio, al sesto tornante."),
                                         ("AREA_BASILICA", "Basilica di Sant'Ubaldo")]), [])


if __name__ == "__main__":
    unittest.main()
