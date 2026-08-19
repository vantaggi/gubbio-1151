#ifndef MAP_DATA_H
#define MAP_DATA_H

#include <stdint.h>

#include "bn_regular_bg_item.h"

#include "bn_regular_bg_items_piazza_ground.h"
#include "bn_regular_bg_items_bargello_ground.h"
#include "bn_regular_bg_items_piazza_sky.h"

#include "city_reference.h"
#include "map_id.h"
#include "largo_bargello_collision.h"
#include "piazza_grande_collision.h"
#include "scene.h"

namespace gubbio {

// Descrizione delle aree di gioco in ROM: cosa si vede, dove si cammina, dove si esce.
//
// UNA CLASSE DI SCENA, N MAPPE. Con le 8-9 aree della Sez. 38 e gli NPC censiti su 5 di esse,
// una classe per mappa sarebbe insostenibile: `ExplorationScene` e' parametrizzata da `MapId` e
// legge tutto da qui.

inline constexpr int MAX_SPAWNS_PER_MAP = 4;
inline constexpr int MAX_TRIGGERS_PER_MAP = 4;

// Punto di comparsa, in PIXEL, riferito al centro dei piedi del giocatore.
struct SpawnPoint
{
    int16_t x;
    int16_t y;
};

// Un valore di tile che, calpestato, cambia scena.
//
// PERCHE' GLI SPAWN POINT NON SONO UN LUSSO: senza, il rientro da una porta riposiziona il
// giocatore SUL TILE DI USCITA, il trigger riscatta nel frame successivo e la transizione si
// ripete all'infinito. `entry_point` e' lo spawn su cui la mappa di destinazione depositera' il
// giocatore, ed e' per costruzione lontano dal trigger che ce l'ha mandato.
struct TriggerRule
{
    uint8_t tile_value;      // valore restituito da get_tile_type
    SceneId scene;           // scena richiesta
    int16_t parameter;       // MapId oppure indice di incontro, secondo `scene`
    uint8_t entry_point;     // spawn su cui comparire al rientro
};

struct MapDescriptor
{
    const uint8_t* collision;              // griglia width*height, un byte per tile
    int16_t width_tiles;
    int16_t height_tiles;
    const bn::regular_bg_item* ground;
    const bn::regular_bg_item* foreground;  // nullptr se la mappa non ne ha
    const bn::regular_bg_item* parallax;    // cielo, mosso a frazione della camera
    bool foreground_covers_full_height;
    SpawnPoint spawns[MAX_SPAWNS_PER_MAP];
    TriggerRule triggers[MAX_TRIGGERS_PER_MAP];

    // Una mappa senza suolo non e' caricabile: e' una riga ancora da scrivere, non un errore.
    [[nodiscard]] constexpr bool is_implemented() const { return ground != nullptr; }

    [[nodiscard]] constexpr int width_px() const { return width_tiles * maps::TILE_SIZE_PX; }
    [[nodiscard]] constexpr int height_px() const { return height_tiles * maps::TILE_SIZE_PX; }

    [[nodiscard]] constexpr uint8_t tile_at(int tile_x, int tile_y) const
    {
        if(tile_x < 0 || tile_x >= width_tiles || tile_y < 0 || tile_y >= height_tiles)
        {
            return uint8_t(maps::TileType::WALL);      // fuori mappa = muro, come la griglia
        }

        return collision[tile_x + tile_y * width_tiles];
    }

