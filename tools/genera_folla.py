#!/usr/bin/env python3
"""La folla della citta' (pezzo VIVA): da mondo/folla.json a include/folla.h.

Per ogni corrente (chi passa, dove, in quali fasi) trova il percorso sulla griglia vera dell'area
(tools/genera_mondo.py, la stessa del gioco): un cammino largo tre celle (lo sprite e' largo 16 pixel, due
celle), che non passa su nessun varco tranne quelli dei capi, e che sta ad almeno due celle dagli NPC fermi
(copione/03, 05, 06: i posti di tools/genera_storia.py), cosi' nessuno passa addosso a chi parla. Il percorso
si accorcia ai soli punti dove cambia direzione. Per gli animali ('giro': N) il percorso va dall'ancora alla
cella libera piu' lontana entro N passi.

Scrive anche le figure: i passanti in 18 fotogrammi (camminata A6: giu', su, destra, 6 ciascuno) e gli
animali in 2 fotogrammi 16x16 (tools/figure_popolo.py), con la palette della gente.

    python3 tools/genera_folla.py            # controlla che include/folla.h sia aggiornato (esce 1 se no)
    python3 tools/genera_folla.py --scrivi   # lo riscrive
"""
import json
import os
import sys
from collections import deque

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RADICE, "tools"))
import figure_popolo as FP  # noqa: E402
import genera_storia as GS  # noqa: E402

DATI = os.path.join(RADICE, "mondo", "folla.json")
USCITA = os.path.join(RADICE, "include", "folla.h")
FOLLA_MAX = 8
FASI = GS.FASI
ANIMALI = list(FP.ANIMALI)
# chi cammina piu' piano o piu' svelto: frame per pixel
LENTEZZA = {"ragazzo": 1, "penitente": 3, "frate": 3, "ronda": 3, "pecora": 4, "gatto": 3, "gallina": 2,
            "cane": 2, "piccione": 3}


class ErroreFolla(Exception):
    pass


def griglia_libera(a, G):
    g = a["griglia"]
    w, h = a["larghezza"], a["altezza"]

    def cammina(x, y):
        return 0 <= x < w and 0 <= y < h and not GS.solida_nel_gioco(g[y][x], G)
    return g, w, h, cammina


def ancora(a, testo, G):
    tipo, _, resto = testo.partition(" ")
    if tipo == "spawn":
        return a["spawn"][int(resto)]
    if tipo == "varco":
        return GS.punto_dell_ancora(a, testo, G)
    if testo not in a.get("edifici", {}):
        raise ErroreFolla(f"{a['id']}: ancora «{testo}» che l'area non ha (edifici: {sorted(a.get('edifici', {}))})")
    return GS.punto_dell_ancora(a, testo, G)


def percorso(a, da, verso, giro, occupati, G):
    """Il cammino piu' comodo che c'e': largo 3 celle e a due celle dagli NPC; se la via e' stretta, a una cella
    dagli NPC; se e' strettissima, largo una cella."""
    ultimo = None
    for largo, distanza in ((1, 2), (1, 1), (0, 1), (0, 0)):
        try:
            return _percorso(a, da, verso, giro, occupati, G, largo, distanza)
        except ErroreFolla as e:
            ultimo = e
    raise ultimo


def _percorso(a, da, verso, giro, occupati, G, largo, distanza):
    """Le celle del cammino, dalla cella buona piu' vicina a 'da' fino a 'verso' (o, col giro, alla piu' lontana)."""
    g, w, h, cammina = griglia_libera(a, G)
    vietate = set()
    for (ox, oy) in occupati:
        for j in range(-distanza, distanza + 1):
            for i in range(-distanza, distanza + 1):
                vietate.add((ox + i, oy + j))

    def larga(x, y, capi):
        if (x, y) in vietate:
            return False
        for i in range(-largo, largo + 1):
            if not cammina(x + i, y):
                return False
            if g[y][x + i] in G.VARCHI and (x, y) not in capi:
                return False
        return True

    def vicina(p, capi=()):
        px, py = p
        for r in range(0, 60):
            for y in range(py - r, py + r + 1):
                for x in range(px - r, px + r + 1):
                    if max(abs(x - px), abs(y - py)) == r and larga(x, y, capi) and \
                            all(g[y][x + i] not in G.VARCHI for i in range(-largo, largo + 1)):
                        return (x, y)
        raise ErroreFolla(f"{a['id']}: nessuna cella libera vicino a {p}")

    inizio = vicina(da)
    fine = None if verso is None else vicina(verso)
    prima = {inizio: None}
    coda = deque([(inizio, 0)])
    lontana, dist_lontana = inizio, 0
    while coda:
        (x, y), d = coda.popleft()
        if (x, y) == fine:
            break
        if giro is not None and d >= giro:
            continue
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n not in prima and larga(n[0], n[1], ()):
                prima[n] = (x, y)
                coda.append((n, d + 1))
                if d + 1 > dist_lontana or (d + 1 == dist_lontana and n < lontana):
                    lontana, dist_lontana = n, d + 1
    meta = fine if fine is not None else lontana
    if meta not in prima:
        raise ErroreFolla(f"{a['id']}: nessun cammino largo da {da} a {verso}")
    celle = []
    c = meta
    while c is not None:
        celle.append(c)
        c = prima[c]
    if len(celle) < 4:
        raise ErroreFolla(f"{a['id']}: percorso di {len(celle)} celle da {da}, troppo corto")
    return celle[::-1]


