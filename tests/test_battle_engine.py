#!/usr/bin/env python3
"""
Test Harness per la Battle Loop di Gubbio 1151.

Questo file e' un PORT FEDELE in Python della logica implementata in
`include/battle_engine.h` e `src/battle_scene.cpp`. Serve a validare formule,
Shield Break, timeline e consumo Fervore senza dover disporre di devkitARM.

REGOLA: ogni modifica alle formule del C++ va replicata qui e viceversa.
Tutta l'aritmetica e' intera con troncamento verso zero, come su ARM7TDMI.
"""

import unittest
from enum import Enum


def idiv(a, b):
    """Divisione intera C++ (troncamento verso zero, non floor come in Python)."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


# ----------------------------------------------------------------------------------------------
# Costanti (mirror di battle_engine.h)
# ----------------------------------------------------------------------------------------------

class Element(Enum):
    PHYSICAL = 0
    FAITH_HOLY = 1
    FLAME = 2
    VOID_SHADOW = 3
    NONE = 4


ELEMENT_WEAK_PERCENT = 150
ELEMENT_NEUTRAL_PERCENT = 100
ELEMENT_RESIST_PERCENT = 50

BOOST_LEVEL_COUNT = 4
BOOST_MAX_LEVEL = 3
BOOST_FERVOR_COST = [0, 25, 50, 100]
BOOST_HIT_COUNT = [1, 1, 2, 1]
BOOST_DAMAGE_PERCENT = [100, 150, 100, 350]
BOOST_SHIELD_PER_HIT = [1, 1, 1, 3]
BOOST_SUPPORT_PERCENT = [100, 200, 200, 350]

BREAK_DURATION_TURNS = 2
BURN_MAX_STACKS = 3
BURN_DURATION_TURNS = 3
# Sessione 04: l'Ustione non e' piu' una percentuale degli HP massimi del bersaglio (che
# rendeva irrilevanti le riserve dei boss) ma un assoluto scalato sul Potere Mistico.
BURN_MAGIC_PERCENT = 25
GUARD_DURATION_TURNS = 1

FERVOR_GAIN_GIORGIO_HIT = 15
FERVOR_GAIN_UBALDO_SUPPORT = 20
FERVOR_GAIN_ANTONIO_BURN = 10


class Skill:
    def __init__(self, name, element, target, effect, cost, power, magic, pierce, priority):
        self.name = name
        self.element = element
        self.target = target          # 'ENEMY' | 'ALLY'
        self.effect = effect          # None | 'BURN' | 'FAITH_SHIELD'
        self.fervor_cost = cost
        self.power_percent = power
        self.base_magic_damage = magic
        self.armor_pierce_percent = pierce
        self.speed_priority = priority


SKILLS = {
    "BASIC_ATTACK":         Skill("Attacco",               Element.PHYSICAL,   'ENEMY', None,           0, 100,  0,  0, 0),
    "MURO_DELLA_FEDE":      Skill("Muro della Fede",       Element.FAITH_HOLY, 'ALLY',  'FAITH_SHIELD', 25,  0,  0,  0, 4),
    "GIUDIZIO_DELLA_VERGA": Skill("Giudizio della Verga",  Element.FAITH_HOLY, 'ENEMY', None,          20,   0, 35,  0, 0),
    "FENDENTE_DEL_DRAGO":   Skill("Fendente del Drago",    Element.PHYSICAL,   'ENEMY', None,          20, 160,  0, 50, 0),
    "BASTIONE_AZZURRO":     Skill("Bastione Azzurro",      Element.NONE,       'ALLY',  'GUARD',       15,   0,  0,  0, 8),
    "FUOCO_DI_SANTANTONIO": Skill("Fuoco di Sant'Antonio", Element.FLAME,      'ENEMY', 'BURN',        15,   0, 40,  0, 0),
    "ENEMY_STRIKE":         Skill("Colpo",                 Element.PHYSICAL,   'ENEMY', None,           0, 100,  0,  0, 0),
}


# ----------------------------------------------------------------------------------------------
# BattleUnit (mirror di battle_engine.h)
# ----------------------------------------------------------------------------------------------

class BattleUnit:
    def __init__(self, name, hp, fervor, atk, dfn, mag, res, spd, level=1,
                 shield=0, weakness=Element.NONE, resistance=Element.NONE, is_enemy=False,
                 start_fervor_percent=100):
        self.name = name
        self.max_hp = hp
        self.current_hp = hp
        self.max_fervor = fervor
        self.current_fervor = idiv(fervor * start_fervor_percent, 100)
        self.attack = atk
        self.defense = dfn
        self.magic_power = mag
        self.magic_resist = res
        self.speed = spd
        self.level = level
        self.barrier_hp = 0
        self.max_shield = shield
        self.current_shield = shield
        self.break_turns = 0
        self.weakness = weakness
        self.resistance = resistance
        self.status = None
        self.status_turns = 0
        self.burn_stacks = 0
        self.burn_damage_per_stack = 0
        self.guard_turns = 0
        self.is_enemy = is_enemy

    def is_alive(self):
        return self.current_hp > 0

    def is_broken(self):
        return self.break_turns > 0

    def is_guarding(self):
        return self.guard_turns > 0

    def effective_defense(self):
        return idiv(self.defense, 2) if self.is_broken() else self.defense

    def effective_resist(self):
        return idiv(self.magic_resist, 2) if self.is_broken() else self.magic_resist

    def take_damage(self, amount):
        if self.barrier_hp > 0:
            absorbed = min(amount, self.barrier_hp)
            self.barrier_hp -= absorbed
            amount -= absorbed
        self.current_hp = max(0, self.current_hp - amount)

    def add_fervor(self, amount):
        self.current_fervor = min(self.max_fervor, self.current_fervor + amount)

    def can_afford(self, amount):
        return self.current_fervor >= amount

    def fervor_percent(self):
        """Scala 0-100 della Sez. 12A GDD: proiezione normalizzata del pool assoluto."""
        return idiv(self.current_fervor * 100, self.max_fervor) if self.max_fervor > 0 else 0

    def spend_fervor(self, amount):
        if self.current_fervor < amount:
            return False
        self.current_fervor -= amount
        return True

    def refresh_status(self):
        """`status` e' derivato dai contatori autoritativi; il BREAK ha la precedenza."""
        if self.break_turns > 0:
            self.status = 'ARMOR_BROKEN'
        elif self.burn_stacks > 0:
            self.status = 'ALCHEMICAL_BURN'
        else:
            self.status = None

    def damage_shield(self, points):
        """Ritorna True se il colpo ha appena innescato lo stato BREAK."""
        if self.current_shield <= 0:
            return False
        self.current_shield -= points
        if self.current_shield > 0:
            return False
        self.current_shield = 0
        self.break_turns = BREAK_DURATION_TURNS
        self.refresh_status()
        return True

    def apply_burn(self, caster_magic_power):
        """Il danno per carica e' fissato all'applicazione, non segue il lanciatore."""
        self.burn_stacks = min(BURN_MAX_STACKS, self.burn_stacks + 1)
        self.burn_damage_per_stack = max(1, idiv(caster_magic_power * BURN_MAGIC_PERCENT, 100))
        self.status_turns = BURN_DURATION_TURNS
        self.refresh_status()

    def start_guard(self, boost_level=0):
        """La durata scala col Boost: senza, spendere Fervore sul Bastione era una trappola."""
        self.guard_turns = GUARD_DURATION_TURNS + boost_level


