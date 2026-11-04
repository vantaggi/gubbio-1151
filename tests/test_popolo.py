"""La gente della citta' (pezzo VIVA): tools/figure_popolo.py, copione/06_npc_mestieri.md, dati/mestieri.json,
i fratelli di Ciotto in copione/05_npc_amici.md. Regole di STANDARD_GRAFICO.md: M1, A5, A7, L4, C1, P1."""
import json
import os
import re
import sys
import unittest

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RADICE, "tools"))
import figure_popolo as FP  # noqa: E402
import genera_storia as GS  # noqa: E402

MESTIERI = json.load(open(os.path.join(RADICE, "dati", "mestieri.json"), encoding="utf-8"))["mestieri"]
TUTTI = GS.leggi_copione()[1]


def altezza(px):
    """Quante righe occupa la persona (senza l'ombra del suolo)."""
    righe = [y for y, r in enumerate(px) if any(v not in (0, FP.OMBRA_SUOLO) for v in r)]
    return righe[-1] - righe[0] + 1, righe[-1]


class Nomi(unittest.TestCase):
    def test_i_fratelli_di_ciotto(self):
        """Milena e Michele, sorella e fratello di Cioti (4 nov 2026): nel gioco Milia e Michelino."""
        amici = {p["amico"]: p for p in TUTTI if p.get("amico")}
        self.assertEqual(GS.AMICI["MILIA"]["nome"], "Milia")
        self.assertEqual(GS.AMICI["MICHELINO"]["nome"], "Michelino")
        self.assertEqual(amici["MILIA"]["area"], "DUOMO_DUCALE")
        self.assertEqual(amici["MICHELINO"]["area"], "SANT_ANDREA")
        for chi in ("MILIA", "MICHELINO"):
            self.assertEqual({b["fase"] for b in amici[chi]["frasi"]}, {"ULTIMATUM", "DIGIUNO", "NOTTE"})

    def test_ogni_mestiere_del_copione_ha_figura_e_posto(self):
        nel_copione = {p["nome"] for p in TUTTI if p.get("mestiere")}
        self.assertEqual(nel_copione, set(MESTIERI))
        self.assertEqual(len(nel_copione), 21)
        for nome, m in MESTIERI.items():
            self.assertIn(m["figura"], FP.COSTUMI, nome)

    def test_nessun_mestiere_si_confonde_con_un_amico(self):
        """I mestieri non hanno nome proprio: nessun parlante dei mestieri e' un amico o un NPC d'ambiente."""
        parlanti = {}
        for p in TUTTI:
            tipo = "mestiere" if p.get("mestiere") else ("amico" if p.get("amico") else "ambiente")
            for b in p["frasi"]:
                if b["chi"] not in GS.SENZA_NOME and b["chi"] not in ("UBALDO", "GIORGIO", "ANTONIO"):
                    parlanti.setdefault(b["chi"], set()).add(tipo)
        doppi = {chi: t for chi, t in parlanti.items() if len(t) > 1}
        self.assertEqual(doppi, {})

    def test_i_mestieri_non_toccano_la_trama(self):
        """Gente di contorno: nessuna bandiera accesa, nessuna scelta."""
        for p in TUTTI:
            if p.get("mestiere"):
                self.assertIsNone(p["imposta"], p["nome"])
                self.assertFalse(any(b["voci"] for b in p["frasi"] if hasattr(b, "get") and b.get("voci")), p["nome"])

    def test_negativa_mestiere_senza_scheda(self):
        vecchio = dict(GS.MESTIERI)
        try:
            del GS.MESTIERI["Il Fabbro"]
            with self.assertRaisesRegex(GS.ErroreStoria, "dati/mestieri.json"):
                GS.leggi_copione()
        finally:
            GS.MESTIERI.clear()
            GS.MESTIERI.update(vecchio)


