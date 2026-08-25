#ifndef BATTLE_ANIMATOR_H
#define BATTLE_ANIMATOR_H

#include "bn_colors.h"
#include "bn_fixed.h"
#include "bn_keypad.h"
#include "bn_optional.h"
#include "bn_span.h"
#include "bn_sprite_animate_actions.h"
#include "bn_sprite_item.h"
#include "bn_sprite_palette_ptr.h"
#include "bn_sprite_palettes.h"
#include "bn_sprite_ptr.h"

#include "battle_anim_table.h"
#include "battle_events.h"

namespace gubbio {

// L'ANIMATORE DI BATTAGLIA (Passo 21 del piano).
//
// COSA FA. Riproduce UN evento del registro (battle_events.h) alla volta: la posa dell'attore,
// il flash bianco sul bersaglio, l'affondo di chi colpisce, lo scossone di chi incassa.
//
// COSA NON FA, ed e' altrettanto importante. Non decide QUANDO un evento comincia e finisce:
// quello lo sa gia' la macchina a stati, che nello stato PLAY_ROUND_ANIMATIONS scorre il
// registro consumandone le durate. L'animatore viene pilotato da chi osserva quel cursore
// (oggi src/battle_hud.cpp) e non conosce ne' BattleSceneManager ne' l'HUD: dipende solo dalle
// due tabelle e da Butano. E' cio' che gli permette di essere letto e discusso da solo.
//
// --- PERCHE' UN SOLO ATTORE ANIMATO PER VOLTA -------------------------------------------------
//
// E' il vincolo di VRAM OBJ a decidere la forma di questa classe, non il gusto.
//
// Nove attori con un animate action CACHED ciascuno costerebbero, al caso peggiore, sei
// fotogrammi di tile ognuno: per i soli sprite 32x32 sono 6 x 512 B x 9 = circa 27 KB sui 32 KB
// di VRAM OBJ, prima dei ~40 sprite di testo dell'HUD e delle particelle. La via opposta —
// nove animate action NON cached — sostituirebbe il problema di spazio con nove flussi
// simultanei di release/create sull'allocatore best-fit dei tile, cioe' frammentazione a ogni
// cambio di fotogramma. Nessuna delle due sta in piedi.
//
// La regola adottata e' quella che la FSM a turni gia' impone da se': si riproduce un evento
// alla volta, quindi si anima un attore alla volta. Un unico `bn::sprite_cached_animate_action`
// da al massimo ANIM_MAX_CLIP_FRAMES fotogrammi, costruito all'inizio dell'evento e distrutto
// alla fine. Il tetto e' scritto qui sotto come static_assert, non come buon proposito.
//
// --- LIMITE NOTO: IL FLASH E' PER-PALETTE, NON PER-SPRITE -------------------------------------
//
// `bn::sprite_palette_ptr::set_fade` tinge la PALETTE, e due nemici dello stesso tipo nascono
// dallo stesso `sprite_item`, quindi condividono la palette: colpire un Fante fa lampeggiare
// anche l'altro Fante. Non e' un difetto di questo file, e' il modello di colore del GBA. Le due
// vie d'uscita, il giorno in cui dara' fastidio: una palette per slot (costo d'arte, tocca il
// generatore) oppure il fade hardware BLDY con `set_blending_enabled` per sprite (costo: un
// secondo meccanismo globale da coordinare con la dissolvenza di scena). Finche' resta cosi', e'
// scritto qui e non scoperto guardando lo schermo.

// --- BUDGET DI VRAM OBJ, DERIVATO DALLE TABELLE -----------------------------------------------
//
// I fogli sono 4bpp per regola di progetto (ogni .json di graphics/ dichiara `bpp_mode`), quindi
// un tile costa 32 byte. Il caso peggiore non e' il fotogramma piu' grande ne' la posa piu'
// lunga: e' il loro prodotto, ed e' Corrado (64x64 = 64 tile = 2 KB a fotogramma).

inline constexpr int BYTES_PER_TILE_4BPP = 32;

[[nodiscard]] constexpr int anim_frame_bytes(int actor)
{
    const AnimSheet& sheet = ANIM_SHEETS[actor];
    return (int(sheet.width) / 8) * (int(sheet.frame_height) / 8) * BYTES_PER_TILE_4BPP;
}

[[nodiscard]] constexpr int anim_max_clip_frames(int actor)
{
    int massimo = 0;

    for(int pose = 0; pose < ANIM_POSE_COUNT; ++pose)
    {
        const int frames = int(ANIM_CLIPS[actor][pose].frame_count);

        if(frames > massimo)
        {
            massimo = frames;
        }
    }

    return massimo;
}

[[nodiscard]] constexpr int anim_vram_caso_peggiore()
{
    int massimo = 0;

    for(int actor = 0; actor < ANIM_ACTOR_COUNT; ++actor)
    {
        const int costo = anim_frame_bytes(actor) * anim_max_clip_frames(actor);

        if(costo > massimo)
        {
            massimo = costo;
        }
    }

    return massimo;
}

// I 32 KB di VRAM OBJ, spesi: residenti nella schermata di battaglia ci sono i 3 Ceri (1 KB), i
// 6 nemici (3 KB al peggio), le 6 barre e il cursore (~0,9 KB), i 9 gettoni della timeline
// (~1,2 KB) e il testo dell'HUD (~2 KB), cioe' poco piu' di 8 KB. Restano circa 24 KB: 12 e'
// meta' di quel margine, e lascia spazio alle particelle della Sez. 35 senza doverlo ricontare.
// Oggi il caso peggiore misura 10 KB (Corrado, 5 fotogrammi di ATTACK): il margine e' reale,
// non e' un tetto ritagliato sul valore corrente.
inline constexpr int ANIM_VRAM_BUDGET_BYTES = 12 * 1024;

static_assert(anim_vram_caso_peggiore() <= ANIM_VRAM_BUDGET_BYTES,
              "una posa costa piu' VRAM OBJ di quanta ne resti all'animatore: allungare una "
              "posa di Corrado non e' gratis, e la VRAM finita non da' un errore di "
              "compilazione ma sprite che spariscono a runtime");

// --- DURATE DEGLI EFFETTI ---------------------------------------------------------------------
//
// Sono in frame di gioco e devono stare DENTRO la durata dell'evento che le ospita
// (`event_duration_frames`, battle_events.h): un effetto piu' lungo del suo evento verrebbe
// tagliato a meta' dal cambio di evento, e si vedrebbe un attore che resta storto o una palette
// che resta bianca.

inline constexpr int LUNGE_FRAMES = 12;         // affondo: andata e ritorno
inline constexpr int LUNGE_PIXELS = 8;
inline constexpr int LUNGE_ATTACK_FRAMES = 4;   // frame dell'andata; il resto e' il rientro
inline constexpr int SHAKE_FRAMES = 10;
inline constexpr int SHAKE_PIXELS = 2;
inline constexpr int SHAKE_HALF_PERIOD = 2;     // frame per ogni mezza oscillazione
inline constexpr int FLASH_FRAMES = 8;
inline constexpr int FLASH_FRAMES_BREAK = 16;   // la rottura dello scudo e' il momento che il
                                                // giocatore cerca: dura il doppio

[[nodiscard]] constexpr int durata_flash(EventKind kind)
{
    return kind == EventKind::SHIELD_BREAK ? FLASH_FRAMES_BREAK : FLASH_FRAMES;
}

[[nodiscard]] constexpr bool flash_entro_le_durate()
{
    for(int i = 0; i < int(EventKind::COUNT); ++i)
    {
        const EventKind kind = EventKind(i);

        if(durata_flash(kind) > event_duration_frames(kind))
        {
            return false;
        }
    }

    return true;
}

static_assert(flash_entro_le_durate(),
              "un flash dura piu' del suo evento: la palette resterebbe tinta di bianco quando "
              "l'evento dopo comincia, e il colore sbagliato si trascinerebbe per tutto il round");

static_assert(LUNGE_FRAMES <= event_duration_frames(EventKind::HIT) &&
              LUNGE_FRAMES <= event_duration_frames(EventKind::SHIELD_BREAK),
              "l'affondo dura piu' del colpo che lo produce: l'attaccante resterebbe fermo "
              "fuori posto, a meta' della falcata, per tutto l'evento successivo");

// Le pose dei fogli di animazione devono stare anch'esse dentro l'evento che le ospita. E' un
// vincolo INCROCIATO fra due tabelle generate da due sorgenti diverse — le durate degli eventi
// stanno in battle_events.h, le durate delle pose escono da tools/make_placeholder_art.py — e
// nessuna delle due sa dell'altra: senza questo controllo, allungare una posa nel generatore
// Python romperebbe l'animazione qui, in silenzio.
[[nodiscard]] constexpr bool pose_entro_le_durate()
{
    for(int actor = 0; actor < ANIM_ACTOR_COUNT; ++actor)
    {
        const AnimActor a = AnimActor(actor);

        if(anim_has_pose(a, AnimPose::ATTACK) &&
           anim_pose_duration(a, AnimPose::ATTACK) > event_duration_frames(EventKind::HIT))
        {
            return false;
        }

        if(anim_has_pose(a, AnimPose::DEATH) &&
           anim_pose_duration(a, AnimPose::DEATH) > event_duration_frames(EventKind::DEFEAT))
        {
            return false;
        }

        if(anim_has_pose(a, AnimPose::HURT) &&
           anim_pose_duration(a, AnimPose::HURT) > event_duration_frames(EventKind::DEFEAT))
        {
            return false;
        }
    }

    return true;
}

static_assert(pose_entro_le_durate(),
              "una posa dura piu' dell'evento che la riproduce: si vedrebbe un attacco troncato "
              "a meta' o un caduto che torna in piedi prima di cadere");

// --- PASSO DI RIPRODUZIONE --------------------------------------------------------------------
//
// ATTENZIONE, VALORE DUPLICATO: lo stesso 4 vive in `_play_round_animations()` di
// src/battle_scene.cpp, che e' il file che possiede il tempo. Se i due divergono, le animazioni
// scorrono a una velocita' e il temporizzatore a un'altra: nessun crash, ma pose che si tagliano
// a meta'. La duplicazione esiste perche' il modello non puo' includere un header di
// presentazione; la sede giusta della costante e' battle_events.h, insieme alle durate.
//
// CONFLITTO DI INPUT, gia' a verbale nel piano: A e B sono assegnati tre volte (fast-forward,
// salto del typewriter, corsa/interazione). La regola presa: durante un dialogo in battaglia il
// fast-forward e' SOSPESO, e il box lo dichiara col proprio prompt.
inline constexpr int FAST_FORWARD_STEP = 4;

[[nodiscard]] inline int passo_riproduzione()
{
    return (bn::keypad::a_held() || bn::keypad::b_held()) ? FAST_FORWARD_STEP : 1;
}

// Chi partecipa a un evento. Lo sprite e' PRESTATO: `bn::sprite_ptr` e' un handle condiviso,
// copiarlo non crea un secondo sprite e non costa VRAM. `x`/`y` sono la posizione di RIPOSO in
// pixel di schermo Butano, quella a cui affondo e scossone devono riportare l'attore: l'animatore
// non la indovina dallo sprite, perche' leggerla mentre e' spostato la falserebbe.
struct AnimSubject
{
    bn::sprite_ptr sprite;
    const bn::sprite_item* item;   // per pescare i tile delle pose; puo' essere nullptr
    AnimActor kind;
    int x;
    int y;
};

class BattleAnimator
{

public:
    ~BattleAnimator()
    {
        // Un animatore che muore a meta' evento lascerebbe una palette bianca e uno sprite
        // fuori posto: sono stati GLOBALI dell'hardware, non muoiono con l'oggetto.
        end();
    }

