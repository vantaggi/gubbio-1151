#ifndef GUBBIO_SCENA_BATTAGLIA_H
#define GUBBIO_SCENA_BATTAGLIA_H

#include <cstdint>

#include "bn_sprite_palette_ptr.h"

#include "battaglia.h"

namespace gubbio
{

// Chi sceglie i comandi dei Santi: il giocatore col menu, o il pilota del modello (per le prove).
enum class Guida : uint8_t
{
    GIOCATORE,
    PILOTA,
};

// Una battaglia a schermo: lo sfondo dell'incontro, i Santi e i nemici, le barre che cambiano solo
// quando la scena consuma l'evento (include/vista_battaglia.h), un attore animato per volta, i
// numeri del danno, la scritta IMMUNE con l'indizio del fuoco, il menu dei comandi. Con
// istantanee=true scrive nel log "Istantanea battaglia_<incontro>_<momento>" nei momenti da
// fotografare (tools/istantanee.py --battaglia). Ritorna l'esito.
battaglia::Esito scena_battaglia(int incontro, uint32_t seme, Guida guida,
                                 const bn::sprite_palette_ptr& palette_testo, bool istantanee = false);

// GUBBIO_AVVIO=4: il menu dei tre scontri, giocabili a mano. Non ritorna.
[[noreturn]] void menu_battaglie(const bn::sprite_palette_ptr& palette_testo);

// GUBBIO_AVVIO=5: i tre scontri col pilota, con le righe di log per le istantanee; poi si ferma.
[[noreturn]] void istantanee_battaglie(const bn::sprite_palette_ptr& palette_testo);

}

#endif
