#!/usr/bin/env python3
"""I compagni sulla mappa: Giorgio e Antonio che seguono Ubaldo in fila (16x32, come tools/sagome_mappa.py).

Stesso formato del giocatore: le direzioni giu', su, destra (sinistra = destra specchiata), 8 fotogrammi
l'una (6 di camminata coi tempi di A6, riposo, respiro A5), i piedi alla riga 31 (M1) e l'ombra 10x3 sotto
(L4). Le vesti e i colori sono quelli della battaglia (tools/sagome_battaglia.py): Giorgio col ciuffo biondo,
la cotta di ferro, la sopravveste bianca con la croce rossa, lo scudo azzurro e la spada; Antonio col saio
bruno, il cappuccio, la barba bianca e il bastone con la fiammella in punta (la gialla della battaglia, 2 px). Giorgio e' alto come Ubaldo
senza mitria; Antonio un poco piu' basso e curvo (la testa piu' bassa e in avanti), come in C3.

    python tools/sagome_compagni.py                 # scrive include/compagni.h
    python tools/sagome_compagni.py --controlla     # controlla che include/compagni.h sia aggiornato
    python tools/sagome_compagni.py tavola.png      # la tavola di controllo (serve Pillow)
"""
import os
import sys

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RADICE, "tools"))
sys.path.insert(0, os.path.join(RADICE, "stile"))

import sagome_battaglia as SB  # noqa: E402
import sagome_mappa as SM  # noqa: E402

M = SB.Materiale
DIREZIONI = SM.DIREZIONI
FOTOGRAMMI = SM.FOTOGRAMMI
CAMMINATA = SM.CAMMINATA
RIPOSO, RESPIRO = SM.RIPOSO, SM.RESPIRO
X0 = SM.X0

# Giorgio: le rampe della battaglia
G_FERRO = M("ferro", ("neutri", 1), ("neutri", 2), ("neutri", 3))
G_BIANCO = M("bianco", ("neutri", 3), ("neutri", 4), ("pietra calcarea", 5))
G_AZZURRO = M("azzurro", ("cielo e acqua", 1), ("cielo e acqua", 2), ("cielo e acqua", 3))
G_BIONDO = M("biondo", ("oro e bronzo", 2), ("oro e bronzo", 3), ("oro e bronzo", 3))
PALETTE_GIORGIO, IND_G, SING_G = SB.palette_di(
    [SB.PELLE, G_FERRO, G_BIANCO, G_AZZURRO, G_BIONDO],
    [SB.OCCHIO, ("ombra", SM.OMBRA), ("rosso", ("vermiglio comunale", 2))])

# Antonio
A_SAIO = M("saio", ("legno e cuoio", 0), ("legno e cuoio", 1), ("legno e cuoio", 2))
A_BIANCO = M("bianco", ("neutri", 3), ("neutri", 4), ("pietra calcarea", 5))
A_BASTONE = M("bastone", ("cotto e coppi", 2), ("cotto e coppi", 3), ("cotto e coppi", 3))
PALETTE_ANTONIO, IND_A, SING_A = SB.palette_di(
    [SB.PELLE, A_SAIO, A_BIANCO, A_BASTONE],
    [SB.OCCHIO, ("ombra", SM.OMBRA), ("corda", ("legno e cuoio", 3)), ("fiamma", ("oro e bronzo", 3))])


def _moto(f):
    """(piede avanti, dy del corpo) del fotogramma f, come Ubaldo: la camminata sale nei passaggi, il respiro
    abbassa di un pixel."""
    if f < CAMMINATA:
        piede, su = SM.passo(f)
        return piede, -su
    return 0, (1 if f == RESPIRO else 0)


# --- Giorgio -------------------------------------------------------------------------------------------------
def _tela_g():
    return SB.Figura(32, PALETTE_GIORGIO, IND_G, SING_G)


