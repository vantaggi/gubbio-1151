#ifndef VIA_DEI_CONSOLI_COLLISION_H
#define VIA_DEI_CONSOLI_COLLISION_H

#include <stdint.h>

#include "piazza_grande_collision.h"   // per TileType e is_solid/is_transition: non si ridefiniscono

namespace gubbio::maps {

// VIA DEI CONSOLI — la strada che scende da Piazza Grande (70 m) a Largo del Bargello (45 m).
//
// COS'E'. La strada medievale piu' caratteristica di Gubbio: STRETTA e RIPIDA, fiancheggiata da
// case in pietra con le cosiddette "porte del morto" — portine strette e rialzate da terra,
// murate. E' un CORRIDOIO: stretto sull'asse x (la sede stradale), lungo sull'asse y (la discesa).
//
// IL DISLIVELLO, MOSTRATO NEI SOLI TRE MODI CHE IL CONTRATTO AMMETTE (mappa_del_mondo.md sez. 2):
//   1. scalinate  -> bande di tile STAIRS lungo la discesa (quattro, per non farle sembrare un
//      unico gradone);
//   2. muri di sostegno -> in due bande la sede stradale si stringe, perche' i muri laterali
//      diventano piu' spessi: e' un muro che sostiene la salita, non un ostacolo arbitrario;
//   3. un affaccio -> un varco nel costruito sul lato nord, un solo tratto, dove il muro cieco
//      lascia il posto a un parapetto (RAILING) sul crinale.
// Non si inventa un quarto linguaggio: la sez. 2 del contratto lo vieta esplicitamente.
//
// ORIENTAMENTO, uguale a tutte le aree (mappa_del_mondo.md sez. 3): alto = OVEST, basso = EST,
// sinistra = SUD, destra = NORD. x cresce verso NORD, y cresce verso EST.
//
//        ALTO SCHERMO (y piccola)   = OVEST reale  -> A MONTE: l'uscita verso Piazza Grande
//        BASSO SCHERMO (y grande)   = EST reale    -> A VALLE: l'uscita verso Largo del Bargello
//        SINISTRA SCHERMO (x piccola) = SUD reale  -> le case sul lato sud, ininterrotte
//        DESTRA SCHERMO (x grande)    = NORD reale -> le case sul lato nord, con l'affaccio
//
// I VALORI 4 E 5 SONO RIUSATI, non ridefiniti. `piazza_grande_collision.h` li chiama
// EXIT_SAN_MARTINO e EXIT_PORTA_ROMANA perche' li' significano quello; qui, in QUESTA area,
// significano "verso Piazza Grande" e "verso Largo del Bargello". E' lo stesso riuso che
// `largo_bargello_collision.h` fa gia' con EXIT_PORTA_ROMANA per il proprio varco verso la
// piazza: il valore numerico e' cio' che conta (Sez. 5 del contratto), non il nome dell'enumerator.
//
// NESSUN MONUMENTO A SCALA FISSA. Via dei Consoli e' una via residenziale: non compare nella
// tabella `LANDMARKS[]` di city_reference.h, quindi non c'e' una `respects_scale()` da verificare
// qui (punto 4 delle static_assert obbligatorie, Sez. 5 del contratto) — annotato invece di
// ometterlo in silenzio.

constexpr int VIA_DEI_CONSOLI_WIDTH  = 16;   // in tile. x cresce verso NORD: la via e' STRETTA
constexpr int VIA_DEI_CONSOLI_HEIGHT = 64;   // in tile. y cresce verso EST: la via e' LUNGA
constexpr int VIA_DEI_CONSOLI_WIDTH_PX  = VIA_DEI_CONSOLI_WIDTH * TILE_SIZE_PX;    // 128
constexpr int VIA_DEI_CONSOLI_HEIGHT_PX = VIA_DEI_CONSOLI_HEIGHT * TILE_SIZE_PX;   // 512

// Quota media: la via scende da 70 m (Piazza Grande) a 45 m (Largo del Bargello), come vuole la
// tabella di mappa_del_mondo.md sez. 2. Un solo numero non puo' rendere una pendenza: qui sta il
// punto medio, perche' e' quello che il contratto (Sez. 5) chiede come `<NOME>_QUOTA_M` singolo;
// i due estremi restano scritti sopra, in commento, per chi cablera' il passaggio fra le aree.
constexpr int VIA_DEI_CONSOLI_QUOTA_M = 58;

static_assert(VIA_DEI_CONSOLI_QUOTA_M > 45 && VIA_DEI_CONSOLI_QUOTA_M < 70,
              "La quota media deve stare fra Largo del Bargello (45 m) e Piazza Grande (70 m)");

// Dove il giocatore compare arrivando da ciascuna area confinante (Sez. 5 del contratto).
//
// PREFISSATE CON VIA_DEI_CONSOLI_, e non semplicemente INGRESSO_DA_<AREA> come mostra il
// contratto alla lettera. Motivo: `map_data.h` include GIA' oggi piu' `*_collision.h` nella
// STESSA unita' di traduzione, tutti dentro `namespace gubbio::maps` (si veda l'inclusione
// congiunta di piazza_grande_collision.h e largo_bargello_collision.h). Piazza Grande ha PIU' di
// un vicino a monte (via dei Consoli qui, via XX Settembre, Duomo/Ducale): se ciascuna di quelle
// aree definisse un `INGRESSO_DA_PIAZZA_GRANDE_X` senza prefisso, il secondo a compilare
// ridefinirebbe il simbolo del primo e la build si fermerebbe. Prefissare con il nome della
// propria area e' l'unico modo per restare dentro la lettera del contratto (il NOME dell'area di
// provenienza compare comunque, per intero, nel nome della costante) senza rischiare una
// collisione che nessuno vedrebbe finche' un'altra area non venisse aggiunta a map_data.h.
constexpr int VIA_DEI_CONSOLI_INGRESSO_DA_PIAZZA_GRANDE_X = 7;
    // OTTO tile dentro, non uno: il contratto (docs/mappa_del_mondo.md sez. 5) impone almeno
    // sei di margine dal proprio varco. Quest'area e' stata autorata PRIMA che quella regola
    // esistesse, e l'autotest ha misurato il difetto che la regola previene: qualche frame
    // residuo di spinta nella direzione d'arrivo, e il giocatore rientra da dove e' appena
    // uscito. Nel giro completo dell'anello il risultato era prendere la strada sbagliata.
constexpr int VIA_DEI_CONSOLI_INGRESSO_DA_PIAZZA_GRANDE_Y = 8;    // appena a valle dell'uscita
constexpr int VIA_DEI_CONSOLI_INGRESSO_DA_LARGO_BARGELLO_X = 7;
constexpr int VIA_DEI_CONSOLI_INGRESSO_DA_LARGO_BARGELLO_Y = 55;  // appena a monte dell'uscita

// --- LA DISPOSIZIONE, in bande lungo y ---------------------------------------------------------

// Le due uscite: bande strette sul bordo corto, ALTO (ovest, a monte) e BASSO (est, a valle).
constexpr int VIA_DEI_CONSOLI_EXIT_PIAZZA_FIRST_Y = 0;
constexpr int VIA_DEI_CONSOLI_EXIT_PIAZZA_LAST_Y  = 1;
constexpr int VIA_DEI_CONSOLI_EXIT_PIAZZA_FIRST_X = 6;
constexpr int VIA_DEI_CONSOLI_EXIT_PIAZZA_LAST_X  = 9;

constexpr int VIA_DEI_CONSOLI_EXIT_BARGELLO_FIRST_Y = VIA_DEI_CONSOLI_HEIGHT - 2;
constexpr int VIA_DEI_CONSOLI_EXIT_BARGELLO_LAST_Y  = VIA_DEI_CONSOLI_HEIGHT - 1;
constexpr int VIA_DEI_CONSOLI_EXIT_BARGELLO_FIRST_X = 6;
constexpr int VIA_DEI_CONSOLI_EXIT_BARGELLO_LAST_X  = 9;

// Spessore base delle case sui due lati lunghi, e quanto si ispessisce nelle bande dei muri di
// sostegno: la' la sede stradale si stringe da 12 a 8 tile.
constexpr int VIA_DEI_CONSOLI_SIDE_WALL_THICK = 2;
constexpr int VIA_DEI_CONSOLI_BUTTRESS_THICK  = 4;

constexpr int VIA_DEI_CONSOLI_BUTTRESS_A_FIRST_Y = 18;
constexpr int VIA_DEI_CONSOLI_BUTTRESS_A_LAST_Y  = 20;
constexpr int VIA_DEI_CONSOLI_BUTTRESS_B_FIRST_Y = 46;
constexpr int VIA_DEI_CONSOLI_BUTTRESS_B_LAST_Y  = 48;

// Quattro bande di scalinata lungo la discesa: 25 metri non si mostrano con un gradone solo.
constexpr int VIA_DEI_CONSOLI_STAIRS_1_FIRST_Y = 10, VIA_DEI_CONSOLI_STAIRS_1_LAST_Y = 12;
constexpr int VIA_DEI_CONSOLI_STAIRS_2_FIRST_Y = 24, VIA_DEI_CONSOLI_STAIRS_2_LAST_Y = 26;
constexpr int VIA_DEI_CONSOLI_STAIRS_3_FIRST_Y = 38, VIA_DEI_CONSOLI_STAIRS_3_LAST_Y = 40;
constexpr int VIA_DEI_CONSOLI_STAIRS_4_FIRST_Y = 52, VIA_DEI_CONSOLI_STAIRS_4_LAST_Y = 54;

// L'affaccio: un solo squarcio nel costruito del lato NORD, a meta' via.
constexpr int VIA_DEI_CONSOLI_AFFACCIO_FIRST_Y = 32;
constexpr int VIA_DEI_CONSOLI_AFFACCIO_LAST_Y  = 34;

[[nodiscard]] inline constexpr uint8_t via_dei_consoli_tile_type(int x, int y)
{
    if(x < 0 || x >= VIA_DEI_CONSOLI_WIDTH || y < 0 || y >= VIA_DEI_CONSOLI_HEIGHT)
    {
        return uint8_t(TileType::WALL);   // fuori mappa = muro
    }

    // Le uscite, controllate per prime: sono finestre piccole sul bordo che la logica sotto,
    // se venisse valutata prima, risolverebbe come casa.
    if(y >= VIA_DEI_CONSOLI_EXIT_PIAZZA_FIRST_Y && y <= VIA_DEI_CONSOLI_EXIT_PIAZZA_LAST_Y &&
       x >= VIA_DEI_CONSOLI_EXIT_PIAZZA_FIRST_X && x <= VIA_DEI_CONSOLI_EXIT_PIAZZA_LAST_X)
    {
        return uint8_t(TileType::EXIT_SAN_MARTINO);    // riusato: "verso Piazza Grande"
    }

    if(y >= VIA_DEI_CONSOLI_EXIT_BARGELLO_FIRST_Y && y <= VIA_DEI_CONSOLI_EXIT_BARGELLO_LAST_Y &&
       x >= VIA_DEI_CONSOLI_EXIT_BARGELLO_FIRST_X && x <= VIA_DEI_CONSOLI_EXIT_BARGELLO_LAST_X)
    {
        return uint8_t(TileType::EXIT_PORTA_ROMANA);   // riusato: "verso Largo del Bargello"
    }

    // Spessore delle case sui due lati lunghi: piu' spesso dentro le bande dei muri di sostegno.
    int thick = VIA_DEI_CONSOLI_SIDE_WALL_THICK;
    if((y >= VIA_DEI_CONSOLI_BUTTRESS_A_FIRST_Y && y <= VIA_DEI_CONSOLI_BUTTRESS_A_LAST_Y) ||
       (y >= VIA_DEI_CONSOLI_BUTTRESS_B_FIRST_Y && y <= VIA_DEI_CONSOLI_BUTTRESS_B_LAST_Y))
    {
        thick = VIA_DEI_CONSOLI_BUTTRESS_THICK;
    }

    // SINISTRA = SUD: le case in pietra, ininterrotte per tutta la lunghezza della via.
    if(x < thick)
    {
        return uint8_t(TileType::WALL);
    }

    // DESTRA = NORD: le case sull'altro lato, salvo l'affaccio a meta' via.
    if(x >= VIA_DEI_CONSOLI_WIDTH - thick)
    {
        if(y >= VIA_DEI_CONSOLI_AFFACCIO_FIRST_Y && y <= VIA_DEI_CONSOLI_AFFACCIO_LAST_Y)
        {
            return uint8_t(TileType::RAILING);
        }

        return uint8_t(TileType::WALL);
    }

    // La sede stradale: gradini dove il dislivello e' piu' ripido, ciottolato altrove.
    if((y >= VIA_DEI_CONSOLI_STAIRS_1_FIRST_Y && y <= VIA_DEI_CONSOLI_STAIRS_1_LAST_Y) ||
       (y >= VIA_DEI_CONSOLI_STAIRS_2_FIRST_Y && y <= VIA_DEI_CONSOLI_STAIRS_2_LAST_Y) ||
       (y >= VIA_DEI_CONSOLI_STAIRS_3_FIRST_Y && y <= VIA_DEI_CONSOLI_STAIRS_3_LAST_Y) ||
       (y >= VIA_DEI_CONSOLI_STAIRS_4_FIRST_Y && y <= VIA_DEI_CONSOLI_STAIRS_4_LAST_Y))
    {
        return uint8_t(TileType::STAIRS);
    }

    return uint8_t(TileType::ROAD);   // ciottolato percorribile
}

// --- La griglia come DATO, derivata dalla funzione, come PIAZZA_GRID e BARGELLO_GRID -----------

struct ViaDeiConsoliGrid
{
    uint8_t data[VIA_DEI_CONSOLI_WIDTH * VIA_DEI_CONSOLI_HEIGHT];
};

[[nodiscard]] consteval ViaDeiConsoliGrid make_via_dei_consoli_grid()
{
    ViaDeiConsoliGrid grid{};

    for(int y = 0; y < VIA_DEI_CONSOLI_HEIGHT; ++y)
    {
        for(int x = 0; x < VIA_DEI_CONSOLI_WIDTH; ++x)
        {
            grid.data[x + y * VIA_DEI_CONSOLI_WIDTH] = via_dei_consoli_tile_type(x, y);
        }
    }

    return grid;
}

inline constexpr ViaDeiConsoliGrid VIA_DEI_CONSOLI_GRID = make_via_dei_consoli_grid();

// --- static_assert obbligatorie (Sez. 5 del contratto) ------------------------------------------

static_assert(sizeof(ViaDeiConsoliGrid) == VIA_DEI_CONSOLI_WIDTH * VIA_DEI_CONSOLI_HEIGHT,
              "La griglia deve restare un blocco contiguo di byte");

// 1. Ogni uscita dichiarata esiste davvero nella griglia ed e' calpestabile.
static_assert(VIA_DEI_CONSOLI_GRID.data[7 + VIA_DEI_CONSOLI_EXIT_PIAZZA_FIRST_Y * VIA_DEI_CONSOLI_WIDTH]
                  == uint8_t(TileType::EXIT_SAN_MARTINO),
              "L'uscita verso Piazza Grande non e' dove dovrebbe");
static_assert(! is_solid(VIA_DEI_CONSOLI_GRID.data[7 + VIA_DEI_CONSOLI_EXIT_PIAZZA_FIRST_Y *
                                                        VIA_DEI_CONSOLI_WIDTH]),
              "L'uscita verso Piazza Grande non e' calpestabile");
static_assert(VIA_DEI_CONSOLI_GRID.data[7 + (VIA_DEI_CONSOLI_HEIGHT - 1) * VIA_DEI_CONSOLI_WIDTH]
                  == uint8_t(TileType::EXIT_PORTA_ROMANA),
              "L'uscita verso Largo del Bargello non e' dove dovrebbe");
static_assert(! is_solid(VIA_DEI_CONSOLI_GRID.data[7 + (VIA_DEI_CONSOLI_HEIGHT - 1) *
                                                        VIA_DEI_CONSOLI_WIDTH]),
              "L'uscita verso Largo del Bargello non e' calpestabile");

// 2. Ogni INGRESSO_DA_* cade su un tile calpestabile: altrimenti il giocatore compare dentro un
// muro e il salvataggio ce lo lascia per sempre.
static_assert(! is_solid(VIA_DEI_CONSOLI_GRID.data[VIA_DEI_CONSOLI_INGRESSO_DA_PIAZZA_GRANDE_X +
                              VIA_DEI_CONSOLI_INGRESSO_DA_PIAZZA_GRANDE_Y * VIA_DEI_CONSOLI_WIDTH]),
              "L'ingresso da Piazza Grande cade dentro un muro");
static_assert(! is_solid(VIA_DEI_CONSOLI_GRID.data[VIA_DEI_CONSOLI_INGRESSO_DA_LARGO_BARGELLO_X +
                              VIA_DEI_CONSOLI_INGRESSO_DA_LARGO_BARGELLO_Y * VIA_DEI_CONSOLI_WIDTH]),
              "L'ingresso da Largo del Bargello cade dentro un muro");

// 3. Almeno un punto notevole per ogni lato, e la coppia che distingue una ROTAZIONE da un
// RIBALTAMENTO: i due lati lunghi stanno su lati OPPOSTI e non sono la stessa cosa. Se qualcuno
// li scambiasse otterrebbe l'immagine allo specchio di Gubbio, gia' successo una volta
// (piazza_grande_collision.h ne porta ancora la cicatrice nei commenti).
static_assert(VIA_DEI_CONSOLI_GRID.data[7 + VIA_DEI_CONSOLI_EXIT_PIAZZA_FIRST_Y * VIA_DEI_CONSOLI_WIDTH]
                  == uint8_t(TileType::EXIT_SAN_MARTINO),
              "In ALTO (ovest reale) deve aprirsi l'uscita verso Piazza Grande, a monte");
static_assert(VIA_DEI_CONSOLI_GRID.data[7 + (VIA_DEI_CONSOLI_HEIGHT - 1) * VIA_DEI_CONSOLI_WIDTH]
                  == uint8_t(TileType::EXIT_PORTA_ROMANA),
              "In BASSO (est reale) deve aprirsi l'uscita verso Largo del Bargello, a valle");
static_assert(VIA_DEI_CONSOLI_GRID.data[0 + 33 * VIA_DEI_CONSOLI_WIDTH] == uint8_t(TileType::WALL),
              "Le case devono stare a SINISTRA (sud reale)");
static_assert(VIA_DEI_CONSOLI_GRID.data[(VIA_DEI_CONSOLI_WIDTH - 1) + 33 * VIA_DEI_CONSOLI_WIDTH]
                  == uint8_t(TileType::RAILING),
              "L'affaccio deve stare a DESTRA (nord reale)");
static_assert(VIA_DEI_CONSOLI_GRID.data[0 + 33 * VIA_DEI_CONSOLI_WIDTH] !=
                  VIA_DEI_CONSOLI_GRID.data[(VIA_DEI_CONSOLI_WIDTH - 1) + 33 * VIA_DEI_CONSOLI_WIDTH],
              "I due lati lunghi non possono essere la stessa cosa");

// 4. Nessun monumento a scala fissa e' nominato in quest'area (vedi il commento in testa al
// file): non c'e' una LANDMARKS[] da verificare con respects_scale().

} // namespace gubbio::maps

#endif // VIA_DEI_CONSOLI_COLLISION_H
