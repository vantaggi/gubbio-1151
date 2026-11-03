#!/usr/bin/env python3
"""Generatore di include/testi.h: una sola tabella di tutti i testi a schermo.

Legge testi/*.testi (righe "ID | CONTESTO | testo") e il font di stile/dati/font.json, e decide
qui, una volta per tutte, tutto quello che riguarda il taglio del testo:

  - rifiuta un file che non e' UTF-8 valido (un byte spezzato) e ogni carattere che non ha un
    glifo nel font, dicendo file, riga e carattere;
  - va a capo in pixel con stile.a_capo, la stessa funzione dei test della Guida di stile, e
    rifiuta un testo che non sta nelle righe del suo contesto;
  - per ogni glifo scrive il suo indice nel font, il byte UTF-8 da cui comincia (un confine di
    carattere: la macchina da scrivere avanza di un glifo per passo) e la sua x nella riga;
  - per ogni riga scrive i punti di taglio sugli sprite da 32 px: il primo glifo che tocca
    ciascuno sprite, cioe' da quale passo della macchina da scrivere lo sprite si accende.

Il C++ non taglia e non decodifica mai da solo: legge queste tabelle. L'autotest esaustivo in
include/testo_autotest.h le ricontrolla tutte a tempo di compilazione.

    python tools/genera_testi.py              # rigenera include/testi.h
    python tools/genera_testi.py --controlla  # esce con 1 se include/testi.h non e' aggiornato
"""
import glob
import os
import re
import sys

RADICE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(RADICE, "stile"))

import stile as S  # noqa: E402

USCITA = os.path.join(RADICE, "include", "testi.h")
SORGENTI = os.path.join(RADICE, "testi", "*.testi")

LARGHEZZA_SPRITE = 32
SPRITE_PER_RIGA = 7

# Contesto: (larghezza massima in pixel, righe massime). Il dialogo e' il riquadro della scelta 9
# (30 tile con un tile di margine per lato, 3 righe); l'etichetta d'area e l'HUD stanno in una riga.
CONTESTI = {
    "DIALOGO": (224, 3),
    "AREA": (192, 1),
    "HUD": (96, 1),
    # la voce del narratore nelle bande nere delle cutscene (24 px): al massimo 2 righe da 224 px
    "NARRATORE": (224, 2),
    # una voce di un menu di scelta nella vista di gioco (copione: 100 px)
    "SCELTA": (100, 1),
}

assert all(l <= LARGHEZZA_SPRITE * SPRITE_PER_RIGA for l, _ in CONTESTI.values())


class ErroreTesti(Exception):
    pass


# Una vocale seguita dall'apostrofo a fine parola ("giu'", "perche'", "citta'") e' l'accento scritto
# alla vecchia maniera delle tastiere: nel gioco si usano le lettere accentate vere. L'apostrofo
# dell'elisione ("Sant'Ubaldo", "dell'armatura") e' seguito da una lettera e resta; "po'" e' giusto.
APOSTROFO_PER_ACCENTO = re.compile(r"\w*[aeiouAEIOU]'(?![^\W\d_])")
# Gli imperativi tronchi ("Va'", "Di'", "Fa'", "Sta'", "Da'") si scrivono con l'apostrofo.
ELISIONI_GIUSTE = {"po'", "va'", "di'", "fa'", "sta'", "da'"}


def leggi_voci(nome, dati):
    """Voci (id, contesto, testo, riga) di un file sorgente, dati in byte."""
    try:
        testo = dati.decode("utf-8")
    except UnicodeDecodeError as e:
        riga = dati[:e.start].count(b"\n") + 1
        raise ErroreTesti(f"{nome}:{riga}: byte UTF-8 non valido 0x{dati[e.start]:02X} "
                          f"alla posizione {e.start} ({e.reason})") from None
    voci = []
    for n, riga in enumerate(testo.splitlines(), 1):
        if not riga.strip() or riga.lstrip().startswith("#"):
            continue
        parti = [p.strip() for p in riga.split("|", 2)]
        if len(parti) != 3 or not parti[2]:
            raise ErroreTesti(f"{nome}:{n}: attesa una riga 'ID | CONTESTO | testo'")
        ident, contesto, frase = parti
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", ident):
            raise ErroreTesti(f"{nome}:{n}: ID '{ident}' non valido (maiuscole, cifre, _)")
        if contesto not in CONTESTI:
            raise ErroreTesti(f"{nome}:{n}: contesto '{contesto}' sconosciuto ({', '.join(CONTESTI)})")
        apostrofo = APOSTROFO_PER_ACCENTO.search(frase)
        if apostrofo and apostrofo.group(0).lower() not in ELISIONI_GIUSTE:
            raise ErroreTesti(f"{nome}:{n}: {ident}: '{apostrofo.group(0)}' ha l'apostrofo al posto "
                              f"dell'accento: si scrive con la lettera accentata (giù, perché, città)")
        voci.append((ident, contesto, frase, f"{nome}:{n}"))
    return voci


