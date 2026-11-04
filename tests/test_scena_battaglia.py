"""La scena di battaglia (F4, parte 2): la grafica procedurale di tools/genera_battaglia.py e le
regole della scena (src/scena_battaglia.cpp) che si controllano senza GBA. La regola centrale, le
barre che cambiano solo consumando l'evento, e' provata a tempo di compilazione in
src/autotest_vista.cpp (con la sua negativa); qui si controlla che la scena non la scavalchi.
Ogni prova ha la sua negativa."""
import copy
import importlib.util
import os
import re
import sys
import unittest

from _stile import RADICE, S

_spec = importlib.util.spec_from_file_location("genera_battaglia", os.path.join(RADICE, "tools", "genera_battaglia.py"))
GB = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(GB)

_spec_sb = importlib.util.spec_from_file_location("sagome_battaglia", os.path.join(RADICE, "tools", "sagome_battaglia.py"))
SB = importlib.util.module_from_spec(_spec_sb)
FB = GB.FB
_spec_sb.loader.exec_module(SB)

PALETTE = S.carica("palette")
SCENA = open(os.path.join(RADICE, "src", "scena_battaglia.cpp"), encoding="utf-8").read()


def colori_della_guida():
    return {c for r in PALETTE["rampe"] for c in r["giorno"]}


def fuori_guida(palette):
    return [r for r in palette if S.colore(PALETTE, r) not in colori_della_guida()]


def letture_dal_modello(sorgente):
    """Le righe che darebbero a una barra i PV o il Fervore letti dal modello invece che dalla vista."""
    return [r.strip() for r in sorgente.splitlines()
            if re.search(r"\.mostra\(.*g_scena\.(eroe|nemico)\(", r) or
            re.search(r"Barra.*g_scena\.(eroe|nemico)\(.*\.(pv|fervore)", r)]


