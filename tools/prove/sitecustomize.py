"""Traccia delle letture per tools/prove.py: con GUBBIO_TRACCIA impostata, ogni processo Python (anche i
figli che un test lancia) annota i file aperti e le cartelle elencate. Senza la variabile non fa niente."""
import os
import sys

_FILE = os.environ.get("GUBBIO_TRACCIA")
if _FILE:
    _visti = set()

    def _annota(tipo, percorso):
        try:
            p = os.fsdecode(percorso)
        except TypeError:
            return
        if not isinstance(p, str) or not p:
            return
        chiave = (tipo, os.path.abspath(p))
        if chiave in _visti:
            return
        _visti.add(chiave)
        with _apri(_FILE, "a", encoding="utf-8") as f:
            f.write(f"{tipo}\t{chiave[1]}\n")

    _apri = open

    def _gancio(evento, argomenti):
        if evento == "open" and argomenti and isinstance(argomenti[0], (str, bytes, os.PathLike)):
            _annota("f", argomenti[0])
        elif evento in ("os.listdir", "os.scandir") and argomenti and argomenti[0] is not None:
            _annota("d", argomenti[0])
        elif evento == "glob.glob" and argomenti:
            _annota("g", argomenti[0])
        elif evento == "glob.glob/2" and argomenti:
            _annota("g", os.path.join(os.fsdecode(argomenti[2]) if argomenti[2] else "", os.fsdecode(argomenti[0])))

    sys.addaudithook(_gancio)
