# I mestieri della città: battute di contorno

Copione v2, 4 novembre 2026 (pezzo VIVA). Richiesta di Cioti: «molti altri npc anche che hanno una sola battuta e non sono utili, per i lavori mancanti in città». Stesso formato di [03_npc_ambiente.md](03_npc_ambiente.md): vince la prima riga che vale, dall'alto; una riga `(se BANDIERA)` sta sopra quella della stessa fase senza condizione; un trattino mancante vuol dire che in quella fase l'NPC non c'è.

Sono gente di passaggio nella storia: nessuno accende bandiere, nessuno dà oggetti, nessuno anticipa la trama. Ognuno dice com'è la sua giornata mentre la città si prepara all'assedio (ULTIMATUM), tace e digiuna (DIGIUNO), aspetta l'alba (NOTTE).

**Scelta dei mestieri.** Mestieri attestati in un comune dell'Italia centrale del XII secolo e legati a quello che serve a una città assediata: frecce, corde, pece, pane che dura, acqua, lana per le sentinelle, il registro dei difensori. Le arti della lana e dei tintori sul Camignano sono una tradizione eugubina vera (più tarda come corporazioni, qui solo come mestieri). Nessun mestiere ripete quelli già presenti fra gli NPC d'ambiente e gli amici.

**Figura e posto** di ognuno in `dati/mestieri.json` (figure di `tools/figure_popolo.py`).

---

## Piazza Grande

**Il Banditore del Comune**

- NOTTE: BANDITORE: Stanotte non ho niente da annunciare. È la prima volta in vent'anni.
- DIGIUNO: BANDITORE: Il vescovo ha chiesto silenzio, così gli annunci li faccio sottovoce. Un banditore che bisbiglia!
- ULTIMATUM: BANDITORE: Udite! Per ordine dei consoli, chi ha un'arma la porti in piazza entro il vespro!

**Il Misuratore del grano**

- NOTTE: MISURATORE: Ho dormito sopra i sacchi del grano del Comune. Qualcuno doveva fargli la guardia.
- DIGIUNO: MISURATORE: Col digiuno il grano dura di più. Per una volta i miei conti tornano.
- ULTIMATUM: MISURATORE: Uno staio di grano a famiglia, non di più. Deve durare per tutto l'assedio.

---

## via dei Consoli

**Il Fabbro**

- NOTTE: FABBRO: Ho battuto l'ultima punta di freccia a mezzanotte. Non mi sento più le braccia.
- DIGIUNO: FABBRO: Tengo basso il fuoco della forgia. Il carbone va risparmiato.
- ULTIMATUM: FABBRO: Punte di freccia, cento al giorno. Il martello non si ferma nemmeno a pranzo.

**La Vasaia**

- NOTTE: VASAIA: Ho cotto brocche tutta la notte. Domani serviranno a portare acqua sulle mura.
- DIGIUNO: VASAIA: Ho rotto tre vasi stamattina. A stomaco vuoto mi tremano le mani.
- ULTIMATUM: VASAIA: Faccio pignatte per la pece, monsignore. Dalle mura la si versa bollente su chi sale.

---

## Largo del Bargello

**L'Acquaiolo**

- NOTTE: ACQUAIOLO: Sentite come scorre forte la fontana? Stanotte l'acqua è tornata.
- DIGIUNO: ACQUAIOLO: La fontana dà meno acqua del solito. Ci metto il doppio a riempire il secchio.
- ULTIMATUM: ACQUAIOLO: Riempio tutte le botti della città. In un assedio l'acqua vale più del vino.

**Il Funaio**

- NOTTE: FUNAIO: Tutte le mie corde sono sulle mura. Mi è rimasto solo un po' di spago.
- DIGIUNO: FUNAIO: La canapa è finita. Le donne mi hanno portato i loro capelli, e intreccio quelli.
- ULTIMATUM: FUNAIO: Faccio corde per le scale e per i secchi delle mura. Me ne chiedono a non finire.

---

## San Martino

**Il Tintore** (sul Camignano)

