#ifndef SCENE_BATTLE_H
#define SCENE_BATTLE_H

#include "battle_hud.h"
#include "battle_scene.h"
#include "game_state.h"
#include "scene.h"

namespace gubbio {

// La battaglia vista dal dispatcher: una `Scene` che possiede il proprio modello e il proprio
// rendering, e che vive come VARIABILE DI SCOPE nello `switch` di `main.cpp`.
//
// PERCHE' ESISTE UN FACADE invece di far derivare `BattleSceneManager` da `Scene`. Il manager
// e' il modello — FSM, unita', formule — ed e' l'oggetto che `tests/test_battle_engine.py`
// rispecchia in Python. L'HUD e' il rendering, e possiede handle VRAM. Tenerli separati e
// riunirli qui significa che la VRAM dell'HUD nasce e muore con la scena: fino alla Sessione 10
// `main.cpp` costruiva l'HUD una volta e lo teneva vivo per sempre, quindi i suoi blocchi non
// sarebbero mai stati liberati da una transizione.
//
// PROPRIETA' DELLE RISORSE. Membri per valore, nessun puntatore, nessuna `bn::optional`: la
// distruzione e' garantita dallo scope: uscendo dallo `switch` il fondale, gli sprite e i testi
// tornano disponibili PRIMA che la scena entrante costruisca i propri. E' la sequenza
// "fade-nero -> distruggi -> costruisci -> fade-in" ottenuta per costruzione e non per
// disciplina; il tetto di 16 `bg_blocks` di Butano non ammette che i due insiemi coesistano.
// `final`: nessuno deriva da una scena concreta. Non e' decorazione — senza, GCC segnala
// (-Wnon-virtual-dtor) che una classe con metodi virtuali ha distruttore pubblico non virtuale,
// che e' esattamente la forma imposta da `Scene` per non trascinare `operator delete` in ROM.
// `final` toglie di mezzo il rischio (non esistono derivate da distruggere per puntatore)
// invece di zittire il warning.
class BattleScene final : public Scene
{
public:
    // `request.parameter` e' l'indice dell'incontro in ENCOUNTERS[].
    BattleScene(GameState& state, const SceneRequest& request);

    [[nodiscard]] SceneRequest run() override;

private:
    GameState& _state;
    BattleSceneManager _battle;
    BattleHud _hud;
};

// Le scene stanno sullo stack di `main`: la loro dimensione e' un vincolo, non un dettaglio.
// IWRAM statica occupata oggi ~11 KB, restano ~21 KB per lo stack. Se questa soglia viene
// superata, si spostano in EWRAM i buffer grandi della scena, non la scena intera.
static_assert(sizeof(BattleScene) < 4096, "BattleScene troppo grande per lo stack di main");

} // namespace gubbio

#endif // SCENE_BATTLE_H
