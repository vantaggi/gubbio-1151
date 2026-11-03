# F3, censimento fonti e misure dei monumenti

> Copiato dal censimento F3 del 1 nov 2026. Il CSV dei monumenti è `mondo/fonti/censimento_osm.csv`; l'elenco delle foto di riferimento resta fuori dal repo di proposito.


Stato al 1 novembre 2026. Fonte di verità della disposizione: `docs/mappa_del_mondo.md` (vince sul GDD).


## Riepilogo finale (dopo il terzo giro sul PC, 1 nov 2026)

**Risultato.** 33 monumenti nelle 14 aree. `censimento.csv` contiene le misure OSM di 29 monumenti,
`foto.csv` 183 foto con autore, URL e licenza (93 usabili, 90 solo consultazione; massimo 12 per
monumento). Nessuna immagine è stata scaricata. I file dei giri precedenti sono `*_giro1.csv` e `giro2/`.

**Cosa ho deciso io sui risultati del terzo giro** (APPROVATO da Cioti il 1 nov 2026, con il principio: è un gioco, la fedeltà guida ma le scelte stilistiche nostre sono ammesse):

1. *Facciate di Piazza Quaranta Martiri: valgono i giri 1 e 2, non il 3.* San Francesco, Loggia dei
   Tiratori e Santa Maria dei Laici stanno in fila sul lato ovest della piazza (coordinate OSM), quindi
   guardano a est o sud-est: 111°, 147°, 148°. Nel terzo giro il nuovo filtro scartava i parcheggi
   anche quando cercava la piazza di riferimento, e Piazza Quaranta Martiri in OSM è proprio un
   parcheggio: il riferimento è finito altrove e le facciate si sono girate. Script corretto.
   Esito: **San Francesco frontale**, Loggia e Laici sul lato sinistro, al limite del frontale.
2. *Fontana dei Matti = "Fontana di San Giuliano" di OSM* (nodo a 11 m dal Bargello). È davanti al
   Bargello, dove dice Cioti, e Porta San Giuliano è lì accanto: lo stesso oggetto con un altro nome
   in OSM. Misura: resta 4,5 m (OSM ha solo un punto).
3. *Ponte di San Martino = tratto di via del Camignano lungo 13,7 m* (circa 9 tile). Accettato.
4. *Porta di Sant'Ubaldo*: uso la sagoma del primo giro (way/1515710955, 8,6 x 8,0 m); il nome in OSM
   ha un apostrofo diverso, filtro corretto per il futuro.
5. *Basilica di Sant'Ubaldo*: OSM dà 70 x 45 m, ma è la relation dell'intero complesso (con il
   convento). Per la chiesa resta il 50 x 22 m del GDD finché una foto o la pianta non dice altro.
6. *San Pietro*: 46 x 23 m (OSM, way/237753058).

**Facciate frontali in gioco (rivolte a est):** Palazzo dei Consoli, Bargello, San Francesco.
Il Pretorio guarda a ovest e si vede da dietro (deciso da Cioti).

**Punti aperti per Cioti** (nessuno blocca F1):
- Rivedere le decisioni qui sopra e quelle in "Decisioni prese in autonomia" (misure: vince OSM).
- Fronte del Consoli: 33 m (GDD) o 40 m (OSM)? Si chiude contando le campate su una foto frontale.
- Nove monumenti non hanno foto libere: si disegnano in procedurale (elenco più sotto).
- ~~`docs/mappa_del_mondo.md` va corretto nella nuova storia: Porta Metauro al posto di Porta di Santa Lucia.~~
  **FATTO** (F2, 1 nov 2026; verificato il 3 nov 2026 con le correzioni R5): il contratto del mondo dice Porta Metauro e nessun nome in gioco usa più «Santa Lucia».

## Cosa c'è in questa cartella

