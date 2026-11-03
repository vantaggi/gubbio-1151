# Censimento della simbologia di Gubbio

> Copiato dal lavoro di censimento del 1 nov 2026. I dati sono in `dati/simboli/` (simboli.json, coalizione.json). Script e tavole di anteprima restano fuori dal repo: le licenze delle immagini si consultano solo sul PC.


Stato al 1 novembre 2026. Stesso metodo di `f3/`: ogni fatto ha una fonte, i dati stanno in
`simboli.json`, le licenze delle immagini si leggono sul PC con `cerca_licenze.py`, e nel repo non
entra nessun pixel da foto. Le scelte di design sono mie; a Cioti chiedo solo ciò che le fonti non dicono.

## In breve

- **Stemma del Comune**: di rosso al monte d'argento a cinque cime, con il lambello e i gigli d'oro
  in azzurro (Regio Decreto del 20 settembre 1934). Nel gioco: **rosso + monte bianco a cinque cime,
  senza lambello**, perché il lambello angioino nel 1151 non può esserci.
- **Quartieri**: Sant'Andrea, San Giuliano, San Martino, San Pietro. I colori ufficiali del Torneo sono
  **blu San Martino, rosso Sant'Andrea, ocra San Giuliano, verde San Pietro**. Sono sbagliati
  sia nella sezione 8B del GDD sia nella 9. Le figure sono quelle della sezione 9 (corona, palme, falcone, rosa): nessuna fonte scritta, confermate da Cioti.
- **Ceri**: camicia gialla per Sant'Ubaldo, azzurra per San Giorgio, nera per Sant'Antonio, con calzoni
  bianchi e fascia e fazzoletto rossi. **Nel gioco non si usano** (decisione di Cioti): sono le divise dei ceraioli durante la festa, recenti e non legate ai santi.
- **Tutto rientra nella palette bloccata**: non serve nessuna rampa nuova (vedi `tavola_simboli.png`).

## Censimento con fonti

