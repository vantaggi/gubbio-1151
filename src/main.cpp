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
// B TENUTO PREMUTO, cioe' il fast-forward che il Passo 20 ha dato al giocatore. Serve anche
// all'autotest: con lo stato PLAY_ROUND_ANIMATIONS ogni round dura cinque volte tanto, e senza
// fast-forward dopo sette minuti di emulazione lo script era ancora al quarto round — la
// camminata e il salvataggio non venivano piu' raggiunti, e il test sul .sav diventava rosso
// senza che nulla nel gioco fosse rotto. Un oracolo che il proprio soggetto ha reso troppo lento
// smette di misurare.
// B (0x002) -> bassi 2 = '2', alti 0 = '0'. A passo 4 per frame, 64 frame coprono 256 frame di
// animazione, cioe' piu' del round peggiore.
#define GUBBIO_FF_4     "20" "20" "20" "20"
#define GUBBIO_FF_16    GUBBIO_FF_4 GUBBIO_FF_4 GUBBIO_FF_4 GUBBIO_FF_4
#define GUBBIO_FF_64    GUBBIO_FF_16 GUBBIO_FF_16 GUBBIO_FF_16 GUBBIO_FF_16

// Fuoco (prima abilita', nessun L), poi tre frame per EXECUTE e CHECK.
#define GUBBIO_AUTOTEST_ROUND \
    "04" "00" "0@" "00" "10" "00"   /* Giorgio -> Bastione Azzurro   */ \
    "04" "00" "0@" "00" "10" "00"   /* Ubaldo  -> Giudizio della Verga */ \
    "04" "00" "10" "00"             /* Antonio -> Fuoco di Sant'Antonio */ \
    "00" "00" "00"                  /* EXECUTE + CHECK + assestamento  */ \
    GUBBIO_FF_64                    /* PLAY_ROUND_ANIMATIONS, in fast-forward */

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
// DESTRA (0x010) + SU (0x040) + B (0x002) = 0x052 -> bassi 0x12 = 'B', alti 0x02 = '2'.
//
// DESTRA e non piu' sinistra: con la piazza raddrizzata (Sessione 20) il ciottolato e i due
// imbocchi stanno a NORD, che sulla mappa ruotata e' il lato DESTRO. Andando a sinistra il
// giocatore trovava il muretto e ci restava appoggiato per 256 frame senza uscire mai — un
// autotest che non fallisce e non prova nulla.
// In corsa (2 px/frame) dal centro (116, 308) al varco di via dei Consoli (240, 64) servono
// ~122 frame sull'asse piu' lungo: 256 lasciano margine anche se la battaglia finisce tardi.
#define GUBBIO_WALK_1    "B2"
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

// DESTRA (0x010) + SU (0x040) + B (0x002) = 0x052 -> bassi 0x12 = 'B', alti 2 = '2'.
// Porta il giocatore dal punto di rientro fino al Podesta' Guido, che sta davanti al Palazzo
// dei Consoli: in corsa servono un centinaio di frame, e la salita si ferma da sola contro la
// facciata del palazzo — che e' proprio dove l'NPC aspetta.
#define GUBBIO_NE_1      "B2"
#define GUBBIO_NE_4      GUBBIO_NE_1 GUBBIO_NE_1 GUBBIO_NE_1 GUBBIO_NE_1
#define GUBBIO_NE_16     GUBBIO_NE_4 GUBBIO_NE_4 GUBBIO_NE_4 GUBBIO_NE_4
#define GUBBIO_NE_64     GUBBIO_NE_16 GUBBIO_NE_16 GUBBIO_NE_16 GUBBIO_NE_16
// 100 frame esatti: in corsa sono 200 px, che e' la distanza dal punto di rientro (x 44) al
// Podesta' (x 244). Con 128 il giocatore lo SUPERAVA e premeva A nel vuoto — la prima stesura
// sbagliava proprio cosi', e il log lo ha mostrato subito.
#define GUBBIO_NE_100    GUBBIO_NE_64 GUBBIO_NE_16 GUBBIO_NE_16 GUBBIO_NE_4

