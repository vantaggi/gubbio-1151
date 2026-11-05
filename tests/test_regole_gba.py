"""Le regole di sviluppo GBA (docs/regole_sviluppo_gba.md) controllate in automatico.

Il codice di src/ e include/ le rispetta (tools/controlla_regole_gba.py) e ogni controllo sa accorgersi di
una violazione (prove negative). L'ordine dei campi delle struct (tools/controlla_struct.py) ha bisogno di
clang e gira nella CI come passo a se'; qui si prova la sua logica su un dump finto e si controlla che le
eccezioni (tabelle in ROM) non finiscano in RAM. Il gate delle divisioni (tools/controlla_divisioni.py) gira
in build.sh sulla ROM; qui si prova su un disassemblato finto.
"""
import os
import sys
import unittest

from _stile import RADICE

sys.path.insert(0, os.path.join(RADICE, "tools"))
import controlla_divisioni as D  # noqa: E402
import controlla_regole_gba as R  # noqa: E402
import controlla_struct as S  # noqa: E402

DUMP = """
*** Dumping AST Record Layout
         0 | struct gubbio::prova::Male
         0 |   uint8_t a
         4 |   int b
         8 |   _Bool c
           | [sizeof=12, dsize=12, align=4,
           |  nvsize=12, nvalign=4]

*** Dumping AST Record Layout
         0 | struct gubbio::prova::Bene
         0 |   int b
         4 |   uint8_t a
         5 |   _Bool c
           | [sizeof=8, dsize=8, align=4,
           |  nvsize=8, nvalign=4]
"""

DISASSEMBLATO = """
08000100 <gubbio::Esplorazione::aggiorna()>:
 8000100:	movs	r1, #6
 8000102:	bl	803eed4 <____aeabi_idiv_from_thumb>
 8000106:	bx	lr

08000200 <gubbio::Folla::aggiorna(gubbio::Esplorazione const&, int, int, int)>:
 8000202:	bl	803eed4 <__aeabi_uidivmod>
"""


class RegoleSulCodice(unittest.TestCase):
    def test_il_codice_rispetta_le_regole(self):
        self.assertEqual(R.controlla(), [])

    def test_ogni_regola_si_accorge(self):
        casi = {
            "float x = 1;": "R1",
            "#include <vector>": "R1",
            "std::array<int, 3> a;": "R1",
            "int* p = new int(3);": "R2",
            "const int T[3] = { 1, 2, 3 };": "R3",
            "const AreaId A[2] = { AreaId::PIAZZA_GRANDE, AreaId::SAN_MARTINO };": "R3",
            "void f(GameState p);": "R4",
            "void f(int a, bn::vector<int, 4> v);": "R4",
            "bn::sprite_text_generator g;": "R5",
            "BN_CODE_IWRAM void f();": "R6",
            "esplorazione.sospendi();\nscena_battaglia(0, 1, g, p);": "R8",
        }
        for riga, regola in casi.items():
            errori = R.controlla_testo("src/x.cpp", riga + "\n")
            self.assertEqual(len(errori), 1, riga)
            self.assertIn(" " + regola + " ", errori[0], riga)

    def test_quello_che_e_permesso(self):
        for riga in ("constexpr int T[3] = { 1, 2, 3 };",
                     "const int v[2] = { a.x, b };",            # valori del momento: non e' una tabella
                     "void f(const GameState& p);",
                     "consteval GameState respira(GameState p, int cella);",
                     "Scena(const Scena&) = delete;",
                     "// IWRAM: il giro delle collisioni, 300 volte per frame\nBN_CODE_IWRAM void f();",
                     "// un float nel commento non conta",
                     "GameState prima = g_game_state;",
                     "esplorazione.sospendi();\n\n    attendi(1);",
                     "esplorazione->sospendi();\nbn::core::update();"):
            self.assertEqual(R.controlla_testo("src/x.cpp", riga + "\n"), [], riga)

    def test_gli_autotest_possono_avere_tabelle_locali(self):
        self.assertEqual(R.controlla_testo("src/autotest_x.cpp", "const int T[3] = { 1, 2, 3 };\n"), [])


class OrdineDeiCampi(unittest.TestCase):
    def test_spreco_trovato_e_riordino_giusto(self):
        self.assertEqual(S.sprechi(DUMP), [("gubbio::prova::Male", 12, 8)])

    def test_migliore(self):
        self.assertEqual(S.migliore([(1, 1), (4, 4), (1, 1)]), 8)
        self.assertEqual(S.migliore([(2, 2), (1, 1)]), 4)

    def test_le_eccezioni_restano_in_rom(self):
        for nome in S.ECCEZIONI:
            self.assertEqual(S.copie_in_ram(nome), [], nome)

    def test_copia_in_ram_trovata(self):
        # una variabile del tipo fuori da constexpr la troverebbe: lo si prova su un tipo che in RAM c'e' davvero
        self.assertNotEqual(S.copie_in_ram("gubbio::battaglia::Unita"), [])


class Divisioni(unittest.TestCase):
    def test_conta(self):
        conti = D.conta(DISASSEMBLATO)
        self.assertEqual(conti["gubbio::Esplorazione::aggiorna()"], 1)
        self.assertEqual(conti["gubbio::Folla::aggiorna(gubbio::Esplorazione const&, int, int, int)"], 1)

    def test_fuori_budget(self):
        errori = D.fuori_budget(D.conta(DISASSEMBLATO))
        self.assertEqual(len(errori), 1)
        self.assertIn("Esplorazione::aggiorna", errori[0])

    def test_build_lo_chiama(self):
        with open(os.path.join(RADICE, "build.sh"), encoding="utf-8") as f:
            self.assertIn("tools/controlla_divisioni.py", f.read())


class Documento(unittest.TestCase):
    def test_regole_nel_repo_e_richiamate(self):
        self.assertTrue(os.path.isfile(os.path.join(RADICE, "docs", "regole_sviluppo_gba.md")))
        with open(os.path.join(RADICE, "README.md"), encoding="utf-8") as f:
            self.assertIn("docs/regole_sviluppo_gba.md", f.read())


if __name__ == "__main__":
    unittest.main()
