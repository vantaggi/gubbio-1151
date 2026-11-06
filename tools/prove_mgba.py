#!/usr/bin/env python3
"""Le prove nel gioco vero: ROM compilate coi modi GUBBIO_AVVIO, fatte girare in libmgba senza finestra
(tools/banco_mgba.c) col loro copione di tasti, e il log del gioco confrontato con quello che deve dire.

    python3 tools/prove_mgba.py                 # tutte le prove di tests/mgba/prove.json
    python3 tools/prove_mgba.py camminata       # quelle nominate
    python3 tools/prove_mgba.py --aggiorna      # riscrive le registrazioni in tests/dati/ col log nuovo
    python3 tools/prove_mgba.py --corte         # senza le lunghe (la caccia ai crash: docs/caccia_ai_crash.md)
    opzioni: -j N (prove in parallelo), --elenco

Serve: docker con l'immagine della CI (mirror.gcr.io/devkitpro/devkitarm:20260610, stesso digest di
toolchain.lock), libmgba-dev, gcc. In cloud: `nohup dockerd &` e `apt-get install -y libmgba-dev`.

Perche' e' veloce: ogni modo ha la sua cartella di oggetti (banco_obj<modo>/), quindi make ricompila solo
cio' che e' cambiato; e la ROM ha accanto l'impronta dei suoi sorgenti (src/, include/, graphics/, audio/,
Makefile, commit di Butano, modo, immagine): se l'impronta e' la stessa docker non parte neanche. Una prova
gira in qualche secondo (la camminata intera: 12 000 frame in circa 2 s).

Il formato delle prove e' spiegato in tests/mgba/prove.json.
"""
import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

RADICE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
PROVE = os.path.join(RADICE, "tests", "mgba", "prove.json")
CARTELLA = os.path.join(RADICE, "build_banco")
IMMAGINE = os.environ.get("BANCO_IMMAGINE", "mirror.gcr.io/devkitpro/devkitarm:20260610")
SORGENTI = ("src", "include", "graphics", "audio")
FILE_SOLI = ("Makefile",)
FRAME = re.compile(r"^\[\d+\] ")
# righe che nessuna prova accetta: un assert di Butano o un errore di mGBA (si cambia con "vietate": [...])
VIETATE = (r"(?i)\bassert", r"(?i)\bROM non caricata\b", r"^!! bloccato", r"^MGBA ")
# con -DGUBBIO_LIMITI (include/limiti.h): una riga a ogni nuovo picco di ogni risorsa; nessuna puo' passare la
# soglia (in percento del tetto), salvo i "tetti" della prova ({"sprite": 100, ...})
PICCO = re.compile(r"^LIMITI picco (\S+) (\d+) su (\d+) \((\d+)%\)")
SOGLIA = 90
CRASH = os.path.join(CARTELLA, "crash")
LOG = os.path.join(CARTELLA, "log")


def nome_rom(modo, flag):
    """Una cartella di oggetti per ogni combinazione di modo e flag: make non ricompila se cambiano solo i
    USERFLAGS, quindi due combinazioni non possono condividere gli oggetti."""
    if not flag:
        return str(modo)
    return f"{modo}_" + hashlib.sha256(" ".join(flag).encode()).hexdigest()[:8]


