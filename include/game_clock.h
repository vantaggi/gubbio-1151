#ifndef GAME_CLOCK_H
#define GAME_CLOCK_H

#include "bn_core.h"

#include "game_state.h"

namespace gubbio {

// L'UNICO punto del progetto in cui si chiama `bn::core::update()`.
//
// PERCHE'. Il tempo di gioco va contato una volta sola e in un posto solo. Se ogni scena
// chiamasse `bn::core::update()` per conto proprio, il contatore `playtime_frames` andrebbe
// incrementato in altrettanti punti: basterebbe che una scena nuova dimenticasse di farlo
// perche' l'orologio rallenti in quella scena e nessuno se ne accorga, visto che l'errore non
// e' visibile finche' qualcuno non confronta due salvataggi.
//
// E' un criterio di accettazione MISURATO, non una convenzione: `tools/check_zero_heap.sh`
// fallisce la build se `bn::core::update()` compare in un file di `src/` o `include/` diverso
// da questo. Nessuna scena ha il permesso di chiamarlo direttamente.
//
// Nota sulla proprieta' di `g_game_state`: la regola generale e' che ogni scena riceva lo stato
// per riferimento e non lo raggiunga per nome globale. Questa funzione e' l'unica eccezione, ed
// e' deliberata — l'orologio non appartiene a nessuna scena, ed e' proprio il fatto di NON
// passare da un riferimento di scena a renderlo un punto unico.
inline void core_update()
{
    bn::core::update();
    ++g_game_state.playtime_frames;
}

// Frame per secondo del GBA: serve a convertire `playtime_frames` nel `playtime_seconds` che
// il salvataggio memorizza (Passo 8) e che il menu mostra.
inline constexpr int FRAMES_PER_SECOND = 60;

[[nodiscard]] inline int playtime_seconds()
{
    return int(g_game_state.playtime_frames / FRAMES_PER_SECOND);
}

} // namespace gubbio

#endif // GAME_CLOCK_H
