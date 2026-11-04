"""Verifica del copione: ogni battuta usa solo caratteri ammessi e sta nelle righe del riquadro.

Uso:  python3 verifica_copione.py            (dalla cartella copione/)

Le larghezze sono quelle del font proporzionale 5x7 della scelta di stile 8 (glifo + 1 px di
spazio). I glifi disegnati in stile/tavole_font.py si leggono da li'; per gli altri si usa una
stima prudente (maiuscole 5 px, minuscole 4, strette 1-3). La larghezza utile del testo e' quella
del riquadro della scelta 9 con il medaglione del ritratto: 180 px. E' un controllo provvisorio:
in F1 lo sostituisce il generatore di testi.h, che taglia sul font vero.

v2 (3 novembre 2026): il riquadro del gioco ha 2 righe da 224 px; la verifica usa quella misura
(tools/genera_storia.py del thread del gioco). I file in v1/ non vengono letti.
"""
import os
import re
import sys

QUI = os.path.dirname(os.path.abspath(__file__))
LARGHEZZA_UTILE = 224
RIGHE_MAX = 2

AMMESSI = set(chr(c) for c in range(0x20, 0x7F)) | set("àèéìòùÀÈÉÌÒÙ«»")

PARLANTI = {
    "NARRATORE", "AREA", "SISTEMA", "OBIETTIVO", "SCELTA",
    "UBALDO", "GIORGIO", "ANTONIO", "GUIDO", "ARALDO", "CORRADO",
    "CECCO", "FANTE", "CANONICO", "SPIA", "SPETTRO", "GUERRIERO", "NELLO",
    "BERTO", "POPOLANA", "MERCIAIO", "TANO", "LAVANDAIA", "VENDITORE", "FRA' MATTEO",
    "LUCIA", "VECCHIO", "FRATE", "SENTINELLA",
    "RANIERO", "AGNESE", "FRA' BERNARDO", "GIACOMO", "SACRESTANO", "FERITO", "INFILTRATO", "MENDICANTE",
    # v2: dilemmi e amici (05_npc_amici.md)
    "RAGAZZO", "FOLLA",
    "CIACCIO", "CIOTTO", "FAZIO", "FEBO", "RUFINO", "FLAVIANO", "GIAMBONO", "VANNI",
    "MASIO", "ANDREUCCIO", "GIORDANO", "GABRIONE", "RENZO", "RAGNETTO", "RICCIARDO",
    "GIULIANA", "LAURETTA", "AURELIA", "VALERIANA", "LEONORA", "VALENZA", "NICOLUCCIO",
    "PADELLINO", "MONTANO",
}
# Gli amici di dati/amici.json (anche quelli aggiunti dopo, come MILIA e MICHELINO) e i mestieri di contorno
# di 06_npc_mestieri.md (pezzo VIVA): i loro parlanti si leggono dai dati, cosi' nessuna battuta resta fuori
# dal controllo quando entra un NPC nuovo (4 nov 2026).
def _parlanti_dai_dati():
    import json
    nomi = set()
    amici = os.path.join(QUI, "..", "dati", "amici.json")
    if os.path.exists(amici):
        with open(amici, encoding="utf-8") as f:
            nomi |= set(json.load(f)["amici"])
    mestieri = os.path.join(QUI, "06_npc_mestieri.md")
    if os.path.exists(mestieri):
        riga_npc = re.compile(r"^- (?:ULTIMATUM|DIGIUNO|NOTTE)(?: \(se (?:non )?[A-Z_0-9]+\))?: ([A-Z][A-Z']*)(?: \([a-z]+\))?: ")
        with open(mestieri, encoding="utf-8") as f:
            for riga in f:
                m = riga_npc.match(riga)
                if m:
                    nomi.add(m.group(1))
    return nomi


PARLANTI |= _parlanti_dai_dati()
ESPRESSIONI = {"calmo", "preoccupato", "deciso"}

G = {}
try:
    sys.path.insert(0, os.path.join(QUI, "..", "stile"))
    os.chdir(os.path.join(QUI, "..", "stile"))
    import tavole_font  # noqa: E402
    G = tavole_font.G
except Exception:  # la stima basta anche senza il modulo
    G = {}
