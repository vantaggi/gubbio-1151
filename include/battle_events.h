#ifndef BATTLE_EVENTS_H
#define BATTLE_EVENTS_H

#include <stdint.h>

#include "battle_engine.h"
#include "enemy_data.h"
#include "game_state.h"

namespace gubbio {

// IL REGISTRO DEGLI EVENTI DI UN ROUND (Passo 20 del piano).
//
// PERCHE' ESISTE. Oggi il round si risolve TUTTO in un frame: il modello viene aggiornato, gli
// SFX suonano, e l'HUD mostra il risultato gia' definitivo. Finche' non c'e' animazione, si
// nota solo che il colpo e' istantaneo. Nel momento in cui l'animazione arriva (Passo 21), la
// stessa struttura diventa un difetto visibile: tutti i rintocchi del round suonerebbero nel
// frame in cui il round e' risolto, fino a un secondo prima dell'animazione che dovrebbero
// accompagnare, e le barre HP scenderebbero prima del colpo che le fa scendere.
//
// La separazione e' questa: il motore CALCOLA e lascia una traccia, l'animatore RIPRODUCE la
// traccia. Ogni evento porta con se' `hp_after`, cioe' lo stato al momento in cui e' accaduto,
// perche' l'HUD debba leggere quello e non lo stato gia' risolto nel modello.

enum class EventKind : uint8_t
{
    HIT = 0,          // danno inferto: `amount` e' il danno, `hp_after` gli HP che restano
    SHIELD_BREAK,     // punti scudo azzerati colpendo il punto debole
    BARRIER_ABSORB,   // il Muro della Fede ha assorbito il colpo
    GUARD_REDIRECT,   // il Bastione ha preso il colpo al posto del bersaglio
    FERVOR_GAIN,      // San Giorgio converte in Fervore i colpi fisici incassati
    BURN_TICK,        // ustione alchemica di fine round
    DEFEAT,           // l'unita' e' caduta
    COUNT
};

// POD, e deve restarlo: il registro vive in un `bn::vector` dentro la scena, e ogni byte in piu'
// e' moltiplicato per MAX_EVENTS. Dieci byte per evento, riempimento compreso.
struct BattleEvent
{
    EventKind kind;
    uint8_t actor_slot;
    uint8_t target_slot;
    bool actor_is_enemy;
    bool target_is_enemy;
    int16_t amount;       // danno, Fervore guadagnato, punti scudo tolti: secondo `kind`
    int16_t hp_after;     // HP del BERSAGLIO subito dopo l'evento
};

// --- IL TETTO, DERIVATO E NON SCELTO A OCCHIO ------------------------------------------------
//
// `bn::ivector::push_back` su contenitore pieno NON tronca: fa scattare un `BN_ASSERT`, cioe' un
// crash. Un `bn::vector<BattleEvent, 64>` scelto a intuito sarebbe quindi una battaglia avanzata
// che muore, e l'autotest a quattro round non la vedrebbe mai — sono proprio i round lunghi, con
// tutti i boost carichi e tutti i nemici in ustione, a produrre piu' eventi.
//
// Il caso peggiore non e' remoto, ed e' questo:
//   * NOVE attori in campo (tre eroi piu' sei nemici);
//   * il Boost livello 2 e' un DOPPIO COLPO reale (BOOST_HIT_COUNT[2] == 2), quindi ogni attore
//     puo' produrre due catene di eventi invece di una;
//   * ogni colpo puo' produrre fino a quattro eventi oltre al danno: rottura dello scudo,
//     barriera assorbita, guardia del Bastione, Fervore di San Giorgio;
//   * piu' una sconfitta per attore;
//   * piu', a fine round, un tick di ustione per ogni unita' in campo e la sconfitta che ne puo'
//     seguire.
//
// I numeri si LEGGONO dalle tabelle del motore invece di essere ricopiati: se un domani il Boost
// livello 2 diventasse un triplo colpo, il tetto salirebbe da se'.

// GAME_PARTY_SIZE e non PARTY_SIZE: quest'ultimo vive in battle_scene.h, che include
// QUESTO header, e includerlo di rimando sarebbe circolare. I due valgono lo stesso e
// una static_assert in battle_scene.h lo impone, cosi' il giro non si puo' rompere in
// silenzio: GAME_PARTY_SIZE e' derivato dalla tabella HEROES, che e' la fonte vera.
inline constexpr int ATTORI_IN_CAMPO = GAME_PARTY_SIZE + MAX_ENEMIES_PER_ENCOUNTER;

[[nodiscard]] constexpr int colpi_massimi_per_attore()
{
    int massimo = 1;

    for(int i = 0; i < BOOST_LEVEL_COUNT; ++i)
    {
        if(BOOST_HIT_COUNT[i] > massimo)
        {
            massimo = BOOST_HIT_COUNT[i];
        }
    }

    return massimo;
}

// Danno, scudo, barriera, guardia, Fervore: cinque eventi al massimo per singolo colpo.
inline constexpr int EVENTI_PER_COLPO = 5;
inline constexpr int EVENTI_PER_ATTORE_CASO_PEGGIORE =
        colpi_massimi_per_attore() * EVENTI_PER_COLPO + 1;   // +1: la sconfitta
inline constexpr int EVENTI_DI_FINE_ROUND = ATTORI_IN_CAMPO * 2;   // ustione + sconfitta

inline constexpr int MAX_EVENTS = 128;

static_assert(MAX_EVENTS >= ATTORI_IN_CAMPO * EVENTI_PER_ATTORE_CASO_PEGGIORE +
                            EVENTI_DI_FINE_ROUND,
              "Il registro degli eventi non regge il round peggiore: con il contenitore pieno "
              "push_back fa scattare un assert, cioe' la battaglia muore invece di perdere "
              "un'animazione");

// DIECI byte, non otto: i cinque campi a un byte occupano cinque posizioni, il
// compilatore ne aggiunge una di riempimento per allineare i due int16 a indirizzo
// pari, e si arriva a dieci. Il tetto e' dodici e non "quanto viene": e' li' per
// fermare chi aggiungesse un campo a cuor leggero, perche' ogni byte qui e'
// moltiplicato per 128 e il registro vive in IWRAM insieme allo stack.
static_assert(sizeof(BattleEvent) <= 12,
              "BattleEvent e' moltiplicato per MAX_EVENTS: ogni byte in piu' costa "
              "128 byte di IWRAM");

// --- DURATE DI RIPRODUZIONE ------------------------------------------------------------------
//
// Quanti frame dura ciascun tipo di evento quando l'animatore lo riproduce. Stanno qui e non
// nell'animatore perche' servono gia' ORA: lo stato PLAY_ROUND_ANIMATIONS le usa come puro
// temporizzatore, prima ancora che esista qualcosa da animare.
//
// Un round con nove attori a queste durate costa 250-350 frame, cioe' 4-6 secondi per ogni
// scontro comune: e' il motivo per cui il fast-forward su A o B esiste fin dalla prima versione
// e non e' un lusso da aggiungere dopo.
[[nodiscard]] constexpr int event_duration_frames(EventKind kind)
{
    switch(kind)
    {
    case EventKind::HIT:            return 24;
    case EventKind::SHIELD_BREAK:   return 30;   // piu' lungo: e' il momento che il giocatore cerca
    case EventKind::BARRIER_ABSORB: return 18;
    case EventKind::GUARD_REDIRECT: return 18;
    case EventKind::FERVOR_GAIN:    return 12;
    case EventKind::BURN_TICK:      return 16;
    case EventKind::DEFEAT:         return 36;
    default:                        return 12;
    }
}

// NESSUN EVENTO PUO' DURARE MENO DEL PASSO DI FAST-FORWARD. `_play_round_animations()` ha un
// `while`, non un `if`: con una durata sotto il passo il cursore avanzerebbe di DUE o piu' eventi
// in un solo frame di gioco, e l'HUD — che confronta il cursore col precedente e riproduce solo
// l'ultimo — salterebbe in silenzio le pose e i flash di quelli in mezzo. Gli HP resterebbero
// corretti, quindi ne' la firma dell'HUD ne' i test se ne accorgerebbero: sparirebbero soltanto
// delle animazioni, che e' il difetto piu' difficile da vedere.
inline constexpr int FAST_FORWARD_STEP = 4;

static_assert([]
{
    for(int k = 0; k < int(EventKind::COUNT); ++k)
    {
        if(event_duration_frames(EventKind(k)) <= FAST_FORWARD_STEP)
        {
            return false;
        }
    }

    return true;
}(), "Un evento dura meno del passo di fast-forward: in riproduzione accelerata verrebbe saltato "
     "senza che nulla lo segnali");

static_assert(event_duration_frames(EventKind::DEFEAT) >= event_duration_frames(EventKind::HIT),
              "Una sconfitta non puo' durare meno di un colpo qualunque: e' l'evento che chiude "
              "la vita di un'unita' e il giocatore deve vederlo");

} // namespace gubbio

#endif // BATTLE_EVENTS_H
