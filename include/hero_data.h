#ifndef HERO_DATA_H
#define HERO_DATA_H

#include "bn_string_view.h"

namespace gubbio {

struct HeroStats {
    bn::string_view name;
    int max_hp;
    int max_fervor;
    int physical_atk;
    int physical_def;
    int magic_resist;
    int faith_power;
    int flame_power;
    int speed;
};

// Dati canonici dei tre Santi Protagonisti (Sezione 5 GDD).
//
// `magic_resist` non e' censita nella Sezione 5: e' derivata applicando alla Difesa Fisica
// il rapporto Resistenza/Difesa della curva di crescita della Sezione 13B GDD
// (Ubaldo 26/16, Giorgio 14/28, Antonio 24/12).
//
// SCALA DEL FERVORE: `max_fervor` e' il pool ASSOLUTO del singolo Cero, perche' i costi di
// Boost della Sezione 20A GDD (25 / 50 / 100) sono valori assoluti. La "barra 0-100" della
// Sezione 12A e' invece la scala NORMALIZZATA di visualizzazione, quella che l'HUD della
// Sezione 14B.3 rende come "[F: 45%]": vedi `BattleUnit::fervor_percent()`.
// Vincolo invariante: ogni pool deve coprire 100 + il costo dell'abilita' firma dell'eroe,
// altrimenti la sua Mossa Suprema e' irraggiungibile. Verificato a compile time dalle
// `static_assert` in battle_scene.h.
constexpr HeroStats HEROES[] = {
    {"Sant'Ubaldo",   240, 180, 25, 45, 72, 95, 10, 30},
    {"San Giorgio",   380, 120, 90, 80, 40, 25,  0, 42},
    {"Sant'Antonio",  210, 210, 18, 28, 56, 20, 95, 38}
};

} // namespace gubbio

#endif // HERO_DATA_H
