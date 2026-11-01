"""Esporta i dati di stile in header C++20 con tabelle constexpr (in ROM, zero heap, niente float).

    python stile/esporta_cpp.py           # scrive include/stile/*.h
    python stile/esporta_cpp.py --verifica  # esce con 1 se gli header non sono allineati ai dati

Gli header sono generati: non si modificano a mano. Il test tests/test_stile_cpp.py fallisce se
qualcuno cambia un JSON senza rigenerarli.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stile as S

USCITA = os.path.join(os.path.dirname(S.RADICE), "include", "stile")

TESTA = """// GENERATO da stile/esporta_cpp.py a partire da stile/dati/{fonte}. Non modificare a mano.
#ifndef {guardia}
#define {guardia}

#include <cstdint>

namespace gubbio::stile
{{
"""
CODA = """
}}

#endif
"""


def identificatore(nome):
    return (nome.replace(" ", "_").replace("'", "").upper()
            .replace("À", "A").replace("È", "E").replace("Ì", "I").replace("Ò", "O").replace("Ù", "U"))


def esa16(v):
    return f"0x{v:04X}"


def righe_numeri(valori, fmt, per_riga=8, rientro="    "):
    out = []
    for i in range(0, len(valori), per_riga):
        out.append(rientro + ", ".join(fmt(v) for v in valori[i:i + per_riga]) + ",")
    return "\n".join(out)


def h_palette():
    p = S.carica("palette")
    corpo = ["// Scelta 3: palette maestra in BGR555. Toni dal piu' scuro al piu' chiaro.",
             "// PALETTE_NOTTE ha gli stessi indici: notte e Bottaccione sono un cambio di palette.", ""]
    giorno, notte, inizio = [], [], 0
    for r in p["rampe"]:
        nome = identificatore(r["nome"])
        corpo.append(f"inline constexpr int RAMPA_{nome} = {inizio};   // {len(r['giorno'])} toni")
        giorno += r["giorno"]
        notte += r["notte"]
        inizio += len(r["giorno"])
    corpo.append(f"inline constexpr int COLORI_PALETTE = {len(giorno)};")
    corpo.append("")
    for nome, valori in (("PALETTE_GIORNO", giorno), ("PALETTE_NOTTE", notte)):
        corpo.append(f"inline constexpr uint16_t {nome}[COLORI_PALETTE] = {{")
        corpo.append(righe_numeri(valori, esa16))
        corpo.append("};")
        corpo.append("")
    return "palette.json", "\n".join(corpo)


def h_font():
    f = S.carica("font")
    corpo = ["// Scelta 8: font proporzionale. Una riga = un byte, bit 7 = pixel piu' a sinistra.",
             "// Riga 0-1 accenti delle maiuscole, 2-8 maiuscole, 4-8 corpo minuscolo, 9 discendenti.",
             "// Glifi in ordine di codice Unicode: si cercano con trova_glifo().",
             "",
             f"inline constexpr int FONT_ALTEZZA = {f['altezza']};",
             f"inline constexpr int FONT_INTERLINEA = {f['interlinea']};",
             f"inline constexpr int FONT_SPAZIATURA = {f['spaziatura']};",
             "",
             "struct Glifo",
             "{",
             "    char32_t codice;",
             "    uint8_t larghezza;",
             f"    uint8_t righe[{f['altezza']}];",
             "};",
             "",
             f"inline constexpr int GLIFI_FONT = {len(f['glifi'])};",
             "inline constexpr Glifo FONT[GLIFI_FONT] = {"]
    for ch in sorted(f["glifi"], key=ord):
        g = f["glifi"][ch]
        byte = []
        for riga in g:
            v = 0
            for i, p in enumerate(riga):
                if p == "#":
                    v |= 0x80 >> i
            byte.append(v)
        vis = ch if ch not in "\\'" else "\\" + ch
        corpo.append(f"    {{ U'{vis}', {len(g[0])}, {{ " + ", ".join(f"0x{b:02X}" for b in byte) + " } },")
    corpo.append("};")
    corpo.append("")
    corpo.append("// Equivalenze tipografiche (es. apostrofo curvo -> dritto), applicate prima della ricerca.")
    eq = sorted(f["equivalenze"].items(), key=lambda kv: ord(kv[0]))
    corpo.append(f"inline constexpr char32_t FONT_EQUIVALENZE[{len(eq)}][2] = {{")
    for da, a in eq:
        corpo.append(f"    {{ U'\\U{ord(da):08X}', U'\\U{ord(a):08X}' }},")
    corpo.append("};")
    corpo.append("")
    corpo.append("""// Ricerca binaria; nullptr se il carattere non ha glifo (il test sui testi lo impedisce).
