# Battute d'ambiente: chi sta dove nelle 14 aree

Fonte: GDD Sez. 31B (NPC di lore), Sez. 38 (punti d'interesse), `docs/mappa_del_mondo.md` (aree e luoghi). Formato nel [README](README.md).

Ogni NPC ha una battuta per fase della storia. La regola è quella del prototipo (`npc_registry.h`): si prende **la prima condizione che vale**, quindi la fase più avanzata sta in cima. Un trattino vuol dire che in quella fase l'NPC non c'è.

Fasi:

- **ULTIMATUM**: da A1-01 ad A1-04 (prima che la città si chiuda).
- **DIGIUNO**: da A1-05 alla partenza per il monte. Le strade sono più vuote.
- **NOTTE**: da B-05 all'epilogo. Lanterne, voci basse, chi è sveglio aspetta l'alba.

I datori di quest sono nel file delle quest, non qui.

---

## Piazza Grande

**Il console Guido** (sotto il portone dei Consoli). Le sue battute di trama sono in A1-01, A1-05 ed E-01.

- NOTTE: GUIDO (preoccupato): Non ho dormito, monsignore. Ho contato i fuochi nella piana. Sono di più.
- DIGIUNO: GUIDO (calmo): La città tace, come avete chiesto. Non l'ho mai sentita così.

**Berto il Tagliapietre** (sul selciato, verso il parapetto)

- NOTTE: BERTO: Siete scesi dal Bottaccione? E la roccia nera... l'avete vista? Ve l'avevo detto.
- DIGIUNO: BERTO: Mio nonno ha scalpellato la pietra del Condotto nel Bottaccione.
- DIGIUNO: BERTO: Diceva sempre: c'è una fessura dove la roccia diventa nera come la pece. Lì la terra non dorme.
- DIGIUNO: BERTO: Fate attenzione, se scendete laggiù.
- ULTIMATUM: BERTO: Undici stendardi. Io ne ho contati dodici, ma uno forse era un lenzuolo steso.

**Popolana** (vicino al parapetto)

- NOTTE: POPOLANA: Dicono che sul monte si sono accese tre luci. Le ho viste anch'io, giuro.
- DIGIUNO: POPOLANA: Tre giorni senza pane. Li faccio, monsignore. Ma il bambino piange.
- ULTIMATUM: POPOLANA: Quel cavaliere col Grifo... ha guardato le nostre case come si guarda il bestiame.

---

## via dei Consoli

**Merciaio** (davanti a una bottega chiusa)

- NOTTE: MERCIAIO: Ho riaperto la finestra solo per vedere chi passava. Siete voi? Allora richiudo contento.
- DIGIUNO: MERCIAIO: Bottega chiusa per ordine del vescovo. Ma se il cavaliere ha bisogno di un ago, bussate.
- ULTIMATUM: MERCIAIO: Se arrivano i perugini, la prima cosa che rubano sono le stoffe. Le nascondo in cantina.

---

## Largo del Bargello

**Mastro Tano** (accanto alla Fontana dei Matti). La Patente da Matto è fuori dalla v1: Tano la promette e basta.

- NOTTE: TANO: Ancora in giro? Solo i matti girano a quest'ora. Siete dei nostri, allora.
- DIGIUNO: TANO: Fermati, cavaliere! Nessuno passa davanti al Bargello senza la follia sacra di chi ama questa terra.
- DIGIUNO: TANO: Ma oggi la fontana digiuna pure lei. Torna quando la città sarà libera, e ti farò matto davvero.
- ULTIMATUM: TANO: L'acqua di questa fonte ha visto più assedi di me. E io ne ho visti tanti.

---

## San Martino

**Cecco il Balestriere** (alla postierla). Le battute di trama sono in A1-03.

- NOTTE: CECCO: Da Porta Metauro? Allora la gola non è più loro. Dormirò un'ora, forse.
- DIGIUNO: CECCO: Postierla chiusa, monsignore. Nemmeno il vento passa senza il mio permesso.

**Lavandaia** (sul Camignano)

- NOTTE: LAVANDAIA: L'acqua del Camignano stasera è più chiara. Non so perché, ma la ringrazio.
- DIGIUNO: LAVANDAIA: L'acqua del fosso ha un colore che non mi piace. Verde, come il ramarro.
- ULTIMATUM: LAVANDAIA: Se chiudono le porte, chi ci porta la legna? Il bosco sta fuori.

---

## Teatro Romano

Fuori dalle mura. Dopo A1-04 restano solo nemici visibili e la quest delle fornaci, se c'è.

- ULTIMATUM: nessun NPC: la scena è A1-04.

---

## Piazza Quaranta Martiri

**Venditore delle Logge dei Tiratori**. Se F5 prevede un negozio, è qui; altrimenti diventa un dono una tantum.

- NOTTE: VENDITORE: Non dovrei vendere, col digiuno. Ma voi non digiunate, vero? Avvicinatevi.
- DIGIUNO: VENDITORE: Crescia, biscotti all'anice, un fiasco di rosso. Per chi combatte, il vescovo ha detto.
- ULTIMATUM: VENDITORE: Comprate oggi, che domani non so se ci sarà ancora una loggia.

**Fra' Matteo il Pescatore** (dona un Baccalà alla Ceraiola una sola volta: bandiera `DONO_MATTEO`)

- DIGIUNO, prima volta: FRA' MATTEO: Il Camignano è torbido, ma le riserve del convento sono piene.
- DIGIUNO, prima volta: FRA' MATTEO: Prendi questo baccalà con le prugne. Basta un boccone per tornare in fiato.
- SISTEMA: Ricevi Baccalà alla Ceraiola.
- dopo il dono: FRA' MATTEO: Uno a testa, e già è troppo. Il resto è per i feriti.

---

## San Pietro

**Lucia la Tessitrice**. Nel GDD cuce i Fazzoletti Ceraioli, che sono della festa di oggi: qui cuce bende e stendardi.

- NOTTE: LUCIA: Ho cucito bende tutta la notte. Ogni punto trattiene una preghiera.
- DIGIUNO: LUCIA: Quando tornerete, cucirò uno stendardo nuovo: rosso, col monte bianco. Ma tornate.
- ULTIMATUM: LUCIA: Se chiudono le porte, la lana finisce in una settimana. Le bende prima.

---

## via XX Settembre

**Vecchio sulla scalinata**

- NOTTE: VECCHIO: Ho sentito l'acqua tornare nelle fontane. A una certa età si sente tutto.
- DIGIUNO: VECCHIO: Questa salita la faccio da settant'anni. I perugini la troveranno più ripida di me.
- ULTIMATUM: VECCHIO: Ubaldo! Ti ricordi quando eri chierico e ti addormentavi ai vespri?
- ULTIMATUM: UBALDO (calmo): Me lo ricordo. Mi svegliavi tu, con un calcio.

---

## Sant'Agostino

**Frate agostiniano**

- NOTTE: FRATE: Preghiamo a turno, tutta la notte. Il mio turno è finito, ma resto sveglio.
- DIGIUNO: FRATE: La chiesa è aperta a chi vuole pregare in silenzio. Il silenzio è l'unica cosa che non manca.
- ULTIMATUM: FRATE: Le mura di qui sono le più basse. Lo sanno anche loro, temo.

---

## Sant'Andrea

**Sentinella di Porta Romana**

- NOTTE: SENTINELLA: I fuochi dei perugini non si muovono. Aspettano l'alba come noi.
- DIGIUNO: SENTINELLA: Da qui si vedono gli stendardi di Spoleto e Foligno. Sono tanti, monsignore.
- ULTIMATUM: SENTINELLA: Porta Romana tiene. Per ora tiene.

---

## Duomo e Palazzo Ducale

**Canonico** (sul varco del monte). La battuta di trama è in A1-06.

- NOTTE: CANONICO: Il capitolo ha pregato per voi tre notti. Vedo che è servito.
- ULTIMATUM: CANONICO: Il vescovo sale al monte? Allora preparo le candele. Tre, mi pare giusto.

---

## Stradoni del Monte, Basilica, Strada del Bottaccione

Nessun NPC d'ambiente: sono i luoghi della trama (A1-07, A1-08, A1-09, B-01...B-04). La spia legata resta in sacrestia dopo A1-09:

- SPIA: Che guardate? Non ho altro da dirvi. E l'acqua... l'acqua l'avete salvata, vero? Peccato.
