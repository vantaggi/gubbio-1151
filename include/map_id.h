#ifndef MAP_ID_H
#define MAP_ID_H

#include "bn_string_view.h"

namespace gubbio {

// Identificatore AUTORITATIVO delle aree di gioco.
//
// PERCHE' ESISTE: prima della Sessione 08 la numerazione delle mappe viveva in tre posti con
// tre convenzioni incompatibili — `save_data.h` la documentava a 4 valori in un commento, la
// Sezione 38 del GDD ne elenca di piu', e i trigger della Sezione 21B ne implicano altri
// ancora. Un `uint8_t current_map_id` scritto su FRAM con una numerazione e riletto con
// un'altra sposta il giocatore in un'area sbagliata, e il salvataggio non se ne accorge.
// Da qui in avanti questa e' l'unica fonte di verita': `save_data.h` serializza questo enum.
//
// I valori numerici sono PERSISTITI SU FRAM: si possono aggiungere voci in coda, mai
// riordinare o rimuovere quelle esistenti senza invalidare i salvataggi.
enum class MapId : uint8_t
{
    PIAZZA_GRANDE = 0,   // Hub: Piazza Grande e Palazzo dei Consoli (Sez. 21 GDD)
    BOTTACCIONE   = 1,   // Dungeon: Gola del Bottaccione e Acquedotto Pensile (Sez. 22 GDD)
    MURA          = 2,   // Assedio alle mura (Atto III)
    PIANA         = 3,   // Piana di Gubbio
    MONTE_INGINO  = 4,   // Stradoni del Monte Ingino (Sez. 10 Reference 3)
    // Largo del Bargello, sulla salita di via dei Consoli: e' QUI che sta la Fontana dei Matti,
    // non in Piazza Grande (correzione topografica della Sessione 18d). Area non ancora autorata.
    LARGO_BARGELLO = 5,
    COUNT
};

constexpr int MAP_COUNT = int(MapId::COUNT);

// I primi quattro valori DEVONO restare quelli gia' documentati in save_data.h, altrimenti i
// salvataggi esistenti puntano all'area sbagliata.
static_assert(int(MapId::PIAZZA_GRANDE) == 0 && int(MapId::BOTTACCIONE) == 1 &&
              int(MapId::MURA) == 2 && int(MapId::PIANA) == 3,
              "I valori 0-3 sono persistiti su FRAM: non si riordinano");

static_assert(MAP_COUNT <= 256, "MapId e' serializzato come uint8_t");

// Nomi per HUD e diagnostica. `inline` e' obbligatorio: senza, ogni unita' di traduzione che
// include l'header riceve la propria copia in .rodata e i puntatori differiscono fra le unita',
// distruggendo proprio la fonte di verita' unica che questo file esiste per garantire.
inline constexpr bn::string_view MAP_NAMES[MAP_COUNT] = {
    "Piazza Grande", "Gola del Bottaccione", "Mura di Gubbio", "Piana", "Monte Ingino",
    "Largo del Bargello"
};

} // namespace gubbio

#endif // MAP_ID_H
