#ifndef QUEST_DATA_H
#define QUEST_DATA_H

#include <stdint.h>

#include "bn_string_view.h"

#include "game_state.h"
#include "item_data.h"

namespace gubbio {

// Le cinque quest secondarie della Sezione 31A GDD, una per Quartiere piu' quella civica.
//
// COME SI LEGA ALLO STATO DELLA PARTITA. Ogni quest occupa **lo stesso indice** in
// `GameState::quest_state` (a che punto e') e in `GameState::quest_counter` (quanti pezzi
// raccolti). I due array esistono separati per una ragione precisa, gia' a verbale al Passo 4:
// **un bit non sa contare fino a 3**, e Q-SM01 chiede 3 blocchi di ferro mentre Q-SA01 ne vuole
// 4 di radici.
//
// Gli indici sono PERSISTITI su FRAM: si aggiunge in coda, non si riordina.
enum class QuestId : uint8_t
{
    SM01_FERRO_MONTE_CALVO = 0,   // San Martino  — Mastro Raniero
    SA01_ERBE_BOTTACCIONE  = 1,   // Sant'Andrea  — Monna Agnese
    SP01_ROSA_ARGENTO      = 2,   // San Pietro   — Fra' Bernardo
    SG01_OCCHI_MERCATALI   = 3,   // San Giuliano — Giacomo il Gufo
    CIV01_TRE_SORSI        = 4,   // Piazza Grande — Mastro Tano
    COUNT
};

// I quattro Quartieri, nell'ordine di `GameState::quartieri_reputation`.
enum class Quartiere : uint8_t
{
    SAN_MARTINO = 0,
    SANT_ANDREA = 1,
    SAN_PIETRO = 2,
    SAN_GIULIANO = 3,
    NESSUNO = 255                 // Q-CIV01 e' civica: non alza la reputazione di un Quartiere
};

struct QuestDef
{
    bn::string_view code;         // "Q-SM01": e' l'identificativo con cui il GDD la chiama
    bn::string_view title;
    bn::string_view giver;        // NPC datore
    Quartiere quartiere;
    uint8_t target_count;         // quanti pezzi servono; 0 se non e' una raccolta
    ItemId reward;                // ricompensa consegnata al completamento
    uint8_t reputation_gain;      // punti di reputazione del Quartiere
};

// La ricompensa e' un `ItemId` della Sez. 8E: le ricompense "vere" della Sez. 31A (Corazza
// Rinforzata, Balsamo di Sant'Andrea, Spilla della Rosa, Mappa dei Cunicoli, Patente da Matto)
// sono EQUIPAGGIAMENTI E CHIAVI, che nel gioco non esistono ancora — non c'e' un sistema di
// equipaggiamento, e la Patente da Matto e' una decisione di design ancora aperta (n.8 del
// piano). Finche' non esistono, ogni quest consegna un consumabile plausibile: e' un
// SEGNAPOSTO dichiarato, non la ricompensa definitiva.
inline constexpr QuestDef QUESTS[int(QuestId::COUNT)] = {
    {"Q-SM01", "Il Ferro del Monte Calvo",   "Mastro Raniero",  Quartiere::SAN_MARTINO,  3,
     ItemId::CRESCIA_PASQUA,   1},
    {"Q-SA01", "Le Erbe del Bottaccione",    "Monna Agnese",    Quartiere::SANT_ANDREA,  4,
     ItemId::BISCOTTI_ANICE,   1},
    {"Q-SP01", "La Rosa d'Argento Scomparsa", "Fra' Bernardo",  Quartiere::SAN_PIETRO,   1,
     ItemId::BACCALA_CERAIOLA, 1},
    {"Q-SG01", "Occhi sui Mercatali",        "Giacomo il Gufo", Quartiere::SAN_GIULIANO, 1,
     ItemId::VINO_ROSSO,       1},
    {"Q-CIV01", "I Tre Sorsi del Matto",     "Mastro Tano",     Quartiere::NESSUNO,      3,
     ItemId::VINO_ROSSO,       0}
};

// Le quest devono stare negli array dello stato di partita, che sono serializzati su FRAM: se
// qualcuno ne aggiunge oltre la capacita', la build si ferma qui invece di scrivere fuori.
static_assert(int(QuestId::COUNT) <= MAX_QUESTS,
              "Piu' quest degli slot in GameState::quest_state");

// Il contatore di una raccolta e' un `uint8_t`: un obiettivo oltre 255 non sarebbe registrabile.
static_assert([]
{
    for(const QuestDef& q : QUESTS)
    {
        if(q.target_count > 255 || int(q.reward) >= int(ItemId::COUNT))
        {
            return false;
        }
    }

    return true;
}(), "Una quest ha un obiettivo o una ricompensa fuori dal dominio rappresentabile");

[[nodiscard]] constexpr const QuestDef& quest_def(QuestId id) { return QUESTS[int(id)]; }

// --- Interrogazioni sullo stato della partita ------------------------------------------------

[[nodiscard]] inline QuestState quest_state(const GameState& state, QuestId id)
{
    return state.quest(int(id));
}

[[nodiscard]] inline int quest_progress(const GameState& state, QuestId id)
{
    return state.quest_counter[int(id)];
}

[[nodiscard]] inline bool quest_is_ready_to_deliver(const GameState& state, QuestId id)
{
    return quest_state(state, id) == QuestState::ACTIVE &&
           quest_progress(state, id) >= QUESTS[int(id)].target_count;
}

} // namespace gubbio

#endif // QUEST_DATA_H
