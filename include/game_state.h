#ifndef GUBBIO_GAME_STATE_H
#define GUBBIO_GAME_STATE_H

namespace gubbio
{

// Lo stato di partita. In F0 contiene solo un contatore di frame: serve a dare al gate
// zero-heap un simbolo da controllare fin dalla prima ROM.
struct GameState
{
    unsigned frames;
};

// L'unica istanza, definita in src/game_state.cpp con BN_DATA_EWRAM_BSS: deve stare in EWRAM
// (0x02......) e non in IWRAM, che e' poca e condivisa con lo stack.
// tools/check_zero_heap.sh lo verifica sull'ELF.
extern GameState g_game_state;

}

#endif