def indici_font(font):
    """Indice di ogni glifo nella tabella FONT di include/stile/font.h (ordine di codice)."""
    return {c: i for i, c in enumerate(sorted(font["glifi"], key=ord))}


def componi(voci, font):
    """Dalle voci alle tabelle. Ritorna un dizionario pronto per scrivi_header."""
    indici = indici_font(font)
    visti = {}
    testi, glifi, byte_glifo, x_glifo, righe, tagli = [], [], [], [], [], []

    for ident, contesto, frase, dove in voci:
        if ident in visti:
            raise ErroreTesti(f"{dove}: ID {ident} gia' usato in {visti[ident]}")
        visti[ident] = dove

        frase = S.normalizza(font, frase)
        mancanti = S.caratteri_mancanti(font, frase)
        if mancanti:
            elenco = ", ".join(f"'{c}' (U+{ord(c):04X})" for c in mancanti)
            raise ErroreTesti(f"{dove}: {ident}: caratteri senza glifo nel font: {elenco}")

        larghezza_max, righe_max = CONTESTI[contesto]
        parti = S.a_capo(font, frase, larghezza_max)
        if len(parti) > righe_max:
            raise ErroreTesti(f"{dove}: {ident}: {len(parti)} righe, il contesto {contesto} "
                              f"ne ammette {righe_max}")

        utf8 = " ".join(parti)
        byte = 0
        primo_glifo, prima_riga = len(glifi), len(righe)
        for parte in parti:
            x, primo = 0, len(glifi)
            for c in parte:
                glifi.append(indici[c])
                byte_glifo.append(byte)
                x_glifo.append(x)
                x += S.avanzamento(font, c)
                byte += len(c.encode("utf-8"))
            byte += 1   # lo spazio dell'a capo non e' un glifo: non si disegna
            n = len(glifi) - primo
            larghezza = x - font["spaziatura"]
            if larghezza > larghezza_max:
                raise ErroreTesti(f"{dove}: {ident}: la riga '{parte}' e' larga {larghezza} px, "
                                  f"il contesto {contesto} ne ammette {larghezza_max}")
            righe.append((primo, n, larghezza))
            # Punto di taglio k: il primo glifo (relativo alla riga) che tocca lo sprite k.
            for k in range(SPRITE_PER_RIGA):
                inizio = k * LARGHEZZA_SPRITE
                tocca = [g for g in range(n)
                         if x_glifo[primo + g] + S.larghezza_glifo(font, parte[g]) > inizio]
                tagli.append(tocca[0] if tocca else n)
        testi.append({"id": ident, "contesto": contesto, "utf8": utf8, "righe": len(parti),
                      "prima_riga": prima_riga, "primo_glifo": primo_glifo,
                      "glifi": len(glifi) - primo_glifo, "byte": len(utf8.encode("utf-8"))})

    return {"testi": testi, "glifi": glifi, "byte_glifo": byte_glifo, "x_glifo": x_glifo,
            "righe": righe, "tagli": tagli}


