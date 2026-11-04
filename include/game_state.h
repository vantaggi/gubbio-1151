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
//
// Versione 4 del salvataggio (MOB, menu/PROPOSTA.md sez. 4): 80 byte invece di 64. I primi 59 byte
// (fino a ferite compreso) sono quelli della v3, allo stesso offset: un salvataggio v3 si aggiorna
// copiandoli (salvataggio::migra_v3). I 5 byte che erano riservati prendono obiettivo, aree_viste e
// scorte_comprate; denari sta nella coda, a offset pari (64), e il resto della coda e' riservato.
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
    uint8_t cutscene_viste[2];  // un bit per cutscene gia' vista (regia::CUTSCENE_DATI)
    uint8_t quest[8];           // le bandiere delle quest e degli indizi (intervallo 64-127)
    uint8_t ferite[3];          // i PV tolti dai miasmi della gola, per Santo: pesano sulla prossima battaglia (T2)
    // --- v4 ---
    uint8_t obiettivo;          // la riga OBIETTIVO della cronaca (indice in storia::OBIETTIVO), NESSUN_OBIETTIVO
    uint8_t aree_viste[3];      // un bit per mondo::AreaId gia' visitata (la nebbia della mappa)
    uint8_t scorte_comprate;    // due contatori da 4 bit: le scorte del Venditore gia' comprate (MNEG)
    uint16_t denari;            // dai nemici, per il Venditore delle Logge (MNEG)
    uint8_t riservato[14];
};

inline constexpr uint8_t NESSUN_OBIETTIVO = 255;

static_assert(sizeof(GameState) == 80, "sizeof(GameState) cambiato: va aggiornato il salvataggio");
static_assert(offsetof(GameState, frames) == 0 && offsetof(GameState, tempo_frames) == 4 &&
              offsetof(GameState, esperienza) == 8 && offsetof(GameState, x) == 14 && offsetof(GameState, y) == 16 &&
              offsetof(GameState, area) == 18 && offsetof(GameState, livello) == 19 &&
              offsetof(GameState, oggetti) == 22 && offsetof(GameState, scontri_vinti) == 30 &&
              offsetof(GameState, storia) == 34 && offsetof(GameState, scene_fatte) == 42 &&
              offsetof(GameState, cutscene_viste) == 46 && offsetof(GameState, quest) == 48 &&
              offsetof(GameState, ferite) == 56 && offsetof(GameState, obiettivo) == 59 &&
              offsetof(GameState, aree_viste) == 60 && offsetof(GameState, scorte_comprate) == 63 &&
              offsetof(GameState, denari) == 64 && offsetof(GameState, riservato) == 66,
              "GameState: gli offset sono congelati");

// L'unica istanza, definita in src/game_state.cpp con BN_DATA_EWRAM_BSS: deve stare in EWRAM
// (0x02......) e non in IWRAM, che e' poca e condivisa con lo stack.
// tools/check_zero_heap.sh lo verifica sull'ELF.
extern GameState g_game_state;

}

#endif
