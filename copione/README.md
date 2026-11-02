# Copione della v1: Prologo, Atto I e Bottaccione

Bozza del 1 novembre 2026, per la fase F6 del [piano di ripartenza](https://claude.ai/artifact/XWPo2448pceE3Ebb7Frvv3). Ambito: «Atto I e Bottaccione». Lingua del gioco: italiano. Nessun codice: è il testo da cui F6 genererà le tabelle (`testi.h` di F1, bandiere, script).

## File

| File | Contenuto | Battute |
| :-- | :-- | --: |
| [00_prologo.md](00_prologo.md) | Avvio, la vetrata chiara, la mappa che annerisce | 10 |
| [01_atto_I.md](01_atto_I.md) | Dall'ultimatum al rito della Basilica e alla visione | 122 |
| [02_bottaccione_epilogo.md](02_bottaccione_epilogo.md) | Il dungeon, Corrado, il rientro, la terza alba, la vetrata | 61 |
| [03_npc_ambiente.md](03_npc_ambiente.md) | NPC d'ambiente delle 14 aree, per fase | 45 |
| [04_quest.md](04_quest.md) | Le 3 quest scelte: il Ferro (San Martino), le Erbe (Sant'Andrea), la Rosa (San Pietro) | 64 |
| [verifica_copione.py](verifica_copione.py) | Controllo di caratteri e righe | |

`python3 verifica_copione.py` dalla cartella `copione/`: oggi 297 battute, 0 errori. Prova negativa fatta: una «ñ», una battuta da 10 righe e un'espressione inventata danno 3 errori e uscita 1.

## La storia della v1 in breve

Il primo giorno l'araldo di Monaldo dà a Gubbio **tre albe** per consegnare le chiavi. Ubaldo risponde che parlerà il cielo, ordina tre giorni di digiuno e sale a pregare sul Monte Ingino con Giorgio, giovane cavaliere impaziente, e Antonio, eremita che la città aveva lasciato fuori dalle porte e che va prima salvato da una pattuglia al Teatro Romano. Salendo gli Stradoni, Giorgio corre avanti e cade in un'imboscata; una spia lascia capire che qualcuno punta all'acqua della città. Nella Basilica, durante il rito, si risvegliano i Tre Ceri e i tre vincono gli Spettri del Dubbio. Una visione nella vetrata mostra Corrado di Spoleto che risale la gola del Bottaccione per spezzare l'acquedotto e aprire da dentro Porta Metauro. I tre scendono dietro il monte, battono Corrado sul Condotto (che si butta nel Camignano, vivo) e rientrano in città di notte. Alla terza alba l'araldo torna per le chiavi e la risposta è il Campanone suonato a doppi. L'assedio comincia: la v1 finisce lì, con un solo vetro della vetrata che ha preso colore.

Il percorso segue l'anello di `docs/mappa_del_mondo.md`: Piazza Grande, via dei Consoli, Bargello, San Martino, Teatro Romano, ritorno, Duomo, Stradoni, Basilica, Bottaccione, Porta Metauro, San Martino, Piazza Grande. Le altre aree (via XX Settembre, Sant'Agostino, Sant'Andrea, Quaranta Martiri, San Pietro) servono per NPC e quest.

## Formato delle battute

Ogni scena ha un codice (`P-`, `A1-`, `B-`, `E-`), una tabella con luogo, condizione e bandiere, le note di regia in corsivo-prosa e le battute in elenco:

```
- PARLANTE (espressione): Testo della battuta.
```

- **PARLANTE** in maiuscolo. Parlanti speciali: `NARRATORE` (riquadro senza nome, con capolettera a inizio capitolo, scelta di stile 8), `AREA` (etichetta di luogo e tempo), `SISTEMA` (istruzioni di gioco, senza ritratto), `OBIETTIVO` (aggiorna l'obiettivo in pausa), `SCELTA` (voci separate da « / »).
- **espressione** solo per chi ha il ritratto (Ubaldo, Giorgio, Antonio, Guido): `calmo`, `preoccupato` o `deciso`, le tre della scelta di stile 10. Senza espressione vale `calmo`. Gli altri parlano senza ritratto, con il solo cartiglio del nome.
- Una battuta sta in **3 righe** del riquadro (scelta 9). Lo script la misura con le larghezze del font 5x7 della scelta 8 su 180 px utili. È una misura provvisoria: in F1 decide il generatore sul font vero.
- **Caratteri**: ASCII stampabile, le 12 accentate italiane e « ». Niente lineette lunghe, niente puntini di sospensione in un solo carattere (si scrive `...`).
- Negli NPC d'ambiente la riga comincia con la fase (`NOTTE:`, `DIGIUNO:`, `ULTIMATUM:`): vince la prima che vale, dall'alto.

## Personaggi e voci

| Personaggio | Chi è nella v1 | Come parla | Arco nella v1 |
| :-- | :-- | :-- | :-- |
| Sant'Ubaldo | Il vescovo, anziano | Frasi brevi, calme, ironia asciutta. Mai una minaccia | Dal pastore che protegge alla guida che porta il digiuno fuori dalla chiesa |
| Giorgio | Giovane cavaliere | Impulsivo, squillante, vuole agire | Impara che chi corre avanti da solo combatte da solo («Insieme») |
| Antonio | Eremita piromante | Roco, sarcastico, poche parole | Da «fino al monte, poi vedremo» a «resto finché c'è legna da bruciare» |
| Console Guido | Capo della città | Ansioso, conta tutto | Dalla paura al «Suonate!» |
| Araldo di Perugia | Voce di Monaldo | Solenne, sprezzante | Compare solo in A1-01 ed E-01 |
| Corrado di Spoleto | Il Colosso delle Forge | Spaccone, gode della fatica | Boss della v1, si salva cadendo nel Camignano |
| Monaldo da Perugia | Il tiranno | Non compare: parla per bocca dell'araldo | Lasciato agli aggiornamenti |

## Bandiere della storia

Intervallo 0-63 di `story_flags.h` (storia principale). In ordine di comparsa:

`PROLOGO_VISTO`, `ULTIMATUM_RICEVUTO`, `GIORGIO_NEL_GRUPPO`, `CHIACCHIERA_CONSOLI`, `POSTIERLA_APERTA`, `ANTONIO_NEL_GRUPPO`, `CITTA_IN_DIGIUNO`, `PORTA_DEL_MONTE`, `IMBOSCATA_STRADONI`, `SPIA_CATTURATA`, `CERI_RISVEGLIATI`, `SPETTRI_VINTI`, `VISIONE_BOTTACCIONE`, `BOTTACCIONE_ENTRATI`, `MIASMI_VISTI`, `PIANO_DI_CORRADO`, `CORRADO_INCONTRATO`, `CONDOTTO_SALVO`, `RIENTRO_PORTA_METAURO`, `ATTO_I_COMPLETATO`, `CRONACA_V1_FINITA`.

Nell'intervallo boss (128-159): `CORRADO_SCONFITTO`, già presente nel prototipo. Nell'intervallo quest (64-127): `DONO_MATTEO` e gli indizi di Q-SP01 (`INDIZIO_LUCIA`, `INDIZIO_VENDITORE`, `INDIZIO_MENDICANTE`); stato e contatori delle quest stanno in `quest_state` e `quest_counter`. Le fasi degli NPC (ULTIMATUM, DIGIUNO, NOTTE) si ricavano dalle bandiere, non sono bandiere nuove: ULTIMATUM fino a `CITTA_IN_DIGIUNO`, DIGIUNO fino a `RIENTRO_PORTA_METAURO`, poi NOTTE.

`SIGILLO_SPEZZATO` del prototipo non serve più: il titolo dell'Atto I nel GDD («Il Sigillo Spezzato») non corrisponde a nessun evento del copione.

## Battaglie richieste

| Battaglia | Dove | In `enemy_data.h` oggi |
| :-- | :-- | :-- |
| Pattuglia perugina (tutorial) | Teatro Romano, A1-04 | Sì, `PATTUGLIA_PERUGINA` |
| Falchi corrotti, spie umbre | Stradoni, nemici visibili | No: da aggiungere |
| Imboscata | Stradoni, A1-07 | No: spie umbre |
| Spettri del Dubbio (boss tutorial) | Basilica, A1-08 | No: da aggiungere, deboli alla Fede |
| Guerrieri della Roccia di Spoleto | Bottaccione, nemici visibili | No: da aggiungere (Sez. 8D) |
| Corrado di Spoleto | Il Condotto, B-04 | Sì, `DUELLO_CORRADO` |

## Decisioni di trama (prese il 1 novembre 2026)

Cioti ha delegato a me le scelte di trama: lui giudicherà giocando se il gioco diverte. Le scelte qui sotto sono quindi **decise**, non più proposte. Si riaprono solo se la prova di gioco (R0) mostra che non funzionano.

1. **Tre albe.** L'ultimatum dà tre albe (non «una seconda alba» come nella Sez. 11 Passo 6), così il digiuno di tre giorni ha una scadenza e l'epilogo cade alla terza alba. Conseguenza: l'Atto IV del GDD dice «all'alba del terzo giorno» per la sortita; andrà letto come terzo giorno d'assedio.
2. **Antonio va salvato al Teatro Romano.** Dà il primo tutorial di battaglia e mette subito in scena il suo conflitto (l'isolamento).
3. **Il motivo per scendere nel Bottaccione** è la visione nella vetrata: Corrado vuole l'acquedotto e Porta Metauro. Nel GDD il Bottaccione è dell'Atto II, per sabotaggi; nella v1 diventa una difesa. Ha anche un appiglio storico: secondo Key to Umbria nel 1151 Ubaldo mandò di notte i soldati sui monti attorno e gli assedianti si ritirarono.
4. **La vetrata come cornice.** Prologo ed epilogo si aprono sulla stessa vetrata (le vetrate della Basilica raffigurano davvero la battaglia delle Undici Città e Sant'Ubaldo che la ferma). Nella v1 si accende un solo vetro.
5. **Corrado non muore**, si getta nel Camignano: la Sez. 11 lo rivuole in un duello.
6. **Tempo libero di notte** dopo il Bottaccione, per consegnare le quest prima dell'epilogo.
7. **«Console Guido», non «Podestà».** Nel 1151 la città era governata da consoli (il palazzo stesso ne porta il nome); il podestà è istituzione più tarda. Il parlante resta GUIDO.

## Revisione sulle regole di mestiere

Prima di decidere ho cercato come si scrive un copione di RPG e ho rivisto il testo su quelle regole. Le fonti e cosa ho cambiato:

| Regola | Fonte | Cosa ho cambiato |
| :-- | :-- | :-- |
| Ogni battuta deve avere uno scopo; se si può togliere, si toglie | [rpgmaker.net, calunio](https://rpgmaker.net/articles/2663); [Slabinski, Game Developer](https://www.gamedeveloper.com/game-platforms/8-key-principles-of-writing-effective-game-dialogue) | A1-01 accorciata di 5 battute: si arriva prima al controllo e alla prima battaglia |
| Una buona apertura porta presto all'azione; i tutorial non vanno imposti a chi non li legge | [GameRant](https://gamerant.com/rpgs-dont-start-slow/); [Grandia II, Game Developer](https://www.gamedeveloper.com/design/narrative-analysis-of-grandia-ii-s-beginning) | Le spiegazioni di gioco (SISTEMA) ridotte a una riga d'istruzione ciascuna; il colore lo danno Cecco e i personaggi |
| Le istruzioni sono prima di tutto istruzioni: brevi, chiare | [Chartier](https://amandalynnchartier.substack.com/p/q-and-a-how-do-you-make-instructional) | Come sopra |
| Si riconosce chi parla senza leggere il nome: registro, atteggiamento, argomenti, tic. Non abusare dell'umorismo | [Hedlund, Game Developer](https://www.gamedeveloper.com/design/driving-character-voice-differences) | Giorgio non fa più battute ironiche (sono di Antonio): resta serio e impulsivo. Due battute spostate o riscritte |
| La storia non va imposta: la lore sta negli NPC facoltativi | Slabinski | Già così: Berto, Tano e gli altri sono facoltativi |
| Seminare presto ciò che ripaga dopo | calunio | Già così: la roccia nera di Berto, il fuoco contro il ferro di Raniero e di Antonio, la vetrata |
| «Un villaggio, un problema, un dungeon» tiene il ritmo | Grandia II | La v1 ha tre blocchi così: città e Teatro Romano, Monte Ingino e Basilica, Bottaccione |

Le voci, sui quattro assi di Hedlund:

| | Registro | Atteggiamento | Argomenti | Tic |
| :-- | :-- | :-- | :-- | :-- |
| Ubaldo | alto ma semplice | calmo, fermo | fede, la città, il passo | frasi brevi che chiudono il discorso |
| Giorgio | familiare | impaziente, sincero | agire, gloria, «adesso» | chiede sempre «perché» e «e adesso?» |
| Antonio | basso, asciutto | sarcastico, diffidente | fuoco, legna, la porta chiusa | sminuisce ciò che fa di buono |
| Guido | formale | ansioso | numeri: grano, uomini, giorni | conta tutto |

Sulla storia: le fonti non concordano. [Wikipedia](https://en.wikipedia.org/wiki/Ubald) dice che nel 1151 Perugia e altre città si allearono contro Gubbio e che Ubaldo guidò le forze cittadine a una vittoria attribuita al suo miracolo; [Key to Umbria](https://keytoumbria.com/Gubbio/12th_century.html) parla di «circa undici» città, di un assedio, delle mura rifatte da Ubaldo e dei soldati mandati di notte sui monti. Il copione resta compatibile con entrambe: Guido cita le mura «che avete rifatto voi». La nascita di Ubaldo è data al 1084 circa o al 1075 circa, quindi nel 1151 ha fra i 67 e i 76 anni: nel copione è «anziano», senza età precisa.

Correzioni da riportare nel GDD (regola R5):

- Prologo e araldica (dal censimento dei simboli, 1 nov 2026): Perugia è **rossa col grifo d'argento coronato d'oro**, non «purpurea» come nella Sez. 7. Gubbio è rossa col monte bianco a cinque cime. Il copione usa il confronto grifo bianco contro monte bianco, entrambi su rosso, in P-02, A1-01 ed E-01. Lucia ora cuce uno stendardo col monte, non «con i vostri tre ceri» (nel 1151 i Ceri della festa non esistono).

- `docs/mappa_del_mondo.md` e il GDD chiamano «Porta di Santa Lucia» il rientro dal Bottaccione: Cioti ha confermato che è **Porta Metauro**. Il copione usa Porta Metauro; il contratto del mondo va corretto.

- Sez. 7 Scena 3 e Sez. 8C: colori delle camicie, fazzoletti rossi e corporazioni dei Ceri sono della festa di oggi e dei ceraioli, non dei personaggi (Cioti, 1 novembre 2026). Il copione non li usa; i tre si distinguono per attributi (mitra e verga, armatura e lancia, saio e fuoco). Il GDD va corretto. L'abilità «Bastione Azzurro» del prototipo tiene il nome: l'azzurro lì è dello scudo, non di una camicia.
- Sez. 31A e 31B su Mastro Raniero: la tabella dice fornaci «occupate da Cagli», il dialogo dice «truppe di Spoleto». Nel copione è Spoleto, che lega la quest a Corrado.
- Sez. 37: «Gubbio è salva» resta all'ultimo aggiornamento; la v1 chiude con «La cronaca continua».

Da segnalare, senza averlo cambiato:

- La **Festa dei Ceri** per tradizione ricorda la vittoria del 1151 (Key to Umbria). Nel gioco i Tre Ceri sono una forza mistica, non la festa: il copione non nomina la festa né il 15 maggio, per non fissare una data che le fonti non danno.
- L'elenco delle undici città è quello della Sez. 3; le fonti storiche non concordano tutte.

## Cosa manca

- La revisione indipendente del copione finito, che il piano prevede in F6 con un agente.
- La prova di gioco di Cioti, che giudica il divertimento (R0).
- I testi di menu, oggetti e abilità: arrivano con F1 e F5, insieme a `testi.h`.
