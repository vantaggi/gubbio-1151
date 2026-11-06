# Revisione a loop del codice (dal 4 novembre 2026)

Ogni loop: analisi e confronto coi grafi, piano, modifiche, build con **zero avvisi e zero errori**
(`-Werror` nel Makefile), grafi e matrici aggiornati, test (`python3 tools/prove.py --tutte`) e fusione in
`main`. I grafi del codice si rifanno con `python3 tools/grafo_moduli.py` (vedi
[docs/architettura/ARCHITETTURA.md](docs/architettura/ARCHITETTURA.md)); il piano di produzione e' in
`/mnt/project-files/piano/` (`produzione.yaml`, `piano.py`, pezzo `REV`); la trama ha il suo grafo
(`tools/grafo_trama.py`), che questa revisione non tocca.

| Loop | Ambito | Stato |
| :-- | :-- | :-- |
| 0 | Audit e riallineamento di grafi e matrici | fatto |
| 1 | Asset e pipeline (sprite, tile, palette, memoria) | fatto |
| 2 | Movimento, fisica e collisioni | fatto |
| 3 | Animazioni e game feel | fatto |
| 4 | Mappe esterne, fondali e rendering | fatto |
| 5 | Interni, transizioni, warp e scene | fatto |
| 6 | Combattimento, interazioni e AI | fatto |
| 7 | Dialoghi, UI, HUD e testo | fatto |
| 8 | Prestazioni e memoria | fatto |
| 9 | Pulizia architetturale e chiusura | fatto |

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

## Loop 2: movimento e collisioni

- Posizioni intere in pixel, collisione dei piedi (7x4 px) sulla griglia delle celle, scivolata sugli spigoli
  gia' fatta dal thread dei bug (`mondo::scivola`), input letto solo in `main.cpp` e passato a
  `Esplorazione::muovi(dx, dy, passi)`: input e logica gia' separati.
- **Corretto:** in diagonale si andava il 41% piu' veloci che dritti (un pixel per asse a frame). Ora
  `mondo::passi_in_diagonale` porta un resto in 256esimi: 181/256 = 0,707 passi a frame, senza divisioni, con
  `static_assert` sulla velocita'. Contro un muro (un asse bloccato) si scivola lungo il muro alla velocita' piena.

## Loop 3: animazioni e game feel

- Gia' presenti: lampo bianco, scossa e rinculo nei colpi della battaglia (con autotest), lampo e scossa nelle
  cutscene, camera morbida con anticipo nella direzione dello sguardo, respiro da fermi sfasato fra i compagni.
- **Corretto:** il fotogramma della camminata era `passo / vblank`: premendo B (corsa, 4 vblank invece di 6) la
  gamba saltava a un altro punto del ciclo, e partendo da fermi il primo passo si vedeva dopo 6 vblank. Ora
  `mondo::avanza_camminata` (con `static_assert`) per Ubaldo e i compagni: continua dal fotogramma in cui era, e
  il primo passo e' subito.
- **Proposte (grafica nuova: passano dal custode visivo):** polvere ai piedi quando si corre (ok di massima del
  custode: piccola, P2/P3 del suolo, solo selciato e ghiaia; fatta sul ramo claude/project-thread-2tvd34, a904d4a,
  poi rifatta: P5/P4, 8 px al centro, un pixel sopra i piedi, fusa in ripartenza), scintille al colpo forte in
  battaglia.

## Loop 4: mappe esterne e rendering

- Un `regular_bg` per area (big map oltre 64 tile), tile e mappa in ROM; camera limitata ai bordi e centrata
  nelle aree piu' piccole dello schermo; notte con il fade dei blending, riflessi dell'acqua nella gola.
- **Corretto (Y-sort):** la fila (Ubaldo e compagni) aveva z sempre negativo e stava davanti a tutta la gente,
  anche a chi le passava davanti piu' in basso; gli NPC della storia e i nemici avevano z 0 fisso. Ora un solo
  ordine dai piedi per tutti, `Esplorazione::z_sulla_mappa(y)`, messo da `colloca_sulla_mappa`; a pari y Ubaldo
  davanti, poi Giorgio e Antonio. HUD e riquadri restano sopra per priorita' di BG.