def giorgio_giu(f):
    """Di fronte: il ciuffo biondo, la sopravveste bianca con la croce rossa sopra la cotta, lo scudo azzurro
    al braccio sinistro (a destra di chi guarda), la spada nella destra puntata a terra."""
    t = _tela_g()
    piede, dy = _moto(f)
    c = X0 + 8
    t.parte_nuova("scarpe", "ferro")          # gli schinieri di maglia
    for lato in (-1, 1):
        t.rett(c - 3 + (lato > 0) * 4, 30 + (1 if piede == lato else 0) - (1 if piede == -lato else 0), 2, 1)
    # le gambe di ferro (le calze di maglia) e la cotta
    t.parte_nuova("gambe", "ferro").rett(c - 3, 25 + dy, 7, 5 - dy)
    t.parte_nuova("cotta", "ferro").poligono([(c - 4, 17 + dy), (c + 5, 17 + dy), (c + 5, 26 + dy), (c - 4, 26 + dy)])
    t.parte_nuova("sopravveste", "bianco").poligono([(c - 3, 18 + dy), (c + 4, 18 + dy), (c + 4 + (piede > 0), 27 + dy),
                                                   (c - 3 - (piede < 0), 27 + dy)])
    t.dettaglio_linea(c + 0.5, 19 + dy, c + 0.5, 25 + dy, "rosso")        # la croce
    t.dettaglio_linea(c - 1.5, 21 + dy, c + 2.5, 21 + dy, "rosso")
    t.dettaglio_rett(c - 3, 24 + dy, 7, 1, ("ferro", 0))                   # la cintura
    # le braccia di ferro, la mano destra con la spada a terra
    t.parte_nuova("braccio_d", "ferro").rett(c - 6, 18 + dy, 2, 6)
    t.parte_nuova("mano_d", "pelle").rett(c - 6, 24 + dy, 2, 1)
    t.parte_nuova("lama", "bianco")
    for y in range(25 + dy, 31):
        t.punto(c - 6, y)
    t.parte_nuova("guardia", "ferro").rett(c - 7, 24 + dy, 4, 1)
    # lo scudo a goccia sul braccio sinistro
    t.parte_nuova("scudo", "azzurro").poligono([(c + 4, 18 + dy), (c + 9, 18 + dy), (c + 9, 23 + dy), (c + 6.5, 27 + dy),
                                              (c + 4, 23 + dy)])
    t.dettaglio_linea(c + 6.5, 19 + dy, c + 6.5, 25 + dy, ("bianco", 2))
    t.dettaglio_linea(c + 5, 21 + dy, c + 8, 21 + dy, ("bianco", 2))
    # la testa: viso giovane senza barba, il ciuffo biondo
    t.parte_nuova("testa", "pelle").ellisse(c + 0.5, 13.5 + dy, 3, 3.2)
    t.parte_nuova("capelli", "biondo").poligono([(c - 2.8, 13 + dy), (c - 2.6, 10.5 + dy), (c - 0.5, 9.3 + dy),
                                               (c + 2.5, 9.5 + dy), (c + 3.8, 11 + dy), (c + 3.8, 13 + dy),
                                               (c + 2.5, 11.6 + dy), (c - 1, 11.6 + dy)])
    t.dettaglio(c - 1, 13 + dy, "occhio")
    t.dettaglio(c + 2, 13 + dy, "occhio")
    t.dettaglio(c + 0.5, 15.2 + dy, ("pelle", 0))
    return t