    // Da chiamare quando comincia la fase di animazione di un round, PRIMA di qualunque flash.
    //
    // ORDINE DI RESET DELLE PALETTE. Il fade globale degli sprite (`bn::sprite_palettes`, usato
    // dalla dissolvenza d'ingresso via scene_fade) e il flash per-palette di questo animatore
    // sono due meccanismi diversi che il banco delle palette di Butano applica IN SEQUENZA sugli
    // stessi colori: un fade globale residuo non verrebbe sostituito dal flash, si sommerebbe.
    // Azzerarlo qui li tiene separati per costruzione.
    //
    // Perche' qui e non a ogni frame: azzerare il fade globale a ogni frame cancellerebbe la
    // dissolvenza d'ingresso della battaglia, che e' esattamente lo stesso registro e vive nei
    // 32 frame dello stato INTRO_FADE_IN.
    void begin_round()
    {
        bn::sprite_palettes::set_fade_intensity(0);
    }

    // Comincia la riproduzione di un evento. Un eventuale evento in corso viene chiuso prima:
    // con il fast-forward attivo due eventi possono cadere nello stesso frame.
    //
    // `attore` viene usato solo dagli eventi che hanno un attaccante (HIT, SHIELD_BREAK); per
    // gli altri il chiamante puo' passare il bersaglio anche come attore.
    void begin(const BattleEvent& evento, const AnimSubject& attore, const AnimSubject& bersaglio)
    {
        end();

        _attore = attore;
        _bersaglio = bersaglio;
        _frame = 0;
        _in_riproduzione = true;
        _durata_flash = durata_flash(evento.kind);

        switch(evento.kind)
        {
        case EventKind::HIT:
        case EventKind::SHIELD_BREAK:
            _affondo = true;
            _scossone = true;
            _avvia_clip(attore, AnimPose::ATTACK);
            break;

        case EventKind::DEFEAT:
            _scossone = true;
            // Gli eroi non hanno la posa DEATH: svengono, non muoiono (Sez. 20B GDD). Per loro
            // la caduta e' resa dalla posa HURT, che esiste per tutti.
            _avvia_clip(bersaglio, anim_has_pose(bersaglio.kind, AnimPose::DEATH)
                                   ? AnimPose::DEATH : AnimPose::HURT);
            break;

        case EventKind::BURN_TICK:
            _scossone = true;
            break;

        case EventKind::BARRIER_ABSORB:
        case EventKind::GUARD_REDIRECT:
        case EventKind::FERVOR_GAIN:
            // Nessun movimento: sono eventi che si leggono dal colore, non dalla posa. Il
            // Fervore di San Giorgio lampeggia su chi lo guadagna, che qui e' il bersaglio.
            break;

        default:
            break;
        }

        _applica_flash();
    }

