# Cosa si porta nel prossimo gioco

Gubbio 1151 contiene due cose mescolate: un **motore e una catena di lavoro** che servono a qualunque
gioco della serie, e il **contenuto di Gubbio**. Questa pagina le separa, così il prossimo gioco
(un'altra storia di Gubbio, Perugia, Città di Castello, le Marche, la Toscana) parte dal motore e
cambia solo il contenuto.

- **Si porta così com'è**: si copia e non si tocca, salvo miglioramenti che tornano anche a Gubbio.
- **Si porta e si riempie**: lo strumento è generico, i dati o i parametri sono di Gubbio.
- **Resta a Gubbio**: contenuto da rifare per ogni gioco.

## 1. Toolchain, build e prove — si porta così com'è

| Pezzo | Dove | Note |
| :-- | :-- | :-- |
| Versioni bloccate | `toolchain.lock`, `.gitmodules` (Butano 21.9.0), `build.sh` | Aggiornare Butano solo a inizio gioco, mai a metà |
| CI con ROM come artifact | `.github/workflows/` | La ROM ufficiale è quella della CI (D021) |
| Build in cloud e banco mGBA | `tools/banco.sh`, `tools/banco_mgba.c` | Docker con il mirror, libmgba senza schermo (D023) |
| Giro corto delle prove | `tools/prove.py`, `tools/prove/`, `docs/prove.md` | Solo i test toccati, in parallelo (D027) |
| Prove nel gioco | `tools/prove_mgba.py`, `tests/mgba/prove.json` | Camminata, storia, battaglie, salvataggio, palette |
| Niente test saltati | `tools/check_no_skip.py` | D025 |
| Zero heap ed EWRAM | `tools/check_zero_heap.sh` | Gate 16 KB |
| Regole del codice GBA | `docs/regole_sviluppo_gba.md`, `tools/controlla_regole_gba.py`, `controlla_divisioni.py`, `controlla_struct.py`, `controlla_header_host.sh`, `include/aritmetica.h` | D029; `-Werror` nel `Makefile` (D028) |
| Pannello di debug e contatori | `include/pannello_debug.h`, flag `GUBBIO_PRESTAZIONI`, `GUBBIO_PALETTE` | Rinominare il prefisso dei flag per il gioco nuovo |
| Grafo dei moduli | `tools/grafo_moduli.py`, `docs/architettura/`, `tests/test_architettura.py` | |
| Metodo | `docs/metodo/`, `tools/controlla_metodo.py`, `tests/test_metodo.py` | Si azzera il registro, si tengono lezioni e percorso |

## 2. Motore del gioco — si porta e si riempie

| Pezzo | Dove | Cosa cambia per un gioco nuovo |
| :-- | :-- | :-- |
| Testi e font | `tools/genera_testi.py`, `include/testo.h`, `vista_testo.h`, `stile/dati/font.json` | Niente, salvo glifi nuovi |
| Storia e scelte | `tools/genera_storia.py`, `include/storia_logica.h`, `storia_scena.h` | Il copione; il formato di scene, bandiere e varianti resta. Da dividere `storia_scena.cpp` prima di riusarlo |
| Grafo della trama | `tools/grafo_trama.py`, `tests/test_grafo_trama.py` | Niente |
| Regia delle cutscene | `tools/genera_regia.py`, `include/regia*.h`, `regia/*.regia` | I copioni di regia e i pittori delle scene |
| Mondo | `tools/genera_mondo.py`, `tools/mondo_dati.py`, `include/mondo*.h`, `esplorazione.h` | `mondo/` (grafo, aree, monumenti, varchi) |
| Folla e NPC | `tools/figure_popolo.py`, `genera_folla.py`, `include/folla*.h` | Costumi e mestieri d'epoca |
| Battaglia | `include/battaglia*.h`, `scena_battaglia.h`, `scheda_mosse.h`, `tools/battaglia_mirror.py`, `bilanciamento.py` | Eroi, mosse, nemici, numeri; FSM e gemello Python restano |
| Menù, mappa, negozio, opzioni | `include/menu_pagine.h`, `vista_menu.h`, `negozio.h`, `opzioni.h`, `tools/genera_mappa_menu.py`, `genera_icone_menu.py` | Voci, icone, mappa |
| Salvataggio | `include/save_data.h`, `save_crc32.h`, `game_state.h` | Il contenuto dello stato; versione e CRC restano |
| Audio | `tools/genera_audio.py`, `genera_colonna_sonora.py`, `include/audio*.h` | I brani in `musica/` |
| Stile in dati | `stile/` (stile.py, genera.py, esporta_cpp.py, genera_bmp.py) | I parametri in `stile/dati/` se la serie cambia aspetto |
| Pittori procedurali | `tools/pennelli.py`, `pittore_citta.py`, `pittore_interni.py`, `pittore_monumenti.py`, `pittore_panorami.py`, `sagome_*.py`, `pittore_ritratti.py` | Le funzioni dei singoli monumenti sono di Gubbio; pennelli, case, tetti, suolo, interni e sagome valgono per ogni borgo medievale dell'Italia centrale |
| Test di stile e standard | `tests/test_stile_*.py`, `test_fondali_standard.py`, `tools/controlla_cutscene.py` | Le soglie seguono lo standard |
| Test di redazione e nomi | `tests/test_redazione.py`, `test_nomi_coerenti.py`, `test_crediti.py` | Le liste di parole e di nomi ritirati |

## 3. Contenuto di Gubbio — resta a Gubbio

`copione/`, `testi/`, `dati/` (amici, mestieri), `mondo/` (14 aree, monumenti, varchi, stradoni), `regia/`,
`musica/`, i pittori dei singoli monumenti e delle cutscene (`pittore_c2.py`…`pittore_c7.py`,
`pittore_trio.py`, `stendardi.py`, `disegna_gola.py`, `disegna_stradoni.py`), `docs/fedelta.md`,
`docs/simboli.md`, `docs/censimento_monumenti.md`, `CREDITI.md`.

Delle decisioni, quelle con Tipo **S** in [DECISIONI.md](DECISIONI.md) restano a Gubbio; quelle **G** sono
il punto di partenza del gioco nuovo; quelle **G+S** hanno una regola generica e valori di Gubbio.

## 4. Decisioni aperte per la serie

Non servono adesso, ma vanno prese prima di cominciare il secondo gioco. Raccomandazione di Claude fra
parentesi.

1. **Un motore comune o una copia per gioco?** (Copia per gioco finché i giochi sono due; quando ce n'è
   un terzo, si estrae il motore in un repo suo, così le correzioni arrivano a tutti.)
2. **Stesso aspetto per tutta la serie?** (Sì per palette, font, cornici e proporzioni, che fanno
   riconoscere la serie; direzione artistica e titolo cambiano per ogni città.)
3. **Personaggi che ritornano?** (Decisione di gusto del committente.)
4. **Storie fuori da Gubbio:** stessa ricerca della fase 1, con qualcuno del posto che fa le conferme
   che a Gubbio ha fatto Cioti.
