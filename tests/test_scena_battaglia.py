"""La scena di battaglia (F4, parte 2): la grafica procedurale di tools/genera_battaglia.py e le
regole della scena (src/scena_battaglia.cpp) che si controllano senza GBA. La regola centrale, le
barre che cambiano solo consumando l'evento, e' provata a tempo di compilazione in
src/autotest_vista.cpp (con la sua negativa); qui si controlla che la scena non la scavalchi.
Ogni prova ha la sua negativa."""
import copy
import importlib.util
import os
import re
import sys
import unittest

from _stile import RADICE, S

_spec = importlib.util.spec_from_file_location("genera_battaglia", os.path.join(RADICE, "tools", "genera_battaglia.py"))
GB = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(GB)

PALETTE = S.carica("palette")
SCENA = open(os.path.join(RADICE, "src", "scena_battaglia.cpp"), encoding="utf-8").read()


def colori_della_guida():
    return {c for r in PALETTE["rampe"] for c in r["giorno"]}


def fuori_guida(palette):
    return [r for r in palette if S.colore(PALETTE, r) not in colori_della_guida()]


def letture_dal_modello(sorgente):
    """Le righe che darebbero a una barra i PV o il Fervore letti dal modello invece che dalla vista."""
    return [r.strip() for r in sorgente.splitlines()
            if re.search(r"\.mostra\(.*g_scena\.(eroe|nemico)\(", r) or
            re.search(r"Barra.*g_scena\.(eroe|nemico)\(.*\.(pv|fervore)", r)]


class Grafica(unittest.TestCase):

    def test_header_aggiornato(self):
        with open(GB.USCITA, encoding="utf-8") as f:
            self.assertEqual(f.read(), GB.genera(PALETTE), "eseguire python tools/genera_battaglia.py --scrivi")

    def test_negativa_header_vecchio(self):
        altra = copy.deepcopy(PALETTE)
        neutri = next(r for r in altra["rampe"] if r["nome"] == "neutri")
        neutri["giorno"][0] ^= 1
        with open(GB.USCITA, encoding="utf-8") as f:
            self.assertNotEqual(f.read(), GB.genera(altra))

    def test_colori_dalla_guida(self):
        for pal in (GB.PALETTE_SFONDO, GB.PALETTE_SANTI, GB.PALETTE_NEMICI):
            self.assertEqual(len(pal), 16)
            self.assertEqual(fuori_guida(pal), [])

    def test_negativa_colore_inventato(self):
        with self.assertRaises(Exception):
            fuori_guida([("magenta", 0)])

    def test_tre_sfondi_entro_i_tile(self):
        tile, mappe = GB.tile_e_mappe()
        self.assertLessEqual(len(tile), 512)
        self.assertEqual(len(mappe), 3)
        self.assertEqual(len({tuple(m) for m in mappe}), 3, "uno sfondo diverso per incontro")

    def test_pannello_dei_comandi(self):
        for i in range(3):
            t = GB.sfondo(i)
            scuri = sum(1 for y in range(GB.PANNELLO_Y + 4, 156) for x in range(4, 236) if t.px[y][x] in (0, 15))
            self.assertGreater(scuri, 0.95 * (156 - GB.PANNELLO_Y - 4) * 232)

    def test_negativa_pannello_mancante(self):
        t = GB.sfondo(0)
        for y in range(GB.PANNELLO_Y, 160):
            t.px[y] = [8] * 256
        scuri = sum(1 for y in range(GB.PANNELLO_Y + 4, 156) for x in range(4, 236) if t.px[y][x] in (0, 15))
        self.assertEqual(scuri, 0)

    def test_figure_riconoscibili(self):
        """Ogni figura ha lo sfondo trasparente e il contorno; le due pose sono diverse; nessuna figura
        e' uguale a un'altra."""
        viste = set()
        for _, pittore in GB.SANTI + GB.NEMICI:
            ferma, azione = pittore(False), pittore(True)
            self.assertEqual(ferma.px[0][0], 0)
            self.assertIn(GB.C, {c for r in ferma.px for c in r})
            self.assertNotEqual(ferma.px, azione.px)
            chiave = tuple(map(tuple, ferma.px))
            self.assertNotIn(chiave, viste)
            viste.add(chiave)
        self.assertEqual(GB.corrado(False).w, 64)

    def test_negativa_figura_doppia(self):
        a, b = GB.ubaldo(False), GB.ubaldo(False)
        self.assertEqual(tuple(map(tuple, a.px)), tuple(map(tuple, b.px)))


