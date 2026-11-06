# Il percorso da zero

Come si fa un gioco della serie dal primo giorno, nell'ordine giusto. È il percorso che avremmo seguito
per Gubbio 1151 sapendo quello che sappiamo ora: ogni fase dice cosa si decide, cosa esce, come si
capisce che è finita, e da quale lezione nasce ([LEZIONI.md](LEZIONI.md)).

La regola che tiene insieme tutto: **prima si decide ciò che costa caro cambiare, poi si produce**. Le
decisioni di fondazione (fase 0), la struttura della storia (fase 3), l'orientamento e lo standard
grafico (fase 4) e i limiti dell'hardware (fase 5) si chiudono prima della produzione in serie; tutto il
resto si può correggere giocando.

## In breve

| Fase | Cosa | Chi decide | Cancello per passare oltre |
| :-- | :-- | :-- | :-- |
| 0 | Fondazioni: rilascio, licenze, asset, repo, ambito, ruoli, toolchain | Il committente, con proposte | Scheda di avvio completa; ROM vuota compilata in cloud, in CI e sul PC |
| 1 | Ricerca e censimento della città e della storia vera | Claude, conferme del committente | Dati versionati con fonti; punti dubbi confermati da chi conosce il posto |
| 2 | Design dal lato di chi gioca: schermate, azioni, sistemi | Claude dopo ricerca | Inventario delle schermate chiuso, mockup approvati |
| 3 | Storia: prompt, Bibbia, scaletta, grafo, copione | Claude, Bibbia approvata dal committente | Grafo della trama a 0 errori |
| 4 | Stile e standard, orientamento con greybox | Il committente sceglie fra proposte | Pezzo campione per tipo approvato; greybox giocato |
| 5 | Fondamenta tecniche dal modello | Claude | Controlli e budget attivi, prove in mGBA in cloud |
| 6 | Fetta verticale al livello finale | Il committente gioca | Ok del committente giocando |
| 7 | Produzione in parallelo | Claude e i custodi | Ogni pezzo con prove verdi e ok dei custodi |
| 8 | Bilanciamento, prove lunghe, caccia ai crash | Claude, il committente gioca | Partita completa senza crash, stress test verdi |
| 9 | Prova privata e rilascio | Il committente | Checklist di rilascio chiusa |

Ogni fase chiude con una **prova giocata** dal committente su una sola ROM (L12): quello che trova
diventa prima una prova automatica e poi una correzione.

---

## Fase 0 · Fondazioni (giorno 1, prima di qualunque codice)

Si compila [modelli/SCHEDA_AVVIO.md](modelli/SCHEDA_AVVIO.md). Ogni domanda si porta al committente una
alla volta, con un'opzione consigliata e il perché (D102).

1. **Cosa vuol dire rilascio** (gratis, a pagamento, prova privata prima): D002, D003.
2. **Da dove vengono gli asset**: procedurali, fonti libere, foto solo come riferimento (D004). Mai foto
   del web nel repo (L01).
3. **Licenze** di codice e contenuti, registro dei crediti con test (D007).
4. **Repo e rami**: repo nuovo per ogni gioco, si sviluppa su `main` dal primo giorno, tag ai punti
   fermi (D006, L01).
5. **Ambito della v1**: ore di gioco, numero di aree, sistemi dentro e lista di quelli fuori (D008).
6. **Ruoli**: chi decide trama e design, chi gioca e giudica, quanta autonomia (D010, D103), merge
   autonomo (D100, D101), niente spoiler al committente (D077).
7. **Lingua e convenzioni dei nomi** (D009; per santi e luoghi vedi D075).
8. **Toolchain verificata in cloud**: versioni bloccate, immagine per digest, mirror per Docker, build e
   una prova mGBA senza schermo che passano in cloud, in CI e sul PC (D020, D021, D023, L07).
9. **Il metodo**: si copia `docs/metodo/` dal gioco precedente e si azzera il registro (D108, L19).

**Esce:** scheda di avvio firmata, repo con licenze, `toolchain.lock`, CI verde su una ROM vuota.
**Prova giocata:** la ROM vuota si avvia in mGBA e sul telefono del committente.

## Fase 1 · Ricerca e censimento

