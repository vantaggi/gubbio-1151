#ifndef SANT_ANDREA_COLLISION_H
#define SANT_ANDREA_COLLISION_H

#include <stdint.h>

#include "piazza_grande_collision.h"   // per TileType, is_solid, is_transition, TILE_SIZE_PX

namespace gubbio::maps {

// QUARTIERE DI SANT'ANDREA — il quartiere orientale, quota 55 m (docs/mappa_del_mondo.md sez. 2).
//
// Non ha un monumento maggiore: e' tessuto edilizio minore, case-torre e vicoli stretti, e il
// carattere e' il tessuto stesso, denso. Un solo confine noto (docs/mappa_del_mondo.md sez. 1):
// Sant'Agostino a OVEST. Non essendoci un secondo vicino, l'area e' un ramo del quartiere che si
// richiude su se stessa: un corridoio d'ingresso, una piccola piazzetta (il campiello) e tre
// vicoli ciechi che si diramano da essa, murati in fondo dal tessuto edilizio.
//
// MISURE. 32x32 tile, cioe' 256x256 px: un BG regolare legale (256 o 512, mai una via di mezzo),
// come Largo del Bargello. Alla scala di 1,5 m/tile (city_reference.h) sono 48x48 metri: un
// quartiere minore, non una piazza.

constexpr int SANT_ANDREA_WIDTH  = 32;   // tile. x cresce verso NORD
constexpr int SANT_ANDREA_HEIGHT = 32;   // tile. y cresce verso EST
constexpr int SANT_ANDREA_QUOTA_M = 55;  // metri sopra Piazza Quaranta Martiri (sez. 2 del contratto)

constexpr int SANT_ANDREA_WIDTH_PX  = SANT_ANDREA_WIDTH * TILE_SIZE_PX;   // 256
constexpr int SANT_ANDREA_HEIGHT_PX = SANT_ANDREA_HEIGHT * TILE_SIZE_PX;  // 256

// --- LA DISPOSIZIONE, E IL SUO ORIENTAMENTO --------------------------------------------------
//
// Uguale a tutte le aree (docs/mappa_del_mondo.md sez. 3): ALTO SCHERMO = OVEST reale, BASSO
// SCHERMO = EST reale, SINISTRA SCHERMO = SUD reale, DESTRA SCHERMO = NORD reale.
//
// Sant'Agostino sta a OVEST (sez. 1 del contratto: "Sant'Agostino -> Sant'Andrea verso est"),
// quindi in questa mappa l'OVEST e' ALTO: il corridoio d'ingresso nasce dal bordo y=0 e scende
// (y crescente) verso l'interno del quartiere. Non c'e' un secondo vicino: gli altri tre lati
// sono tessuto edilizio chiuso, non varchi.
//
//        ALTO SCHERMO (y piccola)   = OVEST reale  -> ingresso da Sant'Agostino
//        BASSO SCHERMO (y grande)   = EST reale    -> case-torri, nessuna uscita
//        SINISTRA SCHERMO (x piccola) = SUD reale  -> case-torri, nessuna uscita
//        DESTRA SCHERMO (x grande)  = NORD reale   -> case-torri, nessuna uscita

// Il corridoio d'ingresso: 4 tile di larghezza, come un vicolo principale. Il tile a y=0 e' il
// varco vero e proprio (si esce verso Sant'Agostino); da y=1 a y=9 e' semplice ciottolato.
constexpr int SANT_ANDREA_CORRIDOIO_FIRST_X = 14;
constexpr int SANT_ANDREA_CORRIDOIO_LAST_X  = 17;
constexpr int SANT_ANDREA_CORRIDOIO_LAST_Y  = 9;

// Il campiello: la piccola piazzetta interna su cui il corridoio si apre, e da cui si diramano
// i tre vicoli. Non e' un monumento: e' solo lo spiazzo dove il tessuto si allarga un poco.
constexpr int SANT_ANDREA_CAMPIELLO_FIRST_X = 10;
constexpr int SANT_ANDREA_CAMPIELLO_LAST_X  = 21;
constexpr int SANT_ANDREA_CAMPIELLO_FIRST_Y = 10;
constexpr int SANT_ANDREA_CAMPIELLO_LAST_Y  = 14;

// Vicolo verso SUD (x decrescente): si stacca dal lato sinistro del campiello e finisce contro
// il tessuto edilizio, cieco. Rappresenta la densita' del quartiere: non ogni vicolo porta da
// qualche parte.
constexpr int SANT_ANDREA_VICOLO_SUD_FIRST_X = 4;
constexpr int SANT_ANDREA_VICOLO_SUD_LAST_X  = 9;
constexpr int SANT_ANDREA_VICOLO_SUD_FIRST_Y = 11;
constexpr int SANT_ANDREA_VICOLO_SUD_LAST_Y  = 12;

// Vicolo verso NORD (x crescente): si stacca dal lato destro del campiello, cieco anch'esso.
constexpr int SANT_ANDREA_VICOLO_NORD_FIRST_X = 22;
constexpr int SANT_ANDREA_VICOLO_NORD_LAST_X  = 27;
constexpr int SANT_ANDREA_VICOLO_NORD_FIRST_Y = 11;
constexpr int SANT_ANDREA_VICOLO_NORD_LAST_Y  = 12;

// Vicolo verso EST (y crescente): si stacca dal lato basso del campiello, il piu' lungo dei tre,
// e finisce anch'esso contro il tessuto edilizio che chiude il quartiere a est.
constexpr int SANT_ANDREA_VICOLO_EST_FIRST_X = 14;
constexpr int SANT_ANDREA_VICOLO_EST_LAST_X  = 15;
constexpr int SANT_ANDREA_VICOLO_EST_FIRST_Y = 15;
constexpr int SANT_ANDREA_VICOLO_EST_LAST_Y  = 24;

// Dove il giocatore compare arrivando da Sant'Agostino: un passo dentro il corridoio, non sul
// varco stesso, cosi' da non ritrovarsi immediatamente sopra il trigger che lo farebbe tornare
// indietro. E' l'unico INGRESSO_DA_*, perche' Sant'Andrea ha un solo vicino (sez. 1 del
// contratto).
constexpr int SANT_ANDREA_INGRESSO_DA_SANT_AGOSTINO_X = 15;
    // OTTO tile dentro, non uno: il contratto (docs/mappa_del_mondo.md sez. 5) impone almeno
    // sei di margine dal proprio varco. Quest'area e' stata autorata PRIMA che quella regola
    // esistesse, e l'autotest ha misurato il difetto che la regola previene: qualche frame
    // residuo di spinta nella direzione d'arrivo, e il giocatore rientra da dove e' appena
    // uscito. Nel giro completo dell'anello il risultato era prendere la strada sbagliata.
constexpr int SANT_ANDREA_INGRESSO_DA_SANT_AGOSTINO_Y = 8;

// USCITA 4 -> Sant'Agostino, verso OVEST. Il valore numerico e' quello di EXIT_SAN_MARTINO in
// piazza_grande_collision.h: le uscite non sanno dove portano (docs/mappa_del_mondo.md sez. 5),
// e' MAPS[] in map_data.h a deciderlo. Qui si dichiara solo che il tile 4 esiste e dove.
[[nodiscard]] inline constexpr uint8_t sant_andrea_tile_type(int x, int y)
{
    if(x < 0 || x >= SANT_ANDREA_WIDTH || y < 0 || y >= SANT_ANDREA_HEIGHT)
    {
        return uint8_t(TileType::WALL);
    }

    // Il corridoio d'ingresso, con il varco verso Sant'Agostino al bordo ovest (y=0).
    if(x >= SANT_ANDREA_CORRIDOIO_FIRST_X && x <= SANT_ANDREA_CORRIDOIO_LAST_X && y <= SANT_ANDREA_CORRIDOIO_LAST_Y)
    {
        if(y == 0)
        {
            return uint8_t(TileType::EXIT_SAN_MARTINO);   // valore 4: USCITA verso Sant'Agostino
        }

        return uint8_t(TileType::ROAD);
    }

    // Il campiello: spiazzo aperto, non ciottolato di passaggio.
    if(x >= SANT_ANDREA_CAMPIELLO_FIRST_X && x <= SANT_ANDREA_CAMPIELLO_LAST_X &&
       y >= SANT_ANDREA_CAMPIELLO_FIRST_Y && y <= SANT_ANDREA_CAMPIELLO_LAST_Y)
    {
        return uint8_t(TileType::GROUND);
    }

    // I tre vicoli ciechi che si diramano dal campiello.
    if(x >= SANT_ANDREA_VICOLO_SUD_FIRST_X && x <= SANT_ANDREA_VICOLO_SUD_LAST_X &&
       y >= SANT_ANDREA_VICOLO_SUD_FIRST_Y && y <= SANT_ANDREA_VICOLO_SUD_LAST_Y)
    {
        return uint8_t(TileType::ROAD);
    }

    if(x >= SANT_ANDREA_VICOLO_NORD_FIRST_X && x <= SANT_ANDREA_VICOLO_NORD_LAST_X &&
       y >= SANT_ANDREA_VICOLO_NORD_FIRST_Y && y <= SANT_ANDREA_VICOLO_NORD_LAST_Y)
    {
        return uint8_t(TileType::ROAD);
    }

    if(x >= SANT_ANDREA_VICOLO_EST_FIRST_X && x <= SANT_ANDREA_VICOLO_EST_LAST_X &&
       y >= SANT_ANDREA_VICOLO_EST_FIRST_Y && y <= SANT_ANDREA_VICOLO_EST_LAST_Y)
    {
        return uint8_t(TileType::ROAD);
    }

    // Tutto il resto e' tessuto edilizio minore: le case-torri, fitte, che chiudono il quartiere
    // sugli altri tre lati. Non c'e' un secondo vicino: qui non ci sono varchi.
    return uint8_t(TileType::WALL);
}

// Griglia materializzata in ROM, come PIAZZA_GRID e BARGELLO_GRID.
struct SantAndreaGrid
{
    uint8_t data[SANT_ANDREA_WIDTH * SANT_ANDREA_HEIGHT];
};

[[nodiscard]] consteval SantAndreaGrid make_sant_andrea_grid()
{
    SantAndreaGrid grid{};

    for(int y = 0; y < SANT_ANDREA_HEIGHT; ++y)
    {
        for(int x = 0; x < SANT_ANDREA_WIDTH; ++x)
        {
            grid.data[x + y * SANT_ANDREA_WIDTH] = sant_andrea_tile_type(x, y);
        }
    }

    return grid;
}

inline constexpr SantAndreaGrid SANT_ANDREA_GRID = make_sant_andrea_grid();

// --- static_assert obbligatorie (docs/mappa_del_mondo.md sez. 5) ------------------------------

// 1. Ogni uscita dichiarata esiste davvero nella griglia ed e' calpestabile.
static_assert(SANT_ANDREA_GRID.data[15 + 0 * SANT_ANDREA_WIDTH] ==
                  uint8_t(TileType::EXIT_SAN_MARTINO),
              "L'uscita verso Sant'Agostino deve stare sul bordo ovest (y=0)");
static_assert(! is_solid(SANT_ANDREA_GRID.data[15 + 0 * SANT_ANDREA_WIDTH]),
              "L'uscita verso Sant'Agostino non e' calpestabile");
static_assert(is_transition(SANT_ANDREA_GRID.data[15 + 0 * SANT_ANDREA_WIDTH]),
              "Il tile dell'uscita deve essere riconosciuto come trigger di cambio scena");

// 2. Ogni INGRESSO_DA_* cade su un tile calpestabile.
static_assert(! is_solid(SANT_ANDREA_GRID.data[SANT_ANDREA_INGRESSO_DA_SANT_AGOSTINO_X +
                                                SANT_ANDREA_INGRESSO_DA_SANT_AGOSTINO_Y * SANT_ANDREA_WIDTH]),
              "INGRESSO_DA_SANT_AGOSTINO cade dentro un muro: il giocatore ci resterebbe chiuso");

// 3. Almeno un punto notevole per ogni lato, con un messaggio che fissa l'orientamento. Sant'Andrea
// non ha monumenti: i punti notevoli sono il varco (unico, a ovest) e il tessuto murario chiuso
// sugli altri tre lati.
static_assert(SANT_ANDREA_GRID.data[15 + 0 * SANT_ANDREA_WIDTH] ==
                  uint8_t(TileType::EXIT_SAN_MARTINO),
              "ALTO SCHERMO = OVEST reale: e' li' che deve stare l'unico varco, verso Sant'Agostino");
static_assert(SANT_ANDREA_GRID.data[4 + 31 * SANT_ANDREA_WIDTH] == uint8_t(TileType::WALL),
              "BASSO SCHERMO = EST reale: qui il tessuto edilizio chiude il quartiere, nessuna uscita");
static_assert(SANT_ANDREA_GRID.data[0 + 16 * SANT_ANDREA_WIDTH] == uint8_t(TileType::WALL),
              "SINISTRA SCHERMO = SUD reale: qui il tessuto edilizio chiude il quartiere, nessuna uscita");
static_assert(SANT_ANDREA_GRID.data[31 + 16 * SANT_ANDREA_WIDTH] == uint8_t(TileType::WALL),
              "DESTRA SCHERMO = NORD reale: qui il tessuto edilizio chiude il quartiere, nessuna uscita");

// Guardia contro il ribaltamento (docs/mappa_del_mondo.md sez. 3): il varco sta SOLO sul bordo
// ovest. Se ovest e est fossero scambiati per errore, questo assert cadrebbe mentre la mappa
// continuerebbe comunque a compilare — che e' esattamente il difetto gia' capitato una volta.
static_assert(SANT_ANDREA_GRID.data[15 + 31 * SANT_ANDREA_WIDTH] != uint8_t(TileType::EXIT_SAN_MARTINO),
              "Il bordo est non puo' avere lo stesso varco del bordo ovest: sarebbe un ribaltamento");

// 4. Nessun monumento e' dichiarato in quest'area (e' tessuto minore, non un edificio maggiore):
// respects_scale() di city_reference.h non si applica qui perche' non c'e' nulla da misurare.

// Sanita' del percorso: il campiello dev'essere raggiungibile e calpestabile, e i tre vicoli
// devono aderire ai suoi bordi senza lasciare un muro fra loro e il campiello.
static_assert(SANT_ANDREA_GRID.data[15 + 12 * SANT_ANDREA_WIDTH] == uint8_t(TileType::GROUND),
              "Il centro del campiello deve essere aperto");
static_assert(! is_solid(SANT_ANDREA_GRID.data[9 + 11 * SANT_ANDREA_WIDTH]),
              "Il vicolo sud deve aderire al campiello, non staccarsene con un muro");
static_assert(! is_solid(SANT_ANDREA_GRID.data[22 + 11 * SANT_ANDREA_WIDTH]),
              "Il vicolo nord deve aderire al campiello, non staccarsene con un muro");
static_assert(! is_solid(SANT_ANDREA_GRID.data[14 + 15 * SANT_ANDREA_WIDTH]),
              "Il vicolo est deve aderire al campiello, non staccarsene con un muro");
static_assert(sizeof(SantAndreaGrid) == SANT_ANDREA_WIDTH * SANT_ANDREA_HEIGHT,
              "La griglia deve restare un blocco contiguo di byte");

} // namespace gubbio::maps

#endif // SANT_ANDREA_COLLISION_H
