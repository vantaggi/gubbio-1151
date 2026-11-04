#!/usr/bin/env python3
"""Grafi e matrici dell'architettura di Gubbio 1151, ricavati dal codice vero.

    python3 tools/grafo_moduli.py              # riscrive docs/architettura/
    python3 tools/grafo_moduli.py --controlla  # esce con 1 se docs/architettura/ e' indietro o se trova errori

Cosa legge e cosa scrive (tutto in docs/architettura/, generato: non si modifica a mano):
- `moduli.mmd`, `matrice_moduli.csv`: chi include chi fra src/ e include/ (solo gli header del progetto e gli
  header che Butano genera dagli asset, `bn_*_items_*.h`);
- `matrice_asset.csv`: ogni file di graphics/ e audio/ e i sorgenti che lo usano (`bn::<tipo>_items::<nome>`
  oppure `#include "bn_<tipo>_items_<nome>.h"`);
- `aree.mmd`: le aree del gioco e i varchi fra di loro (mondo/varchi.json, la stessa fonte di include/mondo.h);
- `ARCHITETTURA.md`: il riassunto, con i controlli.

Controlli (errori: --controlla esce con 1): cicli fra gli header, header scritti a mano che nessuno include,
asset che nessun sorgente usa, varchi senza il ritorno, aree di include/mondo.h che mancano in varchi.json o il
contrario. Avvisi (solo nel riassunto): moduli scritti a mano molto lunghi o con molte dipendenze, candidati a
essere divisi.
"""
import csv
import io
import json
import os
import re
import sys

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USCITA = os.path.join(RADICE, "docs", "architettura")

# soglie degli avvisi: un modulo scritto a mano oltre queste misure e' un candidato da dividere
RIGHE_MOLTE = 1000
DIPENDENZE_MOLTE = 14

TIPI_ASSET = ("sprite_items", "regular_bg_items", "affine_bg_items", "sprite_palette_items",
              "bg_palette_items", "music_items", "sound_items")
# header di asset che si includono tutti insieme (non nominano un asset solo)
HEADER_ASSET_INSIEME = {"bn_music_items.h", "bn_sound_items.h"}


def _leggi(percorso):
    with open(percorso, encoding="utf-8", errors="replace") as f:
        return f.read()


def sorgenti():
    """{nome relativo: testo} di src/*.cpp e include/**/*.h, in ordine."""
    file = {}
    for cartella in ("src", "include"):
        base = os.path.join(RADICE, cartella)
        for radice, _, nomi in os.walk(base):
            for n in sorted(nomi):
                if n.endswith((".cpp", ".h")):
                    p = os.path.join(radice, n)
                    file[os.path.relpath(p, RADICE).replace(os.sep, "/")] = _leggi(p)
    return dict(sorted(file.items()))


def generatore(testo):
    """Lo script che genera l'header (dalle prime righe), o None se e' scritto a mano."""
    testa = "\n".join(testo.splitlines()[:6])
    if not re.search(r"GENERAT|[Nn]on modificare a mano", testa):
        return None
    m = re.search(r"((?:tools|stile)/[\w/]+\.py)", testa)
    return m.group(1) if m else "?"


def includi(testo):
    return re.findall(r'^\s*#\s*include\s+"([^"]+)"', testo, re.M)


def risolvi(nome, file):
    """Il file del progetto che un #include "nome" indica, o None (header di Butano)."""
    if f"include/{nome}" in file:
        return f"include/{nome}"
    return None


def modulo(percorso):
    """Il nome del modulo: src/x.cpp e include/x.h sono lo stesso modulo x."""
    nome = percorso.split("/", 1)[1]
    return nome[:-4] if nome.endswith(".cpp") else nome[:-2]


def grafo_include(file):
    archi = {}
    asset_inclusi = {}
    for p, testo in file.items():
        archi[p] = []
        for nome in includi(testo):
            dest = risolvi(nome, file)
            if dest:
                archi[p].append(dest)
            elif re.match(r"bn_\w+_items_\w+\.h$", nome) or nome in HEADER_ASSET_INSIEME:
                asset_inclusi.setdefault(p, []).append(nome)
    return archi, asset_inclusi


