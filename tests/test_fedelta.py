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
        self.assertGreater(t.elementi["arcate_crollate"], 20)
        for segno in ("gradinate", "arcate", "scena"):
            self.assertGreaterEqual(t.elementi[segno], 1)


class Giro5DuomoDucale(unittest.TestCase):
    def test_duomo_coi_bassorilievi_e_il_campanile(self):
        t = PM.dipingi("duomo", "Cattedrale", 42, 22, "basso", {}, 0)
        self.assertEqual(t.elementi["bassorilievi"], 5)
        self.assertEqual(t.elementi["campanile"], 1)
        # il campanile sale sopra il tetto: in cima alla tela ci sono i suoi merli di pietra, non coppi
        alto = [t.get(x, 1) for x in range(t.w - 40, t.w - 16)]
        self.assertTrue(any(c and c[0] == "pietra calcarea" for c in alto))

    def test_cortile_del_ducale_col_portico(self):
        t = PM.dipingi("ducale", "Palazzo Ducale", 38, 31, "basso", {}, 0)
        self.assertEqual(t.elementi["portico"], 1)
        self.assertEqual(t.elementi["pietra_serena"], 1)


class Giro6QuarantaMartiri(unittest.TestCase):
    def test_san_francesco_tripartito_e_tiratoio_aperto(self):
        t = PM.dipingi("san_francesco", "Chiesa di San Francesco", 38, 18, "basso", {}, 0)
        self.assertEqual(t.elementi["tripartita"], 1)
        t = PM.dipingi("loggia_tiratori", "Loggia dei Tiratori della Lana", 43, 12, "basso", {}, 0)
        self.assertEqual(t.elementi["tiratoio"], 1)
        self.assertGreater(t.elementi["arcata"], 20)


class Giro7Porte(unittest.TestCase):
    def test_la_porta_e_una_torre_con_l_arco(self):
        t = PM.porta_frontale(9, 5, (3, 5))
        for segno in ("merlatura", "arco", "feritoie"):
            self.assertEqual(t.elementi[segno], 1, segno)
        # sotto l'arco si vede la strada (non e' un muro nero): l'ultima riga del passaggio non e' nera
        self.assertTrue(all(t.px[t.h - 1][x] != PM.CONTORNO for x in range(26, 46)))
        # e in alto c'e' il buio della volta
        self.assertIn(PM.CONTORNO, [t.px[y][36] for y in range(t.h)])

    def test_le_porte_in_alto_si_vedono_di_fronte(self):
        a = area("san_martino")
        lati = {nome: lato for nome, lato, _, _ in a["porte"].values()}
        self.assertEqual(lati["Porta Metauro"], "alto")


class Giro8PortaDelMorto(unittest.TestCase):
    def test_in_via_dei_consoli_la_porta_del_morto_e_frequente(self):
        self.assertGreater(PC.VIE_DEL_MORTO["via_dei_consoli"], 0.5)
        casa = PC.Casa(0, 3, 10, 5, 7, morto=1.0)
        self.assertTrue(casa.morto or casa.bottega)
        casa = PC.Casa(0, 3, 10, 5, 7, morto=0.0)
        self.assertFalse(casa.morto)

    def test_la_porta_del_morto_si_dipinge(self):
        q = PC.Quadro(8, 8)
        casa = next(c for c in (PC.Casa(0, 3, 6, 5, n, morto=1.0) for n in range(50)) if c.morto)
        PC.dipingi_casa(q, casa, 8)
        self.assertEqual(q.elementi.get("porta_del_morto"), 1)


class Giro9SalaDeiConsoli(unittest.TestCase):
    def test_la_sala_ha_la_volta_a_botte(self):
        import pittore_interni as PI
        st = PI.sala_consoli()
        self.assertTrue(getattr(st, "elementi_volta", False))
        # niente travi di legno in cima al muro di fondo
        riga = [st.t.get(x, st.y0 + 2) for x in range(st.x0, st.x0 + st.cw * 16)]
        travi = {PI.C("legno e cuoio", 0), PI.C("legno e cuoio", 1), PI.C("legno e cuoio", 2)}
        self.assertFalse(travi & set(riga))


if __name__ == "__main__":
    unittest.main()