# ----------------------------------------------------------------------------------------------
# BattleSystem (mirror di battle_engine.h)
# ----------------------------------------------------------------------------------------------

def element_multiplier_percent(target, element):
    if element == Element.NONE:
        return ELEMENT_NEUTRAL_PERCENT
    if target.weakness == element:
        return ELEMENT_WEAK_PERCENT
    if target.resistance == element:
        return ELEMENT_RESIST_PERCENT
    return ELEMENT_NEUTRAL_PERCENT


def calculate_damage(attacker, target, skill, boost_level):
    if skill.element == Element.PHYSICAL:
        pierced_def = idiv(target.effective_defense() * (100 - skill.armor_pierce_percent), 100)
        damage = idiv((attacker.attack * 2) - pierced_def, 2)
        damage = idiv(damage * skill.power_percent, 100)
    else:
        damage = skill.base_magic_damage + idiv(attacker.magic_power - target.effective_resist(), 2)

    damage = idiv(damage * element_multiplier_percent(target, skill.element), 100)
    damage = idiv(damage * BOOST_DAMAGE_PERCENT[boost_level], 100)
    return max(1, damage)


def calculate_faith_shield(caster, boost_level):
    base = idiv(caster.magic_power * 18, 10) + (caster.level * 12)
    return idiv(base * BOOST_SUPPORT_PERCENT[boost_level], 100)


