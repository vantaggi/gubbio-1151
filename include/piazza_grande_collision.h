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
    FOUNTAIN          = 6,   // Fontana dei Matti: sta in Largo del Bargello, NON in piazza

    // Aggiunti nella Sessione 16, applicando la regola dell'illusione (city_reference.h): gli
    // EDIFICI stanno in scala anche quando le distanze sono compresse. Prima la fascia nord era
    // muro indistinto, e il palazzo simbolo della citta' non si distingueva da un magazzino.
    CONSOLI_FACADE    = 7,   // fronte del Palazzo dei Consoli: 33 m = 22 tile, in scala
    PRETORIO_FACADE   = 8,   // Palazzo Pretorio, che gli sta di fronte: 25 m = 16 tile
    STAIRS            = 9,   // scalinata a ventaglio davanti al portone: si calpesta
    DOOR_PRETORIO     = 10,  // ingresso del Pretorio: oggi solo VISIVO, non porta altrove
    ROAD              = 11   // ciottolato: via dei Consoli / via XX Settembre, a nord
};

// --- LA DISPOSIZIONE DELLA PIAZZA, E IL SUO ORIENTAMENTO ------------------------------------
//
// Disposizione reale (correzione del committente, Sessione 19): **Palazzo dei Consoli a OVEST**,
// **Pretorio a EST**, i due che si fronteggiano; a **nord** la strada in ciottolato dove via dei
// Consoli si unisce a via XX Settembre, e oltre il Palazzo Ranghiasci; a **sud** il muretto sul
// vuoto, perche' la piazza e' PENSILE, sospesa sopra gli Arconi.
//
// **LA MAPPA NON E' ORIENTATA A NORD: e' orientata a OVEST**, per scelta del committente.
// Ruotando di novanta gradi, in gioco si vede cosi':
//
//        ALTO SCHERMO = OVEST reale        -> PALAZZO DEI CONSOLI
//        BASSO SCHERMO = EST reale         -> PALAZZO PRETORIO
//        SINISTRA SCHERMO = NORD reale     -> ciottolato, via dei Consoli e via XX Settembre
//        DESTRA SCHERMO = SUD reale        -> muretto sul vuoto, e sotto gli Arconi
//
// Non e' un compromesso di comodo: mette i due palazzi che si fronteggiano sui lati LUNGHI della
// mappa, dove ci stanno alla loro scala — 22 tile i Consoli, 16 il Pretorio — e lascia le facciate
// fotografate orizzontali, come sono state riprese. Con l'orientamento a nord avrebbero dovuto
// essere ruotate, perdendo la ragione per cui le si e' fotografate frontali.
//
// La regola delle adiacenze di `city_reference.h` resta rispettata: cambia l'orientamento della
// vista, non l'ordine in cui le cose si incontrano.
constexpr int CONSOLI_LAST_Y = 18;       // fascia alta: il palazzo, cioe' OVEST
constexpr int PRETORIO_FIRST_Y = 34;     // fascia bassa: il Pretorio, cioe' EST
constexpr int ROAD_LAST_X = 4;           // fascia sinistra: il ciottolato, cioe' NORD
constexpr int RAILING_FIRST_X = 60;      // fascia destra: il muretto, cioe' SUD

// Fronti in scala (city_reference.h): 33 m = 22 tile per i Consoli, 25 m = 16 per il Pretorio.
constexpr int CONSOLI_FIRST_X = 21;
constexpr int CONSOLI_LAST_X = 42;
constexpr int PRETORIO_FIRST_X = 26;
constexpr int PRETORIO_LAST_X = 41;