| File | Cosa contiene |
| :-- | :-- |
| `monumenti.json` | I 33 monumenti delle 14 aree, con ruolo, datazione, misure già note **con la loro fonte**, segni distintivi, nome OSM e categorie Commons da interrogare. È l'ingresso dello script. |
| `censimento_preliminare.csv` | Lo stesso elenco in tabella, senza i dati di Commons e OSM. |
| `censisci.py` | Script da lanciare sul PC: riempie autore, URL, licenza delle foto e misura sagome e orientamento delle facciate da OpenStreetMap. Scrive `censimento.csv/.json` e `foto.csv/.json`. |
| `FONTI_dal_PC.md` | Sintesi del FONTI.md del prototipo (punto di partenza). |

## Perché manca ancora la parte "foto"

Da questa macchina cloud **Wikimedia Commons, Wikidata e OpenStreetMap sono bloccati** dalla rete
(provato via API e via pagina: sempre rifiutati). Wikipedia si legge, Commons no. Inventare autore e
licenza delle foto a memoria non è accettabile per un registro crediti, quindi la parte foto e la
misura delle sagome sono affidate a `censisci.py`, che va lanciato dove la rete è libera:

```
cd <cartella f3>
python censisci.py --prova     # verifica offline: deve stampare "prova ok"
python censisci.py             # 33 monumenti, qualche minuto (rispetta i limiti di Commons e Overpass)
```

Lo script scarica **solo metadati**, mai immagini. Nessun pixel entra nel repo (scelta 7 della guida di stile).

## Regole applicate

- **Licenze.** `usabile` = CC0, pubblico dominio, CC BY senza SA. `solo_consultazione` = CC BY-SA e
  GFDL: si guardano ma non se ne deriva nulla. `esclusa` = tutto il resto (NC, ND, nessuna licenza).
  Le foto del web del vecchio `riferimenti/` restano fuori.
- **Orientamento.** La mappa è ruotata: alto schermo = ovest reale. Una facciata si vede di fronte
  solo se la sua normale punta a **est** (fra 45 e 135 gradi). Sud = lato sinistro, nord = lato destro,
  ovest = retro, si vede solo il tetto. Lo script calcola la normale della facciata come il lato del
  rettangolo minimo della sagoma OSM rivolto verso `fronte_verso` (la piazza o la via su cui guarda), e
  scrive la colonna `facciata_in_gioco`.
- **Foto frontali.** Se una foto ha le coordinate della fotocamera, lo script calcola da che direzione è
  stata scattata e la marca `frontale_alla_facciata = si` entro 35 gradi dalla normale. Le foto sono
  ordinate: usabili e frontali prima.
- **Misure.** Fronte e profondità vengono da OSM (in metri, ±1 m circa); altezza e piani da OSM se
  taggati, altrimenti dalle fonti scritte. Le misure del GDD (Consoli 33x60, Pretorio 25x30, Fontana
  4,5 m, Basilica 50x22, Teatro 70 m, Piazza 130x40) vanno **confrontate** con OSM: se divergono oltre un
  tile e mezzo, decide Cioti quale tenere.
- Dati OSM: © contributori OpenStreetMap, ODbL. Usati solo per misurare; vanno nei crediti.

## Misure trovate finora (con fonte)

| Monumento | Dato | Fonte |
| :-- | :-- | :-- |
| Palazzo dei Consoli | 60 m dal piano stradale sul lato sud alla cima del campanile | it.wikipedia, Palazzo dei Consoli |
| Palazzo dei Consoli | facciata sulla piazza: in alto 6 finestre a tutto sesto a coppie fra lesene, in basso portale gotico fra 2 bifore; pianta rettangolare | it.wikipedia |
| Palazzo dei Consoli | 5 piani (museo); 1332-1349 | palazzodeiconsoli.it, it.wikipedia |
| Palazzo dei Consoli, Pretorio, Fontana, Basilica, Teatro, Piazza | misure in pianta del prototipo | `include/city_reference.h` (Sez. 23 GDD) |
| Duomo | portale a sesto acuto con rosone sopra; completato 1229, ampliato 1336 | it.wikipedia, Duomo di Gubbio |
| Basilica di Sant'Ubaldo | larga scalinata e portale; quota 803 m | it.wikipedia |
| Teatro romano | 55-27 a.C., fino a 6.000 spettatori | it.wikipedia, Gubbio |
| Sant'Agostino | facciata settecentesca, interno su 8 grandi archi | touringclub.it |

