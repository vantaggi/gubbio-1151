#include "scene_exploration.h"

#include "bn_display.h"
#include "bn_keypad.h"
#include "bn_log.h"
#include "bn_memory.h"
#include "bn_sprite_tiles.h"
#include "bn_sprites.h"

#include "game_clock.h"
#include "save_data.h"
#include "scene_fade.h"

namespace gubbio {

namespace {

// Dissolvenza d'ingresso dell'esplorazione. Piu' breve dei 32 frame della battaglia: entrare in
// una piazza non e' un evento drammatico, e un'attesa lunga a ogni porta si farebbe sentire.
constexpr int ENTRY_FADE_FRAMES = 20;
constexpr int EXIT_FADE_FRAMES = 16;

// Il cielo scorre a un quarto della camera. Il divisore e' una potenza di due di proposito:
// e' uno shift, non una divisione, in un calcolo che gira a ogni frame.
constexpr int PARALLAX_SHIFT = 2;

// Meta' schermo: la camera non puo' avvicinarsi al bordo della mappa piu' di cosi', altrimenti
// oltre il bordo comparirebbe il vuoto (o, peggio, il wrap del BG).
constexpr int CAMERA_MARGIN_X = 120;
constexpr int CAMERA_MARGIN_Y = 80;

[[nodiscard]] int clamp(int value, int low, int high)
{
    return value < low ? low : (value > high ? high : value);
}

// Posizione di comparsa: o lo spawn point richiesto dalla porta da cui si entra, o — con
// `ENTRY_POINT_RESUME` — la posizione esatta salvata su FRAM. Senza questa distinzione, caricare
// una partita salvata in mezzo alla piazza rispedirebbe il giocatore all'ingresso.
[[nodiscard]] SpawnPoint resolve_start_position(const MapDescriptor& map, const GameState& state)
{
    if(state.entry_point == ENTRY_POINT_RESUME)
    {
        return SpawnPoint{state.player_pos_x, state.player_pos_y};
    }

    const int index = state.entry_point < MAX_SPAWNS_PER_MAP ? state.entry_point : 0;
    return map.spawns[index];
}

} // namespace

ExplorationScene::ExplorationScene(GameState& state, const SceneRequest& request) :
    _state(state),
    _map(MAPS[request.parameter >= 0 && request.parameter < MAP_COUNT ? request.parameter : 0]),
    _camera(bn::camera_ptr::create(0, 0)),
    _ground(_map.ground->create_bg(0, 0)),
    _player(_map, resolve_start_position(_map, state).x, resolve_start_position(_map, state).y,
            _camera),
    _last_trigger_tile(0)
// NOTA: `resolve_start_position` e' chiamata due volte perche' la lista di inizializzazione non
// ammette una variabile intermedia. E' una funzione pura su due campi, valutata una volta per
// costruzione di scena: si e' preferito questo a un `_player` costruito in posizione fittizia e
// poi spostato, che lascerebbe per un istante un oggetto in uno stato che non significa nulla.
{
    BN_BASIC_ASSERT(_map.is_implemented(), "Mappa non ancora autorata");

    _state.set_map(MapId(request.parameter));

    _ground.set_camera(_camera);
    _ground.set_priority(2);

    if(_map.parallax)
    {
        // `create_bg_optional` e non `create_bg`: il cielo e' l'unica risorsa condizionale di
        // questa scena, e con quattro BG piu' i blocchi della scena uscente l'allocatore
        // best-fit puo' fallire per frammentazione anche con blocchi liberi a sufficienza.
        // Meglio un'area senza cielo che un assert davanti al giocatore.
        _sky = _map.parallax->create_bg_optional(0, 0);

        if(_sky)
        {
            _sky->set_priority(3);       // dietro a tutto
        }
        else
        {
            BN_LOG("ATTENZIONE: cielo non allocabile, si prosegue senza parallasse");
        }
    }

    _last_trigger_tile = _player.tile_under_feet();

    _update_camera();
    scene_fade::apply(scene_fade::OPAQUE);   // contratto d'ingresso: nero prima del primo update

    BN_LOG("=== ESPLORAZIONE: ", MAP_NAMES[request.parameter], " ===");
    BN_LOG("  comparsa a x ", _player.x(), " y ", _player.y(),
           " (entry point ", int(_state.entry_point), ")");
}

void ExplorationScene::_update_camera()
{
    // Camera rigida con clamping, senza smorzamento: e' la proposta del piano, ed e' anche
    // l'unica che non richiede `bn::fixed` per la posizione del giocatore.
    const int cam_x = clamp(_player.x(), CAMERA_MARGIN_X, _map.width_px() - CAMERA_MARGIN_X);
    const int cam_y = clamp(_player.y(), CAMERA_MARGIN_Y, _map.height_px() - CAMERA_MARGIN_Y);

    _camera.set_position(cam_x, cam_y);

    if(_sky)
    {
        // Il cielo NON e' agganciato alla camera: si muove a un quarto, ed e' il wrap hardware
        // del BG 256x256 a farlo sembrare infinito.
        _sky->set_position(-(cam_x >> PARALLAX_SHIFT), -(cam_y >> PARALLAX_SHIFT));
    }
}

bool ExplorationScene::_check_triggers(SceneRequest& out)
{
    const uint8_t tile = _player.tile_under_feet();

    if(tile == _last_trigger_tile)
    {
        return false;
    }

    _last_trigger_tile = tile;

    if(! maps::is_transition(tile))
    {
        return false;
    }

    for(const TriggerRule& rule : _map.triggers)
    {
        if(rule.scene == SceneId::NONE)
        {
            break;                      // fine dell'elenco
        }

        if(rule.tile_value != tile)
        {
            continue;
        }

        // Il punto di rientro va deciso QUI, da chi conosce la porta attraversata: la scena
        // entrante non ha modo di sapere da dove si arriva.
        _state.entry_point = rule.entry_point;
        _state.player_pos_x = int16_t(_player.x());
        _state.player_pos_y = int16_t(_player.y());

        BN_LOG("TRIGGER tile ", int(tile), " -> scena ", int(rule.scene),
               " parametro ", int(rule.parameter), " rientro su spawn ", int(rule.entry_point));

        out = SceneRequest{rule.scene, rule.parameter};
        return true;
    }

    BN_LOG("ATTENZIONE: tile di transizione ", int(tile), " senza regola in MAPS[]");
    return false;
}

SceneRequest ExplorationScene::run()
{
    SceneRequest next = SceneRequest::none();
    int entry_frame = 0;
    int peak_sprites = 0;

    while(true)
    {
        _player.update();
        _update_camera();

        // SALVATAGGIO su SELECT — punto di collaudo PROVVISORIO.
        // Il GDD prevede il salvataggio dal menu di pausa (Sez. 33A) e all'Eremo di
        // Sant'Ambrogio (Sez. 6); nessuno dei due esiste ancora. Senza un punto qualsiasi in cui
        // il gioco scriva davvero su FRAM, il formato del Passo 8 resterebbe codice mai eseguito
        // e il `.sav` resterebbe a zero byte. Da sostituire quando il menu di pausa arriva.
        if(bn::keypad::select_pressed())
        {
            // La posizione va registrata PRIMA di salvare, e con `ENTRY_POINT_RESUME`: chi
            // ricarica deve ricomparire dov'era, non all'ingresso dell'area.
            _state.player_pos_x = int16_t(_player.x());
            _state.player_pos_y = int16_t(_player.y());
            _state.entry_point = ENTRY_POINT_RESUME;

            if(! SaveSystem::save(SAVE_SLOT_DEFAULT, _state))
            {
                BN_LOG("SALVATAGGIO FALLITO: la rilettura di verifica non corrisponde");
            }
        }

        if(entry_frame <= ENTRY_FADE_FRAMES)
        {
            // La dissolvenza d'ingresso e' guidata dal contatore della scena, come in battaglia:
            // `scene_fade` offre solo le primitive, il tempo appartiene a chi lo scandisce.
            scene_fade::apply(scene_fade::OPAQUE -
                              (entry_frame * scene_fade::OPAQUE) / ENTRY_FADE_FRAMES);
            ++entry_frame;
        }
        else if(_check_triggers(next))
        {
            break;
        }

        peak_sprites = bn::max(peak_sprites, bn::sprites::used_items_count());
        core_update();
    }

    // Misure al picco, che sono i criteri di accettazione del Passo 14: senza numeri, "non ha
    // dato assert" non dice quanto margine e' rimasto.
    BN_LOG("USCITA esplorazione: sprite ", peak_sprites,
           " tile OBJ usati ", bn::sprite_tiles::used_tiles_count(),
           " disponibili ", bn::sprite_tiles::available_tiles_count(),
           " stack IWRAM ", bn::memory::used_stack_iwram());

    for(int frame = 0; frame <= EXIT_FADE_FRAMES; ++frame)
    {
        scene_fade::apply((frame * scene_fade::OPAQUE) / EXIT_FADE_FRAMES);
        core_update();
    }

    scene_fade::reset();
    return next;
}

} // namespace gubbio
