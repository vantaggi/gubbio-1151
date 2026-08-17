#include "scene_battle.h"

#include "bn_log.h"

#include "game_clock.h"
#include "scene_fade.h"

namespace gubbio {

namespace {

[[nodiscard]] const char* state_name(BattleState state)
{
    switch(state)
    {
        case BattleState::INTRO_FADE_IN:          return "INTRO";
        case BattleState::SELECT_COMMAND_GIORGIO: return "CMD GIORGIO";
        case BattleState::SELECT_COMMAND_UBALDO:  return "CMD UBALDO";
        case BattleState::SELECT_COMMAND_ANTONIO: return "CMD ANTONIO";
        case BattleState::EXECUTE_ROUND_ACTIONS:  return "EXECUTE";
        case BattleState::CHECK_ROUND_OUTCOME:    return "CHECK";
        case BattleState::VICTORY:                return "VITTORIA";
        case BattleState::DEFEAT:                 return "SCONFITTA";
        case BattleState::ESCAPED:                return "FUGA";
        default:                                  return "?";
    }
}

// Durata della dissolvenza d'uscita, in frame. Piu' corta dei 32 dell'ingresso: entrare in una
// scena e' un evento drammatico (il rintocco del Campanone la accompagna), uscirne no.
constexpr int OUTRO_DURATION_FRAMES = 16;

// Traccia di collaudo. Non e' decorazione: e' l'oracolo con cui le Sessioni 03-10 hanno
// verificato la FSM su emulatore leggendo stdout di mgba-sdl, senza guardare lo schermo.
void log_round_snapshot(const BattleSceneManager& battle)
{
    for(const BattleUnit& hero : battle.party())
    {
        BN_LOG("  ", hero.name, " HP ", hero.current_hp, " FER ", hero.current_fervor,
               " BARR ", hero.barrier_hp);
    }

    for(const BattleUnit& enemy : battle.enemies())
    {
        BN_LOG("  ", enemy.name, " HP ", enemy.current_hp, " SC ", enemy.current_shield,
               " BRK ", enemy.break_turns, " UST ", enemy.burn_stacks);
    }
}

} // namespace

BattleScene::BattleScene(GameState& state, const SceneRequest& request) :
    _state(state)
{
    _battle.init_battle(request.parameter, state);

    BN_LOG("=== BATTAGLIA: incontro ", request.parameter, " ===");

    for(const BattleUnit& hero : _battle.party())
    {
        BN_LOG("EROE ", hero.name, " HP ", hero.current_hp, "/", hero.max_hp,
               " FERVORE ", hero.current_fervor, "/", hero.max_fervor,
               " (", hero.fervor_percent(), "%)");
    }

    for(const BattleUnit& enemy : _battle.enemies())
    {
        BN_LOG("NEMICO ", enemy.name, " HP ", enemy.current_hp, " SCUDO ", enemy.current_shield);
    }

    // CONTRATTO D'INGRESSO delle scene: lo schermo e' nero PRIMA del primo `core_update()`.
    // La scena uscente ha azzerato il fade (vedi in fondo a `run()`), quindi senza questa riga
    // il primo fotogramma della battaglia comparirebbe a piena luminosita' per poi rituffarsi
    // nel nero dell'INTRO_FADE_IN: uno sfarfallio di un frame, dei piu' difficili da diagnosticare.
    scene_fade::apply(scene_fade::OPAQUE);
}

SceneRequest BattleScene::run()
{
    BattleState last_state = _battle.state();

    while(! _battle.is_finished())
    {
        _battle.update();
        _hud.update(_battle);

        if(_battle.state() != last_state)
        {
            BN_LOG("STATO -> ", state_name(_battle.state()), " (round ", _battle.round_number(), ")");
            last_state = _battle.state();

            if(_battle.state() == BattleState::CHECK_ROUND_OUTCOME)
            {
                log_round_snapshot(_battle);
            }
        }

        core_update();
    }

    // Cio' che sopravvive alla battaglia torna nello stato di partita PRIMA della dissolvenza:
    // se il trasferimento fallisse, si vedrebbe nella traccia insieme all'esito, non dopo.
    _battle.export_party_state(_state);

    BN_LOG("ESITO ", state_name(_battle.state()));

    for(int i = 0; i < GAME_PARTY_SIZE; ++i)
    {
        BN_LOG("  CARRY-OVER ", HEROES[i].name, " HP ", _state.party[i].current_hp,
               " FER ", _state.party[i].current_fervor);
    }

    for(int frame = 0; frame <= OUTRO_DURATION_FRAMES; ++frame)
    {
        scene_fade::apply((frame * scene_fade::OPAQUE) / OUTRO_DURATION_FRAMES);
        core_update();
    }

    // Obbligatorio: il fade e' uno stato globale dell'hardware, non una proprieta' della scena
    // che lo ha impostato. Lo schermo resta comunque nero fino al primo `core_update()` della
    // scena entrante, che per contratto riapplica il proprio fade prima di quel momento.
    scene_fade::reset();

    if(_battle.state() == BattleState::DEFEAT)
    {
        return SceneRequest{SceneId::GAME_OVER, 0};
    }

    // Vittoria e fuga riportano entrambe alla mappa da cui si e' entrati. Nessuna cura di fine
    // battaglia: "la vittoria cura qualcosa?" e' una decisione di design ancora aperta, e
    // curare di nascosto renderebbe il carry-over appena introdotto invisibile.
    return SceneRequest::exploration(_state.map());
}

} // namespace gubbio
