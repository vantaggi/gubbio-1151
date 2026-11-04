#!/usr/bin/env python3
"""I ritratti del dialogo dei quattro personaggi che li hanno nel copione (README del copione:
Ubaldo, Giorgio, Antonio, Guido), con le tre espressioni della scelta di stile 10.

Il pittore vero e' stile.componi_ritratto: sovrappone maschere di ruoli 32x32 e aggiunge il
contorno quasi nero. Qui stanno gli strati nuovi (vesti, capelli, barba, copricapi) e i tre
personaggi nuovi; lo script li fonde in stile/dati/ritratti.json, che resta l'unico dato letto
da genera_bmp.py e dai controlli. Ubaldo era gia' nei dati e non cambia.

Le scelte di aspetto seguono gli sprite di battaglia (tools/genera_battaglia.py) e le sagome
di C3, cosi' il personaggio si riconosce da un riquadro all'altro:
  Giorgio  giovane cavaliere: cotta di maglia, sopravveste bianca con la croce rossa, capelli
           biondi con un ciuffo sulla fronte, senza barba.
  Antonio  eremita: saio col cappuccio, barba bianca lunga, il tau al petto (Sant'Antonio abate).
  Guido    console: berretto e mantello vermiglio del comune col bavero di pelliccia e il
           fermaglio d'oro, tempie grigie, rasato.
Nessun colore nuovo: ogni ruolo punta a una rampa della palette bloccata (controlla_ritratti).

    python3 tools/pittore_ritratti.py              # aggiorna stile/dati/ritratti.json
    python3 tools/pittore_ritratti.py --verifica   # esce con 1 se il dato non e' allineato
    python3 tools/pittore_ritratti.py --tavola t.png   # tavola di controllo (richiede Pillow)
Dopo l'aggiornamento: python3 stile/genera_bmp.py (graphics/ritratto_*.bmp).
"""
import copy
import os
import sys

RADICE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(RADICE, "stile"))

import stile as S  # noqa: E402

LATO = 32

# I personaggi con ritratto secondo il copione, nell'ordine dei cartigli.
CON_RITRATTO = ["Ubaldo", "Giorgio", "Antonio", "Guido"]


def maschera(righe):
    """Da {riga: stringa di 32 caratteri} alla maschera 32x32 dei dati ('.' = vuoto)."""
    m = ["." * LATO for _ in range(LATO)]
    for y, r in righe.items():
        if len(r) != LATO:
            raise ValueError(f"riga {y}: {len(r)} caratteri invece di {LATO}")
        m[y] = r
    return m


