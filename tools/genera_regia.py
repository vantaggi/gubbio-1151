#!/usr/bin/env python3
"""Il motore di regia delle cutscene (F7): dai copioni di regia testuali (regia/*.regia) scrive
include/regia.h, le tabelle constexpr che il lettore in ROM (src/regia.cpp) recita.

Un copione di regia:

    # commento
    cutscene C0 | Prova del motore di regia
    inquadratura 6 | cielo monti citta prato | 12
    narratore R_P_01_00

- "cutscene CODICE | titolo": una per file.
- "inquadratura SECONDI | piani dal piu' lontano al piu' vicino (fino a 4) | px/s del primo piano":
  uno stacco netto la separa dalla precedente; i piani scorrono a 1/4, 1/2, 3/4 e 1 della velocita'
  del primo piano (il piu' vicino), che e' quella data (~12 px/s nella proposta approvata).
- "narratore ID": una battuta del NARRATORE nelle bande nere (contesto NARRATORE di testi.h: al
  massimo 2 righe da 224 px), nell'ordine; le battute di un'inquadratura si dividono il suo tempo.

Le regole della proposta approvata (scambio/cutscene/PROPOSTA.md): bande nere da 24 px, nessuna
cutscene oltre i 60 s, Start salta tutto, A avanza il testo, dissolvenza solo all'inizio e alla fine.
I piani sono dipinti qui, proceduralmente, con la palette bloccata della Guida di stile.

    python tools/genera_regia.py            # controlla che l'header sia aggiornato
    python tools/genera_regia.py --scrivi   # lo riscrive
"""
import glob
import os
import re
import sys

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RADICE, "tools"))
sys.path.insert(0, os.path.join(RADICE, "stile"))

import stile as S  # noqa: E402
from genera_battaglia import Tela, PALETTE_SFONDO, blocchi, parole  # noqa: E402
import pittore_panorami as PP  # noqa: E402

USCITA = os.path.join(RADICE, "include", "regia.h")
COPIONI = os.path.join(RADICE, "regia", "*.regia")
TESTI_COPIONE = os.path.join(RADICE, "testi", "copione.testi")
SECONDI_MAX = 60
FRAME_PER_SECONDO = 60
PIANI_MAX = 4
W, H = 512, 256                  # un piano: mappa 64x32 tile, piu' largo dello schermo per scorrere
TILE_MAX_PER_PIANO = 600
ORIZZONTE = 104                  # nel quadro (240x112 fra le bande) l'orizzonte sta qui, in pixel di mappa


class ErroreRegia(Exception):
    pass


