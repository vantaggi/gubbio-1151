# Bandiere della storia che il gioco non legge ancora

Le scene del copione v1 le accendono, ma per ora nessuna scena e nessun sistema del gioco le legge.
`tests/test_storia.py` controlla che ogni bandiera scritta sia letta da una scena, dal gioco
(`LETTE_DAL_GIOCO` in `tools/genera_storia.py`) oppure sia elencata qui (`DA_FARE`).

| Bandiera | Chi la accende | Cosa dovrà fare | Quando |
| :-- | :-- | :-- | :-- |
| `CERI_RISVEGLIATI` | A1-08 | I tre Ceri accesi nell'interno della Basilica (la grafica dei ceri che brillano) e il Fervore che parte più alto in battaglia | Rifinitura della Basilica |

Già collegate (in `LETTE_DAL_GIOCO`): `GIORGIO_NEL_GRUPPO` (il gruppo in battaglia), `IMBOSCATA_STRADONI`
e `CORRADO_SCONFITTO` (il nemico sulla mappa non torna), `CRONACA_V1_FINITA` (il cartello dei titoli di coda),
`RUFINO_ASCOLTATO` e `Q_SM01_CONSEGNATA` (lo scudo in meno di Corrado), `Q_SA01_CONSEGNATA` e
`Q_SP01_CONSEGNATA` (una consegna sola), e quelle delle quest giocabili qui sotto (SV2c): `Q_SM01_PRESA`,
`Q_SA01_PRESA`, `Q_SP01_PRESA`, `FERRO_1`...`FERRO_3`, `ELLEBORO_1`...`ELLEBORO_4`, `ROSA_RIPRESA`,
`INDIZIO_LUCIA`, `INDIZIO_VENDITORE`, `INDIZIO_FONTANIERE`; e quelle della gola qui sotto (T2): `MIASMI_VISTI`,
`PIANO_DI_CORRADO`, `CORRADO_INCONTRATO`, `FORZIERE_CRESCIA`, `FORZIERE_BISCOTTI`; e quelle dei nemici di F10
qui sotto: `GUERRIERI_VINTI`, `GUARDIA_FORNACE_1`...`GUARDIA_FORNACE_3`.

## Regole del copione ora nel codice (F10, quest)

Tutte in `include/storia_logica.h`, provate a tempo di compilazione in `src/autotest_quest.cpp` (con le
negative) e in `tests/test_quest.py`.

| Regola | Dove nel codice | Fonte |
| :-- | :-- | :-- |
| Ogni quest consegnata dà 55 punti a ogni Santo (`progressione::ESPERIENZA_QUEST`, `assegna_esperienza_fissa()`), il premio della tabella e accende la sua bandiera (`Q_SM01_CONSEGNATA`, `Q_SA01_CONSEGNATA`, `Q_SP01_CONSEGNATA`, intervallo 64-127 di `GameState::quest`: il salvataggio resta v3). Si consegna dalla bandiera di partenza fino a `ATTO_I_COMPLETATO` (E-01), una volta sola | `storia::consegna_quest()`, la tabella `QUEST_V1` di `storia.h` (da `QUEST` in `tools/genera_storia.py`) | 04_quest.md, docs/bilanciamento.md |
| Con `RUFINO_ASCOLTATO` o con Q-SM01 consegnata Corrado entra nel duello con uno scudo in meno (4 → 3; le due cose non si sommano) | `storia::scudi_in_meno()` → `Battaglia::ricomincia(..., scudi_in_meno)`; il mirror ha la stessa manopola, 100 battaglie in più in `ATTESE_SCUDO_IN_MENO` | 02_bottaccione_epilogo.md (B-04), 04_quest.md |
| Ubaldo a digiuno da `CITTA_IN_DIGIUNO` al rientro di B-05 (`RIENTRO_PORTA_METAURO`): in battaglia non usa consumabili e nessuno li usa su di lui; gli altri due mangiano | `storia::a_digiuno()` → `Battaglia::ricomincia(..., a_digiuno)`, `Unita::a_digiuno`, `Puntamento::CHI_MANGIA` nel menu | README del copione («Meccanica nuova»), A1-05 |
| La gola resta aperta dopo B-05: da San Martino si esce da Porta Metauro, si risale fino al Condotto e si torna. Nessun varco legge lo stato di partita, e dopo B-05 nella gola non riparte nessuna scena e Corrado non torna | nessuna modifica serviva: lo provano `cammina(DA_PORTA_METAURO, ...)` e `gola_dopo_il_rientro()` | 04_quest.md, Q-SA01 |

