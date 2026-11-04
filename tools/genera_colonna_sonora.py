#!/usr/bin/env python3
"""F7c: la colonna sonora nel gioco. Da musica/colonna_sonora.txt (quale brano suona dove) e da audio/
(i brani e gli effetti che mmutil mette nella ROM) scrive include/colonna_sonora.h.

    python tools/genera_colonna_sonora.py            # controlla che include/colonna_sonora.h sia aggiornato
    python tools/genera_colonna_sonora.py --scrivi   # lo riscrive

Rifiuta (ErroreColonna) un'area senza brano in una fase, un brano o un effetto che non c'e' in audio/,
un file di audio/ che nessuno usa, una cutscene di regia senza riga o una riga senza cutscene, un evento
di battaglia senza riga, un luogo su un edificio che l'area non ha.

I nomi delle aree, delle cutscene, degli eventi e degli incontri si leggono dagli header generati
(include/mondo.h, regia.h, battaglia.h, battaglia_dati.h, storia.h): l'ordine e' quello del gioco, e
src/autotest_audio.cpp lo ricontrolla a tempo di compilazione.
"""
import json
import os
import re
import sys

RADICE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(RADICE, "tools"))

import genera_audio as GA  # noqa: E402

DATI = os.path.join(RADICE, "musica", "colonna_sonora.txt")
USCITA = os.path.join(RADICE, "include", "colonna_sonora.h")
FASI = ("giorno", "digiuno", "notte", "alba")
MODI = ("fondo", "segnale")
LATO_MAX = 255      # le celle di un luogo stanno in un uint8_t


class ErroreColonna(Exception):
    pass


# =================================================================================================
# Quello che il gioco ha: letto dagli header generati e da audio/
# =================================================================================================

def _leggi(rel):
    with open(os.path.join(RADICE, rel), encoding="utf-8") as f:
        return f.read()


def _enum(testo, nome):
    m = re.search(r"enum class " + nome + r"\s*:\s*\w+\s*\{(.*?)\};", testo, re.S)
    if not m:
        raise ErroreColonna(f"enum {nome} non trovato")
    voci = [re.sub(r"//.*", "", r).strip().rstrip(",").split("=")[0].strip() for r in m.group(1).splitlines()]
    return [v for v in voci if v and v not in ("CONTEGGIO", "COUNT")]


def gioco_del_repo():
    """Le aree, le cutscene, gli eventi, gli incontri, gli eroi e gli NPC come li conosce la ROM."""
    mondo, regia, batt, dati, storia = (_leggi(f"include/{n}.h") for n in
                                        ("mondo", "regia", "battaglia", "battaglia_dati", "storia"))
    cut = re.search(r"Cutscene CUTSCENE_DATI\[CUTSCENE\] = \{(.*?)\};", regia, re.S)
    npc = re.search(r"Npc NPC_AMBIENTE\[NPC\] = \{(.*?)\};", storia, re.S)
    eroi = {m.group(1): int(m.group(2)) for m in re.finditer(r"inline constexpr int (UBALDO|GIORGIO|ANTONIO) = (\d+);", dati)}
    return {
        "aree": _enum(mondo, "AreaId"),
        "cutscene": re.findall(r'\{ "(\w+)",', cut.group(1)),
        "eventi": _enum(batt, "EventKind"),
        "incontri": int(re.search(r"inline constexpr int INCONTRI = (\d+);", dati).group(1)),
        "eroi": eroi,
        "npc": [(m.group(2), m.group(1)) for m in re.finditer(r"mondo::AreaId::(\w+)\).*//\s*(.+)$", npc.group(1), re.M)],
    }


def audio_del_repo():
    """(brani, effetti, anelli): i file di audio/ senza estensione, in ordine; il brano torna da capo?"""
    file = sorted(os.listdir(GA.CARTELLA_AUDIO))
    brani = [f[:-3] for f in file if f.endswith(".xm")]
    effetti = [f[:-4] for f in file if f.endswith(".wav")]
    partiture = {n: GA.leggi_brano(n, t) for n, t in GA.sorgenti_del_repo()}
    anelli = {b: partiture[b]["anello"] if b in partiture else True for b in brani}
    return brani, effetti, anelli


