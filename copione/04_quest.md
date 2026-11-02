# Le tre quest della v1

Scelte da Cioti il 1 novembre 2026: **Q-SM01** (Ferro), **Q-SA01** (Erbe), **Q-SP01** (Rosa). Fuori: Q-SG01 (San Giuliano non è tra le 14 aree) e Q-CIV01 (porta alla Patente da Matto). Fonte: GDD Sez. 31A e 31B. Formato nel [README](README.md).

Regole comuni:

- **Niente equipaggiamento nella v1**: le ricompense della Sez. 31A (corazza, balsamo, spilla) diventano consumabili della Sez. 8E più una conseguenza di trama. Il Quartiere guadagna reputazione come in `quest_data.h`, anche se il suo effetto (Atto III) è fuori dalla v1.
- **Nessuna quest si perde.** Ognuna si può prendere e consegnare fino all'epilogo (la conferma in Piazza Grande alla fine di B-05). Gli oggetti da raccogliere ci sono anche se la quest non è stata presa.
- Stato e contatore usano `quest_state` e `quest_counter` di `GameState`, come nel prototipo. Le bandiere nuove stanno nell'intervallo quest (64-127).

| Quest | Datore e luogo | Si prende | Obiettivo | Ricompensa |
| :-- | :-- | :-- | :-- | :-- |
| Q-SM01 Il ferro del Monte Calvo | Mastro Raniero, San Martino | da `ULTIMATUM_RICEVUTO` | 3 blocchi di ferro dalle fornaci occupate da Spoleto al Teatro Romano | 3 Crescia di Pasqua; Raniero spiega come si apre il ferro di Spoleto |
| Q-SA01 Le erbe del Bottaccione | Monna Agnese, Sant'Andrea | da `CITTA_IN_DIGIUNO` | 4 radici di elleboro nella Strada del Bottaccione | 3 Biscotti all'Anice; i feriti di Porta Romana si salvano |
| Q-SP01 La rosa d'argento | Fra' Bernardo, San Pietro | da `CITTA_IN_DIGIUNO` | Trovare l'infiltrato con tre indizi e riprendere il reliquiario | 1 Crescia sotto la Cenere; la benedizione dei miliziani |

---

## Q-SM01 · Il ferro del Monte Calvo

**Mastro Raniero** sta davanti alla sua bottega spenta, nei vicoli alti di San Martino.

### Proposta (stato NON INIZIATA)

- RANIERO: Le mie fornaci sono spente, ragazzo. Le truppe di Spoleto hanno bloccato il ferro del Monte Calvo al passo.
- RANIERO: E quello che avevo già colato me l'hanno preso. L'hanno ammucchiato nelle fornaci basse, al Teatro Romano.
- RANIERO: Riportami tre blocchi, e ti dico come si fa a bucare una corazza di Spoleto.
- GIORGIO (deciso): Tre blocchi. Fatto.
- RANIERO: Pesano, cavaliere. Non è come dire «fatto».
- OBIETTIVO: Recupera 3 blocchi di ferro alle fornaci del Teatro Romano.

### Teatro Romano: le fornaci

Regia: tre fornaci basse sotto le arcate, ognuna guardata da un Guerriero della Roccia visibile sulla mappa. Battuto il guerriero, il blocco si raccoglie toccando la fornace. Il contatore sale di 1.

- SISTEMA: Hai preso un blocco di ferro. Ancora 2.
- SISTEMA: Hai preso un blocco di ferro. Ancora 1.
- SISTEMA: Hai preso l'ultimo blocco di ferro. Riportalo a Raniero.

Al primo blocco, una volta sola:

- ANTONIO (calmo): Ferro buono. Peccato per chi l'ha rubato: sapeva rubare, non fondere.

### La postierla dopo la chiusura

Dopo `CITTA_IN_DIGIUNO` la postierla di San Martino è chiusa. Se Q-SM01 è attiva e non ancora pronta, Cecco la apre per questa sola ragione:

- CECCO: Il ferro di Raniero? Va bene, apro. Ma se tornate con mezza Spoleto alle spalle, chiudo lo stesso.

### Consegna (contatore 3)

