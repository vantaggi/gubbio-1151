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


SEZIONE_AUDIO = "## Musica ed effetti sonori"
LICENZA_CONTENUTI = "CC BY-NC 4.0"


def righe_registro(testo):
    """Le righe della tabella del registro (salta intestazione e separatore), prima della sezione audio."""
    testo = testo.split(SEZIONE_AUDIO)[0]
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


def controlla_audio(testo, radice=RADICE):
    """La sezione della musica e degli effetti: ogni file di audio/ ha la sua riga, originale con la licenza
    dei contenuti e il suo generatore (che esiste); un brano XM cita la sua partitura musica/<nome>.brano."""
    if SEZIONE_AUDIO not in testo:
        return ["manca la sezione della musica e degli effetti"]
    sezione = testo.split(SEZIONE_AUDIO, 1)[1].split("\n## ")[0]
    righe = [r for r in sezione.splitlines() if r.startswith("|")][2:]
    err, accreditati = [], set()
    for r in righe:
        celle = [c.strip() for c in r.strip().strip("|").split("|")]
        if len(celle) != 5 or not all(celle):
            err.append(f"riga audio malformata: {r[:60]}")
            continue
        file = re.findall(r"`(audio/[^`]+)`", celle[0])
        if len(file) != 1:
            err.append(f"riga audio senza il suo file: {r[:60]}")
            continue
        f = file[0]
        accreditati.add(f)
        if not os.path.isfile(os.path.join(radice, f)):
            err.append(f"il registro audio cita '{f}', che non esiste")
        if LICENZA_CONTENUTI not in celle[4]:
            err.append(f"'{f}' senza la licenza dei contenuti ({LICENZA_CONTENUTI})")
        generatori = re.findall(r"`(tools/[^`]+\.py)`", celle[3])
        if not generatori or not all(os.path.isfile(os.path.join(radice, g)) for g in generatori):
            err.append(f"'{f}' senza un generatore che esiste")
        if f.endswith(".xm"):
            partitura = "musica/" + os.path.basename(f)[:-3] + ".brano"
            if f"`{partitura}`" not in celle[2] or not os.path.isfile(os.path.join(radice, partitura)):
                err.append(f"'{f}' senza la sua partitura '{partitura}'")
    cartella = os.path.join(radice, "audio")
    for nome in sorted(os.listdir(cartella)) if os.path.isdir(cartella) else []:
        if not nome.startswith(".") and f"audio/{nome}" not in accreditati:
            err.append(f"'audio/{nome}' non ha una riga nella sezione audio di CREDITI.md")
    if "maxmod" not in sezione.lower() or "mmutil" not in sezione:
        err.append("la sezione audio non dice di Maxmod e mmutil")
    return err


class Crediti(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(RADICE, "CREDITI.md"), encoding="utf-8") as f:
            self.testo = f.read()

    def aggiungi(self, riga):
        """Una riga in fondo al registro dei terzi, prima della sezione audio."""
        prima, dopo = self.testo.split(SEZIONE_AUDIO, 1)
        a = prima.rindex("|\n") + 2
        return prima[:a] + riga + "\n" + prima[a:] + SEZIONE_AUDIO + dopo

    def test_registro_vero_conforme(self):
        self.assertEqual(controlla(self.testo), [])

    def test_audio_tutto_accreditato(self):
        self.assertEqual(controlla_audio(self.testo), [])
        self.assertIn(LICENZA_CONTENUTI, open(os.path.join(RADICE, "LICENSE-CONTENUTI"), encoding="utf-8").read())

    def test_licenze_dei_contenuti_presenti(self):
        for nome in ("LICENSE", "LICENSE-CONTENUTI"):
            self.assertTrue(os.path.exists(os.path.join(RADICE, nome)), nome)

    # --- prove negative ------------------------------------------------------------------

    def test_negativa_file_inesistente(self):
        guasto = self.aggiungi("| `dati/non_esiste.json` | x | x | x | x |")
        self.assertIn("il registro cita 'dati/non_esiste.json', che non esiste", controlla(guasto))

    def test_negativa_dato_senza_riga(self):
        guasto = "\n".join(r for r in self.testo.splitlines() if "mappa_umbria" not in r)
        self.assertIn("'dati/mappa_umbria.json' cita una fonte esterna ma non ha una riga in CREDITI.md",
                      controlla(guasto))

    def test_negativa_colonna_vuota(self):
        guasto = self.aggiungi("| `CREDITI.md` |  | x | x | x |")
        self.assertTrue(any("colonna vuota" in e for e in controlla(guasto)))

    def test_negativa_audio_senza_riga(self):
        guasto = "\n".join(r for r in self.testo.splitlines() if "`audio/campanone.wav`" not in r)
        self.assertIn("'audio/campanone.wav' non ha una riga nella sezione audio di CREDITI.md", controlla_audio(guasto))
        guasto = "\n".join(r for r in self.testo.splitlines() if "`audio/stradoni.xm`" not in r)
        self.assertIn("'audio/stradoni.xm' non ha una riga nella sezione audio di CREDITI.md", controlla_audio(guasto))

    def test_negativa_audio_senza_licenza_generatore_o_partitura(self):
        guasto = self.testo.replace("| `audio/fede.wav` | effetto (WAV 8 bit mono), `bn::sound_items::fede` | "
                                    "`effetti()` in `tools/genera_audio.py` | `tools/genera_audio.py` | CC BY-NC 4.0",
                                    "| `audio/fede.wav` | effetto | x | `tools/non_esiste.py` | MIT")
        self.assertNotEqual(guasto, self.testo)
        err = controlla_audio(guasto)
        self.assertIn("'audio/fede.wav' senza la licenza dei contenuti (CC BY-NC 4.0)", err)
        self.assertIn("'audio/fede.wav' senza un generatore che esiste", err)
        guasto = self.testo.replace("`musica/notte.brano`", "`musica/citta.brano`")
        self.assertIn("'audio/notte.xm' senza la sua partitura 'musica/notte.brano'", controlla_audio(guasto))

    def test_negativa_audio_file_inesistente_e_sezione_mancante(self):
        riga = "| `audio/non_esiste.wav` | effetto | x | `tools/genera_audio.py` | CC BY-NC 4.0 |"
        guasto = self.testo.replace("| `audio/fede.wav`", riga + "\n| `audio/fede.wav`")
        self.assertIn("il registro audio cita 'audio/non_esiste.wav', che non esiste", controlla_audio(guasto))
        self.assertEqual(controlla_audio(self.testo.split(SEZIONE_AUDIO)[0]),
                         ["manca la sezione della musica e degli effetti"])
        self.assertIn("la sezione audio non dice di Maxmod e mmutil", controlla_audio(self.testo.replace("mmutil", "x")))

    def test_negativa_registro_vuoto(self):
        self.assertIn("registro vuoto", controlla("# Crediti\n"))


if __name__ == "__main__":
    unittest.main()