    [[nodiscard]] constexpr uint8_t tile_at_px(int px, int py) const
    {
        return tile_at(px >> 3, py >> 3);
    }
};

// Indici di spawn di Piazza Grande. Sono `entry_point` serializzati su FRAM: si aggiunge in
// coda, non si riordina.
inline constexpr uint8_t SPAWN_PIAZZA_CENTRO       = 0;
inline constexpr uint8_t SPAWN_PIAZZA_DA_CONSOLI   = 1;
inline constexpr uint8_t SPAWN_PIAZZA_DA_EST       = 2;
inline constexpr uint8_t SPAWN_PIAZZA_DA_BARGELLO  = 3;

// Spawn di Largo del Bargello.
inline constexpr uint8_t SPAWN_BARGELLO_CENTRO    = 0;
inline constexpr uint8_t SPAWN_BARGELLO_DA_PIAZZA = 1;

// Comodita' per scrivere gli spawn in tile, che e' l'unita' in cui la piazza e' autorata,
// depositando il giocatore al centro della cella.
[[nodiscard]] constexpr SpawnPoint spawn_at_tile(int tx, int ty)
{
    return SpawnPoint{int16_t(tx * maps::TILE_SIZE_PX + maps::TILE_SIZE_PX / 2),
                      int16_t(ty * maps::TILE_SIZE_PX + maps::TILE_SIZE_PX / 2)};
}

// La tabella delle aree. `inline` e' obbligatorio (regola del Passo 1): senza, ogni unita' di
// traduzione ne riceverebbe una copia e i puntatori a `collision` differirebbero fra unita'.
//
// Oggi e' popolata la sola Piazza Grande. Le altre righe sono deliberatamente vuote e
// `is_implemented()` le riconosce: e' preferibile una mappa dichiarata assente a una tabella
// che finge di avere cinque aree.
inline constexpr MapDescriptor MAPS[MAP_COUNT] = {
    // --- PIAZZA_GRANDE ---
    {
        .collision = maps::PIAZZA_GRID.data,
        .width_tiles = maps::PIAZZA_WIDTH,
        .height_tiles = maps::PIAZZA_HEIGHT,
        .ground = &bn::regular_bg_items::piazza_ground,
        // FOREGROUND ASSENTE DI PROPOSITO. Un livello di occlusione decide dove possono stare i
        // palazzi ed e' una scelta d'arte non ancora presa (512x512 su tutta l'altezza, oppure
        // fascia alta con nulla di occludente sotto y=256 px). Generarlo ora significherebbe
        // fissare quella scelta con un segnaposto. Il campo esiste gia': quando l'arte arriva,
        // si popola questa riga e non si tocca una riga di C++.
        .foreground = nullptr,
        .parallax = &bn::regular_bg_items::piazza_sky,
        .foreground_covers_full_height = false,
        .spawns = {
            spawn_at_tile(32, 26),   // centro della piazza, sul selciato
            spawn_at_tile(32, 21),   // uscendo dal portone dei Consoli, in alto
            // I rientri stanno SUL CIOTTOLATO, che e' l'unica fascia percorribile a sinistra:
            // la fascia alta e' tutta occupata dal Palazzo dei Consoli e dall'edificato minore.
            spawn_at_tile(2, 28),    // rientrando da via XX Settembre
            spawn_at_tile(2, 12)     // rientrando da via dei Consoli
        },
        .triggers = {
            // Il portone dei Consoli non ha ancora una mappa di destinazione: rimanda alla
            // piazza su un altro spawn. Non e' un ripiego — e' l'unico modo di collaudare a
            // runtime il ciclo uscita/rientro, che e' esattamente dove si annida il loop di
            // transizione che gli spawn point esistono per impedire.
            {uint8_t(maps::TileType::DOOR_CONSOLI), SceneId::EXPLORATION,
             int16_t(MapId::PIAZZA_GRANDE), SPAWN_PIAZZA_DA_CONSOLI},

            // PROVVISORIO: il Bargello apre l'incontro di prova. "Come si entra in battaglia
            // dall'overworld" non e' specificato in alcuna sezione del GDD (niente incontri
            // casuali, contatore di passi, nemici visibili o tile di battaglia nella legenda
            // 21B) ed e' una decisione di design aperta. Finche' non e' presa, questo trigger
            // e' l'unico modo di collaudare il round-trip esplorazione -> battaglia ->
            // esplorazione con HP e Fervore che sopravvivono.
            // Il varco occidentale scende a LARGO DEL BARGELLO, lungo via dei Consoli: e' li'
            // che stanno la Fontana dei Matti e il palazzo omonimo (correzione della Sessione
            // 18d). Prima apriva provvisoriamente una battaglia, perche' l'area non esisteva.
            {uint8_t(maps::TileType::EXIT_SAN_MARTINO), SceneId::EXPLORATION,
             int16_t(MapId::LARGO_BARGELLO), SPAWN_BARGELLO_DA_PIAZZA},

            {uint8_t(maps::TileType::EXIT_PORTA_ROMANA), SceneId::EXPLORATION,
             int16_t(MapId::PIAZZA_GRANDE), SPAWN_PIAZZA_DA_EST},

            {0, SceneId::NONE, 0, 0}      // fine elenco
        }
    },
    // --- BOTTACCIONE, MURA, PIANA, MONTE_INGINO: non ancora autorate ---
    {}, {}, {}, {},

    // --- LARGO_BARGELLO ---
    // Un largo in salita lungo via dei Consoli, non una piazza: 32x24 tile in un solo BG 256x256,
    // contro i quattro blocchi che Piazza Grande consuma. Qui sta la Fontana dei Matti.
    {
        .collision = maps::BARGELLO_GRID.data,
        .width_tiles = maps::BARGELLO_WIDTH,
        .height_tiles = maps::BARGELLO_HEIGHT,
        .ground = &bn::regular_bg_items::bargello_ground,
        .foreground = nullptr,
        .parallax = &bn::regular_bg_items::piazza_sky,
        .foreground_covers_full_height = false,
        .spawns = {
            spawn_at_tile(16, 17),   // in mezzo al largo, sotto la fontana
            spawn_at_tile(28, 12),   // rientrando da Piazza Grande, che sta piu' in alto a est
            spawn_at_tile(16, 17),
            spawn_at_tile(16, 17)
        },
        .triggers = {
            // Verso Piazza Grande, in salita.
            {uint8_t(maps::TileType::EXIT_PORTA_ROMANA), SceneId::EXPLORATION,
             int16_t(MapId::PIAZZA_GRANDE), SPAWN_PIAZZA_DA_BARGELLO},

            {0, SceneId::NONE, 0, 0}
        }
    }
};

static_assert(int(sizeof(MAPS) / sizeof(MAPS[0])) == MAP_COUNT,
              "MAPS deve avere una riga per ogni MapId, anche vuota");
static_assert(MAPS[int(MapId::PIAZZA_GRANDE)].is_implemented(),
              "Piazza Grande e' la mappa zero: deve esistere");

// --- Budget VRAM del Passo 9, MISURATO invece che sperato -----------------------------------
//
// 32 blocchi BG da 2 KB in tutto, condivisi fra tileset e mappe; tetto duro di 1024 tile a 4bpp
// per singolo tileset. I conteggi qui sotto sono letti dagli item generati da grit, quindi un
// domani in cui l'arte definitiva sostituisse i segnaposto sforando il budget romperebbe la
// build invece di manifestarsi come un assert dell'allocatore davanti al giocatore.
inline constexpr int GROUND_TILES = bn::regular_bg_items::piazza_ground.tiles_item()
                                        .tiles_ref().size();
inline constexpr int SKY_TILES = bn::regular_bg_items::piazza_sky.tiles_item()
                                     .tiles_ref().size();

inline constexpr int MAX_GROUND_TILES = 512;
inline constexpr int MAX_SKY_TILES = 128;

static_assert(GROUND_TILES <= MAX_GROUND_TILES, "Tileset del suolo oltre il budget del Passo 9");
static_assert(SKY_TILES <= MAX_SKY_TILES, "Tileset del cielo oltre il budget del Passo 9");
static_assert(GROUND_TILES + SKY_TILES <= 1024, "Tetto duro di Butano per tileset a 4bpp");

// La posizione di spawn dev'essere calpestabile: uno spawn dentro un muro e' un giocatore
// incastrato al primo frame, e si scopre solo giocando.
static_assert(! maps::is_solid(maps::get_tile_type_px(MAPS[0].spawns[0].x, MAPS[0].spawns[0].y)) &&
              ! maps::is_solid(maps::get_tile_type_px(MAPS[0].spawns[1].x, MAPS[0].spawns[1].y)) &&
              ! maps::is_solid(maps::get_tile_type_px(MAPS[0].spawns[2].x, MAPS[0].spawns[2].y)) &&
              ! maps::is_solid(maps::get_tile_type_px(MAPS[0].spawns[3].x, MAPS[0].spawns[3].y)),
              "Uno spawn point di Piazza Grande cade dentro un ostacolo");

static_assert(! maps::is_solid(maps::bargello_tile_type(16, 17)) &&
              ! maps::is_solid(maps::bargello_tile_type(28, 12)),
              "Uno spawn di Largo del Bargello cade dentro un ostacolo");

// E non deve stare SU un trigger, altrimenti il rientro riattiva la transizione da cui si e'
// appena usciti: e' il loop infinito che gli spawn point esistono per impedire.
static_assert(! maps::is_transition(maps::get_tile_type_px(MAPS[0].spawns[1].x, MAPS[0].spawns[1].y)) &&
              ! maps::is_transition(maps::get_tile_type_px(MAPS[0].spawns[2].x, MAPS[0].spawns[2].y)) &&
              ! maps::is_transition(maps::get_tile_type_px(MAPS[0].spawns[3].x, MAPS[0].spawns[3].y)),
              "Uno spawn point di rientro cade su un trigger: transizione in loop");

} // namespace gubbio

#endif // MAP_DATA_H