    // Un passo di riproduzione. `passo` e' 1, oppure FAST_FORWARD_STEP quando il giocatore
    // tiene A o B: gli effetti si comprimono insieme al temporizzatore invece di scorrere a
    // velocita' diversa da esso.
    void tick(int passo)
    {
        for(int i = 0; i < passo; ++i)
        {
            _avanza_un_frame();
        }
    }

    // Chiude l'evento in corso: posizioni di riposo, palette pulita, animate action distrutto.
    // Idempotente: chiamarla due volte non fa nulla la seconda.
    void end()
    {
        if(! _in_riproduzione)
        {
            return;
        }

        // Prima si distrugge l'animate action, poi si rimette la posa: al contrario, i tile del
        // fotogramma IDLE verrebbero allocati mentre i sei della posa sono ancora in VRAM.
        _clip.reset();
        _ripristina_posa();
        _clip_item = nullptr;

        if(_attore)
        {
            _attore->sprite.set_position(_attore->x, _attore->y);
        }

        if(_bersaglio)
        {
            _bersaglio->sprite.set_position(_bersaglio->x, _bersaglio->y);

            bn::sprite_palette_ptr palette = _bersaglio->sprite.palette();
            palette.set_fade_intensity(0);
        }

        _attore.reset();
        _bersaglio.reset();
        _affondo = false;
        _scossone = false;
        _in_riproduzione = false;
        _frame = 0;
    }

