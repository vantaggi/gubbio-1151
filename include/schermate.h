#ifndef GUBBIO_SCHERMATE_H
#define GUBBIO_SCHERMATE_H

#include "bn_sprite_palette_ptr.h"

namespace gubbio
{

class Esplorazione;

// Schermata di prova dei testi (fase F1): non ritorna.
[[noreturn]] void schermata_testi(const bn::sprite_palette_ptr& palette);

// Camminata automatica dell'anello e di ogni arco (fase F2), sulla scena vera, con i picchi di
// sprite, tile OBJ, blocchi BG e stack IWRAM; alla fine mostra i risultati fino a A.
void camminata_automatica(Esplorazione& esplorazione, const bn::sprite_palette_ptr& palette);

// Istantanee (fase F2): ogni area sullo spawn 0, una dopo l'altra, con una riga di log per area
// ("Istantanea N") che dice a tools/istantanee.py quando scattare.
void istantanee(Esplorazione& esplorazione);

}

#endif
