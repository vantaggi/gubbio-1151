#include "scene_exploration.h"

#include "bn_display.h"
#include "bn_keypad.h"
#include "bn_log.h"
#include "bn_memory.h"
#include "bn_sprite_tiles.h"
#include "bn_sprites.h"

#include "game_clock.h"
#include "bn_sprite_items_overworld_npc.h"

#include "npc_registry.h"
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
    _map_id = MapId(request.parameter);

    _ground.set_camera(_camera);
    _ground.set_priority(2);

    // ANCORAGGIO. In Butano l'origine di un background e' il suo CENTRO, non l'angolo: un BG
    // lasciato a (0,0) mette il proprio pixel centrale sull'origine del mondo, e le coordinate
    // della mappa — che partono dall'angolo in alto a sinistra — finiscono spostate di meta'
    // immagine. Il giocatore camminava cosi' fuori dall'area disegnata, vedendo il cielo
    // attraverso le zone trasparenti.
    //
    // La misura si CHIEDE al background invece di scriverla qui. Finche' esisteva una costante
    // GROUND_IMAGE_SIZE valeva 512 su entrambi gli assi, il che era vero per una sola mappa:
    // Piazza Grande trasposta e' 256x512 e il Bargello 256x256, e con una costante quadrata
    // sarebbero finiti fuori centro di 128 px senza che nulla se ne accorgesse.
    _ground.set_position(_ground.dimensions().width() / 2, _ground.dimensions().height() / 2);

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

    // Gli NPC dell'area diventano sprite. La posizione viene dalla tabella in ROM: chi autora il
    // copione mette un personaggio in piazza scrivendo una riga, non toccando questa scena.
    for(int i = 0; i < int(NpcId::COUNT); ++i)
    {
        const NpcDef& npc = NPCS[i];

        if(npc.map != MapId(request.parameter) || _npc_sprites.full())
        {
            continue;
        }

        bn::sprite_ptr sprite = bn::sprite_items::overworld_npc.create_sprite(
            npc.tile_x * maps::TILE_SIZE_PX + maps::TILE_SIZE_PX / 2,
            npc.tile_y * maps::TILE_SIZE_PX - maps::TILE_SIZE_PX / 2, i);

        sprite.set_camera(_camera);
        sprite.set_bg_priority(1);
        _npc_sprites.push_back(bn::move(sprite));
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

        // La POSIZIONE nel log, non solo il tile. Senza, un varco che scatta subito dopo un
        // rientro e' indistinguibile da un varco che scatta dopo una camminata, e le due cose
        // hanno cause opposte: la prima e' un punto di rientro troppo vicino, la seconda no.
        BN_LOG("TRIGGER tile ", int(tile), " a x ", _player.x(), " y ", _player.y(),
               " -> scena ", int(rule.scene), " parametro ", int(rule.parameter),
               " rientro su spawn ", int(rule.entry_point));

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
        // Durante un dialogo il giocatore NON si muove e i trigger non vengono valutati: il box
        // e' un sotto-stato che sospende l'esplorazione. E' anche cio' che disinnesca il
        // conflitto sul tasto B, che nell'overworld e' la corsa e nel dialogo lo skip del
        // testo — le due modalita' non sono mai attive nello stesso frame.
        if(_dialogue.is_active())
        {
            const int riga_prima = _dialogue.active_row();
            _dialogue.update();
            _runner.update(_dialogue, _state);      // battuta chiusa -> apre la successiva
            _dialogue_view.update(_dialogue);

            if(_dialogue.is_active() && _dialogue.active_row() != riga_prima)
            {
                BN_LOG("  riga ", riga_prima, " completata (", _dialogue.visible_row(riga_prima).size(),
                       " byte), passa alla ", _dialogue.active_row());
            }

            // Misure al picco DEL DIALOGO: e' li' che il conteggio degli sprite e' massimo, ed
            // e' il tetto delle 128 allocazioni distinte — non i tile — quello che si tocca prima.
            peak_sprites = bn::max(peak_sprites, bn::sprites::used_items_count());

            if(! _dialogue.is_active())
            {
                BN_LOG("DIALOGO chiuso: sprite al picco ", peak_sprites,
                       " tile OBJ ", bn::sprite_tiles::used_tiles_count());
            }

            core_update();
            continue;
        }

        // INTERAZIONE: tasto A davanti a un NPC. Il trigger provvisorio su R della Sessione 13
        // e' stato rimosso — questa e' la forma definitiva prevista dal piano.
        if(bn::keypad::a_pressed())
        {
            const int indice = npc_at(_map_id, _player.x(), _player.y());

            if(indice < 0)
            {
                // A premuto e nessuno con cui parlare. Sembra un non-evento e invece e' la
                // traccia piu' utile che questa scena produca: sotto autotest e' l'unico modo di
                // accorgersi che la camminata scritta a mano ha mancato l'NPC, invece di leggere
                // l'assenza di "PARLA CON" e non sapere se il difetto sia nella traiettoria o
                // nel dialogo. Un oracolo che tace quando fallisce non e' un oracolo.
                BN_LOG("NESSUN INTERLOCUTORE a x ", _player.x(), " y ", _player.y());
            }
            else
            {
                const NpcDef& npc = NPCS[indice];
                const ScriptId script = npc_script_for_act(npc, _state.current_act);

                if(script != ScriptId::COUNT)
                {
                    _runner.start(script, _dialogue);
                    BN_LOG("PARLA CON ", npc.name, " (atto ", int(_state.current_act),
                           ", script ", int(script), ", ",
                           int(dialogue_script(script).line_count), " battute)");
                }
            }
        }

        _player.update();
        _update_camera();
        _dialogue_view.update(_dialogue);

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
