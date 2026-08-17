# PIANO DI IMPLEMENTAZIONE: COMBO DEI TRE CERI (Sezione 12C GDD)

> Prodotto nella Sessione 07 da un agente di analisi. **Non ancora implementato.**
> Il GDD tabella solo *eroi coinvolti* + *effetto in prosa*: nessun numero, nessuna abilita'
> richiesta. Tutto il resto e' ricostruzione, segnalata come tale.

## 1. Attivazione

Soglia = `fervor_percent() >= 50` sulla **scala normalizzata** (Ubaldo 90, Giorgio 60, Antonio 105
assoluti), coerente con la riconciliazione della Sessione 02b. Conseguenza voluta: con i Fervori
d'ingresso 80/45/20% **nessuna combo e' disponibile al round 1**.

| Combo | Eroi | Abilita' richieste | Soglia |
| :-- | :-- | :-- | :-- |
| Alzata Trionfale | tutti e tre | Giudizio + Fendente + Fuoco | **100%** |
| Lancia Incandescente | Giorgio + Antonio | Fendente + Fuoco | 50% |
| Egida della Purificazione | Ubaldo + Giorgio | Muro della Fede + Bastione Azzurro | 50% |
| Giudizio del Monte Ingino | Ubaldo + Antonio | Giudizio + Fuoco | 50% |

Una sola combo per round, priorita' per ordine di tabella: l'Alzata contiene le abilita' richieste
sia dal Giudizio sia dalla Lancia, quindi senza precedenza non scatterebbe mai. Via d'uscita per il
giocatore: basta scegliere *Attacco* con un eroe per far fallire la combo di rango superiore.

## 2. LA SCOPERTA PRINCIPALE: Alzata = Mossa Suprema dei Tre Ceri

Il GDD usa **due nomi diversi per due cose diverse**, finora confuse in una sola:

* Sez. 20A pilastro 3: "Boost MAX (100 Fervore): attiva l'**Abilita' Suprema del Cero**" —
  individuale, costo assoluto 100. **Gia' implementata, resta com'e'.**
* Sez. 12A: "le **Mosse Supreme dei Tre Ceri** richiedono 100 Fervore e consumano l'intera barra" —
  plurale collettivo. La Sez. 12C descrive esattamente una mossa che "richiede 100 Fervore su tutti
  i membri": **l'Alzata Trionfale E' quella mossa.**

Con questa lettura il conflitto 12A/12C si dissolve, e la clausola **"consuma l'intera barra"** —
che **non e' mai stata implementata** (`_execute_action` spende `100 + costo`, lasciando 19 Fervore
a Ubaldo) — trova finalmente un referente: e' il `fervor_cost_percent = 100` dell'Alzata.

**Policy di esclusione proposta:** `fervor_boost_level == 0` come requisito di partecipazione.
Premere R dichiara "voglio la mia azione potenziata, non la combo".

## 3. Dove va il rilevamento

All'ingresso in `EXECUTE_ROUND_ACTIONS`, **prima** di `_queue_enemy_actions()` e
`_sort_action_queue()`. Tre vincoli fissano quel punto: la sostituzione cambia `calculated_speed`
(quindi prima dell'ordinamento); la coda e' di soli eroi (nessun filtro su `is_enemy`); e il Fervore
va letto **pre-spesa**, altrimenti la combo dipenderebbe dall'ordine di velocita'.

`_detect_combo()` va tenuto **`const` e puro**: cosi' l'HUD puo' anticipare la combo gia' in fase di
input, evitando che scatti senza preavviso. Il **leader** e' il partecipante piu' veloce; la combo
occupa il suo posto in coda, gli altri vengono rimossi. `_sort_action_queue()` e
`_execute_all_queued_actions()` restano invariati.

## 4. Modifica al motore richiesta

`calculate_damage` sceglie la formula in base a `skill.element`. La **Lancia Incandescente** ha
bisogno dell'Attacco fisico di Giorgio (90) con elemento **FLAME**, per ribaltare la resistenza al
fisico di Corrado sfruttandone la debolezza al fuoco. Serve disaccoppiare formula ed elemento, ed
estendere `armor_pierce_percent` al ramo mistico (per "azzera le difese" dell'Alzata).
**Cambio a comportamento invariato:** tutte le skill esistenti hanno pierce 0.

## 5. Conflitti col resto del sistema

* **Loop di Fervore (pre-esistente, amplificato):** Antonio guadagna +10 **per ogni nemico che
  brucia, ogni round**. Con 6 nemici sono +60/round su 210. Lancia e Alzata applicano Ustione ad
  area, rendendo il loop la strategia dominante. **Raccomandazione: limitare il guadagno a una
  volta per round**, indipendentemente dal numero di bersagli in fiamme.
* **"Converte i debuff del party": effetto oggi nullo.** Nessun nemico applica debuff, gli eroi non
  vanno mai in BREAK (`max_shield = 0`), TERRIFIED e STUNNED non sono implementati.
* **"Devia il 100% dei proiettili": non esprimibile.** Non esiste il concetto di attacco a distanza
  (`EnemyStats` non ha `is_ranged`, il Balestriere colpisce con lo stesso `ENEMY_STRIKE` del Fante).
* **"Acceca, -50% Precisione":** non esiste un tiro per colpire. Reso come dimezzamento del danno
  in uscita, identico a valore atteso.
* **Timeline:** `predicted_order()` cerca l'azione di ogni eroe e, non trovandola, ricade sulla
  velocita' base: i partecipanti assorbiti continuerebbero a comparire come se agissero da soli.
  **Va corretto o la timeline mente al giocatore.**
* **`tests/test_battle_engine.py`** va aggiornato in parallelo: e' un port fedele dichiarato.

## 6. Decisioni che spettano al designer

1. **Accettare o respingere la lettura "Alzata = Mossa Suprema dei Tre Ceri"** (punto 2). E' la
   scelta a impatto piu' alto: se respinta, il conflitto 12A/12C resta aperto e "consuma l'intera
   barra" resta senza implementazione.
2. Le **abilita' richieste** per ciascuna combo sono dedotte dalla prosa, non dal GDD.
3. **Costo** 50% del pool per le duo, 100% per l'Alzata: il GDD indica solo la soglia, mai il costo.
4. `fervor_boost_level == 0` come requisito di partecipazione.
5. Tutti i **valori numerici** degli effetti sono un punto di partenza da collaudare.
6. **Combo annullata se un partecipante muore** prima dell'esecuzione, con perdita del turno per
   gli altri.
