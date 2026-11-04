#include "pannello.h"

#include "bn_assert.h"
#include "bn_color.h"
#include "bn_sprite_palette_item.h"
#include "bn_sprite_shape_size.h"
#include "bn_tile.h"

#include "stile/palette.h"
#include "tabella.h"
#include "vista_testo.h"

namespace gubbio::pannello
{

namespace
{
    constexpr int LARGHEZZA_SCHERMO = 240;
    constexpr int ALTEZZA_SCHERMO = 160;
    constexpr int SPRITE_L = 64;
    constexpr int SPRITE_A = 32;

    struct Colori
    {
        bn::color colori[16];
    };

    constexpr bn::color tono(int rampa, int t)
    {
        return bn::color(GUBBIO_VOCE(stile::PALETTE_GIORNO, rampa + t));
    }

    constexpr Colori colori_aiuti()
    {
        Colori c;
        c.colori[PIOMBO] = tono(stile::RAMPA_NEUTRI, 0);
        c.colori[CHIARO] = tono(stile::RAMPA_NEUTRI, 4);
        c.colori[SCURO] = tono(stile::RAMPA_NEUTRI, 1);
        c.colori[LEGNO] = tono(stile::RAMPA_LEGNO_E_CUOIO, 1);
        c.colori[LEGNO_LUCE] = tono(stile::RAMPA_LEGNO_E_CUOIO, 2);
        c.colori[PIETRA] = tono(stile::RAMPA_PIETRA_CALCAREA, 4);
        c.colori[ORO] = tono(stile::RAMPA_ORO_E_BRONZO, 3);
        c.colori[ORO_SPENTO] = tono(stile::RAMPA_ORO_E_BRONZO, 2);
        return c;
    }

    constexpr Colori COLORI_AIUTI = colori_aiuti();
}

bn::sprite_palette_ptr crea_palette()
{
    return bn::sprite_palette_ptr::create(
        bn::sprite_palette_item(bn::span<const bn::color>(COLORI_AIUTI.colori), bn::bpp_mode::BPP_4));
}

Pannello::Pannello(int x, int y, int larghezza, int altezza, const bn::sprite_palette_ptr& palette) :
    _x(x),
    _y(y),
    _larghezza(larghezza),
    _altezza(altezza),
    _colonne((larghezza + SPRITE_L - 1) / SPRITE_L)
{
    int righe = (altezza + SPRITE_A - 1) / SPRITE_A;
    BN_ASSERT(_colonne * righe <= SPRITE_MAX, "Pannello: troppo grande ", larghezza, "x", altezza);

    for(int r = 0; r < righe; ++r)
    {
        for(int c = 0; c < _colonne; ++c)
        {
            _tiles.push_back(bn::sprite_tiles_ptr::allocate(32, bn::bpp_mode::BPP_4));

            for(bn::tile& t : *_tiles.back().vram())
            {
                for(uint32_t& parola : t.data)
                {
                    parola = 0;
                }
            }

            bn::sprite_ptr s = bn::sprite_ptr::create(0, 0, bn::sprite_shape_size(SPRITE_L, SPRITE_A), _tiles.back(),
                                                      palette);
            s.set_bg_priority(PRIORITA_RIQUADRI);
            s.set_z_order(1);   // sotto il testo
            _sprite.push_back(bn::move(s));
        }
    }

    sposta(x, y);
}

void Pannello::sposta(int x, int y)
{
    _x = x;
    _y = y;

    for(int i = 0; i < _sprite.size(); ++i)
    {
        int sx = x + (i % _colonne) * SPRITE_L;
        int sy = y + (i / _colonne) * SPRITE_A;
        _sprite[i].set_position(sx + SPRITE_L / 2 - LARGHEZZA_SCHERMO / 2, sy + SPRITE_A / 2 - ALTEZZA_SCHERMO / 2);
        // uno sprite tutto fuori dallo schermo, in alto, rientrerebbe dal basso (le coordinate dell'OAM girano)
        _sprite[i].set_visible(sy + SPRITE_A > 0 && sy < ALTEZZA_SCHERMO);
    }
}

void Pannello::_punto(int x, int y, int colore)
{
    if(x < 0 || y < 0 || x >= _larghezza || y >= _altezza)
    {
        return;
    }

    int sprite = (y / SPRITE_A) * _colonne + x / SPRITE_L;
    int px = x % SPRITE_L;
    int py = y % SPRITE_A;
    bn::tile& t = (*_tiles[sprite].vram())[(py / 8) * (SPRITE_L / 8) + px / 8];
    int sp = 4 * (px % 8);
    uint32_t& parola = t.data[py % 8];
    parola = (parola & ~(uint32_t(0xF) << sp)) | (uint32_t(colore) << sp);
}

void Pannello::rett(int x0, int y0, int x1, int y1, int colore)
{
    for(int y = y0; y <= y1; ++y)
    {
        for(int x = x0; x <= x1; ++x)
        {
            _punto(x, y, colore);
        }
    }
}

void Pannello::bordo(int x0, int y0, int x1, int y1, int colore)
{
    rett(x0, y0, x1, y0, colore);
    rett(x0, y1, x1, y1, colore);
    rett(x0, y0, x0, y1, colore);
    rett(x1, y0, x1, y1, colore);
}

void Pannello::_punto_del_disegno(int x, int y, char c, bool spento)
{
    if(c == 'k')
    {
        _punto(x, y, PIOMBO);
    }
    else if(c == 'O')
    {
        _punto(x, y, spento ? ORO_SPENTO : ORO);
    }
    else if(c == 'o')
    {
        _punto(x, y, ORO_SPENTO);
    }
}

void Pannello::disegno(const char* const (&righe)[8], int x, int y, bool spento)
{
    disegno_da([&righe](int xx, int yy) { return righe[yy][xx]; }, x, y, spento);
}

}
