#!/usr/bin/env python3
"""Le icone 8x8 dei menu (MDI, MBI, MMA, MNEG; menu/PROPOSTA.md e i mockup approvati di menu/mockup_menu.py):
la cronaca, gli incarichi nel colore del quartiere, gli oggetti delle quest e della bisaccia. Disegni a lettere,
una lettera per colore della Guida; una sola palette da 16 (lo 0 e' trasparente) per tutte le icone.

Scrive include/stile/icone_menu.h: la palette in BGR555, i tile 4bpp (8 parole da 32 bit per icona) e l'elenco.

    python3 tools/genera_icone_menu.py            # controlla che l'header sia aggiornato (esce con 1 se no)
    python3 tools/genera_icone_menu.py --scrivi   # lo riscrive
"""
import os
import sys

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RADICE, "stile"))
import stile as S  # noqa: E402

USCITA = os.path.join(RADICE, "include", "stile", "icone_menu.h")

# Le lettere e i colori della Guida (STANDARD C1). Il mockup ne usava qualcuno in piu' (pelle, vermiglio 1 e 3,
# legno 1, cielo 3): nelle icone di qui non servono, e la palette resta una.
COLORI = [
    ("k", ("neutri", 0)), ("w", ("neutri", 4)), ("r", ("vermiglio comunale", 2)), ("o", ("oro e bronzo", 2)),
    ("O", ("oro e bronzo", 3)), ("y", ("oro e bronzo", 1)), ("b", ("cielo e acqua", 2)), ("g", ("verde dei monti", 2)),
    ("G", ("verde dei monti", 3)), ("c", ("cotto e coppi", 3)), ("C", ("cotto e coppi", 4)), ("l", ("legno e cuoio", 2)),
    ("s", ("pietra calcarea", 4)), ("S", ("pietra calcarea", 2)), ("n", ("neutri", 2)),
]
assert len(COLORI) == 15

# Le bandierine degli incarichi: X e' il colore del quartiere del datore (censimento dei simboli: blu San Martino,
# rosso Sant'Andrea, ocra San Giuliano, verde San Pietro).
QUARTIERI = {"SM": "b", "SA": "r", "SG": "o", "SP": "G"}
BANDIERA = ["kk......", "kXXXXXk.", "kXwwXXXk", "kXwwXXXk", "kXXXXXk.", "kk......", "k.......", "k......."]
CONSEGNA = ["kk......", "kXXXXXk.", "kXOOOXXk", "kXOOOXXk", "kXXXXXk.", "kk......", "k.......", "k......."]

ICONE = {
    "OBIETTIVO": ["...kk...", "..kOOk..", "kkkOokkk", "kOOooOOk", ".kOooOk.", ".kOkkOk.", "kOk..kOk", "kk....kk"],
    "CRESCIA": ["........", "..kkkk..", ".kCOOCk.", "kCOCCOCk", "kCCOOCCk", ".kCCCCk.", "..kkkk..", "........"],
    "BISCOTTI": ["........", ".kkk.kkk", "kCyCkCyC", "kCCCkCCC", ".kkk.kkk", "..kkk...", ".kCyCk..", "..kkk..."],
    "CENERE": ["........", "..kkkk..", ".knSSnk.", "knSlSnSk", "kSnSSnSk", ".knnnnk.", "..kkkk..", "........"],
    "FERRO": ["........", "........", ".kkkkkk.", "knSSSSnk", "kSnnnnSk", ".kkkkkk.", "........", "........"],
    "ELLEBORO": ["...gk...", "..kGgk..", ".kgkgGk.", "..kgk...", "...l....", "..lkl...", ".l.k.l..", "........"],
    "ROSA": ["..kkk...", ".kssSk..", "kssrsSk.", "ksrrrsk.", ".kssSk..", "..kSk...", "...k....", "..kSk..."],
    "INDIZIO": [".kkkkk..", ".kssskk.", ".ksnnsk.", ".kssssk.", ".ksnnsk.", ".kssssk.", ".kkkkkk.", "........"],
    # un pezzo non ancora raccolto: il solo contorno, in grigio
    "VUOTO": ["........", "........", ".nnnnnn.", "n......n", "n......n", ".nnnnnn.", "........", "........"],
    # i segnalini della mappa (MMA, mockup 03 e 03c); la bottega ha la porta in legno 2 (il mockup usava due
    # colori fuori da questa palette, legno 1 e un nero diverso)
    "SEI_QUI": ["...kk...", "..kwwk..", ".kwOOwk.", ".kwOOwk.", "kwwwwwwk", "kwrrrrwk", "kwwwwwwk", ".kkkkkk."],
    "VENDITORE": ["........", "..kkkk..", ".kCCCCk.", "kCyyyyCk", "kCyyyyCk", "kCCCCCCk", ".kkkkkk.", "........"],
    "TAVERNA": ["..k.....", ".kgk....", "kgGgk...", ".kgk....", "..k.....", ".kllk...", ".kllk...", "..kk...."],
    "BOTTEGA": ["........", ".kkkkkk.", "kcccccck", "kCcCcCck", ".kssssk.", ".ksllsk.", ".ksllsk.", ".kkkkkk."],
    "PORTA": [".k.k.k..", ".kkkkk..", ".kSsSk..", ".kSSSk..", ".kSkSk..", ".kk.kk..", ".k...k..", "........"],
    # un angolo del cursore della mappa (quello in alto a sinistra; gli altri sono lo stesso, ribaltato)
    "ANGOLO": ["kkkkk...", "krrrk...", "krkkk...", "krk.....", "kkk.....", "........", "........", "........"],
}
for q, x in QUARTIERI.items():
    ICONE["INCARICO_" + q] = [r.replace("X", x) for r in BANDIERA]
    ICONE["CONSEGNA_" + q] = [r.replace("X", x) for r in CONSEGNA]