def angoli(celle):
    """Solo i punti dove il cammino cambia direzione (e i due capi)."""
    if len(celle) < 2:
        return celle
    out = [celle[0]]
    for a, b, c in zip(celle, celle[1:], celle[2:]):
        if (b[0] - a[0], b[1] - a[1]) != (c[0] - b[0], c[1] - b[1]):
            out.append(b)
    out.append(celle[-1])
    return out


def posti_fermi():
    """I posti degli NPC fermi per area (anche gli accampati del borgo), dal generatore della storia."""
    _, npc = GS.leggi_copione()
    posti = GS.posti_degli_npc(npc)
    occupati = {}
    for p, (xy, borgo) in zip(npc, posti):
        occupati.setdefault(p["area"], []).append(xy)
        if borgo:
            occupati.setdefault("SANT_ANDREA", []).append(borgo)
    return occupati


def calcola():
    import genera_mondo as G  # noqa: E402
    dati = json.load(open(DATI, encoding="utf-8"))
    aree = GS.aree_del_mondo()
    occupati = posti_fermi()
    correnti, punti = [], []
    for c in dati["correnti"]:
        a = aree[c["area"]]
        for f in c["fasi"]:
            if f not in FASI:
                raise ErroreFolla(f"{c['area']}: fase «{f}» sconosciuta")
        animale = c["chi"] in ANIMALI
        if not animale and c["chi"] not in FP.PASSANTI:
            raise ErroreFolla(f"{c['area']}: «{c['chi']}» non e' un passante ne' un animale di tools/figure_popolo.py")
        if animale != ("giro" in c):
            raise ErroreFolla(f"{c['area']} {c['chi']}: gli animali fanno un giro, i passanti vanno da un'ancora all'altra")
        da = ancora(a, c["da"], G)
        verso = None if animale else ancora(a, c["a"], G)
        celle = percorso(a, da, verso, c.get("giro"), occupati.get(c["area"], []), G)
        if len(celle) < 4:
            raise ErroreFolla(f"{c['area']} {c['chi']}: percorso di {len(celle)} celle, troppo corto")
        ang = angoli(celle)
        correnti.append({
            "area": c["area"], "fasi": sum(1 << FASI.index(f) for f in c["fasi"]), "chi": c["chi"],
            "animale": animale, "primo": len(punti), "punti": len(ang), "quanti": c["quanti"],
            "lentezza": LENTEZZA.get(c["chi"], 2),
            "sparisce": (not animale) and c["da"].startswith("varco") and c["a"].startswith("varco"),
            "celle": celle,
        })
        punti += ang
    # al massimo FOLLA_MAX figure per area e fase
    for area in {c["area"] for c in correnti}:
        for k, f in enumerate(FASI):
            n = sum(c["quanti"] for c in correnti if c["area"] == area and (c["fasi"] >> k) & 1)
            if n > FOLLA_MAX:
                raise ErroreFolla(f"{area} {f}: {n} figure, al massimo {FOLLA_MAX}")
    return correnti, punti


