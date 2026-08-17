#ifndef ITEM_DATA_H
#define ITEM_DATA_H

#include "bn_string_view.h"
#include "battle_engine.h"

namespace gubbio {

// Consumabili gastronomici della Sezione 8E GDD. Nessuno e' offensivo: la Sezione censisce
// solo cure, rianimazioni, purificazioni e potenziamenti.
enum class ItemTarget { ALLY, ALLY_FALLEN, PARTY };

enum class ItemEffect { HEAL_HP, REVIVE, RESTORE_FERVOR, CURE_STATUS, BUFF_STATS };

// Maschera di bit degli StatusEffect purificabili.
[[nodiscard]] constexpr int status_bit(StatusEffect status) { return 1 << int(status); }

// Veleno, Confusione e Silenzio della Sezione 8E NON esistono in `StatusEffect`: sono mappati
// sui loro equivalenti funzionali gia' implementati — Veleno -> Ustione (unico danno nel tempo),
// Silenzio -> Terrore Feudale (blocca l'accumulo di Fervore, quindi le abilita'), Confusione ->
// Stordimento (perdita del turno). `ARMOR_BROKEN` e' deliberatamente ESCLUSO: e' lo Shield
// Break, pilastro tattico della Sezione 20A, e renderlo curabile sarebbe un exploit.
// NOTA: oggi solo l'Ustione viene realmente applicata da qualcosa; TERRIFIED e STUNNED non
// hanno ancora una fonte, quindi all'atto pratico i Biscotti curano solo l'Ustione. La maschera
// e' gia' scritta per esteso perche' sia corretta quando quegli status esisteranno.
constexpr int CURE_MASK_ANICE = status_bit(StatusEffect::ALCHEMICAL_BURN) |
                               status_bit(StatusEffect::TERRIFIED) |
                               status_bit(StatusEffect::STUNNED);

// Valore neutro dei modificatori percentuali.
constexpr int BUFF_NEUTRAL_PERCENT = 100;

struct ItemData
{
    bn::string_view name;        // nome esteso della Sezione 8E GDD
    bn::string_view short_name;  // etichetta per il riquadro comandi da 80px (Sez. 14B.3 GDD)
    ItemTarget target;
    ItemEffect effect;
    int heal_hp;               // HP assoluti ripristinati
    int heal_percent;          // HP ripristinati come quota del massimo del bersaglio
    int fervor_percent;        // Fervore ripristinato come quota del pool del bersaglio
    int attack_percent;        // modificatore di Attacco (100 = neutro)
    int defense_percent;       // modificatore di Difesa (100 = neutro)
    int accuracy_percent;      // modificatore di Precisione (100 = neutro)
    int buff_turns;            // durata dei tre modificatori sopra
    int cure_mask;             // maschera degli StatusEffect rimossi
    int speed_priority;        // modificatore di iniziativa sulla timeline, come SkillData
    int max_carry;             // tetto di trasporto: e' la leva di bilanciamento
};

enum class ItemId
{
    CRESCIA_PASQUA,
    CRESCIA_CENERE,
    BACCALA_CERAIOLA,
    BISCOTTI_ANICE,
    VINO_ROSSO,
    COUNT
};

// Tabella dei consumabili in ROM. Nomi ed effetti sono letterali dalla Sezione 8E GDD; i valori
// numerici sono calibrati sui pool reali di hero_data.h (HP 240/380/210, Fervore 180/120/210) e
// sul danno nemico di enemy_data.h. Le priorita' 6 e 10 stanno nel solco di quelle esistenti
// (Muro della Fede 4, Bastione Azzurro 8): con +6 tutti e tre i Ceri precedono ogni nemico
// censito, cosi' una cura atterra prima dei colpi invece che dopo.
constexpr ItemData ITEMS[int(ItemId::COUNT)] = {
    // name                                short        target                   effect                      hp  heal%  fer%  atk%  def%  acc%  turns  cure_mask         prio carry
    {"Crescia di Pasqua al Formaggio",     "Crescia",   ItemTarget::ALLY,        ItemEffect::HEAL_HP,       100,    0,    0,  100,  110,  100,     5, 0,                   6,   5},
    // "Ripristina tutti gli HP": percentuale, perche' i tre Ceri hanno pool molto diversi.
    {"Crescia sotto la Cenere",            "Cenere",    ItemTarget::ALLY_FALLEN, ItemEffect::REVIVE,          0,  100,    0,  100,  100,  100,     0, 0,                   6,   2},
    // Tetto di trasporto 1: 510 Fervore restituiti valgono cinque Boost MAX. E' un'apertura di
    // boss fight, non una risorsa rinnovabile, come il rito della Brocca dell'Alzata (Sez. 8C).
    {"Baccalà alla Ceraiola",             "Baccalà",  ItemTarget::PARTY,       ItemEffect::RESTORE_FERVOR,  0,    0,  100,  100,  100,  100,     0, 0,                   6,   1},
    // "Consumabile rapido" (Sez. 8E): priorita' 10, sopra il Bastione Azzurro.
    {"Biscotti all'Anice di Sant'Ubaldo",  "Biscotti",  ItemTarget::ALLY,        ItemEffect::CURE_STATUS,     0,    0,    0,  100,  100,  100,     0, CURE_MASK_ANICE,    10,   5},
    // Durata 3 turni allineata a BURN_DURATION_TURNS: il GDD non la specifica.
    {"Vino Rosso delle Colline Eugubine",  "Vino",      ItemTarget::ALLY,        ItemEffect::BUFF_STATS,      0,    0,    0,  140,  100,   85,     3, 0,                   6,   3}
};

// Il Baccala' e' l'unico oggetto capace di annullare l'economia del Fervore su cui poggia tutto
// il combattimento: il suo tetto di trasporto va tenuto a 1. Verificato a compile time perche'
// un ritocco distratto passerebbe altrimenti inosservato.
static_assert(ITEMS[int(ItemId::BACCALA_CERAIOLA)].max_carry == 1,
              "Il Baccala' alla Ceraiola restituisce l'intero Fervore del party: max_carry deve restare 1");

} // namespace gubbio

#endif // ITEM_DATA_H
