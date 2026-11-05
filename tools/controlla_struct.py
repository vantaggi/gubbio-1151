#!/usr/bin/env python3
"""Ordine dei campi delle struct (regole GBA, docs/regole_sviluppo_gba.md, punto 7).

Il compilatore mette byte di riempimento (padding) fra un campo piccolo e uno grande. Ordinando i campi
dal piu' grande al piu' piccolo il riempimento sparisce o si riduce. Questo strumento chiede a clang
(-m32: int e puntatori da 4 byte come sull'ARM7TDMI) la disposizione vera di ogni struct e classe di
gubbio:: dichiarata in include/, calcola la dimensione che avrebbe coi campi in ordine di allineamento
e dice quanti byte si sprecano.

    python3 tools/controlla_struct.py            # elenco delle struct che sprecano byte
    python3 tools/controlla_struct.py --tutte    # anche quelle gia' a posto

Serve Butano in butano/ (il submodule) o in ../butano (BUTANO=...). Non tocca la ROM: e' la stessa
analisi che farebbe gcc per ARM, perche' clang -m32 usa le stesse dimensioni e gli stessi allineamenti
per i tipi del progetto (interi fissi, enum con tipo dichiarato, puntatori da 4 byte).
"""
import argparse
import glob
import os
import re
import subprocess
import sys
import tempfile

RADICE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# Struct che restano come sono, con il perche'. Una voce qui va spiegata: la regola vale per tutte le altre.
# Le tabelle in ROM: il riempimento costa ROM (32 MB, ne usiamo una piccola parte), non RAM, e i loro
# inizializzatori sono posizionali e scritti dai generatori di tools/. Il test controlla che restino solo
# in tabelle constexpr: una copia in RAM (un campo, una variabile, un vettore) fa cadere l'eccezione.
SOLO_ROM = "solo in tabelle constexpr in ROM"
ECCEZIONI = {
    "gubbio::battaglia::Attesa": SOLO_ROM + " (le 1000 attese del mirror, include/battaglia_attese.h)",
    "gubbio::battaglia::Oggetto": SOLO_ROM + " (OGGETTI)",
    "gubbio::battaglia::Regola": SOLO_ROM + " (REGOLE)",
    "gubbio::mondo::Area": SOLO_ROM + " (AREE, tools/genera_mondo.py)",
    "gubbio::mondo::Variante": SOLO_ROM + " (VARIANTE, tools/genera_mondo.py)",
    "gubbio::progressione::ScontroSullaMappa": SOLO_ROM + " (SCONTRI_SULLA_MAPPA)",
    "gubbio::regia::Inquadratura": SOLO_ROM + " (INQUADRATURA, tools/genera_regia.py)",
    "gubbio::regia::Piano": SOLO_ROM + " (PIANO, tools/genera_regia.py)",
    "gubbio::storia::BattagliaAMeta": SOLO_ROM + " (BATTAGLIA_A_META, tools/genera_storia.py)",
    "gubbio::storia::Npc": SOLO_ROM + " (NPC_AMBIENTE, tools/genera_storia.py)",
    "gubbio::storia::Scena": SOLO_ROM + " (SCENA, tools/genera_storia.py)",
}

PRIMITIVI = {
    "_Bool": (1, 1), "bool": (1, 1), "char": (1, 1), "int8_t": (1, 1), "uint8_t": (1, 1),
    "signed char": (1, 1), "unsigned char": (1, 1),
    "int16_t": (2, 2), "uint16_t": (2, 2), "short": (2, 2), "unsigned short": (2, 2),
    "int": (4, 4), "unsigned int": (4, 4), "int32_t": (4, 4), "uint32_t": (4, 4), "char32_t": (4, 4),
    "long": (4, 4), "unsigned long": (4, 4),
    # come su ARM (AAPCS): 8 byte allineati a 8; clang -m32 su x86 li allinea a 4 dentro le struct
    "int64_t": (8, 8), "uint64_t": (8, 8), "long long": (8, 8),
}


def butano():
    for c in (os.environ.get("BUTANO"), os.path.join(RADICE, "butano"), os.path.join(RADICE, "..", "butano")):
        if c and os.path.isdir(os.path.join(c, "butano", "include")):
            return os.path.join(c, "butano")
    return None


