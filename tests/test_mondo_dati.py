#!/usr/bin/env python3
"""Il mondo come dati (mondo/*.json, tools/mondo_dati.py).

Ogni controllo gira sul mondo vero (deve passare) e su una copia guastata
apposta (deve essere preso): la prova negativa.

    python -m unittest tests.test_mondo_dati
"""
import copy
import importlib.util
import os
import unittest

from _stile import RADICE

_spec = importlib.util.spec_from_file_location("mondo_dati", os.path.join(RADICE, "tools", "mondo_dati.py"))
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)

GRAFO = M.carica_grafo()
CENS = M.carica_censimento()


def guasto():
    return copy.deepcopy(GRAFO)


def arco(g, da, a):
    return next(e for e in g["archi"] if e["da"] == da and e["a"] == a)


class Rotazione(unittest.TestCase):

    def test_quattro_punti_cardinali(self):
        self.assertEqual(M.lato_schermo(0), "destra")      # nord
        self.assertEqual(M.lato_schermo(90), "basso")      # est
        self.assertEqual(M.lato_schermo(180), "sinistra")  # sud
        self.assertEqual(M.lato_schermo(270), "alto")      # ovest

    def test_facciata_est_frontale(self):
        self.assertEqual(M.vista_facciata(90), "frontale")
        self.assertEqual(M.vista_facciata(270), "retro (solo tetto)")

    def test_rotazione_specchiata_presa(self):
        """Prova negativa: una rotazione con est e ovest scambiati non passa gli stessi controlli."""
        originale = M.vettore_schermo
        try:
            M.vettore_schermo = lambda b: (originale(b)[0], -originale(b)[1])
            self.assertNotEqual(M.lato_schermo(90), "basso")
            self.assertNotEqual(M.vista_facciata(90), "frontale")
        finally:
            M.vettore_schermo = originale

    def test_facciate_note(self):
        """Consoli e Bargello si vedono di fronte, Pretorio da dietro (decisione del 1 nov 2026)."""
        mon = M.calcola_monumenti(GRAFO, CENS)
        self.assertEqual(mon["consoli"]["facciata_vista"], "frontale")
        self.assertEqual(mon["bargello"]["facciata_vista"], "frontale")
        self.assertEqual(mon["pretorio"]["facciata_vista"], "retro (solo tetto)")


class Grafo(unittest.TestCase):

    def test_archi_validi(self):
        self.assertEqual(M.errori_archi(GRAFO), [])

    def test_archi_guasti_presi(self):
        g = guasto()
        g["archi"].append({"da": "PIAZZA_GRANDE", "a": "ATLANTIDE", "verso": "N", "come": "x"})
        self.assertTrue(any("ATLANTIDE" in e for e in M.errori_archi(g)))
        g = guasto()
        g["archi"].append(dict(arco(g, "DUOMO_DUCALE", "MONTE_INGINO")))
        self.assertTrue(any("doppio" in e for e in M.errori_archi(g)))
        g = guasto()
        arco(g, "DUOMO_DUCALE", "MONTE_INGINO")["verso"] = "NNE"
        self.assertTrue(any("sconosciuta" in e for e in M.errori_archi(g)))

    def test_connesso(self):
        self.assertEqual(M.errori_connessione(GRAFO), [])

    def test_arco_tolto_isola_un_area(self):
        """Prova negativa: senza i due archi del Teatro (da San Martino e da Quaranta Martiri) il
        Teatro resta isolato."""
        g = guasto()
        g["archi"].remove(arco(g, "SAN_MARTINO", "TEATRO_ROMANO"))
        g["archi"].remove(arco(g, "PIAZZA_QUARANTA_MARTIRI", "TEATRO_ROMANO"))
        self.assertEqual(M.errori_connessione(g), ["area irraggiungibile: TEATRO_ROMANO"])

    def test_anello_chiuso(self):
        self.assertEqual(M.errori_anello(GRAFO), [])

    def test_anello_rotto_preso(self):
        g = guasto()
        g["archi"].remove(arco(g, "BOTTACCIONE", "SAN_MARTINO"))
        self.assertEqual(M.errori_anello(g), ["passo dell'anello senza arco: BOTTACCIONE>SAN_MARTINO"])
        g = guasto()
        g["anello"] = g["anello"][:-1]
        self.assertTrue(any("non si chiude" in e for e in M.errori_anello(g)))

    def test_rientro_dal_bottaccione_a_san_martino(self):
        """Dal Bottaccione si rientra da Porta Metauro, nell'area San Martino (Cioti, 1 nov 2026)."""
        self.assertIn("porta_metauro", next(a for a in GRAFO["aree"] if a["id"] == "SAN_MARTINO")["monumenti"])
        arco(GRAFO, "BOTTACCIONE", "SAN_MARTINO")


