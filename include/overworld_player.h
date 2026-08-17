#ifndef OVERWORLD_PLAYER_H
#define OVERWORLD_PLAYER_H

#include "bn_camera_ptr.h"
#include "bn_sprite_ptr.h"
#include "bn_sprite_tiles_ptr.h"
#include "bn_vector.h"

#include "map_data.h"

namespace gubbio {

// Il personaggio giocante nell'esplorazione (Sez. 21D GDD).
//
// POSIZIONE IN `int` PIXEL, non in `bn::fixed_point`. La velocita' e' intera (1 px/frame, 2 in
// corsa), la collisione lavora in tile e i trigger sul punto centrale dei piedi: nessun
// consumatore chiede il sub-pixel. In cambio, `bn::fixed` porterebbe due trappole — i
// costruttori impliciti da `float`/`double`, e l'ambiguita' dello `>> 3`, che su un `bn::fixed`
// opera sul valore grezzo a 12 bit di frazione, cioe' un errore di fattore 4096.
// `bn::fixed` resta riservato alla camera, se e quando servira' lo smorzamento.

enum class Direction : uint8_t { DOWN = 0, UP = 1, LEFT = 2, RIGHT = 3, COUNT = 4 };

// Il foglio `overworld_ubaldo` e' ordinato per direzione, 4 fotogrammi ciascuna.
inline constexpr int WALK_FRAMES_PER_DIRECTION = 4;
inline constexpr int WALK_FRAME_COUNT = int(Direction::COUNT) * WALK_FRAMES_PER_DIRECTION;

// Frame di gioco per fotogramma di camminata: a 1 px/frame, un passo ogni 8 px percorsi.
inline constexpr int WALK_ANIM_PERIOD = 8;

inline constexpr int WALK_SPEED_PX = 1;
inline constexpr int RUN_SPEED_PX = 2;

// Hitbox 12x8 ancorata ai piedi, e NON il bounding box 16x16 della Sez. 21D: con un riquadro
// alto 16 centrato sullo sprite, per posare il centro sul portone dei Consoli (y=18) il bordo
// superiore ricadrebbe su y=17, che la griglia restituisce come muro — il portone sarebbe
// LETTERALMENTE irraggiungibile. Un personaggio visto dall'alto collide con i piedi, non con
// la testa.
inline constexpr int HITBOX_HALF_WIDTH = 6;
inline constexpr int HITBOX_HEIGHT = 8;

class OverworldPlayer
{
public:
    OverworldPlayer(const MapDescriptor& map, int start_x, int start_y,
                    const bn::camera_ptr& camera);

    // Legge il D-Pad e prova a muoversi. Ritorna true se la posizione e' cambiata.
    bool update();

    [[nodiscard]] int x() const { return _x; }
    [[nodiscard]] int y() const { return _y; }
    [[nodiscard]] Direction direction() const { return _direction; }

    // Il tile sotto il punto centrale dei piedi: e' su questo, e su nient'altro, che i trigger
    // vengono valutati. Usare l'intera hitbox farebbe scattare una transizione mentre si passa
    // di striscio accanto a una porta.
    [[nodiscard]] uint8_t tile_under_feet() const { return _map.tile_at_px(_x, _y); }

    void set_position(int new_x, int new_y);

private:
    const MapDescriptor& _map;
    int _x;
    int _y;
    Direction _direction;
    int _anim_counter;
    int _anim_frame;

    // I 16 fotogrammi sono creati UNA VOLTA e tenuti vivi: cambiare direzione e' poi un
    // `set_tiles` che non alloca nulla. La forma ingenua — ricreare l'animazione a ogni cambio
    // di direzione — farebbe una release+create sull'allocatore best-fit a ogni fotogramma e a
    // ogni cambio di direzione, e in movimento diagonale il cambio e' continuo: frammentazione
    // progressiva della VRAM OBJ. Costo di tenerli tutti: 16 x 16x16 4bpp = 2 KB su 32 KB.
    bn::vector<bn::sprite_tiles_ptr, WALK_FRAME_COUNT> _frames;
    bn::sprite_ptr _sprite;

    // L'hitbox e' libera nella posizione data? Campiona l'INTERVALLO di tile coperto (al piu'
    // 3x2 celle) e non i quattro angoli: con celle da 8 px e una scatola da 12x8, un ostacolo
    // largo un tile puo' stare interamente fra i quattro angoli e non essere visto.
    [[nodiscard]] bool _box_free(int cx, int cy) const;

    void _apply_sprite_position();
    void _advance_animation(bool moving);
};

} // namespace gubbio

#endif // OVERWORLD_PLAYER_H
