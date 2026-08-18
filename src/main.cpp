#include "bn_core.h"
#include "bn_log.h"

#include "game_clock.h"
#include "game_state.h"
#include "save_data.h"
#include "scene.h"
#include "scene_battle.h"
#include "scene_exploration.h"

// ---------------------------------------------------------------------------------------------
// Entry point e TRAMPOLINO DI SCENE di Gubbio 1151.
//
// Il dispatch e' uno `switch` su `SceneId` con la scena come VARIABILE DI SCOPE. Sono vietati
// per contratto — e il gate `tools/check_zero_heap.sh` lo verifica sui sorgenti — puntatori
// possedenti, `new`, `bn::unique_ptr`, factory che ritornano `Scene*` e tabelle di funzioni che
// costruiscono scene. La conseguenza che conta e' che esiste AL PIU' UNA SCENA VIVA per volta,
// garantito dallo scope: e' la sequenza "fade-nero -> distruggi -> costruisci -> fade-in"
// ottenuta per costruzione. La forma alternativa (una `bn::optional` per scena a scope di main)
// riserverebbe per sempre la SOMMA delle dimensioni di tutte le scene.
//
// Comandi in battaglia: SU/GIU = comando, SX/DX = bersaglio, L = abilita', R = Fervor Boost,
//                       A = conferma, B = indietro.
// ---------------------------------------------------------------------------------------------

#ifdef GUBBIO_BATTLE_AUTOTEST

// Replay dei tasti nativo di Butano (`bn::core::init(keypad_commands)`): due caratteri per
// frame, il primo con i 5 bit bassi della maschera tasti e il secondo con i 5 alti, ciascuno
// codificato come '0' + valore.
//   A    = 0x001 -> bassi 1,  alti 0 -> "10"
//   GIU  = 0x080 -> bassi 0,  alti 4 -> "04"
//   L    = 0x200 -> bassi 0,  alti 16 -> "0@"
//   nulla= 0x000                     -> "00"
//
// Un round: Giorgio alza il Bastione Azzurro (GIU' al menu Abilita', L per scorrere alla
// seconda abilita', A), Ubaldo lancia il Giudizio della Verga (stessa sequenza), Antonio il
// Fuoco (prima abilita', nessun L), poi tre frame per EXECUTE e CHECK.
#define GUBBIO_AUTOTEST_ROUND \
    "04" "00" "0@" "00" "10" "00"   /* Giorgio -> Bastione Azzurro   */ \
    "04" "00" "0@" "00" "10" "00"   /* Ubaldo  -> Giudizio della Verga */ \
    "04" "00" "10" "00"             /* Antonio -> Fuoco di Sant'Antonio */ \
    "00" "00" "00"                  /* EXECUTE + CHECK + assestamento  */

// ALLINEAMENTO: i frame di scarto prima del primo comando utile sono
//   1 (consumato da `bn::core::init()`) + INTRO_DURATION_FRAMES (lo stato INTRO_FADE_IN, che
//   dissolve dal nero senza leggere input) = 33 con l'attuale valore di 32.
//
// ATTENZIONE: questo numero E' ACCOPPIATO a `INTRO_DURATION_FRAMES` in src/battle_scene.cpp e
// il preprocessore non puo' derivarlo. La Sessione 06 ha portato l'intro da 1 a 32 frame senza
// aggiornare qui: lo script e' slittato di 31 posizioni e l'autotest ha continuato a riportare
// "zero assert" eseguendo pero' solo 2 round invece di 7. Un autotest disallineato non fallisce,
// mente. Se si cambia INTRO_DURATION_FRAMES, si cambia anche questo.
// La costruzione della scena (Sessione 11) non consuma frame: fra `bn::core::init()` e il primo
// `core_update()` del ciclo non c'e' alcun aggiornamento, quindi lo scarto resta 33.
#define GUBBIO_ALIGN_2  "00" "00"
#define GUBBIO_ALIGN_8  GUBBIO_ALIGN_2 GUBBIO_ALIGN_2 GUBBIO_ALIGN_2 GUBBIO_ALIGN_2
#define GUBBIO_AUTOTEST_ALIGN     GUBBIO_ALIGN_8 GUBBIO_ALIGN_8 GUBBIO_ALIGN_8 GUBBIO_ALIGN_8 "00"   /* 33 frame */

