#ifndef MONTE_INGINO_COLLISION_H
#define MONTE_INGINO_COLLISION_H

#include <stdint.h>

#include "piazza_grande_collision.h"   // per TileType, is_solid, is_transition, TILE_SIZE_PX

namespace gubbio::maps {

// STRADONI DEL MONTE INGINO — la salita lunga del gioco (docs/mappa_del_mondo.md sez. 1-2).
//
// COSA E'. Due chilometri di strada sterrata che salgono dalla citta', all'altezza del Duomo e
// del Palazzo Ducale, fino alla Basilica di Sant'Ubaldo in vetta. E' l'arco che chiude la meta'
// del giro: da qui non si scende piu' verso Piazza Grande, si sale verso il monte.
//
// LA COMPRESSIONE, DICHIARATA. Duemila metri reali, a 1,5 m/tile (city_reference.h), sono 1333
// tile: impossibile su un solo BG legale (max 512 px = 64 tile per lato) e comunque indesiderabile
// — nessuno vuole premere una direzione per 1333 fotogrammi. La regola della compressione delle
// distanze (docs sez. 4, fattore 73%) da sola non basta a portare 1333 tile dentro un'area
// giocabile: qui la compressione e' STRUTTURALE, non solo percentuale. La lunghezza reale non e'
// resa allungando la mappa, ma FACENDOLE FARE TORNANTI: il percorso attraversa piu' volte la
// larghezza dell'area (64x32 tile, 512x256 px, un solo BG legale) invece di procedere in linea
// retta, cosi' il tragitto CALPESTATO e' piu' lungo dei 64 tile in linea d'aria fra i due varchi,
// pur restando dentro un'unica schermata di collisione. Il ricordo che deve restare al giocatore
// e' "e' stata una salita lunga, con tornanti e scorci sulla citta'" — non il conteggio dei metri.
constexpr int MONTE_INGINO_WIDTH  = 64;   // tile, 512 px. x cresce verso NORD (asse della salita)
constexpr int MONTE_INGINO_HEIGHT = 32;   // tile, 256 px. y cresce verso EST

constexpr int MONTE_INGINO_WIDTH_PX  = MONTE_INGINO_WIDTH * TILE_SIZE_PX;    // 512
constexpr int MONTE_INGINO_HEIGHT_PX = MONTE_INGINO_HEIGHT * TILE_SIZE_PX;   // 256

// QUOTA. L'area non ha una quota unica: sale da 100 a 350 m (docs/mappa_del_mondo.md sez. 2),
// come la Gola del Bottaccione ha una discesa invece di un numero. Stesso rimedio adottato li'
// (bottaccione_collision.h): il contratto tecnico (sez. 5) vuole una singola `<NOME>_QUOTA_M`, e
// si usa la quota di PARTENZA — qui si comincia a salire dal Duomo/Ducale — dichiarando ANCHE i
// due estremi perche' chi cuce le aree in map_data.h sappia che il dislivello e' interno a questa
// mappa, non solo fra questa e le vicine.
constexpr int MONTE_INGINO_QUOTA_BASE_M = 100;   // presso l'ingresso da Duomo/Ducale, a valle
constexpr int MONTE_INGINO_QUOTA_TOP_M  = 350;   // presso l'uscita verso la Basilica, in vetta
constexpr int MONTE_INGINO_QUOTA_M = MONTE_INGINO_QUOTA_BASE_M;   // richiesta dal contratto sez.5

static_assert(MONTE_INGINO_QUOTA_BASE_M < MONTE_INGINO_QUOTA_TOP_M,
              "La quota di valle (Duomo/Ducale) deve restare sotto quella di vetta (Basilica)");

// --- LA DISPOSIZIONE, E IL SUO ORIENTAMENTO ----------------------------------------------------
//
// Uguale a tutte le aree (docs/mappa_del_mondo.md sez. 3): ALTO SCHERMO = OVEST reale, BASSO
// SCHERMO = EST reale, SINISTRA SCHERMO = SUD reale, DESTRA SCHERMO = NORD reale.
//
// Qui l'orientamento fissa il senso della salita, che e' lo stesso di duomo_ducale_collision.h
// (l'area a valle, il cui varco verso questi stradoni sta gia' sul proprio bordo NORD, x grande):
// SINISTRA SCHERMO (x piccola) = SUD reale = si arriva da valle, dal Duomo/Ducale; DESTRA SCHERMO
// (x grande) = NORD reale = si esce verso la vetta, la Basilica. Uscendo da un'area a destra e
// rientrando nella successiva a sinistra la x continua a crescere: e' cosi' che ogni transizione
// del gioco funziona, ed e' la ragione per cui l'asse della salita resta x anche qui.
//
//        ALTO SCHERMO (y piccola)     = OVEST reale  -> il primo belvedere, sul lato a monte
//        BASSO SCHERMO (y grande)     = EST reale    -> il secondo belvedere, sul lato a valle
//        SINISTRA SCHERMO (x piccola) = SUD reale     -> varco verso Duomo/Ducale, si arriva da qui
//        DESTRA SCHERMO (x grande)    = NORD reale    -> varco verso la Basilica, si esce di qui
//
// Il sentiero non sta su una fascia fissa come il camminamento del Bottaccione: SERPEGGIA, ed e'
// il modo in cui questa mappa rende i tornanti. La sua larghezza calpestabile pero' NON cambia
// mai — resta 5 tile per ogni colonna x, dal varco di valle a quello di vetta — ed e' un
// invariante verificato in fondo al file, perche' un sentiero che si allarga o si stringe da solo
// e' un errore di battitura nella tabella dei tornanti, non una scelta di design.
constexpr int MONTE_INGINO_PATH_HALF_WIDTH = 2;   // 2*2+1 = 5 tile calpestabili per colonna

// I TORNANTI, come polilinea. Ogni punto e' (x, y del centro del sentiero in quella colonna); fra
// due punti consecutivi il centro si interpola linearmente. E' la STESSA tabella che il mirror
// Python di tools/make_monte_ingino_art.py deve riprodurre: se le due tabelle divergessero, il
// suolo disegnato non combacerebbe piu' con la griglia di collisione.
struct MonteInginoWaypoint { int x; int y; };

constexpr MonteInginoWaypoint MONTE_INGINO_PATH[] = {
    {0, 15},    // ingresso da valle (Duomo/Ducale), sul bordo sud
    {12, 15},   // tratto in piano prima del primo tornante
    {18, 4},    // primo tornante: sale verso l'alto schermo (ovest)
    {28, 4},    // primo belvedere, in piano lungo il bordo alto
    {34, 27},   // secondo tornante: attraversa tutta l'altezza verso il basso schermo (est).
                // E' il tratto piu' ripido, e per questo e' quello scalinato (vedi sotto).
    {44, 27},   // secondo belvedere, in piano lungo il bordo basso
    {50, 24},   // ultimo tornante, piu' dolce, si riporta verso il centro
    {63, 24},   // uscita verso la Basilica, sul bordo nord
};
constexpr int MONTE_INGINO_PATH_COUNT = int(sizeof(MONTE_INGINO_PATH) / sizeof(MONTE_INGINO_PATH[0]));

static_assert([]
{
    for(int i = 0; i + 1 < MONTE_INGINO_PATH_COUNT; ++i)
    {
        if(MONTE_INGINO_PATH[i].x >= MONTE_INGINO_PATH[i + 1].x)
        {
            return false;
        }
    }

    return true;
}(), "I punti dei tornanti devono avere x strettamente crescente, o l'interpolazione non ha senso");

// Interpolazione lineare in aritmetica intera fra i due punti che racchiudono x. Zero virgola
// mobile (AGENTS.md): solo `int`, come tutta la griglia di collisione.
[[nodiscard]] inline constexpr int monte_ingino_path_center_y(int x)
{
    for(int i = 0; i + 1 < MONTE_INGINO_PATH_COUNT; ++i)
    {
        int x0 = MONTE_INGINO_PATH[i].x;
        int x1 = MONTE_INGINO_PATH[i + 1].x;

        if(x <= x1 || i + 2 == MONTE_INGINO_PATH_COUNT)
        {
            int y0 = MONTE_INGINO_PATH[i].y;
            int y1 = MONTE_INGINO_PATH[i + 1].y;

            return y0 + (y1 - y0) * (x - x0) / (x1 - x0);
        }
    }

    return MONTE_INGINO_PATH[MONTE_INGINO_PATH_COUNT - 1].y;   // irraggiungibile: x resta 0..63
}

// Il tratto piu' ripido (il secondo tornante, quello che attraversa tutta l'altezza): qui la
// salita si fa a gradini, uno dei tre segni ammessi per il dislivello (docs sez. 2).
constexpr int MONTE_INGINO_STAIRS_FIRST_X = 34 - 6;   // 28: inizio del tornante ripido
constexpr int MONTE_INGINO_STAIRS_LAST_X  = 34;       // fine del tornante ripido

// I due belvedere, dove il sentiero corre in piano lungo un bordo: qui il parapetto sostituisce
// il muretto sul lato esterno, ed e' l'affaccio da cui si vede la citta' sempre piu' in basso
// (docs sez. 2, terzo segno ammesso per il dislivello).
constexpr int MONTE_INGINO_BELVEDERE_OVEST_FIRST_X = 18;   // fascia alta (y piccola)
constexpr int MONTE_INGINO_BELVEDERE_OVEST_LAST_X  = 28;
constexpr int MONTE_INGINO_BELVEDERE_EST_FIRST_X   = 34;   // fascia bassa (y grande)
constexpr int MONTE_INGINO_BELVEDERE_EST_LAST_X    = 44;

// Il fontanile di sosta: l'unico arredo lungo la salita, sul primo belvedere. Calpestabile e non
// e' un varco (riusa FOUNTAIN, che ne' is_solid() ne' is_transition() trattano come tale).
constexpr int MONTE_INGINO_FONTANILE_X = 23;
constexpr int MONTE_INGINO_FONTANILE_Y = 4;

// I due varchi, sui bordi corti. La larghezza (5 tile) e' la STESSA del sentiero in quel punto:
// il varco non e' una piazzola aggiunta, e' la sezione del sentiero che tocca il bordo mappa —
// esattamente come in bottaccione_collision.h.
constexpr int MONTE_INGINO_VARCO_VALLE_FIRST_Y = 13;   // bordo sud (x=0), verso Duomo/Ducale
constexpr int MONTE_INGINO_VARCO_VALLE_LAST_Y  = 17;
constexpr int MONTE_INGINO_VARCO_VETTA_FIRST_Y = 22;   // bordo nord (x=WIDTH-1), verso la Basilica
constexpr int MONTE_INGINO_VARCO_VETTA_LAST_Y  = 26;

static_assert(MONTE_INGINO_VARCO_VALLE_LAST_Y - MONTE_INGINO_VARCO_VALLE_FIRST_Y ==
                  2 * MONTE_INGINO_PATH_HALF_WIDTH,
              "Il varco di valle deve essere largo quanto il sentiero");
static_assert(MONTE_INGINO_VARCO_VETTA_LAST_Y - MONTE_INGINO_VARCO_VETTA_FIRST_Y ==
                  2 * MONTE_INGINO_PATH_HALF_WIDTH,
              "Il varco di vetta deve essere largo quanto il sentiero");

// Dove il giocatore compare arrivando da ciascuna area confinante (docs sez. 5). ALMENO SEI TILE
// dentro il sentiero, non a un passo dal proprio varco (AGENTS.md, il ciclo di transizione: a un
// passo dal varco basta tenere premuta la direzione da cui si e' arrivati per rimbalzare
// all'infinito fra le due aree — gia' ricomparso una volta).
//
// PREFISSATE CON MONTE_INGINO_, non semplicemente INGRESSO_DA_<AREA> come mostra il contratto
// alla lettera (sez. 5): AGENTS.md lo vieta esplicitamente, perche' tutte le aree vivono nello
// stesso `namespace gubbio::maps` e un `INGRESSO_DA_BASILICA_X` senza prefisso qui collide col
// primo altro file che definisse a sua volta un ingresso dalla Basilica senza prefisso — e'
// gia' successo tre volte nella prima tornata del progetto.
constexpr int MONTE_INGINO_INGRESSO_DA_DUOMO_DUCALE_X = 8;    // 8 tile dal varco di valle (x=0)
constexpr int MONTE_INGINO_INGRESSO_DA_DUOMO_DUCALE_Y = 15;
constexpr int MONTE_INGINO_INGRESSO_DA_BASILICA_X = 55;       // 8 tile dal varco di vetta (x=63)
constexpr int MONTE_INGINO_INGRESSO_DA_BASILICA_Y = 24;

static_assert(MONTE_INGINO_INGRESSO_DA_DUOMO_DUCALE_X - 0 >= 6,
              "INGRESSO_DA_DUOMO_DUCALE troppo vicino al proprio varco: ciclo di transizione");
static_assert((MONTE_INGINO_WIDTH - 1) - MONTE_INGINO_INGRESSO_DA_BASILICA_X >= 6,
              "INGRESSO_DA_BASILICA troppo vicino al proprio varco: ciclo di transizione");

// USCITA 4 -> Duomo, Giardini Pensili e Palazzo Ducale, a valle. USCITA 5 -> la Basilica di
// Sant'Ubaldo, in vetta. Come sempre (docs sez. 5) le uscite non sanno dove portano: e' MAPS[] in
// map_data.h a deciderlo. Qui si dichiara solo che i tile 4 e 5 esistono e dove.
[[nodiscard]] inline constexpr uint8_t monte_ingino_tile_type(int x, int y)
{
    if(x < 0 || x >= MONTE_INGINO_WIDTH || y < 0 || y >= MONTE_INGINO_HEIGHT)
    {
        return uint8_t(TileType::WALL);
    }

    // Bordo sud (x == 0): il varco verso Duomo/Ducale, a valle.
    if(x == 0)
    {
        if(y >= MONTE_INGINO_VARCO_VALLE_FIRST_Y && y <= MONTE_INGINO_VARCO_VALLE_LAST_Y)
        {
            return uint8_t(TileType::EXIT_SAN_MARTINO);    // valore 4: USCITA verso Duomo/Ducale
        }

        return uint8_t(TileType::WALL);
    }

    // Bordo nord (x == WIDTH-1): il varco verso la Basilica, in vetta.
    if(x == MONTE_INGINO_WIDTH - 1)
    {
        if(y >= MONTE_INGINO_VARCO_VETTA_FIRST_Y && y <= MONTE_INGINO_VARCO_VETTA_LAST_Y)
        {
            return uint8_t(TileType::EXIT_PORTA_ROMANA);   // valore 5: USCITA verso la Basilica
        }

        return uint8_t(TileType::WALL);
    }

    // Il fontanile di sosta, unico arredo del sentiero.
    if(x == MONTE_INGINO_FONTANILE_X && y == MONTE_INGINO_FONTANILE_Y)
    {
        return uint8_t(TileType::FOUNTAIN);
    }

    int centro = monte_ingino_path_center_y(x);
    int distanza = (y >= centro) ? (y - centro) : (centro - y);

    if(distanza <= MONTE_INGINO_PATH_HALF_WIDTH)
    {
        // Sul sentiero. Sterrato, salvo il tornante ripido, che e' scalinato.
        if(x >= MONTE_INGINO_STAIRS_FIRST_X && x <= MONTE_INGINO_STAIRS_LAST_X)
        {
            return uint8_t(TileType::STAIRS);
        }

        return uint8_t(TileType::GROUND);   // sterrato: NON e' ciottolato (ROAD), qui non c'e'
                                             // pavimentazione, e' terra battuta di montagna.
    }

    // Fuori dal sentiero: sui due belvedere il lato esterno ha il parapetto, il resto e' muretto
    // a secco o bosco di lecci (docs sez. 2: muri di sostegno e affacci, gli altri due segni
    // ammessi per il dislivello, insieme alle scalinate di sopra).
    if(x >= MONTE_INGINO_BELVEDERE_OVEST_FIRST_X && x <= MONTE_INGINO_BELVEDERE_OVEST_LAST_X &&
       y < centro)
    {
        return uint8_t(TileType::RAILING);
    }

    if(x >= MONTE_INGINO_BELVEDERE_EST_FIRST_X && x <= MONTE_INGINO_BELVEDERE_EST_LAST_X &&
       y > centro)
    {
        return uint8_t(TileType::RAILING);
    }

    return uint8_t(TileType::WALL);   // muretto a secco / bosco di lecci
}

// Griglia materializzata in ROM, come PIAZZA_GRID, BARGELLO_GRID e BOTTACCIONE_GRID.
struct MonteInginoGrid
{
    uint8_t data[MONTE_INGINO_WIDTH * MONTE_INGINO_HEIGHT];
};

[[nodiscard]] consteval MonteInginoGrid make_monte_ingino_grid()
{
    MonteInginoGrid grid{};

    for(int y = 0; y < MONTE_INGINO_HEIGHT; ++y)
    {
        for(int x = 0; x < MONTE_INGINO_WIDTH; ++x)
        {
            grid.data[x + y * MONTE_INGINO_WIDTH] = monte_ingino_tile_type(x, y);
        }
    }

    return grid;
}

inline constexpr MonteInginoGrid MONTE_INGINO_GRID = make_monte_ingino_grid();

// --- static_assert obbligatorie (docs/mappa_del_mondo.md sez. 5) ------------------------------

// 1. Ogni uscita dichiarata esiste davvero nella griglia ed e' calpestabile.
static_assert(MONTE_INGINO_GRID.data[0 + 15 * MONTE_INGINO_WIDTH] ==
                  uint8_t(TileType::EXIT_SAN_MARTINO),
              "Il varco di valle deve stare sul bordo sud (x=0)");
static_assert(! is_solid(MONTE_INGINO_GRID.data[0 + 15 * MONTE_INGINO_WIDTH]) &&
              is_transition(MONTE_INGINO_GRID.data[0 + 15 * MONTE_INGINO_WIDTH]),
              "L'uscita verso Duomo/Ducale non e' un trigger calpestabile");

static_assert(MONTE_INGINO_GRID.data[(MONTE_INGINO_WIDTH - 1) + 24 * MONTE_INGINO_WIDTH] ==
                  uint8_t(TileType::EXIT_PORTA_ROMANA),
              "Il varco di vetta deve stare sul bordo nord (x=WIDTH-1)");
static_assert(! is_solid(MONTE_INGINO_GRID.data[(MONTE_INGINO_WIDTH - 1) + 24 * MONTE_INGINO_WIDTH]) &&
              is_transition(MONTE_INGINO_GRID.data[(MONTE_INGINO_WIDTH - 1) + 24 * MONTE_INGINO_WIDTH]),
              "L'uscita verso la Basilica non e' un trigger calpestabile");

// 2. Ogni INGRESSO_DA_* cade su un tile calpestabile.
static_assert(! is_solid(MONTE_INGINO_GRID.data[MONTE_INGINO_INGRESSO_DA_DUOMO_DUCALE_X +
                                                 MONTE_INGINO_INGRESSO_DA_DUOMO_DUCALE_Y *
                                                     MONTE_INGINO_WIDTH]),
              "INGRESSO_DA_DUOMO_DUCALE cade dentro un muro: il giocatore ci resterebbe chiuso");
static_assert(! is_solid(MONTE_INGINO_GRID.data[MONTE_INGINO_INGRESSO_DA_BASILICA_X +
                                                 MONTE_INGINO_INGRESSO_DA_BASILICA_Y *
                                                     MONTE_INGINO_WIDTH]),
              "INGRESSO_DA_BASILICA cade dentro un muro: il giocatore ci resterebbe chiuso");

// 3. Almeno un punto notevole per lato, con un messaggio che fissa l'orientamento. Se qualcuno
// ruotasse di nuovo la mappa (docs sez. 3, il tranello del ribaltamento), si deve fermare qui.
static_assert(MONTE_INGINO_GRID.data[0 + 15 * MONTE_INGINO_WIDTH] == uint8_t(TileType::EXIT_SAN_MARTINO),
              "SINISTRA SCHERMO = SUD reale: e' li' che deve stare il varco verso Duomo/Ducale, a valle");
static_assert(MONTE_INGINO_GRID.data[(MONTE_INGINO_WIDTH - 1) + 24 * MONTE_INGINO_WIDTH] ==
                  uint8_t(TileType::EXIT_PORTA_ROMANA),
              "DESTRA SCHERMO = NORD reale: e' li' che deve stare il varco verso la Basilica, in vetta");
static_assert(MONTE_INGINO_GRID.data[23 + 0 * MONTE_INGINO_WIDTH] == uint8_t(TileType::RAILING),
              "ALTO SCHERMO = OVEST reale: qui c'e' il parapetto del primo belvedere");
static_assert(MONTE_INGINO_GRID.data[38 + 31 * MONTE_INGINO_WIDTH] == uint8_t(TileType::RAILING),
              "BASSO SCHERMO = EST reale: qui c'e' il parapetto del secondo belvedere");

// Guardia contro il ribaltamento: le due uscite non possono essere scambiate. Se sud e nord
// fossero invertiti questo assert cadrebbe mentre la mappa continuerebbe comunque a compilare —
// il difetto gia' capitato una volta in Piazza Grande (docs sez. 3).
static_assert(MONTE_INGINO_GRID.data[0 + 15 * MONTE_INGINO_WIDTH] !=
                  MONTE_INGINO_GRID.data[(MONTE_INGINO_WIDTH - 1) + 24 * MONTE_INGINO_WIDTH],
              "I due varchi non possono avere lo stesso valore: sarebbe un ribaltamento");

// 4. Nessun monumento e' dichiarato in quest'area: e' un sentiero di montagna fra muretti a secco
// e bosco di lecci, non un edificio misurabile per fronte. respects_scale() di city_reference.h
// non si applica: non c'e' nulla da verificare in LANDMARKS per gli stradoni del Monte Ingino
// (stesso ragionamento di bottaccione_collision.h per la Gola del Bottaccione).

// L'invariante che rende i tornanti un fatto della griglia, non solo della prosa: il sentiero
// resta largo ESATTAMENTE 5 tile per ogni colonna, dal varco di valle a quello di vetta. Se una
// colonna si allargasse o si stringesse, il gioco cambierebbe difficolta' senza che nessuno
// l'abbia deciso — lo stesso controllo che bottaccione_collision.h fa sul proprio camminamento.
static_assert([]
{
    for(int x = 0; x < MONTE_INGINO_WIDTH; ++x)
    {
        int larghezza = 0;

        for(int y = 0; y < MONTE_INGINO_HEIGHT; ++y)
        {
            if(! is_solid(MONTE_INGINO_GRID.data[x + y * MONTE_INGINO_WIDTH]))
            {
                ++larghezza;
            }
        }

        if(larghezza != 2 * MONTE_INGINO_PATH_HALF_WIDTH + 1)
        {
            return false;
        }
    }

    return true;
}(), "Il sentiero deve restare largo 5 tile per tutta la salita, tornanti compresi");

static_assert(sizeof(MonteInginoGrid) == MONTE_INGINO_WIDTH * MONTE_INGINO_HEIGHT,
              "La griglia deve restare un blocco contiguo di byte");

} // namespace gubbio::maps

#endif // MONTE_INGINO_COLLISION_H
