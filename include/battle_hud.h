#ifndef BATTLE_HUD_H
#define BATTLE_HUD_H

#include "bn_vector.h"
#include "bn_optional.h"
#include "bn_sprite_ptr.h"
#include "bn_regular_bg_ptr.h"
#include "bn_sprite_text_generator.h"

#include "battle_scene.h"

namespace gubbio {

// Rendering della schermata di combattimento (layout della Sezione 14B.3 GDD).
//
//   +-------------------------------------------------------------+
//   | fondale d'assedio: Monte Ingino, nebbia                     |
//   |  [NEMICI x:40-90]                     [PARTY x:150-200]     |
//   +-------------------------------------------------------------+
//   | HUD 48px:  [MENU COMANDI 80px] | [STATO PARTY 160px]        |
//   +-------------------------------------------------------------+
//
// Il pannello HUD e' dipinto nelle righe 112-159 del fondale invece che su un layer separato:
// la scena e' statica e questo risparmia un BG hardware per il futuro parallasse.
class BattleHud
{
public:
    BattleHud();

    // Costruisce sprite e testi dallo stato corrente. Chiamare a ogni frame: internamente
    // ridisegna solo quando lo stato osservabile cambia.
    void update(const BattleSceneManager& battle);

private:
    static constexpr int MAX_TEXT_SPRITES = 64;

    bn::regular_bg_ptr _background;
    bn::sprite_text_generator _text_generator;

    bn::vector<bn::sprite_ptr, PARTY_SIZE> _hero_sprites;
    bn::vector<bn::sprite_ptr, MAX_ENEMIES_PER_ENCOUNTER> _enemy_sprites;
    bn::vector<bn::sprite_ptr, PARTY_SIZE * 2> _bars;      // HP e Fervore per ogni Cero
    bn::optional<bn::sprite_ptr> _cursor;
    bn::vector<bn::sprite_ptr, PARTY_SIZE + MAX_ENEMIES_PER_ENCOUNTER> _timeline;
    bn::vector<bn::sprite_ptr, MAX_TEXT_SPRITES> _texts;

    int _last_signature;
    int _last_intro_progress;
    bool _units_built;

    void _build_units(const BattleSceneManager& battle);
    void _refresh(const BattleSceneManager& battle);
    void _refresh_timeline(const BattleSceneManager& battle);
    void _apply_intro_fade(const BattleSceneManager& battle);
    [[nodiscard]] static int _signature(const BattleSceneManager& battle);
};

} // namespace gubbio

#endif // BATTLE_HUD_H