// Coda di CAMMINATA, aggiunta nella Sessione 11 per collaudare l'esplorazione.
// SINISTRA (0x020) + SU (0x040) + B (0x002) = 0x062 -> bassi 0x02 = '2', alti 0x03 = '3'.
// In corsa (2 px/frame) dal centro della piazza servono ~127 frame per raggiungere il varco
// occidentale a x=6 px: 256 frame lasciano margine anche se la battaglia finisce piu' tardi.
#define GUBBIO_WALK_1    "23"
#define GUBBIO_WALK_4    GUBBIO_WALK_1 GUBBIO_WALK_1 GUBBIO_WALK_1 GUBBIO_WALK_1
#define GUBBIO_WALK_16   GUBBIO_WALK_4 GUBBIO_WALK_4 GUBBIO_WALK_4 GUBBIO_WALK_4
#define GUBBIO_WALK_64   GUBBIO_WALK_16 GUBBIO_WALK_16 GUBBIO_WALK_16 GUBBIO_WALK_16
#define GUBBIO_WALK_256  GUBBIO_WALK_64 GUBBIO_WALK_64 GUBBIO_WALK_64 GUBBIO_WALK_64

// Coda finale: la SECONDA battaglia (quella aperta dal varco) comincia a un frame che dipende
// da quanto e' durata la camminata, quindi non e' allineabile a uno script di round. Si usa
// allora una sequenza grossolana — GIU' e A alternati — che scorre il menu e conferma finche'
// la battaglia non si chiude in un modo qualsiasi. Serve a osservare il RIENTRO, che e' il
// punto in cui nasce il loop di transizione, non a collaudare le formule.
#define GUBBIO_SPAM_4    "04" "10" "04" "10"
#define GUBBIO_SPAM_16   GUBBIO_SPAM_4 GUBBIO_SPAM_4 GUBBIO_SPAM_4 GUBBIO_SPAM_4
#define GUBBIO_SPAM_64   GUBBIO_SPAM_16 GUBBIO_SPAM_16 GUBBIO_SPAM_16 GUBBIO_SPAM_16
#define GUBBIO_SPAM_256  GUBBIO_SPAM_64 GUBBIO_SPAM_64 GUBBIO_SPAM_64 GUBBIO_SPAM_64

// Fermo: mostra dove il giocatore e' ricomparso senza che l'input lo sposti.
#define GUBBIO_IDLE_4    "00" "00" "00" "00"
#define GUBBIO_IDLE_16   GUBBIO_IDLE_4 GUBBIO_IDLE_4 GUBBIO_IDLE_4 GUBBIO_IDLE_4
#define GUBBIO_IDLE_64   GUBBIO_IDLE_16 GUBBIO_IDLE_16 GUBBIO_IDLE_16 GUBBIO_IDLE_16
#define GUBBIO_IDLE_256  GUBBIO_IDLE_64 GUBBIO_IDLE_64 GUBBIO_IDLE_64 GUBBIO_IDLE_64

// A premuto per un frame: nell'esplorazione apre la battuta di prova, e una seconda pressione
// la chiude quando il testo e' completo.
#define GUBBIO_TASTO_A   "10" "00"

// R (0x100) -> bassi 0 = '0', alti 8 = '8'. Apre la battuta di prova nell'esplorazione.
#define GUBBIO_TASTO_R   "08" "00"

// SELECT (0x004) -> bassi 4 = '4', alti 0 = '0'. Un frame premuto, uno rilasciato: il
// salvataggio scatta su `select_pressed()`, cioe' sul fronte, non finche' il tasto e' giu'.
#define GUBBIO_SELECT    "40" "00"

