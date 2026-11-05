# Giri di verifica: mappa, edifici, vie, porte e finestre (5 nov 2026, sera)

Il prompt usato a ogni giro è in [verifica_mappa_prompt.md](verifica_mappa_prompt.md). Il controllo automatico è
`tests/test_aperture.py`.

| Giro | Cosa ho guardato | Cosa non tornava | Cosa è cambiato |
| :-- | :-- | :-- | :-- |
| 1 | Porte e finestre delle case, in tutte le aree di città, con il nuovo registro degli ingombri | 251 sovrapposizioni. 103 finestre toccavano una porta, 53 si accavallavano fra loro (le imposte di due finestre in 8 px), 33 stavano sopra una bottega, 27 erano coperte da uno stendardo, 23 toccavano una porta del morto; in più 8 stendardi e 4 fiaccole sopra la porta del morto | Ogni casa tiene l'elenco dei suoi rettangoli occupati. Una finestra, uno stendardo, una fiaccola o una botte vanno solo dove il muro è libero, con 1 px di distacco |
| 2 | Le facciate dopo il giro 1, a occhio (3x) | Le case basse (4 tile) erano rimaste quasi senza finestre | Le finestre vanno al centro dei tratti di muro liberi accanto alla porta (due se il tratto è largo). Sulle case alte la fila di sopra sale sotto la gronda, così resta muro sopra l'arco della porta |
| 3 | Portali e finestre dei monumenti (gli archi bui di ogni Tela) contro ingressi, tende e lanterne | Niente fuori posto. Le sole coppie che si toccano sono il portale acceso con la sua lanterna e la sua tenda (Consoli, Basilica, le botteghe), come deve essere | Il test lo controlla |
| 4 | Pareti degli interni: finestre, scaffali, camino, stemma, torce, ruote | Le tre ruote appese dal carradore si accavallavano di 2 px | Ruote di raggio 7, staccate. Il test controlla tutte le stanze, di giorno e di notte |
| 5 | Disposizione dei monumenti veri dentro ogni area contro le direzioni di OpenStreetMap | Tutte le coppie entro 60°, tranne due. Duomo e Ducale: nel vero il Duomo sta a sud-est del Ducale, nel gioco sta sopra la stradina perché la sua facciata si veda di fronte (scelta della rotazione, resta). San Francesco e Loggia: nel gioco San Francesco sta a sud della Loggia, nel vero a sud-ovest (60°): a ovest ci sono i giardini | Le due eccezioni sono scritte nel test con il loro perché. San Francesco resta da rivedere se si rifà l'area |
| 6 | Le uscite di ogni area contro la direzione vera dell'area vicina | Nessuna oltre 67° (tutte nel loro ottante o in quello accanto) | Nessuna |
| 7 | Le vie (ordine dei luoghi in via dei Consoli e via XX Settembre, le salite da Quaranta Martiri) | Tornano con `mappa/MAPPA.md` par. 9, e i test del grafo lo controllano già | Nessuna |
| 8 | Ultimo giro completo: test, prove in mGBA e il registro degli ingombri da capo | 0 sovrapposizioni, 928 test verdi, 8 prove mGBA ok | ROM nuova |

## Cosa resta

- San Francesco sta a sud della Loggia invece che a sud-ovest. Per spostarlo bisogna rifare la metà destra di
  Piazza Quaranta Martiri. Le foto e OSM non sono raggiungibili dal cloud, quindi conviene guardarlo con Cioti.
- Alcune facciate strette con la bottega restano senza finestre, perché la bottega prende quasi tutto il muro.
