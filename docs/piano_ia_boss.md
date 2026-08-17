# PIANO DI IMPLEMENTAZIONE: IA DEI BOSS (Sezione 26 GDD)

> Prodotto nella Sessione 07 da un agente di analisi. **Non ancora implementato.**
> Stato attuale: `_queue_enemy_actions()` in `src/battle_scene.cpp` applica a *tutti* i nemici,
> boss inclusi, la sola regola da mob comune della Sez. 13D ("colpisci chi ha meno Difesa").

---

## 1. Architettura proposta: tabella di regole, zero codice per-boss

Nuovo header `include/enemy_ai.h`. Le condizioni si valutano **in ordine, prima corrispondenza
vince**, sullo stile di `SKILLS[]`.

```cpp
enum class AiCond      : uint8_t { ALWAYS, ROUND_EQ, ROUND_GE, ROUND_ODD, ROUND_EVEN,
                                   SELF_HP_BELOW_PCT, ALLIES_ALIVE_LE, ALLIES_ALIVE_GE };
enum class AiLimit     : uint8_t { REPEATABLE, ONCE_PER_ROUND, ONCE_PER_BATTLE };
enum class AiTargeting : uint8_t { LOWEST_DEFENSE, LOWEST_HP, SPECIFIC_HERO, ALL_HEROES, SELF, ALLY_OTHER };
enum class AiSideEffect: uint8_t { NONE, SPAWN_ALLIES, BERSERK, BACK_ROW };

struct AiRule {
    AiCond cond;   int8_t param;      // due condizioni in AND
    AiCond cond2;  int8_t param2;     // AiCond::ALWAYS = inutilizzata
    AiLimit limit;
    SkillId skill;                    // SkillId::COUNT = transizione pura, lo scan prosegue
    AiTargeting targeting; int8_t target_param;
    AiSideEffect effect;   int8_t effect_param; int8_t effect_param2;
};

struct AiScript { uint8_t first_rule; uint8_t rule_count; uint8_t actions_per_turn; };
constexpr int MAX_AI_RULES_PER_SCRIPT = 8;
```

**Idea che elimina i contatori per-boss:** l'indice della regola dentro il proprio script (0-7) e'
anche l'indice di bit in due maschere sull'unita', `ai_flags_battle` e `ai_flags_round`.
`ONCE_PER_BATTLE` testa/setta la prima, `ONCE_PER_ROUND` la seconda (azzerata in
`_end_of_round_ticks`). Nessun campo `once_bit` in tabella. Vincolo: max 8 regole per script,
da imporre con `static_assert`.

**Il mob comune diventa un dato come gli altri:** `AI_MOB_COMUNE` = una sola regola
`{ALWAYS, REPEATABLE, ENEMY_STRIKE, LOWEST_DEFENSE}`, `actions_per_turn = 1`. La regola della
Sez. 13D sparisce dal codice.

Il valutatore (~45 righe) sostituisce il corpo di `_queue_enemy_actions()` ed e' unico per tutti:

```
per ogni nemico vivo e non in BREAK:
  ++ai_round
  ripeti actions_per_turn volte:
    per r in [first_rule, first_rule + count):
      se una delle due condizioni non regge -> continua
      se limit != REPEATABLE e il bit (r - first_rule) e' gia' settato -> continua
      setta il bit nella maschera corrispondente
      applica rule.effect (spawn / berserk / back_row)
      se rule.skill == SkillId::COUNT -> continua lo scan (transizione pura, azione non spesa)
      risolvi il bersaglio, push su _action_queue, esci dallo scan
```

Campi nuovi su `EnemyStats`: `ai_script`, `next_phase_enemy_id` (-1 = nessuna), `element_rules[2]`.
Campi nuovi su `BattleUnit`: `ai_script`, `ai_round`, `ai_flags_battle`, `ai_flags_round`, copia
delle `element_rules`, piu' i campi di buff/status del punto 3.

---

## 2. Le quattro routine

**Corrado di Spoleto** (Scudo 4): turno 1 `Scudo di Forgia` su se' stesso (una volta per
battaglia); turni pari `Martello d'Assedio` su San Giorgio; sempre `Colpo` su chi ha meno Difesa.
Realizza lo "schema alternato attacco pesante + buff" che la Sez. 13D pretende dai mini-boss.

