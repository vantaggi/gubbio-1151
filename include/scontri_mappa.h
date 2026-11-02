#ifndef GUBBIO_SCONTRI_MAPPA_H
#define GUBBIO_SCONTRI_MAPPA_H

#include "bn_sprite_palette_ptr.h"
#include "bn_sprite_ptr.h"
#include "bn_vector.h"

#include "progressione.h"

namespace gubbio
{

class Esplorazione;

// I nemici visibili sulla mappa (include/progressione.h, SCONTRI_SULLA_MAPPA): si vedono nella loro
// area finche' lo scontro non e' vinto; toccarli avvia la battaglia. Vinta, la bandiera si accende e
// il nemico non torna; persa, il giocatore si ritrova all'ingresso dell'area (spawn 1).
class ScontriSullaMappa
{
public:
    // Da chiamare a ogni frame dell'esplorazione, dopo muovi(): rifa' gli sprite se l'area e' cambiata
    // e, se il giocatore tocca un nemico, gioca lo scontro. Ritorna true se c'e' stata una battaglia.
    bool aggiorna(Esplorazione& esplorazione, const bn::sprite_palette_ptr& palette_testo);

    void svuota();

private:
    bn::vector<bn::sprite_ptr, progressione::SCONTRI> _sprite;
    int _area = -1;

    void _prepara(const Esplorazione& esplorazione);
};

}

#endif
