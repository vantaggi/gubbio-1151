#include "scene_fade.h"

#include "bn_bg_palettes.h"
#include "bn_color.h"
#include "bn_fixed.h"
#include "bn_sprite_palettes.h"

namespace gubbio::scene_fade {

namespace {

// Le transizioni del gioco passano tutte dal nero (Sez. 20B GDD, "la scena emerge dal nero").
// Il colore e' fissato qui e non parametrizzato: un secondo colore di dissolvenza sarebbe un
// effetto diverso, e andrebbe deciso insieme all'arte, non aggiunto per simmetria.
constexpr bn::color FADE_COLOR(0, 0, 0);

} // namespace

void apply(int intensity_percent)
{
    const int clamped = intensity_percent < CLEAR  ? CLEAR
                      : intensity_percent > OPAQUE ? OPAQUE
                                                   : intensity_percent;

    // `set_fade` esige un'intensita' in [0,1]: e' l'unico punto del progetto in cui la scala
    // intera 0-100 diventa un `bn::fixed`.
    const bn::fixed intensity = bn::fixed(clamped) / OPAQUE;

    bn::bg_palettes::set_fade(FADE_COLOR, intensity);
    bn::sprite_palettes::set_fade(FADE_COLOR, intensity);
}

void reset()
{
    apply(CLEAR);
}

} // namespace gubbio::scene_fade
