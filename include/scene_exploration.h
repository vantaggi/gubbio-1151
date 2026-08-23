#ifndef SCENE_EXPLORATION_H
#define SCENE_EXPLORATION_H

#include "bn_camera_ptr.h"
#include "bn_sprite_text_generator.h"
#include "bn_optional.h"
#include "bn_regular_bg_ptr.h"

#include "bn_sprite_ptr.h"
#include "bn_vector.h"

#include "dialogue_box.h"
#include "dialogue_runner.h"
#include "dialogue_view.h"
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
    MapId _map_id = MapId::PIAZZA_GRANDE;
    bn::camera_ptr _camera;
    bn::regular_bg_ptr _ground;
    bn::optional<bn::regular_bg_ptr> _sky;
    OverworldPlayer _player;

    // Il motore del testo e il suo disegno vivono nella scena, non nel trampolino: la finestra
    // di dialogo e' un SOTTO-STATO dell'esplorazione, mai una scena a se' — altrimenti servirebbe
    // un quinto layer, che in Mode 0 non esiste.
    DialogueManager _dialogue;
    DialogueView _dialogue_view;
    DialogueRunner _runner;

    // Gli NPC dell'area, presi da NPCS[]. Otto e' il tetto del piano: piu' di otto personaggi
    // nella stessa schermata sarebbero comunque illeggibili a 16x16.
    bn::vector<bn::sprite_ptr, 8> _npc_sprites;

    // IL NOME DELL'AREA, mostrato entrando. Fino alla Sessione 21 il giocatore attraversava
    // quattordici aree senza che nessuna dicesse come si chiamava: il nome esisteva in
    // MAP_NAMES e finiva solo nel log, cioe' lo leggeva chi sviluppa e non chi gioca. In una
    // citta' vera che il gioco vuole far riconoscere, il nome del luogo E' contenuto.
    //
    // Sedici sprite bastano per "Piazza Quaranta Martiri", che e' il nome piu' lungo. Il
    // tetto vero non sono gli sprite ma le ALLOCAZIONI di tile OBJ: il testo di Butano ne
    // consuma una per sprite su un totale di 128 (BN_CFG_SPRITE_TILES_MAX_ITEMS), condivise
    // con la finestra di dialogo, che ne usa fino a 26.
    static constexpr int MAX_ETICHETTA_SPRITES = 16;
    static constexpr int ETICHETTA_FRAME = 110;   // poco meno di due secondi

    bn::sprite_text_generator _etichetta_generator;
    bn::vector<bn::sprite_ptr, MAX_ETICHETTA_SPRITES> _etichetta;
    int _etichetta_frame = ETICHETTA_FRAME;

    void _mostra_nome_area();
    void _aggiorna_etichetta();

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
