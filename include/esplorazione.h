#ifndef GUBBIO_ESPLORAZIONE_H
#define GUBBIO_ESPLORAZIONE_H

#include "bn_bg_palette_ptr.h"
#include "bn_camera_ptr.h"
#include "bn_optional.h"
#include "bn_regular_bg_ptr.h"
#include "bn_regular_bg_tiles_ptr.h"
#include "bn_sprite_ptr.h"
#include "bn_vector.h"

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

    // Rimette il giocatore dove l'ha lasciato un salvataggio: area e piedi in pixel.
    void riprendi(mondo::AreaId id, int x, int y);

    // Per una battaglia: lo sfondo si libera (i suoi tile servono alla scena) e il giocatore si
    // nasconde; ricompari() rimette tutto com'era.
    void sospendi();
    void ricompari();

    // Uno sprite che sta sulla mappa (un nemico): sulla camera dell'area, coi piedi in (x, y) pixel.
    void colloca_sulla_mappa(bn::sprite_ptr& sprite, int x, int y, int altezza) const;

    // Input di un frame: dx, dy in -1..1, 'passi' pixel per asse. Ignorato durante una dissolvenza.
    void muovi(int dx, int dy, int passi);

    // Il giocatore e' stato spostato da fuori (la camminata automatica): ridisegna se serve.
    void sincronizza(mondo::Evento evento);

    void aggiorna();

    void nascondi_etichetta();

    // Il varco 'indice' dell'area si urta come un muro (-1: tutti aperti). Lo decide la storia a ogni frame
    // (storia::varco_chiuso(): il duello del Condotto).
    void chiudi_varco(int indice)
    {
        _varco_chiuso = indice;
    }

    // Il giocatore ha urtato il varco chiuso dall'ultima chiamata? (una volta: poi torna false)
    [[nodiscard]] bool urto_al_varco_chiuso()
    {
        bool urto = _urto_al_varco;
        _urto_al_varco = false;
        return urto;
    }

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
    bn::optional<bn::regular_bg_tiles_ptr> _tiles;
    bn::bg_palette_ptr _palette;
    bn::camera_ptr _camera;
    bn::optional<bn::regular_bg_ptr> _fondale;
    bn::sprite_ptr _giocatore;
    bn::vector<bn::sprite_ptr, 6> _cartiglio;  // creato per primo: sta sotto il testo
    VistaTesto _ombra;              // creata prima: i suoi sprite stanno sotto quelli dell'etichetta
    VistaTesto _etichetta;
    mondo::Esploratore _e;
    mondo::AreaId _area_caricata = mondo::AreaId(0);
    int _mezza_larghezza_mappa = 0;
    int _mezza_altezza_mappa = 0;
    int _dissolvenza = 0;           // >0 in uscita, <0 in entrata
    int _riflessi = 0;              // i frame dei riflessi dell'acqua nelle stanze della gola
    int _varco_chiuso = -1;         // il varco che si urta come un muro (chiudi_varco)
    bool _urto_al_varco = false;
    int _attesa_etichetta = 0;
    // la figura del giocatore (tools/sagome_mappa.py): direzione, passo, respiro
    enum Direzione { GIU, SU, DESTRA, SINISTRA };
    int _direzione = GIU;
    int _passo = 0;
    int _fermo = 0;
    int _mostrato = -1;
    bool _mosso = false;
    bool _corre = false;

    void _carica_fondale(bool etichetta = true);
    void _mostra_etichetta(testi::TestoId id);
    void _mostra_cartiglio(bool visibile);
    void _dopo_evento(mondo::Evento evento);
    void _anima_giocatore();
};

}

#endif
