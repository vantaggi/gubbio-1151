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
import _sagome_x2 as V

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

    def accesi(self):
        return {(nome, i) for nome, pittore in GR.PIANI.items()
                for i, r in enumerate(pittore("notte")[1]) if GR.PP.ACCESO in r[2:]}

    def test_accesi_solo_l_alone_e_l_oro(self):
        """Le luci che di notte restano col tono del giorno: nei panorami solo l'alone e l'oro; le altre solo
        nelle scene di notte di C5 e C6 (LUCI_ACCESE: le candele, i Ceri, il ferro, la maiolica)."""
        panorami = {(n, i) for n, i in self.accesi() if n not in GR.PP.LUCI_ACCESE}
        self.assertEqual({i for _, i in panorami}, {GR.PP.ALONE, GR.PP.ORO})
        self.assertTrue({n for n, _ in panorami} <= {"monte", "gubbio", "campo", "gubbio_fede"})
        self.assertTrue(GR.PP.LUCI_ACCESE <= set(GR.PP.C5.PITTORI) | set(GR.PP.C6.PITTORI))
        for nome in GR.PP.LUCI_ACCESE:
            self.assertTrue(GR.PIANI[nome]("notte")[2], nome)                  # sono scene di notte

    def test_negativa_luci_accese_fuori_dalle_scene_di_notte(self):
        """Un piano di C7 (di giorno) o la bifora del prologo non sono fra le scene con le luci accese."""
        self.assertNotIn("c7_monte", GR.PP.LUCI_ACCESE)
        self.assertNotIn("c6_vetro_scuro", GR.PP.LUCI_ACCESE)
        self.assertFalse(any(n.startswith("c7_") for n, _ in self.accesi()))

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
                      "luce_e_stacchi()", "parallasse()", "viste()", "colpo(int(CutsceneId::C2P))", "! colpo(0)",
                      "passo()"):
            self.assertIn("static_assert(" + prova, autotest)


class C2(unittest.TestCase):
    """Pezzo X: C2 Le undici bandiere e C2P il pastorale (tools/pittore_c2.py)."""

    def test_c2_senza_parole_coi_fanti_in_tre_file_e_il_colpo_in_c2p(self):
        c = {GR.leggi(n, t)["codice"]: GR.leggi(n, t) for n, t in GR.sorgenti_del_repo()}
        prima = c["C2"]["inquadrature"][0]
        self.assertEqual(prima["piani"], ["colli", "fanti_lontani", "fanti_medi", "fanti_vicini"])
        self.assertEqual([b for i in c["C2"]["inquadrature"] for b in i["battute"]], [])
        self.assertTrue(c["C2P"]["inquadrature"][0]["colpo"])
        self.assertTrue(all(p in GR.PP.CON_PASSO for p in prima["piani"][1:]))

    def test_negativa_colpo_troppo_corto(self):
        with self.assertRaisesRegex(GR.ErroreRegia, "almeno 1 s"):
            GR.leggi("corto.regia", "cutscene C9 | x\ninquadratura 0.5 | pastorale | 0 | colpo\n")

    def test_le_due_pose_dei_fanti(self):
        """Le gambe di una posa sono nel colore 13, quelle dell'altra nel 14, che ha il colore del prato
        (12); ogni gamba della posa B ha il prato dietro, cosi' scambiando 13 e 14 sparisce."""
        for nome in GR.PP.C2.CON_PASSO:
            tela, palette, _ = GR.PP.PITTORI[nome]("giorno")
            self.assertEqual(palette[14], palette[12])
            self.assertNotEqual(palette[13], palette[12])
            a = sum(r.count(13) for r in tela.px)
            b = sum(r.count(14) for r in tela.px)
            self.assertGreater(a, 50, nome)
            self.assertGreater(b, 50, nome)

    def test_negativa_un_piano_senza_passo_non_scambia(self):
        self.assertNotIn("araldo", GR.PP.CON_PASSO)
        self.assertNotIn("colli", GR.PP.CON_PASSO)

    def test_gli_alfieri_portano_tutte_le_undici_bandiere(self):
        """Nella fila vicina (18 px) passano tutti gli undici stendardi dei dati: c'e' il campo di ognuno."""
        tela = GR.PP.PITTORI["fanti_vicini"]("giorno")[0]
        colori = {c for r in tela.px[:GR.PP.QUADRO] for c in r}
        indici = GR.PP.C2.INDICI_FANTI
        for citta in GR.PP.ST.COALIZIONE:
            self.assertIn(indici[tuple(citta["gioco"]["campo"])], colori, citta["id"])

    def test_c2_nel_budget(self):
        dipinti = GR.dipingi_piani(["colli", "fanti_lontani", "fanti_medi", "fanti_vicini"])
        tile = sum(len(v[0]) for v in dipinti.values())
        self.assertLessEqual(max(len(v[0]) for v in dipinti.values()), GR.TILE_MAX_PER_PIANO)
        self.assertLess(tile * 32 + 4 * 2048 * 2, 64 * 1024)