- **Proposte (risposta del custode visivo):** BG di primo piano per archi e tetti sopra il giocatore: si', ma solo
  dove c'e' un layer libero e per pochi punti (porte delle mura, archi che si attraversano), con prova nel banco su
  un arco vero e la regola I3 del dialogo intatta. Gradiente del cielo in H-Blank: no per ora (mappa vista
  dall'alto, senza cielo).

## Loop 5: interni, transizioni e scene

- Grafo delle aree in `docs/architettura/aree.mmd`: 25 aree, 7 interni con una porta, ogni varco col ritorno.
  Cambio d'area: dissolvenza di 8 passi, a meta' (schermo nero) si toglie il fondale vecchio **prima** di
  caricare tile e mappa nuovi (`_carica_fondale`). Lo stato del mondo sta tutto in `GameState`: entrare e
  uscire da un interno non perde niente.
- **Corretto:** persone, gente e nemici dell'area nuova si creavano appena passato il varco, sopra il fondale
  vecchio che si scuriva (e le persone una seconda volta a meta' strada). Ora si creano una volta, quando arriva
  il fondale nuovo; fino ad allora quelli vecchi restano fermi e si scuriscono col resto. **Bug vero:** i nemici
  sulla mappa erano messi coi lati del fondale vecchio e restavano spostati se le due aree avevano fondali di
  misura diversa.

## Loop 6: combattimento, interazioni e AI

- La battaglia e' a turni (round, coda delle azioni, mirror Python con 700 scontri identici): hitbox, i-frame e
  cooldown non ci sono per scelta di design. Le persone della folla seguono percorsi fissi (nessun pathfinding a
  frame); il navigatore in ampiezza serve solo alle prove.
- **Corretto:** con due persone a portata di parola rispondeva la prima dell'elenco, anche se stava alle spalle
  di Ubaldo. Ora risponde la piu' vicina, e chi sta alle spalle conta come piu' lontano; il fumetto sta sopra
  quella che risponde.

## Loop 7: dialoghi, UI e testo

- Gia' in regola: testi e glifi pre-composti in ROM (`include/testi.h`, constexpr), nessuna allocazione (gate
  zero-heap), macchina da scrivere con la velocita' delle opzioni e A che rivela tutto e poi chiude, riquadri e
  cornici su un BG (`Riquadri`, 9-slice), testo in sprite (3 righe), il mondo che toglie i suoi sprite prima
  della pausa. Nessuna modifica.

## Loop 8: prestazioni e memoria

- **Corretto:** il navigatore della camminata automatica (96 KB) stava nella EWRAM inizializzata: 96 KB di ROM
  copiati in EWRAM a ogni accensione, anche nel gioco vero. Ora `bn::optional` nella EWRAM azzerata, costruito
  quando la camminata parte. ROM da 2.591.356 a 2.493.640 byte; `.ewram` da 103.048 a 4.532 byte. Il gate
  (`tools/check_zero_heap.sh`) ora rifiuta una `.ewram` oltre 16 KB.
- IWRAM: 8,8 KB di codice (Butano e maxmod) e 2,2 KB di dati; nessun `BN_CODE_IWRAM` nel progetto, e non serve:
  la camminata su tutti gli archi sta sotto il 90% di CPU senza frame persi (prova mGBA). I colli di bottiglia
  ai varchi e nei riquadri li aveva gia' tolti il thread dei bug.

## Loop 9: pulizia e chiusura

- **Codice morto tolto** (trovato col linker, `--print-gc-sections`, e controllato a mano):
  `audio::accendi`/`acceso` (il gancio di prima del menu delle opzioni, ora ci sono i volumi),
  `salvataggio::tempo_secondi(slot)`, `VistaTesto::set_z_order`, `Riquadri::set_visible`, `Striscia::set_visible`.
  Le altre funzioni che il linker scarta sono dei modi di prova (`GUBBIO_AVVIO`) o copie gia' inline.
- Pattern: niente heap (gate), contenitori a misura fissa (`bn::vector`), una battaglia sola riusata sul posto
  in EWRAM, sprite degli effetti di battaglia fissi e riusati.
- **Rimandato apposta:** dividere `src/storia_scena.cpp` (1680 righe, 19 moduli inclusi). Ci lavorano ogni
  giorno i thread del gioco, delle quest e della citta' viva: spezzarlo ora vorrebbe dire conflitti su ogni
  loro fusione. Da fare in una fase ferma.
- Grafi e matrici rifatti (`docs/architettura/`), 0 errori; build 0 errori e 0 avvisi; 902 test e 8 prove mGBA ok.
