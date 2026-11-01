"""Aggancio comune ai test di stile: importa stile/stile.py dalla radice del repo."""
import os
import sys

RADICE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(RADICE, "stile"))

import stile as S  # noqa: E402,F401