def giorgio_su(f):
    """Di schiena: la nuca bionda, la sopravveste bianca con la croce, lo scudo che sporge a sinistra; la spada,
    davanti, non si vede."""
    t = _tela_g()
    piede, dy = _moto(f)
    c = X0 + 8
    t.parte_nuova("scarpe", "ferro")          # gli schinieri di maglia
    for lato in (-1, 1):
        t.rett(c - 3 + (lato > 0) * 4, 30 - (1 if piede == lato else 0), 2, 1)
    t.parte_nuova("gambe", "ferro").rett(c - 3, 25 + dy, 7, 5 - dy)
    t.parte_nuova("braccio_d", "ferro").rett(c + 5, 18 + dy, 2, 6)        # la spada resta davanti, non si vede
    t.parte_nuova("cotta", "ferro").poligono([(c - 4, 17 + dy), (c + 5, 17 + dy), (c + 5, 26 + dy), (c - 4, 26 + dy)])
    t.parte_nuova("sopravveste", "bianco").poligono([(c - 3, 18 + dy), (c + 4, 18 + dy), (c + 4 + (piede > 0), 27 + dy),
                                                   (c - 3 - (piede < 0), 27 + dy)])
    t.dettaglio_linea(c + 0.5, 19 + dy, c + 0.5, 25 + dy, "rosso")        # la croce anche dietro
    t.dettaglio_linea(c - 1.5, 21 + dy, c + 2.5, 21 + dy, "rosso")
    t.parte_nuova("scudo", "azzurro").poligono([(c - 8, 18 + dy), (c - 3, 18 + dy), (c - 3, 23 + dy), (c - 5.5, 27 + dy),
                                              (c - 8, 23 + dy)])
    t.parte_nuova("collo", "pelle").rett(c - 1, 15 + dy, 4, 2)
    t.parte_nuova("capelli", "biondo").ellisse(c + 0.5, 12.6 + dy, 3.1, 3.1)
    return t


