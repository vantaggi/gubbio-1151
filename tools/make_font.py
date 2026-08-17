#!/usr/bin/env python3
"""
Generatore del FONT DI GUBBIO 1151: il font 8x8 di Butano con le lettere accentate italiane.

    python tools/make_font.py

Produce `graphics/font_gubbio.{bmp,json}` e `include/font_gubbio.h`.

IL PROBLEMA CHE RISOLVE. Il font `common_variable_8x8_sprite_font` di Butano mappa 16 caratteri
non ASCII e sono **tutti spagnoli** (Á É Í Ó Ú Ü Ñ á é í ó ú ü ñ ¡ ¿): nessun accento grave
italiano. Un carattere non mappato non e' un errore di compilazione — e' un `BN_ERROR` a runtime,
cioe' il gioco che si ferma davanti al giocatore alla prima battuta che contiene "citta'".

COME SONO OTTENUTI I GLIFI (decisione della Sessione 12, vedi HANDOVER):

* **Minuscole (à è é ì ò ù): derivate, nessun ridisegno.** Misurato sul font di Butano: 'a', 'o'
  e 'u' hanno 3 righe libere sopra, 'e' ne ha 2. L'accento ci sta nello spazio che c'e' gia'.
  Per la 'i' l'accento **sostituisce il puntino**, che e' esattamente cio' che fa la tipografia.
* **Maiuscole (À È É Ì Ò Ù): compresse di una riga.** Le maiuscole occupano tutte e 8 le righe,
  quindi lo spazio va ricavato. Invece di ridisegnarle a mano si toglie **la riga la cui
  rimozione si nota di meno**, cioe' quella che differisce meno dalla successiva: per A, I, O e
  U esiste una riga duplicata e la compressione e' esatta (0 pixel alterati); per la E, che ha
  tutte le righe diverse, il costo misurato e' di 2 pixel. L'accento e' un trattino di 3 px
  sulla riga cosi' liberata.
  La variante piu' aggressiva — comprimere a 6 righe — e' stata **provata e scartata**: accanto
  alle altre maiuscole la lettera appariva visibilmente rimpicciolita.

REGOLA CHE QUESTO GENERATORE NON PUO' DIMENTICARE. La tabella delle larghezze parte dal
carattere 32 (lo spazio), che **ha una larghezza ma non ha una cella** nell'immagine: le celle
partono da 33 ('!'). Sbagliare questo scarto di uno fa scivolare ogni lettera di una posizione, e
"Sant'Ubaldo" viene stampato "Tbou..." — e' successo davvero, nella Sessione 05.
"""

import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
BUTANO_COMMON = os.path.join(ROOT, "..", "butano", "common")

SORGENTE_BMP = os.path.join(BUTANO_COMMON, "graphics", "common_variable_8x8_font.bmp")
SORGENTE_H = os.path.join(BUTANO_COMMON, "include", "common_variable_8x8_sprite_font.h")

CELL = 8
PRIMO_ASCII = 32          # prima larghezza della tabella: lo spazio
PRIMA_CELLA_ASCII = 33    # prima cella dell'immagine: '!'
ASCII_CELLE = 94          # da '!' (33) a '~' (126)

# Le dodici lettere accentate dell'italiano, nell'ordine in cui finiscono nell'immagine.
# `base` e' la lettera da cui il glifo e' derivato; `acuto` distingue é/É da à/è/ì/ò/ù.
ACCENTATE = [
    ("à", "a", False), ("è", "e", False), ("é", "e", True),
    ("ì", "i", False), ("ò", "o", False), ("ù", "u", False),
    ("À", "A", False), ("È", "E", False), ("É", "E", True),
    ("Ì", "I", False), ("Ò", "O", False), ("Ù", "U", False),
]


# ----------------------------------------------------------------------------------------------
# Lettura del font sorgente
# ----------------------------------------------------------------------------------------------

def leggi_bmp4(path):
    d = open(path, "rb").read()
    off = struct.unpack_from("<I", d, 10)[0]
    w, h = struct.unpack_from("<ii", d, 18)
    bpp = struct.unpack_from("<H", d, 28)[0]
    if bpp != 4:
        sys.exit(f"[font] {path}: atteso 4bpp, trovato {bpp}")

    palette = []
    for i in range(16):
        b, g, r, _ = struct.unpack_from("<BBBB", d, 14 + 40 + i * 4)
        palette.append((r, g, b))

    rb = w // 2
    pad = (4 - rb % 4) % 4
    righe = []
    for y in range(h):
        st = off + y * (rb + pad)
        r = []
        for b in d[st:st + rb]:
            r.append(b >> 4)
            r.append(b & 0x0F)
        righe.append(r)
    righe.reverse()                      # il BMP e' bottom-up
    return w, h, righe, palette