constexpr const Glifo* trova_glifo(char32_t c)
{
    for(const auto& e : FONT_EQUIVALENZE)
    {
        if(e[0] == c)
        {
            c = e[1];
        }
    }

    int basso = 0;
    int alto = GLIFI_FONT - 1;

    while(basso <= alto)
    {
        int medio = (basso + alto) / 2;

        if(FONT[medio].codice == c)
        {
            return &FONT[medio];
        }

        if(FONT[medio].codice < c)
        {
            basso = medio + 1;
        }
        else
        {
            alto = medio - 1;
        }
    }

    return nullptr;
}""")
    return "font.json", "\n".join(corpo)


def tile_4bpp(righe):
    """8 parole a 32 bit per tile, come in VRAM: nibble basso = pixel di sinistra."""
    parole = []
    for riga in righe:
        v = 0
        for i, ch in enumerate(riga):
            v |= int(ch, 16) << (4 * i)
        parole.append(v)
    return parole


def h_cornice():
    c = S.carica("cornice")
    p = S.carica("palette")
    nomi = list(c["tile"])
    corpo = ["// Scelta 9: cornice a vetrata, tile 8x8 a 4bpp nel formato della VRAM.",
             "// Si compone a 9-slice (angoli con flip, lati a tessere alternate, centro pieno).", ""]
    colori = [0 if rif is None else S.colore(p, rif) for rif in c["colori"]]
    corpo.append("inline constexpr uint16_t CORNICE_PALETTE[16] = {")
    corpo.append(righe_numeri(colori, esa16))
    corpo.append("};")
    corpo.append("")
    for i, n in enumerate(nomi):
        corpo.append(f"inline constexpr int TILE_{identificatore(n)} = {i};")
    corpo.append(f"inline constexpr int TILE_CORNICE = {len(nomi)};")
    corpo.append("")
    corpo.append("inline constexpr uint32_t CORNICE_TILE[TILE_CORNICE * 8] = {")
    for n in nomi:
        corpo.append(f"    // {n}")
        corpo.append(righe_numeri(tile_4bpp(c["tile"][n]), lambda v: f"0x{v:08X}"))
    corpo.append("};")
    corpo.append("")
    r = c["regole"]
    for lato in ("lato_orizzontale", "lato_verticale"):
        corpo.append(f"inline constexpr int {lato.upper()}[{len(r[lato])}] = {{ "
                     + ", ".join(f"TILE_{identificatore(t)}" for t in r[lato]) + " };")
    corpo.append("")
    for nome, d in c["disposizione"].items():
        for k, v in d.items():
            if isinstance(v, int):
                corpo.append(f"inline constexpr int {identificatore(nome)}_{identificatore(k)} = {v};")
    return "cornice.json", "\n".join(corpo)


def h_pose():
    ps = S.carica("pose")
    corpo = ["// Scelta 11: scheletro delle pose. Coordinate dentro lo sprite 16x32, tempi in vblank.",
             "// Sinistra = destra con flip orizzontale hardware.", "",
             "struct Giunto", "{", "    int8_t x;", "    int8_t y;", "};", "",
             "enum class Direzione : uint8_t", "{", "    giu,", "    su,", "    destra,", "};", "",
             "enum Giunti : uint8_t", "{"]
    for g in ps["giunti"]:
        corpo.append(f"    GIUNTO_{identificatore(g)},")
    corpo.append(f"    GIUNTI_SCHELETRO,")
    corpo.append("};")
    corpo.append("")
    corpo.append("struct Fotogramma")
    corpo.append("{")
    corpo.append("    uint8_t vblank;")
    corpo.append("    Giunto giunti[3][GIUNTI_SCHELETRO];   // [Direzione][Giunti]")
    corpo.append("};")
    corpo.append("")
    for nome, a in ps["animazioni"].items():
        n = identificatore(nome)
        corpo.append(f"inline constexpr bool {n}_CICLO = {'true' if a['ciclo'] else 'false'};")
        corpo.append(f"inline constexpr Fotogramma {n}[{len(a['fotogrammi'])}] = {{")
        for f in a["fotogrammi"]:
            dirs = []
            for d in ("giu", "su", "destra"):
                dirs.append("{ " + ", ".join(f"{{ {f['giunti'][d][g][0]}, {f['giunti'][d][g][1]} }}"
                                             for g in ps["giunti"]) + " }")
            corpo.append(f"    {{ {f['vblank']}, {{ " + ", ".join(dirs) + " } },"
                         + (f"   // {f['posa']}" if "posa" in f else ""))
        corpo.append("};")
        corpo.append("")
    att = ps["animazioni"]["attacco"]["fotogrammi"]
    corpo.append("// Punta dell'arma rispetto alla mano davanti, per posa di attacco (vista di lato).")
    corpo.append(f"inline constexpr Giunto ATTACCO_PUNTA_ARMA[{len(att)}] = {{ "
                 + ", ".join(f"{{ {f['arma']['punta'][0]}, {f['arma']['punta'][1]} }}" for f in att) + " };")
    return "pose.json", "\n".join(corpo)


GENERATORI = {"palette.h": h_palette, "font.h": h_font, "cornice.h": h_cornice, "pose.h": h_pose}


def contenuto(nome):
    fonte, corpo = GENERATORI[nome]()
    guardia = "GUBBIO_STILE_" + nome.replace(".", "_").upper()
    return TESTA.format(fonte=fonte, guardia=guardia) + "\n" + corpo + "\n" + CODA.format()


def main():
    verifica = "--verifica" in sys.argv
    diversi = []
    os.makedirs(USCITA, exist_ok=True)
    for nome in GENERATORI:
        testo = contenuto(nome)
        percorso = os.path.join(USCITA, nome)
        if verifica:
            attuale = open(percorso, encoding="utf-8").read() if os.path.exists(percorso) else ""
            if attuale != testo:
                diversi.append(nome)
        else:
            with open(percorso, "w", encoding="utf-8", newline="\n") as f:
                f.write(testo)
    if diversi:
        print("header non allineati ai dati:", ", ".join(diversi), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
