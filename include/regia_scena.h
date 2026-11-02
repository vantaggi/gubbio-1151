#ifndef GUBBIO_REGIA_SCENA_H
#define GUBBIO_REGIA_SCENA_H

#include "bn_sprite_palette_ptr.h"

namespace gubbio
{

// Una cutscene a schermo (F7): le bande nere da 24 px fatte con la finestra, i piani in parallasse
// su quattro BG, gli stacchi netti, il NARRATORE nella banda di sotto; Start salta tutto, A porta
// avanti il testo. Con automatica=true non legge i tasti; con istantanee=true scrive nel log
// "Istantanea regia_<codice>_<inquadratura>". Segna la cutscene vista; ritorna false se e' stata saltata.
bool recita_cutscene(int cutscene, const bn::sprite_palette_ptr& palette_testo, bool istantanee = false,
                     bool automatica = false);

// GUBBIO_AVVIO=10: tutte le cutscene, senza tasti, con le istantanee. Non ritorna.
[[noreturn]] void prova_regia(const bn::sprite_palette_ptr& palette_testo);

}

#endif
