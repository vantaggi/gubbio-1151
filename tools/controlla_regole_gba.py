#!/usr/bin/env python3
"""Le regole di sviluppo GBA (docs/regole_sviluppo_gba.md) controllate sul codice C++ di src/ e include/.

    python3 tools/controlla_regole_gba.py        # 0 se tutto a posto, 1 con l'elenco di cosa non va

Quello che si vede dal sorgente. Il resto lo controlla la ROM: tools/check_zero_heap.sh (niente heap ne'
virgola mobile nell'ELF), tools/controlla_divisioni.py (niente divisioni software nel ciclo di ogni frame),
tools/controlla_struct.py (l'ordine dei campi). Regole controllate qui:

  R1  niente float o double, niente header della libreria standard pesante (<cmath>, <vector>, <string>...),
      niente std:: (si usano bn::fixed e i contenitori bn::)
  R2  niente heap: new, delete, malloc e famiglia
  R3  le tabelle costanti sono constexpr (in ROM, zero byte di RAM): niente `const T x[] = { ... }` fatto
      solo di costanti
  R4  i tipi pesanti (contenitori bn::, GameState e le struct grandi) si passano per riferimento, non per valore
  R5  niente bn::sprite_text_generator: il testo passa da VistaTesto e VistaNumero, che ridisegnano solo quando
      il testo cambia
  R6  BN_CODE_IWRAM solo con il perche' nella riga sopra (// IWRAM: ...): la IWRAM e' 32 KB
  R7  il pannello di debug (L+Select) resta nel ciclo del gioco
  R8  la scena vecchia si distrugge prima della nuova: dopo esplorazione.sospendi() (che rende fondale, tile e
      sprite) viene un frame, bn::core::update() o attendi(n), prima di creare la battaglia o la cutscene

Gli autotest (src/autotest_*.cpp) girano a tempo di compilazione: R3 e R4 non valgono per loro.
"""
import glob
import os
import re
import sys

RADICE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

HEADER_VIETATI = ("cmath", "math.h", "vector", "string", "map", "unordered_map", "list", "deque", "memory",
                  "algorithm", "iostream", "sstream", "fstream", "array", "functional", "cstdio", "stdio.h",
                  "cstdlib", "stdlib.h", "cstring", "string.h", "regex", "thread", "chrono", "random")
PESANTI = ("GameState", "SaveData", "Battaglia", "Unita", "Opzioni", "Statistiche", "Area", "Scena", "Quadro")


def sorgenti():
    return sorted(glob.glob(os.path.join(RADICE, "src", "*.cpp")) + glob.glob(os.path.join(RADICE, "include", "*.h")))


def senza_commenti(testo):
    """Il testo con commenti e stringhe vuotati (stesse righe, per i numeri di riga)."""
    def vuota(m):
        return re.sub(r"[^\n]", " ", m.group(0))
    return re.sub(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\'', vuota, testo, flags=re.S)


def solo_costanti(inizializzatore):
    """Vero se l'inizializzatore e' fatto solo di letterali, enum qualificati (A::B), costanti MAIUSCOLE e
    conversioni int(...)/uint8_t(...) di queste: allora la tabella poteva essere constexpr."""
    corpo = re.sub(r"\b(?:int|u?int(?:8|16|32)_t|char32_t|bool)\s*\(", "(", inizializzatore)
    for t in re.findall(r"[A-Za-z_][\w:]*", corpo):
        if t in ("true", "false", "nullptr"):
            continue
        if "::" in t or re.fullmatch(r"[A-Z][A-Z0-9_]*", t):
            continue
        return False
    return True


