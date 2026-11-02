#!/usr/bin/env python3
"""Il mondo: mondo/aree/*.area e il generatore tools/genera_mondo.py.

Il grafo ha una sola fonte, mondo/grafo.json: qui si controlla che le uscite delle griglie lo
rispecchino (archi, lati dello schermo di mondo/varchi.json) e che gli spawn d'arrivo stiano
lontani dalla propria uscita.

Riprende i controlli di test_mondo.py del prototipo (varchi reciproci, rientri validi, anello
chiuso, nessun vicolo cieco) sui nuovi file di dati, e aggiunge quelli che il prototipo lasciava
all'autotest: varchi raggiungibili camminando e spawn d'arrivo lontani dai varchi. Ogni
controllo ha la sua prova negativa. La camminata vera, con la collisione del gioco, la fa
l'autotest C++ in include/mondo_autotest.h.

    python -m unittest tests.test_mondo
"""
import copy
import importlib.util
import os
import re
import unittest

from _stile import S, RADICE

_spec = importlib.util.spec_from_file_location("genera_mondo", os.path.join(RADICE, "tools", "genera_mondo.py"))
G = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(G)

PALETTE = S.carica("palette")


def sorgenti_con(nome_file, modifica):
    """I sorgenti del repo, con il file indicato passato per 'modifica(testo) -> testo'."""
    out = []
    for nome, testo in G.sorgenti_del_repo():
        out.append((nome, modifica(testo) if nome.endswith(nome_file) else testo))
    return out


def cambia_griglia(testo, y, x, carattere):
    righe = testo.split("\n")
    g = righe.index("griglia")
    r = list(righe[g + 1 + y])
    r[x] = carattere
    righe[g + 1 + y] = "".join(r)
    return "\n".join(righe)


def griglia_mappata(testo, funzione):
    """Applica funzione(griglia) -> griglia alle sole righe della griglia di un file .area."""
    righe = testo.split("\n")
    g = righe.index("griglia")
    corpo = [r for r in righe[g + 1:] if r]
    nuova = funzione([list(r) for r in corpo])
    return "\n".join(righe[:g + 1] + ["".join(r) for r in nuova]) + "\n"


def togli_varco(lettera, al_posto="#"):
    return lambda testo: griglia_mappata(testo, lambda g: [[al_posto if c == lettera else c for c in r] for r in g])


def mura_attorno(lettera):
    """Mura ogni cella calpestabile accanto al varco: il varco resta ma non ci si arriva."""
    def mura(g):
        celle = [(x, y) for y, r in enumerate(g) for x, c in enumerate(r) if c == lettera]
        for x, y in celle:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= ny < len(g) and 0 <= nx < len(g[0]) and g[ny][nx] in ".,S":
                    g[ny][nx] = "#"
        return g
    return lambda testo: griglia_mappata(testo, mura)


def area_finale(nome):
    """L'area del repo con gli edifici gia' posati dal generatore, e i rettangoli posati."""
    mondo = G.mondo_del_repo()
    testo = dict(G.sorgenti_del_repo())["mondo/aree/%s.area" % nome]
    a = G.leggi_area(nome, testo)
    return a, G.posa_edifici(a, mondo["monumenti"]), mondo["monumenti"]


