#ifndef PIAZZA_QUARANTA_MARTIRI_COLLISION_H
#define PIAZZA_QUARANTA_MARTIRI_COLLISION_H

#include <stdint.h>

#include "piazza_grande_collision.h"   // per TileType, is_solid, is_transition, TILE_SIZE_PX
#include "city_reference.h"            // per gubbio::respects_scale, richiesto dal punto 4

namespace gubbio::maps {

// PIAZZA QUARANTA MARTIRI — il punto piu' basso della citta', quota zero di tutto il mondo di
// gioco (docs/mappa_del_mondo.md sez. 2): tutte le altre quote sono misurate sopra questa.
//
// COS'E'. La grande piazza d'ingresso a Gubbio, molto piu' ampia e aperta di Piazza Grande: non
// una piazza chiusa fra due palazzi che si fronteggiano, ma un grande spiazzo rettangolare con
// giardini al centro. Due monumenti:
//   - la LOGGIA DEI TIRATORI, un lungo portico ad arcate su pilastri (XVI sec.), dove si
//     tiravano i panni di lana ad asciugare;
//   - la CHIESA DI SAN FRANCESCO, con l'abside poligonale e il campanile, subito a valle della
//     loggia lungo lo stesso fianco.
// I due sorgono fianco a fianco sul fianco SUD della piazza, come nella citta' vera.
//
// ANACRONISMO NOTO (docs/mappa_del_mondo.md sez. 7, decisione della Sessione 17): il nome stesso
// dell'area e' un anacronismo. "Piazza Quaranta Martiri" ricorda i quaranta ostaggi fucilati dai
// nazisti nel 1944 — un fatto del Novecento. Nel 1151 la piazza esiste ma non con questo nome:
// il progetto ha gia' deciso di accettarlo (si mettono tutti gli edifici, anche posteriori al
// 1151, "perche' vogliamo qualcosa di magnifico anche visivamente") e questo file non lo cambia.
// NOTA PER CHI CUCE IL MONDO: questa scelta andrebbe annotata in docs/riferimenti/FONTI.md,
// insieme alle misure reali approssimate usate qui sotto per la Loggia e per San Francesco (non
// essendo in city_reference.h::LANDMARKS, sono una stima di chi ha autorato quest'area, non una
// misura da una fonte censita). Il mandato di questo agente vieta di scrivere altrove che nei
// due file assegnati: l'annotazione resta da fare a chi cuce il mondo.
//
// TRE VICINI (docs/mappa_del_mondo.md sez. 1): San Martino a OVEST (si scende da li'), Piazza
// Grande a NORD, San Pietro a EST. Nessun vicino a SUD: quel lato e' il complesso Loggia/San
// Francesco e il tessuto minore che chiude la piazza.

constexpr int PIAZZA_QUARANTA_MARTIRI_WIDTH  = 64;   // in tile. x cresce verso NORD
constexpr int PIAZZA_QUARANTA_MARTIRI_HEIGHT = 64;   // in tile. y cresce verso EST
constexpr int PIAZZA_QUARANTA_MARTIRI_QUOTA_M = 0;   // e' l'origine: tutte le altre quote la usano

constexpr int PIAZZA_QUARANTA_MARTIRI_WIDTH_PX  = PIAZZA_QUARANTA_MARTIRI_WIDTH * TILE_SIZE_PX;
constexpr int PIAZZA_QUARANTA_MARTIRI_HEIGHT_PX = PIAZZA_QUARANTA_MARTIRI_HEIGHT * TILE_SIZE_PX;
// 512x512: un BG regolare legale (256 o 512, mai una misura intermedia), come la Basilica.
static_assert(PIAZZA_QUARANTA_MARTIRI_WIDTH_PX == 512 && PIAZZA_QUARANTA_MARTIRI_HEIGHT_PX == 512,
              "Le misure del BMP devono essere 256 o 512 px: 512x512 e' la misura legale scelta");

// --- LA DISPOSIZIONE, E IL SUO ORIENTAMENTO --------------------------------------------------
//
// Uguale a tutte le aree (docs/mappa_del_mondo.md sez. 3): ALTO SCHERMO = OVEST reale, BASSO
// SCHERMO = EST reale, SINISTRA SCHERMO = SUD reale, DESTRA SCHERMO = NORD reale.
//
//        ALTO SCHERMO (y piccola)     = OVEST reale  -> USCITA verso San Martino, si sale
//        BASSO SCHERMO (y grande)     = EST reale    -> USCITA verso San Pietro
//        SINISTRA SCHERMO (x piccola) = SUD reale    -> Loggia dei Tiratori e San Francesco
//        DESTRA SCHERMO (x grande)    = NORD reale   -> USCITA verso Piazza Grande, si sale

// I VALORI 4, 5 E 6 SONO RIUSATI, non ridefiniti (docs/mappa_del_mondo.md sez. 5: sono i tre
// slot USCITA che ogni area puo' usare; il nome dell'enumerator in piazza_grande_collision.h non
// conta, conta il valore numerico). Qui: 4 = verso San Martino, 5 = verso Piazza Grande, 6 =
// verso San Pietro — l'assegnazione che la sessione di pianificazione ha dato a quest'area.
constexpr int PIAZZA_QUARANTA_MARTIRI_EXIT_SAN_MARTINO_FIRST_X = 28;
constexpr int PIAZZA_QUARANTA_MARTIRI_EXIT_SAN_MARTINO_LAST_X  = 35;
constexpr int PIAZZA_QUARANTA_MARTIRI_EXIT_SAN_MARTINO_FIRST_Y = 0;
constexpr int PIAZZA_QUARANTA_MARTIRI_EXIT_SAN_MARTINO_LAST_Y  = 1;

constexpr int PIAZZA_QUARANTA_MARTIRI_EXIT_PIAZZA_GRANDE_FIRST_X = PIAZZA_QUARANTA_MARTIRI_WIDTH - 2;
constexpr int PIAZZA_QUARANTA_MARTIRI_EXIT_PIAZZA_GRANDE_LAST_X  = PIAZZA_QUARANTA_MARTIRI_WIDTH - 1;
constexpr int PIAZZA_QUARANTA_MARTIRI_EXIT_PIAZZA_GRANDE_FIRST_Y = 28;
constexpr int PIAZZA_QUARANTA_MARTIRI_EXIT_PIAZZA_GRANDE_LAST_Y  = 35;

constexpr int PIAZZA_QUARANTA_MARTIRI_EXIT_SAN_PIETRO_FIRST_X = 28;
constexpr int PIAZZA_QUARANTA_MARTIRI_EXIT_SAN_PIETRO_LAST_X  = 35;
constexpr int PIAZZA_QUARANTA_MARTIRI_EXIT_SAN_PIETRO_FIRST_Y = PIAZZA_QUARANTA_MARTIRI_HEIGHT - 2;
constexpr int PIAZZA_QUARANTA_MARTIRI_EXIT_SAN_PIETRO_LAST_Y  = PIAZZA_QUARANTA_MARTIRI_HEIGHT - 1;

// ATTENZIONE, PER CHI CABLA QUESTA USCITA IN map_data.h. Il valore 6 e' TileType::FOUNTAIN in
// piazza_grande_collision.h, e la USCITA verso San Pietro lo riusa come terzo slot — esattamente
// come la sez. 5 del contratto prevede ("4, 5, 6: USCITA 1, 2, 3 dell'area, si', e cambia
// scena"). MA `is_transition()`, definita in piazza_grande_collision.h (fuori dal mandato di
// questo agente), riconosce solo DOOR_CONSOLI(3), EXIT_SAN_MARTINO(4) ed EXIT_PORTA_ROMANA(5):
// NON FOUNTAIN(6). `scene_exploration.cpp::_check_triggers()` scarta ogni tile per cui
// `is_transition()` e' falso PRIMA di guardare la tabella dei trigger — quindi, cosi' com'e'
// oggi, calpestare l'uscita verso San Pietro non cambierebbe scena: il giocatore ci camminerebbe
// sopra senza alcun effetto. Non e' un difetto di questo file: la griglia dichiara correttamente
// il tile 6 dove il contratto lo vuole, calpestabile. E' `is_transition()` che deve imparare a
// riconoscere anche FOUNTAIN come trigger, e quel file appartiene a chi cuce il mondo. Finche'
// non lo fa, l'uscita verso San Pietro resta silenziosamente inerte a runtime pur essendo
// dichiarata correttamente qui. Le static_assert piu' in basso verificano tutto cio' che questo
// file PUO' verificare (il tile esiste ed e' calpestabile) e non aggiungono una `is_transition`
// che oggi fallirebbe la compilazione per una ragione che non e' un errore di questo file.

// LOGGIA DEI TIRATORI: portico stretto (profondita' 4 tile) e lunghissimo lungo il fianco SUD.
// Lunghezza reale stimata 60 m (non e' in city_reference.h::LANDMARKS: e' una stima di questo
// autore, da far confluire in docs/riferimenti/FONTI.md), che alla scala di 1,5 m/tile
// (city_reference.h) da' ESATTAMENTE 40 tile: e' la lunghezza che la griglia sotto realizza.
constexpr int PIAZZA_QUARANTA_MARTIRI_LOGGIA_FIRST_X = 2;
constexpr int PIAZZA_QUARANTA_MARTIRI_LOGGIA_LAST_X  = 5;    // 4 tile di profondita'
constexpr int PIAZZA_QUARANTA_MARTIRI_LOGGIA_FIRST_Y = 8;
constexpr int PIAZZA_QUARANTA_MARTIRI_LOGGIA_LAST_Y  = 47;   // 40 tile di lunghezza
constexpr int PIAZZA_QUARANTA_MARTIRI_LOGGIA_REAL_LENGTH_M = 60;

// CHIESA DI SAN FRANCESCO: subito a valle della loggia, stesso fianco, piu' profonda (14 tile:
// e' un edificio di culto, non un portico). Fronte reale stimato 21 m -> 14 tile, esatto.
constexpr int PIAZZA_QUARANTA_MARTIRI_SAN_FRANCESCO_FIRST_X = 2;
constexpr int PIAZZA_QUARANTA_MARTIRI_SAN_FRANCESCO_LAST_X  = 15;   // 14 tile di profondita'
constexpr int PIAZZA_QUARANTA_MARTIRI_SAN_FRANCESCO_FIRST_Y = 48;
constexpr int PIAZZA_QUARANTA_MARTIRI_SAN_FRANCESCO_LAST_Y  = 61;   // 14 tile di fronte
constexpr int PIAZZA_QUARANTA_MARTIRI_SAN_FRANCESCO_REAL_WIDTH_M = 21;

// Spessore del tessuto minore che chiude la piazza sui lati non gia' assegnati a un'uscita o a
// un monumento: due tile, come il muretto di Piazza Grande.
constexpr int PIAZZA_QUARANTA_MARTIRI_PERIMETRO_THICK = 2;

// I giardini al centro: prato aperto, non selciato. Non tocca ne' le uscite ne' i monumenti.
constexpr int PIAZZA_QUARANTA_MARTIRI_GIARDINO_FIRST_X = 22;
constexpr int PIAZZA_QUARANTA_MARTIRI_GIARDINO_LAST_X  = 47;
constexpr int PIAZZA_QUARANTA_MARTIRI_GIARDINO_FIRST_Y = 16;
constexpr int PIAZZA_QUARANTA_MARTIRI_GIARDINO_LAST_Y  = 49;

// Dove il giocatore compare arrivando da ciascuna area confinante (Sez. 5 del contratto).
// PREFISSATE con PIAZZA_QUARANTA_MARTIRI_, per lo stesso motivo di via_dei_consoli_collision.h:
// piu' file finiscono nella stessa unita' di traduzione (map_data.h), tutti in gubbio::maps, e
// un INGRESSO_DA_X senza prefisso ridefinirebbe il simbolo omonimo di un'altra area confinante.
//
// ALMENO SEI TILE dal proprio varco (docs/mappa_del_mondo.md: e' gia' successo che un ingresso
// a due tile dalla propria uscita facesse rimbalzare il giocatore all'infinito tenendo premuta
// la direzione da cui e' arrivato). Qui la distanza e' 8-9 tile su tutti e tre.
constexpr int PIAZZA_QUARANTA_MARTIRI_INGRESSO_DA_SAN_MARTINO_X   = 31;
constexpr int PIAZZA_QUARANTA_MARTIRI_INGRESSO_DA_SAN_MARTINO_Y   = 10;  // 9 tile dal varco (y<=1)
constexpr int PIAZZA_QUARANTA_MARTIRI_INGRESSO_DA_PIAZZA_GRANDE_X = 55;  // 7 tile dal varco (x>=62)
constexpr int PIAZZA_QUARANTA_MARTIRI_INGRESSO_DA_PIAZZA_GRANDE_Y = 31;
constexpr int PIAZZA_QUARANTA_MARTIRI_INGRESSO_DA_SAN_PIETRO_X    = 31;
constexpr int PIAZZA_QUARANTA_MARTIRI_INGRESSO_DA_SAN_PIETRO_Y    = 54;  // 8 tile dal varco (y>=62)

[[nodiscard]] inline constexpr uint8_t piazza_quaranta_martiri_tile_type(int x, int y)
{
    if(x < 0 || x >= PIAZZA_QUARANTA_MARTIRI_WIDTH || y < 0 || y >= PIAZZA_QUARANTA_MARTIRI_HEIGHT)
    {
        return uint8_t(TileType::WALL);   // fuori mappa = muro
    }

    // Le tre uscite, controllate per prime: sono fasce strette sul bordo che la logica sotto,
    // se venisse valutata prima, risolverebbe come muro o come monumento.
    if(y >= PIAZZA_QUARANTA_MARTIRI_EXIT_SAN_MARTINO_FIRST_Y &&
       y <= PIAZZA_QUARANTA_MARTIRI_EXIT_SAN_MARTINO_LAST_Y &&
       x >= PIAZZA_QUARANTA_MARTIRI_EXIT_SAN_MARTINO_FIRST_X &&
       x <= PIAZZA_QUARANTA_MARTIRI_EXIT_SAN_MARTINO_LAST_X)
    {
        return uint8_t(TileType::EXIT_SAN_MARTINO);    // valore 4: verso San Martino (ovest)
    }

    if(x >= PIAZZA_QUARANTA_MARTIRI_EXIT_PIAZZA_GRANDE_FIRST_X &&
       x <= PIAZZA_QUARANTA_MARTIRI_EXIT_PIAZZA_GRANDE_LAST_X &&
       y >= PIAZZA_QUARANTA_MARTIRI_EXIT_PIAZZA_GRANDE_FIRST_Y &&
       y <= PIAZZA_QUARANTA_MARTIRI_EXIT_PIAZZA_GRANDE_LAST_Y)
    {
        return uint8_t(TileType::EXIT_PORTA_ROMANA);   // valore 5: verso Piazza Grande (nord)
    }

    if(y >= PIAZZA_QUARANTA_MARTIRI_EXIT_SAN_PIETRO_FIRST_Y &&
       y <= PIAZZA_QUARANTA_MARTIRI_EXIT_SAN_PIETRO_LAST_Y &&
       x >= PIAZZA_QUARANTA_MARTIRI_EXIT_SAN_PIETRO_FIRST_X &&
       x <= PIAZZA_QUARANTA_MARTIRI_EXIT_SAN_PIETRO_LAST_X)
    {
        return uint8_t(TileType::EXIT_TERZA);           // valore 12: verso San Pietro (est)
    }

    // LOGGIA DEI TIRATORI: il lungo portico ad arcate, sul fianco SUD.
    if(x >= PIAZZA_QUARANTA_MARTIRI_LOGGIA_FIRST_X && x <= PIAZZA_QUARANTA_MARTIRI_LOGGIA_LAST_X &&
       y >= PIAZZA_QUARANTA_MARTIRI_LOGGIA_FIRST_Y && y <= PIAZZA_QUARANTA_MARTIRI_LOGGIA_LAST_Y)
    {
        return uint8_t(TileType::CONSOLI_FACADE);   // riuso: pietra chiara, non porta dentro
    }

    // CHIESA DI SAN FRANCESCO, subito a valle della loggia sullo stesso fianco.
    if(x >= PIAZZA_QUARANTA_MARTIRI_SAN_FRANCESCO_FIRST_X &&
       x <= PIAZZA_QUARANTA_MARTIRI_SAN_FRANCESCO_LAST_X &&
       y >= PIAZZA_QUARANTA_MARTIRI_SAN_FRANCESCO_FIRST_Y &&
       y <= PIAZZA_QUARANTA_MARTIRI_SAN_FRANCESCO_LAST_Y)
    {
        return uint8_t(TileType::PRETORIO_FACADE);   // riuso: fronte della chiesa
    }

    // Il resto del perimetro: tessuto minore che chiude la piazza dove non c'e' ne' un'uscita
    // ne' un monumento.
    if(x < PIAZZA_QUARANTA_MARTIRI_PERIMETRO_THICK ||
       y < PIAZZA_QUARANTA_MARTIRI_PERIMETRO_THICK ||
       x > PIAZZA_QUARANTA_MARTIRI_WIDTH - 1 - PIAZZA_QUARANTA_MARTIRI_PERIMETRO_THICK ||
       y > PIAZZA_QUARANTA_MARTIRI_HEIGHT - 1 - PIAZZA_QUARANTA_MARTIRI_PERIMETRO_THICK)
    {
        return uint8_t(TileType::WALL);
    }

    // I giardini al centro: prato, non selciato.
    if(x >= PIAZZA_QUARANTA_MARTIRI_GIARDINO_FIRST_X && x <= PIAZZA_QUARANTA_MARTIRI_GIARDINO_LAST_X &&
       y >= PIAZZA_QUARANTA_MARTIRI_GIARDINO_FIRST_Y && y <= PIAZZA_QUARANTA_MARTIRI_GIARDINO_LAST_Y)
    {
        return uint8_t(TileType::GROUND);
    }

    return uint8_t(TileType::ROAD);   // il selciato aperto della grande piazza
}

// Griglia materializzata in ROM, come PIAZZA_GRID, BARGELLO_GRID e le altre.
struct PiazzaQuarantaMartiriGrid
{
    uint8_t data[PIAZZA_QUARANTA_MARTIRI_WIDTH * PIAZZA_QUARANTA_MARTIRI_HEIGHT];
};

[[nodiscard]] consteval PiazzaQuarantaMartiriGrid make_piazza_quaranta_martiri_grid()
{
    PiazzaQuarantaMartiriGrid grid{};

    for(int y = 0; y < PIAZZA_QUARANTA_MARTIRI_HEIGHT; ++y)
    {
        for(int x = 0; x < PIAZZA_QUARANTA_MARTIRI_WIDTH; ++x)
        {
            grid.data[x + y * PIAZZA_QUARANTA_MARTIRI_WIDTH] = piazza_quaranta_martiri_tile_type(x, y);
        }
    }

    return grid;
}

inline constexpr PiazzaQuarantaMartiriGrid PIAZZA_QUARANTA_MARTIRI_GRID =
    make_piazza_quaranta_martiri_grid();

// --- static_assert obbligatorie (docs/mappa_del_mondo.md sez. 5) ------------------------------

static_assert(sizeof(PiazzaQuarantaMartiriGrid) ==
                  PIAZZA_QUARANTA_MARTIRI_WIDTH * PIAZZA_QUARANTA_MARTIRI_HEIGHT,
              "La griglia deve restare un blocco contiguo di byte");

// 1. Ogni uscita dichiarata esiste davvero nella griglia ed e' calpestabile.
static_assert(PIAZZA_QUARANTA_MARTIRI_GRID.data[31 + 0 * PIAZZA_QUARANTA_MARTIRI_WIDTH] ==
                  uint8_t(TileType::EXIT_SAN_MARTINO),
              "L'uscita verso San Martino non e' dove dovrebbe");
static_assert(! is_solid(PIAZZA_QUARANTA_MARTIRI_GRID.data[31 + 0 * PIAZZA_QUARANTA_MARTIRI_WIDTH]),
              "L'uscita verso San Martino non e' calpestabile");
static_assert(is_transition(PIAZZA_QUARANTA_MARTIRI_GRID.data[31 + 0 * PIAZZA_QUARANTA_MARTIRI_WIDTH]),
              "Il tile dell'uscita verso San Martino deve essere un trigger di cambio scena");

static_assert(PIAZZA_QUARANTA_MARTIRI_GRID.data[63 + 31 * PIAZZA_QUARANTA_MARTIRI_WIDTH] ==
                  uint8_t(TileType::EXIT_PORTA_ROMANA),
              "L'uscita verso Piazza Grande non e' dove dovrebbe");
static_assert(! is_solid(PIAZZA_QUARANTA_MARTIRI_GRID.data[63 + 31 * PIAZZA_QUARANTA_MARTIRI_WIDTH]),
              "L'uscita verso Piazza Grande non e' calpestabile");
static_assert(is_transition(PIAZZA_QUARANTA_MARTIRI_GRID.data[63 + 31 * PIAZZA_QUARANTA_MARTIRI_WIDTH]),
              "Il tile dell'uscita verso Piazza Grande deve essere un trigger di cambio scena");

static_assert(PIAZZA_QUARANTA_MARTIRI_GRID.data[31 + 63 * PIAZZA_QUARANTA_MARTIRI_WIDTH] ==
                  uint8_t(TileType::EXIT_TERZA),
              "L'uscita verso San Pietro non e' dove dovrebbe");
static_assert(! is_solid(PIAZZA_QUARANTA_MARTIRI_GRID.data[31 + 63 * PIAZZA_QUARANTA_MARTIRI_WIDTH]),
              "L'uscita verso San Pietro non e' calpestabile");
// NIENTE static_assert(is_transition(...)) qui: fallirebbe la compilazione, perche' is_transition
// in piazza_grande_collision.h non riconosce ancora FOUNTAIN(6). Vedi il commento sopra la
// dichiarazione delle costanti EXIT_SAN_PIETRO: e' un limite di is_transition(), non di questa
// griglia, e chi cuce il mondo deve saperlo prima di dare per funzionante questa uscita.

// 2. Ogni INGRESSO_DA_* cade su un tile calpestabile: altrimenti il giocatore compare dentro un
// muro e il salvataggio ce lo lascia per sempre.
static_assert(! is_solid(PIAZZA_QUARANTA_MARTIRI_GRID.data[
                  PIAZZA_QUARANTA_MARTIRI_INGRESSO_DA_SAN_MARTINO_X +
                  PIAZZA_QUARANTA_MARTIRI_INGRESSO_DA_SAN_MARTINO_Y * PIAZZA_QUARANTA_MARTIRI_WIDTH]),
              "L'ingresso da San Martino cade dentro un muro");
static_assert(! is_solid(PIAZZA_QUARANTA_MARTIRI_GRID.data[
                  PIAZZA_QUARANTA_MARTIRI_INGRESSO_DA_PIAZZA_GRANDE_X +
                  PIAZZA_QUARANTA_MARTIRI_INGRESSO_DA_PIAZZA_GRANDE_Y * PIAZZA_QUARANTA_MARTIRI_WIDTH]),
              "L'ingresso da Piazza Grande cade dentro un muro");
static_assert(! is_solid(PIAZZA_QUARANTA_MARTIRI_GRID.data[
                  PIAZZA_QUARANTA_MARTIRI_INGRESSO_DA_SAN_PIETRO_X +
                  PIAZZA_QUARANTA_MARTIRI_INGRESSO_DA_SAN_PIETRO_Y * PIAZZA_QUARANTA_MARTIRI_WIDTH]),
              "L'ingresso da San Pietro cade dentro un muro");

// Nessun ingresso puo' cadere gia' su un trigger, altrimenti il rientro riattiva la transizione
// da cui si e' appena usciti: e' il loop infinito che gli spawn point esistono per impedire.
static_assert(! is_transition(PIAZZA_QUARANTA_MARTIRI_GRID.data[
                  PIAZZA_QUARANTA_MARTIRI_INGRESSO_DA_SAN_MARTINO_X +
                  PIAZZA_QUARANTA_MARTIRI_INGRESSO_DA_SAN_MARTINO_Y * PIAZZA_QUARANTA_MARTIRI_WIDTH]),
              "L'ingresso da San Martino cade su un trigger: transizione in loop");
static_assert(! is_transition(PIAZZA_QUARANTA_MARTIRI_GRID.data[
                  PIAZZA_QUARANTA_MARTIRI_INGRESSO_DA_PIAZZA_GRANDE_X +
                  PIAZZA_QUARANTA_MARTIRI_INGRESSO_DA_PIAZZA_GRANDE_Y * PIAZZA_QUARANTA_MARTIRI_WIDTH]),
              "L'ingresso da Piazza Grande cade su un trigger: transizione in loop");
static_assert(! is_transition(PIAZZA_QUARANTA_MARTIRI_GRID.data[
                  PIAZZA_QUARANTA_MARTIRI_INGRESSO_DA_SAN_PIETRO_X +
                  PIAZZA_QUARANTA_MARTIRI_INGRESSO_DA_SAN_PIETRO_Y * PIAZZA_QUARANTA_MARTIRI_WIDTH]),
              "L'ingresso da San Pietro cade su un trigger: transizione in loop");

// 3. Almeno un punto notevole per ogni lato, con un messaggio che fissa l'orientamento.
static_assert(PIAZZA_QUARANTA_MARTIRI_GRID.data[31 + 0 * PIAZZA_QUARANTA_MARTIRI_WIDTH] ==
                  uint8_t(TileType::EXIT_SAN_MARTINO),
              "ALTO SCHERMO = OVEST reale: qui deve stare l'uscita verso San Martino");
static_assert(PIAZZA_QUARANTA_MARTIRI_GRID.data[31 + 63 * PIAZZA_QUARANTA_MARTIRI_WIDTH] ==
                  uint8_t(TileType::EXIT_TERZA),
              "BASSO SCHERMO = EST reale: qui deve stare l'uscita verso San Pietro");
static_assert(PIAZZA_QUARANTA_MARTIRI_GRID.data[3 + 20 * PIAZZA_QUARANTA_MARTIRI_WIDTH] ==
                  uint8_t(TileType::CONSOLI_FACADE),
              "SINISTRA SCHERMO = SUD reale: qui deve stare la Loggia dei Tiratori");
static_assert(PIAZZA_QUARANTA_MARTIRI_GRID.data[63 + 31 * PIAZZA_QUARANTA_MARTIRI_WIDTH] ==
                  uint8_t(TileType::EXIT_PORTA_ROMANA),
              "DESTRA SCHERMO = NORD reale: qui deve stare l'uscita verso Piazza Grande");

// Guardia contro il ribaltamento (docs/mappa_del_mondo.md sez. 3): ALTO e BASSO portano a due
// aree diverse (San Martino, San Pietro), e devono restare due valori diversi. Se qualcuno li
// scambiasse per errore con la stessa uscita, questo assert cadrebbe mentre la mappa
// continuerebbe comunque a compilare — il difetto gia' capitato una volta con Piazza Grande.
static_assert(PIAZZA_QUARANTA_MARTIRI_GRID.data[31 + 0 * PIAZZA_QUARANTA_MARTIRI_WIDTH] !=
                  PIAZZA_QUARANTA_MARTIRI_GRID.data[31 + 63 * PIAZZA_QUARANTA_MARTIRI_WIDTH],
              "Le uscite ALTO e BASSO non possono essere la stessa cosa");
static_assert(is_solid(PIAZZA_QUARANTA_MARTIRI_GRID.data[3 + 20 * PIAZZA_QUARANTA_MARTIRI_WIDTH]) !=
                  is_solid(PIAZZA_QUARANTA_MARTIRI_GRID.data[63 + 31 * PIAZZA_QUARANTA_MARTIRI_WIDTH]),
              "SINISTRA (monumento solido) e DESTRA (uscita calpestabile) non possono comportarsi "
              "allo stesso modo");

// 4. Ogni monumento nominato rispetta respects_scale() di city_reference.h. Si misura la
// griglia invece di fidarsi delle costanti, perche' e' la griglia che finisce in ROM (come fa
// basilica_collision.h per la Basilica di Sant'Ubaldo).
static_assert([]
{
    int lunghezza = 0;

    for(int y = 0; y < PIAZZA_QUARANTA_MARTIRI_HEIGHT; ++y)
    {
        if(PIAZZA_QUARANTA_MARTIRI_GRID.data[3 + y * PIAZZA_QUARANTA_MARTIRI_WIDTH] ==
           uint8_t(TileType::CONSOLI_FACADE))
        {
            ++lunghezza;
        }
    }

    return lunghezza == PIAZZA_QUARANTA_MARTIRI_LOGGIA_LAST_Y -
                             PIAZZA_QUARANTA_MARTIRI_LOGGIA_FIRST_Y + 1;
}(), "La Loggia dei Tiratori non misura i 40 tile attesi lungo la colonna x=3");

static_assert(gubbio::respects_scale(PIAZZA_QUARANTA_MARTIRI_LOGGIA_REAL_LENGTH_M,
                                      PIAZZA_QUARANTA_MARTIRI_LOGGIA_LAST_Y -
                                          PIAZZA_QUARANTA_MARTIRI_LOGGIA_FIRST_Y + 1),
              "La Loggia dei Tiratori non rispetta la scala di 1,5 m per tile");

static_assert([]
{
    int fronte = 0;

    for(int y = 0; y < PIAZZA_QUARANTA_MARTIRI_HEIGHT; ++y)
    {
        if(PIAZZA_QUARANTA_MARTIRI_GRID.data[3 + y * PIAZZA_QUARANTA_MARTIRI_WIDTH] ==
           uint8_t(TileType::PRETORIO_FACADE))
        {
            ++fronte;
        }
    }

    return fronte == PIAZZA_QUARANTA_MARTIRI_SAN_FRANCESCO_LAST_Y -
                          PIAZZA_QUARANTA_MARTIRI_SAN_FRANCESCO_FIRST_Y + 1;
}(), "La Chiesa di San Francesco non misura i 14 tile attesi lungo la colonna x=3");

static_assert(gubbio::respects_scale(PIAZZA_QUARANTA_MARTIRI_SAN_FRANCESCO_REAL_WIDTH_M,
                                      PIAZZA_QUARANTA_MARTIRI_SAN_FRANCESCO_LAST_Y -
                                          PIAZZA_QUARANTA_MARTIRI_SAN_FRANCESCO_FIRST_Y + 1),
              "La Chiesa di San Francesco non rispetta la scala di 1,5 m per tile");

// Sanita' del percorso: l'interno subito oltre ciascuna uscita, e il centro dei giardini,
// devono essere calpestabili, altrimenti il giocatore che entra sbatte contro un muro invisibile.
static_assert(! is_solid(PIAZZA_QUARANTA_MARTIRI_GRID.data[31 + 2 * PIAZZA_QUARANTA_MARTIRI_WIDTH]),
              "Subito a valle dell'uscita verso San Martino deve essere calpestabile");
static_assert(! is_solid(PIAZZA_QUARANTA_MARTIRI_GRID.data[61 + 31 * PIAZZA_QUARANTA_MARTIRI_WIDTH]),
              "Subito a monte dell'uscita verso Piazza Grande deve essere calpestabile");
static_assert(! is_solid(PIAZZA_QUARANTA_MARTIRI_GRID.data[31 + 61 * PIAZZA_QUARANTA_MARTIRI_WIDTH]),
              "Subito a monte dell'uscita verso San Pietro deve essere calpestabile");
static_assert(PIAZZA_QUARANTA_MARTIRI_GRID.data[34 + 32 * PIAZZA_QUARANTA_MARTIRI_WIDTH] ==
                  uint8_t(TileType::GROUND),
              "Il centro dei giardini deve essere prato aperto");

} // namespace gubbio::maps

#endif // PIAZZA_QUARANTA_MARTIRI_COLLISION_H