def total_fervor_cost(skill, boost_level):
    return skill.fervor_cost + BOOST_FERVOR_COST[boost_level]


# ----------------------------------------------------------------------------------------------
# Frammenti di battle_scene.cpp rilevanti per i test
# ----------------------------------------------------------------------------------------------

def redirect_if_guarded(target, giorgio=None):
    """Mirror di _redirect_if_guarded: il Bastione Azzurro intercetta i colpi ai fragili."""
    if target.is_enemy or giorgio is None or target is giorgio:
        return target
    return giorgio if (giorgio.is_alive() and giorgio.is_guarding()) else target


def apply_hit(actor, target, skill, boost_level, giorgio=None):
    """Mirror di BattleSceneManager::_apply_hit (senza varianza RNG)."""
    target = redirect_if_guarded(target, giorgio)
    if not target.is_alive():
        return 0

    if skill.element == target.weakness and target.current_shield > 0:
        target.damage_shield(BOOST_SHIELD_PER_HIT[boost_level])

    damage = calculate_damage(actor, target, skill, boost_level)
    target.take_damage(damage)

    if (not target.is_enemy) and target.name == "San Giorgio" \
            and skill.element == Element.PHYSICAL and target.is_alive():
        target.add_fervor(FERVOR_GAIN_GIORGIO_HIT)

    if skill.effect == 'BURN' and target.is_alive():
        target.apply_burn(actor.magic_power)

    return damage


def sort_action_queue(queue):
    """Mirror di _sort_action_queue: insertion sort stabile, decrescente per velocita'."""
    for i in range(1, len(queue)):
        key = queue[i]
        j = i - 1
        while j >= 0 and queue[j][1] < key[1]:
            queue[j + 1] = queue[j]
            j -= 1
        queue[j + 1] = key
    return queue


def tick_status(unit, antonio=None):
    """Mirror di _tick_status: tick Ustione + uscita dallo stato BREAK."""
    if unit.burn_stacks > 0 and unit.is_alive():
        unit.take_damage(unit.burn_damage_per_stack * unit.burn_stacks)
        if unit.is_enemy and antonio is not None and antonio.is_alive():
            antonio.add_fervor(FERVOR_GAIN_ANTONIO_BURN)
        unit.status_turns -= 1
        if unit.status_turns <= 0:
            unit.burn_stacks = 0
            unit.status_turns = 0

    if unit.guard_turns > 0:
        unit.guard_turns -= 1

    if unit.break_turns > 0:
        unit.break_turns -= 1
        if unit.break_turns == 0:
            unit.current_shield = unit.max_shield

    unit.refresh_status()


# ----------------------------------------------------------------------------------------------
# Fixtures: valori canonici di hero_data.h ed enemy_data.h
# ----------------------------------------------------------------------------------------------

# Fervore d'ingresso dal mockup HUD della Sez. 14B.3 GDD (mirror di HERO_START_FERVOR_PERCENT).
HERO_START_FERVOR_PERCENT = {"Sant'Ubaldo": 80, "San Giorgio": 45, "Sant'Antonio": 20}

HERO_SKILLS = {
    "Sant'Ubaldo":  ["MURO_DELLA_FEDE", "GIUDIZIO_DELLA_VERGA"],
    "San Giorgio":  ["FENDENTE_DEL_DRAGO", "BASTIONE_AZZURRO"],
    "Sant'Antonio": ["FUOCO_DI_SANTANTONIO"],
}


def make_ubaldo(level=1):
    return BattleUnit("Sant'Ubaldo", 240, 180, 25, 45, 95, 72, 30, level, start_fervor_percent=80)


def make_giorgio(level=1):
    return BattleUnit("San Giorgio", 380, 120, 90, 80, 25, 40, 42, level, start_fervor_percent=45)


def make_antonio(level=1):
    return BattleUnit("Sant'Antonio", 210, 210, 18, 28, 95, 56, 38, level, start_fervor_percent=20)


def make_fante():
    return BattleUnit("Fante di Perugia", 228, 0, 45, 40, 8, 20, 26,
                      shield=2, weakness=Element.FLAME, resistance=Element.NONE, is_enemy=True)


