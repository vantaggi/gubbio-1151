#!/bin/bash
# Gate della politica ZERO-HEAP di AGENTS.md, misurata sui simboli dell'ELF invece che
# dichiarata a parole. Fallisce la build se nella ROM finisce un simbolo proibito.
#
# PERCHE' ESISTE: fino alla Sessione 07 la regola era solo scritta. Nella stessa sessione si e'
# scoperto che l'autotest riportava "zero assert" pur eseguendo un terzo dei round: una verifica
# che non puo' fallire non e' una verifica. Questo gate puo' fallire, ed e' il punto.
#
#   bash tools/check_zero_heap.sh [percorso.elf]
set -u

ELF="${1:-gubbio1151.elf}"
NM="${DEVKITARM:-C:/Users/cioti/devkitPro/opt/devkitpro/devkitARM}/bin/arm-none-eabi-nm.exe"

if [ ! -f "$ELF" ]; then
    echo "[zero-heap] ELF non trovato: $ELF (compilare prima)" >&2
    exit 1
fi

# Simboli vietati, per nome esatto. I nomi C++ sono storpiati (mangled):
#   _Znwj = operator new(unsigned)      _Znaj = operator new[](unsigned)
#   _ZdlPv = operator delete(void*)     _ZdaPv = operator delete[](void*)
VIETATI_ESATTI="_Znwj _ZnwjSt11align_val_t _Znaj _ZnajSt11align_val_t _ZdlPv _ZdaPv
_ZdlPvj _ZdaPvj __cxa_pure_virtual malloc calloc realloc _malloc_r _calloc_r _realloc_r _sbrk
ewram_alloc ewram_free"

# Doppia precisione: il GBA non ha FPU, ogni __aeabi_d* e' una routine software costosa e
# tradisce un float/double sfuggito al divieto di AGENTS.md.
VIETATI_PREFISSI="__aeabi_d __aeabi_f2d __adddf3 __muldf3 __divdf3"

# ESCLUSIONI DELIBERATE — senza queste il gate nascerebbe rosso sulla ROM pulita di oggi:
#   free          stub inerte di newlib, trascinato dal linker, mai chiamato dal gioco
#   mm* / mmAlloc gestione canali di maxmod, che alloca da un suo buffer statico, non da heap
# Un gate scritto come `grep -iE 'malloc|free'` fallirebbe da subito e verrebbe disattivato:
# e' il modo tipico in cui un controllo di qualita' muore.
ESCLUSI="free mmAllocChannel"

SIMBOLI="$("$NM" --defined-only --undefined-only "$ELF" 2>/dev/null | awk '{print $NF}' | sort -u)"
if [ -z "$SIMBOLI" ]; then
    SIMBOLI="$("$NM" "$ELF" 2>/dev/null | awk '{print $NF}' | sort -u)"
fi

if [ -z "$SIMBOLI" ]; then
    echo "[zero-heap] impossibile leggere i simboli con $NM" >&2
    exit 1
fi

trovati=0

for s in $VIETATI_ESATTI; do
    if echo "$SIMBOLI" | grep -qx "$s"; then
        escluso=0
        for e in $ESCLUSI; do [ "$s" = "$e" ] && escluso=1; done
        if [ "$escluso" -eq 0 ]; then
            echo "[zero-heap] VIETATO: $s"
            trovati=$((trovati + 1))
        fi
    fi
done

for p in $VIETATI_PREFISSI; do
    for s in $(echo "$SIMBOLI" | grep "^$p" || true); do
        echo "[zero-heap] VIETATO (virgola mobile a doppia precisione): $s"
        trovati=$((trovati + 1))
    done
done

if [ "$trovati" -gt 0 ]; then
    echo "[zero-heap] FALLITO: $trovati simboli proibiti in $ELF" >&2
    echo "[zero-heap] Vedi AGENTS.md sezione 2: nessuna allocazione dinamica, nessun float/double." >&2
    exit 1
fi

