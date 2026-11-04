"""I fondali allo standard grafico (pezzo EDI): il pittore della citta' (tools/pittore_citta.py) ridipinge suolo,
case, tetti, verde, belvedere, mura e Monte con le rampe dello standard, e ogni tile sta in uno dei 6 banchi di
palette. Qui: i banchi, il budget dei tile, la luce (L1), la prospettiva degli oggetti (M6), le ombre (L4) e la
regola che il disegno non tocca le collisioni. Ogni regola ha il suo caso negativo.
"""
import os
import sys
import unittest

from _stile import RADICE

sys.path.insert(0, os.path.join(RADICE, "tools"))
import genera_mondo as G  # noqa: E402
import pittore_citta as PC  # noqa: E402


def area(nome):
    mondo = G.mondo_del_repo()
    src = [s for s in G.sorgenti_del_repo() if s[0].endswith("/%s.area" % nome)][0]
    a = G.leggi_area(*src)
    G.prepara_area(a, mondo)
    return a, mondo


class Banchi(unittest.TestCase):

    def test_sei_banchi_da_sedici(self):
        self.assertEqual(len(G.BANCHI_FONDALI), 6)
        for banco in G.BANCHI_FONDALI:
            self.assertEqual(len(banco), 16)
            self.assertEqual(banco[0], PC.FONDO)
            self.assertEqual(len(set(banco[1:])), 15, banco)

    def test_ogni_colore_dei_banchi_esiste_nello_stile(self):
        banchi = G.banchi_fondali(G.S.carica("palette"))
        self.assertEqual(len(banchi), 6)
        self.assertTrue(all(len(b) == 16 and all(0 <= c < 0x8000 for c in b) for b in banchi))

    def test_un_tile_tutto_pietra_sta_nel_banco_della_pietra(self):
        q = PC.Quadro(1, 1)
        for y in range(8):
            for x in range(8):
                q.px[y][x] = (PC.P, 5) if (x + y) % 2 else (PC.N, 2)
        b, _ = G.indicizza_tile(q, 0, 0, {"id": "prova"})
        self.assertNotIn("prova", G.COMPROMESSI)
        self.assertIn((PC.P, 5), G.BANCHI_FONDALI[b])

    def test_negativa_colori_che_nessun_banco_tiene_insieme(self):
        """Cotto chiaro, acqua scura e verde chiaro nello stesso tile: nessun banco li ha tutti, e' un compromesso."""
        q = PC.Quadro(1, 1)
        for y in range(8):
            for x in range(8):
                q.px[y][x] = ((PC.T, 5), (PC.A, 0), (PC.V, 4))[(x + y) % 3]
        G.COMPROMESSI.pop("prova_negativa", None)
        G.indicizza_tile(q, 0, 0, {"id": "prova_negativa"})
        self.assertEqual(len(G.COMPROMESSI["prova_negativa"]), 1)


