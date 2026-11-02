#ifndef GUBBIO_GAME_STATE_H
#define GUBBIO_GAME_STATE_H

#include <cstddef>
#include <cstdint>

namespace gubbio
{

// Lo stato di partita: quel che il salvataggio copia byte per byte (include/save_data.h). Per
// questo il layout e' fissato dalle static_assert qui sotto: campi in ordine di allineamento
// decrescente, niente padding, ogni offset controllato. Un campo nuovo si aggiunge prendendo i
// byte dal riservato, senza cambiare sizeof (e quindi senza cambiare la versione del salvataggio).
struct GameState
{
    uint32_t frames;            // tutti i frame dall'accensione (anche fuori dalla partita)
    uint32_t tempo_frames;      // il tempo di gioco della partita
    int16_t x;                  // i piedi del giocatore, in pixel dell'area
    int16_t y;
    uint8_t area;               // mondo::AreaId
    uint8_t riservato[3];
};

static_assert(sizeof(GameState) == 16, "sizeof(GameState) cambiato: va aggiornato il salvataggio");
static_assert(offsetof(GameState, frames) == 0 && offsetof(GameState, tempo_frames) == 4 &&
              offsetof(GameState, x) == 8 && offsetof(GameState, y) == 10 && offsetof(GameState, area) == 12 &&
              offsetof(GameState, riservato) == 13, "GameState: gli offset sono congelati");

// L'unica istanza, definita in src/game_state.cpp con BN_DATA_EWRAM_BSS: deve stare in EWRAM
// (0x02......) e non in IWRAM, che e' poca e condivisa con lo stack.
// tools/check_zero_heap.sh lo verifica sull'ELF.
extern GameState g_game_state;

}

#endif
