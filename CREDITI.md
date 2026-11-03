# Crediti

Registro di ogni asset di terzi che entra nel repository. Un asset senza riga qui non si
committa. Le foto prese dal web non entrano, ne' loro derivati (vedi `.gitignore`).

| Asset | Autore | URL | Licenza | Modifiche |
| :-- | :-- | :-- | :-- | :-- |
| `mondo/fonti/censimento_osm.csv`, `mondo/fonti/misure_osm.json`, `mondo/fonti/aree_schede.json`, `mondo/monumenti.json`, `mondo/varchi.json` (misure, coordinate e orientamento dei monumenti; larghezze di vie e piazze) | © contributori OpenStreetMap | https://www.openstreetmap.org/copyright | ODbL 1.0 | Estratti per misurare (lati, assi, coordinate) e convertiti in tile; nessuna geometria copiata. Dai metadati di Wikimedia Commons si conta solo quante foto esistono: nessuna immagine. |
| `dati/mappa_umbria.json` (coordinate delle undici citta' della coalizione nella pergamena del prologo) | Wikipedia in italiano, pagine dei comuni | https://it.wikipedia.org/ | Dati di fatto (coordinate WGS84 al millesimo) | Arrotondate; fiumi, crinale e strade tracciati a mano come punti approssimati, nessun tracciato copiato. |
| `dati/simboli/coalizione.json` (stemmi delle undici citta') | araldicacivica.it, pagine /comune/<nome>/ | https://www.araldicacivica.it/ | Blasonature (descrizioni araldiche) | Ridisegnate da zero come drappi 14x26 semplificati da `tools/stendardi.py`: le semplificazioni sono scelte di gioco. Nessuna immagine presa. |
| `dati/simboli/simboli.json` (simbologia di Gubbio: stemma del 1151, colori dei quartieri) | Fonti elencate nel campo `fonti` (Wikipedia, Cronaca Eugubina su una conferenza di Fabrizio Cece, siti del Palio e del Torneo) | vedi file | Fatti citati | Riassunti a parole; nessuna immagine presa. |
| `butano/` (submodule, libreria e sue dipendenze compilate nella ROM: maxmod, agbabi, libtonc, ETL e altre) | Gustavo Valiente e gli autori in `butano/licenses/` | https://github.com/GValiente/butano | zlib (Butano), ISC (maxmod), MIT, zlib, MPL 2.0 e pubblico dominio (vedi `butano/licenses/`) | Nessuna. Nello zip di rilascio si copiano i testi di `butano/licenses/`. |

Grafica, font, testi, storia e regia sono originali e generati dal codice del repository (`stile/`,
`tools/`): non hanno righe qui perche' non sono di terzi. Le foto di Wikimedia Commons consultate
come riferimento non sono nel repository: il loro elenco, con autori e licenze, accompagna il rilascio
(`rilascio/CREDITI_FOTO_RIFERIMENTO.md` nella cartella del progetto).
