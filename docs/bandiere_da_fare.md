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
e `CORRADO_SCONFITTO` (il nemico sulla mappa non torna), `CRONACA_V1_FINITA` (il cartello dei titoli di coda).

Letta dal copione, con la meccanica ancora da fare: `RUFINO_ASCOLTATO` (Rufino, battuta del DIGIUNO) cambia
una battuta di Giorgio in B-04; la regola decisa è che con lei, o con Q-SM01 consegnata, Corrado entri nel
duello con uno scudo in meno. Lo scudo in meno spetta al codice della battaglia (bilanciamento).
