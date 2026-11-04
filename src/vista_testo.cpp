#include "vista_testo.h"

#include "bn_bg_palette_item.h"
#include "bn_bg_palette_ptr.h"
#include "bn_color.h"
#include "bn_regular_bg_map_cell_info.h"
#include "bn_regular_bg_map_ptr.h"
#include "bn_regular_bg_tiles_ptr.h"
#include "bn_size.h"
#include "bn_sprite_palette_item.h"
#include "bn_sprite_shape_size.h"
#include "bn_tile.h"

#include "formatta.h"
#include "stile/cornice.h"

namespace gubbio
{

namespace
{
    constexpr int LARGHEZZA_SCHERMO = 240;
    constexpr int ALTEZZA_SCHERMO = 160;

    struct ColoriCornice
    {
        bn::color colori[16];
    };

    constexpr ColoriCornice colori_cornice()
    {
        ColoriCornice c;

        for(int i = 0; i < 16; ++i)
        {
            c.colori[i] = bn::color(GUBBIO_VOCE(stile::CORNICE_PALETTE, i));
        }

        return c;
    }

    constexpr ColoriCornice COLORI_CORNICE = colori_cornice();

    // Sprite 32x16: la riga di testo (10 px) sta nella meta' alta.
    bn::sprite_ptr crea_sprite(int x, int y, const bn::sprite_tiles_ptr& tiles,
                               const bn::sprite_palette_ptr& palette)
    {
        return bn::sprite_ptr::create(x + 16 - LARGHEZZA_SCHERMO / 2, y + 8 - ALTEZZA_SCHERMO / 2,
                                      bn::sprite_shape_size(bn::sprite_shape::WIDE, bn::sprite_size::BIG),
                                      tiles, palette);
    }

    void pulisci_tiles(bn::sprite_tiles_ptr& tiles)
    {
        for(bn::tile& t : *tiles.vram())
        {
            for(uint32_t& parola : t.data)
            {
                parola = 0;
            }
        }
    }

    void accendi_pixel(bn::sprite_tiles_ptr& tiles, int x_nello_sprite, int y, int inchiostro)
    {
        int parola = testo::parola_pixel(x_nello_sprite, y);
        bn::span<bn::tile> vram = *tiles.vram();
        vram[parola / 8].data[parola % 8] |= uint32_t(inchiostro) << testo::spostamento_pixel(x_nello_sprite);
    }

    constexpr int larghezza_numero_max()
    {
        int cifra_max = 0;

        for(char32_t c = U'0'; c <= U'9'; ++c)
        {
            int l = stile::trova_glifo(c)->larghezza;
            cifra_max = l > cifra_max ? l : cifra_max;
        }

        return stile::trova_glifo(U'-')->larghezza + stile::FONT_SPAZIATURA +
               5 * (cifra_max + stile::FONT_SPAZIATURA) - stile::FONT_SPAZIATURA;
    }