Si raccoglie la città vera e la storia vera prima di disegnare o scrivere (L16).

- Monumenti con misure in pianta (OSM), altezze, lato della facciata; rete stradale; quote. Le query a
  OSM e Commons si fanno sul PC, perché il cloud non le raggiunge.
- Foto di riferimento con autore e licenza in un elenco versionato, mai nel repo (D004).
- Simboli: stemmi, colori, cose da non usare perché moderne o legate ad altro (D067); la lista la
  conferma chi conosce il posto.
- Fonti storiche e date incerte, con il livello di fiducia.
- Per le persone vere nel gioco: nomi di gioco, regola di rispetto (D074).

**Esce:** `mondo/` con il contratto delle aree scritto dai dati (D063), censimento e simboli.
**Cancello:** i punti dubbi (confini, direzioni, nomi) confermati dal committente.

## Fase 2 · Design dal lato di chi gioca

Prima del piano dei pezzi si scrive cosa deve vedere e poter fare chi gioca (L09).

- Inventario delle schermate: titolo, pausa, diario e obiettivi, mappa con segnalini, bisaccia,
  compagni, salvataggio, opzioni, negozio, dialogo, cartelli, interni, battaglia, aiuti (D096).
- Per ogni schermata di scelta: «cosa deve sapere chi gioca per scegliere» e due o tre giochi del genere
  come riferimento (L11, D095).
- Sistemi: battaglia, crescita, nemici sulla mappa o no (D093), salvataggio (D097), cutscene (D090).
- Mockup generati con i dati di stile, non disegnati a mano.

**Esce:** proposta di design con mockup; pezzi del piano.
**Cancello:** il committente ha visto i mockup e ha detto cosa non gli torna.

## Fase 3 · Storia

Ordine fisso (L03): ricerca → prompt della storia → Bibbia → scaletta → grafo → copione.

1. **Prompt della storia** sul modello di quello di Gubbio (tema, fronti, archi, segreti e indizi,
   dilemmi, tempo, luoghi, meccaniche che raccontano, leggerezza, prove di qualità): D071.
2. **Bibbia della storia** approvata dal committente. Da qui in poi il committente non vede più dettagli
   di trama (D077).
3. **Scaletta** delle scene e delle scelte, poi il **grafo** della trama a 0 errori (D072).
4. **Guida di scrittura** prima delle battute: nome a schermo per tutti, battute concrete, niente
   riferimenti non spiegati (D080, L10); convenzioni di redazione con test (D081).
5. **Copione** in Markdown, unica sorgente dei testi (D073). Le copie fuori dal repo si rigenerano (L13).
6. Il **motore della storia** si scrive solo ora, per il tipo di scelte che la Bibbia chiede (L03).

**Cancello:** grafo a 0 errori, verifica del copione a 0 errori, un campione di battute letto dal
committente.

## Fase 4 · Stile, standard e orientamento

1. **Greybox giocabile** della città: blocchi, nomi delle aree, varchi, orientamento (nord in alto salvo
   motivo forte) giocato dal committente prima di dipingere (L02, D061).
2. **Le 12 scelte di stile** una alla volta, con ricerca e tavole generate (D040-D051). Proporzioni del
   personaggio e scala degli edifici nella stessa tavola, con la figura davanti a una porta (L17, D046).
3. **Guida in dati** con test di conformità (D052).
4. **Standard grafico** con regole siglate e test per quelle misurabili, insieme alla Guida e non dopo
   (L04, D054).
5. **Pezzo campione per tipo** (figura, edificio, suolo, interno, oggetto, riquadro, cutscene con i
   protagonisti), ciascuno passato dal loop di 10 giri (D055) e approvato giocando (L05).
6. **Custode visivo** nominato: ogni grafica nuova passa da lui (D107).

**Cancello:** greybox giocato e campioni approvati.

## Fase 5 · Fondamenta tecniche dal modello

Si parte dal modello di repo (vedi [GENERICO_E_SPECIFICO.md](GENERICO_E_SPECIFICO.md)), non da zero.

- Regole di codice GBA con i loro controlli già attivi, `-Werror`, zero heap, gate EWRAM (D028, D029,
  L08).
