"""Il motore di regia delle cutscene (F7, pezzo U): tools/genera_regia.py e i copioni regia/*.regia.

Le regole della proposta approvata, ognuna con la negativa: nessuna cutscene oltre i 60 s, nelle
bande parla solo il NARRATORE in al massimo 2 righe da 224 px (il contesto NARRATORE di testi.h,
misurato da tools/genera_testi.py), Start salta tutto e A avanza (provati a tempo di compilazione
in src/autotest_regia.cpp, qui si controlla che ci siano), i piani con la palette bloccata.
"""
import importlib.util
import os
import unittest

from _stile import RADICE, S

_spec = importlib.util.spec_from_file_location("genera_regia", os.path.join(RADICE, "tools", "genera_regia.py"))
GR = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(GR)

_spec_t = importlib.util.spec_from_file_location("genera_testi", os.path.join(RADICE, "tools", "genera_testi.py"))
GT = importlib.util.module_from_spec(_spec_t)
_spec_t.loader.exec_module(GT)

PALETTE = S.carica("palette")
PROVA = "cutscene CX | prova\ninquadratura {secondi} | cielo_prova monti | 12\nnarratore {battuta}\n"


class Regia(unittest.TestCase):

    def test_header_aggiornato(self):
        with open(GR.USCITA, encoding="utf-8") as f:
            self.assertEqual(f.read(), GR.genera(GR.sorgenti_del_repo(), PALETTE), "python tools/genera_regia.py --scrivi")

    def test_negativa_header_vecchio(self):
        altri = GR.sorgenti_del_repo() + [("prova.regia", PROVA.format(secondi=3, battuta="R_P_01_00"))]
        with open(GR.USCITA, encoding="utf-8") as f:
            self.assertNotEqual(f.read(), GR.genera(altri, PALETTE))

    def test_ogni_cutscene_entro_il_minuto(self):
        for nome, testo in GR.sorgenti_del_repo():
            c = GR.leggi(nome, testo)
            self.assertLessEqual(sum(i["frame"] for i in c["inquadrature"]), 60 * 60, nome)

    def test_negativa_cutscene_di_61_secondi(self):
        with self.assertRaisesRegex(GR.ErroreRegia, "dura 61 s, il massimo e' 60"):
            GR.genera([("lunga.regia", PROVA.format(secondi=61, battuta="R_P_01_00"))], PALETTE)

    def test_nelle_bande_solo_il_narratore_in_due_righe(self):
        self.assertEqual(GT.CONTESTI["NARRATORE"], (224, 2))
        contesti = GR.contesti_dei_testi()
        for nome, testo in GR.sorgenti_del_repo():
            for i in GR.leggi(nome, testo)["inquadrature"]:
                for b in i["battute"]:
                    self.assertEqual(contesti[b], "NARRATORE", (nome, b))

    def test_negativa_battuta_di_dialogo_nelle_bande(self):
        with self.assertRaisesRegex(GR.ErroreRegia, "non e' una battuta del NARRATORE"):
            GR.genera([("dialogo.regia", PROVA.format(secondi=3, battuta="C_A1_01_01"))], PALETTE)

    def test_negativa_tre_righe_rifiutate(self):
        """Una frase del narratore che non sta in 2 righe da 224 px il generatore dei testi la rifiuta."""
        lunga = "Undici citta' confederate cinsero d'assedio la roccaforte di Gubbio, " * 3
        with self.assertRaisesRegex(GT.ErroreTesti, "il contesto NARRATORE ne ammette 2"):
            GT.genera([("prova.testi", f"X | NARRATORE | {lunga.replace(chr(39), '')}".encode("utf-8"))],
                      S.carica("font"))

    def test_quattro_piani_al_massimo(self):
        with self.assertRaisesRegex(GR.ErroreRegia, "da 1 a 4 piani"):
            GR.leggi("cinque.regia", "cutscene C9 | x\ninquadratura 2 | cielo monti citta prato cielo | 12\n")

    def test_piani_con_la_palette_bloccata(self):
        giorno = {c for r in PALETTE["rampe"] for c in r["giorno"]}
        notte = {c for r in PALETTE["rampe"] for c in r["notte"]}
        for nome, pittore in GR.PIANI.items():
            for momento in GR.PP.MOMENTI:
                tela, palette, di_notte = pittore(momento)
                self.assertEqual(len(palette), 16, nome)
                colori = {GR.colore_del_piano(PALETTE, r, di_notte) for r in palette if GR.PP.ACCESO not in r[2:]}
                accesi = {GR.colore_del_piano(PALETTE, r, di_notte) for r in palette if GR.PP.ACCESO in r[2:]}
                self.assertTrue(colori <= (notte if di_notte else giorno), (nome, momento))
                self.assertTrue(accesi <= giorno, (nome, momento))
                self.assertTrue({c for riga in tela.px for c in riga} <= set(range(16)), nome)

    def test_accesi_solo_l_alone_e_l_oro(self):
        """Le luci che di notte restano col tono del giorno sono solo l'alone e l'oro dei panorami."""
        accesi = {(nome, i) for nome, pittore in GR.PIANI.items()
                  for i, r in enumerate(pittore("notte")[1]) if GR.PP.ACCESO in r[2:]}
        self.assertEqual({i for _, i in accesi}, {GR.PP.ALONE, GR.PP.ORO})
        self.assertTrue({n for n, _ in accesi} <= {"monte", "gubbio", "campo", "gubbio_fede"})

    def test_negativa_un_colore_non_acceso_si_trasforma(self):
        oro = ("oro e bronzo", 3)
        self.assertNotEqual(GR.colore_del_piano(PALETTE, oro, True), GR.colore_del_piano(PALETTE, oro + (GR.PP.ACCESO,), True))
        self.assertEqual(GR.colore_del_piano(PALETTE, oro + (GR.PP.ACCESO,), True), S.colore(PALETTE, oro))


