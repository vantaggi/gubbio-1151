#include "regia_scena.h"

#include "bn_bg_palette_item.h"
#include "bn_bg_palette_ptr.h"
#include "bn_bg_palettes.h"
#include "bn_color.h"
#include "bn_core.h"
#include "bn_fixed.h"
#include "bn_keypad.h"
#include "bn_log.h"
#include "bn_optional.h"
#include "bn_rect_window.h"
#include "bn_regular_bg_map_item.h"
#include "bn_regular_bg_map_ptr.h"
#include "bn_regular_bg_ptr.h"
#include "bn_regular_bg_tiles_item.h"
#include "bn_regular_bg_tiles_ptr.h"
#include "bn_size.h"
#include "bn_sprite_palettes.h"
#include "bn_window.h"

#include "game_state.h"
#include "regia_logica.h"
#include "tabella.h"
#include "vista_testo.h"

namespace gubbio
{

namespace
{
    using namespace regia;

    constexpr int INCHIOSTRO_CHIARO = 2;
    constexpr int BANDA = 24;                       // le bande nere sopra e sotto: il quadro e' 240x112
    constexpr int TESTO_X = 8;
    constexpr int TESTO_Y = 160 - BANDA + 2;        // nella banda di sotto, due righe da 10 px
    // una mappa 64x32 (512x256) centrata sullo schermo ha l'angolo in (-136, -48): (136, 48 + 24)
    // la porta con l'angolo in alto a sinistra del quadro
    constexpr int MAPPA_X = 512 / 2 - 240 / 2;
    constexpr int MAPPA_Y = 256 / 2 - 160 / 2 + BANDA;

    struct Colori
    {
        bn::color colori[16];
    };

    constexpr Colori colori()
    {
        Colori c;

        for(int i = 0; i < 16; ++i)
        {
            c.colori[i] = bn::color(GUBBIO_VOCE(PALETTE, i));
        }

        return c;
    }

    constexpr Colori COLORI = colori();

    void attendi(int frame)
    {
        for(int f = 0; f < frame; ++f)
        {
            ++g_game_state.frames;
            bn::core::update();
        }
    }

    // I piani dell'inquadratura: fino a quattro BG, il piu' lontano dietro; fuori dal quadro (le
    // bande) la finestra non li mostra.
    class Piani
    {
    public:
        explicit Piani(const bn::bg_palette_ptr& palette) :
            _palette(palette)
        {
        }

        void carica(const Inquadratura& q)
        {
            // stacco netto: via i piani vecchi, prima di caricare i nuovi
            for(int k = 0; k < PIANI_PER_INQUADRATURA; ++k)
            {
                _bg[k].reset();
                _tiles[k].reset();
            }

            bn::core::update();
            _quanti = 0;

            for(int k = 0; k < PIANI_PER_INQUADRATURA && q.piani[k] >= 0; ++k)
            {
                const Piano& p = GUBBIO_VOCE(PIANO, q.piani[k]);
                _tiles[k] = bn::regular_bg_tiles_ptr::create(
                    bn::regular_bg_tiles_item(bn::span<const bn::tile>(p.tile, p.tile_conteggio), bn::bpp_mode::BPP_4));
                _bg[k] = bn::regular_bg_ptr::create(MAPPA_X, MAPPA_Y, bn::regular_bg_map_ptr::create(
                    bn::regular_bg_map_item(*p.mappa, bn::size(64, 32)), *_tiles[k], _palette));
                _bg[k]->set_priority(PIANI_PER_INQUADRATURA - 1 - k);
                bn::window::outside().set_show_bg(*_bg[k], false);
                ++_quanti;
            }
        }

        void scorri(const Lettore& l)
        {
            for(int k = 0; k < _quanti; ++k)
            {
                _bg[k]->set_x(MAPPA_X - l.scorrimento(k, _quanti));
            }
        }

    private:
        bn::bg_palette_ptr _palette;
        bn::optional<bn::regular_bg_tiles_ptr> _tiles[PIANI_PER_INQUADRATURA];
        bn::optional<bn::regular_bg_ptr> _bg[PIANI_PER_INQUADRATURA];
        int _quanti = 0;
    };
}

bool recita_cutscene(int cutscene, const bn::sprite_palette_ptr& palette_testo, bool istantanee, bool automatica)
{
    const Cutscene& c = GUBBIO_VOCE(CUTSCENE_DATI, cutscene);
    BN_LOG("Cutscene ", c.codice);
    bool saltata = false;

    {
        bn::rect_window quadro = bn::rect_window::internal();
        quadro.set_boundaries(-80 + BANDA, -120, 80 - BANDA, 120);
        Piani piani(bn::bg_palette_ptr::create(
            bn::bg_palette_item(bn::span<const bn::color>(COLORI.colori), bn::bpp_mode::BPP_4)));
        VistaTesto narratore(testo::Contesto::NARRATORE, TESTO_X, TESTO_Y, INCHIOSTRO_CHIARO, palette_testo);
        Lettore l;
        l.inizia(cutscene);
        int battuta = -2;
        int frame = 0;
        bool avanti = true;

        while(avanti)
        {
            if(l.stacco())
            {
                piani.carica(l.inquadratura());
            }

            if(l.battuta() != battuta)
            {
                battuta = l.battuta();

                if(battuta >= 0)
                {
                    narratore.mostra(GUBBIO_VOCE(BATTUTA, battuta));
                    narratore.rivela_tutto();
                }
                else
                {
                    narratore.nascondi();
                }
            }

            piani.scorri(l);
            bn::fixed buio = bn::fixed(l.buio()) / FRAME_DISSOLVENZA;
            bn::bg_palettes::set_fade(bn::color(0, 0, 0), buio);
            bn::sprite_palettes::set_fade(bn::color(0, 0, 0), buio);

            // le istantanee: a tre quarti di ogni inquadratura
            if(istantanee && l.inquadratura().frame * 3 / 4 == frame)
            {
                BN_LOG("Istantanea regia_", c.codice, "_", l.indice_inquadratura());
            }

            attendi(1);
            bool start = ! automatica && bn::keypad::start_pressed();
            saltata = saltata || start;
            int prima = l.indice_inquadratura();
            avanti = l.passo(! automatica && bn::keypad::a_pressed(), start);
            frame = l.indice_inquadratura() == prima ? frame + 1 : 0;
        }

        bn::bg_palettes::set_fade(bn::color(0, 0, 0), 0);
        bn::sprite_palettes::set_fade(bn::color(0, 0, 0), 0);
        quadro.set_boundaries(-80, -120, 80, 120);
        bn::window::outside().set_show_all();
    }

    attendi(1);
    segna_vista(g_game_state, cutscene);
    BN_LOG("Cutscene ", c.codice, saltata ? " saltata" : " finita");
    return ! saltata;
}

void prova_regia(const bn::sprite_palette_ptr& palette_testo)
{
    for(int c = 0; c < CUTSCENE; ++c)
    {
        recita_cutscene(c, palette_testo, true, true);
    }

    BN_LOG("Istantanee finite");

    while(true)
    {
        bn::core::update();
    }
}

}