- **Tabella dei budget** della console (sprite, palette, tile per area, strati di ordinamento, VRAM,
  EWRAM, CPU per frame) con contatori nel pannello di debug e prove di picco in mGBA (D030, L06).
- Giro corto delle prove e parallelo (D027, L14); prove negative e niente skip (D025); oracoli che
  guardano lo schermo e non solo i log (D026).
- Generatori: testi e font, storia, regia, mondo, stile, audio; salvataggio con versione e CRC (D097).
- Test dei nomi coerenti e dei crediti dal primo giorno (D076, L13).

**Cancello:** tutte le prove verdi in cloud e in CI su una scena di prova, pannello di debug con i
contatori.

## Fase 6 · Fetta verticale

Un'area, un interno, una porta, un dialogo con un NPC e un amico, una battaglia con la scheda delle
mosse, una cutscene con i protagonisti, il menù di pausa: tutti al livello finale (L05).

**Cancello:** il committente la gioca e dice «così». Senza ok non parte la produzione in serie.

## Fase 7 · Produzione in parallelo

- Piano a grafo con dipendenze e **risorse esclusive** (D106): due pezzi che toccano lo stesso file non
  vanno in parallelo (L15).
- Ogni thread ha un brief ([modelli/BRIEF_THREAD.md](modelli/BRIEF_THREAD.md)): contratto, file di sua
  proprietà, custodi, criterio d'uscita, prossimo pezzo in coda (L15).
- Custode visivo e custode di trama e nomi approvano prima di ogni fusione (D107); il coordinatore gira
  ogni decisione ai thread toccati (D105).
- Il repo è l'unica fonte; ogni file fuori dal repo dice da dove viene; WIP committato su un ramo prima
  di fermarsi (L18).
- Ogni decisione e ogni rifacimento entrano in `docs/metodo/` nella stessa fusione (D108).

**Cancello di ogni pezzo:** prove verdi, ok dei custodi, ROM unica in `rom/` (D031).

## Fase 8 · Bilanciamento e crash

- Bilanciamento con il pilota automatico e il gemello Python della battaglia (D092).
- Prove lunghe: partita completa automatica, tutte le combinazioni di scelte, stress test per area e per
  passaggio di scena (D032, L06).
- Il committente gioca una partita completa (L12).

**Cancello:** partita completa senza crash né lag, picchi dei budget sotto il margine.

## Fase 9 · Prova privata e rilascio

Prima gli amici offline (D003), poi, se piace, la checklist di rilascio (D110, D111): persone vere,
beni culturali, dichiarazione IA, crediti, pagina, ROM della CI.

---

## Le prime dieci decisioni, in ordine

1. Cosa vuol dire rilascio (D002, D003).
2. Da dove vengono gli asset (D004).
3. Licenze (D007).
4. Repo e rami (D006).
5. Ambito della v1 (D008).
6. Ruoli e autonomia (D010, D103).
7. Toolchain verificata in cloud (D023).
8. Orientamento e vista, con greybox (D061, D042).
9. Struttura della storia, con prompt e Bibbia (D071).
10. Standard grafico e budget dell'hardware (D054, D030).

## Com'è andata per Gubbio 1151 e come andrebbe

| Giorno | Com'è andata | Come andrebbe col percorso |
| :-- | :-- | :-- |
| 1 nov | Fondazioni, stile in 12 scelte, F0-F1, censimento | Fondazioni e toolchain in cloud; ricerca |
| 2 nov | Mondo e città dipinti, contratto rifatto due volte, cutscene | Censimento chiuso, design e greybox giocato |
| 3 nov | Storia rifatta in v2, grafo della trama, piano a grafo | Bibbia e grafo prima del copione; standard e campioni |
| 4 nov | Standard grafico, 218 commit di rifacimenti, prima prova, rotazione a nord | Fondamenta dal modello e fetta verticale |
| 5 nov | Regole GBA, crash di sprite e palette, NPC e mosse rifatti | Produzione in parallelo senza rifacimenti di fondazione |

Stima onesta: con questo percorso le prime due giornate servono a decidere e provare, non a produrre,
ma si risparmiano i rifacimenti dei giorni 3-5. Per il prossimo gioco la fase 5 parte già fatta dal
modello.
