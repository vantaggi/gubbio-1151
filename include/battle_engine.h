#ifndef BATTLE_ENGINE_H
#define BATTLE_ENGINE_H

#include "bn_string_view.h"

namespace gubbio {

// Triangolo delle affinita' elementali (Sezione 13A GDD)
enum class ElementType { PHYSICAL, FAITH_HOLY, FLAME, VOID_SHADOW, NONE };

// Stati alterati (Sezione 12D GDD)
enum class StatusEffect { NONE, ALCHEMICAL_BURN, ARMOR_BROKEN, BLESSED, TERRIFIED, STUNNED };

// Moltiplicatori elementali espressi in percentuale intera (Sezione 13A GDD).
// Nessun float: il ARM7TDMI non ha FPU hardware.
constexpr int ELEMENT_WEAK_PERCENT    = 150;
constexpr int ELEMENT_NEUTRAL_PERCENT = 100;
constexpr int ELEMENT_RESIST_PERCENT  = 50;

// --- Fervor Boost (Sezione 20A GDD) ---
// Livello 0 = azione standard, 1 = x1 (25 Fervore), 2 = x2 (50), 3 = MAX (100).
constexpr int BOOST_LEVEL_COUNT = 4;
constexpr int BOOST_MAX_LEVEL   = 3;

constexpr int BOOST_FERVOR_COST[BOOST_LEVEL_COUNT]    = {0, 25, 50, 100};
// Boost x2 e' un attacco a doppio colpo: 2 colpi al 100% invece di 1 colpo al 200%.
constexpr int BOOST_HIT_COUNT[BOOST_LEVEL_COUNT]      = {1, 1, 2, 1};
constexpr int BOOST_DAMAGE_PERCENT[BOOST_LEVEL_COUNT] = {100, 150, 100, 350};
constexpr int BOOST_SHIELD_PER_HIT[BOOST_LEVEL_COUNT] = {1, 1, 1, 3};
// Boost x1 raddoppia il valore degli scudi di Sant'Ubaldo (Sezione 20A GDD).
constexpr int BOOST_SUPPORT_PERCENT[BOOST_LEVEL_COUNT] = {100, 200, 200, 350};

// --- Shield Break (Sezione 20A GDD) ---
// Scudo a 0 => il nemico salta il turno corrente e il successivo, difese dimezzate.
constexpr int BREAK_DURATION_TURNS = 2;

// --- Ustione Alchemica (Sezione 12D GDD, rivista nella Sessione 04) ---
// Il GDD prescriveva "10% degli HP massimi per carica": con 3 cariche erano il 30% degli HP
// massimi per round, un valore che azzera per costruzione ogni dimensionamento delle riserve
// di HP dei boss (Corrado, 1520 HP, moriva in 4 round). Il danno e' ora ASSOLUTO e scalato sul
// Potere Mistico di chi appicca l'Ustione, fotografato al momento dell'applicazione.
constexpr int BURN_MAX_STACKS     = 3;
constexpr int BURN_DURATION_TURNS = 3;
constexpr int BURN_MAGIC_PERCENT  = 25; // danno per carica = 25% del Potere Mistico del lanciatore

// --- Bastione Azzurro (Sezione 2 GDD) ---
// San Giorgio intercetta i colpi diretti a Ubaldo e Antonio per il round in cui lo attiva.
constexpr int GUARD_DURATION_TURNS = 1;

// --- Accumulo Fervore (Sezione 12A GDD) ---
constexpr int FERVOR_GAIN_GIORGIO_HIT     = 15; // colpo fisico incassato
constexpr int FERVOR_GAIN_UBALDO_SUPPORT  = 20; // scudo / benedizione applicata
constexpr int FERVOR_GAIN_ANTONIO_BURN    = 10; // tick di Ustione su un nemico

// Varianza del danno RNG(0.9 - 1.1) descritta nella Sezione 12B GDD.
constexpr int DAMAGE_VARIANCE_MIN_PERCENT   = 90;
constexpr int DAMAGE_VARIANCE_SPREAD_STEPS  = 21; // 90..110 inclusi

struct BattleUnit
{
    bn::string_view name;
    int max_hp;
    int current_hp;
    int max_fervor;
    int current_fervor;
    int attack;
    int defense;
    int magic_power;
    int magic_resist;
    int speed;
    int level;
    int barrier_hp;      // Muro della Fede: assorbe danni prima degli HP
    int max_shield;      // Punti Scudo (0 per gli eroi)
    int current_shield;
    int break_turns;
    ElementType weakness;
    ElementType resistance;
    StatusEffect current_status;
    int status_turns;
    int burn_stacks;
    int burn_damage_per_stack; // fotografato dal Potere Mistico di chi applica l'Ustione
    int guard_turns;           // Bastione Azzurro attivo (solo San Giorgio)
    bool is_enemy;

