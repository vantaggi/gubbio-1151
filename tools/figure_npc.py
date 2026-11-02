"""Le figure degli NPC d'ambiente (pezzo S): cinque sagome 16x16 riconoscibili, una per mestiere, con la
palette dei popolani (PALETTE_NEMICI di tools/genera_battaglia.py, la stessa che usa il gioco per gli
NPC). Ogni NPC del copione (copione/03_npc_ambiente.md) prende la figura dal suo nome.

Le figure sono di fronte come il giocatore, col contorno scuro; le cifre sono gli indici della palette
in esadecimale ('.' trasparente):
1 contorno, 2-3 pelle, 4-5 vermiglio, 6 bianco, 7 grigio, 8-9 pietra, a-b cuoio, c-d ferro, e oro, f verde.
"""
import re

FIGURE = {
    # la popolana: il fazzoletto bianco in testa, la veste rossa, il grembiule
    "popolana": [
        "......1111......",
        ".....166661.....",
        "....16666661....",
        "....16333361....",
        "....16131361....",
        "....16333361....",
        ".....133331.....",
        "....14444441....",
        "...1446666441...",
        "...1446666441...",
        "...1446666441...",
        "...1446666441...",
        "...1444444441...",
        "..144444444441..",
        "...1111111111...",
        "................",
    ],
    # il frate: il saio col cappuccio, il cordone bianco coi nodi, i sandali
    "frate": [
        "................",
        ".....1aaaa1.....",
        "....1aa33aa1....",
        "...1aa3333aa1...",
        "...1a313313a1...",
        "...1a333333a1...",
        "....1a3333a1....",
        "...1aaaaaaaa1...",
        "..1abaaaaaaba1..",
        "..1abaaaaaaba1..",
        "..1a66666666a1..",
        "...1aaa6aaaa1...",
        "...1aaa6aaaa1...",
        "...1aaaaaaaa1...",
        "....12....21....",
        "....11....11....",
    ],
    # il soldato: il cappello di ferro a tesa larga, la giubba rossa con la croce, la lancia
    "soldato": [
        ".............d..",
        "......1111...d..",
        "....1dddddd1.b..",
        "...1dd7777dd1b..",
        "....13333331.b..",
        "....13133131.b..",
        "....13333331.b..",
        ".....133331..b..",
        "....14444441.b..",
        "...1444664441b..",
        "...1466666641b..",
        "...1444664441b..",
        "....14444441.b..",
        "....1cccccc1.b..",
        "....1c1..1c1.b..",
        "....11....11.b..",
    ],
    # il mercante: il cappuccio rosso a tesa, la veste lunga di cuoio, la cintura d'oro e la borsa
    "mercante": [
        "......5555......",
        ".....555555.....",
        "....15555551....",
        "....13333331....",
        "....13133131....",
        "....13333331....",
        ".....133331.....",
        "....1bbbbbb1....",
        "...1bbbbbbbb1...",
        "...1bbbbbbbb1...",
        "...1eeeeeeee1...",
        "...1bbbbbbe41...",
        "...1bbbbbbb41...",
        "..1bbbbbbbbbb1..",
        "..111111111111..",
        "................",
    ],
    # l'anziano: i capelli grigi, la barba bianca, il mantello di lana, il bastone, curvo
    "anziano": [
        "................",
        "......1111......",
        ".....1dddd1.....",
        "....1d3333d1....",
        "....1d3133d1....",
        "....1d6336d1....",
        ".....166661.....",
        "....18866881....",
        "..a18888888881..",
        "..318888888881..",
        "..a18888888881..",
        "..a18888888881..",
        "..a.1888888881..",
        "..a.188888881...",
        "..a..1a..1a1....",
        "..a..11..111....",
    ],
}
ORDINE = ["popolana", "frate", "soldato", "mercante", "anziano"]

# il mestiere dal nome dell'NPC nel copione
MESTIERI = [(r"Popolana|Lavandaia|Tessitrice", "popolana"), (r"Fra'|Frate|Canonico", "frate"),
            (r"Balestriere|Sentinella", "soldato"), (r"console|Merciaio|Venditore", "mercante"),
            (r"Vecchio|Mastro|Tagliapietre", "anziano")]


def figura_di(nome):
    """La figura di un NPC dal suo nome nel copione; un nome che non dice il mestiere e' un errore."""
    for schema, figura in MESTIERI:
        if re.search(schema, nome):
            return figura
    raise ValueError(f"NPC '{nome}': nessuna figura per questo nome (tools/figure_npc.py, MESTIERI)")


def pixel(figura):
    return [[int(c, 16) if c != "." else 0 for c in riga] for riga in FIGURE[figura]]


def parole(figura):
    """Le 4 tile 8x8 (mappatura 1D, come TILE_GIOCATORE) in parole da 32 bit, 4 bit per pixel."""
    px = pixel(figura)
    out = []
    for ty in range(2):
        for tx in range(2):
            for riga in px[ty * 8:ty * 8 + 8]:
                parola = 0
                for x, v in enumerate(riga[tx * 8:tx * 8 + 8]):
                    parola |= v << (4 * x)
                out.append(parola)
    return out