class Panorami(unittest.TestCase):
    """Pezzo V: Gubbio vista dalla valle (tools/pittore_panorami.py), dal censimento."""

    def test_monumenti_dal_censimento(self):
        m = {nome: (x, base, alto) for nome, x, base, alto, _ in GR.PP.monumenti_dalla_valle()}
        for nome in ("consoli", "duomo", "san_francesco", "san_pietro", "sant_agostino", "san_domenico"):
            self.assertIn(nome, m)
        # vista da sud-ovest: San Domenico (a nord-ovest) a sinistra di Sant'Agostino (a sud-est)
        self.assertLess(m["san_domenico"][0], m["sant_agostino"][0])
        # la torre dei Consoli (60 m) e' il monumento piu' alto
        self.assertEqual(max(m, key=lambda k: m[k][2]), "consoli")
        # il Duomo (109 m) sta piu' in alto sul pendio di San Francesco (0 m)
        self.assertLess(m["duomo"][1], m["san_francesco"][1])

    def test_negativa_monumento_inventato(self):
        self.assertNotIn("torre_inventata", {n for n, _, _, _, _ in GR.PP.monumenti_dalla_valle()})

    def test_la_notte_e_la_trasformata(self):
        for nome in ("cielo", "monte", "gubbio", "campo"):
            _, palette, notte = GR.PIANI[nome]("notte")
            _, palette_g, giorno_notte = GR.PIANI[nome]("giorno")
            self.assertTrue(notte)
            self.assertFalse(giorno_notte)
            self.assertNotEqual([GR.colore_del_piano(PALETTE, r, True) for r in palette],
                                [GR.colore_del_piano(PALETTE, r, False) for r in palette_g])

    def fuochi_luminosi(self, momento, margine=0.25, pittore=None, minimo=1, x0=0, x1=None):
        """I fuochi (macchie del colore ORO di almeno 'minimo' pixel che cominciano fra x0 e x1) che si
        leggono: la loro luminanza supera di 'margine' la media dello sfondo del piano."""
        tela, palette, notte = (pittore or GR.PP.campo)(momento)

        def luminanza(rif):
            v = GR.colore_del_piano(PALETTE, rif, notte)
            return (0.299 * (v & 31) + 0.587 * ((v >> 5) & 31) + 0.114 * ((v >> 10) & 31)) / 31

        sfondo = [luminanza(palette[c]) for riga in tela.px[:112] for c in riga if c and c != GR.PP.ORO]
        if luminanza(palette[GR.PP.ORO]) < sum(sfondo) / len(sfondo) + margine:
            return 0
        x1 = len(tela.px[0]) if x1 is None else x1
        visti, macchie = set(), 0
        for y, riga in enumerate(tela.px):
            for x, c in enumerate(riga):
                if c == GR.PP.ORO and (x, y) not in visti:
                    prima = len(visti)
                    coda = [(x, y)]
                    while coda:
                        u, v = coda.pop()
                        if (u, v) in visti or not (0 <= v < len(tela.px) and 0 <= u < len(riga)) or tela.px[v][u] != GR.PP.ORO:
                            continue
                        visti.add((u, v))
                        coda += [(u + 1, v), (u - 1, v), (u, v + 1), (u, v - 1)]
                    macchie += len(visti) - prima >= minimo and x0 <= x < x1
        return macchie

    def test_i_fuochi_del_campo_di_notte(self):
        """Di notte almeno 6 fuochi che sono il punto di luce della scena."""
        self.assertGreaterEqual(self.fuochi_luminosi("notte"), 6)

    def test_negativa_fuochi_di_giorno_o_spenti(self):
        self.assertEqual(self.fuochi_luminosi("giorno"), 0)
        self.assertEqual(self.fuochi_luminosi("notte", margine=1.0), 0)

    def test_i_fuochi_del_campo_sono_3x3(self):
        self.assertGreaterEqual(self.fuochi_luminosi("notte", minimo=9), 6)

    def inquadratura_della_fede(self):
        c1 = next(GR.leggi(n, t) for n, t in GR.sorgenti_del_repo() if "c1_" in n)
        return next(i for i in c1["inquadrature"] if "R_P_02_06" in i["battute"])

    def test_il_fuoco_della_fede_si_vede(self):
        """Nell'inquadratura di 'Sorse il fuoco della Fede' c'e' un punto caldo grande (almeno 16 px
        d'oro sopra la media dello sfondo) dentro il quadro ai tre quarti della carrellata."""
        q = self.inquadratura_della_fede()
        self.assertIn("gubbio_fede", q["piani"])
        corsa = q["velocita"] * q["frame"] * 3 // (4 * 60)
        self.assertGreaterEqual(self.fuochi_luminosi("notte", pittore=GR.PP.gubbio_fede, minimo=16,
                                                     x0=corsa, x1=corsa + 240), 1)

    def test_negativa_nessun_punto_caldo_nella_citta_di_notte(self):
        self.assertEqual(self.fuochi_luminosi("notte", pittore=GR.PP.gubbio, minimo=16), 0)

    def test_c1_e_c4_dal_copione(self):
        """C1 recita in ordine le battute del narratore di P-01 e P-02; C4 quelle di E-02. Nessuna supera
        i 60 s."""
        cutscene = {GR.leggi(n, t)["codice"]: GR.leggi(n, t) for n, t in GR.sorgenti_del_repo()}
        def battute(c):
            return [b for i in cutscene[c]["inquadrature"] for b in i["battute"]]
        self.assertEqual(battute("C1"), [f"R_P_01_{k:02d}" for k in range(3)] + [f"R_P_02_{k:02d}" for k in range(7)])
        self.assertEqual(battute("C4"), [f"R_E_02_{k:02d}" for k in range(3)])
        for c in ("C1", "C4"):
            self.assertLessEqual(sum(i["frame"] for i in cutscene[c]["inquadrature"]), 3600, c)
        piani = {p for i in cutscene["C1"]["inquadrature"] for p in i["piani"]}
        self.assertTrue({"vetrata_storia", "vetrata", "pergamena", "gubbio:notte", "campo:notte", "gubbio_fede"} <= piani)
        # la prima inquadratura e' la vetrata a colori; quella di "prima che il vetro avesse un colore"
        # dissolve i colori sui vetri chiari
        prime = cutscene["C1"]["inquadrature"]
        self.assertEqual(prime[0]["piani"], ["vetrata_storia"])
        terza = next(i for i in prime if "R_P_01_02" in i["battute"])
        self.assertTrue(terza["dissolvi"])
        self.assertEqual(terza["piani"], ["vetrata", "vetrata_storia"])
        # in C4 la citta' all'alba c'e' gia' nella prima inquadratura, con la prima battuta
        self.assertIn("gubbio:alba", cutscene["C4"]["inquadrature"][0]["piani"])
        self.assertEqual(cutscene["C4"]["inquadrature"][0]["battute"], ["R_E_02_00"])

    def test_negativa_dissolvi_con_un_solo_piano(self):
        with self.assertRaisesRegex(GR.ErroreRegia, "servono 2 piani"):
            GR.leggi("uno.regia", "cutscene C9 | x\ninquadratura 2 | vetrata | 0 | dissolvi\n")
        with self.assertRaisesRegex(GR.ErroreRegia, "dissolvi"):
            GR.leggi("strano.regia", "cutscene C9 | x\ninquadratura 2 | vetrata vetrata_storia | 0 | sfuma\n")

    def test_negativa_c1_senza_una_battuta(self):
        n, t = next((n, t) for n, t in GR.sorgenti_del_repo() if "c1_" in n)
        corto = GR.leggi(n, t.replace("narratore R_P_02_04\n", ""))
        self.assertNotIn("R_P_02_04", [b for i in corto["inquadrature"] for b in i["battute"]])

    def vetri(self, pittore, momento="giorno"):
        tela = pittore(momento)[0]
        return [tela.px[y][x] for y in range(112) for x in range(240) if GR.PP.nel_vetro(x, y)]

    def test_vetrata_colorata_e_chiara(self):
        """La vetrata come la si vede oggi ha almeno 8 colori di vetro; quella del prologo solo i toni
        chiari (e il piombo)."""
        colorata = set(self.vetri(GR.PP.vetrata_storia)) - {GR.PP.V_BUIO}
        chiara = set(self.vetri(GR.PP.vetrata)) - {GR.PP.V_BUIO}
        self.assertGreaterEqual(len(colorata), 8)
        self.assertTrue(chiara <= GR.PP.VETRI_CHIARI)

    def test_negativa_la_vetrata_chiara_non_ha_colori(self):
        self.assertLess(len(set(self.vetri(GR.PP.vetrata)) - {GR.PP.V_BUIO}), 8)
        self.assertFalse(set(self.vetri(GR.PP.vetrata_storia)) <= GR.PP.VETRI_CHIARI | {GR.PP.V_BUIO})

    def test_vetrata_ogivale_e_centrata(self):
        """La bifora sta al centro del quadro (240 px): la cornice e' simmetrica e l'arco e' acuto (la
        riga in cima e' stretta, quella dell'imposta e' larga quanto la finestra)."""
        cornice = [(x, y) for y in range(112) for x in range(240) if GR.PP.nella_finestra(x, y, 4)]
        xs = [x for x, _ in cornice]
        self.assertAlmostEqual((min(xs) + max(xs) + 1) / 2, 120, delta=1)
        cima = min(y for _, y in cornice)
        self.assertLessEqual(sum(1 for _, y in cornice if y == cima), 6)
        self.assertGreaterEqual(sum(1 for _, y in cornice if y == 80), 80)

    def test_vetrata_con_un_solo_vetro_colorato_all_epilogo(self):
        """All'alba la stessa vetrata ogivale: cambia solo il vetro del Bottaccione."""
        chiara, alba = GR.PP.vetrata("giorno")[0], GR.PP.vetrata("alba")[0]
        diversi = [(x, y) for y in range(112) for x in range(240) if chiara.px[y][x] != alba.px[y][x]]
        self.assertGreater(len(diversi), 300)
        self.assertTrue(all(122 <= x < 158 and 70 <= y < 100 for x, y in diversi))
        colori = {GR.PP.V_ROSSO, GR.PP.V_VERDE, GR.PP.V_LEGNO, GR.PP.V_BLU}
        self.assertEqual(sum(1 for r in chiara.px for c in r if c in colori), 0)

    def test_i_panorami_nel_budget(self):
        dipinti = GR.dipingi_piani(["cielo:notte", "monte:notte", "gubbio:notte", "campo:notte"])
        tile = sum(len(v[0]) for v in dipinti.values())
        self.assertLessEqual(max(len(v[0]) for v in dipinti.values()), GR.TILE_MAX_PER_PIANO)
        self.assertLess(tile * 32 + 4 * 2048 * 2, 64 * 1024, "tile e mappe di un'inquadratura nella VRAM dei BG")

    def test_prove_del_lettore_in_cpp(self):
        autotest = open(os.path.join(RADICE, "src", "autotest_regia.cpp"), encoding="utf-8").read()
        for prova in ("durate_entro_il_minuto()", "dura(0, 0, 0) == 1", "dura(0, 30, -1) < CUTSCENE_DATI[0].frame",
                      "luce_e_stacchi()", "parallasse()", "viste()"):
            self.assertIn("static_assert(" + prova, autotest)


if __name__ == "__main__":
    unittest.main(verbosity=2)
