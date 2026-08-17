#ifndef SCENE_EXPLORATION_H
#define SCENE_EXPLORATION_H

#include "bn_camera_ptr.h"
#include "bn_optional.h"
#include "bn_regular_bg_ptr.h"

#include "game_state.h"
#include "map_data.h"
#include "overworld_player.h"
#include "scene.h"

namespace gubbio {

// Esplorazione di un'area, PARAMETRIZZATA DA `MapId` — non una classe per mappa.
//
// Con le 8-9 aree della Sez. 38 e gli NPC censiti su cinque di esse, una classe-mappa per area
// sarebbe duplicazione insostenibile: tutto cio' che distingue un'area dall'altra vive in
// `MAPS[]` (map_data.h). Il file `scene_piazza_grande.h` che la roadmap prevedeva e' assorbito
// qui e in `map_data.h`.
//
// LAYER (Mode 0, quattro BG regolari disponibili):
//   priority 3  cielo in parallasse, mosso a un quarto della camera, con wrap hardware
//   priority 2  suolo, agganciato alla camera
//   priority 1  foreground, quando l'area ne ha uno (Piazza Grande oggi no)
//   priority 0  riservato all'interfaccia: finestra di dialogo, menu di pausa
// Il menu di pausa e' un SOTTO-STATO di questa scena, mai una scena a se' e mai un quinto
// layer: la Sez. 33B lo vorrebbe a schermo pieno su BG0+BG1, che sono gia' occupati.
class ExplorationScene final : public Scene
{
public:
    // `request.parameter` e' il `MapId` da caricare; il punto di comparsa viene da
    // `state.entry_point`.
    ExplorationScene(GameState& state, const SceneRequest& request);

    [[nodiscard]] SceneRequest run() override;

private:
    GameState& _state;
    const MapDescriptor& _map;
    bn::camera_ptr _camera;
    bn::regular_bg_ptr _ground;
    bn::optional<bn::regular_bg_ptr> _sky;
    OverworldPlayer _player;

    // Debounce dei trigger: preimpostato al tile di comparsa, cosi' che comparire accanto a una
    // porta non la attraversi nello stesso frame. Un trigger scatta solo quando il tile sotto i
    // piedi CAMBIA, non finche' ci si resta sopra.
    uint8_t _last_trigger_tile;

    void _update_camera();
    [[nodiscard]] bool _check_triggers(SceneRequest& out);
};

static_assert(sizeof(ExplorationScene) < 4096, "ExplorationScene troppo grande per lo stack di main");

} // namespace gubbio

#endif // SCENE_EXPLORATION_H