class Quote(unittest.TestCase):

    def test_salite_e_discese_coerenti(self):
        self.assertEqual(M.errori_quote(GRAFO), [])

    def test_quota_sbagliata_presa(self):
        """Prova negativa: se la Basilica stesse in basso, la salita da Monte Ingino non torna."""
        g = guasto()
        next(a for a in g["aree"] if a["id"] == "BASILICA")["quota_m"] = [0, 0]
        err = M.errori_quote(g)
        self.assertTrue(any(e.startswith("MONTE_INGINO>BASILICA") for e in err), err)
        self.assertTrue(any(e.startswith("BASILICA>BOTTACCIONE") for e in err), err)


class Direzioni(unittest.TestCase):

    def test_direzioni_come_sulla_carta(self):
        self.assertEqual(M.errori_direzioni(GRAFO, CENS), [])

    def test_direzione_scambiata_presa(self):
        """Prova negativa: via dei Consoli verso sud-est invece che nord-ovest."""
        g = guasto()
        arco(g, "PIAZZA_GRANDE", "VIA_DEI_CONSOLI")["verso"] = "SE"
        err = M.errori_direzioni(g, CENS)
        self.assertEqual(len(err), 1)
        self.assertTrue(err[0].startswith("PIAZZA_GRANDE>VIA_DEI_CONSOLI"))

    def test_eccezione_necessaria(self):
        """Riallineato alla citta' vera: senza eccezioni nessuna direzione e' fuori tolleranza."""
        g = guasto()
        g["direzioni_da_confermare"] = {}
        self.assertEqual(M.errori_direzioni(g, CENS), [])
        self.assertEqual(M.errori_eccezioni_superflue(GRAFO, CENS), [])

    def test_eccezione_superflua_presa(self):
        """Prova negativa: un'eccezione per un arco che torna con la carta va segnalata."""
        g = guasto()
        g["direzioni_da_confermare"] = {"PIAZZA_GRANDE>VIA_DEI_CONSOLI": "prova"}
        self.assertEqual(M.errori_eccezioni_superflue(g, CENS),
                         ["eccezione non piu' necessaria: PIAZZA_GRANDE>VIA_DEI_CONSOLI"])
        self.assertIn("eccezione non piu' necessaria: PIAZZA_GRANDE>VIA_DEI_CONSOLI", M.tutti_gli_errori(g, CENS))

    def test_eccezione_per_arco_tolto_presa(self):
        """Prova negativa: la vecchia eccezione SANT_AGOSTINO>SANT_ANDREA, ora che l'arco non c'e'."""
        g = guasto()
        g["direzioni_da_confermare"] = {"SANT_AGOSTINO>SANT_ANDREA": "prova"}
        self.assertEqual(M.errori_eccezioni_superflue(g, CENS),
                         ["eccezione per un arco che non c'e': SANT_AGOSTINO>SANT_ANDREA"])

    def test_varchi_andata_e_ritorno(self):
        self.assertEqual(M.errori_lati_varchi(M.calcola_varchi(GRAFO, CENS)), [])

    def test_varco_storto_preso(self):
        var = M.calcola_varchi(GRAFO, CENS)
        ritorno = next(v for v in var["DUOMO_DUCALE"] if v["verso"] == "MONTE_INGINO")
        ritorno["lato"] = "destra"
        self.assertTrue(any("rientra" in e for e in M.errori_lati_varchi(var)))

    def test_accessi_esclusivi_di_piazza_grande(self):
        """Regola di Cioti: a Piazza Grande solo da via dei Consoli e via XX Settembre, che salgono
        tutte e due da Piazza Quaranta Martiri. Il vincolo sta in grafo.json, non nel codice."""
        self.assertEqual(GRAFO["vincoli"]["accessi_esclusivi"]["PIAZZA_GRANDE"]["vicini"],
                         ["VIA_DEI_CONSOLI", "VIA_XX_SETTEMBRE"])
        self.assertEqual(M.errori_accessi_esclusivi(GRAFO), [])

    def test_accesso_in_piu_preso(self):
        """Prova negativa: il vecchio arco Piazza Grande > Duomo rientra di nascosto."""
        g = guasto()
        g["archi"].append({"da": "PIAZZA_GRANDE", "a": "DUOMO_DUCALE", "verso": "NE", "come": "x"})
        err = M.errori_accessi_esclusivi(g)
        self.assertEqual(len(err), 1)
        self.assertTrue(err[0].startswith("a PIAZZA_GRANDE si entra da"))

    def test_via_scollegata_presa(self):
        """Prova negativa: via XX Settembre non sale piu' da Piazza Quaranta Martiri."""
        g = guasto()
        g["archi"] = [e for e in g["archi"]
                      if {e["da"], e["a"]} != {"PIAZZA_QUARANTA_MARTIRI", "VIA_XX_SETTEMBRE"}]
        self.assertEqual(M.errori_accessi_esclusivi(g),
                         ["VIA_XX_SETTEMBRE non e' collegata a PIAZZA_QUARANTA_MARTIRI, "
                          "come vuole il vincolo su PIAZZA_GRANDE"])

    def test_lati_attesi(self):
        """Piazza Grande: via dei Consoli in alto (ovest), via XX Settembre in basso (est), e basta."""
        lati = {v["verso"]: v["lato"] for v in M.calcola_varchi(GRAFO, CENS)["PIAZZA_GRANDE"]}
        self.assertEqual(lati, {"VIA_DEI_CONSOLI": "alto", "VIA_XX_SETTEMBRE": "basso"})

    def test_lati_attesi_quaranta_martiri(self):
        """Quaranta Martiri: San Martino e via dei Consoli a destra (nord), San Pietro e via XX
        Settembre in basso (est), il Teatro in alto (ovest)."""
        lati = {v["verso"]: v["lato"] for v in M.calcola_varchi(GRAFO, CENS)["PIAZZA_QUARANTA_MARTIRI"]}
        self.assertEqual(lati, {"SAN_MARTINO": "destra", "VIA_DEI_CONSOLI": "destra", "SAN_PIETRO": "basso",
                                "VIA_XX_SETTEMBRE": "basso", "TEATRO_ROMANO": "alto"})

    def test_lati_attesi_ordine_nuovo(self):
        """Rete stradale OSM: da via XX Settembre si va a Sant'Andrea (in basso, sud-est), si sale al
        Duomo (a destra, nord) e si scende a Quaranta Martiri (in alto); da Sant'Andrea al Monte."""
        var = M.calcola_varchi(GRAFO, CENS)
        lati = lambda aid: {v["verso"]: v["lato"] for v in var[aid]}  # noqa: E731
        self.assertEqual(lati("VIA_XX_SETTEMBRE"), {"PIAZZA_GRANDE": "alto", "SANT_ANDREA": "basso",
                                                    "PIAZZA_QUARANTA_MARTIRI": "alto", "DUOMO_DUCALE": "destra"})
        self.assertEqual(lati("SANT_ANDREA"), {"VIA_XX_SETTEMBRE": "alto", "SANT_AGOSTINO": "sinistra",
                                               "MONTE_INGINO": "destra"})
        self.assertEqual(lati("SANT_AGOSTINO"), {"SANT_ANDREA": "destra", "SAN_PIETRO": "alto"})
        self.assertEqual(lati("DUOMO_DUCALE"), {"LARGO_BARGELLO": "alto", "MONTE_INGINO": "basso",
                                                "VIA_XX_SETTEMBRE": "sinistra"})


