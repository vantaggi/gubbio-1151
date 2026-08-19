#ifndef CITY_REFERENCE_H
#define CITY_REFERENCE_H

#include <stdint.h>

#include "bn_string_view.h"

#include "piazza_grande_collision.h"

namespace gubbio {

// La Gubbio reale come metro di riferimento della Gubbio giocabile.
//
// DECISIONE DEL COMMITTENTE (Sessione 15): **si accettano compromessi per la giocabilita', purche'
// resti l'illusione della citta' vera.** Questo file esiste perche' "illusione" non e' una
// specifica: senza una regola scritta, ogni sessione la interpreterebbe a modo proprio e la citta'
// deriverebbe un ritocco per volta.
//
// --- LA REGOLA: la scala vincola gli EDIFICI, non le DISTANZE ---
//
// Un occhio non misura quanto e' lunga una piazza. Misura, senza accorgersene, **quanto e' grande
// un palazzo rispetto alla piazza che lo ospita**, e riconosce **l'ordine in cui le cose si
// incontrano** camminando. Da qui i tre vincoli, in ordine di rigidita':
//
// 1. **Dimensioni degli edifici: IN SCALA, vincolanti.** 1,5 metri per tile. Non e' una
//    convenzione nuova: e' quella che la tabella della Sez. 23 GDD gia' usava senza dichiararla,
//    verificata su cinque monumenti su sei. Il fronte del Palazzo dei Consoli e' 33 m, cioe' 22
//    tile, e 22 tile deve restare.
// 2. **Distanze fra gli edifici: LIBERE, comprimibili.** Una piazza percorsa in otto secondi
//    annoia; nessuno pero' si accorge che sia lunga 96 metri invece di 130. Le distanze si
//    accorciano quanto serve al gioco.
// 3. **Ordine e adiacenze: VINCOLANTI.** Se nella citta' vera uscendo da via dei Consoli la
//    piazza si apre a sinistra e il Palazzo dei Consoli sta di fronte, cosi' dev'essere in gioco.
//    E' la parte dell'illusione che costa zero e che, se tradita, rovina tutto il resto.
//
// Corollario che vale la pena scrivere: **la piazza implementata non e' in scala, e va bene**.
// 64x40 tile sono 96 x 60 m contro i 130 x 40 reali. Cio' che conta e' che il Palazzo dei Consoli
// occupi la stessa QUOTA della larghezza della piazza che occupa nella realta' — ed e' quello che
// la `static_assert` in fondo al file verifica.

// Scala: 3 metri ogni 2 tile. In aritmetica intera, che e' l'unica ammessa (AGENTS.md).
inline constexpr int METERS_NUM = 3;
inline constexpr int METERS_DEN = 2;

[[nodiscard]] constexpr int tiles_from_meters(int meters)
{
    return (meters * METERS_DEN) / METERS_NUM;
}

// TOLLERANZA DI UN TILE, e perche' esiste. La tabella della Sez. 23 GDD e' stata compilata a mano
// e arrotonda in modo non uniforme: 130 m danno 86 tile (per difetto), ma 50 m ne danno 34 (per
// eccesso) e 4,5 m ne danno 3. Nessun singolo arrotondamento riproduce tutte e sei le righe.
// Invece di piegare i dati alla formula si dichiara la formula per quello che e': una scala di
// 1,5 m/tile **entro un tile di approssimazione**. A 8 pixel per tile, un tile e' un pixel e
// mezzo di differenza sullo schermo: sotto la soglia di cio' che si nota.
inline constexpr int SCALE_TOLERANCE_TILES = 1;

[[nodiscard]] constexpr bool respects_scale(int meters, int tiles)
{
    const int atteso = tiles_from_meters(meters);
    const int scarto = tiles > atteso ? tiles - atteso : atteso - tiles;
    return scarto <= SCALE_TOLERANCE_TILES;
}

[[nodiscard]] constexpr int meters_from_tiles(int tiles)
{
    return (tiles * METERS_NUM) / METERS_DEN;
}

static_assert(tiles_from_meters(33) == 22, "Palazzo dei Consoli: 33 m devono dare 22 tile");
static_assert(respects_scale(4, 3), "Fontana dei Matti: 4,5 m circa danno 3 tile");
static_assert(meters_from_tiles(64) == 96, "La piazza implementata misura 96 m di larghezza");

// Un monumento reale e la sua trasposizione. `real_*` vengono dalla tabella della Sez. 23 GDD;
// `exists_in_1151` e' INFORMATIVO — la decisione della Sessione 15 e' che si riproduce tutto.
struct Landmark
{
    bn::string_view name;
    int16_t real_width_m;
    int16_t real_depth_m;
    uint8_t tiles_width;         // fronte in tile: e' il numero che deve restare in scala
    bool exists_in_1151;
};

inline constexpr Landmark LANDMARKS[] = {
    {"Palazzo dei Consoli",      33,  60, 22, false},   // 1332-1349, Angelo da Orvieto
    {"Piazza Grande",           130,  40, 86, false},   // esiste perche' esiste il palazzo
    {"Palazzo Pretorio",         25,  30, 16, false},
    {"Fontana dei Matti",         4,   4,  3, true},
    {"Basilica di Sant'Ubaldo",  50,  22, 34, false},   // Ubaldo nel 1151 e' vivo
    {"Teatro Romano",            70,  70, 46, true},    // I sec.: c'era gia', come rudere
};

inline constexpr int LANDMARK_COUNT = int(sizeof(LANDMARKS) / sizeof(LANDMARKS[0]));

// Ogni fronte dichiarato deve essere quello che la scala impone. Se un domani qualcuno ritoccasse
// una misura per farla "stare meglio", la build si ferma qui: e' il punto in cui l'illusione si
// perde, perche' un palazzo fuori scala accanto a uno in scala si nota subito.
static_assert([]
{
    for(const Landmark& l : LANDMARKS)
    {
        if(! respects_scale(l.real_width_m, l.tiles_width))
        {
            return false;
        }
    }

    return true;
}(), "Un monumento non rispetta la scala di 1,5 m per tile");

// --- L'invariante che tiene in piedi l'illusione ---------------------------------------------
//
// ATTENZIONE ALL'ASSE, perche' qui ci si e' gia' sbagliati. Nella griglia della piazza
// `PIAZZA_WIDTH` e' l'asse NORD-SUD, quello CORTO (i 40 m fra il muretto e la strada), e
// `PIAZZA_HEIGHT` e' l'asse OVEST-EST, quello LUNGO fra i due palazzi che si fronteggiano. Fino
// alla Sessione 20 le due assert qui sotto leggevano `PIAZZA_WIDTH` come se fosse il lato lungo:
// erano coerenti con una mappa che aveva i due assi scambiati, e hanno smesso di passare nel
// momento in cui la mappa e' stata raddrizzata. Sono servite esattamente a questo.
//
// Il fronte del Palazzo dei Consoli sta sul lato CORTO — e' li' che il palazzo si affaccia — e
// nella citta' vera lo occupa quasi tutto: 33 m su 40. Il vincolo e' che continui a occuparlo
// quasi tutto, perche' e' cio' che fa leggere "un palazzo che tiene un intero lato della piazza".
inline constexpr int CONSOLI_FRONT_TILES = LANDMARKS[0].tiles_width;

static_assert(CONSOLI_FRONT_TILES * 2 >= maps::PIAZZA_WIDTH &&
              CONSOLI_FRONT_TILES <= maps::PIAZZA_WIDTH,
              "Il fronte del Palazzo dei Consoli e' fuori proporzione rispetto al lato CORTO "
              "della piazza, che e' quello su cui il palazzo si affaccia: deve occuparne fra "
              "meta' e la totalita'");

// La piazza deve restare piu' LUNGA che larga, e per il verso giusto. E' la forma che si vede
// nella fotografia aerea, ed e' anche l'unica compatibile con la tabella qui sopra: due palazzi
// che si fronteggiano da 33 e 25 metri di fronte non possono stare su un lato da 130 m.
static_assert(maps::PIAZZA_HEIGHT > maps::PIAZZA_WIDTH,
              "L'asse Consoli-Pretorio (ovest-est, cioe' PIAZZA_HEIGHT) deve essere il lato "
              "LUNGO: invertirli rimette la piazza per il verso sbagliato");

// Fattore di compressione delle distanze, dichiarato invece che subito. Serve a chi autora le
// altre aree per restare coerente: se ogni area comprimesse a piacere, le distanze relative fra
// i luoghi smetterebbero di somigliare alla citta'.
inline constexpr int DISTANCE_PERCENT = 73;      // 96 / 130, in aritmetica intera

static_assert(meters_from_tiles(maps::PIAZZA_HEIGHT) * 100 / LANDMARKS[1].real_width_m ==
                  DISTANCE_PERCENT,
              "La compressione dichiarata non corrisponde a quella effettiva della piazza, "
              "misurata sul lato LUNGO");

} // namespace gubbio

#endif // CITY_REFERENCE_H