def make_balestriere():
    return BattleUnit("Balestriere Pesante", 456, 0, 62, 55, 12, 26, 34,
                      shield=3, weakness=Element.FAITH_HOLY, resistance=Element.PHYSICAL, is_enemy=True)


def make_corrado():
    return BattleUnit("Corrado di Spoleto", 1520, 0, 95, 60, 20, 30, 22,
                      shield=4, weakness=Element.FLAME, resistance=Element.PHYSICAL, is_enemy=True)


# ----------------------------------------------------------------------------------------------
# Test
# ----------------------------------------------------------------------------------------------

class DamageFormulaTest(unittest.TestCase):
    """Formule standardizzate della Sezione 13C GDD."""

    def test_physical_neutral(self):
        # (90*2 - 40)/2 = 70, elemento neutro
        self.assertEqual(calculate_damage(make_giorgio(), make_fante(), SKILLS["BASIC_ATTACK"], 0), 70)

    def test_physical_against_resistance(self):
        # Corrado resiste al fisico: (180-60)/2 = 60, poi x0.5 = 30
        self.assertEqual(calculate_damage(make_giorgio(), make_corrado(), SKILLS["BASIC_ATTACK"], 0), 30)

    def test_armor_pierce(self):
        # Fendente ignora il 50% dell'armatura: def 60 -> 30
        # (180-30)/2 = 75, x1.60 = 120, resistenza fisica x0.5 = 60
        self.assertEqual(calculate_damage(make_giorgio(), make_corrado(), SKILLS["FENDENTE_DEL_DRAGO"], 0), 60)

    def test_magic_against_weakness(self):
        # 40 + (95-30)/2 = 72, debolezza al fuoco x1.5 = 108
        self.assertEqual(calculate_damage(make_antonio(), make_corrado(), SKILLS["FUOCO_DI_SANTANTONIO"], 0), 108)

    def test_minimum_damage_is_one(self):
        antonio = make_antonio()
        muraglia = BattleUnit("Muraglia", 999, 0, 10, 900, 0, 900, 5, is_enemy=True)
        self.assertEqual(calculate_damage(antonio, muraglia, SKILLS["BASIC_ATTACK"], 0), 1)


class ShieldBreakTest(unittest.TestCase):
    """Sistema Scudo dei Signori Feudali (Sezione 20A GDD)."""

    def test_shield_break_and_damage_scaling(self):
        antonio = make_antonio()
        giorgio = make_giorgio()
        corrado = make_corrado()

        # Solo l'elemento di debolezza intacca i Punti Scudo.
        apply_hit(giorgio, corrado, SKILLS["BASIC_ATTACK"], 0)
        self.assertEqual(corrado.current_shield, 4)

        # Tre colpi di fuoco: scudo 4 -> 1, ancora integro.
        for _ in range(3):
            dmg_unbroken = apply_hit(antonio, corrado, SKILLS["FUOCO_DI_SANTANTONIO"], 0)
        self.assertEqual(corrado.current_shield, 1)
        self.assertFalse(corrado.is_broken())
        self.assertEqual(dmg_unbroken, 108)

        # Quarto colpo: scudo a 0 -> BREAK, e la difesa gia' dimezzata si applica
        # allo stesso colpo che rompe la corazza.
        dmg_breaking = apply_hit(antonio, corrado, SKILLS["FUOCO_DI_SANTANTONIO"], 0)
        self.assertEqual(corrado.current_shield, 0)
        self.assertTrue(corrado.is_broken())
        self.assertEqual(corrado.break_turns, BREAK_DURATION_TURNS)
        self.assertEqual(dmg_breaking, 120)
        self.assertGreater(dmg_breaking, dmg_unbroken)

        # In BREAK anche la Difesa Fisica e' dimezzata: Giorgio infligge di piu'.
        self.assertEqual(corrado.effective_defense(), 30)
        self.assertEqual(calculate_damage(giorgio, corrado, SKILLS["BASIC_ATTACK"], 0), 37)

    def test_break_lasts_two_turns_then_shield_refills(self):
        antonio = make_antonio()
        corrado = make_corrado()
        for _ in range(4):
            apply_hit(antonio, corrado, SKILLS["FUOCO_DI_SANTANTONIO"], 0)
        self.assertTrue(corrado.is_broken())

        tick_status(corrado, antonio)          # fine del round in cui e' avvenuta la rottura
        self.assertTrue(corrado.is_broken())   # salta anche il round successivo
        self.assertEqual(corrado.break_turns, 1)

        tick_status(corrado, antonio)
        self.assertFalse(corrado.is_broken())
        self.assertEqual(corrado.current_shield, corrado.max_shield)
        # L'etichetta di stato torna a riflettere l'Ustione ancora attiva, non resta
        # bloccata su ARMOR_BROKEN: `status` e' derivato, non memorizzato.
        self.assertEqual(corrado.status, 'ALCHEMICAL_BURN')

    def test_break_label_survives_a_burn_applied_on_top(self):
        antonio = make_antonio()
        corrado = make_corrado()
        for _ in range(4):
            apply_hit(antonio, corrado, SKILLS["FUOCO_DI_SANTANTONIO"], 0)
        # L'Ustione applicata dallo stesso colpo che rompe la corazza non deve
        # sovrascrivere l'etichetta di BREAK.
        self.assertTrue(corrado.is_broken())
        self.assertEqual(corrado.burn_stacks, BURN_MAX_STACKS)
        self.assertEqual(corrado.status, 'ARMOR_BROKEN')


