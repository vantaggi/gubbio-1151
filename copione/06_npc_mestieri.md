# I mestieri della città: battute di contorno

Copione v2, 4 novembre 2026 (pezzo VIVA). Richiesta di Cioti: «molti altri npc anche che hanno una sola battuta e non sono utili, per i lavori mancanti in città». Stesso formato di [03_npc_ambiente.md](03_npc_ambiente.md): vince la prima riga che vale, dall'alto; una riga `(se BANDIERA)` sta sopra quella della stessa fase senza condizione; un trattino mancante vuol dire che in quella fase l'NPC non c'è.

Sono gente di passaggio nella storia: nessuno accende bandiere, nessuno dà oggetti, nessuno anticipa la trama. Ognuno dice com'è la sua giornata mentre la città si prepara all'assedio (ULTIMATUM), tace e digiuna (DIGIUNO), aspetta l'alba (NOTTE).

**Scelta dei mestieri.** Mestieri attestati in un comune dell'Italia centrale del XII secolo e legati a quello che serve a una città assediata: frecce, corde, pece, pane che dura, acqua, lana per le sentinelle, il registro dei difensori. Le arti della lana e dei tintori sul Camignano sono una tradizione eugubina vera (più tarda come corporazioni, qui solo come mestieri). Nessun mestiere ripete quelli già presenti fra gli NPC d'ambiente e gli amici.

**Figura e posto** di ognuno in `dati/mestieri.json` (figure di `tools/figure_popolo.py`).

---

## Piazza Grande

**Il Banditore del Comune**

- NOTTE: BANDITORE: Stanotte non ho niente da gridare. È la prima volta in vent'anni.
- DIGIUNO: BANDITORE: Udite... ma piano. Il vescovo ha chiesto silenzio, e io grido sottovoce.
- ULTIMATUM: BANDITORE: Udite! Per ordine dei consoli, chi ha un'arma la porti in piazza entro il vespro!

**Il Misuratore del grano**

- NOTTE: MISURATORE: Ho dormito sopra i sacchi del Comune. Qualcuno doveva pur farlo.
- DIGIUNO: MISURATORE: Col digiuno il grano avanza. Non mi era mai capitato di contare in più.
- ULTIMATUM: MISURATORE: Uno staio a famiglia, non di più. Il grano del Comune deve durare.

---

## via dei Consoli

**Il Fabbro**

- NOTTE: FABBRO: Ho battuto l'ultima punta a mezzanotte. Ora le mani mi suonano da sole.
- DIGIUNO: FABBRO: Il fuoco della forgia lo tengo basso. Digiuna anche lui.
- ULTIMATUM: FABBRO: Punte di freccia, cento al giorno. Il martello non si ferma nemmeno a pranzo.

**La Vasaia**

- NOTTE: VASAIA: Ogni vaso che cuocio stanotte, spero, resterà vuoto.
- DIGIUNO: VASAIA: Ho rotto tre vasi stamattina. Senza mangiare le mani tremano.
- ULTIMATUM: VASAIA: Pignatte per la pece, monsignore. Dalle mura la si versa bollente.

---

## Largo del Bargello

**L'Acquaiolo**

- NOTTE: ACQUAIOLO: Senti come getta? Stanotte la fontana canta.
- DIGIUNO: ACQUAIOLO: La fontana getta meno del solito. Lo sento dal tempo che ci mette il secchio.
- ULTIMATUM: ACQUAIOLO: Riempio ogni botte della città. In un assedio l'acqua vale più del vino.

**Il Funaio**

- NOTTE: FUNAIO: Le corde sono tutte sulle mura. Mi è rimasto lo spago per legare il pane.
- DIGIUNO: FUNAIO: La canapa è finita. Ora intreccio i capelli che le donne mi hanno portato.
- ULTIMATUM: FUNAIO: Corde per le scale e per i secchi delle mura. Me ne chiedono a braccia.