def letterale(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def a_blocchi(valori, per_riga=16):
    return "\n".join("    " + ", ".join(str(v) for v in valori[i:i + per_riga]) + ","
                     for i in range(0, len(valori), per_riga))


def scrivi_header(t):
    contesti = list(CONTESTI)
    out = [
        "// GENERATO da tools/genera_testi.py a partire da testi/*.testi e stile/dati/font.json.",
        "// Non modificare a mano: si accede alle tabelle solo da include/testo.h.",
        "#ifndef GUBBIO_TESTI_H",
        "#define GUBBIO_TESTI_H",
        "",
        "#include <cstdint>",
        "",
        "namespace gubbio::testi",
        "{",
        "",
        f"inline constexpr int LARGHEZZA_SPRITE = {LARGHEZZA_SPRITE};",
        f"inline constexpr int SPRITE_PER_RIGA = {SPRITE_PER_RIGA};",
        "",
        "enum class Contesto : uint8_t",
        "{",
    ]
    out += [f"    {c}," for c in contesti]
    out += [
        "};",
        "",
        f"inline constexpr int CONTESTI_CONTEGGIO = {len(contesti)};",
        "inline constexpr int CONTESTO_LARGHEZZA[CONTESTI_CONTEGGIO] = { "
        + ", ".join(str(CONTESTI[c][0]) for c in contesti) + " };",
        "inline constexpr int CONTESTO_RIGHE[CONTESTI_CONTEGGIO] = { "
        + ", ".join(str(CONTESTI[c][1]) for c in contesti) + " };",
        "",
        "enum class TestoId : uint16_t",
        "{",
    ]
    out += [f"    {x['id']}," for x in t["testi"]]
    out += [
        "};",
        "",
        "struct Riga",
        "{",
        "    uint16_t primo_glifo;   // indice in GLIFI",
        "    uint8_t glifi;",
        "    uint8_t larghezza;      // pixel accesi: avanzamenti meno l'ultima spaziatura",
        "};",
        "",
        "struct Testo",
        "{",
        "    const char* utf8;       // il testo gia' normalizzato, righe separate da uno spazio",
        "    uint16_t byte;",
        "    Contesto contesto;",
        "    uint8_t righe;",
        "    uint16_t prima_riga;    // indice in RIGHE",
        "    uint16_t primo_glifo;   // indice in GLIFI",
        "    uint16_t glifi;         // passi della macchina da scrivere",
        "};",
        "",
        f"inline constexpr int TESTI_CONTEGGIO = {len(t['testi'])};",
        f"inline constexpr int RIGHE_CONTEGGIO = {len(t['righe'])};",
        f"inline constexpr int GLIFI_CONTEGGIO = {len(t['glifi'])};",
        f"inline constexpr int TAGLI_CONTEGGIO = {len(t['tagli'])};",
        "",
        "// Indice del glifo in stile::FONT, per ogni passo della macchina da scrivere.",
        "inline constexpr uint8_t GLIFI[GLIFI_CONTEGGIO] = {",
        a_blocchi(t["glifi"]),
        "};",
        "",
        "// Byte di Testo::utf8 da cui comincia ogni glifo: sempre un confine di carattere UTF-8.",
        "inline constexpr uint16_t BYTE_GLIFO[GLIFI_CONTEGGIO] = {",
        a_blocchi(t["byte_glifo"]),
        "};",
        "",
        "// x del glifo nella sua riga, in pixel.",
        "inline constexpr uint8_t X_GLIFO[GLIFI_CONTEGGIO] = {",
        a_blocchi(t["x_glifo"]),
        "};",
        "",
        "inline constexpr Riga RIGHE[RIGHE_CONTEGGIO] = {",
    ]
    out += [f"    {{ {p}, {n}, {w} }}," for p, n, w in t["righe"]]
    out += [
        "};",
        "",
        "// Per ogni riga, SPRITE_PER_RIGA punti di taglio: il primo glifo della riga che tocca lo",
        "// sprite k (da 32 px). Lo sprite si accende quando i glifi rivelati nella riga lo superano.",
        "inline constexpr uint8_t TAGLI[TAGLI_CONTEGGIO] = {",
        a_blocchi(t["tagli"], SPRITE_PER_RIGA),
        "};",
        "",
        "inline constexpr Testo TESTI[TESTI_CONTEGGIO] = {",
    ]
    for x in t["testi"]:
        out.append(f"    {{ {letterale(x['utf8'])}, {x['byte']}, Contesto::{x['contesto']}, "
                   f"{x['righe']}, {x['prima_riga']}, {x['primo_glifo']}, {x['glifi']} }},")
    out += ["};", "", "}", "", "#endif", ""]
    return "\n".join(out)


def genera(sorgenti, font):
    """sorgenti: lista di (nome, byte). Ritorna il testo di include/testi.h."""
    voci = []
    for nome, dati in sorgenti:
        voci += leggi_voci(nome, dati)
    if not voci:
        raise ErroreTesti("nessun testo trovato in testi/*.testi")
    return scrivi_header(componi(voci, font))


def sorgenti_del_repo():
    out = []
    for p in sorted(glob.glob(SORGENTI)):
        with open(p, "rb") as f:
            out.append((os.path.relpath(p, RADICE).replace(os.sep, "/"), f.read()))
    return out


def main():
    try:
        header = genera(sorgenti_del_repo(), S.carica("font"))
    except ErroreTesti as e:
        print(f"[testi] ERRORE: {e}", file=sys.stderr)
        return 1
    if "--controlla" in sys.argv:
        attuale = open(USCITA, encoding="utf-8").read() if os.path.exists(USCITA) else ""
        if attuale != header:
            print("[testi] include/testi.h non e' aggiornato: python tools/genera_testi.py",
                  file=sys.stderr)
            return 1
        print("[testi] OK: include/testi.h aggiornato")
        return 0
    with open(USCITA, "w", encoding="utf-8", newline="\n") as f:
        f.write(header)
    print(f"[testi] scritto {os.path.relpath(USCITA, RADICE)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