# --- i piani, dipinti dal piu' lontano al piu' vicino (0 e' trasparente, tranne nel cielo) -------
def cielo():
    t = Tela(W, H, 1)
    for y in range(H):
        banda = min(4, y // 22)
        for x in range(W):
            sopra = y % 22 < 2 and (x + y) % 2 == 0 and banda > 0
            t.punto(x, y, 1 + (banda - 1 if sopra else banda))
    return t


def monti():
    t = Tela(W, H)
    for x in range(W):
        cima = 62 + int(16 * abs(((x / 160.0) % 2) - 1)) + (x * 7 % 5)
        for y in range(cima, ORIZZONTE + 10):
            t.punto(x, y, 10 if (x + y) % 9 else 11)
    return t


def citta():
    """Gubbio sul pendio: le case di pietra a gradoni, la torre del Palazzo dei Consoli."""
    t = Tela(W, H)
    for x in range(W):
        base = ORIZZONTE + 4
        pendio = 84 + int(10 * ((x % 256) / 256.0))
        for y in range(pendio, base):
            t.punto(x, y, 7 if (x // 6 + y // 5) % 3 else 8)
        for y in range(pendio - 4, pendio):
            if (x // 8) % 3 != 2:
                t.punto(x, y, 13 if (x // 8) % 2 else 14)
    for x0 in (60, 316):
        t.rett(x0, 56, 40, 30, 8)
        t.rett(x0 + 26, 36, 10, 22, 8)
        for x in range(x0 + 26, x0 + 36, 4):
            t.rett(x, 32, 2, 4, 8)
        for x in range(x0 + 4, x0 + 36, 8):
            t.rett(x, 64, 3, 6, 0)
    return t


def prato():
    t = Tela(W, H)
    for y in range(ORIZZONTE + 2, H):
        for x in range(W):
            t.punto(x, y, 11 if (x * 3 + y * 5) % 7 else 12)
    for k in range(10):
        cx = (k * 53) % W
        t.ellisse(cx, ORIZZONTE - 4, 9, 12, 10)
        t.rett(cx - 1, ORIZZONTE + 4, 3, 6, 15)
    return t


# I piani: quelli generici della prova (pezzo U) e i panorami di Gubbio (pezzo V, tools/pittore_panorami.py).
# Nel copione un piano si scrive "nome" o "nome:momento" (giorno, alba, notte).
PIANI = {"cielo_prova": lambda m: (cielo(), PALETTE_SFONDO, False), "monti": lambda m: (monti(), PALETTE_SFONDO, False),
         "citta": lambda m: (citta(), PALETTE_SFONDO, False), "prato": lambda m: (prato(), PALETTE_SFONDO, False)}
PIANI.update(PP.PITTORI)


def colore_del_piano(palette_stile, rif, notte):
    """Il colore di una voce della palette di un piano: di notte la rampa di notte, tranne le luci
    (le voci segnate ACCESO in tools/pittore_panorami.py), che restano col tono del giorno."""
    return S.colore(palette_stile, rif[:2], notte and PP.ACCESO not in rif[2:])


def nome_e_momento(piano):
    nome, _, momento = piano.partition(":")
    return nome, momento or "giorno"


# --- il copione di regia --------------------------------------------------------------------------
def leggi(nome, testo):
    c = {"file": nome, "codice": None, "titolo": "", "inquadrature": []}
    for n, riga in enumerate(testo.splitlines(), 1):
        riga = riga.split("#", 1)[0].strip()
        if not riga:
            continue
        dove = f"{nome}:{n}"
        if riga.startswith("cutscene "):
            codice, _, titolo = riga[len("cutscene "):].partition("|")
            c["codice"], c["titolo"] = codice.strip(), titolo.strip()
        elif riga.startswith("inquadratura "):
            parti = [p.strip() for p in riga[len("inquadratura "):].split("|")]
            if len(parti) not in (3, 4) or parti[3:] not in ([], ["dissolvi"]):
                raise ErroreRegia(f"{dove}: 'inquadratura SECONDI | piani | px/s [| dissolvi]'")
            secondi, piani, velocita = float(parti[0]), parti[1].split(), int(parti[2])
            dissolvi = parti[3:] == ["dissolvi"]
            if not 1 <= len(piani) <= PIANI_MAX:
                raise ErroreRegia(f"{dove}: da 1 a {PIANI_MAX} piani, non {len(piani)}")
            if dissolvi and len(piani) < 2:
                raise ErroreRegia(f"{dove}: 'dissolvi' sfuma il primo piano su quello dietro: servono 2 piani")
            for p in piani:
                nome, momento = nome_e_momento(p)
                if nome not in PIANI:
                    raise ErroreRegia(f"{dove}: piano '{nome}' sconosciuto ({', '.join(PIANI)})")
                if momento not in PP.MOMENTI:
                    raise ErroreRegia(f"{dove}: momento '{momento}' sconosciuto ({', '.join(PP.MOMENTI)})")
            c["inquadrature"].append({"frame": int(round(secondi * FRAME_PER_SECONDO)), "piani": piani,
                                      "velocita": velocita, "dissolvi": dissolvi, "battute": [], "dove": dove})
        elif riga.startswith("narratore "):
            if not c["inquadrature"]:
                raise ErroreRegia(f"{dove}: una battuta prima della prima inquadratura")
            c["inquadrature"][-1]["battute"].append(riga.split()[1])
        else:
            raise ErroreRegia(f"{dove}: riga non riconosciuta: {riga}")
    if not c["codice"] or not c["inquadrature"]:
        raise ErroreRegia(f"{nome}: servono 'cutscene' e almeno un'inquadratura")
    return c


def contesti_dei_testi():
    """{id: contesto} da testi/copione.testi (le battute del NARRATORE per le bande)."""
    out = {}
    for riga in open(TESTI_COPIONE, encoding="utf-8"):
        if riga.strip() and not riga.startswith("#"):
            parti = [p.strip() for p in riga.split("|", 2)]
            out[parti[0]] = parti[1]
    return out


def controlla(cutscene, contesti):
    for c in cutscene:
        totale = sum(i["frame"] for i in c["inquadrature"])
        if totale > SECONDI_MAX * FRAME_PER_SECONDO:
            raise ErroreRegia(f"{c['file']}: {c['codice']} dura {totale / FRAME_PER_SECONDO:g} s, il massimo e' {SECONDI_MAX}")
        for i in c["inquadrature"]:
            for b in i["battute"]:
                if contesti.get(b) != "NARRATORE":
                    raise ErroreRegia(f"{i['dove']}: {b} non e' una battuta del NARRATORE (contesto NARRATORE, 2 righe)")


def celle(mappa):
    """La mappa 64x32 nell'ordine della VRAM: due blocchi 32x32 affiancati."""
    out = [0] * (64 * 32)
    for y in range(32):
        for x in range(64):
            out[(x // 32) * 1024 + y * 32 + (x % 32)] = mappa[y * 64 + x]
    return out


def dipingi_piani(usati):
    out = {}
    for piano in usati:
        nome, momento = nome_e_momento(piano)
        t, palette, notte = PIANI[nome](momento)
        tile, mappa = {tuple(tuple([0] * 8) for _ in range(8)): 0}, []
        for ty in range(32):
            for tx in range(64):
                chiave = tuple(tuple(t.px[ty * 8 + y][tx * 8:tx * 8 + 8]) for y in range(8))
                mappa.append(tile.setdefault(chiave, len(tile)))
        out[piano] = (list(tile), celle(mappa), palette, notte)
    return out


def id_c(piano):
    return piano.upper().replace(":", "_")


def genera(sorgenti, palette_stile):
    contesti = contesti_dei_testi()
    cutscene = [leggi(n, t) for n, t in sorgenti]
    controlla(cutscene, contesti)
    usati = sorted({p for c in cutscene for i in c["inquadrature"] for p in i["piani"]})
    dipinti = dipingi_piani(usati)
    out = ["// GENERATO da tools/genera_regia.py dai copioni di regia (regia/*.regia): non modificare a mano.",
           "#ifndef GUBBIO_REGIA_H", "#define GUBBIO_REGIA_H", "", "#include <cstdint>", "", "#include \"bn_tile.h\"", "",
           "#include \"testi.h\"", "", "namespace gubbio::regia", "{", "",
           f"inline constexpr int SECONDI_MAX = {SECONDI_MAX};", f"inline constexpr int FRAME_PER_SECONDO = {FRAME_PER_SECONDO};",
           f"inline constexpr int PIANI_PER_INQUADRATURA = {PIANI_MAX};", ""]
    for piano in usati:
        tile, mappa, palette, notte = dipinti[piano]
        if len(tile) > TILE_MAX_PER_PIANO:
            raise ErroreRegia(f"il piano {piano} ha {len(tile)} tile: il massimo e' {TILE_MAX_PER_PIANO}")
        c = id_c(piano)
        out += [f"inline constexpr uint16_t PALETTE_{c}[16] = {{",
                blocchi([colore_del_piano(palette_stile, r, notte) for r in palette], 8, lambda v: f"0x{v:04X}"), "};", "",
                f"inline constexpr bn::tile TILE_{c}[{len(tile)}] = {{"]
        out += ["    { { " + ", ".join(f"0x{v:08X}" for v in parole(t)) + " } }," for t in tile]
        out += ["};", "", f"inline constexpr uint16_t MAPPA_{c}[2048] = {{", blocchi(mappa, 32, str), "};", ""]
    out += ["struct Piano", "{", "    const bn::tile* tile;", "    uint16_t tile_conteggio;", "    const uint16_t* mappa;",
            "    const uint16_t* palette;      // 16 colori della Guida (di notte, le rampe di notte)",
            "    bool notte;                   // di notte il colore 15 (i fuochi, le finestre) trema", "};", "",
            f"inline constexpr int PIANI = {len(usati)};", "inline constexpr Piano PIANO[PIANI] = {"]
    out += [f"    {{ TILE_{id_c(n)}, {len(dipinti[n][0])}, MAPPA_{id_c(n)}, PALETTE_{id_c(n)}, "
            f"{'true' if dipinti[n][3] else 'false'} }},  // {n}" for n in usati]
    out += ["};", "", "struct Inquadratura", "{", "    int8_t piani[PIANI_PER_INQUADRATURA];   // dal piu' lontano, -1 vuoto",
            "    uint16_t frame;", "    uint8_t velocita;                        // px/s del primo piano", "    uint16_t prima_battuta;",
            "    uint8_t battute;", "    bool dissolvi;                           // il primo piano sfuma su quello dietro", "};", "", "struct Cutscene", "{", "    const char* codice;", "    uint16_t prima_inquadratura;",
            "    uint8_t inquadrature;", "    uint16_t frame;", "};", ""]
    battute, inquadrature, righe_c = [], [], []
    for c in cutscene:
        prima = len(inquadrature)
        for i in c["inquadrature"]:
            piani = [str(usati.index(p)) for p in i["piani"]] + ["-1"] * (PIANI_MAX - len(i["piani"]))
            inquadrature.append(f"    {{ {{ {', '.join(piani)} }}, {i['frame']}, {i['velocita']}, {len(battute)}, {len(i['battute'])}, {'true' if i['dissolvi'] else 'false'} }},")
            battute += [f"    testi::TestoId::{b}," for b in i["battute"]]
        totale = sum(i["frame"] for i in c["inquadrature"])
        righe_c.append(f"    {{ \"{c['codice']}\", {prima}, {len(c['inquadrature'])}, {totale} }},  // {c['titolo']}")
    out += [f"inline constexpr int BATTUTE = {len(battute)};", "inline constexpr testi::TestoId BATTUTA[BATTUTE > 0 ? BATTUTE : 1] = {"]
    out += battute or ["    testi::TestoId(0),"]
    out += ["};", "", f"inline constexpr int INQUADRATURE = {len(inquadrature)};", "inline constexpr Inquadratura INQUADRATURA[INQUADRATURE] = {"]
    out += inquadrature + ["};", "", f"inline constexpr int CUTSCENE = {len(cutscene)};", "inline constexpr Cutscene CUTSCENE_DATI[CUTSCENE] = {"]
    out += righe_c + ["};", ""]
    out += ["enum class CutsceneId : uint8_t", "{"] + [f"    {c['codice']}," for c in cutscene] + ["};", "", "}", "", "#endif", ""]
    return "\n".join(out)


def sorgenti_del_repo():
    return [(os.path.relpath(p, RADICE).replace(os.sep, "/"), open(p, encoding="utf-8").read())
            for p in sorted(glob.glob(COPIONI))]


def main(argv):
    try:
        testo = genera(sorgenti_del_repo(), S.carica("palette"))
    except ErroreRegia as e:
        print(f"[regia] ERRORE: {e}")
        return 1
    if "--scrivi" in argv:
        with open(USCITA, "w", encoding="utf-8", newline="\n") as f:
            f.write(testo)
        print(f"[regia] scritto {os.path.relpath(USCITA, RADICE)}")
        return 0
    vecchio = open(USCITA, encoding="utf-8").read() if os.path.exists(USCITA) else ""
    if vecchio != testo:
        print("[regia] include/regia.h da rigenerare con --scrivi")
        return 1
    print("[regia] aggiornato")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