- NOTTE: TINTORE: Stanotte il fosso è tornato chiaro. Domani ricomincio a tingere.
- DIGIUNO: TINTORE: L'acqua del fosso è torbida e i colori non prendono. Ho smesso di tingere.
- ULTIMATUM: TINTORE: Cento pezze rosse per gli stendardi. Ho le braccia rosse fino al gomito.

**Il Conciatore**

- NOTTE: CONCIATORE: Ho finito l'ultimo scudo. All'alba lo porto io stesso sulle mura.
- DIGIUNO: CONCIATORE: Col digiuno non sento più nemmeno la puzza delle pelli. Qualcosa di buono ce l'ha.
- ULTIMATUM: CONCIATORE: Pelli per gli scudi, monsignore. Puzzano, ma fermano le frecce.

**Il Mugnaio**

- NOTTE: MUGNAIO: Ho sentito l'acqua tornare nel canale del mulino. Domani le macine ripartono.
- DIGIUNO: MUGNAIO: Le macine sono ferme. Il vescovo ha chiesto silenzio, e il mulino fa troppo rumore.
- ULTIMATUM: MUGNAIO: Macino tutto il grano prima che chiudano le porte. Giorno e notte.

---

## Piazza Quaranta Martiri

**Il Lanaiolo** (sotto la loggia)

- NOTTE: LANAIOLO: Ho dato l'ultima coperta a un ragazzo di guardia. Stanotte il freddo lo sento io.
- DIGIUNO: LANAIOLO: Ho steso la lana ad asciugare e nessuno la tocca. Col digiuno anche i ladri stanno a casa.
- ULTIMATUM: LANAIOLO: Faccio coperte di lana per le sentinelle. Sulle mura, di notte, fa un freddo che morde.

**Il Pastore**

- NOTTE: PASTORE: Ho contato le pecore tre volte. Ci sono tutte. Ora posso pregare anch'io.
- DIGIUNO: PASTORE: Le pecore mangiano l'erba dei giardini. Il digiuno vale per i cristiani, non per loro.
- ULTIMATUM: PASTORE: Ho portato il gregge dentro le mura. Le mie pecore non avevano mai visto una piazza.

**Il Macellaio**

- DIGIUNO: MACELLAIO: Bottega chiusa per il digiuno. È la prima volta che il mio coltello riposa.
- ULTIMATUM: MACELLAIO: Sale, sale e ancora sale. La carne salata si conserva per tutto l'assedio.

---

## San Pietro

**La Fornaia**

- NOTTE: FORNAIA: Ho riacceso il forno prima dell'alba. Chi torna troverà il pane caldo.
- DIGIUNO: FORNAIA: Il forno è spento. Tengo la brace sotto la cenere, così lo riaccendo in fretta.
- ULTIMATUM: FORNAIA: Faccio pane biscotto: duro come la pietra, ma si conserva un mese. Volete assaggiare?

---

## via XX Settembre

**Il Calzolaio**

- NOTTE (se BORGO_DENTRO): CALZOLAIO: Ho cucito scarpe piccole tutta la notte. I bambini del borgo sono entrati scalzi.
- NOTTE: CALZOLAIO: Ho risuolato scarpe tutta la notte. Sulle mura si consumano in fretta.
- DIGIUNO: CALZOLAIO: Batto piano col martelletto, per non disturbare. La città vuole silenzio.
- ULTIMATUM: CALZOLAIO: Faccio suole doppie per chi sta sulle mura. Le pietre di Gubbio consumano tutto.

---

## Sant'Agostino

**L'Ortolana**

- NOTTE: ORTOLANA: Domani torno al mio orto, fuori dalle mura. Se c'è ancora un orto.
- DIGIUNO: ORTOLANA: Il digiuno non mi pesa. I miei cavoli li ho portati tutti al convento.
- ULTIMATUM: ORTOLANA: Raccolgo tutto, anche quello ancora verde. Meglio acerbo che in bocca ai perugini.

**Il Carbonaio**

- DIGIUNO: CARBONAIO: Sono nero di carbone da capo a piedi. Per fortuna col digiuno non devo toccare il pane.
- ULTIMATUM: CARBONAIO: Porto carbone per le forge e per scaldare la pece. Tutta la città brucia la legna del mio bosco.

