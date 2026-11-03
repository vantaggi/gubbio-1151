#!/usr/bin/env python3
"""Gubbio 1151, F7: musica ed effetti sonori, tutto originale e generato da questo script.

Sorgenti (scritte a mano):
  musica/*.brano       partiture in testo (formato in musica/LEGGIMI.md)
  questo file          gli strumenti (sintesi additiva, nessun campione registrato) e gli effetti

Uscita (generata, mai a mano; tests/test_audio.py controlla che sia aggiornata):
  audio/<brano>.xm     un modulo FastTracker 2 per brano: maxmod (Butano) lo converte da solo,
                       nel gioco diventa bn::music_items::<brano>
  audio/<effetto>.wav  effetti 8 bit mono 22050 Hz: bn::sound_items::<effetto>

Uso:
  python tools/genera_audio.py --scrivi            rigenera audio/
  python tools/genera_audio.py --ascolto DIR       anche WAV/MP3 da ascoltare (serve ffmpeg con
                                                   libopenmpt: e' un motore tracker vero, il
                                                   GBA suona simile ma a 16 kHz)
  python tools/genera_audio.py                     controlla soltanto (codice 1 se audio/ e' vecchio)

Niente numeri a virgola mobile nel gioco: qui si calcola tutto in Python e in ROM vanno solo byte.
"""
import math
import os
import re
import struct
import subprocess
import sys
import wave

import random

# -------------------------------------------------------------------------------------------------
# Vettori minimi in Python puro: il PC e la CI hanno solo la libreria standard (niente numpy).
# Quel poco di numpy che serve alla sintesi, con lo stesso nome, cosi' le formule restano leggibili.
# -------------------------------------------------------------------------------------------------

class A(list):
    """Lista di numeri con le operazioni elemento per elemento."""

    def _op(self, altro, f):
        if isinstance(altro, list):
            return A(f(a, b) for a, b in zip(self, altro))
        return A(f(a, altro) for a in self)

    def __add__(self, o): return self._op(o, lambda a, b: a + b)
    def __radd__(self, o): return self._op(o, lambda a, b: b + a)
    def __sub__(self, o): return self._op(o, lambda a, b: a - b)
    def __rsub__(self, o): return self._op(o, lambda a, b: b - a)
    def __mul__(self, o): return self._op(o, lambda a, b: a * b)
    def __rmul__(self, o): return self._op(o, lambda a, b: b * a)
    def __truediv__(self, o): return self._op(o, lambda a, b: a / b)
    def __neg__(self): return A(-a for a in self)
    def __gt__(self, o): return self._op(o, lambda a, b: 1.0 if a > b else 0.0)
    def __ge__(self, o): return self._op(o, lambda a, b: 1.0 if a >= b else 0.0)
    __iadd__ = __add__
    __isub__ = __sub__
    __imul__ = __mul__

    def __getitem__(self, i):
        r = list.__getitem__(self, i)
        return A(r) if isinstance(i, slice) else r

    @property
    def shape(self):
        return (len(self),)

    def astype(self, _):
        return self

    def copy(self):
        return A(self)


class _Casuale:
    def __init__(self, seme):
        self._r = random.Random(seme)

    def uniform(self, a, b, n=None):
        if n is None:
            return self._r.uniform(a, b)
        return A(self._r.uniform(a, b) for _ in range(n))


def _mappa(f, x):
    return A(f(v) for v in x) if isinstance(x, list) else f(x)


class np:  # noqa: N801  (stesso nome per tenere le formule come si scrivono di solito)
    float64 = float

    @staticmethod
    def arange(a, b=None, dtype=None):
        return A(float(i) for i in (range(a) if b is None else range(a, b)))

    @staticmethod
    def zeros(n):
        return A([0.0] * n)

    @staticmethod
    def zeros_like(x):
        return A([0.0] * len(x))

    empty_like = zeros_like

    @staticmethod
    def sin(x):
        return _mappa(math.sin, x)

    @staticmethod
    def exp(x):
        return _mappa(math.exp, x)

    @staticmethod
    def sign(x):
        return _mappa(lambda v: (v > 0) - (v < 0), x)

    @staticmethod
    def abs(x):
        return _mappa(abs, x)

    @staticmethod
    def max(x):
        return max(x)

    @staticmethod
    def minimum(a, b):
        if isinstance(a, list) and isinstance(b, list):
            return A(min(x, y) for x, y in zip(a, b))
        if isinstance(a, list):
            return A(min(x, b) for x in a)
        return A(min(a, y) for y in b)

    @staticmethod
    def clip(x, lo, hi):
        return A(min(hi if hi is not None else v, max(lo if lo is not None else v, v)) for v in x)

    @staticmethod
    def cumsum(x):
        s, uscita = 0.0, A()
        for v in x:
            s += v
            uscita.append(s)
        return uscita

    @staticmethod
    def concatenate(parti):
        uscita = A()
        for p in parti:
            uscita.extend(p)
        return uscita

    @staticmethod
    def linspace(a, b, n):
        return A(a + (b - a) * i / (n - 1) for i in range(n))

    @staticmethod
    def broadcast_to(x, shape):
        return x if isinstance(x, list) else A([x] * shape[0])

RADICE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
CARTELLA_BRANI = os.path.join(RADICE, "musica")
CARTELLA_AUDIO = os.path.join(RADICE, "audio")

MAX_CANALI = 8           # Butano ne permette 16; 8 bastano e il GBA ringrazia
MAX_RIGHE = 256          # limite di una pattern XM
SFX_FREQ = 22050         # consigliata da Butano per gli effetti
DO4 = 261.6255653005986  # Do centrale: nel modulo e' il C-4 (nota XM 49)


class ErroreMusica(Exception):
    pass


# =================================================================================================
# Sintesi
# =================================================================================================

def _rng(seme):
    return _Casuale(seme)


def _passa_basso(x, a):
    """Filtro a un polo: a in (0,1], piu' piccolo = piu' scuro."""
    y = np.empty_like(x)
    s = 0.0
    for i, v in enumerate(x):
        s += a * (v - s)
        y[i] = s
    return y


def _passa_alto(x, a):
    return x - _passa_basso(x, a)