def amici_del_repo():
    with open(os.path.join(RADICE, "dati", "amici.json"), encoding="utf-8") as f:
        return json.load(f)["amici"]


def luoghi_del_mondo(richiesti):
    """{(area, edificio): ([(x, y) dei portoni], larghezza, altezza)} per le coppie richieste."""
    import genera_mondo as G
    mondo = G.mondo_del_repo()
    out = {}
    aree = {a for a, _ in richiesti}
    for n, t in G.sorgenti_del_repo():
        a = G.leggi_area(n, t)
        if a["id"].upper() not in aree:
            continue
        G.prepara_area(a, mondo)
        for area, mid in richiesti:
            if area == a["id"].upper() and mid == "*":
                # l'area intera (gli interni esplorabili: si e' nel luogo appena entrati)
                out[(area, mid)] = ([(0, 0), (a["larghezza"] - 1, a["altezza"] - 1)], a["larghezza"], a["altezza"])
                continue
            if area != a["id"].upper() or mid not in a.get("edifici", {}):
                continue
            x0, y0, w, h = a["edifici"][mid]
            portoni = [(x, y) for y in range(y0, y0 + h) for x in range(x0, x0 + w)
                       if a["griglia"][y][x] == G.PORTONE_EDIFICIO]
            out[(area, mid)] = (portoni, a["larghezza"], a["altezza"])
    return out


# =================================================================================================
# Il file dei dati
# =================================================================================================

def leggi_dati(testo):
    d = {"fasi": None, "aree": {}, "luoghi": [], "cutscene": {}, "eventi": {}, "uso": {}, "duelli": {},
         "schermate": {}, "fuoco": None}
    for numero, riga in enumerate(testo.splitlines(), 1):
        riga = re.sub(r"(^|\s)#.*", "", riga).strip()
        if not riga:
            continue
        p = riga.split()
        dove = f"colonna_sonora.txt:{numero}"
        chiave = p[0]
        if chiave == "fasi":
            if tuple(p[1:]) != FASI:
                raise ErroreColonna(f"{dove}: le fasi sono {' '.join(FASI)}")
            d["fasi"] = p[1:]
        elif chiave == "area":
            if len(p) != 2 + len(FASI):
                raise ErroreColonna(f"{dove}: l'area {p[1] if len(p) > 1 else '?'} vuole un brano per fase ({len(FASI)})")
            if p[1] in d["aree"]:
                raise ErroreColonna(f"{dove}: l'area {p[1]} e' gia' scritta")
            d["aree"][p[1]] = p[2:]
        elif chiave == "luogo":
            if len(p) not in (7, 8) or p[6] not in MODI or not p[4].isdigit():
                raise ErroreColonna(f"{dove}: luogo NOME AREA EDIFICIO RAGGIO BRANO fondo|segnale [AMICO]")
            d["luoghi"].append({"nome": p[1], "area": p[2], "edificio": p[3], "raggio": int(p[4]), "brano": p[5],
                                "modo": p[6], "amico": p[7] if len(p) == 8 else None, "dove": dove})
        elif chiave == "cutscene":
            if len(p) not in (3, 4):
                raise ErroreColonna(f"{dove}: cutscene CODICE BRANO [EFFETTO]")
            if p[1] in d["cutscene"]:
                raise ErroreColonna(f"{dove}: la cutscene {p[1]} e' gia' scritta")
            d["cutscene"][p[1]] = (p[2], p[3] if len(p) == 4 else "-")
        elif chiave == "evento":
            if len(p) != 3:
                raise ErroreColonna(f"{dove}: evento TIPO EFFETTO")
            d["eventi"][p[1]] = p[2]
        elif chiave == "uso":
            if len(p) != 3 or not re.fullmatch(r"[A-Z_]+", p[1]):
                raise ErroreColonna(f"{dove}: uso NOME EFFETTO (NOME in maiuscolo)")
            d["uso"][p[1]] = p[2]
        elif chiave == "duello":
            if len(p) != 3 or not p[1].isdigit():
                raise ErroreColonna(f"{dove}: duello INCONTRO BRANO")
            d["duelli"][int(p[1])] = p[2]
        elif chiave == "fuoco_di":
            if len(p) != 3:
                raise ErroreColonna(f"{dove}: fuoco_di EROE EFFETTO")
            d["fuoco"] = (p[1], p[2])
        elif chiave in ("titolo", "battaglia", "vittoria", "sconfitta"):
            if len(p) != 2:
                raise ErroreColonna(f"{dove}: {chiave} BRANO")
            d["schermate"][chiave] = p[1]
        else:
            raise ErroreColonna(f"{dove}: riga sconosciuta '{chiave}'")
    if d["fasi"] is None:
        raise ErroreColonna("colonna_sonora.txt: manca la riga 'fasi'")
    return d