def header(correnti, punti):
    passanti = list(FP.PASSANTI)
    out = ["// GENERATO da tools/genera_folla.py da mondo/folla.json: non modificare a mano.",
           "#ifndef GUBBIO_FOLLA_H", "#define GUBBIO_FOLLA_H", "", "#include <cstdint>", "", "#include \"mondo.h\"",
           "", "namespace gubbio::folla", "{", "",
           f"inline constexpr int FOLLA_MAX = {FOLLA_MAX};              // figure per area (sprite)",
           f"inline constexpr int FOTOGRAMMI_PASSO = {FP.FOTOGRAMMI_CAMMINATA};       // camminata A6, per direzione",
           "inline constexpr int PIXEL_PER_PASSO = 3;        // un fotogramma ogni 3 pixel di strada",
           "inline constexpr int PASSANTI = %d;" % len(passanti),
           "inline constexpr int ANIMALI = %d;" % len(ANIMALI),
           *[f"inline constexpr int ANIMALE_{n.upper()} = {i};" for i, n in enumerate(ANIMALI)], "",
           "// Le direzioni dei fotogrammi dei passanti: giu', su, destra (la sinistra e' la destra specchiata).",
           "inline constexpr int DIREZIONE_GIU = 0;", "inline constexpr int DIREZIONE_SU = 1;",
           "inline constexpr int DIREZIONE_DESTRA = 2;", "",
           "struct Punto", "{", "    uint8_t tx;", "    uint8_t ty;", "};", "",
           f"inline constexpr int PUNTI = {len(punti)};", "inline constexpr Punto PUNTO[PUNTI] = {"]
    for i in range(0, len(punti), 8):
        out.append("    " + " ".join(f"{{ {x}, {y} }}," for x, y in punti[i:i + 8]))
    out += ["};", "",
            "struct Corrente", "{", "    int8_t area;                  // mondo::AreaId",
            "    uint8_t fasi;                 // bit 0 ULTIMATUM, 1 DIGIUNO, 2 NOTTE (storia::Fase)",
            "    uint8_t figura;               // FIGURA_PASSANTE o, se animale, FIGURA_ANIMALE",
            "    bool animale;", "    uint16_t primo;               // in PUNTO", "    uint8_t punti;",
            "    uint8_t quanti;", "    uint8_t lentezza;             // frame per pixel",
            "    bool sparisce;                // ai capi esce dall'area (un varco) e torna dopo", "};", "",
            f"inline constexpr int CORRENTI = {len(correnti)};", "inline constexpr Corrente CORRENTE[CORRENTI] = {"]
    for c in correnti:
        fig = ANIMALI.index(c["chi"]) if c["animale"] else passanti.index(c["chi"])
        out.append(f"    {{ int8_t(mondo::AreaId::{c['area']}), {c['fasi']}, {fig}, {'true' if c['animale'] else 'false'}, "
                   f"{c['primo']}, {c['punti']}, {c['quanti']}, {c['lentezza']}, {'true' if c['sparisce'] else 'false'} }},"
                   f"  // {c['chi']}")
    out += ["};", "",
            "// I passanti, 16x32 (8 tile), 18 fotogrammi: giu' 0-5, su 6-11, destra 12-17 (tools/figure_popolo.py).",
            "inline constexpr uint32_t FIGURA_PASSANTE[PASSANTI][18 * 8 * 8] = {"]
    for n in passanti:
        out.append("    {")
        for px in FP.fotogrammi_passante(n):
            pa = FP.parole(px)
            out += ["        " + ", ".join(f"0x{v:08X}" for v in pa[k:k + 8]) + "," for k in range(0, 64, 8)]
        out.append(f"    }},  // {n}")
    out += ["};", "", "// Gli animali, 16x16 (4 tile), 2 fotogrammi (il passo o il becchettare; il piccione: in volo).",
            "inline constexpr uint32_t FIGURA_ANIMALE[ANIMALI][2 * 4 * 8] = {"]
    for n in ANIMALI:
        out.append("    {")
        for k in range(2):
            pa = FP.parole(FP.animale(n, k))
            out += ["        " + ", ".join(f"0x{v:08X}" for v in pa[j:j + 8]) + "," for j in range(0, 32, 8)]
        out.append(f"    }},  // {n}")
    out += ["};", "", "}", "", "#endif", ""]
    return "\n".join(out)


def main(argv):
    try:
        h = header(*calcola())
    except ErroreFolla as e:
        print(f"[folla] ERRORE: {e}")
        return 1
    if "--scrivi" in argv:
        with open(USCITA, "w", encoding="utf-8", newline="\n") as f:
            f.write(h)
        print("[folla] scritto include/folla.h")
        return 0
    vecchio = open(USCITA, encoding="utf-8").read() if os.path.exists(USCITA) else ""
    if vecchio != h:
        print("[folla] da rigenerare con --scrivi")
        return 1
    print("[folla] aggiornato")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
