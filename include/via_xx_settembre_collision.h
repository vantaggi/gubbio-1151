#ifndef VIA_XX_SETTEMBRE_COLLISION_H
#define VIA_XX_SETTEMBRE_COLLISION_H

#include <stdint.h>

#include "piazza_grande_collision.h"   // per TileType, is_solid, is_transition, TILE_SIZE_PX

namespace gubbio::maps {

// VIA XX SETTEMBRE — il corridoio che esce da Piazza Grande verso EST e porta a Sant'Agostino
// (docs/mappa_del_mondo.md sez. 1: "Piazza Grande | Sant'Agostino | via XX Settembre, dal varco
// nord-est").
//
// A differenza di Largo del Bargello e di Sant'Andrea, che hanno un solo vicino autorato e un
// muro cieco dall'altra parte, questa via ha ENTRAMBI i capi che si collegano a un'area vera:
// Piazza Grande da un lato, Sant'Agostino dall'altro. E' un corridoio passante, non un ramo.
//
// CARATTERE. Case a schiera in pietra calcarea, botteghe al piano terra: tessuto edilizio minore
// su entrambi i fianchi della strada, non un monumento maggiore. E' un corridoio, come via dei
// Consoli, ma "meno ripido": il dislivello (70 m in Piazza Grande, 60 m a Sant'Agostino, sez. 2
// del contratto) e' reso con UNA scalinata a meta' percorso, non con l'intera via in pendenza.
//
// MISURE. 32x64 tile, cioe' 256x512 px: un BG regolare legale (256 o 512, mai una via di mezzo),
// la stessa forma di Piazza Grande. Alla scala di 1,5 m/tile (city_reference.h) sono 48x96 metri:
// la via e' stretta (32 tile sull'asse nord-sud, come il lato corto della piazza) e lunga sull'
// asse ovest-est, che e' quello che percorre chi cammina da Piazza Grande a Sant'Agostino.

constexpr int VIA_XX_SETTEMBRE_WIDTH  = 32;   // tile. x cresce verso NORD
constexpr int VIA_XX_SETTEMBRE_HEIGHT = 64;   // tile. y cresce verso EST
// Quota rappresentativa: la via scende da 70 m (Piazza Grande) a 60 m (Sant'Agostino). Non e'
// un'area piatta, ma il contratto vuole UNA quota per header; si dichiara il punto di mezzo, e la
// discesa vera e propria e' quella che la scalinata sotto rende visibile in gioco.
constexpr int VIA_XX_SETTEMBRE_QUOTA_M = 65;  // metri sopra Piazza Quaranta Martiri

constexpr int VIA_XX_SETTEMBRE_WIDTH_PX  = VIA_XX_SETTEMBRE_WIDTH * TILE_SIZE_PX;    // 256
constexpr int VIA_XX_SETTEMBRE_HEIGHT_PX = VIA_XX_SETTEMBRE_HEIGHT * TILE_SIZE_PX;   // 512

// --- LA DISPOSIZIONE, E IL SUO ORIENTAMENTO --------------------------------------------------
//
// Uguale a tutte le aree (docs/mappa_del_mondo.md sez. 3): ALTO SCHERMO = OVEST reale, BASSO
// SCHERMO = EST reale, SINISTRA SCHERMO = SUD reale, DESTRA SCHERMO = NORD reale.
//
// Piazza Grande sta a OVEST, Sant'Agostino a EST (sez. 1 del contratto): quindi in questa mappa
// l'imbocco da Piazza Grande e' al bordo ALTO (y=0, y piccola) e lo sbocco verso Sant'Agostino e'
// al bordo BASSO (y=HEIGHT-1, y grande). I due fianchi (x piccola = SUD, x grande = NORD) sono
// entrambi tessuto edilizio minore: non c'e' un'asimmetria fra i due, a differenza di Piazza
// Grande dove un fianco e' il muretto e l'altro la strada.
//
//        ALTO SCHERMO (y piccola)     = OVEST reale  -> imbocco da Piazza Grande
//        BASSO SCHERMO (y grande)     = EST reale     -> sbocco verso Sant'Agostino
//        SINISTRA SCHERMO (x piccola) = SUD reale     -> case a schiera
//        DESTRA SCHERMO (x grande)    = NORD reale     -> case a schiera

// La carreggiata: 6 tile di larghezza (9 m), centrata sull'asse nord-sud della mappa (13..18 su
// 0..31: il centro geometrico e' 15,5, e la fascia lo rispetta). Ai lati, le case a schiera.
constexpr int VIA_XX_SETTEMBRE_ROAD_FIRST_X = 13;
constexpr int VIA_XX_SETTEMBRE_ROAD_LAST_X  = 18;

// La scalinata che rende visibile la discesa dai 70 ai 60 metri (docs/mappa_del_mondo.md sez. 2,
// modo 1: "scalinate e rampe, calpestabili"), a meta' del percorso.
constexpr int VIA_XX_SETTEMBRE_STAIRS_FIRST_Y = 30;
constexpr int VIA_XX_SETTEMBRE_STAIRS_LAST_Y  = 35;

// Dove il giocatore compare arrivando da Piazza Grande: un passo dentro la via, non sul varco
// stesso, cosi' da non ritrovarsi subito sopra il trigger che lo farebbe tornare indietro.
constexpr int VIA_XX_SETTEMBRE_INGRESSO_DA_PIAZZA_GRANDE_X = 15;
constexpr int VIA_XX_SETTEMBRE_INGRESSO_DA_PIAZZA_GRANDE_Y = 1;

// Dove il giocatore compare arrivando da Sant'Agostino, con lo stesso criterio.
constexpr int VIA_XX_SETTEMBRE_INGRESSO_DA_SANT_AGOSTINO_X = 16;
constexpr int VIA_XX_SETTEMBRE_INGRESSO_DA_SANT_AGOSTINO_Y = VIA_XX_SETTEMBRE_HEIGHT - 2;

// Le uscite non sanno dove portano (docs/mappa_del_mondo.md sez. 5): qui si dichiara solo che i
// tile 4 e 5 esistono e dove. E' MAPS[] in map_data.h a collegarli a Piazza Grande e Sant'Agostino.
// USCITA 4 (valore di TileType::EXIT_SAN_MARTINO, riusato) -> Piazza Grande, al bordo OVEST.
// USCITA 5 (valore di TileType::EXIT_PORTA_ROMANA, riusato) -> Sant'Agostino, al bordo EST.
[[nodiscard]] inline constexpr uint8_t via_xx_settembre_tile_type(int x, int y)
{
    if(x < 0 || x >= VIA_XX_SETTEMBRE_WIDTH || y < 0 || y >= VIA_XX_SETTEMBRE_HEIGHT)
    {
        return uint8_t(TileType::WALL);
    }

    // Fuori dalla carreggiata: case a schiera su entrambi i fianchi, nord e sud reali.
    if(x < VIA_XX_SETTEMBRE_ROAD_FIRST_X || x > VIA_XX_SETTEMBRE_ROAD_LAST_X)
    {
        return uint8_t(TileType::WALL);
    }

    // ALTO SCHERMO = OVEST reale: l'imbocco da Piazza Grande.
    if(y == 0)
    {
        return uint8_t(TileType::EXIT_SAN_MARTINO);   // valore 4: USCITA verso Piazza Grande
    }

    // BASSO SCHERMO = EST reale: lo sbocco verso Sant'Agostino.
    if(y == VIA_XX_SETTEMBRE_HEIGHT - 1)
    {
        return uint8_t(TileType::EXIT_PORTA_ROMANA);   // valore 5: USCITA verso Sant'Agostino
    }

    // La scalinata di meta' percorso: calpestabile, come vuole la legenda del contratto.
    if(y >= VIA_XX_SETTEMBRE_STAIRS_FIRST_Y && y <= VIA_XX_SETTEMBRE_STAIRS_LAST_Y)
    {
        return uint8_t(TileType::STAIRS);
    }

    return uint8_t(TileType::ROAD);   // ciottolato percorribile
}

// Griglia materializzata in ROM, come PIAZZA_GRID, BARGELLO_GRID e SANT_ANDREA_GRID.
struct ViaXxSettembreGrid
{
    uint8_t data[VIA_XX_SETTEMBRE_WIDTH * VIA_XX_SETTEMBRE_HEIGHT];
};

[[nodiscard]] consteval ViaXxSettembreGrid make_via_xx_settembre_grid()
{
    ViaXxSettembreGrid grid{};

    for(int y = 0; y < VIA_XX_SETTEMBRE_HEIGHT; ++y)
    {
        for(int x = 0; x < VIA_XX_SETTEMBRE_WIDTH; ++x)
        {
            grid.data[x + y * VIA_XX_SETTEMBRE_WIDTH] = via_xx_settembre_tile_type(x, y);
        }
    }

    return grid;
}

inline constexpr ViaXxSettembreGrid VIA_XX_SETTEMBRE_GRID = make_via_xx_settembre_grid();

// --- static_assert obbligatorie (docs/mappa_del_mondo.md sez. 5) ------------------------------

// 1. Ogni uscita dichiarata esiste davvero nella griglia ed e' calpestabile.
static_assert(VIA_XX_SETTEMBRE_GRID.data[15 + 0 * VIA_XX_SETTEMBRE_WIDTH] ==
                  uint8_t(TileType::EXIT_SAN_MARTINO),
              "L'uscita verso Piazza Grande deve stare sul bordo ovest (y=0)");
static_assert(! is_solid(VIA_XX_SETTEMBRE_GRID.data[15 + 0 * VIA_XX_SETTEMBRE_WIDTH]),
              "L'uscita verso Piazza Grande non e' calpestabile");
static_assert(is_transition(VIA_XX_SETTEMBRE_GRID.data[15 + 0 * VIA_XX_SETTEMBRE_WIDTH]),
              "Il tile dell'uscita verso Piazza Grande deve essere riconosciuto come trigger");

static_assert(VIA_XX_SETTEMBRE_GRID.data[16 + (VIA_XX_SETTEMBRE_HEIGHT - 1) *
                                              VIA_XX_SETTEMBRE_WIDTH] ==
                  uint8_t(TileType::EXIT_PORTA_ROMANA),
              "L'uscita verso Sant'Agostino deve stare sul bordo est (y=HEIGHT-1)");
static_assert(! is_solid(VIA_XX_SETTEMBRE_GRID.data[16 + (VIA_XX_SETTEMBRE_HEIGHT - 1) *
                                                         VIA_XX_SETTEMBRE_WIDTH]),
              "L'uscita verso Sant'Agostino non e' calpestabile");
static_assert(is_transition(VIA_XX_SETTEMBRE_GRID.data[16 + (VIA_XX_SETTEMBRE_HEIGHT - 1) *
                                                             VIA_XX_SETTEMBRE_WIDTH]),
              "Il tile dell'uscita verso Sant'Agostino deve essere riconosciuto come trigger");

// 2. Ogni INGRESSO_DA_* cade su un tile calpestabile.
static_assert(! is_solid(VIA_XX_SETTEMBRE_GRID.data[VIA_XX_SETTEMBRE_INGRESSO_DA_PIAZZA_GRANDE_X +
                              VIA_XX_SETTEMBRE_INGRESSO_DA_PIAZZA_GRANDE_Y * VIA_XX_SETTEMBRE_WIDTH]),
              "INGRESSO_DA_PIAZZA_GRANDE cade dentro un muro: il giocatore ci resterebbe chiuso");
static_assert(! is_solid(VIA_XX_SETTEMBRE_GRID.data[VIA_XX_SETTEMBRE_INGRESSO_DA_SANT_AGOSTINO_X +
                              VIA_XX_SETTEMBRE_INGRESSO_DA_SANT_AGOSTINO_Y * VIA_XX_SETTEMBRE_WIDTH]),
              "INGRESSO_DA_SANT_AGOSTINO cade dentro un muro: il giocatore ci resterebbe chiuso");

// 3. Almeno un punto notevole per ogni lato, con un messaggio che fissa l'orientamento.
static_assert(VIA_XX_SETTEMBRE_GRID.data[15 + 0 * VIA_XX_SETTEMBRE_WIDTH] ==
                  uint8_t(TileType::EXIT_SAN_MARTINO),
              "ALTO SCHERMO = OVEST reale: qui deve stare l'imbocco da Piazza Grande");
static_assert(VIA_XX_SETTEMBRE_GRID.data[16 + (VIA_XX_SETTEMBRE_HEIGHT - 1) *
                                              VIA_XX_SETTEMBRE_WIDTH] ==
                  uint8_t(TileType::EXIT_PORTA_ROMANA),
              "BASSO SCHERMO = EST reale: qui deve stare lo sbocco verso Sant'Agostino");
static_assert(VIA_XX_SETTEMBRE_GRID.data[0 + 20 * VIA_XX_SETTEMBRE_WIDTH] ==
                  uint8_t(TileType::WALL),
              "SINISTRA SCHERMO = SUD reale: qui le case a schiera chiudono la via");
static_assert(VIA_XX_SETTEMBRE_GRID.data[(VIA_XX_SETTEMBRE_WIDTH - 1) + 20 *
                                              VIA_XX_SETTEMBRE_WIDTH] ==
                  uint8_t(TileType::WALL),
              "DESTRA SCHERMO = NORD reale: qui le case a schiera chiudono la via");

// Guardia contro il ribaltamento (docs/mappa_del_mondo.md sez. 3): le due uscite hanno valori
// diversi e ciascuna sta SOLO sul proprio bordo. Se ovest e est fossero scambiati per errore,
// questi assert cadrebbero mentre la mappa continuerebbe comunque a compilare — che e' esattamente
// il difetto gia' capitato una volta (Sessione 19).
static_assert(uint8_t(TileType::EXIT_SAN_MARTINO) != uint8_t(TileType::EXIT_PORTA_ROMANA),
              "Le due uscite non possono condividere lo stesso valore di tile");
static_assert(VIA_XX_SETTEMBRE_GRID.data[15 + (VIA_XX_SETTEMBRE_HEIGHT - 1) *
                                              VIA_XX_SETTEMBRE_WIDTH] !=
                  uint8_t(TileType::EXIT_SAN_MARTINO),
              "Il bordo est non puo' avere l'uscita di Piazza Grande: sarebbe un ribaltamento");
static_assert(VIA_XX_SETTEMBRE_GRID.data[16 + 0 * VIA_XX_SETTEMBRE_WIDTH] !=
                  uint8_t(TileType::EXIT_PORTA_ROMANA),
              "Il bordo ovest non puo' avere l'uscita di Sant'Agostino: sarebbe un ribaltamento");

// 4. Nessun monumento e' dichiarato in quest'area (e' tessuto minore, case a schiera e botteghe,
// non un edificio maggiore): respects_scale() di city_reference.h non si applica qui perche' non
// c'e' nulla da misurare.

// Sanita' del percorso: la scalinata deve aderire alla carreggiata su entrambi i lati, non
// staccarsene con un muro, e restare interamente dentro la fascia stradale.
static_assert(! is_solid(VIA_XX_SETTEMBRE_GRID.data[VIA_XX_SETTEMBRE_ROAD_FIRST_X + VIA_XX_SETTEMBRE_STAIRS_FIRST_Y *
                                                          VIA_XX_SETTEMBRE_WIDTH]),
              "La scalinata deve aderire alla carreggiata sul lato sud (x piccola)");
static_assert(! is_solid(VIA_XX_SETTEMBRE_GRID.data[VIA_XX_SETTEMBRE_ROAD_LAST_X + VIA_XX_SETTEMBRE_STAIRS_LAST_Y *
                                                          VIA_XX_SETTEMBRE_WIDTH]),
              "La scalinata deve aderire alla carreggiata sul lato nord (x grande)");
static_assert(sizeof(ViaXxSettembreGrid) ==
                  VIA_XX_SETTEMBRE_WIDTH * VIA_XX_SETTEMBRE_HEIGHT,
              "La griglia deve restare un blocco contiguo di byte");

} // namespace gubbio::maps

#endif // VIA_XX_SETTEMBRE_COLLISION_H