def controlla_testo(nome, testo):
    """Le violazioni di un file, come righe 'file:riga: Rn messaggio'."""
    errori = []
    pulito = senza_commenti(testo)
    righe = pulito.splitlines()
    originali = testo.splitlines()
    autotest = os.path.basename(nome).startswith("autotest_")

    def errore(i, regola, msg):
        errori.append(f"{nome}:{i + 1}: {regola} {msg}: {originali[i].strip()}")

    for i, r in enumerate(righe):
        if re.search(r"\b(float|double)\b", r):
            errore(i, "R1", "virgola mobile (usare bn::fixed)")
        m = re.match(r"\s*#\s*include\s*<([\w./]+)>", originali[i])
        if m and m.group(1) in HEADER_VIETATI:
            errore(i, "R1", f"<{m.group(1)}> della libreria standard (usare il corrispettivo bn::)")
        if re.search(r"\bstd::(?!initializer_list\b)\w+", r):
            errore(i, "R1", "std:: (usare il corrispettivo bn::)")
        if re.search(r"\bnew\s+[\w:(]|\bdelete\s+[\w(\[]|\bdelete\s*\[\]|\b(malloc|calloc|realloc|free)\s*\(", r):
            errore(i, "R2", "allocazione dinamica")
        if "sprite_text_generator" in r:
            errore(i, "R5", "bn::sprite_text_generator (usare VistaTesto/VistaNumero)")
        if "BN_CODE_IWRAM" in r and not re.match(r"\s*#\s*define", r):
            sopra = originali[i - 1] if i > 0 else ""
            if "// IWRAM:" not in sopra and "// IWRAM:" not in originali[i]:
                errore(i, "R6", "BN_CODE_IWRAM senza il perche' (// IWRAM: ...) nella riga sopra")
        if re.search(r"\bsospendi\(\)\s*;", r) and not re.match(r"\s*void\b", r):
            dopo = next((righe[j].strip() for j in range(i + 1, min(i + 8, len(righe))) if righe[j].strip()), "")
            if not re.match(r"(bn::core::update\(\)|attendi\(\d+\))\s*;", dopo):
                errore(i, "R8", "dopo sospendi() serve un frame (bn::core::update() o attendi) prima della scena nuova")
        if autotest:
            continue
        # R3: const T nome[...] = { ... };  (fino al primo '};')
        m = re.match(r"\s*(?:static\s+)?const\s+(?!.*constexpr)[\w:<>, ]+?\s+\w+\s*(?:\[[^\]]*\])+\s*=\s*\{", r)
        if m:
            corpo = []
            for j in range(i, min(i + 200, len(righe))):
                corpo.append(righe[j] if j > i else righe[j][m.end() - 1:])
                if "};" in righe[j]:
                    break
            if solo_costanti("\n".join(corpo)):
                errore(i, "R3", "tabella costante non constexpr")
        # R4: un parametro pesante per valore (non consteval: quelle girano nel compilatore)
        if "consteval" not in r:
            for t in PESANTI:
                if re.search(r"[(,]\s*(?:const\s+)?(?:\w+::)*" + t + r"\s+\w+\s*(?:[,)]|=[^=])", r) and \
                        not re.search(r"\b" + t + r"\s+\w+\s*\(", r):
                    errore(i, "R4", f"{t} passato per valore (usare const {t}&)")
            if re.search(r"[(,]\s*(?:const\s+)?bn::(?:string|vector|array|deque|list|pool|unordered_map|"
                         r"istring|bitset)<[^>]*>\s+\w+\s*[,)]", r):
                errore(i, "R4", "contenitore bn:: passato per valore (usare const T&)")
    return errori


def controlla():
    errori = []
    for p in sorgenti():
        with open(p, encoding="utf-8") as f:
            errori += controlla_testo(os.path.relpath(p, RADICE).replace(os.sep, "/"), f.read())
    with open(os.path.join(RADICE, "src", "main.cpp"), encoding="utf-8") as f:
        main = f.read()
    if not re.search(r"PannelloDebug\s+\w+\s*\(", main) or not re.search(r"\w+\.aggiorna\(\)", main):
        errori.append("src/main.cpp: R7 il pannello di debug (PannelloDebug, L+Select) non e' piu' nel ciclo del gioco")
    return errori


def main():
    errori = controlla()
    for e in errori:
        print(e)
    print(f"[regole-gba] {len(sorgenti())} file, {len(errori)} violazioni")
    return 1 if errori else 0


if __name__ == "__main__":
    sys.exit(main())