    [[nodiscard]] bool is_alive() const { return current_hp > 0; }

    [[nodiscard]] bool is_broken() const { return break_turns > 0; }

    [[nodiscard]] bool is_guarding() const { return guard_turns > 0; }

    // In stato BREAK la Difesa Fisica e Mistica viene dimezzata (Sezione 20A GDD).
    [[nodiscard]] int effective_defense() const { return is_broken() ? defense / 2 : defense; }

    [[nodiscard]] int effective_resist() const { return is_broken() ? magic_resist / 2 : magic_resist; }

    void take_damage(int amount)
    {
        if(barrier_hp > 0)
        {
            const int absorbed = amount < barrier_hp ? amount : barrier_hp;
            barrier_hp -= absorbed;
            amount -= absorbed;
        }

        current_hp -= amount;

        if(current_hp < 0)
        {
            current_hp = 0;
        }
    }

    void add_fervor(int amount)
    {
        current_fervor += amount;

        if(current_fervor > max_fervor)
        {
            current_fervor = max_fervor;
        }
    }

    [[nodiscard]] bool can_afford(int amount) const { return current_fervor >= amount; }

    // Riconciliazione della scala del Fervore: i pool sono assoluti e diversi per Cero
    // (Sezione 5 GDD) perche' i costi di Boost sono assoluti (Sezione 20A GDD), mentre la
    // "barra 0-100" della Sezione 12A GDD e' questa proiezione normalizzata, la sola che
    // l'HUD della Sezione 14B.3 GDD deve disegnare ("[F: 45%]").
    [[nodiscard]] int fervor_percent() const
    {
        return max_fervor > 0 ? (current_fervor * 100) / max_fervor : 0;
    }

    bool spend_fervor(int amount)
    {
        if(current_fervor < amount)
        {
            return false;
        }

        current_fervor -= amount;
        return true;
    }

    // `current_status` e' un valore DERIVATO dai contatori autoritativi (break_turns,
    // burn_stacks): con un solo slot di stato, applicare un'Ustione a un nemico gia' in
    // BREAK ne sovrascriverebbe l'etichetta lasciandola incoerente. Il BREAK ha la
    // precedenza di visualizzazione perche' e' lo stato tatticamente piu' rilevante.
    void refresh_status()
    {
        if(break_turns > 0)
        {
            current_status = StatusEffect::ARMOR_BROKEN;
        }
        else if(burn_stacks > 0)
        {
            current_status = StatusEffect::ALCHEMICAL_BURN;
        }
        else
        {
            current_status = StatusEffect::NONE;
        }
    }

    // Sottrae Punti Scudo. Ritorna true se il colpo ha appena innescato lo stato BREAK.
    bool damage_shield(int points)
    {
        if(current_shield <= 0)
        {
            return false;
        }

        current_shield -= points;

        if(current_shield > 0)
        {
            return false;
        }

        current_shield = 0;
        break_turns = BREAK_DURATION_TURNS;
        refresh_status();
        return true;
    }

    // Il danno per carica e' fissato all'APPLICAZIONE PIU' RECENTE, non per singola carica:
    // riapplicare l'Ustione riscrive il valore di tutte le cariche gia' presenti. Oggi non e'
    // osservabile (solo Sant'Antonio la applica, e il suo Potere Mistico non varia in battaglia);
    // lo diventerebbe con un secondo lanciatore o con buff al Potere Mistico. Tenere una
    // fotografia per carica richiederebbe un array per unita': non lo si paga finche' non serve.
    void apply_burn(int caster_magic_power)
    {
        if(burn_stacks < BURN_MAX_STACKS)
        {
            ++burn_stacks;
        }

        const int tick = (caster_magic_power * BURN_MAGIC_PERCENT) / 100;
        burn_damage_per_stack = tick < 1 ? 1 : tick;
        status_turns = BURN_DURATION_TURNS;
        refresh_status();
    }