class C3(unittest.TestCase):
    """Pezzo X: le presentazioni a fermo immagine (tools/pittore_c3.py, regia/c3_*.regia)."""

    PERSONAGGI = {"C3U": "ubaldo", "C3G": "giorgio", "C3A": "antonio", "C3C": "corrado"}

    def controluce(self, tela, palette, margine=0.3):
        """La sagoma scura (colore 1) col bordo acceso (colore 3) davanti a un bagliore piu' chiaro di
        'margine' (luminanza media dello sfondo sopra il terreno)."""
        C3 = GR.PP.C3

        def luminanza(c):
            v = GR.colore_del_piano(PALETTE, palette[c], False)
            return (0.299 * (v & 31) + 0.587 * ((v >> 5) & 31) + 0.114 * ((v >> 10) & 31)) / 31

        righe = tela.px[:C3.SUOLO]
        sagoma = sum(r[:240].count(C3.R_SAGOMA) for r in righe)
        bordo = sum(r[:240].count(C3.R_BORDO) for r in righe)
        sfondo = [luminanza(c) for r in righe for c in r[:240] if c not in (C3.R_SAGOMA, C3.R_BORDO)]
        return sagoma >= 1200 and bordo >= 40 and sum(sfondo) / len(sfondo) - luminanza(C3.R_SAGOMA) >= margine

    def test_quattro_presentazioni_dal_copione(self):
        c = {GR.leggi(n, t)["codice"]: GR.leggi(n, t) for n, t in GR.sorgenti_del_repo()}
        for codice, chi in self.PERSONAGGI.items():
            q = c[codice]["inquadrature"]
            self.assertEqual(len(q), 1, codice)
            self.assertTrue(180 <= q[0]["frame"] <= 240, codice)                     # 3-4 s
            self.assertEqual(q[0]["piani"], [f"ritratto_{chi}"])
            self.assertEqual(q[0]["battute"], [f"R_C3_{chi.upper()}"])

    def test_in_controluce(self):
        for chi in self.PERSONAGGI.values():
            tela, palette, _ = GR.PP.PITTORI[f"ritratto_{chi}"]("giorno")
            self.assertTrue(self.controluce(tela, palette), chi)

    def test_negativa_senza_bordo_o_senza_bagliore(self):
        C3 = GR.PP.C3
        tela, palette, _ = GR.PP.PITTORI["ritratto_giorgio"]("giorno")
        spento = [[C3.R_SAGOMA if c == C3.R_BORDO else c for c in r] for r in tela.px]
        tela.px, vecchi = spento, tela.px
        self.assertFalse(self.controluce(tela, palette))
        tela.px = [[c if c in (C3.R_SAGOMA, C3.R_BORDO) else C3.R_SAGOMA_S for c in r] for r in vecchi]
        self.assertFalse(self.controluce(tela, palette))

    def test_il_cartiglio_col_nome_del_copione(self):
        """Il nome nel cartiglio e' quello del cartiglio dei dialoghi (PARLANTI del copione), scritto in
        bianco su vermiglio."""
        import genera_storia as GS
        for chi, nome in GR.PP.C3.NOMI.items():
            self.assertEqual(GS.PARLANTI[chi.upper()], nome)
            tela = GR.PP.PITTORI[f"ritratto_{chi}"]("giorno")[0]
            x0, y0, largo, alto = GR.PP.C3.cartiglio(GR.PP.Tela(512, 256), nome)
            dentro = [tela.px[y][x] for y in range(y0, y0 + alto) for x in range(x0, x0 + largo)]
            self.assertGreater(dentro.count(GR.PP.C3.R_CARTIGLIO), dentro.count(GR.PP.C3.R_NOME))
            self.assertGreater(dentro.count(GR.PP.C3.R_NOME), 10 * len(nome.replace(" ", "")) // 2)

    def test_negativa_un_nome_diverso_dal_copione(self):
        import genera_storia as GS
        # un nome sbagliato nel cartiglio non e' quello del copione (i tre senza "San", Cioti 4 nov 2026)
        self.assertNotEqual(GS.PARLANTI["UBALDO"], "Sant'Ubaldo")
        self.assertEqual(GS.PARLANTI["UBALDO"], GR.PP.C3.NOMI["ubaldo"])


class SagomeX3(unittest.TestCase):
    """Pezzo X3: Giorgio, Corrado e il maialino di Antonio rifatti. La misura: i vertici del contorno
    (dove il bordo cambia pendenza di piu' di un pixel, per righe e per colonne). Le sagome a blocchi di
    X2 (tests/_sagome_x2.py) sono le negative."""

    SOGLIE = {"giorgio": 56, "corrado": 58, "antonio": 60}

    @staticmethod
    def pixel(disegno):
        s = GR.PP.C3.Sagoma()
        disegno(s)
        return s.pixel()

    def vertici(self, disegno):
        px = self.pixel(disegno)
        tot = 0
        for asse in (0, 1):
            linee = {}
            for p in px:
                linee.setdefault(p[asse], []).append(p[1 - asse])
            for bordo in (min, max):
                seq = [bordo(linee[k]) for k in sorted(linee)]
                d = [b - a for a, b in zip(seq, seq[1:])]
                tot += sum(1 for a, b in zip(d, d[1:]) if abs(b - a) > 1)
        return tot

    def test_contorni_con_i_dettagli(self):
        for chi, soglia in self.SOGLIE.items():
            self.assertGreaterEqual(self.vertici(getattr(GR.PP.C3, chi)), soglia, chi)

    def test_negativa_le_sagome_a_blocchi(self):
        for chi, soglia in self.SOGLIE.items():
            self.assertLess(self.vertici(getattr(V, chi + "_a_blocchi")), soglia, chi)

    def maialino(self, disegno):
        zona = {(x, y) for x, y in self.pixel(disegno) if x >= 166 and y >= 74}
        corpo = min(y for x, y in zona if 182 <= x <= 190)
        orecchio = min(y for _, y in zona)
        punta = sum(1 for _, y in zona if y == orecchio)
        zampe = sorted(x for x, y in zona if y == GR.PP.C3.SUOLO - 2)
        return corpo - orecchio, punta, 1 + sum(1 for a, b in zip(zampe, zampe[1:]) if b - a > 1)

    def test_il_maialino_ha_orecchio_a_punta_e_quattro_zampe(self):
        sopra, punta, zampe = self.maialino(GR.PP.C3.antonio)
        self.assertGreaterEqual(sopra, 4)
        self.assertLessEqual(punta, 2)
        self.assertEqual(zampe, 4)

    def test_negativa_il_maialino_pesce(self):
        sopra, _, _ = self.maialino(V.antonio_a_blocchi)
        self.assertLess(sopra, 4)


class C5C6C7(unittest.TestCase):
    """F10: C5 Il risveglio dei Ceri, C6 La visione nel vetro, C7S e C7B le presentazioni dei luoghi
    (cutscene/v2/SCHEDE.md; tools/pittore_c5.py, pittore_c6.py, pittore_c7.py)."""

    @classmethod
    def setUpClass(cls):
        cls.c = {GR.leggi(n, t)["codice"]: GR.leggi(n, t) for n, t in GR.sorgenti_del_repo()}

    def battute(self, codice):
        return [b for i in self.c[codice]["inquadrature"] for b in i["battute"]]

    def test_come_nelle_schede(self):
        durate = {"C5": 22, "C6": 20, "C7S": 11, "C7B": 12.5}
        inquadrature = {"C5": 7, "C6": 5, "C7S": 2, "C7B": 2}
        for codice, secondi in durate.items():
            q = self.c[codice]["inquadrature"]
            self.assertEqual(sum(i["frame"] for i in q), secondi * 60, codice)
            self.assertEqual(len(q), inquadrature[codice], codice)
        self.assertEqual(self.battute("C5"), ["R_A1_08_09"])                  # la battuta del copione
        self.assertEqual(self.battute("C6"), [])                              # muta
        self.assertEqual(self.battute("C7S"), ["R_C7S_00", "R_C7S_01"])
        self.assertEqual(self.battute("C7B"), ["R_C7B_00", "R_C7B_01", "R_C7B_02"])
        # C6 parte e finisce sulla bifora del prologo; i colpi dove li vuole la scheda
        self.assertEqual(self.c["C6"]["inquadrature"][0]["piani"], ["vetrata"])
        self.assertEqual([i["colpo"] for i in self.c["C5"]["inquadrature"]], [False, True, True, False, False, True, False])
        self.assertTrue(self.c["C6"]["inquadrature"][1]["dissolvi"])

    def test_negativa_c6_con_una_battuta(self):
        n, t = next((n, t) for n, t in GR.sorgenti_del_repo() if "c6_" in n)
        parlata = GR.leggi(n, t + "narratore R_C7B_00\n")
        self.assertNotEqual([b for i in parlata["inquadrature"] for b in i["battute"]], [])

    def test_didascalie_in_una_riga(self):
        """Le battute nuove del narratore stanno in una riga da 224 px (col font vero)."""
        font = S.carica("font")
        testi = {r.split("|")[0].strip(): r.split("|", 2)[2].strip()
                 for r in open(os.path.join(RADICE, "testi", "regia.testi"), encoding="utf-8")
                 if r.startswith("R_C7")}
        self.assertEqual(len(testi), 5)
        for ident, testo in testi.items():
            self.assertEqual(len(S.a_capo(font, S.normalizza(font, testo), 224)), 1, ident)

    def test_negativa_didascalia_troppo_lunga(self):
        font = S.carica("font")
        lunga = "Gli Stradoni: nove tornanti di ghiaia fino alla Basilica, e poi ancora."
        self.assertGreater(len(S.a_capo(font, S.normalizza(font, lunga), 224)), 1)

    def test_i_ceri_girano_e_la_fila_sale(self):
        """Il passo: i Ceri hanno le facce nei colori 13 e 14, tutti e due visibili e diversi (scambiandoli il
        Cero gira); la fila in ferro ha il 14 del colore della roccia del sentiero, come i fanti di C2 il prato."""
        PP = GR.PP
        self.assertTrue({"c5_ceri", "c6_fanti"} <= PP.CON_PASSO)
        tela, palette, _ = PP.PITTORI["c5_ceri"]("giorno")
        self.assertNotEqual(palette[13], palette[14])
        self.assertGreater(sum(r.count(13) for r in tela.px), 200)
        self.assertGreater(sum(r.count(14) for r in tela.px), 200)
        tela, palette, _ = PP.PITTORI["c6_fanti"]("giorno")
        self.assertEqual(palette[14], PP.C6.PALETTE_VISIONE[PP.C6.VI_ROCCIA])
        self.assertNotEqual(palette[13], palette[14])
        self.assertGreater(sum(r.count(13) for r in tela.px), 30)
        self.assertGreater(sum(r.count(14) for r in tela.px), 30)

    def test_negativa_senza_passo(self):
        for nome in ("c5_navata", "c5_raggi", "c6_corrado", "c7_monte"):
            self.assertNotIn(nome, GR.PP.CON_PASSO)

    def test_il_vetro_scuro_e_quello_dell_epilogo(self):
        """C6 scurisce lo stesso vetro della lancetta destra che all'epilogo prende colore: le differenze
        dalla bifora chiara stanno tutte li' dentro."""
        chiara, scura = GR.PP.vetrata("giorno")[0], GR.PP.PITTORI["c6_vetro_scuro"]("giorno")[0]
        diversi = [(x, y) for y in range(112) for x in range(240) if chiara.px[y][x] != scura.px[y][x]]
        self.assertGreater(len(diversi), 300)
        self.assertTrue(all(122 <= x < 158 and 70 <= y < 100 for x, y in diversi))

    def test_negativa_la_bifora_chiara_non_e_scura(self):
        chiara = GR.PP.vetrata("giorno")[0]
        self.assertEqual(sum(1 for y in range(74, 100) for x in range(124, 156) if chiara.px[y][x] == GR.PP.V_BLU), 0)

    def test_la_striscia_nera_una_volta(self):
        """Nella parete vicina della gola la riga scura c'e' e, in ogni colonna, e' una fascia sola; il fondo
        lontano non ce l'ha."""
        C7 = GR.PP.C7
        tela = C7.c7_gola_parete("giorno")[0]
        colonne = 0
        for x in range(0, 336):
            ys = [y for y in range(112) if tela.px[y][x] == C7.G_NERA]
            if ys:
                colonne += 1
                self.assertEqual(ys, list(range(ys[0], ys[-1] + 1)), x)
        self.assertGreater(colonne, 200)
        striscia = C7.c7_striscia("giorno")[0]
        self.assertGreater(sum(r[:240].count(C7.G_NERA) for r in striscia.px[:112]), 300)

    def test_negativa_il_fondo_senza_striscia(self):
        C7 = GR.PP.C7
        self.assertEqual(sum(r.count(C7.G_NERA) for r in C7.c7_gola_fondo("giorno")[0].px), 0)

    def test_nel_budget_della_vram(self):
        """Ogni inquadratura del repo sta nei 32 blocchi da 2 KB della VRAM dei BG (genera_regia lo
        controlla); la piu' piena delle nuove e' la gola dentro il vetro di C6."""
        usati = sorted({p for c in self.c.values() for i in c["inquadrature"] for p in i["piani"]})
        dipinti = GR.dipingi_piani(usati)
        GR.controlla_vram(list(self.c.values()), dipinti)
        nuove = [GR.blocchi_vram([len(dipinti[p][0]) for p in i["piani"]])
                 for k in ("C5", "C6", "C7S", "C7B") for i in self.c[k]["inquadrature"]]
        self.assertLessEqual(max(nuove), GR.VRAM_BLOCCHI)
        self.assertLessEqual(max(len(dipinti[p][0]) for p in usati), GR.TILE_MAX_PER_PIANO)

    def test_negativa_inquadratura_oltre_la_vram(self):
        c = GR.leggi("pieno.regia", "cutscene CX | x\ninquadratura 2 | c6_cielo c6_parete c6_sentiero c6_fanti | 16\n")
        finti = {p: ([None] * 590, None, None, None) for p in c["inquadrature"][0]["piani"]}
        with self.assertRaisesRegex(GR.ErroreRegia, "blocchi di VRAM"):
            GR.controlla_vram([c], finti)
        self.assertEqual(GR.blocchi_vram([590] * 4), 4 * (10 + 2))


if __name__ == "__main__":
    unittest.main(verbosity=2)
