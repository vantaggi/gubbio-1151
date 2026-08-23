#ifndef DUOMO_DUCALE_COLLISION_H
#define DUOMO_DUCALE_COLLISION_H

#include <stdint.h>

#include "piazza_grande_collision.h"   // per TileType, is_solid, is_transition, TILE_SIZE_PX
#include "city_reference.h"            // per respects_scale(): Duomo e Ducale sono monumenti nominati

namespace gubbio::maps {

// DUOMO, GIARDINI PENSILI E PALAZZO DUCALE — la terrazza monumentale sopra Piazza Grande,
// quota 90 m (docs/mappa_del_mondo.md sez. 1-2). Tre cose una accanto all'altra: il DUOMO dei
// Santi Mariano e Giacomo (facciata a capanna col rosone), il PALAZZO DUCALE di Federico da
// Montefeltro (cortile rinascimentale a due ordini di arcate), i GIARDINI PENSILI (aiuole
// squadrate a siepi basse, visibili nella fotografia aerea). CORREZIONE DEL COMMITTENTE: qui
// NON c'e' la Basilica di Sant'Ubaldo, che sta molto piu' in alto in vetta al Monte Ingino
// (docs/mappa_del_mondo.md sez. 7, gia' corretta una volta).
//
// I DUE VICINI VERI (mappa_del_mondo.md sez. 1). Piazza Grande sta A VALLE: il suo stesso header
// (piazza_grande_collision.h, ROAD_FIRST_X) dichiara che il ciottolato a NORD della piazza porta
// proprio "Palazzo Ducale, i giardini pensili e il Duomo" — quindi da QUI, Piazza Grande e' a
// SUD. Gli Stradoni del Monte Ingino continuano A MONTE, verso la vetta: e' la stessa direzione
// "nord e in salita" che porta da Piazza Grande fin qui, prolungata. Da qui la scelta
// d'orientamento sotto: SUD = verso Piazza Grande, NORD = verso gli Stradoni.
//
// LA FORMA. Un lungo camminamento (la "via Ducale" che sale) attraversa la mappa da SUD a NORD,
// con i monumenti allineati sul fianco OVEST (uno dopo l'altro, nell'ordine Duomo -> Palazzo
// Ducale -> Giardini Pensili salendo) e l'affaccio sulla citta' sottostante sul fianco EST, per
// tutta la lunghezza della terrazza — coerente col fatto che quest'intera area sta SOPRA Piazza
// Grande (mappa_del_mondo.md sez. 2, come la piazza stessa e' pensile sugli Arconi).
//
// MISURE. 64x32 tile, cioe' 512x256 px: un BG regolare legale (sez. 5 del contratto: solo 256 o
// 512 per lato). Alla scala di 1,5 m/tile (city_reference.h) sono 96 x 48 metri: l'asse lungo
// (96 m) e' compresso secondo la regola delle distanze (sez. 4, 73% dichiarato altrove), l'asse
// corto (48 m) contiene la profondita' dei monumenti piu' il camminamento piu' l'affaccio.
constexpr int DUOMO_DUCALE_WIDTH  = 64;   // tile, 512 px. x cresce verso NORD (SUD..NORD lungo la salita)
constexpr int DUOMO_DUCALE_HEIGHT = 32;   // tile, 256 px. y cresce verso EST (OVEST..EST, la profondita')
constexpr int DUOMO_DUCALE_QUOTA_M = 90;  // metri sopra Piazza Quaranta Martiri (mappa_del_mondo.md sez. 2)

constexpr int DUOMO_DUCALE_WIDTH_PX  = DUOMO_DUCALE_WIDTH * TILE_SIZE_PX;    // 512
constexpr int DUOMO_DUCALE_HEIGHT_PX = DUOMO_DUCALE_HEIGHT * TILE_SIZE_PX;   // 256

static_assert(DUOMO_DUCALE_QUOTA_M > 70,
              "Il Duomo/Ducale sta SOPRA Piazza Grande (70 m): la quota deve restare piu' alta");

// --- LA DISPOSIZIONE, E IL SUO ORIENTAMENTO --------------------------------------------------
//
// Uguale a tutte le aree (mappa_del_mondo.md sez. 3): ALTO SCHERMO = OVEST reale, BASSO SCHERMO =
// EST reale, SINISTRA SCHERMO = SUD reale, DESTRA SCHERMO = NORD reale. x cresce verso NORD, y
// cresce verso EST.
//
//        ALTO SCHERMO (y piccola)     = OVEST reale  -> i tre monumenti, uno dopo l'altro
//        BASSO SCHERMO (y grande)     = EST reale     -> l'affaccio sulla citta' sottostante
//        SINISTRA SCHERMO (x piccola) = SUD reale     -> USCITA verso Piazza Grande, a valle
//        DESTRA SCHERMO (x grande)    = NORD reale     -> USCITA verso gli Stradoni del Monte
//                                                          Ingino, a monte
//
// Salendo da SUD a NORD (x crescente) si incontrano, nell'ordine: l'imbocco dalla piazza, il
// Duomo, il Palazzo Ducale, i Giardini Pensili, l'imbocco degli stradoni. E' la regola delle
// adiacenze (city_reference.h): l'ordine in cui le cose si incontrano non e' negoziabile quanto
// la metratura.

// I sette segmenti lungo l'asse SUD-NORD (x), in ordine, uno di seguito all'altro senza vuoti fra
// un segmento e il successivo: la static_assert in fondo lo verifica.
constexpr int DUOMO_DUCALE_APRON_SOUTH_FIRST_X = 0;
constexpr int DUOMO_DUCALE_APRON_SOUTH_LAST_X  = 5;    // 6 tile: l'ultimo tratto salendo dalla piazza

constexpr int DUOMO_DUCALE_DUOMO_FIRST_X = 6;
constexpr int DUOMO_DUCALE_DUOMO_LAST_X  = 15;   // 10 tile = 15 m: la facciata del Duomo, in scala

constexpr int DUOMO_DUCALE_GAP1_FIRST_X = 16;
constexpr int DUOMO_DUCALE_GAP1_LAST_X  = 19;    // 4 tile: tessuto edilizio minore fra Duomo e Ducale

constexpr int DUOMO_DUCALE_DUCALE_FIRST_X = 20;
constexpr int DUOMO_DUCALE_DUCALE_LAST_X  = 39;  // 20 tile = 30 m: il fronte del Palazzo Ducale

constexpr int DUOMO_DUCALE_GAP2_FIRST_X = 40;
constexpr int DUOMO_DUCALE_GAP2_LAST_X  = 43;    // 4 tile: tessuto edilizio minore fra Ducale e giardini

constexpr int DUOMO_DUCALE_GARDEN_FIRST_X = 44;
constexpr int DUOMO_DUCALE_GARDEN_LAST_X  = 55;  // 12 tile = 18 m: i Giardini Pensili

constexpr int DUOMO_DUCALE_APRON_NORTH_FIRST_X = 56;
constexpr int DUOMO_DUCALE_APRON_NORTH_LAST_X  = DUOMO_DUCALE_WIDTH - 1;   // 63, 8 tile

// Le fasce lungo l'asse OVEST-EST (y): monumenti, marciapiede/gradini, camminamento, affaccio.
constexpr int DUOMO_DUCALE_MONUMENT_FIRST_Y = 0;
constexpr int DUOMO_DUCALE_MONUMENT_LAST_Y  = 12;   // 13 tile di profondita' per i monumenti

constexpr int DUOMO_DUCALE_FRONT_Y = DUOMO_DUCALE_MONUMENT_LAST_Y + 1;   // 13: marciapiede/gradini

constexpr int DUOMO_DUCALE_PATH_FIRST_Y = DUOMO_DUCALE_FRONT_Y + 1;      // 14
constexpr int DUOMO_DUCALE_PATH_LAST_Y  = 25;    // 12 tile di camminamento

constexpr int DUOMO_DUCALE_RAILING_FIRST_Y = DUOMO_DUCALE_PATH_LAST_Y + 1;   // 26
constexpr int DUOMO_DUCALE_RAILING_LAST_Y  = 27;   // 2 tile di parapetto

// Oltre il parapetto (y 28..31): non raggiungibile, il vuoto sopra Piazza Grande. Non serve una
// costante propria, ricade nel default della funzione sotto.

static_assert(DUOMO_DUCALE_RAILING_LAST_Y < DUOMO_DUCALE_HEIGHT - 1,
              "Deve restare un margine oltre il parapetto: e' li' che sta il vuoto, non al bordo");

// I due portoni, puramente VISIVI come DOOR_PRETORIO in piazza_grande_collision.h ("oggi solo
// VISIVO, non porta altrove"): quest'area non apre scene di interno, quindi si riusa lo stesso
// valore non-transizione invece di DOOR_CONSOLI, che invece E' un trigger di cambio scena
// (is_transition()) e farebbe scattare una transizione mai cablata in MAPS[].
constexpr int DUOMO_DUCALE_DUOMO_DOOR_FIRST_X  = 10;
constexpr int DUOMO_DUCALE_DUOMO_DOOR_LAST_X   = 11;
constexpr int DUOMO_DUCALE_DUCALE_DOOR_FIRST_X = 29;
constexpr int DUOMO_DUCALE_DUCALE_DOOR_LAST_X  = 30;

// Le due uscite: due colonne a ciascun estremo dell'asse SUD-NORD, dentro la fascia del
// camminamento — stesso schema di piazza_grande_collision.h (ROAD_FIRST_X con le uscite agli
// estremi della fascia), solo con gli assi scambiati perche' qui i vicini sono a SUD e a NORD
// invece che a OVEST ed EST. Le uscite non sanno dove portano (mappa_del_mondo.md sez. 5): qui
// si dichiara solo che i tile 4 e 5 esistono e dove; e' MAPS[] in map_data.h a collegarli.
constexpr int DUOMO_DUCALE_EXIT_PIAZZA_GRANDE_LAST_X  = 1;    // x <= 1: USCITA verso Piazza Grande
constexpr int DUOMO_DUCALE_EXIT_MONTE_INGINO_FIRST_X  = DUOMO_DUCALE_WIDTH - 2;   // 62: verso gli stradoni

// Dove il giocatore compare arrivando da ciascuna area confinante (mappa_del_mondo.md sez. 5).
// PREFISSATE CON DUOMO_DUCALE_: piu' aree hanno Piazza Grande o gli Stradoni del Monte Ingino
// come vicino, e un INGRESSO_DA_X senza prefisso ridefinirebbe quello di un'altra area nello
// stesso namespace gubbio::maps (lo stesso motivo gia' scritto in via_dei_consoli_collision.h e
// in tutte le aree consegnate finora).
//
// ALMENO SEI TILE DAL PROPRIO VARCO (AGENTS.md, mappa_del_mondo.md sez. 5): qui ce ne sono
// sedici in entrambi i casi, ben oltre il minimo — le static_assert piu' sotto lo verificano.
constexpr int DUOMO_DUCALE_INGRESSO_DA_PIAZZA_GRANDE_X = 17;
constexpr int DUOMO_DUCALE_INGRESSO_DA_PIAZZA_GRANDE_Y = 19;
constexpr int DUOMO_DUCALE_INGRESSO_DA_MONTE_INGINO_X  = 46;
constexpr int DUOMO_DUCALE_INGRESSO_DA_MONTE_INGINO_Y  = 19;

static_assert(DUOMO_DUCALE_INGRESSO_DA_PIAZZA_GRANDE_X -
                  DUOMO_DUCALE_EXIT_PIAZZA_GRANDE_LAST_X >= 6,
              "L'ingresso da Piazza Grande e' troppo vicino al proprio varco: ciclo di transizione");
static_assert(DUOMO_DUCALE_EXIT_MONTE_INGINO_FIRST_X -
                  DUOMO_DUCALE_INGRESSO_DA_MONTE_INGINO_X >= 6,
              "L'ingresso dagli Stradoni e' troppo vicino al proprio varco: ciclo di transizione");

// I GIARDINI PENSILI: un reticolo formale di siepi (aiuole squadrate, WALL) separate da sentieri
// larghi un tile (GROUND) — il disegno "a scacchiera" che la fotografia aerea mostra per i
// giardini all'italiana. Blocchi 2x2 di siepe, sentiero ogni terza colonna e ogni terza riga:
// e' un motivo periodico, quindi resta economico in tile unici (Passo 9) esattamente come i
// motivi periodici gia' usati altrove in piazza_grande_collision.h per ciottolato e muratura.
[[nodiscard]] inline constexpr bool duomo_ducale_in_garden(int x, int y)
{
    return x >= DUOMO_DUCALE_GARDEN_FIRST_X && x <= DUOMO_DUCALE_GARDEN_LAST_X &&
           y >= DUOMO_DUCALE_MONUMENT_FIRST_Y && y <= DUOMO_DUCALE_MONUMENT_LAST_Y;
}

[[nodiscard]] inline constexpr uint8_t duomo_ducale_garden_tile(int x, int y)
{
    int gx = (x - DUOMO_DUCALE_GARDEN_FIRST_X) % 3;
    int gy = (y - DUOMO_DUCALE_MONUMENT_FIRST_Y) % 3;

    // Il sentiero corre ogni terza colonna E ogni terza riga: e' cio' che tiene il reticolo
    // connesso in ENTRAMBE le direzioni, non solo lungo un asse. Verificato con un flood fill
    // in fase di progettazione (tools/make_duomo_ducale_art.py ne ripete la verifica).
    if(gx == 2 || gy == 2)
    {
        return uint8_t(TileType::GROUND);
    }

    return uint8_t(TileType::WALL);   // la siepe bassa: si vede, non si attraversa
}

[[nodiscard]] inline constexpr uint8_t duomo_ducale_tile_type(int x, int y)
{
    if(x < 0 || x >= DUOMO_DUCALE_WIDTH || y < 0 || y >= DUOMO_DUCALE_HEIGHT)
    {
        return uint8_t(TileType::WALL);   // fuori mappa = muro
    }

    // ALTO SCHERMO = OVEST reale: la fascia dei tre monumenti, profonda 13 tile.
    if(y >= DUOMO_DUCALE_MONUMENT_FIRST_Y && y <= DUOMO_DUCALE_MONUMENT_LAST_Y)
    {
        if(x >= DUOMO_DUCALE_DUOMO_FIRST_X && x <= DUOMO_DUCALE_DUOMO_LAST_X)
        {
            if(y == DUOMO_DUCALE_MONUMENT_LAST_Y &&
               x >= DUOMO_DUCALE_DUOMO_DOOR_FIRST_X && x <= DUOMO_DUCALE_DUOMO_DOOR_LAST_X)
            {
                return uint8_t(TileType::DOOR_PRETORIO);   // il portone del Duomo: visivo, non transizione
            }

            return uint8_t(TileType::CONSOLI_FACADE);   // riuso: "facciata di monumento" (sez. 5)
        }

        if(x >= DUOMO_DUCALE_DUCALE_FIRST_X && x <= DUOMO_DUCALE_DUCALE_LAST_X)
        {
            if(y == DUOMO_DUCALE_MONUMENT_LAST_Y &&
               x >= DUOMO_DUCALE_DUCALE_DOOR_FIRST_X && x <= DUOMO_DUCALE_DUCALE_DOOR_LAST_X)
            {
                return uint8_t(TileType::DOOR_PRETORIO);   // il portone del Palazzo Ducale
            }

            return uint8_t(TileType::PRETORIO_FACADE);   // riuso: secondo trattamento, stessa pietra
        }

        if(duomo_ducale_in_garden(x, y))
        {
            return duomo_ducale_garden_tile(x, y);
        }

        return uint8_t(TileType::WALL);   // tessuto edilizio minore, fra un monumento e l'altro
    }

    // Il marciapiede/gradini davanti ai monumenti, subito dopo la loro fascia.
    if(y == DUOMO_DUCALE_FRONT_Y)
    {
        bool alla_porta_duomo = x >= DUOMO_DUCALE_DUOMO_DOOR_FIRST_X &&
                                 x <= DUOMO_DUCALE_DUOMO_DOOR_LAST_X;
        bool alla_porta_ducale = x >= DUOMO_DUCALE_DUCALE_DOOR_FIRST_X &&
                                  x <= DUOMO_DUCALE_DUCALE_DOOR_LAST_X;

        if(alla_porta_duomo || alla_porta_ducale)
        {
            return uint8_t(TileType::STAIRS);   // i pochi gradini davanti ai due portoni
        }

        return uint8_t(TileType::GROUND);
    }

    // Il camminamento centrale: le due uscite ai due estremi SUD/NORD, ciottolato nel mezzo.
    if(y >= DUOMO_DUCALE_PATH_FIRST_Y && y <= DUOMO_DUCALE_PATH_LAST_Y)
    {
        if(x <= DUOMO_DUCALE_EXIT_PIAZZA_GRANDE_LAST_X)
        {
            return uint8_t(TileType::EXIT_SAN_MARTINO);    // valore 4: USCITA verso Piazza Grande
        }

        if(x >= DUOMO_DUCALE_EXIT_MONTE_INGINO_FIRST_X)
        {
            return uint8_t(TileType::EXIT_PORTA_ROMANA);   // valore 5: USCITA verso gli Stradoni
        }

        return uint8_t(TileType::ROAD);
    }

    // BASSO SCHERMO = EST reale: l'affaccio sulla citta' sottostante, per tutta la lunghezza —
    // coerente col fatto che l'intera terrazza sta sopra Piazza Grande.
    if(y >= DUOMO_DUCALE_RAILING_FIRST_Y && y <= DUOMO_DUCALE_RAILING_LAST_Y)
    {
        return uint8_t(TileType::RAILING);
    }

    return uint8_t(TileType::WALL);   // oltre il parapetto: il vuoto, non raggiungibile
}

// Griglia materializzata in ROM, come PIAZZA_GRID e le altre aree gia' consegnate.
struct DuomoDucaleGrid
{
    uint8_t data[DUOMO_DUCALE_WIDTH * DUOMO_DUCALE_HEIGHT];
};

[[nodiscard]] consteval DuomoDucaleGrid make_duomo_ducale_grid()
{
    DuomoDucaleGrid grid{};

    for(int y = 0; y < DUOMO_DUCALE_HEIGHT; ++y)
    {
        for(int x = 0; x < DUOMO_DUCALE_WIDTH; ++x)
        {
            grid.data[x + y * DUOMO_DUCALE_WIDTH] = duomo_ducale_tile_type(x, y);
        }
    }

    return grid;
}

inline constexpr DuomoDucaleGrid DUOMO_DUCALE_GRID = make_duomo_ducale_grid();

// --- static_assert obbligatorie (mappa_del_mondo.md sez. 5) -----------------------------------

static_assert(sizeof(DuomoDucaleGrid) == DUOMO_DUCALE_WIDTH * DUOMO_DUCALE_HEIGHT,
              "La griglia deve restare un blocco contiguo di byte");

// I sette segmenti dell'asse SUD-NORD devono susseguirsi senza vuoti ne' sovrapposizioni:
// altrimenti l'ordine dei monumenti (city_reference.h, regola delle adiacenze) smette di essere
// garantito dai numeri e diventa solo una speranza scritta nel commento sopra.
static_assert(DUOMO_DUCALE_APRON_SOUTH_LAST_X + 1 == DUOMO_DUCALE_DUOMO_FIRST_X &&
              DUOMO_DUCALE_DUOMO_LAST_X + 1 == DUOMO_DUCALE_GAP1_FIRST_X &&
              DUOMO_DUCALE_GAP1_LAST_X + 1 == DUOMO_DUCALE_DUCALE_FIRST_X &&
              DUOMO_DUCALE_DUCALE_LAST_X + 1 == DUOMO_DUCALE_GAP2_FIRST_X &&
              DUOMO_DUCALE_GAP2_LAST_X + 1 == DUOMO_DUCALE_GARDEN_FIRST_X &&
              DUOMO_DUCALE_GARDEN_LAST_X + 1 == DUOMO_DUCALE_APRON_NORTH_FIRST_X &&
              DUOMO_DUCALE_APRON_NORTH_LAST_X == DUOMO_DUCALE_WIDTH - 1,
              "I segmenti SUD-NORD devono susseguirsi senza vuoti: e' l'ordine Duomo -> Ducale -> "
              "Giardini che tiene l'illusione dell'adiacenza");

// 1. Ogni uscita dichiarata esiste davvero nella griglia, e' calpestabile, ed e' riconosciuta
// come trigger da is_transition().
static_assert(DUOMO_DUCALE_GRID.data[0 + DUOMO_DUCALE_PATH_FIRST_Y * DUOMO_DUCALE_WIDTH] ==
                  uint8_t(TileType::EXIT_SAN_MARTINO),
              "L'uscita verso Piazza Grande deve stare sul bordo sud (x=0) del camminamento");
static_assert(! is_solid(DUOMO_DUCALE_GRID.data[0 + DUOMO_DUCALE_PATH_FIRST_Y * DUOMO_DUCALE_WIDTH]),
              "L'uscita verso Piazza Grande non e' calpestabile");
static_assert(is_transition(DUOMO_DUCALE_GRID.data[0 + DUOMO_DUCALE_PATH_FIRST_Y * DUOMO_DUCALE_WIDTH]),
              "L'uscita verso Piazza Grande non e' riconosciuta come trigger da is_transition()");

static_assert(DUOMO_DUCALE_GRID.data[(DUOMO_DUCALE_WIDTH - 1) +
                                      DUOMO_DUCALE_PATH_FIRST_Y * DUOMO_DUCALE_WIDTH] ==
                  uint8_t(TileType::EXIT_PORTA_ROMANA),
              "L'uscita verso gli Stradoni deve stare sul bordo nord (x=WIDTH-1) del camminamento");
static_assert(! is_solid(DUOMO_DUCALE_GRID.data[(DUOMO_DUCALE_WIDTH - 1) +
                                                 DUOMO_DUCALE_PATH_FIRST_Y * DUOMO_DUCALE_WIDTH]),
              "L'uscita verso gli Stradoni non e' calpestabile");
static_assert(is_transition(DUOMO_DUCALE_GRID.data[(DUOMO_DUCALE_WIDTH - 1) +
                                                     DUOMO_DUCALE_PATH_FIRST_Y * DUOMO_DUCALE_WIDTH]),
              "L'uscita verso gli Stradoni non e' riconosciuta come trigger da is_transition()");

// 2. Ogni INGRESSO_DA_* cade su un tile calpestabile: altrimenti il giocatore compare dentro un
// muro e il salvataggio ce lo lascia per sempre.
static_assert(! is_solid(DUOMO_DUCALE_GRID.data[DUOMO_DUCALE_INGRESSO_DA_PIAZZA_GRANDE_X +
                              DUOMO_DUCALE_INGRESSO_DA_PIAZZA_GRANDE_Y * DUOMO_DUCALE_WIDTH]),
              "INGRESSO_DA_PIAZZA_GRANDE cade dentro un muro");
static_assert(! is_solid(DUOMO_DUCALE_GRID.data[DUOMO_DUCALE_INGRESSO_DA_MONTE_INGINO_X +
                              DUOMO_DUCALE_INGRESSO_DA_MONTE_INGINO_Y * DUOMO_DUCALE_WIDTH]),
              "INGRESSO_DA_MONTE_INGINO cade dentro un muro");

// 3. Almeno un punto notevole per ogni lato, con un messaggio che fissa l'orientamento — e la
// coppia che distingue una ROTAZIONE da un RIBALTAMENTO (mappa_del_mondo.md sez. 3, gia' successo
// una volta in Piazza Grande): i lati opposti stanno su bordi diversi e non sono la stessa cosa.
static_assert(DUOMO_DUCALE_GRID.data[10 + 6 * DUOMO_DUCALE_WIDTH] == uint8_t(TileType::CONSOLI_FACADE),
              "ALTO SCHERMO = OVEST reale: qui deve esserci la facciata del Duomo, primo dei tre monumenti");
static_assert(DUOMO_DUCALE_GRID.data[50 + 26 * DUOMO_DUCALE_WIDTH] == uint8_t(TileType::RAILING),
              "BASSO SCHERMO = EST reale: qui deve esserci l'affaccio sulla citta' sottostante");
static_assert(DUOMO_DUCALE_GRID.data[0 + DUOMO_DUCALE_PATH_FIRST_Y * DUOMO_DUCALE_WIDTH] ==
                  uint8_t(TileType::EXIT_SAN_MARTINO),
              "SINISTRA SCHERMO = SUD reale: qui deve aprirsi l'uscita a valle verso Piazza Grande");
static_assert(DUOMO_DUCALE_GRID.data[(DUOMO_DUCALE_WIDTH - 1) +
                                      DUOMO_DUCALE_PATH_FIRST_Y * DUOMO_DUCALE_WIDTH] ==
                  uint8_t(TileType::EXIT_PORTA_ROMANA),
              "DESTRA SCHERMO = NORD reale: qui deve aprirsi l'uscita a monte verso gli Stradoni");

// Guardia contro il ribaltamento: le due uscite non possono essere scambiate, ne' i due lati
// lunghi (monumenti/affaccio) possono coincidere.
static_assert(DUOMO_DUCALE_GRID.data[0 + DUOMO_DUCALE_PATH_FIRST_Y * DUOMO_DUCALE_WIDTH] !=
                  DUOMO_DUCALE_GRID.data[(DUOMO_DUCALE_WIDTH - 1) +
                                          DUOMO_DUCALE_PATH_FIRST_Y * DUOMO_DUCALE_WIDTH],
              "Le due uscite non possono essere la stessa cosa");
static_assert(DUOMO_DUCALE_GRID.data[10 + 6 * DUOMO_DUCALE_WIDTH] !=
                  DUOMO_DUCALE_GRID.data[50 + 26 * DUOMO_DUCALE_WIDTH],
              "I due lati lunghi (monumenti a ovest, affaccio a est) non possono essere la stessa cosa");

// 4. I monumenti nominati rispettano respects_scale() di city_reference.h. Ne' il Duomo ne' il
// Palazzo Ducale compaiono in LANDMARKS[] (che elenca solo Consoli, Piazza Grande, Pretorio,
// Fontana dei Matti, Basilica e Teatro Romano): si applica quindi la stessa formula, con le
// misure dichiarate qui invece che lette dall'array, esattamente come fa gia'
// sant_agostino_collision.h per la chiesa di Sant'Agostino. I Giardini Pensili non sono un
// EDIFICIO (city_reference.h vincola la scala solo agli edifici, non ai giardini) e restano
// fuori da questo controllo: annotato invece di ometterlo in silenzio.
static_assert(respects_scale(15, DUOMO_DUCALE_DUOMO_LAST_X - DUOMO_DUCALE_DUOMO_FIRST_X + 1),
              "La facciata del Duomo non rispetta la scala di 1,5 m per tile");
static_assert(respects_scale(30, DUOMO_DUCALE_DUCALE_LAST_X - DUOMO_DUCALE_DUCALE_FIRST_X + 1),
              "Il fronte del Palazzo Ducale non rispetta la scala di 1,5 m per tile");

// Sanita' aggiuntiva: i due portoni sono calpestabili (sono DOOR_PRETORIO, non un trigger), e il
// marciapiede davanti a ciascuno e' una scalinata, non ciottolato liscio.
static_assert(! is_solid(DUOMO_DUCALE_GRID.data[DUOMO_DUCALE_DUOMO_DOOR_FIRST_X +
                              DUOMO_DUCALE_MONUMENT_LAST_Y * DUOMO_DUCALE_WIDTH]),
              "Il portone del Duomo deve essere calpestabile");
static_assert(! is_transition(DUOMO_DUCALE_GRID.data[DUOMO_DUCALE_DUOMO_DOOR_FIRST_X +
                              DUOMO_DUCALE_MONUMENT_LAST_Y * DUOMO_DUCALE_WIDTH]),
              "Il portone del Duomo non deve essere un trigger: nessuna scena d'interno e' cablata");
static_assert(DUOMO_DUCALE_GRID.data[DUOMO_DUCALE_DUOMO_DOOR_FIRST_X +
                              DUOMO_DUCALE_FRONT_Y * DUOMO_DUCALE_WIDTH] == uint8_t(TileType::STAIRS),
              "Davanti al portone del Duomo ci devono essere i gradini");
static_assert(! is_solid(DUOMO_DUCALE_GRID.data[DUOMO_DUCALE_DUCALE_DOOR_FIRST_X +
                              DUOMO_DUCALE_MONUMENT_LAST_Y * DUOMO_DUCALE_WIDTH]),
              "Il portone del Palazzo Ducale deve essere calpestabile");
static_assert(DUOMO_DUCALE_GRID.data[DUOMO_DUCALE_DUCALE_DOOR_FIRST_X +
                              DUOMO_DUCALE_FRONT_Y * DUOMO_DUCALE_WIDTH] == uint8_t(TileType::STAIRS),
              "Davanti al portone del Palazzo Ducale ci devono essere i gradini");

// Il reticolo dei Giardini Pensili contiene sia siepe (WALL) sia sentiero (GROUND): se il motivo
// collassasse a un solo valore, la fotografia aerea a scacchiera non avrebbe piu' controparte
// nella griglia.
static_assert(DUOMO_DUCALE_GRID.data[DUOMO_DUCALE_GARDEN_FIRST_X +
                              DUOMO_DUCALE_MONUMENT_FIRST_Y * DUOMO_DUCALE_WIDTH] ==
                  uint8_t(TileType::WALL),
              "L'angolo sud-ovest del reticolo dei giardini deve essere siepe");
static_assert(DUOMO_DUCALE_GRID.data[(DUOMO_DUCALE_GARDEN_FIRST_X + 2) +
                              DUOMO_DUCALE_MONUMENT_FIRST_Y * DUOMO_DUCALE_WIDTH] ==
                  uint8_t(TileType::GROUND),
              "Il reticolo dei giardini deve avere un sentiero ogni tre colonne");

// Il camminamento resta largo ESATTAMENTE DUOMO_DUCALE_WIDTH tile (cioe' tutta la fascia) per
// tutta la sua lunghezza: e' cio' che garantisce che nessuna riga del camminamento si stringa in
// un collo di bottiglia non voluto.
static_assert([]
{
    for(int y = DUOMO_DUCALE_PATH_FIRST_Y; y <= DUOMO_DUCALE_PATH_LAST_Y; ++y)
    {
        for(int x = 0; x < DUOMO_DUCALE_WIDTH; ++x)
        {
            if(is_solid(DUOMO_DUCALE_GRID.data[x + y * DUOMO_DUCALE_WIDTH]))
            {
                return false;
            }
        }
    }

    return true;
}(), "Il camminamento deve restare interamente calpestabile per tutta la sua larghezza");

} // namespace gubbio::maps

#endif // DUOMO_DUCALE_COLLISION_H
