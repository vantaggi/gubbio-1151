# Gli amici di Cioti: NPC e luoghi di lavoro nel 1151

Parte della [Bibbia della storia v2](BIBBIA_STORIA.md), sezione 5.14. Versione del 3 novembre 2026.

## Nomi nel gioco (richiesta di Cioti, 3 nov sera)

I nomi si cambiano un po', in forme d'epoca, perché li riconosca solo chi sa. **Nei file le schede tengono il soprannome come etichetta di lavoro; nelle battute e nel gioco vale la colonna «Nel gioco».** Questo sostituisce la regola «soprannome tale e quale» del prompt, e alleggerisce il problema del consenso.

| Soprannome | Nel gioco | Perché |
| :-- | :-- | :-- |
| Ciacci | Ciaccio | stesso suono, forma toscana d'epoca |
| Cioti | Ciotto | nome antico vero (Ciotto) |
| Fagia | Fazio | nome medievale, stessa iniziale e ritmo |
| Febbo | Febo | il nome classico da cui pare venire |
| Fino | Mastro Rufino | Rufino contiene Fino |
| Flavio | Flaviano | nome d'epoca dalla stessa radice |
| Giamma | Giambono | nome medievale, comincia uguale |
| Cumpà | Compagno | nome medievale vero, e vuol dire la stessa cosa |
| Massi | Masio il Romano | Masio, diminutivo medievale |
| Endriu | Andreuccio | Andrea alla medievale (Boccaccio) |
| Giordy | Giordano | il nome intero |
| Gabrielone | Gabrione | Gabrio più l'accrescitivo, per l'altezza |
| Bubu | Bubo | quasi uguale; in latino è il gufo, giusto per chi custodisce le carte di notte |
| Ragno | Ragnetto | il più forzuto del borgo col nome più piccolo: lo capisce chi lo conosce |
| Ricca | Ricciardo | Riccardo alla medievale (Boccaccio) |
| Giulia | Giuliana | |
| Laura | Lauretta | |
| Aurora | Aurelia | |
| Valeria | Valeriana | anche un'erba: buffo per una guardia |
| Eleonora | Leonora | |
| Valentina | Valenza | |
| Nicolò | Nicoluccio | |
| Padeletto | Padellino | |

Nota: i nomi degli amici sono al maschile e quelli delle compagne al femminile solo perché seguono i nomi che hai dato; se per qualcuno serve un nome diverso, si cambia solo una riga di questa tabella.

## Regole usate

