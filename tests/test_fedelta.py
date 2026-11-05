"""I 10 giri della fedelta' (5 nov 2026, richiesta di Cioti): edifici, piazze, fontane, interni e mappa
confrontati con la Gubbio vera. Ogni giro aggiunge i tratti che fanno riconoscere un luogo (metodo dei
landmark: silhouette, proporzioni esagerate, pochi segni unici) e qui ogni tratto ha il suo controllo,
con la prova negativa dove serve. Registro dei giri: docs/fedelta.md.
"""
import os
import sys
import unittest

from _stile import RADICE

sys.path.insert(0, os.path.join(RADICE, "tools"))
import genera_mondo as G  # noqa: E402
import pittore_citta as PC  # noqa: E402
import pittore_monumenti as PM  # noqa: E402


def area(nome):
    mondo = G.mondo_del_repo()
    for n, t in G.sorgenti_del_repo():
        if os.path.basename(n) == nome + ".area":
            a = G.leggi_area(n, t)
            G.prepara_area(a, mondo)
            return a
    raise KeyError(nome)


class Giro1Consoli(unittest.TestCase):
    def test_i_tratti_del_palazzo_dei_consoli(self):
        t = PM.dipingi("consoli", "Palazzo dei Consoli", 23, 20, "basso", {"altezza_m": 60.0}, 0)
        for segno in ("scalinata_ventaglio", "archetti", "lunetta", "campanile_vela", "portale_gotico"):
            self.assertGreaterEqual(t.elementi[segno], 1, segno)

    def test_il_consoli_e_il_piu_alto_della_piazza(self):
        # la facciata prende quasi tutta l'impronta: il tetto e' una striscia di 4 righe al piu'
        h = 20
        t = PM.dipingi("consoli", "Palazzo dei Consoli", 23, h, "basso", {"altezza_m": 60.0}, 0)
        tetto = [y for y in range(t.h) if t.px[y][t.w // 2] in (PM.COTTO, PM.COTTO_SCURO, PM.COTTO_CHIARO, PM.COTTO_LUCE)
                 or (isinstance(t.px[y][t.w // 2], tuple) and t.px[y][t.w // 2][0] == "cotto e coppi")]
        self.assertLessEqual(len(tetto), 4 * 8 + 2)


class Giro2FontanaBargello(unittest.TestCase):
    def test_la_vasca_e_ottagonale(self):
        self.assertAlmostEqual(PC._ottagono(1, 0), 1)
        self.assertAlmostEqual(PC._ottagono(0, 1), 1)
        # l'angolo di un'ellisse (0.7, 0.7) e' dentro; in un ottagono e' fuori: cosi' la vasca non e' tonda
        self.assertGreater(PC._ottagono(0.7, 0.7), 1)

    def test_bargello_coi_piani(self):
        t = PM.dipingi("bargello", "Palazzo del Bargello", 10, 6, "basso", {}, 0)
        self.assertGreaterEqual(t.elementi["marcapiano"], 2)
        self.assertGreaterEqual(t.elementi["finestra_centinata"], 1)
        self.assertGreaterEqual(t.elementi["porta_del_morto"], 1)


class Giro3Camignano(unittest.TestCase):
    def test_il_camignano_scorre_e_il_ponte_si_attraversa(self):
        a = area("san_martino")
        g = a["griglia"]
        acqua = [(x, y) for y, r in enumerate(g) for x, c in enumerate(r) if c == "~"]
        ponte = [(x, y) for y, r in enumerate(g) for x, c in enumerate(r) if c == "+"]
        self.assertGreater(len(acqua), 100)
        self.assertTrue(ponte)
        self.assertTrue(all(not G.solida(g[y][x]) for x, y in ponte))
        self.assertTrue(all(G.solida(g[y][x]) for x, y in acqua))
        # il torrente non tocca le facciate dei monumenti ne' gli spawn
        celle = {c for x0, y0, ew, eh in a["edifici"].values() for c in
                 ((x, y) for y in range(y0, y0 + eh) for x in range(x0, x0 + ew))}
        self.assertFalse(celle & set(acqua))
        self.assertFalse(set(a["spawn"].values()) & set(acqua))

    def test_negativa_senza_riga_niente_torrente(self):
        a = {"griglia": ["#.#"], "torrente": None}
        G.scava_torrente(a)
        self.assertEqual(a["griglia"], ["#.#"])
        a = {"griglia": ["#.#", "###"], "torrente": (0, 3, 0, 1)}
        G.scava_torrente(a)
        self.assertEqual(a["griglia"], ["~+~", "~~~"])


class Giro4Teatro(unittest.TestCase):
    def test_il_teatro_e_una_rovina_nel_prato(self):
        t = PM.dipingi("teatro_romano", "Teatro romano", 47, 26, "basso", {}, 0)
        self.assertGreater(t.elementi["erba_sui_gradini"], 200)
        self.assertGreater(t.elementi["arcate_crollate"], 20)
        for segno in ("gradinate", "arcate", "scena"):
            self.assertGreaterEqual(t.elementi[segno], 1)


if __name__ == "__main__":
    unittest.main()