inline constexpr uint8_t get_tile_type(int x, int y) {
    if (x < 0 || x >= PIAZZA_WIDTH || y < 0 || y >= PIAZZA_HEIGHT) return 1; // Fuori mappa = muro

    // DESTRA = SUD: il muretto sul vuoto, con gli Arconi sotto.
    if (x >= RAILING_FIRST_X) return 2;

    // SINISTRA = NORD: la strada in ciottolato. Via dei Consoli entra dall'angolo verso i
    // Consoli, via XX Settembre esce dall'angolo verso il Pretorio: sono gli imbocchi
    // nord-ovest e nord-est della piazza vera.
    if (x <= ROAD_LAST_X) {
        if (y <= 8) return 4;                        // via dei Consoli (nord-ovest)
        if (y >= PIAZZA_HEIGHT - 9) return 5;        // via XX Settembre (nord-est)
        return 11;                                   // ciottolato percorribile
    }

    // ALTO = OVEST: Palazzo dei Consoli, col portone al centro del fronte.
    if (y <= CONSOLI_LAST_Y) {
        if (y == CONSOLI_LAST_Y && (x == 31 || x == 32)) return 3;
        if (x >= CONSOLI_FIRST_X && x <= CONSOLI_LAST_X) return 7;
        return 1;                                    // edificato minore ai lati
    }

    // La scalinata a ventaglio, sul selciato davanti al portone.
    if (y == CONSOLI_LAST_Y + 1 && x >= 29 && x <= 34) return 9;

    // BASSO = EST: Palazzo Pretorio, che fronteggia i Consoli.
    if (y >= PRETORIO_FIRST_Y) {
        if (x >= PRETORIO_FIRST_X && x <= PRETORIO_LAST_X) {
            // 31 e 32, non 33 e 34: il portale ad arco della fotografia cade a cinque tile
            // dall'angolo della fascia, non a otto. Finche' i due numeri non coincidono, il
            // giocatore preme A davanti a un muro dipinto e la porta e' altrove.
            if (y == PRETORIO_FIRST_Y && (x == 31 || x == 32)) return 10;
            return 8;
        }

        return 1;
    }

    return 0; // selciato in cotto a lisca di pesce
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
    // ROAD e STAIRS non sono solidi: si cammina sul ciottolato e si sale la scalinata.
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

// Punti notevoli della disposizione, verificati dal compilatore. Sono anche la documentazione
// eseguibile dell'orientamento: se qualcuno ruotasse di nuovo la mappa, si fermerebbe qui.
static_assert(PIAZZA_GRID.data[31 + CONSOLI_LAST_Y * PIAZZA_WIDTH] == uint8_t(TileType::DOOR_CONSOLI),
              "Il portone dei Consoli non e' al centro del fronte");
static_assert(PIAZZA_GRID.data[62 + 20 * PIAZZA_WIDTH] == uint8_t(TileType::RAILING),
              "Il muretto sul vuoto deve stare a DESTRA (sud reale)");
static_assert(PIAZZA_GRID.data[2 + 20 * PIAZZA_WIDTH] == uint8_t(TileType::ROAD),
              "Il ciottolato deve stare a SINISTRA (nord reale)");
static_assert(PIAZZA_GRID.data[2 + 2 * PIAZZA_WIDTH] == uint8_t(TileType::EXIT_SAN_MARTINO),
              "Via dei Consoli sbocca verso il Palazzo dei Consoli");
static_assert(PIAZZA_GRID.data[2 + 36 * PIAZZA_WIDTH] == uint8_t(TileType::EXIT_PORTA_ROMANA),
              "Via XX Settembre sbocca verso il Pretorio");
static_assert(PIAZZA_GRID.data[32 + 10 * PIAZZA_WIDTH] == uint8_t(TileType::CONSOLI_FACADE),
              "Il Palazzo dei Consoli sta in ALTO (ovest reale)");
static_assert(PIAZZA_GRID.data[32 + 36 * PIAZZA_WIDTH] == uint8_t(TileType::PRETORIO_FACADE),
              "Il Palazzo Pretorio sta in BASSO (est reale), di fronte ai Consoli");
static_assert(PIAZZA_GRID.data[32 + 25 * PIAZZA_WIDTH] == uint8_t(TileType::GROUND),
              "Il centro della piazza non e' calpestabile");
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
