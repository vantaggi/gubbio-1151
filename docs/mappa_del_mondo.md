# La mappa del mondo di Gubbio 1151

> **Aggiornamento della ripartenza (fase F2, 1 novembre 2026).** Questo documento viene dal
> prototipo (tag `prototipo-v0`) e resta il contratto del mondo, con le decisioni prese dopo:
>
> * **Il Bottaccione.** L'area dell'anello e' la **Strada del Bottaccione** (`mondo/aree/bottaccione.area`);
>   la **Gola del Bottaccione** e' un dungeon separato che si apre da quell'area. In F2 c'e' solo
>   l'ingresso (varco `I` nel parapetto, verso la gola).
> * **Il rientro in citta' dal Bottaccione e' Porta Metauro**, non la Porta di Santa Lucia
>   (confermato da Cioti).
> * **Grafo riallineato alla citta' vera** (1 novembre 2026, rilievo OSM + DEM): via XX Settembre
>   esce dall'angolo sud-est della piazza e porta a Sant'Andrea, e da Sant'Andrea si scende a
>   Sant'Agostino fuori da Porta Romana; Duomo, Quaranta Martiri > Piazza Grande e San Pietro hanno
>   le direzioni vere. Restano scelte di stile: quote esagerate, il ponte del Bargello in discesa,
>   il versante della discesa dalla Basilica.
> * **Il foreground copre solo la fascia alta** (tetti, archi, chiome).
>
> Le aree non sono piu' header C++: sono i file `mondo/aree/*.area`, e `tools/genera_mondo.py`
> ne fa `include/mondo.h`. I riferimenti a header e costanti qui sotto descrivono il prototipo.
>
> **La fonte di verita' del grafo e' `mondo/grafo.json`** (aree, quote, archi, direzioni, anello):
> dove questo documento e grafo.json non coincidono, vale grafo.json.

Questo documento è **il contratto** a cui ogni area di gioco deve obbedire. Esiste perché le aree
vengono autorate in parallelo da persone e agenti diversi: senza un contratto scritto prima, dieci
autori producono dieci convenzioni incompatibili, e l'incoerenza si scopre solo quando il
giocatore attraversa un varco e si ritrova dall'altra parte della città con la bussola girata.

Dettato dal committente nelle Sessioni 19-20. Il committente è di Gubbio: dove questo documento e
il GDD si contraddicono, **vince questo documento**.

---

## 1. La rete delle aree

Gubbio è costruita sulle pendici del Monte Ingino. La città non è una griglia: è un **anello che
gira attorno al monte**, e il giocatore lo percorre salendo da un lato e ridiscendendo dall'altro.

```
                          BASILICA DI SANT'UBALDO  (vetta del Monte Ingino)
                                 /                \
              STRADONI DEL MONTE (2 km sterrati)   STRADA DEL BOTTACCIONE
                            /                        (dietro il monte, con l'acquedotto)
              DUOMO - GIARDINI PENSILI                        \
                   - PALAZZO DUCALE                            \
                            |                              Porta Metauro
                            | (a nord-est e sopra)              |
                     PIAZZA GRANDE  -- via XX Settembre --> SANT'ANDREA --> SANT'AGOSTINO
                            |          (sud-est)            (sud-est)     (sud-est, Porta Romana)
                     via dei Consoli
                            |
                    LARGO DEL BARGELLO   (Fontana dei Matti)
                            |  si scende
                       SAN MARTINO  <---- rientro dal Bottaccione, Porta Metauro
                        /        \
                       |          \  fuori le mura, piu' in basso
                 si scende a sud    TEATRO ROMANO
                       |
              PIAZZA QUARANTA MARTIRI ------> SAN PIETRO
                  (il punto piu' basso)       (sud-est)
```

**Gli archi, per esteso.** Ogni riga è percorribile nei due sensi salvo dove detto.

