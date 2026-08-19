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
    // La rete completa della citta', dettata dal committente nella Sessione 20 e disegnata in
    // docs/mappa_del_mondo.md. Non e' un elenco di luoghi: e' un ANELLO che gira attorno al
    // Monte Ingino — si sale da Piazza Grande passando per il Duomo e gli stradoni fino alla
    // Basilica, e si ridiscende dall'altro versante lungo il Bottaccione, rientrando in citta'
    // dalla Porta di Santa Lucia a San Martino.
    VIA_DEI_CONSOLI         = 6,
    VIA_XX_SETTEMBRE        = 7,
    SANT_AGOSTINO           = 8,
    SANT_ANDREA             = 9,
    SAN_MARTINO             = 10,
    PIAZZA_QUARANTA_MARTIRI = 11,   // il punto piu' basso della citta': quota zero
    SAN_PIETRO              = 12,
    DUOMO_DUCALE            = 13,   // Duomo, giardini pensili e Palazzo Ducale, sopra la piazza
    BASILICA                = 14,   // la vetta del Monte Ingino
    TEATRO_ROMANO           = 15,   // FUORI dalle mura cittadine, sotto San Martino
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
    "Largo del Bargello", "Via dei Consoli", "Via XX Settembre", "Sant'Agostino",
    "Sant'Andrea", "San Martino", "Piazza Quaranta Martiri", "San Pietro",
    "Duomo e Palazzo Ducale", "Basilica di Sant'Ubaldo", "Teatro Romano"
};

// I nomi devono essere tanti quante le aree. Sembra ovvio; e' invece la svista piu' facile da
// commettere aggiungendo una voce all'enum, e produce una lettura fuori dall'array in un punto
// — l'HUD — dove nessun test guarda.
static_assert(int(sizeof(MAP_NAMES) / sizeof(MAP_NAMES[0])) == MAP_COUNT,
              "Ogni area deve avere il suo nome, e nessun nome deve avanzare");

} // namespace gubbio

#endif // MAP_ID_H
