#ifndef TEATRO_ROMANO_COLLISION_H
#define TEATRO_ROMANO_COLLISION_H

#include <stdint.h>

#include "piazza_grande_collision.h"   // per TileType, is_solid, is_transition, TILE_SIZE_PX
#include "city_reference.h"            // per respects_scale(): punto 4 delle static_assert obbligatorie

namespace gubbio::maps {

// TEATRO ROMANO — fuori le mura cittadine, quota -10 m (docs/mappa_del_mondo.md sez. 1-2): il
// punto piu' basso di tutta Gubbio, sotto perfino Piazza Quaranta Martiri.
//
// L'UNICO MONUMENTO DI QUESTO GIOCO CHE NEL 1151 ESISTEVA GIA' DAVVERO, e gia' allora come
// rudere. E' un teatro del I secolo a.C., costruito quando Iguvium era municipio romano: nel
// 1151 e' rovina da undici secoli. Tutti gli altri monumenti della citta' sono anacronismi
// accettati per volere del committente (docs/mappa_del_mondo.md sez. 7: "vogliamo qualcosa di
// magnifico anche visivamente", Sessione 17); questo no, e vale la pena scriverlo qui perche'
// chi legge il codice non lo dia per scontato insieme agli altri.
//
// FUORI DALLE MURA, PIU' IN BASSO del quartiere di San Martino (25 m). Qui il tessuto edilizio
// della citta' finisce, e si vede: intorno al rudere non ci sono case, solo prato aperto.
//
// COSA C'E'. La cavea semicircolare in blocchi calcarei: il fronte reale e' 70 m, cioe' 46 tile
// (city_reference.h::LANDMARKS, "Teatro Romano"), ed e' un edificio grande quanto il Palazzo
// dei Consoli e il Palazzo Pretorio messi insieme, quindi la scala e' obbligatoria quanto la
// loro. Sotto il fronte, le gradinate: calpestabili, coi gradoni resi come bande alternate e
// l'erba che cresce fra l'una e l'altra — dettaglio che vive nel disegno di
// tools/make_teatro_romano_art.py, non nella collisione, perche' non cambia cio' su cui si
// cammina. Ancora piu' sotto, il corridoio anulare alle spalle della cavea: gli arconi sono in
// parte crollati, resi come un ritmo periodico di piloni (muro) alternati a passaggi (ROAD).
//
// UN SOLO VICINO (docs/mappa_del_mondo.md sez. 1): "San Martino -> Teatro Romano: fuori le mura
// cittadine, piu' in basso". Un teatro fuori le mura non ha altre strade che tornare da dove si
// e' venuti: una sola USCITA, verso San Martino, in salita.

constexpr int TEATRO_ROMANO_WIDTH  = 64;    // tile, 512 px. x cresce verso NORD
constexpr int TEATRO_ROMANO_HEIGHT = 32;    // tile, 256 px. y cresce verso EST
constexpr int TEATRO_ROMANO_QUOTA_M = -10;  // metri sopra Piazza Quaranta Martiri: il punto piu' basso

constexpr int TEATRO_ROMANO_WIDTH_PX  = TEATRO_ROMANO_WIDTH * TILE_SIZE_PX;    // 512
constexpr int TEATRO_ROMANO_HEIGHT_PX = TEATRO_ROMANO_HEIGHT * TILE_SIZE_PX;   // 256

static_assert(TEATRO_ROMANO_QUOTA_M < 0,
              "Il Teatro Romano deve stare sotto Piazza Quaranta Martiri (0 m): e' il punto piu' basso della citta'");

// --- LA DISPOSIZIONE, E IL SUO ORIENTAMENTO --------------------------------------------------
//
// Uguale a tutte le aree (docs/mappa_del_mondo.md sez. 3): ALTO SCHERMO = OVEST reale, BASSO
// SCHERMO = EST reale, SINISTRA SCHERMO = SUD reale, DESTRA SCHERMO = NORD reale. x cresce
// verso NORD, y cresce verso EST.
//
// Il rudere occupa la meta' ALTA della mappa (fascia y 0..CORRIDOIO_LAST_Y): dall'alto verso il
// basso si incontrano, in ordine, la cavea (il fronte calcareo, in scala), le gradinate e il
// corridoio anulare. Ai fianchi del rudere, dentro la stessa fascia, e' rovina non calpestabile:
// non e' ancora prato, e' cio' che resta della struttura fuori dal suo fronte. Superato il
// corridoio, la meta' BASSA della mappa e' tutta prato aperto, fuori le mura: e' li', sul bordo
// DESTRO (nord reale), che si apre l'unico varco, verso San Martino, in salita.
//
//        ALTO SCHERMO (y piccola)     = OVEST reale  -> la cavea, fronte calcareo del rudere
//        BASSO SCHERMO (y grande)     = EST reale     -> prato aperto, oltre il quale la mappa finisce
//        SINISTRA SCHERMO (x piccola) = SUD reale      -> prato aperto: qui il tessuto edilizio non c'e' mai stato
//        DESTRA SCHERMO (x grande)    = NORD reale     -> chiuso, salvo l'unica USCITA verso San Martino

// Il fronte della cavea, in scala: 70 m = 46 tile (city_reference.h::LANDMARKS, "Teatro
// Romano"). E' l'unico vincolo di scala di quest'area, e va rispettato quanto quello del
// Palazzo dei Consoli o della Basilica.
constexpr int TEATRO_ROMANO_CAVEA_FIRST_X = 9;
constexpr int TEATRO_ROMANO_CAVEA_LAST_X  = 54;   // 46 tile: 54 - 9 + 1
constexpr int TEATRO_ROMANO_CAVEA_REAL_WIDTH_M = 70;   // city_reference.h::LANDMARKS, tenuto accanto al numero che descrive

constexpr int TEATRO_ROMANO_CAVEA_FACADE_LAST_Y = 3;

// Le gradinate: piu' strette del fronte esterno, perche' la cavea si restringe salendo verso
// l'alto della gradinata stessa. Qui, per la semplicita' della griglia, il restringimento e' un
// margine fisso invece di una vera curva: la curva la disegna tools/make_teatro_romano_art.py a
// livello di pixel, come gia' fa piazza_grande_collision.h per l'arco del basamento dei Consoli.
constexpr int TEATRO_ROMANO_GRADINATE_FIRST_X = 11;
constexpr int TEATRO_ROMANO_GRADINATE_LAST_X  = 52;
constexpr int TEATRO_ROMANO_GRADINATE_LAST_Y  = 13;

// Il corridoio anulare, con gli arconi in parte crollati: un pilone (muro) ogni ARCO_PASSO
// tile, largo ARCO_PILONE_LARGH; il resto e' passaggio (ROAD).
constexpr int TEATRO_ROMANO_CORRIDOIO_LAST_Y     = 16;
constexpr int TEATRO_ROMANO_ARCO_PASSO           = 8;   // periodo fra due piloni
constexpr int TEATRO_ROMANO_ARCO_PILONE_LARGH    = 2;   // larghezza del pilone, in tile

// L'unica uscita: verso San Martino, sul bordo NORD (destra schermo), in salita — si rientra in
// citta'. Il valore numerico e' quello di EXIT_SAN_MARTINO in piazza_grande_collision.h,
// riusato: le uscite non sanno dove portano (docs/mappa_del_mondo.md sez. 5), il cablaggio verso
// il MapId di San Martino e' compito di map_data.h.
constexpr int TEATRO_ROMANO_EXIT_SAN_MARTINO_FIRST_Y = 24;
constexpr int TEATRO_ROMANO_EXIT_SAN_MARTINO_LAST_Y  = 25;

// Dove il giocatore compare arrivando da San Martino: sul prato, ALMENO SEI TILE dentro dal
// proprio varco (AGENTS.md, mappa_del_mondo.md sez. 5), cosi' chi rientra non ripreme subito la
// direzione da cui e' arrivato e non rimbalza all'infinito fra le due aree.
//
// PREFISSATA CON TEATRO_ROMANO_, non semplicemente INGRESSO_DA_SAN_MARTINO come mostra il
// contratto alla lettera (sez. 5): AGENTS.md lo vieta esplicitamente, perche' tutte le aree
// vivono nello stesso `namespace gubbio::maps` e san_martino_collision.h (che confina con questa
// stessa area) potrebbe un giorno dichiarare a sua volta un ingresso non prefissato — e' gia'
// successo tre volte nella prima tornata del progetto.
constexpr int TEATRO_ROMANO_INGRESSO_DA_SAN_MARTINO_X = 55;   // 8 tile dal varco (colonna 63)
constexpr int TEATRO_ROMANO_INGRESSO_DA_SAN_MARTINO_Y = 24;

static_assert((TEATRO_ROMANO_WIDTH - 1) - TEATRO_ROMANO_INGRESSO_DA_SAN_MARTINO_X >= 6,
              "L'ingresso da San Martino e' troppo vicino al proprio varco: ciclo di transizione");

[[nodiscard]] inline constexpr uint8_t teatro_romano_tile_type(int x, int y)
{
    if(x < 0 || x >= TEATRO_ROMANO_WIDTH || y < 0 || y >= TEATRO_ROMANO_HEIGHT)
    {
        return uint8_t(TileType::WALL);   // fuori mappa = muro
    }

    // L'unica uscita, controllata per prima: e' una finestra piccola dentro un bordo che la
    // logica sotto risolverebbe altrimenti come muro.
    if(x == TEATRO_ROMANO_WIDTH - 1 &&
       y >= TEATRO_ROMANO_EXIT_SAN_MARTINO_FIRST_Y && y <= TEATRO_ROMANO_EXIT_SAN_MARTINO_LAST_Y)
    {
        return uint8_t(TileType::EXIT_SAN_MARTINO);   // valore 4: riusato, "verso San Martino"
    }

    // Il resto del bordo nord: fuori le mura, senza altro varco.
    if(x == TEATRO_ROMANO_WIDTH - 1)
    {
        return uint8_t(TileType::WALL);
    }

    // Il rudere occupa la fascia alta della mappa. Dentro il suo fronte est-ovest si incontrano,
    // scendendo, la cavea, le gradinate e il corridoio; ai suoi fianchi, nella stessa fascia, e'
    // rovina non calpestabile — non ancora prato.
    if(y <= TEATRO_ROMANO_CORRIDOIO_LAST_Y)
    {
        if(x < TEATRO_ROMANO_CAVEA_FIRST_X || x > TEATRO_ROMANO_CAVEA_LAST_X)
        {
            return uint8_t(TileType::WALL);
        }

        // La cavea: fascia esterna in blocchi calcarei, il fronte in scala del rudere.
        if(y <= TEATRO_ROMANO_CAVEA_FACADE_LAST_Y)
        {
            return uint8_t(TileType::CONSOLI_FACADE);   // stesso trattamento grafico: pietra calcarea
        }

        // Le gradinate: calpestabili. L'erba fra i gradoni e' solo un dettaglio del disegno.
        if(y <= TEATRO_ROMANO_GRADINATE_LAST_Y)
        {
            if(x >= TEATRO_ROMANO_GRADINATE_FIRST_X && x <= TEATRO_ROMANO_GRADINATE_LAST_X)
            {
                return uint8_t(TileType::STAIRS);
            }

            return uint8_t(TileType::WALL);   // il margine esterno delle gradinate, crollato
        }

        // Il corridoio anulare, con gli arconi in parte crollati: un pilone ogni ARCO_PASSO tile.
        const int fase = (x - TEATRO_ROMANO_CAVEA_FIRST_X) % TEATRO_ROMANO_ARCO_PASSO;
        return (fase < TEATRO_ROMANO_ARCO_PILONE_LARGH) ? uint8_t(TileType::WALL)
                                                          : uint8_t(TileType::ROAD);
    }

    // Tutto il resto: prato aperto. Fuori le mura, il tessuto edilizio finisce qui.
    return uint8_t(TileType::GROUND);
}

// Griglia materializzata in ROM, come PIAZZA_GRID, BARGELLO_GRID e BASILICA_GRID.
struct TeatroRomanoGrid
{
    uint8_t data[TEATRO_ROMANO_WIDTH * TEATRO_ROMANO_HEIGHT];
};

[[nodiscard]] consteval TeatroRomanoGrid make_teatro_romano_grid()
{
    TeatroRomanoGrid grid{};

    for(int y = 0; y < TEATRO_ROMANO_HEIGHT; ++y)
    {
        for(int x = 0; x < TEATRO_ROMANO_WIDTH; ++x)
        {
            grid.data[x + y * TEATRO_ROMANO_WIDTH] = teatro_romano_tile_type(x, y);
        }
    }

    return grid;
}

inline constexpr TeatroRomanoGrid TEATRO_ROMANO_GRID = make_teatro_romano_grid();

// --- static_assert obbligatorie (docs/mappa_del_mondo.md sez. 5) ------------------------------

static_assert(sizeof(TeatroRomanoGrid) == TEATRO_ROMANO_WIDTH * TEATRO_ROMANO_HEIGHT,
              "La griglia deve restare un blocco contiguo di byte");

// 1. L'uscita dichiarata esiste davvero nella griglia, e' calpestabile, ed e' riconosciuta come
// trigger da is_transition().
static_assert(TEATRO_ROMANO_GRID.data[(TEATRO_ROMANO_WIDTH - 1) +
                  TEATRO_ROMANO_EXIT_SAN_MARTINO_FIRST_Y * TEATRO_ROMANO_WIDTH] ==
                  uint8_t(TileType::EXIT_SAN_MARTINO),
              "L'uscita verso San Martino non e' dove dovrebbe");
static_assert(! is_solid(TEATRO_ROMANO_GRID.data[(TEATRO_ROMANO_WIDTH - 1) +
                  TEATRO_ROMANO_EXIT_SAN_MARTINO_FIRST_Y * TEATRO_ROMANO_WIDTH]),
              "L'uscita verso San Martino non e' calpestabile");
static_assert(is_transition(TEATRO_ROMANO_GRID.data[(TEATRO_ROMANO_WIDTH - 1) +
                  TEATRO_ROMANO_EXIT_SAN_MARTINO_FIRST_Y * TEATRO_ROMANO_WIDTH]),
              "L'uscita verso San Martino non e' riconosciuta come trigger da is_transition()");

// 2. L'ingresso da San Martino cade su un tile calpestabile.
static_assert(! is_solid(TEATRO_ROMANO_GRID.data[TEATRO_ROMANO_INGRESSO_DA_SAN_MARTINO_X +
                  TEATRO_ROMANO_INGRESSO_DA_SAN_MARTINO_Y * TEATRO_ROMANO_WIDTH]),
              "L'ingresso da San Martino cade dentro un muro");

// 3. Almeno un punto notevole per ogni lato, con un messaggio che fissa l'orientamento — e la
// coppia che distingue una ROTAZIONE da un RIBALTAMENTO (mappa_del_mondo.md sez. 3): i lati
// opposti stanno su bordi diversi e non sono la stessa cosa.
static_assert(TEATRO_ROMANO_GRID.data[32 + 1 * TEATRO_ROMANO_WIDTH] == uint8_t(TileType::CONSOLI_FACADE),
              "ALTO SCHERMO = OVEST reale: qui deve stare il fronte calcareo della cavea");
static_assert(TEATRO_ROMANO_GRID.data[32 + (TEATRO_ROMANO_HEIGHT - 1) * TEATRO_ROMANO_WIDTH] ==
                  uint8_t(TileType::GROUND),
              "BASSO SCHERMO = EST reale: qui deve esserci il prato aperto");
static_assert(TEATRO_ROMANO_GRID.data[0 + 20 * TEATRO_ROMANO_WIDTH] == uint8_t(TileType::GROUND),
              "SINISTRA SCHERMO = SUD reale: qui il tessuto edilizio non c'e' mai stato, solo prato");
static_assert(TEATRO_ROMANO_GRID.data[(TEATRO_ROMANO_WIDTH - 1) + 20 * TEATRO_ROMANO_WIDTH] ==
                  uint8_t(TileType::WALL),
              "DESTRA SCHERMO = NORD reale: qui il bordo e' chiuso, salvo l'unica uscita verso San Martino");
static_assert(TEATRO_ROMANO_GRID.data[32 + 1 * TEATRO_ROMANO_WIDTH] !=
                  TEATRO_ROMANO_GRID.data[32 + (TEATRO_ROMANO_HEIGHT - 1) * TEATRO_ROMANO_WIDTH],
              "I due lati lunghi (ovest ed est) non possono essere la stessa cosa");
static_assert(TEATRO_ROMANO_GRID.data[0 + 20 * TEATRO_ROMANO_WIDTH] !=
                  TEATRO_ROMANO_GRID.data[(TEATRO_ROMANO_WIDTH - 1) + 20 * TEATRO_ROMANO_WIDTH],
              "I due lati corti (sud e nord) non possono essere la stessa cosa");

// 4. Il fronte della cavea rispetta la scala di city_reference.h: 70 m devono dare circa 46
// tile. Contato sulla griglia vera, non sulle costanti che la generano, per scoprire un
// eventuale disallineamento fra la dichiarazione e il disegno.
static_assert([]
{
    int larghezza = 0;

    for(int x = 0; x < TEATRO_ROMANO_WIDTH; ++x)
    {
        if(TEATRO_ROMANO_GRID.data[x + 1 * TEATRO_ROMANO_WIDTH] == uint8_t(TileType::CONSOLI_FACADE))
        {
            ++larghezza;
        }
    }

    return respects_scale(TEATRO_ROMANO_CAVEA_REAL_WIDTH_M, larghezza);
}(), "Il fronte del Teatro Romano non rispetta la scala di 1,5 m per tile (70 m devono dare circa 46 tile)");

} // namespace gubbio::maps

#endif // TEATRO_ROMANO_COLLISION_H