// SINISTRA (0x020) + B (0x002) = 0x022 -> bassi 2 = '2', alti 1 = '1'.
// GIU' (0x080) + B (0x002) = 0x082 -> bassi 2 = '2', alti 4 = '4'.
//
// Due tratti dritti invece di una diagonale, ed e' voluto: in diagonale entrambi gli assi
// avanzano ogni frame, quindi la corsa supera la riga di Tano molto prima di raggiungere la sua
// colonna e finisce contro il bordo della mappa. Con due tratti ciascun asse si ferma dove deve.
// CERCA invece di MIRARE, e la differenza non e' stilistica.
//
// Lo script dei tasti e' indicizzato sul FRAME, dal frame zero, mentre la scena di esplorazione
// comincia a un frame che dipende da quanto e' durata la battaglia e da quanti frame consuma la
// dissolvenza d'ingresso — che ignora l'input. Una traiettoria contata al pixel ("48 frame a
// sinistra sono 96 px sono 12 tile") e' quindi esatta solo per caso: misurata, mancava Mastro
// Tano di 22 px sull'asse x e di 28 sull'asse y, e l'unico sintomo era l'assenza silenziosa di
// una riga di log.
//
// Qui invece si cammina PREMENDO A ogni quattro frame. Non serve sapere dove si e': basta
// passare, prima o poi, entro i 12 px di raggio d'interazione di qualcuno. Tre frame di corsa e
// uno di pressione: abbastanza rado da non richiudere la battuta appena aperta.
//
// I DUE CARATTERI VANNO IN QUEST'ORDINE: prima i 5 bit BASSI, poi gli ALTI. Scriverli
// invertiti non e' un errore che si vede — produce una combinazione di tasti diversa ma
// perfettamente valida, e il gioco la esegue. Scritto "42" invece di "24" per GIU'+B,
// l'autotest premeva SELECT+SU: risaliva i varchi appena attraversati facendo rimbalzare
// il giocatore fra due aree, e intanto salvava su FRAM a ogni pressione. Il modello da
// copiare e' GUBBIO_WALK_1, "23" per 0x062: bassi 2 primo carattere, alti 3 secondo.
//
// SINISTRA (0x020) + B (0x002)             = 0x022 -> bassi 2, alti 1 -> "21"
// SINISTRA (0x020) + B (0x002) + A (0x001) = 0x023 -> bassi 3, alti 1 -> "31"
// GIU'     (0x080) + B (0x002)             = 0x082 -> bassi 2, alti 4 -> "24"
// GIU'     (0x080) + B (0x002) + A (0x001) = 0x083 -> bassi 3, alti 4 -> "34"
#define GUBBIO_CERCA_O_4   "21" "21" "21" "31"
#define GUBBIO_CERCA_O_16  GUBBIO_CERCA_O_4 GUBBIO_CERCA_O_4 GUBBIO_CERCA_O_4 GUBBIO_CERCA_O_4
#define GUBBIO_CERCA_O_64  GUBBIO_CERCA_O_16 GUBBIO_CERCA_O_16 GUBBIO_CERCA_O_16 GUBBIO_CERCA_O_16
// Discesa liscia verso EST, senza premere A: serve a PERCORRERE una strada, non a
// cercare qualcuno. GIU' (0x080) + B (0x002) = 0x082 -> "24".
#define GUBBIO_EST_1       "24"
#define GUBBIO_EST_4       GUBBIO_EST_1 GUBBIO_EST_1 GUBBIO_EST_1 GUBBIO_EST_1
#define GUBBIO_EST_16      GUBBIO_EST_4 GUBBIO_EST_4 GUBBIO_EST_4 GUBBIO_EST_4
#define GUBBIO_EST_64      GUBBIO_EST_16 GUBBIO_EST_16 GUBBIO_EST_16 GUBBIO_EST_16
#define GUBBIO_EST_256     GUBBIO_EST_64 GUBBIO_EST_64 GUBBIO_EST_64 GUBBIO_EST_64

#define GUBBIO_CERCA_S_4   "24" "24" "24" "34"
#define GUBBIO_CERCA_S_16  GUBBIO_CERCA_S_4 GUBBIO_CERCA_S_4 GUBBIO_CERCA_S_4 GUBBIO_CERCA_S_4
#define GUBBIO_CERCA_S_48  GUBBIO_CERCA_S_16 GUBBIO_CERCA_S_16 GUBBIO_CERCA_S_16

// DESTRA (0x010) + GIU' (0x080) + B (0x002) = 0x092 -> bassi 0x12 = 'B', alti 4 = '4'.
// Porta dal punto di rientro a MASTRO TANO, accanto alla Fontana dei Matti: 136 px in corsa,
// cioe' 68 frame. E' l'NPC su cui il gioco crashava — le sue battute hanno due righe invece di
// tre, ed e' la riga assente a produrre il puntatore nullo. L'autotest andava solo dal Podesta',
// che ne ha tre, e quindi non lo incontrava mai.
#define GUBBIO_SE_1      "B4"
#define GUBBIO_SE_4      GUBBIO_SE_1 GUBBIO_SE_1 GUBBIO_SE_1 GUBBIO_SE_1
#define GUBBIO_SE_16     GUBBIO_SE_4 GUBBIO_SE_4 GUBBIO_SE_4 GUBBIO_SE_4
#define GUBBIO_SE_68     GUBBIO_SE_16 GUBBIO_SE_16 GUBBIO_SE_16 GUBBIO_SE_16 GUBBIO_SE_4