def cicli(archi):
    """Le componenti fortemente connesse con piu' di un file (Tarjan, iterativo)."""
    indice, basso, pila, in_pila, esito = {}, {}, [], set(), []
    contatore = [0]

    def visita(v):
        lavoro = [(v, iter(archi.get(v, [])))]
        indice[v] = basso[v] = contatore[0]
        contatore[0] += 1
        pila.append(v)
        in_pila.add(v)
        while lavoro:
            nodo, figli = lavoro[-1]
            avanti = False
            for w in figli:
                if w not in indice:
                    indice[w] = basso[w] = contatore[0]
                    contatore[0] += 1
                    pila.append(w)
                    in_pila.add(w)
                    lavoro.append((w, iter(archi.get(w, []))))
                    avanti = True
                    break
                if w in in_pila:
                    basso[nodo] = min(basso[nodo], indice[w])
            if avanti:
                continue
            lavoro.pop()
            if lavoro:
                basso[lavoro[-1][0]] = min(basso[lavoro[-1][0]], basso[nodo])
            if basso[nodo] == indice[nodo]:
                comp = []
                while True:
                    w = pila.pop()
                    in_pila.discard(w)
                    comp.append(w)
                    if w == nodo:
                        break
                if len(comp) > 1:
                    esito.append(sorted(comp))

    for v in sorted(archi):
        if v not in indice:
            visita(v)
    return sorted(esito)


def asset():
    """[(file, tipo)] di graphics/*.bmp (tipo dal .json) e audio/*."""
    elenco = []
    g = os.path.join(RADICE, "graphics")
    for n in sorted(os.listdir(g)):
        if n.endswith(".bmp"):
            meta = json.loads(_leggi(os.path.join(g, n[:-4] + ".json")))
            elenco.append((f"graphics/{n}", meta.get("type", "?")))
    a = os.path.join(RADICE, "audio")
    for n in sorted(os.listdir(a)):
        tipo = "music" if n.endswith((".xm", ".mod", ".s3m", ".it")) else "sound"
        elenco.append((f"audio/{n}", tipo))
    return elenco


def nome_asset(percorso):
    return os.path.splitext(os.path.basename(percorso))[0]


def uso_asset(file, asset_inclusi):
    """{asset: [sorgenti che lo usano]}."""
    uso = {}
    for p, tipo in asset():
        n = nome_asset(p)
        famiglia = ("sprite_items" if tipo == "sprite" else "regular_bg_items" if tipo == "regular_bg" else
                    "affine_bg_items" if tipo == "affine_bg" else "sprite_palette_items" if tipo == "sprite_palette"
                    else "bg_palette_items" if tipo == "bg_palette" else f"{tipo}_items")
        chi = []
        for s, testo in file.items():
            if re.search(rf"\b{famiglia}::{re.escape(n)}\b", testo) or f"bn_{famiglia}_{n}.h" in asset_inclusi.get(s, []):
                chi.append(s)
        uso[p] = chi
    return uso


def aree():
    """(varchi per area da mondo/varchi.json, aree di AreaId in include/mondo.h)."""
    varchi = json.loads(_leggi(os.path.join(RADICE, "mondo", "varchi.json")))["varchi"]
    mondo = _leggi(os.path.join(RADICE, "include", "mondo.h"))
    m = re.search(r"enum class AreaId[^{]*\{([^}]*)\}", mondo)
    enum = [x.strip() for x in m.group(1).split(",") if x.strip()] if m else []
    return varchi, enum


