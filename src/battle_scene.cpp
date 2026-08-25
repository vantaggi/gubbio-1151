#include "battle_scene.h"

#include "bn_core.h"
#include "bn_keypad.h"
#include "bn_assert.h"
#include "bn_log.h"
#include "campanone_audio.h"

namespace gubbio {

namespace {

// Mappa stato FSM -> indice del party. L'ordine di selezione e' Giorgio -> Ubaldo -> Antonio
// (Sezione 20B GDD) mentre l'array HEROES e' ordinato Ubaldo, Giorgio, Antonio.
[[nodiscard]] int hero_index_for_state(BattleState state)
{
    switch(state)
    {
        case BattleState::SELECT_COMMAND_GIORGIO: return PARTY_GIORGIO;
        case BattleState::SELECT_COMMAND_UBALDO:  return PARTY_UBALDO;
        case BattleState::SELECT_COMMAND_ANTONIO: return PARTY_ANTONIO;
        default:                                  return -1;
    }
}

// Durata della dissolvenza d'ingresso, in frame (~mezzo secondo a 60 FPS).
constexpr int INTRO_DURATION_FRAMES = 32;

// Ritorna INTRO_FADE_IN quando non esiste un eroe precedente a cui tornare.
[[nodiscard]] BattleState previous_input_state(BattleState state)
{
    switch(state)
    {
        case BattleState::SELECT_COMMAND_ANTONIO: return BattleState::SELECT_COMMAND_UBALDO;
        case BattleState::SELECT_COMMAND_UBALDO:  return BattleState::SELECT_COMMAND_GIORGIO;
        default:                                  return BattleState::INTRO_FADE_IN;
    }
}

}

BattleSceneManager::BattleSceneManager() :
    _current_state(BattleState::INTRO_FADE_IN),
    _selected_menu_index(0),
    _selected_skill_index(0),
    _boost_level(0),
    _selected_target(UnitRef{true, 0}),
    _round_number(0),
    _intro_frames(0),
    _can_flee(false)
{
}

// --------------------------------------------------------------------------------------------
// Costruzione delle unita'
// --------------------------------------------------------------------------------------------

BattleUnit BattleSceneManager::_make_hero(const HeroStats& stats, int magic_power, int level,
                                          int start_fervor_percent)
{
    return BattleUnit{
        .name = stats.name,
        .max_hp = stats.max_hp,
        .current_hp = stats.max_hp,
        .max_fervor = stats.max_fervor,
        // Il Cero entra in campo con la devozione gia' accumulata dal mockup HUD Sez. 14B.3 GDD,
        // non con la barra piena: le Mosse Supreme vanno guadagnate durante lo scontro.
        .current_fervor = (stats.max_fervor * start_fervor_percent) / 100,
        .attack = stats.physical_atk,
        .defense = stats.physical_def,
        .magic_power = magic_power,
        .magic_resist = stats.magic_resist,
        .speed = stats.speed,
        .level = level,
        .barrier_hp = 0,
        .max_shield = 0,
        .current_shield = 0,
        .break_turns = 0,
        .weakness = ElementType::NONE,
        .resistance = ElementType::NONE,
        .current_status = StatusEffect::NONE,
        .status_turns = 0,
        .burn_stacks = 0,
        .burn_damage_per_stack = 0,
        .guard_turns = 0,
        .is_enemy = false
    };
}

BattleUnit BattleSceneManager::_make_enemy(const EnemyStats& stats)
{
    return BattleUnit{
        .name = stats.name,
        .max_hp = stats.max_hp,
        .current_hp = stats.max_hp,
        .max_fervor = 0,
        .current_fervor = 0,
        .attack = stats.attack,
        .defense = stats.defense,
        .magic_power = stats.magic_power,
        .magic_resist = stats.magic_resist,
        .speed = stats.speed,
        .level = 1,
        .barrier_hp = 0,
        .max_shield = stats.shield_points,
        .current_shield = stats.shield_points,
        .break_turns = 0,
        .weakness = stats.weakness,
        .resistance = stats.resistance,
        .current_status = StatusEffect::NONE,
        .status_turns = 0,
        .burn_stacks = 0,
        .burn_damage_per_stack = 0,
        .guard_turns = 0,
        .is_enemy = true
    };
}

void BattleSceneManager::init_battle(int encounter_id, int party_level)
{
    BN_ASSERT(encounter_id >= 0 && encounter_id < int(EncounterId::COUNT), "Encounter id fuori range");
    BN_ASSERT(party_level >= 1, "Livello del party non valido");

    _party.clear();
    _enemies.clear();
    _action_queue.clear();

    // Il Potere Mistico di ogni Cero e' la sua statistica dominante (Sezione 5 GDD):
    // Fede per Ubaldo e Giorgio, Fiamma per Antonio.
    _party.push_back(_make_hero(HEROES[PARTY_UBALDO],  HEROES[PARTY_UBALDO].faith_power,  party_level,
                                HERO_START_FERVOR_PERCENT[PARTY_UBALDO]));
    _party.push_back(_make_hero(HEROES[PARTY_GIORGIO], HEROES[PARTY_GIORGIO].faith_power, party_level,
                                HERO_START_FERVOR_PERCENT[PARTY_GIORGIO]));
    _party.push_back(_make_hero(HEROES[PARTY_ANTONIO], HEROES[PARTY_ANTONIO].flame_power, party_level,
                                HERO_START_FERVOR_PERCENT[PARTY_ANTONIO]));

    const EncounterData& encounter = ENCOUNTERS[encounter_id];
    _can_flee = encounter.can_flee;

    for(int i = 0; i < encounter.enemy_count; ++i)
    {
        _enemies.push_back(_make_enemy(ENEMIES[encounter.enemy_ids[i]]));
    }

    _round_number = 1;
    _selected_menu_index = 0;
    _selected_skill_index = 0;
    _boost_level = 0;
    _selected_target = UnitRef{true, 0};
    _intro_frames = 0;
    _current_state = BattleState::INTRO_FADE_IN;
}

void BattleSceneManager::init_battle(int encounter_id, const GameState& state)
{
    // Il livello e' quello del capofila. `HeroRuntimeState` ne porta uno per Cero, ma la
    // formula dello scudo (Sez. 12B GDD) ne vuole uno solo, e "livello condiviso o per eroe"
    // e' una decisione ancora aperta (n.12 del piano): finche' non e' presa, si legge il primo
    // e non si inventa una media.
    init_battle(encounter_id, state.party[PARTY_UBALDO].level);

    // Carry-over: HP e Fervore vengono dalla partita in corso, sovrascrivendo i valori di
    // nuova partita appena scritti dall'overload precedente. Il `min` non e' difensivo per
    // abitudine — protegge dal caso reale in cui un salvataggio di una versione futura porti
    // pool piu' alti di quelli di questa build.
    for(int i = 0; i < PARTY_SIZE; ++i)
    {
        BattleUnit& unit = _party[i];
        const HeroRuntimeState& saved = state.party[i];

        unit.current_hp = saved.current_hp < unit.max_hp ? int(saved.current_hp) : unit.max_hp;
        unit.current_fervor = saved.current_fervor < unit.max_fervor ? int(saved.current_fervor)
                                                                    : unit.max_fervor;
    }
}

void BattleSceneManager::export_party_state(GameState& state) const
{
    for(int i = 0; i < PARTY_SIZE; ++i)
    {
        const BattleUnit& unit = _party[i];

        state.party[i].current_hp = uint16_t(unit.current_hp);
        state.party[i].current_fervor = uint16_t(unit.current_fervor);
    }
}

// --------------------------------------------------------------------------------------------
// Ciclo di scena
// --------------------------------------------------------------------------------------------

void BattleSceneManager::update()
{
    // NOTA sul warning -Wswitch-default (attivo nel set di Butano): qui NON si aggiunge un
    // `default:`. Elencando tutti gli stati senza default, e' -Wswitch a fare la guardia: se
    // domani si aggiunge uno stato alla FSM e lo si dimentica qui, il compilatore lo segnala.
    // Con un `default: break;` quel controllo sparirebbe e la dimenticanza passerebbe muta.
    // Si accetta consapevolmente un warning per non perdere una protezione piu' utile.
    switch(_current_state)
    {
        case BattleState::INTRO_FADE_IN:
            if(_intro_frames == 0)
            {
                CampanoneAudio::play_siege_double();
            }

            // La dissolvenza occupa frame reali: il rintocco del Campanone deve avere il tempo
            // di risuonare prima che compaia il menu comandi.
            if(++_intro_frames >= INTRO_DURATION_FRAMES)
            {
                _current_state = BattleState::SELECT_COMMAND_GIORGIO;
                _enter_input_state(PARTY_GIORGIO);
            }
            break;

        case BattleState::SELECT_COMMAND_GIORGIO:
            _handle_command_input(PARTY_GIORGIO, BattleState::SELECT_COMMAND_UBALDO);
            break;

        case BattleState::SELECT_COMMAND_UBALDO:
            _handle_command_input(PARTY_UBALDO, BattleState::SELECT_COMMAND_ANTONIO);
            break;

        case BattleState::SELECT_COMMAND_ANTONIO:
            _handle_command_input(PARTY_ANTONIO, BattleState::EXECUTE_ROUND_ACTIONS);
            break;

        case BattleState::EXECUTE_ROUND_ACTIONS:
            _queue_enemy_actions();
            _sort_action_queue();
            _execute_all_queued_actions();
            _end_of_round_ticks();
            _event_cursor = 0;
            _event_frames = _events.empty() ? 0 :
                    event_duration_frames(_events[0].kind);
            _current_state = BattleState::PLAY_ROUND_ANIMATIONS;
            break;

        case BattleState::PLAY_ROUND_ANIMATIONS:
            _play_round_animations();
            break;

        case BattleState::CHECK_ROUND_OUTCOME:
            if(_all_enemies_dead())
            {
                _current_state = BattleState::VICTORY;
            }
            else if(_all_heroes_dead())
            {
                _current_state = BattleState::DEFEAT;
            }
            else
            {
                _action_queue.clear();
                ++_round_number;
                _current_state = BattleState::SELECT_COMMAND_GIORGIO;
                _enter_input_state(PARTY_GIORGIO);
            }
            break;

        case BattleState::VICTORY:
        case BattleState::DEFEAT:
        case BattleState::ESCAPED:
            break;
    }
}

// NOTA (Sessione 11): `BattleSceneManager::run()` e' stato RIMOSSO. Esisteva dalla Sessione 02
// come "ciclo di scena standard imposto da AGENTS.md", non e' mai stato chiamato da nessuno, e
// aveva un difetto strutturale: faceva girare il modello senza mai aggiornare l'HUD, quindi la
// battaglia si sarebbe risolta a schermo fermo. Il ciclo di scena appartiene ora a
// `BattleScene::run()` (scene_battle.h), che possiede modello e HUD e li fa avanzare insieme.
// Da qui in avanti nessun file fuori da `game_clock.h` chiama `bn::core::update()`, e il gate
// `tools/check_zero_heap.sh` lo verifica a ogni build.

int BattleSceneManager::intro_progress() const
{
    if(_current_state != BattleState::INTRO_FADE_IN)
    {
        return 100;
    }

    return (_intro_frames * 100) / INTRO_DURATION_FRAMES;
}

void BattleSceneManager::predicted_order(OrderQueue& out) const
{
    out.clear();

    bn::vector<int, PARTY_SIZE + MAX_ENEMIES_PER_ENCOUNTER> speeds;

    const auto push = [&](UnitRef ref, int speed)
    {
        // Insertion sort decrescente e stabile, come _sort_action_queue.
        int pos = out.size();

        while(pos > 0 && speeds[pos - 1] < speed)
        {
            --pos;
        }

        out.insert(out.begin() + pos, ref);
        speeds.insert(speeds.begin() + pos, speed);
    };

    for(int slot = 0; slot < _party.size(); ++slot)
    {
        if(! _party[slot].is_alive())
        {
            continue;
        }

        int speed = _party[slot].speed;

        for(const QueuedAction& action : _action_queue)
        {
            if(! action.actor.is_enemy && action.actor.slot == slot)
            {
                speed = action.calculated_speed;
                break;
            }
        }

        push(UnitRef{false, slot}, speed);
    }

    for(int slot = 0; slot < _enemies.size(); ++slot)
    {
        // Un nemico in BREAK salta il turno: non compare nella timeline.
        if(_enemies[slot].is_alive() && ! _enemies[slot].is_broken())
        {
            push(UnitRef{true, slot}, _enemies[slot].speed);
        }
    }
}

int BattleSceneManager::active_hero_index() const
{
    return hero_index_for_state(_current_state);
}

bool BattleSceneManager::is_finished() const
{
    return _current_state == BattleState::VICTORY || _current_state == BattleState::DEFEAT ||
           _current_state == BattleState::ESCAPED;
}

// --------------------------------------------------------------------------------------------
// Accesso alle unita'
// --------------------------------------------------------------------------------------------

BattleUnit& BattleSceneManager::_unit_at(UnitRef ref)
{
    return ref.is_enemy ? _enemies[ref.slot] : _party[ref.slot];
}

const BattleUnit& BattleSceneManager::_unit_at(UnitRef ref) const
{
    return ref.is_enemy ? _enemies[ref.slot] : _party[ref.slot];
}

bool BattleSceneManager::_find_first_alive(bool enemy_side, UnitRef& out) const
{
    const int count = enemy_side ? _enemies.size() : _party.size();

    for(int slot = 0; slot < count; ++slot)
    {
        if(_unit_at(UnitRef{enemy_side, slot}).is_alive())
        {
            out = UnitRef{enemy_side, slot};
            return true;
        }
    }

    return false;
}

void BattleSceneManager::_cycle_target(bool enemy_side, int direction)
{
    const int count = enemy_side ? _enemies.size() : _party.size();

    if(count <= 0)
    {
        return;
    }

    int slot = _selected_target.is_enemy == enemy_side ? _selected_target.slot : 0;

    for(int step = 0; step < count; ++step)
    {
        slot = (slot + direction + count) % count;

        if(_unit_at(UnitRef{enemy_side, slot}).is_alive())
        {
            _selected_target = UnitRef{enemy_side, slot};
            return;
        }
    }
}

// --------------------------------------------------------------------------------------------
// Fase di input: selezione comandi dei tre eroi
// --------------------------------------------------------------------------------------------

void BattleSceneManager::_enter_input_state(int hero_idx)
{
    _selected_menu_index = int(MenuCommand::ATTACK);
    _selected_skill_index = 0;
    _boost_level = 0;
    _reset_target(hero_idx);
}

void BattleSceneManager::_reset_target(int hero_idx)
{
    if(SKILLS[int(_selected_skill(hero_idx))].target == SkillTarget::ENEMY)
    {
        UnitRef found;

        if(_find_first_alive(true, found))
        {
            _selected_target = found;
        }
    }
    else
    {
        _selected_target = UnitRef{false, hero_idx};
    }
}

SkillId BattleSceneManager::_selected_skill(int hero_idx) const
{
    if(MenuCommand(_selected_menu_index) != MenuCommand::SKILL)
    {
        return SkillId::BASIC_ATTACK;
    }

    const int index = _selected_skill_index % HERO_SKILL_COUNT[hero_idx];
    return HERO_SKILLS[hero_idx][index];
}

void BattleSceneManager::_cycle_boost(int hero_idx)
{
    const SkillData& skill = SKILLS[int(_selected_skill(hero_idx))];
    const BattleUnit& hero = _party[hero_idx];

    // Scorre al primo livello di Boost effettivamente sostenibile dalla barra Fervore.
    for(int step = 1; step <= BOOST_LEVEL_COUNT; ++step)
    {
        const int candidate = (_boost_level + step) % BOOST_LEVEL_COUNT;

        if(hero.can_afford(BattleSystem::total_fervor_cost(skill, candidate)))
        {
            _boost_level = candidate;
            return;
        }
    }
}

bool BattleSceneManager::_try_flee() const
{
    if(! _can_flee)
    {
        return false;
    }

    int hero_speed = 0;
    int hero_count = 0;
    int enemy_speed = 0;
    int enemy_count = 0;

    for(const BattleUnit& hero : _party)
    {
        if(hero.is_alive())
        {
            hero_speed += hero.speed;
            ++hero_count;
        }
    }

    for(const BattleUnit& enemy : _enemies)
    {
        if(enemy.is_alive())
        {
            enemy_speed += enemy.speed;
            ++enemy_count;
        }
    }

    if(hero_count == 0 || enemy_count == 0)
    {
        return false;
    }

    // Confronto delle velocita' medie senza divisioni intere.
    return (hero_speed * enemy_count) >= (enemy_speed * hero_count);
}

void BattleSceneManager::_handle_command_input(int hero_idx, BattleState next_state)
{
    // Un Cero caduto non seleziona comandi: la FSM passa direttamente al successivo.
    if(! _party[hero_idx].is_alive())
    {
        _current_state = next_state;

        if(const int next_hero = hero_index_for_state(next_state); next_hero >= 0)
        {
            _enter_input_state(next_hero);
        }

        return;
    }

    // Tasto B: torna al precedente eroe ancora vivo annullando la sua azione accodata.
    if(bn::keypad::b_pressed())
    {
        BattleState previous = _current_state;
        int previous_hero = -1;

        while(true)
        {
            previous = previous_input_state(previous);

            if(previous == BattleState::INTRO_FADE_IN)
            {
                break;
            }

            if(const int candidate = hero_index_for_state(previous);
               candidate >= 0 && _party[candidate].is_alive())
            {
                previous_hero = candidate;
                break;
            }
        }

        if(previous_hero >= 0)
        {
            if(! _action_queue.empty() && ! _action_queue.back().actor.is_enemy &&
               _action_queue.back().actor.slot == previous_hero)
            {
                _action_queue.pop_back();
            }

            _current_state = previous;
            _enter_input_state(previous_hero);
        }

        return;
    }

    // D-Pad Su/Giu': navigazione del menu comandi.
    if(bn::keypad::up_pressed() || bn::keypad::down_pressed())
    {
        const int delta = bn::keypad::up_pressed() ? -1 : 1;
        const int count = int(MenuCommand::COUNT);
        _selected_menu_index = (_selected_menu_index + delta + count) % count;

        // Cambiando comando cambiano costo in Fervore e lato del bersaglio.
        _boost_level = 0;
        _reset_target(hero_idx);
    }

    // D-Pad Sinistra/Destra: scorrimento dei bersagli vivi.
    if(bn::keypad::left_pressed() || bn::keypad::right_pressed())
    {
        const bool enemy_side = SKILLS[int(_selected_skill(hero_idx))].target == SkillTarget::ENEMY;
        _cycle_target(enemy_side, bn::keypad::left_pressed() ? -1 : 1);
    }

    // Tasto L: scorre le abilita' del Cero attivo (solo col comando Abilita' selezionato).
    if(bn::keypad::l_pressed() && MenuCommand(_selected_menu_index) == MenuCommand::SKILL)
    {
        _selected_skill_index = (_selected_skill_index + 1) % HERO_SKILL_COUNT[hero_idx];
        _boost_level = 0;      // il costo cambia con l'abilita'
        _reset_target(hero_idx);
    }

    // Tasto R: incrementa il Fervor Boost (x1 -> x2 -> MAX -> nessuno).
    if(bn::keypad::r_pressed())
    {
        _cycle_boost(hero_idx);
    }

    if(! bn::keypad::a_pressed())
    {
        return;
    }

    const MenuCommand command = MenuCommand(_selected_menu_index);

    // TODO: l'inventario non esiste ancora, il comando Oggetti e' inerte.
    if(command == MenuCommand::ITEM)
    {
        return;
    }

    if(command == MenuCommand::FLEE)
    {
        if(_try_flee())
        {
            _current_state = BattleState::ESCAPED;
        }
        else
        {
            // Fuga fallita: l'eroe perde il turno e il round prosegue.
            _current_state = next_state;

            if(const int next_hero = hero_index_for_state(next_state); next_hero >= 0)
            {
                _enter_input_state(next_hero);
            }
        }

        return;
    }

    const SkillId skill_id = _selected_skill(hero_idx);
    const SkillData& skill = SKILLS[int(skill_id)];
    const BattleUnit& hero = _party[hero_idx];

    // Il Fervore viene verificato ora e speso in fase di esecuzione: ogni eroe ha la
    // propria barra e una sola azione per round, quindi le due fasi non possono divergere.
    if(! hero.can_afford(BattleSystem::total_fervor_cost(skill, _boost_level)))
    {
        // Il rifiuto va TRACCIATO, non solo eseguito. Con l'autotest a tasti fissi uno stato
        // che non avanza fa scivolare tutto lo script sull'eroe successivo: al round 4
        // Sant'Antonio non puo' pagare il Fuoco, i tasti destinati a Giorgio scorrono il suo
        // menu fino a `Fuga` e la battaglia finisce in fuga senza che nulla lo spieghi.
        // Il difetto e' dell'oracolo, non del gioco (Passo 0a del piano: l'autotest va portato
        // a confronto di SEQUENZE DI EVENTI); finche' resta a tasti fissi, almeno lo dichiara.
        BN_LOG("RIFIUTATO ", hero.name, ": Fervore ", hero.current_fervor, " < costo ",
               BattleSystem::total_fervor_cost(skill, _boost_level));
        return;
    }

    _action_queue.push_back(QueuedAction{
        .actor = UnitRef{false, hero_idx},
        .target = _selected_target,
        .skill = skill_id,
        .fervor_boost_level = _boost_level,
        .calculated_speed = hero.speed + skill.speed_priority
    });

    _current_state = next_state;

    if(const int next_hero = hero_index_for_state(next_state); next_hero >= 0)
    {
        _enter_input_state(next_hero);
    }
}

// --------------------------------------------------------------------------------------------
// Fase di esecuzione: timeline, Shield Break e consumo Fervore
// --------------------------------------------------------------------------------------------

void BattleSceneManager::_queue_enemy_actions()
{
    for(int slot = 0, count = _enemies.size(); slot < count; ++slot)
    {
        const BattleUnit& enemy = _enemies[slot];

        if(! enemy.is_alive() || enemy.is_broken())
        {
            continue;
        }

        // Mob comune: colpisce il bersaglio con meno Difesa (Sezione 13D GDD).
        int best = -1;

        for(int hero_idx = 0, party_size = _party.size(); hero_idx < party_size; ++hero_idx)
        {
            if(! _party[hero_idx].is_alive())
            {
                continue;
            }

            if(best < 0 || _party[hero_idx].effective_defense() < _party[best].effective_defense())
            {
                best = hero_idx;
            }
        }

        if(best < 0)
        {
            // Nessun eroe vivo: l'uscita e' dall'intera funzione e non dalla sola iterazione,
            // perche' se non c'e' un bersaglio per questo nemico non ce n'e' per nessun altro.
            return;
        }

        const SkillData& skill = SKILLS[int(SkillId::ENEMY_STRIKE)];

        _action_queue.push_back(QueuedAction{
            .actor = UnitRef{true, slot},
            .target = UnitRef{false, best},
            .skill = SkillId::ENEMY_STRIKE,
            .fervor_boost_level = 0,
            .calculated_speed = enemy.speed + skill.speed_priority
        });
    }
}

void BattleSceneManager::_sort_action_queue()
{
    // Insertion sort stabile e decrescente per Velocita': nessuna allocazione, coda <= 9 elementi.
    for(int i = 1, count = _action_queue.size(); i < count; ++i)
    {
        const QueuedAction key = _action_queue[i];
        int j = i - 1;

        while(j >= 0 && _action_queue[j].calculated_speed < key.calculated_speed)
        {
            _action_queue[j + 1] = _action_queue[j];
            --j;
        }

        _action_queue[j + 1] = key;
    }
}

void BattleSceneManager::_execute_all_queued_actions()
{
    for(const QueuedAction& action : _action_queue)
    {
        if(_all_enemies_dead() || _all_heroes_dead())
        {
            break;
        }

        _execute_action(action);
    }
}

void BattleSceneManager::_execute_action(const QueuedAction& action)
{
    BattleUnit& actor = _unit_at(action.actor);

    // Un'unita' in stato BREAK salta il turno (Sezione 20A GDD).
    if(! actor.is_alive() || actor.is_broken())
    {
        return;
    }

    const SkillData& skill = SKILLS[int(action.skill)];

    if(! actor.spend_fervor(BattleSystem::total_fervor_cost(skill, action.fervor_boost_level)))
    {
        return;
    }

    if(skill.effect == SkillEffect::FAITH_SHIELD)
    {
        _resolve_faith_shield(actor, action);
    }
    else if(skill.effect == SkillEffect::GUARD_ALLIES)
    {
        _resolve_guard(actor, action.fervor_boost_level);
    }
    else
    {
        _resolve_offensive_action(actor, action, skill);
    }
}

void BattleSceneManager::_resolve_guard(BattleUnit& actor, int boost_level)
{
    actor.start_guard(boost_level);
}

// Bastione Azzurro (Sezione 2 GDD): San Giorgio intercetta i colpi diretti a Sant'Ubaldo e
// Sant'Antonio. Senza questa contromisura l'IA della Sezione 13D, che punta sempre il bersaglio
// con meno Difesa, eliminava Sant'Antonio entro il terzo round di ogni scontro.
UnitRef BattleSceneManager::_redirect_if_guarded(UnitRef target_ref) const
{
    if(target_ref.is_enemy || target_ref.slot == PARTY_GIORGIO)
    {
        return target_ref;
    }

    const BattleUnit& giorgio = _party[PARTY_GIORGIO];

    if(giorgio.is_alive() && giorgio.is_guarding())
    {
        return UnitRef{false, PARTY_GIORGIO};
    }

    return target_ref;
}

void BattleSceneManager::_resolve_offensive_action(BattleUnit& actor, const QueuedAction& action,
                                                   const SkillData& skill)
{
    const int boost = action.fervor_boost_level;

    // SkillTarget::ENEMY significa "schieramento avversario" rispetto a chi agisce.
    const bool target_enemy_side = skill.target == SkillTarget::ENEMY ? ! actor.is_enemy : actor.is_enemy;

    // Boost MAX: l'Abilita' Suprema del Cero investe l'intero schieramento (Sezione 20A GDD).
    if(boost == BOOST_MAX_LEVEL)
    {
        const int count = target_enemy_side ? _enemies.size() : _party.size();

        for(int slot = 0; slot < count; ++slot)
        {
            const UnitRef target{target_enemy_side, slot};

            if(_unit_at(target).is_alive())
            {
                _apply_hit(actor, action.actor, target, skill, boost);
            }
        }

        return;
    }

    UnitRef target = action.target;

    if(target.is_enemy != target_enemy_side || ! _unit_at(target).is_alive())
    {
        if(! _find_first_alive(target_enemy_side, target))
        {
            return;
        }
    }

    for(int hit = 0, hits = BOOST_HIT_COUNT[boost]; hit < hits; ++hit)
    {
        if(! _unit_at(target).is_alive())
        {
            break;
        }

        _apply_hit(actor, action.actor, target, skill, boost);
    }
}

void BattleSceneManager::_resolve_faith_shield(BattleUnit& actor, const QueuedAction& action)
{
    UnitRef target = action.target;

    if(target.is_enemy || ! _unit_at(target).is_alive())
    {
        if(! _find_first_alive(false, target))
        {
            return;
        }
    }

    _unit_at(target).barrier_hp += BattleSystem::calculate_faith_shield(actor, action.fervor_boost_level);

    // Applicare scudi genera Fervore per Sant'Ubaldo (Sezione 12A GDD).
    actor.add_fervor(FERVOR_GAIN_UBALDO_SUPPORT);
}

void BattleSceneManager::_emit(const BattleEvent& event)
{
    if(_events.full())
    {
        // SCARTA, non asserisce. Il registro e' dimensionato sul round peggiore
        // (battle_events.h), quindi arrivarci significa che il caso peggiore e' cambiato sotto:
        // il log lo dice, e la battaglia prosegue senza quell'animazione invece di morire.
        if(! _event_log_overflow)
        {
            _event_log_overflow = true;
            BN_LOG("EVENTI: registro pieno a ", int(MAX_EVENTS),
                   ", il round peggiore e' cresciuto oltre il tetto derivato");
        }

        return;
    }

    _events.push_back(event);
}

void BattleSceneManager::_play_round_animations()
{
    // FAST-FORWARD tenendo A o B. Un round con nove attori costa 250-350 frame, cioe' 4-6
    // secondi per ogni scontro comune: senza, si guarda la stessa sequenza per tutta la partita.
    const int passo = (bn::keypad::a_held() || bn::keypad::b_held()) ? FAST_FORWARD_STEP : 1;

    _event_frames -= passo;

    while(_event_frames <= 0 && _event_cursor < _events.size())
    {
        const BattleEvent& evento = _events[_event_cursor];

        // IL RINTOCCO SUONA QUI, non dove il colpo viene calcolato. Prima stava in _apply_hit:
        // tutti gli SFX del round partivano nel frame in cui il round veniva risolto, fino a un
        // secondo prima dell'animazione che dovrebbero accompagnare. E' il difetto che questo
        // stato esiste per chiudere.
        if(evento.kind == EventKind::SHIELD_BREAK)
        {
            CampanoneAudio::play_strike();
        }

        ++_event_cursor;

        _event_frames += (_event_cursor < _events.size())
                ? event_duration_frames(_events[_event_cursor].kind) : 0;
    }

    if(_event_cursor >= _events.size())
    {
        _current_state = BattleState::CHECK_ROUND_OUTCOME;
    }
}

// `actor_ref` NON e' ricavabile da `actor`: BattleUnit sa se e' nemico ma non in quale
// slot sta, e risalirci per indirizzo sarebbe fragile. Va passato da chi il colpo lo
// ordina. Prima non c'era e i quattro _emit scrivevano uno ZERO LETTERALE come
// actor_slot: l'HUD lo usa per scegliere quale sprite animare, quindi animava sempre
// il primo Cero qualunque fosse l'attore. Trovato dalla verifica avversariale, non
// dalla build: e' un difetto che compila benissimo.
void BattleSceneManager::_apply_hit(BattleUnit& actor, UnitRef actor_ref, UnitRef target_ref,
                                    const SkillData& skill, int boost_level)
{
    target_ref = _redirect_if_guarded(target_ref);

    BattleUnit& target = _unit_at(target_ref);

    if(! target.is_alive())
    {
        return;
    }

    // Shield Break: colpire il punto debole sottrae Punti Scudo PRIMA del calcolo del danno,
    // cosi' la difesa dimezzata si applica gia' al colpo che innesca il BREAK.
    if(skill.element == target.weakness && target.current_shield > 0)
    {
        if(target.damage_shield(BOOST_SHIELD_PER_HIT[boost_level]))
        {
            _emit({EventKind::SHIELD_BREAK, uint8_t(actor_ref.slot), uint8_t(target_ref.slot),
                   actor.is_enemy, target.is_enemy,
                   int16_t(BOOST_SHIELD_PER_HIT[boost_level]), int16_t(target.current_hp)});
        }
    }

    const int danno = _apply_variance(BattleSystem::calculate_damage(actor, target, skill,
                                                                    boost_level));
    const bool era_vivo = target.is_alive();
    target.take_damage(danno);

    _emit({EventKind::HIT, uint8_t(actor_ref.slot), uint8_t(target_ref.slot), actor.is_enemy,
           target.is_enemy, int16_t(danno), int16_t(target.current_hp)});

    if(era_vivo && ! target.is_alive())
    {
        _emit({EventKind::DEFEAT, uint8_t(actor_ref.slot), uint8_t(target_ref.slot), actor.is_enemy,
               target.is_enemy, int16_t(0), int16_t(0)});
    }

    // San Giorgio converte i colpi fisici incassati in Fervore (Sezione 12A GDD).
    if(! target.is_enemy && target_ref.slot == PARTY_GIORGIO && skill.element == ElementType::PHYSICAL &&
       target.is_alive())
    {
        target.add_fervor(FERVOR_GAIN_GIORGIO_HIT);
        _emit({EventKind::FERVOR_GAIN, uint8_t(actor_ref.slot), uint8_t(target_ref.slot), actor.is_enemy,
               target.is_enemy, int16_t(FERVOR_GAIN_GIORGIO_HIT), int16_t(target.current_hp)});
    }

    if(skill.effect == SkillEffect::ALCHEMICAL_BURN && target.is_alive())
    {
        target.apply_burn(actor.magic_power);
    }
}

int BattleSceneManager::_apply_variance(int damage)
{
    // RNG(0.9 - 1.1) della Sezione 12B GDD, in percentuale intera.
    const int percent = DAMAGE_VARIANCE_MIN_PERCENT + _rng.get_int(DAMAGE_VARIANCE_SPREAD_STEPS);
    const int result = (damage * percent) / 100;
    return result < 1 ? 1 : result;
}

void BattleSceneManager::_end_of_round_ticks()
{
    for(int slot = 0; slot < _enemies.size(); ++slot)
    {
        _tick_status(_enemies[slot], UnitRef{true, slot});
    }

    for(int slot = 0; slot < _party.size(); ++slot)
    {
        _tick_status(_party[slot], UnitRef{false, slot});
    }
}

void BattleSceneManager::_tick_status(BattleUnit& unit, UnitRef ref)
{
    // Ustione Alchemica: danno assoluto per carica a fine turno, fissato all'applicazione.
    if(unit.burn_stacks > 0 && unit.is_alive())
    {
        const int danno_ustione = unit.burn_damage_per_stack * unit.burn_stacks;
        unit.take_damage(danno_ustione);

        // L'ustione e' l'unico danno che il giocatore subisce senza vedere un colpo:
        // se non lascia un evento, la barra scende e nulla sullo schermo dice perche'.
        // Prima EventKind::BURN_TICK era codice morto — dichiarato, con una durata di
        // riproduzione, e mai emesso da nessuno.
        _emit({EventKind::BURN_TICK, uint8_t(ref.slot), uint8_t(ref.slot),
               unit.is_enemy, unit.is_enemy, int16_t(danno_ustione),
               int16_t(unit.current_hp)});

        if(! unit.is_alive())
        {
            _emit({EventKind::DEFEAT, uint8_t(ref.slot), uint8_t(ref.slot),
                   unit.is_enemy, unit.is_enemy, int16_t(0), int16_t(0)});
        }

        if(unit.is_enemy && _party[PARTY_ANTONIO].is_alive())
        {
            _party[PARTY_ANTONIO].add_fervor(FERVOR_GAIN_ANTONIO_BURN);
        }

        --unit.status_turns;

        if(unit.status_turns <= 0)
        {
            unit.burn_stacks = 0;
            unit.status_turns = 0;
        }
    }

    // Il Bastione Azzurro copre il solo round in cui viene alzato.
    if(unit.guard_turns > 0)
    {
        --unit.guard_turns;
    }

    // Uscita dallo stato BREAK: la barra dei Punti Scudo si ricompone.
    if(unit.break_turns > 0)
    {
        --unit.break_turns;

        if(unit.break_turns == 0)
        {
            unit.current_shield = unit.max_shield;
        }
    }

    unit.refresh_status();
}

// --------------------------------------------------------------------------------------------
// Condizioni di uscita
// --------------------------------------------------------------------------------------------

bool BattleSceneManager::_all_enemies_dead() const
{
    for(const BattleUnit& enemy : _enemies)
    {
        if(enemy.is_alive())
        {
            return false;
        }
    }

    return true;
}

bool BattleSceneManager::_all_heroes_dead() const
{
    for(const BattleUnit& hero : _party)
    {
        if(hero.is_alive())
        {
            return false;
        }
    }

    return true;
}

} // namespace gubbio