---

## San Martino

**Il Tintore** (sul Camignano)

- NOTTE: TINTORE: Stanotte il fosso corre chiaro. Domani lo tingo di festa.
- DIGIUNO: TINTORE: Il fosso si porta via il colore. Sembra che stia male anche lui.
- ULTIMATUM: TINTORE: Cento pezze rosse per gli stendardi. Ho le braccia rosse fino al gomito.

**Il Conciatore**

- NOTTE: CONCIATORE: L'ultimo scudo è finito. All'alba lo porto io, sulle mura.
- DIGIUNO: CONCIATORE: A stomaco vuoto non sento più la puzza. Qualcosa di buono il digiuno ce l'ha.
- ULTIMATUM: CONCIATORE: Pelli per gli scudi, monsignore. Puzzano, ma fermano le frecce.

**Il Mugnaio**

- NOTTE: MUGNAIO: Ho sentito l'acqua nella gora. Domani le macine ripartono.
- DIGIUNO: MUGNAIO: Le macine sono ferme. Il vescovo ha detto digiuno, e obbediscono anche loro.
- ULTIMATUM: MUGNAIO: Macino tutto il grano prima che chiudano le strade. Giorno e notte.

---

## Piazza Quaranta Martiri

**Il Lanaiolo** (sotto la loggia)

- NOTTE: LANAIOLO: L'ultima coperta l'ho data a un ragazzo di guardia. Ora ho freddo io, ed è giusto.
- DIGIUNO: LANAIOLO: Stendo la lana e nessuno la tocca. Il digiuno fa santi anche i ladri.
- ULTIMATUM: LANAIOLO: Lana per le coperte delle sentinelle. Sulle mura, di notte, il freddo morde.

**Il Pastore**

- NOTTE: PASTORE: Le ho contate tre volte. Ci sono tutte. Stanotte posso pregare anch'io.
- DIGIUNO: PASTORE: Le pecore brucano i giardini. Il digiuno vale per i cristiani, non per loro.
- ULTIMATUM: PASTORE: Ho portato il gregge dentro le mura. Le pecore non hanno mai visto una piazza.

**Il Macellaio**

- DIGIUNO: MACELLAIO: Bottega chiusa per digiuno. È la prima volta che il coltello riposa.
- ULTIMATUM: MACELLAIO: Sale, sale e ancora sale. La carne salata dura quanto un assedio.

---

## San Pietro

**La Fornaia**

- NOTTE: FORNAIA: Ho riacceso il forno prima dell'alba. Chi torna troverà il pane caldo.
- DIGIUNO: FORNAIA: Il forno è spento. Tengo la brace sotto la cenere, per quando servirà.
- ULTIMATUM: FORNAIA: Pane biscotto: duro come la pietra, ma dura un mese. Assaggiate?

---

## via XX Settembre

**Il Calzolaio**

- NOTTE (se BORGO_DENTRO): CALZOLAIO: Ho cucito scarpe piccole tutta la notte. Quelli del borgo sono entrati scalzi.
- NOTTE: CALZOLAIO: Ho cucito tutta la notte. Domani in tanti dovranno camminare.
- DIGIUNO: CALZOLAIO: Batto piano col martelletto. La città vuole silenzio.
- ULTIMATUM: CALZOLAIO: Suole doppie per chi sale sulle mura. Le pietre di Gubbio consumano tutto.

---

## Sant'Agostino

**L'Ortolana**

- NOTTE: ORTOLANA: Domani torno all'orto. Se c'è ancora un orto.
- DIGIUNO: ORTOLANA: Il digiuno lo faccio volentieri. I cavoli li ho portati tutti al convento.
- ULTIMATUM: ORTOLANA: Raccolgo tutto, anche il verde. Meglio acerbo che in bocca a loro.

**Il Carbonaio**

