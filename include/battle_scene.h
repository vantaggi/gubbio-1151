#ifndef BATTLE_SCENE_H
#define BATTLE_SCENE_H

#include "bn_vector.h"
#include "bn_random.h"
#include "battle_engine.h"
#include "enemy_data.h"
#include "game_state.h"
#include "hero_data.h"

namespace gubbio {

// Macchina a stati della battaglia (Sezione 20B GDD).
enum class BattleState {
    INTRO_FADE_IN,
    SELECT_COMMAND_GIORGIO,
    SELECT_COMMAND_UBALDO,
    SELECT_COMMAND_ANTONIO,
    EXECUTE_ROUND_ACTIONS,
    CHECK_ROUND_OUTCOME,
    VICTORY,
    DEFEAT,
    ESCAPED
};

// Menu comandi dell'HUD inferiore (Sezione 14B.3 GDD).
enum class MenuCommand { ATTACK, SKILL, ITEM, FLEE, COUNT };

// Indici del party: rispecchiano l'ordine dell'array HEROES di hero_data.h.
// L'ordine di *selezione comandi* e' invece Giorgio -> Ubaldo -> Antonio (Sezione 20B GDD).
constexpr int PARTY_UBALDO  = 0;
constexpr int PARTY_GIORGIO = 1;
constexpr int PARTY_ANTONIO = 2;
constexpr int PARTY_SIZE    = 3;

// Abilita' di ogni eroe, indicizzate come il party (Sezione 2 GDD). Con il comando Abilita'
// selezionato, il tasto L scorre l'elenco del Cero attivo.
constexpr int MAX_SKILLS_PER_HERO = 2;

constexpr int HERO_SKILL_COUNT[PARTY_SIZE] = {2, 2, 1};

constexpr SkillId HERO_SKILLS[PARTY_SIZE][MAX_SKILLS_PER_HERO] = {
    {SkillId::MURO_DELLA_FEDE,      SkillId::GIUDIZIO_DELLA_VERGA},
    {SkillId::FENDENTE_DEL_DRAGO,   SkillId::BASTIONE_AZZURRO},
    {SkillId::FUOCO_DI_SANTANTONIO, SkillId::FUOCO_DI_SANTANTONIO}
};

// Fervore posseduto all'ingresso in battaglia, in percentuale del pool del singolo Cero.
// Sono i valori del mockup HUD della Sezione 14B.3 GDD ("[F: 45%]" Giorgio, "80%" Ubaldo,
// "20%" Antonio), qui promossi da esempio grafico a dato canonico di inizializzazione.
// Indicizzato come il party. In assoluto: Ubaldo 144/180, Giorgio 54/120, Antonio 42/210.
constexpr int HERO_START_FERVOR_PERCENT[PARTY_SIZE] = {80, 45, 20};

// I costi di Boost della Sezione 20A GDD sono assoluti: il Boost MAX costa 100 Fervore a cui
// si somma il costo dell'abilita' firma. Un Cero il cui pool non copre quel totale non potra'
// MAI usare la propria Mossa Suprema (era il caso di San Giorgio, fermo a 70). L'invariante e'
// verificato a compile time perche' la tabella HEROES e' `constexpr` in ROM: un futuro ritocco
// di bilanciamento che lo violasse romperebbe la build invece di passare inosservato.
// Il vincolo va misurato sull'abilita' PIU' COSTOSA dell'eroe: se anche una sola delle sue
// abilita' non fosse potenziabile al massimo, quella Mossa Suprema resterebbe irraggiungibile.
[[nodiscard]] constexpr int most_expensive_skill_cost(int hero_idx)
{
    int cost = 0;

    for(int i = 0; i < HERO_SKILL_COUNT[hero_idx]; ++i)
    {
        const int candidate = SKILLS[int(HERO_SKILLS[hero_idx][i])].fervor_cost;

        if(candidate > cost)
        {
            cost = candidate;
        }
    }

    return cost;
}

[[nodiscard]] constexpr bool supreme_is_reachable(int hero_idx)
{
    return HEROES[hero_idx].max_fervor >=
           BOOST_FERVOR_COST[BOOST_MAX_LEVEL] + most_expensive_skill_cost(hero_idx);
}

static_assert(supreme_is_reachable(PARTY_UBALDO),  "Sant'Ubaldo non puo' raggiungere il Boost MAX");
static_assert(supreme_is_reachable(PARTY_GIORGIO), "San Giorgio non puo' raggiungere il Boost MAX");
static_assert(supreme_is_reachable(PARTY_ANTONIO), "Sant'Antonio non puo' raggiungere il Boost MAX");

// Riferimento stabile a un'unita': gli indici non si invalidano come i puntatori.
struct UnitRef {
    bool is_enemy;
    int slot;
};

struct QueuedAction {
    UnitRef actor;
    UnitRef target;
    SkillId skill;
    int fervor_boost_level;
    int calculated_speed;
};

class BattleSceneManager
{
public:
    BattleSceneManager();

