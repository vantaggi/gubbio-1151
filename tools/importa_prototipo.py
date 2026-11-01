#!/usr/bin/env python3
"""Importazione una tantum delle 14 aree del prototipo come DATI (fase F2).

Nel prototipo le griglie erano funzioni constexpr (get_tile_type), con le regole scritte in C++.
Qui non si riscrivono a mano: si leggono i byte che quelle funzioni producevano, dall'ELF del
prototipo compilato al tag prototipo-v0, insieme alla tabella MAPS (dimensioni, spawn, uscite).
Le quote in metri vengono dai sorgenti del tag (constexpr int <AREA>_QUOTA_M).

    python tools/importa_prototipo.py <elf del prototipo> <clone del repo con il tag prototipo-v0>

Scrive mondo/aree/*.area. Non serve rilanciarlo: i file .area sono ormai la fonte, e si
modificano a mano. Lo script resta per dire da dove vengono.
"""
import os
import re
import struct
import subprocess
import sys

RADICE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
USCITA = os.path.join(RADICE, "mondo", "aree")

# MapId del prototipo (include/map_id.h): indice -> (id, header della griglia, simbolo nell'ELF).
AREE = [
    (0, "piazza_grande", "piazza_grande_collision.h", "PIAZZA_GRID"),
    (1, "bottaccione", "bottaccione_collision.h", "BOTTACCIONE_GRID"),
    (4, "monte_ingino", "monte_ingino_collision.h", "MONTE_INGINO_GRID"),
    (5, "largo_bargello", "largo_bargello_collision.h", "BARGELLO_GRID"),
    (6, "via_dei_consoli", "via_dei_consoli_collision.h", "VIA_DEI_CONSOLI_GRID"),
    (7, "via_xx_settembre", "via_xx_settembre_collision.h", "VIA_XX_SETTEMBRE_GRID"),
    (8, "sant_agostino", "sant_agostino_collision.h", "SANT_AGOSTINO_GRID"),
    (9, "sant_andrea", "sant_andrea_collision.h", "SANT_ANDREA_GRID"),
    (10, "san_martino", "san_martino_collision.h", "SAN_MARTINO_GRID"),
    (11, "piazza_quaranta_martiri", "piazza_quaranta_martiri_collision.h", "PIAZZA_QUARANTA_MARTIRI_GRID"),
    (12, "san_pietro", "san_pietro_collision.h", "SAN_PIETRO_GRID"),
    (13, "duomo_ducale", "duomo_ducale_collision.h", "DUOMO_DUCALE_GRID"),
    (14, "basilica", "basilica_collision.h", "BASILICA_GRID"),
    (15, "teatro_romano", "teatro_romano_collision.h", "TEATRO_ROMANO_GRID"),
]
ID_DI = {i: nome for i, nome, _, _ in AREE}

# Valori della griglia del prototipo (maps::TileType) -> carattere del file .area.
CARATTERI = {
    0: ".",   # GROUND
    1: "#",   # WALL
    2: "=",   # RAILING: parapetto sul vuoto, un affaccio
    3: "D",   # DOOR_CONSOLI: primo varco (nel prototipo anche il portone)
    4: "A",   # EXIT_SAN_MARTINO: varco A
    5: "B",   # EXIT_PORTA_ROMANA: varco B
    6: "F",   # FOUNTAIN
    7: "C",   # CONSOLI_FACADE: facciata monumentale
    8: "P",   # PRETORIO_FACADE: seconda facciata monumentale
    9: "S",   # STAIRS
    10: "d",  # DOOR_PRETORIO: portone solo visivo
    11: ",",  # ROAD
    12: "E",  # EXIT_TERZA: varco E
    13: "G",  # EXIT_QUARTA: varco G
}

# Dove l'header del prototipo non dichiarava la quota, vale la tabella di docs/mappa_del_mondo.md
# (sezione 2). Le strade in salita hanno due quote: dove si entra dal basso e dove si arriva.
QUOTE_DAL_DOCUMENTO = {
    "piazza_grande": "70",
    "largo_bargello": "45",
    "monte_ingino": "100 350",
    "bottaccione": "300 30",
}

DIMENSIONE_MAPDESCRIPTOR = 84
N_SPAWN = 6
N_TRIGGER = 6


