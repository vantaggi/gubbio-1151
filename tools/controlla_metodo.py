#!/usr/bin/env python3
"""Controlla che il metodo di lavoro (docs/metodo/) resti in ordine.

    python3 tools/controlla_metodo.py        # esce con 1 e stampa gli errori se qualcosa non torna

Regole (docs/metodo/README.md, «La regola di aggiornamento»):
- DECISIONI.md: ogni riga del registro ha un ID unico Dnnn, una data AAAA-MM-GG, un Tipo (G, S, G+S) e uno
  Stato fra «valida», «da rivedere», «in corso», «superata da Dnnn» (con Dnnn che esiste).
- Una decisione superata vuol dire che qualcosa e' stato rifatto: deve citarla almeno una lezione.
- LEZIONI.md: ogni lezione «## Lnn · titolo» ha tutti i campi del modello, cita almeno una decisione che
  esiste ed e' citata in PERCORSO_DA_ZERO.md (cosi' la lezione cambia davvero il percorso).
- PERCORSO_DA_ZERO.md: cita solo lezioni e decisioni che esistono.
"""
import os
import re
import sys

RADICE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
METODO = os.path.join(RADICE, "docs", "metodo")

RIGA_DECISIONE = re.compile(r"^\|\s*(D\d{3})\s*\|(.*)\|\s*$")
TITOLO_LEZIONE = re.compile(r"^## (L\d{2}) · (.+)$", re.M)
STATI = re.compile(r"^(valida|da rivedere|in corso|superata da (D\d{3}))$")
TIPI = {"G", "S", "G+S"}
CAMPI_LEZIONE = ("**Cosa è successo.**", "**Quanto è costato.**", "**Perché.**",
                 "**Cosa si doveva decidere prima.**", "**Regola nuova.**", "**Dove vive ora.**")
CITA_D = re.compile(r"\bD\d{3}\b")
CITA_L = re.compile(r"\bL\d{2}\b")


def leggi_decisioni(testo):
    """-> (dizionario id -> campi, errori). Campi: data, ambito, decisione, chi, tipo, stato."""
    decisioni, errori = {}, []
    for n, riga in enumerate(testo.splitlines(), 1):
        m = RIGA_DECISIONE.match(riga)
        if not m:
            continue
        ident, resto = m.group(1), [c.strip() for c in m.group(2).split("|")]
        if len(resto) != 6:
            errori.append(f"DECISIONI riga {n}: {ident} ha {len(resto) + 1} colonne invece di 7")
            continue
        data, ambito, decisione, chi, tipo, stato = resto
        if ident in decisioni:
            errori.append(f"DECISIONI riga {n}: {ident} ripetuta")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", data):
            errori.append(f"DECISIONI riga {n}: {ident} data «{data}» non nel formato AAAA-MM-GG")
        if tipo not in TIPI:
            errori.append(f"DECISIONI riga {n}: {ident} tipo «{tipo}» (ammessi G, S, G+S)")
        if not STATI.match(stato):
            errori.append(f"DECISIONI riga {n}: {ident} stato «{stato}» non ammesso")
        if not decisione or not chi or not ambito:
            errori.append(f"DECISIONI riga {n}: {ident} ha una colonna vuota")
        decisioni[ident] = dict(data=data, ambito=ambito, decisione=decisione, chi=chi, tipo=tipo, stato=stato)
    for ident, d in decisioni.items():
        m = STATI.match(d["stato"])
        if m and m.group(2):
            if m.group(2) not in decisioni:
                errori.append(f"DECISIONI: {ident} superata da {m.group(2)}, che non esiste")
            elif m.group(2) == ident:
                errori.append(f"DECISIONI: {ident} superata da se stessa")
    return decisioni, errori


def leggi_lezioni(testo):
    """-> (dizionario id -> testo della lezione, errori)."""
    lezioni, errori = {}, []
    titoli = list(TITOLO_LEZIONE.finditer(testo))
    for i, m in enumerate(titoli):
        fine = titoli[i + 1].start() if i + 1 < len(titoli) else len(testo)
        corpo = testo[m.end():fine]
        ident = m.group(1)
        if ident in lezioni:
            errori.append(f"LEZIONI: {ident} ripetuta")
        for campo in CAMPI_LEZIONE:
            if campo not in corpo:
                errori.append(f"LEZIONI: {ident} senza il campo {campo}")
        lezioni[ident] = corpo
    return lezioni, errori


def controlla(dec_testo, lez_testo, per_testo):
    decisioni, errori = leggi_decisioni(dec_testo)
    lezioni, e = leggi_lezioni(lez_testo)
    errori += e
    if not decisioni:
        errori.append("DECISIONI: registro vuoto")
    if not lezioni:
        errori.append("LEZIONI: nessuna lezione")
    citate_dalle_lezioni = set()
    for ident, corpo in lezioni.items():
        citate = set(CITA_D.findall(corpo))
        citate_dalle_lezioni |= citate
        if not citate:
            errori.append(f"LEZIONI: {ident} non cita nessuna decisione")
        for d in sorted(citate - set(decisioni)):
            errori.append(f"LEZIONI: {ident} cita {d}, che non esiste")
    for ident, d in decisioni.items():
        if d["stato"].startswith("superata") and ident not in citate_dalle_lezioni:
            errori.append(f"DECISIONI: {ident} e' superata (rifacimento) ma nessuna lezione la cita")
    citate_nel_percorso = set(CITA_L.findall(per_testo))
    for ident in sorted(lezioni):
        if ident not in citate_nel_percorso:
            errori.append(f"PERCORSO: la lezione {ident} non e' citata in nessuna fase")
    for ident in sorted(citate_nel_percorso - set(lezioni)):
        errori.append(f"PERCORSO: cita {ident}, che non esiste")
    for d in sorted(set(CITA_D.findall(per_testo)) - set(decisioni)):
        errori.append(f"PERCORSO: cita {d}, che non esiste")
    return errori


def controlla_il_repo():
    def leggi(nome):
        with open(os.path.join(METODO, nome), encoding="utf-8") as f:
            return f.read()
    return controlla(leggi("DECISIONI.md"), leggi("LEZIONI.md"), leggi("PERCORSO_DA_ZERO.md"))


if __name__ == "__main__":
    errori = controlla_il_repo()
    for e in errori:
        print(e)
    print("metodo:", "0 errori" if not errori else f"{len(errori)} errori")
    sys.exit(1 if errori else 0)
