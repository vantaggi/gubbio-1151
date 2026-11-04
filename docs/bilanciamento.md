# Bilanciamento della v1 (F8)

3 nov 2026. Strumento: `tools/bilanciamento.py` (gioca il mirror Python della battaglia, identico al C++, ai livelli veri della storia). Obiettivi controllati da `tests/test_bilanciamento.py`.

## Piloti
- **forte**: il pilota del mirror, quasi ottimo.
- **medio**: un giocatore plausibile, sceglie a caso fra le mosse sensate (abilità di firma, Muro della Fede quando qualcuno è sotto metà, qualche carica). È il riferimento per la difficoltà.
- **debole**: solo l'Attacco, sempre.
Nessun pilota usa gli oggetti: chi gioca con Crescia e Biscotti sta meglio dei numeri qui sotto.

## Cosa è cambiato
Prima di F8 a Corrado si arrivava al **livello 3** (55 + 36 + 60 = 151 punti) e il pilota medio lo batteva il 44% delle volte. L'esperienza dei nemici è salita (`include/progressione.h`, ESPERIENZA_NEMICO = 35, 45, 200, 27, 60), le statistiche no:

| Scontro | Esperienza | Livello all'arrivo | Livello all'arrivo con le 3 quest |
| :-- | --: | --: | --: |
| Pattuglia Perugina | 115 | 1 | 3 |
| Imboscata agli Stradoni | 81 | 3 | 4 |
| Spettri del Dubbio | 120 | 4 | 5 |
| Corrado | 200 | 5 | 6 |

Ogni quest dà **55 punti** a ogni Santo (`progressione::ESPERIENZA_QUEST`, data da `storia::consegna_quest()`; `tools/bilanciamento.py` legge il numero dal C++). Lo scudo in meno passa da `scudi_in_meno` del mirror, la stessa manopola del C++.

