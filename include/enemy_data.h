#ifndef ENEMY_DATA_H
#define ENEMY_DATA_H

#include "bn_string_view.h"
#include "battle_engine.h"

namespace gubbio {

// Formazione nemica massima 3x2 (Sezione 12 GDD)
constexpr int MAX_ENEMIES_PER_ENCOUNTER = 6;

struct EnemyStats {
    bn::string_view name;
    int max_hp;
    int attack;
    int defense;
    int magic_power;
    int magic_resist;
    int speed;
    int shield_points;      // Punti Scudo 1-6 (Sezione 20A GDD)
    ElementType weakness;
    ElementType resistance;
};

enum class EnemyId { FANTE_DI_PERUGIA, BALESTRIERE_PESANTE, CORRADO_DI_SPOLETO, COUNT };

// HP calibrati sulla tabella di pacing della Sezione 13D GDD, che li esprime come
// percentuale degli HP di San Giorgio (380): Mob 60%, Elite 120%, Mini-Boss 400%.
constexpr EnemyStats ENEMIES[int(EnemyId::COUNT)] = {
    // name                    hp   atk  def  mag  res  spd  shld  weakness                  resistance
    {"Fante di Perugia",      228,  45,  40,   8,  20,  26,   2,  ElementType::FLAME,       ElementType::NONE},
    {"Balestriere Pesante",   456,  62,  55,  12,  26,  34,   3,  ElementType::FAITH_HOLY,  ElementType::PHYSICAL},
    // Corrado resiste al taglio finche' non viene surriscaldato (Sezione 26A GDD).
    {"Corrado di Spoleto",   1520,  95,  60,  20,  30,  22,   4,  ElementType::FLAME,       ElementType::PHYSICAL}
};

struct EncounterData {
    bn::string_view label;
    int enemy_count;
    int enemy_ids[MAX_ENEMIES_PER_ENCOUNTER];
    bool can_flee;
};

enum class EncounterId { PATTUGLIA_PERUGINA, DUELLO_CORRADO, COUNT };

constexpr EncounterData ENCOUNTERS[int(EncounterId::COUNT)] = {
    {"Pattuglia Perugina", 3, {0, 0, 1, 0, 0, 0}, true},
    {"Corrado di Spoleto", 1, {2, 0, 0, 0, 0, 0}, false}
};

} // namespace gubbio

#endif // ENEMY_DATA_H