Nessuna fonte consultata dice verso dove guarda una facciata: l'orientamento arriverà solo da OSM.

## Da confermare con Cioti (conoscenza locale)

1. ~~Porta di Santa Lucia~~ **RISOLTO (Cioti, 1 nov 2026): è Porta Metauro** (o di Santa Croce, l'unica
   con le ante di legno originali). Nel censimento la voce è `porta_metauro`. `docs/mappa_del_mondo.md`
   e i nomi in gioco sono stati corretti nella nuova storia (3 nov 2026: nessuna «Porta di Santa Lucia»
   resta in `mondo/`, `include/`, `src/`, `regia/`, `testi/`).
2. ~~San Martino~~ **RISOLTO (Cioti, 1 nov 2026): l'edificio di riferimento è la chiesa di San Domenico.**
3. ~~Sant'Andrea~~ **RISOLTO (Cioti, 1 nov 2026): la chiesa di riferimento è San Marziale (in origine Sant'Andrea).**
4. ~~Via dei Consoli e via XX Settembre~~ **RISOLTO (Cioti, 1 nov 2026):** su via dei Consoli si riconoscono il
   Bargello con la Fontana dei Matti e il ponte sul Camignano verso San Martino (aggiunto come `ponte_san_martino`); fra via dei Consoli e via XX Settembre, su Piazza Grande, Palazzo Ranghiasci
   (promosso a canonico).
5. ~~Datazioni~~ **RISOLTO:** collocazioni confermate da Cioti; Fontana dei Matti XVI sec. rifatta nel XIX,
   sormontata dai cinque monti e un giglio (italia.it); Loggia dei Tiratori 1326, tiratoio inizio XVII
   (museionline.info); Bargello c. 1302 (en.wikipedia). Resta senza data solo l'Eremo di Sant'Ambrogio (sfondo).
   Cioti (1 nov 2026): anche se posteriori al 1151, questi edifici iconici restano (conferma la decisione sugli anacronismi).
6. ~~Nome del ponte~~ **RISOLTO (Cioti, 1 nov 2026): Ponte di San Martino**, a pochi metri dal Bargello (`ponte_san_martino`).

## Confronto GDD / OpenStreetMap (primo giro sul PC, 1 nov 2026)

Misure in metri; tra parentesi i tile a 1,5 m. "OSM" = rettangolo minimo della sagoma OSM.

| Monumento | GDD (prototipo) | OSM | Lettura |
| :-- | :-- | :-- | :-- |
| Palazzo dei Consoli | fronte 33 (22) x prof. 60 (40) | lato sulla piazza 39,6 (26) x 34,5 (23) | La profondità 60 del GDD coincide con l'**altezza** di 60 m data da it.wikipedia: quasi certamente uno scambio. Il fronte va controllato su una foto frontale (contare le campate): 33 o 40. |
| Palazzo Pretorio | 25 (17) x 30 (20) | 40,5 (27) x 30,4 (20) | Profondità uguale. Il fronte OSM può includere un edificio attaccato: da controllare su foto. |
| Piazza Grande | 130 x 40 | 75,9 x 40,0 | Larghezza uguale. La sagoma OSM della piazza è probabilmente solo la parte pedonale: il 130 resta plausibile, e comunque le distanze si comprimono. |
| Teatro romano | 70 x 70 | 69,9 x 38,7 | Il diametro torna (70). 38,7 è la profondità del semicerchio, non un quadrato: la cavea occupa 47 x 26 tile, non 46 x 46. |
| Basilica di Sant'Ubaldo | 50 x 22 | (OSM sbagliato al primo giro) | Si rifà col secondo giro. |
| Bargello | (non nel GDD) | 15,7 (10) x 9,6 (6), facciata a est | Stretto e alto, come ricordato. |

