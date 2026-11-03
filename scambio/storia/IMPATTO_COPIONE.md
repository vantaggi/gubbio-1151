# Impatto della storia v2 sul copione v1

Parte della [Bibbia della storia v2](BIBBIA_STORIA.md). Versione del 3 novembre 2026. **Niente qui è già stato cambiato**: le battute si riscrivono in un secondo passo, dopo che Cioti ha visto la Bibbia.

Colori:

- **VERDE**: si aggiunge senza toccare niente di approvato (battute nuove, varianti con bandiere nuove).
- **GIALLO**: cambia battute già approvate o una scena già giocabile, senza toccare cutscene o decisioni.
- **ROSSO**: tocca una cutscene (C1-C4) o una decisione approvata. Per ognuno dico perché ne vale la pena.

Stato nel gioco (dal thread del gioco, 3 nov): P-, A1-, B-, E- già giocabili; cutscene C1-C4 fatte; le 3 quest solo dati, ferme in attesa di questa Bibbia.

## Riepilogo

| Colore | Quante | Dove |
| :-- | --: | :-- |
| ROSSO | 3 | C1 (una frase del narratore), C4 con E-01 (una scelta prima della cutscene), decisione n. 3 (la vetrata conferma invece di rivelare) |
| GIALLO | 9 | A1-01, A1-05, A1-09, B-03, B-04, B-05, E-01, Q-SP01, meccanica del digiuno di Ubaldo |
| VERDE | il resto | amici, indizi, varianti NPC, Q-SA01, Q-SM01 |

---

## Prologo

| Scena | Cosa cambia | Colore |
| :-- | :-- | :-- |
| P-00 | niente | — |
| P-01 | niente | — |
| P-02 / **C1** | Una sola frase del narratore: «Nel maggio del 1151, l'invidia e la sete di dominio spezzarono la pace dei colli» diventa **«Nel 1151, vecchi torti e nuove ambizioni spezzarono la pace dei colli.»** Il resto (l'elenco delle città, «Sorse il fuoco della Fede») resta. Tolgo anche «maggio» perché la data è solo tradizionale (Biscarini) | **ROSSO** |

Perché ne vale la pena: è la frase che dice al giocatore chi ha ragione prima di cominciare. Con «invidia» la coalizione è cattiva per definizione e tutta la v2 la smentisce. Costo: una riga di testo nella cutscene, nessuna immagine.

---

## Atto I

| Scena | Cosa cambia | Colore |
| :-- | :-- | :-- |
| A1-01 | Dopo «Avete tre albe...» l'araldo aggiunge una riga: **«E Monaldo parla anche per chi avete cacciato dalle vostre torri.»** Seme di S1 e S6. Più una battuta di Guido che conta i mesi del grano «senza il borgo». C2 e C3 non si toccano: le righe sono nella vista di gioco | GIALLO |
| A1-02 | niente | — |
| A1-03 | niente. Variante VERDE: se il giocatore ha parlato con Giamma, Cecco aggiunge «Quello di San Pietro ti ha detto che tira meglio? Bugia.» | VERDE |
| A1-04 | niente nelle battute. Taglio proposto: le 3 righe SISTEMA del tutorial diventano 2 (per il conto delle battute) | GIALLO leggero, facoltativo |
| A1-05 | Dopo «Sprangate le porte» niente cambia; all'uscita verso Sant'Andrea parte **D1** con Endriu, Fagia e Guido (scena nuova A1-05b). Guido in A1-05 aggiunge una riga: «E il borgo di Sant'Agostino, monsignore?» Ubaldo risponde secondo la scelta | GIALLO (una battuta in A1-05) + VERDE (A1-05b) |
| A1-06 | niente: le battute del canonico sono già i semi di S3. Il parlante resta CANONICO; il nome Ilario arriva nell'Atto II | — |
| A1-07 | niente. La spia resta com'è: «qualcuno sta già bevendo la vostra acqua» è il quarto indizio di S2 | — |
| A1-08 | niente nelle battute. Taglio proposto: le 3 righe SISTEMA del tutorial degli Spettri diventano 2 | GIALLO leggero, facoltativo |
| A1-09 | Prima che il vetro si muova, se il giocatore ha almeno 2 bandiere fra `INDIZIO_CARTA`, `INDIZIO_ACQUA`, `INDIZIO_ROCCIA`, Ubaldo dice: **«La carta che manca, l'acqua che cala, la pietra che non regge...»** e Antonio: «...e la spia che rideva dell'acqua. È il condotto.» Poi la visione **conferma**. Con meno di 2 indizi la scena resta com'è | GIALLO (scena) + **ROSSO** (decisione n. 3) |