class FervorBoostTest(unittest.TestCase):
    """Fervor Boost x1 / x2 / MAX (Sezione 20A GDD)."""

    def test_fervor_boost_math(self):
        base_dmg = 90
        self.assertEqual(idiv(base_dmg * BOOST_DAMAGE_PERCENT[1], 100), 135)   # x1 -> +50%
        self.assertEqual(idiv(base_dmg * BOOST_DAMAGE_PERCENT[3], 100), 315)   # MAX -> x3.5

    def test_boost_costs(self):
        fuoco = SKILLS["FUOCO_DI_SANTANTONIO"]
        self.assertEqual([total_fervor_cost(fuoco, b) for b in range(BOOST_LEVEL_COUNT)], [15, 40, 65, 115])

        antonio = make_antonio()   # pool 210: a barra piena copre ogni livello
        antonio.current_fervor = antonio.max_fervor
        self.assertTrue(all(antonio.can_afford(total_fervor_cost(fuoco, b)) for b in range(BOOST_LEVEL_COUNT)))

    def test_every_cero_can_reach_the_supreme(self):
        """Mirror delle static_assert di battle_scene.h: invariante di bilanciamento.

        L'invariante e' sulla CAPIENZA del pool (`max_fervor`), non sul Fervore posseduto in
        un dato istante: i costi di Boost (Sez. 20A GDD) sono assoluti, quindi il pool di ogni
        Cero deve coprire 100 + il costo della sua abilita' firma. San Giorgio, portato da 70
        a 120, arriva al Boost MAX consumando esattamente l'intera barra (20 + 100).
        """
        for hero in (make_ubaldo(), make_giorgio(), make_antonio()):
            # L'invariante vale sull'abilita' PIU' COSTOSA del Cero: se una sola non fosse
            # potenziabile al massimo, quella Suprema resterebbe irraggiungibile.
            cost = max(total_fervor_cost(SKILLS[k], BOOST_MAX_LEVEL) for k in HERO_SKILLS[hero.name])
            self.assertGreaterEqual(hero.max_fervor, cost,
                                    f"{hero.name} non puo' raggiungere il Boost MAX "
                                    f"({hero.max_fervor} < {cost})")

        giorgio = make_giorgio()
        giorgio.current_fervor = giorgio.max_fervor
        self.assertEqual(total_fervor_cost(SKILLS["FENDENTE_DEL_DRAGO"], BOOST_MAX_LEVEL), 120)
        self.assertEqual(giorgio.max_fervor, 120)
        self.assertTrue(giorgio.spend_fervor(120))
        self.assertEqual(giorgio.current_fervor, 0)   # "consumano l'intera barra" (Sez. 12A GDD)

    def test_fervor_percent_is_the_normalized_display_scale(self):
        """La barra 0-100 della Sez. 12A GDD e' una proiezione, non il pool assoluto."""
        giorgio = make_giorgio()
        giorgio.current_fervor = giorgio.max_fervor
        self.assertEqual(giorgio.fervor_percent(), 100)
        giorgio.spend_fervor(60)
        self.assertEqual(giorgio.fervor_percent(), 50)      # 60/120

        antonio = make_antonio()
        antonio.current_fervor = 105
        self.assertEqual(antonio.fervor_percent(), 50)      # 105/210: pool diverso, stessa lettura HUD

        corrado = make_corrado()                            # i nemici non hanno barra Fervore
        self.assertEqual(corrado.fervor_percent(), 0)

    def test_boost_x2_is_a_double_hit(self):
        antonio = make_antonio()
        corrado = make_corrado()
        total = sum(apply_hit(antonio, corrado, SKILLS["FUOCO_DI_SANTANTONIO"], 2)
                    for _ in range(BOOST_HIT_COUNT[2]))
        self.assertEqual(BOOST_HIT_COUNT[2], 2)
        self.assertEqual(corrado.current_shield, 2)     # due colpi, due Punti Scudo
        self.assertEqual(total, 216)                    # 108 x 2

    def test_boost_max_removes_three_shield_points(self):
        antonio = make_antonio()
        corrado = make_corrado()
        damage = apply_hit(antonio, corrado, SKILLS["FUOCO_DI_SANTANTONIO"], BOOST_MAX_LEVEL)
        self.assertEqual(corrado.current_shield, 1)
        self.assertEqual(damage, 378)                   # 108 x 3.5

    def test_fervor_is_consumed_on_execution(self):
        antonio = make_antonio()
        antonio.current_fervor = antonio.max_fervor
        cost = total_fervor_cost(SKILLS["FUOCO_DI_SANTANTONIO"], 1)
        self.assertEqual(cost, 40)
        self.assertTrue(antonio.spend_fervor(cost))
        self.assertEqual(antonio.current_fervor, 210 - 40)
        self.assertFalse(antonio.spend_fervor(10_000))
        self.assertEqual(antonio.current_fervor, 170)

    def test_battle_start_fervor_follows_hud_mockup(self):
        """Fervore d'ingresso dalle percentuali della Sez. 14B.3 GDD, non barra piena."""
        ubaldo, giorgio, antonio = make_ubaldo(), make_giorgio(), make_antonio()

        self.assertEqual((ubaldo.current_fervor, giorgio.current_fervor, antonio.current_fervor),
                         (144, 54, 42))
        self.assertEqual([h.fervor_percent() for h in (ubaldo, giorgio, antonio)], [80, 45, 20])

        # Conseguenza voluta: nessuno dei tre Ceri apre lo scontro con la Mossa Suprema
        # tranne Sant'Ubaldo, il cui pool d'ingresso (144) copre gia' il suo costo MAX (125).
        self.assertTrue(ubaldo.can_afford(total_fervor_cost(SKILLS["MURO_DELLA_FEDE"], BOOST_MAX_LEVEL)))
        self.assertFalse(giorgio.can_afford(total_fervor_cost(SKILLS["FENDENTE_DEL_DRAGO"], BOOST_MAX_LEVEL)))
        self.assertFalse(antonio.can_afford(total_fervor_cost(SKILLS["FUOCO_DI_SANTANTONIO"], BOOST_MAX_LEVEL)))

    def test_giorgio_earns_his_supreme_by_absorbing_hits(self):
        """Il tank guadagna la Suprema incassando: 54 + 15/colpo -> 120 in 5 colpi (Sez. 12A GDD)."""
        giorgio = make_giorgio()
        corrado = make_corrado()
        supreme_cost = total_fervor_cost(SKILLS["FENDENTE_DEL_DRAGO"], BOOST_MAX_LEVEL)

        hits = 0
        while not giorgio.can_afford(supreme_cost) and giorgio.is_alive() and hits < 20:
            giorgio.current_hp = giorgio.max_hp          # isola l'accumulo dalla letalita'
            apply_hit(corrado, giorgio, SKILLS["ENEMY_STRIKE"], 0)
            hits += 1

        self.assertEqual(hits, 5)
        self.assertEqual(giorgio.current_fervor, 120)    # 54 + 5*15 = 129, limato al pool