class Grafica(unittest.TestCase):

    def test_header_aggiornato(self):
        with open(GB.USCITA, encoding="utf-8") as f:
            self.assertEqual(f.read(), GB.genera(PALETTE), "eseguire python tools/genera_battaglia.py --scrivi")

    def test_negativa_header_vecchio(self):
        altra = copy.deepcopy(PALETTE)
        neutri = next(r for r in altra["rampe"] if r["nome"] == "neutri")
        neutri["giorno"][0] ^= 1
        with open(GB.USCITA, encoding="utf-8") as f:
            self.assertNotEqual(f.read(), GB.genera(altra))

    def test_colori_dalla_guida(self):
        for pal in (GB.PALETTE_SFONDO, GB.PALETTE_SANTI, GB.PALETTE_NEMICI):
            self.assertEqual(len(pal), 16)
            self.assertEqual(fuori_guida(pal), [])

    def test_negativa_colore_inventato(self):
        with self.assertRaises(Exception):
            fuori_guida([("magenta", 0)])

    def test_sfondi_entro_i_tile(self):
        """Cinque fondali (tools/fondali_battaglia.py), ognuno coi suoi tile e la sua palette di 16 colori della
        Guida; la guardia della fornace e l'infiltrato riusano quelli della Pattuglia e del Duello (SFONDO_DI)."""
        fondali = GB.tile_e_mappe()
        self.assertEqual(len(fondali), 5)
        for tile, mappa in fondali:
            self.assertLessEqual(len(tile), GB.TILE_SFONDO_MAX)
            self.assertEqual(len(mappa), 1024)
        self.assertEqual(GB.FONDALE_DI, (0, 1, 2, 3, 4, 0, 2))
        for k in range(5):
            palette = FB.fondale(k)[1]
            self.assertEqual(len(palette), 16)
            self.assertEqual(fuori_guida(palette), [])
            self.assertEqual(palette[:3], FB.PANNELLO, "le voci del pannello sono le stesse in ogni fondale")

    def test_negativa_sfondo_riusato_diverso(self):
        """Senza il riuso (SFONDO_DI) la fornace e l'infiltrato chiederebbero fondali che non esistono."""
        senza_riuso = tuple(range(len(GB.INCONTRI)))
        self.assertTrue(any(k >= len(FB.PITTORI) for k in senza_riuso))
        self.assertFalse(any(k >= len(FB.PITTORI) for k in GB.FONDALE_DI))

    def test_le_file_poggiano_sul_suolo(self):
        """Lo standard (fondali): le tre file di figure stanno sul suolo, non sul cielo o sulle mura: i piedi
        della fila piu' alta (centro y 22, piedi a +14) sono sotto l'orizzonte del fondale."""
        piedi_fila_alta = 80 - 58 + 14
        self.assertLess(FB.ORIZZONTE, piedi_fila_alta)

    def test_negativa_orizzonte_alto(self):
        self.assertFalse(76 < 80 - 58 + 14, "con l'orizzonte di prima (76) la fila alta stava sulle mura")

    def test_fondali_luce_da_sinistra(self):
        """Lo standard L1 sui fondali: lo spigolo sinistro di un muro a conci e' in luce, il destro in ombra."""
        t = FB.Tela()
        FB.conci(t, 10, 10, 30, 12, (FB.PIETRA[2], FB.PIETRA[3], FB.PIETRA[4]), FB.random.Random(1))
        self.assertTrue(all(t.px[y][10] == FB.PIETRA[4] for y in range(10, 22)))
        self.assertTrue(all(t.px[y][39] == FB.PIETRA[2] for y in range(10, 22)))
        self.assertNotIn(FB.NERO, {c for riga in t.px for c in riga}, "i giunti non sono neri (C4)")

    def test_pannello_dei_comandi(self):
        for i in range(len(GB.INCONTRI)):
            t = GB.sfondo(i)
            scuri = sum(1 for y in range(GB.PANNELLO_Y + 4, 156) for x in range(4, 236) if t.px[y][x] in (0, 1))
            self.assertGreater(scuri, 0.95 * (156 - GB.PANNELLO_Y - 4) * 232)

    def test_negativa_pannello_mancante(self):
        t = GB.sfondo(0)
        for y in range(GB.PANNELLO_Y, 160):
            t.px[y] = [8] * 256
        scuri = sum(1 for y in range(GB.PANNELLO_Y + 4, 156) for x in range(4, 236) if t.px[y][x] in (0, 1))
        self.assertEqual(scuri, 0)

    def test_figure_riconoscibili(self):
        """Ogni figura (tools/sagome_battaglia.py) ha sette pose, lo sfondo trasparente e il contorno; le
        pose sono tutte diverse fra loro; nessuna figura e' uguale a un'altra; Corrado e' 64x64."""
        viste = set()
        for nome, pittore in SB.SANTI + SB.NEMICI:
            pose = SB.pose_di(pittore, False)
            self.assertEqual(len(pose), 7, nome)
            griglie = [tuple(map(tuple, px)) for _, px in pose]
            self.assertEqual(len(set(griglie)), 7, f"{nome}: due pose uguali")
            riposo = pose[0][1]
            self.assertEqual(riposo[0][0], 0)
            self.assertIn(SB.CONTORNO, {c for r in riposo for c in r})
            self.assertNotIn(griglie[0], viste)
            viste.add(griglie[0])
        self.assertEqual(len(SB.corrado("riposo").pixel()), 64)

    def test_negativa_figura_doppia(self):
        a, b = SB.ubaldo("riposo").pixel(), SB.ubaldo("riposo").pixel()
        self.assertEqual(a, b)

    def test_palette_delle_figure_dalla_guida(self):
        """Ogni figura ha la sua palette di 16 colori della Guida, e la usa tutta dentro i suoi indici."""
        for nome, pittore in SB.SANTI + SB.NEMICI:
            for posa in SB.POSE:
                f = pittore(posa)
                self.assertEqual(len(f.palette), 16, nome)
                self.assertEqual(fuori_guida(f.palette), [], nome)
                usati = {c for r in f.pixel() for c in r}
                self.assertLessEqual(max(usati), 15)
        self.assertEqual(fuori_guida(SB.PALETTE_EFFETTI), [])
        for _, chiaro, scuro in SB.LAMPI:
            self.assertEqual(fuori_guida(SB.palette_lampo(chiaro, scuro)), [])

    def test_negativa_palette_troppo_lunga(self):
        troppi = [SB.Materiale(f"m{i}", ("neutri", 1), ("neutri", 2), ("neutri", 3 + i % 2)) for i in range(6)]
        troppi += [SB.Materiale("v", ("verde dei monti", 0), ("verde dei monti", 1), ("verde dei monti", 2)),
                   SB.Materiale("c", ("cielo e acqua", 0), ("cielo e acqua", 1), ("cielo e acqua", 2)),
                   SB.Materiale("o", ("oro e bronzo", 0), ("oro e bronzo", 1), ("oro e bronzo", 2)),
                   SB.Materiale("l", ("legno e cuoio", 0), ("legno e cuoio", 1), ("legno e cuoio", 2)),
                   SB.Materiale("r", ("vermiglio comunale", 0), ("vermiglio comunale", 1), ("vermiglio comunale", 2))]
        with self.assertRaises(ValueError):
            SB.palette_di(troppi)

    def test_luce_da_sinistra(self):
        """L'ombreggiatura: nella veste di Ubaldo il bordo sinistro e' piu' chiaro del destro (Guida,
        scelta 4)."""
        import stile as St
        f = SB.ubaldo("riposo")
        px = f.pixel()
        lum = lambda i: St.luminanza(St.colore(PALETTE, f.palette[i]))  # noqa: E731
        riga = px[24]
        pieni = [x for x, c in enumerate(riga) if c > 1]
        self.assertGreater(lum(riga[pieni[0]]), lum(riga[pieni[-1]]))

    def test_negativa_luce_da_destra(self):
        import stile as St
        f = SB.ubaldo("riposo")
        px = [list(reversed(r)) for r in f.pixel()]
        lum = lambda i: St.luminanza(St.colore(PALETTE, f.palette[i]))  # noqa: E731
        pieni = [x for x, c in enumerate(px[24]) if c > 1]
        self.assertLess(lum(px[24][pieni[0]]), lum(px[24][pieni[-1]]))

    def test_effetti_quattro_fotogrammi(self):
        """Gli effetti nell'ordine di animazione::Effetto, quattro fotogrammi non vuoti ciascuno."""
        anim = open(os.path.join(RADICE, "include", "animazione_battaglia.h"), encoding="utf-8").read()
        nomi_cpp = re.findall(r"^    ([A-Z]+),", anim[anim.index("enum class Effetto"):anim.index("CONTEGGIO")], re.M)
        self.assertEqual(nomi_cpp[1:], [n for n, _ in SB.EFFETTI])
        for nome, pittore in SB.EFFETTI:
            for k in range(SB.FOTOGRAMMI_EFFETTO):
                self.assertTrue(any(any(r) for r in pittore(k)), f"{nome} {k} vuoto")
        pose_cpp = re.findall(r"^    ([A-Z]+),", anim[anim.index("enum class Posa"):anim.index("LIBERA")], re.M)
        self.assertEqual([p.lower() for p in pose_cpp], list(SB.POSE))

    def test_le_prove_delle_animazioni(self):
        autotest = open(os.path.join(RADICE, "src", "autotest_animazione.cpp"), encoding="utf-8").read()
        for prova in ("ordine_del_colpo(NORMALE)", "! fermo_tenuto(NORMALE, colpo_senza_fermo)",
                      "! tutti_a_posto(Gesto::COLPO, NORMALE, ritorno_monco)", "immune_senza_danno()", "caduta()",
                      "effetti_validi()", "forte_piu_pesante()"):
            self.assertIn(prova, autotest)

    def test_ordine_dei_tre(self):
        """Regola di Cioti (4 nov 2026): Ubaldo al centro e davanti, Giorgio secondo, Antonio terzo."""
        fila = [int(v) for v in re.search(r"FILA_EROE\[EROI\] = \{ (\d), (\d), (\d) \}", SCENA).groups()]
        x = [int(v) for v in re.search(r"X_EROI\[EROI\] = \{ (-?\d+), (-?\d+), (-?\d+) \}", SCENA).groups()]
        self.assertTrue(ordine_buono(fila, x))

    def test_negativa_ordine_sbagliato(self):
        self.assertFalse(ordine_buono([0, 1, 2], [-64, -52, -60]))


