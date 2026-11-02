#include "esplorazione.h"

#include "bn_bg_palette_item.h"
#include "bn_bg_palettes.h"
#include "bn_color.h"
#include "bn_fixed.h"
#include "bn_regular_bg_map_item.h"
#include "bn_regular_bg_tiles_item.h"
#include "bn_regular_bg_map_ptr.h"
#include "bn_size.h"
#include "bn_sprite_palette_item.h"
#include "bn_sprite_palette_ptr.h"
#include "bn_sprite_palettes.h"
#include "bn_sprite_shape_size.h"
#include "bn_sprite_tiles_item.h"
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
    constexpr Colori COLORI_FONDALI_CUPI = colori(mondo::PALETTE_FONDALI_CUPA);
    constexpr Colori COLORI_GIOCATORE = colori(mondo::PALETTE_GIOCATORE);

    // Il cartiglio: sei pezzi da 32x16 (sinistro, quattro centrali, destro) in cima allo schermo,
    // dietro il nome dell'area, con la palette dei fondali. Nascosto finche' non c'e' un nome.
    constexpr int CARTIGLIO_X = 16;
    constexpr int CARTIGLIO_Y = 4;
    constexpr int CARTIGLIO_PEZZI = 6;

    bn::vector<bn::sprite_ptr, CARTIGLIO_PEZZI> crea_cartiglio()
    {
        bn::sprite_palette_ptr palette = bn::sprite_palette_ptr::create(
            bn::sprite_palette_item(bn::span<const bn::color>(COLORI_FONDALI.colori), bn::bpp_mode::BPP_4));
        bn::vector<bn::sprite_ptr, CARTIGLIO_PEZZI> out;

        for(int i = 0; i < CARTIGLIO_PEZZI; ++i)
        {
            int pezzo = i == 0 ? 0 : (i == CARTIGLIO_PEZZI - 1 ? 2 : 1);
            bn::sprite_tiles_item tiles(bn::span<const bn::tile>(
                mondo::TILE_CARTIGLIO + pezzo * mondo::TILE_PER_PEZZO_CARTIGLIO, mondo::TILE_PER_PEZZO_CARTIGLIO),
                bn::bpp_mode::BPP_4);
            bn::sprite_ptr sprite = bn::sprite_ptr::create(
                CARTIGLIO_X + 16 + i * 32 - LARGHEZZA_SCHERMO / 2, CARTIGLIO_Y + 8 - ALTEZZA_SCHERMO / 2,
                bn::sprite_shape_size(32, 16), tiles.create_tiles(), palette);
            sprite.set_visible(false);
            out.push_back(bn::move(sprite));
        }

        return out;
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

    constexpr int limita(int v, int minimo, int massimo)
    {
        return v < minimo ? minimo : (v > massimo ? massimo : v);
    }
}

Esplorazione::Esplorazione(const bn::sprite_palette_ptr& palette_testo) :
    _palette(bn::bg_palette_ptr::create(
        bn::bg_palette_item(bn::span<const bn::color>(COLORI_FONDALI.colori), bn::bpp_mode::BPP_4))),
    _camera(bn::camera_ptr::create(0, 0)),
    _giocatore(crea_giocatore()),
    _cartiglio(crea_cartiglio()),
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

void Esplorazione::riprendi(mondo::AreaId id, int x, int y)
{
    _e.area = id;
    _e.x = x;
    _e.y = y;
    _e.varco_sotto = -1;
    _carica_fondale();
}

void Esplorazione::sospendi()
{
    nascondi_etichetta();
    _giocatore.set_visible(false);
    _fondale.reset();
    _tiles.reset();
}

void Esplorazione::ricompari()
{
    _carica_fondale();
    _giocatore.set_visible(true);
}

void Esplorazione::colloca_sulla_mappa(bn::sprite_ptr& sprite, int x, int y, int altezza) const
{
    sprite.set_camera(_camera);
    sprite.set_position(x - _mezza_larghezza_mappa, y - altezza / 2 - _mezza_altezza_mappa);
}

void Esplorazione::_carica_fondale()
{
    // Le celle sono gia' in ROM (include/mondo.h): Butano le copia in VRAM, o per una big map ne
    // carica solo la parte vicina allo schermo, e aggiunge da se' gli scostamenti di tile e palette.
    const mondo::Area& a = mondo::area(_e.area);
    _area_caricata = _e.area;
    _fondale.reset();

    // Ogni area ha i suoi tile (suolo e monumenti): prima si lascia la mappa vecchia, poi i suoi tile.
    _tiles.reset();

    // le stanze della gola hanno la palette cupa
    const Colori& c = a.cupa ? COLORI_FONDALI_CUPI : COLORI_FONDALI;

    for(int i = 0; i < 16; ++i)
    {
        _palette.set_color(i, c.colori[i]);
    }

    _tiles = bn::regular_bg_tiles_ptr::create(
        bn::regular_bg_tiles_item(bn::span<const bn::tile>(a.tile, a.tile_conteggio), bn::bpp_mode::BPP_4));

    bn::size lati(a.larghezza_fondale, a.altezza_fondale);
    bn::regular_bg_map_item voce(*a.fondale, lati, bn::compression_type::NONE, 1, a.fondale_grande);
    _mezza_larghezza_mappa = lati.width() * mondo::TILE_PX / 2;
    _mezza_altezza_mappa = lati.height() * mondo::TILE_PX / 2;
    _fondale = bn::regular_bg_ptr::create(0, 0, bn::regular_bg_map_ptr::create(voce, *_tiles, _palette));
    _fondale->set_camera(_camera);
    _mostra_etichetta(a.etichetta);
    aggiorna();
}

void Esplorazione::_mostra_etichetta(testi::TestoId id)
{
    _ombra.mostra(id);
    _etichetta.mostra(id);
    _mostra_cartiglio(true);
    _attesa_etichetta = FRAME_ETICHETTA;
}

void Esplorazione::_mostra_cartiglio(bool visibile)
{
    for(bn::sprite_ptr& pezzo : _cartiglio)
    {
        pezzo.set_visible(visibile);
    }
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
            _mostra_cartiglio(false);
        }
    }
}

void Esplorazione::nascondi_etichetta()
{
    _attesa_etichetta = 0;
    _ombra.nascondi();
    _etichetta.nascondi();
    _mostra_cartiglio(false);
}

}