class Mondo(unittest.TestCase):

    def setUp(self):
        self.aree = {a["id"]: a for a in (G.leggi_area(n, t) for n, t in G.sorgenti_del_repo())}
        self.mondo = G.mondo_del_repo()

    def test_header_del_repo_aggiornato(self):
        atteso = G.genera(G.sorgenti_del_repo(), PALETTE)
        with open(G.USCITA, encoding="utf-8") as f:
            self.assertEqual(f.read(), atteso, "eseguire python tools/genera_mondo.py")

    def test_quattordici_aree(self):
        self.assertEqual(len(self.aree), 14)

    def test_l_anello_si_chiude(self):
        giro = G.anello(self.mondo["grafo"])
        for da, verso in zip(giro, giro[1:] + giro[:1]):
            self.assertIn(verso, [u[1] for u in self.aree[da]["uscite"]], f"{da} -> {verso}")

    def test_ogni_varco_e_reciproco(self):
        for a in self.aree.values():
            for _, dest, _, _ in a["uscite"]:
                if dest in G.DUNGEON:
                    continue
                self.assertIn(a["id"], [u[1] for u in self.aree[dest]["uscite"]], f"{a['id']} -> {dest}")

    def test_nessun_vicolo_cieco(self):
        for a in self.aree.values():
            self.assertTrue(a["uscite"], a["id"])

    def test_bottaccione_ha_l_ingresso_della_gola(self):
        self.assertIn(("I", "gola_bottaccione"), [(u[0], u[1]) for u in self.aree["bottaccione"]["uscite"]])

    def test_orientamento_della_piazza(self):
        """Alto = ovest: i Consoli stanno piu' in alto del Pretorio, che sta piu' a est."""
        _, posati, _ = area_finale("piazza_grande")
        self.assertLess(posati["consoli"][1], posati["pretorio"][1])
        self.assertNotIn("piazza_grande", posati, "la piazza e' uno spazio aperto, non un blocco")

    def test_scala_dei_fronti(self):
        """1 tile = 1,5 m, mai compresso: Consoli 26x23 con la facciata e il portone in basso,
        Pretorio con la facciata in alto (si vede il retro), Bargello frontale, Basilica 33x15."""
        a, posati, _ = area_finale("piazza_grande")
        x, y, w, h = posati["consoli"]
        self.assertEqual((w, h), (26, 23))
        self.assertEqual(set(a["griglia"][y + h - 1][x:x + w]), {"C", "d"})
        x, y, w, h = posati["pretorio"]
        self.assertEqual({c for r in a["griglia"][y:y + h] for c in r[x:x + w]}, {"#"})
        a, posati, _ = area_finale("largo_bargello")
        x, y, w, h = posati["bargello"]
        self.assertIn("d", a["griglia"][y + h - 1][x:x + w])
        _, posati, _ = area_finale("basilica")
        self.assertEqual(sorted(posati["basilica"][2:]), [15, 33])

    def test_ogni_edificio_con_le_misure_esatte(self):
        for n, _ in G.sorgenti_del_repo():
            nome = n.split("/")[-1][:-5]
            a, posati, monumenti = area_finale(nome)
            self.assertEqual(set(posati), set(G.edifici_attesi(nome, monumenti)), nome)
            G.controlla_edifici(a, posati, monumenti)

    def test_negativa_edificio_rimpicciolito(self):
        a, posati, monumenti = area_finale("piazza_grande")
        x, y, w, h = posati["consoli"]
        posati["consoli"] = (x, y, w - 1, h)
        with self.assertRaisesRegex(G.ErroreMondo, "l'edificio consoli e' 25x23 tile, il censimento lo vuole 26x23"):
            G.controlla_edifici(a, posati, monumenti)

    def test_negativa_edificio_che_esce_dalla_griglia(self):
        """Una misura cambiata nel censimento si propaga: un Bargello di 40 tile non ci sta piu'."""
        mondo = copy.deepcopy(G.mondo_del_repo())
        mondo["monumenti"]["bargello"]["misure_tile"] = [40, 6]
        with self.assertRaisesRegex(G.ErroreMondo, "l'edificio bargello \\(6x40 tile in .*\\) esce dalla griglia"):
            G.genera(G.sorgenti_del_repo(), PALETTE, mondo)

    def test_negativa_edifici_sovrapposti(self):
        """Senza lo spostamento dichiarato, i Consoli finirebbero sopra un altro edificio."""
        sorgenti = sorgenti_con("piazza_grande.area", lambda t: "\n".join(
            r for r in t.split("\n") if not r.startswith("sposta consoli")))
        with self.assertRaisesRegex(G.ErroreMondo, "si sovrappone a"):
            G.genera(sorgenti, PALETTE)

    def test_negativa_edificio_sul_varco(self):
        sorgenti = sorgenti_con("largo_bargello.area", lambda t: t.replace("fattore", "sposta bargello 0 -10\nfattore"))
        with self.assertRaisesRegex(G.ErroreMondo, "l'edificio bargello copre il varco 'A'"):
            G.genera(sorgenti, PALETTE)

    def test_negativa_sposta_un_monumento_che_non_e_un_edificio(self):
        sorgenti = sorgenti_con("largo_bargello.area", lambda t: t.replace("fattore", "sposta fontana_matti 1 1\nfattore"))
        with self.assertRaisesRegex(G.ErroreMondo, "fontana_matti non e' un edificio di quest'area"):
            G.genera(sorgenti, PALETTE)

    def test_tracciati_e_spazi_aperti_calpestabili(self):
        """Via dei Consoli e' un tracciato, il ponte di San Martino uno spazio aperto: niente blocchi."""
        _, posati, _ = area_finale("via_dei_consoli")
        self.assertEqual(posati, {})
        _, posati, _ = area_finale("san_martino")
        self.assertNotIn("ponte_san_martino", posati)

    def test_negativa_ponte_come_edificio(self):
        """Prova negativa: senza la voce in SPAZI_APERTI il ponte diventerebbe un blocco, e il
        generatore lo trova sotto San Domenico."""
        vecchio = dict(G.SPAZI_APERTI)
        try:
            del G.SPAZI_APERTI["ponte_san_martino"]
            with self.assertRaisesRegex(G.ErroreMondo, "si sovrappone a ponte_san_martino"):
                area_finale("san_martino")
        finally:
            G.SPAZI_APERTI.clear()
            G.SPAZI_APERTI.update(vecchio)

    def test_ogni_varco_sul_lato_di_varchi_json(self):
        for a in self.aree.values():
            for lettera, dest, _, _ in a["uscite"]:
                if dest in G.DUNGEON:
                    continue
                atteso = [v["lato"] for v in self.mondo["varchi"][a["id"].upper()] if v["verso"] == dest.upper()]
                self.assertEqual(G.lati_del_varco(a, lettera), set(atteso), f"{a['id']} -> {dest}")

    def test_spawn_lontani_dalla_propria_uscita(self):
        for a in self.aree.values():
            for lettera, dest, spawn, _ in a["uscite"]:
                if dest in G.DUNGEON:
                    continue
                self.assertGreaterEqual(G.distanza_dal_varco(a, a["spawn"][spawn], lettera),
                                        G.DISTANZA_MIN_SPAWN_USCITA, f"{a['id']} spawn {spawn}")

    def test_quote_da_grafo_json(self):
        """La quota viene da grafo.json: via dei Consoli sale da 27 a 67 m."""
        with open(G.USCITA, encoding="utf-8") as f:
            header = f.read()
        self.assertIn("GRIGLIA_VIA_DEI_CONSOLI, MAPPA_VIA_DEI_CONSOLI, 32, 64, 27, 67,", header)

    def test_negativa_spawn_a_due_tile_da_un_altro_varco(self):
        """L'arrivo da via dei Consoli spostato a 2 tile dal varco verso San Martino."""
        sorgenti = sorgenti_con("largo_bargello.area", lambda t: t.replace("spawn 1 9 22", "spawn 1 15 3"))
        with self.assertRaisesRegex(G.ErroreMondo, "a 2 tile da un varco"):
            G.genera(sorgenti, PALETTE)

    def test_negativa_spawn_vicino_alla_propria_uscita(self):
        """(c) L'arrivo da via dei Consoli a 5 tile dal varco B, da cui si entra."""
        sorgenti = sorgenti_con("largo_bargello.area", lambda t: t.replace("spawn 1 9 22", "spawn 1 9 25"))
        with self.assertRaisesRegex(G.ErroreMondo, "a 5 tile dalla sua uscita 'B', ne servono almeno 6"):
            G.genera(sorgenti, PALETTE)

    def test_negativa_uscita_senza_arco(self):
        """(a) Un'uscita verso un'area che grafo.json non collega."""
        sorgenti = sorgenti_con("teatro_romano.area", lambda t: t.replace("uscita A san_martino", "uscita A largo_bargello"))
        with self.assertRaisesRegex(G.ErroreMondo, "non ha l'arco teatro_romano-largo_bargello"):
            G.genera(sorgenti, PALETTE)

    def test_negativa_arco_senza_uscita(self):
        """(a) Un arco di grafo.json che nessuna griglia apre."""
        mondo = copy.deepcopy(self.mondo)
        mondo["grafo"]["archi"].append({"da": "SAN_PIETRO", "a": "SANT_ANDREA", "verso": "E", "come": "prova"})
        with self.assertRaisesRegex(G.ErroreMondo, "ha l'arco (san_pietro-sant_andrea|sant_andrea-san_pietro), "
                                                   "ma l'area non ha l'uscita"):
            G.genera(G.sorgenti_del_repo(), PALETTE, mondo)

    def test_negativa_varco_sul_lato_sbagliato(self):
        """(b) Le destinazioni di via dei Consoli come nel prototipo: Piazza Grande in alto."""
        def scambia(testo):
            testo = testo.replace("uscita A largo_bargello", "uscita A X")
            testo = testo.replace("uscita B piazza_grande", "uscita B largo_bargello")
            return testo.replace("uscita A X", "uscita A piazza_grande")
        with self.assertRaisesRegex(G.ErroreMondo, "il varco 'A' verso piazza_grande sta su alto, "
                                                   "varchi.json lo vuole a basso"):
            G.genera(sorgenti_con("via_dei_consoli.area", scambia), PALETTE)

    def test_negativa_lato_cambiato_in_varchi_json(self):
        """(b) Il lato si legge da varchi.json: se cambia li', la griglia non torna piu'."""
        mondo = copy.deepcopy(self.mondo)
        for v in mondo["varchi"]["SANT_ANDREA"]:
            v["lato"] = "basso"
        with self.assertRaisesRegex(G.ErroreMondo, "sta su alto, varchi.json lo vuole a basso"):
            G.genera(G.sorgenti_del_repo(), PALETTE, mondo)

    def test_negativa_varco_lontano_dal_bordo(self):
        """(b) Il varco di Sant'Andrea spostato dentro la griglia, su nessun bordo."""
        def sposta(testo):
            testo = togli_varco("A")(testo)
            return cambia_griglia(testo, 12, 31, "A")
        with self.assertRaisesRegex(G.ErroreMondo, "sta su nessun bordo"):
            G.genera(sorgenti_con("sant_andrea.area", sposta), PALETTE)

    def test_negativa_ingresso_senza_dungeon_in_grafo_json(self):
        mondo = copy.deepcopy(self.mondo)
        for a in mondo["grafo"]["aree"]:
            a.pop("dungeon", None)
        with self.assertRaisesRegex(G.ErroreMondo, "ingresso a gola_bottaccione"):
            G.genera(G.sorgenti_del_repo(), PALETTE, mondo)

    def test_negativa_quota_nel_file_area(self):
        """La quota sta solo in grafo.json: un file .area che la ridichiara e' rifiutato."""
        sorgenti = sorgenti_con("san_pietro.area", lambda t: t.replace("dimensioni", "quota 5\ndimensioni"))
        with self.assertRaisesRegex(G.ErroreMondo, "riga 'quota' sconosciuta"):
            G.genera(sorgenti, PALETTE)

    def test_negativa_varco_murato(self):
        """Il varco G di San Martino (verso il Teatro) chiuso dal muro: non si raggiunge."""
        with self.assertRaisesRegex(G.ErroreMondo, "il varco 'G' non si raggiunge"):
            G.genera(sorgenti_con("san_martino.area", mura_attorno("G")), PALETTE)

    def test_negativa_spawn_iniziale_chiuso(self):
        """Ogni varco si raggiunge da ogni spawn, anche dallo spawn 0 che non e' un arrivo."""
        def chiudi(testo):
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    if dx or dy:
                        testo = cambia_griglia(testo, 16 + dy, 19 + dx, "#")
            return testo
        with self.assertRaisesRegex(G.ErroreMondo, "non si raggiunge camminando dallo spawn 0"):
            G.genera(sorgenti_con("largo_bargello.area", chiudi), PALETTE)

    def test_negativa_varco_senza_uscita(self):
        sorgenti = sorgenti_con("san_martino.area", lambda t: t.replace("uscita G teatro_romano 4\n", ""))
        with self.assertRaisesRegex(G.ErroreMondo, "varco 'G' nella griglia senza riga 'uscita'"):
            G.genera(sorgenti, PALETTE)

    def test_negativa_uscita_senza_varco(self):
        """Il difetto del prototipo: San Martino dichiarava il varco verso il Teatro e non lo aveva."""
        with self.assertRaisesRegex(G.ErroreMondo, "uscita 'G' che non e' nella griglia"):
            G.genera(sorgenti_con("san_martino.area", togli_varco("G")), PALETTE)

    def test_negativa_area_mancante(self):
        """Senza il Monte Ingino l'anello si spezza: grafo.json ha un'area senza file."""
        sorgenti = [(n, t) for n, t in G.sorgenti_del_repo() if not n.endswith("monte_ingino.area")]
        with self.assertRaisesRegex(G.ErroreMondo, "l'area monte_ingino di grafo.json non ha un file .area"):
            G.genera(sorgenti, PALETTE)

    def test_negativa_carattere_sconosciuto(self):
        sorgenti = sorgenti_con("sant_andrea.area", lambda t: cambia_griglia(t, 5, 5, "?"))
        with self.assertRaisesRegex(G.ErroreMondo, "carattere '\\?' sconosciuto"):
            G.genera(sorgenti, PALETTE)

    def test_negativa_spawn_nel_muro(self):
        sorgenti = sorgenti_con("teatro_romano.area", lambda t: t.replace("spawn 1 54 31", "spawn 1 0 0"))
        with self.assertRaisesRegex(G.ErroreMondo, "non e' su una cella calpestabile"):
            G.genera(sorgenti, PALETTE)

    def test_scale_laterali_vicine_a_piazza_grande(self):
        """Le scale da Quaranta Martiri sbucano nelle due vie poco prima di Piazza Grande: il varco
        e il suo spawn stanno entro il vicino_a dichiarato dal varco verso la piazza."""
        consoli = self.aree["via_dei_consoli"]
        self.assertEqual(consoli["vicino"]["G"][:2], ("B", 16))
        self.assertLessEqual(G.distanza_dal_varco(consoli, consoli["spawn"][3], "B"), 16)
        settembre = self.aree["via_xx_settembre"]
        self.assertEqual({k: v[:2] for k, v in settembre["vicino"].items()}, {"E": ("A", 16), "G": ("A", 20)})

    def test_negativa_scala_laterale_lontana(self):
        sorgenti = sorgenti_con("via_dei_consoli.area", lambda t: t.replace("vicino_a B 16", "vicino_a B 2"))
        with self.assertRaisesRegex(G.ErroreMondo, "il varco 'G' e' a \\d+ tile dal varco 'B', ne vuole al massimo 2"):
            G.genera(sorgenti, PALETTE)

    def test_negativa_spawn_della_scala_laterale_lontano(self):
        """Il varco resta in cima alla via, ma chi sale da Quaranta Martiri comparirebbe a meta' via."""
        sorgenti = sorgenti_con("via_xx_settembre.area", lambda t: re.sub(r"spawn 3 \d+ \d+", "spawn 3 16 40", t))
        with self.assertRaisesRegex(G.ErroreMondo, "lo spawn d'arrivo da 'E' e' a \\d+ tile dal varco 'A'"):
            G.genera(sorgenti, PALETTE)

    def test_negativa_vicino_a_un_varco_che_non_c_e(self):
        sorgenti = sorgenti_con("via_dei_consoli.area", lambda t: t.replace("vicino_a B 16", "vicino_a Z 16"))
        with self.assertRaisesRegex(G.ErroreMondo, "'G' vicino_a 'Z', ma 'Z' non e' un'uscita"):
            G.genera(sorgenti, PALETTE)