## Le quest giocabili (SV2c)

Le tre quest si giocano dall'inizio alla fine. Tutte le bandiere nuove stanno nell'intervallo quest (64-127,
`GameState::quest`): nessun campo nuovo, il salvataggio resta v3. Il contatore di una quest è quante delle sue
bandiere consecutive sono accese (`storia::pezzi_raccolti()`). Prove: `src/autotest_quest.cpp` (la camminata con la
collisione vera fino a ogni oggetto, il giro completo di ogni quest, le negative) e `tests/test_quest_giocabili.py`.

| Bandiera | Chi la accende | Chi la legge |
| :-- | :-- | :-- |
| `Q_SM01_PRESA`, `Q_SA01_PRESA`, `Q_SP01_PRESA` (77-79) | la proposta del datore (`storia::prendi_quest()`) | `storia::momento_del_datore()`: proposta, attesa, consegna, dopo; la prima radice senza la quest presa (Ubaldo, «Prendiamolo»); gli indizi |
| `FERRO_1`...`FERRO_3` (80-82) | toccare un blocco alle fornaci sotto le arcate del Teatro Romano (`storia::raccogli()`) | il contatore di Q-SM01 e le righe «Ancora 2», «Ancora 1», «l'ultimo» (guardia `CONTEGGIO`); il blocco non torna sulla mappa |
| `ELLEBORO_1`...`ELLEBORO_4` (83-86) | toccare una radice: sulla Strada del Bottaccione, nella gola (striscia nera), fra i miasmi, sotto gli archi di B-03 | il contatore di Q-SA01; le radici non leggono la storia, quindi si raccolgono anche dopo B-05 rientrando da Porta Metauro |
| `INDIZIO_LUCIA`, `INDIZIO_VENDITORE`, `INDIZIO_FONTANIERE` (71-73) | con Q-SP01 presa, Lucia, il Venditore delle Logge e Giordano dicono l'indizio dopo le loro battute (`storia::trova_indizio()`); Giordano dopo la sua battuta del DIGIUNO, che accende `INDIZIO_ACQUA` | `storia::infiltrato_presente()`: con tutti e tre l'infiltrato compare sotto le Logge dei Tiratori |
| `ROSA_RIPRESA` (87) | la battaglia con l'infiltrato vinta (`storia::riprendi_la_rosa()`; da F10 la sua battaglia: l'infiltrato e due spie umbre) | l'obiettivo di Q-SP01; l'infiltrato sparisce |

