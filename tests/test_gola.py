"""La gola del Bottaccione (T2): le griglie delle quattro stanze (tools/disegna_gola.py), la striscia nera,
le celle d'innesco che sbarrano la via, la palette cupa senza colori nuovi, i tile della gola, i forzieri e i
soldati di B-03 (tools/genera_storia.py). Ogni prova ha la sua negativa."""
import copy
import os
import re
import sys
import unittest

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RADICE, "tools"))
import disegna_gola as D  # noqa: E402
import genera_mondo as G  # noqa: E402
import genera_storia as GS  # noqa: E402

with open(os.path.join(RADICE, "include", "storia.h"), encoding="utf-8") as _f:
    STORIA_H = _f.read()
with open(os.path.join(RADICE, "include", "mondo.h"), encoding="utf-8") as _f:
    MONDO_H = _f.read()
GRIGLIE = D.griglie()


def griglia_del_file(nome):
    with open(os.path.join(RADICE, "mondo", "aree", nome + ".area"), encoding="utf-8") as f:
        testo = f.read()
    return [list(r) for r in testo.partition("griglia\n")[2].split("\n") if r]


def striscia_sbagliata(g):
    """I difetti della striscia nera: righe diverse (non e' uno strato orizzontale), colonne di rupe dove manca
    (non e' continua), nessuna riga di rupe fra lei e la via sotto."""
    righe = {y for y in range(D.H) for x in range(D.W) if g[y][x] == "x"}
    if len(righe) != 1:
        return ["righe"]
    riga = righe.pop()
    difetti = []
    if any(g[riga][x] == "#" for x in range(D.W)):
        difetti.append("buchi")
    if any(g[riga + 1][x] in G.CALPESTABILI_GOLA for x in range(D.W)):
        difetti.append("sulla via")
    return difetti


class Griglie(unittest.TestCase):

    def test_i_file_sono_le_griglie_di_disegna_gola(self):
        for nome, g in GRIGLIE.items():
            self.assertEqual(griglia_del_file(nome), g, nome)

    def test_negativa_griglia_toccata_a_mano(self):
        g = griglia_del_file("gola_arco")
        g[15][20] = "#"
        self.assertNotEqual(g, GRIGLIE["gola_arco"])

    def test_inneschi_sbarrano_la_via(self):
        """Da A a B non si passa senza la cella che fa partire la scena (B-02 la nebbia, B-03 l'arco)."""
        for nome, c in D.SBARRANO.items():
            self.assertTrue(D.percorso_senza(GRIGLIE[nome], ""), nome)
            self.assertFalse(D.percorso_senza(GRIGLIE[nome], c), nome)
        self.assertEqual({GS.AREE[k].lower(): c for k, c in GS.INNESCHI.items()}, D.SBARRANO)

    def test_negativa_nebbia_aggirabile(self):
        """Un varco largo una cella sulla riga di mezzo attraverso tutte le chiazze, e la nebbia si aggira."""
        g = copy.deepcopy(GRIGLIE["gola_miasmi"])
        g[15] = ["," if c == "g" else c for c in g[15]]
        self.assertTrue(D.percorso_senza(g, "g"))

    def test_striscia_nera(self):
        self.assertEqual(striscia_sbagliata(GRIGLIE["gola_striscia"]), [])

    def test_negative_striscia(self):
        g = copy.deepcopy(GRIGLIE["gola_striscia"])
        riga = next(y for y in range(D.H) if "x" in g[y])
        g[riga][30] = "#"
        self.assertEqual(striscia_sbagliata(g), ["buchi"])
        g[riga][30] = "x"
        g[riga + 1][31] = ","
        self.assertEqual(striscia_sbagliata(g), ["sulla via"])
        g[riga - 1][5] = "x"
        self.assertEqual(striscia_sbagliata(g), ["righe"])

    def test_ponticello_corto(self):
        """Il torrente taglia la via dei miasmi ripido: il ponticello e' largo poche colonne, non una passerella
        di traverso lunga mezza stanza come nel primo giro."""
        g = GRIGLIE["gola_miasmi"]
        colonne = {x for y in range(D.H) for x in range(D.W) if g[y][x] == "+"}
        self.assertTrue(colonne)
        self.assertLessEqual(max(colonne) - min(colonne) + 1, 6)

    def test_negativa_ponticello_lungo(self):
        g = D.stanza("prova", 1.3, 2.0, lambda x: 26 - x * 0.3 if 0 < x < 60 else None)
        colonne = {x for y in range(D.H) for x in range(D.W) if g[y][x] == "+"}
        self.assertGreater(max(colonne) - min(colonne) + 1, 6)


