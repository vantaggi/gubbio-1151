#ifndef BATTLE_ANIM_TABLE_H
#define BATTLE_ANIM_TABLE_H

// GENERATO DA tools/make_placeholder_art.py - non modificare a mano.
//
// Dove stanno le pose dentro i fogli di graphics/*.bmp. La tabella e' derivata dalle
// STESSE liste di keyframe da cui escono i .bmp: e' l'unico modo perche' un ritocco
// all'animazione non possa lasciare indietro gli indici che il C++ usa per pescarla.
//
// I fogli sono strisce verticali: l'indice grafico di Butano scorre dall'alto al basso,
// un fotogramma per cella. Non costano VRAM: `create_sprite` copia in OBJ VRAM il solo
// fotogramma richiesto, il resto resta in ROM.

#include <stdint.h>

namespace gubbio
{

enum class AnimActor : uint8_t
{
    UBALDO = 0,       // graphics/ubaldo.bmp, 16x672
    GIORGIO = 1,       // graphics/giorgio.bmp, 32x608
    ANTONIO = 2,       // graphics/antonio.bmp, 16x672
    ENEMY_FANTE = 3,       // graphics/enemy_fante.bmp, 32x448
    ENEMY_BALESTRIERE = 4,       // graphics/enemy_balestriere.bmp, 32x448
    ENEMY_CORRADO = 5,       // graphics/enemy_corrado.bmp, 64x1216
};

inline constexpr int ANIM_ACTOR_COUNT = 6;

// L'ordine e' quello di POSE_ORDER nel generatore, ed e' anche l'ordine in cui le pose
// si succedono dentro il foglio. Non tutti gli attori hanno tutte le pose: gli eroi non
// hanno DEATH (svengono, non muoiono - Sez. 20B), i nemici non hanno VICTORY.
enum class AnimPose : uint8_t
{
    IDLE = 0,
    ATTACK = 1,
    CAST = 2,
    HURT = 3,
    VICTORY = 4,
    DEATH = 5,
};

inline constexpr int ANIM_POSE_COUNT = 6;

// Una posa assente ha frame_count == 0: chiederla e' un errore del chiamante, non un
// caso da disegnare. Usare anim_has_pose() prima.
struct AnimClip
{
    uint16_t first_frame;
    uint8_t frame_count;
    uint8_t frame_duration;    // frame di gioco per fotogramma
};

struct AnimSheet
{
    uint16_t width;
    uint16_t frame_height;
    uint16_t total_frames;
};

inline constexpr AnimSheet ANIM_SHEETS[ANIM_ACTOR_COUNT] = {
    { 16, 32, 21 },    // ubaldo
    { 32, 32, 19 },    // giorgio
    { 16, 32, 21 },    // antonio
    { 32, 32, 14 },    // enemy_fante
    { 32, 32, 14 },    // enemy_balestriere
    { 64, 64, 19 },    // enemy_corrado
};

inline constexpr AnimClip ANIM_CLIPS[ANIM_ACTOR_COUNT][ANIM_POSE_COUNT] = {
    // ubaldo
    { { 0, 4, 14 }, { 4, 5, 4 }, { 9, 5, 6 }, { 14, 3, 5 }, { 17, 4, 10 }, { 0, 0, 0 } },
    // giorgio
    { { 0, 4, 14 }, { 4, 5, 4 }, { 9, 4, 6 }, { 13, 3, 5 }, { 16, 3, 10 }, { 0, 0, 0 } },
    // antonio
    { { 0, 4, 14 }, { 4, 5, 4 }, { 9, 5, 6 }, { 14, 3, 5 }, { 17, 4, 10 }, { 0, 0, 0 } },
    // enemy_fante
    { { 0, 4, 14 }, { 4, 4, 4 }, { 0, 0, 0 }, { 8, 3, 5 }, { 0, 0, 0 }, { 11, 3, 8 } },
    // enemy_balestriere
    { { 0, 4, 14 }, { 4, 4, 4 }, { 0, 0, 0 }, { 8, 3, 5 }, { 0, 0, 0 }, { 11, 3, 8 } },
    // enemy_corrado
    { { 0, 4, 14 }, { 4, 5, 4 }, { 9, 4, 6 }, { 13, 3, 5 }, { 0, 0, 0 }, { 16, 3, 8 } },
};

[[nodiscard]] constexpr const AnimClip& anim_clip(AnimActor actor, AnimPose pose)
{
    return ANIM_CLIPS[int(actor)][int(pose)];
}

[[nodiscard]] constexpr bool anim_has_pose(AnimActor actor, AnimPose pose)
{
    return ANIM_CLIPS[int(actor)][int(pose)].frame_count > 0;
}

// Indice grafico da passare a bn::sprite::set_item / set_tiles.
[[nodiscard]] constexpr int anim_graphics_index(AnimActor actor, AnimPose pose, int frame)
{
    return int(ANIM_CLIPS[int(actor)][int(pose)].first_frame) + frame;
}

// Durata totale della posa in frame di gioco: quanto deve attendere il temporizzatore
// dello stato PLAY_ROUND_ANIMATIONS del Passo 20 prima di passare all'evento dopo.
[[nodiscard]] constexpr int anim_pose_duration(AnimActor actor, AnimPose pose)
{
    const AnimClip& clip = ANIM_CLIPS[int(actor)][int(pose)];
    return int(clip.frame_count) * int(clip.frame_duration);
}

// Le pose in fila senza buchi ne' sovrapposizioni, e la fila che copre tutto il foglio.
// Un buco qui significa fotogrammi in ROM che nessuna posa nomina; una sovrapposizione
// significa due pose che si contendono le stesse celle.
[[nodiscard]] constexpr bool anim_clips_are_contiguous(int actor)
{
    int next = 0;

    for(int pose = 0; pose < ANIM_POSE_COUNT; ++pose)
    {
        const AnimClip& clip = ANIM_CLIPS[actor][pose];

        if(clip.frame_count == 0)
        {
            if(clip.first_frame != 0 || clip.frame_duration != 0)
            {
                return false;      // posa assente ma descrittore non azzerato
            }

            continue;
        }

        if(int(clip.first_frame) != next)
        {
            return false;
        }

        next += int(clip.frame_count);
    }

    return next == int(ANIM_SHEETS[actor].total_frames);
}

// Misure OBJ legali del GBA, applicate al FOTOGRAMMA e non al foglio.
[[nodiscard]] constexpr bool anim_frame_size_is_legal(int width, int height)
{
    return (width == 8  && (height == 8 || height == 16 || height == 32)) ||
           (width == 16 && (height == 8 || height == 16 || height == 32)) ||
           (width == 32 && (height == 8 || height == 16 || height == 32 || height == 64)) ||
           (width == 64 && (height == 32 || height == 64));
}

// -------------------------------------------------------------------------------------
// Le invarianti. Sono le stesse di _verifica_tabelle() in tools/make_placeholder_art.py:
// se una delle due sponde cede, il foglio .bmp e questa tabella hanno gia' divergiuto.
// -------------------------------------------------------------------------------------

// --- ubaldo ---
static_assert(ANIM_CLIPS[0][int(AnimPose::IDLE)].first_frame == 0 &&
              ANIM_CLIPS[0][int(AnimPose::IDLE)].frame_count > 0,
              "ubaldo: l'indice grafico 0 non e' IDLE fotogramma 0. battle_hud.cpp crea gli sprite con create_sprite(x, y), che usa l'indice 0 senza dirlo: ogni combattente nascerebbe nella posa sbagliata.");
static_assert(anim_clips_are_contiguous(0),
              "ubaldo: le pose non coprono il foglio senza buchi. Il .bmp e questa tabella non descrivono piu' lo stesso file.");
static_assert(int(ANIM_SHEETS[0].total_frames) * int(ANIM_SHEETS[0].frame_height) == 672,
              "ubaldo: il foglio non e' alto 672 px come prescrive il Passo 19 del piano.");
static_assert(anim_frame_size_is_legal(ANIM_SHEETS[0].width, ANIM_SHEETS[0].frame_height),
              "ubaldo: il fotogramma non e' una misura OBJ del GBA, l'hardware non saprebbe disegnarlo.");

// --- giorgio ---
static_assert(ANIM_CLIPS[1][int(AnimPose::IDLE)].first_frame == 0 &&
              ANIM_CLIPS[1][int(AnimPose::IDLE)].frame_count > 0,
              "giorgio: l'indice grafico 0 non e' IDLE fotogramma 0. battle_hud.cpp crea gli sprite con create_sprite(x, y), che usa l'indice 0 senza dirlo: ogni combattente nascerebbe nella posa sbagliata.");
static_assert(anim_clips_are_contiguous(1),
              "giorgio: le pose non coprono il foglio senza buchi. Il .bmp e questa tabella non descrivono piu' lo stesso file.");
static_assert(int(ANIM_SHEETS[1].total_frames) * int(ANIM_SHEETS[1].frame_height) == 608,
              "giorgio: il foglio non e' alto 608 px come prescrive il Passo 19 del piano.");
static_assert(anim_frame_size_is_legal(ANIM_SHEETS[1].width, ANIM_SHEETS[1].frame_height),
              "giorgio: il fotogramma non e' una misura OBJ del GBA, l'hardware non saprebbe disegnarlo.");

// --- antonio ---
static_assert(ANIM_CLIPS[2][int(AnimPose::IDLE)].first_frame == 0 &&
              ANIM_CLIPS[2][int(AnimPose::IDLE)].frame_count > 0,
              "antonio: l'indice grafico 0 non e' IDLE fotogramma 0. battle_hud.cpp crea gli sprite con create_sprite(x, y), che usa l'indice 0 senza dirlo: ogni combattente nascerebbe nella posa sbagliata.");
static_assert(anim_clips_are_contiguous(2),
              "antonio: le pose non coprono il foglio senza buchi. Il .bmp e questa tabella non descrivono piu' lo stesso file.");
static_assert(int(ANIM_SHEETS[2].total_frames) * int(ANIM_SHEETS[2].frame_height) == 672,
              "antonio: il foglio non e' alto 672 px come prescrive il Passo 19 del piano.");
static_assert(anim_frame_size_is_legal(ANIM_SHEETS[2].width, ANIM_SHEETS[2].frame_height),
              "antonio: il fotogramma non e' una misura OBJ del GBA, l'hardware non saprebbe disegnarlo.");

// --- enemy_fante ---
static_assert(ANIM_CLIPS[3][int(AnimPose::IDLE)].first_frame == 0 &&
              ANIM_CLIPS[3][int(AnimPose::IDLE)].frame_count > 0,
              "enemy_fante: l'indice grafico 0 non e' IDLE fotogramma 0. battle_hud.cpp crea gli sprite con create_sprite(x, y), che usa l'indice 0 senza dirlo: ogni combattente nascerebbe nella posa sbagliata.");
static_assert(anim_clips_are_contiguous(3),
              "enemy_fante: le pose non coprono il foglio senza buchi. Il .bmp e questa tabella non descrivono piu' lo stesso file.");
static_assert(int(ANIM_SHEETS[3].total_frames) * int(ANIM_SHEETS[3].frame_height) == 448,
              "enemy_fante: il foglio non e' alto 448 px come prescrive il Passo 19 del piano.");
static_assert(anim_frame_size_is_legal(ANIM_SHEETS[3].width, ANIM_SHEETS[3].frame_height),
              "enemy_fante: il fotogramma non e' una misura OBJ del GBA, l'hardware non saprebbe disegnarlo.");

// --- enemy_balestriere ---
static_assert(ANIM_CLIPS[4][int(AnimPose::IDLE)].first_frame == 0 &&
              ANIM_CLIPS[4][int(AnimPose::IDLE)].frame_count > 0,
              "enemy_balestriere: l'indice grafico 0 non e' IDLE fotogramma 0. battle_hud.cpp crea gli sprite con create_sprite(x, y), che usa l'indice 0 senza dirlo: ogni combattente nascerebbe nella posa sbagliata.");
static_assert(anim_clips_are_contiguous(4),
              "enemy_balestriere: le pose non coprono il foglio senza buchi. Il .bmp e questa tabella non descrivono piu' lo stesso file.");
static_assert(int(ANIM_SHEETS[4].total_frames) * int(ANIM_SHEETS[4].frame_height) == 448,
              "enemy_balestriere: il foglio non e' alto 448 px come prescrive il Passo 19 del piano.");
static_assert(anim_frame_size_is_legal(ANIM_SHEETS[4].width, ANIM_SHEETS[4].frame_height),
              "enemy_balestriere: il fotogramma non e' una misura OBJ del GBA, l'hardware non saprebbe disegnarlo.");

// --- enemy_corrado ---
static_assert(ANIM_CLIPS[5][int(AnimPose::IDLE)].first_frame == 0 &&
              ANIM_CLIPS[5][int(AnimPose::IDLE)].frame_count > 0,
              "enemy_corrado: l'indice grafico 0 non e' IDLE fotogramma 0. battle_hud.cpp crea gli sprite con create_sprite(x, y), che usa l'indice 0 senza dirlo: ogni combattente nascerebbe nella posa sbagliata.");
static_assert(anim_clips_are_contiguous(5),
              "enemy_corrado: le pose non coprono il foglio senza buchi. Il .bmp e questa tabella non descrivono piu' lo stesso file.");
static_assert(int(ANIM_SHEETS[5].total_frames) * int(ANIM_SHEETS[5].frame_height) == 1216,
              "enemy_corrado: il foglio non e' alto 1216 px come prescrive il Passo 19 del piano.");
static_assert(anim_frame_size_is_legal(ANIM_SHEETS[5].width, ANIM_SHEETS[5].frame_height),
              "enemy_corrado: il fotogramma non e' una misura OBJ del GBA, l'hardware non saprebbe disegnarlo.");

// Nessuna posa oltre i fotogrammi che l'animatore del Passo 21 puo' tenere: uno solo,
// cached, bn::sprite_animate_action<6>, per l'unico attore animato per volta.
inline constexpr int ANIM_MAX_CLIP_FRAMES = 6;

[[nodiscard]] constexpr bool anim_clips_fit_animator()
{
    for(int actor = 0; actor < ANIM_ACTOR_COUNT; ++actor)
    {
        for(int pose = 0; pose < ANIM_POSE_COUNT; ++pose)
        {
            if(int(ANIM_CLIPS[actor][pose].frame_count) > ANIM_MAX_CLIP_FRAMES)
            {
                return false;
            }
        }
    }

    return true;
}

static_assert(anim_clips_fit_animator(),
              "una posa supera i fotogrammi di bn::sprite_animate_action<6>: l'animatore del Passo 21 non potrebbe riprodurla senza allargare il tetto VRAM di ~3 KB gia' calcolato nel piano.");

// -------------------------------------------------------------------------------------
// Fogli a fotogrammi che NON sono attori: barre e gettoni della timeline. Stanno qui
// perche' sono le costanti che src/battle_hud.cpp e tools/preview_battle_screen.py
// duplicavano a mano - il difetto dichiarato nella Sessione 05 che il Passo 19 chiude.
// -------------------------------------------------------------------------------------

inline constexpr int HUD_BAR_FRAMES = 17;
inline constexpr int HUD_BAR_FERVOR_OFFSET = 17;   // secondo set, in oro
inline constexpr int HUD_BAR_WIDTH = 32;
inline constexpr int HUD_BAR_FRAME_HEIGHT = 8;
inline constexpr int TIMELINE_ICON_COUNT = 6;
inline constexpr int TIMELINE_ICON_SIZE = 16;

static_assert(HUD_BAR_FERVOR_OFFSET == HUD_BAR_FRAMES,
              "il set Fervore non comincia dove finisce quello HP: le barre d'oro mostrerebbero valori di HP.");
static_assert(anim_frame_size_is_legal(HUD_BAR_WIDTH, HUD_BAR_FRAME_HEIGHT) &&
              anim_frame_size_is_legal(TIMELINE_ICON_SIZE, TIMELINE_ICON_SIZE),
              "barra o gettone fuori dalle misure OBJ del GBA.");

}

#endif