def _parziali(lunghezza, periodo, parziali, fasi=None):
    """Somma di armoniche esatte di un periodo intero: (k, ampiezza)."""
    t = np.arange(lunghezza, dtype=np.float64)
    y = np.zeros(lunghezza)
    for i, (k, a) in enumerate(parziali):
        f = 0.0 if fasi is None else fasi[i]
        y += a * np.sin(2 * math.pi * k * t / periodo + f)
    return y


def _insieme(periodo, cicli, parziali, voci, seme):
    """Loop di `cicli` periodi con piu' voci leggermente scordate (cicli-1, cicli, cicli+1 nel loop):
    il loop resta esatto perche' ogni voce compie un numero intero di cicli."""
    lunghezza = periodo * cicli
    rng = _rng(seme)
    t = np.arange(lunghezza, dtype=np.float64)
    y = np.zeros(lunghezza)
    for scarto, peso in voci:
        c = cicli + scarto
        for k, a in parziali:
            y += peso * a * np.sin(2 * math.pi * k * c * t / lunghezza + rng.uniform(0, 2 * math.pi))
    return y


def _a_8bit(x, picco=118):
    m = float(max(abs(v) for v in x)) or 1.0
    return [max(-128, min(127, int(round(v / m * picco)))) for v in x]


class Strumento:
    """Un campione 8 bit con loop opzionale, la sua intonazione e l'inviluppo (in secondi)."""

    def __init__(self, nome, dati, freq, f0, loop=None, inviluppo=None, sostegno=None, rilascio=1024,
                 vibrato=(0, 0, 0, 0), pizzico=False):
        self.nome = nome
        self.dati = dati
        self.freq = freq          # frequenza di campionamento
        self.f0 = f0              # altezza del suono registrato nel campione (Hz)
        self.loop = loop          # (inizio, lunghezza) in campioni
        self.inviluppo = inviluppo  # [(secondi, livello 0-64)]
        self.sostegno = sostegno    # indice del punto di sostegno
        self.rilascio = rilascio    # fadeout XM
        self.vibrato = vibrato      # (tipo, sweep, profondita', velocita')
        self.pizzico = pizzico      # suona fino in fondo: una pausa non lo spegne


def _decadimento(t0, lam, livello=64):
    """Punti d'inviluppo per un decadimento esponenziale che parte a t0."""
    punti = [(0.0, livello), (t0, livello)]
    for s in (0.12, 0.3, 0.55, 0.9, 1.4, 2.1, 3.0, 4.2):
        punti.append((t0 + s, max(0, int(round(livello * math.exp(-lam * s))))))
    punti.append((t0 + 5.0, 0))
    return punti


def str_pizzicato(nome, freq, periodo, beta, inclinazione, d0, d1, attacco_periodi, seme):
    """Corda pizzicata: armoniche con decadimenti propri nell'attacco, poi un loop che il volume
    dell'inviluppo spegne con il decadimento della fondamentale."""
    n = periodo * attacco_periodi
    kmax = (periodo - 1) // 2
    ks = range(1, min(kmax, 40) + 1)
    amp = {k: abs(math.sin(math.pi * k * beta)) / k ** inclinazione for k in ks}
    dec = {k: d0 + d1 * k ** 1.3 for k in ks}
    t = np.arange(n, dtype=np.float64)
    y = np.zeros(n)
    for k in ks:
        y += amp[k] * np.exp(-dec[k] * t / freq) * np.sin(2 * math.pi * k * t / periodo)
    rng = _rng(seme)
    rumore = _passa_basso(rng.uniform(-1, 1, n), 0.5) * np.exp(-t / freq * 300) * 0.25
    y += rumore
    lun = periodo * 2
    tt = np.arange(n, n + lun, dtype=np.float64)
    T = n / freq
    coda = np.zeros(lun)
    for k in ks:
        coda += amp[k] * math.exp(-dec[k] * T) * np.sin(2 * math.pi * k * tt / periodo)
    dati = _a_8bit(np.concatenate([y, coda]))
    return Strumento(nome, dati, freq, freq / periodo, loop=(n, lun), inviluppo=_decadimento(T, d0 + d1),
                     rilascio=3000, pizzico=True)


def str_flauto(seme):
    freq, periodo = 16000, 31
    parz = [(1, 1.0), (2, 0.16), (3, 0.11), (4, 0.03), (5, 0.025)]
    att = periodo * 16
    t = np.arange(att, dtype=np.float64)
    tono = _parziali(att, periodo, parz) * np.minimum(1.0, t / (att * 0.7))
    rng = _rng(seme)
    soffio = _passa_alto(_passa_basso(rng.uniform(-1, 1, att), 0.45), 0.25) * np.exp(-t / freq * 60) * 0.5
    coda = _parziali(periodo * 4, periodo, parz)
    dati = _a_8bit(np.concatenate([tono + soffio, coda]))
    return Strumento("flauto", dati, freq, freq / periodo, loop=(att, periodo * 4),
                     inviluppo=[(0, 50), (0.04, 64), (0.18, 54), (0.30, 0)], sostegno=2,
                     vibrato=(0, 40, 2, 10))


def _formanti(f, formanti):
    return sum(g * math.exp(-((f - fc) / b) ** 2) for fc, b, g in formanti)


def str_ciaramella(seme):
    freq, periodo = 16000, 41
    f0 = freq / periodo
    form = [(1150, 400, 1.0), (2600, 500, 0.55), (600, 300, 0.4)]
    parz = [(k, (0.35 / k ** 0.4 + _formanti(k * f0, form))) for k in range(1, 20)]
    att = periodo * 12
    t = np.arange(att, dtype=np.float64)
    tono = _parziali(att, periodo, parz) * np.minimum(1.0, t / (att * 0.5))
    coda = _parziali(periodo * 4, periodo, parz)
    dati = _a_8bit(np.concatenate([tono, coda]))
    return Strumento("ciaramella", dati, freq, f0, loop=(att, periodo * 4),
                     inviluppo=[(0, 40), (0.03, 64), (0.12, 56), (0.22, 0)], sostegno=2,
                     vibrato=(0, 30, 2, 12))