class TimelineTest(unittest.TestCase):
    """Ordine di azione per Velocita' (Sezione 20A GDD)."""

    def test_queue_sorted_by_speed_descending(self):
        ubaldo, giorgio, antonio, corrado = make_ubaldo(), make_giorgio(), make_antonio(), make_corrado()
        queue = [
            ("Ubaldo",  ubaldo.speed + SKILLS["MURO_DELLA_FEDE"].speed_priority),
            ("Giorgio", giorgio.speed + SKILLS["BASIC_ATTACK"].speed_priority),
            ("Antonio", antonio.speed + SKILLS["FUOCO_DI_SANTANTONIO"].speed_priority),
            ("Corrado", corrado.speed + SKILLS["ENEMY_STRIKE"].speed_priority),
        ]
        self.assertEqual([name for name, _ in sort_action_queue(queue)],
                         ["Giorgio", "Antonio", "Ubaldo", "Corrado"])

    def test_priority_modifier_can_overtake(self):
        # Muro della Fede ha priorita' +4: Ubaldo (30+4=34) resta sotto Antonio (38).
        self.assertEqual(SKILLS["MURO_DELLA_FEDE"].speed_priority, 4)
        queue = sort_action_queue([("Ubaldo", 34), ("Antonio", 38)])
        self.assertEqual(queue[0][0], "Antonio")

    def test_sort_is_stable_on_ties(self):
        queue = sort_action_queue([("primo", 40), ("secondo", 40), ("terzo", 40)])
        self.assertEqual([name for name, _ in queue], ["primo", "secondo", "terzo"])