class Palette(unittest.TestCase):

    def test_solo_colori_della_palette_bloccata(self):
        palette = G.S.carica("palette")
        rampe = {r["nome"]: r for r in palette["rampe"]}
        cupa = G.palette_cupa(palette)
        self.assertEqual(len(cupa), 16)
        for nome, tono in cupa:
            self.assertIn(nome, rampe)
            self.assertLess(tono, len(rampe[nome]["notte"]))
        valori = {G.S.colore(palette, r, True) for r in cupa}
        bloccati = {c for r in palette["rampe"] for c in r["notte"]}
        self.assertLessEqual(valori, bloccati)
        self.assertIn("inline constexpr uint16_t PALETTE_FONDALI_CUPA[16]", MONDO_H)

    def test_nessun_doppione(self):
        """Dentro la gola ogni voce oltre il contorno ha un colore suo (la scaglia bianca ha due toni)."""
        cupa = G.palette_cupa(G.S.carica("palette"))
        self.assertEqual(len(set(cupa[2:])), 14)

    def test_negativa_il_primo_giro_aveva_doppioni(self):
        """La palette cupa del primo giro (un tono piu' chiara, fermata all'ultimo tono) metteva la pietra chiara e
        la chiarissima sullo stesso colore."""
        palette = G.S.carica("palette")
        toni = {r["nome"]: len(r["notte"]) for r in palette["rampe"]}
        vecchia = [r if i < 2 else (r[0], min(r[1] + 1, toni[r[0]] - 1)) for i, r in enumerate(G.PALETTE_FONDALI)]
        self.assertLess(len(set(vecchia[2:])), 14)


class Tile(unittest.TestCase):

    def test_i_tile_della_gola_esistono(self):
        nomi = set(G.INDICE_TILE)
        for nome, g in GRIGLIE.items():
            for y in range(D.H):
                for x in range(D.W):
                    t = G.tile_della_gola(g, x, y, g[y][x])
                    self.assertTrue(t is None or t in nomi, (nome, x, y, t))

    def test_ogni_stanza_ha_i_suoi_tratti(self):
        usati = {nome: {G.tile_della_gola(g, x, y, g[y][x]) for y in range(D.H) for x in range(D.W)}
                 for nome, g in GRIGLIE.items()}
        self.assertIn("STRISCIA_NERA", usati["gola_striscia"])
        self.assertIn("i", {c for r in GRIGLIE["gola_striscia"] for c in r})       # la lapide (tile LAPIDE, di sempre)
        self.assertTrue({"PONTE", "PONTE_SPONDA", "PONTE_SPONDA_GIU"} & usati["gola_miasmi"])
        self.assertTrue({"ARCO_GOLA_S", "ARCO_GOLA_D", "CONTRAFFORTE"} <= usati["gola_arco"])
        self.assertTrue({"ACQUEDOTTO_CORNICE", "ACQUEDOTTO_PILASTRO", "ACQUEDOTTO_ARCO_10", "CANALETTA",
                         "DIGA_LUCE", "DIGA_OMBRA"} <= usati["condotto"])
        for nome in GRIGLIE:
            self.assertTrue({"RUPE", "RUPE_BIANCA"} <= usati[nome], nome)

    def test_negativa_fuori_dalla_gola_niente_tile_della_gola(self):
        """Il muro di un'area della citta' resta tetto o fronte: tile_della_gola vale solo per le quattro stanze."""
        g = [list("#####"), list("#,,,#"), list("#####")]
        self.assertNotEqual(G.tile_per_cella(g, 0, 0, False), G.INDICE_TILE["RUPE"])
        self.assertIn(G.tile_per_cella(g, 0, 0, "gola"), (G.INDICE_TILE["RUPE"], G.INDICE_TILE["RUPE_BIANCA"],
                                                          G.INDICE_TILE["EDERA"], G.INDICE_TILE["RUPE_FRATTURA"]))

    def test_sopra_la_striscia_rossa_sotto_bianca(self):
        g = GRIGLIE["gola_striscia"]
        riga = next(y for y in range(D.H) if "x" in g[y])
        sopra = [G.tile_della_gola(g, x, y, "#") for y in range(riga) for x in range(D.W) if g[y][x] == "#"]
        sotto = [G.tile_della_gola(g, x, y, "#") for y in range(riga + 1, D.H) for x in range(D.W) if g[y][x] == "#"]
        self.assertGreater(sopra.count("RUPE"), 3 * sopra.count("RUPE_BIANCA"))
        self.assertGreater(sotto.count("RUPE_BIANCA"), sotto.count("RUPE"))


