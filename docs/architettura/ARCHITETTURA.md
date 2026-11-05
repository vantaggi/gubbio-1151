<!-- GENERATO da tools/grafo_moduli.py: non modificare a mano. -->
# Architettura del codice (fotografia del ramo)

Si rifa' con `python3 tools/grafo_moduli.py`; `tests/test_architettura.py` controlla che sia aggiornata.

| File | Cosa |
| :-- | :-- |
| [moduli.mmd](moduli.mmd) | grafo dei moduli (Mermaid): x.cpp e x.h sono un nodo; in grigio i generati |
| [matrice_moduli.csv](matrice_moduli.csv) | chi include chi (righe: file; colonne: header) |
| [matrice_asset.csv](matrice_asset.csv) | ogni asset di graphics/ e audio/ e chi lo usa |
| [aree.mmd](aree.mmd) | aree e varchi (tratteggiati gli ingressi agli interni) |

## Numeri

- 94 file: 78 scritti a mano (22839 righe), 16 generati (65343 righe).
- 259 include fra file del progetto.
- 38 asset, 38 usati.
- 25 aree, 7 interni con una sola porta; 62 varchi.

## Header generati e il loro script

| Header | Generato da | Righe |
| :-- | :-- | --: |
| `include/battaglia_attese.h` | `tools/battaglia_mirror.py` | 1040 |
| `include/battaglia_grafica.h` | `tools/genera_battaglia.py` | 4146 |
| `include/cartelli.h` | `tools/genera_cartelli.py` | 90 |
| `include/colonna_sonora.h` | `tools/genera_colonna_sonora.py` | 293 |
| `include/compagni.h` | `tools/sagome_compagni.py` | 428 |
| `include/folla.h` | `tools/genera_folla.py` | 1363 |
| `include/mondo.h` | `tools/genera_mondo.py` | 18668 |
| `include/regia.h` | `tools/genera_regia.py` | 20904 |
| `include/stile/cornice.h` | `stile/esporta_cpp.py` | 77 |
| `include/stile/font.h` | `stile/esporta_cpp.py` | 169 |
| `include/stile/icone_menu.h` | `tools/genera_icone_menu.py` | 101 |
| `include/stile/mappa_menu.h` | `tools/genera_mappa_menu.py` | 537 |
| `include/stile/palette.h` | `stile/esporta_cpp.py` | 45 |
| `include/stile/pose.h` | `stile/esporta_cpp.py` | 80 |
| `include/storia.h` | `tools/genera_storia.py` | 3581 |
| `include/testi.h` | `tools/genera_testi.py` | 13821 |

## Gli header piu' inclusi

| Header | Inclusi da |
| :-- | --: |
| `include/storia_logica.h` | 19 |
| `include/game_state.h` | 18 |
| `include/tabella.h` | 17 |
| `include/audio.h` | 14 |
| `include/progressione.h` | 12 |
| `include/vista_testo.h` | 12 |
| `include/menu_pagine.h` | 11 |
| `include/battaglia.h` | 10 |
| `include/stile/cornice.h` | 10 |
| `include/esplorazione.h` | 9 |

## Controlli

- Nessun errore: niente cicli, niente header o asset orfani, ogni varco ha il ritorno.

## Candidati da dividere (avvisi)

- include/battaglia.h: 1091 righe scritte a mano
- include/storia_logica.h: 1211 righe scritte a mano
- src/esplorazione.cpp: 1381 righe scritte a mano
- src/scena_battaglia.cpp: 1229 righe scritte a mano
- src/storia_scena.cpp: 1755 righe scritte a mano
- src/storia_scena.cpp: include 19 moduli del progetto
- src/titolo.cpp: include 14 moduli del progetto
