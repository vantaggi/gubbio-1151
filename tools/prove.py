#!/usr/bin/env python3
"""Le prove Python di tests/, veloci: in parallelo e, di default, solo quelle toccate dalla modifica.

    python3 tools/prove.py              # solo i test che leggono un file cambiato rispetto a origin/main
    python3 tools/prove.py --da HEAD    # ... rispetto a un altro punto (qui: le sole modifiche non committate)
    python3 tools/prove.py --veloci     # tutti tranne i lenti (quelli che l'ultima volta hanno superato 15 s)
    python3 tools/prove.py --tutte      # tutti, in parallelo: prima di una fusione (la CI fa lo stesso)
    python3 tools/prove.py test_mondo test_storia.Storia     # quelli nominati
    opzioni: -j N processi (default: i core), --elenco (dice cosa farebbe e si ferma)

Come sa quali test toccano un file: ogni volta che un modulo di test gira, un gancio di audit
(tools/prove/sitecustomize.py, anche nei processi figli) annota i file che apre e le cartelle che elenca o
in cui cerca con glob. Le tracce stanno in build_prove/tracce.json (fuori dal repo) con i tempi. Un file
cambiato tocca un modulo se il modulo l'ha letto o se ha guardato nella sua cartella (cosi' conta anche
un file nuovo o tolto). Un modulo senza traccia, nuovo o cambiato, gira sempre. Se non e' cambiato niente
non gira niente. La scelta serve al giro corto mentre si lavora: prima di fondere si lancia --tutte.

I moduli piu' lunghi si dividono per classe, cosi' i pezzi vanno su core diversi; si parte dai piu' lunghi.
Ogni pezzo e' un `python -m unittest` a se': nessun test si salta (tools/check_no_skip.py vale lo stesso).
"""
import argparse
import concurrent.futures
import fnmatch
import json
import os
import re
import subprocess
import sys
import tempfile
import time

RADICE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
TESTS = os.path.join(RADICE, "tests")
GANCIO = os.path.join(RADICE, "tools", "prove")
CARTELLA = os.path.join(RADICE, "build_prove")
TRACCE = os.path.join(CARTELLA, "tracce.json")
LENTO = 15.0             # secondi: oltre, il modulo e' lento (--veloci lo lascia alla CI)
DA_DIVIDERE = 20.0       # secondi: oltre, il modulo si divide per classe
MAX_PEZZI = 3           # oltre non conviene: ogni pezzo rifà da sé il lavoro comune (es. il mondo, 13 s)
# i file da cui dipende la ROM o il banco: se ne cambia uno girano anche le prove in mGBA (tools/prove_mgba.py)
DELLA_ROM = re.compile(r"^(src/|include/|graphics/|audio/|butano$|Makefile$|tests/mgba/|tests/dati/.*_mgba\.txt$|tools/(banco_mgba\.c|prove_mgba\.py)$)")
IGNORATI = re.compile(r"(^|/)(__pycache__|\.git)(/|$)|\.pyc$")


def rel(p):
    r = os.path.relpath(os.path.abspath(p), RADICE).replace(os.sep, "/")
    return None if r.startswith("../") or r == ".." else r


