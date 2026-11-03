# Gli amici di Cioti: battute d'ambiente

Copione v2, 3 novembre 2026. Fonte: `storia/NPC_AMICI.md` (Bibbia della storia v2). Stesso formato di [03_npc_ambiente.md](03_npc_ambiente.md): vince la prima riga che vale, dall'alto; una riga `(se BANDIERA)` sta sopra quella della stessa fase senza condizione.

**Nomi.** Nel gioco i nomi sono forme d'epoca dei soprannomi, riconoscibili solo a chi sa (tabella in `storia/NPC_AMICI.md`). **Genere e figura** li ho decisi io (Cioti, 3 nov 2026: «decidili tu»): gli amici sono uomini, le compagne donne, Nicoluccio un bambino. Sono modificabili: si cambia solo la figura o il nome.

**Sant'Agostino.** Con `BORGO_DENTRO` gli NPC del borgo, nelle fasi DIGIUNO e NOTTE, stanno accampati in Sant'Andrea dietro Porta Romana; con `BORGO_FUORI` (anche se il giocatore non è passato da A1-05b) restano nel borgo. Andreuccio resta sempre fuori, sulla soglia.

Regola di rispetto (approvata da Cioti): nessuno di loro è traditore, vigliacco o zimbello, nessuno muore in scena; Nicoluccio non è mai in pericolo.

---

## San Martino

**Ciaccio**, possidente e arciere. Luogo: sulle mura sopra la postierla. Figura: soldato con l'arco lungo.

- NOTTE (se GIUSTIZIA_OFFERTA): CIACCIO: Giustizia agli esuli? E a me chi la rende, monsignore?
- NOTTE: CIACCIO: Ho tirato tutta la notte. Domani si esce, vero, cavaliere?
- DIGIUNO: CIACCIO: Mio nonno quelle terre le ha prese con la spada. Ora le perdo pregando.
- ULTIMATUM: CIACCIO: Vedi quel fumo? È la mia vigna. Dammi dieci archi e ci vado.

**Giuliana**, maestra di canto, moglie di Ciaccio. Luogo: sulla soglia della chiesa di San Martino. Figura: popolana col salterio.

- NOTTE (se GIUSTIZIA_OFFERTA): GIULIANA: Ciaccio è arrabbiato. Io no: le terre si riprendono, le persone no.
- NOTTE: GIULIANA: Flaviano ha la canzone nuova. Io le ho trovato le note. Domani la sentirete.
- DIGIUNO: GIULIANA: I bambini cantano piano, come ha chiesto il vescovo. Piano, ma cantano.
- ULTIMATUM: GIULIANA: Ciaccio vuole uscire con dieci archi. Io gli ho nascosto le frecce.

**Flaviano**, cantore con la viella. Luogo: sul Ponte di San Martino. Figura: mercante con la viella.

- NOTTE: FLAVIANO: Tre luci sul monte. Ecco la canzone nuova. Manca solo l'alba.
- DIGIUNO: FLAVIANO: C'è una canzone di dieci anni fa, sui Valmarcola. Non la canto più.
- ULTIMATUM: FLAVIANO: Undici stendardi e un monte solo: la rima è facile, il finale no.

**Compagno**, medico, studioso di assedi. Luogo: casa del medico (edificio nuovo). Figura: anziano con la borsa del medico, senza barba bianca.

- NOTTE: COMPAGNO: Undici eserciti mangiano la piana in due settimane. Monaldo ha fretta.
- DIGIUNO: COMPAGNO: Nel 1140 cacciammo i Valmarcola. Chi è cacciato prima o poi torna.
- ULTIMATUM: COMPAGNO: Cento assedi ho studiato. Novanta finiscono con la fame, gli altri peggio.

**Masio il Romano**, gabelliere romano bloccato in città. Luogo: casotto del pedaggio a Porta Metauro, con Nello. Figura: mercante con la fascia gialla e rossa.

