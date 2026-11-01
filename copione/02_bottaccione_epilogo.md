# Atto I, parte seconda: Il Bottaccione e la terza alba

Fonte: GDD Sez. 11 Passo 4 (beat 4-6, anticipati nella v1), Sez. 22 (dungeon), Sez. 26A (Corrado), Sez. 31B (Berto), Sez. 37 (vetrata). Formato nel [README](README.md).

Nella v1 il Bottaccione chiude l'Atto I invece di aprire l'Atto II, come deciso nell'ambito «Atto I e Bottaccione». Si scende dalla Basilica dietro il monte e si rientra in città da Porta Metauro, cioè si chiude l'anello del mondo.

| Scena | Area | Cosa succede | Bandiera alla fine |
| :-- | :-- | :-- | :-- |
| B-01 | Strada del Bottaccione, alto | La striscia nera nella roccia | `BOTTACCIONE_ENTRATI` |
| B-02 | Strada del Bottaccione | I miasmi di Cagli | `MIASMI_VISTI` |
| B-03 | Strada del Bottaccione | Due soldati parlano troppo | `PIANO_DI_CORRADO` |
| B-04 | Il Condotto | Battaglia con Corrado di Spoleto | `CORRADO_SCONFITTO`, `CONDOTTO_SALVO` |
| B-05 | Porta Metauro e San Martino | Rientro di notte, tempo libero | `RIENTRO_PORTA_METAURO` |
| E-01 | Piazza Grande | La terza alba e la risposta del Campanone | `ATTO_I_COMPLETATO` |
| E-02 | Basilica, vetrata | Il primo vetro prende colore; titoli di coda | `CRONACA_V1_FINITA` |

---

## B-01 · La striscia nera

| | |
| :-- | :-- |
| Luogo | Strada del Bottaccione, primo tratto sotto la Basilica |
| Condizione | `VISIONE_BOTTACCIONE` e non `BOTTACCIONE_ENTRATI` |
| Imposta | `BOTTACCIONE_ENTRATI`, palette del Bottaccione (scelta di stile 1: cupo) |

Regia: la gola si stringe. Sulla parete calcarea corre una sottile striscia scura.

- ANTONIO (calmo): Guarda la roccia, ragazzo. Quella striscia nera.
- ANTONIO (calmo): Berto il tagliapietre dice che lì la terra non dorme.
- GIORGIO (calmo): Berto dice un sacco di cose.
- UBALDO (calmo): E qualcuna è vera. Camminate piano.

> Nota. La striscia è il livello scuro della parete del Bottaccione, quello della Sez. 22 (BG3). Le battute di Berto in città (Sez. 31B) la annunciano: se Berto non è stato ascoltato, la scena regge lo stesso.

---

## B-02 · I miasmi

| | |
| :-- | :-- |
| Luogo | Strada del Bottaccione, prima zona di nebbia verde |
| Condizione | primo ingresso in una zona di miasmi |
| Imposta | `MIASMI_VISTI` |

Regia: nebbia verde bassa sull'acqua del Camignano. Vale solo se F6 tiene il pericolo dei miasmi della Sez. 22A; altrimenti la scena si taglia e resta solo la prima battuta come colore.

- ANTONIO (preoccupato): Quest'aria puzza di Cagli. Hanno versato veleno nel fosso.
- UBALDO (calmo): Restate nel mio passo. Finché mi siete vicini, la benedizione vi copre.
- SISTEMA: Nella nebbia verde si perdono HP. Restare vicini a Ubaldo li protegge.

---

## B-03 · Due soldati parlano troppo

| | |
| :-- | :-- |
| Luogo | Strada del Bottaccione, sotto un arco di contrafforte |
| Condizione | il giocatore entra nella zona d'ascolto senza farsi vedere |
| Imposta | `PIANO_DI_CORRADO` |

Regia: due Guerrieri della Roccia di Spoleto stanno di guardia vicino a un fuoco. Il gruppo è nascosto sotto l'arco. Se il giocatore si fa vedere prima, parte la battaglia e la scena si salta.

