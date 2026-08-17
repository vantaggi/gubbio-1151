#ifndef PIAZZA_GRANDE_COLLISION_H
#define PIAZZA_GRANDE_COLLISION_H

#include <stdint.h>

namespace gubbio::maps {

constexpr int PIAZZA_WIDTH = 64;
constexpr int PIAZZA_HEIGHT = 40;

// Misure in PIXEL. Servono alla camera e al clamping del giocatore, che lavorano in pixel
// mentre la collisione lavora in tile: tenerle derivate invece che riscritte a mano e' cio'
// che impedisce alle due unita' di divergere.
constexpr int TILE_SIZE_PX = 8;
constexpr int PIAZZA_WIDTH_PX = PIAZZA_WIDTH * TILE_SIZE_PX;    // 512
constexpr int PIAZZA_HEIGHT_PX = PIAZZA_HEIGHT * TILE_SIZE_PX;  // 320

// Legenda Collisioni (Sez. 21B GDD). I valori numerici sono quelli originali: la griglia e'
// nata come numeri nudi e i numeri restano la rappresentazione in memoria.
enum class TileType : uint8_t
{
    GROUND            = 0,   // suolo libero
    WALL              = 1,   // Palazzo dei Consoli / Pretorio / ostacoli
    RAILING           = 2,   // parapetto panoramico sud: blocca il passo, non la vista
    DOOR_CONSOLI      = 3,   // trigger: ingresso del Palazzo dei Consoli
    EXIT_SAN_MARTINO  = 4,   // trigger: Quartiere San Martino (Bargello)
    EXIT_PORTA_ROMANA = 5,   // trigger: Porta Romana
    FOUNTAIN          = 6    // Fontana dei Matti: interazione (Patente da Matto)
};

inline constexpr uint8_t get_tile_type(int x, int y) {
    if (x < 0 || x >= PIAZZA_WIDTH || y < 0 || y >= PIAZZA_HEIGHT) return 1; // Fuori mappa = muro

    // Ringhiera sud
    if (y >= 38) return 2;

    // Palazzi Consoli e Pretorio a Nord
    if (y <= 18) {
        if (y == 18 && (x == 32 || x == 33)) return 3; // Portone Consoli
        return 1;
    }

    // Trigger Laterali
    if (x <= 2 && y >= 19 && y <= 22) return 4; // Verso San Martino / Bargello
    if (x >= 61 && y >= 19 && y <= 22) return 5; // Verso Porta Romana

    // Fontana dei Matti
    if (x >= 23 && x <= 24 && y >= 24 && y <= 25) return 6;

    return 0; // Terreno calpestabile
}

// Variante in PIXEL, e la ragione per cui esiste.
//
// La Sez. 21D del GDD stampa `get_tile_type(const uint8_t* grid, int pixel_x, int pixel_y)` —
// puntatore e pixel — mentre il codice implementa `get_tile_type(int x, int y)` in TILE.
// Omettendo il puntatore le due firme hanno lo STESSO NUMERO DI ARGOMENTI dello stesso tipo:
// un chiamante che segue il documento sbaglia di un fattore 8 senza il minimo errore di
// compilazione, e il difetto si manifesta come un giocatore che attraversa i muri. Da qui in
// avanti l'unita' e' nel NOME della funzione.
//
// Lo `>> 3` si applica a un `int`. Su un `bn::fixed` opererebbe sul valore grezzo a 12 bit di
// frazione, cioe' un errore di fattore 4096; da un `bn::fixed` si passa per `.floor_integer()`
// e mai per `.integer()`, che tronca verso zero e sbaglia in negativo.
// Lo shift e' preferito alla divisione anche per una ragione di CORRETTEZZA, non solo di costo:
// `-1 / 8` vale 0 (troncamento verso zero), quindi un pixel appena fuori dal bordo sinistro
// verrebbe letto come tile 0 — suolo libero — e il giocatore uscirebbe dalla mappa. `-1 >> 3`
// vale -1, che `get_tile_type` riconosce come fuori mappa e quindi come muro.
[[nodiscard]] inline constexpr uint8_t get_tile_type_px(int pixel_x, int pixel_y)
{
    return get_tile_type(pixel_x >> 3, pixel_y >> 3);
}

// Blocca il passo? I trigger NON sono solidi: bisogna poterci salire sopra perche' scattino.
// La Fontana e' oggi calpestabile (l'eroe cammina dentro il bacino): la sua solidita' e le sue
// misure — 2x2 nel codice contro 3x3 della Sez. 15B — sono una decisione di design aperta.
[[nodiscard]] inline constexpr bool is_solid(uint8_t tile)
{
    return tile == uint8_t(TileType::WALL) || tile == uint8_t(TileType::RAILING);
}

// Porta verso un'altra area: il giocatore che vi sale cambia scena.
[[nodiscard]] inline constexpr bool is_transition(uint8_t tile)
{
    return tile == uint8_t(TileType::DOOR_CONSOLI) ||
           tile == uint8_t(TileType::EXIT_SAN_MARTINO) ||
           tile == uint8_t(TileType::EXIT_PORTA_ROMANA);
}

// --- La griglia come DATO, derivata dalla funzione -------------------------------------------
//
// `MapDescriptor` (map_data.h) vuole un `const uint8_t*`: le mappe 2..9 della Sez. 38 lo
// riceveranno da Tiled via `tools/map_exporter.py`, Piazza Grande — che e' la mappa zero e il
// riferimento con cui il generatore d'arte va tenuto coerente — resta autorata in codice.
//
// La forma conta: `consteval` calcola l'array A COMPILE TIME dalla stessa `get_tile_type` di
// sopra, quindi non esistono due descrizioni della piazza da tenere allineate a mano. E
// `inline constexpr` fa esistere i 2560 byte UNA SOLA VOLTA in ROM: senza `inline`, a namespace
// scope, ogni unita' di traduzione che include l'header ne riceve una copia propria e i
// puntatori memorizzati in `MapDescriptor` differirebbero da una unita' all'altra.
struct CollisionGrid
{
    uint8_t data[PIAZZA_WIDTH * PIAZZA_HEIGHT];
};

[[nodiscard]] consteval CollisionGrid make_piazza_grid()
{
    CollisionGrid grid{};

    for(int y = 0; y < PIAZZA_HEIGHT; ++y)
    {
        for(int x = 0; x < PIAZZA_WIDTH; ++x)
        {
            grid.data[x + y * PIAZZA_WIDTH] = get_tile_type(x, y);
        }
    }

    return grid;
}

inline constexpr CollisionGrid PIAZZA_GRID = make_piazza_grid();

// Che la derivazione sia avvenuta davvero, e nel verso giusto, e' verificato dal compilatore su
// punti notevoli — non asserito in un documento.
static_assert(PIAZZA_GRID.data[32 + 18 * PIAZZA_WIDTH] == uint8_t(TileType::DOOR_CONSOLI),
              "Portone dei Consoli assente dalla griglia derivata");
static_assert(PIAZZA_GRID.data[0 + 39 * PIAZZA_WIDTH] == uint8_t(TileType::RAILING),
              "Ringhiera sud assente dalla griglia derivata");
static_assert(PIAZZA_GRID.data[32 + 30 * PIAZZA_WIDTH] == uint8_t(TileType::GROUND),
              "Il centro della piazza non e' calpestabile");
static_assert(PIAZZA_GRID.data[23 + 24 * PIAZZA_WIDTH] == uint8_t(TileType::FOUNTAIN),
              "Fontana dei Matti assente dalla griglia derivata");
static_assert(sizeof(CollisionGrid) == PIAZZA_WIDTH * PIAZZA_HEIGHT,
              "La griglia deve restare un blocco contiguo di byte");

// La conversione pixel -> tile deve concordare con la griglia, altrimenti il giocatore
// collide contro qualcosa che non e' dove crede.
static_assert(get_tile_type_px(32 * TILE_SIZE_PX + 7, 18 * TILE_SIZE_PX + 7) ==
                  uint8_t(TileType::DOOR_CONSOLI),
              "get_tile_type_px non concorda con get_tile_type sull'ultimo pixel del tile");
static_assert(get_tile_type_px(-1, 30 * TILE_SIZE_PX) == uint8_t(TileType::WALL),
              "Un pixel fuori dal bordo sinistro deve essere muro, non suolo libero");

} // namespace gubbio::maps

#endif // PIAZZA_GRANDE_COLLISION_H
