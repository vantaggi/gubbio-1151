#ifndef SCENE_H
#define SCENE_H

#include "map_id.h"

namespace gubbio {

// Contratto comune delle scene, come prescritto dalla skill `butano-gba-dev`.
//
// PERCHE' IL DISTRUTTORE NON E' VIRTUAL. La skill mostra `virtual ~Scene() = default;`, ma su
// questo progetto quella forma entrerebbe in conflitto con la politica zero-heap di AGENTS.md:
// un distruttore virtuale fa emettere a GCC anche il *deleting destructor* (slot D0 della
// vtable), che referenzia `operator delete` e lo trascina nella ROM — dove il gate
// `tools/check_zero_heap.sh` lo intercetterebbe come violazione.
//
// La forma corretta e' quella della linea guida C.35: distruttore **non virtuale e protected**.
// E' legittima qui perche' le scene vivono sullo stack di `main` e non vengono MAI distrutte
// attraverso un puntatore alla base; `protected` rende quell'errore impossibile da scrivere.
// Si ottiene cosi' l'unico valore reale della classe base — l'imposizione del contratto — senza
// pagarne il costo.
//
// Ogni scena concreta implementa `run()`, che contiene il ciclo obbligatorio di AGENTS.md
// (`while(!uscita) { update(); bn::core::update(); }`) e ritorna la scena successiva.

// Punto d'ingresso richiesto alla scena entrante.
enum class SceneId : uint8_t
{
    NONE = 0,        // nessuna transizione: la scena corrente prosegue
    EXPLORATION,     // esplorazione di una mappa (Sez. 21 GDD)
    BATTLE,          // schermata di combattimento (Sez. 14B.3 GDD)
    GAME_OVER
};

// Cosa una scena chiede al dispatcher quando termina. Aggregato POD: nessuna allocazione,
// nessun costruttore, copiabile in un registro.
struct SceneRequest
{
    SceneId id;
    // Significato del parametro secondo `id`:
    //   EXPLORATION -> MapId dell'area da caricare
    //   BATTLE      -> indice dell'incontro in ENCOUNTERS[]
    //   GAME_OVER   -> ignorato
    int parameter;

    [[nodiscard]] static SceneRequest none() { return SceneRequest{SceneId::NONE, 0}; }

    [[nodiscard]] static SceneRequest exploration(MapId map)
    {
        return SceneRequest{SceneId::EXPLORATION, int(map)};
    }

    [[nodiscard]] static SceneRequest battle(int encounter_id)
    {
        return SceneRequest{SceneId::BATTLE, encounter_id};
    }
};

class Scene
{
public:
    Scene(const Scene&) = delete;
    Scene& operator=(const Scene&) = delete;

    // Esegue la scena fino alla sua conclusione e dichiara cosa deve succedere dopo.
    [[nodiscard]] virtual SceneRequest run() = 0;

protected:
    Scene() = default;

    // Non virtuale e protected di proposito: vedi il commento in testa al file.
    ~Scene() = default;
};

} // namespace gubbio

#endif // SCENE_H