| Simbolo | Cosa dicono le fonti | Fonte | Stato |
| :-- | :-- | :-- | :-- |
| Stemma del Comune | «Di rosso al monte d'argento a cinque cime caricato del lambello a sei pendenti con cinque gigli d'oro in campo azzurro» | [araldicacivica](https://www.araldicacivica.it/comune/gubbio/), [heraldry-wiki](https://heraldry-wiki.com/wiki/Gubbio), [comuni-italiani](https://www.comuni-italiani.it/054/024/stemma.html) | confermato |
| Concessione | Regio Decreto, 20 settembre 1934 (numero non trovato) | araldicacivica, heraldry-wiki | confermato |
| Gonfalone | «Drappo di rosso» con lo stemma; ornamenti e iscrizione non trovati | araldicacivica | parziale |
| Bandiera del Comune | «Drappo di bianco caricato al centro dallo stemma comunale» | araldicacivica | confermato |
| Colori civici | Nessuna fonte li dichiara. Il rosso viene dal campo dello stemma e dal gonfalone | — | non trovato |
| Quartieri, nomi | Sant'Andrea, San Giuliano, San Martino, San Pietro; Torneo con la balestra il 14 agosto in Piazza Grande | [Maggio Eugubino](https://www.maggioeugubino.it/tornei-dei-quartieri/), [Umbria Tourism](https://www.umbriatourism.it/en/w/torneo-dei-quartieri-event) | confermato |
| Quartieri, colori | «I 4 costumi sono stati ideati rispettando i colori dei quartieri (blu san Martino, rosso sant'Andrea, ocra san Giuliano e verde san Pietro)» | [Comune di Gubbio](https://comune.gubbio.pg.it/en/news/torneo-dei-quartieri-53-edizione), [Maggio Eugubino](https://www.maggioeugubino.it/2026/08/torneo-dei-quartieri-2026-presentazione-palio/), [Cronaca Eugubina](https://www.cronacaeugubina.it/2026/08/15/torneo-dei-quartieri-2026-vince-san-pietro-con-marcello-cerbella-miglior-corteo-storico-san-giuliano/) | confermato (costumi: fonti; bandiere: Cioti) |
| Quartieri, figure | San Martino: «Di rosso alla corona d'oro», corona reale, documentata dal XVI secolo (foglio volante di Gabriele Gabrielli, circa 1580); il quartiere è citato dal 1279. Gli altri tre non sono descritti da nessuna fonte | [Cronaca Eugubina 2018, conferenza di Fabrizio Cece](https://www.cronacaeugubina.it/2018/02/01/di-rosso-alla-corona-doro-alla-societa-operaia-fabrizio-cece-ha-spiegato-la-storia-dello-stemma-del-quartiere-di-san-martino/) | San Martino confermato; Sant'Andrea dall'immagine di Cioti (sotto); falcone e rosa confermati solo da Cioti |
| Sant'Andrea, stemma | Campo rosso; tre palme (o piume) d'argento a ventaglio, attraversate da due bastoni d'argento in croce di Sant'Andrea | Immagine mandata da Cioti (stemma stampato «S. Andrea», origine non indicata; non entra nel repo) | confermato |
| Quartieri, formato comune | Nella presentazione comune i quattro stemmi sono tutti in campo rosso con la figura d'argento; poi ogni quartiere ha i suoi colori e una sua versione. Le versioni proprie non le ho trovate: i siti dei Balestrieri e del Comune non hanno araldica, e le pagine Facebook dei quartieri non si leggono dal cloud | Cioti (1 nov 2026); coerente con Cece 2018 | formato confermato, varianti da cercare |
| Quartieri, origine | «Tra il settimo e l'ottavo decennio del sec. 13°, alla divisione della città in vici si era sostituita quella in quartieri» | [Treccani, Enciclopedia dell'Arte Medievale](https://www.treccani.it/enciclopedia/gubbio_(Enciclopedia-dell'-Arte-Medievale)/) | confermato |
| Stemma più antico | «Sul portale di Palazzo dei Consoli [...] sfondo rosso e un monte bianco»; i gigli sono «l'aderenza della città al partito angioino» | Cronaca Eugubina 2018 | confermato |
| Contrade | A metà del '300 ogni quartiere è diviso in 6 contrade, ciascuna col suo vessillo; colori ignoti, «si pensa» sfondo rosso | Cronaca Eugubina 2018 | confermato |
| Compagnie del 1461 | «Corona, santa Croce, Sole, Fonte de Fosso, et santo Pietro» (cronaca di Ser Silvestri Angelelli Manni) | it.wikipedia Palio della Balestra | confermato, ma non sono i quartieri di oggi |
| Ceri, divisa | Calzoni bianchi, camicia gialla (Ubaldo), azzurra (Giorgio), nera (Antonio), fascia rossa (fusciacca), fazzoletto rosso sulle spalle | [it.wikipedia Festa dei Ceri](https://it.wikipedia.org/wiki/Festa_dei_Ceri), [Wikivoyage](https://it.wikivoyage.org/wiki/Gubbio) | confermato |
| Ceri, corporazioni | Muratori e scalpellini (Ubaldo), merciai, commercianti e artigiani (Giorgio), contadini (Antonio; «asinari» nell'incipit di Wikipedia) | it.wikipedia, [ceri.it](https://www.ceri.it/i-ceri/) | confermato |
| Ceri, forma | Due prismi ottagonali sovrapposti a clessidra, tavolette d'abete su anima d'olmo, barella ad H, quattro «manicchie»; 4,9-5,0 m con la statua, 263-287 kg | it.wikipedia, ceri.it | confermato |
| Ceri, statue | Ubaldo in veste episcopale benedicente; Giorgio a cavallo con lancia, scudo e mantello azzurro; Antonio col saio e il fuoco in mano | it.wikipedia | confermato |
| Ceri, origine | La corsa si svolge «dalla morte di Sant'Ubaldo (16 maggio 1160) in avanti» | [ceri.it](https://www.ceri.it/programma-della-corsa/) | confermato |
| Regione Umbria | Dal 1973 i tre Ceri stilizzati sono nel gonfalone e nella bandiera della Regione | it.wikipedia Festa dei Ceri | confermato |
| Tavole Eugubine | 7 tavole di bronzo, 12 facce scritte, lingua umbra in alfabeto umbro (dall'etrusco) e latino, III-I sec. a.C.; ritrovamento datato per tradizione 1444 (vendita sicura nel 1456); oggi al Palazzo dei Consoli | [it.wikipedia](https://it.wikipedia.org/wiki/Tavole_eugubine), [en.wikipedia](https://en.wikipedia.org/wiki/Iguvine_Tablets) | confermato |
| Balestrieri, sbandieratori | Società Balestrieri erede della «Congrega dei Balestrieri», sede al Bargello; sbandieratori dal 1968, società autonoma dal 1999. Colori delle loro bandiere non trovati (i loro siti non si leggono dal cloud) | [Eugubini nel mondo](http://www.eugubininelmondo.com/Balestrieri.html) | parziale |

## Il GDD contro le fonti

| Punto | GDD | Fonti | Verdetto |
| :-- | :-- | :-- | :-- |
| Colori dei quartieri | 8B: San Martino rosso e oro, Sant'Andrea verde e bianco, San Pietro azzurro e giallo, San Giuliano blu notte e argento. Sezione 9: tutti in campo rosso con figura bianca | Blu San Martino, rosso Sant'Andrea, ocra San Giuliano, verde San Pietro | **Entrambe sbagliate**: valgono i colori del Torneo |
| Figure dei quartieri | 8B: corona, croce di Sant'Andrea, chiavi con tiara, olivo e stella. Sezione 9: corona, palme, falcone, rosa | Nessuna fonte trovata | **Vale la 9**, confermata da Cioti; la 8B è sbagliata |
| Stemma del Comune (9) | «Monte di cinque cime alla tedesca», «rastrello», «capo d'Angiò» | Monte d'argento a cinque cime, lambello a sei pendenti, cinque gigli d'oro in azzurro | Il nucleo è giusto; «alla tedesca» e «capo d'Angiò» non hanno fonte |
| Ceri, Giorgio (8C) | Simbolo «elmo e spada», corporazione con falegnami | Statua a cavallo con lancia e scudo; merciai e commercianti | Si correggono in lancia e scudo; i falegnami non hanno fonte |
| Ceri, Antonio (8C) | «Fiamma e porcellino»; bestionari e zappatori | Statua col fuoco in mano; contadini o asinari | Resta la fiamma; il porcellino è iconografia comune del santo, ma non è sulla statua |
| Brocche «Mastro Giorgio» (8C) | Brocca di lustro oro e rubino all'alzata | Le brocche non sono nelle pagine di ceri.it; Mastro Giorgio è del Cinquecento | Anacronismo: si toglie il nome di Mastro Giorgio |
| Colori dei Ceri (8C, 9) | Gialla, azzurra e nera, calzoni bianchi, fazzoletto rosso | Uguale | Corretto |

I colori sono giusti come divise della festa, ma nel gioco non si usano (vedi sotto). Le correzioni al GDD sono in `docs/errata_gdd.md`.

## Il problema del 1151

Il gioco è ambientato nel 1151. Tre di questi simboli in quell'anno non esistevano ancora:

1. **Lambello e gigli d'oro.** Sono la brisura angioina, e gli Angiò arrivano in Italia nel 1266. Lo
   stemma più antico databile, sul portale del Palazzo dei Consoli, ha solo il campo rosso e un monte
   bianco (Cece, 2018); la data dell'aggiunta dei gigli resta ignota. **Decisione**: nel gioco il Comune usa solo il campo rosso e il monte a cinque cime. È anche
   più leggibile a 16 px.
2. **Ceri.** La festa nasce dopo la morte di Ubaldo (1160), e nel gioco Ubaldo è vivo. Le camicie
   gialla, azzurra e nera sono le divise dei ceraioli durante la festa, non dei santi. **Decisione di
   Cioti (1 nov 2026)**: nel gioco non si usano, nemmeno come codice dell'interfaccia. I tre eroi si
   riconoscono dalle vesti e dagli attributi dei ritratti (mitra, armatura e lancia, saio e fuoco).
   La battuta di Lucia nel copione («Giallo per il vescovo, azzurro per il cavaliere, nero per
   l'eremita») è stata tolta (1 nov 2026); nel copione v2 Lucia cuce «uno stendardo nuovo: rosso, col
   monte bianco».
3. **Tavole Eugubine.** Nel 1151 sono sepolte e dimenticate (ritrovamento tradizionale nel 1444). Possono
   comparire solo come un reperto che qualcuno trova. Il GDD le mette nel post-game, fuori dalla v1:
   restano lì.

Anche i quartieri sono più tardi: nascono nel XIII secolo (Treccani). Restano come fazioni del gioco, per scelta. Il formato rosso e argento ha il vantaggio di stare vicino al rosso del Comune e ai vessilli rossi delle contrade del Trecento. I colori del Torneo sono moderni, ma si usano come colori di fazione: è un
riconoscimento per chi conosce Gubbio, e nel 1151 non contraddice niente di documentato.

## Come si usano nello stile bloccato

Tutti i colori vengono da rampe già presenti in `stile_dati/stile/dati/palette.json`. Nessuna modifica
alla palette, nessuna deviazione dalla Guida. La tavola `tavola_simboli.png` (240x160 a x3, generata da
`tavola_simboli.py`) mostra la proposta.

| Simbolo | Dove compare | Colori (rampa, tono) |
| :-- | :-- | :-- |
| **Vessillo del Comune**: drappo rosso con monte bianco a cinque cime di profilo (richiama lo skyline dell'Ingino) | Sulle porte, sul Palazzo dei Consoli e sulle mura; sulle tuniche dei soldati di Gubbio, che il ritratto «Soldato» veste già in vermiglio; nel prologo, il punto chiaro al centro della mappa | vermiglio 1-3, neutri 3-4, contorno quasi nero |
| **Scudetto** 16x18 con lo stesso monte | Interfaccia: icona del salvataggio, angolo del cartiglio dei nomi, schermata del titolo sotto il logo | come sopra |
| **Drappi dei quartieri**: formato comune, cioè campo rosso con la figura d'argento (la corona di San Martino in oro), più una fascia in alto nel colore del quartiere | Sulla porta del datore di quest di ogni quartiere e sulle finestre della sua area; il colore del quartiere torna nella voce del diario delle quest | vermiglio 1-3, neutri 4, oro 3; fasce: San Martino cielo 2, Sant'Andrea vermiglio 2, San Giuliano oro 1, San Pietro verde 2 |
| **Tavola Eugubina** come reperto | Fuori dalla v1. La tavola mostra righe incise generate a caso, nessun testo vero copiato | oro e bronzo 0-2 |

Accorgimenti:
- Sant'Andrea e il Comune sono entrambi rossi: li distingue la figura (il monte c'è solo sul Comune).
- Le bandiere ondeggiano con 2 fotogrammi da 12 vblank: nessuna regola nuova, si usa il sistema
  delle pose della scelta 11.
- Non si usa l'emblema della Regione Umbria (i tre Ceri del 1973), perché è il simbolo di un ente.
  Non si riproduce nemmeno lo stemma ufficiale del 1934: la versione del gioco, senza lambello, è un
  disegno nostro. Va comunque aggiunta alla verifica legale prevista prima del rilascio.

## Immagini di riferimento e licenze

Commons dal cloud è bloccato, quindi le licenze non le scrivo a memoria. `cerca_licenze.py` usa le
stesse funzioni di `f3/censisci.py` (usabile = CC0, PD o CC BY; solo consultazione = CC BY-SA o GFDL;
esclusa = il resto). Interroga le categorie che stanno in `simboli.json` (stemma, Ceri, Tavole) e
scrive `licenze_simboli.csv/.json`:

```
cd <cartella simboli>
python cerca_licenze.py
```

Il nome di categoria «Category:Iguvine Tablets» viene da Wikipedia. Gli altri due sono una mia ipotesi:
se mancano, lo script ripiega sulla ricerca per testo. Le immagini servono solo da riferimento:
tutti i simboli del gioco sono disegnati da regole, come nella tavola.

**Esito (lanciato sul PC il 1 nov 2026, 36 immagini, vedi `licenze_simboli.csv` e `LICENZE_NOTE.md`).**
Ceri: 12 foto usabili (CC BY 2.0 e 3.0). Tavole Eugubine: 12 usabili (10 di Sailko, CC BY 3.0, e 2 in
pubblico dominio). Stemma: su Commons non c'è un disegno dello stemma del Comune. L'unica immagine
pertinente è la foto dello stemma sul Palazzo dei Consoli (Sailko, CC BY 3.0); le altre sono stemmi di
famiglie, come «Blason gabrielli.png», in CC0. Non cambia niente nella proposta: il monte a cinque cime
si disegna dalla blasonatura, e le foto servono solo da riferimento.

## Gli stendardi della coalizione

Dati in `coalizione.json`, tavola in `tavola_coalizione.png` (generata da `tavola_coalizione.py`). Le
blasonature vengono tutte da araldicacivica.it (`/comune/<nome>/`); l'elenco delle undici città è quello
della Sez. 3 del GDD, come nel copione.

| Città | Stemma ufficiale (sintesi) | Drappo nel gioco |
| :-- | :-- | :-- |
| Perugia | Di rosso al grifone d'argento, coronato d'oro | rosso scuro, grifo bianco con la corona d'oro |
| Spoleto | Partito: d'argento alla croce rossa; di rosso al cavaliere d'argento (cavaliere attestato dalla fine del XII secolo) | partito bianco e rosso, croce rossa |
| Cagli | Di rosso al capriolo d'argento con tre palle d'oro | rosso, capriolo bianco, palle d'oro |
| Foligno | Croce rossa in argento, rosso, giglio d'oro in rosso | rosso, giglio d'oro |
| Todi | Di rosso all'aquila d'argento coronata (scolpita nel 1267) | rosso, aquila bianca |
| Nocera | Nessuna blasonatura (stemma non ufficiale) | bruno, senza figura |
| Gualdo Tadino | D'argento alle tre bande di rosso | bianco a bande rosse |
| Fossato di Vico | Azzurro, grifo d'oro su castello d'argento | azzurro, torre bianca |
| Assisi | Nessuna blasonatura; la storia cita «il leone rampante sulla campagna verde» | verde, leone d'oro (provvisorio) |
| Bettona | Rosso con croce bianca e tre foglie di bettonica | rosso, croce bianca |
| Spello | Di rosso alla torre fra due leoni d'oro | rosso, torre d'oro |

Regole di semplificazione (mie): una sola figura per drappo, leggibile a 8x8 px. Se due città finirebbero
uguali, si tiene la parte che le distingue (Foligno perde la croce e tiene il giglio; Fossato perde il
grifo, che è di Perugia, e tiene il castello). Perugia, che guida la coalizione, ha il rosso più scuro. Il
grifo bianco di Perugia contro il monte bianco di Gubbio, entrambi su rosso, è il confronto principale del gioco.

## Decisioni prese da Claude mentre Cioti era via (1 nov 2026)

1. Quartieri nel formato comune rosso e argento, con fascia nel colore del Torneo (sopra).
2. Stendardi della coalizione disegnati come nella tabella qui sopra.
3. Nocera senza figura e Assisi col leone d'oro su verde finché non si trova una blasonatura.
4. La battuta di Lucia sui colori dei Ceri era già stata tolta dal copione (`01_atto_I.md`, nota del 1 nov).

Note per il copione (non le ho cambiate io, sono di un altro lavoro). **Entrambe applicate** nel
copione (verificato il 3 nov 2026):
- ~~`00_prologo.md`: l'ultimo stendardo è «più grande e purpureo, il Grifo di Perugia».~~ Ora è
  «rosso scuro, con il grifo bianco coronato d'oro».
- ~~`03_npc_ambiente.md`, Lucia: «cucirò uno stendardo con i vostri tre ceri».~~ Ora cuce uno
  stendardo «rosso, col monte bianco».

Le stesse correzioni valgono per il GDD del prototipo (Sez. 7, 8B, 8C, 9, 31, 32, 34): sono raccolte
in `docs/errata_gdd.md`, perché il GDD non è in questo ramo e non si riscrive.

## Domande per Cioti

Nessuna. Falcone (San Giuliano) e rosa (San Pietro) restano confermati da Cioti a memoria (1 nov 2026,
sera): se un giorno arriva un'immagine degli stemmi propri, si aggiorna `simboli.json`.

## File

| File | Cosa contiene |
| :-- | :-- |
| `CENSIMENTO_SIMBOLI.md` | Questo documento |
| `simboli.json` | I dati, con le fonti per chiave, lo stato e i colori della palette |
| `tavola_simboli.py` / `.png` | La tavola della proposta, disegnata solo con la palette bloccata |
| `coalizione.json`, `tavola_coalizione.py` / `.png` | Stemmi delle undici città e i loro drappi nel gioco |
| `cerca_licenze.py` | Script da lanciare sul PC per autore e licenza delle immagini su Commons |

