#!/usr/bin/env python3
"""Fallisce se un test Python si salta da solo.

Un test che si dichiara saltato quando manca qualcosa passa in verde senza aver verificato
niente: nel prototipo succedeva ai test del salvataggio quando il file .sav non c'era. Qui un
test o gira o fallisce.

    python tools/check_no_skip.py [cartella]      # default: tests/
"""

import pathlib
import re
import sys

VIETATI = re.compile(
    r"\.skip(If|Unless)?\b"          # unittest.skip, skipIf, skipUnless, self.skipTest no (vedi sotto)
    r"|\bskipTest\b"                 # self.skipTest(...)
    r"|\bSkipTest\b"                 # raise unittest.SkipTest
    r"|\bexpectedFailure\b"          # un fallimento atteso e' un fallimento nascosto
    r"|\bpytest\.(mark\.)?(skip|skipif|xfail)\b"
)


def main():
    radice = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "tests")
    file_test = sorted(radice.rglob("*.py"))
    if not file_test:
        print(f"[no-skip] FALLITO: nessun file .py in {radice}", file=sys.stderr)
        return 1

    trovati = []
    for percorso in file_test:
        for numero, riga in enumerate(percorso.read_text(encoding="utf-8").splitlines(), 1):
            codice = riga.split("#", 1)[0]
            if VIETATI.search(codice):
                trovati.append(f"{percorso}:{numero}: {riga.strip()}")

    if trovati:
        print("[no-skip] FALLITO: test che si saltano da soli:", file=sys.stderr)
        for t in trovati:
            print("  " + t, file=sys.stderr)
        return 1

    print(f"[no-skip] OK: {len(file_test)} file di test, nessuno si salta")
    return 0


if __name__ == "__main__":
    sys.exit(main())