### Facciate: cosa si vede di fronte nella mappa ruotata

| Monumento | Normale della facciata principale | In gioco |
| :-- | --: | :-- |
| Palazzo dei Consoli | 123 (est-sud-est) | **frontale** |
| Palazzo del Bargello | 104 (est) | **frontale** |
| San Francesco | 111 (est) | **frontale** |
| Santa Maria dei Laici | 148 (sud-est) | lato sinistro, quasi frontale |
| Palazzo Ranghiasci | 212 (sud-ovest) | lato sinistro |
| Palazzo Pretorio | 300 (ovest-nord-ovest) | **retro: si vedrebbe solo il tetto** |

Il Pretorio e il Consoli si fronteggiano sulla piazza: se uno guarda a est, l'altro per forza guarda a
ovest. Con la vista scelta (FS scelta 2) la facciata del Pretorio verso la piazza finisce sul lato alto,
nascosta dal tetto. **DECISO (Cioti, 1 nov 2026): fedele.** In mappa il Pretorio si vede da dietro (tetto e retro); la facciata compare solo in primo piano o entrando. Nessuna eccezione alla regola della mappa ruotata.

## Decisioni prese in autonomia (1 nov 2026, Cioti assente; da rivedere)

1. **Misure in pianta: vince OSM, salvo verifica su foto frontale.** OSM è l'unica misura rilevata; le
   cifre del GDD non hanno fonte. Valori da usare in F1/F2:
   - Palazzo dei Consoli: fronte sulla piazza 40 m (26 tile) x profondità 35 m (23 tile). Il "60 m" del
     GDD è l'altezza (it.wikipedia), non la profondità: l'altezza resta 60 m, compressa col fattore unico
     della scelta 6.
   - Palazzo Pretorio: 40 x 30 m (27 x 20 tile). Se una foto frontale mostra che la sagoma OSM include un
     edificio attaccato, si torna a 25 m di fronte.
   - Teatro romano: semicerchio di 70 m di diametro e 39 m di profondità (47 x 26 tile), non un quadrato.
   - Piazza Grande: resta 130 x 40 m (le distanze si comprimono comunque; la sagoma OSM è solo una parte).
   - Loggia dei Tiratori: 65 x 18,5 m (43 x 12 tile), facciata a sud, lato sinistro.
   Reversibile: basta cambiare i numeri qui e in `include/city_reference.h` della nuova storia.
2. **Foto trovate per testo:** tenute solo se sono immagini e nominano Gubbio (lo script ora le filtra).
   Restano valide solo le colonne `uso = usabile` per derivare qualcosa; `solo_consultazione` solo per guardare.
3. **Monumenti senza nessuna foto libera** (Porta San Giuliano, San Marziale, Arco di San Marziale,
   Palazzo dei Canonici, Porta di Sant'Ubaldo, mura e Rocca, Gola, acquedotto): si disegnano in
   procedurale dalle descrizioni e dalle misure OSM, come da guida di stile.

## Fonti consultate

- [it.wikipedia, Palazzo dei Consoli](https://it.wikipedia.org/wiki/Palazzo_dei_Consoli)
- [it.wikipedia, Duomo di Gubbio](https://it.wikipedia.org/wiki/Duomo_di_Gubbio)
- [it.wikipedia, Basilica di Sant'Ubaldo](https://it.wikipedia.org/wiki/Basilica_di_Sant%27Ubaldo)
- [en.wikipedia, San Domenico (Gubbio)](https://en.wikipedia.org/wiki/San_Domenico,_Gubbio)
- [Key to Umbria, monumenti di Gubbio](https://keytoumbria.com/Gubbio/Monuments.html) e [porte](https://www.keytoumbria.com/Gubbio/City_Gates.html)
- [Palazzo dei Consoli, storia](https://palazzodeiconsoli.it/en/?p=269)
- [Touring Club, quartiere di S. Andrea](https://www.touringclub.it/destinazioni/gubbio/vedere/217675-quartiere-di-s-andrea)