def analizza():
    file = sorgenti()
    archi, asset_inclusi = grafo_include(file)
    gen = {p: generatore(t) for p, t in file.items()}
    righe = {p: t.count("\n") for p, t in file.items()}
    entranti = {p: 0 for p in file}
    for p, dest in archi.items():
        for d in dest:
            entranti[d] += 1
    errori, avvisi = [], []

    for c in cicli(archi):
        errori.append("ciclo di include: " + " -> ".join(c))
    for p in file:
        if p.endswith(".h") and entranti[p] == 0 and gen[p] is None:
            errori.append(f"{p}: header scritto a mano che nessuno include")

    uso = uso_asset(file, asset_inclusi)
    for p, chi in uso.items():
        if not chi:
            errori.append(f"{p}: asset che nessun sorgente usa (orfano)")

    varchi, enum = aree()
    for a in enum:
        if a not in varchi:
            errori.append(f"area {a} in include/mondo.h ma non in mondo/varchi.json")
    for a in varchi:
        if a not in enum:
            errori.append(f"area {a} in mondo/varchi.json ma non in include/mondo.h")
    for a, vs in varchi.items():
        for v in vs:
            if not any(r["verso"] == a for r in varchi.get(v["verso"], [])):
                errori.append(f"varco {a} -> {v['verso']} senza il ritorno")

    for p in file:
        if gen[p] is None and righe[p] > RIGHE_MOLTE and "autotest" not in p:
            avvisi.append(f"{p}: {righe[p]} righe scritte a mano")
        if gen[p] is None and len(archi[p]) >= DIPENDENZE_MOLTE:
            avvisi.append(f"{p}: include {len(archi[p])} moduli del progetto")

    return {"file": file, "archi": archi, "gen": gen, "righe": righe, "entranti": entranti, "uso": uso,
            "varchi": varchi, "enum": enum, "errori": errori, "avvisi": avvisi}


# --------------------------------------------------------------------------------------------- uscite

def _id(p):
    return re.sub(r"\W", "_", p)


def mermaid_moduli(a):
    """Il grafo dei moduli: un nodo per modulo (x.cpp + x.h), gli autotest raccolti in un nodo solo."""
    def nodo(p):
        return "autotest" if os.path.basename(p).startswith("autotest_") else modulo(p)
    archi = set()
    for p, dest in a["archi"].items():
        for d in dest:
            if nodo(p) != nodo(d):
                archi.add((nodo(p), nodo(d)))
    generati = sorted({modulo(p) for p, g in a["gen"].items() if g})
    righe = ["%% GENERATO da tools/grafo_moduli.py: non modificare a mano.", "graph LR",
             "  classDef generato fill:#eee,stroke:#999,color:#555"]
    for x, y in sorted(archi):
        righe.append(f"  {_id(x)}[{x}] --> {_id(y)}[{y}]")
    if generati:
        righe.append("  class " + ",".join(_id(g) for g in generati) + " generato")
    return "\n".join(righe) + "\n"


def mermaid_aree(a):
    righe = ["%% GENERATO da tools/grafo_moduli.py da mondo/varchi.json: non modificare a mano.", "graph TD"]
    fatti = set()
    for x, vs in a["varchi"].items():
        for v in vs:
            y = v["verso"]
            chiave = tuple(sorted((x, y)))
            if chiave in fatti:
                continue
            fatti.add(chiave)
            freccia = "-.-" if v["lato"] == "dentro" or any(r["lato"] == "dentro" and r["verso"] == x
                                                             for r in a["varchi"].get(y, [])) else "---"
            righe.append(f"  {x} {freccia} {y}")
    return "\n".join(righe) + "\n"


def csv_moduli(a):
    nomi = sorted(a["file"])
    header = sorted(p for p in nomi if p.endswith(".h"))
    out = io.StringIO()
    w = csv.writer(out, lineterminator="\n")
    w.writerow(["file", "righe", "generato_da"] + header)
    for p in nomi:
        w.writerow([p, a["righe"][p], a["gen"][p] or ""] + ["1" if h in a["archi"][p] else "" for h in header])
    return out.getvalue()


def csv_asset(a):
    out = io.StringIO()
    w = csv.writer(out, lineterminator="\n")
    w.writerow(["asset", "usato_da"])
    for p, chi in a["uso"].items():
        w.writerow([p, " ".join(chi)])
    return out.getvalue()