def str_coro(seme):
    freq, periodo = 16000, 82
    f0 = freq / periodo
    form = [(750, 130, 1.0), (1150, 160, 0.55), (2600, 260, 0.22)]
    parz = [(k, (0.15 / k ** 0.8 + _formanti(k * f0, form))) for k in range(1, 38)]
    dati = _a_8bit(_insieme(periodo, 96, parz, [(-1, 0.8), (0, 1.0), (1, 0.8)], seme))
    return Strumento("coro", dati, freq, f0, loop=(0, len(dati)),
                     inviluppo=[(0, 8), (0.3, 64), (0.6, 58), (1.2, 0)], sostegno=2,
                     vibrato=(0, 60, 1, 8))


def str_corno(seme):
    freq, periodo = 16000, 82
    f0 = freq / periodo
    parz = [(k, 1.0 / k ** 1.5 * (1.4 if k in (2, 3) else 1.0)) for k in range(1, 18)]
    dati = _a_8bit(_insieme(periodo, 96, parz, [(0, 1.0), (1, 0.7)], seme))
    return Strumento("corno", dati, freq, f0, loop=(0, len(dati)),
                     inviluppo=[(0, 10), (0.07, 64), (0.25, 50), (0.45, 0)], sostegno=2)


def str_viella(seme):
    """Viella ad arco (lo strumento di Flaviano): dente di sega filtrato dalla cassa, due corde
    appena scordate, un po' di fruscio d'arco nell'attacco."""
    freq, periodo = 16000, 82
    f0 = freq / periodo
    cassa = [(300, 120, 0.8), (1000, 300, 1.0), (2600, 600, 0.45)]
    parz = [(k, (1.0 / k) * (0.3 + _formanti(k * f0, cassa))) for k in range(1, 40)]
    loop = _insieme(periodo, 96, parz, [(0, 1.0), (1, 0.6)], seme)
    att = periodo * 12
    t = np.arange(att, dtype=np.float64)
    rng = _rng(seme + 1)
    fruscio = _passa_alto(rng.uniform(-1, 1, att), 0.5) * np.exp(-t / freq * 40) * 0.35 * float(np.max(np.abs(loop)))
    testa = loop[-att:] * np.minimum(1.0, t / att) + fruscio
    dati = _a_8bit(np.concatenate([testa, loop]))
    return Strumento("viella", dati, freq, f0, loop=(att, len(loop)),
                     inviluppo=[(0, 30), (0.08, 64), (0.25, 56), (0.45, 0)], sostegno=2,
                     vibrato=(0, 50, 3, 11))


def str_bordone(seme):
    freq, periodo = 8000, 62
    f0 = freq / periodo
    parz = [(k, 1.0 / k * (1.5 if 7 <= k <= 12 else 1.0)) for k in range(1, 30)]
    dati = _a_8bit(_insieme(periodo, 96, parz, [(0, 1.0), (1, 0.8)], seme))
    return Strumento("bordone", dati, freq, f0, loop=(0, len(dati)),
                     inviluppo=[(0, 24), (0.45, 64), (1.1, 0)], sostegno=1)


def str_campana(seme):
    """Campana di bronzo: parziali inarmonici (bordone basso, fondamentale, terza minore, quinta,
    nominale...) ognuno col suo decadimento. Suonata alta fa da campanella."""
    freq, f = 8000, 220.0
    n = int(freq * 3.0)
    t = np.arange(n, dtype=np.float64) / freq
    parz = [(0.5, 0.55, 0.7), (0.503, 0.25, 0.75), (1.0, 0.7, 1.1), (1.19, 0.5, 1.4), (1.5, 0.3, 1.8),
            (2.0, 0.8, 1.6), (2.51, 0.3, 2.5), (2.66, 0.25, 2.8), (3.01, 0.2, 3.0), (4.1, 0.12, 4.5),
            (5.4, 0.06, 6.0)]
    y = np.zeros(n)
    rng = _rng(seme)
    for r, a, d in parz:
        y += a * np.exp(-d * t) * np.sin(2 * math.pi * r * f * t + rng.uniform(0, 6.28))
    y += _passa_basso(rng.uniform(-1, 1, n), 0.6) * np.exp(-t * 120) * 0.4
    return Strumento("campana", _a_8bit(y), freq, f, pizzico=True)


def str_vento(seme):
    freq = 8000
    n = freq
    rng = _rng(seme)
    r = _passa_basso(_passa_basso(rng.uniform(-1, 1, n + 800), 0.12), 0.3)
    # loop senza scatto: la coda sfuma nella testa
    corpo, testa = r[:n], r[n:n + 800]
    w = np.linspace(0, 1, 800)
    corpo[:800] = corpo[:800] * w + testa * (1 - w)
    t = np.arange(n) / freq
    corpo *= 0.75 + 0.25 * np.sin(2 * math.pi * 2 * t)
    return Strumento("vento", _a_8bit(corpo), freq, DO4, loop=(0, n),
                     inviluppo=[(0, 0), (1.5, 64), (3.0, 0)], sostegno=1)


def str_goccia(seme):
    freq, f0 = 16000, 1046.5
    n = int(freq * 0.16)
    t = np.arange(n) / freq
    fr = f0 * (1 + 0.6 * (1 - np.exp(-t * 60)))
    fase = 2 * math.pi * np.cumsum(fr) / freq
    y = np.sin(fase) * np.exp(-t * 28) * np.minimum(1, t * 2000)
    return Strumento("goccia", _a_8bit(y), freq, f0, pizzico=True)


def str_tamburo(seme):
    freq = 16000
    n = int(freq * 0.25)
    t = np.arange(n) / freq
    fr = 90 + 120 * np.exp(-t * 40)
    corpo = np.sin(2 * math.pi * np.cumsum(fr) / freq) * np.exp(-t * 18)
    rng = _rng(seme)
    cordiera = _passa_alto(rng.uniform(-1, 1, n), 0.6) * np.exp(-t * 22) * 0.55
    return Strumento("tamburo", _a_8bit(corpo + cordiera), freq, DO4, pizzico=True)


def str_grancassa(seme):
    freq = 8000
    n = int(freq * 0.6)
    t = np.arange(n) / freq
    fr = 50 + 60 * np.exp(-t * 25)
    corpo = np.sin(2 * math.pi * np.cumsum(fr) / freq) * np.exp(-t * 6)
    rng = _rng(seme)
    colpo = _passa_basso(rng.uniform(-1, 1, n), 0.3) * np.exp(-t * 60) * 0.5
    return Strumento("grancassa", _a_8bit(corpo + colpo), freq, DO4, pizzico=True)