class StatusAndSupportTest(unittest.TestCase):
    """Ustione Alchemica, Muro della Fede e accumulo Fervore (Sezioni 12A/12B/12D GDD)."""

    def test_burn_damage_is_absolute_and_scales_on_magic_power(self):
        antonio = make_antonio()
        antonio.current_fervor = 0
        corrado = make_corrado()

        apply_hit(antonio, corrado, SKILLS["FUOCO_DI_SANTANTONIO"], 0)
        self.assertEqual(corrado.burn_stacks, 1)

        # 25% del Potere Mistico di Antonio (95) = 23 per carica, indipendente dagli HP del bersaglio.
        self.assertEqual(corrado.burn_damage_per_stack, 23)
        hp_before = corrado.current_hp
        tick_status(corrado, antonio)
        self.assertEqual(hp_before - corrado.current_hp, 23)
        self.assertEqual(antonio.current_fervor, FERVOR_GAIN_ANTONIO_BURN)

        # Il punto della revisione: un bersaglio con il doppio degli HP subisce lo STESSO
        # danno assoluto, quindi le riserve di HP dei boss tornano a contare.
        piccolo, grande = make_fante(), make_corrado()   # 228 HP contro 1520
        apply_hit(make_antonio(), piccolo, SKILLS["FUOCO_DI_SANTANTONIO"], 0)
        apply_hit(make_antonio(), grande, SKILLS["FUOCO_DI_SANTANTONIO"], 0)
        self.assertEqual(piccolo.burn_damage_per_stack, grande.burn_damage_per_stack)

    def test_burn_stacks_cap_at_three(self):
        antonio = make_antonio()
        corrado = make_corrado()
        for _ in range(5):
            apply_hit(antonio, corrado, SKILLS["FUOCO_DI_SANTANTONIO"], 0)
        self.assertEqual(corrado.burn_stacks, BURN_MAX_STACKS)
        self.assertEqual(corrado.burn_damage_per_stack * corrado.burn_stacks, 69)

    def test_faith_shield_absorbs_before_hp(self):
        ubaldo = make_ubaldo(level=12)
        giorgio = make_giorgio()

        # (95 * 1.8) + (12 * 12) = 171 + 144 = 315
        shield = calculate_faith_shield(ubaldo, 0)
        self.assertEqual(shield, 315)
        self.assertEqual(calculate_faith_shield(ubaldo, 1), 630)       # Boost x1 raddoppia lo scudo

        giorgio.barrier_hp += shield
        giorgio.take_damage(400)
        self.assertEqual(giorgio.barrier_hp, 0)
        self.assertEqual(giorgio.current_hp, 380 - 85)

    def test_ubaldo_gains_fervor_on_support(self):
        ubaldo = make_ubaldo()
        ubaldo.current_fervor = 0
        ubaldo.add_fervor(FERVOR_GAIN_UBALDO_SUPPORT)
        self.assertEqual(ubaldo.current_fervor, 20)

    def test_giorgio_gains_fervor_when_hit(self):
        giorgio = make_giorgio()
        giorgio.current_fervor = 0
        corrado = make_corrado()
        apply_hit(corrado, giorgio, SKILLS["ENEMY_STRIKE"], 0)
        self.assertEqual(giorgio.current_fervor, FERVOR_GAIN_GIORGIO_HIT)
        self.assertTrue(giorgio.current_hp < 380)


