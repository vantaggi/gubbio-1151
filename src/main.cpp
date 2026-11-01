#include "bn_core.h"
#include "bn_sprite_ptr.h"
#include "bn_sprite_text_generator.h"
#include "bn_vector.h"

#include "common_variable_8x8_sprite_font.h"

#include "game_state.h"

// Schermata di prova della fase F0: dimostra solo che la ROM si avvia e disegna.
int main()
{
    bn::core::init();

    bn::sprite_text_generator text_generator(common::variable_8x8_sprite_font);
    text_generator.set_center_alignment();

    bn::vector<bn::sprite_ptr, 16> text_sprites;
    text_generator.generate(0, 0, "Gubbio 1151 - F0", text_sprites);

    gubbio::g_game_state.frames = 0;

    while(true)
    {
        ++gubbio::g_game_state.frames;
        bn::core::update();
    }
}
