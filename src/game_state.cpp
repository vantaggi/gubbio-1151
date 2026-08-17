#include "game_state.h"

#include "bn_common.h"

// `battle_scene.h` e' incluso per una sola costante, `HERO_START_FERVOR_PERCENT`, che vive li'
// dalla Sessione 02c ed e' la fonte unica del Fervore di partenza. La dipendenza sta in questo
// `.cpp` e NON in `game_state.h`: lo stato della partita non deve dipendere dalla macchina a
// stati della battaglia, il verso della dipendenza e' l'opposto (Passo 6).
#include "battle_scene.h"

namespace gubbio {

// Le due dimensioni del party sono derivate dalla stessa tabella `HEROES`, ma da due header
// diversi. Qui sono entrambe visibili: se un giorno divergono, la build si ferma.
static_assert(GAME_PARTY_SIZE == PARTY_SIZE, "Le due dimensioni del party sono divergenti");

// LIVELLO DI NUOVA PARTITA — decisione da confermare.
// Il GDD non definisce un sistema di esperienza (decisione aperta n.12 del piano): la Sez. 30
// fissa il cap a 20 e la tabella dei tempi indica "Liv. 1-4" per l'Atto I, ma non esiste ne'
// una curva di XP ne' un campo dove accumularla. Finche' non esiste, si conserva il 12 con cui
// TUTTI i collaudi a runtime finora eseguiti (Sessioni 03, 04, 08, 10) sono stati tarati:
// abbassarlo adesso invaliderebbe l'unica traccia di riferimento pubblicata in HANDOVER senza
// dare in cambio alcun sistema di progressione. `party_level` alimenta solo la formula dello
// scudo di Sant'Ubaldo (Sez. 12B GDD).
constexpr uint8_t NEW_GAME_PARTY_LEVEL = 12;

// La POSIZIONE di partenza non e' scritta qui. Una nuova partita comincia sullo spawn point di
// default di Piazza Grande, e gli spawn point vivono in `map_data.h`: duplicarne le coordinate
// qui significherebbe avere due verita' sulla stessa cosa, e la seconda smetterebbe di seguire
// la prima al primo ritocco della mappa. `player_pos_x/y` resta a zero finche' la scena di
// esplorazione non deposita il giocatore, cosa che fa leggendo `entry_point`.

void GameState::reset_new_game()
{
    playtime_frames = 0;

    for(int i = 0; i < GAME_PARTY_SIZE; ++i)
    {
        const HeroStats& stats = HEROES[i];

        party[i].current_hp = uint16_t(stats.max_hp);
        // Stessa aritmetica intera usata da `BattleSceneManager::_make_hero`: il Fervore di
        // partenza e' una quota del pool del singolo Cero, non un valore assoluto condiviso.
        party[i].current_fervor = uint16_t(stats.max_fervor * HERO_START_FERVOR_PERCENT[i] / 100);
        party[i].level = NEW_GAME_PARTY_LEVEL;
        party[i].reserved = 0;
    }

    player_pos_x = 0;
    player_pos_y = 0;
    gold = 0;

    set_map(MapId::PIAZZA_GRANDE);
    entry_point = ENTRY_POINT_DEFAULT;
    current_act = 1;
    tavole_mask = 0;

    for(int i = 0; i < QUARTIERI_COUNT; ++i)
    {
        quartieri_reputation[i] = 0;
    }

    for(int i = 0; i < INVENTORY_SLOTS; ++i)
    {
        inventory[i] = 0;
    }

    for(int i = 0; i < MAX_QUESTS; ++i)
    {
        quest_state[i] = uint8_t(QuestState::UNKNOWN);
        quest_counter[i] = 0;
    }

    story_flags.clear_all();
}

void GameState::clamp_after_load()
{
    // Una mappa inesistente rimanda all'hub invece di indicizzare `MAPS[]` fuori tabella.
    if(current_map >= MAP_COUNT)
    {
        set_map(MapId::PIAZZA_GRANDE);
        entry_point = ENTRY_POINT_DEFAULT;
    }

    for(int i = 0; i < GAME_PARTY_SIZE; ++i)
    {
        const HeroStats& stats = HEROES[i];

        if(party[i].current_hp > stats.max_hp)
        {
            party[i].current_hp = uint16_t(stats.max_hp);
        }

        if(party[i].current_fervor > stats.max_fervor)
        {
            party[i].current_fervor = uint16_t(stats.max_fervor);
        }

        // Un party interamente a 0 HP riletto da FRAM sarebbe una partita che si apre su una
        // sconfitta immediata: il capofila viene rimesso in piedi con 1 HP.
        if(party[i].level == 0)
        {
            party[i].level = 1;
        }
    }

    if(party[0].current_hp == 0 && party[1].current_hp == 0 && party[2].current_hp == 0)
    {
        party[0].current_hp = 1;
    }

    for(int i = 0; i < MAX_QUESTS; ++i)
    {
        if(quest_state[i] > uint8_t(QuestState::COMPLETED))
        {
            quest_state[i] = uint8_t(QuestState::UNKNOWN);
        }
    }

    for(int i = 0; i < INVENTORY_SLOTS; ++i)
    {
        // Oltre `ItemId::COUNT` non esiste alcun oggetto: gli slot di riserva restano vuoti.
        if(i >= int(ItemId::COUNT))
        {
            inventory[i] = 0;
        }
        else if(inventory[i] > ITEMS[i].max_carry)
        {
            inventory[i] = uint8_t(ITEMS[i].max_carry);
        }
    }

    if(current_act < 1 || current_act > 4)
    {
        current_act = 1;
    }

    tavole_mask = uint8_t(tavole_mask & ((1 << TAVOLE_COUNT) - 1));
}

// L'UNICA istanza dello stato di partita, in EWRAM e non in IWRAM.
//
// `BN_DATA_EWRAM_BSS` (bn_hw_common.h:24) colloca il simbolo nella sezione EWRAM *non
// inizializzata*: azzerata dal boot, senza copia ROM->RAM e senza byte di zeri in ROM.
// `BN_DATA_EWRAM` (:12), la variante che verrebbe naturale scrivere, punta invece alla sezione
// `.ewram` inizializzata e pagherebbe entrambe le cose per nulla.
//
// La collocazione non e' un atto di fede: `tools/check_zero_heap.sh` verifica che l'indirizzo
// di questo simbolo cominci per `0x02` (EWRAM) e non per `0x03` (IWRAM, condivisa con lo stack).
BN_DATA_EWRAM_BSS GameState g_game_state;

} // namespace gubbio