    [[nodiscard]] bool is_playing() const
    {
        return _in_riproduzione;
    }

private:
    bn::optional<bn::sprite_cached_animate_action<ANIM_MAX_CLIP_FRAMES>> _clip;
    // Copia dell'handle dello sprite che porta la posa: serve DOPO la distruzione dell'animate
    // action, per riportarlo all'indice 0 (IDLE). L'action espone il proprio sprite in sola
    // lettura, e comunque non sopravvive al ripristino.
    bn::optional<bn::sprite_ptr> _clip_sprite;
    const bn::sprite_item* _clip_item = nullptr;
    AnimActor _clip_kind = AnimActor::UBALDO;
    int _durata_clip = 0;

    bn::optional<AnimSubject> _attore;
    bn::optional<AnimSubject> _bersaglio;

    int _frame = 0;
    int _durata_flash = 0;
    bool _affondo = false;
    bool _scossone = false;
    bool _in_riproduzione = false;

    void _avvia_clip(const AnimSubject& soggetto, AnimPose posa)
    {
        if(! soggetto.item || ! anim_has_pose(soggetto.kind, posa))
        {
            return;
        }

        const AnimClip& clip = anim_clip(soggetto.kind, posa);
        uint16_t indici[ANIM_MAX_CLIP_FRAMES];

        for(int i = 0; i < int(clip.frame_count); ++i)
        {
            indici[i] = uint16_t(anim_graphics_index(soggetto.kind, posa, i));
        }

        _clip_sprite = soggetto.sprite;
        _clip_item = soggetto.item;
        _clip_kind = soggetto.kind;
        _durata_clip = anim_pose_duration(soggetto.kind, posa);

        // `wait_updates` e' l'attesa FRA un cambio di tile e il successivo, quindi un fotogramma
        // dura `wait_updates + 1`: passare `frame_duration` allungherebbe ogni posa di un frame
        // per fotogramma, e la somma sforerebbe la durata dell'evento verificata qui sopra.
        _clip = bn::sprite_cached_animate_action<ANIM_MAX_CLIP_FRAMES>::once(
                soggetto.sprite, int(clip.frame_duration) - 1, soggetto.item->tiles_item(),
                bn::span<const uint16_t>(indici, int(clip.frame_count)));
    }

