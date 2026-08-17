#ifndef STORY_FLAGS_H
#define STORY_FLAGS_H

#include "bn_assert.h"

namespace gubbio {

// Stato narrativo persistente: 256 bit in 32 byte, serializzati su FRAM.
//
// PERCHE' ESISTE: tre aree del progetto (quest, IA dei boss, combo) hanno bisogno di ricordare
// "e' gia' successo" e tre analisi indipendenti l'avevano dimensionato a 32, 128 e 256 bit,
// ciascuna rivendicandone la proprieta'. Il problema non e' tecnico ma di governance: senza
// intervalli assegnati, due moduli finiscono per scrivere lo stesso bit e il bug e' invisibile.
//
// INTERVALLI RISERVATI - nessun modulo esce dal proprio:
//   0-63    storia principale e avanzamento degli Atti
//   64-127  quest secondarie e dialoghi gia' visti (Sez. 31 GDD)
//   128-159 boss: fasi superate, evocazioni gia' fatte (Sez. 26 GDD)
//   160-191 combo dei Tre Ceri gia' scoperte (Sez. 12C GDD)
//   192-255 riserva
//
// I numeri dei bit sono PERSISTITI: si aggiunge in coda al proprio intervallo, non si riordina.
constexpr int STORY_FLAG_COUNT = 256;
constexpr int STORY_FLAG_BYTES = STORY_FLAG_COUNT / 8;

constexpr int FLAG_RANGE_STORIA_FIRST = 0;
constexpr int FLAG_RANGE_QUEST_FIRST  = 64;
constexpr int FLAG_RANGE_BOSS_FIRST   = 128;
constexpr int FLAG_RANGE_COMBO_FIRST  = 160;
constexpr int FLAG_RANGE_RISERVA_FIRST = 192;

// Bandiere gia' assegnate. Aggiungere qui, dentro il proprio intervallo.
enum class StoryFlag : int
{
    PROLOGO_VISTO        = FLAG_RANGE_STORIA_FIRST + 0,
    ATTO_I_COMPLETATO    = FLAG_RANGE_STORIA_FIRST + 1,
    SIGILLO_SPEZZATO     = FLAG_RANGE_STORIA_FIRST + 2,

    CORRADO_SCONFITTO    = FLAG_RANGE_BOSS_FIRST + 0,
    VALERIO_SCONFITTO    = FLAG_RANGE_BOSS_FIRST + 1,

    COMBO_LANCIA_VISTA   = FLAG_RANGE_COMBO_FIRST + 0,
    COMBO_ALZATA_VISTA   = FLAG_RANGE_COMBO_FIRST + 1
};

class StoryFlags
{
public:
    // Nessun costruttore utente: resta un aggregato, quindi serializzabile con un memcpy
    // e azzerabile con `StoryFlags flags{};`.
    uint8_t bits[STORY_FLAG_BYTES];

    [[nodiscard]] bool is_set(StoryFlag flag) const
    {
        const int i = int(flag);
        BN_ASSERT(i >= 0 && i < STORY_FLAG_COUNT, "Indice di bandiera fuori range: ", i);
        return (bits[i / 8] >> (i % 8)) & 1;
    }

    void set(StoryFlag flag)
    {
        const int i = int(flag);
        BN_ASSERT(i >= 0 && i < STORY_FLAG_COUNT, "Indice di bandiera fuori range: ", i);
        bits[i / 8] = uint8_t(bits[i / 8] | (1 << (i % 8)));
    }

    void clear(StoryFlag flag)
    {
        const int i = int(flag);
        BN_ASSERT(i >= 0 && i < STORY_FLAG_COUNT, "Indice di bandiera fuori range: ", i);
        bits[i / 8] = uint8_t(bits[i / 8] & ~(1 << (i % 8)));
    }

    void clear_all()
    {
        for(int i = 0; i < STORY_FLAG_BYTES; ++i)
        {
            bits[i] = 0;
        }
    }
};

static_assert(sizeof(StoryFlags) == STORY_FLAG_BYTES, "StoryFlags va su FRAM: niente padding");

// Ogni bandiera dichiarata deve stare nella maschera e nel proprio intervallo: se qualcuno
// aggiunge una bandiera di boss con un numero da quest, la build si ferma qui.
static_assert(int(StoryFlag::SIGILLO_SPEZZATO) < FLAG_RANGE_QUEST_FIRST,
              "Bandiera di storia fuori dal proprio intervallo");
static_assert(int(StoryFlag::VALERIO_SCONFITTO) >= FLAG_RANGE_BOSS_FIRST &&
              int(StoryFlag::VALERIO_SCONFITTO) < FLAG_RANGE_COMBO_FIRST,
              "Bandiera di boss fuori dal proprio intervallo");
static_assert(int(StoryFlag::COMBO_ALZATA_VISTA) >= FLAG_RANGE_COMBO_FIRST &&
              int(StoryFlag::COMBO_ALZATA_VISTA) < FLAG_RANGE_RISERVA_FIRST,
              "Bandiera di combo fuori dal proprio intervallo");

} // namespace gubbio

#endif // STORY_FLAGS_H
