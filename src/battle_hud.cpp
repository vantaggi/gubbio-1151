#include "battle_hud.h"

#include "bn_string.h"
#include "bn_display.h"

#include "bn_regular_bg_items_battle_bg.h"
#include "bn_sprite_items_ubaldo.h"
#include "bn_sprite_items_giorgio.h"
#include "bn_sprite_items_antonio.h"
#include "bn_sprite_items_enemy_fante.h"
#include "bn_sprite_items_enemy_balestriere.h"
#include "bn_sprite_items_enemy_corrado.h"
#include "bn_sprite_items_hud_bar.h"
#include "bn_sprite_items_target_cursor.h"
#include "bn_sprite_items_timeline_icons.h"
#include "scene_fade.h"

#include "font_gubbio.h"

namespace gubbio {

namespace {

// Coordinate della Sezione 14B.3 GDD, convertite dal sistema a origine in alto a sinistra
// (0-239 / 0-159) a quello centrato di Butano (-120..119 / -80..79).
[[nodiscard]] constexpr int sx(int screen_x) { return screen_x - 120; }
[[nodiscard]] constexpr int sy(int screen_y) { return screen_y - 80; }

// Party a destra (x 150-200), schieramento nemico a sinistra (x 40-90).
constexpr int HERO_X[PARTY_SIZE]  = {196, 162, 218};   // Ubaldo, Giorgio, Antonio
constexpr int HERO_Y[PARTY_SIZE]  = { 86,  94,  94};   // i piedi poggiano sulla fascia di terreno
// Formazione 3x2 (Sez. 12 GDD): prima riga in avanguardia, seconda in retrovia.
constexpr int ENEMY_X[MAX_ENEMIES_PER_ENCOUNTER] = {60, 94, 44, 78, 112, 28};
constexpr int ENEMY_Y[MAX_ENEMIES_PER_ENCOUNTER] = {96, 96, 78, 78,  78, 96};

// Timeline degli ordini in alto a destra (Sez. 20A GDD, pilastro 1).
constexpr int TIMELINE_X = 228;
constexpr int TIMELINE_Y = 12;
constexpr int TIMELINE_STEP = 15;
constexpr int ICON_UBALDO = 0, ICON_GIORGIO = 1, ICON_ANTONIO = 2;
constexpr int ICON_FANTE = 3, ICON_BALESTRIERE = 4, ICON_CORRADO = 5;

constexpr int BAR_FRAMES = 17;
constexpr int BAR_FERVOR_OFFSET = 17;   // secondo set di fotogrammi, in oro

// Riquadro del menu comandi: 80px a sinistra dell'HUD (Sezione 14B.3 GDD).
constexpr int MENU_X = 8;
constexpr int MENU_Y = 118;
constexpr int MENU_LINE = 10;

// Riquadro di stato del party: i restanti 160px.
constexpr int STATUS_X = 84;
constexpr int STATUS_Y = 118;
constexpr int STATUS_LINE = 12;
constexpr int NUMBERS_X = 133;   // solo HP correnti: la frazione la dice la barra
constexpr int BAR_HP_X = 157;
constexpr int BAR_FER_X = 193;

// Nomi abbreviati: la fascia di stato e' larga 157px e deve ospitare nome, HP e due barre.
constexpr const char* HERO_SHORT_NAME[PARTY_SIZE] = {"Ubaldo", "Giorgio", "Antonio"};

[[nodiscard]] const char* command_label(MenuCommand command)
{
    switch(command)
    {
        case MenuCommand::ATTACK: return "Attacca";
        case MenuCommand::SKILL:  return "Abilità";
        case MenuCommand::ITEM:   return "Oggetti";
        case MenuCommand::FLEE:   return "Fuga";
        default:                  return "";
    }
}

[[nodiscard]] bn::sprite_ptr make_enemy_sprite(bn::string_view name, int x, int y)
{
    // I nemici sono distinti per nome: la tabella ENEMIES vive in ROM e non porta con se'
    // un riferimento grafico, che appartiene a questo livello di presentazione.
    if(name == bn::string_view("Corrado di Spoleto"))
    {
        return bn::sprite_items::enemy_corrado.create_sprite(x, y);
    }

    if(name == bn::string_view("Balestriere Pesante"))
    {
        return bn::sprite_items::enemy_balestriere.create_sprite(x, y);
    }

    return bn::sprite_items::enemy_fante.create_sprite(x, y);
}

[[nodiscard]] int timeline_icon_for(const BattleUnit& unit, int slot)
{
    if(! unit.is_enemy)
    {
        return slot == PARTY_UBALDO ? ICON_UBALDO : (slot == PARTY_GIORGIO ? ICON_GIORGIO : ICON_ANTONIO);
    }

    if(unit.name == bn::string_view("Corrado di Spoleto"))
    {
        return ICON_CORRADO;
    }

    return unit.name == bn::string_view("Balestriere Pesante") ? ICON_BALESTRIERE : ICON_FANTE;
}

[[nodiscard]] int bar_frame(int current, int maximum)
{
    if(maximum <= 0)
    {
        return 0;
    }

    const int frame = (current * (BAR_FRAMES - 1)) / maximum;
    return frame < 0 ? 0 : (frame > BAR_FRAMES - 1 ? BAR_FRAMES - 1 : frame);
}

} // namespace

BattleHud::BattleHud() :
    _background(bn::regular_bg_items::battle_bg.create_bg(0, 0)),
    _text_generator(FONT_GUBBIO),
    _last_signature(0),
    _last_intro_progress(-1),
    _units_built(false)
{
    _text_generator.set_left_alignment();
    _text_generator.set_bg_priority(0);
}

void BattleHud::update(const BattleSceneManager& battle)
{
    if(! _units_built)
    {
        _build_units(battle);
        _units_built = true;
        _last_signature = _signature(battle) - 1;
    }

    _apply_intro_fade(battle);

    if(const int signature = _signature(battle); signature != _last_signature)
    {
        _last_signature = signature;
        _refresh(battle);
    }
}

// La scena emerge dal nero: e' lo stato INTRO_FADE_IN della Sez. 20B GDD, che finora
// transitava in un solo frame senza che si vedesse nulla.
void BattleHud::_apply_intro_fade(const BattleSceneManager& battle)
{
    const int progress = battle.intro_progress();

    if(progress == _last_intro_progress)
    {
        return;
    }

    _last_intro_progress = progress;

    // La dissolvenza passa dalle primitive di `scene_fade` (Passo 5): la FSM resta padrona del
    // tempo — l'avanzamento e' ancora `intro_progress()` — ma il tocco alle palette globali
    // avviene in un punto solo, lo stesso che le scene azzerano uscendo.
    scene_fade::apply(scene_fade::OPAQUE - progress);
}

void BattleHud::_refresh_timeline(const BattleSceneManager& battle)
{
    BattleSceneManager::OrderQueue order;
    battle.predicted_order(order);

    while(_timeline.size() > order.size())
    {
        _timeline.pop_back();
    }

    for(int i = 0; i < order.size(); ++i)
    {
        const UnitRef ref = order[i];
        const BattleUnit& unit = ref.is_enemy ? battle.enemies()[ref.slot] : battle.party()[ref.slot];
        const int frame = timeline_icon_for(unit, ref.slot);
        const int y = sy(TIMELINE_Y + i * TIMELINE_STEP);

        if(i < _timeline.size())
        {
            _timeline[i].set_item(bn::sprite_items::timeline_icons, frame);
            _timeline[i].set_position(sx(TIMELINE_X), y);
        }
        else
        {
            _timeline.push_back(bn::sprite_items::timeline_icons.create_sprite(
                sx(TIMELINE_X), y, frame));
        }
    }
}

void BattleHud::_build_units(const BattleSceneManager& battle)
{
    _hero_sprites.push_back(bn::sprite_items::ubaldo.create_sprite(
        sx(HERO_X[PARTY_UBALDO]), sy(HERO_Y[PARTY_UBALDO])));
    _hero_sprites.push_back(bn::sprite_items::giorgio.create_sprite(
        sx(HERO_X[PARTY_GIORGIO]), sy(HERO_Y[PARTY_GIORGIO])));
    _hero_sprites.push_back(bn::sprite_items::antonio.create_sprite(
        sx(HERO_X[PARTY_ANTONIO]), sy(HERO_Y[PARTY_ANTONIO])));

    for(int slot = 0, count = battle.enemies().size(); slot < count; ++slot)
    {
        _enemy_sprites.push_back(make_enemy_sprite(battle.enemies()[slot].name,
                                                   sx(ENEMY_X[slot]), sy(ENEMY_Y[slot])));
    }

    // Due barre per Cero: HP e Fervore, allineate alle righe di stato.
    for(int hero = 0; hero < PARTY_SIZE; ++hero)
    {
        const int y = sy(STATUS_Y + hero * STATUS_LINE + 3);
        _bars.push_back(bn::sprite_items::hud_bar.create_sprite(sx(BAR_HP_X + 16), y));
        _bars.push_back(bn::sprite_items::hud_bar.create_sprite(sx(BAR_FER_X + 16), y));
    }

    _cursor = bn::sprite_items::target_cursor.create_sprite(0, 0);
}

void BattleHud::_refresh(const BattleSceneManager& battle)
{
    _texts.clear();

    // --- Sprite delle unita': i caduti spariscono dal campo ---
    for(int hero = 0; hero < PARTY_SIZE; ++hero)
    {
        _hero_sprites[hero].set_visible(battle.party()[hero].is_alive());
    }

    for(int slot = 0, count = _enemy_sprites.size(); slot < count; ++slot)
    {
        _enemy_sprites[slot].set_visible(battle.enemies()[slot].is_alive());
    }

    // --- Menu comandi (riquadro sinistro, 80px) ---
    const int active_hero = battle.active_hero_index();

    for(int i = 0; i < int(MenuCommand::COUNT); ++i)
    {
        const bool selected = active_hero >= 0 && i == int(battle.selected_command());
        bn::string<20> line;
        bn::ostringstream stream(line);
        stream << (selected ? "> " : "  ") << command_label(MenuCommand(i));

        if(selected && battle.boost_level() > 0)
        {
            stream << (battle.boost_level() == BOOST_MAX_LEVEL ? " MAX" : " x");

            if(battle.boost_level() != BOOST_MAX_LEVEL)
            {
                stream << battle.boost_level();
            }
        }

        _text_generator.generate(sx(MENU_X), sy(MENU_Y + i * MENU_LINE), line, _texts);
    }

    // --- Stato del party (riquadro destro, 160px) ---
    for(int hero = 0; hero < PARTY_SIZE; ++hero)
    {
        const BattleUnit& unit = battle.party()[hero];
        const int y = STATUS_Y + hero * STATUS_LINE;

        bn::string<20> line;
        bn::ostringstream stream(line);
        stream << (hero == active_hero ? ">" : " ") << HERO_SHORT_NAME[hero];
        _text_generator.generate(sx(STATUS_X), sy(y), line, _texts);

        bn::string<12> numbers;
        bn::ostringstream numbers_stream(numbers);
        numbers_stream << unit.current_hp;
        _text_generator.generate(sx(NUMBERS_X), sy(y), numbers, _texts);

        _bars[hero * 2].set_item(bn::sprite_items::hud_bar, bar_frame(unit.current_hp, unit.max_hp));
            _bars[hero * 2 + 1].set_item(bn::sprite_items::hud_bar,
            BAR_FERVOR_OFFSET + bar_frame(unit.current_fervor, unit.max_fervor));
    }

    _refresh_timeline(battle);

    // --- Cursore sul bersaglio selezionato ---
    const UnitRef target = battle.selected_target();
    const bool show_cursor = active_hero >= 0 && target.is_enemy &&
                             target.slot < _enemy_sprites.size() &&
                             battle.enemies()[target.slot].is_alive();

    if(_cursor)
    {
        _cursor->set_visible(show_cursor);

        if(show_cursor)
        {
            _cursor->set_position(sx(ENEMY_X[target.slot]), sy(ENEMY_Y[target.slot] - 28));
        }
    }
}

int BattleHud::_signature(const BattleSceneManager& battle)
{
    // `is_enemy` DEVE entrare nella firma: passando da Muro della Fede (alleato, slot 0) a
    // Giudizio della Verga (nemico, slot 0) cambia il lato del bersaglio ma non il suo indice.
    // Senza questo termine la firma non cambiava e il cursore restava nascosto sul primo
    // scontro del gioco, pur essendo il bersaglio interno corretto.
    int signature = int(battle.state()) + battle.round_number() * 31 +
                    int(battle.selected_command()) * 7 + battle.boost_level() * 3 +
                    battle.selected_target().slot * 11 + battle.active_hero_index() * 101 +
                    (battle.selected_target().is_enemy ? 1009 : 0);

    for(const BattleUnit& hero : battle.party())
    {
        signature += hero.current_hp + hero.current_fervor * 5 + hero.barrier_hp;
    }

    for(const BattleUnit& enemy : battle.enemies())
    {
        signature += enemy.current_hp + enemy.current_shield * 13 + enemy.break_turns * 17;
    }

    return signature;
}

} // namespace gubbio
