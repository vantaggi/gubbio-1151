#!/bin/bash
# Build della ROM di Gubbio 1151.
#
# La toolchain e' installata SENZA privilegi di amministratore, estraendo i pacchetti pacman
# ufficiali di devkitPro invece di usare l'installer GUI (che richiede UAC). Non essendo
# un'installazione "di sistema", non esporta variabili d'ambiente globali: le imposta questo
# script. Eseguire da Git Bash nella root del progetto:
#
#     bash tools/build_rom.sh          # build incrementale
#     bash tools/build_rom.sh clean    # pulizia
#
set -eu

DKP_ROOT="${DKP_ROOT:-C:/Users/cioti/devkitPro}"

# devkitARM e make vogliono percorsi Windows (C:/...), mentre la ricerca degli eseguibili nel
# PATH di MSYS/Git Bash funziona solo con percorsi POSIX (/c/...): servono entrambe le forme.
export DEVKITPRO="$DKP_ROOT/opt/devkitpro"
export DEVKITARM="$DEVKITPRO/devkitARM"

DKP_POSIX="$(cygpath -u "$DKP_ROOT")"
export PATH="$DKP_POSIX/opt/devkitpro/devkitARM/bin:$DKP_POSIX/opt/devkitpro/tools/bin:$DKP_POSIX/usr/bin:$PATH"

if [ ! -x "$DEVKITARM/bin/arm-none-eabi-g++.exe" ]; then
    echo "ERRORE: devkitARM non trovato in $DEVKITARM" >&2
    echo "Reinstallare i pacchetti devkitPro, oppure impostare DKP_ROOT." >&2
    exit 1
fi

cd "$(dirname "$0")/.."

# Butano genera gli header degli asset da queste cartelle: devono esistere anche se vuote.
mkdir -p graphics audio dmg_audio

make "$@"
STATO=$?

# Il gate zero-heap gira solo su una build riuscita e non per `clean`.
if [ "$STATO" -eq 0 ] && [ "${1:-}" != "clean" ] && [ -f gubbio1151.elf ]; then
    bash tools/check_zero_heap.sh gubbio1151.elf || exit 1
fi

exit $STATO
