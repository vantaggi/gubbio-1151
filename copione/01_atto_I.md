# Atto I: Il digiuno del Monte Ingino

Fonte: GDD Sez. 4 (Atto I), Sez. 7 (Scene 1-3), Sez. 11 Passi 3, 4 e 6, Sez. 31B (Guido), Sez. 34A-B (cinematiche). Percorso sulle aree di `docs/mappa_del_mondo.md`. Formato nel [README](README.md).

Il filo dell'atto, in una riga per scena:

| Scena | Area | Cosa succede | Bandiera alla fine |
| :-- | :-- | :-- | :-- |
| A1-01 | Piazza Grande | L'araldo porta l'ultimatum, Ubaldo risponde, Giorgio entra nel gruppo | `ULTIMATUM_RICEVUTO` |
| A1-02 | via dei Consoli | Giorgio non capisce il digiuno | `CHIACCHIERA_CONSOLI` |
| A1-03 | San Martino | Cecco alla postierla: come si rompono gli scudi | `POSTIERLA_APERTA` |
| A1-04 | Teatro Romano | Prima battaglia; Antonio salvato e convinto | `ANTONIO_NEL_GRUPPO` |
| A1-05 | Piazza Grande | La città si chiude; tempo libero per le quest | `CITTA_IN_DIGIUNO` |
| A1-05b | Sant'Agostino, fuori Porta Romana | Il borgo chiede di entrare (dilemma D1) | `BORGO_DENTRO` o `BORGO_FUORI` |
| A1-06 | Duomo e Ducale | Congedo dalla città | `PORTA_DEL_MONTE` |
| A1-07 | Stradoni del Monte | Salita, imboscata, la spia | `SPIA_CATTURATA` |
| A1-08 | Basilica | Il rito: risveglio dei Ceri e Spettri del Dubbio | `CERI_RISVEGLIATI` |
| A1-09 | Basilica | Gli indizi e la visione del Bottaccione | `VISIONE_BOTTACCIONE` |

Il seguito (dungeon, Corrado, epilogo) è in [02_bottaccione_epilogo.md](02_bottaccione_epilogo.md).

---

## A1-01 · L'ultimatum sul loggiato

| | |
| :-- | :-- |
| Luogo | Piazza Grande, davanti a Palazzo dei Consoli |
| Condizione | `PROLOGO_VISTO` |
| Imposta | `ULTIMATUM_RICEVUTO`, `GIORGIO_NEL_GRUPPO`, fase NPC = ULTIMATUM |

Regia: si controlla Ubaldo per pochi passi fino al console Guido (cinematica 1 della Sez. 34A subito dopo). Etichetta d'area: «Piazza Grande». Sul parapetto c'è Giorgio che guarda la valle.

- AREA: Gubbio, Piazza Grande. Il primo giorno.
- GUIDO (preoccupato): Monsignore... undici stendardi circondano la conca.
- GIORGIO (deciso): Datemi venti cavalieri, console. Prima di sera li ricaccio oltre i colli.
- GUIDO (preoccupato): Venti? Non ne ho dieci che sappiano stare in sella, ragazzo.

Regia: tamburi lontani. Un cavaliere entra in piazza: sul petto e sul drappo della lancia, il grifo bianco di Perugia su rosso. Sopra di lui, sulla torre, sventola il monte bianco di Gubbio sullo stesso rosso. È la cinematica 1: le ombre delle truppe avanzano nelle valli, l'araldo getta la pergamena insanguinata ai piedi di Ubaldo.

- ARALDO: Popolo di Gubbio! Parla Monaldo, signore di Perugia e delle undici città.
- ARALDO: Aprite le porte e consegnate le chiavi del Cassero.
- ARALDO: Avete tre albe. Alla terza, se le porte saranno ancora chiuse, non resterà pietra su pietra.
- ARALDO: E Monaldo parla anche per chi avete cacciato dalle vostre torri.

Regia: il colpo del pastorale sulla pietra interrompe i tamburi. Silenzio.

- UBALDO (deciso): Gubbio non piega la schiena davanti al ferro corrotto.
- UBALDO (deciso): Riferisci al tuo padrone che la pietra di questo monte è saldata con la fede, non con la paura.
- UBALDO (deciso): Prima che parli la spada, parlerà il cielo.
- ARALDO: Il cielo, vescovo? Il cielo non ha mai fermato un esercito. Tre albe.

