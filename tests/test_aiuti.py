"""MAI: gli aiuti al giocatore senza il menu di pausa nuovo (menu/PROPOSTA.md sez. 3.8). La logica sta in
include/aiuti.h ed e' provata con static_assert in src/autotest_menu.cpp; qui: i cartelli generati da
mondo/grafo.json (aggiornati, uno per varco nei due versi, ognuno in una riga del contesto AREA), i testi nuovi
e gli agganci nel gioco. Prove negative: un arco verso un'area che non c'e', una porta troppo lunga per la riga.
"""
import copy
import os
import re
import sys
import unittest

from _stile import RADICE

sys.path.insert(0, os.path.join(RADICE, "tools"))
sys.path.insert(0, os.path.join(RADICE, "stile"))
import genera_cartelli as GC  # noqa: E402
import stile as S  # noqa: E402


def leggi(*parti):
    with open(os.path.join(RADICE, *parti), encoding="utf-8") as f:
        return f.read()


GRAFO = GC.leggi_grafo()
RIGHE = GC.cartelli(GRAFO)


class Cartelli(unittest.TestCase):

    def test_file_generati_aggiornati(self):
        h, t = GC.genera()
        self.assertEqual(h, leggi("include", "cartelli.h"))
        self.assertEqual(t, leggi("testi", "cartelli.testi"))

    def test_uno_per_varco_nei_due_versi(self):
        self.assertEqual(len(RIGHE), 2 * len(GRAFO["archi"]))
        coppie = {(da, verso) for da, verso, _ in RIGHE}
        self.assertEqual(len(coppie), len(RIGHE))
        for a in GRAFO["archi"]:
            self.assertIn((a["da"], a["a"]), coppie)
            self.assertIn((a["a"], a["da"]), coppie)
        self.assertIn(f"inline constexpr int CARTELLI = {len(RIGHE)};", leggi("include", "cartelli.h"))

    def test_ogni_riga_sta_nel_contesto_area(self):
        font = S.carica("font")
        for da, verso, riga in RIGHE:
            self.assertEqual(len(S.a_capo(font, riga, GC.LARGHEZZA_AREA)), 1, f"{da} -> {verso}: {riga}")

    def test_niente_area_da_cui_si_viene(self):
        for da, verso, riga in RIGHE:
            self.assertNotIn(GC.BREVI[da], riga.split("poi ")[-1].split(", "), f"{da} -> {verso}")

    def test_la_porta_prima_delle_aree(self):
        riga = dict(((da, verso), r) for da, verso, r in RIGHE)[("SAN_MARTINO", "BOTTACCIONE")]
        self.assertTrue(riga.startswith("Porta Metauro, poi "), riga)


class Negative(unittest.TestCase):

    def test_arco_verso_un_area_che_non_c_e(self):
        g = copy.deepcopy(GRAFO)
        g["archi"].append({"da": "PIAZZA_GRANDE", "a": "TEATRO_GRECO"})
        with self.assertRaisesRegex(GC.ErroreCartelli, "TEATRO_GRECO"):
            GC.cartelli(g)

    def test_porta_troppo_lunga(self):
        g = copy.deepcopy(GRAFO)
        g["archi"][0]["porta"] = "Porta " + "lunghissima " * 12
        with self.assertRaisesRegex(GC.ErroreCartelli, "non sta"):
            GC.cartelli(g)

    def test_le_aree_si_tolgono_finche_la_riga_sta(self):
        g = copy.deepcopy(GRAFO)
        g["archi"][0]["porta"] = "Porta della Mattonata vecchia e un po' lunga"
        righe = GC.cartelli(g)
        riga = next(r for da, verso, r in righe if (da, verso) == (g["archi"][0]["da"], g["archi"][0]["a"]))
        self.assertLess(riga.count(","), 1 + GC.OLTRE_MAX)