def leggi_larghezze(path):
    testo = open(path, encoding="utf-8").read()
    blocco = testo.split("character_widths[] = {")[1].split("};")[0]
    return [int(m) for m in re.findall(r"(\d+),", blocco)]


def scrivi_bmp4(path, width, height, pixels, palette):
    rb = width // 2
    pad = (4 - rb % 4) % 4
    body = bytearray()
    for y in range(height - 1, -1, -1):
        riga = pixels[y]
        for x in range(0, width, 2):
            body.append(((riga[x] & 0xF) << 4) | (riga[x + 1] & 0xF))
        body.extend(b"\x00" * pad)

    off = 14 + 40 + 16 * 4
    header = b"BM" + struct.pack("<IHHI", off + len(body), 0, 0, off)
    dib = struct.pack("<IiiHHIIiiII", 40, width, height, 1, 4, 0, len(body), 2835, 2835, 16, 0)
    pal = b"".join(struct.pack("<BBBB", b, g, r, 0) for (r, g, b) in palette)
    open(path, "wb").write(header + dib + pal + bytes(body))


# ----------------------------------------------------------------------------------------------
# Derivazione dei glifi accentati
# ----------------------------------------------------------------------------------------------

def colore_tratto(cella):
    """L'indice di palette con cui il font disegna: si legge dal glifo, non si indovina."""
    for riga in cella:
        for v in riga:
            if v:
                return v
    return 1


def comprimi_di_una_riga(cella):
    """Toglie la riga la cui rimozione si nota di meno: quella che differisce meno dalla
    successiva. Quando esiste una riga duplicata la distanza e' zero e viene scelta quella —
    che e' il caso di quasi tutte le maiuscole di questo font. Quando non esiste (la 'E' ha
    righe tutte diverse fra loro) si toglie comunque la piu' ridondante, invece di rinunciare."""
    migliore, costo_migliore = 0, None

    for y in range(len(cella) - 1):
        costo = sum(1 for a, b in zip(cella[y], cella[y + 1]) if a != b)

        if costo_migliore is None or costo < costo_migliore:
            migliore, costo_migliore = y, costo

    return [r[:] for r in cella[:migliore] + cella[migliore + 1:]] + [[0] * CELL], costo_migliore


def applica_accento(cella, riga, colore, acuto, sottile):
    if sottile:
        # Trattino di 3 px: per le maiuscole, dove si dispone di una riga sola.
        for x in (1, 2, 3):
            cella[riga][x] = colore
    elif acuto:
        cella[riga][3] = colore
        cella[riga][2] = colore
        cella[riga + 1][2] = colore
        cella[riga + 1][1] = colore
    else:
        cella[riga][1] = colore
        cella[riga][2] = colore
        cella[riga + 1][2] = colore
        cella[riga + 1][3] = colore
    return cella


def prima_riga_occupata(cella):
    for y, r in enumerate(cella):
        if any(r):
            return y
    return len(cella)


def deriva(cella_base, lettera, acuto):
    cella = [r[:] for r in cella_base]
    colore = colore_tratto(cella)

    if lettera.isupper():
        compressa, costo = comprimi_di_una_riga(cella)
        # La lettera scende di una riga: si libera la riga 0 per il trattino.
        cella = [[0] * CELL] + compressa[:CELL - 1]
        deriva.ultimo_costo = costo
        return applica_accento(cella, 0, colore, acuto, sottile=True)

    if lettera == "i":
        # L'accento PRENDE IL POSTO del puntino: e' cosi' che si scrive una i accentata.
        alto = prima_riga_occupata(cella)
        for y in range(alto, min(alto + 2, CELL)):
            if sum(1 for v in cella[y] if v) <= 3:      # il puntino, non l'asta
                cella[y] = [0] * CELL
        return applica_accento(cella, 0, colore, acuto, sottile=False)

    libere = prima_riga_occupata(cella)
    if libere < 2:
        sys.exit(f"[font] '{lettera}': solo {libere} righe libere, l'accento non ci sta")

    # L'accento sta appena sopra la lettera, non incollato al bordo della cella.
    return applica_accento(cella, max(0, libere - 2), colore, acuto, sottile=False)


# ----------------------------------------------------------------------------------------------