def str_sonagli(seme):
    freq = 16000
    n = int(freq * 0.3)
    t = np.arange(n) / freq
    rng = _rng(seme)
    y = np.zeros(n)
    for inizio in (0.0, 0.028, 0.065):
        tt = np.clip(t - inizio, 0, None)
        acceso = t >= inizio
        squillo = sum(np.sin(2 * math.pi * fq * tt + rng.uniform(0, 6)) for fq in (4200, 5300, 6100, 7100))
        y += acceso * np.exp(-tt * 25) * (0.5 * squillo + _passa_alto(rng.uniform(-1, 1, n), 0.7))
    return Strumento("sonagli", _a_8bit(y), freq, DO4, pizzico=True)


def str_incudine(seme):
    freq, f = 16000, 800.0
    n = int(freq * 0.5)
    t = np.arange(n) / freq
    y = np.zeros(n)
    for r, a, d in ((1, 1.0, 6), (2.76, 0.6, 9), (5.40, 0.35, 14), (8.93, 0.2, 20)):
        if r * f < freq / 2:
            y += a * np.exp(-d * t) * np.sin(2 * math.pi * r * f * t)
    rng = _rng(seme)
    y += rng.uniform(-1, 1, n) * np.exp(-t * 300) * 0.6
    return Strumento("incudine", _a_8bit(y), freq, f, pizzico=True)


def _crea_strumenti():
    return {
        "liuto": str_pizzicato("liuto", 16000, 82, 0.18, 1.1, 2.5, 0.9, 24, 11),
        "arpa": str_pizzicato("arpa", 16000, 41, 0.3, 1.6, 1.5, 0.5, 40, 12),
        "flauto": str_flauto(13),
        "ciaramella": str_ciaramella(14),
        "coro": str_coro(15),
        "corno": str_corno(16),
        "bordone": str_bordone(17),
        "viella": str_viella(25),
        "campana": str_campana(18),
        "vento": str_vento(19),
        "goccia": str_goccia(20),
        "tamburo": str_tamburo(21),
        "grancassa": str_grancassa(22),
        "sonagli": str_sonagli(23),
        "incudine": str_incudine(24),
    }


_STRUMENTI = None


def strumenti():
    global _STRUMENTI
    if _STRUMENTI is None:
        _STRUMENTI = _crea_strumenti()
    return _STRUMENTI


# =================================================================================================
# Partiture
# =================================================================================================

NOMI_NOTE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
RE_NOTA = re.compile(r"^([A-G])([#b]?)(\d)$")
RE_GETTONE = re.compile(r"^(?P<cosa>[A-G][#b]?\d|r|x|X|\^|~)(?::(?P<dur>\d+))?(?:!(?P<vol>\d+))?$")
RE_COPIA = re.compile(r"^=\s*(?P<src>\w+)(?:\s+(?P<tr>[+-]\d+))?(?:\s+>(?P<rit>\d+))?(?:\s+!(?P<vol>\d+))?\s*$")


def midi(nome):
    m = RE_NOTA.match(nome)
    if not m:
        raise ErroreMusica(f"nota non valida: {nome}")
    alt = {"": 0, "#": 1, "b": -1}[m.group(2)]
    return 12 * (int(m.group(3)) + 1) + NOMI_NOTE[m.group(1)] + alt


def nome_nota(n):
    return ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"][n % 12] + str(n // 12 - 1)


def _trasponi_gettone(g, semitoni):
    m = re.match(r"^([A-G][#b]?\d)(.*)$", g)
    if not m or semitoni == 0:
        return g
    return nome_nota(midi(m.group(1)) + semitoni) + m.group(2)


def _gettoni(testo, macro, profondita=0):
    if profondita > 8:
        raise ErroreMusica("macro annidate troppo a fondo")
    testo = re.sub(r"\)\s*\*\s*(\d+)", r" )*\1 ", testo.replace("(", " ( "))
    uscita = []
    for g in testo.split():
        mm = re.match(r"^\$(\w+)([+-]\d+)?$", g)
        if mm:
            if mm.group(1) not in macro:
                raise ErroreMusica(f"macro sconosciuta: ${mm.group(1)}")
            tr = int(mm.group(2) or 0)
            uscita.extend(_trasponi_gettone(x, tr) for x in _gettoni(macro[mm.group(1)], macro, profondita + 1))
        else:
            uscita.append(g)
    return uscita


def _espandi(gettoni):
    """Risolve i gruppi ( ... )*n."""
    pila = [[]]
    for g in gettoni:
        if g == "(":
            pila.append([])
        elif g.startswith(")*"):
            if len(pila) < 2:
                raise ErroreMusica("parentesi chiusa senza aperta")
            gruppo = pila.pop()
            pila[-1].extend(gruppo * int(g[2:]))
        elif g == ")":
            raise ErroreMusica("dopo ')' serve '*n'")
        else:
            pila[-1].append(g)
    if len(pila) != 1:
        raise ErroreMusica("parentesi aperta senza chiusa")
    return pila[0]


def leggi_riga(gettoni, battuta, contesto):
    """Gettoni -> (eventi, righe). Evento: (riga, tipo, nota_midi, volume) con tipo
    'nota', 'pausa', 'stacca', 'tempo'."""
    eventi = []
    pos = 0
    dur = 4
    vol_base = 48
    for g in _espandi(gettoni):
        if g == "|":
            if pos % battuta:
                raise ErroreMusica(f"{contesto}: battuta storta, la stanghetta cade alla riga {pos} "
                                   f"(una battuta = {battuta} righe)")
            continue
        if re.match(r"^!\d+$", g):
            vol_base = int(g[1:])
            continue
        if re.match(r"^T\d+$", g):
            if not 32 <= int(g[1:]) <= 255:
                raise ErroreMusica(f"{contesto}: tempo {g[1:]} fuori da 32-255")
            eventi.append((pos, "tempo", int(g[1:]), 0))
            continue
        m = RE_GETTONE.match(g)
        if not m:
            raise ErroreMusica(f"{contesto}: gettone non valido '{g}'")
        if m.group("dur"):
            dur = int(m.group("dur"))
            if dur <= 0:
                raise ErroreMusica(f"{contesto}: durata nulla in '{g}'")
        cosa = m.group("cosa")
        vol = int(m.group("vol")) if m.group("vol") else None
        if vol is not None and vol > 64:
            raise ErroreMusica(f"{contesto}: volume {vol} oltre 64")
        if cosa == "r":
            eventi.append((pos, "pausa", 0, 0))
        elif cosa == "^":
            eventi.append((pos, "stacca", 0, 0))
        elif cosa == "~":
            pass
        elif cosa in ("x", "X"):
            eventi.append((pos, "nota", 60, vol if vol is not None else (60 if cosa == "X" else min(64, vol_base))))
        else:
            eventi.append((pos, "nota", midi(cosa), vol if vol is not None else vol_base))
        pos += dur
    return eventi, pos


