"""Le icone dei menu (tools/genera_icone_menu.py): l'header e' aggiornato e i disegni sono 8x8 coi colori della
Guida; ogni icona usata dal codice esiste."""
import os
import re
import subprocess
import sys

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RADICE, "tools"))
import genera_icone_menu as G  # noqa: E402


def test_header_aggiornato():
    r = subprocess.run([sys.executable, os.path.join(RADICE, "tools", "genera_icone_menu.py")],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout


def test_disegni_validi():
    for nome, righe in G.ICONE.items():
        assert len(G.tile(nome, righe)) == 8


def test_icone_usate_esistono():
    usate = set()
    for cartella in ("src", "include"):
        for radice, _, file in os.walk(os.path.join(RADICE, cartella)):
            for f in file:
                if f.endswith((".cpp", ".h")):
                    with open(os.path.join(radice, f), encoding="utf-8") as h:
                        usate |= set(re.findall(r"IconaMenu::([A-Z_]+)", h.read()))
    assert usate, "nessuna icona usata?"
    assert usate <= set(G.ICONE), sorted(usate - set(G.ICONE))
