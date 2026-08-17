#include "overworld_player.h"

#include "bn_keypad.h"
#include "bn_sprite_items_overworld_ubaldo.h"

namespace gubbio {

namespace {

// Lo sprite e' 16x16 con i piedi sul bordo inferiore: il suo centro sta 8 px sopra il punto
// logico, che e' il centro dei piedi.
constexpr int SPRITE_FEET_OFFSET_Y = 8;

[[nodiscard]] int frame_index(Direction direction, int frame)
{
    return int(direction) * WALK_FRAMES_PER_DIRECTION + frame;
}

} // namespace

OverworldPlayer::OverworldPlayer(const MapDescriptor& map, int start_x, int start_y,
                                 const bn::camera_ptr& camera) :
    _map(map),
    _x(start_x),
    _y(start_y),
    _direction(Direction::DOWN),
    _anim_counter(0),
    _anim_frame(0),
    _sprite(bn::sprite_items::overworld_ubaldo.create_sprite(0, 0))
{
    const bn::sprite_tiles_item& tiles = bn::sprite_items::overworld_ubaldo.tiles_item();

    for(int i = 0; i < WALK_FRAME_COUNT; ++i)
    {
        _frames.push_back(tiles.create_tiles(i));
    }

    _sprite.set_tiles(_frames[frame_index(_direction, 0)]);
    _sprite.set_camera(camera);
    _sprite.set_bg_priority(1);
    _sprite.set_z_order(0);
    _apply_sprite_position();
}

bool OverworldPlayer::_box_free(int cx, int cy) const
{
    // Intervallo di tile coperto dalla scatola [cx-6, cx+5] x [cy-7, cy].
    const int left = cx - HITBOX_HALF_WIDTH;
    const int right = cx + HITBOX_HALF_WIDTH - 1;
    const int top = cy - HITBOX_HEIGHT + 1;
    const int bottom = cy;

    for(int ty = top >> 3; ty <= (bottom >> 3); ++ty)
    {
        for(int tx = left >> 3; tx <= (right >> 3); ++tx)
        {
            if(maps::is_solid(_map.tile_at(tx, ty)))
            {
                return false;
            }
        }
    }

    return true;
}

bool OverworldPlayer::update()
{
    // Corsa col tasto B (Sez. 21D). Velocita' da approvare: 1 px/frame a passo (60 px/s,
    // ~8,5 s per attraversare la piazza), 2 px/frame in corsa.
    const int speed = bn::keypad::b_held() ? RUN_SPEED_PX : WALK_SPEED_PX;

    int dx = 0;
    int dy = 0;

    if(bn::keypad::left_held())       { dx = -speed; _direction = Direction::LEFT; }
    else if(bn::keypad::right_held()) { dx = speed;  _direction = Direction::RIGHT; }

    if(bn::keypad::up_held())         { dy = -speed; _direction = Direction::UP; }
    else if(bn::keypad::down_held())  { dy = speed;  _direction = Direction::DOWN; }

    const int old_x = _x;
    const int old_y = _y;

    // ASSI SEPARATI, e non un singolo test sul punto d'arrivo diagonale: con il test unico,
    // camminare in diagonale contro un muro verticale blocca ANCHE la componente verticale, e
    // il personaggio si incolla all'ostacolo invece di scivolarci lungo.
    if(dx != 0 && _box_free(_x + dx, _y))
    {
        _x += dx;
    }

    if(dy != 0 && _box_free(_x, _y + dy))
    {
        _y += dy;
    }

    const bool moved = (_x != old_x) || (_y != old_y);
    _advance_animation(dx != 0 || dy != 0);

    if(moved)
    {
        _apply_sprite_position();
    }

    return moved;
}

void OverworldPlayer::_advance_animation(bool moving)
{
    if(! moving)
    {
        // Fermo: posa neutra della direzione corrente, contatore azzerato perche' il passo
        // riparta sempre dallo stesso fotogramma.
        _anim_counter = 0;
        _anim_frame = 0;
    }
    else if(++_anim_counter >= WALK_ANIM_PERIOD)
    {
        _anim_counter = 0;
        _anim_frame = (_anim_frame + 1) % WALK_FRAMES_PER_DIRECTION;
    }

    _sprite.set_tiles(_frames[frame_index(_direction, _anim_frame)]);
}

void OverworldPlayer::_apply_sprite_position()
{
    _sprite.set_position(_x, _y - SPRITE_FEET_OFFSET_Y);
}

void OverworldPlayer::set_position(int new_x, int new_y)
{
    _x = new_x;
    _y = new_y;
    _apply_sprite_position();
}

} // namespace gubbio
