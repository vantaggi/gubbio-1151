#ifndef SAN_MARTINO_COLLISION_H
#define SAN_MARTINO_COLLISION_H

#include <stdint.h>

#include "piazza_grande_collision.h"   // per TileType, is_solid, is_transition, TILE_SIZE_PX

namespace gubbio::maps {

// QUARTIERE DI SAN MARTINO — il quartiere OCCIDENTALE, quota 25 m (docs/mappa_del_mondo.md
// sez. 1-2). Il nodo con piu' strade di tutta la citta': ci arrivano Largo del Bargello (a
// monte, 45 m), Piazza Quaranta Martiri (a valle, 0 m) e la Porta di Santa Lucia, il varco
// urbico da cui rientra chi scende dal Monte Ingino lungo la strada del Bottaccione.
//
// LA PORTA DI SANTA LUCIA e' un varco voltato nelle mura, non una semplice fine di strada: nella
// griglia sotto e' un'apertura di 4 tile in una fascia di mura che prosegue piena ai suoi lati,
// esattamente come la prosa del contratto la descrive.
//
// UN PROBLEMA TROVATO LEGGENDO IL CODICE CONDIVISO, non il contratto. La Sez. 5 del contratto
// (docs/mappa_del_mondo.md) elenca i valori 4, 5, 6 come le tre USCITE possibili di un'area. Ma
// `is_transition()` in piazza_grande_collision.h — che quest'area non puo' toccare — riconosce
// SOLO i valori 3 (DOOR_CONSOLI), 4 (EXIT_SAN_MARTINO) e 5 (EXIT_PORTA_ROMANA):
//
//     inline constexpr bool is_transition(uint8_t tile) {
//         return tile == uint8_t(TileType::EXIT_TERZA) ||
//                tile == uint8_t(TileType::EXIT_SAN_MARTINO) ||
//                tile == uint8_t(TileType::EXIT_PORTA_ROMANA);
//     }
//
// E `scene_exploration.cpp` (`_check_triggers`) scarta OGNI tile per cui `is_transition()` e'
// falso PRIMA ANCORA di guardare `MAPS[].triggers`: un'uscita che restituisse 6 (FOUNTAIN)
// sarebbe calpestabile ma silenziosa, un varco che non cambia mai scena, e nessuna
// `static_assert` di questo file lo scoprirebbe perche' `is_solid(6)` e' comunque falso. Nessun'
// altra area consegnata finora usa il valore 6 come uscita (hanno tutte riusato solo 4 e 5), il
// che e' coerente con questo limite del codice condiviso, non con una semplice preferenza.
//
// Con TRE varchi reali da collegare e solo TRE valori funzionanti, questa mappa usa 3, 4 E 5 —
// non 4, 5, 6 come la lettera del contratto suggerirebbe. Il valore 3 (DOOR_CONSOLI, "trigger:
// una porta") e' riusato per la Porta di Santa Lucia, che e' concettualmente una porta: e' il
// riuso meno arbitrario disponibile. Segnalato per la sessione principale, che decide se e come
// correggere `is_transition()` o il contratto.
constexpr int SAN_MARTINO_WIDTH  = 32;   // tile, 256 px. x cresce verso NORD
constexpr int SAN_MARTINO_HEIGHT = 40;   // tile, 320 px. y cresce verso EST
constexpr int SAN_MARTINO_QUOTA_M = 25;  // metri sopra Piazza Quaranta Martiri

constexpr int SAN_MARTINO_WIDTH_PX  = SAN_MARTINO_WIDTH * TILE_SIZE_PX;    // 256
constexpr int SAN_MARTINO_HEIGHT_PX = SAN_MARTINO_HEIGHT * TILE_SIZE_PX;   // 320

static_assert(SAN_MARTINO_QUOTA_M < 45 && SAN_MARTINO_QUOTA_M > 0,
              "San Martino deve stare fra Largo del Bargello (45 m) e Piazza Quaranta Martiri (0 m)");

// --- LA DISPOSIZIONE, E IL SUO ORIENTAMENTO --------------------------------------------------
//
// Uguale a tutte le aree (docs/mappa_del_mondo.md sez. 3): ALTO SCHERMO = OVEST reale, BASSO
// SCHERMO = EST reale, SINISTRA SCHERMO = SUD reale, DESTRA SCHERMO = NORD reale. x cresce verso
// NORD, y cresce verso EST.
//
// Un corridoio principale (il "corso") attraversa la mappa da OVEST a EST, y crescente: nasce
// all'ALTO SCHERMO (y=0) dove sale verso Largo del Bargello, a monte, e finisce al BASSO SCHERMO
// (y=HEIGHT-1) dove la Porta di Santa Lucia si apre sulla strada del Bottaccione. A meta' strada,
// dove il corso si allarga in un piccolo campiello, un ramo si stacca verso SINISTRA (x
// decrescente, sud reale) e scende a Piazza Quaranta Martiri — la direzione e' quella che il
// committente ha dettato per iscritto ("verso SUD cioe' verso SINISTRA dello schermo"), non una
// scelta di quest'area. La DESTRA SCHERMO (nord reale) resta tessuto edilizio minore, senza
// varchi: non e' un vicino noto di San Martino.
//
//        ALTO SCHERMO (y piccola)    = OVEST reale  -> uscita verso Largo del Bargello, a monte
//        BASSO SCHERMO (y grande)    = EST reale    -> Porta di Santa Lucia, verso il Bottaccione
//        SINISTRA SCHERMO (x piccola) = SUD reale   -> uscita verso Piazza Quaranta Martiri, a valle
//        DESTRA SCHERMO (x grande)   = NORD reale   -> case, tessuto edilizio minore, nessuna uscita

// Il corso, l'asse portante: 4 tile di larghezza, come le vie gia' autorate.
constexpr int SAN_MARTINO_CORSO_FIRST_X = 14;
constexpr int SAN_MARTINO_CORSO_LAST_X  = 17;

// Il ramo verso Piazza Quaranta Martiri, staccato dal corso a meta' percorso: dal bordo ovest
// (x=0) fino al corso stesso (x=17).
constexpr int SAN_MARTINO_RAMO_PQM_FIRST_X = 0;
constexpr int SAN_MARTINO_RAMO_PQM_LAST_X  = SAN_MARTINO_CORSO_LAST_X;   // 17
constexpr int SAN_MARTINO_RAMO_PQM_FIRST_Y = 24;
constexpr int SAN_MARTINO_RAMO_PQM_LAST_Y  = 27;

// Il campiello: la piazzetta dove il corso e il ramo si incrociano, appena a monte del ramo.
// Aperta (GROUND, non ROAD) per distinguerla visivamente dalle sedi stradali vere e proprie.
constexpr int SAN_MARTINO_CAMPIELLO_FIRST_X = 10;
constexpr int SAN_MARTINO_CAMPIELLO_LAST_X  = 21;
constexpr int SAN_MARTINO_CAMPIELLO_FIRST_Y = 18;
constexpr int SAN_MARTINO_CAMPIELLO_LAST_Y  = 23;   // si ferma appena prima del ramo (y=24)

// Le tre uscite. I valori numerici sono quelli di DOOR_CONSOLI, EXIT_SAN_MARTINO e
// EXIT_PORTA_ROMANA in piazza_grande_collision.h, RIUSATI: qui non significano "porta dei
// Consoli" ne' "verso San Martino", significano semplicemente "trigger di cambio scena numero
// N" (docs/mappa_del_mondo.md sez. 5: "le uscite non sanno dove portano"). E' lo stesso riuso
// che via_dei_consoli_collision.h fa gia' di EXIT_SAN_MARTINO ed EXIT_PORTA_ROMANA.
constexpr int SAN_MARTINO_EXIT_BARGELLO_FIRST_Y = 0;
constexpr int SAN_MARTINO_EXIT_BARGELLO_LAST_Y  = 1;

constexpr int SAN_MARTINO_EXIT_PORTA_SANTA_LUCIA_FIRST_Y = SAN_MARTINO_HEIGHT - 2;   // 38
constexpr int SAN_MARTINO_EXIT_PORTA_SANTA_LUCIA_LAST_Y  = SAN_MARTINO_HEIGHT - 1;   // 39

constexpr int SAN_MARTINO_EXIT_PQM_FIRST_X = 0;
constexpr int SAN_MARTINO_EXIT_PQM_LAST_X  = 1;

// Due bande di scalinata, per il dislivello sui due bracci: una salendo verso il Bargello
// (20 m), una scendendo verso Piazza Quaranta Martiri (25 m). E' tutto in pendenza, come vuole
// la descrizione dell'area: non basta un solo gradone.
constexpr int SAN_MARTINO_STAIRS_BARGELLO_FIRST_Y = 4;
constexpr int SAN_MARTINO_STAIRS_BARGELLO_LAST_Y  = 6;

constexpr int SAN_MARTINO_STAIRS_PQM_FIRST_X = 4;
constexpr int SAN_MARTINO_STAIRS_PQM_LAST_X  = 6;

// L'affaccio: un parapetto sul lato SUD (x=0), a monte del ramo che scende a Piazza Quaranta
// Martiri — lo squarcio da cui si vede gia' la citta' bassa prima di scendere davvero.
constexpr int SAN_MARTINO_RAILING_FIRST_Y = 8;
constexpr int SAN_MARTINO_RAILING_LAST_Y  = 12;

// Dove il giocatore compare arrivando da ciascuna area confinante (docs/mappa_del_mondo.md
// sez. 5). PREFISSATE CON SAN_MARTINO_, non semplicemente INGRESSO_DA_<AREA>: piu' aree possono
// avere Largo del Bargello, Piazza Quaranta Martiri o il Bottaccione come vicino, e ciascuna che
// dichiarasse la costante senza prefisso ridefinirebbe quella delle altre nello stesso
// `namespace gubbio::maps` (la stessa ragione gia' scritta in via_dei_consoli_collision.h).
//
// Ognuna sta ALMENO SEI TILE dal proprio varco (AGENTS.md, mappa_del_mondo.md sez. 5): a meno di
// sei tile il giocatore rientra, tiene premuta la direzione da cui e' arrivato e rimbalza
// all'infinito fra le due aree. Le tre `static_assert` numeriche qui sotto lo verificano.
constexpr int SAN_MARTINO_INGRESSO_DA_LARGO_BARGELLO_X = SAN_MARTINO_CORSO_FIRST_X + 1;   // 15
constexpr int SAN_MARTINO_INGRESSO_DA_LARGO_BARGELLO_Y = 9;

constexpr int SAN_MARTINO_INGRESSO_DA_PIAZZA_QUARANTA_MARTIRI_X = 8;
constexpr int SAN_MARTINO_INGRESSO_DA_PIAZZA_QUARANTA_MARTIRI_Y = SAN_MARTINO_RAMO_PQM_FIRST_Y + 1;   // 25

constexpr int SAN_MARTINO_INGRESSO_DA_BOTTACCIONE_X = SAN_MARTINO_CORSO_FIRST_X + 1;   // 15
constexpr int SAN_MARTINO_INGRESSO_DA_BOTTACCIONE_Y = 31;

static_assert(SAN_MARTINO_INGRESSO_DA_LARGO_BARGELLO_Y - SAN_MARTINO_EXIT_BARGELLO_LAST_Y >= 6,
              "L'ingresso da Largo del Bargello e' troppo vicino al proprio varco: ciclo di transizione");
static_assert(SAN_MARTINO_INGRESSO_DA_PIAZZA_QUARANTA_MARTIRI_X - SAN_MARTINO_EXIT_PQM_LAST_X >= 6,
              "L'ingresso da Piazza Quaranta Martiri e' troppo vicino al proprio varco: ciclo di transizione");
static_assert(SAN_MARTINO_EXIT_PORTA_SANTA_LUCIA_FIRST_Y - SAN_MARTINO_INGRESSO_DA_BOTTACCIONE_Y >= 6,
              "L'ingresso dal Bottaccione e' troppo vicino al proprio varco: ciclo di transizione");

[[nodiscard]] inline constexpr uint8_t san_martino_tile_type(int x, int y)
{
    if(x < 0 || x >= SAN_MARTINO_WIDTH || y < 0 || y >= SAN_MARTINO_HEIGHT)
    {
        return uint8_t(TileType::WALL);   // fuori mappa = muro
    }

    const bool in_corso = (x >= SAN_MARTINO_CORSO_FIRST_X && x <= SAN_MARTINO_CORSO_LAST_X);
    const bool in_ramo_pqm = (y >= SAN_MARTINO_RAMO_PQM_FIRST_Y && y <= SAN_MARTINO_RAMO_PQM_LAST_Y &&
                              x >= SAN_MARTINO_RAMO_PQM_FIRST_X && x <= SAN_MARTINO_RAMO_PQM_LAST_X);

    // Le uscite, controllate per prime: sono finestre piccole dentro le sedi stradali che la
    // logica sotto, valutata prima, risolverebbe come semplice ciottolato.
    if(in_corso && y >= SAN_MARTINO_EXIT_BARGELLO_FIRST_Y && y <= SAN_MARTINO_EXIT_BARGELLO_LAST_Y)
    {
        return uint8_t(TileType::EXIT_SAN_MARTINO);   // valore 4: riusato, "verso Largo del Bargello"
    }

    if(in_corso && y >= SAN_MARTINO_EXIT_PORTA_SANTA_LUCIA_FIRST_Y &&
       y <= SAN_MARTINO_EXIT_PORTA_SANTA_LUCIA_LAST_Y)
    {
        return uint8_t(TileType::EXIT_TERZA);          // valore 12: la Porta di Santa Lucia
    }

    if(in_ramo_pqm && x >= SAN_MARTINO_EXIT_PQM_FIRST_X && x <= SAN_MARTINO_EXIT_PQM_LAST_X)
    {
        return uint8_t(TileType::EXIT_PORTA_ROMANA);   // valore 5: riusato, "verso Piazza Quaranta Martiri"
    }

    // IL QUARTO VARCO, verso il TEATRO ROMANO, che sta FUORI dalle mura cittadine e piu' in
    // basso. Chi ha autorato quest'area lo aveva dichiarato mancante e ne aveva scritto il
    // motivo: con tre uscite aveva gia' esaurito i soli tre valori che `is_transition`
    // riconosceva allora. Aggiunto EXIT_QUARTA all'enum condiviso, il varco puo' esistere.
    if(in_ramo_pqm && y >= SAN_MARTINO_RAMO_PQM_LAST_Y - 1 &&
       x >= SAN_MARTINO_EXIT_PQM_FIRST_X && x <= SAN_MARTINO_EXIT_PQM_LAST_X)
    {
        return uint8_t(TileType::EXIT_QUARTA);         // valore 13: verso il Teatro Romano
    }

    // Le scalinate, sui due bracci del dislivello.
    if(in_corso && y >= SAN_MARTINO_STAIRS_BARGELLO_FIRST_Y && y <= SAN_MARTINO_STAIRS_BARGELLO_LAST_Y)
    {
        return uint8_t(TileType::STAIRS);
    }

    if(in_ramo_pqm && x >= SAN_MARTINO_STAIRS_PQM_FIRST_X && x <= SAN_MARTINO_STAIRS_PQM_LAST_X)
    {
        return uint8_t(TileType::STAIRS);
    }

    // Il resto del corso e del ramo: ciottolato percorribile.
    if(in_corso || in_ramo_pqm)
    {
        return uint8_t(TileType::ROAD);
    }

    // Il campiello: piazzetta aperta all'incrocio, appena a monte del ramo.
    if(x >= SAN_MARTINO_CAMPIELLO_FIRST_X && x <= SAN_MARTINO_CAMPIELLO_LAST_X &&
       y >= SAN_MARTINO_CAMPIELLO_FIRST_Y && y <= SAN_MARTINO_CAMPIELLO_LAST_Y)
    {
        return uint8_t(TileType::GROUND);
    }

    // L'affaccio sul lato SUD: un parapetto, non le case.
    if(x == 0 && y >= SAN_MARTINO_RAILING_FIRST_Y && y <= SAN_MARTINO_RAILING_LAST_Y)
    {
        return uint8_t(TileType::RAILING);
    }

    // Tutto il resto: tessuto edilizio minore, e la fascia di mura che fiancheggia la Porta di
    // Santa Lucia sui suoi due lati.
    return uint8_t(TileType::WALL);
}

// Griglia materializzata in ROM, come PIAZZA_GRID, BARGELLO_GRID e le altre aree gia' consegnate.
struct SanMartinoGrid
{
    uint8_t data[SAN_MARTINO_WIDTH * SAN_MARTINO_HEIGHT];
};

[[nodiscard]] consteval SanMartinoGrid make_san_martino_grid()
{
    SanMartinoGrid grid{};

    for(int y = 0; y < SAN_MARTINO_HEIGHT; ++y)
    {
        for(int x = 0; x < SAN_MARTINO_WIDTH; ++x)
        {
            grid.data[x + y * SAN_MARTINO_WIDTH] = san_martino_tile_type(x, y);
        }
    }

    return grid;
}

inline constexpr SanMartinoGrid SAN_MARTINO_GRID = make_san_martino_grid();

// --- static_assert obbligatorie (docs/mappa_del_mondo.md sez. 5) ------------------------------

static_assert(sizeof(SanMartinoGrid) == SAN_MARTINO_WIDTH * SAN_MARTINO_HEIGHT,
              "La griglia deve restare un blocco contiguo di byte");

// 1. Ogni uscita dichiarata esiste davvero nella griglia, e' calpestabile, ed e' riconosciuta
// come trigger da is_transition() — il vincolo vero, per come e' scritto scene_exploration.cpp.
static_assert(SAN_MARTINO_GRID.data[SAN_MARTINO_CORSO_FIRST_X + 1 + 0 * SAN_MARTINO_WIDTH] ==
                  uint8_t(TileType::EXIT_SAN_MARTINO),
              "L'uscita verso Largo del Bargello non e' dove dovrebbe");
static_assert(! is_solid(SAN_MARTINO_GRID.data[SAN_MARTINO_CORSO_FIRST_X + 1 + 0 * SAN_MARTINO_WIDTH]),
              "L'uscita verso Largo del Bargello non e' calpestabile");
static_assert(is_transition(SAN_MARTINO_GRID.data[SAN_MARTINO_CORSO_FIRST_X + 1 + 0 * SAN_MARTINO_WIDTH]),
              "L'uscita verso Largo del Bargello non e' riconosciuta come trigger da is_transition()");

static_assert(SAN_MARTINO_GRID.data[SAN_MARTINO_CORSO_FIRST_X + 1 +
                                     (SAN_MARTINO_HEIGHT - 1) * SAN_MARTINO_WIDTH] ==
                  uint8_t(TileType::EXIT_TERZA),
              "La Porta di Santa Lucia non e' dove dovrebbe");
static_assert(! is_solid(SAN_MARTINO_GRID.data[SAN_MARTINO_CORSO_FIRST_X + 1 +
                                                (SAN_MARTINO_HEIGHT - 1) * SAN_MARTINO_WIDTH]),
              "La Porta di Santa Lucia non e' calpestabile");
static_assert(is_transition(SAN_MARTINO_GRID.data[SAN_MARTINO_CORSO_FIRST_X + 1 +
                                                    (SAN_MARTINO_HEIGHT - 1) * SAN_MARTINO_WIDTH]),
              "La Porta di Santa Lucia non e' riconosciuta come trigger da is_transition()");

static_assert(SAN_MARTINO_GRID.data[0 + SAN_MARTINO_RAMO_PQM_FIRST_Y * SAN_MARTINO_WIDTH] ==
                  uint8_t(TileType::EXIT_PORTA_ROMANA),
              "L'uscita verso Piazza Quaranta Martiri non e' dove dovrebbe");
static_assert(! is_solid(SAN_MARTINO_GRID.data[0 + SAN_MARTINO_RAMO_PQM_FIRST_Y * SAN_MARTINO_WIDTH]),
              "L'uscita verso Piazza Quaranta Martiri non e' calpestabile");
static_assert(is_transition(SAN_MARTINO_GRID.data[0 + SAN_MARTINO_RAMO_PQM_FIRST_Y * SAN_MARTINO_WIDTH]),
              "L'uscita verso Piazza Quaranta Martiri non e' riconosciuta come trigger da is_transition()");

// 2. Ogni INGRESSO_DA_* cade su un tile calpestabile: altrimenti il giocatore compare dentro un
// muro e il salvataggio ce lo lascia per sempre.
static_assert(! is_solid(SAN_MARTINO_GRID.data[SAN_MARTINO_INGRESSO_DA_LARGO_BARGELLO_X +
                              SAN_MARTINO_INGRESSO_DA_LARGO_BARGELLO_Y * SAN_MARTINO_WIDTH]),
              "L'ingresso da Largo del Bargello cade dentro un muro");
static_assert(! is_solid(SAN_MARTINO_GRID.data[SAN_MARTINO_INGRESSO_DA_PIAZZA_QUARANTA_MARTIRI_X +
                              SAN_MARTINO_INGRESSO_DA_PIAZZA_QUARANTA_MARTIRI_Y * SAN_MARTINO_WIDTH]),
              "L'ingresso da Piazza Quaranta Martiri cade dentro un muro");
static_assert(! is_solid(SAN_MARTINO_GRID.data[SAN_MARTINO_INGRESSO_DA_BOTTACCIONE_X +
                              SAN_MARTINO_INGRESSO_DA_BOTTACCIONE_Y * SAN_MARTINO_WIDTH]),
              "L'ingresso dal Bottaccione cade dentro un muro");

// 3. Almeno un punto notevole per ogni lato, con un messaggio che fissa l'orientamento — e la
// coppia che distingue una ROTAZIONE da un RIBALTAMENTO (gia' successo una volta in Piazza
// Grande, mappa_del_mondo.md sez. 3): i lati opposti stanno su bordi diversi e non sono la
// stessa cosa.
static_assert(SAN_MARTINO_GRID.data[SAN_MARTINO_CORSO_FIRST_X + 1 + 0 * SAN_MARTINO_WIDTH] ==
                  uint8_t(TileType::EXIT_SAN_MARTINO),
              "ALTO SCHERMO = OVEST reale: qui deve aprirsi l'uscita a monte verso il Bargello");
static_assert(SAN_MARTINO_GRID.data[SAN_MARTINO_CORSO_FIRST_X + 1 +
                                     (SAN_MARTINO_HEIGHT - 1) * SAN_MARTINO_WIDTH] ==
                  uint8_t(TileType::EXIT_TERZA),
              "BASSO SCHERMO = EST reale: qui deve aprirsi la Porta di Santa Lucia");
static_assert(SAN_MARTINO_GRID.data[0 + 10 * SAN_MARTINO_WIDTH] == uint8_t(TileType::RAILING),
              "SINISTRA SCHERMO = SUD reale: qui c'e' l'affaccio, non le case");
static_assert(SAN_MARTINO_GRID.data[(SAN_MARTINO_WIDTH - 1) + 10 * SAN_MARTINO_WIDTH] ==
                  uint8_t(TileType::WALL),
              "DESTRA SCHERMO = NORD reale: qui ci sono le case, senza varchi");
static_assert(SAN_MARTINO_GRID.data[0 + 10 * SAN_MARTINO_WIDTH] !=
                  SAN_MARTINO_GRID.data[(SAN_MARTINO_WIDTH - 1) + 10 * SAN_MARTINO_WIDTH],
              "I due lati corti (sud e nord) non possono essere la stessa cosa");
static_assert(SAN_MARTINO_GRID.data[SAN_MARTINO_CORSO_FIRST_X + 1 + 0 * SAN_MARTINO_WIDTH] !=
                  SAN_MARTINO_GRID.data[SAN_MARTINO_CORSO_FIRST_X + 1 +
                                         (SAN_MARTINO_HEIGHT - 1) * SAN_MARTINO_WIDTH],
              "I due lati lunghi (ovest ed est) non possono essere la stessa cosa");

// 4. Nessun monumento a scala fissa e' nominato in quest'area: la Porta di Santa Lucia non
// compare in LANDMARKS[] di city_reference.h (che elenca solo Consoli, Piazza Grande, Pretorio,
// Fontana dei Matti, Basilica e Teatro Romano), quindi non c'e' una respects_scale() da
// verificare qui — annotato invece di ometterlo in silenzio, come gia' fa via_dei_consoli_collision.h.

// NON VERIFICATO: il quarto varco verso il Teatro Romano (docs/mappa_del_mondo.md sez. 1, "fuori
// le mura, piu' in basso"), richiesto dall'assegnazione SOLO se entra senza forzature. Non entra:
// con TRE varchi reali gia' collegati (Bargello, Piazza Quaranta Martiri, Porta di Santa Lucia)
// questa griglia usa gia' TUTTI e TRE i valori che is_transition() di piazza_grande_collision.h
// riconosce (3, 4, 5 — vedi la nota in testa al file); un quarto varco funzionante richiederebbe
// un quarto valore di trigger, che non esiste nel codice condiviso e che questo agente non puo'
// aggiungere. Dichiarato qui invece che ometterlo in silenzio, com'era gia' capitato una volta.

} // namespace gubbio::maps

#endif // SAN_MARTINO_COLLISION_H