// SELECT (0x004) -> bassi 4 = '4', alti 0 = '0'. Un frame premuto, uno rilasciato: il
// salvataggio scatta su `select_pressed()`, cioe' sul fronte, non finche' il tasto e' giu'.
#define GUBBIO_SELECT    "40" "00"

// --- L'ANELLO DELLA CITTA', PERCORSO PER INTERO -----------------------------------------------
//
// Otto aree in fila: Piazza Grande -> via dei Consoli -> Largo del Bargello -> San Martino ->
// (Porta di Santa Lucia) -> Bottaccione -> Basilica -> stradoni del Monte -> Duomo e Palazzo
// Ducale -> Piazza Grande. E' l'anello dettato dal committente, e questo e' il solo modo di
// sapere che le quattordici aree sono davvero cucite: la build dice che compilano, non che si
// attraversano.
//
// ZIGZAG, non spinta dritta. Il movimento risolve i due assi SEPARATAMENTE
// (overworld_player.cpp), quindi in diagonale contro un muro si scivola invece di incollarsi.
// Una spinta dritta funziona in un corridoio dritto e si pianta al primo tornante — e gli
// stradoni del monte sono tutti tornanti. Alternando la componente trasversale, la componente
// utile avanza comunque ogni frame in cui e' libera, e il percorso storto viene seguito da se'.
//
// Ordine dei due caratteri: prima i 5 bit BASSI, poi gli ALTI. Invertirli produce una
// combinazione valida ma diversa, che il gioco esegue senza lamentarsi: e' gia' costato tre
// giri a vuoto.
//   SU        SU+B          = 0x042 -> "22"      GIU'      GIU'+B        = 0x082 -> "24"
//   SINISTRA  SX+B          = 0x022 -> "21"      SU+SX     SU+SX+B       = 0x062 -> "23"
//   GIU'+SX   GIU'+SX+B     = 0x0A2 -> "25"      SU+DX     SU+DX+B       = 0x052 -> "B2"
//   GIU'+DX   GIU'+DX+B     = 0x092 -> "B4"
#define GUBBIO_ZIG_SU_8    "22" "22" "22" "22" "23" "23" "B2" "B2"
#define GUBBIO_ZIG_GIU_8   "24" "24" "24" "24" "25" "25" "B4" "B4"
#define GUBBIO_ZIG_SX_8    "21" "21" "21" "21" "23" "23" "25" "25"

// Spinta DRITTA a sinistra, senza ondeggiare. Lo zigzag serve solo dove il corridoio e' storto:
// dove e' dritto e la fascia d'uscita e' stretta, l'ondeggio porta fuori bersaglio. In Largo
// del Bargello il varco verso San Martino e' alto quattro tile e il rientro cade gia' dentro
// quella fascia: bastava non muoversi in verticale, e lo zigzag invece ne usciva di un tile.
#define GUBBIO_SX_8        "21" "21" "21" "21" "21" "21" "21" "21"

#define GUBBIO_Q(m)        m m m m
#define GUBBIO_ZIG_SU_32   GUBBIO_Q(GUBBIO_ZIG_SU_8)
#define GUBBIO_ZIG_GIU_32  GUBBIO_Q(GUBBIO_ZIG_GIU_8)
#define GUBBIO_ZIG_SX_32   GUBBIO_Q(GUBBIO_ZIG_SX_8)
#define GUBBIO_SX_32       GUBBIO_Q(GUBBIO_SX_8)
#define GUBBIO_SX_128      GUBBIO_Q(GUBBIO_SX_32)
#define GUBBIO_ZIG_SU_128  GUBBIO_Q(GUBBIO_ZIG_SU_32)
#define GUBBIO_ZIG_GIU_128 GUBBIO_Q(GUBBIO_ZIG_GIU_32)
#define GUBBIO_ZIG_SX_128  GUBBIO_Q(GUBBIO_ZIG_SX_32)
#define GUBBIO_ZIG_SU_512  GUBBIO_Q(GUBBIO_ZIG_SU_128)
#define GUBBIO_ZIG_GIU_512 GUBBIO_Q(GUBBIO_ZIG_GIU_128)
#define GUBBIO_ZIG_SX_512  GUBBIO_Q(GUBBIO_ZIG_SX_128)

