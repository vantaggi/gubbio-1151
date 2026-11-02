# Cutscene cinematografiche: proposta decisa (2 nov 2026)

Pagina completa con mockup: https://claude.ai/artifact/NPWdXLMUy8dW3uS79oyhHh
Mockup e generatore: `/mnt/project-files/cutscene/mockup/`, `/mnt/project-files/cutscene/mockup_cutscene.py` (usa `stile/dati/` veri).

## Approvato da Cioti
- Bande nere 24 px sopra e sotto (quadro 240x112): con le bande si guarda, senza si gioca.
- Carrellata più lenta: riferimento ~12 px/s sul primo piano (BG0), piani a 1/4, 1/2, 3/4, 1.
- Numero di cutscene: delegato a Claude dopo ricerca → le quattro sotto.

## Cutscene della v1
| Codice | Dove nel copione | Durata | Contenuto |
| :-- | :-- | --: | :-- |
| C1 Prologo | sostituisce P-01 e P-02 | ~60 s | vetrata chiara, salita della camera, mosaico dentro un vetro, pergamena con stendardi, carrellata di Gubbio dalla valle dall'alba alla sera con i fuochi del campo nella conca, salita sulla torre dei Consoli → A1-01 |
| C2 Le undici bandiere | dentro A1-01 (cinematica 1 del GDD) | ~25 s | tre file di fanti (tile ripetuti su BG, 2 pose) con stendardi sprite da `dati/simboli/coalizione.json`, araldo a cavallo, dettaglio della pergamena, dettaglio del pastorale con scossa e lampo; le bande si ritirano e il dialogo riprende nella vista di gioco |
| C3 Presentazioni | Ubaldo e Giorgio (A1-01), Antonio (A1-04), Corrado (B-04) | 3-4 s ciascuna | fermo immagine in controluce, cartiglio vermiglio col nome + 2 righe |
| C4 La terza alba | E-01 ed E-02 | ~40 s | stessi piani di C1 all'alba rosata, drappo sulla torre, Campanone a doppi, fuochi che si spengono, cavallo dell'araldo impennato, salita al monte e vetrata con un solo vetro colorato; poi i titoli |
Dopo, da rivalutare dopo la prova: C5 risveglio dei Ceri, C6 visione nel vetro, C7 inquadrature di presentazione di Stradoni e Bottaccione.

## Regole
1. Stessa palette (notte = trasformata), luce alto-sinistra, contorni scelta 5, font nostro. Nuove solo le inquadrature di profilo e i primi piani.
2. Nelle bande parla solo NARRATORE, max 2 righe da 224 px (le battute del prologo ci stanno già tutte). I personaggi col ritratto parlano nella vista di gioco, senza bande.
3. Niente mixel: primi piani disegnati alla loro misura; zoom affine solo in transizioni < 0,5 s.
4. Niente finto 3D / Mode 7 poligonale (GDD Sez. 34 B va corretto). Niente Inno dei Ceri.
5. Start salta tutto, titoli di coda compresi; A avanza il testo; una cutscene già vista non riparte da sola; nessuna supera 60 s; controllo al giocatore entro 90 s dall'avvio.
6. Niente pulsanti a tempo dentro le cutscene.
7. Stacchi netti fra inquadrature; dissolvenza solo all'inizio e alla fine.

## Tecnica (Butano)
4 BG regolari in modo 0 per la parallasse (+ H-blank dove serve); finestra per le bande; testo su sprite come oggi; blending per luce e nebbia; mosaico per entrare nel vetro; scossa della camera. Misura sulla carrellata da 480 px: ~400 tile unici (~13 KB) + mappe 16 KB su 64 KB. ROM: tutte < 1 MB. Rispettare la regola zero heap.

## Ordine di lavoro proposto
1. Motore di regia a dati: copioni di regia testuali → `tools/genera_regia.py` → tabelle constexpr; lettore in ROM; bande, parallasse, salto; test Python e istantanee mGBA.
2. Pittore dei panorami dal censimento (giorno e notte).
3. C1 + C4 (stessi piani) → ROM di prova per Cioti.
4. C2 + C3.
Nel copione: le note di regia di P-01, P-02, A1-01, A1-04, B-04, E-01, E-02 diventano rimandi alle cutscene; battute invariate.

## Fonti della decisione
- https://itch.io/devlog/677410/intro-cutscenes-how-long.amp (FF SNES 5-6 min di apertura)
- https://www.gamedeveloper.com/design/the-rules-of-the-game-cutting-cut-scenes (3-10 min, «too damn long», niente ripetizioni)
- https://automaton-media.com/en/?p=34004 (Sakurai: tutto saltabile, titoli compresi; niente QTE)
- https://fredzed.substack.com/p/why-do-players-skip (si salta soprattutto ciò che si è già visto)
- https://tvtropes.org/pmwiki/pmwiki.php/Main/FreezeFrameIntroduction (presentazione a fermo immagine)
- https://gbstudiocentral.com/?p=5270 (pochi attori in scena, dissolvenze ripetute spezzano il ritmo)