- GUERRIERO: Il Colosso dice che all'alba il condotto sarà nostro.
- GUERRIERO: E l'alchimista di Cagli?
- GUERRIERO: Ha già versato il suo nel fosso. Gli eugubini berranno la morte, e ringrazieranno.
- GUERRIERO: Io non bevo niente, quaggiù. Neanche l'acqua.
- GIORGIO (deciso): Il Colosso... Corrado di Spoleto. È lui quello del martello.
- UBALDO (calmo): Allora sappiamo chi cercare. E sappiamo che abbiamo tempo fino all'alba.

---

## B-04 · Corrado al Condotto

| | |
| :-- | :-- |
| Luogo | il Condotto, sopra gli archi dell'acquedotto |
| Condizione | arrivo in fondo al dungeon |
| Imposta | `CORRADO_INCONTRATO` prima, `CORRADO_SCONFITTO` e `CONDOTTO_SALVO` dopo |
| Battaglia | `DUELLO_CORRADO`, non si fugge |

Regia: Corrado, il doppio di un uomo, batte il martello sulla pietra del condotto. A ogni colpo l'acqua schizza da una crepa.

- CORRADO: Tre preti su un sentiero di capre. Monaldo mi aveva promesso nemici più grossi.
- GIORGIO (deciso): Io non sono un prete.
- CORRADO: Allora morirai da cavaliere. Fa più rumore.
- UBALDO (deciso): Corrado di Spoleto. Posa il martello e torna a casa con le tue gambe.
- CORRADO: Questa corazza l'ha battuta il patto del Grifo, vescovo. Nessuna lama la apre.
- ANTONIO (deciso): Le lame no. Il fuoco sì.

### Battute in battaglia

Una per evento, la prima volta che succede. Gli eventi sono quelli della Sez. 26A e del piano IA dei boss.

| Evento | Battuta |
| :-- | :-- |
| Turno 1, Scudo di Forgia | CORRADO: Forgia, rispondi! |
| Turno 2, Martello d'Assedio su Giorgio | CORRADO: Il martello cerca il cavaliere! |
| Primo colpo fisico respinto prima dell'ustione | ANTONIO (deciso): Giorgio, la lancia scivola! Prima scaldo io il ferro. |
| Prima Ustione su Corrado | CORRADO: Le piastre... bruciano! |
| Corrado in BREAK | CORRADO: Il ferro... non risponde... |
| Un eroe cade | UBALDO (deciso): In piedi! Non qui, non stanotte! |
| Corrado sotto metà HP | CORRADO: Bene! Finalmente si suda! |

### Dopo la vittoria

Regia: la corazza di Corrado fuma, le piastre colano come cera. Lui arretra fino al bordo del condotto.

- CORRADO: Il ferro... si piega?
- CORRADO: Non è finita, vescovo. Spoleto ha altre forge, e Monaldo altri martelli.

Regia: Corrado si lascia cadere nel vuoto. Sotto, un tonfo nell'acqua del Camignano. Silenzio. Poi solo il rumore della crepa.

- GIORGIO (preoccupato): È caduto... L'ho lasciato andare.
- UBALDO (calmo): No, Giorgio. Hai difeso l'acqua. Il resto non è tuo.
- ANTONIO (calmo): La crepa, piuttosto. Fatevi da parte.

Regia: Antonio raccoglie il martello abbandonato, lo scalda tra le mani finché il ferro diventa rosso, e lo preme nella crepa. Il vapore sale. L'acqua smette di uscire.

- ANTONIO (calmo): Ferro di Spoleto per tappare un buco di Gubbio. Mi piace.
- UBALDO (calmo): Antonio. Hai appena salvato la città che ti chiudeva la porta.
- ANTONIO (calmo): Ho tappato un buco. Non farne una predica.
- SISTEMA: Il condotto è salvo.
- OBIETTIVO: Rientra in città da Porta Metauro.

> Nota. Corrado non muore: nella v1 è l'ultimo boss, ma la Sez. 11 (beat 6) lo rivuole in un duello al passo. Così resta disponibile per un aggiornamento.

---

## B-05 · Porta Metauro

| | |
| :-- | :-- |
| Luogo | Porta Metauro, poi San Martino |
| Condizione | `CONDOTTO_SALVO` |
| Imposta | `RIENTRO_PORTA_METAURO`, fase NPC = NOTTE |

