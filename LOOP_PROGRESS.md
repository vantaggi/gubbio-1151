# Revisione a loop del codice (dal 4 novembre 2026)

Ogni loop: analisi e confronto coi grafi, piano, modifiche, build con **zero avvisi e zero errori**
(`-Werror` nel Makefile), grafi e matrici aggiornati, test (`python3 tools/prove.py --tutte`) e fusione in
`ripartenza`. I grafi del codice si rifanno con `python3 tools/grafo_moduli.py` (vedi
[docs/architettura/ARCHITETTURA.md](docs/architettura/ARCHITETTURA.md)); il piano di produzione e' in
`/mnt/project-files/piano/` (`produzione.yaml`, `piano.py`, pezzo `REV`); la trama ha il suo grafo
(`tools/grafo_trama.py`), che questa revisione non tocca.

| Loop | Ambito | Stato |
| :-- | :-- | :-- |
| 0 | Audit e riallineamento di grafi e matrici | fatto |
| 1 | Asset e pipeline (sprite, tile, palette, memoria) | fatto |
| 2 | Movimento, fisica e collisioni | da fare |
| 3 | Animazioni e game feel | da fare |
| 4 | Mappe esterne, fondali e rendering | da fare |
| 5 | Interni, transizioni, warp e scene | da fare |
| 6 | Combattimento, interazioni e AI | da fare |
| 7 | Dialoghi, UI, HUD e testo | da fare |
| 8 | Prestazioni e memoria | da fare |
| 9 | Pulizia architetturale e chiusura | da fare |

## Loop 0: grafi e matrici

**Cosa c'era.** Tre grafi, tutti fuori dal codice C++: il piano di produzione (`produzione.yaml` ->
`piano.py` -> grafo e matrice dei pezzi di lavoro), il grafo della trama (`tools/grafo_trama.py`) e il grafo
delle aree (`mondo/grafo.json`, `mondo/varchi.json`, `docs/mappa_del_mondo.md`). **Nessun grafo dei moduli
del codice e nessuna matrice degli include o degli asset.**

**Discrepanze trovate e corrette.**

| Dove | Cosa diceva | Com'e' davvero |
| :-- | :-- | :-- |
| codice | nessun grafo dei moduli | nuovo `tools/grafo_moduli.py` -> `docs/architettura/` (moduli.mmd, matrice_moduli.csv, matrice_asset.csv, aree.mmd, ARCHITETTURA.md), controllato da `tests/test_architettura.py` |
| `mondo/grafo.json` (`_leggimi`) | 14 aree; rotazione «alto = ovest» | 25 aree; nord in alto dal 4 nov |
| `docs/mappa_del_mondo.md` | 20 archi, nessuna parola su nord in alto, interni e gola | nota del 4 nov: 25 aree, 62 varchi (31 collegamenti), nord in alto, rimando ad `aree.mmd` |
| `produzione.yaml`, risorsa `stato` | salvataggio v3 | v4 da 80 byte |
| `produzione.yaml`, risorsa `avvio` | GUBBIO_AVVIO 1-11 | 0-15 (13 libero) e `tests/mgba/prove.json` |
| `produzione.yaml`, R0 | prova di Cioti «mai fatta» | prima prova il 4 nov sera; quella completa resta da fare |
| `src/main.cpp` | elenco dei modi senza il 13 | «13 libero» |
| repo | `build.log` e `test.log` committati per sbaglio | tolti e ignorati |

**Controlli del nuovo grafo.** Nessun ciclo fra gli header (259 include fra 94 file), nessun header scritto a
mano che nessuno include, ogni varco ha il suo ritorno, le 25 aree di `include/mondo.h` sono tutte in
`mondo/varchi.json`. Trovati **5 asset orfani** (Loop 1).

**Candidati da dividere** (avvisi, per i loop successivi): `src/storia_scena.cpp` (1680 righe, 19 moduli
inclusi: e' il regista della partita, il «God object» del progetto), `src/esplorazione.cpp` (1233),
`src/scena_battaglia.cpp` (1229), `include/storia_logica.h` (1208), `include/battaglia.h` (1091),
`src/titolo.cpp` (14 moduli inclusi). Gli header grossi (`regia.h` 20904 righe, `mondo.h` 18642, `testi.h`
13821) sono generati: dati in ROM, non logica.

**Build.** Prima: 0 errori, **69 avvisi** (51 `switch` senza `default` in `storia_logica.h`, 14 campi non
inizializzati in `autotest_salvataggio.cpp`, 2 funzioni dichiarate e mai definite nello spazio anonimo,
2 casi mancanti in `autotest_storia.cpp`). Dopo: **0 errori, 0 avvisi**, e `-Werror` perche' non tornino.
I due casi mancanti erano un buco vero: l'autotest delle guardie del copione non controllava le guardie delle
quest (`CONTEGGIO`, `CONTEGGIO_E_NON_BANDIERA`); ora le prova con zero pezzi, con tutti i pezzi e con la
bandiera dalla parte sbagliata.

## Loop 1: asset e pipeline

- `graphics/`: 11 BMP, tutti 4bpp (sprite dei ritratti 32x32 x3 fotogrammi, 2 fondali 256x256 `bpp_4_auto`).
  La grafica del mondo, della battaglia e delle cutscene e' procedurale: tile in header generati, tutti
  `constexpr` in ROM (nessun array globale modificabile fuori da quelli voluti in EWRAM).
- **Orfani tolti:** `cornice_dialogo`, `cornice_menu` (i riquadri sono i tile 9-slice di
  `include/stile/cornice.h`), `logo_mono` (il titolo usa il logo a colori), `ritratto_giovane`,
  `ritratto_soldato` (i dialoghi hanno i ritratti dei 4 parlanti). Il linker li scartava gia', ma Butano li
  convertiva a ogni build. Restano disegnati e provati (`FUORI_ROM` in `stile/genera_bmp.py`), e la
  `--verifica` rifiuta un loro BMP rimasto in `graphics/`.
- `audio/`: 19 XM e 13 WAV (8 bit, mono, 22050 Hz), tutti usati; soundbank 289 KB.
- `matrice_asset.csv`: ogni asset e chi lo usa; un asset nuovo senza utenti fa fallire `test_architettura`.
- Segnato per il Loop 8: `g_camminata` (navigatore della camminata automatica, 96 KB) e' in `.ewram`
  inizializzata, quindi occupa anche 96 KB di ROM e si copia all'accensione.
