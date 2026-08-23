#ifndef SAN_PIETRO_COLLISION_H
#define SAN_PIETRO_COLLISION_H

#include <stdint.h>

#include "piazza_grande_collision.h"   // per TileType, is_solid, is_transition, TILE_SIZE_PX
#include "city_reference.h"            // per gubbio::respects_scale, richiesto dal punto 4

namespace gubbio::maps {

// QUARTIERE DI SAN PIETRO — il quartiere MERIDIONALE, quota 5 m (docs/mappa_del_mondo.md sez.
// 1-2), subito a EST di Piazza Quaranta Martiri, il punto piu' basso della citta'. Il monumento
// e' la CHIESA DI SAN PIETRO, romanica di origine con facciata rimaneggiata (anacronismo gia'
// accettato dalla Sessione 17, docs sez. 7: si mettono tutti gli edifici, anche i rimaneggiamenti
// posteriori al 1151). Il tessuto edilizio e' piu' basso e piu' largo che nei quartieri alti,
// perche' qui Gubbio e' quasi in piano: un solo gradino di dislivello separa questo quartiere da
// Piazza Quaranta Martiri (5 m contro 0), e la griglia sotto lo mostra con una sola breve
// scalinata subito dopo l'ingresso, invece delle rampe lunghe che servono altrove in citta'.
//
// UN SOLO VARCO NOTO (mandato di questo agente, non un'omissione): USCITA verso Piazza Quaranta
// Martiri, a OVEST, che sullo schermo sta in ALTO (docs/mappa_del_mondo.md sez. 3: alto schermo
// = ovest reale). Nessun altro vicino e' stato assegnato a quest'area nel piano: gli altri tre
// lati (basso/est, sinistra/sud, destra/nord) restano la chiesa, un affaccio e tessuto edilizio,
// senza varchi che portino altrove.
//
// IL VALORE DELL'USCITA E' 4 (EXIT_SAN_MARTINO in piazza_grande_collision.h), riusato per quello
// che vale numericamente e non per il nome dell'enumerator (docs/mappa_del_mondo.md sez. 5: "le
// uscite non sanno dove portano, ed e' voluto"). Il valore 4 e' fra quelli che `is_transition()`
// riconosce davvero (a differenza del 6, che altrove nel progetto — Piazza Quaranta Martiri, San
// Martino — e' rimasto un'uscita silenziosa finche' qualcuno non tocca codice condiviso fuori dal
// mandato di questi agenti): questa uscita funziona da subito, senza quella riserva.

constexpr int SAN_PIETRO_WIDTH  = 64;   // in tile. x cresce verso NORD
constexpr int SAN_PIETRO_HEIGHT = 64;   // in tile. y cresce verso EST
constexpr int SAN_PIETRO_QUOTA_M = 5;   // metri sopra Piazza Quaranta Martiri (docs sez. 2)

static_assert(SAN_PIETRO_QUOTA_M == 5, "La quota di San Pietro e' fissata dal piano a 5 m");

constexpr int SAN_PIETRO_WIDTH_PX  = SAN_PIETRO_WIDTH * TILE_SIZE_PX;    // 512
constexpr int SAN_PIETRO_HEIGHT_PX = SAN_PIETRO_HEIGHT * TILE_SIZE_PX;   // 512
static_assert((SAN_PIETRO_WIDTH_PX == 256 || SAN_PIETRO_WIDTH_PX == 512) &&
              (SAN_PIETRO_HEIGHT_PX == 256 || SAN_PIETRO_HEIGHT_PX == 512),
              "Le misure del BMP devono essere 256 o 512 px, mai una misura intermedia (il GBA "
              "non conosce un BG 512x320)");

// --- LA DISPOSIZIONE, E IL SUO ORIENTAMENTO --------------------------------------------------
//
// Uguale a tutte le aree (docs/mappa_del_mondo.md sez. 3): ALTO SCHERMO = OVEST reale, BASSO
// SCHERMO = EST reale, SINISTRA SCHERMO = SUD reale, DESTRA SCHERMO = NORD reale. x cresce verso
// NORD, y cresce verso EST.
//
// Da Piazza Quaranta Martiri (ALTO, y piccola) una via scende verso EST (y crescente): sale una
// breve scalinata subito dopo l'ingresso (l'unico dislivello dell'area), attraversa un crocevia
// con un vicolo trasversale, si allarga in una piazzetta e finisce, con un'ultima scalinata a
// ventaglio, alla CHIESA DI SAN PIETRO — che occupa il fondo del quartiere, verso BASSO SCHERMO
// (y grande). A SINISTRA (SUD reale), allo stesso fianco della chiesa, corre un affaccio: il
// margine meridionale della citta', dove le case cedono il passo a un parapetto. A DESTRA (NORD
// reale) il tessuto edilizio minore prosegue senza varchi, verso il resto del quartiere non
// ancora autorato.
//
//        ALTO SCHERMO (y piccola)     = OVEST reale  -> USCITA verso Piazza Quaranta Martiri
//        BASSO SCHERMO (y grande)     = EST reale    -> Chiesa di San Pietro, in fondo alla via
//        SINISTRA SCHERMO (x piccola) = SUD reale    -> affaccio, margine meridionale della citta'
//        DESTRA SCHERMO (x grande)    = NORD reale   -> case, tessuto edilizio minore

// L'USCITA verso Piazza Quaranta Martiri: valore 4 riusato (vedi sopra).
constexpr int SAN_PIETRO_EXIT_PIAZZA_QUARANTA_MARTIRI_FIRST_X = 28;
constexpr int SAN_PIETRO_EXIT_PIAZZA_QUARANTA_MARTIRI_LAST_X  = 35;
constexpr int SAN_PIETRO_EXIT_PIAZZA_QUARANTA_MARTIRI_FIRST_Y = 0;
constexpr int SAN_PIETRO_EXIT_PIAZZA_QUARANTA_MARTIRI_LAST_Y  = 1;

// La via principale, 4 tile di larghezza come le strade gia' autorate altrove in citta'.
constexpr int SAN_PIETRO_VIA_FIRST_X = 30;
constexpr int SAN_PIETRO_VIA_LAST_X  = 33;
constexpr int SAN_PIETRO_VIA_FIRST_Y = 0;
constexpr int SAN_PIETRO_VIA_LAST_Y  = 34;   // si ferma dove comincia la piazzetta

// La breve scalinata subito dopo l'ingresso: l'UNICO dislivello di quest'area (5 m contro gli
// 0 di Piazza Quaranta Martiri), reso con la stessa convenzione delle altre aree (docs sez. 2:
// scalinate e rampe, non una terza dimensione inventata).
constexpr int SAN_PIETRO_STAIRS_INGRESSO_FIRST_Y = 4;
constexpr int SAN_PIETRO_STAIRS_INGRESSO_LAST_Y  = 5;

// Il vicolo trasversale, che attraversa il quartiere da un fianco all'altro e incrocia la via.
constexpr int SAN_PIETRO_VICOLO_FIRST_X = 5;
constexpr int SAN_PIETRO_VICOLO_LAST_X  = 58;
constexpr int SAN_PIETRO_VICOLO_FIRST_Y = 15;
constexpr int SAN_PIETRO_VICOLO_LAST_Y  = 18;

// Un campiello minore all'incrocio del vicolo, decentrato verso SUD: una piazzetta piu' piccola
// di quella davanti alla chiesa, come ce ne sono diverse nei quartieri bassi di Gubbio. Il
// vicolo, controllato per primo nella funzione sotto, lo attraversa: due strisce di campiello
// restano visibili ai due lati dell'incrocio.
constexpr int SAN_PIETRO_CAMPIELLO_FIRST_X = 6;
constexpr int SAN_PIETRO_CAMPIELLO_LAST_X  = 14;
constexpr int SAN_PIETRO_CAMPIELLO_FIRST_Y = 13;
constexpr int SAN_PIETRO_CAMPIELLO_LAST_Y  = 20;

// La piazzetta davanti alla chiesa, dove la via si allarga prima della scalinata del portone. La
// via stessa, che la attraversa, resta ciottolato (ROAD) e non prato/selciato aperto (GROUND):
// e' la stessa precedenza gia' vista nel "giardino" di Piazza Quaranta Martiri.
constexpr int SAN_PIETRO_PIAZZETTA_FIRST_X = 20;
constexpr int SAN_PIETRO_PIAZZETTA_LAST_X  = 43;
constexpr int SAN_PIETRO_PIAZZETTA_FIRST_Y = 24;
constexpr int SAN_PIETRO_PIAZZETTA_LAST_Y  = 34;

// La scalinata a ventaglio davanti al portone, piu' larga della via: lo stesso principio della
// scalinata di Piazza Grande davanti al Palazzo dei Consoli.
constexpr int SAN_PIETRO_STAIRS_CHIESA_FIRST_X = 28;
constexpr int SAN_PIETRO_STAIRS_CHIESA_LAST_X  = 35;
constexpr int SAN_PIETRO_STAIRS_CHIESA_FIRST_Y = 35;
constexpr int SAN_PIETRO_STAIRS_CHIESA_LAST_Y  = 37;

// LA CHIESA DI SAN PIETRO. Fronte stimato 24 m (non e' in city_reference.h::LANDMARKS, che elenca
// solo Consoli, Piazza Grande, Pretorio, Fontana dei Matti, Basilica e Teatro Romano: e' una
// stima di questo autore, da far confluire in docs/riferimenti/FONTI.md insieme alla nota
// sull'anacronismo della facciata rimaneggiata — annotazione che spetta a chi cuce il mondo,
// perche' il mandato di questo agente vieta di scrivere fuori dai due file assegnati, come gia'
// notato in piazza_quaranta_martiri_collision.h per la Loggia e San Francesco). Alla scala di
// 1,5 m/tile (city_reference.h) 24 m danno ESATTAMENTE 16 tile: e' la larghezza che la griglia
// sotto realizza.
constexpr int SAN_PIETRO_CHIESA_FIRST_X = 24;
constexpr int SAN_PIETRO_CHIESA_LAST_X  = 39;   // 16 tile di fronte
constexpr int SAN_PIETRO_CHIESA_FIRST_Y = 38;
constexpr int SAN_PIETRO_CHIESA_LAST_Y  = 58;   // corpo dell'edificio, in profondita'
constexpr int SAN_PIETRO_CHIESA_REAL_WIDTH_M = 24;

// Il portone, al centro del fronte, sulla prima fila del corpo di fabbrica.
constexpr int SAN_PIETRO_CHIESA_DOOR_FIRST_X = 31;
constexpr int SAN_PIETRO_CHIESA_DOOR_LAST_X  = 32;

// L'affaccio sul margine meridionale del quartiere (SINISTRA SCHERMO = SUD reale), allo stesso
// fianco della chiesa: il bordo abitato cede il passo a un parapetto, come il muretto di Piazza
// Grande e l'affaccio di San Martino.
constexpr int SAN_PIETRO_RAILING_LAST_X  = 1;
constexpr int SAN_PIETRO_RAILING_FIRST_Y = SAN_PIETRO_CHIESA_FIRST_Y;   // 38
constexpr int SAN_PIETRO_RAILING_LAST_Y  = SAN_PIETRO_CHIESA_LAST_Y;    // 58

// Dove il giocatore compare arrivando da Piazza Quaranta Martiri (docs/mappa_del_mondo.md sez.
// 5). PREFISSATA con SAN_PIETRO_, non semplicemente INGRESSO_DA_PIAZZA_QUARANTA_MARTIRI: piu'
// aree finiscono nella stessa unita' di traduzione (map_data.h), tutte in gubbio::maps, e un
// INGRESSO_DA_X senza prefisso ridefinirebbe il simbolo omonimo di un'altra area confinante con
// lo stesso vicino (gia' capitato tre volte nella prima tornata, per AGENTS.md).
//
// ALMENO SEI TILE dal proprio varco: qui la distanza e' 8 tile, verificata dalla static_assert
// subito sotto (docs/mappa_del_mondo.md: un ingresso troppo vicino alla propria uscita fa
// rimbalzare il giocatore fra le due aree all'infinito, tenendo premuta la direzione da cui e'
// arrivato — e' il ciclo di transizione, gia' ricomparso una volta).
constexpr int SAN_PIETRO_INGRESSO_DA_PIAZZA_QUARANTA_MARTIRI_X = 31;
constexpr int SAN_PIETRO_INGRESSO_DA_PIAZZA_QUARANTA_MARTIRI_Y = 9;

static_assert(SAN_PIETRO_INGRESSO_DA_PIAZZA_QUARANTA_MARTIRI_Y -
                  SAN_PIETRO_EXIT_PIAZZA_QUARANTA_MARTIRI_LAST_Y >= 6,
              "L'ingresso da Piazza Quaranta Martiri e' troppo vicino al proprio varco: ciclo di "
              "transizione");

[[nodiscard]] inline constexpr uint8_t san_pietro_tile_type(int x, int y)
{
    if(x < 0 || x >= SAN_PIETRO_WIDTH || y < 0 || y >= SAN_PIETRO_HEIGHT)
    {
        return uint8_t(TileType::WALL);   // fuori mappa = muro
    }

    // L'uscita, controllata per prima: e' una finestra piccola dentro la via che la logica sotto,
    // valutata prima, risolverebbe come semplice ciottolato.
    if(y >= SAN_PIETRO_EXIT_PIAZZA_QUARANTA_MARTIRI_FIRST_Y &&
       y <= SAN_PIETRO_EXIT_PIAZZA_QUARANTA_MARTIRI_LAST_Y &&
       x >= SAN_PIETRO_EXIT_PIAZZA_QUARANTA_MARTIRI_FIRST_X &&
       x <= SAN_PIETRO_EXIT_PIAZZA_QUARANTA_MARTIRI_LAST_X)
    {
        return uint8_t(TileType::EXIT_SAN_MARTINO);   // valore 4: verso Piazza Quaranta Martiri
    }

    const bool in_via = (x >= SAN_PIETRO_VIA_FIRST_X && x <= SAN_PIETRO_VIA_LAST_X &&
                         y >= SAN_PIETRO_VIA_FIRST_Y && y <= SAN_PIETRO_VIA_LAST_Y);

    // La scalinata subito dopo l'ingresso: l'unico dislivello di quest'area.
    if(in_via && y >= SAN_PIETRO_STAIRS_INGRESSO_FIRST_Y && y <= SAN_PIETRO_STAIRS_INGRESSO_LAST_Y)
    {
        return uint8_t(TileType::STAIRS);
    }

    // LA CHIESA DI SAN PIETRO, in fondo alla via: il portone al centro del fronte, il resto
    // facciata romanica rimaneggiata.
    if(x >= SAN_PIETRO_CHIESA_FIRST_X && x <= SAN_PIETRO_CHIESA_LAST_X &&
       y >= SAN_PIETRO_CHIESA_FIRST_Y && y <= SAN_PIETRO_CHIESA_LAST_Y)
    {
        if(y == SAN_PIETRO_CHIESA_FIRST_Y &&
           x >= SAN_PIETRO_CHIESA_DOOR_FIRST_X && x <= SAN_PIETRO_CHIESA_DOOR_LAST_X)
        {
            return uint8_t(TileType::DOOR_PRETORIO);   // portone: oggi solo visivo, come il Pretorio
        }

        return uint8_t(TileType::CONSOLI_FACADE);   // riuso: pietra della facciata romanica
    }

    // La scalinata a ventaglio davanti al portone, fra la piazzetta e la chiesa.
    if(y >= SAN_PIETRO_STAIRS_CHIESA_FIRST_Y && y <= SAN_PIETRO_STAIRS_CHIESA_LAST_Y &&
       x >= SAN_PIETRO_STAIRS_CHIESA_FIRST_X && x <= SAN_PIETRO_STAIRS_CHIESA_LAST_X)
    {
        return uint8_t(TileType::STAIRS);
    }

    if(in_via)
    {
        return uint8_t(TileType::ROAD);
    }

    // Il vicolo trasversale.
    if(y >= SAN_PIETRO_VICOLO_FIRST_Y && y <= SAN_PIETRO_VICOLO_LAST_Y &&
       x >= SAN_PIETRO_VICOLO_FIRST_X && x <= SAN_PIETRO_VICOLO_LAST_X)
    {
        return uint8_t(TileType::ROAD);
    }

    // La piazzetta davanti alla chiesa.
    if(x >= SAN_PIETRO_PIAZZETTA_FIRST_X && x <= SAN_PIETRO_PIAZZETTA_LAST_X &&
       y >= SAN_PIETRO_PIAZZETTA_FIRST_Y && y <= SAN_PIETRO_PIAZZETTA_LAST_Y)
    {
        return uint8_t(TileType::GROUND);
    }

    // Il campiello minore, decentrato a sud del vicolo.
    if(x >= SAN_PIETRO_CAMPIELLO_FIRST_X && x <= SAN_PIETRO_CAMPIELLO_LAST_X &&
       y >= SAN_PIETRO_CAMPIELLO_FIRST_Y && y <= SAN_PIETRO_CAMPIELLO_LAST_Y)
    {
        return uint8_t(TileType::GROUND);
    }

    // L'affaccio sul margine meridionale, allo stesso fianco della chiesa.
    if(x <= SAN_PIETRO_RAILING_LAST_X &&
       y >= SAN_PIETRO_RAILING_FIRST_Y && y <= SAN_PIETRO_RAILING_LAST_Y)
    {
        return uint8_t(TileType::RAILING);
    }

    // Tutto il resto: tessuto edilizio minore, piu' basso e piu' largo che nei quartieri alti.
    return uint8_t(TileType::WALL);
}

// Griglia materializzata in ROM, come PIAZZA_GRID, BARGELLO_GRID e le altre aree gia' consegnate.
struct SanPietroGrid
{
    uint8_t data[SAN_PIETRO_WIDTH * SAN_PIETRO_HEIGHT];
};

[[nodiscard]] consteval SanPietroGrid make_san_pietro_grid()
{
    SanPietroGrid grid{};

    for(int y = 0; y < SAN_PIETRO_HEIGHT; ++y)
    {
        for(int x = 0; x < SAN_PIETRO_WIDTH; ++x)
        {
            grid.data[x + y * SAN_PIETRO_WIDTH] = san_pietro_tile_type(x, y);
        }
    }

    return grid;
}

inline constexpr SanPietroGrid SAN_PIETRO_GRID = make_san_pietro_grid();

// --- static_assert obbligatorie (docs/mappa_del_mondo.md sez. 5) ------------------------------

static_assert(sizeof(SanPietroGrid) == SAN_PIETRO_WIDTH * SAN_PIETRO_HEIGHT,
              "La griglia deve restare un blocco contiguo di byte");

// 1. L'uscita dichiarata esiste davvero nella griglia, e' calpestabile, ed e' riconosciuta come
// trigger da is_transition().
static_assert(SAN_PIETRO_GRID.data[31 + 0 * SAN_PIETRO_WIDTH] ==
                  uint8_t(TileType::EXIT_SAN_MARTINO),
              "L'uscita verso Piazza Quaranta Martiri non e' dove dovrebbe");
static_assert(! is_solid(SAN_PIETRO_GRID.data[31 + 0 * SAN_PIETRO_WIDTH]),
              "L'uscita verso Piazza Quaranta Martiri non e' calpestabile");
static_assert(is_transition(SAN_PIETRO_GRID.data[31 + 0 * SAN_PIETRO_WIDTH]),
              "L'uscita verso Piazza Quaranta Martiri non e' riconosciuta come trigger da "
              "is_transition()");

// 2. L'INGRESSO_DA_* cade su un tile calpestabile e non su un trigger: altrimenti il giocatore
// compare dentro un muro (e il salvataggio ce lo lascia per sempre) oppure su un'uscita che lo
// rimanda subito indietro.
static_assert(! is_solid(SAN_PIETRO_GRID.data[
                  SAN_PIETRO_INGRESSO_DA_PIAZZA_QUARANTA_MARTIRI_X +
                  SAN_PIETRO_INGRESSO_DA_PIAZZA_QUARANTA_MARTIRI_Y * SAN_PIETRO_WIDTH]),
              "L'ingresso da Piazza Quaranta Martiri cade dentro un muro");
static_assert(! is_transition(SAN_PIETRO_GRID.data[
                  SAN_PIETRO_INGRESSO_DA_PIAZZA_QUARANTA_MARTIRI_X +
                  SAN_PIETRO_INGRESSO_DA_PIAZZA_QUARANTA_MARTIRI_Y * SAN_PIETRO_WIDTH]),
              "L'ingresso da Piazza Quaranta Martiri cade su un trigger: transizione in loop");

// 3. Almeno un punto notevole per ogni lato, con un messaggio che fissa l'orientamento — e la
// coppia che distingue una ROTAZIONE da un RIBALTAMENTO (gia' successo una volta in Piazza
// Grande, docs/mappa_del_mondo.md sez. 3): i lati opposti stanno su bordi diversi e non sono la
// stessa cosa.
static_assert(SAN_PIETRO_GRID.data[31 + 0 * SAN_PIETRO_WIDTH] ==
                  uint8_t(TileType::EXIT_SAN_MARTINO),
              "ALTO SCHERMO = OVEST reale: qui deve aprirsi l'uscita verso Piazza Quaranta Martiri");
static_assert(SAN_PIETRO_GRID.data[31 + 50 * SAN_PIETRO_WIDTH] ==
                  uint8_t(TileType::CONSOLI_FACADE),
              "BASSO SCHERMO = EST reale: qui deve stare la facciata della Chiesa di San Pietro");
static_assert(SAN_PIETRO_GRID.data[1 + 45 * SAN_PIETRO_WIDTH] == uint8_t(TileType::RAILING),
              "SINISTRA SCHERMO = SUD reale: qui c'e' l'affaccio sul margine meridionale, non le case");
static_assert(SAN_PIETRO_GRID.data[62 + 45 * SAN_PIETRO_WIDTH] == uint8_t(TileType::WALL),
              "DESTRA SCHERMO = NORD reale: qui ci sono le case, senza varchi");
static_assert(SAN_PIETRO_GRID.data[31 + 0 * SAN_PIETRO_WIDTH] !=
                  SAN_PIETRO_GRID.data[31 + 50 * SAN_PIETRO_WIDTH],
              "I due lati lunghi (ovest ed est) non possono essere la stessa cosa");
static_assert(SAN_PIETRO_GRID.data[1 + 45 * SAN_PIETRO_WIDTH] !=
                  SAN_PIETRO_GRID.data[62 + 45 * SAN_PIETRO_WIDTH],
              "I due lati corti (sud e nord) non possono essere la stessa cosa");

// 4. Il monumento nominato rispetta respects_scale() di city_reference.h. Si misura la griglia
// invece di fidarsi delle costanti, perche' e' la griglia che finisce in ROM (come fanno
// basilica_collision.h e piazza_quaranta_martiri_collision.h per i loro monumenti).
static_assert([]
{
    int fronte = 0;

    for(int x = 0; x < SAN_PIETRO_WIDTH; ++x)
    {
        // y=45: dentro il corpo della chiesa, ma non sulla riga del portone (y=38): conta solo
        // la facciata piena.
        if(SAN_PIETRO_GRID.data[x + 45 * SAN_PIETRO_WIDTH] == uint8_t(TileType::CONSOLI_FACADE))
        {
            ++fronte;
        }
    }

    return fronte == SAN_PIETRO_CHIESA_LAST_X - SAN_PIETRO_CHIESA_FIRST_X + 1;
}(), "La facciata della Chiesa di San Pietro non misura i 16 tile attesi lungo la riga y=45");

static_assert(gubbio::respects_scale(SAN_PIETRO_CHIESA_REAL_WIDTH_M,
                                      SAN_PIETRO_CHIESA_LAST_X - SAN_PIETRO_CHIESA_FIRST_X + 1),
              "La facciata della Chiesa di San Pietro non rispetta la scala di 1,5 m per tile");

// Sanita' del percorso: subito oltre l'uscita, il portone e il centro della piazzetta devono
// essere calpestabili, altrimenti il giocatore che entra sbatte contro un muro invisibile.
static_assert(! is_solid(SAN_PIETRO_GRID.data[31 + 2 * SAN_PIETRO_WIDTH]),
              "Subito a valle dell'uscita verso Piazza Quaranta Martiri deve essere calpestabile");
static_assert(SAN_PIETRO_GRID.data[31 + 38 * SAN_PIETRO_WIDTH] == uint8_t(TileType::DOOR_PRETORIO),
              "Il portone della chiesa non e' al centro del fronte");
static_assert(! is_solid(SAN_PIETRO_GRID.data[31 + 38 * SAN_PIETRO_WIDTH]),
              "Il portone della chiesa deve essere calpestabile, come quello del Pretorio");
static_assert(SAN_PIETRO_GRID.data[22 + 29 * SAN_PIETRO_WIDTH] == uint8_t(TileType::GROUND),
              "Il centro della piazzetta (fuori dalla via che l'attraversa) deve essere prato/"
              "selciato aperto");

} // namespace gubbio::maps

#endif // SAN_PIETRO_COLLISION_H
