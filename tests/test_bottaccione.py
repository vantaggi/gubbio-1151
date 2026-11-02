"""Il dungeon della gola del Bottaccione (pezzo T): quattro stanze lungo il Camignano, dal Bottaccione al
Condotto (mondo/aree/gola_*.area, condotto.area, mondo/grafo.json), le scene B-01..B-04 una per stanza
nell'ordine della gola, Corrado sul Condotto, la palette cupa.
"""
import copy
import importlib.util
import os
import re
import sys
import unittest
from collections import deque

from _stile import RADICE

sys.path.insert(0, os.path.join(RADICE, "tools"))
import mondo_dati as M  # noqa: E402

_spec = importlib.util.spec_from_file_location("genera_mondo", os.path.join(RADICE, "tools", "genera_mondo.py"))
G = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(G)
_spec_s = importlib.util.spec_from_file_location("genera_storia", os.path.join(RADICE, "tools", "genera_storia.py"))
GS = importlib.util.module_from_spec(_spec_s)
_spec_s.loader.exec_module(GS)
_spec_i = importlib.util.spec_from_file_location("istantanee", os.path.join(RADICE, "tools", "istantanee.py"))
I = importlib.util.module_from_spec(_spec_i)
_spec_i.loader.exec_module(I)

GOLA = ["BOTTACCIONE", "GOLA_STRISCIA", "GOLA_MIASMI", "GOLA_ARCO", "CONDOTTO"]
SCENE_DELLA_GOLA = ["B-01", "B-02", "B-03", "B-04"]
PROGRESSIONE = open(os.path.join(RADICE, "include", "progressione.h"), encoding="utf-8").read()


def raggiungibili(griglia, partenza):
    """Le celle calpestabili che si raggiungono camminando da 'partenza' (i varchi compresi)."""
    h, w = len(griglia), len(griglia[0])
    visti, coda = {partenza}, deque([partenza])
    while coda:
        x, y = coda.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in visti:
                c = griglia[ny][nx]
                if c in G.VARCHI or not G.CELLE[c][1]:
                    visti.add((nx, ny))
                    coda.append((nx, ny))
    return visti


def in_ordine(aree_delle_scene):
    """Le scene stanno in stanze sempre piu' avanti lungo la gola."""
    passi = [GOLA.index(a) for a in aree_delle_scene]
    return all(b > a for a, b in zip(passi, passi[1:]))


class Gola(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.grafo = M.carica_grafo()
        cls.aree = {a["id"]: a for a in I.aree_finali()}

    def test_le_stanze_in_fila_lungo_la_gola(self):
        """Ogni stanza confina solo con quella prima e quella dopo; il Condotto e' in fondo; si sale."""
        vicini = {}
        for e in self.grafo["archi"]:
            vicini.setdefault(e["da"], set()).add(e["a"])
            vicini.setdefault(e["a"], set()).add(e["da"])
        for i, aid in enumerate(GOLA[1:], 1):
            attesi = {GOLA[i - 1]} | ({GOLA[i + 1]} if i + 1 < len(GOLA) else set())
            self.assertEqual(vicini[aid], attesi, aid)
        quote = {a["id"]: M.quota_media(a) for a in self.grafo["aree"]}
        self.assertTrue(all(quote[a] < quote[b] for a, b in zip(GOLA, GOLA[1:])))
        self.assertEqual(M.errori_connessione(self.grafo), [])

    def test_negativa_senza_un_arco_il_condotto_non_si_raggiunge(self):
        rotto = copy.deepcopy(self.grafo)
        rotto["archi"] = [e for e in rotto["archi"] if (e["da"], e["a"]) != ("GOLA_ARCO", "CONDOTTO")]
        self.assertIn("area irraggiungibile: CONDOTTO", M.errori_connessione(rotto))

    def test_in_ogni_stanza_si_cammina_da_varco_a_varco(self):
        for aid in GOLA[1:]:
            a = self.aree[aid.lower()]
            g = a["griglia"]
            visti = raggiungibili(g, a["spawn"][0])
            varchi = {(x, y) for y, r in enumerate(g) for x, c in enumerate(r) if c in G.VARCHI}
            self.assertTrue(varchi and varchi <= visti, aid)

    def test_negativa_via_murata(self):
        a = self.aree["gola_miasmi"]
        g = [list(r) for r in a["griglia"]]
        for y in range(len(g)):
            g[y][32] = "#"
        visti = raggiungibili(["".join(r) for r in g], a["spawn"][0])
        varchi = {(x, y) for y, r in enumerate(g) for x, c in enumerate(r) if c in G.VARCHI}
        self.assertFalse(varchi <= visti)

    def test_corrado_sul_condotto(self):
        """Il Colosso sta nel Condotto, su una cella calpestabile che si raggiunge dall'ingresso."""
        m = re.search(r"\{ mondo::AreaId::(\w+), (\d+), (\d+), 2, Bandiera::CORRADO_SCONFITTO \}", PROGRESSIONE)
        area, tx, ty = m.group(1), int(m.group(2)), int(m.group(3))
        self.assertEqual(area, "CONDOTTO")
        a = self.aree["condotto"]
        self.assertIn((tx, ty), raggiungibili(a["griglia"], a["spawn"][0]))

    def test_negativa_corrado_nella_rupe(self):
        a = self.aree["condotto"]
        self.assertNotIn((50, 2), raggiungibili(a["griglia"], a["spawn"][0]))

    def test_b01_b04_una_per_stanza_nell_ordine(self):
        self.assertEqual([GS.AREE[c] for c in SCENE_DELLA_GOLA], GOLA[1:])
        self.assertTrue(in_ordine([GS.AREE[c] for c in SCENE_DELLA_GOLA]))
        self.assertEqual([GS.SEGUE[c] for c in SCENE_DELLA_GOLA[1:]], SCENE_DELLA_GOLA[:-1])
        log = open(os.path.join(RADICE, "tests", "dati", "storia_mgba.txt"), encoding="utf-8").read()
        visti = [c for c in re.findall(r"^Scena (\S+)$", log, re.M) if c in SCENE_DELLA_GOLA]
        self.assertEqual(visti, SCENE_DELLA_GOLA)

    def test_negativa_scene_scambiate(self):
        self.assertFalse(in_ordine(["GOLA_STRISCIA", "GOLA_ARCO", "GOLA_MIASMI", "CONDOTTO"]))

    def test_palette_cupa_solo_nella_gola(self):
        h = open(os.path.join(RADICE, "include", "mondo.h"), encoding="utf-8").read()
        blocchi = re.findall(r"\{   // (\w+)\n(.*?)\n    \},", h, re.S)
        self.assertEqual(len(blocchi), 19)
        for blocco in blocchi:
            aid, corpo = blocco
            cupa = corpo.strip().endswith("true,")
            self.assertEqual(cupa, aid in G.AREE_GOLA, aid)
        self.assertIn("PALETTE_FONDALI_CUPA[16]", h)

    def test_negativa_la_cupa_non_e_quella_del_giorno(self):
        from _stile import S
        palette = S.carica("palette")
        giorno = [S.colore(palette, r) for r in G.PALETTE_FONDALI]
        notte = [S.colore(palette, r, True) for r in G.PALETTE_FONDALI]
        self.assertNotEqual(giorno, notte)


if __name__ == "__main__":
    unittest.main(verbosity=2)
