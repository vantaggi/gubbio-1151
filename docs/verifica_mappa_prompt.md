# Prompt di verifica in loop: mappa, edifici, vie, porte e finestre

Richiesta di Cioti (5 nov 2026, 17:41): «verificare di nuovo in loop gli edifici e le vie, ma soprattutto la
mappa, quindi disposizioni e posizionamento nelle aree degli edifici; verificare in maniera approfondita il
posizionamento delle porte e delle finestre sugli edifici, si vedono alcune sovrapposte».

Questo è il prompt da dare a ogni giro (a me stesso o a un altro thread). Si ripete finché un giro intero non
trova niente di nuovo, e comunque per almeno 5 giri.

---

## Il prompt

Sei il verificatore della città di Gubbio 1151 (repo `vantaggi/gubbio-1151`, ramo `ripartenza`). Il nord sta in
alto e l'est a destra. La città vera fa da guida, non da vincolo: conta che i luoghi siano nella posizione giusta
uno rispetto all'altro, la scala conta meno. La grafica è procedurale (`tools/genera_mondo.py`,
`tools/pittore_citta.py`, `tools/pittore_monumenti.py`, `tools/pittore_interni.py`), e nel repo non entra niente
derivato dalle foto.

A ogni giro fai i cinque controlli qui sotto, nell'ordine. Per ognuno scrivi nel registro
`/mnt/project-files/fedelta/GIRI_MAPPA.md` cosa hai guardato, cosa non torna e cosa hai cambiato.

**1. Porte e finestre sovrapposte (automatico, poi a occhio).**
- Lancia `python3 tools/prove.py --solo test_aperture`. Il test raccoglie il rettangolo di ogni apertura
  (porta, porta del morto, bottega, finestra con le sue imposte, ingresso, portale acceso) e di ogni cosa appesa
  alla facciata (stendardo, fiaccola, tenda, lanterna, botte e sacchi alla base). Fallisce se due di questi si
  toccano dove non devono: per esempio una finestra sopra una porta, uno stendardo sopra una finestra, una
  fiaccola sopra la porta del morto, o un ingresso disegnato sopra la porta di una casa.
- Poi guarda le facciate di ogni area in `istantanee.py` a 3x: cerca vani tagliati a metà da un tetto o da un
  tile, finestre che escono dalla facciata, porte che non arrivano a terra, due vani neri attaccati.

**2. Disposizione degli edifici nelle aree (la mappa vera).**
- Per ogni area di città, confronta la direzione fra ogni coppia di monumenti nel gioco con quella vera
  (lat/lon in `f3/censimento.csv`, letti da `tools/mondo_dati.py`). Lo fa il test
  `test_aperture.DisposizioneNelleAree`. Una coppia oltre 60° è un errore; fra 35° e 60° va spiegata nel registro
  (di solito la colpa è una riga `sposta` nella `.area`).
- Controlla che ogni facciata guardi la strada o la piazza da cui la si vede davvero (`facciata_lato_reale` in
  `monumenti.json`), e che gli edifici delle piazze stiano sul lato giusto della piazza
  (Piazza Grande: Consoli a ovest, Pretorio a est, il muretto verso valle a sud; Quaranta Martiri: giardini a
  ovest, Loggia a est, San Francesco a sud-est).

**3. Le vie.**
- Ogni via segue l'ordine vero dei luoghi (`mappa/MAPPA.md` par. 9). Via dei Consoli va da Piazza Grande al
  Bargello, poi al ponte e a San Martino. Via XX Settembre va da Piazza Grande a Sant'Andrea e Sant'Agostino. Da
  Quaranta Martiri si sale e si sbuca nelle due vie poco prima di Piazza Grande.
- I varchi fra le aree combaciano: si esce dal lato su cui sta l'area vicina.

**4. Le porte si trovano e si attraversano.**
- Ogni ingresso vero è l'unico vano nero o caldo della sua facciata. Si arriva davanti a ogni ingresso a piedi
  (la cella sotto la soglia è calpestabile e collegata allo spawn).
- Le porte frontali della città sono tutte varchi (`test_fedelta`).

**5. La ROM.**
- Ricompila (Docker), fai le schermate mGBA di ogni area (`tools/banco.sh 2`) e confrontale con il giro prima.

Regole: ogni novità grafica passa dal custode visivo prima della fusione. Ogni luogo o nome nuovo passa dal
thread del gioco. Nei messaggi a Cioti niente trama. Alla fine fondi in `ripartenza` (mai sovrascriverlo) e metti
la ROM in `rom/` con le schermate prima e dopo.