- RANIERO: Tre blocchi. E li hai portati tu, non i muli. Ti ho giudicato male, ragazzo.
- RANIERO: Ascolta. Il ferro di Spoleto è battuto a freddo, a strati. Contro la lama regge come un muro.
- RANIERO: Ma col fuoco gli strati si aprono come le pagine di un libro bagnato. Ricordatelo, se incontri uno grosso.
- ANTONIO (calmo): Col fuoco. Sento che questa la ricorderò io.
- RANIERO: E per la strada, prendete queste. Mia moglie le ha fatte prima che il vescovo vietasse tutto.
- SISTEMA: Ricevi 3 Crescia di Pasqua al Formaggio.
- SISTEMA: San Martino ti è grato.

Regia: la fornace di Raniero si riaccende. Da qui la sua battuta cambia.

### Dopo

- NOTTE: RANIERO: Ho riacceso la fornace. Lavoro di notte, per non rompere il digiuno con il rumore di giorno.
- DIGIUNO: RANIERO: Le fornaci tornano a fumare. È il fumo più bello che si veda in città.

> Nota. La consegna anticipa la meccanica di Corrado (immune al taglio finché non è ustionato, Sez. 26A) e la battuta di Antonio in B-04 («Le lame no. Il fuoco sì»). Se la quest non è fatta, B-04 regge lo stesso.

---

## Q-SA01 · Le erbe del Bottaccione

**Monna Agnese** sta nell'orto a ridosso dell'abbazia di Sant'Andrea. Accanto a lei, su una stuoia, c'è un miliziano ferito.

### Proposta

- AGNESE: Gli alchimisti di Cagli stanno versando veleno nel fosso. I feriti di Porta Romana hanno le labbra viola.
- AGNESE: Le bende non bastano. Mi serve l'elleboro, quello che cresce solo sulle rocce umide del Bottaccione.
- AGNESE: Quattro radici. Senza, non supereranno la notte.
- UBALDO (preoccupato): Il Bottaccione è dietro il monte, Agnese. Dentro le loro linee.
- AGNESE: Lo so, monsignore. Per questo lo chiedo a voi e non a mio figlio.
- FERITO: ...acqua...
- OBIETTIVO: Raccogli 4 radici di elleboro nel Bottaccione.

### Strada del Bottaccione: le radici

Regia: quattro ciuffi di elleboro sulle rocce bagnate, ben visibili (fiore verde chiaro sulla pietra cupa). Uno è dentro una zona di miasmi, uno vicino agli archi di B-03. Si raccolgono anche se la quest non è stata presa: in quel caso il messaggio è diverso.

- SISTEMA: Hai raccolto una radice di elleboro.
- ANTONIO (calmo): Elleboro. Cura e veleno nella stessa radice: dipende da chi lo usa.

Se la quest non è attiva, alla prima radice:

- UBALDO (calmo): Prendiamolo. In città qualcuno saprà che farne.

### Consegna (contatore 4)

Si consegna in qualunque momento; di solito in fase NOTTE, dopo il rientro da Porta Metauro.

- AGNESE: Quattro radici! E sono ancora umide. Siete scesi davvero laggiù.
- AGNESE: Non me lo dite, cosa c'era. Me lo racconterete quando sarà finita.
- AGNESE: Prendete questi biscotti all'anice. Tolgono il veleno dal sangue, e la paura dallo stomaco.
- SISTEMA: Ricevi 3 Biscotti all'Anice di Sant'Ubaldo.
- SISTEMA: Sant'Andrea ti è grato.

Se la consegna avviene dopo `CONDOTTO_SALVO`, una battuta in più:

- AGNESE: E l'acqua stanotte è tornata chiara. Questo, monsignore, non l'ha fatto l'elleboro.

### Dopo

- NOTTE: FERITO: Agnese dice che ho sputato veleno verde. Io dico che ho sputato Cagli.
- NOTTE: AGNESE: Dormono. Tutti e sei. Domani si alzano, se Dio vuole e se l'alba è nostra.

---

## Q-SP01 · La rosa d'argento

