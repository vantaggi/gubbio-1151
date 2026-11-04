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
        bn::sprite_ptr s = bn::sprite_ptr::create(x + 16 - LARGHEZZA_SCHERMO / 2, y + 8 - ALTEZZA_SCHERMO / 2,
                                                  bn::sprite_shape_size(bn::sprite_shape::WIDE, bn::sprite_size::BIG),
                                                  tiles, palette);
        s.set_bg_priority(PRIORITA_RIQUADRI);     // sopra i riquadri e la scena
        return s;
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
    char cifre[FORMATTA_CARATTERI_MAX + 1] = {};
    int n = formatta_intero(valore, cifre);
    _scrivi(cifre, n);
}

void VistaNumero::mostra_tempo(int secondi)
{
    char caratteri[TEMPO_CARATTERI_MAX + 1] = {};
    int n = formatta_tempo(secondi, caratteri);
    _scrivi(caratteri, n);
}

void VistaNumero::mostra_livelli(int a, int b, int c)
{
    char caratteri[LIVELLI_CARATTERI + 1] = {};
    int n = formatta_livelli(a, b, c, caratteri);
    _scrivi(caratteri, n);
}

void VistaNumero::_scrivi(const char* caratteri, int n)
{
    constexpr int L = testi::LARGHEZZA_SPRITE;
    constexpr int A = 16;
    int x = _contorno >= 0 ? 1 : 0;     // col contorno, un pixel di margine a sinistra
    bool acceso[A][L] = {};

    pulisci_tiles(_tiles);

    for(int i = 0; i < n; ++i)
    {
        const stile::Glifo* g = stile::trova_glifo(char32_t(caratteri[i]));
        BN_ASSERT(g, "VistaNumero: carattere senza glifo ", int(caratteri[i]));

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

namespace
{
    constexpr int TILE_VUOTO = stile::TILE_CORNICE;      // l'ultimo tile del fondo dei riquadri: trasparente

    bn::regular_bg_tiles_ptr tiles_riquadri()
    {
        bn::regular_bg_tiles_ptr tiles = bn::regular_bg_tiles_ptr::allocate(TILE_VUOTO + 1, bn::bpp_mode::BPP_4);
        bn::span<bn::tile> vram_tiles = *tiles.vram();

        for(int t = 0; t <= TILE_VUOTO; ++t)
        {
            for(int r = 0; r < 8; ++r)
            {
                vram_tiles[t].data[r] = t < TILE_VUOTO ? GUBBIO_VOCE(stile::CORNICE_TILE, t * 8 + r) : 0;
            }
        }

        return tiles;
    }

}

int larghezza_testo(testo::TestoId id)
{
    const testo::Testo& t = testo::dati(id);
    return testo::riga(testo::indice_riga(t, 0)).larghezza;
}

Riquadri::Riquadri() :
    _mappa(bn::regular_bg_map_ptr::allocate(
        bn::size(32, 32), tiles_riquadri(),
        bn::bg_palette_ptr::create(bn::bg_palette_item(bn::span<const bn::color>(COLORI_CORNICE.colori),
                                                       bn::bpp_mode::BPP_4)))),
    // Una mappa 256x256 centrata sullo schermo ha l'angolo in (-8, -48): si sposta in (0, 0).
    _bg(bn::regular_bg_ptr::create(256 / 2 - LARGHEZZA_SCHERMO / 2, 256 / 2 - ALTEZZA_SCHERMO / 2, _mappa))
{
    _bg.set_priority(PRIORITA_RIQUADRI);
    svuota();
}

void Riquadri::_cella(int tx, int ty, TileRiquadro t)
{
    if(tx < 0 || tx >= 32 || ty < 0 || ty >= 32)
    {
        return;
    }

    // La radice del vecchio bug della cornice: le celle scritte a mano in VRAM vogliono l'indice ASSOLUTO del
    // tile, cioe' quello nel blocco piu' tiles_offset(). Il blocco dei riquadri sta all'inizio della VRAM solo se
    // e' il primo fondo creato (la schermata di prova, la storia); in battaglia viene dopo il fondale, e senza
    // l'offset la cornice prendeva i tile del fondale.
    bn::regular_bg_map_cell_info info;
    info.set_tile_index(t.tile + _mappa.tiles_offset());
    info.set_horizontal_flip(t.hflip);
    info.set_vertical_flip(t.vflip);
    info.set_palette_id(_mappa.palette().id());
    (*_mappa.vram())[ty * 32 + tx] = info.cell();
}

void Riquadri::svuota()
{
    for(int ty = 0; ty < 32; ++ty)
    {
        for(int tx = 0; tx < 32; ++tx)
        {
            _cella(tx, ty, { TILE_VUOTO, false, false });
        }
    }
}

void Riquadri::cornice(int x, int y, int colonne, int righe)
{
    BN_ASSERT(x % 8 == 0 && y % 8 == 0, "Riquadri: la cornice va sulla griglia dei tile");
    BN_ASSERT(colonne >= 3 && righe >= 3, "Riquadri: una cornice 9-slice vuole almeno 3x3 tile");

    for(int cy = 0; cy < righe; ++cy)
    {
        for(int cx = 0; cx < colonne; ++cx)
        {
            _cella(x / 8 + cx, y / 8 + cy, tile_cornice(cx, cy, colonne, righe));
        }
    }
}

void Riquadri::cartiglio(int x, int y, int colonne)
{
    BN_ASSERT(x % 8 == 0 && y % 8 == 0, "Riquadri: il cartiglio va sulla griglia dei tile");

    for(int cy = 0; cy < 2; ++cy)
    {
        for(int cx = 0; cx < colonne; ++cx)
        {
            _cella(x / 8 + cx, y / 8 + cy, tile_cartiglio(cx, cy, colonne));
        }
    }
}

void Riquadri::set_visible(bool visibile)
{
    _bg.set_visible(visibile);
}

bn::regular_bg_ptr crea_riquadro_dialogo()
{
    Riquadri r;
    r.cornice(stile::DIALOGO_X, stile::DIALOGO_Y, stile::DIALOGO_COLONNE, stile::DIALOGO_RIGHE);
    return r.bg();
}

}
