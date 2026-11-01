#include "esplorazione.h"

#include "bn_bg_palette_item.h"
#include "bn_bg_palettes.h"
#include "bn_color.h"
#include "bn_fixed.h"
#include "bn_regular_bg_map_cell_info.h"
#include "bn_regular_bg_map_ptr.h"
#include "bn_size.h"
#include "bn_sprite_palette_item.h"
#include "bn_sprite_palette_ptr.h"
#include "bn_sprite_palettes.h"
#include "bn_sprite_shape_size.h"
#include "bn_sprite_tiles_ptr.h"
#include "bn_tile.h"

namespace gubbio
{

namespace
{
    constexpr int LARGHEZZA_SCHERMO = 240;
    constexpr int ALTEZZA_SCHERMO = 160;
    constexpr int PASSI_DISSOLVENZA = 8;
    constexpr int FRAME_ETICHETTA = 150;
    // Etichetta chiara con ombra scura: si legge sui suoli chiari, sui tetti e sul fondo nero.
    constexpr int INCHIOSTRO_ETICHETTA = 2;
    constexpr int INCHIOSTRO_OMBRA = 1;

    struct Colori
    {
        bn::color colori[16];
    };

    constexpr Colori colori(const uint16_t (&parole)[16])
    {
        Colori c;

        for(int i = 0; i < 16; ++i)
        {
            c.colori[i] = bn::color(GUBBIO_VOCE(parole, i));
        }

        return c;
    }

    constexpr Colori COLORI_FONDALI = colori(mondo::PALETTE_FONDALI);
    constexpr Colori COLORI_GIOCATORE = colori(mondo::PALETTE_GIOCATORE);

    bn::regular_bg_tiles_ptr crea_tiles_fondali()
    {
        bn::regular_bg_tiles_ptr tiles = bn::regular_bg_tiles_ptr::allocate(mondo::TILE_FONDALI, bn::bpp_mode::BPP_4);
        bn::span<bn::tile> vram = *tiles.vram();

        for(int t = 0; t < mondo::TILE_FONDALI; ++t)
        {
            for(int r = 0; r < 8; ++r)
            {
                vram[t].data[r] = GUBBIO_VOCE(mondo::TILE_FONDALE, t * 8 + r);
            }
        }

        return tiles;
    }

    bn::sprite_ptr crea_giocatore()
    {
        bn::sprite_tiles_ptr tiles = bn::sprite_tiles_ptr::allocate(4, bn::bpp_mode::BPP_4);
        bn::span<bn::tile> vram = *tiles.vram();

        for(int t = 0; t < 4; ++t)
        {
            for(int r = 0; r < 8; ++r)
            {
                vram[t].data[r] = GUBBIO_VOCE(mondo::TILE_GIOCATORE, t * 8 + r);
            }
        }

        bn::sprite_palette_ptr palette = bn::sprite_palette_ptr::create(
            bn::sprite_palette_item(bn::span<const bn::color>(COLORI_GIOCATORE.colori), bn::bpp_mode::BPP_4));
        return bn::sprite_ptr::create(0, 0, bn::sprite_shape_size(bn::sprite_shape::SQUARE, bn::sprite_size::NORMAL),
                                      bn::move(tiles), bn::move(palette));
    }

    // Lato in celle della mappa hardware che contiene 'celle' celle: 32 o 64.
    constexpr int lato_mappa(int celle)
    {
        return celle <= 32 ? 32 : 64;
    }

    // Indice di una cella in una mappa hardware larga 'pitch': blocchi da 32x32 (come Butano).
    constexpr int indice_mappa(int x, int y, int pitch)
    {
        int blocco = ((y / 32) * (pitch / 32)) + (x / 32);
        return (blocco * 1024) + ((y % 32) * 32) + (x % 32);
    }