def carica_tracce():
    try:
        with open(TRACCE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def salva_tracce(tracce):
    os.makedirs(CARTELLA, exist_ok=True)
    tmp = TRACCE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(tracce, f, indent=0, sort_keys=True)
    os.replace(tmp, TRACCE)


def moduli_di_test():
    return sorted(f[:-3] for f in os.listdir(TESTS) if f.startswith("test_") and f.endswith(".py"))


def classi_di(modulo):
    """Le classi TestCase di un modulo, lette dal sorgente (senza importarlo)."""
    with open(os.path.join(TESTS, modulo + ".py"), encoding="utf-8") as f:
        return re.findall(r"^class (\w+)\(.*TestCase\)", f.read(), re.M)


def git(*argomenti):
    r = subprocess.run(["git", *argomenti], cwd=RADICE, capture_output=True, text=True)
    return r.stdout.split("\n") if r.returncode == 0 else None


def file_cambiati(da):
    """{file: True se nuovo o tolto, False se solo modificato} rispetto al punto in comune con 'da'."""
    base = git("merge-base", "HEAD", da)
    if not base or not base[0]:
        print(f"[prove] non trovo {da}: giro tutto", file=sys.stderr)
        return None
    cambiati = {}
    for r in git("diff", "--name-status", "--no-renames", base[0]) or []:
        stato, _, nome = r.partition("\t")
        if nome and not IGNORATI.search(nome):
            cambiati[nome] = stato[:1] in "AD"
    for nome in git("ls-files", "--others", "--exclude-standard") or []:
        if nome and not IGNORATI.search(nome):
            cambiati[nome] = True
    return cambiati


def tocca(traccia, cambiati):
    """I file cambiati che il modulo ha letto; e quelli nuovi o tolti in una cartella che ha elencato o in
    cui ha cercato con glob (un .area nuovo conta per chi legge mondo/aree/*.area)."""
    letti, cartelle, motivi = set(traccia["f"]), set(traccia["d"]), set()
    for c, nuovo_o_tolto in cambiati.items():
        if c in letti or any(fnmatch.fnmatch(c, g) for g in traccia["g"]) or (nuovo_o_tolto and os.path.dirname(c) in cartelle):
            motivi.add(c)
    return motivi


def pezzi(moduli, tracce):
    """[(nome, [bersagli unittest], moduli coinvolti)], dal piu' lungo; i moduli lenti divisi per classe."""
    out = []
    for m in moduli:
        tempo = tracce.get(m, {}).get("tempo", 0.0)
        classi = classi_di(m) if tempo > DA_DIVIDERE else []
        if len(classi) > 1:
            n = min(len(classi), MAX_PEZZI, os.cpu_count() or 2)
            gruppi = [classi[i::n] for i in range(n)]
            for k, g in enumerate(gruppi):
                out.append((f"{m}[{k + 1}/{n}]", [f"{m}.{c}" for c in g], m, tempo / n))
        else:
            out.append((m, [m], m, tempo))
    return sorted(out, key=lambda p: -p[3])


def esegui(pezzo):
    nome, bersagli, modulo, _ = pezzo
    fd, traccia = tempfile.mkstemp(prefix="traccia_", suffix=".txt", dir=CARTELLA)
    os.close(fd)
    env = dict(os.environ, GUBBIO_TRACCIA=traccia,
               PYTHONPATH=os.pathsep.join([GANCIO, TESTS] + ([os.environ["PYTHONPATH"]] if os.environ.get("PYTHONPATH") else [])),
               PYTHONDONTWRITEBYTECODE="1")
    t0 = time.perf_counter()
    r = subprocess.run([sys.executable, "-m", "unittest", *bersagli], cwd=RADICE, env=env,
                       capture_output=True, text=True)
    durata = time.perf_counter() - t0
    letti = {"f": set(), "d": set(), "g": set()}
    with open(traccia, encoding="utf-8") as f:
        for riga in f:
            tipo, _, p = riga.rstrip("\n").partition("\t")
            q = rel(p)
            # un modulo importato dal suo .pyc: conta il sorgente (tools/__pycache__/x.cpython-313.pyc -> tools/x.py)
            pyc = re.match(r"(.*?)/?__pycache__/([^/.]+)\.[^/]*\.pyc$", q or "")
            if pyc:
                q = (pyc.group(1) + "/" if pyc.group(1) else "") + pyc.group(2) + ".py"
            if q is not None and not IGNORATI.search(q) and not q.startswith("build_prove"):
                letti[tipo].add(q if q != "." else "")
    os.remove(traccia)
    conto = re.search(r"Ran (\d+) test", r.stderr)
    return nome, modulo, r.returncode, durata, int(conto.group(1)) if conto else 0, r.stderr, letti


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("nomi", nargs="*", help="moduli o test da far girare (es. test_mondo, test_mondo.Mondo)")
    ap.add_argument("--tutte", action="store_true")
    ap.add_argument("--veloci", action="store_true")
    ap.add_argument("--da", default="origin/main")
    ap.add_argument("-j", type=int, default=os.cpu_count() or 2)
    ap.add_argument("--elenco", action="store_true")
    ap.add_argument("--senza-mgba", action="store_true", help="non lanciare le prove in mGBA anche se la ROM e' cambiata")
    a = ap.parse_args()
    os.makedirs(CARTELLA, exist_ok=True)
    tracce = carica_tracce()
    tutti = moduli_di_test()

    perche = {}
    mgba = a.tutte
    if a.nomi:
        scelti = [n for n in a.nomi]
        lista = [(n, [n], n.split(".")[0], tracce.get(n.split(".")[0], {}).get("tempo", 0.0)) for n in scelti]
    else:
        if a.tutte:
            scelti = tutti
        elif a.veloci:
            scelti = [m for m in tutti if tracce.get(m, {}).get("tempo", 0.0) <= LENTO]
            lenti = sorted(set(tutti) - set(scelti))
            if lenti:
                print(f"[prove] lenti, lasciati alla CI e a --tutte: {', '.join(lenti)}")
        else:
            cambiati = file_cambiati(a.da)
            if cambiati is None:
                scelti = tutti
            else:
                scelti = []
                for m in tutti:
                    if m not in tracce:
                        scelti.append(m)
                        perche[m] = "nessuna traccia"
                        continue
                    motivi = tocca(tracce[m], cambiati)
                    if motivi:
                        scelti.append(m)
                        perche[m] = ", ".join(sorted(motivi)[:3]) + (" ..." if len(motivi) > 3 else "")
                print(f"[prove] {len(cambiati)} file cambiati rispetto a {a.da}; {len(scelti)} moduli su {len(tutti)} li leggono")
                della_rom = sorted(c for c in cambiati if DELLA_ROM.search(c))
                if della_rom:
                    mgba = True
                    print(f"[prove] cambia la ROM ({', '.join(della_rom[:3])}{' ...' if len(della_rom) > 3 else ''}): anche le prove in mGBA")
        lista = pezzi(scelti, tracce)

    for nome, _, m, tempo in lista:
        motivo = f"  ({perche[m]})" if m in perche else ""
        print(f"[prove]   {nome:32s} ~{tempo:5.1f} s{motivo}")
    mgba = mgba and not a.senza_mgba
    if a.elenco:
        return 0
    if not lista:
        print("[prove] niente da provare in Python")
        return prove_mgba(a.j) if mgba else 0

    t0 = time.perf_counter()
    falliti, conti, nuove = [], 0, {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, a.j)) as ex:
        for nome, modulo, codice, durata, n, uscita, letti in ex.map(esegui, lista):
            conti += n
            stato = "ok" if codice == 0 else "FALLITO"
            print(f"[prove] {stato:7s} {nome:32s} {n:4d} test {durata:6.1f} s", flush=True)
            if codice:
                falliti.append((nome, uscita))
            voce = nuove.setdefault(modulo, {"f": set(), "d": set(), "g": set(), "tempo": 0.0, "intero": True})
            for k in "fdg":
                voce[k] |= letti[k]
            voce["tempo"] += durata
            voce["intero"] &= nome == modulo or "[" in nome
    for nome, uscita in falliti:
        print(f"\n===== {nome} =====\n{uscita}", file=sys.stderr)

    tracce = carica_tracce()
    for modulo, v in nuove.items():
        vecchia = tracce.get(modulo, {})
        if not v["intero"] and vecchia:           # un test solo: si aggiungono le letture, il tempo resta
            for k in "fdg":
                vecchia[k] = sorted(set(vecchia[k]) | v[k])
            continue
        tracce[modulo] = {"f": sorted(v["f"]), "d": sorted(v["d"]), "g": sorted(v["g"]), "tempo": round(v["tempo"], 2)}
    salva_tracce(tracce)
    print(f"[prove] {conti} test in {time.perf_counter() - t0:.1f} s, {len(falliti)} pezzi falliti")
    esito = 1 if falliti else 0
    return max(esito, prove_mgba(a.j)) if mgba else esito


def prove_mgba(j):
    """Le prove in mGBA. Se qui non si possono fare (niente docker o libmgba, es. sul PC Windows) lo dice e
    non fallisce: le fa il prossimo giro in cloud prima della fusione."""
    sys.path.insert(0, os.path.join(RADICE, "tools"))
    import prove_mgba as P
    esito = P.main(["-j", str(j)])
    if esito == 3:
        print("[prove] ATTENZIONE: prove in mGBA non fatte qui; vanno fatte prima di fondere", file=sys.stderr)
        return 0
    return esito


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:          # python3 tools/prove.py --elenco | head
        sys.exit(0)
