"""Rigenera i dati di stile che nascono da parametri: palette, cornici, pose.
Font, logo e ritratti sono disegnati a mano come dati e non passano di qui.

    python stile/genera.py            # riscrive stile/dati/{palette,cornice,pose}.json
    python stile/esporta_cpp.py       # poi rigenera gli header constexpr
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stile as S

# ---------------------------------------------------------------------------------------------
# Scelta 3: palette. Valori della tavola tavole_palette.py (variante A, hue shift 10).
PARAMETRI = {
    "hue_shift_per_tono": 10,
    "rampe": [
        {"nome": n, "tinta": h, "toni": t, "saturazione_max": s, "luce_min": a, "luce_max": b}
        for n, h, t, s, a, b in [
            ("pietra calcarea", 40, 6, 0.28, 0.30, 0.95),
            ("cotto e coppi", 14, 6, 0.62, 0.22, 0.88),
            ("vermiglio comunale", 356, 4, 0.85, 0.22, 0.85),
            ("verde dei monti", 100, 5, 0.45, 0.20, 0.80),
            ("cielo e acqua", 205, 5, 0.50, 0.35, 0.95),
            ("legno e cuoio", 28, 4, 0.55, 0.18, 0.65),
            ("oro e bronzo", 45, 4, 0.75, 0.40, 0.95),
            ("pelle", 22, 3, 0.40, 0.55, 0.92),
            ("neutri", 230, 5, 0.10, 0.08, 0.98),
        ]
    ],
    # notte e Bottaccione: cambio di palette, la grafica non cambia (scelte 1 e 3)
    "notte": {"luce": 0.55, "saturazione": 0.6, "blu": 1.15,
              "canali": [[200, 10], [215, 14], [235, 30]]},
}


def palette():
    return {
        "nota": "Scelta 3. Parole BGR555 (bit 0-4 rosso, 5-9 verde, 10-14 blu), toni dal piu' scuro "
                "al piu' chiaro. 'notte' e' la stessa rampa trasformata: vale per la notte e per il "
                "Bottaccione. Non modificare a mano: cambiare 'parametri' e lanciare stile/genera.py.",
        "parametri": PARAMETRI,
        "rampe": S.calcola_palette(PARAMETRI),
    }


# ---------------------------------------------------------------------------------------------
# Scelta 9: cornice a vetrata, tile 8x8 a 4bpp
def cornice():
    colori = [None,
              ["legno e cuoio", 0],        # 1 piombo, testo scuro
              ["neutri", 4],               # 2 fondo chiaro, riflesso, testo del cartiglio
              ["vermiglio comunale", 2],   # 3 tessera, cartiglio, cursore
              ["oro e bronzo", 2],         # 4 tessera
              ["cielo e acqua", 2],        # 5 tessera
              ["verde dei monti", 3],      # 6 tessera
              ["cielo e acqua", 3],        # 7 tessera
              ["vermiglio comunale", 1],   # 8 tessera
              ["oro e bronzo", 3]]         # 9 rosetta
    colori += [None] * (16 - len(colori))

    def oriz(t):
        return ["11111111", t * 7 + "1", t + "2" + t * 5 + "1"] + [t * 7 + "1"] * 4 + ["11111111"]

    def vert(t):
        return ["1" + t * 6 + "1", "1" + t + "2" + t * 4 + "1"] + ["1" + t * 6 + "1"] * 5 + ["11111111"]

    tile = {
        "angolo": ["11111111", "11999911", "19999991", "19933991",
                   "19933991", "19999991", "11999911", "11111111"],
        "oriz_0": oriz("3"), "oriz_1": oriz("4"), "oriz_2": oriz("5"),
        "vert_0": vert("6"), "vert_1": vert("7"), "vert_2": vert("8"),
        "centro": ["22222222"] * 8,
        "cartiglio_sx": ["11111111"] + ["13333333"] * 7,
        "cartiglio_centro": ["11111111"] + ["33333333"] * 7,
        "cursore": ["00000000", "11000000", "13100000", "13310000",
                    "13331000", "13310000", "13100000", "11000000"],
    }
    return {
        "nota": "Scelta 9. Tile 8x8 a 4bpp, una cifra esadecimale per pixel = indice nella "
                "sottopalette 'colori' (0 trasparente). Un riquadro di qualunque misura (almeno 3x3 "
                "tile) si compone con 'regole' (stile.componi_cornice): angolo con flip hardware, lati "
                "a tessere alternate, centro pieno. Il cartiglio e' alto 2 tile: la riga di sotto e' "
                "quella di sopra con vflip, l'estremita' destra e' la sinistra con hflip.",
        "colori": colori,
        "ruoli": {"piombo": 1, "fondo": 2, "riflesso": 2, "testo": 1, "testo_cartiglio": 2,
                  "tessere": [3, 4, 5, 6, 7, 8], "rosetta": 9},
        "tile": tile,
        "regole": {"angolo": "angolo", "lato_orizzontale": ["oriz_0", "oriz_1", "oriz_2"],
                   "lato_verticale": ["vert_0", "vert_1", "vert_2"], "centro": "centro",
                   "cartiglio": ["cartiglio_sx", "cartiglio_centro"], "cursore": "cursore"},
        "disposizione": {
            "dialogo": {"x": 0, "y": 104, "colonne": 30, "righe": 7, "righe_testo_max": 3,
                        "testo": [8, 112], "ritratto": [10, 113]},
            "cartiglio_nome": {"x": 8, "y": 96, "righe": 2},
            "menu": {"x": 168, "y": 8, "colonne": 8, "righe": 6, "passo_voci": 10, "voci_max": 3},
        },
    }


# ---------------------------------------------------------------------------------------------
# Scelta 11: scheletro delle pose. Sprite 16x32, corpo 16x24 dalla riga 8, piedi sulla riga 31.
CX, Y0 = 8, 8
GIUNTI = ["testa", "collo", "bacino", "mano_a", "mano_b", "piede_a", "piede_b"]


def lato(passo=0, braccio=0, chino=0, bob=0, mano=None):
    """Vista di lato verso destra: _a e' l'arto davanti, _b quello dietro."""
    g = {
        "testa": [CX + chino, Y0 + 5 + bob], "collo": [CX + chino, Y0 + 9 + bob],
        "bacino": [CX, Y0 + 16 + bob],
        "mano_a": [CX + braccio + chino, Y0 + 15 + bob], "mano_b": [CX - braccio + chino, Y0 + 15 + bob],
        "piede_a": [CX + passo, Y0 + 23], "piede_b": [CX - passo, Y0 + 23],
    }
    if mano:
        g["mano_a"] = [mano[0], Y0 + mano[1]]
    return g


def fronte(su_a=0, su_b=0, bob=0, mano_a=None, chino=0):
    g = {
        "testa": [CX, Y0 + 5 + bob + chino], "collo": [CX, Y0 + 9 + bob + chino],
        "bacino": [CX, Y0 + 16 + bob],
        "mano_a": [CX - 5, Y0 + 14 + su_b + bob], "mano_b": [CX + 4, Y0 + 14 + su_a + bob],
        "piede_a": [CX - 2, Y0 + 23 - su_a], "piede_b": [CX + 1, Y0 + 23 - su_b],
    }
    if mano_a:
        g["mano_a"] = [CX - 5, Y0 + mano_a]
    return g


def tutte(lat, fr):
    return {"destra": lat, "giu": fr, "su": fr}


def pose():
    an = {}
    # camminata: 6 fotogrammi da 6 vblank (scelta 11, variante C). Contatto a 0 e 3, corpo
    # piu' alto di un pixel nei fotogrammi di passaggio.
    # (x piede a, x piede b, piede a alzato, piede b alzato): contatto a 0 e 3, il piede che
    # avanza si stacca da terra; di fronte il piede davanti sta un pixel piu' in basso.
    passi = [(3, -3, 0, 0), (1, -1, 0, 2), (-1, 1, 0, 1), (-3, 3, 0, 0), (-1, 1, 2, 0), (1, -1, 1, 0)]
    cam = []
    for i, (xa, xb, la, lb) in enumerate(passi):
        bob = 0 if i in (0, 3) else -1
        braccio = -round(xa * 2 / 3)
        lat = lato(0, braccio, bob=bob)
        lat["piede_a"] = [CX + xa, Y0 + 23 - min(la, 1)]
        lat["piede_b"] = [CX + xb, Y0 + 23 - min(lb, 1)]
        fr = fronte(la, lb, bob=bob)
        if i == 0:
            fr["piede_b"][1] -= 1
        if i == 3:
            fr["piede_a"][1] -= 1
        cam.append({"vblank": 6, "giunti": tutte(lat, fr)})
    an["camminata"] = {"ciclo": True, "fotogrammi": cam}
    an["riposo"] = {"ciclo": True, "fotogrammi": [
        {"vblank": 30, "giunti": tutte(lato(), fronte())},
        {"vblank": 30, "giunti": tutte(lato(bob=1), fronte(chino=1))},
    ]}
    # attacco con la lancia: (posa, vblank, passo, chino, mano rispetto al corpo, punta dell'arma)
    att = [("pronto", 12, 3, 0, (CX + 1, 11), (0, -8)),
           ("anticipa", 10, 1, -2, (CX - 5, 11), (-10, -2)),
           ("colpo", 3, 4, 2, (CX + 7, 11), (9, 0)),
           ("tenuta", 12, 4, 2, (CX + 7, 11), (9, 0)),
           ("rientro", 8, 2, 1, (CX + 4, 11), (6, 0))]
    fot = []
    for nome, vb, passo, chino, mano, punta in att:
        f = {"posa": nome, "vblank": vb,
             "giunti": tutte(lato(passo, 0, chino, mano=mano),
                             fronte(mano_a={"anticipa": 9, "colpo": 16, "tenuta": 16}.get(nome, 12))),
             "arma": {"mano": "mano_a", "punta": list(punta)}}
        if nome == "colpo":
            f["scia"] = True
        fot.append(f)
    an["attacco"] = {"ciclo": False, "fotogrammi": fot}
    an["colpito"] = {"ciclo": False, "provvisorio": "durate non fissate dalla guida: da provare in F1",
                     "fotogrammi": [
                         {"posa": "lampo", "vblank": 4, "lampo": True, "giunti": tutte(lato(), fronte())},
                         {"posa": "arretramento", "vblank": 8,
                          "giunti": tutte(lato(1, 0, -2), fronte(chino=-1))}]}
    return {
        "nota": "Scelta 11. Scheletro unico per tutti i personaggi: gli strati (veste, elmo, armi) "
                "si appoggiano ai giunti. Coordinate in pixel dentro lo sprite 16x32, origine in alto "
                "a sinistra. Tempi in vblank (1/60 s). Sinistra = destra con flip orizzontale "
                "hardware. Polvere e scintille sono particelle separate.",
        "sprite": [16, 32], "corpo": [16, 24], "linea_piedi": Y0 + 23, "vblank_al_secondo": 60,
        "giunti": GIUNTI, "direzioni": ["giu", "su", "destra"], "specchiate": {"sinistra": "destra"},
        "animazioni": an,
    }


if __name__ == "__main__":
    S.salva("palette", palette())
    S.salva("cornice", cornice())
    S.salva("pose", pose())
    print("palette, cornice, pose rigenerate")