Regia: l'araldo esce. Giorgio scatta verso le scale.

- GIORGIO (deciso): Lasciatemelo inseguire, padre! Un araldo in meno è una bugia in meno.
- UBALDO (calmo): Un araldo si rispetta, Giorgio. Anche quando porta parole sporche.
- GUIDO (preoccupato): Il grano basta per una settimana. Le mura che avete rifatto voi reggeranno, ma la fame no.
- UBALDO (calmo): Non contare le lance dei perugini, Guido. Conta la fede di chi abita queste pietre.
- UBALDO (deciso): Sprangate le porte. Per tre giorni, quante sono le albe che ci ha dato, la città digiuni e taccia.
- UBALDO (calmo): Io li passerò in preghiera sul Monte Ingino. Giorgio verrà con me. E ci serve Antonio.
- GIORGIO (preoccupato): L'eremita? Quello che parla solo con i maiali?
- UBALDO (calmo): Parla anche con me. Di rado, ma parla.
- GUIDO (preoccupato): Ieri era fuori dalle mura, al Teatro Romano. E al tramonto chiudo l'ultima postierla.
- UBALDO (deciso): Allora andiamo prima del tramonto.
- SISTEMA: Giorgio si unisce al gruppo.
- OBIETTIVO: Raggiungi il Teatro Romano, fuori dalle mura di San Martino.

> Nota. «Monaldo non concederà una seconda alba» (Sez. 11 Passo 6) diventa «tre albe», così il digiuno di tre giorni ha un senso preciso e l'epilogo della v1 cade alla terza alba. Vedi le note di coerenza nel README.

---

## A1-02 · Due passi per via dei Consoli

| | |
| :-- | :-- |
| Luogo | via dei Consoli, al primo ingresso |
| Condizione | `ULTIMATUM_RICEVUTO`, né `CHIACCHIERA_CONSOLI` né `CITTA_IN_DIGIUNO` (via dei Consoli si può evitare: dopo la chiusura della città la chiacchiera non parte più) |
| Imposta | `CHIACCHIERA_CONSOLI` |

Regia: si ferma il controllo per due battute, poi si riparte. Nessuna cinematica.

- GIORGIO (preoccupato): Padre, perché tre giorni? Le battaglie non si vincono in ginocchio.
- UBALDO (calmo): Nemmeno di corsa. Cammina.

---

## A1-03 · La postierla di San Martino

| | |
| :-- | :-- |
| Luogo | San Martino, varco verso il Teatro Romano |
| Condizione | `ULTIMATUM_RICEVUTO` e non `POSTIERLA_APERTA` (prima di allora il varco è chiuso da Cecco) |
| Imposta | `POSTIERLA_APERTA` |

Regia: Cecco il Balestriere sta di guardia alla postierla. È il personaggio che spiega la battaglia. Le sue battute di tutorial vanno lette con il sistema dello Shield Break del prototipo.

- CECCO: Monsignore, fuori ci sono pattuglie perugine. Al vespro chiudo, con voi o senza.
- UBALDO (calmo): Ci basta meno del vespro, Cecco.
- CECCO: Allora ascolta, cavaliere. Un cavaliere senza mira è solo un bersaglio di latta.
- CECCO: Ogni nemico porta i suoi scudi. Colpiscilo con ciò che teme e li spezzi uno a uno.
- CECCO: A scudi rotti barcolla e perde il turno. È lì che devi piantare la punta della lancia.
- GIORGIO (deciso): Ho capito. Colpire forte.
- CECCO: Colpire giusto. Il forte viene dopo.
- OBIETTIVO: Esci dalla postierla e trova Antonio.

---

## A1-04 · Antonio al Teatro Romano

| | |
| :-- | :-- |
| Luogo | Teatro Romano, tra le arcate |
| Condizione | `POSTIERLA_APERTA` e non `ANTONIO_NEL_GRUPPO` |
| Imposta | `ANTONIO_NEL_GRUPPO` |
| Battaglia | `PATTUGLIA_PERUGINA` (3 nemici), non si fugge, Antonio presente come ospite |

