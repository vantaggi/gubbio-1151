#include "vista_menu.h"

#include "bn_color.h"
#include "bn_sprite_palette_item.h"
#include "bn_sprite_shape_size.h"
#include "bn_tile.h"

#include "stile/cornice.h"
#include "stile/palette.h"
#include "tabella.h"
#include "vista_testo.h"

namespace gubbio::menu
{

namespace
{
    constexpr int LARGHEZZA_SCHERMO = 240;
    constexpr int ALTEZZA_SCHERMO = 160;

    struct Colori
    {
        bn::color colori[16];
    };

    constexpr bn::color tono(int rampa, int t)
    {
        return bn::color(GUBBIO_VOCE(stile::PALETTE_GIORNO, rampa + t));
    }

    constexpr Colori colori_menu()
    {
        Colori c;

        for(int i = 0; i < 16; ++i)
        {
            c.colori[i] = bn::color(GUBBIO_VOCE(stile::CORNICE_PALETTE, i));
        }

        c.colori[NOTA] = tono(stile::RAMPA_PIETRA_CALCAREA, 1);
        c.colori[SPENTO] = tono(stile::RAMPA_NEUTRI, 2);
        c.colori[BORDO] = tono(stile::RAMPA_NEUTRI, 0);
        c.colori[GRIGIO] = tono(stile::RAMPA_NEUTRI, 3);
        return c;
    }

    constexpr Colori COLORI_MENU = colori_menu();

    // gli indici aggiunti stanno dove la cornice non ha colori: le scritte del gioco restano uguali
    static_assert(GUBBIO_VOCE(stile::CORNICE_PALETTE, NOTA) == 0 && GUBBIO_VOCE(stile::CORNICE_PALETTE, SPENTO) == 0 &&
                  GUBBIO_VOCE(stile::CORNICE_PALETTE, BORDO) == 0 && GUBBIO_VOCE(stile::CORNICE_PALETTE, GRIGIO) == 0);
}

bn::sprite_palette_ptr crea_palette()
{
    return bn::sprite_palette_ptr::create(
        bn::sprite_palette_item(bn::span<const bn::color>(COLORI_MENU.colori), bn::bpp_mode::BPP_4));
}

void colloca(bn::sprite_ptr& sprite, int x, int y, int larghezza, int altezza)
{
    sprite.set_position(x + larghezza / 2 - LARGHEZZA_SCHERMO / 2, y + altezza / 2 - ALTEZZA_SCHERMO / 2);
}

Striscia::Striscia(int x, int y, int larghezza, const bn::sprite_palette_ptr& palette) :
    _larghezza(larghezza)
{
    int n = (larghezza + 31) / 32;
    BN_ASSERT(n >= 1 && n <= SPRITE_MAX, "Striscia: larghezza ", larghezza);

    for(int k = 0; k < n; ++k)
    {
        _tiles.push_back(bn::sprite_tiles_ptr::allocate(4, bn::bpp_mode::BPP_4));
        bn::sprite_ptr s = bn::sprite_ptr::create(0, 0, bn::sprite_shape_size(32, 8), _tiles.back(), palette);
        colloca(s, x + k * 32, y, 32, 8);
        s.set_bg_priority(PRIORITA_RIQUADRI);
        _sprite.push_back(bn::move(s));
    }

    pulisci();
}

void Striscia::pulisci()
{
    for(bn::sprite_tiles_ptr& t : _tiles)
    {
        for(bn::tile& tile : *t.vram())
        {
            for(uint32_t& parola : tile.data)
            {
                parola = 0;
            }
        }
    }
}

void Striscia::rett(int x0, int y0, int x1, int y1, int colore)
{
    x0 = x0 < 0 ? 0 : x0;
    y0 = y0 < 0 ? 0 : y0;
    x1 = x1 >= _larghezza ? _larghezza - 1 : x1;
    y1 = y1 > 7 ? 7 : y1;

    for(int x = x0; x <= x1; ++x)
    {
        bn::span<bn::tile> vram = *_tiles[x / 32].vram();
        bn::tile& tile = vram[(x % 32) / 8];
        int p = x % 8;

        for(int y = y0; y <= y1; ++y)
        {
            tile.data[y] = (tile.data[y] & ~(uint32_t(0xF) << (4 * p))) | (uint32_t(colore) << (4 * p));
        }
    }
}

void disegna_barra(Striscia& s, int x, int y, int larghezza, int valore, int massimo, int colore)
{
    // come pieno() della battaglia: arrotondato in su, chi ha ancora qualcosa ha almeno un pixel
    int n = massimo <= 0 || valore <= 0 ? 0 : (valore * larghezza + massimo - 1) / massimo;
    n = n > larghezza ? larghezza : n;
    s.rett(x, y, x + larghezza + 1, y + 3, BORDO);
    s.rett(x + 1, y + 1, x + larghezza, y + 2, SPENTO);

    if(n > 0)
    {
        s.rett(x + 1, y + 1, x + n, y + 2, colore);
    }
}

void disegna_tessere(Striscia& s, int x, int aperta)
{
    for(int i = 0; i < 6; ++i)
    {
        int xx = x + i * 9;
        s.rett(xx, 0, xx + 6, 6, BORDO);
        s.rett(xx + 1, 1, xx + 5, 5, i == aperta ? VERMIGLIO : GRIGIO);
    }
}

bn::sprite_palette_ptr crea_palette_icone()
{
    struct ColoriIcone
    {
        bn::color c[16];
    };

    static constexpr ColoriIcone COLORI = [] {
        ColoriIcone r;

        for(int i = 0; i < 16; ++i)
        {
            r.c[i] = bn::color(GUBBIO_VOCE(stile::ICONE_MENU_PALETTE, i));
        }

        return r;
    }();

    return bn::sprite_palette_ptr::create(bn::sprite_palette_item(bn::span<const bn::color>(COLORI.c),
                                                                  bn::bpp_mode::BPP_4));
}

bn::sprite_ptr crea_icona(stile::IconaMenu icona, int x, int y, const bn::sprite_palette_ptr& palette)
{
    bn::sprite_tiles_ptr tiles = bn::sprite_tiles_ptr::allocate(1, bn::bpp_mode::BPP_4);
    bn::span<bn::tile> vram = *tiles.vram();

    for(int r = 0; r < 8; ++r)
    {
        vram[0].data[r] = GUBBIO_VOCE(stile::ICONE_MENU_TILE, int(icona) * 8 + r);
    }

    bn::sprite_ptr s = bn::sprite_ptr::create(0, 0, bn::sprite_shape_size(8, 8), bn::move(tiles), palette);
    colloca(s, x, y, 8, 8);
    s.set_bg_priority(PRIORITA_RIQUADRI);
    return s;
}

bn::sprite_ptr crea_cursore(const bn::sprite_palette_ptr& palette)
{
    bn::sprite_tiles_ptr tiles = bn::sprite_tiles_ptr::allocate(1, bn::bpp_mode::BPP_4);
    bn::span<bn::tile> vram = *tiles.vram();

    for(int r = 0; r < 8; ++r)
    {
        vram[0].data[r] = GUBBIO_VOCE(stile::CORNICE_TILE, stile::TILE_CURSORE * 8 + r);
    }

    bn::sprite_ptr cursore = bn::sprite_ptr::create(0, 0, bn::sprite_shape_size(8, 8), bn::move(tiles), palette);
    cursore.set_bg_priority(PRIORITA_RIQUADRI);
    return cursore;
}

}