- **Nomi**: vedi la tabella «Nomi nel gioco» qui sopra (cambiata il 3 nov sera su richiesta di Cioti).
- **Rispetto** (regola di default, Cioti non l'ha ancora confermata): nessun amico è traditore, vigliacco o zimbello, nessuno muore in scena. Possono sbagliare, avere paura, stare con chi vuole trattare o con chi vuole uscire a combattere.
- **Genere e figura: da confermare con Cioti.** Non ho dato per scontato il genere di nessuno. Le figure sotto partono dalle 5 che il gioco ha già (popolana, frate, soldato, mercante, anziano) più un accessorio; se per qualcuno serve una figura femminile o maschile diversa, si cambia solo la figura. Nelle battute evito aggettivi che obblighino a un genere; i nomi dei mestieri (maestro, cavatore, medico...) sono al maschile grammaticale solo come segnaposto.
- **Mestiere del 1151.** Niente orologi meccanici, polvere da sparo, occhiali, stampa. Le licenze sono dichiarate nella scheda.
- **Battute** in 2 righe da 224 px (circa 70 caratteri), accenti veri, niente apostrofi al posto degli accenti.
- **Sant'Agostino è fuori Porta Romana.** Gli amici del borgo (Cioti, Fagia, Bubu, Ragno, Endriu, Laura, Nicolò, Valeria) cambiano posto con il dilemma D1: con `BORGO_DENTRO` nelle fasi DIGIUNO e NOTTE stanno accampati in Sant'Andrea, dietro la porta; con `BORGO_FUORI` restano nel borgo.

## Chi ha un ruolo di trama nella v1

Dieci su quindici (il minimo era sei):

| Amico | Ruolo nella v1 | Aggancio |
| :-- | :-- | :-- |
| Bubu | indizio `INDIZIO_CARTA` (S2): manca il disegno del condotto | A1-09 |
| Giordy | indizio `INDIZIO_ACQUA` (S13); terzo indizio di Q-SP01 al posto del mendicante | A1-09, Q-SP01 |
| Giamma | indizio `INDIZIO_ROCCIA` (S13): la pietra nera non regge | A1-09, B-01 |
| Endriu | apre il dilemma D1 alla porta | A1-05 |
| Gabrielone | riconosce il veratro (S4) in Q-SA01; ritratto del canonico (S3) | Q-SA01 |
| Ricca | sente l'eugubino del soldato (S1) in B-03 se il gruppo ha parlato con Ricca; tace sulla lettera di Guido (S11); sa della Rosa (S12) | B-03, D2, Q-SP01 |
| Ciacci | voce del partito della sortita; il torto delle terre (S6); paga il costo di D4 | A1-01, D4 |
| Cumpà | ricorda il 1140 (S1); conta i giorni di Monaldo (S7) | A1-05 |
| Fino | smonta il Patto del Grifo (S5): uno scudo in meno a Corrado | B-04 |
| Flavio | la canzone del 1140 (S1) | B-04 |

NPC d'ambiente con un tratto: Cioti, Fagia, Febbo, Massi, Ragno (Massi e Ragno portano comunque un indizio degli Atti II-III).

---

## Le quindici schede

### Ciacci

| | |
| :-- | :-- |
| Mestiere nel 1151 | possidente con vigne e campi nella piana, arciere della milizia |
| Area e luogo | San Martino, sulle mura sopra la postierla di Cecco (riuso delle mura) |
| Sullo schermo | figura soldato con **l'arco lungo** in spalla |
| Come parla | poche parole, con decisione; guarda sempre verso la piana |
| Vuole | una sortita subito: i perugini gli bruciano il raccolto |
| Sa | che metà delle sue terre la famiglia l'ha avuta dopo la guerra di confine (S6) |
| Entra in | San Martino; tenta Giorgio; paga il costo di D4 |

- ULTIMATUM: CIACCIO: Vedi quel fumo? È la mia vigna. Dammi dieci archi e ci vado.
- DIGIUNO: CIACCIO: Mio nonno quelle terre le ha prese con la spada. Ora le perdo pregando.
- NOTTE (con `GIUSTIZIA_OFFERTA`): CIACCIO: Giustizia agli esuli? E a me chi la rende, monsignore?
- NOTTE: CIACCIO: Ho tirato tutta la notte. Domani si esce, vero, cavaliere?

### Cioti

| | |
| :-- | :-- |
| Mestiere nel 1151 | maestro dei conti col tavoliere e le pedine, e giocatore di tavola reale e di filetto. Cameo del creatore del gioco |
| Area e luogo | Sant'Agostino, **bottega dei conti e dei congegni** con Fagia (nuovo edificio 4) |
| Sullo schermo | figura mercante con **il tavoliere a scacchi sotto il braccio** |
| Come parla | con allegria, pensa a mosse, trasforma tutto in un gioco |
| Vuole | che qualcuno giochi con lui, assedio o no; e non perdere la bottega |
| Sa | come si contano uomini e cavalli: fa i conti con Cumpà (S7, Atto III) |
| Entra in | Sant'Agostino; D1 |

Licenza: il tavoliere con le pedine («abaco a gettoni») e i giochi di tavola esistono nel XII secolo (Wikipedia, Abacus e Tables); il «maestro d'abaco» come mestiere è del Duecento, quindi qui è «maestro dei conti».

- ULTIMATUM: CIOTTO: Undici contro uno? In tre mosse la vinco, se le pedine stanno ferme.
- DIGIUNO: CIOTTO: Niente pane, niente vino. Una partita a filetto, almeno?
- NOTTE (`BORGO_DENTRO`): CIOTTO: Ho salvato il tavoliere. Le pedine no: le ha mangiate un mulo.
- NOTTE (`BORGO_FUORI`): CIOTTO: La bottega l'hanno rovesciata. Il tavoliere l'avevo sotto il mantello.

### Fagia

| | |
| :-- | :-- |
| Mestiere nel 1151 | maestro di congegni: serrature, argani, carrucole |
| Area e luogo | Sant'Agostino, retro della bottega con Cioti (nuovo edificio 4) |
| Sullo schermo | figura mercante con **una grande chiave di ferro** alla cintura |
| Come parla | con precisione, spiega come funzionano le cose, parla per «se... allora» |
| Vuole | che l'argano di Porta Romana regga: l'ha fatto lui |
| Sa | che la porta si apre e si richiude in un fiato (rende possibile D1) |
| Entra in | D1, con Endriu |

- ULTIMATUM: FAZIO: Se tirate questa leva, la porta scende. Se non la tirate, no. Facile.
- DIGIUNO: FAZIO: La porta si apre e si richiude in un fiato. L'argano l'ho fatto io.
- NOTTE: FAZIO: Ho unto i cardini. Se domani si apre, almeno non cigola.

### Febbo

| | |
| :-- | :-- |
| Mestiere nel 1151 | costruttore di congegni e tamburino della milizia, aiuta i campanari di San Pietro |
| Area e luogo | San Pietro, ai piedi del campanile dell'abbazia (riuso) |
| Sullo schermo | figura soldato con **il tamburo al fianco** |
| Come parla | a ritmo, batte le dita su tutto; riconosce i tamburi nemici |
| Vuole | suonare, e che le campane non tacciano per sempre |
| Sa | leggere i tamburi: «quel ritmo è di Foligno» (presagi dei fronti) |
| Entra in | San Pietro; in E-01 risponde al Campanone dal campanile (regia) |

- ULTIMATUM: FEBO: Senti i tamburi? Tre colpi e una pausa: sono di Foligno.
- DIGIUNO: FEBO: Campane mute per tre giorni. Le dita mi tremano da sole.
- NOTTE: FEBO: All'alba, se il Campanone chiama, San Pietro risponde. Parola.

### Fino

| | |
| :-- | :-- |
| Mestiere nel 1151 | mastro carpentiere di mulini, argani e ruote |
| Area e luogo | Piazza Quaranta Martiri, **mulino sul Camignano coperto** (nuovo edificio 2) |
| Sullo schermo | figura mercante con **l'ascia da carpentiere** |
| Come parla | da persona pratica, diffida dei miracoli, crede alle leve |
| Vuole | che la ruota del mulino giri ancora, acqua permettendo |
| Sa | che nessuna corazza è stregata: il ferro piegato a strati regge le lame (S5) |
| Entra in | indizio per Corrado: una battuta toglie a Corrado uno scudo (5.12) |

Nelle battute degli altri si chiama «Mastro Rufino».

- ULTIMATUM: RUFINO: Un trabucco? Datemi tre giorni e travi buone, e ve ne faccio due.
- DIGIUNO: RUFINO: Nessun ferro è stregato, è solo piegato bene. Si apre col calore.
- NOTTE: RUFINO: La ruota ha ripreso a girare. L'acqua è tornata: qualcuno ha lavorato.

### Flavio

| | |
| :-- | :-- |
| Mestiere nel 1151 | cantore con la viella: porta le notizie in rima |
| Area e luogo | San Martino, sul Ponte di San Martino (riuso) |
| Sullo schermo | figura mercante con **la viella** |
| Come parla | in rima quando può, con malinconia quando la rima non viene |
| Vuole | tenere su la gente; una canzone nuova da cantare alla fine |
| Sa | la canzone della cacciata dei Valmarcola, che nessuno vuole più sentire (S1) |
| Entra in | San Martino; S1 |

Licenza: le fonti lette danno la viella dal Duecento (Wikipedia, Vielle); strumenti ad arco simili esistono prima, e la tengo come licenza di gioco.

- ULTIMATUM: FLAVIANO: Undici stendardi e un monte solo: la rima è facile, il finale no.
- DIGIUNO: FLAVIANO: C'è una canzone di dieci anni fa, sui Valmarcola. Non la canto più.
- NOTTE: FLAVIANO: Tre luci sul monte. Ecco la canzone nuova. Manca solo l'alba.

### Giamma

| | |
| :-- | :-- |
| Mestiere nel 1151 | cavatore che legge la roccia, balestriere della milizia |
| Area e luogo | San Pietro, sulle mura verso la piana (riuso) |
| Sullo schermo | figura soldato con **la balestra** |
| Come parla | frasi asciutte, confronta tutto con le pietre; sfida Cecco di San Martino |
| Vuole | tirare meglio di Cecco |
| Sa | che la striscia nera del Bottaccione si sbriciola (S13) |
| Entra in | indizio `INDIZIO_ROCCIA`; B-01 |

Fatto storico: il secondo concilio lateranense (1139, canone 29) vietò archi e balestre contro i cristiani. Fra' Bernardo glielo ricorda, una volta.

- ULTIMATUM: GIAMBONO: Cecco dice che tira meglio lui. Cecco dice tante cose.
- DIGIUNO: GIAMBONO: La pietra nera della gola si sbriciola come pane secco. Lì scava chiunque.
- NOTTE: GIAMBONO: Il frate dice che il concilio vieta la balestra. Tiro ai perugini, pregano male.

### Cumpà

| | |
| :-- | :-- |
| Mestiere nel 1151 | medico, studioso degli assedi antichi, li rifà sul tavolo con i sassolini |
| Area e luogo | San Martino, **casa del medico** (nuovo edificio 1) |
| Sullo schermo | figura anziano con **la borsa del medico**, senza barba bianca |
| Come parla | con calma, cita battaglie antiche, ragiona in numeri come Guido ma senza ansia |
| Vuole | che si tratti: sa come finiscono gli assedi lunghi (sta con il partito della trattativa) |
| Sa | cosa successe nel 1140 (S1); che un esercito così mangia la piana in due settimane (S7) |
| Entra in | San Martino; S1, S7 |

- ULTIMATUM: COMPAGNO: Cento assedi ho studiato. Novanta finiscono con la fame, gli altri peggio.
- DIGIUNO: COMPAGNO: Nel 1140 cacciammo i Valmarcola. Chi è cacciato prima o poi torna.
- NOTTE: COMPAGNO: Undici eserciti mangiano la piana in due settimane. Monaldo ha fretta.

### Massi

| | |
| :-- | :-- |
| Mestiere nel 1151 | gabelliere romano: riscuote il pedaggio per un mercante di Roma, bloccato in città dall'assedio |
| Area e luogo | San Martino, casotto del pedaggio accanto a Porta Metauro, con Nello (riuso della porta) |
| Sullo schermo | figura mercante con **la fascia di lana gialla e rossa** |
| Come parla | tutto a Roma è meglio; un filo di romanesco; scherza col vescovo ma sul papa tace |
| Vuole | tornare a Roma; nel frattempo, che qualcuno ammetta che Roma è la più bella |
| Sa | del pedaggio della Flaminia (S8); le notizie da Roma e dal re di Germania (S7) |
| Entra in | San Martino; S6 come voce di fuori |

Fatto storico: nel 1151 Roma ha il suo Senato (dal 1143-44) e papa Eugenio III vive fuori città (Viterbo, Tivoli); Arnaldo da Brescia predica in città. Licenza: i colori giallo e rosso di Roma sono più tardi.

- ULTIMATUM: MASIO: A Roma 'sto grifo lo famo arrosto. Co' le patate no, che non ci stanno.
- DIGIUNO: MASIO: Da fuori, Gubbio è quella che s'allarga. Da dentro, ve lo giuro, è più carina.
- NOTTE: MASIO: Gualdo e Nocera vogliono solo er pedaggio. Gli fate lo sconto e tornano a casa.

Nota: «patate» è un anacronismo apposta, e la battuta lo dice. Se non piace si toglie (da rivedere dopo la prova).

### Endriu

| | |
| :-- | :-- |
| Mestiere nel 1151 | miliziano della guardia di Porta Romana |
| Area e luogo | Sant'Agostino, fuori Porta Romana, davanti a casa sua (riuso della porta) |
| Sullo schermo | figura soldato con **lo scudo col monte bianco** |
| Come parla | da soldato, dritto al punto, ma parla della sua strada come di una famiglia |
| Vuole | che il borgo entri, o di restare fuori a difenderlo |
| Sa | quante famiglie ci sono nel borgo: settanta bocche |
| Entra in | **apre D1** |

- ULTIMATUM: ANDREUCCIO: Le mura qui sono basse. Il borgo è ancora più basso, monsignore.
- DIGIUNO (D1): ANDREUCCIO: Settanta bocche fuori dalla porta. Le facciamo entrare o no?
- NOTTE (`BORGO_DENTRO`): ANDREUCCIO: Dormono tutti dentro. Io resto fuori: la mia porta è questa.
- NOTTE (`BORGO_FUORI`): ANDREUCCIO: Hanno bruciato tre case. Ne abbiamo salvate dieci. Ho contato.

### Giordy

| | |
| :-- | :-- |
| Mestiere nel 1151 | fontaniere: cerca le vene d'acqua, cura le fontane e il condotto in città |
| Area e luogo | Piazza Quaranta Martiri, alla vasca dove sbocca l'acqua (oggetto, non edificio) |
| Sullo schermo | figura anziano con **il secchio e la corda**, senza barba bianca |
| Come parla | misura tutto in «spanne d'acqua», ascolta le fontane |
| Vuole | che l'acqua non si fermi |
| Sa | che di notte l'acqua alle fontane cala: qualcuno tocca il condotto (S13) |
| Entra in | indizio `INDIZIO_ACQUA`; terzo indizio di Q-SP01 al posto del mendicante; coppia con Giamma |

- ULTIMATUM: GIORDANO: Quest'acqua viene dal Bottaccione, tre miglia di pietra. Dolce come il latte.
- DIGIUNO: GIORDANO: Stanotte la vasca è calata di due spanne. Il condotto ha una ferita.
- NOTTE: GIORDANO: È tornata su. Tre spanne. Non so chi siate, ma vi offro da bere.

### Gabrielone

| | |
| :-- | :-- |
| Mestiere nel 1151 | speziale: erbe, unguenti, polveri; ritrae tutto a carboncino |
| Area e luogo | San Pietro, **spezieria** (nuovo edificio 3) |
| Sullo schermo | figura nuova **altissima** (una testa più delle altre), **testa pelata**, carboncino in mano |
| Come parla | con gentilezza e curiosità, chiede di stare fermi «un momento solo» per il ritratto |
| Vuole | fermare con il carboncino quello che vede, prima che sparisca |
| Sa | che il veleno è veratro (S4); ha ritratto un canonico che usciva di notte (S3) |
| Entra in | **Q-SA01**: fornisce ad Agnese e spiega il veleno; S3 per l'Atto II |

- ULTIMATUM: GABRIONE: Fermi un momento. Così. Vi ritraggo, che domani chissà.
- DIGIUNO: GABRIONE: Quest'acqua sa di veratro, l'elleboro bianco. Agnese lo sa curare.
- NOTTE: GABRIONE: Ho ritratto chi passava stanotte. Uno aveva l'abito da canonico.

### Bubu

| | |
| :-- | :-- |
| Mestiere nel 1151 | custode delle carte della pieve di Sant'Agostino, collezionista di giochi antichi (tavole da gioco romane trovate al Teatro) |
| Area e luogo | Sant'Agostino, la cella delle carte nella chiesa (riuso) |
| Sullo schermo | figura frate senza tonsura, con **un rotolo** |
| Come parla | con entusiasmo per le cose vecchie, si perde nei dettagli |
| Vuole | che le carte non brucino |
| Sa | che manca la copia del disegno dell'acquedotto, chiesta «dal capitolo» (S2, S3); ha visto il sigillo dei consoli su una lettera in uscita (S11) |
| Entra in | indizio `INDIZIO_CARTA` |

I «videogiochi retrò» diventano giochi romani: le tavole incise per giocare (tabulae lusoriae) che si trovano nei teatri antichi. Licenza: nessuna fonte su tavole trovate a Gubbio.

- ULTIMATUM: BUBO: Guarda: un gioco inciso dai romani. Mille anni e ancora si gioca.
- DIGIUNO: BUBO: Manca il disegno dell'acquedotto. L'aveva chiesto il capitolo, e non torna.
- NOTTE: BUBO: Le carte le ho salvate tutte. Una sola manca, e lo sapete già quale.

### Ragno

| | |
| :-- | :-- |
| Mestiere nel 1151 | lavorante della calcara del borgo: cuoce la calce per le mura, il più forzuto di Sant'Agostino |
| Area e luogo | Sant'Agostino, **la calcara** (nuovo edificio 5) |
| Sullo schermo | figura soldato senza elmo, **braccia nude e una trave in spalla** |
| Come parla | con bonarietà, fa le cose prima di dirle |
| Vuole | alzare le mura basse del borgo prima dell'assalto |
| Sa | la storia del fuoco del borgo, raccontata dalla nonna (S10); quella di Ubaldo spinto nella calce da un capomastro e perdonato |
| Entra in | Sant'Agostino; S10 seminato |

Fatto storico: secondo la vita di Ubaldo, un capomastro che riparava le mura lo spinse in un mucchio di calce, e Ubaldo lo perdonò (Wikipedia, Ubald).

- ULTIMATUM: RAGNETTO: Datemi un'ora e questa trave sta sulle mura. Due, se ci metto la calce.
- DIGIUNO: RAGNETTO: Mia nonna diceva che il fuoco del borgo fu un male che salvò. Non so cosa vuol dire.
- NOTTE: RAGNETTO: Il vescovo nella calce, una volta. E ha perdonato. Io non ci riuscirei.

### Ricca

| | |
| :-- | :-- |
| Mestiere nel 1151 | interprete dell'abate di San Pietro: dialetti delle undici città, latino dei chierici, lingua dei mercanti |
| Area e luogo | San Pietro, nel chiostro dell'abbazia, accanto a Fra' Bernardo (riuso) |
| Sullo schermo | figura mercante con **la tavoletta di cera e lo stilo** |
| Come parla | con misura, sceglie le parole con cura; tace su quello che traduce per altri |
| Vuole | che l'abate tratti la pace (Biscarini: forse fu l'abate di San Pietro a trattare) |
| Sa | la lettera di Guido (S11, tace); che la Rosa fu un dono di Perugia (S12); i dialetti (S1, S8) |
| Entra in | Q-SP01; se il gruppo ha parlato con Ricca, in B-03 Ubaldo riconosce l'accento eugubino (S1) |