class Scena(unittest.TestCase):

    def test_le_barre_si_leggono_dalla_vista(self):
        self.assertEqual(letture_dal_modello(SCENA), [])
        self.assertIn("_pv[s].mostra(_vista.pv(s), _vista.pv_max(s));", SCENA)
        self.assertIn("_fervore[e].mostra(_vista.fervore(e), _vista.fervore_max(e));", SCENA)

    def test_negativa_barra_letta_dal_modello(self):
        finto = "    _pv[s].mostra(g_scena.eroe(s).pv, g_scena.eroe(s).pv_max);"
        self.assertTrue(letture_dal_modello(finto))

    def test_pv_in_cifre_dalla_vista(self):
        """I PV dei Santi in cifre accanto alle barre si scrivono dalla vista, come le barre."""
        self.assertIn("_numeri_pv[e].mostra(_vista.pv(e));", SCENA)
        self.assertEqual(re.findall(r"_numeri_pv\[[a-z]+\]\.mostra\(([^;]*)\);", SCENA), ["_vista.pv(e)"])

    def test_negativa_pv_in_cifre_dal_modello(self):
        finto = "_numeri_pv[e].mostra(g_scena.eroe(e).pv);"
        self.assertNotEqual(re.findall(r"_numeri_pv\[[a-z]+\]\.mostra\(([^;]*)\);", finto), ["_vista.pv(e)"])
        self.assertTrue(letture_dal_modello("    _numeri_pv[e].mostra(g_scena.eroe(e).pv);"))

    def test_scelta_del_bersaglio(self):
        """Il bersaglio parte dal predefinito del modello e si sposta fra i vivi (le regole sono provate
        a tempo di compilazione in src/autotest_vista.cpp); B torna alla scelta del comando."""
        corpo = SCENA[SCENA.index("bool scegli_bersaglio("):SCENA.index("void anima(")]
        self.assertIn("bersaglio_predefinito(g_scena, mira)", corpo)
        self.assertIn("prossimo_bersaglio(g_scena, mira, scelto,", corpo)
        self.assertIn("comando.bersaglio = scelto;", corpo)
        self.assertIn("b_pressed()", corpo)
        vista = open(os.path.join(RADICE, "src", "autotest_vista.cpp"), encoding="utf-8").read()
        self.assertIn("static_assert(prova_bersagli()", vista)
        self.assertIn("static_assert(giro_cieco_finisce_su_un_caduto()", vista)

    def test_negativa_bersaglio_scelto_a_mano(self):
        finto = "bool scegli_bersaglio( scelto = (scelto + 1) % 3; void anima("
        corpo = finto[finto.index("bool scegli_bersaglio("):finto.index("void anima(")]
        self.assertNotIn("prossimo_bersaglio(g_scena, mira, scelto,", corpo)

    def test_un_attore_per_volta(self):
        """Nell'animazione di un evento si muove solo m.attore: nessun altro sprite cambia x se non il
        bersaglio che trema."""
        anima = SCENA[SCENA.index("void anima("):SCENA.index("int scegli_incontro(")]
        mossi = set(re.findall(r"_sprite\[([a-z.]+)\]->set_x", anima))
        self.assertEqual(mossi, {"m.attore", "m.bersaglio"})

    def test_negativa_due_attori(self):
        finto = "void anima(\n _sprite[m.attore]->set_x(1); _sprite[altro]->set_x(2);\nint scegli_incontro("
        anima = finto[finto.index("void anima("):finto.index("int scegli_incontro(")]
        self.assertNotEqual(set(re.findall(r"_sprite\[([a-z.]+)\]->set_x", anima)), {"m.attore", "m.bersaglio"})

    def test_avvio_4_e_5(self):
        main = open(os.path.join(RADICE, "src", "main.cpp"), encoding="utf-8").read()
        self.assertIn("GUBBIO_AVVIO == 4", main)
        self.assertIn("menu_battaglie(palette)", main)
        self.assertIn("GUBBIO_AVVIO == 5", main)
        self.assertIn("istantanee_battaglie(palette)", main)


if __name__ == "__main__":
    unittest.main(verbosity=2)
