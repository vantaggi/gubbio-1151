#ifndef GUBBIO_ESPLORAZIONE_H
#define GUBBIO_ESPLORAZIONE_H

#include "bn_bg_palette_ptr.h"
#include "bn_camera_ptr.h"
#include "bn_optional.h"
#include "bn_regular_bg_ptr.h"
#include "bn_regular_bg_tiles_ptr.h"
#include "bn_sprite_ptr.h"

#include "mondo_logica.h"
#include "vista_testo.h"

namespace gubbio
{

// La scena di esplorazione: il fondale dell'area (dalla mappa generata), la camera che segue il
// giocatore senza uscire dall'area, i varchi con una dissolvenza e l'etichetta col nome
// dell'area. Muoversi, urtare e attraversare passa tutto da mondo_logica.h.
class Esplorazione
{
public:
    explicit Esplorazione(const bn::sprite_palette_ptr& palette_testo);

    void entra(mondo::AreaId id, int spawn);

    // Input di un frame: dx, dy in -1..1, 'passi' pixel per asse. Ignorato durante una dissolvenza.
    void muovi(int dx, int dy, int passi);

    // Il giocatore e' stato spostato da fuori (la camminata automatica): ridisegna se serve.
    void sincronizza(mondo::Evento evento);

    void aggiorna();

    void nascondi_etichetta();

    [[nodiscard]] const mondo::Esploratore& esploratore() const
    {
        return _e;
    }

    [[nodiscard]] mondo::Esploratore& esploratore()
    {
        return _e;
    }

    [[nodiscard]] bool in_dissolvenza() const
    {
        return _dissolvenza != 0;
    }

private:
    bn::regular_bg_tiles_ptr _tiles;
    bn::bg_palette_ptr _palette;
    bn::camera_ptr _camera;
    bn::optional<bn::regular_bg_ptr> _fondale;
    bn::sprite_ptr _giocatore;
    VistaTesto _ombra;              // creata prima: i suoi sprite stanno sotto quelli dell'etichetta
    VistaTesto _etichetta;
    mondo::Esploratore _e;
    mondo::AreaId _area_caricata = mondo::AreaId(0);
    int _mezza_larghezza_mappa = 0;
    int _mezza_altezza_mappa = 0;
    int _dissolvenza = 0;           // >0 in uscita, <0 in entrata
    int _attesa_etichetta = 0;

    void _carica_fondale();
    void _mostra_etichetta(testi::TestoId id);
    void _dopo_evento(mondo::Evento evento);
};

}

#endif