def _senza_commento(riga):
    """'#' apre un commento solo a inizio riga o dopo uno spazio: F#4 resta una nota."""
    return re.sub(r"(^|\s)#.*$", "", riga).rstrip()


def temi_comuni():
    """Le frasi condivise fra i brani (il Tema di Gubbio e i suoi accompagnamenti)."""
    macro = {}
    percorso = os.path.join(CARTELLA_BRANI, "temi.comuni")
    if os.path.exists(percorso):
        with open(percorso, encoding="utf-8") as f:
            for riga in f:
                riga = _senza_commento(riga).strip()
                if not riga:
                    continue
                m = re.match(r"^def\s+(\w+)\s*:\s*(.*)$", riga)
                if not m:
                    raise ErroreMusica(f"temi.comuni: riga non capita '{riga}'")
                macro[m.group(1)] = macro.get(m.group(1), "") + " " + m.group(2)
    return macro


def leggi_brano(nome, testo, macro_comuni=None):
    b = {"nome": nome, "titolo": nome, "bpm": 120, "velocita": 6, "battuta": 16, "canali": [],
         "macro": dict(temi_comuni() if macro_comuni is None else macro_comuni), "sezioni": {}, "ordine": [], "ripresa": 0, "durata_attesa": None, "anello": True}
    sezione = None
    righe_sez = {}
    for numero, riga in enumerate(testo.splitlines(), 1):
        riga = _senza_commento(riga)
        if not riga.strip():
            continue
        ctx = f"{nome}:{numero}"
        m = re.match(r"^\[(\w+)\]\s+(\d+)(?:\s+/(\d+))?\s*$", riga)
        if m:
            sezione = m.group(1)
            if sezione in b["sezioni"]:
                raise ErroreMusica(f"{ctx}: sezione {sezione} ripetuta")
            b["sezioni"][sezione] = {"righe": int(m.group(2)), "linee": {},
                                     "battuta": int(m.group(3)) if m.group(3) else None}
            righe_sez[sezione] = numero
            continue
        if sezione is None:
            m = re.match(r"^canale\s+(\w+)\s+(\w+)(?:\s+(\d+))?\s*$", riga)
            if m:
                if m.group(2) not in strumenti():
                    raise ErroreMusica(f"{ctx}: strumento sconosciuto {m.group(2)}")
                b["canali"].append({"nome": m.group(1), "strumento": m.group(2),
                                    "pan": int(m.group(3)) if m.group(3) else None})
                continue
            m = re.match(r"^def\s+(\w+)\s*:\s*(.*)$", riga)
            if m:
                b["macro"][m.group(1)] = b["macro"].get(m.group(1), "") + " " + m.group(2)
                continue
            m = re.match(r"^(\w+)\s*:\s*(.*)$", riga)
            if not m:
                raise ErroreMusica(f"{ctx}: riga non capita")
            k, v = m.group(1), m.group(2).strip()
            if k in ("bpm", "velocita", "battuta"):
                b[k] = int(v)
            elif k == "durata_attesa":
                b[k] = float(v)
            elif k == "titolo":
                b[k] = v
            elif k == "anello":
                b[k] = v.lower() in ("si", "sì", "vero", "1")
            elif k == "ordine":
                voci = v.split()
                for i, s in enumerate(voci):
                    if s.startswith("*"):
                        b["ripresa"] = i
                b["ordine"] = [s.lstrip("*") for s in voci]
            else:
                raise ErroreMusica(f"{ctx}: chiave sconosciuta {k}")
            continue
        m = re.match(r"^(\w+)\s*:\s*(.*)$", riga)
        if not m:
            raise ErroreMusica(f"{ctx}: riga non capita")
        linee = b["sezioni"][sezione]["linee"]
        if m.group(1) in linee and m.group(2).lstrip().startswith("="):
            raise ErroreMusica(f"{ctx}: la copia va da sola")
        linee[m.group(1)] = (linee.get(m.group(1), "") + " " + m.group(2)).strip()
    _valida_brano(b)
    return b