#           0         1         2         3
#           01234567890123456789012345678901
STRATI = {
    "veste": {
        # cotta di maglia sulle spalle (m in luce, M in ombra) e sopravveste con la croce (X)
        "cotta_croce": {
            24: "...........mm......MM...........",
            25: "....mmmmmVVVVVVXXvvvvvvMMMMM....",
            26: "...mmmmmmVVVVVVXXvvvvvvMMMMMM...",
            27: "...mmmmmmVVXXXXXXXXXXvvMMMMMM...",
            28: "...mmmmmmVVVVVVXXvvvvvvMMMMMM...",
            29: "...mmmmmmVVVVVVXXvvvvvvMMMMMM...",
            30: "...mmmmmmVVVVVVXXvvvvvvMMMMMM...",
            31: "...mmmmmmVVVVVVXXvvvvvvMMMMMM...",
        },
        # saio con le spalle cadenti e il tau d'oro sul lato in luce
        "saio_tau": {
            25: "....VVVVVVVVVVVVvvvvvvvvvvvv....",
            26: "...VVVVVVVVVVVVVvvvvvvvvvvvvv...",
            27: "...VVVVVVoooooVVvvvvvvvvvvvvv...",
            28: "...VVVVVVVVoVVVVvvvvvvvvvvvvv...",
            29: "...VVVVVVVVoVVVVvvvvvvvvvvvvv...",
            30: "...VVVVVVVVoVVVVvvvvvvvvvvvvv...",
            31: "...VVVVVVVVVVVVVvvvvvvvvvvvvv...",
        },
        # mantello del console: bavero di pelliccia (w luce, g ombra), fermaglio d'oro
        "mantello_console": {
            24: "..........www......ggg..........",
            25: "....wwwwwwwwwwwoogggggggggggg...",
            26: "...VVVVVVwwwwwwooggggggvvvvvv...",
            27: "...VVVVVVVVVVVVVvvvvvvvvvvvvv...",
            28: "...VVVVVVVVVVVVVvvvvvvvvvvvvv...",
            29: "...VVVVVVVVVVVVVvvvvvvvvvvvvv...",
            30: "...VVVVVVVVVVVVVvvvvvvvvvvvvv...",
            31: "...VVVVVVVVVVVVVvvvvvvvvvvvvv...",
        },
    },
    "barba": {
        # lunga, bianca, che scende sul saio (B in luce, Z in ombra)
        "lunga": {
            18: "..........BBBBBBBBBBZZ..........",
            19: "..........BBBBBBBBBBZZ..........",
            20: "..........BBBBBBBBBBZZ..........",
            21: "...........BBBBBBBBBZZ..........",
            22: "...........BBBBBBBBBZZ..........",
            23: "............BBBBBBBZZ...........",
            24: "............BBBBBBBZZ...........",
            25: ".............BBBBBZZ............",
            26: ".............BBBBBZZ............",
            27: "..............BBBZ..............",
            28: "...............BZ...............",
        },
    },
    "capelli": {
        # biondi, il ciuffo che cade sulla fronte (C luce, c ombra a destra)
        "ciuffo": {
            4: "............CCCCCc..............",
            5: "..........CCCCCCCCcc............",
            6: ".........CCCCCCCCCccc...........",
            7: "........CCCCCCCCCCcccc..........",
            8: "........CCCCCCCCCCCcccc.........",
            9: ".......CCCCCCCCCCCCcccc.........",
            10: ".......CCCC..CCCC...ccc.........",
            11: ".......CCC....CC.....cc.........",
            12: ".......CC.............c.........",
            13: ".......CC..............c........",
            14: ".......CC..............c........",
            15: ".......CC.......................",
        },
        # solo le tempie grigie sotto il berretto
        "tempie": {
            11: "........CC............cc........",
            12: "........CC............cc........",
            13: ".......CC..............c........",
            14: ".......CC..............c........",
            15: ".......CC..............c........",
            16: "........C.......................",
        },
    },
    "copricapo": {
        # cappuccio del saio, aperto sul viso (V luce, v ombra)
        "cappuccio": {
            3: "............VVVVVv..............",
            4: "..........VVVVVVVVvv............",
            5: ".........VVVVVVVVVvvv...........",
            6: "........VVVVVVVVVVvvvv..........",
            7: ".......VVVVVVVVVVVvvvvv.........",
            8: ".......VVVVVVVVVVVvvvvv.........",
            9: "......VVVVV.........vvvvv.......",
            10: "......VVVVV..........vvvv.......",
            11: "......VVVV............vvvv......",
            12: "......VVVV............vvvv......",
            13: "......VVVV............vvvv......",
            14: "......VVVV............vvvv......",
            15: "......VVVV............vvvv......",
            16: "......VVVV............vvvv......",
            17: "......VVVV............vvvv......",
            18: "......VVVV............vvvv......",
            19: "......VVVV............vvvv......",
            20: "......VVVV............vvvv......",
            21: "......VVVV............vvvv......",
            22: ".......VVVV..........vvvv.......",
            23: ".......VVVVV........vvvvv.......",
            24: ".....VVVVVVV........vvvvvvv.....",
        },
        # berretto tondo del console con la tesa scura (K)
        "berretto": {
            3: "..............VVVv..............",
            4: "...........VVVVVVVvvv...........",
            5: "..........VVVVVVVVvvvv..........",
            6: ".........VVVVVVVVVvvvvv.........",
            7: ".........VVVVVVVVVvvvvv.........",
            8: "........VVVVVVVVVVvvvvvv........",
            9: "........vvvvvvvvvvKKKKKK........",
            10: "........vvvvvvvvvvKKKKKK........",
        },
    },
}

