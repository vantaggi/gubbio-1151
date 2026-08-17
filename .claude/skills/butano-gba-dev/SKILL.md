---
name: butano-gba-dev
description: Linee guida avanzate, best practices e template per lo sviluppo di giochi GBA C++20 con Butano Engine per il progetto Gubbio 1151.
---

> **Nota:** copia operativa per Claude Code. La sorgente canonica e' `.agents/skills/butano-gba-dev/SKILL.md`
> (convenzione Antigravity): le due vanno tenute allineate a mano.

# Butano Engine & GBA Development Skill

Questa skill fornisce i pattern di riferimento per implementare scene, audio, FSM di battaglia e salvataggi persistenti in Butano Engine (C++20).

## 1. Pattern per Scene FSM
Ogni scena vive sullo **stack** del trampolino di `src/main.cpp`, come variabile di scope in uno
`switch` su `SceneId`. La forma canonica del progetto e' in [`include/scene.h`](../../../include/scene.h):

```cpp
class Scene {
public:
    [[nodiscard]] virtual SceneRequest run() = 0;   // possiede il ciclo di AGENTS.md 2.3
protected:
    Scene() = default;
    ~Scene() = default;        // NON virtuale e protected: linea guida C.35
};

class BattleScene final : public Scene { ... };     // `final` sulle scene concrete
```

**Il distruttore NON e' virtuale, ed e' `protected`** (rettifica della Sessione 09: fino ad
allora questa skill mostrava `virtual ~Scene() = default`). Un distruttore virtuale fa emettere
a GCC anche il *deleting destructor* — slot D0 della vtable — che referenzia `operator delete`
e lo trascina in ROM, dove `tools/check_zero_heap.sh` lo intercetta come violazione della
politica zero-heap. `protected` rende impossibile scrivere l'errore che il distruttore virtuale
proteggerebbe (distruzione tramite puntatore alla base), visto che le scene non sono mai
possedute da un puntatore. `final` sulle scene concrete evita `-Wnon-virtual-dtor`.

**Vietati per contratto, e verificati dal gate sui sorgenti:** `new`, `bn::unique_ptr`,
puntatori possedenti, factory che ritornano `Scene*`, tabelle di funzioni che costruiscono
scene. Al piu' UNA scena viva per volta, garantito dallo scope.

## 1-bis. Transizioni e tempo (Sessione 11)

* Tutte le transizioni fra scene sono **dissolvenze su palette**, con le primitive di
  [`include/scene_fade.h`](../../../include/scene_fade.h) (`apply(0-100)`, `reset()`). Il
  *tempo* appartiene alla scena, che fa avanzare il proprio contatore: `scene_fade` non cicla.
* `reset()` e' obbligatoria all'uscita di ogni scena; ogni scena entrante applica il proprio
  fade **prima** del primo `core_update()`, altrimenti il suo primo fotogramma compare a piena
  luminosita' per poi rituffarsi nel nero.
* **Qualunque effetto affine e' una SCENA A SE'**, con teardown completo dei BG regolari, mai un
  sotto-stato: Boost MAX a schermo intero (Sez. 20A/28B), Battle Swirl d'ingresso (Sez. 35C),
  Cinematica 2 (Sez. 34B). In Mode 1 restano 2 BG regolari + 1 affine, e si perderebbero due
  layer proprio quando le risorse di due scene rischiano di coesistere.
* `bn::core::update()` si chiama in **un solo posto**, `include/game_clock.h`, che lo avvolge in
  `gubbio::core_update()` incrementando `playtime_frames`. Il gate fallisce la build se compare
  altrove.

## 2. Gestione Fervore & Shield Break
Formula del danno e calcolo Break:
- Se l'elemento/tipo colpo corrisponde alla debolezza del nemico: `shield_points--`.
- Quando `shield_points == 0`: lo stato del target passa a `StatusEffect::BREAK`.
- Moltiplicatori Fervor Boost:
  - Livello 0: Danno base 1.0x
  - Livello 1: 1.5x (Consuma 25 Fervore)
  - Livello 2: 2.0x / Doppio colpo (Consuma 50 Fervore)
  - Livello MAX: 3.5x + Abilità Speciale Cero (Consuma 100 Fervore)

## 3. Gestione Salvataggio FRAM (32 KB)
- Usare sempre Magic Header `char magic_header[4] = {'G', '1', '1', '5'};`
- Calcolare checksum prima della scrittura SRAM.