# =================================================================================================
# Controlli e header
# =================================================================================================

def _id(nome):
    return nome.upper()


def risolvi(d, gioco, brani, effetti, luoghi_mondo, amici):
    """I dati controllati e tradotti in indici. Solleva ErroreColonna al primo problema."""
    def brano(b, dove):
        if b not in brani:
            raise ErroreColonna(f"{dove}: il brano '{b}' non c'e' in audio/")
        return b

    def effetto(e, dove):
        if e not in effetti:
            raise ErroreColonna(f"{dove}: l'effetto '{e}' non c'e' in audio/")
        return e

    usati_b, usati_e = set(), set()

    # le aree: tutte, nessuna di troppo, un brano esistente per fase
    for a in d["aree"]:
        if a not in gioco["aree"]:
            raise ErroreColonna(f"area {a}: non e' un'area del gioco (mondo::AreaId)")
    aree = []
    for a in gioco["aree"]:
        if a not in d["aree"]:
            raise ErroreColonna(f"area {a}: senza brano")
        aree.append([brano(b, f"area {a}") for b in d["aree"][a]])
        usati_b.update(aree[-1])

    # i luoghi: sull'edificio dell'area, un rettangolo di celle intorno ai portoni
    luoghi = []
    nomi_npc = [n for n, _ in gioco["npc"]]
    for l in d["luoghi"]:
        if l["area"] not in gioco["aree"]:
            raise ErroreColonna(f"{l['dove']}: {l['area']} non e' un'area del gioco")
        trovato = luoghi_mondo.get((l["area"], l["edificio"]))
        if not trovato or not trovato[0]:
            raise ErroreColonna(f"{l['dove']}: {l['area']} non ha l'edificio {l['edificio']} (o non ha portone)")
        portoni, larghezza, altezza = trovato
        r = l["raggio"]
        x0 = max(0, min(x for x, _ in portoni) - r)
        y0 = max(0, min(y for _, y in portoni) - r)
        x1 = min(larghezza - 1, max(x for x, _ in portoni) + r)
        y1 = min(altezza - 1, max(y for _, y in portoni) + r)
        if x1 > LATO_MAX or y1 > LATO_MAX:
            raise ErroreColonna(f"{l['dove']}: il luogo esce dagli uint8_t")
        npc = -1
        if l["amico"]:
            amico = amici.get(l["amico"])
            if not amico:
                raise ErroreColonna(f"{l['dove']}: l'amico {l['amico']} non e' in dati/amici.json")
            if amico["nome"] not in nomi_npc:
                raise ErroreColonna(f"{l['dove']}: {amico['nome']} non e' fra gli NPC di storia.h")
            npc = nomi_npc.index(amico["nome"])
            if gioco["npc"][npc][1] != l["area"]:
                raise ErroreColonna(f"{l['dove']}: {amico['nome']} non sta in {l['area']}")
        if l["modo"] == "segnale" and l["brano"] in d["aree"].get(l["area"], []):
            raise ErroreColonna(f"{l['dove']}: il segnale e' lo stesso brano dell'area")
        luoghi.append({"nome": l["nome"], "area": l["area"], "rett": (x0, y0, x1, y1),
                       "brano": brano(l["brano"], l["dove"]), "modo": l["modo"], "npc": npc})
        usati_b.add(l["brano"])

    # le cutscene: tutte quelle di regia, nessuna inventata
    for c in d["cutscene"]:
        if c not in gioco["cutscene"]:
            raise ErroreColonna(f"cutscene {c}: non c'e' in regia (regia::CUTSCENE_DATI)")
    cutscene = []
    for c in gioco["cutscene"]:
        if c not in d["cutscene"]:
            raise ErroreColonna(f"cutscene {c}: senza riga (il brano, o '-')")
        b, e = d["cutscene"][c]
        cutscene.append((None if b == "-" else brano(b, f"cutscene {c}"),
                         None if e == "-" else effetto(e, f"cutscene {c}")))
        usati_b.add(b)
        usati_e.add(e)

    # schermate e battaglia
    schermate = {}
    for k in ("titolo", "battaglia", "vittoria", "sconfitta"):
        if k not in d["schermate"]:
            raise ErroreColonna(f"manca la riga '{k}'")
        schermate[k] = brano(d["schermate"][k], k)
        usati_b.add(schermate[k])
    incontri = [schermate["battaglia"]] * gioco["incontri"]
    for i, b in d["duelli"].items():
        if i >= gioco["incontri"]:
            raise ErroreColonna(f"duello {i}: gli incontri sono {gioco['incontri']}")
        incontri[i] = brano(b, f"duello {i}")
        usati_b.add(b)

    # gli eventi della battaglia: tutti
    for k in d["eventi"]:
        if k not in gioco["eventi"]:
            raise ErroreColonna(f"evento {k}: non e' un battaglia::EventKind")
    eventi = []
    for k in gioco["eventi"]:
        if k not in d["eventi"]:
            raise ErroreColonna(f"evento {k}: senza riga (l'effetto, o '-')")
        e = d["eventi"][k]
        eventi.append(None if e == "-" else effetto(e, f"evento {k}"))
        usati_e.add(e)
    if not d["fuoco"] or d["fuoco"][0] not in gioco["eroi"]:
        raise ErroreColonna("fuoco_di: manca, o l'eroe non e' UBALDO, GIORGIO o ANTONIO")
    fuoco = (gioco["eroi"][d["fuoco"][0]], effetto(d["fuoco"][1], "fuoco_di"))
    usati_e.add(fuoco[1])

    usi = [(u, effetto(e, f"uso {u}")) for u, e in d["uso"].items()]
    usati_e.update(e for _, e in usi)

    orfani = [f"{b}.xm" for b in brani if b not in usati_b] + [f"{e}.wav" for e in effetti if e not in usati_e]
    if orfani:
        raise ErroreColonna("file di audio/ che nessuno usa: " + ", ".join(orfani))

    return {"aree": aree, "luoghi": luoghi, "cutscene": cutscene, "schermate": schermate, "incontri": incontri,
            "eventi": eventi, "fuoco": fuoco, "usi": usi}