- DIGIUNO: CARBONAIO: Sono nero da capo a piedi. Almeno col digiuno non sporco il pane.
- ULTIMATUM: CARBONAIO: Carbone per le forge e per la pece. Tutta la città brucia il mio bosco.

---

## Sant'Andrea

**Il Carpentiere**

- NOTTE: CARPENTIERE: La palizzata è finita. Ci ho inciso il mio nome in basso, dove non si vede.
- DIGIUNO: CARPENTIERE: Inchiodo piano, per rispetto. Le palizzate crescono lo stesso.
- ULTIMATUM: CARPENTIERE: Palizzate dietro le porte. Il legno fresco geme, ma regge.

**Il Frecciaio**

- NOTTE: FRECCIAIO: Diecimila frecce. Le ho contate una per una, con le dita nere.
- DIGIUNO: FRECCIAIO: Le oche mi guardano storto. Sanno chi è stato.
- ULTIMATUM: FRECCIAIO: Penne d'oca per le frecce. Ho spennato tutte le oche del quartiere.

---

## Duomo e Palazzo Ducale

**Il Campanaro**

- NOTTE: CAMPANARO: All'alba suono a festa o a martello. Speriamo a festa, monsignore.
- DIGIUNO: CAMPANARO: La campana tace. Il silenzio della città suona più forte di lei.
- ULTIMATUM: CAMPANARO: Se arrivano, suono a martello: tre colpi, poi tre, poi tre. Ricordatevelo.

**Il Viandante**

- NOTTE: VIANDANTE: Quando apriranno le porte riprenderò la strada. Ma racconterò di questa città.
- DIGIUNO: VIANDANTE: Digiuno anch'io. Per chi è in cammino è il pane di ogni giorno.
- ULTIMATUM: VIANDANTE: Andavo a Roma e mi hanno chiuso dentro Gubbio. Il Signore ha i suoi piani.

---

## Sala dei Consoli

**Il Notaio del Comune**

- NOTTE: NOTAIO: Lascio una riga bianca nel registro. Domani ci scriverò com'è andata.
- DIGIUNO: NOTAIO: Ho scritto il voto del digiuno nel registro. Così nessuno lo dimentica.
- ULTIMATUM: NOTAIO: Scrivo i nomi di chi va sulle mura. Il ruolo dei difensori è già di tre fogli.

**La Guardia della sala**

- NOTTE: GUARDIA: I consoli sono sulle mura. La sala si veglia lo stesso.
- DIGIUNO: GUARDIA: Niente pane neanche per le guardie. Sto dritto lo stesso.
- ULTIMATUM: GUARDIA: Qui si entra con rispetto, monsignore. Per voi, sempre.

---

## Taverna del corso

**L'Avventore**

- NOTTE: AVVENTORE: Non bevo, sto qui per la compagnia. Al buio da solo non ci so stare.
- DIGIUNO: AVVENTORE: Taverna chiusa, ma la panca è aperta. Guardo il camino spento.
- ULTIMATUM: AVVENTORE: Un bicchiere per il coraggio, monsignore. Uno solo, lo giuro.

---

## Spezieria e ospizio

**Il Ricoverato dell'ospizio**

- NOTTE: RICOVERATO: Valenza mi ha rimboccato la coperta. Alla mia età, pensate.
- DIGIUNO: RICOVERATO: Digiuno anch'io, monsignore. A me riesce bene da anni.
- ULTIMATUM: RICOVERATO: Dalla finestra si vedono le tende sul piano. Tante. Io conto le stelle: sono di più.

---

## Bottega del carradore

**Il Garzone del carradore**

- NOTTE: GARZONE: Mastro Rufino dorme accanto al carro. Dice che così non glielo rubano.
- DIGIUNO: GARZONE: Ingrasso i mozzi a stomaco vuoto. Il grasso lo guardo e basta.
- ULTIMATUM: GARZONE: Il mastro dice che le ruote cantano, se sono fatte bene. Io sento solo cigolare.