- NOTTE: MASIO: Gualdo e Nocera vogliono solo er pedaggio. Gli fate lo sconto e tornano a casa.
- DIGIUNO: MASIO: Da fuori, Gubbio è quella che s'allarga. Da dentro, ve lo giuro, è più carina.
- ULTIMATUM: MASIO: A Roma 'sto grifo lo famo arrosto. Co' le patate no, che non ci stanno.

---

## Via dei Consoli

**Montano**, cavadenti e ritrattista, eugubino che lavora a Bergamo. Tornato per la madre, è rimasto chiuso dentro dall'assedio. Luogo: un banco all'aperto sotto le case di via dei Consoli (nessun edificio nuovo). Figura: mercante con le pinze alla cintura e una tavoletta dipinta. Galante con tutte, ma sempre con garbo: nessuna battuta lo mette in ridicolo.

- NOTTE: MONTANO: Stanotte ho ritratto le ragazze di guardia. Tutte più belle del Grifo, s'intende.
- DIGIUNO: MONTANO: A Bergamo cavo denti da dieci anni. Qui li cavo gratis, finché dura l'assedio.
- ULTIMATUM: MONTANO: Torno da Bergamo per mia madre e trovo undici eserciti. Gubbio sa accogliere.

---

## Piazza Quaranta Martiri

**Mastro Rufino**, carradore: costruisce e prepara i carri da corsa e da traino. Luogo: bottega del carradore (edificio nuovo). Figura: mercante con una ruota cerchiata di ferro. Nota: la battuta del DIGIUNO imposta `RUFINO_ASCOLTATO`.

- NOTTE: RUFINO: Finito l'assedio, si rifà la corsa dei carri giù per la piana. Il mio è già unto.
- DIGIUNO: RUFINO: Da vent'anni cerchio le ruote col ferro. Nessun ferro è stregato: col calore si apre.
- ULTIMATUM: RUFINO: Undici eserciti e nemmeno un carro decente. Il mio arriva a Perugia prima di loro.

**Giordano**, fontaniere. Luogo: vasca del fontaniere. Figura: anziano con secchio e corda, senza barba bianca. Nota: la battuta del DIGIUNO imposta `INDIZIO_ACQUA`; è anche il terzo indizio di Q-SP01.

- NOTTE: GIORDANO: È tornata su. Tre spanne. Non so chi siate, ma vi offro da bere.
- DIGIUNO: GIORDANO: Stanotte la vasca è calata di due spanne. Il condotto ha una ferita.
- ULTIMATUM: GIORDANO: Quest'acqua viene dal Bottaccione, tre miglia di pietra. Dolce come il latte.

---

## San Pietro

**Febo**, costruttore di congegni e tamburino. Luogo: ai piedi del campanile di San Pietro. Figura: soldato col tamburo.

- NOTTE: FEBO: All'alba, se il Campanone chiama, San Pietro risponde. Parola.
- DIGIUNO: FEBO: Campane mute per tre giorni. Le dita mi tremano da sole.
- ULTIMATUM: FEBO: Senti i tamburi? Tre colpi e una pausa: sono di Foligno.

**Giambono**, cavatore e balestriere. Luogo: sulle mura di San Pietro. Figura: soldato con la balestra. Nota: la battuta del DIGIUNO imposta `INDIZIO_ROCCIA`.

- NOTTE: GIAMBONO: Il frate dice che il concilio vieta la balestra. Tiro ai perugini, pregano male.
- DIGIUNO: GIAMBONO: La pietra nera della gola si sbriciola come pane secco. Lì scava chiunque.
- ULTIMATUM: GIAMBONO: Cecco dice che tira meglio lui. Cecco dice tante cose.

**Gabrione**, speziale, ritrae tutto a carboncino. Luogo: spezieria e ospizio (edificio nuovo). Figura: figura nuova: una testa più alta, pelata, carboncino in mano.

- NOTTE: GABRIONE: Ho ritratto chi passava stanotte. Uno aveva l'abito da canonico.
- DIGIUNO: GABRIONE: Quest'acqua sa di veratro, l'elleboro bianco. Agnese lo sa curare.
- ULTIMATUM: GABRIONE: Fermi un momento. Così. Vi ritraggo, che domani chissà.

