"""La caccia ai crash (docs/caccia_ai_crash.md): la rete che prende gli assert, i limiti delle risorse e il
giocatore scimmia sono agganciati e nessuno li ha spenti. Ogni controllo ha la sua prova negativa."""
import json
import os
import re
import sys
import unittest

from _stile import RADICE

sys.path.insert(0, os.path.join(RADICE, "tools"))
import prove_mgba as P  # noqa: E402


def leggi(*parti):
    with open(os.path.join(RADICE, *parti), encoding="utf-8") as f:
        return f.read()


def prove():
    return json.loads(leggi("tests", "mgba", "prove.json"))["prove"]


def assert_agganciato(main, limiti):
    """L'assert va nel log in ogni build: installa() subito dopo bn::core::init(), la callback impostata
    senza #ifdef e la riga che il banco cerca."""
    dopo_init = main[main.index("bn::core::init();"):][:400]
    if "gubbio::limiti::installa();" not in dopo_init:
        return False
    corpo = limiti[limiti.index("void installa()"):]
    prima_dell_if = corpo.split("#if", 1)[0]
    return "bn::assert::set_callback(all_assert);" in prima_dell_if and '"ASSERT scattato area "' in limiti


def caccia_completa(lista):
    """Le cacce: gioco vero, slot, salti d'area, tutte con GUBBIO_LIMITI e il comando caso; e la rete."""
    cacce = [p for p in lista if p["nome"].startswith("caccia")]
    modi = {p["modo"] for p in cacce}
    if not {0, 13, 15} <= modi:
        return False
    for p in cacce:
        if "-DGUBBIO_LIMITI" not in p.get("flag", []) or not any(c.startswith("caso ") for c in p.get("copione", [])):
            return False
        if "vietate" in p or set(p.get("tetti", {})) - {"fondali"}:
            return False
    rete = [p for p in lista if p["nome"] == "rete"]
    return len(rete) == 1 and rete[0].get("assert_atteso") and "-DGUBBIO_PROVA_ASSERT" in rete[0]["flag"]


class Rete(unittest.TestCase):
    def test_assert_nel_log(self):
        self.assertTrue(assert_agganciato(leggi("src", "main.cpp"), leggi("src", "limiti.cpp")))

    def test_assert_nel_log_negativa(self):
        main, limiti = leggi("src", "main.cpp"), leggi("src", "limiti.cpp")
        self.assertFalse(assert_agganciato(main.replace("gubbio::limiti::installa();", ""), limiti))
        self.assertFalse(assert_agganciato(main, limiti.replace("bn::assert::set_callback(all_assert);", "")))
        chiuso = limiti.replace("    bn::assert::set_callback(all_assert);",
                                "#ifdef GUBBIO_LIMITI\n    bn::assert::set_callback(all_assert);\n#endif", 1)
        self.assertFalse(assert_agganciato(main, chiuso))

    def test_il_banco_cerca_la_riga(self):
        banco = leggi("tools", "banco_mgba.c")
        self.assertIn('strstr(ultimo, "ASSERT scattato")', banco)
        self.assertIn('foto("assert")', banco)
        self.assertIn("mLOG_GAME_ERROR", banco)
        for vietata in (r"(?i)\bassert", r"^!! bloccato", r"^MGBA "):
            self.assertIn(vietata, P.VIETATE)

    def test_le_cacce(self):
        self.assertTrue(caccia_completa(prove()))

    def test_le_cacce_negativa(self):
        lista = prove()
        senza_limiti = json.loads(json.dumps(lista))
        next(p for p in senza_limiti if p["nome"].startswith("caccia"))["flag"] = []
        self.assertFalse(caccia_completa(senza_limiti))
        self.assertFalse(caccia_completa([p for p in lista if p["modo"] != 13 or p["nome"] == "rete"]))
        self.assertFalse(caccia_completa([p for p in lista if p["nome"] != "rete"]))
        tetto_alto = json.loads(json.dumps(lista))
        next(p for p in tetto_alto if p["nome"].startswith("caccia"))["tetti"] = {"sprite": 100}
        self.assertFalse(caccia_completa(tetto_alto))


class Tetti(unittest.TestCase):
    RIGHE = ["LIMITI picco sprite 60 su 128 (46%) area 0 frame 1",
             "LIMITI picco sprite 120 su 128 (93%) area 3 frame 9",
             "LIMITI picco fondali 4 su 4 (100%) area -1 frame 2",
             "LIMITI picco colori_sprite 208 su 256 (81%) area 14 frame 5"]

    def test_soglia(self):
        errori = P.vicino_al_tetto(self.RIGHE, {"fondali": 100})
        self.assertEqual(len(errori), 1)
        self.assertIn("sprite vicino al tetto: 120 su 128 (93%", errori[0])

    def test_soglia_negativa(self):
        self.assertEqual(P.vicino_al_tetto(self.RIGHE[:1] + self.RIGHE[2:], {"fondali": 100}), [])
        self.assertEqual(len(P.vicino_al_tetto(self.RIGHE, {})), 2)          # senza eccezione anche i fondali
        self.assertEqual(P.vicino_al_tetto(["LIMITI picco sprite 1 su 2 (50%)"], {}), [])

    def test_ogni_risorsa_ha_la_sua_riga(self):
        limiti = leggi("src", "limiti.cpp")
        nomi = re.findall(r'\{ "(\w+)", \w+, \w+ \}', limiti)
        self.assertGreaterEqual(len(nomi), 12)
        for n in ("sprite", "tile_sprite", "colori_sprite", "tile_fondali", "blocchi_vram_fondali", "stack_iwram"):
            self.assertIn(n, nomi)
        for n in nomi:
            self.assertTrue(P.PICCO.match(f"LIMITI picco {n} 1 su 2 (50%) area 0 frame 0"), n)


if __name__ == "__main__":
    unittest.main()