PERSONAGGI = {
    "Giorgio": {
        "strati": {"veste": "cotta_croce", "viso": "adulto", "occhi": "base", "barba": None,
                   "capelli": "ciuffo", "copricapo": None},
        "colori": {"V": ["neutri", 4], "v": ["neutri", 3], "X": ["vermiglio comunale", 2],
                   "S": ["oro e bronzo", 1], "C": ["oro e bronzo", 2], "c": ["oro e bronzo", 1]},
    },
    "Antonio": {
        "strati": {"veste": "saio_tau", "viso": "vecchio", "occhi": "base", "barba": "lunga",
                   "capelli": None, "copricapo": "cappuccio"},
        "colori": {"V": ["legno e cuoio", 2], "v": ["legno e cuoio", 1], "S": ["neutri", 2],
                   "B": ["neutri", 4], "Z": ["neutri", 3]},
    },
    "Guido": {
        "strati": {"veste": "mantello_console", "viso": "adulto", "occhi": "base", "barba": None,
                   "capelli": "tempie", "copricapo": "berretto"},
        "colori": {"V": ["vermiglio comunale", 2], "v": ["vermiglio comunale", 1],
                   "K": ["vermiglio comunale", 0], "S": ["neutri", 2], "C": ["neutri", 3],
                   "c": ["neutri", 2]},
    },
}


# Coppie (luce, ombra) degli strati nuovi: la luce viene da alto-sinistra (scelta 4), quindi in
# ogni maschera il tono in ombra sta in media a destra di quello in luce.
COPPIE_LUCE = [("V", "v"), ("C", "c"), ("B", "Z"), ("m", "M"), ("w", "g")]


def controlla_luce(strati):
    err = []
    for s, varianti in strati.items():
        for v, righe in varianti.items():
            m = maschera(righe)
            for luce, ombra in COPPIE_LUCE:
                xl = [x for r in m for x, ch in enumerate(r) if ch == luce]
                xo = [x for r in m for x, ch in enumerate(r) if ch == ombra]
                if xl and xo and sum(xo) / len(xo) <= sum(xl) / len(xl):
                    err.append(f"strato {s}/{v}: l'ombra {ombra} non sta a destra della luce {luce}")
    return err


def parlanti_con_espressione(cartella):
    """I parlanti del copione che hanno almeno una battuta con espressione: '- NOME (espr): ...'."""
    import re
    esp = re.compile(r"\b([A-Z]{3,}) \((calmo|preoccupato|deciso)\)")
    trovati = set()
    for nome in sorted(os.listdir(cartella)):
        if nome.endswith(".md") and nome[0].isdigit():
            with open(os.path.join(cartella, nome), encoding="utf-8") as f:
                trovati |= {m.group(1) for m in esp.finditer(f.read())}
    return trovati


def controlla_copertura(rt, parlanti):
    """Ogni parlante con espressione ha il suo ritratto, con le tre espressioni."""
    err = []
    nomi = {n.upper(): n for n in rt["personaggi"]}
    for chi in sorted(parlanti):
        if chi not in nomi:
            err.append(f"{chi} parla con espressione ma non ha ritratto")
    for n in CON_RITRATTO:
        if n not in rt["personaggi"]:
            err.append(f"manca il ritratto di {n}")
    return err


def dati_attesi(rt):
    """ritratti.json con gli strati e i personaggi di questo file fusi dentro."""
    out = copy.deepcopy(rt)
    for s, varianti in STRATI.items():
        for v, righe in varianti.items():
            out["strati"][s][v] = maschera(righe)
    for nome, p in PERSONAGGI.items():
        out["personaggi"][nome] = copy.deepcopy(p)
    return out