    // party_level alimenta la formula dello scudo di Sant'Ubaldo (Sezione 12B GDD).
    // Questa forma costruisce un party "da nuova partita": HP pieni e Fervore da
    // HERO_START_FERVOR_PERCENT. Resta in vita perche' e' quella su cui sono tarati tutti i
    // collaudi a runtime pubblicati in HANDOVER (Sessioni 03, 04, 08, 10).
    void init_battle(int encounter_id, int party_level);

    // Forma usata dal gioco vero: HP e Fervore vengono DALLA PARTITA IN CORSO e non da valori
    // di partenza. Vedi `HeroRuntimeState` in game_state.h per la motivazione del carry-over.
    void init_battle(int encounter_id, const GameState& state);

    // Riporta nello stato di partita cio' che di questa battaglia sopravvive: solo HP e
    // Fervore. Barriera, BREAK, Ustione e guardia sono condizioni di combattimento e NON
    // escono dalla scena — un Cero non resta "in BREAK" mentre cammina per la piazza.
    void export_party_state(GameState& state) const;

    void update();

    // Ciclo di scena: vedi `BattleScene::run()` in scene_battle.h. Il manager non lo possiede
    // piu' (nota in cima a src/battle_scene.cpp).
    [[nodiscard]] bool is_finished() const;

    [[nodiscard]] BattleState state() const { return _current_state; }
    [[nodiscard]] const bn::vector<BattleUnit, PARTY_SIZE>& party() const { return _party; }
    [[nodiscard]] const bn::vector<BattleUnit, MAX_ENEMIES_PER_ENCOUNTER>& enemies() const { return _enemies; }
    [[nodiscard]] const bn::vector<QueuedAction, PARTY_SIZE + MAX_ENEMIES_PER_ENCOUNTER>& action_queue() const
    {
        return _action_queue;
    }
    [[nodiscard]] MenuCommand selected_command() const { return MenuCommand(_selected_menu_index); }
    [[nodiscard]] int boost_level() const { return _boost_level; }
    [[nodiscard]] UnitRef selected_target() const { return _selected_target; }
    [[nodiscard]] int round_number() const { return _round_number; }

    // Indice del Cero che sta selezionando il comando, -1 fuori dalle fasi di input.
    [[nodiscard]] int active_hero_index() const;

    using OrderQueue = bn::vector<UnitRef, PARTY_SIZE + MAX_ENEMIES_PER_ENCOUNTER>;

    // Ordine previsto del round, per la timeline in alto a destra (Sez. 20A GDD, pilastro 1).
    // Usa la velocita' gia' calcolata per chi ha scelto, quella base per chi deve ancora farlo.
    void predicted_order(OrderQueue& out) const;

    // Avanzamento della dissolvenza d'ingresso, 0-100.
    [[nodiscard]] int intro_progress() const;

private:
    BattleState _current_state;
    bn::vector<BattleUnit, PARTY_SIZE> _party;
    bn::vector<BattleUnit, MAX_ENEMIES_PER_ENCOUNTER> _enemies;
    bn::vector<QueuedAction, PARTY_SIZE + MAX_ENEMIES_PER_ENCOUNTER> _action_queue;
    bn::random _rng;
    int _selected_menu_index;
    int _selected_skill_index;
    int _boost_level;
    UnitRef _selected_target;
    int _round_number;
    int _intro_frames;
    bool _can_flee;

    // --- Costruzione delle unita' ---
    [[nodiscard]] static BattleUnit _make_hero(const HeroStats& stats, int magic_power, int level,
                                               int start_fervor_percent);
    [[nodiscard]] static BattleUnit _make_enemy(const EnemyStats& stats);

    // --- Accesso alle unita' ---
    [[nodiscard]] BattleUnit& _unit_at(UnitRef ref);
    [[nodiscard]] const BattleUnit& _unit_at(UnitRef ref) const;
    [[nodiscard]] bool _find_first_alive(bool enemy_side, UnitRef& out) const;
    void _cycle_target(bool enemy_side, int direction);

    // --- Fase di input ---
    void _handle_command_input(int hero_idx, BattleState next_state);
    void _enter_input_state(int hero_idx);
    void _reset_target(int hero_idx);
    void _cycle_boost(int hero_idx);
    [[nodiscard]] SkillId _selected_skill(int hero_idx) const;
    [[nodiscard]] bool _try_flee() const;

    // --- Fase di esecuzione ---
    void _queue_enemy_actions();
    void _sort_action_queue();
    void _execute_all_queued_actions();
    void _execute_action(const QueuedAction& action);
    void _resolve_offensive_action(BattleUnit& actor, const QueuedAction& action, const SkillData& skill);
    void _resolve_faith_shield(BattleUnit& actor, const QueuedAction& action);
    void _resolve_guard(BattleUnit& actor, int boost_level);
    [[nodiscard]] UnitRef _redirect_if_guarded(UnitRef target_ref) const;
    void _apply_hit(BattleUnit& actor, UnitRef target_ref, const SkillData& skill, int boost_level);
    [[nodiscard]] int _apply_variance(int damage);
    void _end_of_round_ticks();
    void _tick_status(BattleUnit& unit);

    // --- Condizioni di uscita ---
    [[nodiscard]] bool _all_enemies_dead() const;
    [[nodiscard]] bool _all_heroes_dead() const;
};

} // namespace gubbio

#endif // BATTLE_SCENE_H
