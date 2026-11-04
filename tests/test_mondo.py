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


def cella_che(nome, buona):
    """Una cella calpestabile dell'area finale (edifici e dislivello applicati) per cui buona(a, x, y)."""
    a = area_con_dislivello(nome)
    for y, r in enumerate(a["griglia"]):
        for x, c in enumerate(r):
            if c in ".," and buona(a, x, y):
                return x, y
    raise AssertionError(f"nessuna cella adatta in {nome}")


def con_spawn(numero, xy):
    return lambda t: re.sub(r"\nspawn %d \d+ \d+" % numero, "\nspawn %d %d %d" % (numero, xy[0], xy[1]), t)


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

    def test_diciannove_aree(self):
        """Le 14 dell'anello e dei dintorni, l'interno della Basilica e le 4 stanze della gola."""
        self.assertEqual(len(self.aree), 19)

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

    def test_bottaccione_porta_nella_gola(self):
        """Dal Bottaccione si risale la gola: il varco G porta alla prima stanza del dungeon."""
        self.assertIn(("G", "gola_striscia"), [(u[0], u[1]) for u in self.aree["bottaccione"]["uscite"]])

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
        """Il Bargello spostato sopra il varco A del Largo."""
        a, posati, _ = area_finale("largo_bargello")
        x0, y0, _, _ = posati["bargello"]
        ax, ay = min(G.celle_varco(a, "A"))
        vecchio = a["sposta"].get("bargello", (0, 0))
        nuovo = (vecchio[0] + ax - x0, vecchio[1] + ay - y0)

        def sposta(t):
            t = re.sub(r"\nsposta bargello -?\d+ -?\d+", "", t)
            return t.replace("\nfattore", "\nsposta bargello %d %d\nfattore" % nuovo)
        with self.assertRaisesRegex(G.ErroreMondo, "l'edificio bargello copre il varco 'A'"):
            G.genera(sorgenti_con("largo_bargello.area", sposta), PALETTE)

    def test_negativa_sposta_un_monumento_che_non_e_un_edificio(self):
        sorgenti = sorgenti_con("largo_bargello.area", lambda t: t.replace("fattore", "sposta fontana_matti 1 1\nfattore"))
        with self.assertRaisesRegex(G.ErroreMondo, "fontana_matti non e' un edificio di quest'area"):
            G.genera(sorgenti, PALETTE)

    def test_tracciati_e_spazi_aperti_calpestabili(self):
        """Via dei Consoli e' un tracciato, il ponte di San Martino uno spazio aperto: niente blocchi. In via
        dei Consoli c'e' solo il banco di Montano (storia v2), addossato alle case e non sulla via."""
        a, posati, _ = area_finale("via_dei_consoli")
        self.assertEqual(set(posati), {"banco_montano"})
        x0, y0, w, h = posati["banco_montano"]
        sorgente = next(G.leggi_area(n, t) for n, t in G.sorgenti_del_repo() if n.endswith("via_dei_consoli.area"))
        self.assertTrue(all(sorgente["griglia"][y][x] == "#" for y in range(y0, y0 + h) for x in range(x0, x0 + w)))
        _, posati, _ = area_finale("san_martino")
        self.assertNotIn("ponte_san_martino", posati)

    def test_negativa_ponte_come_edificio(self):
        """Prova negativa: senza la voce in SPAZI_APERTI il ponte diventa un blocco (o, se non ha
        posto, il generatore lo rifiuta: in tutti e due i casi non e' piu' strada)."""
        vecchio = dict(G.SPAZI_APERTI)
        try:
            del G.SPAZI_APERTI["ponte_san_martino"]
            try:
                _, posati, _ = area_finale("san_martino")
                self.assertIn("ponte_san_martino", posati)
            except G.ErroreMondo as e:
                self.assertIn("ponte_san_martino", str(e))
        finally:
            G.SPAZI_APERTI.clear()
            G.SPAZI_APERTI.update(vecchio)

    def test_ogni_varco_sul_lato_di_varchi_json(self):
        for a in self.aree.values():
            for lettera, dest, _, _ in a["uscite"]:
                if dest in G.DUNGEON:
                    continue
                atteso = [v["lato"] for v in self.mondo["varchi"][a["id"].upper()] if v["verso"] == dest.upper()]
                if atteso == ["dentro"]:
                    # il portale: il varco sta sul portone dell'edificio, non sul bordo
                    self.assertIn(lettera, a.get("ingressi", {}), f"{a['id']} -> {dest}")
                    continue
                self.assertEqual(G.lati_del_varco(a, lettera), set(atteso), f"{a['id']} -> {dest}")

    def test_spawn_lontani_dalla_propria_uscita(self):
        for a in self.aree.values():
            for lettera, dest, spawn, _ in a["uscite"]:
                if dest in G.DUNGEON or lettera in a.get("ingressi", {}):
                    continue  # il portale c'e' solo con gli edifici posati: lo prova LaBasilica
                self.assertGreaterEqual(G.distanza_dal_varco(a, a["spawn"][spawn], lettera),
                                        G.DISTANZA_MIN_SPAWN_USCITA, f"{a['id']} spawn {spawn}")

    def test_quote_da_grafo_json(self):
        """La quota viene da grafo.json: via dei Consoli sale da 27 a 67 m."""
        a = self.aree["via_dei_consoli"]
        with open(G.USCITA, encoding="utf-8") as f:
            header = f.read()
        self.assertRegex(header, r"GRIGLIA_VIA_DEI_CONSOLI, MAPPA_VIA_DEI_CONSOLI, %d, %d,\s+FONDALE_VIA_DEI_CONSOLI, "
                                 r"\d+, \d+, false, TILE_VIA_DEI_CONSOLI, \d+, 27, 67," % (a["larghezza"], a["altezza"]))

    def test_negativa_spawn_a_due_tile_da_un_altro_varco(self):
        """Uno spawn d'arrivo, lontano dalla sua uscita, spostato a 2 tile da un altro varco."""
        for nome, a0 in sorted(self.aree.items()):
            uscite = [u for u in a0["uscite"] if u[2] is not None]
            for propria, _, numero, _ in uscite:
                altre = [u[0] for u in a0["uscite"] if u[0] != propria and u[0] not in a0.get("ingressi", {})]
                try:
                    xy = cella_che(nome, lambda a, x, y: G.distanza_dal_varco(a, (x, y), propria) >= 6
                                   and min(G.distanza_dal_varco(a, (x, y), l) for l in altre) == 2)
                except AssertionError:
                    continue
                with self.assertRaisesRegex(G.ErroreMondo, "a 2 tile da un varco"):
                    G.genera(sorgenti_con(nome + ".area", con_spawn(numero, xy)), PALETTE)
                return
        self.fail("nessuna area adatta alla prova")

    def test_negativa_spawn_vicino_alla_propria_uscita(self):
        """(c) L'arrivo da via dei Consoli a 5 tile dal varco B, da cui si entra."""
        xy = cella_che("largo_bargello", lambda a, x, y: G.distanza_dal_varco(a, (x, y), "B") == 5
                       and G.distanza_dal_varco(a, (x, y), "A") >= 3 and G.distanza_dal_varco(a, (x, y), "E") >= 3)
        with self.assertRaisesRegex(G.ErroreMondo, "a 5 tile dalla sua uscita 'B', ne servono almeno 6"):
            G.genera(sorgenti_con("largo_bargello.area", con_spawn(1, xy)), PALETTE)

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

    def test_negativa_stanza_della_gola_senza_arco(self):
        """Una stanza della gola che porta al Condotto senza l'arco in grafo.json e' rifiutata."""
        mondo = copy.deepcopy(self.mondo)
        mondo["grafo"]["archi"] = [e for e in mondo["grafo"]["archi"] if (e["da"], e["a"]) != ("GOLA_ARCO", "CONDOTTO")]
        with self.assertRaisesRegex(G.ErroreMondo, "non ha l'arco GOLA_ARCO-CONDOTTO|non ha l'arco"):
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
        nome = next(n for n, a in sorted(self.aree.items()) if "piazza" not in a and all(
            max(abs(x - a["spawn"][0][0]), abs(y - a["spawn"][0][1])) > 2 for s, (x, y) in a["spawn"].items() if s))
        sx, sy = self.aree[nome]["spawn"][0]

        def chiudi(testo):
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    if dx or dy:
                        testo = cambia_griglia(testo, sy + dy, sx + dx, "#")
            return testo
        with self.assertRaisesRegex(G.ErroreMondo, "non si raggiunge camminando dallo spawn 0"):
            G.genera(sorgenti_con(nome + ".area", chiudi), PALETTE)

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
        with self.assertRaisesRegex(G.ErroreMondo, "non e' su una cella calpestabile"):
            G.genera(sorgenti_con("teatro_romano.area", con_spawn(1, (0, 0))), PALETTE)

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
        xy = cella_che("via_xx_settembre", lambda a, x, y: G.distanza_dal_varco(a, (x, y), "A") > 20
                       and all(G.distanza_dal_varco(a, (x, y), l) >= 6 for l in "BEG"))
        with self.assertRaisesRegex(G.ErroreMondo, "lo spawn d'arrivo da 'E' e' a \\d+ tile dal varco 'A'"):
            G.genera(sorgenti_con("via_xx_settembre.area", con_spawn(3, xy)), PALETTE)

    def test_negativa_vicino_a_un_varco_che_non_c_e(self):
        sorgenti = sorgenti_con("via_dei_consoli.area", lambda t: t.replace("vicino_a B 16", "vicino_a Z 16"))
        with self.assertRaisesRegex(G.ErroreMondo, "'G' vicino_a 'Z', ma 'Z' non e' un'uscita"):
            G.genera(sorgenti, PALETTE)


