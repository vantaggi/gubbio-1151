#!/usr/bin/env python3
"""Gate delle divisioni software nel ciclo dell'esplorazione (docs/regole_sviluppo_gba.md, punto 3).

L'ARM7TDMI non divide: ogni / o % che il compilatore non sa fare con uno spostamento diventa una chiamata a
__aeabi_idiv o __aeabi_uidivmod (decine di cicli). In Thumb succede anche per i divisori costanti come 30.
Questo gate disassembla l'ELF e conta, nelle funzioni che girano a ogni frame dell'esplorazione, le chiamate
alla divisione software. Ogni funzione ha il suo budget, scritto qui sotto con il perche': di solito zero;
uno quando un ritmo si riduce una volta per frame (frame % GIRO) fuori dal giro sulle figure.

    python3 tools/controlla_divisioni.py [gubbio1151.elf]      # lo chiama build.sh dopo il gate zero-heap
    python3 tools/controlla_divisioni.py --tutte                # tutte le funzioni del gioco che dividono

Per togliere una divisione: include/aritmetica.h (dividi, resto, giro, avanti).
"""
import argparse
import os
import re
import shutil
import subprocess
import sys

DIVISIONI = re.compile(r"\sbl\w*\s+[0-9a-f]+ <_*aeabi_u?idiv(?:mod)?(?:_from_thumb)?>")
FUNZIONE = re.compile(r"^[0-9a-f]+ <(.+)>:$")

# Le funzioni di ogni frame dell'esplorazione (main.cpp, il while(true)) e il loro budget. Il nome e' quello
# demangled, fino alla parentesi.
BUDGET = {
    "main": (0, "il ciclo del gioco"),
    "gubbio::Esplorazione::muovi": (0, "il passo del giocatore"),
    "gubbio::Esplorazione::aggiorna": (0, "camera, riflessi, fumetto, dissolvenza"),
    "gubbio::Esplorazione::_anima_giocatore": (0, "camminata e respiro"),
    "gubbio::Esplorazione::_anima_compagni": (0, "la fila sulle orme"),
    "gubbio::Esplorazione::_segna_orme": (0, "le orme"),
    "gubbio::Esplorazione::_anima_promemoria": (0, "il promemoria di Select"),
    "gubbio::Folla::aggiorna": (1, "frame % GIRO una volta per frame, fuori dal giro dei viandanti"),
    "gubbio::Storia::_anima_npc": (1, "frames % 60 una volta per frame, fuori dal giro degli NPC"),
    "gubbio::Storia::aggiorna": (2, "le due / 100 di ferite_massime, solo correndo nei miasmi della gola (la "
                                    "stessa aritmetica del mirror della battaglia, che non si tocca)"),
    "gubbio::ScontriSullaMappa::aggiorna": (0, "i nemici sulla mappa"),
    "gubbio::VistaNumero::_scrivi": (0, "il disegno dei numeri"),
}


def objdump():
    for c in ("arm-none-eabi-objdump", os.path.join(os.environ.get("DEVKITARM", ""), "bin", "arm-none-eabi-objdump")):
        if shutil.which(c) or os.path.isfile(c):
            return c
    return None


def conta(testo):
    """{funzione demangled: chiamate alla divisione software} dal disassemblato."""
    esito = {}
    corrente = None
    for riga in testo.splitlines():
        m = FUNZIONE.match(riga)
        if m:
            corrente = m.group(1)
            continue
        if corrente and DIVISIONI.search(riga):
            esito[corrente] = esito.get(corrente, 0) + 1
    return esito


def nome_corto(f):
    return f.split("(")[0].replace(" [clone", "").strip()


def fuori_budget(conti):
    """Le righe di errore: funzioni di BUDGET con piu' divisioni del permesso."""
    errori = []
    per_nome = {}
    for f, n in conti.items():
        per_nome[nome_corto(f)] = per_nome.get(nome_corto(f), 0) + n
    for nome, (massimo, perche) in BUDGET.items():
        n = per_nome.get(nome, 0)
        if n > massimo:
            errori.append(f"{nome}: {n} divisioni software, budget {massimo} ({perche})")
    return errori


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("elf", nargs="?", default="gubbio1151.elf")
    ap.add_argument("--tutte", action="store_true")
    a = ap.parse_args()
    od = objdump()
    if od is None:
        print("[divisioni] arm-none-eabi-objdump non trovato (DEVKITARM)", file=sys.stderr)
        return 1
    if not os.path.isfile(a.elf):
        print(f"[divisioni] ELF non trovato: {a.elf}", file=sys.stderr)
        return 1
    testo = subprocess.run([od, "-d", "-C", "--no-show-raw-insn", a.elf], capture_output=True, text=True,
                           check=True).stdout
    conti = conta(testo)
    if a.tutte:
        for f, n in sorted(conti.items(), key=lambda x: -x[1]):
            if "gubbio" in f or f.startswith("main"):
                print(f"{n:3}  {f[:150]}")
    errori = fuori_budget(conti)
    for e in errori:
        print("[divisioni] ERRORE " + e)
    if not errori:
        print(f"[divisioni] OK: nessuna divisione software oltre il budget nelle {len(BUDGET)} funzioni di ogni frame")
    return 1 if errori else 0


if __name__ == "__main__":
    sys.exit(main())
