#!/usr/bin/env python3
"""
Esportatore del COPIONE di Gubbio 1151: da testo italiano a tabelle C++ in ROM.

    python tools/dialogue_exporter.py

Produce `include/dialogue_data.h`: battute gia' spezzate in righe, script e parlanti.

PERCHE' IL WORD-WRAP LO FA QUESTO SCRIPT E NON IL GIOCO. Spezzare le righe a runtime
costerebbe, a ogni battuta, di misurare il testo con il generatore di sprite e di tenere da
qualche parte il risultato; farlo qui costa zero byte di RAM e zero cicli sul GBA, perche' le
righe finiscono gia' divise nelle tabelle `constexpr` in ROM. E' anche la ragione per cui
`dialogue_box.h` non ha alcuna nozione di larghezza: riceve righe, non paragrafi.

IL WRAP E' IN PIXEL, NON IN CARATTERI. Il font del progetto e' a larghezza variabile: una 'i'
occupa 2 px e una 'M' 8. Spezzare a 28 caratteri — il numero della Sez. 25 GDD — produce righe
che vanno da 90 a 220 px, cioe' alcune che escono dal box e altre mezze vuote. Qui si somma la
larghezza reale di ogni glifo, letta dalla stessa tabella che il C++ usa per disegnarli.

VERIFICA DEI CARATTERI. Ogni carattere del copione deve esistere nel font (94 ASCII + le 12
accentate italiane). Un carattere non mappato non e' un errore di compilazione: e' un `BN_ERROR`
a runtime, cioe' il gioco che si ferma davanti al giocatore su quella battuta. Qui lo script
fallisce prima, dicendo quale carattere e in quale battuta.
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")

# Larghezza utile del box: da TEXT_X=14 a 226, cioe' i 240 px dello schermo meno i bordi della
# cornice. Deve restare allineata a src/dialogue_view.cpp.
LARGHEZZA_UTILE_PX = 212

MAX_ROWS = 3          # DIALOGUE_MAX_ROWS in dialogue_box.h

ACCENTATE = "àèéìòùÀÈÉÌÒÙ"

# I parlanti, nell'ordine dell'enum `Speaker` di dialogue_box.h.
SPEAKER = ["UBALDO", "GIORGIO", "ANTONIO", "MONALDO", "PODESTA", "CITIZEN"]

# ----------------------------------------------------------------------------------------------
# IL COPIONE. Trascritto dalla Sezione 31B del GDD, che riporta le battute in prosa continua:
# qui restano IDENTICHE nel testo e vengono solo spezzate in righe dallo script.
#
# Dove il GDD e' piu' lungo di tre righe da 212 px, la battuta e' divisa in piu' BATTUTE
# successive — non tagliata. Il taglio del contenuto sarebbe una scelta di sceneggiatura, e non
# spetta a un esportatore.
# ----------------------------------------------------------------------------------------------

COPIONE = [
    # (id dello script, elenco di battute; ogni battuta e' (parlante, testo))
    ("PODESTA_ATTO_I", [
        ("PODESTA", "Monsignore... undici stendardi circondano la conca."),
        ("PODESTA", "Le nostre milizie sono poche, e le scorte di grano a "
                    "Palazzo Pretorio basteranno per una settimana."),
        ("PODESTA", "Se non troviamo un miracolo, cadremo prima dell'estate."),
        ("UBALDO", "Non contare le lance dei perugini, Guido. Conta la fede "
                   "di chi abita queste pietre."),
        ("UBALDO", "Fate sprangare le porte e ordinate alla citta' tre giorni "
                   "di silenzio e digiuno."),
    ]),
    ("PODESTA_ATTO_III", [
        ("PODESTA", "Porta Romana sta cedendo sotto i colpi dei mangani di Foligno!"),
        ("PODESTA", "Giorgio, guida i balestrieri sui camminamenti prima che "
                    "aprano una breccia!"),
    ]),
    ("TANO_INGAGGIO", [
        ("CITIZEN", "Fermati, cavaliere! Nessuno passa davanti al Bargello "
                    "senza dimostrare la follia sacra"),
        ("CITIZEN", "di chi ama questa terra piu' della propria vita!"),
        ("CITIZEN", "Sei pronto a compiere i tre giri e a bagnarti la fronte?"),
    ]),
    ("TANO_PATENTE", [
        ("CITIZEN", "Che l'acqua della fonte liberi il tuo braccio dalla paura!"),
        ("CITIZEN", "Eccoti la patente, ceraiolo!"),
    ]),
    ("BERTO_LORE", [
        ("CITIZEN", "Mio nonno ha scalpellato la pietra del Condotto nel Bottaccione."),
        ("CITIZEN", "Diceva sempre: c'e' una fessura dove la roccia diventa "
                    "nera come la pece... li' la terra non dorme."),
        ("CITIZEN", "Fate attenzione se scendete laggiu'."),
    ]),
    ("RANIERO_QUEST", [
        ("CITIZEN", "Le mie fornaci sono spente, ragazzo. Le truppe di Spoleto "
                    "hanno bloccato i carichi al passo."),
        ("CITIZEN", "Se mi riporti il ferro sequestrato alle fornaci basse,"),
        ("CITIZEN", "forgero' per Giorgio un pettorale che nessun dardo potra' scalfire."),
    ]),
    ("AGNESE_QUEST", [
        ("CITIZEN", "Gli alchimisti di Cagli stanno riversando veleno nel fosso."),
        ("CITIZEN", "I feriti alle porte hanno le labbra viola e le bende non bastano."),
        ("CITIZEN", "Mi serve l'elleboro che cresce solo sulle rocce umide del "
                    "Bottaccione, o non supereranno la notte."),
    ]),
]

# Gli apostrofi del copione qui sopra sono la convenzione con cui il GDD stesso scrive le
# accentate in alcuni punti; il font le ha tutte, quindi si sostituiscono con le lettere vere.
# Fatto qui e non a mano nel testo perche' sia una regola e non una dimenticanza possibile.
SOSTITUZIONI = [
    ("citta'", "città"), ("Citta'", "Città"), ("piu'", "più"), ("Piu'", "Più"),
    ("perche'", "perché"), ("Perche'", "Perché"), ("laggiu'", "laggiù"),
    ("c'e'", "c'è"), ("C'e'", "C'è"), ("li'", "lì"), ("Li'", "Lì"),
    ("forgero'", "forgerò"), ("potra'", "potrà"), ("e'", "è"),
]


def carica_larghezze():
    """Le larghezze reali del font del progetto: la stessa tabella che usa il C++."""
    testo = open(os.path.join(ROOT, "include", "font_gubbio.h"), encoding="utf-8").read()
    blocco = testo.split("FONT_CHARACTER_WIDTHS[] = {")[1].split("};")[0]
    valori = [int(m) for m in re.findall(r"^\s*(\d+),", blocco, re.M)]

    larghezze = {}
    for i, larg in enumerate(valori[:95]):          # da ASCII 32 a 126
        larghezze[chr(32 + i)] = larg
    for i, ch in enumerate(ACCENTATE):
        larghezze[ch] = valori[95 + i]
    return larghezze


def applica_sostituzioni(testo):
    for prima, dopo in SOSTITUZIONI:
        # Confine di parola SOLO all'inizio: la forma da sostituire finisce gia' con un
        # apostrofo, e fra un apostrofo e lo spazio che segue `\b` NON vale — con `\b` anche in
        # coda nessuna sostituzione scattava, e il copione sarebbe finito in ROM con "citta'"
        # pur avendo il font le accentate. Difetto trovato da tests/test_dialogue_quest.py.
        testo = re.sub(r"\b" + re.escape(prima) + r"(?![\w'])", dopo, testo)
    return testo


def larghezza(testo, larghezze, dove):
    totale = 0
    for ch in testo:
        if ch not in larghezze:
            sys.exit(f"[copione] carattere non nel font: {ch!r} (U+{ord(ch):04X}) in {dove!r}\n"
                     f"           il gioco si fermerebbe con BN_ERROR su questa battuta")
        totale += larghezze[ch]
    return totale


def spezza(testo, larghezze, dove):
    """Word-wrap in PIXEL. Non spezza mai una parola: se una parola sola eccede la riga, e' un
    errore del copione e va riscritta, non troncata."""
    righe, corrente = [], ""

    for parola in testo.split():
        prova = parola if not corrente else corrente + " " + parola

        if larghezza(prova, larghezze, dove) <= LARGHEZZA_UTILE_PX:
            corrente = prova
        else:
            if not corrente:
                sys.exit(f"[copione] la parola {parola!r} da sola eccede {LARGHEZZA_UTILE_PX} px "
                         f"in {dove!r}: riscrivere la battuta")
            righe.append(corrente)
            corrente = parola

    if corrente:
        righe.append(corrente)

    if len(righe) > MAX_ROWS:
        sys.exit(f"[copione] {dove}: la battuta occupa {len(righe)} righe, il box ne mostra "
                 f"{MAX_ROWS}. Dividerla in due battute successive.")

    return righe


def main():
    larghezze = carica_larghezze()
    linee = []          # (parlante, [righe])
    script = []         # (nome, prima_linea, conteggio)

    for nome, battute in COPIONE:
        prima = len(linee)

        for indice, (parlante, testo) in enumerate(battute):
            dove = f"{nome}[{indice}]"
            righe = spezza(applica_sostituzioni(testo), larghezze, dove)
            linee.append((parlante, righe))

        script.append((nome, prima, len(battute)))

    _scrivi_header(linee, script, larghezze)

    piu_larga = max((larghezza(r, larghezze, "x"), r) for _, righe in linee for r in righe)
    print(f"[copione] {len(script)} script, {len(linee)} battute, "
          f"{sum(len(r) for _, r in linee)} righe")
    print(f"[copione] riga piu' larga: {piu_larga[0]} px su {LARGHEZZA_UTILE_PX} disponibili "
          f"-> {piu_larga[1][:44]!r}")


def _scrivi_header(linee, script, larghezze):
    voci = []
    for parlante, righe in linee:
        campi = ", ".join('"%s"' % r.replace('"', '\\"') for r in righe)
        vuote = ", ".join(['""'] * (MAX_ROWS - len(righe)))
        tutte = campi + (", " + vuote if vuote else "")
        voci.append("    {{{{{}}}, Speaker::{}}},".format(tutte, parlante))

    id_script = "\n".join(f"    {nome}," for nome, _, _ in script)
    tab_script = "\n".join(
        f"    {{{prima}, {conteggio}}},   // {nome}" for nome, prima, conteggio in script)

    contenuto = '''#ifndef DIALOGUE_DATA_H
#define DIALOGUE_DATA_H

#include <stdint.h>

#include "bn_string_view.h"

#include "dialogue_box.h"

// GENERATO DA tools/dialogue_exporter.py — non modificare a mano.
//
// Il copione della Sezione 31B del GDD, gia' spezzato in righe. Il taglio e' fatto **in pixel**
// sulle larghezze reali di `font_gubbio.h`: spezzare a 28 caratteri, come dice alla lettera la
// Sez. 25, darebbe righe da 90 a 220 px, alcune fuori dal box e altre mezze vuote.
//
// PERCHE' LE TABELLE SONO PIATTE. Il codice della Sez. 31C del GDD **non e' trascrivibile**:
// usa `bn::vector<DialogueNode, 4>` dentro un array `constexpr`, e `bn::vector` non e' un tipo
// letterale in Butano — non compilerebbe. Qui le battute stanno in un unico array e ogni script
// e' un INTERVALLO su quell'array: nessun contenitore annidato, tutto in ROM, zero RAM.

namespace gubbio {{

struct DialogueLine
{{
    bn::string_view row[DIALOGUE_MAX_ROWS];
    Speaker speaker;
}};

// Tutte le battute del gioco, in fila. `inline` obbligatorio: senza, ogni unita' di traduzione
// ne riceverebbe una copia in .rodata (regola del Passo 1 del piano).
inline constexpr DialogueLine DIALOGUE_LINES[] = {{
{voci}
}};

inline constexpr int DIALOGUE_LINE_COUNT = int(sizeof(DIALOGUE_LINES) / sizeof(DIALOGUE_LINES[0]));

// Uno script e' una sequenza di battute consecutive.
struct DialogueScript
{{
    uint16_t first_line;
    uint8_t line_count;
}};

enum class ScriptId : uint8_t
{{
{id_script}
    COUNT
}};

inline constexpr DialogueScript DIALOGUE_SCRIPTS[int(ScriptId::COUNT)] = {{
{tab_script}
}};

[[nodiscard]] constexpr const DialogueScript& dialogue_script(ScriptId id)
{{
    return DIALOGUE_SCRIPTS[int(id)];
}}

// Ogni script deve stare dentro la tabella delle battute: un intervallo che sborda sarebbe una
// lettura fuori array, e nessun assert lo direbbe prima che accada.
static_assert([]
{{
    for(const DialogueScript& s : DIALOGUE_SCRIPTS)
    {{
        if(s.line_count == 0 || int(s.first_line) + int(s.line_count) > DIALOGUE_LINE_COUNT)
        {{
            return false;
        }}
    }}

    return true;
}}(), "Uno script di dialogo esce dalla tabella delle battute");

}} // namespace gubbio

#endif // DIALOGUE_DATA_H
'''.format(voci="\n".join(voci), id_script=id_script, tab_script=tab_script)

    open(os.path.join(ROOT, "include", "dialogue_data.h"), "w", encoding="utf-8").write(contenuto)


if __name__ == "__main__":
    main()