def area_con_dislivello(nome, mondo=None, modifica=None):
    """L'area del repo con edifici e dislivello applicati (modifica: testo -> testo del file .area)."""
    mondo = mondo or G.mondo_del_repo()
    testo = dict(G.sorgenti_del_repo())["mondo/aree/%s.area" % nome]
    a = G.leggi_area(nome, modifica(testo) if modifica else testo)
    G.posa_edifici(a, mondo["monumenti"])
    G.applica_dislivello(a, mondo["grafo"])
    return a


def celle(a, carattere):
    return sum(r.count(carattere) for r in a["griglia"])


class Dislivello(unittest.TestCase):
    """Il dislivello in tre modi: scale ai varchi, gradoni, belvederi. Tutto da quote e lati a monte."""

    def test_la_salita_va_in_basso_a_destra(self):
        for n, t in G.sorgenti_del_repo():
            self.assertIn(G.leggi_area(n, t)["monte"], ("basso", "destra"), n)

    def test_negativa_lato_a_monte_in_alto(self):
        sorgenti = sorgenti_con("san_pietro.area", lambda t: t.replace("monte basso", "monte alto"))
        with self.assertRaisesRegex(G.ErroreMondo, "lato a monte 'alto': la salita va verso nord-est"):
            G.genera(sorgenti, PALETTE)

    def test_belvederi_delle_aree_alte(self):
        """Piazza Grande, Duomo, Basilica e Monte Ingino hanno il parapetto sul bordo a valle."""
        for nome in ("piazza_grande", "duomo_ducale", "basilica", "monte_ingino"):
            a = area_con_dislivello(nome)
            self.assertTrue(a["belvedere"], nome)
            self.assertGreater(celle(a, "="), 0, nome)

    def test_negativa_belvedere_sul_lato_a_monte(self):
        with self.assertRaisesRegex(G.ErroreMondo, "belvedere sul lato a monte \\(basso\\)"):
            area_con_dislivello("piazza_grande", modifica=lambda t: t.replace("belvedere sinistra", "belvedere basso"))

    def test_negativa_belvedere_in_un_area_bassa(self):
        with self.assertRaisesRegex(G.ErroreMondo, "belvedere a 0 m: un'area sotto 60 m"):
            area_con_dislivello("piazza_quaranta_martiri",
                                modifica=lambda t: t.replace("monte basso", "monte basso\nbelvedere alto"))

    def test_gradoni_dalla_quota(self):
        """Via dei Consoli sale da 27 a 67 m: due gradoni da 15 m, con muro e scala di passaggio.
        Piazza Grande e' in piano: nessun gradone."""
        a = area_con_dislivello("via_dei_consoli")
        self.assertEqual(len(a["gradoni"]), 2)
        for y in a["gradoni"]:
            self.assertIn("S", a["griglia"][y])
        self.assertEqual(area_con_dislivello("piazza_grande")["gradoni"], [])
        # dove la strada e' larga, il gradone e' muro di contenimento con la scala in mezzo
        monte = area_con_dislivello("monte_ingino")
        colonne = ["".join(r[x] for r in monte["griglia"]) for x in monte["gradoni"]]
        self.assertTrue(all("M" in c and "S" in c for c in colonne))

    def test_negativa_quota_piatta_niente_gradoni(self):
        """La quota decide: con via dei Consoli in piano i gradoni spariscono."""
        mondo = copy.deepcopy(G.mondo_del_repo())
        for x in mondo["grafo"]["aree"]:
            if x["id"] == "VIA_DEI_CONSOLI":
                x["quota_m"] = [47, 47]
        a = area_con_dislivello("via_dei_consoli", mondo)
        self.assertEqual((a["gradoni"], celle(a, "M")), ([], 0))

    def test_ombra_a_valle_del_gradone(self):
        """Un'area che sale verso destra: l'ombra del gradone cade sul suolo a sinistra. (Monte Ingino,
        l'unica area "monte destra", ora sale con i tornanti degli stradoni e non ha gradoni.)"""
        self.assertEqual(area_con_dislivello("monte_ingino")["monte"], "destra")
        g, x, y = ["...", ".M.", "..."], 1, 1
        valle = G.tile_per_cella(g, x - 1, y, False, "destra")
        monte = G.tile_per_cella(g, x + 1, y, False, "destra")
        self.assertIn(valle, (G.INDICE_TILE["SUOLO_OMBRA"], G.INDICE_TILE["STRADA_OMBRA"]))
        self.assertIn(monte, (G.INDICE_TILE["SUOLO"], G.INDICE_TILE["STRADA"]))

    def test_scale_ai_varchi_fra_quote_diverse(self):
        """Quaranta Martiri (0 m) e via dei Consoli (27-67 m): scala davanti al varco G della via;
        verso il Largo del Bargello (27 m) la via e' allo stesso livello e non c'e' scala."""
        a = area_con_dislivello("via_dei_consoli")
        g = a["griglia"]
        interne = [(x, y) for x, y in G.celle_varco(a, "G") if g[y][x + 1] != "G"]
        self.assertTrue(interne)
        for x, y in interne:
            self.assertEqual(g[y][x + 1: x + 1 + G.PROFONDITA_SCALE], "S" * G.PROFONDITA_SCALE)
        for x, y in G.celle_varco(a, "A"):
            if y == 1:
                self.assertNotEqual(g[y + 1][x], "S")

    def test_negativa_stessa_quota_niente_scala(self):
        mondo = copy.deepcopy(G.mondo_del_repo())
        for x in mondo["grafo"]["aree"]:
            if x["id"] == "PIAZZA_QUARANTA_MARTIRI":
                x["quota_m"] = [27, 27]
        a = area_con_dislivello("via_dei_consoli", mondo)
        g = a["griglia"]
        interne = [(x, y) for x, y in G.celle_varco(a, "G") if g[y][x + 1] != "G"]
        self.assertTrue(interne)
        for x, y in interne:
            self.assertNotEqual(g[y][x + 1], "S")

    def test_tile_unici_sotto_512(self):
        with open(G.USCITA, encoding="utf-8") as f:
            aree = griglie_e_mappe(f.read())
        picco = max(len(set(mappa)) for _, mappa in aree.values())
        self.assertLessEqual(picco, 512)
        self.assertLessEqual(len(G.TILE_FONDALI), 512)


def griglie_e_mappe(header):
    """Da include/mondo.h: {area: (griglia, mappa)} come liste di interi, quelle che usa la ROM."""
    out = {}
    for tipo, nome, corpo in re.findall(r"inline constexpr uint8_t (GRIGLIA|MAPPA)_(\w+)\[\d+\] = \{([^}]*)\}", header):
        out.setdefault(nome, {})[tipo] = [int(v) for v in corpo.replace("\n", " ").split(",") if v.strip()]
    return {k: (v["GRIGLIA"], v["MAPPA"]) for k, v in out.items()}


TILE_CALPESTABILI = {"SUOLO", "STRADA", "SCALINATA", "PORTONE", "VARCO", "INGRESSO", "SUOLO_OMBRA",
                     "STRADA_OMBRA", "LASTRICO", "LASTRICO_2", "LASTRICO_3", "CORSO", "VIALETTO", "ARCO", "PRATO",
                     "BRECCIA", "BRECCIA_2", "BRECCIA_SOLCO",
                     # la gola (T2): la via di ghiaia e terra, le sponde d'erba, la nebbia, il ponticello
                     "GHIAIA", "GHIAIA_2", "TERRA", "ERBA", "ERBA_2", "MIASMA", "PONTE", "PONTE_SPONDA",
                     "PONTE_SPONDA_GIU", "ARCO_GOLA", "ARCO_GOLA_S", "ARCO_GOLA_D"}


def errori_fondale(griglia, mappa):
    """Sotto ogni cella calpestabile (o varco) un tile di suolo, selciato, scala, portone o varco."""
    prima_solida = list(G.CELLE).index("F")
    nomi = [n for n, _ in G.TILE_FONDALI]
    return [(i, nomi[t]) for i, (c, t) in enumerate(zip(griglia, mappa))
            if (c < prima_solida or c >= G.PRIMO_VARCO) and nomi[t] not in TILE_CALPESTABILI]


