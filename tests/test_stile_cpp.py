#!/usr/bin/env python3
"""Gli header include/stile/*.h sono generati dai JSON di stile/dati/ e devono restare allineati.
Controlla anche le regole di AGENTS.md: tabelle constexpr in ROM, niente float, niente heap.

    python -m unittest tests.test_stile_cpp
"""
import os
import re
import unittest

from _stile import S, RADICE
import esporta_cpp as E

VIETATI = re.compile(r"\b(float|double|new|malloc|std::vector|std::string)\b")


class HeaderCpp(unittest.TestCase):
    def test_header_allineati_ai_dati(self):
        for nome in E.GENERATORI:
            percorso = os.path.join(RADICE, "include", "stile", nome)
            self.assertTrue(os.path.exists(percorso), f"manca {nome}: lanciare stile/esporta_cpp.py")
            with open(percorso, encoding="utf-8") as f:
                self.assertEqual(f.read(), E.contenuto(nome),
                                 f"{nome} non allineato: lanciare stile/esporta_cpp.py")

    def test_tabelle_in_rom_senza_float_ne_heap(self):
        for nome in E.GENERATORI:
            testo = E.contenuto(nome)
            codice = "\n".join(r.split("//")[0] for r in testo.splitlines())
            self.assertIsNone(VIETATI.search(codice), nome)
            for riga in codice.splitlines():
                if re.match(r"\s*\w.*\[.*\]\s*=\s*\{", riga):
                    self.assertIn("inline constexpr", riga, f"{nome}: tabella non constexpr: {riga}")

    def test_glifo_impacchettato_bit_7_a_sinistra(self):
        testo = E.contenuto("font.h")
        # '!' e' una colonna sola: righe 2-6 accese, 7 spenta, 8 accesa
        self.assertIn("{ U'!', 1, { 0x00, 0x00, 0x80, 0x80, 0x80, 0x80, 0x80, 0x00, 0x80, 0x00 } }", testo)

    def test_tile_4bpp_nibble_basso_a_sinistra(self):
        self.assertEqual(E.tile_4bpp(["12000000"] * 8)[0], 0x00000021)

    # --- prove negative ------------------------------------------------------------------

    def test_negativa_header_vecchio(self):
        vero = E.contenuto("palette.h")
        self.assertNotEqual(vero.replace("0x", "0X", 1), vero)

    def test_negativa_float_rilevato(self):
        self.assertIsNotNone(VIETATI.search("inline constexpr float X[2] = {0.5f, 1};"))
        self.assertIsNone(VIETATI.search("inline constexpr uint16_t X[2] = {1, 2};"))


if __name__ == "__main__":
    unittest.main()
