#!/usr/bin/env python3
"""Scelta 8: font proporzionale in dati, e copertura dei caratteri dei testi del gioco.

Il test sui testi legge ogni file di testo del gioco (TESTI_DEL_GIOCO) piu' le frasi fisse
della Guida: se un carattere usato non ha glifo, fallisce e dice quale.

    python -m unittest tests.test_stile_font
"""
import glob
import os
import re
import unittest

from _stile import S, RADICE

# Dove stanno i testi che vanno a schermo. Le stringhe del codice (asserzioni, log) no.
TESTI_DEL_GIOCO = ["include/testi*.h", "include/**/testi*.h", "include/dialog*.h", "testi/**/*.txt"]

# Frasi fisse decise nella Guida (tavole delle scelte 8, 9, 10, 12): valgono sempre, anche
# quando i testi del gioco non sono ancora stati scritti.
FRASI_GUIDA = [
    "È l'anno 1151. Undici città marciano su Gubbio, e il vescovo Ubaldo sale sulle mura: "
    "«Non abbiate paura. Chi può, resti al suo posto.»",
    "La Guerra delle Undici Città",
    "Premi Start", "Attacca", "Oggetti", "Attendi", "Ubaldo",
]


def letterali(testo):
    return re.findall(r'(?:u8)?"((?:[^"\\]|\\.)*)"', testo)


def testi_del_gioco():
    trovati = {}
    for schema in TESTI_DEL_GIOCO:
        for p in glob.glob(os.path.join(RADICE, schema), recursive=True):
            t = open(p, encoding="utf-8").read()
            trovati[os.path.relpath(p, RADICE)] = "".join(letterali(t)) if p.endswith(".h") else t
    return trovati


class Font(unittest.TestCase):
    def setUp(self):
        self.f = S.carica("font")

    def test_font_vero_conforme(self):
        self.assertEqual(S.controlla_font(self.f), [])

    def test_frasi_della_guida_coperte(self):
        for frase in FRASI_GUIDA:
            self.assertEqual(S.caratteri_mancanti(self.f, frase), [], frase)

    def test_testi_del_gioco_coperti(self):
        for nome, testo in testi_del_gioco().items():
            self.assertEqual(S.caratteri_mancanti(self.f, testo), [], nome)

    def test_frase_della_tavola_in_tre_righe(self):
        # scelte 8 e 9: nel riquadro largo 30 tile, con un tile di margine per lato, la frase
        # di prova chiude in 3 righe (il monospaziato ne chiedeva 5)
        self.assertEqual(len(S.a_capo(self.f, FRASI_GUIDA[0], 240 - 16)), 3)

    # --- prove negative ------------------------------------------------------------------

    def test_negativa_glifo_mancante_nei_testi(self):
        g = S.guasta(self.f)
        del g["glifi"]["à"]
        self.assertEqual(S.caratteri_mancanti(g, "città"), ["à"])
        self.assertIn("manca il glifo obbligatorio 'à'", S.controlla_font(g))

    def test_negativa_carattere_estraneo(self):
        self.assertEqual(S.caratteri_mancanti(self.f, "a ~ b"), ["~"])

    def test_negativa_letterali_letti_dai_sorgenti(self):
        self.assertEqual(letterali('auto t = u8"Ciò è ~"; auto u = "x";'), ["Ciò è ~", "x"])

    def test_negativa_maiuscola_bassa(self):
        g = S.guasta(self.f)
        g["glifi"]["E"] = ["....."] * 3 + g["glifi"]["E"][2:9]
        self.assertTrue(any("'E': la maiuscola non e' alta 7 px" in e for e in S.controlla_font(g)))

    def test_negativa_minuscola_fuori_corpo(self):
        g = S.guasta(self.f)
        g["glifi"]["o"] = g["glifi"]["o"][1:] + ["...."]
        self.assertTrue(any("'o': il corpo minuscolo" in e for e in S.controlla_font(g)))

    def test_negativa_discendente_corto(self):
        g = S.guasta(self.f)
        g["glifi"]["p"] = g["glifi"]["p"][:9] + ["...."]
        self.assertTrue(any("'p': discendente" in e for e in S.controlla_font(g)))

    def test_negativa_glifo_troppo_largo(self):
        g = S.guasta(self.f)
        g["glifi"]["m"] = [r + "#" * 4 for r in g["glifi"]["m"]]
        self.assertTrue(any("larghezza 9" in e for e in S.controlla_font(g)))

    def test_negativa_font_largo_sfora_le_tre_righe(self):
        g = S.guasta(self.f)
        g["spaziatura"] = 2
        self.assertGreater(len(S.a_capo(g, FRASI_GUIDA[0], 240 - 16)), 3)

    def test_negativa_colonna_vuota(self):
        g = S.guasta(self.f)
        g["glifi"]["n"] = [r + "." for r in g["glifi"]["n"]]
        self.assertIn("'n': colonna vuota sul bordo", S.controlla_font(g))

    def test_negativa_accento_mancante(self):
        g = S.guasta(self.f)
        g["glifi"]["È"] = g["glifi"]["E"]
        self.assertTrue(any("'È': maiuscola accentata" in e for e in S.controlla_font(g)))


if __name__ == "__main__":
    unittest.main()