class Proporzioni(unittest.TestCase):
    """Vie e piazze dalle misure muro a muro di mondo/fonti/misure_osm.json."""

    def test_vie_larghe_quanto_la_misura(self):
        mondo = G.mondo_del_repo()
        for nome, attesa in (("via_dei_consoli", 4), ("via_xx_settembre", 5), ("bottaccione", 6),
                             ("sant_agostino", 12), ("duomo_ducale", 5)):
            a = area_con_dislivello(nome)
            misura = mondo["misure"]["vie"][a["via"][0]]
            self.assertEqual(G.larghezza_via_tile(misura), attesa, nome)
            righe = sorted(G.larghezze_lungo_l_asse(a))
            self.assertLessEqual(righe[len(righe) // 2], attesa * a.get("tolleranza_via", G.TOLLERANZA_VIA), nome)

    def test_negativa_via_troppo_larga(self):
        """Via dei Consoli allargata a tutta la griglia, come al giro scorso: rifiutata."""
        def allarga(t):
            return griglia_mappata(t, lambda g: [[c if c in G.VARCHI or x in (0, len(r) - 1) else ","
                                                  for x, c in enumerate(r)] for r in g])
        with self.assertRaisesRegex(G.ErroreMondo, "Via dei Consoli e' larga \\d+ tile sulla griglia, la misura dice 4"):
            G.genera(sorgenti_con("via_dei_consoli.area", allarga), PALETTE)

    def test_negativa_misura_piu_stretta(self):
        """Se il censimento dicesse 3 m, la via di 4 tile sarebbe troppo larga: la misura si propaga."""
        mondo = copy.deepcopy(G.mondo_del_repo())
        mondo["misure"]["vie"]["Via dei Consoli"]["larghezza_mediana_m"] = 3.0
        with self.assertRaisesRegex(G.ErroreMondo, "la misura dice 2"):
            G.genera(G.sorgenti_del_repo(), PALETTE, mondo)

    def test_negativa_via_senza_misura(self):
        sorgenti = sorgenti_con("via_dei_consoli.area", lambda t: t.replace("via Via dei Consoli", "via Via Galeotti"))
        with self.assertRaisesRegex(G.ErroreMondo, "la via 'Via Galeotti' non ha una larghezza misurata"):
            G.genera(sorgenti, PALETTE)

    def test_tolleranza_solo_nel_sud_est(self):
        """Tolleranza piu' larga solo dove OSM e' incompleto, e mai oltre il doppio."""
        for nome, a in self.aree_lette().items():
            if "tolleranza_via" in a:
                self.assertIn(nome, ("via_xx_settembre", "duomo_ducale", "sant_andrea", "san_pietro"))

    def test_negativa_tolleranza_oltre_il_doppio(self):
        sorgenti = sorgenti_con("via_xx_settembre.area", lambda t: t.replace("tolleranza_via 2.0", "tolleranza_via 2.5"))
        with self.assertRaisesRegex(G.ErroreMondo, "tolleranza_via 2.5 fuori"):
            G.genera(sorgenti, PALETTE)

    def test_strettoia(self):
        a = area_con_dislivello("via_dei_consoli")
        self.assertEqual(min(G.larghezze_lungo_l_asse(a)), 2)

    def test_negativa_strettoia_che_non_c_e(self):
        sorgenti = sorgenti_con("via_dei_consoli.area", lambda t: t.replace("strettoia 2", "strettoia 1"))
        with self.assertRaisesRegex(G.ErroreMondo, "la strettoia di 1 tile non c'e'"):
            G.genera(sorgenti, PALETTE)

    def test_piazze_in_scala(self):
        mondo = G.mondo_del_repo()
        attese = {"largo_bargello": (13, 9), "san_pietro": (26, 25), "sant_andrea": (4, 15)}
        for nome, wh in attese.items():
            a = self.aree_lette()[nome]
            self.assertNotIn("fattore_piazza", a, nome)
            self.assertEqual(G.misure_piazza_tile(mondo["misure"]["piazze"][a["piazza"][0]]), wh, nome)

    def test_piazze_grandi_a_misura_vera(self):
        """Piazza Grande (51x27, in fila con Consoli e Pretorio), Piazza 40 Martiri (120x49) e Piazza
        Giordano Bruno (21x15) a misura vera, senza fattore, in aree oltre i 64 tile."""
        mondo = G.mondo_del_repo()
        attese = {"piazza_grande": (27, 51), "piazza_quaranta_martiri": (120, 49), "san_martino": (21, 15)}
        for nome, wh in attese.items():
            a = self.aree_lette()[nome]
            self.assertNotIn("fattore_piazza", a, nome)
            self.assertEqual(G.misure_piazza_tile(mondo["misure"]["piazze"][a["piazza"][0]]), wh, nome)
            self.assertTrue(G.grande(a), nome)
        _, posati, _ = area_finale("piazza_grande")
        self.assertLess(posati["consoli"][1], self.aree_lette()["piazza_grande"]["riferimento"][1] - 25,
                        "i Consoli stanno in cima alla piazza, in fila")

    def test_negativa_piazza_fuori_misura_senza_fattore(self):
        """Una Piazza 40 Martiri di 300 m non sta nemmeno in 128 tile: senza fattore e' rifiutata."""
        mondo = copy.deepcopy(G.mondo_del_repo())
        mondo["misure"]["piazze"]["Piazza 40 Martiri"]["lato_lungo_m"] = 300
        with self.assertRaisesRegex(G.ErroreMondo, "Piazza 40 Martiri in scala e' 200x49 tile e non sta nella "
                                                   "griglia .*: serve un fattore_piazza"):
            G.genera(G.sorgenti_del_repo(), PALETTE, mondo)

    def test_negativa_area_oltre_128_tile(self):
        sorgenti = sorgenti_con("piazza_quaranta_martiri.area",
                                lambda t: re.sub(r"\ndimensioni \d+ \d+", "\ndimensioni 129 128", t))
        with self.assertRaisesRegex(G.ErroreMondo, "area 129x128: il lato massimo e' 128 tile"):
            G.genera(sorgenti, PALETTE)

    def test_negativa_piazza_ingombra(self):
        """Un muro nel Largo del Bargello: la piazza non e' piu' libera nella sua misura."""
        a = self.aree_lette()["largo_bargello"]
        rx, ry = a["riferimento"]
        sorgenti = sorgenti_con("largo_bargello.area", lambda t: cambia_griglia(t, ry + 3, rx + 5, "#"))
        with self.assertRaisesRegex(G.ErroreMondo, "Largo del Bargello \\(13x9 tile intorno al riferimento\\) non e' libera"):
            G.genera(sorgenti, PALETTE)

    def aree_lette(self):
        return {a["id"]: a for a in (G.leggi_area(n, t) for n, t in G.sorgenti_del_repo())}


def fondali(header):
    """Da include/mondo.h: {area: (celle del fondale, larghezza, altezza, grande)}."""
    celle = {n: [int(v) for v in c.replace("\n", " ").split(",") if v.strip()]
             for n, c in re.findall(r"inline constexpr uint16_t FONDALE_(\w+)\[\d+\] = \{([^}]*)\}", header)}
    voci = re.findall(r"FONDALE_(\w+), (\d+), (\d+), (true|false), TILE_", header)
    return {n: (celle[n], int(w), int(h), g == "true") for n, w, h, g in voci}


def errori_disposizione(mappa, larghezza, altezza, fondale, fw, fh, grande):
    """Il fondale in ROM e' la mappa dell'area: riga per riga (big map) o a blocchi 32x32 (VRAM)."""
    err = []
    for y in range(altezza):
        for x in range(larghezza):
            i = y * fw + x if grande else (((y // 32) * (fw // 32)) + (x // 32)) * 1024 + (y % 32) * 32 + (x % 32)
            if fondale[i] != mappa[y * larghezza + x]:
                err.append((x, y))
    return err


class FondaliInRom(unittest.TestCase):
    """Le celle dei fondali che la ROM passa a Butano, contro la mappa dell'area."""

    def setUp(self):
        with open(G.USCITA, encoding="utf-8") as f:
            header = f.read()
        self.fondali = fondali(header)
        self.aree = {a["id"].upper(): a for a in I.aree_finali()}
        # le celle del fondale sono gli indici dei tile dell'area, come li calcola disegna_area
        self.mappe = {n: (None, a["indici"]) for n, a in self.aree.items()}

    def test_ogni_fondale_e_la_sua_mappa(self):
        self.assertEqual(len(self.fondali), 19)
        for nome, (fondale, fw, fh, grande) in self.fondali.items():
            a = self.aree[nome]
            self.assertEqual(grande, a["larghezza"] > 64 or a["altezza"] > 64, nome)
            self.assertEqual(fw % 32 + fh % 32, 0, nome)
            if not grande:
                self.assertIn(fw, (32, 64), nome)
                self.assertIn(fh, (32, 64), nome)
            self.assertEqual(errori_disposizione(self.mappe[nome][1], a["larghezza"], a["altezza"], fondale, fw, fh,
                                                 grande), [], nome)

    def test_negativa_big_map_letta_a_blocchi(self):
        """Piazza Grande e' una big map: se le sue celle fossero a blocchi, non tornerebbero."""
        fondale, fw, fh, grande = self.fondali["PIAZZA_GRANDE"]
        a = self.aree["PIAZZA_GRANDE"]
        self.assertTrue(grande)
        self.assertNotEqual(errori_disposizione(self.mappe["PIAZZA_GRANDE"][1], a["larghezza"], a["altezza"],
                                                fondale, fw, fh, False), [])

    def test_negativa_cella_sbagliata(self):
        fondale, fw, fh, grande = self.fondali["TEATRO_ROMANO"]
        a = self.aree["TEATRO_ROMANO"]
        fondale = list(fondale)
        fondale[33] = (fondale[33] + 1) % len(G.TILE_FONDALI)
        self.assertEqual(len(errori_disposizione(self.mappe["TEATRO_ROMANO"][1], a["larghezza"], a["altezza"],
                                                 fondale, fw, fh, grande)), 1)


class GraficaDeiMonumenti(unittest.TestCase):
    """I monumenti disegnati da tools/pittore_monumenti.py, area per area."""

    @classmethod
    def setUpClass(cls):
        cls.mondo = G.mondo_del_repo()
        cls.aree = {a["id"]: a for a in I.aree_finali()}

    def test_consoli_con_i_suoi_elementi(self):
        a = self.aree["piazza_grande"]
        _, _, elementi = G.disegna_area(a, self.mondo)
        for mid in ("consoli", "pretorio"):
            self.assertEqual(I.PM.elementi_mancanti(mid, elementi[mid]), {}, mid)
        self.assertEqual(elementi["consoli"]["finestra_arco"], 6)

    def test_negativa_consoli_senza_i_6_archi(self):
        """Una facciata del Consoli con 4 finestre invece di 6 e' rifiutata."""
        originale = I.PM.PITTORI["consoli"]

        def quattro_archi(w, h, info):
            t = originale(w, h, info)
            t.elementi["finestra_arco"] = 4
            return t
        I.PM.PITTORI["consoli"] = quattro_archi
        try:
            with self.assertRaisesRegex(G.ErroreMondo, "il monumento consoli non ha finestra_arco \\(4 di 6\\)"):
                G.genera(G.sorgenti_del_repo(), PALETTE)
        finally:
            I.PM.PITTORI["consoli"] = originale

    def test_primo_lotto_completo(self):
        for nome, mid in (("largo_bargello", "bargello"), ("san_martino", "san_domenico"), ("basilica", "basilica"),
                          ("teatro_romano", "teatro_romano")):
            _, _, elementi = G.disegna_area(self.aree[nome], self.mondo)
            self.assertEqual(I.PM.elementi_mancanti(mid, elementi[mid]), {}, mid)
        _, _, elementi = G.disegna_area(self.aree["largo_bargello"], self.mondo)
        self.assertEqual(elementi["fontana_matti"]["vasca"], 1)

    def test_negativa_bargello_senza_porta_del_morto(self):
        self.assertEqual(I.PM.elementi_mancanti("bargello", {"portale": 1}), {"porta_del_morto": 1})

    def test_tetti_diversi_per_ruolo(self):
        self.assertEqual([I.PM.ruolo(n) for n in ("Chiesa di San Francesco", "Porta Romana", "Palazzo Ducale")],
                         ["chiesa", "porta", "palazzo"])
        chiesa = I.PM.generico("x", "Chiesa di Santa Maria", 10, 12, "basso", 0)
        palazzo = I.PM.generico("x", "Palazzo del Capitano", 10, 12, "basso", 1)
        self.assertNotEqual(chiesa.px, palazzo.px)

    def test_budget_dei_tile_per_area(self):
        for nome, a in self.aree.items():
            self.assertLessEqual(len(a["tile"]), G.TILE_MAX_PER_AREA, nome)

    def test_negativa_budget_sforato(self):
        a = self.aree["teatro_romano"]
        troppi = [[[i % 16] * 8 for _ in range(8)] for i in range(G.TILE_MAX_PER_AREA + 1)]
        elementi = G.disegna_area(a, self.mondo)[2]
        with self.assertRaisesRegex(G.ErroreMondo, "513 tile unici, il massimo per un BG e' 512"):
            G.controlla_grafica(a, troppi, elementi)

    def test_colori_nella_palette(self):
        for nome, a in self.aree.items():
            self.assertTrue(all(0 <= v < 16 for t in a["tile"] for r in t for v in r), nome)

    def test_negativa_colore_fuori_palette(self):
        a = self.aree["largo_bargello"]
        tile = [list(r) for r in a["tile"][1]]
        tile[0][0] = 16
        elementi = G.disegna_area(a, self.mondo)[2]
        with self.assertRaisesRegex(G.ErroreMondo, "colore 16 fuori dalla palette"):
            G.controlla_grafica(a, [tile], elementi)

    def test_facciate_non_calpestabili(self):
        """Ogni cella di un edificio e' solida, portone compreso (non e' un varco ne' un punto
        d'interazione)."""
        self.assertTrue(G.CELLE["d"][1])
        for nome, a in self.aree.items():
            self.assertEqual(G.celle_edifici_calpestabili(a), [], nome)

    def test_negativa_facciata_calpestabile(self):
        a = copy.deepcopy(self.aree["piazza_grande"])
        x0, y0, w, h = a["edifici"]["consoli"]
        riga = list(a["griglia"][y0 + h - 1])
        riga[x0 + w // 2] = "."
        a["griglia"][y0 + h - 1] = "".join(riga)
        self.assertEqual(G.celle_edifici_calpestabili(a), [(x0 + w // 2, y0 + h - 1)])

    def test_fontana_solida_e_intorno_calpestabile(self):
        a = self.aree["largo_bargello"]
        g = a["griglia"]
        fontana = {(x, y) for y, r in enumerate(g) for x, c in enumerate(r) if c == "F"}
        self.assertEqual(len(fontana), 9)
        intorno = {(x + dx, y + dy) for x, y in fontana for dx in (-1, 0, 1) for dy in (-1, 0, 1)} - fontana
        self.assertTrue(all(not G.solida(g[y][x]) for x, y in intorno))
        self.assertTrue(all(G.solida(g[y][x]) for x, y in fontana))


class BelvederiECase(unittest.TestCase):
    """Il belvedere si vede (parapetto e citta' bassa oltre), le case non sono tutte uguali, il
    secondo lotto di monumenti ha i suoi elementi."""

    @classmethod
    def setUpClass(cls):
        cls.mondo = G.mondo_del_repo()
        cls.aree = {a["id"]: a for a in I.aree_finali()}

    def test_belvederi_visibili(self):
        for nome in ("piazza_grande", "duomo_ducale", "basilica", "monte_ingino"):
            a = self.aree[nome]
            self.assertGreater(celle(a, "="), 0, nome)
            self.assertGreater(celle(a, "V"), 0, nome)
            self.assertEqual(G.errori_belvedere(a), [], nome)

    def test_piazza_grande_aperta_a_sinistra(self):
        """Il parapetto corre sul lato sinistro della piazza (sud-ovest reale), fra Consoli e Pretorio."""
        a = self.aree["piazza_grande"]
        x0, y0, w, h = G.rettangolo_piazza(a)
        self.assertEqual(a["belvedere"][0][0], "sinistra")
        parapetti = [y for y in range(y0, y0 + h) if a["griglia"][y][x0 - 1] == "="]
        self.assertGreater(len(parapetti), h // 3)

    def test_negativa_tetto_oltre_il_parapetto(self):
        a = copy.deepcopy(self.aree["piazza_grande"])
        y, x = next((y, x) for y, r in enumerate(a["griglia"]) for x, c in enumerate(r) if c == "V")
        a["griglia"][y] = a["griglia"][y][:x] + "#" + a["griglia"][y][x + 1:]
        self.assertIn((x, y), G.errori_belvedere(a))

    def test_citta_bassa_non_calpestabile(self):
        self.assertTrue(G.CELLE["V"][1])

    def test_case_variate(self):
        a = self.aree["piazza_grande"]
        tipi = {G.tetto_della_casa(x, y) for y, r in enumerate(a["griglia"]) for x, c in enumerate(r) if c == "#"}
        self.assertGreaterEqual(len(tipi & {"TETTO", "TETTO_ORIZZONTALE", "TETTO_SCURO", "COMIGNOLO", "CORTILE"}), 4)

    def test_negativa_varianti_per_blocco(self):
        """La variante dipende dal blocco 4x4: dentro un blocco non cambia, fra blocchi si'."""
        self.assertEqual(len({G.variante_tetto(x, y) for x in range(4) for y in range(4)}), 1)
        self.assertGreater(len({G.variante_tetto(x * 4, y * 4) for x in range(4) for y in range(4)}), 2)

    def test_secondo_lotto(self):
        coppie = (("duomo_ducale", "duomo"), ("duomo_ducale", "ducale"), ("piazza_quaranta_martiri", "san_francesco"),
                  ("piazza_quaranta_martiri", "loggia_tiratori"), ("sant_agostino", "sant_agostino"),
                  ("san_pietro", "san_pietro"), ("san_martino", "porta_metauro"), ("sant_agostino", "porta_romana"))
        for nome, mid in coppie:
            _, _, elementi = G.disegna_area(self.aree[nome], self.mondo)
            self.assertEqual(I.PM.elementi_mancanti(mid, elementi[mid]), {}, mid)

    def test_negativa_loggia_con_meno_arcate(self):
        self.assertEqual(I.PM.elementi_mancanti("loggia_tiratori", {"arcata": 5, "ospedale": 1, "fianco": 1}),
                         {"arcata": 6})


class TerzoLotto(unittest.TestCase):
    """Terzo lotto di monumenti, facciate scelte nelle .area, mura, varieta' dei tetti, cartiglio."""

    @classmethod
    def setUpClass(cls):
        cls.mondo = G.mondo_del_repo()
        cls.aree = {a["id"]: a for a in I.aree_finali()}

    def test_terzo_lotto(self):
        coppie = (("sant_andrea", "san_marziale"), ("sant_andrea", "santa_maria_nuova"),
                  ("san_martino", "capitano_popolo"), ("piazza_grande", "ranghiasci"),
                  ("bottaccione", "sant_ambrogio"))
        for nome, mid in coppie:
            _, _, elementi = G.disegna_area(self.aree[nome], self.mondo)
            self.assertEqual(I.PM.elementi_mancanti(mid, elementi[mid]), {}, mid)

    def test_porta_san_pietro_senza_misure_non_disegnata(self):
        self.assertEqual(self.mondo["monumenti"]["porta_san_pietro"]["tipo"], "senza_misura")
        self.assertNotIn("porta_san_pietro", self.aree["san_pietro"]["edifici"])

    def test_negativa_ranghiasci_con_meno_finestre(self):
        self.assertEqual(I.PM.elementi_mancanti("ranghiasci", {"finestra_regolare": 9, "portone": 1}),
                         {"finestra_regolare": 10})

    def test_facciate_scelte(self):
        """Duomo verso la stradina del Ducale (destra, pezzo O), Sant'Agostino a ovest (alto), San Pietro
        verso la piazza (sinistra): scelte dichiarate nelle .area, il censimento non da' il lato."""
        attese = {("duomo_ducale", "duomo"): "destra", ("sant_agostino", "sant_agostino"): "alto",
                  ("san_pietro", "san_pietro"): "sinistra"}
        for (nome, mid), lato in attese.items():
            a = self.aree[nome]
            self.assertIsNone(self.mondo["monumenti"][mid].get("facciata_lato_schermo"))
            self.assertEqual(a["facciata"][mid][0], lato)
            self.assertEqual(G.faccia_di(a, mid, self.mondo["monumenti"]), lato)

    def test_negativa_facciata_contro_il_censimento(self):
        """Il censimento vuole la facciata del Ranghiasci a sinistra: una .area che dice destra e' rifiutata."""
        sorgenti = sorgenti_con("piazza_grande.area", lambda t: t.replace("\nfattore ", "\nfacciata ranghiasci destra\nfattore "))
        with self.assertRaisesRegex(G.ErroreMondo, "facciata di ranghiasci a destra, ma il censimento la vuole a "
                                                   "sinistra: vince il dato"):
            G.genera(sorgenti, PALETTE)

    def test_negativa_facciata_di_un_monumento_altrove(self):
        sorgenti = sorgenti_con("san_pietro.area", lambda t: t.replace("\nfattore ", "\nfacciata duomo basso\nfattore "))
        with self.assertRaisesRegex(G.ErroreMondo, "duomo non e' un edificio di quest'area"):
            G.genera(sorgenti, PALETTE)

    def test_mura_sul_perimetro(self):
        for nome, lati in (("san_martino", ["destra"]), ("sant_agostino", ["basso"]), ("san_pietro", ["sinistra"]),
                           ("teatro_romano", ["destra", "basso"])):
            a = self.aree[nome]
            self.assertEqual(a["mura"], lati, nome)
            lato = lati[0]
            bordo = {"alto": a["griglia"][0], "basso": a["griglia"][-1],
                     "sinistra": "".join(r[0] for r in a["griglia"]),
                     "destra": "".join(r[-1] for r in a["griglia"])}[lato]
            self.assertGreater(bordo.count("W"), len(bordo) // 2, nome)

    def test_negativa_mura_su_un_lato_sconosciuto(self):
        sorgenti = sorgenti_con("san_pietro.area", lambda t: t.replace("mura sinistra", "mura sopra"))
        with self.assertRaisesRegex(G.ErroreMondo, "lato delle mura 'sopra' sconosciuto"):
            G.genera(sorgenti, PALETTE)

    def test_tetti_piu_vari(self):
        a = self.aree["san_martino"]
        tipi = {G.tetto_della_casa(x, y) for y, r in enumerate(a["griglia"]) for x, c in enumerate(r) if c == "#"}
        self.assertGreaterEqual(len(tipi), 7)
        self.assertEqual(G.VARIANTI_TETTO, 6)

    def test_negativa_tetto_di_una_variante_fissa(self):
        """Dentro un blocco della variante a capanna le falde cambiano a meta': luce sopra, ombra sotto."""
        x, y = next((x * 4, y * 4) for x in range(40) for y in range(40) if G.variante_tetto(x * 4, y * 4) == 4)
        self.assertEqual(G.tetto_della_casa(x, y), "TETTO_FALDA_LUCE")
        self.assertEqual(G.tetto_della_casa(x, y + 3), "TETTO_FALDA_OMBRA")
        self.assertNotEqual(G.tetto_della_casa(x, y), G.tetto_della_casa(x, y + 3))

    def test_cartiglio(self):
        """Tre pezzi da 32x16 con i colori della palette, il bordo scuro in alto e in basso."""
        for pezzo in ("sinistro", "centrale", "destro"):
            px = G.pixel_cartiglio(pezzo)
            self.assertEqual((len(px), len(px[0])), (16, 32))
            self.assertTrue(all(0 <= v < 16 for r in px for v in r))
            self.assertEqual(set(px[0]) | set(px[15]), {1})
        self.assertEqual([len(p) for p in G.tile_cartiglio()], [64, 64, 64])
        with open(G.USCITA, encoding="utf-8") as f:
            self.assertIn("inline constexpr bn::tile TILE_CARTIGLIO[3 * TILE_PER_PEZZO_CARTIGLIO]", f.read())

    def test_negativa_cartiglio_senza_bordo(self):
        """Il pezzo centrale non ha le volute: e' diverso dai pezzi di estremita'."""
        self.assertNotEqual(G.pixel_cartiglio("centrale"), G.pixel_cartiglio("sinistro"))
        self.assertNotEqual(G.pixel_cartiglio("sinistro"), G.pixel_cartiglio("destro"))


class OrdineDelleCelle(unittest.TestCase):
    """Il gioco dice solida una cella dal suo indice (mondo::solida, da PRIMA_CELLA_SOLIDA in su): le
    calpestabili devono stare tutte prima della prima solida, o la .area e il gioco non vanno d'accordo
    (il MIASMA a indice 42 bloccava la via dei miasmi, il PONTE il ponticello)."""

    def test_calpestabili_prima_delle_solide(self):
        G.controlla_ordine_celle()
        valori = list(G.CELLE.values())
        prima = [s for _, s in valori].index(True)
        self.assertTrue(all(not s for _, s in valori[:prima]) and all(s for _, s in valori[prima:]))
        with open(G.USCITA, encoding="utf-8") as f:
            self.assertIn(f"inline constexpr int PRIMA_CELLA_SOLIDA = {prima};", f.read())
        for c in "g+":
            self.assertLess(list(G.CELLE).index(c), prima, c)

    def test_negativa_miasma_dopo_le_solide(self):
        """L'ordine di prima di T2 (MIASMA e PONTE in coda) si rifiuta."""
        celle = {k: v for k, v in G.CELLE.items() if k not in "g+"}
        celle["g"], celle["+"] = ("MIASMA", False), ("PONTE", False)
        with self.assertRaises(G.ErroreMondo) as e:
            G.controlla_ordine_celle(celle)
        self.assertIn("MIASMA, PONTE", str(e.exception))


class FondaleControGriglia(unittest.TestCase):
    """La mappa BG generata e la griglia di collisione dicono la stessa cosa: dove si cammina non si
    vede mai un tetto o un muro. Si controllano gli array veri di include/mondo.h."""

    def setUp(self):
        with open(G.USCITA, encoding="utf-8") as f:
            self.aree = griglie_e_mappe(f.read())

    def test_diciannove_coppie(self):
        self.assertEqual(len(self.aree), 19)
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


_spec_ist = importlib.util.spec_from_file_location("istantanee", os.path.join(RADICE, "tools", "istantanee.py"))
I = importlib.util.module_from_spec(_spec_ist)
_spec_ist.loader.exec_module(I)


def celle_senza_colore(celle, colori):
    return sorted(c for c in celle if c not in colori and c not in G.VARCHI)


class ColoriDelleIstantanee(unittest.TestCase):
    """tools/istantanee.py ha un colore per ogni cella del generatore: una cella nuova senza colore
    fermerebbe le griglie PNG."""

    def test_ogni_cella_ha_un_colore(self):
        self.assertEqual(celle_senza_colore(G.CELLE, I.COLORI), [])

    def test_negativa_cella_nuova_senza_colore(self):
        self.assertEqual(celle_senza_colore(list(G.CELLE) + ["9"], I.COLORI), ["9"])


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


class LaCitta(unittest.TestCase):
    """Pezzo J: le piazze composte (dallo spawn si vede qualcosa), le porte della citta' e la cavea."""

    PIAZZE = ("piazza_grande", "piazza_quaranta_martiri", "teatro_romano", "san_pietro")

    @classmethod
    def setUpClass(cls):
        cls.mondo = G.mondo_del_repo()
        cls.aree = {a["id"]: a for a in I.aree_finali()}

    def composta(self, a):
        visti, nudo = G.composizione(a)
        return len(visti) >= 2 and nudo <= 0.60

    def test_dallo_spawn_almeno_due_elementi_e_poco_suolo_nudo(self):
        for nome in self.PIAZZE:
            visti, nudo = G.composizione(self.aree[nome])
            self.assertGreaterEqual(len(visti), 2, (nome, visti))
            self.assertLessEqual(nudo, 0.60, nome)

    def test_negativa_teatro_spogliato(self):
        """Senza cavea, alberi, mura e porta il Teatro dallo spawn e' solo prato: la regola da' rosso."""
        a = copy.deepcopy(self.aree["teatro_romano"])
        a["griglia"] = [re.sub("[RUTWXLP]", "N", r) for r in a["griglia"]]
        a["edifici"] = {}
        self.assertFalse(self.composta(a))

    def test_negativa_piazza_vuota(self):
        a = copy.deepcopy(self.aree["san_pietro"])
        a["griglia"] = [re.sub("[^A-Z#.]|[LKOQC]", ".", r) for r in a["griglia"]]
        a["edifici"] = {}
        self.assertFalse(self.composta(a))

    def test_ogni_uscita_fuori_le_mura_passa_sotto_una_porta(self):
        fuori = {x["id"] for x in self.mondo["grafo"]["aree"] if x.get("fuori_le_mura")}
        archi = [e for e in self.mondo["grafo"]["archi"] if (e["da"] in fuori) != (e["a"] in fuori)]
        self.assertGreaterEqual(len(archi), 6)
        for e in archi:
            for qui in (e["da"], e["a"]):
                a = self.aree.get(qui.lower())
                if a is None:
                    continue  # un'area di un altro lotto (dungeon o atto successivo)
                lettere = dict(G.porte_dell_area(a, self.mondo["grafo"]))
                self.assertTrue(lettere, (qui, e))
                for lettera in lettere:
                    _, piloni, arco = G.geometria_porta(a, lettera)
                    self.assertTrue(all(a["griglia"][y][x] == "J" for x, y in arco), (qui, lettera))
                    self.assertTrue(all(a["griglia"][y][x] == "X" for x, y in piloni), (qui, lettera))
                    self.assertFalse(G.solida("J"), "sotto l'arco si cammina")
                    self.assertEqual(G.errori_porte(a, self.mondo["grafo"]), [], qui)

    def test_negativa_arco_murato(self):
        a = copy.deepcopy(self.aree["teatro_romano"])
        a["griglia"] = [r.replace("J", "#") for r in a["griglia"]]
        self.assertTrue(any("non passa sotto l'arco" in e for e in G.errori_porte(a, self.mondo["grafo"])))

    def test_negativa_porta_senza_torre(self):
        a = copy.deepcopy(self.aree["san_martino"])
        a["griglia"] = [r.replace("X", "#") for r in a["griglia"]]
        self.assertTrue(any("incompleta" in e for e in G.errori_porte(a, self.mondo["grafo"])))

    def test_negativa_uscita_dalle_mura_senza_porta(self):
        grafo = copy.deepcopy(self.mondo["grafo"])
        for e in grafo["archi"]:
            if e.get("porta") == "Porta Castello":
                del e["porta"]
        self.assertTrue(any("senza porta" in e for e in G.errori_cinta(grafo)))

    def facciate_duomo_ducale(self, a):
        """(distanza in tile fra le due facciate, righe in cui si guardano) per Duomo e Ducale."""
        dx, dy, dw, dh = a["edifici"]["duomo"]
        cx, cy, cw, ch = a["edifici"]["ducale"]
        righe = set(range(dy, dy + dh)) & set(range(cy, cy + ch))
        if dx < cx:
            return cx - (dx + dw), righe
        return dx - (cx + cw), righe

    def test_duomo_e_ducale_sulla_stradina(self):
        """Davanti al Duomo non c'e' una piazza: le facciate di Duomo e Ducale si guardano attraverso
        una stradina di al massimo 3 tile, e fra loro c'e' solo la strada."""
        a = self.aree["duomo_ducale"]
        distanza, righe = self.facciate_duomo_ducale(a)
        self.assertLessEqual(distanza, 3)
        self.assertGreaterEqual(len(righe), 10)
        self.assertEqual(G.faccia_di(a, "duomo", self.mondo["monumenti"]), "destra")
        self.assertEqual(G.faccia_di(a, "ducale", self.mondo["monumenti"]), "sinistra")
        dx, _, dw, _ = a["edifici"]["duomo"]
        for y in righe:
            fra = a["griglia"][y][dx + dw:dx + dw + distanza]
            self.assertTrue(all(c in ",.S" for c in fra), (y, fra))
        visti, nudo = G.composizione(a)
        self.assertTrue({"duomo", "ducale"} <= visti)
        self.assertLessEqual(nudo, 0.60)

    def test_negativa_piazzetta_davanti_al_duomo(self):
        """Il Ducale spostato di 3 tile (una piazzetta davanti al Duomo): la stradina e' troppo larga."""
        a = copy.deepcopy(self.aree["duomo_ducale"])
        x, y, w, h = a["edifici"]["ducale"]
        a["edifici"]["ducale"] = (x + 3, y, w, h)
        self.assertGreater(self.facciate_duomo_ducale(a)[0], 3)

    def test_le_piazze_e_i_loro_monumenti(self):
        pg, p40 = self.aree["piazza_grande"], self.aree["piazza_quaranta_martiri"]
        self.assertTrue({"consoli", "pretorio", "ranghiasci"} <= set(pg["edifici"]))
        self.assertGreater(sum(r.count("=") for r in pg["griglia"]), 40, "il parapetto sul quarto lato")
        self.assertTrue({"loggia_tiratori", "santa_maria_laici", "san_francesco"} <= set(p40["edifici"]))
        for c in "YTDZ":
            self.assertGreater(sum(r.count(c) for r in p40["griglia"]), 10, c)
        self.assertTrue(any("O" in r or "Q" in r for r in pg["griglia"]), "un pozzo o i lampioni")

    def test_negativa_quaranta_martiri_senza_giardini(self):
        testo = dict(G.sorgenti_del_repo())["mondo/aree/piazza_quaranta_martiri.area"]
        a = G.leggi_area("piazza_quaranta_martiri", testo.replace(chr(10) + "giardini" + chr(10), chr(10)))
        G.prepara_area(a, self.mondo)
        self.assertEqual(sum(r.count("Y") + r.count("T") for r in a["griglia"]), 0)

    def semicerchio(self, a):
        """Sulla griglia: per ogni riga della cavea l'ultima gradinata sta a sqrt(r^2 - dy^2) dal centro."""
        x0, y0, w, h = a["edifici"]["teatro_romano"]
        cx, cy, r, _ = G.geometria_teatro(x0, y0, w, h)
        scarti = []
        for y in range(y0, y0 + h):
            cavea = [x for x in range(x0, x0 + w) if a["griglia"][y][x] in "RU"]
            atteso = (r * r - (y - cy) ** 2) ** 0.5 if abs(y - cy) <= r else None
            if atteso is None:
                scarti.append(len(cavea))
            else:
                scarti.append(abs((max(cavea) - cx if cavea else 0) - atteso))
        return max(scarti), G.errori_semicerchio(a, (x0, y0, w, h))

    def test_la_cavea_e_un_semicerchio(self):
        scarto, err = self.semicerchio(self.aree["teatro_romano"])
        self.assertLessEqual(scarto, 1.5)
        self.assertEqual(err, [])
        g = self.aree["teatro_romano"]["griglia"]
        self.assertGreater(sum(r.count("R") for r in g), 300, "gradinate concentriche")
        self.assertGreater(sum(r.count("U") for r in g), 40, "anello di arcate")

    def test_negativa_cavea_quadrata(self):
        """Una cavea a rettangolo pieno non e' un semicerchio."""
        a = copy.deepcopy(self.aree["teatro_romano"])
        x0, y0, w, h = a["edifici"]["teatro_romano"]
        g = [list(r) for r in a["griglia"]]
        for y in range(y0, y0 + h):
            for x in range(x0 + 3, x0 + w):
                g[y][x] = "R"
        a["griglia"] = ["".join(r) for r in g]
        scarto, err = self.semicerchio(a)
        self.assertGreater(scarto, 1.5)
        self.assertTrue(err)


_spec_s = importlib.util.spec_from_file_location("disegna_stradoni", os.path.join(RADICE, "tools", "disegna_stradoni.py"))
DS = importlib.util.module_from_spec(_spec_s)
_spec_s.loader.exec_module(DS)


class GliStradoni(unittest.TestCase):
    """Pezzo K: il Monte Ingino come percorso, 9 tratti a zig-zag (Cioti, 2 nov 2026) e le cappellette
    ai tornanti."""

    @classmethod
    def setUpClass(cls):
        cls.mondo = G.mondo_del_repo()
        cls.dati = cls.mondo["stradoni"]
        cls.a = {a["id"]: a for a in I.aree_finali()}["monte_ingino"]

    def area_da(self, dati):
        a = G.leggi_area("monte_ingino", DS.testo(dati))
        G.prepara_area(a, self.mondo)
        return a

    def test_nove_tratti_di_lunghezze_diverse(self):
        tratti = G.tratti_degli_stradoni(self.a)
        self.assertEqual(len(tratti), 9)
        self.assertEqual([t[3] - t[2] + 1 for t in tratti], self.dati["tratti"])
        self.assertEqual(len(set(self.dati["tratti"])), 9, "lunghezze diverse")
        self.assertEqual(G.errori_stradoni(self.a, self.dati), [])

    def test_cappellette_ai_tornanti_3_6_7(self):
        attese = {3: "Cappelletta di Sant'Ubaldo", 6: "Cappelletta di San Giorgio", 7: "Cappelletta di Sant'Antonio"}
        self.assertEqual({c["tornante"]: c["nome"] for c in self.dati["cappellette"]}, attese)
        tornanti = G.tornanti_degli_stradoni(self.a, G.tratti_degli_stradoni(self.a))
        self.assertEqual(len(tornanti), 8)
        trovati = []
        for blocco in G.blocchi(self.a["griglia"], "c"):
            accanto = {(x + dx, y + dy) for x, y in blocco for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))}
            trovati += [n for n, celle in enumerate(tornanti, 1) if accanto & celle]
        self.assertEqual(sorted(trovati), [3, 6, 7])

    def test_negativa_cappelletta_spostata_di_tornante(self):
        """San Giorgio disegnata al 5o tornante invece che al 6o: contro i dati veri e' rosso."""
        spostati = copy.deepcopy(self.dati)
        spostati["cappellette"][1]["tornante"] = 5
        err = G.errori_stradoni(self.area_da(spostati), self.dati)
        self.assertTrue(any("San Giorgio" in e and "tornante 6" in e for e in err), err)

    def test_negativa_otto_tratti(self):
        """Con 8 tratti (il conto di prima) contro i dati di 9: rosso."""
        otto = copy.deepcopy(self.dati)
        otto["tratti"] = otto["tratti"][:8]
        err = G.errori_stradoni(self.area_da(otto), self.dati)
        self.assertTrue(any(e.startswith("tratti") for e in err), err)

    def test_ogni_tornante_si_raggiunge(self):
        tornanti = G.tornanti_degli_stradoni(self.a, G.tratti_degli_stradoni(self.a))
        for s, xy in self.a["spawn"].items():
            visti = G.raggiungibili(self.a, xy)
            for n, celle in enumerate(tornanti, 1):
                self.assertTrue(celle & visti, f"tornante {n} dallo spawn {s}")

    def test_negativa_tratto_franato(self):
        """Il 4o tratto chiuso da una frana: i tornanti dal 4o in poi non si raggiungono dal basso."""
        a = copy.deepcopy(self.a)
        tratti = G.tratti_degli_stradoni(a)
        x0, x1, y0, y1 = tratti[3]
        g = [list(r) for r in a["griglia"]]
        for x in range(x0, x1 + 1):
            g[(y0 + y1) // 2][x] = "k"
        a["griglia"] = ["".join(r) for r in g]
        tornanti = G.tornanti_degli_stradoni(a, tratti)
        visti = G.raggiungibili(a, a["spawn"][1])
        self.assertTrue(tornanti[2] & visti)
        self.assertFalse(tornanti[3] & visti)

    def test_la_griglia_viene_dai_dati(self):
        with open(DS.AREA, encoding="utf-8") as f:
            self.assertEqual(f.read(), DS.testo(self.dati), "eseguire python tools/disegna_stradoni.py --scrivi")

    def test_negativa_dati_cambiati(self):
        altri = copy.deepcopy(self.dati)
        altri["tratti"][0] -= 2
        with open(DS.AREA, encoding="utf-8") as f:
            self.assertNotEqual(f.read(), DS.testo(altri))

    def test_porta_sant_ubaldo_in_fondo_e_basilica_in_cima(self):
        a = self.a
        self.assertEqual(sorted(a["porte"]), ["A", "E"])
        self.assertTrue(all(n == "Porta Sant'Ubaldo" for n, _, _, _ in a["porte"].values()))
        self.assertEqual(G.lati_del_varco(a, "B"), {"destra"})
        tratti = G.tratti_degli_stradoni(a)
        self.assertLess(tratti[0][0], tratti[-1][0], "si sale verso destra")


class LaBasilica(unittest.TestCase):
    """Pezzo K: la Basilica curata e il suo interno, raggiungibile dal portale."""

    @classmethod
    def setUpClass(cls):
        cls.mondo = G.mondo_del_repo()
        cls.aree = {a["id"]: a for a in I.aree_finali()}

    def test_dallo_spawn_almeno_due_elementi(self):
        for nome in ("basilica", "basilica_interno", "monte_ingino"):
            visti, nudo = G.composizione(self.aree[nome])
            self.assertGreaterEqual(len(visti), 2, (nome, visti))
            self.assertLessEqual(nudo, 0.60, nome)

    def test_negativa_interno_spoglio(self):
        a = copy.deepcopy(self.aree["basilica_interno"])
        a["griglia"] = [re.sub("[nae]", "L", r) for r in a["griglia"]]
        self.assertLess(len(G.composizione(a)[0]), 2)

    def test_il_portale_porta_dentro(self):
        b, dentro = self.aree["basilica"], self.aree["basilica_interno"]
        self.assertEqual(b["ingressi"], {"E": "basilica"})
        x0, y0, w, h = b["edifici"]["basilica"]
        portale = G.celle_varco(b, "E")
        self.assertTrue(portale and all(x0 <= x < x0 + w and y == y0 + h - 1 for x, y in portale))
        self.assertGreaterEqual(G.distanza_dal_varco(b, b["spawn"][3], "E"), G.DISTANZA_MIN_SPAWN_USCITA)
        self.assertEqual(G.lati_del_varco(dentro, "A"), {"basso"})
        self.assertGreaterEqual(G.distanza_dal_varco(dentro, dentro["spawn"][1], "A"), G.DISTANZA_MIN_SPAWN_USCITA)

    def test_negativa_portale_senza_riga_ingresso(self):
        sorgenti = sorgenti_con("basilica.area", lambda t: t.replace("ingresso E basilica\n", ""))
        with self.assertRaisesRegex(G.ErroreMondo, "uscita 'E' che non e' nella griglia"):
            G.genera(sorgenti, PALETTE)

    def test_negativa_portale_sul_bordo(self):
        """Un varco "dentro" messo sul bordo dell'area non e' un portale."""
        def sposta(testo):
            testo = testo.replace("ingresso E basilica\n", "")
            return griglia_mappata(testo, lambda g: [r if y < 20 or y > 23 else (["E", "E"] + r[2:])
                                                     for y, r in enumerate(g)])
        with self.assertRaisesRegex(G.ErroreMondo, "e' un portale"):
            G.genera(sorgenti_con("basilica.area", sposta), PALETTE)

    def test_l_interno_navate_altare_ceri(self):
        g = self.aree["basilica_interno"]["griglia"]
        self.assertEqual(len(G.blocchi(g, "a")), 1, "l'altare con l'urna")
        self.assertEqual(len(G.blocchi(g, "e")), 3, "i tre ceri")
        pilastri = G.blocchi(g, "n")
        self.assertTrue(all(len(p) == 4 for p in pilastri), "pilastri 2x2")
        self.assertEqual(len({min(x for x, _ in p) for p in pilastri}), 2, "due file di pilastri: tre navate")
        self.assertGreaterEqual(len(G.blocchi(g, "q")), 12, "le panche in file")
        self.assertGreaterEqual(sum(r.count("w") for r in g), 6, "le vetrate")
        self.assertEqual(len(G.blocchi(g, "l")), 2, "i candelieri")
        y_altare = min(y for y, r in enumerate(g) if "a" in r)
        self.assertTrue(any("S" in g[y_altare + k] for k in (2, 3)), "l'altare e' rialzato sui gradini")
        self.assertTrue(all(len(c) >= 8 for c in G.blocchi(g, "e")), "ceri alti, 2x4")
        a = self.aree["basilica_interno"]
        celle = G.finestra_dello_spawn(a)
        y0 = min(y for _, y in celle)
        self.assertGreaterEqual(y_altare, y0 + 3, "l'altare non finisce sotto il cartiglio")

    def test_negativa_due_ceri(self):
        g = [r.replace("ee", "LL", 1) if i in (10, 11, 12, 13) else r
             for i, r in enumerate(self.aree["basilica_interno"]["griglia"])]
        self.assertEqual(len(G.blocchi(g, "e")), 2)

    def test_la_basilica_ha_chiostro_campanile_scalinata(self):
        el = G.PM.basilica(15, 33, {}).elementi
        for k in ("scalinata", "portale", "facciata", "campanile"):
            self.assertGreaterEqual(el.get(k, 0), 1, k)
        el = G.PM.chiostro(11, 18).elementi
        for k in ("loggiato", "pozzo", "giardino"):
            self.assertGreaterEqual(el.get(k, 0), 1, k)
        b = self.aree["basilica"]
        x0, y0, w, h = b["edifici"]["basilica"]
        chiostro = G.blocchi(b["griglia"], "h")
        self.assertEqual(len(chiostro), 1)
        self.assertLess(max(x for x, _ in chiostro[0]), x0, "il chiostro sta accanto alla chiesa, non davanti")
        self.assertTrue(any(b["griglia"][y0 + h][x] == "S" for x in range(x0, x0 + w)), "la scalinata al portale")

    def test_negativa_basilica_senza_facciata(self):
        self.assertEqual(G.PM.elementi_mancanti("basilica", {"scalinata": 1, "portale": 1, "campanile": 1}),
                         {"facciata": 1})


def dispersione_vicini(punti):
    """Coefficiente di variazione delle distanze dal vicino piu' vicino: 0 per un reticolo regolare."""
    d = []
    for x, y in punti:
        d.append(min(((x - u) ** 2 + (y - v) ** 2) ** 0.5 for u, v in punti if (u, v) != (x, y)))
    media = sum(d) / len(d)
    return (sum((v - media) ** 2 for v in d) / len(d)) ** 0.5 / media


class LaRifinitura(unittest.TestCase):
    """Pezzo L: alberi mai in griglia, lastricato irregolare, torri delle porte, i tipi di cella."""

    @classmethod
    def setUpClass(cls):
        cls.mondo = G.mondo_del_repo()
        cls.aree = {a["id"]: a for a in I.aree_finali()}

    def alberi(self, a):
        """I centri degli alberi (chiome 2x2, cipressi 1x2, alberi piccoli e cespugli)."""
        return [(x + w / 2, y + h / 2) for x, y, w, h, _ in G.alberi_dell_area(a["griglia"])]

    def test_alberi_mai_in_griglia(self):
        provate = 0
        for nome, a in sorted(self.aree.items()):
            punti = self.alberi(a)
            if len(punti) < 10:
                continue
            provate += 1
            self.assertGreater(dispersione_vicini(punti), 0.15, nome)
        self.assertGreaterEqual(provate, 4)

    def test_negativa_alberi_a_reticolo(self):
        reticolo = [(x, y) for x in range(2, 40, 4) for y in range(3, 30, 3)]
        self.assertLess(dispersione_vicini(reticolo), 0.15)

    def test_alberi_grandi(self):
        """Chiome di 2x2 tile, cipressi di 1x2 e cespugli, in ogni area alberata; nel bosco degli
        stradoni le chiome grandi sono la maggioranza."""
        for nome in ("teatro_romano", "piazza_quaranta_martiri", "basilica", "monte_ingino"):
            forme = {(w, h, c) for _, _, w, h, c in G.alberi_dell_area(self.aree[nome]["griglia"])}
            self.assertTrue({(2, 2, "T"), (1, 2, "u"), (1, 1, "r")} <= forme, (nome, forme))
        bosco = G.alberi_dell_area(self.aree["monte_ingino"]["griglia"])
        self.assertGreater(sum(1 for t in bosco if t[2] == 2), len(bosco) // 2)
        self.assertEqual(G.PM.chioma("leccio").w, 16)
        self.assertEqual((G.PM.cipresso().w, G.PM.cipresso().h), (8, 16))

    def test_negativa_alberi_da_un_tile(self):
        """Una fila di T sparsi a un tile non diventa una chioma 2x2."""
        forme = {(w, h) for _, _, w, h, _ in G.alberi_dell_area(["T.T.T", ".T.T."])}
        self.assertEqual(forme, {(1, 1)})

    def passi_dei_corsi(self, a):
        x0, y0, pw, ph = G.rettangolo_piazza(a)
        righe = [y for y in range(y0, y0 + ph) if sum(a["griglia"][y][x] == "K" for x in range(x0, x0 + pw)) > pw // 2]
        return {b - a_ for a_, b in zip(righe, righe[1:])}

    def test_lastricato_non_a_scacchiera(self):
        a = self.aree["piazza_grande"]
        self.assertGreater(len(self.passi_dei_corsi(a)), 1)
        x0, y0, pw, ph = G.rettangolo_piazza(a)
        toni = {G.TILE_FONDALI[G.tile_per_cella(a["griglia"], x, y)][0] for y in range(y0, y0 + ph)
                for x in range(x0, x0 + pw) if a["griglia"][y][x] == "L"}
        self.assertEqual(toni, {"LASTRICO", "LASTRICO_2", "LASTRICO_3"})

    def test_negativa_corsi_a_passo_fisso(self):
        a = copy.deepcopy(self.aree["piazza_grande"])
        x0, y0, pw, ph = G.rettangolo_piazza(a)
        a["griglia"] = ["".join(("K" if (y - y0) % 5 == 2 else "L") if x0 <= x < x0 + pw and y0 <= y < y0 + ph
                                and c in "LK" else c for x, c in enumerate(r)) for y, r in enumerate(a["griglia"])]
        self.assertEqual(self.passi_dei_corsi(a), {5})

    def test_vasca_all_incrocio_dei_giardini(self):
        g = self.aree["piazza_quaranta_martiri"]["griglia"]
        vasche = G.blocchi(g, "v")
        self.assertEqual(len(vasche), 1)
        self.assertEqual(len(vasche[0]), 25)

    def test_torri_grandi(self):
        for nome, a in sorted(self.aree.items()):
            for lettera, (porta, lato, piloni, arco) in a.get("porte", {}).items():
                xs = {x for x, _ in piloni + arco}
                ys = {y for _, y in piloni + arco}
                largo, fondo = (len(xs), len(ys)) if lato in ("alto", "basso") else (len(ys), len(xs))
                self.assertGreaterEqual(largo, 9, (nome, porta))
                self.assertGreaterEqual(fondo, 5, (nome, porta))
                self.assertGreaterEqual(len(arco), 3 * (largo - 2 * G.LATO_PILONE), (nome, porta))

    def test_negativa_torre_mozza(self):
        a = copy.deepcopy(self.aree["teatro_romano"])
        _, piloni, _ = G.geometria_porta(a, "A")
        x, y = piloni[-1]
        a["griglia"][y] = a["griglia"][y][:x] + "#" + a["griglia"][y][x + 1:]
        self.assertTrue(any("incompleta" in e for e in G.errori_porte(a, self.mondo["grafo"])))

    def test_monte_organico(self):
        """Tornanti con il gomito tondo e il muretto a secco fuori, paracarri, ghiaia a due toni coi
        solchi, la cappelletta col gradino."""
        a = self.aree["monte_ingino"]
        g = a["griglia"]
        tornanti = G.tornanti_degli_stradoni(a, G.tratti_degli_stradoni(a))
        for n, celle in enumerate(tornanti, 1):
            accanto = {(x + dx, y + dy) for x, y in celle for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))}
            self.assertGreater(sum(1 for x, y in accanto if g[y][x] == "m"), 8, f"muretto al tornante {n}")
            righe = {y for _, y in celle}
            self.assertGreater(len(righe), G.LUNGHEZZA_MIN_TRATTO // 2 - 1, f"gomito tondo al tornante {n}")
        self.assertGreater(sum(r.count("p") for r in g), 40, "paracarri")
        nomi = {G.TILE_FONDALI[G.tile_per_cella(g, x, y, True, "destra")][0]
                for y, r in enumerate(g) for x, c in enumerate(r) if c == "b"}
        self.assertEqual(nomi, {"BRECCIA", "BRECCIA_2", "BRECCIA_SOLCO"})
        self.assertGreaterEqual(G.PM.cappelletta(3, 3).elementi.get("gradino", 0), 1)

    def test_negativa_tornante_a_squadra(self):
        """Un tornante rifatto a squadra, senza gomito ne' muretto, non passa."""
        a = copy.deepcopy(self.aree["monte_ingino"])
        tornanti = G.tornanti_degli_stradoni(a, G.tratti_degli_stradoni(a))
        g = [list(r) for r in a["griglia"]]
        for y, r in enumerate(g):
            for x, c in enumerate(r):
                if c == "m":
                    g[y][x] = "#"
        a["griglia"] = ["".join(r) for r in g]
        celle = tornanti[0]
        accanto = {(x + dx, y + dy) for x, y in celle for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))}
        self.assertEqual(sum(1 for x, y in accanto if a["griglia"][y][x] == "m"), 0)

    def test_i_tipi_di_cella_stanno_sotto_i_varchi(self):
        """Le celle sono indici fino a PRIMO_VARCO escluso: oltre, il gioco le legge come varchi."""
        self.assertLess(len(G.CELLE), G.PRIMO_VARCO)
        with open(G.USCITA, encoding="utf-8") as f:
            self.assertIn(f"PRIMO_VARCO = {G.PRIMO_VARCO};", f.read())

    def test_negativa_troppi_tipi_di_cella(self):
        troppe = dict(G.CELLE, **{chr(0x100 + k): ("X", True) for k in range(G.PRIMO_VARCO)})
        self.assertFalse(len(troppe) < G.PRIMO_VARCO)


if __name__ == "__main__":
    unittest.main(verbosity=2)