def tabella(nome, struttura):
    blocco = re.search(r"inline constexpr %s %s\[[A-Z_]+\] = \{(.*?)\n\};" % (struttura, nome), STORIA_H, re.S).group(1)
    return [re.findall(r"[\w:()]+", r) for r in blocco.strip().split("\n")]


class Forzieri(unittest.TestCase):

    def righe(self):
        out = []
        for r in tabella("FORZIERE", "Forziere"):
            area = re.search(r"AreaId::(\w+)", " ".join(r)).group(1)
            numeri = [t for t in r if t.isdigit()]
            out.append((area, int(numeri[0]), int(numeri[1]), r[r.index(numeri[1]) + 1]))
        return out

    def test_negli_slarghi_e_raggiungibili(self):
        aree = GS.aree_del_mondo()
        for area, x, y, bandiera in self.righe():
            self.assertIn((x, y), D.SLARGHI.values())
            a = aree[area]
            self.assertIn((x, y), GS.raggiungibili_da(a, *a["spawn"][0], G))

    def test_negativa_forziere_nella_rupe(self):
        a = GS.aree_del_mondo()["GOLA_ARCO"]
        self.assertNotIn((20, 5), GS.raggiungibili_da(a, *a["spawn"][0], G))

    def test_bandiere_libere_nell_intervallo_quest(self):
        """88 e 89: dopo le bandiere di SV2c (77-87), dentro 64-127; il salvataggio resta v3."""
        indici = {b: GS.PRIMA_QUEST + i for i, b in enumerate(GS.BANDIERE_QUEST)}
        self.assertEqual((indici["FORZIERE_CRESCIA"], indici["FORZIERE_BISCOTTI"]), (88, 89))
        self.assertEqual(len(set(indici.values())), len(indici))
        self.assertLess(max(indici.values()), 128)
        self.assertIn("inline constexpr uint8_t FORZIERE_CRESCIA = 88;", STORIA_H)
        with open(os.path.join(RADICE, "include", "save_data.h"), encoding="utf-8") as f:
            self.assertIn("VERSIONE = 3;", f.read())

    def test_negativa_bandiera_sopra_sv2c(self):
        indici = [GS.PRIMA_QUEST + i for i, b in enumerate(GS.BANDIERE_QUEST)]
        self.assertNotIn(87, indici[-2:])

    def test_negativa_slargo_irraggiungibile_rifiutato(self):
        vecchio = dict(D.SLARGHI)
        try:
            D.SLARGHI["gola_arco"] = (20, 5)
            with self.assertRaises(GS.ErroreStoria):
                GS.posti_dei_forzieri(posti_raccolte())
        finally:
            D.SLARGHI.clear()
            D.SLARGHI.update(vecchio)


def posti_raccolte():
    _, npc = GS.leggi_copione()
    return GS.posti_della_quest(npc, GS.leggi_le_quest())[2]


class Sentinelle(unittest.TestCase):

    def test_due_soldati_oltre_l_arco_con_la_figura_del_soldato(self):
        righe = tabella("SENTINELLA", "Sentinella")
        self.assertEqual(len(righe), 2)
        g = GRIGLIE["gola_arco"]
        arco = max(x for y in range(D.H) for x in range(D.W) if g[y][x] == "J")
        for r in righe:
            numeri = [int(t) for t in r if t.isdigit()]
            x, y = numeri[0], numeri[1]
            self.assertGreater(x, arco)
            self.assertIn(g[y][x], ",")
        figura = int([t for t in righe[0] if t.isdigit()][-1])
        figure = re.search(r"FIGURA_NPC\[FIGURE_NPC\]\[POSE_NPC \* 8 \* 8\] = \{(.*?)\n\};", STORIA_H, re.S).group(1)
        attesa = [v for px in GS.FP.fotogrammi_npc("soldato") for v in GS.FP.parole(px)]
        blocchi = re.findall(r"\{\s*((?:0x[0-9A-F]{8},\s*)+)\s*\}", figure)
        self.assertEqual([int(v, 16) for v in re.findall(r"0x[0-9A-F]{8}", blocchi[figura])], attesa)

    def test_negativa_soldato_addosso_alla_radice(self):
        """Tre colonne prima della fine dell'arco un soldato starebbe sulla radice di elleboro di B-03: rifiutato."""
        vecchio = GS.SENTINELLE["passi"]
        try:
            GS.SENTINELLE["passi"] = -3
            with self.assertRaises(GS.ErroreStoria):
                GS.posti_delle_sentinelle(posti_raccolte())
        finally:
            GS.SENTINELLE["passi"] = vecchio


if __name__ == "__main__":
    unittest.main()