def main():
    w, h, righe, palette = leggi_bmp4(SORGENTE_BMP)
    larghezze = leggi_larghezze(SORGENTE_H)
    celle_sorgente = h // CELL

    def cella_ascii(ch):
        k = ord(ch) - PRIMA_CELLA_ASCII
        return [r[:] for r in righe[k * CELL:(k + 1) * CELL]]

    def larghezza(ch):
        return larghezze[ord(ch) - PRIMO_ASCII]

    print(f"[font] sorgente: {celle_sorgente} celle, {len(larghezze)} larghezze")

    # Verifica dello scarto di uno, prima di qualunque altra cosa: se l'indicizzazione fosse
    # sbagliata i glifi uscirebbero traslati e ce ne accorgeremmo solo a schermo.
    if any(cella_ascii("!")[y] != righe[y] for y in range(CELL)):
        sys.exit("[font] la prima cella non e' '!': l'indicizzazione delle celle e' cambiata")

    nuove_righe = [r[:] for r in righe[:ASCII_CELLE * CELL]]
    nuove_larghezze = larghezze[:PRIMA_CELLA_ASCII - PRIMO_ASCII + ASCII_CELLE]

    for accentata, base, acuto in ACCENTATE:
        glifo = deriva(cella_ascii(base), base, acuto)
        nuove_righe.extend(glifo)
        nuove_larghezze.append(larghezza(base))
        nota = ""
        if base.isupper():
            costo = getattr(deriva, "ultimo_costo", None)
            nota = f"  (compressa di 1 riga, {costo} px alterati)"
        print(f"    {accentata}  <- '{base}'  larghezza {larghezza(base)}{nota}")

    altezza = len(nuove_righe)
    scrivi_bmp4(os.path.join(ROOT, "graphics", "font_gubbio.bmp"), CELL, altezza,
                nuove_righe, palette)

    with open(os.path.join(ROOT, "graphics", "font_gubbio.json"), "w", encoding="utf-8") as f:
        f.write('{\n    "type": "sprite",\n    "bpp_mode": "bpp_4",\n    "height": 8\n}\n')

    scrivi_header(nuove_larghezze)

    print(f"[font] scritte {altezza // CELL} celle ({ASCII_CELLE} ASCII + {len(ACCENTATE)} "
          f"accentate) e {len(nuove_larghezze)} larghezze")


def scrivi_header(larghezze):
    elenco = ", ".join(f'"{a}"' for a, _, _ in ACCENTATE)
    righe_larghezze = []
    for i, larg in enumerate(larghezze):
        codice = PRIMO_ASCII + i
        if i < PRIMA_CELLA_ASCII - PRIMO_ASCII + ASCII_CELLE:
            # Il backslash chiuderebbe il commento con una continuazione di riga
            # (-Wcomment): l'etichetta va scritta a parole.
            etichetta = {32: "spazio", 92: "backslash"}.get(codice, chr(codice))
        else:
            etichetta = ACCENTATE[i - (PRIMA_CELLA_ASCII - PRIMO_ASCII + ASCII_CELLE)][0]
        righe_larghezze.append(f"    {larg},  // {etichetta}")

    contenuto = f'''#ifndef FONT_GUBBIO_H
#define FONT_GUBBIO_H

// GENERATO DA tools/make_font.py — non modificare a mano.
//
// Font 8x8 del progetto: i 94 glifi ASCII di `common_variable_8x8_font` di Butano piu' le
// {len(ACCENTATE)} lettere accentate italiane, che quel font non ha (i suoi 16 caratteri non ASCII sono
// tutti spagnoli). Un carattere non mappato non e' un errore di compilazione: e' un `BN_ERROR`
// a runtime, davanti al giocatore.
//
// Le minuscole sono derivate senza ridisegno — lo spazio sopra c'era gia'; le maiuscole sono
// compresse di una riga eliminando una riga duplicata. Vedi il commento in testa al generatore.

#include "bn_sprite_font.h"
#include "bn_utf8_characters_map.h"
#include "bn_sprite_items_font_gubbio.h"

namespace gubbio {{

inline constexpr bn::utf8_character FONT_UTF8_CHARACTERS[] = {{
    {elenco}
}};

// La tabella parte dal carattere 32, LO SPAZIO, che ha una larghezza ma non ha una cella
// nell'immagine (le celle partono da '!'). Sbagliare questo scarto di uno fa scivolare ogni
// lettera di una posizione: e' il difetto della Sessione 05, per cui "Sant'Ubaldo" usciva
// "Tbou...".
inline constexpr int8_t FONT_CHARACTER_WIDTHS[] = {{
{chr(10).join(righe_larghezze)}
}};

inline constexpr bn::span<const bn::utf8_character> FONT_UTF8_SPAN(FONT_UTF8_CHARACTERS);

inline constexpr auto FONT_UTF8_MAP = bn::utf8_characters_map<FONT_UTF8_SPAN>();

inline constexpr bn::sprite_font FONT_GUBBIO(
        bn::sprite_items::font_gubbio, FONT_UTF8_MAP.reference(), FONT_CHARACTER_WIDTHS);

}} // namespace gubbio

#endif // FONT_GUBBIO_H
'''
    open(os.path.join(ROOT, "include", "font_gubbio.h"), "w", encoding="utf-8").write(contenuto)


if __name__ == "__main__":
    main()