def riassunto(a):
    mano = [p for p in a["file"] if a["gen"][p] is None]
    gen = [p for p in a["file"] if a["gen"][p]]
    piu_inclusi = sorted(a["file"], key=lambda p: (-a["entranti"][p], p))[:10]
    interni = [x for x, vs in a["varchi"].items() if all(v["lato"] == "basso" for v in vs) and len(vs) == 1
               and any(r["lato"] == "dentro" for r in a["varchi"].get(vs[0]["verso"], []))]
    r = ["<!-- GENERATO da tools/grafo_moduli.py: non modificare a mano. -->",
         "# Architettura del codice (fotografia del ramo)", "",
         "Si rifa' con `python3 tools/grafo_moduli.py`; `tests/test_architettura.py` controlla che sia aggiornata.",
         "", "| File | Cosa |", "| :-- | :-- |",
         "| [moduli.mmd](moduli.mmd) | grafo dei moduli (Mermaid): x.cpp e x.h sono un nodo; in grigio i generati |",
         "| [matrice_moduli.csv](matrice_moduli.csv) | chi include chi (righe: file; colonne: header) |",
         "| [matrice_asset.csv](matrice_asset.csv) | ogni asset di graphics/ e audio/ e chi lo usa |",
         "| [aree.mmd](aree.mmd) | aree e varchi (tratteggiati gli ingressi agli interni) |", "",
         "## Numeri", "",
         f"- {len(a['file'])} file: {len(mano)} scritti a mano ({sum(a['righe'][p] for p in mano)} righe), "
         f"{len(gen)} generati ({sum(a['righe'][p] for p in gen)} righe).",
         f"- {sum(len(d) for d in a['archi'].values())} include fra file del progetto.",
         f"- {len(a['uso'])} asset, {sum(1 for c in a['uso'].values() if c)} usati.",
         f"- {len(a['enum'])} aree, {len(interni)} interni con una sola porta; "
         f"{sum(len(v) for v in a['varchi'].values())} varchi.", "",
         "## Header generati e il loro script", "", "| Header | Generato da | Righe |", "| :-- | :-- | --: |"]
    for p in gen:
        r.append(f"| `{p}` | `{a['gen'][p]}` | {a['righe'][p]} |")
    r += ["", "## Gli header piu' inclusi", "", "| Header | Inclusi da |", "| :-- | --: |"]
    for p in piu_inclusi:
        r.append(f"| `{p}` | {a['entranti'][p]} |")
    r += ["", "## Controlli", ""]
    r += [f"- ERRORE: {e}" for e in a["errori"]] or ["- Nessun errore: niente cicli, niente header o asset orfani, "
                                                       "ogni varco ha il ritorno."]
    r += ["", "## Candidati da dividere (avvisi)", ""]
    r += [f"- {x}" for x in a["avvisi"]] or ["- Nessuno."]
    return "\n".join(r) + "\n"


def uscite(a):
    return {"moduli.mmd": mermaid_moduli(a), "aree.mmd": mermaid_aree(a), "matrice_moduli.csv": csv_moduli(a),
            "matrice_asset.csv": csv_asset(a), "ARCHITETTURA.md": riassunto(a)}


def indietro(a):
    """I file di docs/architettura/ diversi da come li scriverebbe lo script."""
    diversi = []
    for nome, testo in uscite(a).items():
        p = os.path.join(USCITA, nome)
        if not os.path.exists(p) or _leggi(p) != testo:
            diversi.append(nome)
    return diversi


def main(argv):
    a = analizza()
    if "--controlla" in argv:
        diversi = indietro(a)
        for d in diversi:
            print(f"docs/architettura/{d} e' indietro: python3 tools/grafo_moduli.py")
        for e in a["errori"]:
            print("ERRORE", e)
        return 1 if diversi or a["errori"] else 0
    os.makedirs(USCITA, exist_ok=True)
    for nome, testo in uscite(a).items():
        with open(os.path.join(USCITA, nome), "w", encoding="utf-8", newline="\n") as f:
            f.write(testo)
    for e in a["errori"]:
        print("ERRORE", e)
    for x in a["avvisi"]:
        print("avviso", x)
    print(f"docs/architettura/ scritto: {len(a['errori'])} errori, {len(a['avvisi'])} avvisi")
    return 1 if a["errori"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
