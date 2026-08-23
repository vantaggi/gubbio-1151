#ifndef SANT_AGOSTINO_COLLISION_H
#define SANT_AGOSTINO_COLLISION_H

#include <stdint.h>

#include "piazza_grande_collision.h"   // per TileType, is_solid, is_transition, TILE_SIZE_PX
#include "city_reference.h"            // per respects_scale(): la chiesa e' un monumento nominato

namespace gubbio::maps {

// ZONA DI SANT'AGOSTINO — quartiere orientale, presso Porta Romana, quota 60 m
// (docs/mappa_del_mondo.md sez. 2). Il monumento e' la CHIESA DI SANT'AGOSTINO: impianto
// duecentesco, gotica, pietra chiara, navata unica con abside affrescata. Uno slargo si apre
// davanti al suo fronte.
//
// DUE VICINI VERI (docs/mappa_del_mondo.md sez. 1): via XX Settembre a OVEST ("Piazza Grande |
// Sant'Agostino | via XX Settembre, dal varco nord-est") e Sant'Andrea a EST ("Sant'Agostino |
// Sant'Andrea | verso est"). E' quindi un'area DI PASSAGGIO, come via XX Settembre, non un ramo
// cieco come Sant'Andrea o Largo del Bargello.
//
// LA FORMA: NON e' un corridoio dritto che attraversa la chiesa — un corridoio a fondo chiuso
// bloccherebbe il transito, dato che la facciata occupa quasi tutta la larghezza disponibile.
// Si riprende invece lo schema di piazza_grande_collision.h, che e' il modello da seguire: una
// STRADA che corre lungo il fianco NORD (destra schermo, x alta) dall'imbocco ovest fino allo
// sbocco est SENZA dover attraversare l'edificio, e uno SLARGO interno (x bassa) dove sta la
// chiesa, raggiungibile dalla strada senza che l'attraversamento sia obbligato.
//
// MISURE. 32x64 tile, cioe' 256x512 px: un BG regolare legale, la stessa forma di Piazza Grande
// e di via XX Settembre. Alla scala di 1,5 m/tile (city_reference.h) sono 48x96 metri.

constexpr int SANT_AGOSTINO_WIDTH  = 32;   // tile. x cresce verso NORD
constexpr int SANT_AGOSTINO_HEIGHT = 64;   // tile. y cresce verso EST
constexpr int SANT_AGOSTINO_QUOTA_M = 60;  // metri sopra Piazza Quaranta Martiri (sez. 2 del contratto)

constexpr int SANT_AGOSTINO_WIDTH_PX  = SANT_AGOSTINO_WIDTH * TILE_SIZE_PX;    // 256
constexpr int SANT_AGOSTINO_HEIGHT_PX = SANT_AGOSTINO_HEIGHT * TILE_SIZE_PX;   // 512

// --- LA DISPOSIZIONE, E IL SUO ORIENTAMENTO --------------------------------------------------
//
// Uguale a tutte le aree (docs/mappa_del_mondo.md sez. 3): ALTO SCHERMO = OVEST reale, BASSO
// SCHERMO = EST reale, SINISTRA SCHERMO = SUD reale, DESTRA SCHERMO = NORD reale.
//
//        ALTO SCHERMO (y piccola)     = OVEST reale  -> imbocco dalla strada, verso via XX Settembre
//        BASSO SCHERMO (y grande)     = EST reale     -> sbocco dalla strada, verso Sant'Andrea
//        SINISTRA SCHERMO (x piccola) = SUD reale     -> tessuto edilizio minore, chiuso
//        DESTRA SCHERMO (x grande)    = NORD reale     -> la strada di passaggio, poi il fronte
//                                                          edificato oltre di essa
//
// La strada corre sul fianco NORD (x alta): e' il ciottolato che porta i due varchi, come il
// ciottolato di Piazza Grande porta via dei Consoli e via XX Settembre sullo stesso fianco.
constexpr int SANT_AGOSTINO_ROAD_FIRST_X = 27;
// Il fronte edificato oltre la strada, che la chiude sul lato esterno: senza, la carreggiata
// finirebbe contro il bordo invisibile della mappa (stesso ragionamento di piazza_grande_collision.h).
constexpr int SANT_AGOSTINO_NORTH_FRONT_X = 31;

// La facciata della chiesa, in scala: 15 m reali danno 10 tile (city_reference.h::tiles_from_meters),
// una chiesa a navata unica, modesta rispetto ai palazzi civici. Comincia dal bordo y=0: quel
// bordo, sul fianco SLARGO (x < ROAD_FIRST_X), non porta a nessuna area — l'unico varco vero
// verso via XX Settembre sta sulla strada, a x >= ROAD_FIRST_X.
constexpr int SANT_AGOSTINO_CHIESA_FACADE_FIRST_X = 9;
constexpr int SANT_AGOSTINO_CHIESA_FACADE_LAST_X  = 18;   // 10 tile = 15 m, in scala
constexpr int SANT_AGOSTINO_CHIESA_FACADE_LAST_Y  = 18;

// La breve scalinata davanti al portale, come in piazza_grande_collision.h.
constexpr int SANT_AGOSTINO_SCALINATA_CHIESA_FIRST_X = 13;
constexpr int SANT_AGOSTINO_SCALINATA_CHIESA_LAST_X  = 14;
constexpr int SANT_AGOSTINO_SCALINATA_CHIESA_Y = SANT_AGOSTINO_CHIESA_FACADE_LAST_Y + 1;   // 19

// Lo slargo davanti alla chiesa: si apre subito dopo la facciata e confina con la strada
// (SLARGO_LAST_X = ROAD_FIRST_X - 1), cosi' che il giocatore possa raggiungerla senza dover
// passare per forza davanti al portale.
constexpr int SANT_AGOSTINO_SLARGO_FIRST_X = 2;
constexpr int SANT_AGOSTINO_SLARGO_LAST_X  = SANT_AGOSTINO_ROAD_FIRST_X - 1;   // 26
constexpr int SANT_AGOSTINO_SLARGO_FIRST_Y = SANT_AGOSTINO_SCALINATA_CHIESA_Y;  // 19
constexpr int SANT_AGOSTINO_SLARGO_LAST_Y  = 40;

// Dove il giocatore compare arrivando da via XX Settembre: sulla strada, ben oltre la fascia
// dell'uscita 4 (y<=8), cosi' da non ritrovarsi subito sopra il trigger che lo farebbe tornare
// indietro (docs/mappa_del_mondo.md, regola del ciclo di transizione).
constexpr int SANT_AGOSTINO_INGRESSO_DA_VIA_XX_SETTEMBRE_X = 28;
constexpr int SANT_AGOSTINO_INGRESSO_DA_VIA_XX_SETTEMBRE_Y = 16;

// Dove il giocatore compare arrivando da Sant'Andrea: sulla strada, ben prima della fascia
// dell'uscita 5 (y >= HEIGHT-9), con lo stesso criterio.
constexpr int SANT_AGOSTINO_INGRESSO_DA_SANT_ANDREA_X = 28;
constexpr int SANT_AGOSTINO_INGRESSO_DA_SANT_ANDREA_Y = 47;

// Le uscite non sanno dove portano (docs/mappa_del_mondo.md sez. 5): qui si dichiara solo che i
// tile 4 e 5 esistono e dove. E' MAPS[] in map_data.h a collegarli a via XX Settembre e Sant'Andrea.
// USCITA 4 (valore di TileType::EXIT_SAN_MARTINO, riusato) -> via XX Settembre, verso OVEST.
// USCITA 5 (valore di TileType::EXIT_PORTA_ROMANA, riusato) -> Sant'Andrea, verso EST.
[[nodiscard]] inline constexpr uint8_t sant_agostino_tile_type(int x, int y)
{
    if(x < 0 || x >= SANT_AGOSTINO_WIDTH || y < 0 || y >= SANT_AGOSTINO_HEIGHT)
    {
        return uint8_t(TileType::WALL);
    }

    // Oltre la strada, il fronte edificato che la chiude sul lato esterno.
    if(x >= SANT_AGOSTINO_NORTH_FRONT_X)
    {
        return uint8_t(TileType::WALL);
    }

    // DESTRA SCHERMO = NORD reale: la strada che passa davanti allo slargo, e collega i due
    // varchi senza attraversare la chiesa. Stesso schema del ciottolato di Piazza Grande.
    if(x >= SANT_AGOSTINO_ROAD_FIRST_X)
    {
        if(y <= 8)
        {
            return uint8_t(TileType::EXIT_SAN_MARTINO);    // valore 4: USCITA verso via XX Settembre
        }

        if(y >= SANT_AGOSTINO_HEIGHT - 9)
        {
            return uint8_t(TileType::EXIT_PORTA_ROMANA);   // valore 5: USCITA verso Sant'Andrea
        }

        return uint8_t(TileType::ROAD);
    }

    // ALTO SCHERMO = OVEST reale: la facciata della chiesa di Sant'Agostino, in pietra chiara.
    if(y <= SANT_AGOSTINO_CHIESA_FACADE_LAST_Y)
    {
        if(x >= SANT_AGOSTINO_CHIESA_FACADE_FIRST_X && x <= SANT_AGOSTINO_CHIESA_FACADE_LAST_X)
        {
            return uint8_t(TileType::CONSOLI_FACADE);   // riuso: facciata di monumento (sez. 5)
        }

        return uint8_t(TileType::WALL);   // tessuto edilizio minore ai fianchi della chiesa
    }

    // La breve scalinata davanti al portale.
    if(y == SANT_AGOSTINO_SCALINATA_CHIESA_Y &&
       x >= SANT_AGOSTINO_SCALINATA_CHIESA_FIRST_X && x <= SANT_AGOSTINO_SCALINATA_CHIESA_LAST_X)
    {
        return uint8_t(TileType::STAIRS);
    }

    // Lo slargo davanti alla chiesa.
    if(y >= SANT_AGOSTINO_SLARGO_FIRST_Y && y <= SANT_AGOSTINO_SLARGO_LAST_Y)
    {
        if(x >= SANT_AGOSTINO_SLARGO_FIRST_X && x <= SANT_AGOSTINO_SLARGO_LAST_X)
        {
            return uint8_t(TileType::GROUND);
        }

        return uint8_t(TileType::WALL);
    }

    // Oltre lo slargo, il tessuto edilizio verso l'interno: qui non ci sono varchi, il
    // passaggio verso le altre aree e' tutto sulla strada (x >= ROAD_FIRST_X).
    return uint8_t(TileType::WALL);
}

// Griglia materializzata in ROM, come PIAZZA_GRID, BARGELLO_GRID, SANT_ANDREA_GRID e
// VIA_XX_SETTEMBRE_GRID.
struct SantAgostinoGrid
{
    uint8_t data[SANT_AGOSTINO_WIDTH * SANT_AGOSTINO_HEIGHT];
};

[[nodiscard]] consteval SantAgostinoGrid make_sant_agostino_grid()
{
    SantAgostinoGrid grid{};

    for(int y = 0; y < SANT_AGOSTINO_HEIGHT; ++y)
    {
        for(int x = 0; x < SANT_AGOSTINO_WIDTH; ++x)
        {
            grid.data[x + y * SANT_AGOSTINO_WIDTH] = sant_agostino_tile_type(x, y);
        }
    }

    return grid;
}

inline constexpr SantAgostinoGrid SANT_AGOSTINO_GRID = make_sant_agostino_grid();

// --- static_assert obbligatorie (docs/mappa_del_mondo.md sez. 5) ------------------------------

// 1. Ogni uscita dichiarata esiste davvero nella griglia ed e' calpestabile.
static_assert(SANT_AGOSTINO_GRID.data[28 + 0 * SANT_AGOSTINO_WIDTH] ==
                  uint8_t(TileType::EXIT_SAN_MARTINO),
              "L'uscita verso via XX Settembre deve stare sulla strada, al bordo ovest (y=0)");
static_assert(! is_solid(SANT_AGOSTINO_GRID.data[28 + 0 * SANT_AGOSTINO_WIDTH]),
              "L'uscita verso via XX Settembre non e' calpestabile");
static_assert(is_transition(SANT_AGOSTINO_GRID.data[28 + 0 * SANT_AGOSTINO_WIDTH]),
              "Il tile dell'uscita verso via XX Settembre deve essere un trigger di cambio scena");

static_assert(SANT_AGOSTINO_GRID.data[28 + (SANT_AGOSTINO_HEIGHT - 1) * SANT_AGOSTINO_WIDTH] ==
                  uint8_t(TileType::EXIT_PORTA_ROMANA),
              "L'uscita verso Sant'Andrea deve stare sulla strada, al bordo est (y=HEIGHT-1)");
static_assert(! is_solid(SANT_AGOSTINO_GRID.data[28 + (SANT_AGOSTINO_HEIGHT - 1) *
                                                      SANT_AGOSTINO_WIDTH]),
              "L'uscita verso Sant'Andrea non e' calpestabile");
static_assert(is_transition(SANT_AGOSTINO_GRID.data[28 + (SANT_AGOSTINO_HEIGHT - 1) *
                                                          SANT_AGOSTINO_WIDTH]),
              "Il tile dell'uscita verso Sant'Andrea deve essere un trigger di cambio scena");

// 2. Ogni INGRESSO_DA_* cade su un tile calpestabile.
static_assert(! is_solid(SANT_AGOSTINO_GRID.data[SANT_AGOSTINO_INGRESSO_DA_VIA_XX_SETTEMBRE_X +
                              SANT_AGOSTINO_INGRESSO_DA_VIA_XX_SETTEMBRE_Y * SANT_AGOSTINO_WIDTH]),
              "INGRESSO_DA_VIA_XX_SETTEMBRE cade dentro un muro: il giocatore ci resterebbe chiuso");
static_assert(! is_solid(SANT_AGOSTINO_GRID.data[SANT_AGOSTINO_INGRESSO_DA_SANT_ANDREA_X +
                              SANT_AGOSTINO_INGRESSO_DA_SANT_ANDREA_Y * SANT_AGOSTINO_WIDTH]),
              "INGRESSO_DA_SANT_ANDREA cade dentro un muro: il giocatore ci resterebbe chiuso");

// Il punto di rientro sta almeno sei tile dal proprio varco (docs/mappa_del_mondo.md): un
// ingresso troppo vicino alla propria uscita fa rimbalzare il giocatore fra le due aree
// all'infinito, gli basta tenere premuta la direzione da cui e' arrivato.
static_assert(SANT_AGOSTINO_INGRESSO_DA_VIA_XX_SETTEMBRE_Y - 8 >= 6,
              "INGRESSO_DA_VIA_XX_SETTEMBRE e' troppo vicino alla fascia dell'uscita 4 (y<=8): "
              "rischio di rimbalzo fra le due aree");
static_assert((SANT_AGOSTINO_HEIGHT - 9) - SANT_AGOSTINO_INGRESSO_DA_SANT_ANDREA_Y >= 6,
              "INGRESSO_DA_SANT_ANDREA e' troppo vicino alla fascia dell'uscita 5 "
              "(y>=HEIGHT-9): rischio di rimbalzo fra le due aree");

// 3. Almeno un punto notevole per ogni lato, con un messaggio che fissa l'orientamento.
static_assert(SANT_AGOSTINO_GRID.data[28 + 0 * SANT_AGOSTINO_WIDTH] ==
                  uint8_t(TileType::EXIT_SAN_MARTINO),
              "ALTO SCHERMO = OVEST reale: qui, sulla strada, deve stare l'imbocco verso via XX Settembre");
static_assert(SANT_AGOSTINO_GRID.data[28 + (SANT_AGOSTINO_HEIGHT - 1) * SANT_AGOSTINO_WIDTH] ==
                  uint8_t(TileType::EXIT_PORTA_ROMANA),
              "BASSO SCHERMO = EST reale: qui, sulla strada, deve stare lo sbocco verso Sant'Andrea");
static_assert(SANT_AGOSTINO_GRID.data[0 + 25 * SANT_AGOSTINO_WIDTH] == uint8_t(TileType::WALL),
              "SINISTRA SCHERMO = SUD reale: qui il tessuto edilizio minore chiude lo slargo");
static_assert(SANT_AGOSTINO_GRID.data[31 + 25 * SANT_AGOSTINO_WIDTH] == uint8_t(TileType::WALL),
              "DESTRA SCHERMO = NORD reale: oltre la strada, qui il fronte edificato la chiude");
static_assert(SANT_AGOSTINO_GRID.data[13 + 10 * SANT_AGOSTINO_WIDTH] ==
                  uint8_t(TileType::CONSOLI_FACADE),
              "La chiesa di Sant'Agostino sta in ALTO (ovest reale), non su un lato qualunque");

// Guardia contro il ribaltamento (docs/mappa_del_mondo.md sez. 3): le due uscite hanno valori
// diversi e ciascuna sta SOLO sulla propria estremita' della strada. Se ovest e est fossero
// scambiati per errore, questi assert cadrebbero mentre la mappa continuerebbe comunque a
// compilare — il difetto gia' capitato una volta (Sessione 19).
static_assert(uint8_t(TileType::EXIT_SAN_MARTINO) != uint8_t(TileType::EXIT_PORTA_ROMANA),
              "Le due uscite non possono condividere lo stesso valore di tile");
static_assert(SANT_AGOSTINO_GRID.data[28 + (SANT_AGOSTINO_HEIGHT - 1) * SANT_AGOSTINO_WIDTH] !=
                  uint8_t(TileType::EXIT_SAN_MARTINO),
              "L'estremita' est della strada non puo' avere l'uscita di via XX Settembre: sarebbe un ribaltamento");
static_assert(SANT_AGOSTINO_GRID.data[28 + 0 * SANT_AGOSTINO_WIDTH] !=
                  uint8_t(TileType::EXIT_PORTA_ROMANA),
              "L'estremita' ovest della strada non puo' avere l'uscita di Sant'Andrea: sarebbe un ribaltamento");

// 4. Il monumento nominato rispetta la scala di 1,5 m/tile (city_reference.h).
static_assert(respects_scale(15, SANT_AGOSTINO_CHIESA_FACADE_LAST_X -
                                      SANT_AGOSTINO_CHIESA_FACADE_FIRST_X + 1),
              "La facciata della chiesa di Sant'Agostino non rispetta la scala di 1,5 m per tile");

// Sanita' del percorso: la scalinata deve aderire allo slargo, non staccarsene con un muro, e
// il centro dello slargo dev'essere aperto e raggiungibile dalla strada.
static_assert(! is_solid(SANT_AGOSTINO_GRID.data[SANT_AGOSTINO_SCALINATA_CHIESA_FIRST_X +
                              SANT_AGOSTINO_SCALINATA_CHIESA_Y * SANT_AGOSTINO_WIDTH]),
              "La scalinata davanti al portale deve essere calpestabile");
static_assert(SANT_AGOSTINO_GRID.data[14 + 30 * SANT_AGOSTINO_WIDTH] == uint8_t(TileType::GROUND),
              "Il centro dello slargo deve essere aperto");
static_assert(! is_solid(SANT_AGOSTINO_GRID.data[SANT_AGOSTINO_SLARGO_LAST_X +
                              30 * SANT_AGOSTINO_WIDTH]),
              "Lo slargo deve confinare con la strada, non staccarsene con un muro");
static_assert(sizeof(SantAgostinoGrid) == SANT_AGOSTINO_WIDTH * SANT_AGOSTINO_HEIGHT,
              "La griglia deve restare un blocco contiguo di byte");

} // namespace gubbio::maps

#endif // SANT_AGOSTINO_COLLISION_H