**Ricciardo**, interprete dell'abate. Luogo: chiostro dell'abbazia di San Pietro. Figura: mercante con tavoletta di cera e stilo. Nota: una qualunque sua battuta imposta `RICCIARDO_ASCOLTATO`.

- NOTTE: RICCIARDO: La Rosa la donò Perugia, in un anno di pace. L'abate se lo ricorda.
- DIGIUNO: RICCIARDO: I soldati di Gualdo cantano che il soldo non arriva. In tre dialetti.
- ULTIMATUM: RICCIARDO: Ho tradotto molte lettere oggi. Di quali, monsignore, non chiedetemelo.

**Aurelia**, maestra dei fanciulli, fidanzata di Giambono. Luogo: chiostro dell'abbazia. Figura: popolana con un libro.

- NOTTE: AURELIA: Ho insegnato una parola nuova: «alba». La scrivono tutti, storta ma la scrivono.
- DIGIUNO: AURELIA: I bambini sono nel chiostro. Imparano le lettere, così non sentono i tamburi.
- ULTIMATUM: AURELIA: Giambono dice che tira meglio di Cecco. Io dico che parlano meglio di come tirano.

**Leonora**, tiene i turni di guardia, fidanzata di Febo. Luogo: torre della porta di San Pietro. Figura: popolana col rotolo dei turni.

- NOTTE: LEONORA: Tutti al loro posto, stanotte. Anche quelli che avevano la febbre. Contati.
- DIGIUNO: LEONORA: Un pellegrino si era messo nei turni di guardia. Mai visto alla torre. Strano.
- ULTIMATUM: LEONORA: Febo al tamburo, Giambono sulle mura, gli altri a turno. Il ruolo è fatto.

**Valenza**, tiene l'ospizio dei poveri e dei matti, moglie di Gabrione. Luogo: spezieria e ospizio. Figura: popolana col grembiule e la ciotola.

- NOTTE (se PANE_DATO): VALENZA: La popolana mi ha portato mezza crescia per gli altri. Viene da voi?
- NOTTE: VALENZA: Gabrione ha ritratto anche me, stanotte. Dice che ho la faccia dell'alba.
- DIGIUNO: VALENZA: Il pane dei poveri basta per oggi. Domani lo dividiamo per due.
- ULTIMATUM: VALENZA: Tano dice che i matti veri stanno fuori le mura. Qui ci sono solo i miei.

**Padellino**, oste. Luogo: taverna del corso, verso Sant'Andrea (edificio nuovo). Figura: mercante col fiasco e il grembiule. Nota: le tre righe «se non INDIZIO_...» sono l'aiuto: dicono dove cercare l'indizio che manca.

- NOTTE: PADELLINO: All'alba riapro. Il primo bicchiere lo offro io, chiunque vinca la piazza.
- DIGIUNO (se non INDIZIO_CARTA): PADELLINO: Bubo cercava una carta e non la trovava. Bubo non perde mai niente.
- DIGIUNO (se non INDIZIO_ACQUA): PADELLINO: Giordano stamattina guardava la vasca come si guarda un malato.
- DIGIUNO (se non INDIZIO_ROCCIA): PADELLINO: Giambono dice che certe pietre non reggono. Chiedetegli quali.
- DIGIUNO: PADELLINO: Taverna chiusa, voci aperte. Dicono che al Bottaccione l'acqua parla strano.
- ULTIMATUM: PADELLINO: Monsignore! Il solito? Ah no, oggi niente vino. Allora il solito di domani.

---

## Sant'Agostino (fuori Porta Romana)

**Ciotto**, maestro dei conti e giocatore di tavola. Luogo: bottega dei conti e dei congegni (edificio nuovo). Figura: mercante col tavoliere sotto il braccio.

- NOTTE (se BORGO_DENTRO): CIOTTO: Ho salvato il tavoliere. Le pedine no: le ha mangiate un mulo.
- NOTTE (se BORGO_FUORI): CIOTTO: La bottega l'hanno rovesciata. Il tavoliere l'avevo sotto il mantello.
- DIGIUNO: CIOTTO: Niente pane, niente vino. Una partita a filetto, almeno?
- ULTIMATUM: CIOTTO: Undici contro uno? In tre mosse la vinco, se le pedine stanno ferme.

