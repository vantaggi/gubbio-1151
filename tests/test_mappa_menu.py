"""La mappa della pausa (MMA): tools/genera_mappa_menu.py e' aggiornato, i nodi sono le aree all'aperto di
mondo/grafo.json, e il cursore (src/menu_mappa.cpp: accanto) arriva a ogni area da ogni altra con le sole frecce."""
import json
import os
import re
import subprocess
import sys
import unittest

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RADICE, "tools"))
import genera_mappa_menu as G  # noqa: E402

MAPPA = open(os.path.join(RADICE, "src", "menu_mappa.cpp"), encoding="utf-8").read()


def accanto(pos, n, dx, dy):
    """Lo stesso di accanto() in src/menu_mappa.cpp."""
    migliore, punti_migliori = -1, 0
    for m, (x, y) in enumerate(pos):
        vx, vy = x - pos[n][0], y - pos[n][1]
        avanti = vx * dx + vy * dy
        lato = abs(vx * dy - vy * dx)
        if m == n or avanti <= 0 or lato > 2 * avanti:
            continue
        punti = avanti + 2 * lato
        if migliore < 0 or punti < punti_migliori:
            migliore, punti_migliori = m, punti
    return migliore


class MappaMenu(unittest.TestCase):
    def setUp(self):
        self.d, self.aree, self.archi = G.carica()
        self.pos = [G.M(p) for p in self.d["nodi"].values()]

    def test_aggiornata(self):
        r = subprocess.run([sys.executable, os.path.join(RADICE, "tools", "genera_mappa_menu.py")],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_nodi_all_aperto(self):
        with open(os.path.join(RADICE, "mondo", "grafo.json"), encoding="utf-8") as f:
            interni = {a["id"] for a in json.load(f)["aree"] if a["id"].endswith("_INTERNO") or a["id"] == "SALA_CONSOLI"}
        self.assertFalse(set(self.d["nodi"]) & interni)
        self.assertEqual(len(self.d["nodi"]), 18)

    def test_ogni_nodo_ha_una_strada(self):
        toccati = {a for arco in self.archi for a in arco}
        self.assertEqual(toccati, set(self.d["nodi"]))

    def test_il_cursore_arriva_ovunque(self):
        n = len(self.pos)
        for partenza in range(n):
            visti, coda = {partenza}, [partenza]
            while coda:
                k = coda.pop()
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    m = accanto(self.pos, k, dx, dy)
                    if m >= 0 and m not in visti:
                        visti.add(m)
                        coda.append(m)
            self.assertEqual(len(visti), n, "da %s non si arriva dappertutto" % list(self.d["nodi"])[partenza])

    def test_il_cursore_del_codice_e_questo(self):
        self.assertIn("int punti = avanti + 2 * lato;", MAPPA)
        self.assertIn("avanti <= 0 || lato > 2 * avanti", MAPPA)

    def test_segni_nel_riquadro(self):
        for x, y in self.pos:
            self.assertTrue(3 <= x <= G.W - 4 and 3 <= y <= G.H - 4, (x, y))


if __name__ == "__main__":
    unittest.main()
