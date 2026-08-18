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
    FOUNTAIN          = 6,   // Fontana dei Matti: interazione (Patente da Matto)

    // Aggiunti nella Sessione 16, applicando la regola dell'illusione (city_reference.h): gli
    // EDIFICI stanno in scala anche quando le distanze sono compresse. Prima la fascia nord era
    // muro indistinto, e il palazzo simbolo della citta' non si distingueva da un magazzino.
    CONSOLI_FACADE    = 7,   // fronte del Palazzo dei Consoli: 33 m = 22 tile, in scala
    PRETORIO_FACADE   = 8,   // Palazzo Pretorio, che gli sta di fronte: 25 m = 16 tile
    STAIRS            = 9,   // scalinata a ventaglio davanti al portone: si calpesta
    DOOR_PRETORIO     = 10   // ingresso del Pretorio: oggi solo VISIVO, non porta altrove
};

// I lati corti. Piazza Grande e' uno spazio CHIUSO su quattro lati, ed e' da li' che viene
// l'effetto che fa: un vuoto vasto ritagliato dentro un tessuto urbano fitto. Finche' i lati
// corti restavano aperti, la piazza sfumava nel nulla e sembrava un cortile. Restano liberi solo
// i due varchi dei trigger, che nella citta' vera sono passaggi voltati.
constexpr int SIDE_WEST_LAST_X = 3;
constexpr int SIDE_EAST_FIRST_X = 60;
constexpr int SIDE_FIRST_Y = 23;      // sotto il corridoio dei varchi (y 19-22)
constexpr int SIDE_LAST_Y = 37;       // sopra la ringhiera

// Il fronte dei Consoli, centrato sul portone. La larghezza NON e' scelta a occhio: e' quella
// che la scala impone (vedi city_reference.h), ed e' l'unico modo perche' il palazzo resti
// riconoscibile in una piazza accorciata di un quarto.
constexpr int CONSOLI_FIRST_X = 21;
constexpr int CONSOLI_LAST_X = 42;      // 22 tile
constexpr int PRETORIO_FIRST_X = 24;
constexpr int PRETORIO_LAST_X = 39;     // 16 tile
constexpr int PRETORIO_FIRST_Y = 34;
constexpr int PRETORIO_LAST_Y = 37;

inline constexpr uint8_t get_tile_type(int x, int y) {
    if (x < 0 || x >= PIAZZA_WIDTH || y < 0 || y >= PIAZZA_HEIGHT) return 1; // Fuori mappa = muro

    // Ringhiera sud
    if (y >= 38) return 2;

    // Palazzo Pretorio: fronteggia i Consoli dal lato opposto della piazza, come nella citta'
    // vera. Sta davanti alla ringhiera, non al posto suo.
    if (y >= PRETORIO_FIRST_Y && y <= PRETORIO_LAST_Y &&
        x >= PRETORIO_FIRST_X && x <= PRETORIO_LAST_X) {
        // Ingresso sul fronte che guarda la piazza. Non e' ancora un trigger: aprirlo vorrebbe
        // dire una quarta regola in MAPS[], e le sale del Pretorio non esistono. Disegnarlo
        // adesso costa un tile e rende il palazzo un edificio invece di un blocco cieco.
        if (y == PRETORIO_FIRST_Y && (x == 31 || x == 32)) return 10;
        return 8;
    }

    // Fronte nord: il Palazzo dei Consoli al centro, edifici minori ai lati.
    if (y <= 18) {
        if (y == 18 && (x == 32 || x == 33)) return 3; // Portone Consoli
        if (x >= CONSOLI_FIRST_X && x <= CONSOLI_LAST_X) return 7;
        return 1;
    }

    // Scalinata a ventaglio davanti al portone: calpestabile, ed e' il primo dei tre segni
    // distintivi del palazzo (docs/riferimenti/FONTI.md).
    if (y == 19 && x >= 29 && x <= 34) return 9;

    // Lati corti edificati: chiudono la piazza a est e a ovest, lasciando liberi i varchi.
    if (y >= SIDE_FIRST_Y && y <= SIDE_LAST_Y &&
        (x <= SIDE_WEST_LAST_X || x >= SIDE_EAST_FIRST_X)) return 1;

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
    return tile == uint8_t(TileType::WALL) || tile == uint8_t(TileType::RAILING) ||
           tile == uint8_t(TileType::CONSOLI_FACADE) || tile == uint8_t(TileType::PRETORIO_FACADE);
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
// Il fronte del palazzo deve misurare in griglia esattamente i 22 tile che la scala impone: se
// qualcuno lo allargasse "perche' sta meglio", l'illusione si romperebbe proprio sull'edificio
// che la regge.
static_assert([]
{
    int larghezza = 0;

    for(int x = 0; x < PIAZZA_WIDTH; ++x)
    {
        const uint8_t t = PIAZZA_GRID.data[x + 17 * PIAZZA_WIDTH];

        if(t == uint8_t(TileType::CONSOLI_FACADE))
        {
            ++larghezza;
        }
    }

    return larghezza == 22;
}(), "Il fronte del Palazzo dei Consoli non misura i 22 tile della scala");

// La piazza dev'essere CHIUSA: sui bordi laterali, fuori dai varchi, non puo' esserci suolo
// libero — altrimenti si cammina fuori dallo spazio urbano e l'illusione cade.
static_assert([]
{
    for(int y = SIDE_FIRST_Y; y <= SIDE_LAST_Y; ++y)
    {
        if(PIAZZA_GRID.data[0 + y * PIAZZA_WIDTH] == uint8_t(TileType::GROUND) ||
           PIAZZA_GRID.data[PIAZZA_WIDTH - 1 + y * PIAZZA_WIDTH] == uint8_t(TileType::GROUND))
        {
            return false;
        }
    }

    return true;
}(), "I lati corti della piazza non sono chiusi");

// I due varchi restano percorribili: chiudere la piazza non deve murare le uscite.
static_assert(! is_solid(PIAZZA_GRID.data[0 + 20 * PIAZZA_WIDTH]) &&
              ! is_solid(PIAZZA_GRID.data[62 + 20 * PIAZZA_WIDTH]),
              "Un varco laterale e' stato murato");

static_assert(PIAZZA_GRID.data[31 + 34 * PIAZZA_WIDTH] == uint8_t(TileType::DOOR_PRETORIO),
              "Manca l'ingresso del Palazzo Pretorio");

static_assert(PIAZZA_GRID.data[32 + 19 * PIAZZA_WIDTH] == uint8_t(TileType::STAIRS),
              "Manca la scalinata davanti al portone dei Consoli");
static_assert(! is_solid(uint8_t(TileType::STAIRS)), "La scalinata deve essere calpestabile");

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
