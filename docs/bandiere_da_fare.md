# Bandiere della storia che il gioco non legge ancora

Le scene del copione v1 le accendono, ma per ora nessuna scena e nessun sistema del gioco le legge.
`tests/test_storia.py` controlla che ogni bandiera scritta sia letta da una scena, dal gioco
(`LETTE_DAL_GIOCO` in `tools/genera_storia.py`) oppure sia elencata qui (`DA_FARE`).

| Bandiera | Chi la accende | Cosa dovrà fare | Quando |
| :-- | :-- | :-- | :-- |
| `MIASMI_VISTI` | B-02 | La nebbia verde del Bottaccione: i miasmi tolgono PV a chi li attraversa, la prima volta parte la scena | Dungeon del Bottaccione (pezzo T) |
| `PIANO_DI_CORRADO` | B-03 | Le guardie del Condotto in allerta: dopo aver ascoltato il piano, Corrado aspetta al Condotto | Dungeon del Bottaccione (pezzo T) |
| `CORRADO_INCONTRATO` | B-04 | Il duello da cui non si fugge: dopo l'incontro l'uscita del Condotto resta chiusa finché Corrado non è battuto | Dungeon del Bottaccione (pezzo T) |
| `CERI_RISVEGLIATI` | A1-08 | I tre Ceri accesi nell'interno della Basilica (la grafica dei ceri che brillano) e il Fervore che parte più alto in battaglia | Rifinitura della Basilica |

Già collegate (in `LETTE_DAL_GIOCO`): `GIORGIO_NEL_GRUPPO` (il gruppo in battaglia), `IMBOSCATA_STRADONI`
e `CORRADO_SCONFITTO` (il nemico sulla mappa non torna), `CRONACA_V1_FINITA` (il cartello dei titoli di coda),
`RUFINO_ASCOLTATO` e `Q_SM01_CONSEGNATA` (lo scudo in meno di Corrado), `Q_SA01_CONSEGNATA` e
`Q_SP01_CONSEGNATA` (una consegna sola).

## Regole del copione ora nel codice (F10, quest)

Tutte in `include/storia_logica.h`, provate a tempo di compilazione in `src/autotest_quest.cpp` (con le
negative) e in `tests/test_quest.py`.

| Regola | Dove nel codice | Fonte |
| :-- | :-- | :-- |
| Ogni quest consegnata dà 55 punti a ogni Santo (`progressione::ESPERIENZA_QUEST`, `assegna_esperienza_fissa()`), il premio della tabella e accende la sua bandiera (`Q_SM01_CONSEGNATA`, `Q_SA01_CONSEGNATA`, `Q_SP01_CONSEGNATA`, intervallo 64-127 di `GameState::quest`: il salvataggio resta v3). Si consegna dalla bandiera di partenza fino a `ATTO_I_COMPLETATO` (E-01), una volta sola | `storia::consegna_quest()`, la tabella `QUEST_V1` di `storia.h` (da `QUEST` in `tools/genera_storia.py`) | 04_quest.md, docs/bilanciamento.md |
| Con `RUFINO_ASCOLTATO` o con Q-SM01 consegnata Corrado entra nel duello con uno scudo in meno (4 → 3; le due cose non si sommano) | `storia::scudi_in_meno()` → `Battaglia::ricomincia(..., scudi_in_meno)`; il mirror ha la stessa manopola, 100 battaglie in più in `ATTESE_SCUDO_IN_MENO` | 02_bottaccione_epilogo.md (B-04), 04_quest.md |
| Ubaldo a digiuno da `CITTA_IN_DIGIUNO` al rientro di B-05 (`RIENTRO_PORTA_METAURO`): in battaglia non usa consumabili e nessuno li usa su di lui; gli altri due mangiano | `storia::a_digiuno()` → `Battaglia::ricomincia(..., a_digiuno)`, `Unita::a_digiuno`, `Puntamento::CHI_MANGIA` nel menu | README del copione («Meccanica nuova»), A1-05 |
| La gola resta aperta dopo B-05: da San Martino si esce da Porta Metauro, si risale fino al Condotto e si torna. Nessun varco legge lo stato di partita, e dopo B-05 nella gola non riparte nessuna scena e Corrado non torna | nessuna modifica serviva: lo provano `cammina(DA_PORTA_METAURO, ...)` e `gola_dopo_il_rientro()` | 04_quest.md, Q-SA01 |

Ancora da fare (SV2c, quest giocabili): i dialoghi di proposta e consegna, i contatori (blocchi, radici,
indizi), gli oggetti da raccogliere sulla mappa. Quando ci saranno, la consegna chiama
`storia::consegna_quest()`; fino ad allora le tre bandiere delle consegne non si accendono giocando.