class AreeAlloStandard(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.aree = {}
        for nome in ("san_martino", "piazza_grande", "teatro_romano", "monte_ingino"):
            a, mondo = area(nome)
            G.COMPROMESSI.pop(nome, None)
            a["tile"], a["indici"], _ = G.disegna_area(a, mondo)
            cls.aree[nome] = a

    def test_budget_dei_tile(self):
        for nome, a in self.aree.items():
            self.assertLessEqual(len(a["tile"]), G.TILE_MAX_PER_AREA, nome)

    def test_pochi_compromessi_di_banco(self):
        """Al piu' il 2% dei tile di un'area prende un colore vicino al posto di quello voluto."""
        for nome, a in self.aree.items():
            celle = a["larghezza"] * a["altezza"]
            self.assertLess(len(G.COMPROMESSI.get(nome, [])), celle * 0.02, nome)

    def test_banchi_e_specchi_per_ogni_tile(self):
        for nome, a in self.aree.items():
            self.assertEqual(len(a["banchi"]), len(a["tile"]), nome)
            self.assertEqual(len(a["specchi"]), len(a["indici"]), nome)
            self.assertTrue(all(0 <= b < 6 for b in a["banchi"]), nome)
            self.assertTrue(all(0 <= s < 4 for s in a["specchi"]), nome)

    def test_due_run_uguali(self):
        """Il pittore non tiene stato fra un'area e l'altra: rifatta, l'area esce identica."""
        a, mondo = area("via_xx_settembre")
        t1 = G.disegna_area(a, mondo)[0]
        a, mondo = area("via_xx_settembre")
        t2 = G.disegna_area(a, mondo)[0]
        self.assertEqual(t1, t2)


class Collisioni(unittest.TestCase):

    def test_il_disegno_non_cambia_la_griglia(self):
        a, mondo = area("san_martino")
        prima = list(a["griglia"])
        G.disegna_area(a, mondo)
        self.assertEqual(a["griglia"], prima)

    def test_negativa_facciata_solo_su_celle_solide(self):
        """Le case stanno sulle celle di muro: nessun pixel di facciata su una cella calpestabile."""
        a, mondo = area("san_martino")
        g = a["griglia"]
        q = PC.Quadro(a["larghezza"], a["altezza"])
        calp = lambda x, y: 0 <= y < len(g) and 0 <= x < len(g[0]) and not G.solida(g[y][x])  # noqa: E731
        celle = {(x, y) for y in range(len(g)) for x in range(len(g[0])) if g[y][x] == "#"}
        case = PC.dividi_in_case(g, celle, calp)
        self.assertTrue(case)
        for casa in case:
            for y in range(casa.yb - casa.fh + 1, casa.yb + 1):
                for x in range(casa.x0, casa.x1 + 1):
                    self.assertFalse(calp(x, y), (x, y))
        # il caso negativo: con una via al posto del muro, quella cella non e' piu' di nessuna facciata
        casa = case[0]
        g2 = [list(r) for r in g]
        g2[casa.yb][casa.x0] = "."
        g2 = ["".join(r) for r in g2]
        calp2 = lambda x, y: 0 <= y < len(g2) and 0 <= x < len(g2[0]) and not G.solida(g2[y][x])  # noqa: E731
        celle2 = celle - {(casa.x0, casa.yb)}
        for c in PC.dividi_in_case(g2, celle2, calp2):
            celle_casa = {(x, y) for y in range(c.yb - c.fh + 1, c.yb + 1) for x in range(c.x0, c.x1 + 1)}
            self.assertNotIn((casa.x0, casa.yb), celle_casa)


class Luce(unittest.TestCase):

    def _tetto(self):
        q = PC.Quadro(4, 4)
        colmo = PC.dipingi_tetto(q, 0, 31, 0, 31, 3, 0)
        return q, colmo

    @staticmethod
    def _media(q, xs, ys):
        v = [q.px[y][x][1] for y in ys for x in xs]
        return sum(v) / len(v)

    def test_tetto_alla_luce_dello_standard(self):
        """F1, L1: la falda lontana (sopra il colmo) e' un tono sotto quella vicina; il bordo sinistro prende la
        luce, il destro l'ombra."""
        q, colmo = self._tetto()
        self.assertLess(self._media(q, range(4, 28), range(0, colmo)), self._media(q, range(4, 28), range(colmo + 2, 26)))
        self.assertGreater(self._media(q, [0], range(colmo + 2, 26)), self._media(q, [31], range(colmo + 2, 26)))

    def test_negativa_tetto_specchiato(self):
        """Lo stesso tetto specchiato ha la luce a destra: il controllo lo rifiuta."""
        q, colmo = self._tetto()
        q.px = [r[::-1] for r in q.px]
        self.assertFalse(self._media(q, [0], range(colmo + 2, 26)) > self._media(q, [31], range(colmo + 2, 26)))

    def test_roccia_chiara_in_alto_a_sinistra(self):
        q = PC.Quadro(1, 1)
        PC.dipingi_roccia(q, 0, 0, 0)
        self.assertGreater(q.px[3][2][1], q.px[6][5][1])


class Ombre(unittest.TestCase):

    def test_l_albero_getta_l_ombra_della_chioma(self):
        """L4: l'ombra portata ha la forma della chioma, non quella quadrata delle celle (giro 8)."""
        q = PC.Quadro(4, 4)
        for y in range(32):
            for x in range(32):
                q.px[y][x] = (PC.V, 2)
                q.tipo[y][x] = "suolo"
        for y in range(8, 24):
            for x in range(8, 24):
                q.tipo[y][x] = "verde"
                q.alto[y][x] = 20
        PC.dipingi_albero(q, 1, 1, 2, 2, "T", 0)
        # l'angolo in alto a sinistra delle celle dell'albero non e' chioma: non e' piu' alto
        self.assertEqual(q.alto[8][8], 0)
        self.assertEqual(q.tipo[8][8], "suolo")

    def test_negativa_l_ombra_non_scende_nel_nero(self):
        q = PC.Quadro(2, 2)
        for y in range(16):
            for x in range(16):
                q.px[y][x] = (PC.P, 1)
                q.tipo[y][x] = "suolo"
        q.alto[4][4] = 16
        q.tipo[4][4] = "basso"
        PC.ombre_portate(q)
        self.assertEqual(q.px[5][5], (PC.P, 0))
        self.assertNotEqual(q.px[5][5], PC.NERO)


class Prospettiva(unittest.TestCase):
    """M6: gli oggetti in 3/4 mostrano il piano di sopra (il coperchio, il cappello) piu' chiaro del fianco."""

    def test_paracarro_col_cappello(self):
        q = PC.Quadro(1, 1)
        PC.dipingi_paracarro(q, 0, 0, lambda x, y: (PC.V, 2))
        cappello = q.px[2][3]
        fusto = q.px[5][4]
        self.assertEqual(cappello[0], PC.P)
        self.assertGreater(cappello[1], fusto[1])

    def test_negativa_paracarro_senza_cappello(self):
        q = PC.Quadro(1, 1)
        PC.dipingi_paracarro(q, 0, 0, lambda x, y: (PC.V, 2))
        for x in range(8):
            q.px[2][x] = q.px[5][4]
        self.assertFalse(q.px[2][3][1] > q.px[5][4][1])


class Motivi(unittest.TestCase):

    def test_motivi_periodici(self):
        """I motivi si ripetono: e' cosi' che i tile tornano uguali e l'area sta nel budget."""
        for x, y in ((0, 0), (5, 9), (31, 31)):
            self.assertEqual(PC.colore_suolo("lastrico", x, y), PC.colore_suolo("lastrico", x + 32, y + 64))
            self.assertEqual(PC.colore_breccia(x, y), PC.colore_breccia(x + 32, y + 32))
            self.assertEqual(PC.colore_citta_bassa(x, y), PC.colore_citta_bassa(x + 48, y + 32))

    def test_nessun_buco_nei_motivi(self):
        for nome in ("lastrico", "suolo", "strada", "muro_chiaro", "muro", "muro_scuro", "muro_secco"):
            m = PC.motivo(nome)
            self.assertTrue(all(c is not None for r in m for c in r), nome)

    def test_citta_bassa_senza_toni_chiari(self):
        """C5: la citta' bassa e' lontana, niente tono 5 e niente nero."""
        m = PC._motivo_citta_bassa()
        self.assertTrue(all(c[1] < 5 and c != PC.NERO for r in m for c in r))


if __name__ == "__main__":
    unittest.main()


class ScalaDelleFacciate(unittest.TestCase):
    """M2: il giocatore e' alto 22-24 pixel (Ubaldo 16x32): porte e botteghe sulle vie alte almeno 26 pixel."""

    @staticmethod
    def _altezza_porta(fh, bottega=False):
        """L'altezza del vano della porta (o della bottega) che dipingi_casa disegna: il vano piu' alto della casa."""
        q = PC.Quadro(6, 8)
        casa = PC.Casa(0, 4, 6, fh, 3)
        casa.bottega, casa.morto = bottega, False
        vani = []
        originale = PC._vano_arco

        def conta(q_, x0, y0, w, h, *a, **k):
            vani.append(h)
            return originale(q_, x0, y0, w, h, *a, **k)
        PC._vano_arco = conta
        try:
            PC.dipingi_casa(q, casa, 6)
        finally:
            PC._vano_arco = originale
        return max(vani)

    def test_porte_e_botteghe_alte_almeno_26(self):
        self.assertEqual(PC.ALTEZZA_FACCIATA_MAX, 5)
        self.assertGreaterEqual(self._altezza_porta(5), 26)
        self.assertGreaterEqual(self._altezza_porta(5, bottega=True), 26)
        self.assertGreaterEqual(self._altezza_porta(4), 26)

    def test_negativa_facciata_di_tre_tile_non_basta(self):
        """Una facciata di 3 tile (24 pixel) non tiene una porta da 26: e' per questo che le vie ne vogliono 4-5."""
        self.assertLess(self._altezza_porta(3), 26)
