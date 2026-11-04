#!/bin/bash
# Banco di prova in cloud (o su Linux): compila una ROM col modo GUBBIO_AVVIO voluto nell'immagine
# Docker della CI, la fa girare in libmgba senza finestra seguendo un copione di tasti e salva le
# schermate in PNG. Vedi tools/banco_mgba.c per il formato del copione.
#
#     bash tools/banco.sh AVVIO COPIONE CARTELLA     # es. bash tools/banco.sh 0 prove/camminata.txt /tmp/foto
#
# Serve: docker (immagine mirror.gcr.io/devkitpro/devkitarm:20260610, stesso digest di toolchain.lock),
# libmgba-dev e Pillow. La ROM di ogni modo resta in build_banco_<AVVIO>/ per i giri seguenti.
set -euo pipefail
cd "$(dirname "$0")/.."
AVVIO="$1"; COPIONE="$(realpath "$2")"; OUT="$3"
IMMAGINE="${BANCO_IMMAGINE:-mirror.gcr.io/devkitpro/devkitarm:20260610}"
mkdir -p "$OUT" build_banco
ROM="build_banco/gubbio_avvio$AVVIO.gba"
# Butano vuole TARGET e BUILD senza barre: si compila in banco_obj<AVVIO>/ e la ROM si sposta dopo.
docker run --rm -v "$PWD":/w -w /w "$IMMAGINE" bash -c "
    git config --global --add safe.directory /w; git config --global --add safe.directory /w/butano
    make -j8 TARGET=banco_rom$AVVIO BUILD=banco_obj$AVVIO USERFLAGS=-DGUBBIO_AVVIO=$AVVIO" \
    > build_banco/build$AVVIO.log 2>&1 || { tail -30 build_banco/build$AVVIO.log; exit 1; }
mv -f banco_rom$AVVIO.gba "$ROM"; rm -f banco_rom$AVVIO.elf
gcc -O2 -o build_banco/banco tools/banco_mgba.c -lmgba
DOVE="$(realpath "$OUT")"
RADICE="$PWD"
( cd "$DOVE" && "$RADICE/build_banco/banco" "$RADICE/$ROM" "$COPIONE" ) 2> "$OUT/log.txt" || true
python3 - "$OUT" <<'PY'
import glob, os, sys
from PIL import Image
for p in glob.glob(os.path.join(sys.argv[1], "*.ppm")):
    Image.open(p).save(p[:-4] + ".png"); os.remove(p)
PY
echo "[banco] $(ls "$OUT"/*.png 2>/dev/null | wc -l) schermate in $OUT; log del gioco in $OUT/log.txt"