def ordine_buono(fila, x):
    """Ubaldo nella fila di mezzo e piu' avanti di tutti, Giorgio piu' avanti (o pari) di Antonio."""
    ubaldo, giorgio, antonio = 0, 1, 2
    return fila[ubaldo] == 1 and x[ubaldo] > x[giorgio] >= x[antonio]


PROGRESSIONE = open(os.path.join(RADICE, "include", "progressione.h"), encoding="utf-8").read()


def scontri_sulla_mappa(sorgente):
    """(area, incontro, bandiera) degli scontri sulla mappa scritti in include/progressione.h."""
    return re.findall(r"\{ mondo::AreaId::(\w+), \d+, \d+, (\d), Bandiera::(\w+) \}", sorgente)


class ScontriSullaMappa(unittest.TestCase):
    """Dove stanno i nemici sulla mappa: dal copione v1 (le regole di posto e contatto sono provate
    a tempo di compilazione in src/autotest_progressione.cpp)."""

    def test_dal_copione(self):
        self.assertIn("copione v1", PROGRESSIONE)
        self.assertEqual(scontri_sulla_mappa(PROGRESSIONE), [
            ("TEATRO_ROMANO", "0", "PATTUGLIA_SCONFITTA"),
            ("MONTE_INGINO", "1", "IMBOSCATA_SCONFITTA"),
            ("CONDOTTO", "2", "CORRADO_SCONFITTO"),
        ])

    def test_negativa_corrado_fuori_posto(self):
        finto = PROGRESSIONE.replace("{ mondo::AreaId::CONDOTTO, 50, 14, 2", "{ mondo::AreaId::SANT_AGOSTINO, 29, 20, 2")
        self.assertNotEqual(scontri_sulla_mappa(finto)[2][0], "CONDOTTO")

    def test_le_prove_a_tempo_di_compilazione(self):
        autotest = open(os.path.join(RADICE, "src", "autotest_progressione.cpp"), encoding="utf-8").read()
        for prova in ("curva_buona(ESPERIENZA_PER_LIVELLO)", "! curva_buona(CURVA_SBAGLIATA)", "crescita_buona()",
                      "livello_dopo_gli_scontri_della_storia() == 6", "livello_prima_di_corrado() == 5",
                      "livello_con_guerrieri_generosi() == 6", "i_livelli_contano()", "posti_dei_nemici()", "contatto()"):
            self.assertIn("static_assert(" + prova, autotest)