def _valida_brano(b):
    nomi = [c["nome"] for c in b["canali"]]
    if not nomi:
        raise ErroreMusica(f"{b['nome']}: nessun canale")
    if len(set(nomi)) != len(nomi):
        raise ErroreMusica(f"{b['nome']}: canali con lo stesso nome")
    if len(nomi) > MAX_CANALI:
        raise ErroreMusica(f"{b['nome']}: {len(nomi)} canali, il massimo e' {MAX_CANALI}")
    if not b["ordine"]:
        raise ErroreMusica(f"{b['nome']}: manca l'ordine")
    for s in b["ordine"]:
        if s not in b["sezioni"]:
            raise ErroreMusica(f"{b['nome']}: l'ordine cita la sezione {s} che non esiste")
    if not 32 <= b["bpm"] <= 255:
        raise ErroreMusica(f"{b['nome']}: bpm {b['bpm']} fuori da 32-255")
    for nome_s, s in b["sezioni"].items():
        if not 1 <= s["righe"] <= MAX_RIGHE:
            raise ErroreMusica(f"{b['nome']} [{nome_s}]: {s['righe']} righe, il massimo e' {MAX_RIGHE}")
        for c in s["linee"]:
            if c not in nomi:
                raise ErroreMusica(f"{b['nome']} [{nome_s}]: canale {c} non dichiarato")
        s["eventi"] = {}
        for c in nomi:
            testo = s["linee"].get(c)
            if testo is None or testo.startswith("="):
                continue
            ev, n = leggi_riga(_gettoni(testo, b["macro"]), s["battuta"] or b["battuta"], f"{b['nome']} [{nome_s}] {c}")
            if n != s["righe"]:
                raise ErroreMusica(f"{b['nome']} [{nome_s}] {c}: {n} righe invece di {s['righe']}")
            s["eventi"][c] = ev
        for c in nomi:
            testo = s["linee"].get(c)
            if testo is None:
                s["eventi"][c] = [(0, "pausa", 0, 0)]
            elif testo.startswith("="):
                m = RE_COPIA.match(testo)
                if not m or m.group("src") not in s["eventi"] or s["linee"][m.group("src")].startswith("="):
                    raise ErroreMusica(f"{b['nome']} [{nome_s}] {c}: copia non valida '{testo}'")
                tr, rit = int(m.group("tr") or 0), int(m.group("rit") or 0)
                fattore = int(m.group("vol")) / 64 if m.group("vol") else 1.0
                copia = []
                for (r, tipo, n, v) in s["eventi"][m.group("src")]:
                    if tipo == "tempo" or r + rit >= s["righe"]:
                        continue
                    copia.append((r + rit, tipo, n + tr if tipo == "nota" else n,
                                  max(1, int(round(v * fattore))) if tipo == "nota" else v))
                if rit:
                    copia.insert(0, (0, "pausa", 0, 0))
                s["eventi"][c] = copia
        for c in nomi:
            for (r, tipo, n, v) in s["eventi"][c]:
                if tipo == "nota" and not 12 <= n <= 107:
                    raise ErroreMusica(f"{b['nome']} [{nome_s}] {c}: nota {nome_nota(n)} fuori portata")


def durata_brano(b, ordine=None):
    """Secondi di una passata dell'ordine (tiene conto dei cambi di tempo)."""
    ordine = ordine if ordine is not None else b["ordine"]
    bpm = b["bpm"]
    secondi = 0.0
    for s in ordine:
        sez = b["sezioni"][s]
        cambi = {}
        for ev in sez["eventi"].values():
            for (r, tipo, n, _) in ev:
                if tipo == "tempo":
                    cambi[r] = n
        bpm = b["bpm"] if 0 not in cambi else bpm
        for r in range(sez["righe"]):
            bpm = cambi.get(r, bpm)
            secondi += b["velocita"] * 2.5 / bpm
    return secondi


# =================================================================================================
# Scrittura XM
# =================================================================================================

def _testo(s, n):
    return s.encode("ascii", "replace")[:n].ljust(n, b"\0")


def _intonazione(st):
    v = 12 * math.log2(st.freq * DO4 / (st.f0 * 8363.0))
    rel = int(round(v))
    fine = int(round((v - rel) * 128))
    fine = max(-128, min(127, fine))
    return rel, fine


def _strumento_xm(st, bpm):
    tick = bpm * 0.4  # tick al secondo
    punti = []
    if st.inviluppo:
        x_prec = -1
        for sec, liv in st.inviluppo[:12]:
            x = int(round(sec * tick))
            x = max(x, x_prec + 1)
            punti.append((x, max(0, min(64, liv))))
            x_prec = x
    env = b"".join(struct.pack("<HH", x, y) for x, y in punti).ljust(48, b"\0")
    tipo_env = 0
    if punti:
        tipo_env = 1 | (2 if st.sostegno is not None else 0)
    rel, fine = _intonazione(st)
    tipo_vib, sweep, prof, vel = st.vibrato
    corpo = _testo(st.nome, 22) + struct.pack("<BH", 0, 1)
    corpo += struct.pack("<I", 40) + bytes(96) + env + bytes(48)
    corpo += struct.pack("<BBBBBBBBBBBBBBBB", len(punti), 0, st.sostegno or 0, 0, 0, 0, 0, 0,
                         tipo_env, 0, tipo_vib, sweep, prof, vel, 0, 0)[:14]
    corpo += struct.pack("<HH", st.rilascio, 0)
    testa = struct.pack("<I", 263) + corpo
    testa = testa.ljust(263, b"\0")
    dati = st.dati
    if st.loop:
        inizio, lun = st.loop
        tipo = 1
    else:
        inizio, lun, tipo = 0, 0, 0
    campione = struct.pack("<IIIBbBBbB", len(dati), inizio, lun, 64, fine, tipo, 128, rel, 0) + _testo(st.nome, 22)
    delta = bytes((v - p) & 0xFF for p, v in zip([0] + dati[:-1], dati))
    return testa + campione + delta


