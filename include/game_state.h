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
    uint16_t esperienza[3];     // dei tre Santi (include/progressione.h)
    int16_t x;                  // i piedi del giocatore, in pixel dell'area
    int16_t y;
    uint8_t area;               // mondo::AreaId
    uint8_t livello[3];         // 1..8
    uint8_t oggetti[8];         // quanti consumabili per tipo
    uint8_t scontri_vinti[4];   // un bit per progressione::Bandiera
    uint8_t storia[8];          // le bandiere della storia (storia::Bandiera, intervallo 0-63)
    uint8_t scene_fatte[4];     // un bit per scena del copione gia' giocata (storia::SCENA)
    uint8_t riservato[18];
};

static_assert(sizeof(GameState) == 64, "sizeof(GameState) cambiato: va aggiornato il salvataggio");
static_assert(offsetof(GameState, frames) == 0 && offsetof(GameState, tempo_frames) == 4 &&
              offsetof(GameState, esperienza) == 8 && offsetof(GameState, x) == 14 && offsetof(GameState, y) == 16 &&
              offsetof(GameState, area) == 18 && offsetof(GameState, livello) == 19 &&
              offsetof(GameState, oggetti) == 22 && offsetof(GameState, scontri_vinti) == 30 &&
              offsetof(GameState, storia) == 34 && offsetof(GameState, scene_fatte) == 42 &&
              offsetof(GameState, riservato) == 46, "GameState: gli offset sono congelati");

// L'unica istanza, definita in src/game_state.cpp con BN_DATA_EWRAM_BSS: deve stare in EWRAM
// (0x02......) e non in IWRAM, che e' poca e condivisa con lo stack.
// tools/check_zero_heap.sh lo verifica sull'ELF.
extern GameState g_game_state;

}

#endif
