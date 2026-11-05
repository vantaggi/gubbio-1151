# Battute d'ambiente: chi sta dove nelle 14 aree

Fonte: GDD Sez. 31B (NPC di lore), Sez. 38 (punti d'interesse), `docs/mappa_del_mondo.md` (aree e luoghi). Formato nel [README](README.md).

Ogni NPC ha una battuta per fase della storia. La regola è quella del prototipo (`npc_registry.h`): si prende **la prima condizione che vale**, quindi la fase più avanzata sta in cima. Un trattino vuol dire che in quella fase l'NPC non c'è.

Fasi:

- **ULTIMATUM**: da A1-01 ad A1-04 (prima che la città si chiuda).
- **DIGIUNO**: da A1-05 alla partenza per il monte. Le strade sono più vuote.
- **NOTTE**: da B-05 all'epilogo. Lanterne, voci basse, chi è sveglio aspetta l'alba.

I datori di quest sono nel file delle quest, non qui. Gli amici di Cioti e le loro famiglie sono in [05_npc_amici.md](05_npc_amici.md).

Varianti con bandiera (v2): una riga `- NOTTE (se BANDIERA): ...` vale solo con quella bandiera e sta sopra la riga della stessa fase senza condizione, che vale altrimenti.

---

## Piazza Grande

**Il console Guido** (sotto il portone dei Consoli). Le sue battute di trama sono in A1-01, A1-05 ed E-01. Nella NOTTE rifà la domanda di B-05 a chi ha detto «Non ancora»: con «Sì, è ora» accende `ALBA_CONFERMATA` e parte E-01.

- NOTTE: GUIDO (preoccupato): Non ho dormito, monsignore. Ho contato i fuochi nella piana. Sono di più.

Se `BORGO_DENTRO`:

- GUIDO (preoccupato): Con quelli del borgo sono settanta bocche in più. Ho rifatto i conti del grano tre volte.

Poi, per tutti:

- GUIDO (calmo): L'alba sta per sorgere, monsignore. Andiamo incontro all'araldo?
- SCELTA: Sì, è ora / Non ancora

Con «Sì, è ora» (`ALBA_CONFERMATA`):

- GUIDO (deciso): Allora andiamo. Il popolo vi aspetta già in piazza.

- DIGIUNO: GUIDO (calmo): La città tace, come avete chiesto. Non l'avevo mai sentita così silenziosa.

**Berto il Tagliapietre** (sul selciato, verso il parapetto)

- NOTTE: BERTO: Siete tornati dal Bottaccione! L'avete vista, la roccia nera di cui vi parlavo?
- DIGIUNO: BERTO: Mio nonno faceva lo scalpellino. Ha tagliato le pietre del condotto, giù nella gola del Bottaccione.
- DIGIUNO: BERTO: Raccontava di un punto dove la roccia diventa nera come la pece, diversa da tutta l'altra.
- DIGIUNO: BERTO: Se scendete laggiù, state attenti. Quel punto lo conoscevano solo i costruttori del condotto.
- ULTIMATUM: BERTO: Quest'estate ho rattoppato io le mura. Adesso vedremo se ho lavorato bene.

**Popolana** (vicino al parapetto)

- NOTTE (se PANE_DATO): POPOLANA: Dicono che sul monte si sono accese tre luci. Le ho viste anch'io, giuro.
- NOTTE: POPOLANA: Dicono che sul monte si sono accese tre luci. Mio figlio non le ha viste: dormiva, sfinito dalla fame.
- DIGIUNO (se PANE_DATO): POPOLANA: Il bambino dorme, finalmente. Che Dio vi renda il doppio, monsignore.
- DIGIUNO: POPOLANA: Il digiuno lo faccio, monsignore. Ma il mio bambino piange dalla fame.

Dilemma D3: dopo la battuta del DIGIUNO, se il gruppo ha almeno una Crescia di Pasqua e non c'è `PANE_DATO`:

- SCELTA: Dalle una fetta / Non ora

Con «Dalle una fetta» si toglie 1 Crescia di Pasqua e si imposta `PANE_DATO`:

- GIORGIO (calmo): Per il bambino. Io ho mangiato stamattina, mi basta.
- SISTEMA: Hai dato una fetta di Crescia di Pasqua.

Con «Non ora»:

- ANTONIO (calmo): La fame di un giorno non uccide. Lassù ci servirà tutto quello che abbiamo.

- ULTIMATUM: POPOLANA: Quel cavaliere di Perugia guardava le nostre case come si guarda il bestiame al mercato.

---

## via dei Consoli

**Merciaio** (davanti a una bottega chiusa)

- ULTIMATUM: MERCIAIO: Se entrano i perugini, la prima cosa che rubano sono le stoffe. Le nascondo in cantina.

---

## Largo del Bargello

**Mastro Tano** (accanto alla Fontana dei Matti). La Patente da Matto è fuori dalla v1: Tano la promette e basta.

- NOTTE: TANO: Ancora in giro a quest'ora? Qui si dice che di notte girano solo i matti.
- DIGIUNO: TANO: Questa è la Fontana dei Matti. A città libera, tre giri intorno e vi faccio matti anche voi.
- ULTIMATUM: TANO: Questa fontana ha visto più assedi di me. E io, alla mia età, ne ho visti parecchi.

---

## San Martino

**Cecco il Balestriere** (alla postierla). Le battute di trama sono in A1-03.

- NOTTE (se ESULE_LIBERATO): CECCO: Avete lasciato andare quel ragazzo? Speriamo che trovi la strada di casa.
- NOTTE: CECCO: Siete rientrati da Porta Metauro? Allora la gola è di nuovo nostra. Stanotte dormo un'ora.
- DIGIUNO (se INDIZIO_ROCCIA): CECCO: Quello di San Pietro dice che con la balestra tira meglio di me? È una bugia.
- DIGIUNO: CECCO: La postierla è chiusa, monsignore. Da qui non passa nemmeno il vento senza il mio permesso.

**Lavandaia** (sul Camignano)

- NOTTE: LAVANDAIA: Stasera l'acqua del Camignano è tornata limpida. Non so cosa sia successo, ma ringrazio il cielo.
- DIGIUNO: LAVANDAIA: L'acqua del fosso ha un colore strano, verdastro. Non ci lavo più nemmeno gli stracci.
- ULTIMATUM: LAVANDAIA: Se chiudono le porte, chi ci porta la legna? Il bosco sta fuori dalle mura.

---

## Teatro Romano

Fuori dalle mura. Dopo A1-04 restano solo nemici visibili e la quest delle fornaci, se c'è.

Nessun NPC d'ambiente nella fase ULTIMATUM: al Teatro Romano c'è la scena A1-04.

---

## Piazza Quaranta Martiri

**Venditore delle Logge dei Tiratori**. Se F5 prevede un negozio, è qui; altrimenti diventa un dono una tantum.

- NOTTE: VENDITORE: Col digiuno non dovrei vendere. Ma chi combatte può mangiare, l'ha detto il vescovo.
- DIGIUNO (se BORGO_DENTRO): VENDITORE: Con la gente del borgo dentro, il cibo non basta. Ho meno Crescia per voi, mi spiace.
- DIGIUNO: VENDITORE: Ho Crescia, Biscotti all'anice e poco altro. Il vescovo ha detto: il cibo a chi combatte.
- ULTIMATUM: VENDITORE: Comprate oggi! Stasera chiudono le porte, e chissà cosa resterà da vendere.

**Fra' Matteo il Pescatore**. Dona un Baccalà alla Ceraiola una sola volta: la battuta del DIGIUNO imposta `DONO_MATTEO`. La prima volta parla la variante «se non `DONO_MATTEO`», che dà il baccalà (il dono dell'oggetto è da collegare nel codice degli NPC: oggi una battuta d'ambiente non dà oggetti); dopo, la riga senza condizione.

- DIGIUNO (se non DONO_MATTEO): FRA' MATTEO: Il Camignano è torbido, ma il convento ha delle riserve. Prendete questo baccalà.
- DIGIUNO: FRA' MATTEO: Uno solo, mi dispiace. Il resto lo teniamo per i feriti.

---

## San Pietro

**Lucia la Tessitrice**. Nel GDD cuce i Fazzoletti Ceraioli, che sono della festa di oggi: qui cuce bende e stendardi.

- NOTTE: LUCIA: Ho cucito bende tutta la notte. Domani ne serviranno tante.
- DIGIUNO: LUCIA: Quando tornerete dal monte vi cucirò uno stendardo nuovo, rosso col monte bianco. Ma tornate.
- ULTIMATUM: LUCIA: Se chiudono le porte, la lana finirà in una settimana. E le bende anche prima.

---

## via XX Settembre

**Vecchio sulla scalinata**

- NOTTE: VECCHIO: Ho sentito l'acqua tornare nelle fontane. Alla mia età il sonno è leggero, si sente tutto.
- DIGIUNO: VECCHIO: Anni fa abbiamo cacciato i Valmarcola dalle loro torri. Dicono che ora sono là fuori, con Perugia.
- DIGIUNO: VECCHIO: Questa salita la faccio da settant'anni. Ai perugini sembrerà ancora più ripida.
- ULTIMATUM: VECCHIO: Ubaldo! Ti ricordi quando eri chierico e ti addormentavi ai vespri?
- ULTIMATUM: UBALDO (calmo): Me lo ricordo. Mi svegliavi tu, con un calcio.

---

## Sant'Agostino

**Frate agostiniano**

- NOTTE (se BORGO_FUORI): FRATE: Hanno bruciato tre case del borgo, fuori dalle mura. Il convento si è salvato.
- NOTTE: FRATE: Preghiamo a turno, tutta la notte. Il mio turno è finito, ma non riesco a dormire.
- DIGIUNO: FRATE: La chiesa è aperta a chi vuole pregare in silenzio. Di cibo non ne abbiamo, di silenzio sì.
- DIGIUNO: FRATE: Vent'anni fa nel borgo c'era un morbo. Qualcuno diede fuoco alle case dei malati e il morbo si fermò.
- ULTIMATUM: FRATE: Le mura da questa parte sono le più basse della città. Temo che lo sappiano anche loro.

---

## Sant'Andrea

**Sentinella di Porta Romana**

- NOTTE: SENTINELLA: I fuochi dei perugini sono fermi. Anche loro aspettano l'alba, come noi.
- DIGIUNO: SENTINELLA: Da qui si vedono gli stendardi di Spoleto e Foligno. Sono tanti, monsignore.
- DIGIUNO: SENTINELLA: Da qui si vedono gli stendardi di Gualdo e Fossato. Da ieri non si sono mossi.
- ULTIMATUM: SENTINELLA: Porta Romana regge. Per ora regge.

---

## Duomo e Palazzo Ducale

**Canonico** (sul varco del monte). La battuta di trama è in A1-06.

- NOTTE: CANONICO: Noi canonici abbiamo pregato per voi tutte le notti. Vedo che è servito.
- ULTIMATUM: CANONICO: Il vescovo sale al monte? Allora vi preparo tre candele, una per ciascuno.

---

## Stradoni del Monte, Basilica, Strada del Bottaccione

Nessun NPC d'ambiente: sono i luoghi della trama (A1-07, A1-08, A1-09, B-01...B-04). Fa eccezione la spia legata, che resta in sacrestia dopo A1-09. Questa sezione non è un'area di `tools/genera_storia.py`: la spia entrerà nel gioco quando la sacrestia avrà un posto per lei.

**La spia legata** (in sacrestia, da `VISIONE_BOTTACCIONE`). Prima di `CONDOTTO_SALVO` non sa ancora come è andata.

- NOTTE: SPIA: Che guardate? Non ho altro da dirvi. E l'acqua... l'acqua l'avete salvata, vero? Peccato.
- DIGIUNO (se CONDOTTO_SALVO): SPIA: Che guardate? Non ho altro da dirvi. E l'acqua... l'acqua l'avete salvata, vero? Peccato.
- DIGIUNO: SPIA: Andate pure giù. La gola è lunga, e l'acqua corre più veloce di voi.