- ULTIMATUM: RICCIARDO: Ho tradotto molte lettere oggi. Di quali, monsignore, non chiedetemelo.
- DIGIUNO: RICCIARDO: I soldati di Gualdo cantano che il soldo non arriva. In tre dialetti.
- NOTTE: RICCIARDO: La Rosa la donò Perugia, in un anno di pace. L'abate se lo ricorda.

---

## Le compagne e la famiglia (aggiunte da Cioti, 3 nov sera)

Sei NPC nuovi, più Nicolò. Stanno nella stessa area del compagno e quasi sempre nello stesso luogo di lavoro, così **nessun edificio nuovo** (si resta a 5 su 8). Figura di partenza: la popolana più un accessorio. Due di loro portano un indizio nuovo, tre toccano un dilemma.

| NPC | Compagno | Mestiere nel 1151 | Area e luogo | Sullo schermo | Ruolo nella v1 |
| :-- | :-- | :-- | :-- | :-- | :-- |
| **Giulia** | moglie di Ciacci | maestra di canto dei fanciulli, suona il salterio | San Martino, sulla soglia della chiesa (riuso) | popolana con **il salterio** | frena Ciacci sulla sortita; canta con Flavio; voce del costo di D4 |
| **Laura** | moglie di Fagia, madre di Nicolò | maestra dei numeri: insegna a contare ai ragazzi del borgo e tiene i conti della pieve | Sant'Agostino, nella bottega di famiglia (nuovo edificio 4, condiviso) | popolana con **la tavoletta dei conti** | dà a D1 il suo costo esatto: con il borgo dentro il grano dura un giorno in meno |
| **Aurora** | fidanzata di Giamma | maestra dei fanciulli alla scuola dell'abbazia | San Pietro, nel chiostro (riuso) | popolana con **un libro sotto il braccio** | porta i bambini dentro l'abbazia; prende in giro la sfida fra Giamma e Cecco |
| **Valeria** | fidanzata di Bubu | guardia di ronda del borgo: fa rispettare i bandi dei consoli | Sant'Agostino, sulla strada verso Porta Romana (riuso) | popolana con **la lanterna e il bastone** | fa rispettare il digiuno nel borgo; **indizio nuovo di S3**: di notte ha visto un uomo in abito da canonico prendere la strada di San Girolamo verso il monte |
| **Eleonora** | fidanzata di Febbo | tiene il ruolo dei turni di guardia della milizia di San Pietro | San Pietro, alla torre della porta (riuso delle mura) | popolana con **il rotolo dei turni** | **indizio nuovo per Q-SP01**: un «pellegrino» si era fatto mettere nei turni e non si è mai presentato |
| **Valentina** | moglie di Gabrielone | tiene l'ospizio dei poveri e dei matti accanto alla spezieria | San Pietro, nella spezieria (nuovo edificio 3, condiviso) | popolana con **il grembiule e la ciotola** | dentro D3: distribuisce il pane dei poveri; conosce Tano e i «matti» della fontana |
| **Nicolò** | figlio di Laura e Fagia | bambino del borgo | Sant'Agostino, con Laura | figura nuova **bambino** | una battuta per fase, solo d'ambiente; nessun pericolo in scena |

