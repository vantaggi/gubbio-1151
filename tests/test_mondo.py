"""Il grafo del mondo, verificato leggendo `MAPS[]` invece di percorrerlo.

PERCHE' ESISTE. L'autotest cammina con uno script di tasti indicizzato sul FRAME: per una
singola transizione basta, per un anello di otto tratte no. Ogni tratta che eccede di qualche
frame spinge il giocatore dentro l'area seguente nella direzione sbagliata, e l'errore si
accumula tratta dopo tratta finche' il percorso non e' piu' quello previsto. Ci si e' cascati
quattro volte di fila nella Sessione 21, ogni volta credendo di aver corretto l'ultima.

La topografia non ha pero' bisogno di essere CAMMINATA per essere verificata: e' una proprieta'
della tabella, e la tabella si legge. Questi test provano che il mondo e' cucito bene —
reciprocita' dei varchi, indici di rientro validi, anello chiuso. Quello che NON provano, e che
resta compito dell'autotest e del giocare, e' che i varchi siano RAGGIUNGIBILI camminando: un
varco murato dietro un ostacolo passerebbe di qui indisturbato.
"""

import os
import re
import unittest

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def leggi_maps():
    """Estrae il grafo da include/map_data.h: per ogni area, i varchi che ne escono.

    La tabella e' generata, quindi regolare, e una regex basta. Se un domani venisse riscritta
    a mano in una forma diversa, questi test fallirebbero rumorosamente invece di passare
    misurando il nulla — ed e' il comportamento che si vuole.
    """
    testo = open(os.path.join(RADICE, "include", "map_data.h"), encoding="utf-8").read()
    corpo = testo[testo.index("MAPS[MAP_COUNT] = {"):testo.index("static_assert(int(sizeof(MAPS)")]

    # L'ordine delle righe E' l'ordine dei MapId: la riga i-esima descrive l'area i-esima.
    ordine = re.findall(r"^\s*// --- ([A-Z_]+)(?:,| ---)", corpo, re.M)

    aree = {}
    pezzi = re.split(r"^\s*// --- ", corpo, flags=re.M)[1:]

    for pezzo in pezzi:
        nome = re.match(r"([A-Z_]+)", pezzo).group(1)
        if nome in aree:
            continue
        varchi = re.findall(r"int16_t\(MapId::([A-Z_]+)\),\s*(\w+)\}", pezzo)
        spawn = len(re.findall(r"spawn_at_tile\(", pezzo))
        implementata = ".collision = maps::" in pezzo
        aree[nome] = {"varchi": varchi, "spawn": spawn, "implementata": implementata}

    return aree, ordine


# Le costanti simboliche usate come indice di rientro, con il loro valore.
INDICI = {"SPAWN_AREA_CENTRO": 0, "SPAWN_AREA_DA_MONTE": 1, "SPAWN_AREA_DA_VALLE": 2,
          "SPAWN_PIAZZA_DA_CONSOLI": 1, "SPAWN_PIAZZA_DA_EST": 2, "SPAWN_PIAZZA_DA_OVEST": 3,
          "SPAWN_BARGELLO_DA_PIAZZA": 1}


def indice(v):
    return INDICI[v] if v in INDICI else int(v)


class MondoTest(unittest.TestCase):

    def setUp(self):
        self.aree, self.ordine = leggi_maps()

    def test_ogni_varco_porta_a_un_area_autorata(self):
        """Un varco verso un'area non autorata deposita il giocatore in una scena vuota."""
        for nome, dati in self.aree.items():
            for dest, _ in dati["varchi"]:
                self.assertTrue(self.aree.get(dest, {}).get("implementata"),
                                "%s ha un varco verso %s, che non e' autorata" % (nome, dest))

    def test_ogni_rientro_esiste(self):
        """L'indice di rientro deve stare dentro l'elenco degli spawn dell'area di arrivo.

        Fuori intervallo la scena ripiega sullo spawn 0 (scene_exploration.cpp), quindi il
        difetto NON crasha: deposita semplicemente il giocatore nel posto sbagliato, il che e'
        molto piu' difficile da notare.
        """
        for nome, dati in self.aree.items():
            for dest, idx in dati["varchi"]:
                n = self.aree[dest]["spawn"]
                self.assertLess(indice(idx), n,
                                "%s -> %s rientra sullo spawn %s, ma %s ne ha %d" %
                                (nome, dest, idx, dest, n))

    def test_ogni_varco_e_percorribile_nei_due_sensi(self):
        """Chi entra da una porta deve poterne uscire. Un varco a senso unico intrappola."""
        for nome, dati in self.aree.items():
            for dest, _ in dati["varchi"]:
                if dest == nome:
                    continue          # il portone dei Consoli rimanda alla piazza stessa
                ritorni = [d for d, _ in self.aree[dest]["varchi"]]
                self.assertIn(nome, ritorni,
                              "Da %s si entra in %s, ma da %s non si torna a %s" %
                              (nome, dest, dest, nome))

    def test_l_anello_si_chiude(self):
        """L'anello dettato dal committente, percorso sulla tabella invece che sulla ROM.

        Piazza Grande -> Duomo -> stradoni -> Basilica -> Bottaccione -> San Martino ->
        Bargello -> via dei Consoli -> Piazza Grande. E' la struttura del mondo, non un
        dettaglio: la citta' e' costruita attorno al Monte Ingino e ci si gira intorno.
        """
        anello = ["PIAZZA_GRANDE", "DUOMO_DUCALE", "MONTE_INGINO", "BASILICA", "BOTTACCIONE",
                  "SAN_MARTINO", "LARGO_BARGELLO", "VIA_DEI_CONSOLI", "PIAZZA_GRANDE"]

        for a, b in zip(anello, anello[1:]):
            uscite = [d for d, _ in self.aree[a]["varchi"]]
            self.assertIn(b, uscite, "L'anello si spezza fra %s e %s" % (a, b))

    def test_nessuna_area_e_un_vicolo_cieco(self):
        """Ogni area autorata deve avere almeno un varco, altrimenti ci si resta dentro."""
        for nome, dati in self.aree.items():
            if dati["implementata"]:
                self.assertTrue(dati["varchi"], "%s non ha nessuna uscita" % nome)


if __name__ == "__main__":
    unittest.main(verbosity=2)