DATI = open(os.path.join(RADICE, "include", "battaglia_dati.h"), encoding="utf-8").read()


def consumo_all_evento(sorgente):
    """Il corpo che toglie un oggetto dall'inventario: deve stare nel consumo dell'evento."""
    m = re.search(r"void consuma_oggetto\(const Evento& e\)(.*?)\n        \}\n", sorgente, re.S)
    return m.group(1) if m else ""


class Consumabili(unittest.TestCase):
    """Gli oggetti in battaglia: i dati dal prototipo (item_data.h) e il consumo quando l'effetto
    arriva a schermo. Le regole (cura entro i PV massimi, purifica, non usabili inerti) sono provate a
    tempo di compilazione in src/autotest_oggetti.cpp."""

    def test_dati_dal_prototipo(self):
        righe = re.findall(r"\{ (true|false), (\d+), (true|false), (\d+), (\d+) \},\s+// (\w+)", DATI)
        self.assertEqual([r[5] for r in righe], ["Crescia", "Cenere", "Baccala", "Biscotti", "Vino"])
        crescia, _, baccala, biscotti, _ = righe
        self.assertEqual((crescia[0], crescia[1]), ("true", "100"))
        self.assertEqual((biscotti[0], biscotti[2], biscotti[3]), ("true", "true", "10"))
        self.assertEqual(baccala[4], "1")

    def test_si_consuma_all_evento(self):
        corpo = consumo_all_evento(SCENA)
        self.assertIn("EventKind::CURA", corpo)
        self.assertIn("EventKind::PURIFICA", corpo)
        self.assertIn("quanti - 1", corpo)
        self.assertIn("consuma_oggetto(evento);", SCENA)
        autotest = open(os.path.join(RADICE, "src", "autotest_oggetti.cpp"), encoding="utf-8").read()
        self.assertIn("static_assert(CRESCIA.pv_dopo <= CRESCIA.pv_max", autotest)

    def test_negativa_consumo_alla_scelta(self):
        """Togliere l'oggetto quando lo si sceglie (e non all'evento) e' quello che il test rifiuta."""
        finto = "void scegli_comandi() { _partita->oggetti[0] -= 1; }"
        self.assertEqual(consumo_all_evento(finto), "")