Licenze: nel XII secolo le donne insegnano e curano poveri e malati, ma una donna di ronda o che tiene i ruoli della milizia è una scelta di gioco (Valeria, Eleonora), come i quartieri. Il salterio è uno strumento a corde del XII secolo, il più vicino al pianoforte di Giulia.

Regola di rispetto applicata anche qui. Per Nicolò, che è un bambino vero, nessuna scena di pericolo e nessuna battuta sui grandi; il consenso va chiesto ai genitori.

### Battute per fase

- ULTIMATUM: GIULIANA: Ciaccio vuole uscire con dieci archi. Io gli ho nascosto le frecce.
- DIGIUNO: GIULIANA: I bambini cantano piano, come ha chiesto il vescovo. Piano, ma cantano.
- NOTTE (con `GIUSTIZIA_OFFERTA`): GIULIANA: Ciaccio è arrabbiato. Io no: le terre si riprendono, le persone no.
- NOTTE: GIULIANA: Flaviano ha la canzone nuova. Io le ho trovato le note. Domani la sentirete.

- ULTIMATUM: LAURETTA: Settanta bocche nel borgo. Con il grano dei consoli, un giorno in meno per tutti.
- DIGIUNO (D1): LAURETTA: Ho rifatto il conto tre volte. Dentro: sei giorni di grano. Fuori: sette, e il borgo.
- NOTTE: LAURETTA: Nicoluccio dorme sulle pedine di Ciotto. Le ha contate tutte prima di chiudere gli occhi.

