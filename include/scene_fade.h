#ifndef SCENE_FADE_H
#define SCENE_FADE_H

namespace gubbio {

// Dissolvenza su palette: le PRIMITIVE, senza ciclo.
//
// PERCHE' NON C'E' UN `fade_in(frames)` CHE CICLA. La dissolvenza d'ingresso della battaglia e'
// gia' guidata dalla FSM verificata su emulatore: stato `INTRO_FADE_IN`, 32 frame, con il
// rintocco del Campanone al frame 0 (`src/battle_scene.cpp`, decisione della Sessione 06B) e
// letta dall'HUD via `battle.intro_progress()`. Una funzione che possedesse il proprio ciclo
// produrrebbe due dissolvenze sovrapposte, oppure imporrebbe di smontare una FSM che oggi
// funziona. Ogni scena continua quindi a far avanzare il proprio contatore e chiama `apply()`.
//
// REGOLA GENERALE (Passo 5 del piano, valida da qui in avanti): tutte le transizioni fra scene
// sono dissolvenze su palette. Qualunque effetto affine — Boost MAX "a schermo intero"
// (Sez. 20A/28B), Battle Swirl d'ingresso (Sez. 35C), Cinematica 2 (Sez. 34B) — e' una SCENA A
// SE' con teardown completo dei BG regolari, mai un sotto-stato: in Mode 1 restano 2 BG
// regolari + 1 affine, e si perderebbero due layer proprio nell'istante in cui le risorse di
// due scene rischiano di coesistere.
namespace scene_fade {

// Intensita' in percentuale: 0 = scena pienamente visibile, 100 = schermo nero.
// Scala intera come tutto il resto del progetto; la conversione a `bn::fixed` avviene una sola
// volta, dentro `apply()`.
inline constexpr int CLEAR  = 0;
inline constexpr int OPAQUE = 100;

void apply(int intensity_percent);

// Azzera la dissolvenza. OBBLIGATORIA all'uscita di ogni scena: `bn::bg_palettes::set_fade` e
// `bn::sprite_palettes::set_fade` sono stati GLOBALI dell'hardware, non proprieta' della scena
// che li ha impostati. Una scena che esce lasciando il fade a 100 consegna alla successiva uno
// schermo nero che nessuno sa piu' di dover schiarire; e il flash bianco per-palette del
// Passo 21 si sommerebbe a un fade residuo invece di sostituirlo.
void reset();

} // namespace scene_fade

} // namespace gubbio

#endif // SCENE_FADE_H