constexpr const char* AUTOTEST_KEYPAD_SCRIPT =
    GUBBIO_AUTOTEST_ALIGN
    GUBBIO_AUTOTEST_ROUND GUBBIO_AUTOTEST_ROUND GUBBIO_AUTOTEST_ROUND GUBBIO_AUTOTEST_ROUND
    GUBBIO_AUTOTEST_ROUND GUBBIO_AUTOTEST_ROUND GUBBIO_AUTOTEST_ROUND GUBBIO_AUTOTEST_ROUND
    // LA CATENA DELLA CITTA', percorsa per intero. Dalla Sessione 20 il varco nord-ovest della
    // piazza non salta piu' al Bargello: scende per VIA DEI CONSOLI, che e' un'area a se'. Il
    // percorso collaudato qui e' quindi Piazza Grande -> via dei Consoli -> Largo del Bargello,
    // cioe' due transizioni consecutive invece di una. E' il punto in cui nascono i loop di
    // transizione che gli spawn point esistono per impedire, e ora ce ne sono due in fila.
    // 128 frame e non 256: ne bastano ~122 per arrivare al varco, e i restanti continuavano a
    // spingere VERSO L'ALTO anche dopo la transizione, ributtando il giocatore dentro il varco
    // opposto. Un autotest che tiene premuta una direzione oltre il proprio scopo non collauda
    // la transizione: la fa fallire.
    // TRATTA 1 - Piazza Grande: dal centro (14,38) al varco nord-ovest, in salita a destra.
    GUBBIO_WALK_64 GUBBIO_WALK_64
    GUBBIO_IDLE_64        // attesa che la dissolvenza d'ingresso finisca
    GUBBIO_SELECT         // salvataggio su FRAM, verificabile nel `.sav` e nel log
    GUBBIO_IDLE_16
    // TRATTA 2 - via dei Consoli, in discesa: 59 tile dal rientro (7,3) al varco a valle.
    // 224 frame, non 288: dal rientro (7,8) al varco a valle ci sono 54 tile, cioe' 216
    // frame in corsa. I 70 di troppo non si fermavano al confine dell'area — proseguivano
    // DENTRO il Bargello spingendo il giocatore contro il muro sud, dove il varco verso San
    // Martino non c'e', e da li' le tratte successive non riuscivano piu' a rimetterlo in
    // riga. Una tratta troppo lunga non e' prudenza: e' un guasto per l'area seguente.
    GUBBIO_ZIG_GIU_128 GUBBIO_ZIG_GIU_32 GUBBIO_ZIG_GIU_32 GUBBIO_ZIG_GIU_32
    GUBBIO_IDLE_16
    // TRATTA 3 - Largo del Bargello, verso ovest: 27 tile dal rientro (28,12) alla discesa.
    GUBBIO_SX_128
    GUBBIO_IDLE_16
    // TRATTA 4 - San Martino, in giu': 29 tile dal rientro (15,9) alla Porta di Santa Lucia.
    GUBBIO_ZIG_GIU_128
    GUBBIO_IDLE_16
    // TRATTA 5 - Bottaccione, in su': 51 tile dal rientro (10,57) al varco verso la vetta.
    // 288 e non 256: il camminamento e' lungo 453 px e 256 frame ne coprono 448. Mancavano
    // CINQUE PIXEL, e il giocatore restava fermo a un tile dal varco della vetta senza che
    // nulla, nel log, distinguesse quel caso da un percorso sbagliato.
    GUBBIO_ZIG_SU_128 GUBBIO_ZIG_SU_128 GUBBIO_ZIG_SU_32
    GUBBIO_IDLE_16
    // TRATTA 6 e 7 - Basilica e stradoni del Monte, verso ovest: 55 tile piu' 54, tutti in
    // discesa a tornanti. Un blocco solo: cio' che avanza della tratta 6 spinge gia' nella
    // direzione giusta della 7, invece di ributtare indietro il giocatore.
    GUBBIO_ZIG_SX_512
    GUBBIO_IDLE_16
    // TRATTA 8 - Duomo e Palazzo Ducale, verso ovest: 45 tile fino alla discesa in piazza.
    GUBBIO_ZIG_SX_128 GUBBIO_ZIG_SX_128
    GUBBIO_IDLE_256       // la macchina da scrivere percorre la prima battuta
    GUBBIO_TASTO_A GUBBIO_IDLE_64 GUBBIO_TASTO_A GUBBIO_IDLE_64
    GUBBIO_TASTO_A GUBBIO_IDLE_64 GUBBIO_TASTO_A GUBBIO_IDLE_64
    GUBBIO_TASTO_A GUBBIO_IDLE_64;

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