- ULTIMATUM: AURELIA: Giambono dice che tira meglio di Cecco. Io dico che parlano meglio di come tirano.
- DIGIUNO: AURELIA: I bambini sono nel chiostro. Imparano le lettere, così non sentono i tamburi.
- NOTTE: AURELIA: Ho insegnato una parola nuova: «alba». La scrivono tutti, storta ma la scrivono.

- ULTIMATUM: VALERIANA: Bando dei consoli: chi ha un carro lo porta a Porta Romana. Subito.
- DIGIUNO: VALERIANA: Botteghe chiuse anche nel borgo. Bubo, quel rotolo lo leggi domani.
- NOTTE: VALERIANA: Stanotte un canonico ha preso la strada di San Girolamo. Verso il monte, da solo.

- ULTIMATUM: LEONORA: Febo al tamburo, Giambono sulle mura, gli altri a turno. Il ruolo è fatto.
- DIGIUNO: LEONORA: Un pellegrino si era messo nei turni di guardia. Mai visto alla torre. Strano.
- NOTTE: LEONORA: Tutti al loro posto, stanotte. Anche quelli che avevano la febbre. Contati.

- ULTIMATUM: VALENZA: Tano dice che i matti veri stanno fuori le mura. Qui ci sono solo i miei.
- DIGIUNO (D3): VALENZA: Il pane dei poveri basta per oggi. Domani lo dividiamo per due.
- NOTTE (con `PANE_DATO`): VALENZA: La popolana mi ha portato mezza crescia per gli altri. Viene da voi?
- NOTTE: VALENZA: Gabrione ha ritratto anche me, stanotte. Dice che ho la faccia dell'alba.