def genera_xm(b, ordine=None, ripresa=None):
    ordine = ordine if ordine is not None else b["ordine"]
    ripresa = b["ripresa"] if ripresa is None else ripresa
    canali = b["canali"]
    # sempre almeno un canale vuoto in fondo: ci vanno i cambi di tempo (Fxx); pari come vuole FT2
    n_canali = len(canali) + 1 + ((len(canali) + 1) % 2)
    usati = []
    for c in canali:
        if c["strumento"] not in usati:
            usati.append(c["strumento"])
    indice_str = {s: i + 1 for i, s in enumerate(usati)}
    tutti = strumenti()
    nomi_sez = []
    for s in ordine:
        if s not in nomi_sez:
            nomi_sez.append(s)
    pattern = []
    for s in nomi_sez:
        sez = b["sezioni"][s]
        celle = {}
        tempo_in_testa = any(r == 0 and t == "tempo" for ev in sez["eventi"].values() for (r, t, _, _) in ev)
        for ci, c in enumerate(canali):
            st = tutti[c["strumento"]]
            for (r, tipo, n, v) in sez["eventi"][c["nome"]]:
                cella = celle.setdefault((r, ci), [0, 0, 0, 0, 0])
                if tipo == "nota":
                    cella[0], cella[1], cella[2] = n - 11, indice_str[c["strumento"]], 0x10 + v
                    if c["pan"] is not None:
                        cella[3], cella[4] = 0x08, c["pan"]
                elif tipo in ("pausa", "stacca"):
                    if tipo == "stacca" or not st.pizzico:
                        if cella[0] == 0:
                            cella[0] = 97
        eventi_tempo = [(r, n) for ev in sez["eventi"].values() for (r, t, n, _) in ev if t == "tempo"]
        if not tempo_in_testa:
            eventi_tempo.append((0, b["bpm"]))
        for r, n in eventi_tempo:
            for ci in reversed(range(n_canali)):
                cella = celle.setdefault((r, ci), [0, 0, 0, 0, 0])
                if cella[3] == 0:
                    cella[3], cella[4] = 0x0F, n
                    break
            else:
                raise ErroreMusica(f"{b['nome']} [{s}]: nessun canale libero per il tempo alla riga {r}")
        dati = bytearray()
        for r in range(sez["righe"]):
            for ci in range(n_canali):
                cella = celle.get((r, ci))
                if not cella or not any(cella):
                    dati.append(0x80)
                    continue
                bandiere = 0x80
                corpo = bytearray()
                for bit, val in enumerate(cella):
                    if val:
                        bandiere |= 1 << bit
                        corpo.append(val)
                dati.append(bandiere)
                dati += corpo
        pattern.append(struct.pack("<IBHH", 9, 0, sez["righe"], len(dati)) + bytes(dati))
    indice_pat = {s: i for i, s in enumerate(nomi_sez)}
    ordini = bytes(indice_pat[s] for s in ordine).ljust(256, b"\0")
    testa = b"Extended Module: " + _testo(b["titolo"], 20) + b"\x1a" + _testo("genera_audio.py", 20)
    testa += struct.pack("<HIHHHHHHHH", 0x0104, 276, len(ordine), ripresa, n_canali, len(pattern),
                         len(usati), 1, b["velocita"], b["bpm"]) + ordini
    corpo = b"".join(pattern) + b"".join(_strumento_xm(tutti[s], b["bpm"]) for s in usati)
    return testa + corpo


def leggi_xm(dati):
    """Lettore minimo, per i test: intestazione, pattern grezze e campioni decodificati."""
    if dati[:17] != b"Extended Module: ":
        raise ErroreMusica("non e' un XM")
    (ver, hsz, lung, rip, can, npat, nstr, flag, vel, bpm) = struct.unpack_from("<HIHHHHHHHH", dati, 58)
    pos = 60 + hsz
    ordine = list(dati[80:80 + lung])
    pattern = []
    for _ in range(npat):
        plen, _, righe, psz = struct.unpack_from("<IBHH", dati, pos)
        pattern.append((righe, bytes(dati[pos + plen:pos + plen + psz])))
        pos += plen + psz
    strum = []
    for _ in range(nstr):
        isz, = struct.unpack_from("<I", dati, pos)
        nome = dati[pos + 4:pos + 26].rstrip(b"\0").decode()
        ncamp, = struct.unpack_from("<H", dati, pos + 27)
        intest = bytes(dati[pos:pos + isz])
        pos += isz
        campioni = []
        teste = []
        for _ in range(ncamp):
            teste.append(bytes(dati[pos:pos + 40]))
            pos += 40
        for t in teste:
            n, = struct.unpack_from("<I", t, 0)
            somma, valori = 0, []
            for d in dati[pos:pos + n]:
                somma = (somma + d) & 0xFF
                valori.append(somma - 256 if somma > 127 else somma)
            campioni.append((valori, t))
            pos += n
        strum.append({"nome": nome, "intestazione": intest, "campioni": campioni})
    if pos != len(dati):
        raise ErroreMusica(f"XM: {len(dati) - pos} byte avanzati")
    return {"canali": can, "ordine": ordine, "ripresa": rip, "velocita": vel, "bpm": bpm, "flag": flag,
            "pattern": pattern, "strumenti": strum}


# =================================================================================================
# Effetti sonori
# =================================================================================================

def _t(sec, freq=SFX_FREQ):
    return np.arange(int(sec * freq)) / freq


def _tono(fr, t, forma="seno"):
    fase = 2 * math.pi * np.cumsum(np.broadcast_to(fr, t.shape)) / SFX_FREQ
    if forma == "quadra":
        return np.sign(np.sin(fase)) * 0.6 + np.sin(fase) * 0.4
    return np.sin(fase)


def _pizzico_sfx(f, sec, dec=12.0):
    t = _t(sec)
    y = sum(np.sin(2 * math.pi * k * f * t) / k ** 1.4 * np.exp(-dec * k ** 0.6 * t) for k in range(1, 7) if k * f < 10000)
    return y * np.minimum(1, t * 3000)


def _campana_sfx(f, sec, seme):
    t = _t(sec)
    rng = _rng(seme)
    y = np.zeros_like(t)
    for r, a, d in ((0.5, 0.5, 0.6), (1.0, 0.7, 1.0), (1.19, 0.5, 1.3), (1.5, 0.3, 1.7), (2.0, 0.8, 1.5),
                    (2.51, 0.3, 2.4), (3.01, 0.2, 3.0), (4.1, 0.1, 4.4)):
        if r * f < 10000:
            y += a * np.exp(-d * t) * np.sin(2 * math.pi * r * f * t + rng.uniform(0, 6))
    y += _passa_basso(rng.uniform(-1, 1, len(t)), 0.5) * np.exp(-t * 100) * 0.3
    return y


def _sequenza(note, durata_nota, f=_pizzico_sfx, coda=0.15):
    passo = int(durata_nota * SFX_FREQ)
    tot = passo * len(note) + int(coda * SFX_FREQ)
    y = np.zeros(tot)
    for i, n in enumerate(note):
        s = f(440 * 2 ** ((midi(n) - 69) / 12), tot / SFX_FREQ - i * durata_nota)
        y[i * passo:i * passo + len(s)] += s[:tot - i * passo]
    return y


def _sfumatura(y, ms=8):
    n = min(len(y), int(SFX_FREQ * ms / 1000))
    y = y.copy()
    y[-n:] *= np.linspace(1, 0, n)
    return y


