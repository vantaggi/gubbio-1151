#include "bn_bg_palettes.h"
#include "bn_color.h"
#include "bn_core.h"
#include "bn_keypad.h"

#include "esplorazione.h"
#include "game_state.h"
#include "schermate.h"
#include "vista_testo.h"

// All'avvio: con L premuto la schermata dei testi (F1), con SELECT la camminata automatica del
// mondo (F2), altrimenti l'esplorazione da Piazza Grande. Croce per muoversi, B per correre.
int main()
{
    bn::core::init();
    bn::core::update();

    gubbio::g_game_state.frames = 0;
    bn::sprite_palette_ptr palette = gubbio::crea_palette_testo();

    if(bn::keypad::l_held())
    {
        gubbio::schermata_testi(palette);
    }

    bn::bg_palettes::set_transparent_color(bn::color(0, 0, 0));
    gubbio::Esplorazione esplorazione(palette);

    if(bn::keypad::select_held())
    {
        gubbio::camminata_automatica(esplorazione, palette);
    }

    esplorazione.entra(gubbio::mondo::AreaId::PIAZZA_GRANDE, 0);

    while(true)
    {
        ++gubbio::g_game_state.frames;

        int dx = bn::keypad::left_held() ? -1 : (bn::keypad::right_held() ? 1 : 0);
        int dy = bn::keypad::up_held() ? -1 : (bn::keypad::down_held() ? 1 : 0);
        esplorazione.muovi(dx, dy, bn::keypad::b_held() ? 2 : 1);
        esplorazione.aggiorna();

        bn::core::update();
    }
}
