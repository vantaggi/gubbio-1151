# T2: stato del lavoro (WIP, 2 nov 2026 sera)

Ramo `f8-t2a`, non unito. Fermato su richiesta (il PC si spegne).

## Fatto (non verificato)
- `tools/disegna_gola.py`: griglie nuove delle 4 stanze (via che curva e respira, slarghi in
  SLARGHI, torrente con ponticello `+` in gola_miasmi, erba/cespugli/massi/lecci, striscia nera
  continua e lapide `i`, arco del contrafforte, Condotto stretto sopra gli archi `P` con canaletta
  e diga `|`). Griglie scritte in mondo/aree/*.area; genera_mondo passa i suoi controlli.
- `tools/genera_mondo.py`: celle `i` `+` `|`; tile della gola (scaglia rossa/bianca a strati
  irregolari, frattura, piede con muschio, edera, striscia nera, lapide, ghiaia, terra, erba, acqua
  con sassi e schiuma, ponte, diga, archi dell'acquedotto) scelti da `tile_della_gola`;
  palette cupa un tono piu' chiara (`palette_cupa`).
- `src/esplorazione.cpp`: riflessi dell'acqua (colori 12/13 scambiati ogni 20 frame nelle aree cupe).
- `tools/istantanee.py`: colori delle celle nuove.

## Da sistemare subito
- La build si ferma: `src/autotest_mondo.cpp:25` static_assert fallisce (autotest del mondo a tempo
  di compilazione: una camminata o uno spawn delle griglie nuove non regge). Prossimo passo: capire
  quale area/varco (autotest_mondo_fallito(errore, area, varco)) e correggere disegna_gola.py.
- Poi: istantanee AVVIO=2, test (test_mondo, test_bottaccione: aggiornare se servono), camminata.

## Manca (T2b, gioco)
- Miasmi che tolgono PV (regola semplice da scegliere), lampeggio e messaggio la prima volta.
- I due soldati di B-03 con la figura soldato di S.
- Lettura di MIASMI_VISTI, PIANO_DI_CORRADO, CORRADO_INCONTRATO; chiudere docs/bandiere_da_fare.md.
- 1-2 forzieri (Crescia, Biscotti) negli slarghi, presi una volta e salvati.
- Test con negative, camminata, log della storia.

Poi F7 (audio) e F8 (bilanciamento), come da coda del coordinatore.