class Sessione04FixTest(unittest.TestCase):
    """Le tre correzioni di bilanciamento della Sessione 04."""

    def test_giudizio_della_verga_breaks_the_balestriere(self):
        """La debolezza a FAITH_HOLY del Balestriere ora ha una chiave che la apre."""
        ubaldo = make_ubaldo()
        ubaldo.current_fervor = ubaldo.max_fervor
        bal = make_balestriere()
        self.assertEqual(bal.weakness, Element.FAITH_HOLY)

        # Prima della Sessione 04 nessuna abilita' del party era FAITH_HOLY offensiva:
        # il Muro della Fede e' un supporto che non tocca lo scudo.
        self.assertEqual(SKILLS["MURO_DELLA_FEDE"].target, 'ALLY')

        dmg = apply_hit(ubaldo, bal, SKILLS["GIUDIZIO_DELLA_VERGA"], 0)
        self.assertEqual(bal.current_shield, 2)          # 3 -> 2: lo scudo si erode
        self.assertEqual(dmg, 103)                       # (35 + (95-26)//2) * 1.5

        apply_hit(ubaldo, bal, SKILLS["GIUDIZIO_DELLA_VERGA"], 0)
        apply_hit(ubaldo, bal, SKILLS["GIUDIZIO_DELLA_VERGA"], 0)
        self.assertEqual(bal.current_shield, 0)
        self.assertTrue(bal.is_broken())

    def test_bastione_azzurro_intercepts_hits_on_the_fragile(self):
        """San Giorgio incassa al posto di Antonio, che altrimenti moriva al round 3."""
        giorgio, antonio = make_giorgio(), make_antonio()
        fante = make_fante()

        # Senza guardia il colpo arriva ad Antonio.
        apply_hit(fante, antonio, SKILLS["ENEMY_STRIKE"], 0, giorgio=giorgio)
        self.assertLess(antonio.current_hp, antonio.max_hp)
        self.assertEqual(giorgio.current_hp, giorgio.max_hp)

        # Con il Bastione alzato il colpo viene deviato su Giorgio.
        antonio_hp = antonio.current_hp
        giorgio.start_guard()
        self.assertTrue(giorgio.is_guarding())
        apply_hit(fante, antonio, SKILLS["ENEMY_STRIKE"], 0, giorgio=giorgio)
        self.assertEqual(antonio.current_hp, antonio_hp)      # illeso
        self.assertLess(giorgio.current_hp, giorgio.max_hp)   # ha parato lui

        # E la parata gli genera Fervore (Sez. 12A GDD).
        self.assertGreater(giorgio.current_fervor, 54)

    def test_guard_lasts_only_its_own_round(self):
        giorgio = make_giorgio()
        giorgio.start_guard()
        tick_status(giorgio)
        self.assertFalse(giorgio.is_guarding())

    def test_guard_duration_scales_with_boost(self):
        """Prima della revisione, il Boost sul Bastione costava fino a 115 Fervore per nulla."""
        for boost, attesa in ((0, 1), (1, 2), (2, 3), (BOOST_MAX_LEVEL, 4)):
            giorgio = make_giorgio()
            giorgio.start_guard(boost)
            self.assertEqual(giorgio.guard_turns, attesa)


class EnemyAiTest(unittest.TestCase):
    """Mob comune: colpisce il bersaglio con meno Difesa (Sezione 13D GDD)."""

    def test_targets_lowest_defense_hero(self):
        party = [make_ubaldo(), make_giorgio(), make_antonio()]
        best = min((h for h in party if h.is_alive()), key=lambda h: h.effective_defense())
        self.assertEqual(best.name, "Sant'Antonio")     # def 28 < 45 < 80

    def test_dead_heroes_are_not_targeted(self):
        party = [make_ubaldo(), make_giorgio(), make_antonio()]
        party[2].current_hp = 0
        best = min((h for h in party if h.is_alive()), key=lambda h: h.effective_defense())
        self.assertEqual(best.name, "Sant'Ubaldo")


if __name__ == "__main__":
    unittest.main(verbosity=2)