| Da | Verso | Come |
| :-- | :-- | :-- |
| Piazza Grande | Largo del Bargello | via dei Consoli, in discesa dal varco **nord-ovest** |
| Piazza Grande | via XX Settembre | dall'angolo **sud-est** oltre il Pretorio, in piano |
| via XX Settembre | Sant'Andrea | **sud-est**: in fondo alla via, San Marziale |
| Sant'Andrea | Sant'Agostino | **sud-est**: si scende fuori da Porta Romana |
| Piazza Grande | Duomo / Giardini Pensili / Palazzo Ducale | a **nord-est**, e in salita |
| Duomo / Ducale | Stradoni del Monte | in salita, verso la vetta |
| Stradoni del Monte | Basilica di Sant'Ubaldo | 2 km di sterrato: è la salita lunga del gioco |
| Basilica | Strada del Bottaccione | si scende **dietro** il monte, sul versante ovest |
| Strada del Bottaccione | San Martino | rientro in città da **Porta Metauro** |
| Largo del Bargello | San Martino | si scende |
| San Martino | Piazza Quaranta Martiri | si scende ancora, verso **sud** |
| San Martino | Teatro Romano | **fuori le mura cittadine**, piu' in basso |
| Piazza Quaranta Martiri | San Martino | a **ovest** |
| Piazza Quaranta Martiri | Piazza Grande | a **nord-est**: la salita ripida, via della Repubblica, poi le scale |
| Piazza Quaranta Martiri | San Pietro | a **sud-est**, via Mazzini |

**L'anello si chiude.** Piazza Grande → Ducale → stradoni → Basilica → Bottaccione → Porta
Metauro → San Martino → Bargello → via dei Consoli → Piazza Grande. Chi autora un'area che sta
sull'anello sta autorando un pezzo di un percorso circolare, non un vicolo cieco.

---

## 2. Il dislivello, che non è un dettaglio

Gubbio è **in pendenza**, e il committente lo ha dichiarato fondamentale. Piazza Quaranta Martiri
sta in basso, Piazza Grande a mezza costa, la Basilica in vetta. Un mondo piatto sarebbe la
falsificazione piu' grossa che questo gioco possa fare della città che rappresenta.

Ogni area dichiara nel proprio header una **quota in metri**, misurata sopra Piazza Quaranta
Martiri, che vale zero:

```cpp
constexpr int QUOTA_M = 0;   // metri sul livello di Piazza Quaranta Martiri
```