- ULTIMATUM: NICOLUCCIO: Mamma dice che undici è più di dieci. Io lo sapevo già.
- DIGIUNO: NICOLUCCIO: Ciotto mi ha insegnato il filetto. Gli ho vinto tre volte. Quasi.
- NOTTE: NICOLUCCIO: Ho visto tre luci sul monte. Le ho contate: sono tre.

## Padeletto, l'oste del corso (aggiunto da Cioti, 3 nov sera)

Barista che a Gubbio conoscono tutti, sul corso. Nel gioco la sua taverna sta sulla strada fra San Pietro e Sant'Andrea, cioè dove oggi corre corso Garibaldi (MAPPA.md, arco San Pietro → Sant'Andrea).

| | |
| :-- | :-- |
| Mestiere nel 1151 | oste: vino, crescia, e tutte le voci della città |
| Area e luogo | San Pietro, all'uscita verso Sant'Andrea: **la taverna del corso** (nuovo edificio 6, si resta sotto gli 8) |
| Sullo schermo | figura mercante con **il fiasco e il grembiule** |
| Come parla | saluta tutti per nome, sa tutto di tutti, non giudica nessuno |
| Vuole | riaprire la taverna; che la città torni a passare dal corso |
| Ruolo nella v1 | **le voci della città**: durante il digiuno la taverna è chiusa ma Padeletto è sulla soglia, e dice al giocatore quale indizio gli manca ancora («Dicono che il fontaniere ha visto una cosa strana...»). È un aiuto facoltativo, una battuta per indizio mancante, scelta dalle bandiere |
| Rispetto | è una persona reale e conosciuta: battute affettuose, nessuna presa in giro; consenso da chiedere come per gli amici |

