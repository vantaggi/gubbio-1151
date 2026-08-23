#ifndef BASILICA_COLLISION_H
#define BASILICA_COLLISION_H

#include <stdint.h>

#include "piazza_grande_collision.h"   // per TileType, is_solid, is_transition, TILE_SIZE_PX
#include "city_reference.h"            // per respects_scale(): punto 4 delle static_assert obbligatorie

namespace gubbio::maps {

// BASILICA DI SANT'UBALDO — la vetta del Monte Ingino, quota 380 m (docs/mappa_del_mondo.md
// sez. 2), e il luogo simbolico del gioco: e' dalle vetrate di questa basilica che viene la
// storia dell'assedio del 1151 che il gioco racconta.
//
// ANACRONISMO NOTO E ACCETTATO (docs/mappa_del_mondo.md sez. 7, decisione della Sessione 17):
// la basilica attuale e' successiva alla morte di Sant'Ubaldo, che nel 1151 e' vivo ed e' un
// personaggio giocante. Si costruisce comunque, perche' "vogliamo qualcosa di magnifico anche
// visivamente" e un giocatore che arriva in vetta deve riconoscere l'edificio vero.
//
// COSA C'E'. Una navata unica lunga (in realta' cinque navate, ma si legge come un volume
// lungo), con una scalinata d'accesso e il monte alle spalle; davanti, uno spiazzo panoramico
// da cui si vede tutta la citta' e la piana, chiuso da un parapetto (tile RAILING).
//
// DUE VICINI SOLI (docs/mappa_del_mondo.md sez. 1): si sale dagli Stradoni del Monte (2 km di
// sterrato, la salita lunga del gioco) e si scende, sull'altro versante, verso la Strada del
// Bottaccione. Nessun terzo vicino: qui non serve la USCITA di valore 6.

constexpr int BASILICA_WIDTH  = 64;    // tile. x cresce verso NORD
constexpr int BASILICA_HEIGHT = 32;    // tile. y cresce verso EST
constexpr int BASILICA_QUOTA_M = 380;  // metri sopra Piazza Quaranta Martiri (sez. 2): la vetta

constexpr int BASILICA_WIDTH_PX  = BASILICA_WIDTH * TILE_SIZE_PX;    // 512
constexpr int BASILICA_HEIGHT_PX = BASILICA_HEIGHT * TILE_SIZE_PX;   // 256, un solo blocco BG

// --- LA DISPOSIZIONE, E IL SUO ORIENTAMENTO --------------------------------------------------
//
// Uguale a tutte le aree (docs/mappa_del_mondo.md sez. 3): ALTO SCHERMO = OVEST reale, BASSO
// SCHERMO = EST reale, SINISTRA SCHERMO = SUD reale, DESTRA SCHERMO = NORD reale.
//
// La basilica occupa la fascia ALTA (ovest): la roccia della vetta le sta alle spalle, oltre il
// bordo y=0, e la facciata guarda verso BASSO (est), lo spiazzo panoramico e la vista sulla
// citta'. I due varchi stanno sui fianchi LUNGHI, uno per lato: a SINISTRA (sud) si torna giu'
// dagli Stradoni del Monte, a DESTRA (nord) si scende verso il Bottaccione. Sono fianchi
// OPPOSTI dello stesso spiazzo, non lo stesso lato: se si scambiassero, un giocatore che rientra
// dagli Stradoni si ritroverebbe a uscire verso il Bottaccione — il ribaltamento silenzioso di
// cui parla la sez. 3 del contratto, gia' successo una volta con Piazza Grande.
//
//        ALTO SCHERMO (y piccola)     = OVEST reale  -> roccia della vetta, poi la basilica
//        BASSO SCHERMO (y grande)     = EST reale    -> spiazzo panoramico, parapetto (RAILING)
//        SINISTRA SCHERMO (x piccola) = SUD reale    -> USCITA verso gli Stradoni del Monte
//        DESTRA SCHERMO (x grande)    = NORD reale   -> USCITA verso la Strada del Bottaccione

// La roccia della vetta, dietro la basilica: nessuno ci cammina, e non e' un edificio da mettere
// in scala, e' il monte stesso.
constexpr int BASILICA_ROCCIA_LAST_Y = 1;

// La facciata, fotografata frontale (docs/riferimenti/FONTI.md: "dev'essere frontale... e in
// luce piena"; ingredienti/basilica_facciata.bmp e' 272x160 px, cioe' 34x20 tile). 34 tile e'
// anche il tiles_width della Basilica in city_reference.h::LANDMARKS (50 m reali, entro la
// tolleranza di un tile): i due numeri devono restare uguali, e la static_assert piu' in basso
// lo verifica misurando la griglia invece di fidarsi del commento.
constexpr int BASILICA_FACADE_FIRST_Y = BASILICA_ROCCIA_LAST_Y + 1;    // 2
constexpr int BASILICA_FACADE_LAST_Y  = BASILICA_FACADE_FIRST_Y + 19;  // 21: 20 righe, come la foto
constexpr int BASILICA_FACADE_FIRST_X = 15;
constexpr int BASILICA_FACADE_LAST_X  = 48;   // 34 tile: 48 - 15 + 1

// 50 m reali, la stessa cifra di city_reference.h::LANDMARKS[4].real_width_m: serve qui come
// argomento di respects_scale(), non ricopiata a mente ma tenuta accanto al numero che descrive.
constexpr int BASILICA_FACADE_REAL_WIDTH_M = 50;

// Il portone, al centro del fronte lungo (centro di 15..48 e di 0..63: 31,5 in entrambi i casi,
// non e' un caso). Oggi e' solo VISIVO come DOOR_PRETORIO in piazza_grande_collision.h: non
// porta all'interno della basilica, che non e' un'area assegnata a questo file.
constexpr int BASILICA_PORTONE_X0 = 31;
constexpr int BASILICA_PORTONE_X1 = 32;

// La scalinata d'accesso, una sola fila, centrata sotto il portone.
constexpr int BASILICA_STAIRS_Y       = BASILICA_FACADE_LAST_Y + 1;    // 22
constexpr int BASILICA_STAIRS_FIRST_X = 28;
constexpr int BASILICA_STAIRS_LAST_X  = 35;

// Il parapetto panoramico, sul bordo basso (est): da qui si vede tutta la citta' e la piana
// (docs/mappa_del_mondo.md sez. 2: "Affacci — tile RAILING: dove si guarda in basso").
constexpr int BASILICA_RAILING_FIRST_Y = BASILICA_HEIGHT - 2;   // 30: le ultime due righe

// I due varchi laterali, sui fianchi OPPOSTI dello spiazzo panoramico (righe fra la scalinata e
// il parapetto, cioe' 23..29). Restano separati da una riga di cuscinetto (26) perche' non si
// confondano leggendo la griglia a occhio.
constexpr int BASILICA_VARCO_SUD_LAST_X  = 1;    // fianco sud: gli Stradoni del Monte
constexpr int BASILICA_VARCO_SUD_FIRST_Y = 23;
constexpr int BASILICA_VARCO_SUD_LAST_Y  = 25;

constexpr int BASILICA_VARCO_NORD_FIRST_X = BASILICA_WIDTH - 2;   // 62: fianco nord, il Bottaccione
constexpr int BASILICA_VARCO_NORD_FIRST_Y = 27;
constexpr int BASILICA_VARCO_NORD_LAST_Y  = 29;

static_assert(BASILICA_VARCO_NORD_FIRST_X > BASILICA_VARCO_SUD_LAST_X,
              "I due varchi laterali si sovrappongono");

// Dove il giocatore compare arrivando da ciascun vicino: ALMENO SEI TILE dentro lo spiazzo, non
// a un passo dal proprio varco. Con meno margine basta tenere premuta la direzione da cui si e'
// arrivati per rientrare subito nella tessera di uscita e rimbalzare all'infinito fra le due aree
// (AGENTS.md/docs/mappa_del_mondo.md sez. 5, gia' ricomparso una volta). Sei tile, come per
// bottaccione_collision.h::INGRESSO_DA_BASILICA_Y: qui il varco sud occupa le colonne 0-1, quindi
// 1 + 6 = 7 e' il minimo per l'ingresso dagli Stradoni; il varco nord occupa le colonne 62-63,
// quindi 62 - 6 = 56 e' il massimo per l'ingresso dal Bottaccione.
//
// PREFISSATE CON BASILICA_, e non semplicemente INGRESSO_DA_<AREA> come mostra il contratto alla
// lettera (docs/mappa_del_mondo.md sez. 5). Motivo, lo stesso di via_dei_consoli_collision.h:
// map_data.h include piu' *_collision.h nella STESSA unita' di traduzione, tutti dentro
// `namespace gubbio::maps`. Bottaccione (che confina con questa stessa Basilica) dichiara gia'
// un INGRESSO_DA_BASILICA_X senza prefisso; se un domani un'altra area che confina con gli
// Stradoni del Monte o col Bottaccione definisse a sua volta un INGRESSO_DA_MONTE_INGINO_X o un
// INGRESSO_DA_BOTTACCIONE_X senza prefisso, il secondo a compilare ridefinirebbe il simbolo del
// primo e la build si fermerebbe. Prefissare con il nome della propria area resta dentro la
// lettera del contratto (il NOME del vicino compare comunque, per intero) senza rischiare una
// collisione che nessuno vedrebbe finche' quell'altra area non venisse aggiunta a map_data.h.
constexpr int BASILICA_INGRESSO_DA_MONTE_INGINO_X = 8;    // 7 tile dal varco sud (colonne 0-1)
constexpr int BASILICA_INGRESSO_DA_MONTE_INGINO_Y = 24;

constexpr int BASILICA_INGRESSO_DA_BOTTACCIONE_X = 56;    // 6 tile dal varco nord (colonne 62-63)
constexpr int BASILICA_INGRESSO_DA_BOTTACCIONE_Y = 28;

static_assert(BASILICA_INGRESSO_DA_MONTE_INGINO_X - BASILICA_VARCO_SUD_LAST_X >= 6,
              "L'ingresso dagli Stradoni del Monte e' troppo vicino al proprio varco: ciclo di "
              "transizione");
static_assert(BASILICA_VARCO_NORD_FIRST_X - BASILICA_INGRESSO_DA_BOTTACCIONE_X >= 6,
              "L'ingresso dal Bottaccione e' troppo vicino al proprio varco: ciclo di "
              "transizione");

// USCITA 4 -> Stradoni del Monte (si torna giu' da dove si e' saliti). USCITA 5 -> Strada del
// Bottaccione (si scende dietro il monte, sull'altro versante). Le uscite non sanno dove
// portano (docs/mappa_del_mondo.md sez. 5): qui si dichiara solo che i tile 4 e 5 esistono e
// dove; il cablaggio verso i MapId e' compito di map_data.h.
[[nodiscard]] inline constexpr uint8_t basilica_tile_type(int x, int y)
{
    if(x < 0 || x >= BASILICA_WIDTH || y < 0 || y >= BASILICA_HEIGHT)
    {
        return uint8_t(TileType::WALL);
    }

    // La roccia della vetta, dietro la basilica.
    if(y <= BASILICA_ROCCIA_LAST_Y)
    {
        return uint8_t(TileType::WALL);
    }

    // La facciata della basilica, con il portone al centro del fronte lungo.
    if(y <= BASILICA_FACADE_LAST_Y)
    {
        if(y == BASILICA_FACADE_LAST_Y &&
           (x == BASILICA_PORTONE_X0 || x == BASILICA_PORTONE_X1))
        {
            return uint8_t(TileType::DOOR_PRETORIO);    // solo visivo, come in piazza
        }

        if(x >= BASILICA_FACADE_FIRST_X && x <= BASILICA_FACADE_LAST_X)
        {
            return uint8_t(TileType::CONSOLI_FACADE);   // riuso del valore: l'edificio maggiore
        }

        return uint8_t(TileType::WALL);    // il fianco roccioso oltre la facciata
    }

    // La scalinata d'accesso, sotto il portone.
    if(y == BASILICA_STAIRS_Y)
    {
        if(x >= BASILICA_STAIRS_FIRST_X && x <= BASILICA_STAIRS_LAST_X)
        {
            return uint8_t(TileType::STAIRS);
        }

        return uint8_t(TileType::GROUND);   // selciato davanti alla basilica, ai lati dei gradini
    }

    // Il parapetto panoramico, sul bordo basso: qui la vista si apre su tutta la citta'.
    if(y >= BASILICA_RAILING_FIRST_Y)
    {
        return uint8_t(TileType::RAILING);
    }

    // Lo spiazzo panoramico, coi due varchi sui fianchi opposti.
    if(x <= BASILICA_VARCO_SUD_LAST_X)
    {
        if(y >= BASILICA_VARCO_SUD_FIRST_Y && y <= BASILICA_VARCO_SUD_LAST_Y)
        {
            return uint8_t(TileType::EXIT_SAN_MARTINO);    // valore 4: USCITA verso gli Stradoni
        }

        return uint8_t(TileType::WALL);
    }

    if(x >= BASILICA_VARCO_NORD_FIRST_X)
    {
        if(y >= BASILICA_VARCO_NORD_FIRST_Y && y <= BASILICA_VARCO_NORD_LAST_Y)
        {
            return uint8_t(TileType::EXIT_PORTA_ROMANA);   // valore 5: USCITA verso il Bottaccione
        }

        return uint8_t(TileType::WALL);
    }

    return uint8_t(TileType::GROUND);
}

// Griglia materializzata in ROM, come PIAZZA_GRID, BARGELLO_GRID e SANT_ANDREA_GRID.
struct BasilicaGrid
{
    uint8_t data[BASILICA_WIDTH * BASILICA_HEIGHT];
};

[[nodiscard]] consteval BasilicaGrid make_basilica_grid()
{
    BasilicaGrid grid{};

    for(int y = 0; y < BASILICA_HEIGHT; ++y)
    {
        for(int x = 0; x < BASILICA_WIDTH; ++x)
        {
            grid.data[x + y * BASILICA_WIDTH] = basilica_tile_type(x, y);
        }
    }

    return grid;
}

inline constexpr BasilicaGrid BASILICA_GRID = make_basilica_grid();

// --- static_assert obbligatorie (docs/mappa_del_mondo.md sez. 5) ------------------------------

// 1. Ogni uscita dichiarata esiste davvero nella griglia ed e' calpestabile.
static_assert(BASILICA_GRID.data[0 + BASILICA_VARCO_SUD_FIRST_Y * BASILICA_WIDTH] ==
                  uint8_t(TileType::EXIT_SAN_MARTINO),
              "L'uscita verso gli Stradoni del Monte (valore 4) non e' dove dichiarato");
static_assert(! is_solid(BASILICA_GRID.data[0 + BASILICA_VARCO_SUD_FIRST_Y * BASILICA_WIDTH]) &&
              is_transition(BASILICA_GRID.data[0 + BASILICA_VARCO_SUD_FIRST_Y * BASILICA_WIDTH]),
              "L'uscita verso gli Stradoni del Monte deve essere calpestabile e riconosciuta come trigger");
static_assert(BASILICA_GRID.data[(BASILICA_WIDTH - 1) +
                                  BASILICA_VARCO_NORD_FIRST_Y * BASILICA_WIDTH] ==
                  uint8_t(TileType::EXIT_PORTA_ROMANA),
              "L'uscita verso la Strada del Bottaccione (valore 5) non e' dove dichiarato");
static_assert(! is_solid(BASILICA_GRID.data[(BASILICA_WIDTH - 1) +
                                             BASILICA_VARCO_NORD_FIRST_Y * BASILICA_WIDTH]) &&
              is_transition(BASILICA_GRID.data[(BASILICA_WIDTH - 1) +
                                                BASILICA_VARCO_NORD_FIRST_Y * BASILICA_WIDTH]),
              "L'uscita verso la Strada del Bottaccione deve essere calpestabile e riconosciuta come trigger");

// 2. Ogni INGRESSO_DA_* cade su un tile calpestabile.
static_assert(! is_solid(BASILICA_GRID.data[BASILICA_INGRESSO_DA_MONTE_INGINO_X +
                                             BASILICA_INGRESSO_DA_MONTE_INGINO_Y * BASILICA_WIDTH]),
              "INGRESSO_DA_MONTE_INGINO cade dentro un muro: il giocatore ci resterebbe chiuso");
static_assert(! is_solid(BASILICA_GRID.data[BASILICA_INGRESSO_DA_BOTTACCIONE_X +
                                             BASILICA_INGRESSO_DA_BOTTACCIONE_Y * BASILICA_WIDTH]),
              "INGRESSO_DA_BOTTACCIONE cade dentro un muro: il giocatore ci resterebbe chiuso");

// 3. Almeno un punto notevole per ogni lato, con un messaggio che fissa l'orientamento.
static_assert(BASILICA_GRID.data[31 + 10 * BASILICA_WIDTH] == uint8_t(TileType::CONSOLI_FACADE),
              "ALTO SCHERMO = OVEST reale: qui deve stare la facciata della basilica");
static_assert(BASILICA_GRID.data[31 + (BASILICA_HEIGHT - 1) * BASILICA_WIDTH] ==
                  uint8_t(TileType::RAILING),
              "BASSO SCHERMO = EST reale: qui deve stare il parapetto panoramico");
static_assert(BASILICA_GRID.data[0 + BASILICA_VARCO_SUD_FIRST_Y * BASILICA_WIDTH] ==
                  uint8_t(TileType::EXIT_SAN_MARTINO),
              "SINISTRA SCHERMO = SUD reale: qui deve stare l'uscita verso gli Stradoni del Monte");
static_assert(BASILICA_GRID.data[(BASILICA_WIDTH - 1) +
                                  BASILICA_VARCO_NORD_FIRST_Y * BASILICA_WIDTH] ==
                  uint8_t(TileType::EXIT_PORTA_ROMANA),
              "DESTRA SCHERMO = NORD reale: qui deve stare l'uscita verso la Strada del Bottaccione");

// Guardia contro il ribaltamento (docs/mappa_del_mondo.md sez. 3): i due varchi stanno su fianchi
// OPPOSTI. Se si scambiassero, questo assert cadrebbe mentre la mappa continuerebbe comunque a
// compilare — il difetto gia' capitato una volta con Piazza Grande.
static_assert(BASILICA_GRID.data[0 + BASILICA_VARCO_SUD_FIRST_Y * BASILICA_WIDTH] !=
                  BASILICA_GRID.data[(BASILICA_WIDTH - 1) +
                                      BASILICA_VARCO_NORD_FIRST_Y * BASILICA_WIDTH],
              "I due varchi laterali non possono essere la stessa uscita: sarebbe un ribaltamento");

// 4. Il monumento nominato (Basilica di Sant'Ubaldo, gia' in city_reference.h::LANDMARKS con
// tiles_width=34) rispetta respects_scale(). Si misura la griglia invece di fidarsi della
// costante, perche' e' la griglia che finisce in ROM; la chiamata a respects_scale(), non un
// letterale == 34, e' cio' che il punto 4 del contratto chiede esplicitamente.
static_assert([]
{
    int larghezza = 0;

    for(int x = 0; x < BASILICA_WIDTH; ++x)
    {
        if(BASILICA_GRID.data[x + BASILICA_FACADE_FIRST_Y * BASILICA_WIDTH] ==
           uint8_t(TileType::CONSOLI_FACADE))
        {
            ++larghezza;
        }
    }

    return respects_scale(BASILICA_FACADE_REAL_WIDTH_M, larghezza);
}(), "Il fronte della Basilica di Sant'Ubaldo non rispetta la scala di 1,5 m per tile (50 m)");

// Sanita' del percorso: la scalinata deve aderire al portone, e lo spiazzo davanti dev'essere
// calpestabile, altrimenti il giocatore che scende i gradini sbatte contro un muro invisibile.
static_assert(! is_solid(BASILICA_GRID.data[BASILICA_PORTONE_X0 +
                                             BASILICA_STAIRS_Y * BASILICA_WIDTH]),
              "La scalinata deve aderire al portone, non staccarsene con un muro");
static_assert(BASILICA_GRID.data[31 + 26 * BASILICA_WIDTH] == uint8_t(TileType::GROUND),
              "Il centro dello spiazzo panoramico deve essere aperto");
static_assert(sizeof(BasilicaGrid) == BASILICA_WIDTH * BASILICA_HEIGHT,
              "La griglia deve restare un blocco contiguo di byte");

} // namespace gubbio::maps

#endif // BASILICA_COLLISION_H
