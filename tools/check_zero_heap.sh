#!/bin/bash
# Gate della politica ZERO-HEAP, misurata sui simboli dell'ELF invece che dichiarata a parole.
# Ripreso dal prototipo (tag prototipo-v0). Fallisce se nella ROM finisce:
#   - un'allocazione dinamica (new/delete, malloc e famiglia);
#   - una routine software di virgola mobile, double o float: il GBA non ha FPU;
#   - g_game_state fuori dalla EWRAM.
# Una verifica che non puo' fallire non e' una verifica: questa puo', ed e' il punto.
#
#   bash tools/check_zero_heap.sh [percorso.elf]
set -u

ELF="${1:-gubbio1151.elf}"

if command -v arm-none-eabi-nm > /dev/null; then
    NM=arm-none-eabi-nm
else
    NM="${DEVKITARM:?DEVKITARM non impostata}/bin/arm-none-eabi-nm"
fi

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

# Virgola mobile in software: le routine __aeabi_d* / __aeabi_f* e i nomi libgcc equivalenti.
VIETATI_PREFISSI="__aeabi_d __aeabi_f __adddf3 __subdf3 __muldf3 __divdf3 __addsf3 __subsf3
__mulsf3 __divsf3 __extendsfdf2 __truncdfsf2 __floatsi __floatunsi __fixdf __fixsf __fixunsdf
__fixunssf"

# ESCLUSIONI DELIBERATE: senza queste il gate nascerebbe rosso su una ROM pulita.
#   free  stub inerte di newlib, trascinato dal linker, mai chiamato dal gioco
# Un gate scritto come `grep -iE 'malloc|free'` fallirebbe da subito e verrebbe disattivato.
ESCLUSI="free"

SIMBOLI="$("$NM" "$ELF" 2> /dev/null | awk '{print $NF}' | sort -u)"

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
        echo "[zero-heap] VIETATO (virgola mobile in software): $s"
        trovati=$((trovati + 1))
    done
done

if [ "$trovati" -gt 0 ]; then
    echo "[zero-heap] FALLITO: $trovati simboli proibiti in $ELF" >&2
    exit 1
fi

# --- g_game_state in EWRAM ------------------------------------------------------------------------
# BN_DATA_EWRAM_BSS e' un attributo di sezione: se qualcuno lo toglie la variabile finisce in
# .bss, cioe' in IWRAM (0x03......), i pochi KB condivisi con lo stack. Nessun errore, solo
# meno stack: per questo lo si misura.
RIGA_STATO="$("$NM" "$ELF" 2> /dev/null | grep "gubbio12g_game_state" || true)"

if [ -z "$RIGA_STATO" ]; then
    echo "[zero-heap] FALLITO: g_game_state non e' nell'ELF (rinominato o non usato)." >&2
    exit 1
fi

INDIRIZZO_STATO="$(echo "$RIGA_STATO" | awk '{print $1}')"

case "$INDIRIZZO_STATO" in
    02*) echo "[zero-heap] OK: g_game_state in EWRAM a 0x$INDIRIZZO_STATO" ;;
    *)   echo "[zero-heap] FALLITO: g_game_state a 0x$INDIRIZZO_STATO, fuori da EWRAM (0x02......)." >&2
         echo "[zero-heap] Manca BN_DATA_EWRAM_BSS: la variabile sta rubando stack all'IWRAM." >&2
         exit 1 ;;
esac

# --- Sorgenti ---------------------------------------------------------------------------------------
# Nessuna proprieta' dinamica degli oggetti: `new`, unique_ptr. Le righe di commento sono escluse,
# perche' le regole vanno citate nei commenti dei file che le rispettano.
PROGETTO="$(dirname "$0")/.."
PROPRIETA_DINAMICA="$(grep -rnE "\bnew [A-Za-z_]|unique_ptr" "$PROGETTO/src" "$PROGETTO/include" 2> /dev/null |
    grep -vE "^[^:]+:[0-9]+: *(//|\*|/\*)" | cut -d: -f1 | sort -u || true)"

if [ -n "$PROPRIETA_DINAMICA" ]; then
    echo "[zero-heap] FALLITO: proprieta' dinamica di oggetti nei sorgenti:" >&2
    echo "$PROPRIETA_DINAMICA" >&2
    exit 1
fi

# --- Memoria ----------------------------------------------------------------------------------------
# La EWRAM inizializzata (.ewram) si copia dalla ROM a ogni accensione e occupa ROM: solo dati piccoli con un
# valore iniziale (la battaglia). Le tabelle grandi stanno nella parte azzerata (BN_DATA_EWRAM_BSS, .sbss).
# Prima della revisione a loop (Loop 8) il navigatore della camminata automatica ci teneva 96 KB.
EWRAM_INIZIALIZZATA_MAX=16384
SIZE="${NM%nm}size"
EWRAM_INIZIALIZZATA="$("$SIZE" -A "$ELF" | awk '$1 == ".ewram" {print $2}')"

if [ -n "$EWRAM_INIZIALIZZATA" ] && [ "$EWRAM_INIZIALIZZATA" -gt "$EWRAM_INIZIALIZZATA_MAX" ]; then
    echo "[zero-heap] FALLITO: .ewram inizializzata di $EWRAM_INIZIALIZZATA byte (massimo $EWRAM_INIZIALIZZATA_MAX):" >&2
    echo "[zero-heap] le tabelle grandi vanno in BN_DATA_EWRAM_BSS (bn::optional se serve un costruttore)." >&2
    exit 1
fi
echo "[zero-heap] OK: EWRAM inizializzata ${EWRAM_INIZIALIZZATA:-0} byte (massimo $EWRAM_INIZIALIZZATA_MAX)"

echo "[zero-heap] OK: nessuna allocazione dinamica ne' virgola mobile in software in $ELF"
exit 0
