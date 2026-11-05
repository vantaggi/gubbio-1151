# Fedeltà alla Gubbio vera: il metodo e i 10 giri (5 nov 2026)

Richiesta di Cioti (5 nov 2026): dieci giri per verificare edifici, piazze, fontane, interni e mappa
rispetto agli originali, cercando prima come lavorano i professionisti. Principio di sempre: la città
vera è la guida, non un vincolo; grafica procedurale, nessun derivato delle foto. Il nord è in alto e le
facciate che guardano a est o a ovest si disegnano verso il basso.

## Il metodo dei professionisti, ridotto a regole nostre

Fonti lette: l'art director di *Assassin's Creed Shadows* sul rapporto di scala (circa 1:16, scelto perché
con una scala troppo larga «le montagne sembrano colline»); l'articolo *The illusion of scale* di Game
Developer (edifici più bassi del vero, suoni e tempi che li fanno sembrare grandi); il racconto della
documentazione di Istanbul per *Revelations* (scomporre un edificio nei suoi elementi: aggetti, sporti,
materiali); l'analisi di Sinnoh in *Pokémon Diamante e Perla* (pochi luoghi riconoscibili presi da Hokkaido,
non la copia della città); un pezzo sulla pixel art di *Eastward* (esagerare le proporzioni che contano,
poche linee e pochi colori).

Da qui le regole che abbiamo usato a ogni giro:

1. **Comprimere le distanze, non i segni.** Le vie e le piazze si accorciano (già fatto con il `fattore`
   delle aree); i tratti che fanno riconoscere un edificio restano interi.
2. **Tre segni per edificio** (STANDARD M5), scelti dalle descrizioni vere: il profilo (torre, merli,
   campanile), il ritmo delle aperture, un elemento unico (scalinata a ventaglio, porta del morto, tiratoio).
3. **Esagerare la proporzione che distingue.** Il Palazzo dei Consoli è il più alto: la facciata prende
   quasi tutta l'impronta. Una porta della città è «una torre alta con l'arco» (Cioti).
4. **La silhouette prima del dettaglio.** Campanili e merli escono sopra il tetto e si vedono anche quando
   lo schermo ne mostra solo un pezzo.
5. **Ogni cosa al suo posto rispetto alle altre.** Le direzioni vere fra i luoghi (OSM) contano più delle
   misure: si controlla la disposizione, non la scala.

## I giri

| Giro | Luogo | Cosa non tornava col vero | Cosa è cambiato |
| :-- | :-- | :-- | :-- |
| 1 | Palazzo dei Consoli | Basso e tozzo come il Pretorio; merli piatti; campanile in mezzo al tetto; niente scalinata | Facciata alta quasi tutta l'impronta; merlatura su archetti ogivali; il campanile del Campanone sull'angolo con la campana; portale gotico rialzato sulla scalinata a ventaglio, con la lunetta affrescata |
| 2 | Largo del Bargello | Fontana tonda e piatta; Bargello senza piani | Vasca ottagonale col fusto e la tazza che salgono sopra l'orlo; Bargello con le cornici marcapiano e le finestre centinate col davanzale su mensola |
| 3 | San Martino | Il Camignano mancava del tutto | Il torrente scoperto in un canale di pietra fra le case, esce da sotto le mura accanto a Porta Metauro, passa sotto il Ponte di San Martino di pietra (parapetti e volta) sulla via del Bargello, poi va coperto |
| 4 | Teatro romano | Le arcate erano un anello intero, da edificio nuovo | Le arcate superiori in parte crollate, come oggi. (Provata anche l'erba sulle file alte: sforava i 1024 tile e i banchi, tolta) |
| 5 | Duomo e Palazzo Ducale | Duomo senza campanile e senza i bassorilievi; cortile del Ducale un quadrato piatto | Grande finestra con i cinque bassorilievi intorno e la robusta torre campanaria; cortile d'onore col portico ad archi in pietra serena e il piano nobile di mattoni fra le lesene |
| 6 | Piazza Quaranta Martiri | Disposizione verificata su OSM: giusta (giardini a ovest, Loggia a est, San Francesco a sud-est). Facciata di San Francesco piatta; il tiratoio era una fila di quadretti | San Francesco con la facciata tripartita, il rosone grande e il portale gotico; il tiratoio come galleria aperta coi ritti di legno e le pezze di lana tese |
| 7 | Le porte della città | Viste da dentro erano una fascia piatta con una riga nera | Le quattro porte sul lato alto (Metauro, Romana, Sant'Ubaldo, Castello) sono torri di fronte: merli, feritoie, il grande arco con la volta buia e la strada che passa sotto (ribassato dove il passaggio è largo) |
| 8 | Via dei Consoli e via XX Settembre | La porta del morto c'era nel codice ma non si vedeva quasi mai | Frequente nelle vie dove la si trova davvero (80% in via dei Consoli), con lo stipite chiaro e la soglia rialzata: si legge come porta murata |
| 9 | Sala dei Consoli | Travi di legno e soffitto basso | La testa della grande volta a botte di pietra del Salone dell'Arengo, la ghiera a conci e la volta in ombra |
| 10 | Mappa del menù | Le direzioni fra le aree di città tornano col vero (1 sola coppia oltre 45°), ma la gola del Bottaccione andava verso ovest | La gola sale da Porta Metauro verso nord-nord-est lungo il fianco del Monte Ingino, con il Camignano e il sentiero dalla Basilica |

Ogni giro ha il suo controllo in `tests/test_fedelta.py`. Le schermate prima e dopo, dal generatore e dalla
ROM in mGBA, sono nella cartella del progetto `fedelta/`.

## Cosa resta (non bloccante)

- Il Duomo resta una lunga facciata sulla via: la facciata vera a capanna guarda di lato, e girarla
  vorrebbe dire rifare l'area.
- Il Teatro: l'erba sui gradini alti si può riprovare con tile interi, se avanzano tile.
- La Fontana dei Matti è di 3 tile: più grande vorrebbe dire allargare il Largo del Bargello.
