#ifndef DIALOGUE_RUNNER_H
#define DIALOGUE_RUNNER_H

#include <stdint.h>

#include "dialogue_box.h"
#include "dialogue_data.h"
#include "game_state.h"
#include "npc_registry.h"

namespace gubbio {

// Esecutore di uno script di dialogo: recita le battute IN SEQUENZA e, alla fine, applica gli
// effetti sulla partita.
//
// PERCHE' NON STA DENTRO `DialogueManager`. Il manager sa una cosa sola — come si rivela un
// testo — e quella cosa la fa bene. Chi decide *quale* testo, *in che ordine* e *cosa succede
// dopo* e' un'altra responsabilita': tenerle separate significa che il motore del testo resta
// verificabile da solo, e che questo esecutore puo' crescere (scelte, salti condizionati) senza
// toccare la macchina da scrivere.
//
// LO STATO E' DUE INTERI. Uno script e' un intervallo di battute in `DIALOGUE_LINES` (vedi
// dialogue_data.h): per eseguirlo basta sapere quale script e a che punto si e'. Niente stack di
// chiamate, niente contenitori: due `uint16_t` in tutto, che e' anche cio' che rende banale
// salvarne lo stato se un giorno servira' riprendere un dialogo interrotto.

class DialogueRunner
{
public:
    // Avvia uno script. `dialogue` viene aperto sulla prima battuta.
    void start(ScriptId script, DialogueManager& dialogue)
    {
        _script = script;
        _line = 0;
        _running = true;
        _show_current(dialogue);
    }

    // Da chiamare a ogni frame in cui il runner e' attivo, DOPO `dialogue.update()`.
    // Quando il giocatore chiude una battuta, apre la successiva; esaurite le battute, applica
    // gli effetti e si ferma.
    void update(DialogueManager& dialogue, GameState& state)
    {
        if(! _running || dialogue.is_active())
        {
            return;
        }

        ++_line;

        if(_line < dialogue_script(_script).line_count)
        {
            _show_current(dialogue);
            return;
        }

        _apply_effects(state);
        _running = false;
    }

    [[nodiscard]] bool is_running() const { return _running; }
    [[nodiscard]] ScriptId script() const { return _script; }

    // Battuta corrente, per la diagnostica.
    [[nodiscard]] int line_index() const { return _line; }

private:
    ScriptId _script = ScriptId::COUNT;
    uint16_t _line = 0;
    bool _running = false;

    void _show_current(DialogueManager& dialogue)
    {
        const DialogueScript& script = dialogue_script(_script);
        const DialogueLine& linea = DIALOGUE_LINES[script.first_line + _line];

        dialogue.show_message(linea.speaker, linea.row[0], linea.row[1], linea.row[2]);
    }

    // EFFETTI DI FINE SCRIPT. Oggi sono le sole bandiere di "gia' visto": segnare che un dialogo
    // e' avvenuto e' il minimo che serva perche' un NPC non ripeta all'infinito la stessa
    // battuta d'ingaggio. Gli altri passi previsti dal piano — CHOICE, JUMP_IF_FLAG, START_QUEST,
    // ADVANCE_QUEST, GIVE_ITEM — entrano qui, e la forma e' gia' quella giusta: uno `switch`
    // sullo script concluso, non una macchina di istruzioni da interpretare.
    //
    // La scelta di NON aggiungerli adesso e' deliberata: `START_QUEST` senza un modo di
    // consegnare l'oggetto e' meta' meccanica, e meta' meccanica in un salvataggio persistente
    // e' peggio di nessuna meccanica.
    void _apply_effects(GameState& state)
    {
        switch(_script)
        {
            case ScriptId::TANO_INGAGGIO:
                state.story_flags.set(StoryFlag::COMBO_ALZATA_VISTA);   // segnaposto: vedi sopra
                break;

            default:
                break;
        }
    }
};

// Interazione: quale NPC ha davanti il giocatore.
//
// Il raggio e' generoso — una cella e mezzo — perche' con una hitbox ai piedi e un NPC alto 16 px
// il centro dei due non coincide mai, e pretendere la sovrapposizione esatta significherebbe un
// giocatore che preme A e non succede nulla senza capire perche'.
inline constexpr int NPC_INTERACTION_RANGE_PX = 12;

[[nodiscard]] inline int npc_at(MapId map, int player_x, int player_y)
{
    for(int i = 0; i < int(NpcId::COUNT); ++i)
    {
        const NpcDef& npc = NPCS[i];

        if(npc.map != map)
        {
            continue;
        }

        const int npc_x = npc.tile_x * maps::TILE_SIZE_PX + maps::TILE_SIZE_PX / 2;
        const int npc_y = npc.tile_y * maps::TILE_SIZE_PX + maps::TILE_SIZE_PX / 2;
        const int dx = player_x > npc_x ? player_x - npc_x : npc_x - player_x;
        const int dy = player_y > npc_y ? player_y - npc_y : npc_y - player_y;

        if(dx <= NPC_INTERACTION_RANGE_PX && dy <= NPC_INTERACTION_RANGE_PX)
        {
            return i;
        }
    }

    return -1;
}

} // namespace gubbio

#endif // DIALOGUE_RUNNER_H
