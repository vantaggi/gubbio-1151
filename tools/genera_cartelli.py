#!/usr/bin/env python3
"""I cartelli ai varchi (MAI, menu/PROPOSTA.md sez. 3.8): a 3 celle da un varco compare un cartello con la
destinazione e, sotto, dove si va da li'. I testi vengono da mondo/grafo.json: per ogni varco fra due aree (nei
due versi) una riga con la porta, se c'e', e le aree che si raggiungono oltre la destinazione (senza quella da
cui si viene). La prima riga del cartello e' il nome dell'area di destinazione (la sua etichetta, gia' nei testi).

Scrive testi/cartelli.testi (per tools/genera_testi.py, che misura le righe) e include/cartelli.h (la tabella
da, verso -> testo, letta da include/aiuti.h).

    python3 tools/genera_cartelli.py            # controlla che i file generati siano aggiornati
    python3 tools/genera_cartelli.py --scrivi   # li riscrive
"""
import json
import os
import sys

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RADICE, "stile"))
import stile as S  # noqa: E402
GRAFO = os.path.join(RADICE, "mondo", "grafo.json")
USCITA_TESTI = os.path.join(RADICE, "testi", "cartelli.testi")
USCITA_H = os.path.join(RADICE, "include", "cartelli.h")

# I nomi brevi sul cartello (il nome intero e' gia' sulla prima riga, o nell'etichetta d'area).
BREVI = {"PIAZZA_GRANDE": "Piazza Grande", "VIA_DEI_CONSOLI": "via dei Consoli", "LARGO_BARGELLO": "Bargello",
         "SAN_MARTINO": "San Martino", "TEATRO_ROMANO": "Teatro Romano", "PIAZZA_QUARANTA_MARTIRI": "Quaranta Martiri",
         "SAN_PIETRO": "San Pietro", "VIA_XX_SETTEMBRE": "via XX Settembre", "SANT_AGOSTINO": "Sant'Agostino",
         "SANT_ANDREA": "Sant'Andrea", "DUOMO_DUCALE": "Duomo", "MONTE_INGINO": "Monte Ingino", "BASILICA": "Basilica",
         "BASILICA_INTERNO": "dentro la Basilica", "BOTTACCIONE": "Bottaccione", "GOLA_STRISCIA": "la gola",
         "GOLA_MIASMI": "i miasmi", "GOLA_ARCO": "l'arco", "CONDOTTO": "il Condotto",
         # gli interni esplorabili (pezzo INT)
         "TAVERNA_INTERNO": "la taverna", "SPEZIERIA_INTERNO": "la spezieria", "BOTTEGA_CONTI_INTERNO": "la bottega dei conti",
         "CARRADORE_INTERNO": "il carradore", "CASA_MEDICO_INTERNO": "il medico", "SALA_CONSOLI": "la Sala dei Consoli"}
OLTRE_MAX = 3           # quante aree al massimo sulla seconda riga
LARGHEZZA_AREA = 192    # il contesto AREA di tools/genera_testi.py: una riga da 192 px


class ErroreCartelli(Exception):
    pass


def leggi_grafo(percorso=GRAFO):
    with open(percorso, encoding="utf-8") as f:
        return json.load(f)


def cartelli(grafo):
    """[(da, verso, riga)] per ogni varco, nei due versi, nell'ordine degli archi."""
    ids = [a["id"] for a in grafo["aree"]]
    vicine = {i: [] for i in ids}
    for a in grafo["archi"]:
        for x, y in ((a["da"], a["a"]), (a["a"], a["da"])):
            if x not in vicine or y not in vicine:
                raise ErroreCartelli(f"arco {x} - {y} con un'area che non c'e'")
            vicine[x].append((y, a.get("porta"), bool(a.get("dentro"))))
    font = S.carica("font")
    righe = []
    for da in ids:
        for verso, porta, _ in vicine[da]:
            # oltre la destinazione si contano le strade, non i portoni degli edifici (gli interni)
            oltre = [BREVI[z] for z, _, dentro in vicine[verso] if z != da and not dentro][:OLTRE_MAX]
            # si tolgono aree dalla fine finche' la riga sta in una riga del contesto AREA
            while True:
                pezzi = ([porta] if porta else []) + ([("poi " if porta else "") + ", ".join(oltre)] if oltre else [])
                riga = ", ".join(pezzi) if pezzi else "Qui la strada finisce."
                if len(S.a_capo(font, riga, LARGHEZZA_AREA)) <= 1 or not oltre:
                    break
                oltre = oltre[:-1]
            if len(S.a_capo(font, riga, LARGHEZZA_AREA)) > 1:
                raise ErroreCartelli(f"{da} -> {verso}: «{riga}» non sta in {LARGHEZZA_AREA} px")
            righe.append((da, verso, riga))
    return righe


def id_testo(da, verso):
    return f"CARTELLO_{da}_{verso}"


def testi_dei_cartelli(righe):
    out = ["# GENERATO da tools/genera_cartelli.py da mondo/grafo.json: non modificare a mano.",
           "# La seconda riga dei cartelli ai varchi (MAI): la porta e dove si va oltre la destinazione.", ""]
    out += [f"{id_testo(da, verso):48s}| AREA | {riga}" for da, verso, riga in righe]
    return "\n".join(out) + "\n"


def header(righe):
    out = ["// GENERATO da tools/genera_cartelli.py da mondo/grafo.json: non modificare a mano.",
           "#ifndef GUBBIO_CARTELLI_H", "#define GUBBIO_CARTELLI_H", "", "#include <cstdint>", "",
           "#include \"mondo.h\"", "#include \"testi.h\"", "", "namespace gubbio::cartelli", "{", "",
           "// Il cartello del varco dall'area 'da' all'area 'verso' (mondo::AreaId): la seconda riga, sotto il nome",
           "// della destinazione. Lo legge aiuti::cartello().",
           "struct Cartello", "{", "    int8_t da;", "    int8_t verso;", "    testi::TestoId oltre;", "};", "",
           f"inline constexpr int CARTELLI = {len(righe)};", "inline constexpr Cartello CARTELLO[CARTELLI] = {"]
    out += [f"    {{ int8_t(mondo::AreaId::{da}), int8_t(mondo::AreaId::{verso}), testi::TestoId::{id_testo(da, verso)} }},"
            for da, verso, _ in righe]
    out += ["};", "", "}", "", "#endif", ""]
    return "\n".join(out)


def genera(grafo=None):
    righe = cartelli(grafo or leggi_grafo())
    return header(righe), testi_dei_cartelli(righe)


def main(argv):
    try:
        h, t = genera()
    except ErroreCartelli as e:
        print(f"[cartelli] ERRORE: {e}")
        return 1
    if "--scrivi" in argv:
        for p, testo in ((USCITA_H, h), (USCITA_TESTI, t)):
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write(testo)
        print("[cartelli] scritti include/cartelli.h e testi/cartelli.testi")
        return 0
    vecchi = []
    for p in (USCITA_H, USCITA_TESTI):
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                vecchi.append(f.read())
        else:
            vecchi.append("")
    if vecchi != [h, t]:
        print("[cartelli] da rigenerare con --scrivi")
        return 1
    print("[cartelli] aggiornato")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