Perché il ROSSO di A1-09 ne vale la pena: la decisione approvata n. 3 dice che il motivo per scendere nel Bottaccione è la visione. Resta vero per chi non indaga; per chi indaga la visione diventa la prova di ciò che ha capito. È il punto debole n. 3 della diagnosi («informazioni per rivelazione») ed è il cambiamento che chi gioca sente di più. Costo: 3 battute e 3 bandiere, nessuna cutscene.

---

## Bottaccione ed epilogo

| Scena | Cosa cambia | Colore |
| :-- | :-- | :-- |
| B-01 | Variante VERDE: se `INDIZIO_ROCCIA`, Giorgio non dice «Berto dice un sacco di cose» ma **«Giambono diceva lo stesso. Due che dicono la stessa cosa...»**, e la striscia nera mostra un varco scavato (S13) | VERDE |
| B-02 | Taglio proposto se i miasmi saltano (era già condizionale) | — |
| B-03 | Il secondo guerriero diventa **il ragazzo eugubino**: una battuta cambia («E la guida? Il signore di Valmarcola dice che conosce ogni pietra»). Con `RICCA_ASCOLTATA` Ubaldo riconosce l'accento: «Quel ragazzo parla come noi.» Poi **D2** | GIALLO |
| B-04 | Corrado sconfitto, prima di buttarsi, aggiunge: **«Chiedete ai vostri esuli chi mi ha mostrato la strada.»** È il colpo di scena della v1. Con Q-SM01 fatta o Fino ascoltato, Corrado entra con uno scudo in meno (meccanica). C3 (presentazione di Corrado) invariata | GIALLO |
| B-05 | Due varianti di Nello e Massi al rientro; con `ESULE_PRIGIONIERO`, due battute di folla in San Martino che Ubaldo calma | GIALLO (aggiunte nella scena) |
| E-01 / **C4** | Dopo «Le tre albe sono passate, vescovo. Le chiavi.», **nella vista di gioco e prima di C4**, parte **D4**: «Offri giustizia / Le chiavi restano dove sono». Con l'offerta: Ubaldo offre riparazione ai Valmarcola e un giudizio giusto sulle terre; l'araldo: «Monaldo non vende la vittoria.» Senza: come oggi, più la riga dell'araldo sulla lettera di Guido e quella di Antonio. Poi C4 parte uguale per tutti | **ROSSO** |
| E-02 | niente | — |

Perché il ROSSO di E-01 ne vale la pena: è la risposta alla domanda drammatica e l'unico momento in cui Ubaldo paga un prezzo scelto dal giocatore. Viene dalle fonti (Ubaldo offrì giustizia, riparazione e un patto, tutti rifiutati: Biscarini, da Giordano e Tebaldo). Costo: la cutscene C4 non cambia, ma deve partire **dopo** la scelta e non dentro (regola 6 delle cutscene: niente pulsanti); servono 4-6 battute nuove e una bandiera.

Nota per il thread del gioco: le battute di E-01 oggi stanno prima e dentro C4? Se il dialogo dell'araldo è dentro le bande, la scelta va spostata prima delle bande: è l'unica cosa da verificare sul gioco.

---

## NPC d'ambiente (03_npc_ambiente.md)

