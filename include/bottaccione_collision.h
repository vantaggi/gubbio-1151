#ifndef BOTTACCIONE_COLLISION_H
#define BOTTACCIONE_COLLISION_H

#include <stdint.h>

#include "piazza_grande_collision.h"   // per TileType, is_solid, is_transition, TILE_SIZE_PX

namespace gubbio::maps {

// STRADA E GOLA DEL BOTTACCIONE — l'acquedotto medievale dietro il Monte Ingino
// (docs/mappa_del_mondo.md sez. 1-2, GDD Sez. 22).
//
// COSA E'. La seconda meta' dell'anello: dalla Basilica di Sant'Ubaldo (vetta, 380 m) si scende
// DIETRO il monte, sul versante ovest, lungo il camminamento stretto dell'acquedotto medievale,
// fra pareti calcaree scure segnate dalle vene di roccia K-T — lo stesso strato geologico che ha
// reso la Gola del Bottaccione un riferimento per i geologi (Alvarez, 1980). Si rientra in citta'
// dalla Porta di Santa Lucia, nel quartiere di San Martino.
//
// MISURE E LA DISCREPANZA DICHIARATA. Il GDD (Sez. 22) descrive questo dungeon come "a
// scorrimento verticale, 256x1024 px". 1024 px NON e' un'altezza BG legale sul GBA (solo 256 o
// 512): un BMP cosi' non esiste e la build muore. Si usa quindi 256x512 — meta' dell'altezza
// descritta — che resta comunque un BG regolare legale. La discrepanza e' voluta e sta scritta
// qui: chi legge il GDD dopo questo file sappia che il numero e' cambiato per un vincolo
// hardware, non per una svista.
constexpr int BOTTACCIONE_WIDTH  = 32;   // tile, 256 px. x cresce verso NORD
constexpr int BOTTACCIONE_HEIGHT = 64;   // tile, 512 px (non 1024: vedi sopra). y cresce verso EST

constexpr int BOTTACCIONE_WIDTH_PX  = BOTTACCIONE_WIDTH * TILE_SIZE_PX;    // 256
constexpr int BOTTACCIONE_HEIGHT_PX = BOTTACCIONE_HEIGHT * TILE_SIZE_PX;   // 512

// QUOTA. L'area non ha una quota unica: scende da 300 a 30 m (docs/mappa_del_mondo.md sez. 2),
// l'unica dell'anello a cui il contratto assegna un intervallo invece di un numero. Il contratto
// tecnico (sez. 5) chiede pero' una singola costante `<NOME>_QUOTA_M`: si usa la quota di testa,
// quella da cui si comincia scendendo dalla Basilica, e si dichiarano ANCHE i due estremi perche'
// chi cuce le aree in `map_data.h` sappia che il dislivello e' interno a questa mappa, non solo
// fra questa e le vicine.
constexpr int BOTTACCIONE_QUOTA_TOP_M    = 300;   // presso l'ingresso dalla Basilica, a monte
constexpr int BOTTACCIONE_QUOTA_BOTTOM_M = 30;    // presso l'uscita a San Martino, Porta S. Lucia
constexpr int BOTTACCIONE_QUOTA_M = BOTTACCIONE_QUOTA_TOP_M;   // <NOME>_QUOTA_M richiesto dal contratto

static_assert(BOTTACCIONE_QUOTA_BOTTOM_M < BOTTACCIONE_QUOTA_TOP_M,
              "La quota di valle (San Martino) deve restare sotto quella di monte (Basilica)");

// --- LA DISPOSIZIONE, E IL SUO ORIENTAMENTO --------------------------------------------------
//
// Uguale a tutte le aree (docs/mappa_del_mondo.md sez. 3): ALTO SCHERMO = OVEST reale, BASSO
// SCHERMO = EST reale, SINISTRA SCHERMO = SUD reale, DESTRA SCHERMO = NORD reale.
//
// Qui l'orientamento fissa anche il senso della discesa: la Basilica, "a monte", sta all'ALTO
// SCHERMO (y piccola); San Martino, piu' in basso, sta al BASSO SCHERMO (y grande). Camminare con
// y crescente e' scendere — cio' che il GDD chiama "scorrimento verticale" e' esattamente lo
// scorrere della camera lungo l'asse lungo (64 tile) della mappa, dall'alto verso il basso.
//
//        ALTO SCHERMO (y piccola)    = OVEST reale  -> ingresso dalla Basilica, a monte
//        BASSO SCHERMO (y grande)    = EST reale    -> uscita a San Martino, Porta di Santa Lucia
//        SINISTRA SCHERMO (x piccola) = SUD reale   -> il vuoto della gola, oltre il parapetto
//        DESTRA SCHERMO (x grande)   = NORD reale   -> la roccia viva del monte, contro cui
//                                                       l'acquedotto e' addossato
//
// Il camminamento e' stretto per tutta la mappa — "largo 2 tile" (Sez. 22 GDD) non e' una
// descrizione approssimativa, e' un vincolo che la static_assert in fondo verifica riga per riga.
// Da qui la scelta di NON allargarlo agli estremi per fare spazio alle uscite: le uscite stanno
// sulle stesse due colonne del camminamento, non su una piazzola aggiunta.

// Colonne, in ordine da SUD (x piccola) a NORD (x grande). Tutto cio' che non e' esplicitamente
// elencato qui e' non calpestabile: a ovest del parapetto e' il vuoto della gola, a est della
// roccia viva e' il corpo del monte. Non serve elencarli: la funzione sotto lo fa ricadendo sul
// caso finale.
constexpr int BOTTACCIONE_RAILING_X             = 9;    // il parapetto sul lato SUD, sul vuoto della gola
constexpr int BOTTACCIONE_CAMMINAMENTO_FIRST_X  = 10;   // il camminamento, 2 tile: le uscite stanno qui sopra
constexpr int BOTTACCIONE_CAMMINAMENTO_LAST_X   = 11;
constexpr int BOTTACCIONE_ROCCIA_X              = 12;   // la roccia viva che borda il cammino sul lato NORD

// Dove il giocatore compare arrivando da ciascuna area confinante (docs/mappa_del_mondo.md
// sez. 5): ALMENO SEI TILE dentro il camminamento, non a un passo dalla tessera di uscita. Un
// corridoio largo 2 tile rende il ciclo di transizione particolarmente facile da innescare: a un
// passo dal varco basta tenere premuta la direzione da cui si e' arrivati per rimbalzare
// all'infinito fra le due aree (AGENTS.md/mappa_del_mondo.md sez. 5, gia' capitato tre volte).
// Sei tile di margine, come per tutte le altre aree.
//
// PREFISSATE CON BOTTACCIONE_, e non semplicemente INGRESSO_DA_<AREA> come mostra il contratto
// alla lettera (sez. 5): AGENTS.md lo vieta esplicitamente, perche' tutte le aree vivono nello
// stesso `namespace gubbio::maps` e un `INGRESSO_DA_BASILICA_X` senza prefisso, dichiarato qui,
// collide col primo altro file che definisse a sua volta un ingresso dalla Basilica o da San
// Martino senza prefisso — e' gia' successo tre volte nella prima tornata del progetto. Lo stesso
// prefisso vale per BOTTACCIONE_RAILING_X, BOTTACCIONE_CAMMINAMENTO_FIRST_X/LAST_X e
// BOTTACCIONE_ROCCIA_X qui sopra: nomi generici come RAILING_X sarebbero i primi a scontrarsi con
// una qualunque altra area che disegnasse un affaccio.
constexpr int BOTTACCIONE_INGRESSO_DA_BASILICA_X = BOTTACCIONE_CAMMINAMENTO_FIRST_X;
constexpr int BOTTACCIONE_INGRESSO_DA_BASILICA_Y = 6;
constexpr int BOTTACCIONE_INGRESSO_DA_SAN_MARTINO_X = BOTTACCIONE_CAMMINAMENTO_FIRST_X;
constexpr int BOTTACCIONE_INGRESSO_DA_SAN_MARTINO_Y = BOTTACCIONE_HEIGHT - 7;

static_assert(BOTTACCIONE_INGRESSO_DA_BASILICA_Y >= 6,
              "L'ingresso da Basilica deve stare ad almeno 6 tile dalla propria uscita (y=0)");
static_assert((BOTTACCIONE_HEIGHT - 1) - BOTTACCIONE_INGRESSO_DA_SAN_MARTINO_Y >= 6,
              "L'ingresso da San Martino deve stare ad almeno 6 tile dalla propria uscita "
              "(y=HEIGHT-1)");

// USCITA 4 -> Basilica, verso OVEST (a monte). USCITA 5 -> San Martino, verso EST (Porta di Santa
// Lucia). I valori numerici sono quelli di EXIT_SAN_MARTINO e EXIT_PORTA_ROMANA in
// piazza_grande_collision.h: le uscite non sanno dove portano (docs/mappa_del_mondo.md sez. 5),
// e' MAPS[] in map_data.h a deciderlo. Qui si dichiara solo che i tile 4 e 5 esistono e dove.
[[nodiscard]] inline constexpr uint8_t bottaccione_tile_type(int x, int y)
{
    if(x < 0 || x >= BOTTACCIONE_WIDTH || y < 0 || y >= BOTTACCIONE_HEIGHT)
    {
        return uint8_t(TileType::WALL);
    }

    // Il camminamento, con le due uscite alle estremita' della discesa.
    if(x >= BOTTACCIONE_CAMMINAMENTO_FIRST_X && x <= BOTTACCIONE_CAMMINAMENTO_LAST_X)
    {
        if(y == 0)
        {
            return uint8_t(TileType::EXIT_SAN_MARTINO);    // valore 4: USCITA verso la Basilica
        }

        if(y == BOTTACCIONE_HEIGHT - 1)
        {
            return uint8_t(TileType::EXIT_PORTA_ROMANA);   // valore 5: USCITA verso San Martino
        }

        return uint8_t(TileType::ROAD);
    }

    // Il parapetto: blocca il passo, non la vista, come in Piazza Grande.
    if(x == BOTTACCIONE_RAILING_X)
    {
        return uint8_t(TileType::RAILING);
    }

    // La roccia viva addossata al camminamento sul lato a monte.
    if(x == BOTTACCIONE_ROCCIA_X)
    {
        return uint8_t(TileType::PRETORIO_FACADE);   // riuso: stesso trattamento, pietra
    }

    // Tutto il resto: a SUD del parapetto il vuoto della gola, a NORD della roccia il corpo del
    // monte. Nessuno dei due si attraversa.
    return uint8_t(TileType::WALL);
}

// Griglia materializzata in ROM, come PIAZZA_GRID, BARGELLO_GRID e SANT_ANDREA_GRID.
struct BottaccioneGrid
{
    uint8_t data[BOTTACCIONE_WIDTH * BOTTACCIONE_HEIGHT];
};

[[nodiscard]] consteval BottaccioneGrid make_bottaccione_grid()
{
    BottaccioneGrid grid{};

    for(int y = 0; y < BOTTACCIONE_HEIGHT; ++y)
    {
        for(int x = 0; x < BOTTACCIONE_WIDTH; ++x)
        {
            grid.data[x + y * BOTTACCIONE_WIDTH] = bottaccione_tile_type(x, y);
        }
    }

    return grid;
}

inline constexpr BottaccioneGrid BOTTACCIONE_GRID = make_bottaccione_grid();

// --- static_assert obbligatorie (docs/mappa_del_mondo.md sez. 5) ------------------------------

// 1. Ogni uscita dichiarata esiste davvero nella griglia ed e' calpestabile.
static_assert(BOTTACCIONE_GRID.data[BOTTACCIONE_CAMMINAMENTO_FIRST_X + 0 * BOTTACCIONE_WIDTH] ==
                  uint8_t(TileType::EXIT_SAN_MARTINO),
              "L'uscita verso la Basilica deve stare sul bordo ovest (y=0)");
static_assert(! is_solid(BOTTACCIONE_GRID.data[BOTTACCIONE_CAMMINAMENTO_FIRST_X + 0 * BOTTACCIONE_WIDTH]),
              "L'uscita verso la Basilica non e' calpestabile");
static_assert(is_transition(BOTTACCIONE_GRID.data[BOTTACCIONE_CAMMINAMENTO_FIRST_X + 0 * BOTTACCIONE_WIDTH]),
              "Il tile dell'uscita verso la Basilica non e' riconosciuto come trigger");

static_assert(BOTTACCIONE_GRID.data[BOTTACCIONE_CAMMINAMENTO_FIRST_X +
                                     (BOTTACCIONE_HEIGHT - 1) * BOTTACCIONE_WIDTH] ==
                  uint8_t(TileType::EXIT_PORTA_ROMANA),
              "L'uscita verso San Martino deve stare sul bordo est (y=HEIGHT-1)");
static_assert(! is_solid(BOTTACCIONE_GRID.data[BOTTACCIONE_CAMMINAMENTO_FIRST_X +
                                                (BOTTACCIONE_HEIGHT - 1) * BOTTACCIONE_WIDTH]),
              "L'uscita verso San Martino non e' calpestabile");
static_assert(is_transition(BOTTACCIONE_GRID.data[BOTTACCIONE_CAMMINAMENTO_FIRST_X +
                                                    (BOTTACCIONE_HEIGHT - 1) * BOTTACCIONE_WIDTH]),
              "Il tile dell'uscita verso San Martino non e' riconosciuto come trigger");

// 2. Ogni INGRESSO_DA_* cade su un tile calpestabile.
static_assert(! is_solid(BOTTACCIONE_GRID.data[BOTTACCIONE_INGRESSO_DA_BASILICA_X +
                                                BOTTACCIONE_INGRESSO_DA_BASILICA_Y * BOTTACCIONE_WIDTH]),
              "BOTTACCIONE_INGRESSO_DA_BASILICA cade dentro un muro: il giocatore ci resterebbe chiuso");
static_assert(! is_solid(BOTTACCIONE_GRID.data[BOTTACCIONE_INGRESSO_DA_SAN_MARTINO_X +
                                                BOTTACCIONE_INGRESSO_DA_SAN_MARTINO_Y * BOTTACCIONE_WIDTH]),
              "BOTTACCIONE_INGRESSO_DA_SAN_MARTINO cade dentro un muro: il giocatore ci resterebbe chiuso");

// 3. Almeno un punto notevole per ogni lato, con un messaggio che fissa l'orientamento.
static_assert(BOTTACCIONE_GRID.data[BOTTACCIONE_CAMMINAMENTO_FIRST_X + 0 * BOTTACCIONE_WIDTH] ==
                  uint8_t(TileType::EXIT_SAN_MARTINO),
              "ALTO SCHERMO = OVEST reale: e' li' che deve stare l'ingresso, a monte verso la Basilica");
static_assert(BOTTACCIONE_GRID.data[BOTTACCIONE_CAMMINAMENTO_FIRST_X +
                                     (BOTTACCIONE_HEIGHT - 1) * BOTTACCIONE_WIDTH] ==
                  uint8_t(TileType::EXIT_PORTA_ROMANA),
              "BASSO SCHERMO = EST reale: e' li' che deve stare l'uscita a valle verso San Martino");
static_assert(BOTTACCIONE_GRID.data[BOTTACCIONE_RAILING_X + 32 * BOTTACCIONE_WIDTH] ==
                  uint8_t(TileType::RAILING),
              "SINISTRA SCHERMO = SUD reale: qui c'e' il parapetto sul vuoto della gola");
static_assert(BOTTACCIONE_GRID.data[BOTTACCIONE_ROCCIA_X + 32 * BOTTACCIONE_WIDTH] ==
                  uint8_t(TileType::PRETORIO_FACADE),
              "DESTRA SCHERMO = NORD reale: qui c'e' la roccia viva del monte");

// Guardia contro il ribaltamento (docs/mappa_del_mondo.md sez. 3): le due uscite non possono
// essere scambiate. Se ovest e est fossero invertiti per errore questo assert cadrebbe mentre la
// mappa continuerebbe comunque a compilare — il difetto gia' capitato una volta in Piazza Grande.
static_assert(BOTTACCIONE_GRID.data[BOTTACCIONE_CAMMINAMENTO_FIRST_X +
                                     (BOTTACCIONE_HEIGHT - 1) * BOTTACCIONE_WIDTH] !=
                  uint8_t(TileType::EXIT_SAN_MARTINO),
              "Il bordo est non puo' avere l'uscita della Basilica: sarebbe un ribaltamento");
static_assert(BOTTACCIONE_GRID.data[BOTTACCIONE_CAMMINAMENTO_FIRST_X + 0 * BOTTACCIONE_WIDTH] !=
                  uint8_t(TileType::EXIT_PORTA_ROMANA),
              "Il bordo ovest non puo' avere l'uscita di San Martino: sarebbe un ribaltamento");

// 4. Nessun monumento e' dichiarato in quest'area: e' un corridoio di dungeon, non un edificio
// misurabile per fronte. respects_scale() di city_reference.h non si applica: non c'e' nulla da
// misurare in LANDMARKS per la Gola del Bottaccione.

// Sanita' del camminamento: resta largo ESATTAMENTE 2 tile per tutta la discesa, come vuole la
// Sez. 22 GDD. E' l'invariante che rende "la caduta laterale punita" un fatto della griglia, non
// solo della prosa: se una riga si allargasse o si chiudesse, il gioco cambierebbe difficolta'
// senza che nessuno l'abbia deciso.
static_assert([]
{
    for(int y = 0; y < BOTTACCIONE_HEIGHT; ++y)
    {
        int larghezza = 0;

        for(int x = 0; x < BOTTACCIONE_WIDTH; ++x)
        {
            if(! is_solid(BOTTACCIONE_GRID.data[x + y * BOTTACCIONE_WIDTH]))
            {
                ++larghezza;
            }
        }

        if(larghezza != 2)
        {
            return false;
        }
    }

    return true;
}(), "Il camminamento deve restare largo 2 tile per tutta la lunghezza (Sez. 22 GDD)");

// Il camminamento e' sempre nella stessa fascia di colonne: verifica che nessuna riga sposti il
// corridoio, che renderebbe l'assert sopra vero per il motivo sbagliato.
static_assert([]
{
    for(int y = 0; y < BOTTACCIONE_HEIGHT; ++y)
    {
        uint8_t a = BOTTACCIONE_GRID.data[BOTTACCIONE_CAMMINAMENTO_FIRST_X + y * BOTTACCIONE_WIDTH];
        uint8_t b = BOTTACCIONE_GRID.data[BOTTACCIONE_CAMMINAMENTO_LAST_X + y * BOTTACCIONE_WIDTH];

        if(is_solid(a) || is_solid(b))
        {
            return false;
        }
    }

    return true;
}(), "Le due colonne del camminamento devono restare calpestabili per tutta la discesa");

static_assert(sizeof(BottaccioneGrid) == BOTTACCIONE_WIDTH * BOTTACCIONE_HEIGHT,
              "La griglia deve restare un blocco contiguo di byte");

} // namespace gubbio::maps

#endif // BOTTACCIONE_COLLISION_H