Regia: Antonio, curvo sotto una fascina, è circondato da tre Fanti di Perugia. Dietro di loro fuma una tenda bruciata.

- FANTE: Vecchio, quel fuoco l'hai acceso tu? Hai bruciato la nostra tenda!
- ANTONIO (calmo): La vostra tenda stava sopra la mia legna. Non è colpa mia.
- FANTE: Prendetelo!
- GIORGIO (deciso): Giù le mani dall'eremita!

Regia: transizione di battaglia. Durante lo scontro compaiono le battute di tutorial, una alla volta, al primo turno utile.

- SISTEMA: Scegli Attacca e poi il bersaglio. Ogni colpo giusto toglie uno scudo.
- SISTEMA: A zero scudi il nemico va in BREAK e perde il turno.
- SISTEMA: Antonio combatte con voi, ma per ora non ascolta ordini.

Dopo la vittoria:

- ANTONIO (calmo): Ce la facevo da solo.
- GIORGIO (deciso): Erano tre contro uno, eremita!
- UBALDO (calmo): Antonio. La città chiude le porte al tramonto. Vieni dentro.
- ANTONIO (deciso): La città mi ha chiuso le porte in faccia per vent'anni, Ubaldo. Può continuare.
- UBALDO (calmo): Non ti chiedo di venire per la città. Ti chiedo di salire con me sul monte. Tre giorni.
- ANTONIO (calmo): A pregare? Io prego da solo.
- UBALDO (calmo): Lo so. E il tuo fuoco brucia da solo. Per questo resta piccolo.
- ANTONIO (preoccupato): ...
- ANTONIO (calmo): Hai sempre avuto la lingua più affilata della verga.
- ANTONIO (deciso): Va bene, vescovo. Fino al monte. Poi vedremo.
- SISTEMA: Antonio si unisce al gruppo.
- OBIETTIVO: Torna in città prima che chiudano la postierla.

> Se la quest «Il ferro del Monte Calvo» entra nella v1, le fornaci occupate stanno qui al Teatro Romano: vedi il file delle quest.

---

## A1-05 · La città si chiude

| | |
| :-- | :-- |
| Luogo | Piazza Grande, al rientro |
| Condizione | `ANTONIO_NEL_GRUPPO` e non `CITTA_IN_DIGIUNO` |
| Imposta | `CITTA_IN_DIGIUNO`, fase NPC = DIGIUNO |

Regia: la postierla si chiude alle spalle del gruppo con un tonfo (si sente anche se il giocatore è già lontano). In Piazza Grande la gente è radunata. Il Campanone batte tre rintocchi lenti.

- GUIDO (calmo): Le porte sono sprangate, monsignore. Ora la città aspetta voi.
- UBALDO (deciso): Gente di Gubbio! Per tre giorni le botteghe tacciano e le tavole restino vuote.
- UBALDO (deciso): Non per paura. Perché chi digiuna insieme impara a resistere insieme.
- UBALDO (calmo): Io salgo al monte con questi due. Pregate per noi, e noi pregheremo per voi.
- GUIDO (preoccupato): E il borgo di Sant'Agostino, monsignore? Sta fuori da Porta Romana.
- UBALDO (preoccupato): Il borgo... Passerò da Porta Romana prima di salire.
- GIORGIO (preoccupato): Padre, se tutti digiunano... noi cosa mangiamo per la strada?
- UBALDO (calmo): Il digiuno è per chi prega. Chi combatte, mangi.
- ANTONIO (calmo): Finalmente una regola che capisco.
- SISTEMA: Ubaldo digiuna: fino al ritorno in città non può usare il cibo.
- GUIDO (calmo): La strada del monte passa dal Duomo. Che Dio vi accompagni.
- UBALDO (calmo): Prima, Porta Romana. Poi il monte.
- SISTEMA: Prima di salire puoi girare la città.
- OBIETTIVO: Sali al Monte Ingino passando dal Duomo.

Regia: da qui i Quartieri sono aperti e i datori di quest parlano. Il gioco non spinge: l'obiettivo resta in alto finché il giocatore non entra negli Stradoni.

---

## A1-05b · Il borgo fuori Porta Romana (dilemma D1)