**Valerio di Cagli** (Scudo 3): sotto il 50% di HP arretra e evoca due Balestrieri (due regole a
transizione pura, quindi nello stesso turno agisce comunque); turni dispari `Nube di Pece` su
tutto il party; sempre `Dardo di Cerbottana` su Sant'Ubaldo.

**Gemelli della Tempesta** (Scudo 3 ciascuno): finche' il fratello vive, Foligno gli raddoppia la
velocita' con `Folata di Vento` e Todi tira `Raffica Fulminea` a 3 colpi; alla morte di uno,
il superstite entra in `BERSERK` (+50% Attacco permanente e resistenza all'elemento del caduto).

**Monaldo / Avatar del Grifo:** le tre fasi **non** sono uno stato dell'IA ma **tre righe distinte
di `ENEMIES[]`** legate da `next_phase_enemy_id`. A 0 HP, se il campo e' valorizzato, l'unita' non
muore: viene riscritta con le statistiche della fase successiva (HP pieni, nuovo scudo, nuovo
script, `ai_round = 0`, flag azzerati). Nessun codice speciale nella morte.
La Fase 2 e' **immune al fisico**, il che rende letterale il "richiede il Fuoco di Antonio" del GDD.

---

## 3. Abilita' nemiche nuove (13) per `SKILLS[]`

`SkillData` va esteso con `bool is_area` (riusa il ramo AoE gia' scritto per il Boost MAX),
`int hit_count` e `int effect_param`. Tutte hanno `fervor_cost = 0`.

| Skill | Elemento | Bersaglio | Numeri |
| :-- | :-- | :-- | :-- |
| Scudo di Forgia | NONE | se' | `SELF_DEF_UP`, param 50, prio +6 |
| Martello d'Assedio | PHYSICAL | singolo | power 220, pierce 25, prio -4 |
| Richiamo dei Mercenari | NONE | se' | prio +5 |
| Nube di Pece | VOID_SHADOW | area | magic 20, `POISON` |
| Dardo di Cerbottana | PHYSICAL | singolo | power 90, prio +2 |
| Folata di Vento | NONE | alleato | `ALLY_SPEED_UP` 100, 1 round, prio +8 |
| Raffica Fulminea | PHYSICAL | singolo | power 60, hit_count 3, prio +2 |
| Spadone d'Ombra | VOID_SHADOW | area | magic 45 |
| Contrattacco Marziale | NONE | se' | `COUNTER_STANCE` 120, 1 round, prio +7 |
| Tempesta di Sangue | VOID_SHADOW | area | magic 55 |
| Artiglio d'Ombra | VOID_SHADOW | singolo | magic 40 |
| Ruggito dell'Ingino | VOID_SHADOW | area | magic 30, `TERROR` |
| Apocalisse dei Colli | VOID_SHADOW | area | magic 140, prio -6 |

**Il Veleno segue la decisione della Sessione 04 sull'Ustione: danno ASSOLUTO** (20% del Potere
Mistico del lanciatore, 3 turni, non cumulabile), mai percentuale sugli HP massimi, altrimenti si
ripresenta identico il rilievo 1 gia' corretto.
Il Contrattacco scatta solo su elemento PHYSICAL da un eroe, e va protetto da un flag di rientro:
un contrattacco non contrattacca mai.

---

## 4. Immunita' CONDIZIONATA di Corrado (Sez. 26A)

Oggi Corrado ha `resistance = PHYSICAL`, cioe' una resistenza fissa x0.5: non e' l'immunita' del
GDD. La coppia `weakness`/`resistance` non puo' esprimere una condizione e **non va sostituita**
(serve allo Shield Break), ma **affiancata** da una tabellina di eccezioni:

```cpp
constexpr int ELEMENT_IMMUNE_PERCENT = 0;
enum class ElementGate : uint8_t { ALWAYS, TARGET_HAS_BURN, TARGET_IS_BROKEN };
struct ElementRule { ElementType element; ElementGate gate; int percent_closed; int percent_open; };

// Corrado: il taglio non lo scalfisce finche' l'Ustione non lo surriscalda.
{ ElementType::PHYSICAL, ElementGate::TARGET_HAS_BURN, 0, 100 }
// Avatar del Grifo fase 2 ("fuori portata"): cancello sempre chiuso.
{ ElementType::PHYSICAL, ElementGate::ALWAYS,          0, 0   }
```

`element_multiplier_percent()` scandisce prima le 2 regole del bersaglio, poi cade sulla logica
attuale. Due punti del codice attuale non reggono e vanno corretti:
* `calculate_damage()` finisce con `return damage < 1 ? 1 : damage`: con moltiplicatore 0
  restituirebbe comunque 1. Serve un'uscita anticipata **prima** del clamp.
* `_apply_hit()` a danno 0 deve saltare anche l'erosione dello Scudo e i guadagni di Fervore, e
  segnalare "IMMUNE" all'HUD: senza feedback il giocatore legge l'immunita' come un bug.

Sulla frase "in BREAK la resistenza al fuoco scende a zero": Corrado e' gia' **debole** al fuoco
(x1.5), quindi non puo' riferirsi al triangolo elementale. Lettura consigliata: e' la descrizione
narrativa del dimezzamento di `magic_resist` che il BREAK **applica gia'**. Nessuna regola nuova.

---

## 5. DECISIONI CHE SPETTANO AL DESIGNER

1. **Azioni per turno: 1 o 2?** La Sez. 26 descrive routine da 1 azione; la Sez. 13D assegna 2
   ai mini-boss e 3 alla Fase 2 di Monaldo. Seguendo la 13D **il danno in uscita di Corrado
   raddoppia** rispetto al collaudo della Sessione 04: va ritarato tutto il duello.
2. **`StatusEffect::POISONED` non esiste.** Lo richiede la Sez. 26B e i Biscotti della Sez. 8E
   dichiarano di curarlo, ma la Sez. 12D non lo elenca. Va aggiunto all'enum e alla Sez. 12D.
3. **Non esiste un elemento fulmine/tempesta.** I Gemelli sono "della Tempesta" ma `ElementType`
   ha solo PHYSICAL / FAITH_HOLY / FLAME / VOID_SHADOW. Aggiungere `STORM` obbligherebbe a
   ridefinire debolezze e resistenze dell'intero bestiario.
4. **"Assorbe l'elemento del compagno caduto"**: acquisisce resistenza a quell'elemento (scelto,
   solo dati) oppure i suoi attacchi diventano di quell'elemento (alternativa).