def scrivi_header(r, gioco, brani, effetti, anelli):
    B = lambda b: f"Brano::{_id(b)}"                                     # noqa: E731
    E = lambda e: f"Effetto::{_id(e)}"                                   # noqa: E731
    ib = lambda b: f"int8_t({B(b)})" if b else "NESSUNO"                 # noqa: E731
    ie = lambda e: f"int8_t({E(e)})" if e else "NESSUNO"                 # noqa: E731
    o = ["// GENERATO da tools/genera_colonna_sonora.py da musica/colonna_sonora.txt e audio/: non modificare a mano.",
         "#ifndef GUBBIO_COLONNA_SONORA_H", "#define GUBBIO_COLONNA_SONORA_H", "", "#include <cstdint>", "",
         "namespace gubbio::colonna", "{", "",
         "// I brani di audio/*.xm e gli effetti di audio/*.wav, in ordine di nome (bn::music_items, bn::sound_items).",
         "enum class Brano : uint8_t", "{"]
    o += [f"    {_id(b)}," for b in brani] + ["};", "", f"inline constexpr int BRANI = {len(brani)};",
                                               "inline constexpr int NESSUNO = -1;   // nessun brano, nessun effetto", ""]
    o += ["// Torna da capo? I jingle (anello: no nella partitura) suonano una volta.",
          "inline constexpr bool IN_ANELLO[BRANI] = {"]
    o += [f"    {'true' if anelli[b] else 'false'},   // {b}" for b in brani] + ["};", ""]
    o += ["enum class Effetto : uint8_t", "{"] + [f"    {_id(e)}," for e in effetti]
    o += ["};", "", f"inline constexpr int EFFETTI = {len(effetti)};", ""]

    o += ["// Le fasi della musica: quelle degli NPC (storia::Fase) piu' l'alba dell'epilogo.",
          "enum class Fase : uint8_t", "{"] + [f"    {f.upper()}," for f in FASI]
    o += ["};", "", f"inline constexpr int FASI = {len(FASI)};", f"inline constexpr int AREE = {len(gioco['aree'])};", "",
          "// Il brano di ogni area (mondo::AreaId) in ogni fase.",
          "inline constexpr Brano BRANO_AREA[AREE][FASI] = {"]
    for a, riga in zip(gioco["aree"], r["aree"]):
        o.append("    { " + ", ".join(B(b) for b in riga) + " },   // " + a)
    o += ["};", ""]

    o += ["enum class Modo : uint8_t", "{", "    FONDO,      // al posto del brano dell'area, finche' si resta",
          "    SEGNALE,    // una volta entrando, poi torna il brano dell'area", "};", "",
          "// Un luogo dentro un'area: le celle da (x0, y0) a (x1, y1) comprese, intorno al portone di un edificio.",
          "struct Luogo", "{", "    uint8_t area;       // mondo::AreaId", "    uint8_t x0;", "    uint8_t y0;",
          "    uint8_t x1;", "    uint8_t y1;", "    Brano brano;", "    Modo modo;",
          "    int8_t npc;         // l'amico (storia::NPC_AMBIENTE) che deve essere in bottega, o -1", "};", "",
          f"inline constexpr int LUOGHI = {len(r['luoghi'])};",
          f"inline constexpr Luogo LUOGO[{max(1, len(r['luoghi']))}] = {{"]
    for l in r["luoghi"]:
        x0, y0, x1, y1 = l["rett"]
        o.append(f"    {{ {gioco['aree'].index(l['area'])}, {x0}, {y0}, {x1}, {y1}, {B(l['brano'])}, "
                 f"Modo::{l['modo'].upper()}, {l['npc']} }},   // {l['nome']}")
    o += ["};", ""]
    for l in r["luoghi"]:
        o.append(f"inline constexpr int LUOGO_{_id(l['nome'])} = {r['luoghi'].index(l)};")
    o.append("")

    o += [f"inline constexpr int CUTSCENE = {len(gioco['cutscene'])};",
          "// Per cutscene (regia::CUTSCENE_DATI): il codice (ricontrollato), il brano (Brano, o NESSUNO: resta",
          "// quello che suonava) e l'effetto del primo quadro (Effetto, o NESSUNO).",
          "inline constexpr const char* CODICE_CUTSCENE[CUTSCENE] = { " +
          ", ".join(f'"{c}"' for c in gioco["cutscene"]) + " };",
          "inline constexpr int8_t BRANO_CUTSCENE[CUTSCENE] = {"]
    o += [f"    {ib(b)},   // {c}" for c, (b, _) in zip(gioco["cutscene"], r["cutscene"])]
    o += ["};", "inline constexpr int8_t EFFETTO_CUTSCENE[CUTSCENE] = {"]
    o += [f"    {ie(e)},   // {c}" for c, (_, e) in zip(gioco["cutscene"], r["cutscene"])]
    o += ["};", ""]

    s = r["schermate"]
    o += [f"inline constexpr Brano BRANO_TITOLO = {B(s['titolo'])};",
          f"inline constexpr Brano BRANO_VITTORIA = {B(s['vittoria'])};",
          f"inline constexpr Brano BRANO_SCONFITTA = {B(s['sconfitta'])};", "",
          f"inline constexpr int INCONTRI = {gioco['incontri']};",
          "// Il brano di ogni incontro (battaglia::INCONTRO): la battaglia, o il duello.",
          "inline constexpr Brano BRANO_INCONTRO[INCONTRI] = { " + ", ".join(B(b) for b in r["incontri"]) + " };", ""]

    o += [f"inline constexpr int EVENTI = {len(gioco['eventi'])};",
          "// L'effetto di ogni evento della battaglia (battaglia::EventKind), o NESSUNO.",
          "inline constexpr int8_t EFFETTO_EVENTO[EVENTI] = {"]
    o += [f"    {ie(e)},   // {k}" for k, e in zip(gioco["eventi"], r["eventi"])]
    o += ["};", "", "// Il colpo di questo eroe non e' 'colpo': e' il suo fuoco.",
          f"inline constexpr int EROE_DEL_FUOCO = {r['fuoco'][0]};",
          f"inline constexpr Effetto EFFETTO_DEL_FUOCO = {E(r['fuoco'][1])};", ""]

    o += ["// Gli effetti dell'interfaccia, per uso (audio::suona).", "enum class Suono : uint8_t", "{"]
    o += [f"    {u}," for u, _ in r["usi"]] + ["};", "", f"inline constexpr int SUONI = {len(r['usi'])};",
                                                "inline constexpr Effetto EFFETTO_SUONO[SUONI] = {"]
    o += [f"    {E(e)},   // {u}" for u, e in r["usi"]] + ["};", "", "}", ""]

    o += ["// Gli item di Butano, nello stesso ordine: solo nella build della ROM, dove mmutil genera gli header.",
          '#if __has_include("bn_music_items.h") && __has_include("bn_sound_items.h")',
          '    #include "bn_music_items.h"', '    #include "bn_sound_items.h"', "",
          "namespace gubbio::colonna", "{", "",
          "inline constexpr bn::music_item MUSICA[BRANI] = {"]
    o += [f"    bn::music_items::{b}," for b in brani] + ["};", "", "inline constexpr bn::sound_item SUONO[EFFETTI] = {"]
    o += [f"    bn::sound_items::{e}," for e in effetti] + ["};", "", "}", "", "#endif", "", "#endif", ""]
    return "\n".join(o)


