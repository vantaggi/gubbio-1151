---
name: asset-pipeline
description: Pipeline e strumenti di conversione asset da formati di authoring (Tiled JSON, PNG indexed 16-color, XM chiptune) a header e sorgenti C++ per Butano GBA.
---

> **Nota:** copia operativa per Claude Code. La sorgente canonica e' `.agents/skills/asset-pipeline/SKILL.md`
> (convenzione Antigravity): le due vanno tenute allineate a mano.

# Asset Pipeline Skill

## 1. Mappe Tiled -> Header C++
Script Python `tools/map_exporter.py`:
- Input: file JSON esportato da Tiled con dimensioni $W \times H$.
- Output: header C++ contenente `constexpr uint8_t COLLISION_MAP[]` e costanti di mappa.

## 2. Specifiche Sprite
- Palette: 16 colori indexed (colore 0 = trasparenza).
- Dimensioni: potenze di 2 conformi all'hardware GBA ($8\times 8, 16\times 16, 32\times 32, 64\times 64, 16\times 32, 32\times 64$, etc.).
- File posizionati in `graphics/`.

## 3. Audio & SFX Maxmod
- Moduli tracker `.xm` o `.it` a 4-8 canali leggeri in `audio/music/`.
- Campioni SFX `.wav` (PCM 8-bit mono a 16kHz o 21kHz) in `audio/sound_effects/`.

## 4. Font italiano (Sessione 12)

`tools/make_font.py` genera `graphics/font_gubbio.{bmp,json}` e `include/font_gubbio.h` **derivando**
il font 8x8 di Butano e aggiungendo le 12 lettere accentate italiane, che quello di Butano non ha
(i suoi 16 caratteri non ASCII sono tutti spagnoli).

Regole della pipeline del font:
* **Le celle partono da ASCII 33 ('!'), la tabella delle larghezze da 32 (lo spazio).** Lo spazio
  ha una larghezza ma nessuna cella: sbagliare questo scarto di uno fa scivolare ogni lettera di
  una posizione, e "Sant'Ubaldo" esce "Tbou..." (accaduto nella Sessione 05).
* Le accentate stanno **in coda** alle 94 celle ASCII, nell'ordine dell'array `FONT_UTF8_CHARACTERS`.
* Chi rende testo fuori dalla ROM (`tools/preview_battle_screen.py`) deve leggere **questo** font,
  non quello di Butano: altrimenti l'anteprima mostra un testo che il gioco non stampera' mai.
* `tests/test_assets.py` verifica che ogni carattere delle stringhe dei sorgenti esista nel font.
  Un carattere non mappato e' un `BN_ERROR` a runtime, non un errore di compilazione.
