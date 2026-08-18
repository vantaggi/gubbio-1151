#!/usr/bin/env python3
"""
Scarica in locale i riferimenti iconografici elencati in docs/riferimenti/FONTI.md.

    python tools/fetch_riferimenti.py

Le immagini finiscono in `riferimenti/`, che `.gitignore` esclude: pesano, e versionarle
significherebbe portarsi dietro le loro licenze dentro il repo. Cio' che sta in repo e' il
file delle FONTI, con URL, autore e licenza di ciascuna.

Si usa Wikimedia Commons e non una ricerca immagini generica: li' la licenza e' dichiarata e
l'autore tracciabile. Una foto qualsiasi presa dal web e' opera protetta del fotografo —
guardarla e' lecito, partirne per disegnare no.

Lo script chiede all'API di Commons anche AUTORE e LICENZA di ogni file, e li scrive accanto
all'immagine: assolvere l'attribuzione a posteriori e' molto piu' faticoso che farlo adesso.
"""

import json
import os
import sys
import urllib.parse
import urllib.request

DEST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "riferimenti")
API = "https://commons.wikimedia.org/w/api.php"
UA = "Gubbio1151-AssetPipeline/1.0 (progetto di gioco amatoriale; contatto via repo)"

# I file verificati finora. Si aggiungono qui man mano che FONTI.md cresce.
FILE_COMMONS = [
    "Gubbio Palazzo dei Consoli.jpg",
    "Gubbio Piazza Grande.jpg",
    "Piazza Grande Gubbio 02.jpg",
    "Gubbio, via dei consoli, 01.JPG",
]


def interroga(titolo):
    query = urllib.parse.urlencode({
        "action": "query", "format": "json", "prop": "imageinfo",
        "iiprop": "url|extmetadata", "titles": "File:" + titolo,
    })
    richiesta = urllib.request.Request(API + "?" + query, headers={"User-Agent": UA})

    with urllib.request.urlopen(richiesta, timeout=30) as risposta:
        pagine = json.load(risposta)["query"]["pages"]

    for pagina in pagine.values():
        info = pagina.get("imageinfo")
        if not info:
            return None
        meta = info[0].get("extmetadata", {})
        return {
            "url": info[0]["url"],
            "autore": _testo(meta.get("Artist")),
            "licenza": _testo(meta.get("LicenseShortName")),
        }
    return None


def _testo(voce):
    if not voce:
        return "non dichiarato"
    grezzo = voce.get("value", "")
    return " ".join(_senza_tag(grezzo).split())


def _senza_tag(html):
    fuori, dentro = [], False
    for c in html:
        if c == "<":
            dentro = True
        elif c == ">":
            dentro = False
        elif not dentro:
            fuori.append(c)
    return "".join(fuori)


def main():
    os.makedirs(DEST, exist_ok=True)
    righe_credito = []

    for titolo in FILE_COMMONS:
        dati = interroga(titolo)

        if not dati:
            print(f"  ATTENZIONE: {titolo} non trovato su Commons")
            continue

        destinazione = os.path.join(DEST, titolo.replace(" ", "_"))
        richiesta = urllib.request.Request(dati["url"], headers={"User-Agent": UA})

        with urllib.request.urlopen(richiesta, timeout=60) as risposta:
            contenuto = risposta.read()

        open(destinazione, "wb").write(contenuto)
        righe_credito.append(f"{titolo}\n    autore:  {dati['autore']}\n"
                             f"    licenza: {dati['licenza']}\n    url:     {dati['url']}")
        print(f"  {titolo}  ({len(contenuto) // 1024} KB)  {dati['licenza']}")

    with open(os.path.join(DEST, "CREDITI.txt"), "w", encoding="utf-8") as f:
        f.write("Attribuzioni dei riferimenti scaricati da Wikimedia Commons.\n"
                "Vanno riportate se una di queste immagini viene ridistribuita.\n\n")
        f.write("\n\n".join(righe_credito) + "\n")

    print(f"\n[riferimenti] {len(righe_credito)} file in {os.path.normpath(DEST)}"
          f" — attribuzioni in CREDITI.txt")


if __name__ == "__main__":
    sys.exit(main())