class Testi(unittest.TestCase):

    NUOVI = ("ETICHETTA_OBIETTIVO", "PROMEMORIA_NESSUNO", "FASE_ULTIMATUM", "FASE_DIGIUNO", "FASE_NOTTE",
             "FASE_DOPO_L_ALBA", "TITOLO_LIVELLI", "DOVE_ERAVAMO", "DOVE_ERAVAMO_INCARICHI", "DOVE_ERAVAMO_TEMPO",
             "DOVE_ERAVAMO_AIUTO", "SCONFITTA_INGRESSO", "SCONFITTA_ARCO", "SCONFITTA_SUBITO", "RIPROVA_DOMANDA",
             "RIPROVA_SCONTRO", "RIPROVA_CARICA", "RIPROVA_TITOLO", "CARICA_SLOT_1", "CARICA_SLOT_2", "CARICA_FALLITO")

    def test_i_testi_nuovi_ci_sono(self):
        partita = leggi("testi", "partita.testi")
        testi_h = leggi("include", "testi.h")
        for t in self.NUOVI:
            self.assertTrue(re.search(rf"^{t}\s*\|", partita, re.M), t)
            self.assertIn(f"{t},", testi_h)
        for da, verso, _ in RIGHE:
            self.assertIn(f"{GC.id_testo(da, verso)},", testi_h)

    def test_le_voci_del_riprova_sono_scelte(self):
        partita = leggi("testi", "partita.testi")
        for t in ("RIPROVA_SCONTRO", "RIPROVA_CARICA", "RIPROVA_TITOLO"):
            self.assertTrue(re.search(rf"^{t}\s*\| SCELTA\s*\|", partita, re.M), t)


MODI_CON_AIUTI = {0, 14, 15}    # il gioco vero e le due partite di prova che servono a fotografarli
MODI_COL_TITOLO = {0, 15}       # titolo e «Dove eravamo»: il gioco vero e la partita con gli slot di prova


def modi_di(main, nome):
    """I modi GUBBIO_AVVIO (0-15) in cui vale la costante 'nome' di main.cpp: ne valuta l'espressione."""
    m = re.search(rf"constexpr bool {nome} = ([^;]+);", main)
    if not m:
        return None
    espressione = m.group(1).replace("||", " or ").replace("&&", " and ")
    if not re.fullmatch(r"[\sA-Z_0-9=!()orand]+", espressione):
        return None
    return {modo for modo in range(16) if eval(espressione, {"GUBBIO_AVVIO": modo})}