def tavola(percorso, z=4):
    """I quattro ritratti nelle tre espressioni, e ciascuno nel riquadro di dialogo."""
    from PIL import Image, ImageDraw
    sys.path.insert(0, os.path.join(RADICE, "stile"))
    import anteprime as A

    rt, p = S.carica("ritratti"), S.carica("palette")
    fondo = S.rgb_di(S.colore(p, ["pietra calcarea", 4]))
    celle = Image.new("RGB", (3 * 36 + 4, len(CON_RITRATTO) * 36 + 4), fondo)
    for j, nome in enumerate(CON_RITRATTO):
        for i, e in enumerate(rt["espressioni"]):
            px, _ = S.componi_ritratto(rt, p, nome, e)
            for y, r in enumerate(px):
                for x, c in enumerate(r):
                    if c is not None:
                        celle.putpixel((4 + i * 36 + x, 4 + j * 36 + y), S.rgb_di(c))
    grande = celle.resize((celle.width * z, celle.height * z), Image.NEAREST)

    frasi = {"Ubaldo": ("preoccupato", "Undici città marciano su Gubbio. Chi può, resti al suo posto."),
             "Giorgio": ("deciso", "Datemi venti cavalieri e li ricaccio io giù per la piana."),
             "Antonio": ("calmo", "Fino al monte, poi vedremo. La legna non si accende da sola."),
             "Guido": ("preoccupato", "Grano per quaranta giorni, uomini per trenta. E poi?")}
    schermi = []
    for nome in CON_RITRATTO:
        e, frase = frasi[nome]
        schermi.append(schermo(A, rt, p, nome, e, frase))
    W = grande.width + 24 + 2 * (240 * 2) + 16
    H = max(grande.height, 2 * (160 * 2) + 16) + 70
    out = Image.new("RGB", (W, H), (245, 243, 238))
    d = ImageDraw.Draw(out)
    d.text((16, 10), "Ritratti del dialogo  -  calmo / preoccupato / deciso", fill=(40, 30, 30))
    out.paste(grande, (16, 40))
    for k, im in enumerate(schermi):
        out.paste(im.resize((480, 320), Image.NEAREST),
                  (16 + grande.width + 24 + (k % 2) * 496, 40 + (k // 2) * 336))
    out.save(percorso)


def schermo(A, rt, p, nome, e, frase):
    """Il riquadro di dialogo della scelta 9 con il ritratto (anteprime.schermo_dialogo, generico)."""
    from PIL import Image
    C = A.C
    img = Image.new("RGB", (240, 160), A.rgb(["pietra calcarea", 2]))
    dia = C["disposizione"]["dialogo"]
    A.cornice(img, dia["x"], dia["y"], dia["colonne"], dia["righe"])
    px, _ = S.componi_ritratto(rt, p, nome, e)
    for yy, riga in enumerate(px):
        for xx, c in enumerate(riga):
            if c is not None:
                img.putpixel((dia["ritratto"][0] + xx, dia["ritratto"][1] + 1 + yy), S.rgb_di(c))
    cn = C["disposizione"]["cartiglio_nome"]
    etichetta = {"Guido": "Console Guido"}.get(nome, nome)
    larghezza = sum(len(A.F["glifi"][ch][0]) + A.F["spaziatura"] for ch in S.normalizza(A.F, etichetta))
    A.cartiglio(img, cn["x"], cn["y"] - 4, max(5, (larghezza + 12 + 7) // 8))
    A.testo(img, cn["x"] + 6, cn["y"] + 1, etichetta, A.rgb(C["colori"][2]))
    for i, r in enumerate(S.a_capo(A.F, frase, 240 - 52 - 10)[:3]):
        A.testo(img, 50, dia["y"] + 9 + i * 10, r, A.rgb(C["colori"][1]))
    return img


def main():
    rt = S.carica("ritratti")
    nuovo = dati_attesi(rt)
    if "--tavola" in sys.argv:
        tavola(sys.argv[sys.argv.index("--tavola") + 1])
        return 0
    if "--verifica" in sys.argv:
        if nuovo != rt:
            print("stile/dati/ritratti.json non allineato: lanciare tools/pittore_ritratti.py")
            return 1
        print("ritratti allineati")
        return 0
    err = S.controlla_ritratti(nuovo, S.carica("palette"))
    if err:
        print("\n".join(err))
        return 1
    S.salva("ritratti", nuovo)
    print(f"ritratti.json aggiornato: {', '.join(nuovo['personaggi'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
