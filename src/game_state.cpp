#include "game_state.h"

#include "bn_common.h"

namespace gubbio
{

// BN_DATA_EWRAM_BSS e non BN_DATA_EWRAM: la seconda punta alla sezione inizializzata.
BN_DATA_EWRAM_BSS GameState g_game_state;

}