La consegna chiama `storia::consegna_quest()`, che ora rifiuta una quest non presa o con l'obiettivo a metà
(`storia::quest_pronta()`). Non ancora nel gioco: i Guerrieri della Roccia davanti alle fornaci (il nemico non
c'è) e la postierla che Cecco apre per Raniero (nessun varco si chiude).

## La gola del Bottaccione (T2)

Le quattro stanze della gola (`tools/disegna_gola.py`) si giocano. Tutto in `include/storia_logica.h`, provato a
tempo di compilazione in `src/autotest_gola.cpp` (con le negative) e in `tests/test_gola.py`. Le due bandiere nuove
dei forzieri stanno nell'intervallo quest (88-89, `GameState::quest`); le ferite dei miasmi prendono 3 byte del
riservato (`GameState::ferite`): `sizeof(GameState)` resta 64 e il salvataggio resta v3.

| Bandiera | Chi la accende | Chi la legge |
| :-- | :-- | :-- |
| `MIASMI_VISTI` | B-02, che ora parte sulla **prima nebbia** (non entrando nella stanza): prima un lampo verde, poi l'avviso di Ubaldo e la riga del SISTEMA | `storia::respira_i_miasmi()`: da qui i miasmi feriscono. La regola: solo sulla nebbia e solo **correndo** (B: chi corre lascia indietro Ubaldo, «Restate nel mio passo»); ogni 30 frame 4 PV a Giorgio e ad Antonio (Ubaldo mai), fino al 15% dei loro PV; un lampo leggero a ogni ferita. Le ferite pesano sulla prossima battaglia (i Santi partono con quei PV in meno, mai sotto 1: nessuno muore), poi si azzerano; uscendo dalla gola guariscono |
| `PIANO_DI_CORRADO` | B-03, che ora parte **sotto l'arco** del contrafforte («il gruppo è nascosto sotto l'arco») | `storia::sentinelle_presenti()`: i due soldati (la figura del soldato) stanno oltre l'arco finché il piano non è ascoltato |
| `CORRADO_INCONTRATO` | B-04, ma già **quando parte il duello** (`storia::all_incontro()`), non alla fine | `storia::varco_chiuso()`: l'uscita del Condotto verso la gola si urta come un muro finché Corrado non è battuto («Corrado vi sbarra il ritorno»); persa la battaglia si torna all'ingresso del Condotto e si riprova a PV pieni. `storia::gia_incontrata()`: al secondo tentativo le battute di B-04 non si ripetono |
| `FORZIERE_CRESCIA`, `FORZIERE_BISCOTTI` (88-89) | toccare il forziere nello slargo della striscia nera (2 Crescia) e in quello dell'arco (3 Biscotti) (`storia::apri_forziere()`) | `storia::forziere_chiuso()`: preso una volta, il forziere resta lì aperto |

## I nemici che mancavano (F10, ramo `f10-b03`)

| Bandiera | Chi la accende | Cosa fa nel gioco |
| :-- | :-- | :-- |
| `GUERRIERI_VINTI` (90) | B-03: la battaglia breve con i due Guerrieri della Roccia, **a metà scena** (dopo l'ascolto, prima del ragazzo eugubino; `BATTAGLIA_A_META` di `storia.h`), vinta (`storia::vinta_a_meta()`); nel giro senza camminare la accende `storia::chiudi_scena()` | `storia::battaglia_da_combattere()`: non si rigioca. Persa, la scena resta da giocare e si torna all'ingresso della stanza dell'arco (spawn 1); ripassando sotto l'arco l'ascolto si ripete e si rifà la battaglia |
| `GUARDIA_FORNACE_1`...`GUARDIA_FORNACE_3` (91-93) | toccare la guardia (un Guerriero della Roccia, la figura della battaglia) davanti a un blocco di ferro al Teatro Romano e vincere la sua battaglia (`storia::batti_la_guardia()`) | `storia::guardia_presente()`: la guardia non torna. `storia::raccolta_libera()`: il blocco che guardava si prende solo da qui («Battuto il guerriero, il blocco si raccoglie toccando la fornace»). Persa, si torna all'ingresso del Teatro (spawn 1) e la guardia resta. Le guardie ci sono anche senza la quest presa, come i blocchi |

Le battaglie e l'esperienza sono in `docs/bilanciamento.md`.

Le celle che fanno partire B-02 e B-03 (la nebbia, l'arco) sbarrano la via da parete a parete: lo controllano
`tools/disegna_gola.py` (si rifiuta di scrivere le griglie), `src/autotest_gola.cpp` (`si_passa_senza`) e
`tests/test_gola.py`. Così le scene non si saltano e la storia non si ferma.