    // La durata scala col Fervor Boost speso. Senza questo, selezionare il Bastione con Boost
    // MAX costava 115 Fervore invece di 15 senza alcun beneficio: una trappola per il giocatore,
    // perche' ne' l'HUD ne' il codice segnalavano che la spesa era inutile.
    void start_guard(int boost_level)
    {
        guard_turns = GUARD_DURATION_TURNS + boost_level;
    }
};

enum class SkillTarget { ENEMY, ALLY };

enum class SkillEffect { NONE, ALCHEMICAL_BURN, FAITH_SHIELD, GUARD_ALLIES };

struct SkillData
{
    bn::string_view name;
    ElementType element;
    SkillTarget target;
    SkillEffect effect;
    int fervor_cost;
    int power_percent;         // moltiplicatore delle skill fisiche (100 = standard)
    int base_magic_damage;     // danno base delle skill mistiche
    int armor_pierce_percent;  // quota di armatura ignorata
    int speed_priority;        // modificatore di iniziativa sulla timeline
};

enum class SkillId
{
    BASIC_ATTACK,
    MURO_DELLA_FEDE,
    GIUDIZIO_DELLA_VERGA,
    FENDENTE_DEL_DRAGO,
    BASTIONE_AZZURRO,
    FUOCO_DI_SANTANTONIO,
    ENEMY_STRIKE,
    COUNT
};

// Tabella abilita' in ROM (Sezione 2 GDD per i nomi, Sezione 12A per i costi 15-35 Fervore).
constexpr SkillData SKILLS[int(SkillId::COUNT)] = {
    // name                     element                  target                effect                        cost pow  magic pierce prio
    {"Attacco",                 ElementType::PHYSICAL,   SkillTarget::ENEMY,   SkillEffect::NONE,             0,  100,   0,    0,    0},
    {"Muro della Fede",         ElementType::FAITH_HOLY, SkillTarget::ALLY,    SkillEffect::FAITH_SHIELD,    25,    0,   0,    0,    4},
    // Aggiunta Sessione 04: senza un'abilita' sacra OFFENSIVA la debolezza a FAITH_HOLY del
    // Balestriere Pesante non era sfruttabile da nessun membro del party.
    {"Giudizio della Verga",    ElementType::FAITH_HOLY, SkillTarget::ENEMY,   SkillEffect::NONE,            20,    0,  35,    0,    0},
    {"Fendente del Drago",      ElementType::PHYSICAL,   SkillTarget::ENEMY,   SkillEffect::NONE,            20,  160,   0,   50,    0},
    // Aggiunta Sessione 04: priorita' alta perche' la guardia deve alzarsi prima che i nemici
    // agiscano, altrimenti non intercetta nulla.
    {"Bastione Azzurro",        ElementType::NONE,       SkillTarget::ALLY,    SkillEffect::GUARD_ALLIES,    15,    0,   0,    0,    8},
    {"Fuoco di Sant'Antonio",   ElementType::FLAME,      SkillTarget::ENEMY,   SkillEffect::ALCHEMICAL_BURN, 15,    0,  40,    0,    0},
    {"Colpo",                   ElementType::PHYSICAL,   SkillTarget::ENEMY,   SkillEffect::NONE,             0,  100,   0,    0,    0}
};

class BattleSystem
{
public:
    [[nodiscard]] static int element_multiplier_percent(const BattleUnit& target, ElementType element)
    {
        if(element == ElementType::NONE)
        {
            return ELEMENT_NEUTRAL_PERCENT;
        }

        if(target.weakness == element)
        {
            return ELEMENT_WEAK_PERCENT;
        }

        if(target.resistance == element)
        {
            return ELEMENT_RESIST_PERCENT;
        }

        return ELEMENT_NEUTRAL_PERCENT;
    }

    // Formule standardizzate della Sezione 13C GDD, in aritmetica intera a 32 bit.
    // Fisico:  max(1, floor((Atk*2 - Def) / 2) * ModSkill * ModElem * ModBoost)
    // Mistico: max(1, (DannoBase + floor((Mistico - ResNemico) / 2)) * ModElem * ModBoost)
    [[nodiscard]] static int calculate_damage(const BattleUnit& attacker, const BattleUnit& target,
                                              const SkillData& skill, int boost_level)
    {
        int damage;

        if(skill.element == ElementType::PHYSICAL)
        {
            const int pierced_def = (target.effective_defense() * (100 - skill.armor_pierce_percent)) / 100;
            damage = ((attacker.attack * 2) - pierced_def) / 2;
            damage = (damage * skill.power_percent) / 100;
        }
        else
        {
            damage = skill.base_magic_damage + ((attacker.magic_power - target.effective_resist()) / 2);
        }

        damage = (damage * element_multiplier_percent(target, skill.element)) / 100;
        damage = (damage * BOOST_DAMAGE_PERCENT[boost_level]) / 100;

        return damage < 1 ? 1 : damage;
    }

    // HPScudo = (PotereFede * 1.8) + (LivelloEroe * 12)  (Sezione 12B GDD)
    [[nodiscard]] static int calculate_faith_shield(const BattleUnit& caster, int boost_level)
    {
        const int base = ((caster.magic_power * 18) / 10) + (caster.level * 12);
        return (base * BOOST_SUPPORT_PERCENT[boost_level]) / 100;
    }

    [[nodiscard]] static int total_fervor_cost(const SkillData& skill, int boost_level)
    {
        return skill.fervor_cost + BOOST_FERVOR_COST[boost_level];
    }
};

} // namespace gubbio

#endif // BATTLE_ENGINE_H