class Monumenti(unittest.TestCase):

    def test_ogni_monumento_in_un_area(self):
        self.assertEqual(M.errori_monumenti(GRAFO, CENS), [])

    def test_monumento_doppio_o_orfano_preso(self):
        g = guasto()
        g["aree"][1]["monumenti"].append("consoli")
        self.assertTrue(any("in 2 aree: consoli" in e for e in M.errori_monumenti(g, CENS)))
        g = guasto()
        g["aree"][0]["monumenti"].remove("ranghiasci")
        self.assertTrue(any("senza area: ranghiasci" in e for e in M.errori_monumenti(g, CENS)))

    def test_scala(self):
        """1 tile = 1,5 m: il Palazzo dei Consoli (39,6 x 34,5 m in OSM) e' 26 x 23 tile."""
        mon = M.calcola_monumenti(GRAFO, CENS)
        self.assertEqual(mon["consoli"]["misure_tile"], [26, 23])
        self.assertEqual(M.tile(39.6), 26)
        self.assertNotEqual(M.tile(60), 26, "il 60 del GDD e' l'altezza, non la pianta")

    def test_eccezione_basilica(self):
        mon = M.calcola_monumenti(GRAFO, CENS)
        self.assertEqual(mon["basilica"]["misure_m"], [50.0, 22.0])
        self.assertEqual(mon["basilica"]["fonte_misure"], "eccezione")

    def test_tracciati_senza_impronta(self):
        """La gola e la via sono percorsi, non edifici da 900 tile."""
        mon = M.calcola_monumenti(GRAFO, CENS)
        for mid in ("gola_bottaccione", "acquedotto", "case_consoli"):
            self.assertEqual(mon[mid]["tipo"], "tracciato", mid)
            self.assertNotIn("misure_tile", mon[mid])
        self.assertEqual(mon["bargello"]["tipo"], "edificio")


class FileGenerati(unittest.TestCase):

    def test_json_aggiornati(self):
        """mondo/monumenti.json e mondo/varchi.json coincidono con quello che il generatore produce oggi."""
        for percorso, doc in M.documenti().items():
            with open(percorso, encoding="utf-8") as f:
                self.assertEqual(f.read(), M.serializza(doc),
                                 "eseguire python tools/mondo_dati.py --scrivi")

    def test_json_vecchio_preso(self):
        """Prova negativa: un monumento con misure diverse non coincide piu'."""
        cens = copy.deepcopy(CENS)
        cens["consoli"]["osm_lato_lungo_m"] = "60"
        docs = M.documenti(GRAFO, cens)
        with open(M.OUT_MONUMENTI, encoding="utf-8") as f:
            self.assertNotEqual(f.read(), M.serializza(docs[M.OUT_MONUMENTI]))


if __name__ == "__main__":
    unittest.main()