class Elf:
    def __init__(self, percorso):
        self.dati = open(percorso, "rb").read()
        d = self.dati
        assert d[:4] == b"\x7fELF" and d[4] == 1 and d[5] == 1, "attesto un ELF32 little endian"
        shoff, = struct.unpack_from("<I", d, 0x20)
        shentsize, shnum = struct.unpack_from("<HH", d, 0x2E)
        self.sezioni = []
        for i in range(shnum):
            _, tipo, _, addr, offset, size = struct.unpack_from("<IIIIII", d, shoff + i * shentsize)
            if addr and tipo != 8:   # SHT_NOBITS non ha byte nel file
                self.sezioni.append((addr, offset, size))

    def leggi(self, indirizzo, n):
        for addr, offset, size in self.sezioni:
            if addr <= indirizzo and indirizzo + n <= addr + size:
                inizio = offset + indirizzo - addr
                return self.dati[inizio:inizio + n]
        raise ValueError(f"indirizzo 0x{indirizzo:08X} non in una sezione con dati")


def simboli(elf_percorso):
    nm = os.path.join(os.environ.get("DEVKITARM", "C:/Users/cioti/devkitPro/opt/devkitpro/devkitARM"),
                      "bin", "arm-none-eabi-nm")
    uscita = subprocess.run([nm, "-S", "-C", elf_percorso], capture_output=True, text=True, check=True).stdout
    out = {}
    for riga in uscita.splitlines():
        parti = riga.split(None, 3)
        if len(parti) == 4:
            out[parti[3]] = (int(parti[0], 16), int(parti[1], 16))
    return out


def quota(repo, header):
    testo = subprocess.run(["git", "-C", repo, "show", f"prototipo-v0:include/{header}"],
                           capture_output=True, text=True, encoding="utf-8", check=True).stdout
    m = re.search(r"constexpr\s+int\s+\w*QUOTA_M\s*=\s*(-?\d+)", testo)
    return int(m.group(1)) if m else None


def main():
    elf_percorso, repo = sys.argv[1], sys.argv[2]
    elf = Elf(elf_percorso)
    sim = simboli(elf_percorso)
    maps_addr, maps_size = sim["gubbio::MAPS"]
    assert maps_size == 16 * DIMENSIONE_MAPDESCRIPTOR, maps_size
    os.makedirs(USCITA, exist_ok=True)

    for indice, nome, header, simbolo in AREE:
        d = elf.leggi(maps_addr + indice * DIMENSIONE_MAPDESCRIPTOR, DIMENSIONE_MAPDESCRIPTOR)
        collisione, larghezza, altezza = struct.unpack_from("<Ihh", d, 0)
        grid_addr, grid_size = sim[f"gubbio::maps::{simbolo}"]
        assert collisione == grid_addr and grid_size == larghezza * altezza, nome
        griglia = elf.leggi(grid_addr, grid_size)

        spawn = [struct.unpack_from("<hh", d, 22 + 4 * i) for i in range(N_SPAWN)]
        trigger = []
        for i in range(N_TRIGGER):
            tile, scena, parametro, ingresso = struct.unpack_from("<BBhB", d, 46 + 6 * i)
            if scena:
                trigger.append((tile, scena, parametro, ingresso))

        righe = [f"# Area importata dal prototipo (tag prototipo-v0): {simbolo}, MapId {indice}.",
                 f"id {nome}",
                 f"quota {QUOTE_DAL_DOCUMENTO.get(nome) or quota(repo, header)}",
                 f"dimensioni {larghezza} {altezza}"]
        for i, (x, y) in enumerate(spawn):
            righe.append(f"spawn {i} {(x - 4) // 8} {(y - 4) // 8}")
        for tile, scena, parametro, ingresso in trigger:
            destinazione = ID_DI.get(parametro, f"mapid_{parametro}") if scena == 1 else f"scena_{scena}_{parametro}"
            righe.append(f"uscita {CARATTERI[tile]} {destinazione} {ingresso}")
        righe.append("griglia")
        for y in range(altezza):
            righe.append("".join(CARATTERI[griglia[x + y * larghezza]] for x in range(larghezza)))
        with open(os.path.join(USCITA, nome + ".area"), "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(righe) + "\n")
        print(f"{nome}: {larghezza}x{altezza}, {len(trigger)} uscite")


if __name__ == "__main__":
    main()