---

## Sant'Andrea

**Il Carpentiere**

- NOTTE: CARPENTIERE: La palizzata è finita. Ci ho inciso il mio nome in basso, dove non si vede.
- DIGIUNO: CARPENTIERE: Pianto i chiodi piano, per rispetto del silenzio. Ma la palizzata deve crescere lo stesso.
- ULTIMATUM: CARPENTIERE: Costruisco palizzate dietro le porte. Il legno fresco scricchiola, ma regge.

**Il Frecciaio**

- NOTTE: FRECCIAIO: Diecimila frecce pronte per le mura. Le ho contate una per una.
- DIGIUNO: FRECCIAIO: Le oche del quartiere mi guardano storto. Sanno che sono stato io a spennarle.
- ULTIMATUM: FRECCIAIO: Faccio frecce. Per le penne ho dovuto spennare tutte le oche del quartiere.

---

## Duomo e Palazzo Ducale

**Il Campanaro**

- NOTTE: CAMPANARO: All'alba suonerò a festa o a martello. Speriamo a festa, monsignore.
- DIGIUNO: CAMPANARO: Le campane tacciono per il digiuno. Non avevo mai sentito la città così silenziosa.
- ULTIMATUM: CAMPANARO: Se attaccano, suono a martello: tre colpi, poi tre, poi tre. Ricordatevelo.

**Il Viandante**

- NOTTE: VIANDANTE: Quando riapriranno le porte riprenderò la strada. Ma racconterò a tutti di questa città.
- DIGIUNO: VIANDANTE: Digiuno anch'io. Per chi è in viaggio, saltare i pasti è normale.
- ULTIMATUM: VIANDANTE: Andavo a Roma in pellegrinaggio e mi hanno chiuso dentro Gubbio. Il Signore ha i suoi piani.

---

## Sala dei Consoli

**Il Notaio del Comune**

- NOTTE: NOTAIO: Ho lasciato una pagina bianca nel registro. Domani ci scriverò com'è andata.
- DIGIUNO: NOTAIO: Ho scritto il voto del digiuno nel registro del Comune. Così nessuno potrà dimenticarlo.
- ULTIMATUM: NOTAIO: Scrivo i nomi di chi va a difendere le mura. Ho già riempito tre fogli.

**La Guardia della sala**

- NOTTE: GUARDIA: I consoli sono sulle mura. Io resto qui a fare la guardia alla sala.
- DIGIUNO: GUARDIA: Niente pane neanche per le guardie. Ma resto in piedi lo stesso.
- ULTIMATUM: GUARDIA: Qui si entra con rispetto, monsignore. Per voi la porta è sempre aperta.

---

## Taverna del corso

**L'Avventore**

- NOTTE: AVVENTORE: Non bevo, sto qui per la compagnia. Al buio da solo non ci so stare.
- DIGIUNO: AVVENTORE: La taverna è chiusa per il digiuno, ma la panca è libera. Mi siedo e guardo il camino spento.
- ULTIMATUM: AVVENTORE: Un bicchiere per farmi coraggio, monsignore. Uno solo, lo giuro.

---

## Spezieria e ospizio

**Il Ricoverato dell'ospizio**

- NOTTE: RICOVERATO: Valenza mi ha rimboccato la coperta. Alla mia età, pensate un po'.
- DIGIUNO: RICOVERATO: Digiuno anch'io, monsignore. Alla mia età si mangia poco comunque.
- ULTIMATUM: RICOVERATO: Dalla finestra vedo le tende dei nemici nella valle. Sono tante, ma le stelle sono di più.

---

## Bottega del carradore

**Il Garzone del carradore**

- NOTTE: GARZONE: Mastro Rufino dorme accanto al carro. Dice che così nessuno glielo ruba.
- DIGIUNO: GARZONE: Ungo le ruote a stomaco vuoto. Il grasso lo guardo e basta.
- ULTIMATUM: GARZONE: Il mastro dice che le ruote fatte bene cantano. Io le sento solo cigolare.
