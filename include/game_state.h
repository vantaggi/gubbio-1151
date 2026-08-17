#ifndef GAME_STATE_H
#define GAME_STATE_H

#include <stdint.h>

#include "bn_type_traits.h"

#include "hero_data.h"
#include "item_data.h"
#include "map_id.h"
#include "story_flags.h"

namespace gubbio {

// Stato persistente della partita: TUTTO cio' che sopravvive al cambio di scena e che il
// salvataggio su FRAM dovra' trasportare (Passi 8 e 17 del piano).
//
// PERCHE' ESISTE. Fino alla Sessione 10 lo stato del giocatore viveva dentro la scena di
// battaglia e moriva con essa: `main.cpp` costruiva un `BattleSceneManager`, lo faceva girare
// per sempre e non c'era nulla che potesse sopravvivergli. Con due scene (esplorazione e
// battaglia) serve un contenitore che nessuna delle due possieda.
//
// TRE VINCOLI, tutti verificati a compile time in fondo al file:
//   1. Nessun handle Butano (`bn::sprite_ptr`, `bn::regular_bg_ptr`, ...) e nessuna
//      `bn::string_view`: un handle e' una prenotazione di VRAM e non ha senso in un record
//      che verra' scritto su FRAM; una view punterebbe a memoria che il salvataggio non porta
//      con se'. Solo interi a larghezza fissa e aggregati di interi.
//   2. `bn::is_trivially_copyable`, richiesto da `bn::sram::write_offset` al Passo 8.
//   3. Nessun padding: la somma delle dimensioni dei campi e' uguale a `sizeof(GameState)`.
//      Senza, i byte di riempimento finiscono nel CRC32 con valori indeterminati e lo stesso
//      stato salvato due volte puo' produrre due checksum diversi.
//
// COLLOCAZIONE IN MEMORIA. L'unica istanza e' definita in `src/game_state.cpp` con
// `BN_DATA_EWRAM_BSS` ed e' dichiarata `extern` qui. Il motivo e' misurato, non presunto:
// nell'ELF di questo progetto `.bss` sta a `0x030022f0`, cioe' in IWRAM, che il gioco condivide
// con lo stack (~21 KB liberi). Una `GameState g_game_state;` scritta ingenuamente in un header
// finirebbe li'. `BN_DATA_EWRAM_BSS` e non `BN_DATA_EWRAM`: la seconda punta alla sezione
// `.ewram` *inizializzata*, cioe' byte di zeri in ROM piu' una copia ROM->RAM al boot per nulla.
//
// PROPRIETA'. Una sola istanza, ma **passata per riferimento** al costruttore di ogni scena;
// nessuna scena la raggiunge per nome globale. E' il modello gia' in uso nel progetto
// (`BattleHud::update(const BattleSceneManager&)`): l'istanza unica garantisce la fonte di
// verita', il passaggio per riferimento evita la scrivibilita' globale diffusa.

// Dimensione del party, DERIVATA dalla stessa tabella da cui `battle_scene.h` deriva la propria
// `PARTY_SIZE`. Non e' una seconda costante da tenere allineata a mano: le due sono legate da
// una `static_assert` in `src/game_state.cpp`, dove entrambi gli header sono visibili.
inline constexpr int GAME_PARTY_SIZE = int(sizeof(HEROES) / sizeof(HEROES[0]));

// Slot di inventario. Gli oggetti della Sez. 8E sono 5 e l'inventario e' CONDIVISO fra i tre
// Ceri (decisione della Sessione 07, a verbale in `item_data.h`): un byte per oggetto contiene
// il numero di copie possedute, ed e' indicizzato da `ItemId`.
inline constexpr int INVENTORY_SLOTS = 8;

// Quest tracciabili. Le quest censite nella Sez. 31A sono 5; i 32 slot sono deliberatamente
// sovradimensionati perche' `quest_state` e `quest_counter` entrano nel payload di salvataggio
// e allargarli DOPO il congelamento del formato costerebbe un bump di versione (Passo 8).
// `quest_counter` esiste separato da `quest_state` perche' un bit non sa contare fino a 3:
// Q-SM01 chiede 3 blocchi di ferro, Q-SA01 4 radici.
inline constexpr int MAX_QUESTS = 32;

// I quattro Quartieri: San Martino, Sant'Andrea, San Pietro, San Giuliano (Sez. 31 GDD).
inline constexpr int QUARTIERI_COUNT = 4;

// Le sette Tavole Eugubine della Sez. 17C, una maschera di bit su 8: `tavole_mask`.
inline constexpr int TAVOLE_COUNT = 7;

// Punto d'ingresso 0: lo spawn di default di ogni mappa (Passo 12).
inline constexpr uint8_t ENTRY_POINT_DEFAULT = 0;

// Punto d'ingresso speciale: NON usare uno spawn, riprendere da `player_pos_x/y`. E' cio' che
// distingue "entro dalla porta del Bargello" da "ricarico una partita salvata in mezzo alla
// piazza": senza questa distinzione, caricare un salvataggio rispedirebbe il giocatore
// all'ingresso dell'area ogni volta.
inline constexpr uint8_t ENTRY_POINT_RESUME = 255;

// Stato di una quest. Numerato esplicitamente: e' persistito su FRAM.
enum class QuestState : uint8_t
{
    UNKNOWN   = 0,   // il giocatore non l'ha ancora incontrata
    ACTIVE    = 1,
    COMPLETED = 2
};

// Cio' che di un Cero sopravvive alla singola battaglia.
//
// DECISIONE (Sessione 11): HP e Fervore SONO trasportati fra le scene. La prova sta nel GDD:
// la Sez. 6 assegna all'Eremo di Sant'Ambrogio "riposo, salvataggio e recupero MP/Fervore".
// Un luogo che ripristina il Fervore non ha alcuna funzione se il Fervore si ripristinasse da
// solo all'inizio di ogni scontro. Di conseguenza `HERO_START_FERVOR_PERCENT` (battle_scene.h)
// e' degradato da inizializzatore di ogni battaglia a **default di nuova partita**: e' cio' che
// `reset_new_game()` scrive, e da li' in poi il valore evolve e viene trasportato.
struct HeroRuntimeState
{
    uint16_t current_hp;
    uint16_t current_fervor;
    uint8_t  level;
    uint8_t  reserved;   // sempre 0: tiene la struttura senza padding e riserva un byte
};

static_assert(sizeof(HeroRuntimeState) == 6, "HeroRuntimeState va su FRAM: niente padding");

// Campi ordinati per allineamento decrescente (4, 2, 1): e' cio' che rende vera la
// `static_assert` di assenza di padding in fondo al file.
struct GameState
{
    // --- 4 byte ---
    uint32_t playtime_frames;          // unico contatore del tempo di gioco (vedi game_clock.h)

