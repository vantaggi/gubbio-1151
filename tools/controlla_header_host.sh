#!/bin/bash
# Controlla sull'host (senza devkitARM) che gli autotest a tempo di compilazione reggano:
# compila src/autotest_*.cpp con clang in modalita' 32 bit (int e puntatori come su ARM7TDMI),
# solo sintassi e static_assert. Serve quando la ROM non si puo' compilare (lavoro in cloud):
# non sostituisce build.sh, che resta la prova vera.
#
#   BUTANO=../butano bash tools/controlla_header_host.sh            # tutti gli autotest
#   BUTANO=../butano bash tools/controlla_header_host.sh src/x.cpp  # solo quelli indicati
set -u
RADICE="$(cd "$(dirname "$0")/.." && pwd)"
B="${BUTANO:-$RADICE/../butano}/butano"
[ -d "$B/include" ] || { echo "[host] Butano non trovato in $B (imposta BUTANO)"; exit 2; }
STUB="$(mktemp -d)"; mkdir -p "$STUB/gnu"; : > "$STUB/gnu/stubs-32.h"
GXX="$(ls -d /usr/include/c++/* | sort -V | tail -1)"; V="$(basename "$GXX")"
FILE=("$@"); [ ${#FILE[@]} -eq 0 ] && FILE=("$RADICE"/src/autotest_*.cpp)
esito=0
for f in "${FILE[@]}"; do
    if clang++ -m32 -std=c++20 -fsyntax-only -fconstexpr-steps=2000000000 -nostdinc++ \
        -isystem "$GXX" -isystem "/usr/include/x86_64-linux-gnu/c++/$V" -isystem "$STUB" \
        -isystem /usr/include/x86_64-linux-gnu -I"$RADICE/include" -I"$B/include" -I"$B/hw/include" \
        -DBN_CFG_ASSERT_ENABLED=0 -Wno-everything "$f" 2> "$STUB/err"; then
        echo "[host] OK    $(basename "$f")"
    else
        echo "[host] ERRORE $(basename "$f")"; grep -m3 "error" "$STUB/err"; esito=1
    fi
done
rm -rf "$STUB"; exit $esito