def tipi_enum():
    """Il tipo dichiarato di ogni enum di include/ (enum class X : uint8_t). Senza tipo: int."""
    enum = {}
    for p in glob.glob(os.path.join(RADICE, "include", "**", "*.h"), recursive=True):
        with open(p, encoding="utf-8") as f:
            for m in re.finditer(r"\benum\s+(?:class\s+|struct\s+)?(\w+)\s*(?::\s*([\w:]+))?\s*\{", f.read()):
                base = (m.group(2) or "int").split("::")[-1]
                enum[m.group(1)] = PRIMITIVI.get(base, (4, 4))
    return enum


def disposizioni(header=None):
    """Il dump delle disposizioni di clang per tutti gli header di include/ (o per il testo dato)."""
    b = butano()
    if b is None:
        raise RuntimeError("Butano non trovato: git submodule update --init (o BUTANO=...)")
    gxx = sorted(glob.glob("/usr/include/c++/*"), key=lambda s: [int(x) for x in re.findall(r"\d+", s)])[-1]
    v = os.path.basename(gxx)
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "gnu"))
        open(os.path.join(tmp, "gnu", "stubs-32.h"), "w").close()
        sorgente = os.path.join(tmp, "tutti.cpp")
        with open(sorgente, "w", encoding="utf-8") as f:
            if header is None:
                for h in sorted(glob.glob(os.path.join(RADICE, "include", "*.h"))):
                    f.write(f'#include "{os.path.basename(h)}"\n')
            else:
                f.write(header)
        r = subprocess.run(
            ["clang++", "-m32", "-std=c++20", "-fsyntax-only", "-fconstexpr-steps=2000000000", "-nostdinc++",
             "-isystem", gxx, "-isystem", f"/usr/include/x86_64-linux-gnu/c++/{v}", "-isystem", tmp,
             "-isystem", "/usr/include/x86_64-linux-gnu", "-I", os.path.join(RADICE, "include"),
             "-I", os.path.join(b, "include"), "-I", os.path.join(b, "hw", "include"),
             "-DBN_CFG_ASSERT_ENABLED=0", "-Wno-everything", "-Xclang", "-fdump-record-layouts", sorgente],
            capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError("clang non compila gli header:\n" + r.stderr[-2000:])
        return r.stdout


def leggi(dump):
    """{nome: {"size", "align", "campi": [(tipo, nome, offset)]}} per ogni record del dump."""
    record = {}
    for blocco in dump.split("*** Dumping AST Record Layout")[1:]:
        righe = [r for r in blocco.splitlines() if "|" in r]
        if not righe:
            continue
        m = re.match(r"\s*0 \| (?:struct|class|union) (\S+)", righe[0])
        if not m:
            continue
        nome = m.group(1)
        unione = " union " in righe[0]
        campi = []
        size = align = None
        for r in righe[1:]:
            mm = re.match(r"\s*(\d+)(?::\d+-\d+)? \|   (\S.*?) (\w+)$", r)
            if mm:
                campi.append((mm.group(2), mm.group(3), int(mm.group(1)), ":" in r.split("|")[0]))
                continue
            ms = re.search(r"\[sizeof=(\d+),.*align=(\d+)", r)
            if ms:
                size, align = int(ms.group(1)), int(ms.group(2))
        if size is not None and nome not in record:
            record[nome] = {"size": size, "align": align, "campi": campi, "unione": unione}
    return record


def misura(tipo, record, enum, dentro=""):
    """(dimensione, allineamento) di un tipo di campo dentro il record `dentro`; None se non si sa.
    Un nome corto si cerca prima fra i record dello stesso spazio dei nomi (Evento e' sia una struct della
    battaglia sia un enum dell'audio), poi fra gli enum."""
    tipo = tipo.replace("const ", "").replace("volatile ", "").strip()
    dims = [int(x) for x in re.findall(r"\[(\d+)\]", tipo)]
    base = re.sub(r"\[\d+\]", "", tipo).strip()
    n = 1
    for d in dims:
        n *= d
    if base.endswith("*") or base.endswith("&"):
        s = (4, 4)
    elif base in PRIMITIVI:
        s = PRIMITIVI[base]
    else:
        nudo = re.sub(r"^(struct|class|union|enum) ", "", base)
        corto = nudo.split("::")[-1]
        spazio = dentro.rsplit("::", 1)[0]
        vicini = []
        while spazio and not vicini:
            vicini = [k for k in (spazio + "::" + nudo,) if k in record]
            spazio = spazio.rsplit("::", 1)[0] if "::" in spazio else ""
        if nudo in record:
            s = (record[nudo]["size"], record[nudo]["align"])
        elif vicini:
            s = (record[vicini[0]]["size"], record[vicini[0]]["align"])
        elif corto in enum and not nudo.startswith("bn::"):
            s = enum[corto]
        else:
            return None
    return s[0] * n, s[1]


def migliore(campi):
    """Dimensione coi campi in ordine di allineamento decrescente (a parita', i piu' grandi prima)."""
    off = 0
    allin = 1
    for size, al in sorted(campi, key=lambda c: (-c[1], -c[0])):
        off = (off + al - 1) // al * al + size
        allin = max(allin, al)
    return (off + allin - 1) // allin * allin


def analizza(dump=None):
    """Elenco di (nome, size, migliore, campi) per i record di gubbio:: che hanno dei campi."""
    record = leggi(dump if dump is not None else disposizioni())
    enum = tipi_enum()
    esito = []
    for nome, r in sorted(record.items()):
        if not nome.startswith("gubbio::") or "<" in nome or r["unione"] or not r["campi"]:
            continue
        if any(bit for *_, bit in r["campi"]):
            continue       # campi a bit: l'ordine lo decide chi li impacchetta
        misure = [misura(t, record, enum, nome) for t, *_ in r["campi"]]
        if None in misure:
            continue
        # le basi (classi derivate) non sono nel dump come campi: si confronta solo se i campi coprono tutto
        if r["campi"][0][2] != 0:
            continue
        esito.append((nome, r["size"], max(migliore(misure), r["align"] if misure else 1), r["campi"]))
    return esito


def copie_in_ram(nome):
    """Le righe di src/ e include/ che mettono una struct di ECCEZIONI fuori da una tabella constexpr:
    un campo o una variabile del tipo (non un riferimento ne' un puntatore). Gli autotest sono a tempo di
    compilazione (constexpr) e non contano."""
    corto = nome.split("::")[-1]
    trovate = []
    decl = re.compile(r"^\s*(?:static\s+)?(?:const\s+)?(?:\w+::)*" + corto + r"\s+_?\w+\s*(\[[^]]*\])*\s*(;|=|\{)")
    vettore = re.compile(r"bn::(?:vector|array|deque|list|optional)<\s*(?:\w+::)*" + corto + r"\b")
    for p in sorted(glob.glob(os.path.join(RADICE, "src", "*.cpp")) + glob.glob(os.path.join(RADICE, "include", "*.h"))):
        if os.path.basename(p).startswith("autotest_"):
            continue
        with open(p, encoding="utf-8") as f:
            for i, riga in enumerate(f, 1):
                codice = riga.split("//")[0]
                if "constexpr" in codice:
                    continue
                if decl.search(codice) or vettore.search(codice):
                    trovate.append(f"{os.path.relpath(p, RADICE)}:{i}: {riga.strip()}")
    return trovate


def sprechi(dump=None):
    return [(n, s, m) for n, s, m, _ in analizza(dump) if s > m and n not in ECCEZIONI]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tutte", action="store_true")
    a = ap.parse_args()
    tutte = analizza()
    peggio = [(n, s, m) for n, s, m, _ in tutte if s > m]
    for n, s, m, _ in tutte:
        if a.tutte or s > m:
            nota = "  (eccezione: " + ECCEZIONI[n] + ")" if n in ECCEZIONI else ""
            print(f"{n}: {s} byte, ordinata {m}{'' if s == m else f' (spreca {s - m})'}{nota}")
    fuori = [p for p in peggio if p[0] not in ECCEZIONI]
    print(f"[struct] {len(tutte)} struct controllate, {len(fuori)} da riordinare")
    return 1 if fuori else 0


if __name__ == "__main__":
    sys.exit(main())
