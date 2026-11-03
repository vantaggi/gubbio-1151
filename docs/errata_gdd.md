# Errata del GDD (regola R5)

Il GDD del prototipo (`GUBBIO_1151_LA_BIBBIA_GDD.md`) non è nel ramo `ripartenza`: sta su `main` e nel
tag `prototipo-v0`, e non si riscrive. Questo file elenca dove il GDD va letto diversamente, perché la
ripartenza ha deciso altro. **Quando GDD e questo file non concordano, vale questo file**; quando questo
file e il copione non concordano, vale il copione (`copione/README.md`).

Raccolto il 3 novembre 2026 dall'elenco «Correzioni da riportare nel GDD (regola R5)» e dalle «Decisioni
di trama» del README del copione, più le note del censimento dei simboli (`docs/simboli.md`). Le righe
citate sono quelle del GDD su `main` al commit `c62412d`.

Gravità: **rossa** = il GDD dice una cosa sbagliata che finirebbe nel gioco; **gialla** = da leggere in
un altro modo; **verde** = solo una segnalazione.

## In breve

| # | Tema | Dove nel GDD | Gravità |
| :-- | :-- | :-- | :-- |
| E1 | Araldica di Perugia: rossa, non purpurea | Sez. 7 Prologo | rossa |
| E2 | Stemma di Gubbio e colori dei quartieri | Sez. 8B, 9.1, 9.2 | rossa |
| E3 | Rientro dal Bottaccione: Porta Metauro | (solo `docs/mappa_del_mondo.md` del prototipo) | gialla |
| E4 | Camicie, fazzoletti e corporazioni dei Ceri fuori dal gioco | Sez. 7 Atto I Sc. 3, 8C, 9.3, 14C, 23, 31B, 32, 34B | rossa |
| E5 | Mastro Raniero: fornaci occupate da Spoleto, non da Cagli | Sez. 31A | rossa |
| E6 | «Console Guido», non «Podestà» | Sez. 7 Atto I Sc. 1, 8A, 31B, 31C | rossa |
| E7 | Tre albe, non «una seconda alba» | Sez. 11 Passo 6; Sez. 4 e 7 Atto IV | gialla |
| E8 | «Gubbio è salva» solo all'ultimo aggiornamento | Sez. 37B | gialla |
| E9 | Festa dei Ceri, maggio 1151, elenco delle undici città | testata, Sez. 3, 7, 8E, 11 Passo 1 | verde |

## E1 · Araldica di Perugia (rossa)

- **Sez. 7, Prologo (riga 187).** Ora: «Al centro, la bandiera purpurea del Grifo di Perugia domina la
  scena.» Leggi: «Al centro, il drappo di Perugia, rosso scuro col grifo d'argento coronato d'oro,
  domina la scena.»
- **Motivo.** Lo stemma di Perugia è «di rosso al grifone d'argento, coronato d'oro» (araldicacivica.it,
  in `docs/simboli.md`). Il gioco usa il confronto grifo bianco contro monte bianco, entrambi su rosso
  (copione P-02, A1-01, E-01).