class Figure(unittest.TestCase):
    def test_m1_persona_alta_22_24_coi_piedi_alla_riga_31(self):
        for nome, c in FP.COSTUMI.items():
            px = FP.figura(c.con(accessorio=None))          # la persona, senza lance e ceste sopra la testa
            h, piedi = altezza(px)
            self.assertEqual(piedi, 31, nome)
            if c.scala < 1:
                self.assertLess(h, 20, nome)            # il bambino e il ragazzo
            elif c.giu > 0:
                self.assertGreaterEqual(h, 19, nome)    # chi e' bassa (Milia)
                self.assertLess(h, 22, nome)
            else:
                self.assertGreaterEqual(h, 22, nome)
                self.assertLessEqual(h, 26 if c.giu < 0 else 24, nome)      # Gabrione, una testa piu' alto

    def test_l4_ombra_ai_piedi(self):
        for nome, c in FP.COSTUMI.items():
            px = FP.figura(c)
            self.assertGreaterEqual(sum(v == FP.OMBRA_SUOLO for v in px[31] + px[30]), 3, nome)

    def test_p1_contorno(self):
        for nome, c in FP.COSTUMI.items():
            px = FP.figura(c)
            for y in range(32):
                for x in range(16):
                    if px[y][x] not in (0, FP.OMBRA_SUOLO):
                        continue
                    vicini = [px[v][u] for u, v in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
                              if 0 <= u < 16 and 0 <= v < 32]
                    if px[y][x] == 0:
                        pieni = [v for v in vicini if v not in (0, 1, FP.OMBRA_SUOLO)]
                        self.assertEqual(pieni, [], f"{nome}: pixel ({x}, {y}) accanto alla figura senza contorno")

    def test_a5_respiro_e_a7_le_pose_si_distinguono(self):
        for nome in FP.COSTUMI:
            pose = FP.fotogrammi_npc(nome)
            self.assertEqual(len(pose), 4)
            self.assertEqual(len({str(p) for p in pose}), 4, nome)

    def test_a6_camminata_tre_direzioni_sei_fotogrammi(self):
        for nome in FP.PASSANTI:
            self.assertEqual(len(FP.fotogrammi_passante(nome)), 18)

    def test_c1_palette_della_guida(self):
        rampe = {r["nome"]: r for r in json.load(open(os.path.join(RADICE, "stile", "dati", "palette.json"),
                                                       encoding="utf-8"))["rampe"]}
        for nome, tono in FP.PALETTE_POPOLO:
            self.assertLess(tono, len(rampe[nome]["giorno"]))
        self.assertEqual(len(FP.PALETTE_POPOLO), 16)
        h = open(os.path.join(RADICE, "include", "storia.h"), encoding="utf-8").read()
        self.assertIn(", ".join(f"0x{v:04X}" for v in FP.bgr555("giorno")), h)
        self.assertIn(", ".join(f"0x{v:04X}" for v in FP.bgr555("notte")), h)

    def test_p3_nessuna_luce_orfana(self):
        for nome, c in FP.COSTUMI.items():
            for d in FP.DIREZIONI:
                px = FP.figura(c, d)
                for y in range(32):
                    for x in range(16):
                        v = px[y][x]
                        if v in FP.LUCI:
                            vicini = [px[y + j][x + i] for j in (-1, 0, 1) for i in (-1, 0, 1)
                                      if (i or j) and 0 <= x + i < 16 and 0 <= y + j < 32]
                            self.assertIn(v, vicini, f"{nome} {d} ({x}, {y})")

    def test_negativa_p3_luce_orfana(self):
        px = [[0] * 5 for _ in range(5)]
        for y in range(5):
            for x in range(5):
                px[y][x] = 13
        px[2][2] = 14
        self.assertEqual(FP.senza_orfani(px)[2][2], 13)

    def test_barba_sotto_la_bocca(self):
        """La barba non copre il viso: sotto gli occhi resta una riga di pelle (revisione del custode visivo)."""
        for nome in ("anziano", "fabbro", "pastore", "carbonaio", "viandante"):
            px = FP.figura(FP.COSTUMI[nome])
            occhi = min(y for y in range(32) for x in range(16) if px[y][x] == 1 and 0 < x < 15
                        and px[y][x - 1] in (2, 3, 4) and px[y][x + 1] in (2, 3, 4))
            self.assertTrue(any(v in (2, 3, 4) for v in px[occhi + 2]), nome)

    def test_negativa_figura_troppo_alta(self):
        alta = FP.COSTUMI["popolana"].con(giu=-6)
        self.assertGreater(altezza(FP.figura(alta))[0], 24)

    def test_vesti_diverse_per_nome(self):
        """Chi ha la stessa figura base non veste uguale (le tinte dal nome)."""
        mercanti = [a["nome"] for a in GS.AMICI.values() if a["base"] == "mercante" and not a.get("figura")]
        vesti = {FP.costume_npc("mercante", None, n).veste for n in mercanti}
        self.assertGreaterEqual(len(vesti), 3)

    def test_ogni_figura_in_storia_h_ha_quattro_pose(self):
        h = open(os.path.join(RADICE, "include", "storia.h"), encoding="utf-8").read()
        self.assertIn("FIGURA_NPC[FIGURE_NPC][POSE_NPC * 8 * 8]", h)
        n = int(re.search(r"inline constexpr int FIGURE_NPC = (\d+);", h).group(1))
        self.assertEqual(n, len({GS.figura_dell_npc(p) for p in TUTTI}) + 2 + GS.QUEST.__len__())   # + infiltrato, soldato di B-03, datori


if __name__ == "__main__":
    unittest.main()