class ErroreIcone(Exception):
    pass


def tile(nome, righe):
    indice = {lettera: i + 1 for i, (lettera, _) in enumerate(COLORI)}
    if len(righe) != 8 or any(len(r) != 8 for r in righe):
        raise ErroreIcone("icona %s: non e' 8x8" % nome)
    parole = []
    for r in righe:
        v = 0
        for p, ch in enumerate(r):
            if ch == ".":
                continue
            if ch not in indice:
                raise ErroreIcone("icona %s: lettera %r senza colore" % (nome, ch))
            v |= indice[ch] << (4 * p)
        parole.append(v)
    return parole


def header():
    P = S.carica("palette")
    pal = [0] + [S.colore(P, list(rif)) for _, rif in COLORI]
    nomi = list(ICONE)
    out = ["// GENERATO da tools/genera_icone_menu.py. Non modificare a mano.",
           "#ifndef GUBBIO_STILE_ICONE_MENU_H", "#define GUBBIO_STILE_ICONE_MENU_H", "", "#include <cstdint>", "",
           "namespace gubbio::stile", "{", "",
           "// I colori delle icone dei menu, tutti della Guida (0 trasparente).",
           "inline constexpr uint16_t ICONE_MENU_PALETTE[16] = {",
           "    " + ", ".join("0x%04X" % c for c in pal), "};", "",
           "enum class IconaMenu : uint8_t", "{"]
    out += ["    %s," % n for n in nomi]
    out += ["};", "", "inline constexpr int ICONE_MENU = %d;" % len(nomi), "",
            "// Una icona = un tile 4bpp: 8 righe, il pixel p di una riga nei bit 4p..4p+3.",
            "inline constexpr uint32_t ICONE_MENU_TILE[ICONE_MENU * 8] = {"]
    for n in nomi:
        out.append("    " + ", ".join("0x%08X" % w for w in tile(n, ICONE[n])) + ",  // " + n)
    out += ["};", "", "// Il rettangolo dei pixel pieni di ogni icona: x0, y0, x1, y1 compresi (i segnalini della mappa non si",
            "// devono toccare: src/menu_mappa.cpp).", "inline constexpr uint8_t ICONE_MENU_PIENO[ICONE_MENU * 4] = {"]
    for n in nomi:
        pieni = [(x, y) for y, r in enumerate(ICONE[n]) for x, ch in enumerate(r) if ch != "."]
        out.append("    %d, %d, %d, %d,  // %s" % (min(p[0] for p in pieni), min(p[1] for p in pieni),
                                                    max(p[0] for p in pieni), max(p[1] for p in pieni), n))
    out += ["};", "", "}", "", "#endif", ""]
    return "\n".join(out)


def main(argv):
    testo = header()
    if "--scrivi" in argv:
        with open(USCITA, "w", encoding="utf-8", newline="\n") as f:
            f.write(testo)
        print("[icone] scritto", os.path.relpath(USCITA, RADICE))
        return 0
    with open(USCITA, encoding="utf-8") as f:
        if f.read() != testo:
            print("[icone] include/stile/icone_menu.h non e' aggiornato: python3 tools/genera_icone_menu.py --scrivi")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