finally:
    os.chdir(QUI)

STRETTE = {"i": 1, "l": 2, "!": 1, ".": 1, ",": 2, ":": 1, ";": 2, "'": 1, "|": 1,
           "ì": 2, "I": 3, "j": 3, "t": 3, "r": 3, "f": 3, " ": 2, "(": 2, ")": 2,
           "\"": 3, "1": 3}
LARGHE = {"m": 5, "w": 5, "M": 5, "W": 5}


def w_car(c):
    if c in G:
        return len(G[c][0]) + 1
    if c in STRETTE:
        return STRETTE[c] + 1
    if c in LARGHE:
        return LARGHE[c] + 1
    if c.isupper():
        return 6
    return 5


def larghezza(s):
    return sum(w_car(c) for c in s)


def a_capo(testo, maxw):
    righe, cur = [], ""
    for parola in testo.split(" "):
        prova = (cur + " " + parola).strip()
        if larghezza(prova) <= maxw:
            cur = prova
        else:
            righe.append(cur)
            cur = parola
    righe.append(cur)
    return righe


META_OBIETTIVO = re.compile(r"\s*\(area: [A-Z_]+\)\s*$")

RE_BATTUTA = re.compile(
    r"(?P<chi>[A-Z][A-Z']*(?: [A-Z][A-Z']*)?)(?: \((?P<espr>[a-z]+)\))?: (?P<testo>.+)$")


def battute(percorso):
    for n, riga in enumerate(open(percorso, encoding="utf-8"), 1):
        riga = riga.rstrip("\n")
        if not (riga.startswith("- ") or riga.startswith("| ")):
            continue
        corpo = riga[2:]
        if riga.startswith("| "):
            celle = [c.strip() for c in riga.strip("|").split("|")]
            corpo = celle[-1] if celle else ""
        # prefissi di fase o di condizione: "NOTTE: ", "DIGIUNO, prima volta: ", "dopo il dono: "
        for m in RE_BATTUTA.finditer(corpo):
            pass
        cand = None
        pos = 0
        while True:
            m = RE_BATTUTA.search(corpo, pos)
            if not m:
                break
            if m.group("chi") in PARLANTI:
                cand = m
                break
            pos = m.start() + 1
        if cand:
            testo = cand.group("testo").rstrip()
            if testo.endswith("|"):
                testo = testo[:-1].rstrip()
            # l'area meta di un OBIETTIVO, «(area: ID)» in fondo alla riga, non va a schermo (MOB)
            if cand.group("chi") == "OBIETTIVO":
                testo = META_OBIETTIVO.sub("", testo)
            yield n, cand.group("chi"), cand.group("espr"), testo


def main():
    errori, conteggio, per_file = [], 0, {}
    for nome in sorted(os.listdir(QUI)):
        if not nome.endswith(".md") or nome == "README.md":
            continue
        k = 0
        for n, chi, espr, testo in battute(os.path.join(QUI, nome)):
            conteggio += 1
            k += 1
            dove = f"{nome}:{n}"
            if espr and espr not in ESPRESSIONI:
                errori.append(f"{dove}: espressione sconosciuta «{espr}»")
            fuori = sorted(set(c for c in testo if c not in AMMESSI))
            if fuori:
                errori.append(f"{dove}: caratteri fuori dal font {fuori}")
            if chi == "SCELTA":
                for voce in testo.split(" / "):
                    if larghezza(voce) > 100:
                        errori.append(f"{dove}: voce di scelta troppo larga ({larghezza(voce)} px)")
                continue
            righe = a_capo(testo, LARGHEZZA_UTILE)
            if len(righe) > RIGHE_MAX:
                errori.append(f"{dove}: {len(righe)} righe ({chi}): {testo}")
        per_file[nome] = k
    for nome, k in per_file.items():
        print(f"{nome}: {k} battute")
    print(f"Totale: {conteggio} battute, {len(errori)} errori")
    for e in errori:
        print("  " + e)
    if conteggio == 0:
        print("Nessuna battuta trovata: il parser non sta leggendo nulla.")
        return 1
    return 1 if errori else 0


if __name__ == "__main__":
    sys.exit(main())
