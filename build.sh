#!/bin/bash
# Build della ROM di Gubbio 1151.
#
#     bash build.sh          # controlla la toolchain, compila, passa il gate, stampa lo SHA-256
#     bash build.sh clean    # pulizia
#
# Prima di compilare confronta Butano e devkitARM con toolchain.lock e si ferma se non
# coincidono: una ROM fatta con una toolchain diversa non e' la stessa ROM.
set -euo pipefail

cd "$(dirname "$0")"

leggi_lock()   # $1 = chiave
{
    local valore
    valore="$(grep -E "^$1=" toolchain.lock | head -1 | cut -d= -f2- | tr -d '\r')"
    if [ -z "$valore" ]; then
        echo "ERRORE: $1 manca in toolchain.lock" >&2
        exit 1
    fi
    echo "$valore"
}

BUTANO_COMMIT="$(leggi_lock BUTANO_COMMIT)"
DEVKITARM_RELEASE="$(leggi_lock DEVKITARM_RELEASE)"
DEVKITARM_GCC="$(leggi_lock DEVKITARM_GCC)"

# --- devkitARM ------------------------------------------------------------------------------------
# In CI (immagine devkitpro/devkitarm) DEVKITPRO e DEVKITARM sono gia' impostate. Sul PC la
# toolchain e' estratta senza installer e non esporta variabili: si usa DKP_ROOT.
if [ -z "${DEVKITARM:-}" ]; then
    DKP_ROOT="${DKP_ROOT:-C:/Users/cioti/devkitPro}"
    export DEVKITPRO="$DKP_ROOT/opt/devkitpro"
    export DEVKITARM="$DEVKITPRO/devkitARM"
    if command -v cygpath > /dev/null; then
        DKP_POSIX="$(cygpath -u "$DKP_ROOT")"
        export PATH="$DKP_POSIX/opt/devkitpro/tools/bin:$DKP_POSIX/usr/bin:$PATH"
    fi
fi
export PATH="$(command -v cygpath > /dev/null && cygpath -u "$DEVKITARM" || echo "$DEVKITARM")/bin:$PATH"

if ! command -v arm-none-eabi-gcc > /dev/null; then
    echo "ERRORE: arm-none-eabi-gcc non trovato in $DEVKITARM/bin" >&2
    exit 1
fi

GCC_TROVATO="$(arm-none-eabi-gcc -dumpfullversion)"
if [ "$GCC_TROVATO" != "$DEVKITARM_GCC" ]; then
    echo "ERRORE: devkitARM con gcc $GCC_TROVATO, toolchain.lock vuole $DEVKITARM_GCC ($DEVKITARM_RELEASE)" >&2
    exit 1
fi

# La release (r68) e' scritta solo nel database dei pacchetti, che c'e' dove devkitARM e'
# installato con pacman (l'immagine Docker) e manca dove e' estratto a mano (il PC). Dove manca,
# fa fede il gcc, che cambia a ogni release.
RELEASE_TROVATA=""
for pm in dkp-pacman pacman; do
    if command -v "$pm" > /dev/null && "$pm" -Q devkitARM > /dev/null 2>&1; then
        RELEASE_TROVATA="$("$pm" -Q devkitARM | awk '{print $2}' | sed 's/-[0-9]*$//')"
        break
    fi
done
if [ -n "$RELEASE_TROVATA" ]; then
    if [ "$RELEASE_TROVATA" != "$DEVKITARM_RELEASE" ]; then
        echo "ERRORE: devkitARM $RELEASE_TROVATA, toolchain.lock vuole $DEVKITARM_RELEASE" >&2
        exit 1
    fi
    echo "[toolchain] devkitARM $RELEASE_TROVATA, gcc $GCC_TROVATO"
else
    echo "[toolchain] devkitARM: release non leggibile (niente pacman), gcc $GCC_TROVATO come da $DEVKITARM_RELEASE"
fi

# --- Butano ---------------------------------------------------------------------------------------
if [ ! -f butano/butano/butano.mak ]; then
    echo "ERRORE: submodule Butano assente: git submodule update --init" >&2
    exit 1
fi
BUTANO_TROVATO="$(git -C butano rev-parse HEAD)"
if [ "$BUTANO_TROVATO" != "$BUTANO_COMMIT" ]; then
    echo "ERRORE: Butano a $BUTANO_TROVATO, toolchain.lock vuole $BUTANO_COMMIT" >&2
    echo "Allineare con: git submodule update --init" >&2
    exit 1
fi
echo "[toolchain] Butano $(leggi_lock BUTANO_TAG) ($BUTANO_COMMIT)"

# --- Build ----------------------------------------------------------------------------------------
if [ "${1:-}" = "clean" ]; then
    make clean
    exit 0
fi

make -j"$(nproc 2> /dev/null || echo 4)" "$@"

echo "[rom] SHA-256 $(sha256sum gubbio1151.gba | awk '{print $1}')  gubbio1151.gba"