5. **RISCHIO DI SOFTLOCK.** Se Sant'Antonio muore prima di applicare l'Ustione, Corrado diventa
   invulnerabile a San Giorgio; se cadono sia Antonio sia Ubaldo nella Fase 2, il Grifo e'
   inattaccabile. Serve una valvola: l'Ustione persiste gia' oltre la morte del lanciatore
   (`burn_damage_per_stack` e' fotografato all'applicazione), oppure un consumabile che la applichi.
6. **Formazione e "colonna posteriore".** Il motore non ha sistema posizionale. Proposta a costo
   quasi zero: generalizzare ai nemici il redirect gia' scritto per il Bastione Azzurro, cosi' i
   Balestrieri evocati intercettano i colpi a Valerio. L'alternativa (vere righe) e' un lavoro a se'.
7. **Durate mai indicate dal GDD:** Scudo di Forgia (scelto: permanente, una volta), Folata di
   Vento (1 round), Contrattacco Marziale (1 round).

---

## 6. Lavoro collaterale obbligatorio

* `ENEMIES[]` non contiene Valerio, i due Gemelli, ne' le tre fasi di Monaldo: servono statistiche
  secondo la Sez. 13D (mini-boss 1520 HP, Fase 1 2280, Fase 2 3800) e i relativi `ENCOUNTERS[]`.
* Lo spawn di Valerio va protetto contro `MAX_ENEMIES_PER_ENCOUNTER = 6`.
* `calculated_speed` deve usare `effective_speed()` (velocita' + Folata) e **`predicted_order()`
  va allineato**, altrimenti la timeline mente al giocatore.
* `tests/test_battle_engine.py` e' un port fedele dichiarato: valutatore di regole, immunita'
  condizionata e nuovi status vanno rispecchiati, o la suite smette di validare il motore reale.