- ULTIMATUM: PADELLINO: Monsignore! Il solito? Ah no, oggi niente vino. Allora il solito di domani.
- DIGIUNO: PADELLINO: Taverna chiusa, voci aperte. Dicono che al Bottaccione l'acqua parla strano.
- DIGIUNO (aiuto, se manca `INDIZIO_CARTA`): PADELLINO: Bubo cercava una carta e non la trovava. Bubo non perde mai niente.
- DIGIUNO (aiuto, se manca `INDIZIO_ACQUA`): PADELLINO: Giordano stamattina guardava la vasca come si guarda un malato.
- DIGIUNO (aiuto, se manca `INDIZIO_ROCCIA`): PADELLINO: Giambono dice che certe pietre non reggono. Chiedetegli quali.
- NOTTE: PADELLINO: All'alba riapro. Il primo bicchiere lo offro io, chiunque vinca la piazza.

## Tabella area per area

Tutti gli NPC, vecchi e nuovi. «Nuovo» = edificio da disegnare (6 su un massimo di 8, con la taverna di Padeletto).

| Area | NPC del copione v1 | Amici | Luoghi di lavoro |
| :-- | :-- | :-- | :-- |
| Piazza Grande | Guido, Berto, popolana | — | — |
| Via dei Consoli | merciaio | — | — |
| Largo del Bargello | Tano | — | — |
| San Martino | Cecco, lavandaia, Raniero (Q-SM01), Nello (Porta Metauro) | Ciacci, Flavio, Cumpà, Massi, Giulia | mura (riuso), Ponte di San Martino (riuso), **casa del medico** (nuovo 1), casotto del pedaggio a Porta Metauro (riuso) |
| Teatro Romano | — | — | — |
| Piazza Quaranta Martiri | venditore delle Logge, Fra' Matteo, (mendicante di Q-SP01: sostituito da Giordy) | Fino, Giordy | **mulino** (nuovo 2), vasca del fontaniere (oggetto) |
| San Pietro | Lucia, Fra' Bernardo (Q-SP01) | Febbo, Giamma, Gabrielone, Ricca, Aurora, Eleonora, Valentina, Padeletto | campanile (riuso), mura (riuso), **spezieria e ospizio** (nuovo 3), chiostro (riuso), **taverna del corso** (nuovo 6) |
| Via XX Settembre | vecchio sulla scalinata | — | — |
| Sant'Andrea | sentinella di Porta Romana, Agnese (Q-SA01) | (con `BORGO_DENTRO`: Cioti, Fagia, Bubu, Ragno, Laura, Nicolò, Valeria accampati) | — |
| Sant'Agostino | frate agostiniano | Cioti, Fagia, Bubu, Ragno, Endriu, Laura, Nicolò, Valeria | **bottega dei conti e dei congegni** (nuovo 4), cella delle carte (riuso della chiesa), **calcara** (nuovo 5), Porta Romana (riuso) |
| Duomo e Ducale | canonico (Ilario) | — | — |
| Monte, Basilica, Bottaccione | spia, Guerrieri, Corrado | — | — |