def effetti():
    """Nome -> campioni float. I nomi diventano bn::sound_items::<nome>."""
    rng = _rng(99)
    e = {}
    t = _t(0.035)
    e["cursore"] = _tono(1320, t, "quadra") * np.exp(-t * 60) * 0.7
    e["conferma"] = _sequenza(["A5", "D6"], 0.06, coda=0.12)
    e["annulla"] = _sequenza(["D5", "A4"], 0.06, coda=0.12)
    t = _t(0.02)
    e["testo"] = _pizzico_sfx(880, 0.02, 60) * np.minimum(1, (0.02 - t) * 400)
    t = _t(0.18)
    e["colpo"] = (_passa_basso(rng.uniform(-1, 1, len(t)), 0.35) * np.exp(-t * 25)
                  + np.sin(2 * math.pi * np.cumsum(70 + 150 * np.exp(-t * 50)) / SFX_FREQ) * np.exp(-t * 18))
    t = _t(0.5)
    crepitio = (rng.uniform(0, 1, len(t)) > 0.985).astype(float) * rng.uniform(-1, 1, len(t))
    soffio = _passa_basso(rng.uniform(-1, 1, len(t)), 0.08) * np.sin(math.pi * t / 0.5) * 2.5
    e["fuoco"] = soffio + _passa_basso(crepitio, 0.6) * 3 * np.exp(-t * 3)
    e["cura"] = _sequenza(["D5", "F5", "A5", "D6", "F6"], 0.05, coda=0.35)
    e["fede"] = _campana_sfx(880, 0.9, 7) + _campana_sfx(1318.5, 0.9, 8) * 0.6
    t = _t(0.35)
    e["scudo"] = sum(np.sin(2 * math.pi * f * t) * np.exp(-d * t) for f, d in ((523, 9), (1444, 12), (2830, 16), (4670, 22))) \
        + rng.uniform(-1, 1, len(t)) * np.exp(-t * 200)
    e["salva"] = _sequenza(["A5", "E6", "A6"], 0.08, f=lambda f, s: _campana_sfx(f, s, 3), coda=0.4)
    t = _t(0.4)
    e["svanisce"] = _passa_alto(rng.uniform(-1, 1, len(t)), 0.4) * np.exp(-t * 6) * 0.6 \
        + _tono(900 * np.exp(-t * 4), t) * np.exp(-t * 5)
    e["livello"] = _sequenza(["D5", "A5", "D6", "F#6", "A6"], 0.07, coda=0.4)
    e["campanone"] = _campana_sfx(146.83, 2.8, 5)
    return {k: _sfumatura(v) for k, v in e.items()}


def wav_8bit(campioni, freq=SFX_FREQ):
    m = float(max(abs(v) for v in campioni)) or 1.0
    u = bytes(max(0, min(255, int(round(v / m * 118)) + 128)) for v in campioni)
    import io
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(1)
        w.setframerate(freq)
        w.writeframes(u)
    return buf.getvalue()


# =================================================================================================
# Repo
# =================================================================================================

def sorgenti_del_repo():
    uscita = []
    for f in sorted(os.listdir(CARTELLA_BRANI)):
        if f.endswith(".brano"):
            with open(os.path.join(CARTELLA_BRANI, f), encoding="utf-8") as h:
                uscita.append((f[:-6], h.read()))
    return uscita


def genera_tutto():
    """Nome file -> byte di tutto cio' che va in audio/."""
    uscita = {}
    for nome, testo in sorgenti_del_repo():
        uscita[nome + ".xm"] = genera_xm(leggi_brano(nome, testo))
    for nome, y in effetti().items():
        if nome + ".xm" in uscita:
            raise ErroreMusica(f"{nome}: stesso nome per un brano e un effetto")
        uscita[nome + ".wav"] = wav_8bit(y)
    return uscita


def _ascolto(cartella):
    """Una passata + la ripresa (i brani ad anello), rese da libopenmpt via ffmpeg, in WAV e MP3."""
    import tempfile
    os.makedirs(cartella, exist_ok=True)
    righe = []
    with tempfile.TemporaryDirectory() as tmp:
        for nome, testo in sorgenti_del_repo():
            b = leggi_brano(nome, testo)
            ordine = b["ordine"] + (b["ordine"][b["ripresa"]:] if b["anello"] else [])
            xm = os.path.join(tmp, nome + ".xm")
            with open(xm, "wb") as f:
                f.write(genera_xm(b, ordine, ripresa=0))
            passata = durata_brano(b)
            tot = durata_brano(b, ordine)
            filtro = f"afade=t=out:st={max(0.0, tot - 4):.2f}:d=4" if b["anello"] else "anull"
            wav = os.path.join(cartella, nome + ".wav")
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", xm, "-t", f"{tot + 2.5:.2f}",
                            "-af", filtro, "-ar", "32000", wav], check=True)
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", wav, "-b:a", "128k",
                            os.path.join(cartella, nome + ".mp3")], check=True)
            righe.append((nome, b["titolo"], passata, b["anello"], len(b["canali"])))
    for nome, y in effetti().items():
        with open(os.path.join(cartella, "effetto_" + nome + ".wav"), "wb") as f:
            f.write(wav_8bit(y))
    return righe


def main(argv):
    uscita = genera_tutto()
    if "--scrivi" in argv:
        os.makedirs(CARTELLA_AUDIO, exist_ok=True)
        for f in os.listdir(CARTELLA_AUDIO):
            if f not in uscita and f.endswith((".xm", ".wav")):
                os.remove(os.path.join(CARTELLA_AUDIO, f))
        for nome, dati in uscita.items():
            with open(os.path.join(CARTELLA_AUDIO, nome), "wb") as f:
                f.write(dati)
        print(f"audio/: {len(uscita)} file, {sum(len(d) for d in uscita.values()) // 1024} KB")
    if "--ascolto" in argv:
        cartella = argv[argv.index("--ascolto") + 1]
        for nome, titolo, sec, anello, can in _ascolto(cartella):
            print(f"{nome:16} {sec:6.1f} s  {can} canali  {'anello' if anello else 'una volta'}  {titolo}")
    if "--scrivi" not in argv and "--ascolto" not in argv:
        vecchi = [n for n, d in uscita.items()
                  if not os.path.exists(os.path.join(CARTELLA_AUDIO, n))
                  or open(os.path.join(CARTELLA_AUDIO, n), "rb").read() != d]
        if vecchi:
            print("audio/ vecchio: python tools/genera_audio.py --scrivi", *vecchi)
            return 1
        print("audio/ aggiornato")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