## F10: i nemici che mancavano (4 nov 2026)
Tre incontri nuovi, coi nemici nuovi in `include/battaglia_dati.h` (il Guerriero della Roccia: 520 PV, Difesa 62, resiste al fisico, debole alla Fiamma; l'infiltrato: 300 PV, rapido, colpisce chi ha meno PV come le spie):

| Scontro | Nemici | Esperienza | Quando |
| :-- | :-- | --: | :-- |
| Guerrieri della Roccia (B-03) | 2 Guerrieri della Roccia | 40 | obbligatorio, fra gli Spettri e Corrado, a metà della scena B-03 |
| Guardia della fornace (Q-SM01) | 1 Guerriero della Roccia | 20 | facoltativo, tre volte (una per blocco di ferro), dall'ultimatum |
| L'infiltrato delle Logge (Q-SP01) | l'infiltrato e 2 spie umbre | 84 | facoltativo, dal digiuno, con i tre indizi |

L'esperienza dei nemici nuovi (`ESPERIENZA_NEMICO` = 35, 45, 200, 27, 60, **20, 30**) è bassa di proposito, perché i livelli all'arrivo da Corrado non cambino:
- **senza quest**: 115 + 81 + 120 + 40 = **356** punti, livello **5** (il 6 è a 470);
- **con le tre quest e tutte le facoltative**: 356 + 165 + 3 × 20 + 84 = **665** punti, livello **6** (il 7 è a 680: restano 15 punti di margine, e un'altra guardia da 20 basterebbe a passare al 7; lo provano `livello_con_un_altra_guardia()` in `src/autotest_quest.cpp` e `test_negativa_facoltative_troppo_generose`).

`tools/bilanciamento.py` conta le facoltative tutte all'inizio nello scenario con le quest (il caso peggiore per i livelli) e misura le facoltative al livello più basso con cui si possono affrontare: la fornace al livello 1, l'infiltrato al 3 (il digiuno comincia dopo la Pattuglia). Il mirror gioca sempre in tre: al livello 1 una guardia della fornace affrontata prima di salvare Antonio si combatte in due, senza il fuoco che rompe lo scudo (più lunga, da provare a mano).

## F10: i Ceri risvegliati (4 nov 2026)
Da A1-08 (`CERI_RISVEGLIATI`, accesa a fine scena) ogni Santo entra in battaglia con **15 punti percentuali** di Fervore in più del suo massimo, mai oltre il massimo: Ubaldo 80 → 95%, Giorgio 45 → 60%, Antonio 20 → 35% (`battaglia::FERVORE_CERI`, `storia::ceri_accesi()`; nel mirror la manopola `ceri`, come `scudi_in_meno`). È il «Fervore che parte più alto» di `docs/bandiere_da_fare.md`: non tocca il massimo né il guadagno durante lo scontro.

Nell'ordine della storia la bandiera viene **prima dei Guerrieri di B-03 e di Corrado** (A1-08 → A1-09 → B-01...B-04), quindi le loro righe qui sotto sono misurate coi Ceri (`DOPO_I_CERI` di `tools/bilanciamento.py`). Gli Spettri si combattono dentro A1-08, prima che la bandiera si accenda: senza. Le facoltative (guardie, infiltrato) restano misurate senza, al livello più basso, cioè prima del rito.

Effetto su Corrado (pilota medio, 200 semi): al livello 5 dal **59%** al **61%**; al livello 6 con le quest e lo scudo in meno dal 74% al **75%**, ancora dentro gli obiettivi. Con 10 punti invece di 15 il pilota forte coi Guerrieri passava a 8 round (fuori dai 3-6): con 15 restano 4. Anche a Fervore pieno Corrado al livello 5 non supera il 66%, e al livello 3 coi Ceri resta sotto il 55% (`test_negativa_corrado_troppo_presto`).

Le firme: 200 battaglie in più in `ATTESE_CERI` (Corrado e i Guerrieri, 50 semi × 2 piloti), confrontate col C++ da `src/autotest_battaglia.cpp`; le 700 di prima non cambiano.

## Risultati (200 semi)

| Scontro | forte | medio | debole |
| :-- | :-- | :-- | :-- |
| Pattuglia (liv 1) | 100%, 5 round | 100%, 6 | 98%, 23 |
| Imboscata (liv 3) | 100%, 4 | 100%, 3 | 100%, 6 |
| Spettri (liv 4) | 100%, 4 | 100%, 3 | 100%, 12 |
| Guerrieri della Roccia (liv 5, coi Ceri) | 100%, 4 | 100%, 5 | 100%, 24 |
| Corrado (liv 5, coi Ceri) | 100%, 6 | **61%**, 7 | 0% |
| Corrado (liv 6, coi Ceri, con quest e scudo in meno) | 100%, 6 | **75%**, 6 | 0% |
| Guardia della fornace (liv 1) | 100%, 4 | 100%, 3 | 100%, 18 |
| L'infiltrato (liv 3) | 100%, 4 | 100%, 4 | 100%, 8 |

Obiettivi: scontri normali vinti oltre il 90% in 3-6 round (forte e medio); Corrado 55-75% per il pilota medio al livello atteso; nessun livello in cui Corrado si batte con il solo Attacco. Tutti rispettati. Lo scudo in meno (Q-SM01 o Rufino) vale circa 8-10 punti di percentuale al livello 5 (coi Ceri 61 → 69%); i Ceri circa 2.

## Da rifare dopo
- Le quest ora sono giocabili (SV2c): ricontrollare con le quest fatte una alla volta e non tutte all'inizio. Con F10 le battaglie facoltative sono quattro (tre guardie delle fornaci, l'infiltrato con le sue spie: 144 punti) e B-03 ne aggiunge una obbligatoria (40): con tutto si arriva a Corrado con 665 punti, ancora al livello 6; lo prova `livello_con_l_infiltrato()` in `src/autotest_quest.cpp`.
- La regola "Ubaldo non usa il cibo da DIGIUNO a B-05" (ora nel codice, `storia::a_digiuno()`) tocca solo gli oggetti, che i piloti non usano: nessun effetto qui.
- Prova a mano di Cioti: se Corrado risulta troppo duro o troppo facile, si tocca solo la sua scheda in `battaglia_dati.h` e si rigenera.