    // --- 2 byte ---
    HeroRuntimeState party[GAME_PARTY_SIZE];   // indicizzato come HEROES: Ubaldo, Giorgio, Antonio
    int16_t  player_pos_x;             // posizione sulla mappa, in PIXEL (Passo 13)
    int16_t  player_pos_y;
    uint16_t gold;

    // --- 1 byte ---
    uint8_t  current_map;              // MapId serializzato: unica numerazione ammessa
    uint8_t  entry_point;              // spawn point da cui rientrare nella mappa (Passo 12)
    uint8_t  current_act;              // Atto I..IV
    uint8_t  tavole_mask;              // 7 bit: Tavole Eugubine raccolte (Sez. 17C GDD)
    uint8_t  quartieri_reputation[QUARTIERI_COUNT];
    uint8_t  inventory[INVENTORY_SLOTS];       // copie possedute, indicizzato da ItemId
    uint8_t  quest_state[MAX_QUESTS];          // valori di QuestState
    uint8_t  quest_counter[MAX_QUESTS];        // progresso numerico della quest attiva
    StoryFlags story_flags;                    // 256 bandiere, intervalli riservati per modulo

    // Stato di partenza di una partita nuova. E' l'unico posto in cui i valori iniziali sono
    // scritti: `SaveSystem` non deve "formattare" nulla da solo (Passo 8).
    void reset_new_game();

    // Riporta nel dominio valido i campi riletti da FRAM. Un salvataggio corrotto ma con CRC
    // valido (o scritto da una versione precedente) non deve poter indicizzare fuori tabella:
    // qui un valore impossibile diventa un valore legale, non un assert davanti al giocatore.
    void clamp_after_load();

    [[nodiscard]] MapId map() const { return MapId(current_map); }
    void set_map(MapId id) { current_map = uint8_t(id); }

    [[nodiscard]] QuestState quest(int quest_id) const { return QuestState(quest_state[quest_id]); }
    void set_quest(int quest_id, QuestState state) { quest_state[quest_id] = uint8_t(state); }

    [[nodiscard]] int item_count(ItemId item) const { return inventory[int(item)]; }
};

// --- Invarianti verificati dal compilatore -------------------------------------------------

static_assert(bn::is_trivially_copyable<GameState>(),
              "GameState viene scritto su FRAM con bn::sram::write_offset, che lo esige");

static_assert(sizeof(GameState) <= 256, "GameState eccede il budget del Passo 4");

// Assenza di padding: se qualcuno inserisce un campo fuori dall'ordine di allineamento, la
// somma smette di quadrare e la build si ferma qui invece di produrre un CRC32 instabile.
static_assert(sizeof(GameState) ==
                  sizeof(uint32_t) +                                   // playtime_frames
                  sizeof(HeroRuntimeState) * GAME_PARTY_SIZE +         // party
                  sizeof(int16_t) * 2 + sizeof(uint16_t) +             // pos + gold
                  4 +                                                  // map, entry, act, tavole
                  QUARTIERI_COUNT + INVENTORY_SLOTS + MAX_QUESTS * 2 + // array a byte
                  STORY_FLAG_BYTES,
              "GameState ha padding: riordinare i campi per allineamento decrescente");

// L'inventario e la tabella degli oggetti devono restare rappresentabili l'uno nell'altra.
static_assert(int(ItemId::COUNT) <= INVENTORY_SLOTS,
              "Aggiunto un oggetto alla Sez. 8E senza allargare l'inventario");

static_assert(TAVOLE_COUNT <= 8, "tavole_mask e' un uint8_t");

// L'istanza unica. Definita in src/game_state.cpp, mai qui: una definizione in un header
// darebbe una copia per unita' di traduzione, che e' l'opposto di una fonte di verita' unica.
extern GameState g_game_state;

} // namespace gubbio

#endif // GAME_STATE_H