class Agganci(unittest.TestCase):

    def test_aiuti_nei_modi_di_prova(self):
        main = leggi("src", "main.cpp")
        self.assertEqual(modi_di(main, "AIUTI_ATTIVI"), MODI_CON_AIUTI)
        self.assertEqual(modi_di(main, "COL_TITOLO"), MODI_COL_TITOLO)
        self.assertIn("esplorazione.attiva_aiuti(AIUTI_ATTIVI);", main)
        self.assertIn("bn::keypad::select_pressed() && AIUTI_ATTIVI", main)
        # «Dove eravamo» col titolo; il prologo resta del solo gioco vero
        prima = main[main.index("gubbio::dove_eravamo(") - 120:main.index("gubbio::dove_eravamo(")]
        self.assertIn("if(COL_TITOLO)", prima)
        prologo = main[main.index("prologo.prologo(palette);") - 120:main.index("prologo.prologo(palette);")]
        self.assertIn("if(GUBBIO_AVVIO == 0)", prologo)
        # il modo 15 scrive gli slot prima del titolo
        self.assertLess(main.index("gubbio::prepara_slot_di_prova();"), main.index("gubbio::titolo(palette)"))

    def test_aiuti_nei_modi_di_prova_negativa(self):
        main = leggi("src", "main.cpp")
        espressione = re.search(r"constexpr bool AIUTI_ATTIVI = ([^;]+);", main).group(1)
        solo_zero = main.replace(espressione, "GUBBIO_AVVIO == 0")
        self.assertNotEqual(modi_di(solo_zero, "AIUTI_ATTIVI"), MODI_CON_AIUTI)
        troppi = main.replace(espressione, "GUBBIO_AVVIO != 7")
        self.assertNotEqual(modi_di(troppi, "AIUTI_ATTIVI"), MODI_CON_AIUTI)
        self.assertIsNone(modi_di(main.replace("constexpr bool AIUTI_ATTIVI", "bool aiuti"), "AIUTI_ATTIVI"))
        self.assertIsNone(modi_di(main.replace(espressione, "__import__('os')"), "AIUTI_ATTIVI"))

    @staticmethod
    def update_fra_titolo_ed_esplorazione(main):
        """Fra il titolo e l'esplorazione passa un bn::core::update(): Butano rende i tile degli sprite del titolo
        solo li', e senza «Dove eravamo» li finiva (No more sprite tiles items available)."""
        titolo = main.find("gubbio::titolo(palette, true)")
        esplorazione = main.find("gubbio::Esplorazione esplorazione(palette);")
        return 0 <= titolo < esplorazione and "bn::core::update();" in main[titolo:esplorazione]

    def test_tile_del_titolo_resi_prima_dell_esplorazione(self):
        self.assertTrue(self.update_fra_titolo_ed_esplorazione(leggi("src", "main.cpp")))
        # gli aiuti si creano solo mentre si vedono: niente VistaTesto sempre allocate nell'esplorazione
        esp_h = leggi("include", "esplorazione.h")
        for nome in ("_promemoria", "_targa_nome", "_cartello", "_oltre"):
            self.assertRegex(esp_h, rf"bn::optional<VistaTesto> {nome};", nome)
        # e i riquadri a pixel (include/pannello.h) lo stesso
        for nome in ("_promemoria_fondo", "_targa", "_cartello_fondo"):
            self.assertRegex(esp_h, rf"bn::optional<pannello::Pannello> {nome};", nome)

    def test_tile_del_titolo_resi_prima_dell_esplorazione_negativa(self):
        main = leggi("src", "main.cpp")
        titolo = main.index("gubbio::titolo(palette, true)")
        esplorazione = main.index("gubbio::Esplorazione esplorazione(palette);")
        senza = main[:titolo] + main[titolo:esplorazione].replace("bn::core::update();", "") + main[esplorazione:]
        self.assertFalse(self.update_fra_titolo_ed_esplorazione(senza))

    def test_main(self):
        main = leggi("src", "main.cpp")
        self.assertIn("esplorazione.promemoria();", main)
        self.assertIn("gubbio::dove_eravamo(esplorazione, palette);", main)
        self.assertLess(main.index("storia::dopo_il_caricamento(gubbio::g_game_state);"),
                        main.index("gubbio::dove_eravamo(esplorazione, palette);"))

    def test_esplorazione_e_storia(self):
        esp = leggi("src", "esplorazione.cpp")
        self.assertIn("aiuti::varco_vicino(", esp)
        self.assertIn("aiuti::varco_verso_la_meta(", esp)
        # il cartello accende il fumetto (STANDARD I2) dove la storia spegnerebbe quello delle persone
        self.assertIn("aiuti::cartello_a_portata(", esp)
        self.assertIn("aiuti::pixel_freccia(", esp)
        storia = leggi("src", "storia_scena.cpp")
        self.assertIn("aiuti::riprova_dopo_la_sconfitta(k)", storia)
        self.assertIn("aiuti::ritirata_della_scena(k)", storia)
        self.assertIn("if(! a_portata && ! esplorazione.segnala_cartello())", storia)

    def test_genera_cartelli_nei_controlli(self):
        # il generatore ha la sua prova di aggiornamento qui sopra; la tabella la legge aiuti.h
        self.assertIn('#include "cartelli.h"', leggi("include", "aiuti.h"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