**Fazio**, maestro di congegni. Luogo: bottega dei conti e dei congegni. Figura: mercante con una grande chiave.

- NOTTE: FAZIO: Ho unto i cardini. Se domani si apre, almeno non cigola.
- DIGIUNO: FAZIO: La porta si apre e si richiude in un fiato. L'argano l'ho fatto io.
- ULTIMATUM: FAZIO: Se tirate questa leva, la porta scende. Se non la tirate, no. Facile.

**Lauretta**, maestra dei numeri, moglie di Fazio. Luogo: bottega di famiglia. Figura: popolana con la tavoletta dei conti.

- NOTTE: LAURETTA: Nicoluccio dorme sulle pedine di Ciotto. Le ha contate tutte prima di chiudere gli occhi.
- DIGIUNO: LAURETTA: Ho rifatto il conto tre volte. Dentro: sei giorni di grano. Fuori: sette, e il borgo.
- ULTIMATUM: LAURETTA: Settanta bocche nel borgo. Con il grano dei consoli, un giorno in meno per tutti.

**Nicoluccio**, bambino, figlio di Lauretta e Fazio. Luogo: con Lauretta. Figura: figura nuova: bambino.

- NOTTE: NICOLUCCIO: Ho visto tre luci sul monte. Le ho contate: sono tre.
- DIGIUNO: NICOLUCCIO: Ciotto mi ha insegnato il filetto. Gli ho vinto tre volte. Quasi.
- ULTIMATUM: NICOLUCCIO: Mamma dice che undici è più di dieci. Io lo sapevo già.

**Bubo**, custode delle carte della pieve. Luogo: cella delle carte nella chiesa. Figura: frate senza tonsura, con un rotolo. Nota: la battuta del DIGIUNO imposta `INDIZIO_CARTA`.

- NOTTE: BUBO: Le carte le ho salvate tutte. Una sola manca, e lo sapete già quale.
- DIGIUNO: BUBO: Manca il disegno dell'acquedotto. L'aveva chiesto il capitolo, e non torna.
- ULTIMATUM: BUBO: Guarda: un gioco inciso dai romani. Mille anni e ancora si gioca.

**Valeriana**, guardia di ronda del borgo, fidanzata di Bubo. Luogo: strada verso Porta Romana. Figura: popolana con lanterna e bastone.

- NOTTE: VALERIANA: Stanotte un canonico ha preso la strada di San Girolamo. Verso il monte, da solo.
- DIGIUNO: VALERIANA: Botteghe chiuse anche nel borgo. Bubo, quel rotolo lo leggi domani.
- ULTIMATUM: VALERIANA: Bando dei consoli: chi ha un carro lo porta a Porta Romana. Subito.

**Ragnetto**, lavorante della calcara. Luogo: la calcara (edificio nuovo). Figura: soldato senza elmo, braccia nude, trave in spalla.

- NOTTE: RAGNETTO: Il vescovo nella calce, una volta. E ha perdonato. Io non ci riuscirei.
- DIGIUNO: RAGNETTO: Mia nonna diceva che il fuoco del borgo fu un male che salvò. Non so cosa vuol dire.
- ULTIMATUM: RAGNETTO: Datemi un'ora e questa trave sta sulle mura. Due, se ci metto la calce.

**Andreuccio**, miliziano di Porta Romana. Luogo: fuori Porta Romana. Figura: soldato con lo scudo col monte bianco.

- NOTTE (se BORGO_DENTRO): ANDREUCCIO: Dormono tutti dentro. Io resto fuori: la mia porta è questa.
- NOTTE (se BORGO_FUORI): ANDREUCCIO: Hanno bruciato tre case. Ne abbiamo salvate dieci. Ho contato.
- DIGIUNO: ANDREUCCIO: Porta Romana è mia finché c'è luce. Poi è di Dio, e un po' anche mia.
- ULTIMATUM: ANDREUCCIO: Le mura qui sono basse. Il borgo è ancora più basso, monsignore.