    static_assert(larghezza_numero_max() <= testi::LARGHEZZA_SPRITE, "\"-32768\" deve stare in uno sprite");
}

VistaTesto::VistaTesto(testo::Contesto contesto, int x, int y, int inchiostro,
                       const bn::sprite_palette_ptr& palette) :
    _contesto(contesto),
    _sprite_per_riga(testo::sprite_per_riga(contesto)),
    _inchiostro(inchiostro)
{
    int righe = testo::righe_contesto(contesto);
    BN_ASSERT(righe * _sprite_per_riga <= SPRITE_MAX, "VistaTesto: contesto troppo grande");

    for(int r = 0; r < righe; ++r)
    {
        for(int k = 0; k < _sprite_per_riga; ++k)
        {
            _tiles.push_back(bn::sprite_tiles_ptr::allocate(8, bn::bpp_mode::BPP_4));
            _sprite.push_back(crea_sprite(x + k * testi::LARGHEZZA_SPRITE,
                                          y + r * stile::FONT_INTERLINEA, _tiles.back(), palette));
            _sprite.back().set_visible(false);
        }
    }
}

void VistaTesto::_pulisci()
{
    for(bn::sprite_tiles_ptr& tiles : _tiles)
    {
        pulisci_tiles(tiles);
    }

    for(bn::sprite_ptr& sprite : _sprite)
    {
        sprite.set_visible(false);
    }
}

void VistaTesto::mostra(testo::TestoId id)
{
    const testo::Testo& t = testo::dati(id);
    BN_ASSERT(t.contesto == _contesto, "VistaTesto: testo ", int(id), " di un altro contesto");

    _pulisci();
    _testo = &t;
    _rivelati = 0;
    _riga = 0;
    _nella_riga = 0;
}

void VistaTesto::avanza()
{
    if(! _testo || completo())
    {
        return;
    }

    int ir = testo::indice_riga(*_testo, _riga);

    while(_nella_riga == testo::riga(ir).glifi)
    {
        ++_riga;
        _nella_riga = 0;
        ir = testo::indice_riga(*_testo, _riga);
    }

    int ig = testo::riga(ir).primo_glifo + _nella_riga;
    ++_nella_riga;
    ++_rivelati;

    int primo_sprite = _riga * _sprite_per_riga;
    int accesi = testo::sprite_accesi(ir, _nella_riga);
    BN_ASSERT(accesi <= _sprite_per_riga, "VistaTesto: punto di taglio oltre la riga");

    for(int k = 0; k < accesi; ++k)
    {
        _sprite[primo_sprite + k].set_visible(true);
    }

    testo::per_ogni_pixel(testo::glifo(testo::glifo_font(ig)), testo::x_glifo(ig), [&](int px, int py) {
        int k = px / testi::LARGHEZZA_SPRITE;
        BN_ASSERT(k < accesi, "VistaTesto: pixel in uno sprite spento, glifo ", ig);
        accendi_pixel(_tiles[primo_sprite + k], px % testi::LARGHEZZA_SPRITE, py, _inchiostro);
    });
}

void VistaTesto::rivela_tutto()
{
    while(_testo && ! completo())
    {
        avanza();
    }
}

void VistaTesto::nascondi()
{
    _pulisci();
    _testo = nullptr;
    _rivelati = 0;
}

bool VistaTesto::completo() const
{
    return _testo && _rivelati == _testo->glifi;
}

int VistaTesto::rivelati() const
{
    return _rivelati;
}

VistaNumero::VistaNumero(int x, int y, int inchiostro, const bn::sprite_palette_ptr& palette, int contorno) :
    _inchiostro(inchiostro),
    _contorno(contorno),
    _tiles(bn::sprite_tiles_ptr::allocate(8, bn::bpp_mode::BPP_4)),
    _sprite(crea_sprite(x, y, _tiles, palette))
{
}

void VistaNumero::mostra(int valore)
{
    constexpr int L = testi::LARGHEZZA_SPRITE;
    constexpr int A = 16;
    char cifre[FORMATTA_CARATTERI_MAX + 1] = {};
    int n = formatta_intero(valore, cifre);
    int x = _contorno >= 0 ? 1 : 0;     // col contorno, un pixel di margine a sinistra
    bool acceso[A][L] = {};

    pulisci_tiles(_tiles);

    for(int i = 0; i < n; ++i)
    {
        const stile::Glifo* g = stile::trova_glifo(char32_t(cifre[i]));
        BN_ASSERT(g, "VistaNumero: cifra senza glifo ", int(cifre[i]));

        testo::per_ogni_pixel(*g, x, [&](int px, int py) {
            if(px >= 0 && px < L && py >= 0 && py < A)
            {
                acceso[py][px] = true;
                accendi_pixel(_tiles, px, py, _inchiostro);
            }
        });

        x += g->larghezza + stile::FONT_SPAZIATURA;
    }

    if(_contorno < 0)
    {
        return;
    }

    // il contorno: ogni pixel spento con un vicino acceso (anche in diagonale)
    for(int py = 0; py < A; ++py)
    {
        for(int px = 0; px < L; ++px)
        {
            if(acceso[py][px])
            {
                continue;
            }

            bool vicino = false;

            for(int dy = -1; dy <= 1 && ! vicino; ++dy)
            {
                for(int dx = -1; dx <= 1 && ! vicino; ++dx)
                {
                    int vx = px + dx;
                    int vy = py + dy;
                    vicino = vx >= 0 && vx < L && vy >= 0 && vy < A && acceso[vy][vx];
                }
            }

            if(vicino)
            {
                accendi_pixel(_tiles, px, py, _contorno);
            }
        }
    }
}

void VistaNumero::colloca(int x, int y)
{
    _sprite.set_position(x + 16 - LARGHEZZA_SCHERMO / 2, y + 8 - ALTEZZA_SCHERMO / 2);
    _sprite.set_visible(true);
}

void VistaNumero::nascondi()
{
    _sprite.set_visible(false);
}

bn::sprite_palette_ptr crea_palette_testo()
{
    return bn::sprite_palette_ptr::create(
        bn::sprite_palette_item(bn::span<const bn::color>(COLORI_CORNICE.colori), bn::bpp_mode::BPP_4));
}

bn::regular_bg_ptr crea_riquadro_dialogo()
{
    constexpr int TILE_VUOTO = stile::TILE_CORNICE;

    bn::regular_bg_tiles_ptr tiles = bn::regular_bg_tiles_ptr::allocate(TILE_VUOTO + 1, bn::bpp_mode::BPP_4);
    bn::span<bn::tile> vram_tiles = *tiles.vram();

    for(int t = 0; t <= TILE_VUOTO; ++t)
    {
        for(int r = 0; r < 8; ++r)
        {
            vram_tiles[t].data[r] = t < TILE_VUOTO ? GUBBIO_VOCE(stile::CORNICE_TILE, t * 8 + r) : 0;
        }
    }

    bn::bg_palette_ptr palette = bn::bg_palette_ptr::create(
        bn::bg_palette_item(bn::span<const bn::color>(COLORI_CORNICE.colori), bn::bpp_mode::BPP_4));
    bn::regular_bg_map_ptr mappa = bn::regular_bg_map_ptr::allocate(bn::size(32, 32), tiles, palette);
    bn::span<bn::regular_bg_map_cell> celle = *mappa.vram();

    int x0 = stile::DIALOGO_X / 8;
    int y0 = stile::DIALOGO_Y / 8;
    int colonne = stile::DIALOGO_COLONNE;
    int righe = stile::DIALOGO_RIGHE;

    for(int y = 0; y < 32; ++y)
    {
        for(int x = 0; x < 32; ++x)
        {
            int cx = x - x0;
            int cy = y - y0;
            int tile = TILE_VUOTO;
            bool hflip = false;
            bool vflip = false;

            if(cx >= 0 && cx < colonne && cy >= 0 && cy < righe)
            {
                bool bordo_x = cx == 0 || cx == colonne - 1;
                bool bordo_y = cy == 0 || cy == righe - 1;

                if(bordo_x && bordo_y)
                {
                    tile = stile::TILE_ANGOLO;
                    hflip = cx != 0;
                    vflip = cy != 0;
                }
                else if(bordo_y)
                {
                    tile = GUBBIO_VOCE(stile::LATO_ORIZZONTALE, (cx - 1) % 3);
                }
                else if(bordo_x)
                {
                    tile = GUBBIO_VOCE(stile::LATO_VERTICALE, (cy - 1) % 3);
                }
                else
                {
                    tile = stile::TILE_CENTRO;
                }
            }

            bn::regular_bg_map_cell_info info;
            info.set_tile_index(tile);
            info.set_horizontal_flip(hflip);
            info.set_vertical_flip(vflip);
            info.set_palette_id(palette.id());
            celle[y * 32 + x] = info.cell();
        }
    }

    // Una mappa 256x256 centrata sullo schermo ha l'angolo in (-8, -48): si sposta in (0, 0).
    return bn::regular_bg_ptr::create(256 / 2 - LARGHEZZA_SCHERMO / 2, 256 / 2 - ALTEZZA_SCHERMO / 2,
                                      mappa);
}

}
