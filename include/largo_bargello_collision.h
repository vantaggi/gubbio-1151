#ifndef LARGO_BARGELLO_COLLISION_H
#define LARGO_BARGELLO_COLLISION_H

#include <stdint.h>

#include "piazza_grande_collision.h"

namespace gubbio::maps {

// LARGO DEL BARGELLO — l'area dove sta davvero la Fontana dei Matti.
//
// PERCHE' ESISTE QUESTA MAPPA. Fino alla Sessione 18 la fontana era dentro Piazza Grande, perche'
// la legenda della Sez. 21B GDD la elencava fra i tile della piazza e il codice l'aveva ereditata.
// E' sbagliato: la **Fontana del Bargello** sta in Largo del Bargello, lungo la salita di **via
// dei Consoli**, davanti al palazzo omonimo. La correzione e' arrivata dal committente, che
// conosce la citta' — nessuna verifica automatica poteva trovarla, perche' il gioco funzionava
// benissimo con la fontana nel posto sbagliato.
//
// MISURE. Un largo, non una piazza: 32x24 tile, cioe' 256x192 px, che alla scala di 1,5 m/tile
// (city_reference.h) fanno circa 48 x 36 metri. Sta in un BG regolare 256x256 — uno solo, contro
// i quattro blocchi che Piazza Grande consuma con i suoi 512x512.
//
// TOPOGRAFIA, per la regola delle adiacenze (city_reference.h §3): il largo e' in salita, e
// **Piazza Grande sta piu' in alto, a est**. L'uscita verso la piazza e' quindi sul lato
// orientale; a ovest la via prosegue a scendere verso il quartiere di San Martino, che non e'
// ancora autorato.

constexpr int BARGELLO_WIDTH = 32;
constexpr int BARGELLO_HEIGHT = 24;
constexpr int BARGELLO_WIDTH_PX = BARGELLO_WIDTH * TILE_SIZE_PX;
constexpr int BARGELLO_HEIGHT_PX = BARGELLO_HEIGHT * TILE_SIZE_PX;

// Il fronte del Palazzo del Bargello, in scala: nella realta' e' un palazzo medievale stretto,
// molto piu' piccolo dei Consoli. 18 metri di fronte fanno 12 tile.
constexpr int BARGELLO_FIRST_X = 9;
constexpr int BARGELLO_LAST_X = 20;      // 12 tile
constexpr int BARGELLO_FACADE_LAST_Y = 7;

// La fontana ottagonale, 3x3 tile come vuole la Sez. 23 GDD (4,5 m di diametro), davanti al
// palazzo e leggermente decentrata — com'e' nella realta'.
constexpr int FONTANA_FIRST_X = 13;
constexpr int FONTANA_LAST_X = 15;
constexpr int FONTANA_FIRST_Y = 12;
constexpr int FONTANA_LAST_Y = 14;

// Valori di tile: gli stessi di `TileType`, cosi' che collisione, trigger e disegno restino una
// lingua sola in tutte le aree.
[[nodiscard]] inline constexpr uint8_t bargello_tile_type(int x, int y)
{
    if(x < 0 || x >= BARGELLO_WIDTH || y < 0 || y >= BARGELLO_HEIGHT)
    {
        return uint8_t(TileType::WALL);
    }

    // Palazzo del Bargello a nord, con il suo portone al centro del fronte.
    if(y <= BARGELLO_FACADE_LAST_Y)
    {
        if(x >= BARGELLO_FIRST_X && x <= BARGELLO_LAST_X)
        {
            return uint8_t(TileType::PRETORIO_FACADE);   // stesso trattamento grafico: pietra
        }

        return uint8_t(TileType::WALL);
    }

    // Case che chiudono il largo a sud: la via e' stretta, non e' uno spiazzo aperto.
    if(y >= BARGELLO_HEIGHT - 3)
    {
        return uint8_t(TileType::WALL);
    }

    // Uscita a EST, in salita verso Piazza Grande.
    if(x >= BARGELLO_WIDTH - 2 && y >= 10 && y <= 13)
    {
        return uint8_t(TileType::EXIT_PORTA_ROMANA);     // riusa il valore: e' un varco laterale
    }

    // A ovest la via scende verso San Martino: muro finche' quell'area non esiste.
    if(x <= 1)
    {
        return uint8_t(TileType::WALL);
    }

    // LA FONTANA DEI MATTI, finalmente al posto suo.
    if(x >= FONTANA_FIRST_X && x <= FONTANA_LAST_X &&
       y >= FONTANA_FIRST_Y && y <= FONTANA_LAST_Y)
    {
        return uint8_t(TileType::FOUNTAIN);
    }

    return uint8_t(TileType::GROUND);
}

struct BargelloGrid
{
    uint8_t data[BARGELLO_WIDTH * BARGELLO_HEIGHT];
};

[[nodiscard]] consteval BargelloGrid make_bargello_grid()
{
    BargelloGrid grid{};

    for(int y = 0; y < BARGELLO_HEIGHT; ++y)
    {
        for(int x = 0; x < BARGELLO_WIDTH; ++x)
        {
            grid.data[x + y * BARGELLO_WIDTH] = bargello_tile_type(x, y);
        }
    }

    return grid;
}

inline constexpr BargelloGrid BARGELLO_GRID = make_bargello_grid();

// La fontana c'e', ed e' calpestabile come lo era in piazza (la sua solidita' resta una
// decisione di design aperta, n.9 del piano).
static_assert(BARGELLO_GRID.data[14 + 13 * BARGELLO_WIDTH] == uint8_t(TileType::FOUNTAIN),
              "La Fontana dei Matti non e' in Largo del Bargello");

// Il fronte del palazzo misura i 12 tile che la scala impone ai suoi 18 metri.
static_assert([]
{
    int larghezza = 0;

    for(int x = 0; x < BARGELLO_WIDTH; ++x)
    {
        if(BARGELLO_GRID.data[x + 3 * BARGELLO_WIDTH] == uint8_t(TileType::PRETORIO_FACADE))
        {
            ++larghezza;
        }
    }

    return larghezza == 12;
}(), "Il fronte del Palazzo del Bargello non misura i 12 tile della scala");

// L'uscita verso Piazza Grande dev'essere raggiungibile: un varco murato e' un vicolo cieco che
// si scopre solo giocando.
static_assert(! is_solid(BARGELLO_GRID.data[BARGELLO_WIDTH - 1 + 12 * BARGELLO_WIDTH]),
              "Il varco verso Piazza Grande e' murato");

} // namespace gubbio::maps

#endif // LARGO_BARGELLO_COLLISION_H