Coppie con i PNG esistenti: Giamma **fa coppia e rivalità** con Cecco; Giamma e Giordy **affiancano** Berto (la roccia e l'acqua); Gabrielone **affianca** Agnese; Fino **affianca** Raniero (Raniero il ferro, Fino le macchine); Ricca e Febbo **affiancano** Fra' Bernardo; Massi **fa coppia** con Nello; Endriu **affianca** la sentinella di Porta Romana (lei dentro, Endriu fuori). **Una sola sostituzione**: Giordy prende il posto del mendicante come terzo indizio di Q-SP01 (GIALLO).

---

## Prove di qualità (punto 6 del prompt)

| # | Prova | Esito |
| :-- | :-- | :-- |
| 1 | Movente di ogni fronte in una frase, senza «malvagio», «invidia», «dominio» | **Passa.** Grifo: un padrone solo per le strade dei monti. Forge: il ferro e il soldo. Flaminia: il pedaggio. Nord: tornare a casa. (Ho controllato le quattro frasi in 5.2: le tre parole non ci sono) |
| 2 | Ogni segreto della v1 ha almeno 3 indizi in 3 posti | **Passa.** S1 (5 indizi), S2 (4), S4 (4), S5 (3), S6 (3), S9 (3), S12 (3), S13 (4). Il più debole è S5: Raniero sta in una quest facoltativa, Fino è facoltativo, B-04 è obbligato |
| 3 | Ogni colpo di scena ha almeno 2 semi prima | **Passa.** v1: 4 semi, due già nel copione. II: 4. III: 4. IV: 2 (Patto come giuramento, Spettri del Dubbio): è il più fragile, va rafforzato negli Atti II-III |
| 4 | Ogni dilemma ha due voci con un costo vero, nessuna premiata | **Passa con una riserva.** D1: grano contro saccheggio. D2: testimone contro messaggio. D3: un oggetto contro una battuta fredda: il costo di «tieni» è debole, da rivedere dopo la prova. D4: fiducia di San Martino contro il rimprovero di Antonio |
| 5 | Ogni personaggio con un arco ha una prova nella v1 | **Passa.** Ubaldo D1 e D4; Giorgio A1-07 e D2; Antonio A1-04 e D1; Guido D1 ed E-01. Rinaldo **no**: nella v1 non compare (lo dichiaro: il suo arco parte nell'Atto II) |
| 6 | Nessun BLOCCATO violato; licenze dichiarate | **Passa.** Niente Ceri fuori dalla Basilica, niente divise, stemmi invariati, Porta Metauro, Guido console, tre albe, Antonio al Teatro, Corrado vivo nel Camignano, un solo vetro, le 3 quest con consumabili. Licenze dichiarate: Valmarcola come nome della famiglia esule, viella, maestro dei conti, colori di Roma, pieve di Sant'Agostino, «patate» (voluto), tavole da gioco romane |
| 7 | Conto delle battute | vedi sotto |
| 8 | Continuità: ogni elemento nuovo ha un aggancio | **Passa.** Fronti → P-02, A1-01, Q-SM01, Q-SP01, B-04. Segreti → tabella 5.7, colonna indizi. Dilemmi → A1-05, B-03, NPC Piazza Grande, E-01. Amici → tabella sopra |
| 9 | Amici: 15 schede, almeno 6 con ruolo, rispetto, massimo 8 edifici | **Passa.** 15 schede, 10 con ruolo, nessun traditore o zimbello (Massi scherza ma ha ragione sul pedaggio; Ciacci è amaro ma leale), 6 edifici nuovi con la taverna di Padeletto; le sei compagne e Nicolò non ne aggiungono |
| 10 | Lettura avversaria | vedi sotto |

### Conto delle battute (prova 7)

| Voce | Battute |
| :-- | --: |
| Copione v1 oggi | 297 |
| Amici: 15 × 3 fasi, più 4 varianti per D1 e D4 | +49 |
| Dilemmi D1-D4 (proposta, scelta, conseguenze) | +22 |
| Indizi in A1-09 (Ubaldo collega gli indizi) | +3 |
| Rivelazione degli esuli in B-03 e B-04 | +4 |
| E-01 con l'offerta di giustizia | +4 |
| Battute nuove dell'araldo (A1-01) e di Q-SP01 | +3 |
| **Tagli proposti**: B-02 intero se i miasmi saltano (−3); tutorial di A1-04 e A1-08 da 6 a 3 righe SISTEMA (−3); merciaio da 3 a 1 fase (−2); Tano da 4 a 2 battute (−2); Fra' Matteo da 3 a 2 (−1); mendicante di Q-SP01 (−2, lo sostituisce Giordy) | −13 |
| Compagne e famiglia (aggiunte il 3 nov sera): 7 NPC × 3 fasi, più 2 varianti | +23 |
| Padeletto: 3 fasi più 3 aiuti | +6 |
| **Totale v2** | **~398** |

Il costo è di circa **100 battute in più** (+34%), contando le aggiunte del 3 nov sera (le compagne, Nicolò e Padeletto). Quasi tutto viene dagli amici (49). Se serve tornare verso 300, la leva è una sola: dare agli amici d'ambiente (Cioti, Fagia, Febbo, Massi, Ragno) 1 battuta invece di 3 (−10) e togliere la terza fase a Flavio, Fino e Cumpà (−3): si scende a ~356. Sotto non scenderei senza togliere amici, cosa che Cioti non vuole.

### Lettura avversaria (prova 10)

**Il giocatore annoiato.**

1. *«Quindici NPC nuovi da ascoltare? Non leggo.»* Risposta: nessuno è obbligato. Gli indizi servono solo a rendere più ricca A1-09: senza, la vetrata funziona come oggi.
2. *«I dilemmi sono finti, tanto il finale è lo stesso.»* Risposta: vero per il finale, ed è dichiarato. Cambiano chi ti parla male la notte, cosa hai nello zaino al Bottaccione, e la frase di Antonio all'alba. Per un gioco da GBA di un'ora è la misura giusta.
3. *«Ubaldo che non può mangiare mi complica le battaglie.»* Risposta: è voluto, ma è anche il punto più facile da tarare: se la prova dice che è frustrante, Ubaldo mangia solo nel Bottaccione.

**Lo storico pignolo.**

1. *«I Valmarcola esuli non sono documentati.»* Risposta: giusto. Le fonti dicono «nobili esuli» (Key to Umbria) e Piccotti mette i conti di Valmarcola fra gli alleati: ho unito le due cose e l'ho dichiarato come licenza.
2. *«Nel 1151 non c'erano i quartieri né Sant'Agostino.»* Risposta: già deciso nel censimento dei simboli e nel copione v1: i quartieri sono fazioni del gioco, e Sant'Agostino è un borgo.
3. *«Ubaldo offrì giustizia prima dell'assalto, non alla terza alba.»* Risposta: vero (Biscarini: le offerte vengono prima, poi le processioni). Lo sposto all'ultimo momento per farne una scelta del giocatore; la sostanza, offrire riparazione prima di benedire la resistenza, resta.

## Punti aperti per Cioti

1. **Regola di rispetto** (nessun amico traditore, vigliacco, zimbello o morto in scena): applicata come default, da confermare.
2. **Consenso degli amici** a comparire col soprannome in una ROM pubblica su itch.io: da chiedere a ognuno prima del rilascio. Se qualcuno dice di no, si cambia solo il nome del parlante. Vale anche per le sei compagne e per Padeletto; per Nicolò lo danno i genitori.
3. **Genere e figura** di ciascun amico: da confermare (vedi le regole in cima).
4. **Massi e la battuta delle patate**: anacronismo comico voluto, da tenere o togliere dopo la prova.