**Fra' Bernardo** sta nel chiostro dell'abbazia di San Pietro. Il reliquiario non è in una cripta (non c'è un'area per le cripte nella v1): l'infiltrato è scappato con la Rosa e si nasconde in città, alle Logge dei Tiratori di Piazza Quaranta Martiri. Il giocatore lo trova raccogliendo tre indizi.

### Proposta

- FRA' BERNARDO: Hanno profanato l'altare, Vescovo Ubaldo! Ci hanno rubato la Rosa d'Argento.
- FRA' BERNARDO: Con quella benediciamo i miliziani prima della guardia notturna. Senza, gli uomini tremano davanti al Grifo.
- UBALDO (calmo): Chi è entrato, Bernardo?
- FRA' BERNARDO: Un pellegrino, diceva. Parlava come noi, ma pregava male. Ha preso la Rosa ed è sparito.
- UBALDO (deciso): Se è ancora in città, lo troveremo. Le porte sono chiuse anche per lui.
- OBIETTIVO: Trova chi ha rubato la Rosa d'Argento. Chiedi in giro.

### Gli indizi

Tre NPC già presenti hanno una battuta in più finché la quest è attiva. L'ordine è libero. Ogni indizio imposta la sua bandiera (`INDIZIO_LUCIA`, `INDIZIO_VENDITORE`, `INDIZIO_MENDICANTE`).

**Lucia la Tessitrice** (San Pietro):

- LUCIA: Un pellegrino? Ne ho visto uno uscire dal chiostro di corsa, con un sacco stretto al petto.
- LUCIA: È sceso verso la piazza del mercato. I pellegrini veri non corrono mai.

**Venditore delle Logge** (Piazza Quaranta Martiri):

- VENDITORE: Uno straniero mi ha comprato del pane ieri. Ha pagato con monete di Perugia, e mi ha detto di stare zitto.
- VENDITORE: Io sto zitto. Con voi, però, no.

**Mendicante** (Piazza Quaranta Martiri, sotto le Logge; compare solo con la quest attiva):

- MENDICANTE: Sotto le Logge dorme uno che non chiede mai l'elemosina. Strano mendicante, no?
- MENDICANTE: Di notte si alza e guarda verso il monte, come se aspettasse qualcuno.

Con i tre indizi, sotto le Logge compare l'infiltrato:

- SISTEMA: Sotto le Logge dei Tiratori c'è qualcuno che non dorme.

### L'infiltrato

Regia: un uomo avvolto in un mantello da pellegrino, la mano sotto il mantello. Battaglia: l'infiltrato e due spie umbre. Non si fugge.

- INFILTRATO: Il vescovo in persona. Dovevo immaginarlo: in questa città ficcate il naso dappertutto.
- GIORGIO (deciso): Ridacci la Rosa.
- INFILTRATO: Questa? Monaldo la vuole sul suo altare, a Perugia. Venite a prenderla.

Dopo la vittoria:

- INFILTRATO: Tenetevela, la vostra rosa. Tanto all'alba non ci sarà più nessuno da benedire.
- UBALDO (calmo): All'alba vedremo. Intanto ci sarà qualcuno a pregare per te.
- SISTEMA: Hai ripreso la Rosa d'Argento. Riportala a Fra' Bernardo.

### Consegna

- FRA' BERNARDO: La Rosa! Integra, grazie al cielo. E grazie a voi, che col cielo avete buoni rapporti.
- FRA' BERNARDO: Stanotte i miliziani avranno la loro benedizione. E voi la mia, che vale meno ma è di cuore.
- FRA' BERNARDO: Prendete questa crescia sotto la cenere. Chi la mangia, si rialza anche quando è caduto.
- SISTEMA: Ricevi 1 Crescia sotto la Cenere.
- SISTEMA: San Pietro ti è grato.

### Dopo

- NOTTE: FRA' BERNARDO: Ho benedetto le guardie una per una. Nessuna ha tremato.
- DIGIUNO: FRA' BERNARDO: La Rosa è tornata sull'altare. Il pellegrino, spero, in una cella.

> Nota. «Benedizione Porta Vittoria» della Sez. 31A è un effetto dell'Atto III: nella v1 resta solo come battuta. L'infiltrato richiede la stessa «spia umbra» degli Stradoni (vedi le battaglie nel README).
