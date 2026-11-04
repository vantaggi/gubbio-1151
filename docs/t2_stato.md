# T2: la gola del Bottaccione

Ramo `f10-t2`, da `ripartenza` (portato il WIP di `f8-t2a` @ 91bf736).

## Le quattro stanze (`tools/disegna_gola.py`)

`python tools/disegna_gola.py` riscrive le griglie in `mondo/aree/*.area`; con `--controlla` dice se i file sono
aggiornati. Si rifiuta di scriverle se in `gola_miasmi` si passa da A a B senza la nebbia o in `gola_arco` senza
l'arco (`SBARRANO`): sono le celle che fanno partire B-02 e B-03.

| Stanza | Cosa c'è |
| :-- | :-- |
| `gola_striscia` | la via quasi dritta sotto la **striscia nera** del limite K-Pg: uno strato orizzontale e continuo da un capo all'altro, con la scaglia rossa sopra e la bianca sotto; la lapide ai piedi della rupe; lo slargo del forziere (2 Crescia) sulla sponda del Camignano |
| `gola_miasmi` | il torrente scende ripido dal monte e taglia la via: il **ponticello** è corto (assi di traverso, corrimano a monte e a valle); tre chiazze di nebbia, una delle quali sbarra la via appena passato il ponte, bassa sull'acqua |
| `gola_arco` | l'**arco del contrafforte** da parete a parete (la ghiera dei conci, i piloni nella rupe sopra e sotto); i due soldati di B-03 oltre l'arco; lo slargo del forziere (3 Biscotti) |
| `condotto` | il camminamento sopra gli **archi dell'acquedotto** (cornice, ghiere a tutto sesto, pilastri, sotto gli archi la rupe lontana e il torrente), la canaletta col labbro di pietra, la **diga** col lago dietro |

I tile (`tile_della_gola` in `tools/genera_mondo.py`): la scaglia a fasce rosse e bianche che salgono piano verso
monte, fratture ed edera più fitte vicino alla via, il piede della rupe col muschio, la ghiaia della via un tono sotto
la scaglia bianca (la via si legge), terra e felci sulle sponde, l'acqua con sassi e creste di schiuma (i riflessi:
`Esplorazione::aggiorna` scambia i colori 12 e 13 ogni 20 frame). La palette è quella cupa (`palette_cupa`): le
rampe di notte della palette bloccata, un tono più chiare senza mai due voci sullo stesso colore. Nessun colore nuovo.

Le istantanee dei fondali usano la palette cupa per le stanze della gola, come le vede il giocatore:
`python3 tools/istantanee.py CARTELLA --fondale gola_striscia --fondale gola_miasmi --fondale gola_arco --fondale condotto`.

## Il gioco

Le regole e le bandiere sono in `docs/bandiere_da_fare.md` (sezione «La gola del Bottaccione»). In breve: la cella
`MIASMA` (e il `PONTE`) ora è calpestabile anche nel gioco (le celle calpestabili stanno tutte prima di
`PRIMA_CELLA_SOLIDA`, `genera_mondo.controlla_ordine_celle`); B-02 parte sulla prima nebbia col lampo verde, B-03
sotto l'arco; i miasmi feriscono chi corre (poco, mai a morte) e le ferite pesano sulla battaglia dopo; i soldati di
B-03 ci sono fino al piano di Corrado; nel duello l'uscita del Condotto è chiusa; due forzieri presi una volta.

Prove: `src/autotest_gola.cpp`, `tests/test_gola.py`, e le prove di sempre (`test_mondo`, `test_quest_giocabili`,
`autotest_quest`: le radici di Q-SA01 restano raggiungibili, la camminata San Martino → Porta Metauro → gola →
Condotto e ritorno regge).

## Da vedere in mGBA

- le quattro stanze nella palette cupa, i riflessi del torrente;
- B-02 al primo passo nella nebbia (il lampo, poi Antonio e Ubaldo), le ferite correndo (lampo leggero) e i PV in
  meno all'inizio del duello con Corrado;
- B-03 sotto l'arco con i due soldati visibili oltre l'arco, che spariscono dopo la scena;
- il duello: perso, l'uscita del Condotto non si attraversa («Corrado vi sbarra il ritorno») e al secondo tentativo
  le battute non si ripetono;
- i due forzieri (chiuso, poi aperto) e gli oggetti nel menu della battaglia.