def impronta(modo, flag):
    h = hashlib.sha256(f"modo {modo}\nflag {' '.join(flag)}\nimmagine {IMMAGINE}\n".encode())
    butano = subprocess.run(["git", "-C", os.path.join(RADICE, "butano"), "rev-parse", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    h.update(f"butano {butano}\n".encode())
    file = [os.path.join(RADICE, f) for f in FILE_SOLI]
    for cartella in SORGENTI:
        for radice, sotto, nomi in os.walk(os.path.join(RADICE, cartella)):
            sotto.sort()
            file += [os.path.join(radice, n) for n in sorted(nomi)]
    for p in file:
        if os.path.isfile(p):
            h.update(os.path.relpath(p, RADICE).replace(os.sep, "/").encode() + b"\0")
            with open(p, "rb") as f:
                h.update(hashlib.sha256(f.read()).digest())
    return h.hexdigest()


def rom(modo, flag=()):
    """Il percorso della ROM del modo (con i flag in piu', es. -DGUBBIO_PRESTAZIONI), compilata solo se i
    sorgenti sono cambiati. Ritorna (rom, secondi, da_cache)."""
    os.makedirs(CARTELLA, exist_ok=True)
    n = nome_rom(modo, flag)
    gba = os.path.join(CARTELLA, f"gubbio_avvio{n}.gba")
    chiave_file = gba + ".impronta"
    chiave = impronta(modo, flag)
    if os.path.exists(gba) and os.path.exists(chiave_file) and open(chiave_file).read().strip() == chiave:
        return gba, 0.0, True
    t0 = time.perf_counter()
    # make non ricompila se cambiano solo i flag del Makefile (es. un BN_CFG_* in USERCXXFLAGS): allora
    # gli oggetti vecchi (anche quelli di Butano) vanno buttati, se no la ROM resta col flag di prima
    oggetti = os.path.join(RADICE, f"banco_obj{n}")
    with open(os.path.join(RADICE, "Makefile"), "rb") as f:
        impronta_make = hashlib.sha256(f.read()).hexdigest()
    segno = os.path.join(CARTELLA, f"makefile{n}.impronta")
    if os.path.isdir(oggetti) and (not os.path.exists(segno) or open(segno).read().strip() != impronta_make):
        shutil.rmtree(oggetti, ignore_errors=True)
        if os.path.isdir(oggetti):
            subprocess.run(["sudo", "rm", "-rf", oggetti], check=False)
    comando = ("git config --global --add safe.directory /w; git config --global --add safe.directory /w/butano; "
               f"make -j{os.cpu_count() or 4} TARGET=banco_rom{n} BUILD=banco_obj{n} "
               f"USERFLAGS='-DGUBBIO_AVVIO={modo} {' '.join(flag)}'")
    log = os.path.join(CARTELLA, f"build{n}.log")
    with open(log, "w") as f:
        r = subprocess.run(["docker", "run", "--rm", "-v", f"{RADICE}:/w", "-w", "/w", IMMAGINE, "bash", "-c", comando],
                           stdout=f, stderr=subprocess.STDOUT)
    if r.returncode != 0:
        with open(log) as f:
            coda = f.read()[-3000:]
        raise RuntimeError(f"la ROM {n} non compila (log in {os.path.relpath(log, RADICE)}):\n{coda}")
    shutil.move(os.path.join(RADICE, f"banco_rom{n}.gba"), gba)
    elf = os.path.join(RADICE, f"banco_rom{n}.elf")
    if os.path.exists(elf):
        os.remove(elf)
    with open(chiave_file, "w") as f:
        f.write(chiave + "\n")
    with open(segno, "w") as f:
        f.write(impronta_make + "\n")
    return gba, time.perf_counter() - t0, False


def banco():
    sorgente = os.path.join(RADICE, "tools", "banco_mgba.c")
    eseguibile = os.path.join(CARTELLA, "banco")
    chiave = hashlib.sha256(open(sorgente, "rb").read()).hexdigest()
    if not (os.path.exists(eseguibile) and os.path.exists(eseguibile + ".impronta")
            and open(eseguibile + ".impronta").read().strip() == chiave):
        os.makedirs(CARTELLA, exist_ok=True)
        subprocess.run(["gcc", "-O2", "-o", eseguibile, sorgente, "-lmgba"], check=True)
        with open(eseguibile + ".impronta", "w") as f:
            f.write(chiave + "\n")
    return eseguibile


def manca_qualcosa():
    if not shutil.which("docker"):
        return "manca docker"
    if subprocess.run(["docker", "info"], capture_output=True).returncode != 0:
        return "docker non risponde (in cloud: nohup dockerd &)"
    if not shutil.which("gcc"):
        return "manca gcc"
    prova = subprocess.run(["gcc", "-xc", "-", "-o", os.devnull, "-lmgba"], input="int main(){return 0;}",
                           capture_output=True, text=True)
    if prova.returncode != 0:
        return "manca libmgba (apt-get install -y libmgba-dev)"
    return None


def gira(prova, eseguibile, gba, aggiorna):
    """Fa girare la prova e ritorna (nome, errori, secondi, log)."""
    t0 = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix=f"mgba_{prova['nome']}_") as dove:
        copione = os.path.join(dove, "copione.txt")
        if "copione_file" in prova:
            shutil.copy(os.path.join(RADICE, prova["copione_file"]), copione)
        else:
            with open(copione, "w") as f:
                f.write("\n".join(prova["copione"]) + "\n")
        r = subprocess.run([eseguibile, gba, copione], cwd=dove, capture_output=True, text=True,
                           errors="replace", timeout=prova.get("secondi", 300))
        foto_assert = salva_foto_assert(prova["nome"], dove)
    righe = [FRAME.sub("", x) for x in r.stderr.splitlines()]
    os.makedirs(LOG, exist_ok=True)               # il log intero, per rileggerlo dopo (anche quando passa)
    with open(os.path.join(LOG, f"{prova['nome']}.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write(r.stderr)
    errori = []
    if foto_assert and not prova.get("assert_atteso"):
        errori.append(f"assert di Butano: la schermata e' in {os.path.relpath(foto_assert, RADICE)}")
    errori += vicino_al_tetto(righe, prova.get("tetti", {}))
    for attesa in prova.get("attese", []):
        if not any(re.search(attesa, x) for x in righe):
            errori.append(f"nel log manca una riga come /{attesa}/")
    for vietata in prova.get("vietate", VIETATE):
        cattive = [x for x in righe if re.search(vietata, x)]
        if cattive:
            errori.append(f"nel log c'e' /{vietata}/: {cattive[0]!r}")
    for limite in prova.get("limiti", []):
        valori, scarta = [], 0
        for x in righe:
            if limite.get("scarta_dopo") and re.search(limite["scarta_dopo"], x):
                scarta = limite.get("quante", 1)          # la finestra del cambio d'area non conta
                continue
            m = re.search(limite["regex"], x)
            if m:
                if scarta:
                    scarta -= 1
                    continue
                valori.append(int(m.group(1)))
        if "righe" in limite and len(valori) != limite["righe"]:
            errori.append(f"/{limite['regex']}/ compare {len(valori)} volte, ne servono {limite['righe']}")
        if not valori:
            errori.append(f"nel log manca /{limite['regex']}/")
            continue
        if "massimo" in limite and max(valori) > limite["massimo"]:
            errori.append(f"/{limite['regex']}/ arriva a {max(valori)}, il massimo e' {limite['massimo']}")
        if "sopra" in limite:                         # un picco ogni tanto va bene, un costo fisso no
            oltre = sum(v > limite["sopra"] for v in valori)
            if oltre > limite.get("al_piu", 0):
                errori.append(f"/{limite['regex']}/ supera {limite['sopra']} in {oltre} righe su {len(valori)}, "
                              f"al piu' {limite.get('al_piu', 0)}")
        if "minimo" in limite and min(valori) < limite["minimo"]:
            errori.append(f"/{limite['regex']}/ scende a {min(valori)}, il minimo e' {limite['minimo']}")
    if prova.get("assert_atteso") and not foto_assert:
        errori.append("l'assert voluto non ha lasciato la foto della schermata d'errore")
    reg = prova.get("registrazione")
    if reg:
        dentro = [x for x in righe if re.search(reg["filtro"], x) and not x.startswith("LIMITI ")]
        percorso = os.path.join(RADICE, reg["file"])
        attese = open(percorso, encoding="utf-8").read().splitlines() if os.path.exists(percorso) else []
        if dentro != attese:
            if aggiorna:
                with open(percorso, "w", encoding="utf-8", newline="\n") as f:
                    f.write("\n".join(dentro) + "\n")
            else:
                prima = next((i for i, (x, y) in enumerate(zip(dentro, attese)) if x != y), min(len(dentro), len(attese)))
                errori.append(f"il log non rifa' {reg['file']}: {len(dentro)} righe contro {len(attese)}, la prima diversa "
                              f"e' la {prima + 1}: {dentro[prima] if prima < len(dentro) else '(finito)'!r} invece di "
                              f"{attese[prima] if prima < len(attese) else '(finito)'!r} (--aggiorna se il cambio e' voluto)")
    return prova["nome"], errori, time.perf_counter() - t0, righe


def vicino_al_tetto(righe, tetti):
    """Le risorse di -DGUBBIO_LIMITI oltre la soglia (SOGLIA, o quella della prova in tetti): un errore per
    risorsa, col suo picco piu' alto."""
    picchi = {}
    for x in righe:
        m = PICCO.match(x)
        if m and int(m.group(4)) >= picchi.get(m.group(1), (0, 0, -1, ""))[2]:
            picchi[m.group(1)] = (int(m.group(2)), int(m.group(3)), int(m.group(4)), x)
    errori = []
    for nome, (uso, tetto, percento, riga) in sorted(picchi.items()):
        if percento > tetti.get(nome, SOGLIA):
            errori.append(f"{nome} vicino al tetto: {uso} su {tetto} ({percento}%, soglia {tetti.get(nome, SOGLIA)}%): {riga!r}")
    return errori


def salva_foto_assert(nome, dove):
    """La schermata d'errore di Butano (assert.ppm del banco) in build_banco/crash/<prova>.png, se c'e'."""
    ppm = os.path.join(dove, "assert.ppm")
    if not os.path.exists(ppm):
        return None
    os.makedirs(CRASH, exist_ok=True)
    try:
        from PIL import Image
        destinazione = os.path.join(CRASH, f"{nome}.png")
        Image.open(ppm).resize((480, 320), Image.NEAREST).save(destinazione)
    except ImportError:
        destinazione = os.path.join(CRASH, f"{nome}.ppm")
        shutil.copy(ppm, destinazione)
    return destinazione


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("nomi", nargs="*")
    ap.add_argument("--aggiorna", action="store_true")
    ap.add_argument("--elenco", action="store_true")
    ap.add_argument("--corte", action="store_true", help="senza le prove lunghe (la caccia ai crash)")
    ap.add_argument("-j", type=int, default=os.cpu_count() or 2)
    a = ap.parse_args(argv)
    with open(PROVE, encoding="utf-8") as f:
        prove = json.load(f)["prove"]
    if a.nomi:
        sconosciute = set(a.nomi) - {p["nome"] for p in prove}
        if sconosciute:
            print(f"[mgba] prove sconosciute: {', '.join(sorted(sconosciute))}", file=sys.stderr)
            return 2
        prove = [p for p in prove if p["nome"] in a.nomi]
    elif a.corte:
        prove = [p for p in prove if not p.get("lunga")]
    for p in prove:
        print(f"[mgba]   {p['nome']:16s} modo {p['modo']:2d} {' '.join(p.get('flag', [])):24s} {p['cosa'][:70]}")
    if a.elenco:
        return 0
    motivo = manca_qualcosa()
    if motivo:
        print(f"[mgba] NON ESEGUITE: {motivo}. Le prove in mGBA girano in cloud o su Linux.", file=sys.stderr)
        return 3
    t0 = time.perf_counter()
    eseguibile = banco()
    roms = {}
    for chiave in sorted({(p["modo"], tuple(p.get("flag", []))) for p in prove}):   # una alla volta: make usa gia' tutti i core
        try:
            roms[chiave], secondi, cache = rom(*chiave)
        except RuntimeError as e:
            print(f"[mgba] FALLITO {e}", file=sys.stderr)
            return 1
        print(f"[mgba] ROM del modo {chiave[0]} {' '.join(chiave[1])}: " + ("dalla cache" if cache else f"compilata in {secondi:.0f} s"), flush=True)
    falliti = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, a.j)) as ex:
        for nome, errori, secondi, righe in ex.map(lambda p: gira(p, eseguibile, roms[(p["modo"], tuple(p.get("flag", [])))], a.aggiorna), prove):
            print(f"[mgba] {'ok' if not errori else 'FALLITO':7s} {nome:16s} {secondi:5.1f} s", flush=True)
            for e in errori:
                print(f"         {e}", file=sys.stderr)
            if errori:
                falliti += 1
                print("         ultime righe del log:\n" + "\n".join("           " + x for x in righe[-8:]), file=sys.stderr)
    print(f"[mgba] {len(prove)} prove in {time.perf_counter() - t0:.1f} s, {falliti} fallite")
    return 1 if falliti else 0


if __name__ == "__main__":
    sys.exit(main())
