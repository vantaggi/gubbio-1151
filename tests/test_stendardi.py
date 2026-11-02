"""Gli stendardi e la pergamena del prologo (pezzo W2): tools/stendardi.py, dati/simboli/coalizione.json,
dati/mappa_umbria.json e la pergamena di tools/pittore_panorami.py.

Gli stendardi vengono dai dati (la versione "gioco" decisa per ogni citta'), ognuno diverso dagli altri;
quello di Gubbio e' rosso col monte d'argento a cinque cime, senza lambello. Sulla mappa le citta' stanno
dove dicono le coordinate vere, con una scala sola, e i drappi non si toccano.
"""
import importlib.util
import os
import sys
import unittest

from _stile import RADICE

sys.path.insert(0, os.path.join(RADICE, "tools"))
_spec = importlib.util.spec_from_file_location("pittore_panorami", os.path.join(RADICE, "tools", "pittore_panorami.py"))
PP = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(PP)
ST = PP.ST


def disegna(gioco, w=10, h=10):
    t = PP.Tela(w + 2, h + 2)
    indici = {c: i + 1 for i, c in enumerate(ST.COLORI)}
    ST.drappo(t, 1, 1, gioco, indici, w, h)
    inverso = {i: c for c, i in indici.items()}
    return tuple(tuple(r) for r in t.px), {inverso[c] for r in t.px for c in r if c}


def ordine_rispettato(posizioni, coordinate, soglia=0.02):
    """Per ogni coppia di citta' piu' distanti della soglia (in gradi): chi e' piu' a nord sta piu' in
    alto, chi e' piu' a est sta piu' a destra."""
    nomi = list(coordinate)
    for a in nomi:
        for b in nomi:
            (la, lo), (lb, lob) = coordinate[a], coordinate[b]
            (xa, ya), (xb, yb) = posizioni[a], posizioni[b]
            if la - lb > soglia and not ya < yb:
                return False
            if lo - lob > soglia and not xa > xb:
                return False
    return True