def genera(testo=None, gioco=None, audio=None, luoghi_mondo=None, amici=None):
    """Il testo di include/colonna_sonora.h. Gli argomenti sostituiscono i dati del repo (per i test)."""
    if testo is None:
        with open(DATI, encoding="utf-8") as f:
            testo = f.read()
    d = leggi_dati(testo)
    gioco = gioco or gioco_del_repo()
    brani, effetti, anelli = audio or audio_del_repo()
    amici = amici if amici is not None else amici_del_repo()
    if luoghi_mondo is None:
        luoghi_mondo = luoghi_del_mondo({(l["area"], l["edificio"]) for l in d["luoghi"]})
    r = risolvi(d, gioco, brani, effetti, luoghi_mondo, amici)
    return scrivi_header(r, gioco, brani, effetti, anelli)


def main(argv):
    try:
        testo = genera()
    except ErroreColonna as e:
        print(f"[colonna] ERRORE: {e}")
        return 1
    if "--scrivi" in argv:
        with open(USCITA, "w", encoding="utf-8", newline="\n") as f:
            f.write(testo)
        print(f"[colonna] scritto {os.path.relpath(USCITA, RADICE)}")
        return 0
    vecchio = open(USCITA, encoding="utf-8").read() if os.path.exists(USCITA) else ""
    if vecchio != testo:
        print("[colonna] include/colonna_sonora.h da rigenerare con --scrivi")
        return 1
    print("[colonna] aggiornato")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
