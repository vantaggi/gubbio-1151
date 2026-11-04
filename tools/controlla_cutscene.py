#!/usr/bin/env python3
"""Il giro di controllo delle cutscene (STANDARD_GRAFICO, W3): misura ogni piano usato dai copioni di
regia (regia/*.regia) sulle regole che si contano in automatico.

- P3  pixel orfani: un pixel diverso da tutti gli 8 vicini (pieni). Esclusi i colori ACCESO (fuochi,
      finestre, candele), i riflessi (l'ultimo tono di oro e bronzo) e il bianco (stelle, scintille).
- C4  il quasi nero (neutri 0) nei fondali: la sua quota sui pixel pieni del piano visibile.
- C5  le superfici grandi nei toni medi: la quota di pixel nel tono piu' chiaro della propria rampa.

Si guarda solo il quadro visibile fra le bande (le prime 112 righe della mappa), come in ROM.

    python tools/controlla_cutscene.py            # la tabella di tutti i piani
    python tools/controlla_cutscene.py c7_ghiaia  # solo i piani che contengono il nome
"""
import os
import sys

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RADICE, "tools"))
sys.path.insert(0, os.path.join(RADICE, "stile"))

import stile as S  # noqa: E402
import genera_regia as GR  # noqa: E402
import pittore_panorami as PP  # noqa: E402

QUADRO = 112
RAMPE = {r["nome"]: len(r["giorno"]) for r in S.carica("palette")["rampe"]}
# I piani che non sono fondali: figure in controluce, fanti, cartigli, effetti. Per loro il nero del
# contorno e' la regola (P1), non un difetto (C4).
FIGURE = ("fanti", "ritratto", "luce_", "trio", "araldo", "c5_ceri", "c5_cocci", "c5_brocca", "c6_fanti",
          "c6_corrado", "c7s_eroi", "c7b_eroi")


def esenti(palette):
    """Le voci per cui un pixel isolato e' ammesso (P3: luci, riflessi, stelle e scintille)."""
    out = {0}
    for i, rif in enumerate(palette):
        nome, tono = rif[0], rif[1]
        if PP.ACCESO in rif[2:] or (nome == "oro e bronzo" and tono == RAMPE[nome] - 1) or rif[:2] == ("neutri", 4):
            out.add(i)
    return out


def orfani(px, esenti_):
    n = 0
    for y in range(1, min(QUADRO, len(px)) - 1):
        r0, r1, r2 = px[y - 1], px[y], px[y + 1]
        for x in range(1, len(r1) - 1):
            c = r1[x]
            if c in esenti_:
                continue
            vicini = (r0[x - 1], r0[x], r0[x + 1], r1[x - 1], r1[x + 1], r2[x - 1], r2[x], r2[x + 1])
            if c not in vicini and all(vicini):
                n += 1
    return n


def misura(piano):
    nome, momento = GR.nome_e_momento(piano)
    t, palette, notte = GR.PIANI[nome](momento)
    px = t.px[:QUADRO]
    pieni = [c for riga in px for c in riga if c]
    nero = sum(1 for c in pieni if palette[c][:2] == ("neutri", 0))
    chiaro = sum(1 for c in pieni if palette[c][0] in RAMPE and palette[c][0] != "neutri"
                 and palette[c][1] == RAMPE[palette[c][0]] - 1 and PP.ACCESO not in palette[c][2:])
    figura = any(f in nome for f in FIGURE)
    return {"piano": piano, "figura": figura, "orfani": orfani(px, esenti(palette)),
            "nero": nero / max(len(pieni), 1), "chiaro": chiaro / max(len(pieni), 1), "pieni": len(pieni)}


def piani_usati():
    return sorted({p for c in (GR.leggi(n, t) for n, t in GR.sorgenti_del_repo()) for i in c["inquadrature"]
                   for p in i["piani"]})


def main(argv):
    filtro = argv[0] if argv else ""
    print(f"{'piano':32} {'tipo':7} {'P3 orfani':>9} {'C4 nero':>8} {'C5 chiaro':>9}")
    for p in piani_usati():
        if filtro not in p:
            continue
        m = misura(p)
        print(f"{p:32} {'figura' if m['figura'] else 'fondale':7} {m['orfani']:9d} {m['nero']:8.1%} {m['chiaro']:9.1%}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