# --- (a) Collocazione di g_game_state: EWRAM, non IWRAM -------------------------------------
# `BN_DATA_EWRAM_BSS` e' un attributo di sezione: se qualcuno lo toglie, o sposta la definizione
# in un header, la variabile finisce in `.bss` — che su questo progetto sta a 0x030022f0, cioe'
# in IWRAM, i ~21 KB condivisi con lo stack. Non produrrebbe alcun errore: solo meno stack.
RIGA_STATO="$("$NM" --print-size "$ELF" 2>/dev/null | grep "gubbio12g_game_state" || true)"

if [ -z "$RIGA_STATO" ]; then
    echo "[zero-heap] FALLITO: g_game_state non e' nell'ELF." >&2
    echo "[zero-heap] O nessuno lo usa (trampolino scollegato), o e' stato rinominato." >&2
    exit 1
fi

INDIRIZZO_STATO="$(echo "$RIGA_STATO" | awk '{print $1}')"

case "$INDIRIZZO_STATO" in
    02*) echo "[zero-heap] OK: g_game_state in EWRAM a 0x$INDIRIZZO_STATO" ;;
    *)   echo "[zero-heap] FALLITO: g_game_state a 0x$INDIRIZZO_STATO, fuori da EWRAM (0x02......)." >&2
         echo "[zero-heap] Manca BN_DATA_EWRAM_BSS: la variabile sta rubando stack all'IWRAM." >&2
         exit 1 ;;
esac

# --- Controlli sui SORGENTI (Passo 5 del piano) --------------------------------------------
# Il gate finora guardava solo l'ELF. Questi due controlli riguardano invece regole che non
# lasciano traccia nei simboli e che quindi si romperebbero in silenzio.

PROGETTO="$(dirname "$0")/.."

# (d) `bn::core::update()` deve comparire in UN SOLO file: include/game_clock.h, che lo avvolge
# in `gubbio::core_update()` incrementando `playtime_frames`. Una scena che lo chiami per conto
# proprio fa perdere frame all'orologio di gioco senza che nulla lo segnali a runtime.
#
# Le righe di COMMENTO sono escluse da entrambi i controlli: le regole vanno CITATE nei
# commenti dei file che le rispettano (`scene.h` enuncia il divieto, `main.cpp` elenca cio' che
# non si puo' scrivere), e un gate che vietasse di nominarle costringerebbe a storpiare la
# prosa per farlo tacere — il modo tipico in cui un controllo di qualita' viene disattivato.
codice_che_contiene()   # $1 = regex ERE; stampa i file di src/ e include/ che la contengono
{
    grep -rnE "$1" "$PROGETTO/src" "$PROGETTO/include" 2>/dev/null |
        grep -vE "^[^:]+:[0-9]+: *(//|\*|/\*)" |
        cut -d: -f1 | sort -u
}

FUORI_CLOCK="$(codice_che_contiene "bn::core::update\(\)" | grep -v "game_clock.h" || true)"

if [ -n "$FUORI_CLOCK" ]; then
    echo "[zero-heap] FALLITO: bn::core::update() fuori da include/game_clock.h:" >&2
    echo "$FUORI_CLOCK" >&2
    echo "[zero-heap] Usare gubbio::core_update(): e' l'unico punto che conta playtime_frames." >&2
    exit 1
fi

# (e) Nessuna forma di proprieta' dinamica delle scene. Il dispatch le tiene come variabili di
# scope in uno `switch` (Passo 3c): puntatori possedenti, `new` e factory che ritornano `Scene*`
# reintrodurrebbero l'heap dalla porta di servizio, prima ancora che l'ELF possa accorgersene.
PROPRIETA_DINAMICA="$(codice_che_contiene "\bnew [A-Za-z_]|unique_ptr|Scene\* *[a-z_]+ *\(" || true)"

if [ -n "$PROPRIETA_DINAMICA" ]; then
    echo "[zero-heap] FALLITO: proprieta' dinamica di oggetti nei sorgenti:" >&2
    echo "$PROPRIETA_DINAMICA" >&2
    exit 1
fi

echo "[zero-heap] OK: nessuna allocazione dinamica ne' doppia precisione in $ELF"
echo "[zero-heap] OK: bn::core::update() confinato in include/game_clock.h"
exit 0