Regia: notte (palette notturna della scelta di stile 3). La porta è chiusa. Una lanterna si muove sulle mura.

- NELLO: Chi va là? Di notte non si apre a nessuno!
- UBALDO (calmo): Nemmeno al tuo vescovo, Nello?
- NELLO: Monsignore! Ma voi... non eravate sul monte?
- ANTONIO (calmo): C'eravamo. Poi il vescovo ha voluto fare due passi.
- NELLO: Dalla gola? Di notte? Aprite, aprite, presto!

Regia: la porta si apre. Si entra in San Martino.

- AREA: San Martino. La notte prima della terza alba.
- UBALDO (calmo): Manca poco all'alba. Se avete promesso qualcosa a qualcuno, è il momento di mantenerlo.
- SISTEMA: Ora puoi girare la città. Quando sei pronto, raggiungi Piazza Grande.
- OBIETTIVO: All'alba, raggiungi Piazza Grande.

Regia: tempo libero. È qui che si consegnano le quest aperte. Entrando in Piazza Grande compare una conferma:

- SISTEMA: L'alba sta per sorgere. Vuoi andare incontro all'araldo?
- SCELTA: Sì, è ora / Non ancora

«Non ancora» riporta il giocatore un passo indietro sul varco. «Sì» avvia E-01. Prima di E-01 il gioco propone di salvare.

---

## E-01 · La terza alba

| | |
| :-- | :-- |
| Luogo | Piazza Grande, alba |
| Condizione | `RIENTRO_PORTA_METAURO` e conferma |
| Imposta | `ATTO_I_COMPLETATO` |

Regia: luce bassa e rosata. Il popolo in piazza, stanco e affamato. L'araldo rientra a cavallo, con la stessa scorta del primo giorno.

- ARALDO: Le tre albe sono passate, vescovo. Le chiavi.
- UBALDO (calmo): Le chiavi restano dove sono.
- ARALDO: Allora Monaldo verrà a prenderle.
- UBALDO (deciso): Che venga. Questa è la nostra risposta.

Regia: Ubaldo alza il pastorale verso la torre. Sul Palazzo dei Consoli il drappo rosso col monte bianco si srotola davanti al grifo dell'araldo. Il Campanone suona a doppi, a lungo. Le note scendono per la valle. Il cavallo dell'araldo si impenna.

- GUIDO (deciso): Suonate! Che lo sentano fino a Perugia!
- ARALDO: Avete scelto, eugubini. Ricordatevelo quando bruceranno le vostre case.

Regia: l'araldo esce al galoppo. Il Campanone continua.

- GIORGIO (calmo): E adesso, padre?
- UBALDO (calmo): Adesso cominciano, Giorgio. Ma ci hanno visti in piedi.
- ANTONIO (calmo): Mi serve altra legna.
- GIORGIO (calmo): Resti, allora?
- ANTONIO (calmo): Resto finché c'è legna da bruciare. Qui, mi pare, ce ne sarà parecchia.

---

## E-02 · La vetrata

| | |
| :-- | :-- |
| Luogo | Basilica, la vetrata del prologo |
| Condizione | `ATTO_I_COMPLETATO` |
| Imposta | `CRONACA_V1_FINITA`, salvataggio di completamento |

Regia: la stessa inquadratura di P-01. Un solo vetro ha preso colore e figure: un gigante di ferro sopra gli archi di un acquedotto, e sotto tre uomini con un cero ciascuno. Gli altri vetri restano chiari.

- NARRATORE: Così passò la terza alba, e Gubbio non aprì le porte.
- NARRATORE: Un vetro ha preso il suo colore. Gli altri aspettano ancora la loro storia.

Regia: titoli di coda sulla destra (crediti storici, fonti CC0 e CC BY dal registro dei crediti, musiche, strumenti). Poi la schermata finale.

- NARRATORE: Fine del primo atto. La cronaca continua.

> Nota. La Sez. 37 chiude con «Gubbio è salva. Anno Domini 1151», ma la v1 lascia l'assedio aperto. Quella frase resta all'ultimo aggiornamento.
