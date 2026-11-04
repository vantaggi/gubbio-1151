# Copione della v1: Prologo, Atto I e Bottaccione (storia v2)

Bozza del 1 novembre 2026, per la fase F6 del [piano di ripartenza](https://claude.ai/artifact/XWPo2448pceE3Ebb7Frvv3). Ambito: «Atto I e Bottaccione». Lingua del gioco: italiano. Nessun codice: è il testo da cui F6 genererà le tabelle (`testi.h` di F1, bandiere, script).

**3 novembre 2026: applicata la storia v2** ([Bibbia della storia](https://claude.ai/artifact/NthrSb1HiqWFaXqW76GA1k), file in `../storia/`), approvata da Cioti. La copia della v1 è in [v1/](v1/) e non va toccata.

## File

| File | Contenuto | Battute |
| :-- | :-- | --: |
| [00_prologo.md](00_prologo.md) | Avvio, la vetrata chiara, la mappa che annerisce | 10 |
| [01_atto_I.md](01_atto_I.md) | Dall'ultimatum al rito della Basilica e alla visione; il borgo (D1) | 136 |
| [02_bottaccione_epilogo.md](02_bottaccione_epilogo.md) | Il dungeon, il ragazzo esule (D2), Corrado, il rientro, la terza alba (D4), la vetrata | 90 |
| [03_npc_ambiente.md](03_npc_ambiente.md) | NPC d'ambiente delle 14 aree, per fase; il pane (D3) | 59 |
| [04_quest.md](04_quest.md) | Le 3 quest scelte: il Ferro (San Martino), le Erbe (Sant'Andrea), la Rosa (San Pietro) | 74 |
| [05_npc_amici.md](05_npc_amici.md) | Gli amici di Cioti e le loro famiglie come NPC del 1151, per area e fase | 84 |
| [verifica_copione.py](verifica_copione.py) | Controllo di caratteri e righe | |
| [v1/](v1/) | Copia del copione v1 (297 battute), prima della storia v2 | |

`python3 verifica_copione.py` dalla cartella `copione/`: oggi 453 battute, 0 errori (dopo la revisione indipendente, 4 nov 2026, e le battute di attesa e di dopo delle quest giocabili, SV2c), con la misura v2 (2 righe da 224 px). La v1 misurava 3 righe da 180 px. Prova negativa fatta: una «ñ», una battuta da 10 righe e un'espressione inventata danno 3 errori e uscita 1.

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
- Una battuta sta in **2 righe da 224 px** del riquadro del gioco. Lo script la misura con le larghezze del font 5x7 della scelta 8. Una voce di SCELTA sta in 100 px.
- Le condizioni sulle bandiere sono righe di regia chiare (`se INDIZIO_ROCCIA:`) prima delle battute che valgono solo in quel caso.
- **Caratteri**: ASCII stampabile, le 12 accentate italiane e « ». Niente lineette lunghe, niente puntini di sospensione in un solo carattere (si scrive `...`).
- Negli NPC d'ambiente la riga comincia con la fase (`NOTTE:`, `DIGIUNO:`, `ULTIMATUM:`): vince la prima che vale, dall'alto.
- Variante con bandiera: `- NOTTE (se BORGO_DENTRO): GUIDO: ...` (o `se non BANDIERA`), sempre sopra la riga senza condizione della stessa fase. La variante che vale parla da sola; per aggiungere una battuta alle altre si usa un blocco `Se `BANDIERA`:` sotto la riga di fase.
- **Righe di battaglia**: le battute che si dicono dentro uno scontro, la prima volta che succede un evento, si scrivono `- IN BATTAGLIA (evento): PARLANTE (espressione): testo` (B-04). `tools/genera_storia.py` le mette da parte e non le recita nel dialogo della scena; `verifica_copione.py` le misura come le altre.
- **Note di regia** in prosa, mai in forma di battuta: una riga che comincia con `- ` e un nome in maiuscolo è una battuta.
- **Le quest** (`04_quest.md`, letto da `tools/genera_storia.py`, SV2c): per ogni `## Q-XXNN · titolo` il datore è il primo nome in grassetto; le sezioni `###` sono Proposta, Attesa (quest presa, obiettivo a metà), Consegna, Dopo (righe con la fase, come gli NPC: serve una riga per ogni fase in cui la quest si può consegnare), la sezione di raccolta (titolo con i due punti, «Teatro Romano: le fornaci»), Gli indizi e L'infiltrato. Nella raccolta più righe SISTEMA in cima valgono una per pezzo, nell'ordine (una sola vale a ogni pezzo); «Al primo blocco, una volta sola[, ... (`BANDIERA`)]:» vale al primo pezzo; «Se la quest non è attiva, alla prima radice:» al primo pezzo senza la quest presa. Negli indizi, «**Nome** (...). Imposta `BANDIERA`.» apre l'indizio di quell'NPC d'ambiente; «Con i tre indizi...» la riga che segue il terzo. Nell'infiltrato, «Dopo la vittoria:» separa le battute di prima da quelle dopo la battaglia.

## Regole decise con la revisione (4 novembre 2026)

La revisione indipendente del copione (`revisione/REVISIONE_COPIONE_v2.md` nella cartella del progetto) è applicata: i gialli T1-T12 e i verdi V1, V2, V4-V8, V11-V14, V16; V9 e V17 restano come sono (V9 è una nota per l'Atto II, V17 chiederebbe una condizione «dopo aver parlato con» che il lettore non ha), V10 non è applicata (la prova di gioco dirà se serve). Da qui valgono queste regole:

- **Nessuna quest si perde.** Ogni quest si prende e si consegna fino alla conferma di E-01, e i luoghi dove si raccolgono gli oggetti restano raggiungibili fino alla fine. In particolare la Strada del Bottaccione resta percorribile dopo B-05, rientrando da Porta Metauro, e Agnese accetta le radici di Q-SA01 fino alla fine (`04_quest.md`).
- **Giordano e Q-SP01 (T7).** Con Q-SP01 attiva, Giordano dice **prima** la sua battuta del DIGIUNO, che accende `INDIZIO_ACQUA`, e **poi** le due battute dell'indizio della quest. Con la regola «vince la prima che vale» la battuta della quest non deve coprire quella del DIGIUNO: chi fa Q-SP01 riceve sempre anche `INDIZIO_ACQUA`. Da rispettare nel codice delle quest.
- **Dopo E-01 non si gira la città.** E-02 parte subito, a schermo intero; le battute che devono pesare su D4 stanno dentro E-01 (Ciaccio, T1).
- **Licenze dichiarate (V3).** La città del gioco è la Gubbio di oggi: molti edifici sono più tardi del 1151 (il Palazzo dei Consoli e il grande acquedotto del Trecento, la Loggia dei Tiratori del Cinque-Seicento, il Palazzo Ducale del Quattrocento, la Fontana dei Matti, Porta Metauro). Anche il condotto del Bottaccione nel 1151 è una licenza. Le battute non li correggono uno per uno: la licenza va detta una volta, qui e nei crediti. Solo i personaggi del 1151 non nominano ciò che non possono conoscere (V2: il canonico non parla del «Ducale»).
- **La canzone di Flaviano (V15).** Flaviano e Giuliana promettono «la canzone nuova»: la ripaga il brano dei titoli di coda, che nell'audio si chiama già `canzone_di_flaviano` (`audio/canzone_di_flaviano.xm`). Nessuna battuta nuova.
- **Nomi.** Su richiesta di Cioti il medico si chiama **Vanni** (da Giovanni, prima «Compagno») e il custode delle carte **Renzo** (da Lorenzo, prima «Bubo»).

## La storia v2 in breve

Tema: **una città si giudica da chi lascia fuori dalle porte.** L'assedio resta quello della v1, ma ha una ragione vera: Gubbio è cresciuta a spese dei vicini, e fra gli assedianti ci sono gli **esuli eugubini** della famiglia di **Rinaldo di Valmarcola**, cacciati nella pace del 1140 (licenza dichiarata: la famiglia c'è nell'elenco di Piccotti, la cacciata no). Il traditore in città, il **canonico Ilario** fratello di Rinaldo, si rivela nell'Atto II, fuori dalla v1. Il piano del condotto non arriva più solo dalla visione: Renzo (la carta), Giordano (l'acqua) e Giambono (la roccia) danno tre indizi, e la vetrata conferma. Quattro scelte cambiano battute e bandiere, non il finale: il borgo fuori Porta Romana (D1), il ragazzo esule al Bottaccione (D2), il pane alla popolana (D3), la giustizia offerta agli esuli alla terza alba (D4).

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
| Rinaldo di Valmarcola | Capo degli esuli eugubini | Non compare nella v1: lo nominano l'araldo, Corrado e l'infiltrato | Atto II |
| Gli amici (24 NPC) | Mestieri del 1151 nei quartieri | Una voce ciascuno, vedi [05_npc_amici.md](05_npc_amici.md) | Indizi, aiuti e colore; nessuno è traditore, vigliacco o zimbello, nessuno muore in scena |

## Bandiere della storia

Intervallo 0-63 di `story_flags.h` (storia principale). In ordine di comparsa:

`PROLOGO_VISTO`, `ULTIMATUM_RICEVUTO`, `GIORGIO_NEL_GRUPPO`, `CHIACCHIERA_CONSOLI`, `POSTIERLA_APERTA`, `ANTONIO_NEL_GRUPPO`, `CITTA_IN_DIGIUNO`, `PORTA_DEL_MONTE`, `IMBOSCATA_STRADONI`, `SPIA_CATTURATA`, `CERI_RISVEGLIATI`, `SPETTRI_VINTI`, `VISIONE_BOTTACCIONE`, `BOTTACCIONE_ENTRATI`, `MIASMI_VISTI`, `PIANO_DI_CORRADO`, `CORRADO_INCONTRATO`, `CONDOTTO_SALVO`, `RIENTRO_PORTA_METAURO`, `ATTO_I_COMPLETATO`, `CRONACA_V1_FINITA`.

Nell'intervallo boss (128-159): `CORRADO_SCONFITTO`, già presente nel prototipo. Nell'intervallo quest (64-127): `DONO_MATTEO` e gli indizi di Q-SP01 (`INDIZIO_LUCIA`, `INDIZIO_VENDITORE`, `INDIZIO_FONTANIERE`, che nella v2 sostituisce `INDIZIO_MENDICANTE`); stato e contatori delle quest sono bandiere dello stesso intervallo (SV2c): `Q_SM01_PRESA`, `Q_SA01_PRESA`, `Q_SP01_PRESA` per la quest presa e un bit per pezzo dell'obiettivo (`FERRO_1`...`FERRO_3`, `ELLEBORO_1`...`ELLEBORO_4`, `ROSA_RIPRESA`); il contatore è quanti sono accesi. Nessun campo nuovo in `GameState`. Le fasi degli NPC (ULTIMATUM, DIGIUNO, NOTTE) si ricavano dalle bandiere, non sono bandiere nuove: ULTIMATUM fino a `CITTA_IN_DIGIUNO`, DIGIUNO fino a `RIENTRO_PORTA_METAURO`, poi NOTTE.

Bandiere nuove della v2 (intervallo quest, 64-127):

- Indizi del condotto: `INDIZIO_CARTA` (Renzo), `INDIZIO_ACQUA` (Giordano), `INDIZIO_ROCCIA` (Giambono). Con almeno due, in A1-09 Ubaldo arriva alla visione già sapendo.
- Scelte: `BORGO_DENTRO` / `BORGO_FUORI` (D1; saltare A1-05b vale `BORGO_FUORI`), `ESULE_PRIGIONIERO` / `ESULE_LIBERATO` (D2), `PANE_DATO` (D3), `GIUSTIZIA_OFFERTA` (D4).
- Conferma dell'alba: `ALBA_CONFERMATA` (intervallo 0-63), accesa da «Sì, è ora» in B-05 o dal console Guido nella NOTTE; E-01 la richiede, così il tempo libero della notte (decisione 6) c'è davvero.
- Ascolti: `RICCIARDO_ASCOLTATO`, `RUFINO_ASCOLTATO` (con Q-SM01 consegnata, Corrado ha uno scudo in meno).

Meccanica nuova: durante il DIGIUNO Ubaldo non può usare il cibo fino al rientro in città.

`SIGILLO_SPEZZATO` del prototipo non serve più: il titolo dell'Atto I nel GDD («Il Sigillo Spezzato») non corrisponde a nessun evento del copione.

## Battaglie richieste

Nel gioco le battaglie sono in `include/battaglia_dati.h` (`INCONTRO`), con il gemello Python in `tools/battaglia_mirror.py`.

| Battaglia | Dove | Nel gioco |
| :-- | :-- | :-- |
| Pattuglia perugina (tutorial) | Teatro Romano, A1-04 | Sì, la Pattuglia Perugina (incontro 0) |
| Falchi corrotti, spie umbre | Stradoni, nemici visibili | Le spie sì (l'Imboscata); i falchi no |
| Imboscata | Stradoni, A1-07 | Sì, tre spie umbre (incontro 1) |
| Spettri del Dubbio (boss tutorial) | Basilica, A1-08 | Sì, due Spettri, deboli alla Fede (incontro 3) |
| Guerrieri della Roccia di Spoleto | Bottaccione, B-03 (battaglia breve a metà scena) | Sì, due Guerrieri della Roccia, deboli alla Fiamma (incontro 4) |
| Guerrieri della Roccia alle fornaci | Teatro Romano, Q-SM01, nemici visibili | Sì, uno per fornace (incontro 5) |
| L'infiltrato | Logge dei Tiratori, Q-SP01 | Sì, l'infiltrato e due spie umbre (incontro 6) |
| Corrado di Spoleto | Il Condotto, B-04 | Sì, il Duello con Corrado (incontro 2) |

## Decisioni di trama (prese il 1 novembre 2026)

Cioti ha delegato a me le scelte di trama: lui giudicherà giocando se il gioco diverte. Le scelte qui sotto sono quindi **decise**, non più proposte. Si riaprono solo se la prova di gioco (R0) mostra che non funzionano.

1. **Tre albe.** L'ultimatum dà tre albe (non «una seconda alba» come nella Sez. 11 Passo 6), così il digiuno di tre giorni ha una scadenza e l'epilogo cade alla terza alba. Conseguenza: l'Atto IV del GDD dice «all'alba del terzo giorno» per la sortita; andrà letto come terzo giorno d'assedio.
2. **Antonio va salvato al Teatro Romano.** Dà il primo tutorial di battaglia e mette subito in scena il suo conflitto (l'isolamento).
3. **Il motivo per scendere nel Bottaccione** è la visione nella vetrata: Corrado vuole l'acquedotto e Porta Metauro. Nel GDD il Bottaccione è dell'Atto II, per sabotaggi; nella v1 diventa una difesa. Ha anche un appiglio storico: secondo Key to Umbria nel 1151 Ubaldo mandò di notte i soldati sui monti attorno e gli assedianti si ritirarono.
4. **La vetrata come cornice.** Prologo ed epilogo si aprono sulla stessa vetrata (le vetrate della Basilica raffigurano davvero la battaglia delle Undici Città e Sant'Ubaldo che la ferma). Nella v1 si accende un solo vetro.
5. **Corrado non muore**, si getta nel Camignano: la Sez. 11 lo rivuole in un duello.
6. **Tempo libero di notte** dopo il Bottaccione, per consegnare le quest prima dell'epilogo.
7. **«Console Guido», non «Podestà».** Nel 1151 la città era governata da consoli (il palazzo stesso ne porta il nome); il podestà è istituzione più tarda. Il parlante resta GUIDO.

## Decisioni della v2 (3 novembre 2026, approvate da Cioti)

1. **I tre punti rossi** della Bibbia sono approvati: la battuta del narratore in P-02 cambia («vecchi torti e nuove ambizioni»), la scelta D4 viene prima della carrellata C4, e in A1-09 la vetrata conferma il piano invece di rivelarlo (riapre la decisione n. 3 qui sopra, che resta valida come motivo per scendere).
2. **Regola di rispetto** per gli amici (vedi sopra), approvata.
3. **Nomi**: i soprannomi degli amici sono adattati al 1151 in modo che li riconosca solo chi li conosce (tabella in `../storia/NPC_AMICI.md`). Genere e figura li ho decisi io in modo plausibile: gli amici sono uomini, le compagne donne, Nicoluccio un bambino. **Sono modificabili**: basta dirlo.
4. Gli amici usano posti di lavoro condivisi: 6 edifici nuovi su 8 al massimo.

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

- Il dono del baccalà di Fra' Matteo e lo scudo in meno di Corrado con `RUFINO_ASCOLTATO`: il copione li scrive, il codice ancora no.
- La spia legata in sacrestia (`03_npc_ambiente.md`): il copione ha le sue battute, il gioco non le ha ancora un posto.
- La prova di gioco di Cioti, che giudica il divertimento (R0).
- I testi di menu, oggetti e abilità: arrivano con F1 e F5, insieme a `testi.h`.