def giorgio_destra(f):
    """Di profilo verso destra: lo scudo sul braccio verso la camera, la spada nella mano avanti, il ciuffo
    sulla fronte."""
    t = _tela_g()
    piede, dy = _moto(f)
    c = X0 + 7
    apre = abs(piede) * 2
    t.parte_nuova("scarpe", "ferro")          # gli schinieri di maglia
    t.rett(c - 2 - apre, 30, 3, 1)
    t.rett(c + 1 + apre, 30, 3, 1)
    t.parte_nuova("gambe", "ferro").poligono([(c - 2, 25 + dy), (c + 2, 25 + dy), (c + 2 + apre, 30), (c - 2 - apre, 30)])
    t.parte_nuova("cotta", "ferro").poligono([(c - 3, 17 + dy), (c + 3, 17 + dy), (c + 3, 26 + dy), (c - 3, 26 + dy)])
    t.parte_nuova("sopravveste", "bianco").poligono([(c - 2, 18 + dy), (c + 3, 18 + dy), (c + 3 + apre // 2, 27 + dy),
                                                   (c - 3 - apre // 2, 27 + dy)])
    t.dettaglio_linea(c + 1.5, 19 + dy, c + 1.5, 25 + dy, "rosso")
    t.parte_nuova("braccio", "ferro").arto([(c + 1, 18 + dy), (c + 2, 22 + dy), (c + 4, 23 + dy)], 2)
    t.parte_nuova("mano", "pelle").rett(c + 4, 22 + dy, 2, 2)
    # la spada dritta e corta, inclinata di 45 gradi verso il basso: la lama chiara, l'elsa d'oro nella mano
    t.dettaglio_linea(c + 6, 24 + dy, c + 8, 26 + dy, ("bianco", 2))
    t.dettaglio(c + 6, 23 + dy, ("biondo", 1))
    # lo scudo sul braccio verso la camera: davanti al corpo, con la croce bianca
    t.parte_nuova("scudo", "azzurro").poligono([(c - 4, 18 + dy), (c + 1, 18 + dy), (c + 1, 23 + dy), (c - 1.5, 27 + dy),
                                              (c - 4, 23 + dy)])
    t.dettaglio_linea(c - 1.5, 19 + dy, c - 1.5, 25 + dy, ("bianco", 2))
    t.dettaglio_linea(c - 3, 21 + dy, c, 21 + dy, ("bianco", 2))
    t.parte_nuova("testa", "pelle").ellisse(c + 1, 13.5 + dy, 2.8, 3.2)
    t.rett(c + 3.5, 14 + dy, 1, 1)                                            # il naso
    t.parte_nuova("capelli", "biondo").poligono([(c - 2, 15 + dy), (c - 2.2, 11 + dy), (c, 9.4 + dy), (c + 3, 9.6 + dy),
                                               (c + 4, 11.5 + dy), (c + 1.5, 11.5 + dy), (c + 0.5, 13 + dy),
                                               (c - 0.5, 15.5 + dy)])
    t.dettaglio(c + 2, 13 + dy, "occhio")
    return t


# --- Antonio -------------------------------------------------------------------------------------------------
def _tela_a():
    return SB.Figura(32, PALETTE_ANTONIO, IND_A, SING_A)


def antonio_giu(f):
    """Di fronte: il saio bruno fino ai piedi col cordone, il cappuccio sulla testa, la barba bianca lunga, il
    bastone nella sinistra (a destra di chi guarda) con la fiammella in punta."""
    t = _tela_a()
    piede, dy = _moto(f)
    c = X0 + 8
    t.parte_nuova("piedi", "pelle")
    for lato in (-1, 1):
        t.rett(c - 3 + (lato > 0) * 4, 30 + (1 if piede == lato else 0) - (1 if piede == -lato else 0), 2, 1)
    o = piede
    t.parte_nuova("saio", "saio").poligono([(c - 4, 17 + dy), (c + 5, 17 + dy), (c + 6 + o, 30), (c - 5 + o, 30)])
    t.dettaglio_rett(c - 3, 23 + dy, 8, 1, "corda")                       # il cordone
    t.dettaglio_linea(c - 1, 24 + dy, c - 1 + o, 28, "corda")
    t.parte_nuova("maniche", "saio").rett(c - 5, 19 + dy, 11, 3)
    t.parte_nuova("mani", "pelle").rett(c - 1, 21 + dy, 3, 1)
    # il bastone con la fiammella
    t.parte_nuova("tau", "bastone")
    for y in range(9 + dy, 31):
        t.punto(c + 7, y)
    t.dettaglio_rett(c + 7, 7 + dy, 1, 2, "fiamma")                       # la fiammella in punta (2 px)
    t.parte_nuova("mano_s", "pelle").rett(c + 6, 20 + dy, 2, 2)
    # la testa nel cappuccio, la barba bianca fin sul petto
    t.parte_nuova("cappuccio", "saio").ellisse(c + 0.5, 13 + dy, 4.2, 4.4)
    t.parte_nuova("viso", "pelle").ellisse(c + 0.5, 13.8 + dy, 2.6, 2.6)
    t.parte_nuova("barba", "bianco").poligono([(c - 2.4, 14.6 + dy + 2), (c + 3.4, 14.6 + dy + 2), (c + 2.4, 19.5 + dy + 2),
                                             (c + 0.5, 20.5 + dy + 2), (c - 1.4, 19.5 + dy + 2)])
    t.dettaglio(c - 1, 13 + dy, "occhio")
    t.dettaglio(c + 2, 13 + dy, "occhio")
    t.dettaglio_rett(c - 1.5, 12 + dy, 5, 1, ("bianco", 1))               # le sopracciglia bianche
    return t


def antonio_su(f):
    """Di schiena: il cappuccio a punta, il saio, il bastone che sporge a sinistra."""
    t = _tela_a()
    piede, dy = _moto(f)
    c = X0 + 8
    t.parte_nuova("piedi", "pelle")
    for lato in (-1, 1):
        t.rett(c - 3 + (lato > 0) * 4, 30 - (1 if piede == lato else 0), 2, 1)
    t.parte_nuova("tau", "bastone")
    for y in range(9 + dy, 31):
        t.punto(c - 6, y)
    t.dettaglio_rett(c - 6, 7 + dy, 1, 2, "fiamma")
    o = piede
    t.parte_nuova("saio", "saio").poligono([(c - 4, 17 + dy), (c + 5, 17 + dy), (c + 6 + o, 30), (c - 5 + o, 30)])
    t.dettaglio_rett(c - 3, 23 + dy, 8, 1, "corda")
    t.parte_nuova("cappuccio", "saio").poligono([(c - 3.6, 18 + dy + 2), (c - 4, 12 + dy + 2), (c - 1.5, 9 + dy + 2), (c + 2.5, 9 + dy + 2),
                                               (c + 5, 12 + dy + 2), (c + 4.6, 18 + dy + 2), (c + 0.5, 21 + dy + 2)])
    t.parte_nuova("mano", "pelle").rett(c - 6, 20 + dy, 2, 2)
    return t


def antonio_destra(f):
    """Di profilo verso destra, curvo: il cappuccio, la barba che scende avanti, il bastone piantato davanti."""
    t = _tela_a()
    piede, dy = _moto(f)
    c = X0 + 7
    apre = abs(piede) * 2
    t.parte_nuova("piedi", "pelle")
    t.rett(c - 2 - apre, 30, 3, 1)
    t.rett(c + 1 + apre, 30, 3, 1)
    t.parte_nuova("saio", "saio").poligono([(c - 3, 17 + dy), (c + 3, 17 + dy), (c + 4 + apre, 30), (c - 4 - apre, 30)])
    t.dettaglio_rett(c - 3, 23 + dy, 7, 1, "corda")
    t.parte_nuova("tau", "bastone")
    for y in range(9 + dy, 31):
        t.punto(c + 7, y)
    t.dettaglio_rett(c + 7, 7 + dy, 1, 2, "fiamma")                       # la fiammella in punta (2 px)
    t.parte_nuova("braccio", "saio").arto([(c + 1, 18 + dy), (c + 3, 21 + dy), (c + 5, 21 + dy)], 2)
    t.parte_nuova("mano", "pelle").rett(c + 6, 20 + dy, 1, 2)
    t.parte_nuova("cappuccio", "saio").ellisse(c, 13 + dy, 4, 4.4)
    t.parte_nuova("viso", "pelle").ellisse(c + 2, 13.8 + dy, 2.2, 2.6)
    t.parte_nuova("barba", "bianco").poligono([(c + 0.5, 15 + dy + 2), (c + 4, 15 + dy + 2), (c + 3.5, 20 + dy + 2), (c + 1.5, 20 + dy + 2)])
    t.dettaglio(c + 2.5, 13 + dy, "occhio")
    return t


PITTORI = {
    "giorgio": {"giu": giorgio_giu, "su": giorgio_su, "destra": giorgio_destra},
    "antonio": {"giu": antonio_giu, "su": antonio_su, "destra": antonio_destra},
}
PALETTE = {"giorgio": PALETTE_GIORGIO, "antonio": PALETTE_ANTONIO}
SINGOLI = {"giorgio": SING_G, "antonio": SING_A}
COMPAGNI = ("giorgio", "antonio")


def fotogramma(chi, direzione, f):
    """La griglia 16x32 di indici del fotogramma f (0-7) della direzione, con l'ombra sotto i piedi."""
    px = PITTORI[chi][direzione](f).pixel()
    griglia = [riga[X0:X0 + SM.LARGO] for riga in px]
    ombra = SINGOLI[chi]["ombra"]
    for y in (30, 31):
        for x in range(3, 13):
            if griglia[y][x] == 0 and (y == 31 or 4 <= x <= 11):
                griglia[y][x] = ombra
    for x in range(4, 12):
        if griglia[31][x] == 0:
            griglia[31][x] = ombra
    return griglia


def fotogrammi(chi):
    """Tutti i fotogrammi di un compagno, direzione per direzione (giu, su, destra), 8 ciascuna."""
    return [fotogramma(chi, d, f) for d in DIREZIONI for f in range(FOTOGRAMMI)]


def tavola(percorso):
    """Ubaldo, Giorgio e Antonio, tre righe per figura (giu, su, destra), 8 fotogrammi."""
    from PIL import Image
    import stile as S
    pal = S.carica("palette")
    sfondo = S.rgb_di(S.colore(pal, ("pietra calcarea", 3)))
    figure = [(SM.PALETTE, SM.fotogrammi())] + [(PALETTE[c], fotogrammi(c)) for c in COMPAGNI]
    out = Image.new("RGB", (FOTOGRAMMI * 20, len(figure) * len(DIREZIONI) * 36), sfondo)
    for n, (palette, fot) in enumerate(figure):
        rgb = [S.rgb_di(S.colore(pal, r)) for r in palette]
        for i, g in enumerate(fot):
            for y, riga in enumerate(g):
                for x, c in enumerate(riga):
                    if c:
                        out.putpixel(((i % FOTOGRAMMI) * 20 + 2 + x, (n * len(DIREZIONI) + i // FOTOGRAMMI) * 36 + 2 + y),
                                     rgb[c])
    out.resize((out.width * 4, out.height * 4), Image.NEAREST).save(percorso)


USCITA = os.path.join(RADICE, "include", "compagni.h")


def _parole_tile(pixel):
    out = []
    for riga in pixel:
        parola = 0
        for x, v in enumerate(riga):
            parola |= v << (4 * x)
        out.append(parola)
    return out


def _blocchi(valori, per_riga, formato):
    return "\n".join("    " + ", ".join(formato(v) for v in valori[i:i + per_riga]) + ","
                     for i in range(0, len(valori), per_riga))


def header():
    """include/compagni.h: i tile e le palette (giorno e notte) di Giorgio e Antonio sulla mappa."""
    import stile as S
    pal = S.carica("palette")
    out = ["#ifndef GUBBIO_COMPAGNI_H", "#define GUBBIO_COMPAGNI_H", "",
           "// Generato da tools/sagome_compagni.py: non modificare a mano.",
           "// I compagni che seguono Ubaldo in fila sulla mappa (Giorgio, poi Antonio), 16x32 come il giocatore:",
           "// le direzioni giu', su, destra (sinistra = destra specchiata), 8 fotogrammi l'una nello stesso ordine",
           "// di TILE_GIOCATORE (include/mondo.h), 8 tile in mappatura 1D a fotogramma. L'ombra e' nel disegno.",
           "", "#include <cstdint>", "", "namespace gubbio::compagni", "{", "",
           f"inline constexpr int COMPAGNI = {len(COMPAGNI)};", ""]
    for chi in COMPAGNI:
        nome = chi.upper()
        tiles = []
        for griglia in fotogrammi(chi):
            for ty in range(4):
                for tx in range(2):
                    tiles += _parole_tile([riga[tx * 8:tx * 8 + 8] for riga in griglia[ty * 8:ty * 8 + 8]])
        fot = len(DIREZIONI) * FOTOGRAMMI
        out += [f"inline constexpr uint32_t TILE_{nome}[{fot} * 8 * 8] = {{",
                _blocchi(tiles, 8, lambda v: f"0x{v:08X}"), "};", "",
                f"inline constexpr uint16_t PALETTE_{nome}[16] = {{",
                _blocchi([S.colore(pal, r) for r in PALETTE[chi]], 8, lambda v: f"0x{v:04X}"), "};", "",
                f"inline constexpr uint16_t PALETTE_{nome}_NOTTE[16] = {{",
                _blocchi([S.colore(pal, r, True) for r in PALETTE[chi]], 8, lambda v: f"0x{v:04X}"), "};", ""]
    out += ["}", "", "#endif", ""]
    return "\n".join(out)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--controlla":
        attuale = open(USCITA, encoding="utf-8").read() if os.path.exists(USCITA) else ""
        if attuale != header():
            print("[compagni] include/compagni.h non e' aggiornato: python tools/sagome_compagni.py", file=sys.stderr)
            sys.exit(1)
        print("[compagni] OK")
    elif len(sys.argv) > 1:
        tavola(sys.argv[1])
    else:
        with open(USCITA, "w", encoding="utf-8", newline="\n") as f:
            f.write(header())
        print("[compagni] scritto include/compagni.h")
