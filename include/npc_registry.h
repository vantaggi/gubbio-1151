#ifndef NPC_REGISTRY_H
#define NPC_REGISTRY_H

#include <stdint.h>

#include "bn_string_view.h"

#include "dialogue_data.h"
#include "map_id.h"
#include "largo_bargello_collision.h"
#include "piazza_grande_collision.h"
#include "story_flags.h"

namespace gubbio {

// Chi sta dove, e cosa dice (Sezione 31B GDD).
//
// REGOLA PRIMA-CORRISPONDENZA-VINCE. Un NPC dice cose diverse a seconda di quanto e' avanzata la
// storia: il Podesta' Guido ha una battuta per l'Atto I e una per l'Atto III. Le condizioni sono
// elencate in ordine e si prende **la prima che vale**, non la piu' specifica. E' la regola piu'
// semplice che si possa scrivere, ed e' anche l'unica che non richiede di confrontare fra loro
// condizioni eterogenee: chi scrive il copione mette le condizioni piu' strette in cima.
//
// Se nessuna vale, l'NPC non parla — non e' un errore: significa che in quel momento della
// storia quel personaggio non ha nulla da dire.

// Nessun requisito di atto: la battuta vale sempre.
inline constexpr uint8_t ACT_ANY = 0;

struct DialogueEntry
{
    uint8_t required_act;      // atto minimo perche' la battuta valga; ACT_ANY = nessun vincolo
    ScriptId script;
};

struct NpcDef
{
    bn::string_view name;
    MapId map;
    uint8_t tile_x;            // posizione in TILE: e' l'unita' in cui le mappe sono autorate
    uint8_t tile_y;
    uint16_t first_entry;      // intervallo su NPC_DIALOGUE_ENTRIES
    uint8_t entry_count;
};

// Le battute condizionate, in fila. Tabelle piatte e intervalli, mai contenitori annidati: il
// codice della Sez. 31C usa `bn::vector<DialogueNode,4>` dentro un array `constexpr`, e
// `bn::vector` non e' un tipo letterale in Butano — non compilerebbe.
inline constexpr DialogueEntry NPC_DIALOGUE_ENTRIES[] = {
    // Podesta' Guido: l'Atto III viene PRIMA perche' e' la condizione piu' stretta.
    {3, ScriptId::PODESTA_ATTO_III},
    {ACT_ANY, ScriptId::PODESTA_ATTO_I},

    // Mastro Tano, custode della Fontana dei Matti.
    {ACT_ANY, ScriptId::TANO_INGAGGIO},

    // Berto il Tagliapietre, NPC di lore.
    {ACT_ANY, ScriptId::BERTO_LORE},
};

enum class NpcId : uint8_t
{
    PODESTA_GUIDO = 0,
    MASTRO_TANO = 1,
    BERTO_TAGLIAPIETRE = 2,
    COUNT
};

// Solo Piazza Grande e' autorata (Sessione 11b): gli NPC dei quattro Quartieri entreranno qui
// quando le loro mappe esisteranno. Le posizioni sono scelte sul calpestabile della piazza — un
// NPC dentro un muro sarebbe irraggiungibile, e la `static_assert` in fondo lo impedisce.
inline constexpr NpcDef NPCS[int(NpcId::COUNT)] = {
    {"Podesta' Guido",  MapId::PIAZZA_GRANDE, 31, 21, 0, 2},   // sotto il portone dei Consoli
    {"Mastro Tano",     MapId::LARGO_BARGELLO, 16, 16, 2, 1},  // custode della Fontana dei Matti
    {"Berto",           MapId::PIAZZA_GRANDE, 45, 27, 3, 1},   // sul selciato, verso il muretto
};

inline constexpr int NPC_ENTRY_COUNT =
        int(sizeof(NPC_DIALOGUE_ENTRIES) / sizeof(NPC_DIALOGUE_ENTRIES[0]));

// Lo script da recitare adesso, secondo l'atto in corso. Ritorna `ScriptId::COUNT` se l'NPC in
// questo momento non ha nulla da dire.
[[nodiscard]] constexpr ScriptId npc_script_for_act(const NpcDef& npc, int current_act)
{
    for(int i = 0; i < npc.entry_count; ++i)
    {
        const DialogueEntry& entry = NPC_DIALOGUE_ENTRIES[npc.first_entry + i];

        if(entry.required_act == ACT_ANY || current_act >= entry.required_act)
        {
            return entry.script;      // prima corrispondenza vince
        }
    }

    return ScriptId::COUNT;
}

// Ogni intervallo deve stare dentro la tabella delle battute condizionate.
static_assert([]
{
    for(const NpcDef& npc : NPCS)
    {
        if(npc.entry_count == 0 || int(npc.first_entry) + int(npc.entry_count) > NPC_ENTRY_COUNT)
        {
            return false;
        }
    }

    return true;
}(), "Un NPC punta fuori dalla tabella delle battute");

// Nessun NPC dentro un ostacolo: sarebbe un personaggio con cui e' impossibile parlare, e ce ne
// si accorgerebbe solo giocando.
static_assert([]
{
    for(const NpcDef& npc : NPCS)
    {
        const bool dentro_un_muro =
            (npc.map == MapId::PIAZZA_GRANDE &&
             maps::is_solid(maps::get_tile_type(npc.tile_x, npc.tile_y))) ||
            (npc.map == MapId::LARGO_BARGELLO &&
             maps::is_solid(maps::bargello_tile_type(npc.tile_x, npc.tile_y)));

        if(dentro_un_muro)
        {
            return false;
        }
    }

    return true;
}(), "Un NPC e' collocato dentro un muro");

// L'Atto III del Podesta' precede l'Atto I nell'elenco: se qualcuno li invertisse, dall'Atto III
// in poi si vedrebbe ancora la battuta dell'Atto I e nessuno se ne accorgerebbe fino a giocarci.
static_assert(npc_script_for_act(NPCS[int(NpcId::PODESTA_GUIDO)], 3) == ScriptId::PODESTA_ATTO_III,
              "Nell'Atto III il Podesta' deve dire la sua battuta d'assedio");
static_assert(npc_script_for_act(NPCS[int(NpcId::PODESTA_GUIDO)], 1) == ScriptId::PODESTA_ATTO_I,
              "Nell'Atto I il Podesta' deve dire la sua battuta di apertura");

} // namespace gubbio

#endif // NPC_REGISTRY_H
