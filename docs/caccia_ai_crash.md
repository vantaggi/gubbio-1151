# La caccia ai crash

Richiesta di Cioti (6 nov 2026): trovare *tutti* i crash possibili (colori, sprite, memoria...), non solo quelli
che capitano giocando. Decisione D032 in [metodo/DECISIONI.md](metodo/DECISIONI.md).

## Perche' in automatico e non sull'emulatore del PC

I crash del GBA con Butano sono quasi tutti un tetto fisso che si supera: 256 colori di sprite, 128 sprite,
1024 tile di sprite, 32 blocchi da 2 KB per tile e mappe dei fondali, 4 fondali, lo stack in IWRAM. Si superano
solo in certe combinazioni (questa area, con questa folla, piu' una battaglia, piu' il menu aperto). Un umano
in un'ora ne prova qualche decina; il banco in cloud ne prova migliaia a ogni fusione, sempre le stesse, e si
accorge di un tetto *prima* che si superi. Al PC resta una sessione breve per le cose che deve vedere un
umano (in fondo).

## Le tre reti

1. **Gli assert nel log** (sempre, anche nel gioco vero: `include/limiti.h`). Prima, un errore di Butano
   compariva solo a schermo e una prova automatica poteva passare senza vederlo. Ora la callback degli assert
   scrive `ASSERT scattato area A x X y Y frame F` nel log di mGBA; il banco (`tools/banco_mgba.c`) lascia
   passare 30 frame, salva la schermata d'errore (col messaggio di Butano) e si ferma. `tools/prove_mgba.py`
   la mette in `build_banco/crash/<prova>.png` e la prova fallisce. Il banco fa fallire anche gli errori di
   mGBA (righe `MGBA ...`, es. accessi a memoria non valida) e un gioco che non chiama piu'
   `bn::core::update()` per 20 000 frame (`!! bloccato`).
2. **I limiti** (`-DGUBBIO_LIMITI`, solo per le prove). A ogni frame l'uso di dodici risorse: sprite, tile e
   pezzi di tile degli sprite, colori di sprite e fondali, matrici affini, fondali, tile dei fondali, celle
   delle mappe, blocchi VRAM dei fondali, stack IWRAM, EWRAM allocata. A ogni nuovo picco una riga
   `LIMITI picco NOME USO su TOT (P%)`; la prova fallisce se una risorsa passa il **90%** (eccezione:
   `fondali` 4 su 4 nei titoli e nelle cutscene e' voluto). Conta l'uso di due frame di fila: Butano rende la
   VRAM lasciata solo dentro `bn::core::update()` (o subito, se serve), quindi nel frame del cambio d'area
   area vecchia e nuova si sommerebbero senza stare mai davvero insieme. Ogni 7200 frame `LIMITI vivo`.
3. **Il giocatore scimmia** (comando `caso SEME N` del banco). Tasti a caso ma "da giocatore": croce tenuta
   (anche in diagonale, a volte di corsa), A a raffica (dialoghi, cartelli, menu, battaglie), una freccia e A
   (voci dei menu), B, Start (pausa, salvataggi), Select (promemoria), L+Select (pannello di debug), L/R. Mai
   A+B+Select+Start. Lo stesso seme rifa' gli stessi tasti, quindi un crash trovato si rifa' uguale.

## Le prove (tests/mgba/prove.json)

| prova | modo | cosa gioca la scimmia |
|---|---|---|
| caccia_vero_1, _2 | 0 | il gioco vero: titolo, partita nuova, prologo, citta', menu, battaglie della storia |
| caccia_slot | 15 | il titolo con due slot gia' scritti: Continua, «Dove eravamo», salva e carica |
| caccia_salti_1..4 | 13 | la partita (come il 14) e in piu', ogni 1500 frame, un salto al prossimo varco del mondo (in giro tutte le aree e tutti gli ingressi, dove porta il varco vero) e ogni tre salti una battaglia lasciando la mappa piena, giocata coi tasti a caso |
| rete | 13 | `-DGUBBIO_PROVA_ASSERT`: un assert voluto al frame 600. Se questa fallisce, le altre non vedrebbero un crash |

Ogni caccia dura 100 000 frame (quasi mezz'ora di gioco) in circa 35 s. In piu' le prove di sempre (camminata,
storia, prologo, folla, palette_*) hanno anche `-DGUBBIO_LIMITI`.

    python3 tools/prove_mgba.py caccia_salti_1     # una
    python3 tools/prove.py --tutte                 # tutto, prima di fondere (il giro corto salta le "lunghe")

Per cercare piu' a fondo: un altro seme o piu' frame nel copione (`caso 5 300000`).

## Esito del 6 nov 2026 (main 2970f8c piu' questo lavoro)

Sette giri da 100 000 frame e le 13 prove di sempre: **0 assert, 0 errori di mGBA, 0 blocchi**. La rete
prende l'assert voluto e lo fotografa. Picchi piu' alti, da tenere d'occhio:

| risorsa | picco | dove |
|---|---|---|
| blocchi VRAM dei fondali | 28 su 32 (87%) | Teatro Romano (969 tile, l'area piu' pesante) |
| tile dei fondali | 1408 su 1664 (84%) | Teatro Romano |
| colori degli sprite | 208 su 256 (81%) | Piazza Quaranta Martiri con la folla |
| sprite | 84 su 128 (65%) | |
| tile degli sprite | 646 su 1024 (63%) | |
| stack IWRAM | 12 236 su 21 736 byte (56%) | |
| colori dei fondali | 144 su 256 (56%) | |

Il Teatro Romano e' il primo candidato a un crash futuro: un monumento o un tile in piu' in quell'area, o un
fondale in piu' sopra la sua mappa, e si passa il 90%.

## La sessione breve sul PC (per Cioti)

Quello che il banco non vede: se si *vede* bene, se si *sente* bene, se e' lento a occhio.

1. La ROM dell'ultima fusione in mGBA, pannello di debug con **L+Select**.
2. Teatro Romano: entrarci da tutti gli ingressi, aprire la pausa, parlare con chi c'e'. Guardare che i
   fondali non si sporchino.
3. Piazza Quaranta Martiri con la folla: una battaglia, poi la pausa e la mappa.
4. Un cambio d'area di corsa avanti e indietro (sfarfallii, tile sbagliati per un frame).
5. Se compare una schermata rossa d'errore: una foto dello schermo basta (il messaggio dice gia' file e riga).
