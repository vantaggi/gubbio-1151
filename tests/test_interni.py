"""Gli interni esplorabili della citta' (pezzi INT0-INT2, tools/pittore_interni.py): sei stanze (taverna,
spezieria, bottega dei conti, carradore, casa del medico, Sala dei Consoli) a cui si entra dal portone della
facciata. Qui: le .area sono quelle che il pittore scrive, la griglia segue gli arredi, si entra e si esce,
il fondale sta nei banchi e nei toni medi (C5). Ogni regola ha il suo caso negativo.
"""
import json
import os
import sys
import unittest

from _stile import RADICE

sys.path.insert(0, os.path.join(RADICE, "tools"))
import genera_mondo as G  # noqa: E402
import pittore_interni as PI  # noqa: E402

AREE = os.path.join(RADICE, "mondo", "aree")


def sorgenti():
    return G.sorgenti_del_repo()


def area_preparata(aid, mondo, src=None):
    src = src or [s for s in sorgenti() if s[0].endswith("/%s.area" % aid)][0]
    a = G.leggi_area(*src)
    G.prepara_area(a, mondo)
    return a


class AreeScritteDalPittore(unittest.TestCase):

    def test_sei_interni(self):
        self.assertEqual(len(PI.INTERNI), 6)
        self.assertEqual(sorted(PI.STANZA_DELL_AREA), sorted(v[0] for v in PI.INTERNI.values()))

    def test_ogni_area_coincide_col_pittore(self):
        for nome, (aid, *_resto) in PI.INTERNI.items():
            with open(os.path.join(AREE, aid + ".area"), encoding="utf-8") as f:
                self.assertEqual(f.read(), PI.testo_area(nome), "eseguire python tools/pittore_interni.py --aree")

    def test_la_griglia_segue_gli_arredi(self):
        """Dentro la stanza una cella da 16 px solida (un arredo, il muro di fondo) e' '#' in tutti i suoi 4 tile."""
        for nome in PI.INTERNI:
            st = PI.stanza_di_gioco(nome)
            g = PI.griglia_di_gioco(st)
            for cy in range(st.ch):
                for cx in range(st.cw):
                    tx, ty = (st.x0 + cx * PI.CELLA) // 8, (st.y0 + cy * PI.CELLA) // 8
                    atteso = "#" if st.solide[cy][cx] else "L"
                    for dy in (0, 1):
                        for dx in (0, 1):
                            self.assertEqual(g[ty + dy][tx + dx], atteso, (nome, cx, cy))

    def test_negativa_un_arredo_in_piu_cambia_la_griglia(self):
        st = PI.stanza_di_gioco("taverna")
        prima = PI.griglia_di_gioco(st)
        libere = [(cx, cy) for cy in range(st.ch) for cx in range(st.cw) if not st.solide[cy][cx]]
        cx, cy = libere[len(libere) // 2]
        st.solide[cy][cx] = True
        self.assertNotEqual(PI.griglia_di_gioco(st), prima)


class SiEntraESiEsce(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.mondo = G.mondo_del_repo()

    def test_portone_della_facciata_e_varco(self):
        for nome, (aid, fuori, mid, lettera, spawn) in PI.INTERNI.items():
            a = area_preparata(fuori, self.mondo)
            self.assertEqual(a["ingressi"].get(lettera), mid, nome)
            self.assertTrue(G.celle_varco(a, lettera), nome)
            self.assertIn((lettera, aid, spawn), [u[:3] for u in a["uscite"]], nome)
            self.assertGreaterEqual(G.distanza_dal_varco(a, a["spawn"][spawn], lettera), G.DISTANZA_MIN_SPAWN_USCITA)

    def test_archi_dentro_nel_grafo(self):
        with open(os.path.join(RADICE, "mondo", "grafo.json"), encoding="utf-8") as f:
            grafo = json.load(f)
        archi = {(e["da"], e["a"]) for e in grafo["archi"] if e.get("dentro")} | \
                {(e["a"], e["da"]) for e in grafo["archi"] if e.get("dentro")}
        for nome, (aid, fuori, *_r) in PI.INTERNI.items():
            self.assertIn((fuori.upper(), aid.upper()), archi, nome)

    def test_dallo_spawn_si_raggiunge_l_uscita(self):
        for nome, (aid, *_r) in PI.INTERNI.items():
            a = area_preparata(aid, self.mondo)
            visti = G.raggiungibili(a, a["spawn"][0])
            uscita = G.celle_varco(a, "A")
            self.assertTrue(uscita, nome)
            self.assertTrue(any((x, y - 1) in visti for x, y in uscita), nome)
            self.assertEqual(G.lati_del_varco(a, "A"), {"basso"}, nome)

    def test_negativa_uscita_murata(self):
        """Con la soglia sotto la porta murata il generatore del mondo si ferma."""
        src = [s for s in sorgenti() if s[0].endswith("/taverna_interno.area")][0]
        righe = src[1].split("\n")
        i = righe.index("griglia") + 1
        alto = len([r for r in righe[i:] if r.strip()])
        r = list(righe[i + alto - 3])
        r = ["#" if c == "L" else c for c in r]
        righe[i + alto - 3] = "".join(r)
        altre = [s for s in sorgenti() if not s[0].endswith("/taverna_interno.area")]
        with self.assertRaises(G.ErroreMondo):
            G.genera(altre + [(src[0], "\n".join(righe))], G.S.carica("palette"), self.mondo)


class OrdineDelleAree(unittest.TestCase):
    """I salvataggi tengono l'indice dell'area: gli interni stanno in coda, le 19 aree di prima non cambiano."""

    PRIMA = ["piazza_grande", "via_xx_settembre", "duomo_ducale", "monte_ingino", "basilica", "bottaccione",
             "san_martino", "largo_bargello", "via_dei_consoli", "basilica_interno", "condotto", "gola_arco",
             "gola_miasmi", "gola_striscia", "piazza_quaranta_martiri", "san_pietro", "sant_agostino",
             "sant_andrea", "teatro_romano"]

    def test_interni_in_coda(self):
        with open(G.USCITA, encoding="utf-8") as f:
            h = f.read()
        corpo = h[h.index("enum class AreaId"):]
        corpo = corpo[corpo.index("{") + 1:corpo.index("};")]
        ids = [r.strip().rstrip(",").lower() for r in corpo.split("\n") if r.strip()]
        self.assertEqual(ids[:19], self.PRIMA)
        self.assertEqual(ids[19:], G.AREE_IN_CODA)

    def test_all_aperto_sotto_24(self):
        """La nebbia della mappa (aree_viste, 24 bit) conta solo le aree all'aperto."""
        ordine = [a["id"] for a in G.ordina([{"id": i} for i in self.PRIMA + G.AREE_IN_CODA],
                                            G.anello(G.mondo_del_repo()["grafo"]))]
        for i, aid in enumerate(ordine):
            if aid not in G.AREE_IN_CODA and aid != "basilica_interno":
                self.assertLess(i, 24, aid)

    def test_negativa_un_interno_fuori_coda(self):
        ordine = [a["id"] for a in G.ordina([{"id": i} for i in self.PRIMA + ["aaa_interno"]],
                                            G.anello(G.mondo_del_repo()["grafo"]))]
        self.assertNotEqual(ordine[-1], "aaa_interno")


class PortaliAperti(unittest.TestCase):
    """Dove si entra il portone e' aperto: il vano buio sopra le celle del varco (P2)."""

    @classmethod
    def setUpClass(cls):
        cls.mondo = G.mondo_del_repo()

    def test_i_portali_frontali_sono_aperti(self):
        frontali = {"taverna": "san_pietro", "spezieria": "san_pietro", "casa_medico": "san_martino",
                    "consoli": "piazza_grande"}
        for mid, fuori in frontali.items():
            a = area_preparata(fuori, self.mondo)
            G.disegna_area(a, self.mondo)
            aperti = dict(PI.PORTALI_APERTI.get(fuori, []))
            self.assertGreater(aperti.get(mid, 0), 40, mid)

    def test_negativa_senza_ingresso_niente_portale(self):
        a = area_preparata("via_dei_consoli", self.mondo)
        self.assertFalse(a.get("ingressi"))
        G.disegna_area(a, self.mondo)
        self.assertEqual(PI.PORTALI_APERTI.get("via_dei_consoli"), [])


class ArriviDelleAree(unittest.TestCase):

    def test_quaranta_martiri_ha_l_arrivo_del_carradore(self):
        src = [s for s in sorgenti() if s[0].endswith("/piazza_quaranta_martiri.area")][0]
        self.assertIn(6, G.leggi_area(*src)["spawn"])
        self.assertLess(6, G.SPAWN_PER_AREA)

    def test_negativa_spawn_oltre_il_limite(self):
        src = [s for s in sorgenti() if s[0].endswith("/piazza_quaranta_martiri.area")][0]
        testo = src[1].replace("griglia\n", "spawn %d 38 56\ngriglia\n" % G.SPAWN_PER_AREA, 1)
        with self.assertRaises(G.ErroreMondo):
            G.leggi_area(src[0], testo)


class FondaleNeiBanchi(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.mondo = G.mondo_del_repo()
        cls.aree = {}
        for aid in PI.STANZA_DELL_AREA:
            a = area_preparata(aid, cls.mondo)
            G.COMPROMESSI.pop(aid, None)
            a["tile"], a["indici"], _ = G.disegna_area(a, cls.mondo)
            cls.aree[aid] = a

    def test_budget_dei_tile(self):
        for aid, a in self.aree.items():
            self.assertLessEqual(len(a["tile"]), 400, aid)

    def test_compromessi_pochi_e_vicini(self):
        """Nota alla regola C1: dove nessun banco ha tutti i colori di un tile, il pittore mette un tono della
        stessa rampa; restano compromessi di genera_mondo (fra rampe) al piu' nel 3% dei tile, e vicini."""
        for aid, a in self.aree.items():
            comp = G.COMPROMESSI.get(aid, [])
            self.assertLess(len(comp), a["larghezza"] * a["altezza"] * 0.03, aid)
            self.assertLess(max([c for *_xy, c in comp], default=0), 300, aid)

    def test_le_sostituzioni_restano_nella_rampa(self):
        for aid in self.aree:
            fatte = PI.SOSTITUZIONI.get(aid, [])
            self.assertTrue(fatte, aid)
            self.assertTrue(all(c[0] == v[0] for c, v in fatte), aid)

    def test_negativa_un_tile_senza_banco_viene_portato_nella_rampa(self):
        q = G.PC.Quadro(1, 1)
        for y in range(8):
            for x in range(8):
                q.px[y][x] = (("legno e cuoio", 3), ("cotto e coppi", 2), ("oro e bronzo", 1))[(x + y) % 3]
        prima = {c for r in q.px for c in r}
        self.assertFalse(any(prima <= set(b[1:]) for b in G.BANCHI_FONDALI))
        PI.nella_rampa(q, "prova_rampa")
        dopo = {c for r in q.px for c in r}
        self.assertTrue(any(dopo <= set(b[1:]) for b in G.BANCHI_FONDALI))
        self.assertEqual({c[0] for c in dopo}, {c[0] for c in prima})

    def test_banco_degli_interni(self):
        self.assertIn(PI.BANCO_INTERNI, G.BANCHI_FONDALI)
        self.assertEqual(len(PI.BANCO_INTERNI), 16)
        self.assertTrue({("legno e cuoio", t) for t in range(4)} <= set(PI.BANCO_INTERNI))

    def test_le_assi_del_carradore_nei_toni_medi(self):
        """C5: il pavimento di assi sta nei toni 2-3 del legno, non nel buio (0-1)."""
        st = PI.stanza_di_gioco("bottega_carradore")
        conta = {}
        for cy in range(4, st.ch):
            for cx in range(st.cw):
                if st.solide[cy][cx]:
                    continue
                for y in range(st.y0 + cy * PI.CELLA, st.y0 + (cy + 1) * PI.CELLA):
                    for x in range(st.x0 + cx * PI.CELLA, st.x0 + (cx + 1) * PI.CELLA):
                        c = st.t.px[y][x]
                        if c[0] == "legno e cuoio":
                            conta[c[1]] = conta.get(c[1], 0) + 1
        medi = conta.get(2, 0) + conta.get(3, 0)
        self.assertGreater(medi, 2 * (conta.get(0, 0) + conta.get(1, 0)), conta)

    def test_negativa_colori_fuori_banco_sono_compromessi(self):
        q = G.PC.Quadro(1, 1)
        for y in range(8):
            for x in range(8):
                q.px[y][x] = (("legno e cuoio", 3), ("verde dei monti", 4), ("vermiglio comunale", 1))[(x + y) % 3]
        G.COMPROMESSI.pop("prova_interni", None)
        G.indicizza_tile(q, 0, 0, {"id": "prova_interni"})
        self.assertEqual(len(G.COMPROMESSI["prova_interni"]), 1)


class CoseDaEsaminare(unittest.TestCase):
    """INTC: due cose per stanza, coi loro testi, ai piedi dell'oggetto, lontane da chi sta nella stanza."""

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(RADICE, "testi", "interni.testi"), encoding="utf-8") as f:
            cls.testi = f.read()

    def test_due_per_stanza_coi_testi(self):
        per = {}
        for stanza, _, _, _, testo in PI.COSE:
            per[stanza] = per.get(stanza, 0) + 1
            self.assertIn(testo + " ", self.testi.replace("\t", " "), testo)
        self.assertEqual(sorted(per), sorted(PI.INTERNI))
        self.assertEqual(set(per.values()), {2})

    def test_celle_libere_e_lontane(self):
        evita = {"BOTTEGA_CONTI_INTERNO": [(12, 9)]}
        for area, nome, tx, ty, _ in PI.cose_di_gioco(evita):
            st = PI.stanza_di_gioco([k for k, v in PI.INTERNI.items() if v[0] == area][0])
            g = PI.griglia_di_gioco(st)
            self.assertTrue(all(g[ty + j][tx + i] == "L" for i in (-1, 0, 1) for j in (-1, 0, 1)), nome)
            for u, v in evita.get(area.upper(), []):
                self.assertGreaterEqual(max(abs(tx - u), abs(ty - v)), PI.LONTANO_DAGLI_NPC, nome)

    def test_negativa_un_npc_sposta_la_cosa(self):
        prima = {n: (x, y) for _, n, x, y, _ in PI.cose_di_gioco()}
        x, y = prima["camino"]
        dopo = {n: (x, y) for _, n, x, y, _ in PI.cose_di_gioco({"TAVERNA_INTERNO": [(x, y)]})}
        self.assertNotEqual(prima["camino"], dopo["camino"])


class DoniDegliAmici(unittest.TestCase):
    """INTB: Padellino da' 1 Crescia, Valenza 2 Biscotti, con bandiere libere delle quest."""

    def test_doni_e_bandiere(self):
        import genera_storia as GS
        doni = {d["npc"]: (d["oggetto"], d["quanti"]) for d in GS.DONI}
        self.assertEqual(doni, {"Padellino": ("CRESCIA", 1), "Valenza": ("BISCOTTI", 2)})
        for d in GS.DONI:
            self.assertIn(d["bandiera"], GS.BANDIERE_QUEST)

    def test_negativa_nessun_dono_da_chi_non_sta_dentro(self):
        import genera_storia as GS
        self.assertNotIn("Ciaccio", [d["npc"] for d in GS.DONI])


class VariantiDiFase(unittest.TestCase):
    """INTp: le stanze che cambiano con la fase hanno un fondale loro, con la stessa griglia della stanza di giorno."""

    def test_stessa_griglia(self):
        for aid, var in PI.VARIANTI_DI_GIOCO:
            nome = PI.STANZA_DELL_AREA[aid]
            self.assertIn(var, PI.VARIANTI[nome])
            self.assertEqual(PI.griglia_di_gioco(PI.stanza_di_gioco(nome)),
                             PI.griglia_di_gioco(PI.stanza_di_gioco(nome, var)), aid)

    def test_nel_mondo_e_diverse(self):
        with open(os.path.join(RADICE, "include", "mondo.h"), encoding="utf-8") as f:
            h = f.read()
        for aid, var in PI.VARIANTI_DI_GIOCO:
            n = f"{aid.upper()}_{var.upper()}"
            self.assertIn(f"{{ AreaId::{aid.upper()}, FONDALE_{n}, TILE_{n},", h)
            base = h.split(f"inline constexpr uint16_t FONDALE_{aid.upper()}[")[1].split("};")[0]
            altro = h.split(f"inline constexpr uint16_t FONDALE_{n}[")[1].split("};")[0]
            self.assertNotEqual(base, altro, n)

    def test_negativa_una_panca_tolta_cambia_la_griglia(self):
        st = PI.stanza_di_gioco("taverna", "digiuno")
        g = PI.griglia_di_gioco(st)
        self.assertNotEqual(g, PI.griglia_di_gioco(PI.stanza_di_gioco("sala_consoli")))


class NotteDentro(unittest.TestCase):
    """Di notte negli interni anche oro e vermiglio vanno alle rampe di notte (il tappeto della soglia non brilla)."""

    def test_vermiglio_di_notte_dentro(self):
        pal = G.S.carica("palette")
        fuori = G.banchi_fondali(pal, notte=True)
        dentro = G.banchi_fondali(pal, notte=True, dentro=True)
        rossi = [i for i, r in enumerate(G.BANCHI_FONDALI[3]) if r[0] == G.PC.R]
        self.assertTrue(rossi)
        for i in rossi:
            self.assertNotEqual(fuori[3][i], dentro[3][i])

    def test_negativa_gli_altri_banchi_uguali(self):
        pal = G.S.carica("palette")
        fuori = G.banchi_fondali(pal, notte=True)
        dentro = G.banchi_fondali(pal, notte=True, dentro=True)
        self.assertEqual([b for k, b in enumerate(fuori) if k != 3], [b for k, b in enumerate(dentro) if k != 3])


if __name__ == "__main__":
    unittest.main()