Quote di riferimento (approssimate, ma l'**ordine** è vincolante e non si discute):

| Area | Quota | |
| :-- | --: | :-- |
| Piazza Quaranta Martiri | 0 m | il punto piu' basso della città |
| Teatro Romano | −10 m | fuori le mura, piu' in basso ancora |
| San Pietro | 5 m | |
| San Martino | 25 m | |
| Largo del Bargello | 45 m | |
| Piazza Grande | 70 m | piazza **pensile**, sospesa sopra gli Arconi |
| via XX Settembre | da 70 m a 72 m | in piano dalla piazza |
| Sant'Andrea | 72 m | |
| Sant'Agostino | 55 m | fuori da Porta Romana, piu' in basso |
| Duomo / Giardini Pensili / Palazzo Ducale | 90 m | sopra Piazza Grande |
| Strada del Bottaccione | da 300 m a 30 m | scende dietro il monte |
| Stradoni del Monte | da 100 m a 350 m | 2 km di sterrato |
| Basilica di Sant'Ubaldo | 380 m | la vetta |

**Come il dislivello si vede in gioco.** Non c'è terza dimensione: la si suggerisce, e la si
suggerisce sempre negli stessi tre modi, mai in un quarto inventato per l'occasione.

1. **Scalinate e rampe** — tile `STAIRS`, calpestabili. Dove la strada sale, si vedono i gradini.
2. **Muri di sostegno** — un'area piu' alta di quella accanto poggia su un muro cieco, non
   sfuma nel nulla.
3. **Affacci** — tile `RAILING`: dove si guarda in basso, c'è un parapetto e oltre il vuoto.

---

## 3. L'orientamento, uguale per tutte le aree

**Tutte le aree sono disegnate ruotate di novanta gradi rispetto al nord**, come Piazza Grande. È
la scelta del committente, presa per Piazza Grande e poi estesa a tutto il mondo per non far
girare la bussola al giocatore a ogni varco.

```
                 ALTO SCHERMO   = OVEST reale
                 BASSO SCHERMO  = EST reale
                 SINISTRA       = SUD reale
                 DESTRA         = NORD reale
```

Conseguenza sulle coordinate della griglia, da tenere a mente leggendo qualunque
`*_collision.h`: **`y` cresce verso EST, `x` cresce verso NORD.**

> **Il tranello, già caduto una volta.** Ruotare non è ribaltare. Ruotando di novanta gradi una
> mappa con il nord in alto fino a portare l'**ovest** in cima, il **nord finisce a destra** e il
> sud a sinistra. Mettendoli al contrario si ottiene l'immagine allo specchio della città: una
> mappa che compila, si gioca, e non dà il minimo segno di sé. Se ne accorge solo chi conosce
> Gubbio. È successo nella Sessione 19, ed è la ragione per cui questo paragrafo esiste.

---

## 4. La scala, e cosa si può comprimere

Regola già scritta in [`include/city_reference.h`](../include/city_reference.h) e qui ribadita
perché è il punto in cui l'illusione si perde.

* **1,5 metri per tile.**
* **Gli EDIFICI sono in scala, ed è obbligatorio.** Il Palazzo dei Consoli è 33 m di fronte, cioè
  22 tile. Un palazzo fuori scala accanto a uno in scala si nota subito.
* **Le DISTANZE si comprimono, ed è permesso.** Il fattore in uso è **73%**. Camminare un
  chilometro reale non è gioco; riconoscere il palazzo davanti a cui si passa lo è.
* **L'ORDINE e le ADIACENZE sono obbligatori.** Se nella città vera girando l'angolo si trova il
  Bargello, in gioco girando quell'angolo si trova il Bargello. Questa è la regola che rende
  l'illusione, non la metratura.

---

## 5. Il contratto tecnico di un'area

Ogni area consegna **due file** e nient'altro. **Entrambi**: un header senza il proprio script
d'arte non produce il `.bmp`, non è cablabile in `MAPS[]` e non serve a niente. È già successo.

### `include/<nome>_collision.h`

```cpp
#ifndef <NOME>_COLLISION_H
#define <NOME>_COLLISION_H

#include <stdint.h>
#include "piazza_grande_collision.h"   // per TileType e is_solid: non si ridefiniscono

namespace gubbio { namespace maps {

constexpr int <NOME>_WIDTH  = ...;   // in tile. x cresce verso NORD
constexpr int <NOME>_HEIGHT = ...;   // in tile. y cresce verso EST
constexpr int <NOME>_QUOTA_M = ...;  // metri sopra Piazza Quaranta Martiri

// Dove il giocatore compare arrivando da ciascuna area confinante. Una costante per arco,
// col nome dell'area di provenienza: e' cio' che permette a map_data.h di cucire le aree
// senza che chi autora un'area debba conoscere le coordinate interne dell'altra.
constexpr int INGRESSO_DA_<AREA>_X = ...;
constexpr int INGRESSO_DA_<AREA>_Y = ...;

[[nodiscard]] inline constexpr uint8_t <nome>_tile_type(int x, int y) { ... }

// Griglia materializzata in ROM, come PIAZZA_GRID.
...

} }
#endif
```

> **PREFISSA OGNI COSTANTE COL NOME DELL'AREA.** Tutte le aree vivono nello **stesso**
> `namespace gubbio::maps`. Una costante chiamata `ROAD_FIRST_X` o `INGRESSO_DA_SANT_AGOSTINO_X`
> collide con quella di un'altra area e la build si ferma con una ridefinizione. Si scrive
> `SAN_MARTINO_ROAD_FIRST_X`, mai `ROAD_FIRST_X`. Nella prima tornata di autori paralleli è
> successo tre volte, e nessuno dei tre poteva accorgersene: ciascuno vedeva solo il proprio file.

> **IL PUNTO DI RIENTRO STA ALMENO SEI TILE DAL PROPRIO VARCO.** Un `INGRESSO_DA_X` a due tile
> dall'uscita verso X fa rimbalzare il giocatore fra le due aree all'infinito: gli basta tenere
> premuta la direzione da cui è arrivato per rientrare nel frame successivo. È il **ciclo di
> transizione**, la ragione per cui gli spawn point esistono, ed è già ricomparso una volta —
> misurato dall'autotest come `piazza → via dei Consoli → piazza`, tre volte di fila.

**Valori di tile.** Si riusano quelli di `piazza_grande_collision.h`, non se ne inventano:

| Valore | Significato | Calpestabile |
| --: | :-- | :-- |
| 0 | suolo | sì |
| 1 | muro / edificato | no |
| 2 | parapetto su affaccio | no |
| 4, 5, 6 | **USCITA 1, 2, 3** dell'area | sì, e cambia scena |
| 7, 8 | facciata di monumento | no |
| 9 | scalinata / rampa | sì |
| 10 | portone interattivo | no |
| 11 | strada in ciottolato | sì |

> **Le uscite non sanno dove portano, ed è voluto.** Un'area dichiara "qui c'è l'uscita 1"; a cosa
> quell'uscita sia collegata lo decide `MAPS[]` in `map_data.h`. Così ricucire il mondo, o
> inserire un'area nuova in mezzo a due esistenti, non richiede di riaprire nessun `*_collision.h`.

**`static_assert` obbligatorie**, che sono la documentazione eseguibile della disposizione:

1. Ogni uscita dichiarata esiste davvero nella griglia ed è calpestabile.
2. Ogni `INGRESSO_DA_*` cade su un tile calpestabile — altrimenti il giocatore compare dentro un
   muro e il salvataggio lo ci lascia per sempre.
3. Almeno un punto notevole per ogni lato, con un messaggio che dice quale orientamento si sta
   fissando. Se qualcuno ruota di nuovo la mappa, si deve fermare lì.
4. Ogni monumento nominato rispetta `respects_scale()` di `city_reference.h`.

### `tools/make_<nome>_art.py`

Genera `graphics/<nome>_ground.bmp` + `.json`. **Importa gli helper**, non li ricopia:

```python
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from make_piazza_art import (TILE, canvas, check_and_write, leggi_indici_bmp4,
                             PALETTE_GROUND, C_WALL, C_WALL_DARK, C_JOINT, C_RAIL,
                             C_STONE, C_ARCH, C_WOOD, C_VOID)
```

Vincoli non negoziabili:

* Il file contiene un **mirror Python di `<nome>_tile_type`**, con le **stesse assert sugli stessi
  punti notevoli** del C++. Due copie che divergono in silenzio sono peggio di una copia sola.
* Misure BMP legali: larghezza e altezza devono essere **256 o 512 px**. Un BG 512×320 non esiste
  sul GBA e la build muore.
* Tetto di **512 tile unici** per tileset, ed è un tetto vero: nella prima tornata la Basilica
  ne ha prodotti 607 e il suo asset era inutilizzabile. Se si sfora si **semplifica il disegno** —
  meno varietà casuale, più ripetizione — e si rifà girare finché non rientra. Lo strumento dice
  di quanto si è fuori.
* La `.json` dichiara sempre `"bpp_mode": "bpp_4"`. Senza, `butano_graphics_tool` promuove in
  silenzio a 8bpp: VRAM raddoppiata e tutti e 16 i banchi di palette occupati.

---

## 6. Da dove viene la grafica: nessun budget, nessun disegnatore

Vincolo dichiarato dal committente e non aggirabile: **budget zero, e nessuno che sappia
disegnare.** Ogni asset del gioco nasce da una **fotografia** del committente, convertita in pixel
art indicizzata a 16 colori da [`tools/photo_to_tiles.py`](../tools/photo_to_tiles.py). Le foto
stanno in `riferimenti/`, gli ingredienti convertiti in `ingredienti/`.

Chi autora un'area:

* usa gli ingredienti che già esistono in `ingredienti/`, leggendoli con `leggi_indici_bmp4()`;
* dove manca l'ingrediente, **disegna in procedurale** e dichiara quale ritaglio fotografico
  servirebbe. Il ripiego procedurale non è un abbozzo da sostituire un giorno: è ciò che tiene la
  build riproducibile per chi clona il progetto senza le foto, che non sono versionate.

**Errore già commesso due volte: scegliere un ritaglio senza guardare la foto.** Il Bargello
inquadrava tetto e cavi elettrici, il Pretorio due sole finestre. Prima di scrivere coordinate di
ritaglio, si apre l'immagine e la si guarda.

---

## 7. Anacronismi: la decisione è presa

Decisione del committente, Sessione 17: **si mettono tutti gli edifici, anche quelli molto
posteriori al 1151.** Il Palazzo dei Consoli è del 1332, il Palazzo Ducale è quattrocentesco, la
Basilica di Sant'Ubaldo è successiva alla morte del santo — che nel 1151 è vivo, ed è un
personaggio giocante.

La ragione, testuale: *«vogliamo qualcosa di magnifico anche visivamente»*. Un giocatore che
arriva a Gubbio e non trova il Palazzo dei Consoli non riconosce Gubbio.

Chi autora un'area **non deve quindi verificare la datazione** di ciò che disegna. Deve però
annotarla in [`docs/riferimenti/FONTI.md`](riferimenti/FONTI.md), perché la scelta resti una
scelta consapevole e non una svista.

**Un errore di collocazione, invece, resta un errore.** Correzioni già dovute dal committente:

* La **Fontana dei Matti non è in Piazza Grande**: è in Largo del Bargello.
* La **Basilica di Sant'Ubaldo non affaccia sulla piazza**: sta molto più in alto, in vetta al
  Monte Ingino. A nord di Piazza Grande ci sono il **Palazzo Ducale, i giardini pensili e il
  Duomo**.