    constexpr int limita(int v, int minimo, int massimo)
    {
        return v < minimo ? minimo : (v > massimo ? massimo : v);
    }
}

Esplorazione::Esplorazione(const bn::sprite_palette_ptr& palette_testo) :
    _tiles(crea_tiles_fondali()),
    _palette(bn::bg_palette_ptr::create(
        bn::bg_palette_item(bn::span<const bn::color>(COLORI_FONDALI.colori), bn::bpp_mode::BPP_4))),
    _camera(bn::camera_ptr::create(0, 0)),
    _giocatore(crea_giocatore()),
    _ombra(testo::Contesto::AREA, 25, 9, INCHIOSTRO_OMBRA, palette_testo),
    _etichetta(testo::Contesto::AREA, 24, 8, INCHIOSTRO_ETICHETTA, palette_testo)
{
    _giocatore.set_camera(_camera);
}

void Esplorazione::entra(mondo::AreaId id, int spawn)
{
    mondo::colloca(_e, id, spawn);
    _carica_fondale();
}

void Esplorazione::_carica_fondale()
{
    const mondo::Area& a = mondo::area(_e.area);
    int w = lato_mappa(a.larghezza);
    int h = lato_mappa(a.altezza);
    _area_caricata = _e.area;

    _fondale.reset();
    bn::regular_bg_map_ptr mappa = bn::regular_bg_map_ptr::allocate(bn::size(w, h), _tiles, _palette);
    bn::span<bn::regular_bg_map_cell> celle = *mappa.vram();
    int palette_id = _palette.id();

    for(int y = 0; y < h; ++y)
    {
        for(int x = 0; x < w; ++x)
        {
            int tile = int(mondo::TileFondale::VUOTO);

            if(x < a.larghezza && y < a.altezza)
            {
                int i = x + y * a.larghezza;
                BN_ASSERT(i < a.larghezza * a.altezza, "Mappa: indice ", i, " fuori area");
                tile = a.mappa[i];
            }

            bn::regular_bg_map_cell_info info;
            info.set_tile_index(tile);
            info.set_palette_id(palette_id);
            celle[indice_mappa(x, y, w)] = info.cell();
        }
    }

    _mezza_larghezza_mappa = w * mondo::TILE_PX / 2;
    _mezza_altezza_mappa = h * mondo::TILE_PX / 2;
    _fondale = bn::regular_bg_ptr::create(0, 0, bn::move(mappa));
    _fondale->set_camera(_camera);
    _mostra_etichetta(a.etichetta);
    aggiorna();
}

void Esplorazione::_mostra_etichetta(testi::TestoId id)
{
    _ombra.mostra(id);
    _etichetta.mostra(id);
    _attesa_etichetta = FRAME_ETICHETTA;
}

void Esplorazione::_dopo_evento(mondo::Evento evento)
{
    if(evento == mondo::Evento::CAMBIO_AREA)
    {
        _dissolvenza = PASSI_DISSOLVENZA;
    }
    else if(evento == mondo::Evento::INGRESSO_DUNGEON)
    {
        const mondo::Area& a = mondo::area(_e.area);
        _mostra_etichetta(mondo::varco_di(a, _e.ultimo_varco).etichetta);
    }
}

void Esplorazione::muovi(int dx, int dy, int passi)
{
    if(_dissolvenza)
    {
        return;
    }

    for(int p = 0; p < passi; ++p)
    {
        mondo::Evento evento = mondo::Evento::NESSUNO;

        if(dx && mondo::muovi(_e, dx, 0))
        {
            evento = mondo::controlla_varco(_e);
        }

        if(evento == mondo::Evento::NESSUNO && dy && mondo::muovi(_e, 0, dy))
        {
            evento = mondo::controlla_varco(_e);
        }

        if(evento != mondo::Evento::NESSUNO)
        {
            _dopo_evento(evento);
            return;
        }
    }

    if(dx)
    {
        _giocatore.set_horizontal_flip(dx < 0);
    }
}

void Esplorazione::sincronizza(mondo::Evento evento)
{
    if(evento == mondo::Evento::CAMBIO_AREA)
    {
        _carica_fondale();
    }
    else if(evento == mondo::Evento::INGRESSO_DUNGEON)
    {
        _dopo_evento(evento);
    }
}

void Esplorazione::aggiorna()
{
    // Dissolvenza: in uscita scurisce, a meta' carica la nuova area, in entrata schiarisce.
    if(_dissolvenza > 0)
    {
        --_dissolvenza;
        bn::fixed intensita = bn::fixed(PASSI_DISSOLVENZA - _dissolvenza) / PASSI_DISSOLVENZA;
        bn::bg_palettes::set_fade(bn::color(0, 0, 0), intensita);
        bn::sprite_palettes::set_fade(bn::color(0, 0, 0), intensita);

        if(_dissolvenza == 0)
        {
            _carica_fondale();
            _dissolvenza = -PASSI_DISSOLVENZA;
        }

        return;
    }

    if(_dissolvenza < 0)
    {
        ++_dissolvenza;
        bn::fixed intensita = bn::fixed(-_dissolvenza) / PASSI_DISSOLVENZA;
        bn::bg_palettes::set_fade(bn::color(0, 0, 0), intensita);
        bn::sprite_palettes::set_fade(bn::color(0, 0, 0), intensita);
    }

    // La camera segue il giocatore ma non mostra oltre i bordi dell'area; un'area piu' stretta
    // dello schermo resta centrata.
    const mondo::Area& a = mondo::area(_e.area);
    int larghezza = a.larghezza * mondo::TILE_PX;
    int altezza = a.altezza * mondo::TILE_PX;
    int cx = larghezza <= LARGHEZZA_SCHERMO ? larghezza / 2 :
             limita(_e.x, LARGHEZZA_SCHERMO / 2, larghezza - LARGHEZZA_SCHERMO / 2);
    int cy = altezza <= ALTEZZA_SCHERMO ? altezza / 2 :
             limita(_e.y, ALTEZZA_SCHERMO / 2, altezza - ALTEZZA_SCHERMO / 2);
    _camera.set_position(cx - _mezza_larghezza_mappa, cy - _mezza_altezza_mappa);

    // Lo sprite 16x16 ha i piedi sull'ultima riga.
    _giocatore.set_position(_e.x - _mezza_larghezza_mappa, _e.y - 7 - _mezza_altezza_mappa);

    if(_attesa_etichetta > 0)
    {
        _ombra.avanza();
        _etichetta.avanza();

        if(--_attesa_etichetta == 0)
        {
            _ombra.nascondi();
            _etichetta.nascondi();
        }
    }
}

void Esplorazione::nascondi_etichetta()
{
    _attesa_etichetta = 0;
    _ombra.nascondi();
    _etichetta.nascondi();
}

}