| | |
| :-- | :-- |
| Luogo | Sant'Andrea, a Porta Romana; davanti, il borgo di Sant'Agostino |
| Condizione | `CITTA_IN_DIGIUNO`, né `BORGO_DENTRO` né `BORGO_FUORI` |
| Imposta | `BORGO_DENTRO` oppure `BORGO_FUORI` |

Regia: la porta è socchiusa. Fuori, la gente del borgo con fagotti e carretti. Andreuccio, il miliziano, tiene la soglia; accanto, Fazio con la mano sull'argano e Lauretta con la tavoletta dei conti. Se il giocatore entra negli Stradoni senza essere passato di qui, vale `BORGO_FUORI`: è l'errore di Ubaldo per dimenticanza.

- ANDREUCCIO: Settanta bocche fuori dalla porta, monsignore. Le facciamo entrare o no?
- LAURETTA: Ho fatto il conto. Con il borgo dentro, il grano dura un giorno in meno per tutti.
- FAZIO: L'argano l'ho fatto io. Si apre e si richiude in un fiato, ma va deciso adesso.
- GIORGIO (deciso): Restino fuori. Li difende la milizia, e al ritorno li difendo io.
- ANTONIO (calmo): Io ci ho vissuto vent'anni, fuori da una porta. Non lo consiglio.
- SCELTA: Apri al borgo / Tieni chiusa la porta

Se «Apri al borgo» (`BORGO_DENTRO`):

- UBALDO (deciso): Aprite. Nessuno resta fuori, stanotte. Il grano lo divideremo.
- ANDREUCCIO: Dentro, svelti! Lauretta, conta tu. Io resto fuori per ultimo.
- SISTEMA: Il borgo è dentro le mura. Il venditore delle Logge avrà meno da vendere.

Se «Tieni chiusa la porta» (`BORGO_FUORI`):

- UBALDO (preoccupato): Restate nel borgo. La milizia vi guarda, e Dio con lei.
- LAURETTA: Allora sette giorni di grano, dentro. E per noi, quello che c'è.
- ANTONIO (calmo): Sette giorni. Te li ricorderò, vescovo.

Regia: la porta si chiude. Da qui le battute degli NPC del borgo cambiano con la bandiera (vedi `05_npc_amici.md`).

---

## A1-06 · La porta del monte

| | |
| :-- | :-- |
| Luogo | Duomo e Palazzo Ducale, varco verso gli Stradoni |
| Condizione | `CITTA_IN_DIGIUNO` e non `PORTA_DEL_MONTE` |
| Imposta | `PORTA_DEL_MONTE` |

Regia: un canonico del Duomo sta sul varco. Il dialogo parte quando il giocatore lo tocca; dopo, il varco è libero.

- CANONICO: Monsignore, il capitolo pregherà con voi. Anche il palazzo del vescovo tace, stasera.
- CANONICO: Lassù il sentiero è lungo, e dicono che nei boschi ci siano occhi che non sono di Gubbio.
- UBALDO (calmo): Allora vuol dire che ci stanno guardando salire. Bene: che vedano.
- SISTEMA: Da qui la città non si vede più. Salva prima di partire.

---

## A1-07 · Gli Stradoni del Monte

| | |
| :-- | :-- |
| Luogo | Stradoni del Monte, i tornanti |
| Condizione | `PORTA_DEL_MONTE` |
| Imposta | `IMBOSCATA_STRADONI` dopo la battaglia, `SPIA_CATTURATA` alla fine |
| Battaglie | nemici visibili lungo il sentiero (falchi corrotti, spie umbre); una battaglia obbligata di imboscata |

### Ingresso (primo tornante)

Regia: prima delle battute, la presentazione del luogo: la cutscene C7S «Gli Stradoni del Monte» (`regia/c7s_stradoni.regia`), solo la prima volta.

- ANTONIO (calmo): Due chilometri di sterrato. E il vescovo ha le gambe di un mulo.
- UBALDO (calmo): E il mulo ti sente.
- GIORGIO (deciso): Così lassù ci arriviamo a notte, padre!
- UBALDO (calmo): Ci arriviamo quando ci arriviamo. Il monte non scappa.

### L'imboscata (a metà salita)