constexpr const char* AUTOTEST_KEYPAD_SCRIPT =
    GUBBIO_AUTOTEST_ALIGN
    GUBBIO_AUTOTEST_ROUND GUBBIO_AUTOTEST_ROUND GUBBIO_AUTOTEST_ROUND GUBBIO_AUTOTEST_ROUND
    GUBBIO_AUTOTEST_ROUND GUBBIO_AUTOTEST_ROUND GUBBIO_AUTOTEST_ROUND GUBBIO_AUTOTEST_ROUND
    GUBBIO_WALK_256
    GUBBIO_SPAM_256
    GUBBIO_IDLE_64        // attesa che la dissolvenza d'ingresso finisca
    GUBBIO_SELECT         // salvataggio su FRAM, verificabile nel `.sav` e nel log
    GUBBIO_IDLE_16
    GUBBIO_TASTO_R        // apre il dialogo di prova
    GUBBIO_IDLE_256       // la macchina da scrivere percorre le tre righe (~156 frame)
    GUBBIO_TASTO_A        // lo chiude
    GUBBIO_IDLE_64;

#endif

#ifndef GUBBIO_AUTOTEST_ENCOUNTER
#define GUBBIO_AUTOTEST_ENCOUNTER 0
#endif

int main()
{
#ifdef GUBBIO_BATTLE_AUTOTEST
    bn::core::init(AUTOTEST_KEYPAD_SCRIPT);
#else
    bn::core::init();
#endif

    BN_LOG("=== GUBBIO 1151: avvio ===");

    // Caricamento all'avvio. Uno slot corrotto NON viene riformattato: si comincia una partita
    // nuova in memoria e i byte sul chip restano come sono, cosi' che il giocatore possa
    // decidere se sovrascriverli e chi indaga possa ancora leggerli (Passo 8).
    const gubbio::SlotStatus stato_slot = gubbio::SaveSystem::probe(gubbio::SAVE_SLOT_DEFAULT);
    bool caricata = false;

    if(stato_slot == gubbio::SlotStatus::VALID)
    {
        caricata = gubbio::SaveSystem::load(gubbio::SAVE_SLOT_DEFAULT, gubbio::g_game_state);
        BN_LOG("SLOT 0 valido, tempo di gioco ",
               int(gubbio::SaveSystem::stored_playtime_seconds(gubbio::SAVE_SLOT_DEFAULT)), "s: ",
               caricata ? "partita CARICATA" : "caricamento fallito");
    }
    else
    {
        BN_LOG("SLOT 0 non caricabile (stato ", int(stato_slot), "): nuova partita");
    }

    if(! caricata)
    {
        gubbio::g_game_state.reset_new_game();
    }

    // Il gioco comincia dall'hub: Piazza Grande.
    // Sotto autotest comincia invece dalla battaglia, perche' lo script a tasti fissi e' tarato
    // sui 33 frame di scarto di quello scontro (vedi GUBBIO_AUTOTEST_ALIGN) e ogni frame speso
    // altrove lo disallineerebbe. La coda di camminata dello script porta poi il giocatore sul
    // varco occidentale, che riapre una battaglia: e' cosi' che il round-trip viene collaudato.
#ifdef GUBBIO_BATTLE_AUTOTEST
    gubbio::SceneRequest request = gubbio::SceneRequest::battle(GUBBIO_AUTOTEST_ENCOUNTER);
#else
    gubbio::SceneRequest request = gubbio::SceneRequest::exploration(gubbio::MapId::PIAZZA_GRANDE);
#endif

    while(true)
    {
        // Nessun `default:`, come nella FSM di battaglia e per lo stesso motivo a verbale dalla
        // Sessione 10: elencando tutti gli `SceneId` senza default e' -Wswitch a fare la
        // guardia, e aggiungere domani una scena senza gestirla qui diventa un errore visibile
        // invece di un ramo muto. Si accetta il -Wswitch-default per non perdere quel controllo.
        switch(request.id)
        {
            case gubbio::SceneId::BATTLE:
                {
                    gubbio::BattleScene scene(gubbio::g_game_state, request);
                    request = scene.run();
                }
                break;

            case gubbio::SceneId::EXPLORATION:
                {
                    gubbio::ExplorationScene scene(gubbio::g_game_state, request);
                    request = scene.run();
                }
                break;

            case gubbio::SceneId::GAME_OVER:
                BN_LOG("SCENA -> GAME OVER");
                request = gubbio::SceneRequest{gubbio::SceneId::NONE, 0};
                break;

            case gubbio::SceneId::NONE:
                gubbio::core_update();
                break;
        }
    }
}