def griglie_e_mappe(header):
    """Da include/mondo.h: {area: (griglia, mappa)} come liste di interi, quelle che usa la ROM."""
    out = {}
    for tipo, nome, corpo in re.findall(r"inline constexpr uint8_t (GRIGLIA|MAPPA)_(\w+)\[\d+\] = \{([^}]*)\}", header):
        out.setdefault(nome, {})[tipo] = [int(v) for v in corpo.replace("\n", " ").split(",") if v.strip()]
    return {k: (v["GRIGLIA"], v["MAPPA"]) for k, v in out.items()}


TILE_CALPESTABILI = {"SUOLO", "STRADA", "SCALINATA", "PORTONE", "VARCO", "INGRESSO"}


def errori_fondale(griglia, mappa):
    """Sotto ogni cella calpestabile (o varco) un tile di suolo, selciato, scala, portone o varco."""
    prima_solida = list(G.CELLE).index("F")
    nomi = [n for n, _ in G.TILE_FONDALI]
    return [(i, nomi[t]) for i, (c, t) in enumerate(zip(griglia, mappa))
            if (c < prima_solida or c >= G.PRIMO_VARCO) and nomi[t] not in TILE_CALPESTABILI]


class FondaleControGriglia(unittest.TestCase):
    """La mappa BG generata e la griglia di collisione dicono la stessa cosa: dove si cammina non si
    vede mai un tetto o un muro. Si controllano gli array veri di include/mondo.h."""

    def setUp(self):
        with open(G.USCITA, encoding="utf-8") as f:
            self.aree = griglie_e_mappe(f.read())

    def test_quattordici_coppie(self):
        self.assertEqual(len(self.aree), 14)
        for nome, (griglia, mappa) in self.aree.items():
            self.assertEqual(len(griglia), len(mappa), nome)

    def test_dove_si_cammina_mai_tetto_ne_muro(self):
        for nome, (griglia, mappa) in self.aree.items():
            self.assertEqual(errori_fondale(griglia, mappa), [], nome)

    def test_negativa_tetto_sotto_una_cella_calpestabile(self):
        griglia, mappa = self.aree["VIA_DEI_CONSOLI"]
        i = griglia.index(list(G.CELLE).index(","))
        mappa = list(mappa)
        mappa[i] = G.INDICE_TILE["TETTO"]
        self.assertEqual(errori_fondale(griglia, mappa), [(i, "TETTO")])

    def test_selciato_non_in_cotto(self):
        """Il selciato e' di pietra: con i colori dei coppi (6-9) si confonderebbe con i tetti."""
        cotto = {6, 7, 8, 9}
        self.assertFalse({v for r in G._tile(G.tile_strada) for v in r} & cotto)
        self.assertTrue({v for r in G._tile(G.tile_tetto) for v in r} & cotto)

    def test_negativa_selciato_in_cotto_preso(self):
        """Il selciato del primo giro (cotto a spina di pesce) viene riconosciuto come cotto."""
        def vecchio(x, y):
            blocco = ((x // 4) + (y // 4)) % 2
            posizione = (x % 4 if blocco else y % 4)
            return [9, 8, 8, 7][posizione] if (x + y) % 4 != 3 else 6
        self.assertTrue({v for r in G._tile(vecchio) for v in r} & {6, 7, 8, 9})


class Fondali(unittest.TestCase):

    def test_tile_a_16_colori(self):
        for nome, funzione in G.TILE_FONDALI:
            for riga in G._tile(funzione):
                for v in riga:
                    self.assertIn(v, range(16), nome)

    def test_palette_dalla_guida(self):
        """Ogni colore dei fondali e' un colore della palette di stile."""
        tutti = {c for r in PALETTE["rampe"] for c in r["giorno"]}
        for rif in G.PALETTE_FONDALI + G.PALETTE_GIOCATORE:
            self.assertIn(S.colore(PALETTE, rif), tutti, rif)

    def test_muro_davanti_a_suolo_si_vede_di_fronte(self):
        g = ["##", ".."]
        self.assertEqual(G.tile_per_cella(g, 0, 0), G.INDICE_TILE["MURO_FRONTE"])
        self.assertEqual(G.tile_per_cella(["##", "##"], 0, 0), G.INDICE_TILE["TETTO"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
