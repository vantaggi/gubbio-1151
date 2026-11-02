#!/usr/bin/env python3
"""Generatore dei testi (tools/genera_testi.py) e regole d'accesso alle sue tabelle.

Ogni controllo ha la sua prova negativa: un sorgente costruito apposta che deve essere rifiutato.
I controlli sul C++ (punti di taglio, byte UTF-8, disegno a ogni passo) stanno nell'autotest a
tempo di compilazione, include/testo_autotest.h.

    python -m unittest tests.test_testi
"""
import glob
import importlib.util
import os
import re
import unittest

from _stile import S, RADICE

_spec = importlib.util.spec_from_file_location("genera_testi", os.path.join(RADICE, "tools", "genera_testi.py"))
G = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(G)

FONT = S.carica("font")


def genera(*righe):
    return G.genera([("prova.testi", "\n".join(righe).encode("utf-8"))], FONT)


class Generatore(unittest.TestCase):

    def test_header_del_repo_aggiornato(self):
        """include/testi.h e' generato: deve coincidere con quello che il generatore produce oggi."""
        atteso = G.genera(G.sorgenti_del_repo(), FONT)
        with open(G.USCITA, encoding="utf-8") as f:
            self.assertEqual(f.read(), atteso, "eseguire python tools/genera_testi.py")

    def test_testo_valido(self):
        h = genera("SALUTO | HUD | Ciao")
        self.assertIn("SALUTO,", h)
        self.assertIn('"Ciao"', h)

    def test_a_capo_come_la_guida(self):
        """Le righe sono quelle di stile.a_capo: la stessa funzione dei test della Guida."""
        frase = ("È l'anno 1151. Undici città marciano su Gubbio, e il vescovo Ubaldo sale sulle mura: "
                 "«Non abbiate paura. Chi può, resti al suo posto.»")
        t = G.componi([("X", "DIALOGO", frase, "prova")], FONT)
        self.assertEqual(t["testi"][0]["righe"], len(S.a_capo(FONT, frase, 224)))

    def test_byte_glifo_sui_confini_utf8(self):
        t = G.componi([("X", "HUD", "Più ù", "prova")], FONT)
        utf8 = t["testi"][0]["utf8"].encode("utf-8")
        for b in t["byte_glifo"]:
            self.assertNotEqual(utf8[b] & 0xC0, 0x80, f"byte {b} in mezzo a un carattere")

    def test_tagli_coerenti(self):
        """Il punto di taglio k e' il primo glifo che tocca lo sprite k."""
        t = G.componi([("X", "DIALOGO", "Mmmmmmmmmm Mmmmmmmmmm Mmmmmmmmmm Mmmmmmmmmm", "prova")], FONT)
        primo, n, _ = t["righe"][0]
        for k in range(G.SPRITE_PER_RIGA):
            taglio = t["tagli"][k]
            if taglio < n:
                g = primo + taglio
                self.assertGreater(t["x_glifo"][g] + 6, k * 32)

    # --- prove negative ---------------------------------------------------------------------

    def test_negativa_enne_con_tilde(self):
        with self.assertRaisesRegex(G.ErroreTesti, "U\\+00F1"):
            genera("SPAGNOLO | HUD | España")

    def test_negativa_byte_spezzato(self):
        """'à' e' C3 A0 in UTF-8: senza il secondo byte il file non e' UTF-8."""
        dati = "OK | HUD | Ciao\nROTTO | HUD | Citt".encode("utf-8") + b"\xc3" + b" fine\n"
        with self.assertRaisesRegex(G.ErroreTesti, r"prova\.testi:2: byte UTF-8 non valido 0xC3"):
            G.genera([("prova.testi", dati)], FONT)

    def test_negativa_troppe_righe(self):
        lungo = " ".join(["Gubbio"] * 60)
        with self.assertRaisesRegex(G.ErroreTesti, "righe, il contesto DIALOGO ne ammette 3"):
            genera(f"LUNGO | DIALOGO | {lungo}")

    def test_negativa_hud_troppo_largo(self):
        with self.assertRaisesRegex(G.ErroreTesti, "il contesto HUD"):
            genera("LARGO | HUD | Precipitevolissimevolmente")

    def test_negativa_contesto_sconosciuto(self):
        with self.assertRaisesRegex(G.ErroreTesti, "contesto 'MENU' sconosciuto"):
            genera("X | MENU | Ciao")

    def test_negativa_id_doppio(self):
        with self.assertRaisesRegex(G.ErroreTesti, "gia' usato"):
            genera("X | HUD | Ciao", "X | HUD | Addio")

    def test_negativa_id_non_valido(self):
        with self.assertRaisesRegex(G.ErroreTesti, "ID 'saluto' non valido"):
            genera("saluto | HUD | Ciao")


