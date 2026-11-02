#include "scontri_mappa.h"

#include "bn_core.h"
#include "bn_log.h"
#include "bn_sprite_shape_size.h"

#include "esplorazione.h"
#include "game_state.h"
#include "scena_battaglia.h"
#include "storia_logica.h"
#include "storia_scena.h"

namespace gubbio
{

void ScontriSullaMappa::svuota()
{
    _sprite.clear();
    _area = -1;
}

void ScontriSullaMappa::_prepara(const Esplorazione& esplorazione)
{
    _sprite.clear();
    _area = int(esplorazione.esploratore().area);

    for(int k = 0; k < progressione::SCONTRI; ++k)
    {
        const progressione::ScontroSullaMappa& s = GUBBIO_VOCE(progressione::SCONTRI_SULLA_MAPPA, k);

        if(int(s.area) == _area && _visibile(s))
        {
            bn::sprite_ptr sprite = sprite_sulla_mappa(s.incontro);
            esplorazione.colloca_sulla_mappa(sprite, mondo::piedi_x(s.tx), mondo::piedi_y(s.ty),
                                             sprite.shape_size().height());
            _sprite.push_back(bn::move(sprite));
        }
    }
}

bool ScontriSullaMappa::_visibile(const progressione::ScontroSullaMappa& s) const
{
    return ! progressione::vinto(g_game_state, s.bandiera) && (! _storia || storia::scontro_attivo(g_game_state, s.incontro));
}

bool ScontriSullaMappa::aggiorna(Esplorazione& esplorazione, const bn::sprite_palette_ptr& palette_testo)
{
    const mondo::Esploratore& e = esplorazione.esploratore();

    if(int(e.area) != _area)
    {
        _prepara(esplorazione);
    }

    if(esplorazione.in_dissolvenza())
    {
        return false;
    }

    int k = progressione::scontro_toccato(g_game_state, e.area, e.x, e.y);

    if(k < 0)
    {
        return false;
    }

    const progressione::ScontroSullaMappa& s = GUBBIO_VOCE(progressione::SCONTRI_SULLA_MAPPA, k);
    mondo::AreaId area = e.area;

    if(! _visibile(s))
    {
        return false;
    }

    // con la storia, il nemico e' l'inizio della sua scena: battute, battaglia, bandiere
    if(_storia)
    {
        svuota();
        _storia->recita(storia::scena_dello_scontro(s.incontro), &esplorazione, palette_testo);
        return true;
    }

    // la mappa si libera (tile e sprite) prima che la battaglia carichi i suoi
    svuota();
    esplorazione.sospendi();
    bn::core::update();

    battaglia::Esito esito = scena_battaglia(s.incontro, uint32_t(g_game_state.frames) | 1u, Guida::GIOCATORE,
                                             palette_testo, false, &g_game_state);
    BN_LOG("Scontro sulla mappa ", k, " esito ", int(esito));

    if(esito == battaglia::Esito::VITTORIA)
    {
        progressione::segna_vinto(g_game_state, s.bandiera);
    }
    else
    {
        // persa (o in sospeso): si torna all'ingresso dell'area, il nemico resta dov'e'
        mondo::colloca(esplorazione.esploratore(), area, 1);
    }

    esplorazione.ricompari();
    return true;
}

}
