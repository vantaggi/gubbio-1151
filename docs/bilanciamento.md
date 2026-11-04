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

## Risultati (200 semi)

| Scontro | forte | medio | debole |
| :-- | :-- | :-- | :-- |
| Pattuglia (liv 1) | 100%, 5 round | 100%, 6 | 98%, 23 |
| Imboscata (liv 3) | 100%, 4 | 100%, 3 | 100%, 6 |
| Spettri (liv 4) | 100%, 4 | 100%, 3 | 100%, 12 |
| Corrado (liv 5) | 100%, 6 | **59%**, 7 | 0% |
| Corrado (liv 6, con quest e scudo in meno) | 100%, 6 | **74%**, 6 | 0% |

Obiettivi: scontri normali vinti oltre il 90% in 3-6 round (forte e medio); Corrado 55-75% per il pilota medio al livello atteso; nessun livello in cui Corrado si batte con il solo Attacco. Tutti rispettati. Lo scudo in meno (Q-SM01 o Rufino) vale circa 10 punti di percentuale al livello 5.

## Da rifare dopo
- Le quest ora sono giocabili (SV2c): ricontrollare con le quest fatte una alla volta e non tutte all'inizio. Q-SP01 aggiunge una battaglia (l'infiltrato, con le tre spie umbre degli Stradoni: 81 punti): con le tre quest e l'infiltrato si arriva a Corrado con 316 + 165 + 81 = 562 punti, ancora al livello 6 (il 7 è a 680); lo prova `livello_con_l_infiltrato()` in `src/autotest_quest.cpp`.
- La regola "Ubaldo non usa il cibo da DIGIUNO a B-05" (ora nel codice, `storia::a_digiuno()`) tocca solo gli oggetti, che i piloti non usano: nessun effetto qui.
- Prova a mano di Cioti: se Corrado risulta troppo duro o troppo facile, si tocca solo la sua scheda in `battaglia_dati.h` e si rigenera.