- La Sez. 8D n. 3 («scudi recanti il Grifo d'Argento rampante») è già coerente.

## E2 · Stemma di Gubbio e quartieri (rossa)

- **Sez. 9.1.** Il nucleo (rosso, monte d'argento a cinque cime) è giusto; «alla tedesca» e «capo
  d'Angiò» non hanno fonte. **Nel gioco**: rosso + monte bianco a cinque cime, **senza lambello né
  gigli** (la brisura angioina è posteriore al 1266).
- **Sez. 8B.** Colori e figure dei quartieri sono sbagliati. Valgono le figure della Sez. 9.2 (corona,
  palme, falcone, rosa) e i colori del Torneo: **blu San Martino, rosso Sant'Andrea, ocra San Giuliano,
  verde San Pietro**, come fascia sul drappo rosso e argento.
- **Sez. 9.2**, colonna dei colori: «tutti in campo rosso» resta per il drappo; il colore del quartiere
  è la fascia.
- Dettagli e fonti: `docs/simboli.md`.

## E3 · Porta Metauro (gialla)

- Il GDD **non** nomina la «Porta di Santa Lucia»: il nome era solo nel `docs/mappa_del_mondo.md` del
  prototipo, già corretto nella ripartenza. La Sez. 8A elenca «Porta Metauro / Marmorea» verso la
  Flaminia, ed è giusta.
- **Leggi**: il rientro in città dal Bottaccione è **Porta Metauro** (confermato da Cioti, 1 nov 2026),
  da lì San Martino, Bargello, via dei Consoli. È la porta che Corrado vuole aprire da dentro (copione
  A1-09).

## E4 · I Ceri: niente camicie, fazzoletti né corporazioni (rossa)

Decisione di Cioti (1 nov 2026): camicie gialla, azzurra e nera, fazzoletti e fasce rosse e corporazioni
sono della festa di oggi e dei ceraioli, non dei personaggi. Nel 1151 la festa non c'è (nasce dopo la
morte di Ubaldo, 1160). I tre si riconoscono per attributi: **Ubaldo mitra e verga (pastorale),
Giorgio armatura e lancia (e scudo), Antonio saio e fuoco**. I Tre Ceri restano come forza mistica.

| Dove | Ora | Leggi |
| :-- | :-- | :-- |
| Sez. 7 Atto I Sc. 3 (r. 205) | «la Lancia Radiante del Cero dei Muratori», «custode del Cero della Terra» | «la Lancia Radiante del Cero di San Giorgio», «custode del Cero di Sant'Antonio»: nessuna corporazione |
| Sez. 8C.1 (r. 315-318) | Camicia, fazzoletto, pantaloni e corporazione per ciascun santo | Solo il simbolo: mitra (Ubaldo), lancia e scudo (Giorgio, non «elmo e spada»), fiamma (Antonio; il porcellino è iconografia comune, facoltativo) |
| Sez. 8C.2 (r. 321-323) | Brocche «Mastro Giorgio» | Mastro Giorgio è del Cinquecento: la brocca, se resta, è senza quel nome |
| Sez. 8C.2 (r. 330-331) | Accessorio «Fazzoletto Ceraiolo» | Non entra nel gioco (non c'è un sostituto deciso) |
| Sez. 9.3 (r. 385-389) | Colori e corporazioni della festa | Informazione vera ma fuori dal gioco, nemmeno come codice dell'interfaccia |
| Sez. 14C (r. 955-957) | Palette OBJ: «giallo ocra» Ubaldo, «azzurro cavaliere … rosso fazzoletto» Giorgio, «nero saio» Antonio | Le palette vengono dalla Guida di stile (palette bloccata), non dai colori delle camicie |
| Sez. 23 (r. 1702) | `VICTORY_CHEER`: «sollevamento del fazzoletto ceraiolo» | Gesto di vittoria con l'attributo (pastorale, lancia, fuoco) |
| Sez. 31B NPC 2 (r. 2211) | «Eccoti la patente, ceraiolo!» | Senza «ceraiolo» |
| Sez. 31B NPC 8 (r. 2255-2259) | «Lucia la Tessitrice dei Ceri», fazzoletto al collo di Giorgio | Lucia è una tessitrice; nel copione cuce «uno stendardo nuovo: rosso, col monte bianco» |
| Sez. 32B (r. 2349) | Splash: «I Tre Ceri che brillano in sequenza (Giallo, Azzurro, Nero)» | Tre ceri accesi, senza il codice dei tre colori |
| Sez. 34B (r. 2406-2407) | «Inno dei Ceri», brocca spezzata | Musica originale del gioco; nessun inno della festa |

Eccezioni: l'abilità **«Bastione Azzurro»** (Sez. 2, 12A) tiene il nome, perché l'azzurro lì è dello
scudo, non di una camicia. I ceri compaiono come oggetti **solo dentro la Basilica** (decisione del
censimento dei simboli).

## E5 · Mastro Raniero e Spoleto (rossa)

- **Sez. 31A, Q-SM01 (r. 2182).** Ora: «Recuperare 3 blocchi di ferro fuso dalle fornaci occupate da
  Cagli.» Leggi: «… dalle fornaci occupate da **Spoleto**» (nel copione: al Teatro Romano).
- **Motivo.** Il dialogo della Sez. 31B (r. 2221) dice già «Le truppe di Spoleto hanno bloccato i
  carichi»: la tabella si contraddiceva. Spoleto lega la quest a Corrado, e Raniero spiega come si apre
  il ferro di Spoleto (copione `04_quest.md`).

## E6 · «Console Guido», non «Podestà» (rossa)

Nel 1151 Gubbio era governata da consoli (il palazzo ne porta il nome); il podestà è un'istituzione più
tarda. Il parlante resta GUIDO.

| Dove | Ora | Leggi |
| :-- | :-- | :-- |
| Sez. 7 Atto I Sc. 1 (r. 196) | «Il Podestà e i capitani delle milizie» | «Il console Guido e i capitani delle milizie» |
| Sez. 8A (r. 292) | Palazzo dei Consoli «sede del Podestà e dei Consoli di Giustizia» | «sede dei Consoli» |
| Sez. 31B NPC 1 (r. 2194-2203) | «Il Podestà Guido da Gubbio», «PODESTÀ GUIDO» | «Il console Guido», parlante GUIDO |
| Sez. 31C (r. 2309-2312) | `"Podestà Guido"` in `NPC_DATABASE` | Esempio del prototipo, superato da `include/storia.h` generato dal copione |

Il nome del **Palazzo Pretorio (del Podestà)** in `mondo/` resta: è il nome dell'edificio, del
Trecento, non una carica del 1151.

## E7 · Tre albe (gialla)

- **Sez. 11 Passo 6, BOX 1 (r. 528).** Ora: «Monaldo non concederà una seconda alba.» Leggi:
  l'araldo dà **tre albe** («Avete tre albe. Alla terza, se le porte saranno ancora chiuse, non resterà
  pietra su pietra», copione A1-01). Così il digiuno di tre giorni ha una scadenza e l'epilogo della v1
  cade alla terza alba.
- **Sez. 4 Atto IV (r. 122)** «All'alba del terzo giorno» e **Sez. 7 Atto IV Sc. 1 (r. 244)** «All'alba
  del terzo giorno dopo la visione»: la sortita non è la terza alba dell'ultimatum. Leggi «all'alba del
  terzo giorno **d'assedio**».

## E8 · Il finale della v1 (gialla)

- **Sez. 37B punto 4 (r. 2486).** «GUBBIO È SALVA. ANNO DOMINI 1151.» resta, ma solo all'**ultimo
  aggiornamento**, quando l'assedio finisce. La v1 lascia l'assedio aperto e chiude con «Fine del primo
  atto. La cronaca continua.» (copione E-01).

## E9 · Da segnalare, senza cambiare (verde)

- **Festa dei Ceri e data.** Per tradizione la festa ricorda la vittoria del 1151 (Key to Umbria). Nel
  gioco i Tre Ceri sono una forza mistica, non la festa: il copione non nomina la festa né il 15 maggio.
  Il GDD fissa «maggio 1151» (testata, Sez. 7 Prologo, 11 Passo 1) e lega il Baccalà al 15 maggio
  (Sez. 8E): le fonti non danno il mese, quindi nei testi del gioco il mese non si dice.
- **Le undici città** sono quelle della Sez. 3 (Perugia, Spoleto, Cagli, Foligno, Todi, Nocera, Gualdo
  Tadino, Fossato, Assisi, Bettona, Spello); le fonti storiche non concordano tutte. Va bene per il
  gioco, ed è segnata come scelta.