Regia: un'ombra attraversa il sentiero più avanti e sparisce dietro un masso.

- GIORGIO (deciso): Uno di loro! Lo prendo io!
- UBALDO (preoccupato): Giorgio, aspetta!

Regia: Giorgio corre avanti di qualche tile, dai cespugli escono altre spie. Battaglia obbligata (`IMBOSCATA_STRADONI`). Al termine:

- UBALDO (calmo): Chi corre avanti da solo, Giorgio, combatte da solo.
- GIORGIO (preoccupato): ...Ho capito, padre.
- ANTONIO (calmo): Non ha capito. Ma ha cominciato.

### La spia (sotto la vetta)

Regia: l'ultima spia è a terra, senza fiato, appoggiata a un tronco.

- SPIA: Ridete pure. Pregate, pregate sul vostro monte.
- SPIA: Mentre voi siete in ginocchio, qualcuno sta già bevendo la vostra acqua.
- GIORGIO (deciso): Cosa vuol dire? Parla!
- SPIA: Vuol dire che tre albe sono tante. Per voi, troppe.
- ANTONIO (calmo): Lascialo, ragazzo. Ha detto tutto quello che sa, e anche un po' di più.
- UBALDO (preoccupato): Lo legheremo e lo porteremo su. Nessuno muore sul mio monte, nemmeno lui.
- OBIETTIVO: Raggiungi la Basilica in vetta.

> Nemici. Falchi corrotti e spie umbre vengono dalla Sez. 7 Scena 2 del GDD; in `enemy_data.h` oggi non esistono. Vanno aggiunti in F6 o sostituiti da Fanti di Perugia con un nome diverso.

---

## A1-08 · Il rito dei tre giorni

| | |
| :-- | :-- |
| Luogo | Basilica di Sant'Ubaldo, interno |
| Condizione | `SPIA_CATTURATA` |
| Imposta | `CERI_RISVEGLIATI`, poi `SPETTRI_VINTI` |
| Battaglia | Spettri del Dubbio (boss tutorial), non si fugge |

### Arrivo

Regia: la navata è buia. In fondo, la vetrata grande con i vetri ancora chiari. È la stessa del prologo.

- ANTONIO (calmo): Vetri chiari. Nessun santo, nessun drago. Chi l'ha fatta, si è dimenticato di dipingerla?
- UBALDO (calmo): I vetrai lasciano chiaro il vetro dove la storia non è ancora scritta.
- GIORGIO (preoccupato): E chi la scrive?
- UBALDO (calmo): Chi resta in piedi, Giorgio.

### Il digiuno (passano due notti)

Regia: dissolvenze. Tre ceri spenti sull'altare. Etichette «Prima notte», «Seconda notte». Fuori, il vento.

- AREA: Prima notte.
- GIORGIO (preoccupato): Padre... da quassù si vedono i loro fuochi. Cosa possono tre uomini contro undici eserciti?
- ANTONIO (calmo): La fiamma più piccola consuma la foresta più fitta, ragazzo. Stringi quella lancia e taci.
- AREA: Seconda notte.
- UBALDO (calmo): Signore, non ti chiedo di vincere per noi. Ti chiedo di non farci cedere.

### Il risveglio dei Ceri (cinematica 2, Sez. 34B)

Regia: tre pilastri di legno e luce si alzano dall'altare, ruotano e si ergono. Sul primo brilla una mitra, sul secondo un elmo e una lancia, sul terzo una fiamma. I tre non hanno colori propri: sono legno e luce. Una brocca di maiolica cade dall'altare e si spezza: i cocci brillano. È la cutscene C5 «Il risveglio dei Ceri» (`regia/c5_risveglio_ceri.regia`): la riga del narratore la dice nelle bande, e nella vista di gioco non si ripete.

- NARRATORE: E il legno si fece luce.
- SISTEMA: Il Cero della mitra si accende sopra Ubaldo. La sua verga risplende.
- SISTEMA: Il Cero dell'elmo si accende sopra Giorgio. La sua lancia diventa d'oro.
- SISTEMA: Il Cero della fiamma si accende sopra Antonio. Il suo fuoco si alza fino alle volte.
- GIORGIO (preoccupato): Padre... cos'è questo peso? Non è l'armatura.
- UBALDO (calmo): È la città, Giorgio. Adesso la porti anche tu.
- SISTEMA: Nuove abilità: Giudizio della Verga, Bastione Azzurro, Fuoco di Sant'Antonio.