    void _ripristina_posa()
    {
        if(_clip_sprite && _clip_item)
        {
            // Indice 0 = IDLE fotogramma 0, invariante garantita da battle_anim_table.h. Senza
            // questo ripristino l'attore resterebbe per sempre nell'ultima posa dell'attacco.
            _clip_sprite->set_item(*_clip_item, anim_graphics_index(_clip_kind, AnimPose::IDLE, 0));
        }

        _clip_sprite.reset();
        _durata_clip = 0;
    }

    void _avanza_un_frame()
    {
        if(! _in_riproduzione)
        {
            return;
        }

        ++_frame;

        // `update()` di Butano asserisce su action gia' conclusa: il controllo di `done()` non e'
        // prudenza, e' il contratto.
        if(_clip && ! _clip->done())
        {
            _clip->update();
        }

        // Il ripristino avviene alla DURATA DELLA POSA e non su `done()`: `done()` diventa vero
        // nell'istante in cui l'ultimo fotogramma viene messo, quindi si vedrebbe per un frame
        // solo invece che per la sua durata.
        if(_clip && _durata_clip > 0 && _frame >= _durata_clip)
        {
            _clip.reset();
            _ripristina_posa();
        }

        _applica_affondo();
        _applica_scossone();
        _applica_flash();
    }

    void _applica_affondo()
    {
        if(! _affondo || ! _attore || ! _bersaglio || _frame > LUNGE_FRAMES)
        {
            return;
        }

        // Verso il bersaglio: i Ceri stanno a destra e i nemici a sinistra, quindi il segno esce
        // dalle posizioni e non da una tabella che potrebbe smentirle.
        const int direzione = _bersaglio->x > _attore->x ? 1 : -1;
        int offset = 0;

        if(_frame < LUNGE_ATTACK_FRAMES)
        {
            offset = (LUNGE_PIXELS * _frame) / LUNGE_ATTACK_FRAMES;
        }
        else if(_frame < LUNGE_FRAMES)
        {
            offset = (LUNGE_PIXELS * (LUNGE_FRAMES - _frame)) / (LUNGE_FRAMES - LUNGE_ATTACK_FRAMES);
        }

        _attore->sprite.set_position(_attore->x + direzione * offset, _attore->y);
    }

    void _applica_scossone()
    {
        if(! _scossone || ! _bersaglio || _frame > SHAKE_FRAMES)
        {
            return;
        }

        const int offset = _frame < SHAKE_FRAMES
                ? (((_frame / SHAKE_HALF_PERIOD) % 2) == 0 ? SHAKE_PIXELS : -SHAKE_PIXELS)
                : 0;

        _bersaglio->sprite.set_position(_bersaglio->x + offset, _bersaglio->y);
    }

    void _applica_flash()
    {
        if(! _bersaglio || _frame > _durata_flash)
        {
            return;
        }

        // Intensita' che scende da piena a zero: il colpo si vede nell'istante in cui arriva, e
        // il colore torna quello vero da se'. L'unica conversione a `bn::fixed` sta qui.
        const int residuo = _durata_flash - _frame;
        bn::sprite_palette_ptr palette = _bersaglio->sprite.palette();
        palette.set_fade(bn::colors::white, bn::fixed(residuo) / _durata_flash);
    }
};

} // namespace gubbio

#endif // BATTLE_ANIMATOR_H