class Scena(unittest.TestCase):

    def test_le_barre_si_leggono_dalla_vista(self):
        self.assertEqual(letture_dal_modello(SCENA), [])
        self.assertIn("_pv[s].mostra(_vista.pv(s), _vista.pv_max(s));", SCENA)
        self.assertIn("_fervore[e].mostra(_vista.fervore(e), _vista.fervore_max(e));", SCENA)

    def test_negativa_barra_letta_dal_modello(self):
        finto = "    _pv[s].mostra(g_scena.eroe(s).pv, g_scena.eroe(s).pv_max);"
        self.assertTrue(letture_dal_modello(finto))

    def test_pv_in_cifre_dalla_vista(self):
        """I PV dei Santi in cifre accanto alle barre si scrivono dalla vista, come le barre."""
        self.assertIn("_numeri_pv[e].mostra(_vista.pv(e));", SCENA)
        self.assertEqual(re.findall(r"_numeri_pv\[[a-z]+\]\.mostra\(([^;]*)\);", SCENA), ["_vista.pv(e)"])

    def test_negativa_pv_in_cifre_dal_modello(self):
        finto = "_numeri_pv[e].mostra(g_scena.eroe(e).pv);"
        self.assertNotEqual(re.findall(r"_numeri_pv\[[a-z]+\]\.mostra\(([^;]*)\);", finto), ["_vista.pv(e)"])
        self.assertTrue(letture_dal_modello("    _numeri_pv[e].mostra(g_scena.eroe(e).pv);"))

    def test_scelta_del_bersaglio(self):
        """Il bersaglio parte dal predefinito del modello e si sposta fra i vivi (le regole sono provate
        a tempo di compilazione in src/autotest_vista.cpp); B torna alla scelta del comando."""
        corpo = SCENA[SCENA.index("bool scegli_bersaglio("):SCENA.index("void anima(")]
        self.assertIn("bersaglio_predefinito(g_scena, mira)", corpo)
        self.assertIn("prossimo_bersaglio(g_scena, mira, scelto,", corpo)
        self.assertIn("comando.bersaglio = scelto;", corpo)
        self.assertIn("b_pressed()", corpo)
        vista = open(os.path.join(RADICE, "src", "autotest_vista.cpp"), encoding="utf-8").read()
        self.assertIn("static_assert(prova_bersagli()", vista)
        self.assertIn("static_assert(giro_cieco_finisce_su_un_caduto()", vista)

    def test_negativa_bersaglio_scelto_a_mano(self):
        finto = "bool scegli_bersaglio( scelto = (scelto + 1) % 3; void anima("
        corpo = finto[finto.index("bool scegli_bersaglio("):finto.index("void anima(")]
        self.assertNotIn("prossimo_bersaglio(g_scena, mira, scelto,", corpo)

    def test_un_attore_per_volta(self):
        """Nell'animazione di un evento si muove solo m.attore: nessun altro sprite cambia x se non il
        bersaglio che arretra (il tremito dello schermo sposta tutti in verticale, insieme)."""
        anima = SCENA[SCENA.index("void anima("):SCENA.index("int scegli_incontro(")]
        mossi = set(re.findall(r"_sprite\[([a-z.]+)\]->set_x", anima))
        self.assertEqual(mossi, {"m.attore", "m.bersaglio"})

    def test_negativa_due_attori(self):
        finto = "void anima(\n _sprite[m.attore]->set_x(1); _sprite[altro]->set_x(2);\nint scegli_incontro("
        anima = finto[finto.index("void anima("):finto.index("int scegli_incontro(")]
        self.assertNotEqual(set(re.findall(r"_sprite\[([a-z.]+)\]->set_x", anima)), {"m.attore", "m.bersaglio"})

    def test_avvio_4_e_5(self):
        main = open(os.path.join(RADICE, "src", "main.cpp"), encoding="utf-8").read()
        self.assertIn("GUBBIO_AVVIO == 4", main)
        self.assertIn("menu_battaglie(palette)", main)
        self.assertIn("GUBBIO_AVVIO == 5", main)
        self.assertIn("istantanee_battaglie(palette)", main)


if __name__ == "__main__":
    unittest.main(verbosity=2)