> Decisione di Cioti (1 novembre 2026). Colori delle camicie (giallo, azzurro, nero), fazzoletti rossi e corporazioni (muratori, merciai, contadini) sono della Festa dei Ceri di oggi e dei ceraioli, non dei personaggi: nel copione non compaiono. I tre si riconoscono dagli attributi: Ubaldo dalla mitra e dalla verga, Giorgio da armatura e lancia, Antonio dal saio e dal fuoco.

### Gli Spettri del Dubbio

Regia: i ceri tremano. Dalle ombre delle colonne escono tre figure senza volto. Ognuna parla a uno dei tre.

- SPETTRO: Nessuno canterà il tuo nome, cavaliere. Morirai su un sentiero, senza gloria.
- SPETTRO: Li salvi, eremita, e domani ti chiuderanno di nuovo la porta.
- SPETTRO: Hai ordinato la fame a una città intera. Quanti bambini piangono stanotte, vescovo?

Regia: battaglia contro gli Spettri del Dubbio. Battute di tutorial al primo turno utile:

- SISTEMA: Proteggersi a vicenda dà Fervore. Con Bastione Azzurro Giorgio para per gli altri.
- SISTEMA: Gli Spettri temono la Fede: usa Giudizio della Verga.

Dopo la vittoria, ognuno risponde al proprio spettro mentre svanisce:

- GIORGIO (deciso): Non mi serve che cantino il mio nome. Mi basta che domani cantino.
- ANTONIO (calmo): Forse la chiuderanno. Ma stanotte è aperta, e io sono dentro.
- UBALDO (preoccupato): Piangono, sì. E io piango con loro.
- UBALDO (deciso): Ma non piangeranno in catene.

---

## A1-09 · La visione del Bottaccione

| | |
| :-- | :-- |
| Luogo | Basilica, davanti alla vetrata |
| Condizione | `SPETTRI_VINTI` |
| Imposta | `VISIONE_BOTTACCIONE`, varco verso la Strada del Bottaccione aperto |

Regia: prima del vetro, gli indizi. Se il giocatore ha almeno due bandiere fra `INDIZIO_CARTA` (Bubo), `INDIZIO_ACQUA` (Giordano) e `INDIZIO_ROCCIA` (Giambono), parte questo scambio; altrimenti si passa subito alla visione.

Se almeno due indizi:

- UBALDO (preoccupato): Quello che ci hanno detto in città... tutte le voci portano all'acqua.
- ANTONIO (deciso): E la spia che rideva della nostra acqua. È il condotto, Ubaldo.
- UBALDO (calmo): Allora il vetro ci dirà soltanto quando.

Regia: uno dei vetri chiari si scurisce e mostra un'immagine che si muove: uomini in ferro salgono una gola stretta dietro il monte, verso gli archi di un acquedotto. Uno di loro, enorme, porta un martello. È la cutscene C6 «La visione nel vetro» (`regia/c6_visione_vetro.regia`), muta; le battute dopo, senza bande.

- UBALDO (preoccupato): Il Bottaccione... Salgono dalla gola, dietro il monte.
- ANTONIO (preoccupato): Vogliono il condotto. Se lo tagliano, la città beve fango in due giorni.
- ANTONIO (deciso): E se arrivano a Porta Metauro, la aprono da dentro. Altro che tre albe.
- GIORGIO (deciso): Allora scendiamo. Adesso.
- UBALDO (calmo): Adesso. Ma insieme, Giorgio.
- GIORGIO (calmo): Insieme.
- UBALDO (calmo): Il digiuno non finisce perché scendiamo. Lo portiamo con noi.
- SISTEMA: La spia resta legata in sacrestia. Puoi salvare davanti all'altare.
- OBIETTIVO: Scendi per la Strada del Bottaccione, dietro il monte.

> Nota v2. Decisione n. 3 del README riaperta e approvata da Cioti (3 nov 2026): per chi indaga in città la vetrata conferma il piano invece di rivelarlo; per chi non indaga funziona come prima.