| NPC | Cosa cambia | Colore |
| :-- | :-- | :-- |
| Guido | variante NOTTE con `BORGO_DENTRO`: «Settanta bocche in più. Ho rifatto i conti tre volte.» | VERDE |
| Berto | DIGIUNO, una battuta in più: «La crepa la conosceva solo chi l'ha costruita.» (S2) | VERDE |
| Popolana | D3 in DIGIUNO (dai o tieni la Crescia); NOTTE diversa con `PANE_DATO` | VERDE |
| Merciaio | taglio proposto: resta solo ULTIMATUM | GIALLO leggero, facoltativo |
| Tano | taglio proposto: DIGIUNO da 2 battute a 1 | GIALLO leggero, facoltativo |
| Cecco | variante con Giamma (sopra) | VERDE |
| Lavandaia | niente: è già l'indizio di S4 | — |
| Venditore | con `BORGO_DENTRO` ha 1 Crescia in meno; una battuta: «Il borgo mangia anche lui.» | VERDE |
| Fra' Matteo | taglio proposto: da 3 battute a 2 | GIALLO leggero, facoltativo |
| Lucia | niente | — |
| Vecchio (via XX Settembre) | DIGIUNO, una battuta in più: «Dieci anni fa le torri dei Valmarcola. Ora tornano, lo sento.» (S1) | VERDE |
| Frate agostiniano | NOTTE diversa con `BORGO_FUORI` | VERDE |
| Sentinella di Porta Romana | niente; Endriu sta fuori | — |
| Canonico | niente: le battute sono già semi (S3) | — |
| Spia in sacrestia | niente | — |
| **Amici** | 15 NPC nuovi con 3 fasi ciascuno: vedi [NPC_AMICI.md](NPC_AMICI.md) | VERDE |

---

## Quest (04_quest.md)

| Quest | Cosa cambia | Colore |
| :-- | :-- | :-- |
| Q-SM01 Ferro | niente nelle battute. La consegna (o una battuta di Fino) toglie uno scudo a Corrado | VERDE (meccanica nuova) |
| Q-SA01 Erbe | una battuta in più di Agnese alla proposta: «Gabrione dice che è veratro. Lui lo riconosce, io lo curo.» Gabrielone in San Pietro spiega il veleno (S4) | VERDE |
| Q-SP01 Rosa | Il **mendicante** è sostituito da **Giordy** (stesso luogo, stesso contenuto: l'uomo sotto le Logge che guarda il monte). L'**infiltrato** diventa un servo dei Valmarcola: una battuta cambia («Questa città mi ha cacciato una volta. Monaldo la Rosa la rivuole indietro.»). Alla consegna Fra' Bernardo dice che la Rosa fu un dono di Perugia (S12) | GIALLO |

---

## Meccaniche e bandiere

| Cosa | Colore |
| :-- | :-- |
| **Ubaldo non usa il cibo** dalla fase DIGIUNO a B-05 (5.12). Tocca il menu oggetti in battaglia | GIALLO |
| Corrado con uno scudo in meno se Q-SM01 o Fino | VERDE |
| Bandiere nuove, storia (0-63): `BORGO_DENTRO`, `BORGO_FUORI`, `ESULE_PRIGIONIERO`, `ESULE_LIBERATO`, `GIUSTIZIA_OFFERTA` | VERDE |
| Bandiere nuove, quest e indizi (64-127): `INDIZIO_CARTA`, `INDIZIO_ACQUA`, `INDIZIO_ROCCIA`, `RICCA_ASCOLTATA`, `FINO_ASCOLTATO`, `PANE_DATO`, `GIAMMA_ASCOLTATO` | VERDE |
| Le scelte con conseguenza sono 4 (D1-D4), il massimo previsto. «Sì, è ora / Non ancora» di B-05 resta e non conta | — |

## Per il thread del gioco

1. **Figure degli NPC nuovi**: per ogni amico la figura di partenza (una delle 5: popolana, frate, soldato, mercante, anziano) e l'accessorio sono nelle schede di [NPC_AMICI.md](NPC_AMICI.md). Una sola figura davvero nuova: **Gabrielone** (una testa più alta, pelata). Ragno usa il soldato senza elmo, a braccia nude.
2. **Edifici nuovi**: 6 (casa del medico a San Martino, mulino a Quaranta Martiri, spezieria con ospizio e taverna del corso a San Pietro, bottega dei conti e dei congegni e calcara a Sant'Agostino). Aggiunte del 3 nov sera: sei compagne (figura popolana più accessorio), Nicolò (figura nuova: bambino) e Padeletto l'oste (mercante con fiasco), tutte in NPC_AMICI.md.
3. **Cosa rompe scene già giocabili**: solo i tre ROSSI (C1 una frase, C4 la scelta prima, A1-09 la conferma) e i GIALLI di A1-01, A1-05, B-03, B-04, B-05, E-01. Le quest possono ripartire dalle schede, con la sola sostituzione del mendicante in Q-SP01.
4. **Battute**: tutte quelle d'esempio sono scritte per 2 righe da 224 px, con gli accenti veri.