class Stendardi(unittest.TestCase):

    def test_undici_citta_e_gubbio_tutti_diversi(self):
        self.assertEqual(len(ST.COALIZIONE), 11)
        disegni = [disegna(c["gioco"])[0] for c in ST.tutte()]
        self.assertEqual(len(set(disegni)), 12)

    def test_negativa_due_stendardi_uguali_si_vedono(self):
        doppio = [disegna(ST.per_id("perugia")["gioco"])[0], disegna(dict(ST.per_id("perugia")["gioco"]))[0]]
        self.assertEqual(len(set(doppio)), 1)

    def test_i_colori_sono_quelli_dei_dati(self):
        for c in ST.tutte():
            _, usati = disegna(c["gioco"])
            self.assertEqual(usati, ST.colori(c["gioco"]) | {ST.CONTORNO}, c["id"])

    def test_negativa_un_colore_cambiato_si_vede(self):
        gioco = dict(ST.per_id("assisi")["gioco"], campo=["cielo e acqua", 1])
        self.assertNotEqual(disegna(gioco)[1], ST.colori(ST.per_id("assisi")["gioco"]) | {ST.CONTORNO})

    def test_gubbio_rosso_col_monte_a_cinque_cime_senza_lambello(self):
        g = ST.GUBBIO["gioco"]
        self.assertEqual(g["campo"][0], "vermiglio comunale")
        self.assertEqual(g["figura_colore"], ["neutri", 4])
        self.assertEqual(ST.colori(g), {("vermiglio comunale", 2), ("neutri", 4)})   # niente azzurro, niente oro
        monte = ST.FIGURE["monte"]
        altezze = [sum(1 for riga in monte if riga[x] == "#") for x in range(len(monte[0]))]
        cime = [x for x in range(len(altezze)) if altezze[x] > max(altezze[x - 1] if x else 0,
                                                                  altezze[x + 1] if x + 1 < len(altezze) else 0)]
        self.assertEqual(len(cime), 5)
        self.assertEqual(max(altezze), altezze[len(altezze) // 2])                # la centrale e' la piu' alta
        self.assertIn("lambello", ST.SIMBOLI["stemma_comune"]["nel_gioco"])

    def test_negativa_un_monte_a_tre_cime_non_passa(self):
        tre = ["...#...", ".#.#.#.", "#######"]
        altezze = [sum(1 for riga in tre if riga[x] == "#") for x in range(7)]
        cime = [x for x in range(7) if altezze[x] > max(altezze[x - 1] if x else 0, altezze[x + 1] if x < 6 else 0)]
        self.assertNotEqual(len(cime), 5)

    def test_il_drappo_di_gubbio_sui_consoli_almeno_8x8(self):
        tela = PP.gubbio("giorno")[0]
        x = next(mx for n, mx, _, _, _ in PP.monumenti_dalla_valle() if n == "consoli")
        rossi = [(u, v) for v in range(PP.QUADRO) for u in range(x - 12, x + 20) if tela.px[v][u] == PP.VERMIGLIO]
        xs, ys = [u for u, _ in rossi], [v for _, v in rossi]
        self.assertGreaterEqual(max(xs) - min(xs) + 1, 8)
        self.assertGreaterEqual(max(ys) - min(ys) + 1, 8)


class Mappa(unittest.TestCase):

    def setUp(self):
        self.coord = PP.MAPPA["citta"]
        self.pos = {c: PP.proietta(*ll) for c, ll in self.coord.items()}

    def test_le_citta_nell_ordine_delle_coordinate_vere(self):
        self.assertTrue(ordine_rispettato(self.pos, self.coord))

    def test_negativa_perugia_e_spoleto_scambiate(self):
        sbagliate = dict(self.pos, perugia=self.pos["spoleto"], spoleto=self.pos["perugia"])
        self.assertFalse(ordine_rispettato(sbagliate, self.coord))

    def test_una_scala_sola(self):
        """Un km vale gli stessi pixel in orizzontale e in verticale."""
        (x0, y0), (x1, y1) = PP.proietta(43.0, 12.5), PP.proietta(43.1, 12.6)
        self.assertAlmostEqual(abs(x1 - x0) / (0.1 * PP.KM_PER_GRADO_LON), abs(y1 - y0) / (0.1 * PP.KM_PER_GRADO_LAT))

    def test_solo_cagli_a_nord_di_gubbio_e_tutte_nel_quadro(self):
        gy = self.pos["gubbio"][1]
        self.assertEqual([c for c, (_, y) in self.pos.items() if y < gy], ["cagli"])
        for c, (x, y) in self.pos.items():
            self.assertTrue(0 <= x < 240 and 2 <= y < PP.QUADRO - 2, c)

    def test_appennino_a_est_e_ingino_dietro_gubbio(self):
        for c in ("gualdo", "fossato", "nocera"):
            lat, lon = self.coord[c]
            crinale = min(PP.MAPPA["appennino"], key=lambda p: abs(p[0] - lat))
            self.assertGreater(crinale[1], lon, c)
        ingino, gubbio = PP.MAPPA["luoghi"]["monte_ingino"], self.coord["gubbio"]
        self.assertGreater(ingino[0], gubbio[0])                              # a nord, sopra la citta'
        self.assertLess(abs(ingino[1] - gubbio[1]), 0.05)

    def test_i_drappi_non_si_toccano(self):
        posti = PP.posti_delle_bandiere()
        self.assertEqual(set(posti), {c["id"] for c in ST.COALIZIONE})
        scatole = [(fx - 1, fy - 1, fx + PP.BANDIERA + 1, fy + PP.BANDIERA + 1) for fx, fy, _, _ in posti.values()]
        for i, a in enumerate(scatole):
            self.assertTrue(2 <= a[1] and a[3] <= PP.QUADRO - 2, a)
            for b in scatole[i + 1:]:
                self.assertFalse(a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3], (a, b))

    def test_negativa_senza_spostarli_i_drappi_si_toccherebbero(self):
        ys = sorted(PP.proietta(*self.coord[c])[1] for c in ("gualdo", "fossato", "nocera", "spello", "foligno"))
        self.assertTrue(any(b - a < PP.BANDIERA + 2 for a, b in zip(ys, ys[1:])))

    def test_i_nomi_quando_il_narratore_li_dice(self):
        uno = PP.nominate(["R_P_02_01"])
        self.assertEqual(set(uno), {"spoleto", "foligno", "assisi", "spello", "bettona", "todi", "cagli"})
        due = PP.nominate(["R_P_02_01", "R_P_02_02"])
        self.assertEqual(set(due), {c["id"] for c in ST.COALIZIONE})
        self.assertEqual(due["fossato"], "Fossato")
        self.assertEqual(due["gualdo"], "Gualdo Tadino")
        self.assertEqual(PP.nominate([]), {})
        senza, con = PP.pergamena("giorno")[0], PP.pergamena_nomi1("giorno")[0]
        self.assertNotEqual(senza.px, con.px)

    def test_negativa_una_citta_non_detta_resta_senza_nome(self):
        self.assertNotIn("perugia", PP.nominate(["R_P_02_01"]))

    def test_la_mappa_usa_i_colori_degli_stendardi(self):
        self.assertTrue(set(ST.COLORI) <= set(PP.INDICI_PERGAMENA))


if __name__ == "__main__":
    unittest.main(verbosity=2)
