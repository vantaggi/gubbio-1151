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
// il nemico non torna; persa, il giocatore si ritrova all'ingresso dell'area (spawn 1). Con la storia
// la battaglia e' quella della scena del copione che il nemico apre.
class Storia;

class ScontriSullaMappa
{
public:
    // Con la storia (il gioco vero) un nemico compare solo quando la sua scena e' pronta e toccarlo
    // fa partire la scena; senza (le prove), compare finche' non e' vinto e toccarlo avvia la battaglia.
    explicit ScontriSullaMappa(Storia* storia = nullptr) :
        _storia(storia)
    {
    }

    // Da chiamare a ogni frame dell'esplorazione, dopo muovi(): rifa' gli sprite se l'area e' cambiata
    // e, se il giocatore tocca un nemico, gioca lo scontro. Ritorna true se c'e' stata una battaglia.
    bool aggiorna(Esplorazione& esplorazione, const bn::sprite_palette_ptr& palette_testo);

    void svuota();

    [[nodiscard]] int visibili() const
    {
        return _sprite.size();
    }

private:
    Storia* _storia;
    bn::vector<bn::sprite_ptr, progressione::SCONTRI> _sprite;
    int _area = -1;
    int _caricata = -1;     // il fondale su cui sono messi gli sprite

    void _prepara(const Esplorazione& esplorazione);
    [[nodiscard]] bool _visibile(const progressione::ScontroSullaMappa& s) const;
};

}

#endif