# Le tabelle generate si leggono solo dalle funzioni di include/testo.h (con BN_ASSERT su tabella e
# indice). Un accesso diretto "TABELLA[" altrove scavalcherebbe il controllo.
TABELLE = ["GLIFI", "BYTE_GLIFO", "X_GLIFO", "RIGHE", "TAGLI", "TESTI", "CONTESTO_LARGHEZZA",
           "CONTESTO_RIGHE", "FONT", "CORNICE_PALETTE", "CORNICE_TILE", "LATO_ORIZZONTALE",
           "LATO_VERTICALE", "AREE", "ANELLO", "TILE_FONDALE", "PALETTE_FONDALI", "TILE_GIOCATORE",
           "PALETTE_GIOCATORE", "PALETTE_SFONDO", "PALETTE_SANTI", "PALETTE_NEMICI", "SFONDO", "TILE_SFONDO"]
# I file che le definiscono o le avvolgono: header generati e la funzione d'accesso.
DEFINIZIONI = {"include/testi.h", "include/tabella.h", "include/mondo.h", "include/battaglia_grafica.h"}
ACCESSO_DIRETTO = re.compile(r"\b(" + "|".join(TABELLE) + r")\s*\[")


def accessi_diretti(nome, testo):
    trovati = []
    for n, riga in enumerate(testo.splitlines(), 1):
        codice = riga.split("//", 1)[0]
        # in un static_assert l'indice e' costante: fuori tabella e' gia' un errore di compilazione
        if "static_assert" in codice:
            continue
        for m in ACCESSO_DIRETTO.finditer(codice):
            # una dichiarazione "constexpr ... NOME[" e' la definizione, non un accesso
            if "constexpr" in codice[:m.start()]:
                continue
            trovati.append(f"{nome}:{n}: {riga.strip()}")
    return trovati


class AccessoTabelle(unittest.TestCase):

    def test_nessun_accesso_diretto(self):
        trovati = []
        for p in glob.glob(os.path.join(RADICE, "src", "*.cpp")) + glob.glob(os.path.join(RADICE, "include", "*.h")):
            nome = os.path.relpath(p, RADICE).replace(os.sep, "/")
            if nome in DEFINIZIONI:
                continue
            with open(p, encoding="utf-8") as f:
                trovati += accessi_diretti(nome, f.read())
        self.assertEqual(trovati, [])

    def test_negativa_accesso_diretto(self):
        self.assertTrue(accessi_diretti("finto.cpp", "int g = testi::GLIFI[i];"))
        self.assertTrue(accessi_diretti("finto.cpp", "auto& t = TESTI [3];"))

    def test_static_assert_ammesso(self):
        self.assertEqual(accessi_diretti("finto.cpp", 'static_assert(CORNICE_PALETTE[0] == 0, "x");'), [])

    def test_accesso_tramite_voce_ammesso(self):
        self.assertEqual(accessi_diretti("finto.cpp", "return GUBBIO_VOCE(testi::GLIFI, glifo);"), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
