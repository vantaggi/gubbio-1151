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

## Musica ed effetti sonori

Tutti originali, composti e sintetizzati per il gioco, nessun campione registrato e nessuna melodia
esistente (neanche l'Inno dei Ceri o «O lume della fede»: vedi `musica/LEGGIMI.md`). Autore: Cioti /
vantaggi, come i contenuti in `LICENSE-CONTENUTI`. Le partiture sono scritte a mano in `musica/*.brano` (le frasi comuni, come il Tema di Gubbio, in `musica/temi.comuni`);
gli strumenti (sintesi additiva) e gli effetti sono nel codice di `tools/genera_audio.py`, che scrive
`audio/` (`python3 tools/genera_audio.py --scrivi`; senza argomenti controlla che sia aggiornato). Ogni
file di `audio/` ha la sua riga qui sotto (`tests/test_crediti.py` lo controlla).

| File | Tipo | Sorgente | Generatore | Licenza |
| :-- | :-- | :-- | :-- | :-- |
| `audio/bandiere.xm` | brano (modulo XM), `bn::music_items::bandiere` | `musica/bandiere.brano` | `tools/genera_audio.py` | CC BY-NC 4.0 (`LICENSE-CONTENUTI`) |
| `audio/basilica.xm` | brano (modulo XM), `bn::music_items::basilica` | `musica/basilica.brano` | `tools/genera_audio.py` | CC BY-NC 4.0 (`LICENSE-CONTENUTI`) |
| `audio/battaglia.xm` | brano (modulo XM), `bn::music_items::battaglia` | `musica/battaglia.brano` | `tools/genera_audio.py` | CC BY-NC 4.0 (`LICENSE-CONTENUTI`) |
| `audio/bottaccione.xm` | brano (modulo XM), `bn::music_items::bottaccione` | `musica/bottaccione.brano` | `tools/genera_audio.py` | CC BY-NC 4.0 (`LICENSE-CONTENUTI`) |
| `audio/canzone_di_flaviano.xm` | brano (modulo XM), `bn::music_items::canzone_di_flaviano` | `musica/canzone_di_flaviano.brano` | `tools/genera_audio.py` | CC BY-NC 4.0 (`LICENSE-CONTENUTI`) |
| `audio/citta.xm` | brano (modulo XM), `bn::music_items::citta` | `musica/citta.brano` | `tools/genera_audio.py` | CC BY-NC 4.0 (`LICENSE-CONTENUTI`) |
| `audio/corrado.xm` | brano (modulo XM), `bn::music_items::corrado` | `musica/corrado.brano` | `tools/genera_audio.py` | CC BY-NC 4.0 (`LICENSE-CONTENUTI`) |
| `audio/fazio.xm` | brano (modulo XM), `bn::music_items::fazio` | `musica/fazio.brano` | `tools/genera_audio.py` | CC BY-NC 4.0 (`LICENSE-CONTENUTI`) |
| `audio/notte.xm` | brano (modulo XM), `bn::music_items::notte` | `musica/notte.brano` | `tools/genera_audio.py` | CC BY-NC 4.0 (`LICENSE-CONTENUTI`) |
| `audio/pastorale.xm` | brano (modulo XM), `bn::music_items::pastorale` | `musica/pastorale.brano` | `tools/genera_audio.py` | CC BY-NC 4.0 (`LICENSE-CONTENUTI`) |
| `audio/presentazione.xm` | brano (modulo XM), `bn::music_items::presentazione` | `musica/presentazione.brano` | `tools/genera_audio.py` | CC BY-NC 4.0 (`LICENSE-CONTENUTI`) |
| `audio/prologo.xm` | brano (modulo XM), `bn::music_items::prologo` | `musica/prologo.brano` | `tools/genera_audio.py` | CC BY-NC 4.0 (`LICENSE-CONTENUTI`) |
| `audio/sconfitta.xm` | brano (modulo XM), `bn::music_items::sconfitta` | `musica/sconfitta.brano` | `tools/genera_audio.py` | CC BY-NC 4.0 (`LICENSE-CONTENUTI`) |
| `audio/stradoni.xm` | brano (modulo XM), `bn::music_items::stradoni` | `musica/stradoni.brano` | `tools/genera_audio.py` | CC BY-NC 4.0 (`LICENSE-CONTENUTI`) |
| `audio/taverna.xm` | brano (modulo XM), `bn::music_items::taverna` | `musica/taverna.brano` | `tools/genera_audio.py` | CC BY-NC 4.0 (`LICENSE-CONTENUTI`) |
| `audio/terza_alba.xm` | brano (modulo XM), `bn::music_items::terza_alba` | `musica/terza_alba.brano` | `tools/genera_audio.py` | CC BY-NC 4.0 (`LICENSE-CONTENUTI`) |
| `audio/titolo.xm` | brano (modulo XM), `bn::music_items::titolo` | `musica/titolo.brano` | `tools/genera_audio.py` | CC BY-NC 4.0 (`LICENSE-CONTENUTI`) |
| `audio/undici_bandiere.xm` | brano (modulo XM), `bn::music_items::undici_bandiere` | `musica/undici_bandiere.brano` | `tools/genera_audio.py` | CC BY-NC 4.0 (`LICENSE-CONTENUTI`) |
| `audio/vittoria.xm` | brano (modulo XM), `bn::music_items::vittoria` | `musica/vittoria.brano` | `tools/genera_audio.py` | CC BY-NC 4.0 (`LICENSE-CONTENUTI`) |
| `audio/annulla.wav` | effetto (WAV 8 bit mono), `bn::sound_items::annulla` | `effetti()` in `tools/genera_audio.py` | `tools/genera_audio.py` | CC BY-NC 4.0 (`LICENSE-CONTENUTI`) |
| `audio/campanone.wav` | effetto (WAV 8 bit mono), `bn::sound_items::campanone` | `effetti()` in `tools/genera_audio.py` | `tools/genera_audio.py` | CC BY-NC 4.0 (`LICENSE-CONTENUTI`) |
| `audio/colpo.wav` | effetto (WAV 8 bit mono), `bn::sound_items::colpo` | `effetti()` in `tools/genera_audio.py` | `tools/genera_audio.py` | CC BY-NC 4.0 (`LICENSE-CONTENUTI`) |
| `audio/conferma.wav` | effetto (WAV 8 bit mono), `bn::sound_items::conferma` | `effetti()` in `tools/genera_audio.py` | `tools/genera_audio.py` | CC BY-NC 4.0 (`LICENSE-CONTENUTI`) |
| `audio/cura.wav` | effetto (WAV 8 bit mono), `bn::sound_items::cura` | `effetti()` in `tools/genera_audio.py` | `tools/genera_audio.py` | CC BY-NC 4.0 (`LICENSE-CONTENUTI`) |
| `audio/cursore.wav` | effetto (WAV 8 bit mono), `bn::sound_items::cursore` | `effetti()` in `tools/genera_audio.py` | `tools/genera_audio.py` | CC BY-NC 4.0 (`LICENSE-CONTENUTI`) |
| `audio/fede.wav` | effetto (WAV 8 bit mono), `bn::sound_items::fede` | `effetti()` in `tools/genera_audio.py` | `tools/genera_audio.py` | CC BY-NC 4.0 (`LICENSE-CONTENUTI`) |
| `audio/fuoco.wav` | effetto (WAV 8 bit mono), `bn::sound_items::fuoco` | `effetti()` in `tools/genera_audio.py` | `tools/genera_audio.py` | CC BY-NC 4.0 (`LICENSE-CONTENUTI`) |
| `audio/livello.wav` | effetto (WAV 8 bit mono), `bn::sound_items::livello` | `effetti()` in `tools/genera_audio.py` | `tools/genera_audio.py` | CC BY-NC 4.0 (`LICENSE-CONTENUTI`) |
| `audio/salva.wav` | effetto (WAV 8 bit mono), `bn::sound_items::salva` | `effetti()` in `tools/genera_audio.py` | `tools/genera_audio.py` | CC BY-NC 4.0 (`LICENSE-CONTENUTI`) |
| `audio/scudo.wav` | effetto (WAV 8 bit mono), `bn::sound_items::scudo` | `effetti()` in `tools/genera_audio.py` | `tools/genera_audio.py` | CC BY-NC 4.0 (`LICENSE-CONTENUTI`) |
| `audio/svanisce.wav` | effetto (WAV 8 bit mono), `bn::sound_items::svanisce` | `effetti()` in `tools/genera_audio.py` | `tools/genera_audio.py` | CC BY-NC 4.0 (`LICENSE-CONTENUTI`) |
| `audio/testo.wav` | effetto (WAV 8 bit mono), `bn::sound_items::testo` | `effetti()` in `tools/genera_audio.py` | `tools/genera_audio.py` | CC BY-NC 4.0 (`LICENSE-CONTENUTI`) |

Riproduzione e conversione (terze parti, non contenuti nostri): nel gioco suona Maxmod, incluso in Butano
(licenza ISC, `butano/licenses/maxmod.txt`); al build `mmutil` di devkitPro (lo strumento di Maxmod,
Mukunda Johnson e altri, licenza ISC come Maxmod) converte `audio/` nella soundbank della ROM. `mmutil` non
entra nella ROM e non e' nel repository: nella ROM finisce solo il suo prodotto, fatto dai file qui sopra.
