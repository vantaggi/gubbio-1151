# GUBBIO 1151: REGISTRO STORICO & STATO DI AVANZAMENTO (HANDOVER LOG)

> **Documento di Continuità Operativa:** Questo file deve essere letto all'inizio di ogni sessione da qualsiasi IA/agente e aggiornato obbligatoriamente al termine di ogni modifica significativa.

---

## 0. RIPARTENZA RAPIDA (leggere per primo)

**Dove siamo.** Il motore di combattimento e' completo, bilanciato e verificato su emulatore.
**Piazza Grande si esplora**: il giocatore cammina, collide, attraversa i varchi, entra in
battaglia e ne torna con HP e Fervore intatti — round-trip verificato su emulatore (Sessione
11b). Tutta la grafica e' ancora **segnaposto**. Restano da fare: salvataggio su FRAM
(Passi 7-8), font italiano (15), dialoghi e quest (16-18), animazioni di battaglia (19-21).

**Come si compila e si prova.** La toolchain NON e' installata a livello di sistema: le variabili
d'ambiente le imposta lo script, non il PATH.

```bash
bash tools/build_rom.sh                 # build + gate zero-heap automatico
python tests/test_battle_engine.py      # 31 test, mirror fedele del motore C++
python tests/test_assets.py             # 6 test sugli asset di graphics/
python tests/test_save_system.py        # 9 test su CRC32 e sul .sav prodotto da mGBA
python tests/test_dialogue_quest.py     # 6 test sul copione e sulle quest
bash tools/build_rom.sh "USERFLAGS=-DGUBBIO_BATTLE_AUTOTEST"   # ROM che si autogioca
```

* Emulatore: `C:/Users/cioti/mGBA-0.10.5/mGBA.exe`. La build console `mgba-sdl.exe` stampa i
  `BN_LOG` su stdout ed e' il modo con cui si collauda **senza guardare lo schermo**. Per
  catturarlo: `timeout 200 mgba-sdl.exe gubbio1151.gba > log.txt 2>&1` **in primo piano**.
  Lanciarlo in background e poi ucciderlo restituisce un file vuoto — il buffer non viene mai
  scaricato, e per due sessioni si e' creduto che l'emulatore non stampasse nulla.

### Comandi da tastiera: WASD

Il Game Boy Advance non ha una tastiera. La ROM legge i **tasti hardware** (croce direzionale,
A, B, L, R, Start, Select) e non sa nulla di come siano mappati: la corrispondenza vive
nell'emulatore, non nel C++. Su richiesta del committente (Sessione 20) le frecce sono state
sostituite da WASD in `C:/Users/cioti/mGBA-0.10.5/config.ini`, sezione `[gba.input.QT_K]`:

| Tastiera | Tasto GBA | A cosa serve nel gioco |
| :-- | :-- | :-- |
| `W` `A` `S` `D` | croce direzionale | camminare |
| `K` | **A** | parlare, confermare, avanzare il dialogo |
| `J` | **B** | correre (tenuto), annullare |
| `Q` / `E` | L / R | non ancora usati |
| `Invio` | Start | — |
| `Backspace` | Select | salvare su FRAM |

`L` e `R` sono stati spostati su `Q` ed `E` perche' stavano proprio su `A` e `S`, che ora
servono alla croce direzionale. Il formato del file ammette **un solo tasto per pulsante**:
attivando WASD le frecce smettono di funzionare, non si sommano. La copia precedente e' in
`config.ini.prima-di-wasd`.

Due avvertenze che valgono la pena di essere scritte:

* La modifica riguarda **l'emulatore, non il progetto**: vale per ogni ROM aperta con questo
  mGBA, e non e' versionata perche' quel file sta fuori dal repository. Questa tabella e' la
  sua unica copia di sicurezza dentro il progetto.
* Il frontend **SDL** (`mgba-sdl.exe`) ha una sezione di binding propria e separata, che NON e'
  stata toccata: li' l'input dell'autotest viene iniettato via `bn::core::init(keypad_commands)`
  e non passa dalla tastiera, quindi rimapparla non servirebbe a nulla.
* Quando il gioco scrive «premi A» intende sempre il **pulsante A del GBA**, che ora sta sul
  tasto `K`. I testi non vanno cambiati: nominano l'hardware, non la tastiera.
* Toolchain: `C:/Users/cioti/devkitPro` (installata estraendo i pacchetti pacman ufficiali, senza
  privilegi di amministratore). Butano: `../butano`, accanto al progetto.
* Anteprima della schermata fuori dall'emulatore: `python tools/preview_battle_screen.py`.

## PUNTO DI RIPRESA — fine Sessione 23 (25 agosto 2026)

**Cinque gruppi di test verdi, e la verifica su VRAM e zero-heap e' finalmente girata.**

**Il dialogo con un NPC e' collaudato a runtime, per la prima volta.** L'autotest di
esplorazione ora sale dal centro della piazza al Podesta' Guido premendo A ogni quattro frame, e
gli fa scorrere tutte e cinque le battute: `PARLA CON Podesta' Guido (atto 1, script 0, 5
battute)`, zero assert. E' la prima prova che la correzione UTF-8 della Sessione 18 regge — il
crash "Invalid character" nasceva dal fatto che la finestra taglia le righe ai confini degli
SPRITE, misurati in pixel, che non sanno nulla della codifica.

**Quel che resta aperto:**

1. **`_refresh_timeline` legge il modello gia' risolto**, non gli eventi: durante le animazioni
   la timeline mostra l'ordine del round successivo invece di quello in corso. Segnalato dalla
   verifica sulla firma dell'HUD, non corretto.
2. **`_soggetto()` maschera in silenzio uno slot fuori intervallo** ripiegando sull'indice 0
   (`src/battle_hud.cpp:336`). E' la stessa forma del difetto di `actor_slot` appena chiuso: un
   valore sbagliato verrebbe di nuovo mappato sul primo attore senza lasciare traccia. Con
   `_enemy_sprites` vuoto anche l'indice 0 e' fuori intervallo e fa scattare l'assert di
   `bn::ivector::operator[]` — oggi irraggiungibile, perche' ogni incontro ha almeno un nemico.
3. **`BARRIER_ABSORB` e `GUARD_REDIRECT` sono codice morto**: dichiarati, con una durata di
   riproduzione e un ramo nell'animatore, e mai emessi dal motore. `_redirect_if_guarded` sposta
   il colpo senza lasciare evento, quindi il giocatore non vede che il Bastione ha parato.
4. **Il cursore bersaglio si nasconde sulle abilita' a bersaglio alleato** invece di puntare
   l'alleato: Muro della Fede e Bastione Azzurro si lanciano senza vedere su chi.
5. **I gettoni della timeline con nove unita' cadono dentro la fascia HUD** (y 132 su una fascia
   che parte a 112). Oggi nessun incontro ne ha nove.
6. **L'autotest non chiude l'anello camminando**: arriva a cinque aree in fila. La topologia e'
   pero' verificata per intero da `tests/test_mondo.py`, che legge `MAPS[]` invece di percorrerla.

**Le quattro regole che questo progetto ha imparato a sue spese:**

0. **I log e le anteprime non sostituiscono il GIOCARE.** Alla Sessione 18 l'autotest riportava
   "zero assert, ciclo completo verificato" — ed era vero, la logica funzionava. Tre minuti di
   gioco vero hanno poi mostrato che il suolo era nel posto sbagliato, la cornice del dialogo 48
   px sopra il suo testo, e che una battuta con meno di tre righe faceva crashare il gioco. Un
   oracolo che legge solo testo non puo' accorgersi di dove stiano le cose sullo schermo:
   **prima di dire che un passo e' finito, la ROM va giocata.**

1. **Un oracolo che non puo' fallire non e' un oracolo.** L'autotest ha riportato "zero assert"
   per due sessioni mentre eseguiva un terzo dei round (Sess. 07F). Ogni controllo nuovo va fatto
   fallire di proposito almeno una volta prima di fidarsene.
2. **Compilare in incrementale nasconde i warning.** Rifare `clean` periodicamente (Sess. 10C).
3. **Il GDD si contraddice spesso.** Quando succede: scegliere motivando, e **correggere anche il
   GDD** con nota di revisione, altrimenti la sessione dopo ripristina il valore vecchio (Sess. 02b).

**Il prossimo passo** e' il **Passo 18** di [`docs/piano_fase_successiva.md`](./docs/piano_fase_successiva.md):
`dialogue_runner.h`, l'esecutore di script (LINE, CHOICE, SET_FLAG, JUMP_IF_FLAG, START_QUEST,
ADVANCE_QUEST, GIVE_ITEM, END) agganciato all'esplorazione, con gli NPC visibili sulla mappa e
l'interazione su tasto A. I Passi 0-8 e 10-17 sono fatti.
Due cose gia' pronte per il 18: le tabelle del copione e degli NPC (`dialogue_data.h`,
`npc_registry.h`) con la regola prima-corrispondenza-vince gia' implementata e verificata a
compile time, e il motore del testo che recita una battuta per volta. Restano da fare: la
sequenza di battute di uno script, gli sprite degli NPC sulla mappa, e la sostituzione del
trigger provvisorio su tasto R.

**Decisioni aperte che spettano al designer.** Nessuna blocca il Passo 7, ma tutte prima o poi si
presentano:

* Chi produce la **pixel art** vera? E' il collo di bottiglia dichiarato.
* L'**Alzata Trionfale e' la "Mossa Suprema dei Tre Ceri"** della Sez. 12A? Scioglie il conflitto
  12A/12C — vedi [`docs/piano_combo_tre_ceri.md`](./docs/piano_combo_tre_ceri.md).
* I boss agiscono **1 o 2 volte per turno**? Sez. 26 contro Sez. 13D: con due, il duello con
  Corrado va ritarato — vedi [`docs/piano_ia_boss.md`](./docs/piano_ia_boss.md).
* ~~Il **font non ha le lettere accentate italiane**~~ — **CHIUSA nella Sessione 12**: font 8x8 proprio del progetto con le 12 accentate italiane (`tools/make_font.py`).

**CHIUSA nella Sessione 15:** l'anacronismo. Si riproducono tutti i monumenti, anche quelli
posteriori al 1151 — conta che un eugubino riconosca la propria citta' (GDD Sez. 23, nota datata).

**CHIUSA nella Sessione 15:** Piazza Grande non e' in scala, **e va bene cosi'**. Decisione del
committente: compromessi per la giocabilita', purche' resti l'illusione. Tradotta in regola
verificabile in [`include/city_reference.h`](./include/city_reference.h) — **la scala vincola gli
EDIFICI (1,5 m/tile, entro un tile), non le DISTANZE (comprimibili, oggi al 73%)**; ordine e
adiacenze restano vincolanti.

**Due decisioni maturate con Piazza Grande, che ora chiedono una risposta** (dettagli in Sess. 11b):

* **Come si entra in battaglia dall'overworld?** Nessuna sezione del GDD lo dice. Oggi c'e' un
  trigger PROVVISORIO sul varco occidentale, messo li' per poter collaudare il round-trip: va
  sostituito, non ereditato.
* **Copertura del foreground della piazza** (occlusione su tutta l'altezza contro fascia alta):
  vincola dove possono stare i palazzi, quindi va decisa **prima** di disegnare l'arte vera.

## 1. Stato Generale del Progetto
* **Piattaforma:** Game Boy Advance (ARM7TDMI 32-bit)
* **Framework:** Butano Engine (C++20) / devkitARM
* **Target:** 32MB Flash ROM + 256Kbit FRAM Non-Volatile Save
* **Documento di Design Master:** [`GUBBIO_1151_LA_BIBBIA_GDD.md`](./GUBBIO_1151_LA_BIBBIA_GDD.md)
* **Regole & Vincoli AI:** [`AGENTS.md`](./AGENTS.md)

---

## 2. Architettura & Componenti Attualmente Implementati

| Componente | File Sorgente / Header | Descrizione & Stato |
| :--- | :--- | :--- |
| **Statistiche Eroi** | [`include/hero_data.h`](./include/hero_data.h) | Dati canonicizzati per Sant'Ubaldo, San Giorgio, Sant'Antonio (HP, Fervore, Atk, Def, **ResMistica**, Fede, Fuoco, Vel). |
| **Battle Engine** | [`include/battle_engine.h`](./include/battle_engine.h) | `BattleUnit`, tabella `SKILLS` in ROM, formule di danno Sez. 13C, moltiplicatori elementali, costanti Fervor Boost / BREAK / Ustione. |
| **Database Nemici** | [`include/enemy_data.h`](./include/enemy_data.h) | Tabelle `constexpr` di nemici (Fante, Balestriere, Corrado) e incontri, con Punti Scudo, debolezze e resistenze. |
| **Battle Scene FSM** | [`include/battle_scene.h`](./include/battle_scene.h) / [`src/battle_scene.cpp`](./src/battle_scene.cpp) | Macchina a stati completa: selezione comandi dei 3 eroi, timeline per Velocita', Shield Break, Fervor Boost x1/x2/MAX, IA nemica, tick di Ustione. |
| **FRAM Save System** | [`include/save_data.h`](./include/save_data.h) / [`src/save_system.cpp`](./src/save_system.cpp) | Involucro congelato (276 B) con magic `G115`, versione, contatore, payload riservato e checksum; 2 slot x 2 banche in ping-pong, rilettura di verifica, nessun auto-format. **Verificato su `.sav` reale.** |
| **CRC32** | [`include/save_crc32.h`](./include/save_crc32.h) | Tabella a nibble (64 B di ROM) derivata dal polinomio a compile time; vettore di prova standard in `static_assert`. |
| **Test Salvataggio** | [`tests/test_save_system.py`](./tests/test_save_system.py) | 9 test: CRC del progetto contro `zlib`, e ispezione del `.sav` prodotto da mGBA. |
| **Audio Trigger** | [`include/campanone_audio.h`](./include/campanone_audio.h) | Metodi statici per rintocchi singoli e sequenza a doppi d'assedio del Campanone. |
| **Dialogue Engine** | [`include/dialogue_box.h`](./include/dialogue_box.h) | Macchina da scrivere per CODEPOINT (non per byte), contratto sulla durata delle view, `show_composed()` con buffer da 64 B, guardia re-entrante e `close()`. **Eseguito su emulatore.** |
| **Dialogue View** | [`include/dialogue_view.h`](./include/dialogue_view.h) / [`src/dialogue_view.cpp`](./src/dialogue_view.cpp) / [`tools/make_dialogue_frame.py`](./tools/make_dialogue_frame.py) | Cornice su BG0 (12 tile unici) e testo a sprite: si rigenera solo la coda in crescita, con il confine misurato in pixel. |
| **Collision Grid** | [`include/piazza_grande_collision.h`](./include/piazza_grande_collision.h) | Matrice 64x40 per Piazza Grande con trigger Consoli, Bargello, Porta Romana e Fontana dei Matti. `TileType`, `is_solid`, `is_transition`, `get_tile_type_px`, e `PIAZZA_GRID` derivata a compile time. |
| **Stato di Partita** | [`include/game_state.h`](./include/game_state.h) / [`src/game_state.cpp`](./src/game_state.cpp) | `GameState`, 140 byte in EWRAM: party, mappa, spawn, quest, inventario, bandiere, tempo di gioco. Zero padding, banalmente copiabile. |
| **Transizioni** | [`include/scene_fade.h`](./include/scene_fade.h) / [`src/scene_fade.cpp`](./src/scene_fade.cpp) | Primitive di dissolvenza su palette, senza ciclo: `apply(0-100)`, `reset()`. |
| **Orologio di Gioco** | [`include/game_clock.h`](./include/game_clock.h) | `gubbio::core_update()`: **unico** punto che chiama `bn::core::update()` e conta `playtime_frames`. |
| **Scena Battaglia** | [`include/scene_battle.h`](./include/scene_battle.h) / [`src/scene_battle.cpp`](./src/scene_battle.cpp) | Facade `Scene` che possiede modello e HUD per valore; esporta HP e Fervore nello stato di partita. |
| **Dati delle Mappe** | [`include/map_data.h`](./include/map_data.h) | `MAPS[]` in ROM: collisione, tileset, spawn point e trigger. Budget VRAM verificato da `static_assert` sui tile veri. |
| **Giocatore Overworld** | [`include/overworld_player.h`](./include/overworld_player.h) / [`src/overworld_player.cpp`](./src/overworld_player.cpp) | Hitbox 12x8 ai piedi, assi separati, 16 fotogrammi cached senza riallocazioni. |
| **Scena Esplorazione** | [`include/scene_exploration.h`](./include/scene_exploration.h) / [`src/scene_exploration.cpp`](./src/scene_exploration.cpp) | Parametrizzata da `MapId`: suolo, cielo in parallasse, camera clampata, trigger con debounce. |
| **Arte Piazza** | [`tools/make_piazza_art.py`](./tools/make_piazza_art.py) / [`tools/preview_piazza.py`](./tools/preview_piazza.py) | Segnaposto di Piazza Grande derivato dalla griglia di collisione, con controllo di colori e tile unici; anteprima 240x160 fuori emulatore. |
| **Main Loop** | [`src/main.cpp`](./src/main.cpp) | Entry point e **trampolino di scene**: `switch` su `SceneId` con la scena come variabile di scope. Avvia Piazza Grande (la battaglia sotto autotest). **Eseguito su mGBA.** |
| **Battle HUD** | [`include/battle_hud.h`](./include/battle_hud.h) / [`src/battle_hud.cpp`](./src/battle_hud.cpp) | Schermata di combattimento Sez. 14B.3: fondale, schieramenti, menu comandi, barre HP/Fervore, cursore bersaglio. |
| **Font Italiano** | [`tools/make_font.py`](./tools/make_font.py) / [`include/font_gubbio.h`](./include/font_gubbio.h) | Font 8x8 del progetto: 94 glifi ASCII di Butano + 12 accentate italiane derivate. Sostituisce `common_variable_8x8_sprite_font`, che ha solo accenti spagnoli. |
| **Grafica Segnaposto** | [`tools/make_placeholder_art.py`](./tools/make_placeholder_art.py) | Genera i 9 asset di `graphics/` nelle misure della Sez. 23A. Da sostituire con l'arte definitiva. |
| **Anteprima Schermata** | [`tools/preview_battle_screen.py`](./tools/preview_battle_screen.py) | Compone i 240x160 fuori dall'emulatore per iterare su layout e arte. |
| **Build Configuration** | [`Makefile`](./Makefile) | Makefile allineato alla convenzione Butano attuale (`LIBBUTANOABS`), ROM title `GUBBIO1151`. **Build verificata: produce `gubbio1151.gba`.** |
| **Build Script** | [`tools/build_rom.sh`](./tools/build_rom.sh) | Imposta le variabili della toolchain (non persistenti nel sistema) ed esegue `make`. Unico modo supportato di compilare. |
| **Asset Exporter** | [`tools/map_exporter.py`](./tools/map_exporter.py) | Parser Python da Tiled JSON a header `constexpr uint8_t` C++. |
| **Environment Setup** | [`tools/setup_environment.ps1`](./tools/setup_environment.ps1) | Script PowerShell per clone e verifica automatica toolchain. |
| **Identita' Mappe** | [`include/map_id.h`](./include/map_id.h) | `MapId` autoritativo, unica fonte di verita' per il `current_map_id` serializzato su FRAM. |
| **Stato Narrativo** | [`include/story_flags.h`](./include/story_flags.h) | 256 bandiere persistenti con intervalli riservati per modulo (storia / quest / boss / combo). |
| **Contratto Scene** | [`include/scene.h`](./include/scene.h) | `Scene`, `SceneId`, `SceneRequest`. Distruttore non virtuale e protected (C.35): contratto senza `operator delete` in ROM. |
| **Consumabili** | [`include/item_data.h`](./include/item_data.h) | I 5 oggetti della Sez. 8E in ROM, con `static_assert` sul tetto del Baccala' e sull'esclusione dello Shield Break dalle cure. |
| **Gate Zero-Heap** | [`tools/check_zero_heap.sh`](./tools/check_zero_heap.sh) | Ispeziona i simboli dell'ELF a ogni build. **Prova negativa eseguita: diventa rosso su violazione.** |
| **Test Asset** | [`tests/test_assets.py`](./tests/test_assets.py) | Valida i `.bmp` di `graphics/` contro i `.json`: 4bpp, misure OBJ/BG legali, conformita' Sez. 23A. |
| **Controllo di Versione** | [`.gitignore`](./.gitignore) / [`.gitattributes`](./.gitattributes) | Repository git inizializzato nella Sessione 11d. Esclusi build, ROM, ELF e `.sav`; gli `.sh` sono forzati a fine riga LF perche' Git Bash non esegue script con CRLF. |
| **Skill Decisioni** | `.agents/skills/decisioni-aperte/SKILL.md` (+ copia in `.claude/`) | Procedura per sciogliere UNA decisione di design aperta: round sulla frontiera, prove dal GDD, chiusura obbligatoria in GDD + HANDOVER + codice. |
| **Scala della Citta'** | [`include/city_reference.h`](./include/city_reference.h) | La regola dell'illusione: edifici in scala entro un tile, distanze comprimibili al 73%, adiacenze vincolanti. Verificata da `static_assert` sui monumenti della Sez. 23. |
| **Foto -> Tile** | [`tools/photo_to_tiles.py`](./tools/photo_to_tiles.py) | Converte fotografie in pixel art indicizzata: palette per famiglia, fusione dei tile fino a rientrare nel budget, `solo_indici` per forzare una tinta. **E' la risposta al progetto senza budget.** |
| **Riferimenti Reali** | [`docs/riferimenti/FONTI.md`](./docs/riferimenti/FONTI.md) / [`tools/fetch_riferimenti.py`](./tools/fetch_riferimenti.py) | I 30 monumenti della pianta ufficiale, classificati, con i tre segni distintivi per la pixel art e le fonti Commons. Immagini non versionate. |
| **Piani non implementati** | [`docs/`](./docs/) | `piano_ia_boss.md` (Sez. 26), `piano_combo_tre_ceri.md` (Sez. 12C), `piano_fase_successiva.md` (23 passi). |
| **Runner Dialoghi** | [`include/dialogue_runner.h`](./include/dialogue_runner.h) | Esegue uno script battuta per battuta con due interi di stato; interazione su tasto A entro 12 px da un NPC. |
| **Copione & NPC** | [`tools/dialogue_exporter.py`](./tools/dialogue_exporter.py) / [`include/dialogue_data.h`](./include/dialogue_data.h) / [`include/npc_registry.h`](./include/npc_registry.h) | Battute della Sez. 31B con word-wrap **in pixel**, script come intervalli, NPC con regola prima-corrispondenza-vince. Tabelle generate, mai scritte a mano. |
| **Quest** | [`include/quest_data.h`](./include/quest_data.h) | Le 5 quest della Sez. 31A legate a `quest_state`/`quest_counter`; ricompense segnaposto finche' non esiste l'equipaggiamento. |
| **Test Copione** | [`tests/test_dialogue_quest.py`](./tests/test_dialogue_quest.py) | 6 test: header allineato al copione, righe dentro il box, nessun apostrofo al posto di un accento, parlanti esistenti, obiettivi conformi al GDD. |
| **Combat Test Harness** | [`tests/test_battle_engine.py`](./tests/test_battle_engine.py) | Port fedele in Python del Battle Engine C++: 31 unit test su formule, Shield Break, timeline, Fervore, status e IA. |

---

## 3. Log delle Sessioni e Cronologia Modifiche

### [2026-08-15 19:25] - Sessione 01: Setup Iniziale, Tooling, Skills e Regole
* **Autore / Agente:** Antigravity (Orchestrator)
* **Azioni Eseguite:**
  1. Analisi approfondita di [`GUBBIO_1151_LA_BIBBIA_GDD.md`](./GUBBIO_1151_LA_BIBBIA_GDD.md) (2419 righe).
  2. Registrazione subagenti specializzati: `gba_engine_architect` e `asset_pipeline_agent`.
  3. Creazione custom skills: `.agents/skills/butano-gba-dev/` e `.agents/skills/asset-pipeline/`.
  4. Redazione regole ferree di memoria e compilazione in [`AGENTS.md`](./AGENTS.md).
  5. Scrittura primi header C++20 (`hero_data.h`, `save_data.h`, `campanone_audio.h`, `dialogue_box.h`, `piazza_grande_collision.h`).
  6. Realizzazione ed esecuzione test harness `tests/test_battle_engine.py` (Esito: OK 2/2 test superati).
  7. Istituzione protocollo di handover permanente e tracciabilità continua.

### [2026-08-16] - Sessione 02: Battle Scene Loop in C++20

* **Autore / Agente:** Claude Opus 5 (Claude Code)
* **File creati:** `include/battle_engine.h`, `include/enemy_data.h`, `include/battle_scene.h`, `src/battle_scene.cpp`
* **File modificati:** `include/hero_data.h` (aggiunto campo `magic_resist`), `tests/test_battle_engine.py` (riscritto come port fedele del C++)

* **Azioni Eseguite:**
  1. Implementata la FSM completa della Sezione 20B GDD: `INTRO_FADE_IN` -> selezione comandi Giorgio/Ubaldo/Antonio -> `EXECUTE_ROUND_ACTIONS` -> `CHECK_ROUND_OUTCOME` -> `VICTORY`/`DEFEAT`/`ESCAPED`.
  2. Timeline degli ordini: insertion sort stabile e decrescente su `velocita' + priorita' abilita'`, senza allocazioni.
  3. Shield Break completo: sottrazione Punti Scudo solo sull'elemento di debolezza, stato BREAK per 2 turni con Difesa **e** Resistenza dimezzate, salto turno e ricomposizione della barra scudo all'uscita.
  4. Fervor Boost x1/x2/MAX con costi 25/50/100 cumulati al costo dell'abilita'; il Boost x2 e' un doppio colpo reale (2 Punti Scudo), il Boost MAX colpisce tutto lo schieramento nemico.
  5. Aggiunti: IA nemica base (Sez. 13D), Ustione Alchemica con tick a fine round, Muro della Fede con barriera assorbente, accumulo Fervore per i tre Ceri (Sez. 12A).

* **Decisioni Tecniche (conflitti del GDD risolti esplicitamente):**
  * **Formula di danno:** adottata la Sezione 13C (`⌊(Atk×2 − Def)/2⌋ × Mod`) e **non** la Sezione 12B/12E (`(Atk×2 − Def) × Mod`), perche' la 13C e' la passata di bilanciamento successiva ed e' intitolata "FORMULE STANDARDIZZATE". Il moltiplicatore elementale della Sez. 13A e' applicato sia al fisico sia al mistico.
  * **Ordine del party:** l'array `HEROES` resta `[Ubaldo, Giorgio, Antonio]` mentre l'ordine di *selezione comandi* e' Giorgio -> Ubaldo -> Antonio (Sez. 20B). Lo pseudocodice del GDD alla Sez. 20C usa `handle_command_input(0, ...)` per Giorgio: e' errato rispetto a `HEROES[0]`, qui la mappatura stato -> indice e' esplicita.
  * **`magic_resist`:** assente dalla Sez. 5, derivata applicando alla Difesa Fisica il rapporto Resistenza/Difesa della curva Sez. 13B (Ubaldo 72, Giorgio 40, Antonio 56). **Valore da confermare in fase di bilanciamento.**
  * **`current_status` derivato:** con un solo slot di stato, applicare un'Ustione a un nemico gia' in BREAK ne sovrascriveva l'etichetta. Il campo e' ora ricalcolato da `break_turns`/`burn_stacks` via `refresh_status()`, con precedenza al BREAK.
  * **Varianza RNG:** la `RNG(0.9-1.1)` della Sez. 12B e' applicata in fase di esecuzione (`_apply_variance`) e non dentro `calculate_damage`, che resta deterministico e verificabile dal test harness.
  * **Riferimenti alle unita':** `UnitRef{is_enemy, slot}` al posto dei `BattleUnit*` dello pseudocodice GDD, per evitare puntatori pendenti nei `bn::vector`.
  * **Fervore iniziale:** le barre partono piene. Il carry-over dal salvataggio FRAM e' una decisione di design ancora aperta (vedi Prossimi Passi).

* **Esito dei Test:**
  * `python tests/test_battle_engine.py` -> **OK, 23/23 test superati.**
  * **Build ROM NON verificata:** su questa macchina non sono installati devkitARM/devkitPro ne' Butano (`BUTANO_PATH` non definito, nessun compilatore C++ nel PATH). Il codice C++20 e' stato validato solo staticamente (corrispondenza dichiarazioni/definizioni, bilanciamento dei blocchi, coerenza delle firme). **La prima compilazione reale va considerata un passo di verifica ancora da eseguire.**

### [2026-08-16] - Sessione 02b: Riconciliazione della Scala del Fervore

* **Autore / Agente:** Claude Opus 5 (Claude Code)
* **File modificati:** `include/hero_data.h`, `include/battle_engine.h`, `include/battle_scene.h`, `tests/test_battle_engine.py`, **`GUBBIO_1151_LA_BIBBIA_GDD.md`** (Sez. 5 e Sez. 12A)

* **Problema risolto:** i due nodi di bilanciamento aperti dalla Sessione 02 — Boost MAX irraggiungibile per San Giorgio, e la contraddizione fra la barra `0-100` della Sez. 12A e i massimali `180/70/210` della Sez. 5.

* **Decisione e sua motivazione:** le prove nel GDD sono asimmetriche. I pool per-eroe compaiono in **una** sede (Sez. 5), mentre la scala `0-100` e' corroborata da **tre** (Sez. 12A esplicita, costi assoluti 25/50/100 della Sez. 20A, HUD a percentuali della Sez. 14B.3). Si e' quindi mantenuta la scala assoluta per i costi e i pool differenziati della Sez. 5, riconoscendo lo `0-100` per cio' che coerentemente e': **la scala normalizzata di visualizzazione**.

* **Azioni Eseguite:**
  1. Fervore massimo di San Giorgio: **70 -> 120**. Il valore non e' arbitrario: 100 (Boost MAX) + 20 (`Fendente del Drago`) = 120, quindi la sua Suprema costa *esattamente l'intera barra*, restituendo letteralmente la frase della Sez. 12A "consumano l'intera barra". Resta il pool piu' basso dei tre: la sua identita' di Cero meno mistico ora e' portata dal tasso di accumulo (+15 per colpo incassato) e non dal tetto.
  2. Aggiunto `BattleUnit::fervor_percent()`: la scala `0-100` diventa una proiezione reale nel codice, non un commento. E' l'unico valore che l'HUD deve disegnare.
  3. Aggiunte tre `static_assert` in `battle_scene.h` (via `supreme_is_reachable()`): poiche' `HEROES` e' `constexpr` in ROM, un futuro ritocco che rendesse di nuovo irraggiungibile una Mossa Suprema **rompe la build** invece di passare inosservato. E' la garanzia che questo bug non possa ripresentarsi in silenzio.
  4. **Allineato il GDD master:** aggiornata la tabella `HEROES` della Sez. 5 (nuovo campo `magic_resist` + Giorgio 120) con nota di revisione, e inserito in Sez. 12A il chiarimento sulla scala. Senza questo passo la riconciliazione non sarebbe durevole: la sessione successiva avrebbe letto `70` nel documento master e lo avrebbe ripristinato.

* **Esito dei Test:** `python tests/test_battle_engine.py` -> **OK, 25/25 test superati** (2 nuovi: invariante della Mossa Suprema per tutti e tre i Ceri, e scala normalizzata di visualizzazione). Build ROM tuttora non verificata: vedi Prossimi Passi punto 1.

### [2026-08-16] - Sessione 02c: Fervore d'Ingresso, Toolchain e Prima Build Reale

* **Autore / Agente:** Claude Opus 5 (Claude Code)
* **File creati:** `tools/build_rom.sh`
* **File modificati:** `include/battle_scene.h`, `src/battle_scene.cpp`, `include/campanone_audio.h`, `Makefile`, `tests/test_battle_engine.py`, `GUBBIO_1151_LA_BIBBIA_GDD.md` (Sez. 12A)

* **A. Fervore d'ingresso dalle percentuali HUD.** Le percentuali del mockup della Sez. 14B.3 sono promosse da esempio grafico a dato canonico: `HERO_START_FERVOR_PERCENT = {80, 45, 20}` (Ubaldo 144/180, Giorgio 54/120, Antonio 42/210). I Ceri non entrano piu' a barra piena, quindi le Mosse Supreme vanno guadagnate in combattimento: San Giorgio raggiunge la sua incassando 5 colpi (+15 ciascuno), come da suo ruolo di tank. Unica eccezione: Sant'Ubaldo entra gia' sopra il proprio costo MAX (144 contro 125).

* **B. Toolchain installata (senza privilegi di amministratore).** L'installer ufficiale devkitPro e' una GUI che richiede elevazione UAC, non utilizzabile in sessione non interattiva. Si e' quindi usata la via dei pacchetti pacman ufficiali, estratti a mano:
  * **Percorso:** `C:\Users\cioti\devkitPro\opt\devkitpro` — **non** e' un'installazione di sistema, non esporta variabili d'ambiente globali.
  * **Contenuto:** devkitARM r68 (arm-none-eabi-gcc **16.1.0**), binutils 2.46, newlib, crtls, rules, general-tools, gba-tools, grit, mmutil. ~92 MB scaricati da `pkg.devkitpro.org`.
  * **GNU Make 4.4.1** dal repo MSYS2 (`repo.msys2.org`), estratto in `C:\Users\cioti\devkitPro\usr\bin`: gira sotto Git Bash perche' ne condivide il runtime `msys-2.0.dll`.
  * **Butano** clonato in `C:\Users\cioti\Desktop\PROGETTI\butano` (come previsto dal Makefile).
  * **Uso:** `bash tools/build_rom.sh` — lo script imposta le variabili d'ambiente, che *non* sono persistenti nel sistema. `tools/setup_environment.ps1` e' ora parzialmente superato: indica ancora l'installer GUI.

* **C. Due correzioni necessarie per far compilare il progetto** (entrambe difetti preesistenti, non introdotti dalla Battle Scene):
  1. **`Makefile`**: usava `BUTANO_PATH` + `include $(BUTANO_PATH)/butano.mak`, convenzione superata. Il `butano.mak` attuale risolve i propri sotto-makefile via `LIBBUTANOABS`, che il progetto deve esportare; senza, il build muore con `No rule to make target '/butano_dka.mak'`. Allineato al template ufficiale mantenendo TARGET/ROMTITLE/ROMCODE e l'override `BUTANO_PATH`.
  2. **`include/campanone_audio.h`**: includeva incondizionatamente `bn_sound_items.h`, che Butano **genera solo in presenza di asset audio**. Con `audio/` vuota l'header non esiste e la compilazione si interrompe. L'include e' stato commentato (le chiamate sonore che lo userebbero erano gia' commentate) con nota per riattivarlo insieme ai campioni.
  * Create le cartelle `graphics/`, `audio/`, `dmg_audio/`, richieste dalla pipeline asset di Butano anche se vuote.

* **Esito dei Test — la build ROM non e' piu' un passo pendente:**
  * **`bash tools/build_rom.sh` -> ROM `gubbio1151.gba` prodotta (81 KB), header `GUBBIO1151` / codice `GU11`.** Verificata anche la ricostruzione da zero dopo `rm` dell'artefatto.
  * **`battle_scene.cpp` compila pulito**: `-Wall -Wextra`, zero diagnostiche attribuibili ai file del progetto. Nessuna delle firme Butano temute nella Sessione 02 (`bn::random::get_int`, `bn::vector::size`, gli initializer designati, l'insertion sort sui `bn::vector`) ha richiesto correzioni.
  * **Le tre `static_assert` di bilanciamento sono state validate da un compilatore reale**, e si e' verificato che non siano vacue: compilando `static_assert(!supreme_is_reachable(PARTY_GIORGIO))` la build fallisce come atteso, prova che la guardia valuta davvero le tabelle in ROM.
  * `python tests/test_battle_engine.py` -> **OK, 27/27 test superati** (2 nuovi: Fervore d'ingresso HUD, e Giorgio che guadagna la Suprema incassando 5 colpi).
  * **Limite residuo:** la ROM compila e linka, ma `main.cpp` non richiama la Battle Scene, quindi la FSM **non e' mai stata eseguita**. Correttezza a runtime ancora da verificare su emulatore.
  * Nota informativa: Butano richiede oggi `-std=gnu++23` (usa `if consteval`), mentre `AGENTS.md` prescrive C++20. Il codice del progetto e' C++20 valido e compila sotto entrambi; e' la libreria a innalzare lo standard effettivo del build.

### [2026-08-16] - Sessione 02d: Aggancio al Main e Prima Esecuzione su Emulatore

* **Autore / Agente:** Claude Opus 5 (Claude Code)
* **File modificati:** `src/main.cpp` (riscritto), `Makefile` (aggiunta la libreria `common` di Butano)

* **Azioni Eseguite:**
  1. `src/main.cpp` non e' piu' la demo dei dialoghi: istanzia `BattleSceneManager`, avvia l'incontro `PATTUGLIA_PERUGINA` a livello 12 e ne esegue il ciclo di scena.
  2. Aggiunto un **tabulato testuale di collaudo** (font `common_variable_8x8_sprite_font` di Butano): stato FSM, round, HP/Fervore%/scudo di ogni Cero, HP/Punti Scudo/BREAK/Ustione di ogni nemico, comando e Boost selezionati. **Non e' l'HUD della Sez. 14B.3**, che resta un task a se': serve a rendere osservabile la FSM. Il tabulato viene ridisegnato solo quando cambia una firma dello stato, per non generare decine di sprite di testo a ogni frame.
  3. Aggiunta una traccia `BN_LOG` di stato iniziale e transizioni, leggibile da mGBA.
  4. `Makefile`: aggiunti `../butano/common/{src,include,graphics}`, necessari per i font. Da rimuovere quando l'HUD avra' asset propri.

* **Emulatore installato:** mGBA 0.10.5 portabile (7z ufficiale, nessun privilegio di amministratore) in `scratchpad/mgba/`. La build `mgba-sdl.exe` inoltra l'output `BN_LOG` su stdout, il che rende la verifica automatizzabile e testuale invece che affidata a uno screenshot.

* **Esito dei Test — la ROM e' stata eseguita su emulatore:**
  ```
  === GUBBIO 1151: avvio Battle Scene ===
  EROE Sant'Ubaldo   HP 240/240  FERVORE 144/180 (80%)
  EROE San Giorgio   HP 380/380  FERVORE  54/120 (45%)
  EROE Sant'Antonio  HP 210/210  FERVORE  42/210 (20%)
  NEMICO Fante di Perugia    HP 228  SCUDO 2
  NEMICO Fante di Perugia    HP 228  SCUDO 2
  NEMICO Balestriere Pesante HP 456  SCUDO 3
  STATO -> CMD GIORGIO (round 1)
  TABULATO ridisegnato: 48/112 sprite
  ```
  * **Provato su ARM7TDMI emulato:** `init_battle` popola party e formazione nemica esattamente come da tabelle in ROM; il Fervore d'ingresso e' 144/54/42, cioe' l'80/45/20% deciso nella Sessione 02c; la FSM entra in `SELECT_COMMAND_GIORGIO`; il tabulato si disegna in 48 sprite sui 112 disponibili; **zero assert, zero errori, nessun crash in ~720 frame**.
  * **NON ancora provato a runtime:** il ramo `EXECUTE_ROUND_ACTIONS` (danno, Shield Break, consumo Fervore). Richiede la pressione del tasto A e mGBA 0.10.5 non espone input programmabile da riga di comando; la sessione non interattiva non consente di inviare tasti. Quella logica resta verificata dai 27 test del mirror Python e dalla sola compilazione. Vedi Prossimi Passi punto 1.
  * `python tests/test_battle_engine.py` -> **OK, 27/27**. Build da zero -> ROM 81 KB (ora ~**118 KB** con font e tabulato).

### [2026-08-16] - Sessione 02e: Esecuzione Automatizzata della Battle Loop su Emulatore

* **Autore / Agente:** Claude Opus 5 (Claude Code)
* **File modificati:** `src/main.cpp` (autotest keypad opzionale)
* **Installato:** `devkitARM-gdb 14.1`, mGBA 0.10.5 spostato in posizione stabile `C:\Users\cioti\mGBA-0.10.5`

* **L'iniezione su KEYINPUT NON funziona su mGBA — spiegazione:** lo stub GDB e' stato installato e collegato con successo (96 hit del breakpoint su `bn::keypad_manager::update()`), ma scrivere `0x04000130` non ha alcun effetto: **mGBA sintetizza KEYINPUT in lettura dallo stato interno dell'input invece di restituire il contenuto della memoria**, quindi il valore iniettato viene ignorato. Da sapere anche: il frontend **SDL non riesce ad aprire la socket** del server GDB su Windows ("Debugger: Couldn't open socket"); funziona solo il frontend **Qt** (`mGBA.exe -g`), che pero' non stampa `BN_LOG` su stdout — serve `-C logToFile=1 -C logFile=<path>`.

* **Soluzione adottata (migliore della richiesta originale):** Butano possiede gia' un **replay dei tasti nativo**, `bn::core::init(keypad_commands)`: due caratteri per frame, 5 bit bassi e 5 alti della maschera tasti, codificati come `'0' + valore`. Non richiede ne' emulatore ne' debugger, ed e' deterministico e riproducibile. Attivato in `main.cpp` dietro la macro **`GUBBIO_BATTLE_AUTOTEST`**, disattivata di default (costo zero nella ROM di gioco):
  ```bash
  bash tools/build_rom.sh USERFLAGS=-DGUBBIO_BATTLE_AUTOTEST
  ```
  **Attenzione:** il `Makefile` assegna `USERFLAGS :=`, che ha la precedenza sulla variabile d'ambiente: il flag va passato come *argomento di make*, non come variabile d'ambiente. Inoltre make non traccia i define, quindi serve `touch src/main.cpp` (o `clean`) per forzare la ricompilazione.

* **Esito: la fase di esecuzione e' ora verificata a runtime.** Traccia reale su mGBA, 4+ round completi:
  ```
  STATO -> CMD GIORGIO / CMD UBALDO / CMD ANTONIO / EXECUTE / CHECK (round 1)
    Sant'Ubaldo HP 240 FER 139 BARR 315      <- Muro della Fede applicato, Fervore speso 144->139(+20 guadagno)
    Sant'Antonio HP 102 FER 42               <- bersagliato da tutti e tre i nemici
    Fante di Perugia HP 156                  <- 228-72: due attacchi fisici andati a segno
  ... round 3: Fante di Perugia HP 0         <- primo nemico abbattuto
  ```
  Sono cosi' provati sull'ARM7TDMI emulato: ciclo completo della FSM su piu' round, timeline, applicazione del danno, barriera assorbente di Sant'Ubaldo, accumulo/consumo di Fervore, morte di un'unita' e IA nemica. Nessun assert, nessun crash.

* **Due osservazioni emerse dalla traccia (da valutare in bilanciamento):**
  1. **Sant'Antonio muore al round 2** (210 -> 102 -> 0): l'IA della Sez. 13D fa colpire "il bersaglio con meno Difesa" e tutti e tre i nemici convergono su di lui (Def 28). La regola funziona come specificato, ma senza un meccanismo di taunt (`Bastione Azzurro` di Giorgio, Sez. 2) il mago viene eliminato subito. **Conseguenza:** lo Shield Break resta non verificato a runtime, perche' Antonio non arriva mai a lanciare il Fuoco.
  2. **Il Muro della Fede finisce su Sant'Ubaldo stesso** (BARR 315 su di lui), perche' il bersaglio alleato predefinito e' il lanciatore. Valutare se il default debba essere l'alleato con meno HP.

### [2026-08-16] - Sessione 03: Shield Break Verificato a Runtime e Rilievi di Bilanciamento

* **Autore / Agente:** Claude Opus 5 (Claude Code)
* **File modificati:** `src/main.cpp` (allineamento dello script di autotest, incontro parametrico)

* **A. Corretto il disallineamento dell'autotest.** Nella Sessione 02e il `GIU'`+`A` destinati a Sant'Antonio finivano su Sant'Ubaldo (che lanciava il Muro della Fede al posto del Fuoco). Causa: **due frame di scarto** precedono il primo comando utile — uno consumato da `bn::core::init()`, uno dallo stato `INTRO_FADE_IN`, che transita senza leggere input. Aggiunto `GUBBIO_AUTOTEST_ALIGN` ("0000") in testa allo script. L'incontro di collaudo e' ora selezionabile con `-DGUBBIO_AUTOTEST_ENCOUNTER=<id>`.

* **B. SHIELD BREAK VERIFICATO SU HARDWARE EMULATO** (incontro Pattuglia Perugina). Ciclo completo osservato nella traccia:
  ```
  round 1:  Fante di Perugia  SC 1  UST 1     <- il Fuoco toglie 1 Punto Scudo e applica Ustione
  round 3:  Fante di Perugia  SC 0  BRK 1     <- scudo esaurito: stato BREAK innescato
  round 4:  Fante di Perugia  SC 2  BRK 0     <- uscita dal BREAK: la barra si ricompone al massimo
  ```
  Verificati inoltre a runtime: consumo del Fervore di Antonio (42 -> 32 -> 22: -20 per lancio, +10 per tick di Ustione), accumulo cariche di Ustione, ritargeting dell'IA su Ubaldo dopo la morte di Antonio. **Con questo tutti i rami della FSM sono stati eseguiti almeno una volta.** Il dimezzamento della difesa in BREAK resta verificato dal solo mirror Python: il nemico era gia' a 0 HP quando si e' rotto.

* **C. Quattro rilievi di bilanciamento emersi dall'esecuzione** (nessuno risolto: sono decisioni di design che toccano il GDD).
  1. **L'Ustione Alchemica e' fuori scala e rende irrilevanti gli HP dei boss.** La Sez. 12D GDD prescrive "10% degli HP massimi per carica", cumulabile fino a 3: sono **30% degli HP massimi per round**, indipendentemente da quanto e' grosso il nemico. Traccia dell'incontro con Corrado (mini-boss, 1520 HP, che la Sez. 13D vuole al 400% di San Giorgio): **morto in 4 round**, di cui 456 danni/round dalla sola Ustione contro i ~139 di tutto il resto del party. Un danno percentuale sul massimo annulla per costruzione ogni dimensionamento delle riserve di HP dei boss.
  2. **I 4 Punti Scudo di Corrado sono di fatto irrompibili.** Solo Sant'Antonio infligge FLAME, ossia 1 Punto Scudo per lancio, e la sua economia di Fervore (42 iniziali, -20 per lancio, +10 per tick) consente ~3 lanci prima di esaurirsi. Il BREAK — meccanica cardine della Sez. 20A — non si attiva mai sul boss per cui e' pensata.
  3. **La debolezza del Balestriere Pesante e' inutilizzabile:** e' debole a FAITH_HOLY, ma nessun membro del party possiede un'abilita' *offensiva* di quell'elemento (il Muro della Fede di Ubaldo e' un supporto senza danno). Il suo scudo non e' rompibile con il set di abilita' attuale.
  4. **Sant'Antonio muore sistematicamente al round 3.** L'IA della Sez. 13D concentra il fuoco sul bersaglio con meno Difesa e nessun meccanismo di taunt esiste ancora: il `Bastione Azzurro` di San Giorgio (Sez. 2 GDD) e' la contromisura prevista dal design ma non implementata.
  * Nota correlata: la Sez. 26A GDD descrive Corrado come "immune al danno da taglio finche' non viene applicata l'Ustione". E' implementato come *resistenza* al fisico (x0.5) e non come immunita' condizionata allo status: da riconciliare insieme al punto 1.

* **Esito dei Test:** ROM ricostruita in versione di gioco (116 KB), `python tests/test_battle_engine.py` -> **OK, 27/27**.

### [2026-08-16] - Sessione 04: Passaggio di Bilanciamento (tutti e quattro i rilievi risolti)

* **Autore / Agente:** Claude Opus 5 (Claude Code)
* **File modificati:** `include/battle_engine.h`, `include/battle_scene.h`, `src/battle_scene.cpp`, `src/main.cpp`, `tests/test_battle_engine.py`, `GUBBIO_1151_LA_BIBBIA_GDD.md` (Sez. 2 e Sez. 12B)

* **1. Ustione Alchemica: da percentuale ad assoluto** (decisione dell'utente). Il danno per carica e' ora `25% del Potere Mistico di chi la applica`, **fotografato all'applicazione** (l'incendio appiccato in quel momento, non un effetto che insegue le statistiche del lanciatore). Con Antonio a 95 di Potere Mistico sono 23 per carica, 69 con 3 cariche. GDD Sez. 12B aggiornata con nota di revisione.

* **2. `Giudizio della Verga`, nuova abilita' di Sant'Ubaldo** (FAITH_HOLY offensiva, 20 Fervore, danno base 35). Era l'unica abilita' sacra *offensiva* del party e senza di essa la debolezza del Balestriere Pesante non era sfruttabile da nessuno. GDD Sez. 2 aggiornata.

* **3. `Bastione Azzurro` implementato** (15 Fervore, priorita' +8 perche' la guardia deve alzarsi prima che i nemici agiscano). Era gia' canonico nella Sez. 2 GDD ma mancava nel codice: San Giorgio intercetta i colpi diretti a Ubaldo e Antonio per il round in cui lo attiva, e la parata gli genera Fervore (+15, Sez. 12A).

* **4. Costo del `Fuoco di Sant'Antonio` da 20 a 15** (resta nell'intervallo 15-35 della Sez. 12A). Con il guadagno di +10 per tick l'economia diventa -5 netti per round invece di -10: Antonio sostiene abbastanza lanci da erodere i 4 Punti Scudo di un boss.

* **Menu abilita' multiplo:** ogni Cero ha ora un elenco di abilita' (`HERO_SKILLS`), scorribile col **tasto L** quando il comando Abilita' e' selezionato. La `static_assert` di raggiungibilita' della Mossa Suprema e' stata estesa all'abilita' *piu' costosa* di ciascun eroe.

* **Esito dei Test — le quattro correzioni sono verificate su hardware emulato**, non solo nei test. Traccia dell'incontro con Corrado di Spoleto:
  ```
  round 1   Corrado HP 1319  SC 3  UST 1      Antonio 210/210   <- il Bastione regge
  round 2   Corrado HP 1103  SC 2  UST 2      Antonio 210/210
  round 3   Corrado HP  856  SC 1  UST 3      Antonio 210/210
  round 4   Corrado HP  591  SC 0  BRK 1      <- BREAK sul boss, e su un nemico VIVO
  round 5   Corrado HP  327  SC 4  BRK 0      <- scudo ricomposto all'uscita
  ```
  * **Rilievo 1 risolto:** Corrado supera i 7 round invece di morire in 4; le riserve di HP contano di nuovo.
  * **Rilievo 2 risolto:** il BREAK si attiva finalmente sul boss per cui la meccanica e' pensata. Poiche' stavolta il nemico e' **vivo** quando si rompe, e' anche la prima verifica a runtime del **dimezzamento della difesa** in BREAK (591 -> 327, 264 danni contro i ~250 dei round precedenti nonostante il turno saltato).
  * **Rilievo 3 risolto:** il Giudizio della Verga infligge danno reale (103 sul Balestriere, x1.5 da debolezza) e ne erode lo scudo fino al BREAK.
  * **Rilievo 4 risolto:** Sant'Antonio chiude tutti i round a **210/210 HP**, dove prima moriva al round 3. Giorgio incassa al posto suo (380 -> 324 -> 274 -> 222).
  * Dettaglio emerso: il Fervore di Giorgio resta stabile a 54 finche' intercetta (paga 15, guadagna 15), e cala solo quando Corrado e' in BREAK e non attacca. L'economia si autoregola.
  * `python tests/test_battle_engine.py` -> **OK, 30/30** (3 nuovi: Giudizio contro il Balestriere, intercettazione del Bastione, durata della guardia). ROM di gioco ricostruita, 116 KB.

### [2026-08-16] - Sessione 05: Grafica Segnaposto e Schermata di Combattimento

* **Autore / Agente:** Claude Opus 5 (Claude Code)
* **File creati:** `tools/make_placeholder_art.py`, `tools/preview_battle_screen.py`, `include/battle_hud.h`, `src/battle_hud.cpp`, `graphics/*` (9 asset)
* **File modificati:** `src/main.cpp` (usa l'HUD al posto del tabulato), `include/battle_scene.h` + `src/battle_scene.cpp` (accessore `active_hero_index()`), `Makefile`

* **A. Grafica segnaposto generata proceduralmente** (`python tools/make_placeholder_art.py`). Non e' arte definitiva: sono silhouette leggibili **nelle misure esatte della Sez. 23A GDD**, con le palette della Sez. 14C. Sostituire un personaggio significa sovrascrivere il suo `.bmp`, senza toccare una riga di C++.
  | asset | misura | note |
  | :-- | :-- | :-- |
  | `ubaldo` | 16x32 | mitra, pastorale, bianco liturgico e oro |
  | `giorgio` | 32x32 | lancia, scudo, azzurro cavaliere |
  | `antonio` | 16x32 | saio nero, bastone a tau, fiamma |
  | `enemy_fante` / `enemy_balestriere` | 32x32 | rosso Perugia / cuoio e acciaio |
  | `enemy_corrado` | 64x64 | boss, misura della Sez. 14B.3 |
  | `hud_bar` | 32x8 x34 | 17 fotogrammi HP cremisi + 17 Fervore oro |
  | `target_cursor` | 16x16 | cuneo bronzeo |
  | `battle_bg` | 256x256 | fondale d'assedio + pannello HUD |

* **B. Schermata di combattimento** (`BattleHud`), layout della Sez. 14B.3 GDD: fondale con Monte Ingino e nebbia, schieramento nemico 3x2 a sinistra, i tre Ceri a destra, fascia HUD di 48px con menu comandi (80px) e stato del party (160px: nome, HP, barra HP, barra Fervore). Cursore bronzeo sul bersaglio, marcatore di Boost sulla riga di comando selezionata, gli sprite dei caduti spariscono dal campo.
  * **Decisione tecnica:** il pannello HUD e' *dipinto nelle righe 112-159 del fondale* invece che su un layer separato. La scena e' statica e cosi' resta libero un BG hardware per il parallasse futuro.
  * L'HUD si ridisegna solo quando cambia una firma dello stato, non a ogni frame.

* **C. Anteprima fuori emulatore** (`python tools/preview_battle_screen.py`). Compone i 240x160 dagli stessi `.bmp` e dalle stesse coordinate del C++, col font 8x8 vero di Butano: serve a iterare su layout e arte senza ricompilare. **Le costanti di posizione sono duplicate rispetto a `battle_hud.cpp` e vanno tenute allineate a mano.**

* **Tre difetti trovati e corretti proprio grazie all'anteprima**, che a schermo nero sarebbero passati inosservati:
  1. Il foglio del font di Butano **non contiene la cella dello spazio**: senza lo scarto di uno ogni lettera scivolava e "Sant'Ubaldo" usciva "Tbou...".
  2. Le figure **fluttuavano sopra il terreno**: le y della Sez. 14B.3 sono un intervallo, non la linea d'appoggio. Riposizionate perche' i piedi tocchino la fascia di terreno.
  3. La riga di dettaglio cadeva a **y=161, fuori dai 160px** dello schermo. Rimossa; il livello di Boost e' ora un marcatore sulla riga di comando.

* **Esito dei Test:** ROM **149 KB**, build pulita, eseguita su mGBA: **zero assert, zero errori**. `python tests/test_battle_engine.py` -> **OK, 30/30**.
  * **Limite dichiarato:** l'anteprima e' una *composizione* dagli stessi asset e dalle stesse coordinate, **non un fotogramma catturato dall'emulatore**. mGBA 0.10.5 non espone cattura da riga di comando e la sessione non interattiva non puo' premere i tasti. Che la ROM giri senza assert e' verificato; che il PPU disponga i pixel esattamente come nell'anteprima e' dedotto dalle coordinate, non osservato.

### [2026-08-16] - Sessione 06: Timeline degli Ordini, Dissolvenza d'Ingresso e Audit delle Regole

* **Autore / Agente:** Claude Opus 5 (Claude Code)
* **File modificati:** `include/battle_scene.h`, `src/battle_scene.cpp`, `include/battle_hud.h`, `src/battle_hud.cpp`, `tools/make_placeholder_art.py`

* **A. Timeline degli ordini** (Sez. 20A GDD, **pilastro 1 dei tre**, finora del tutto assente). Gettoni 16x16 in alto a destra che mostrano l'ordine del round: `predicted_order()` usa la velocita' gia' calcolata per chi ha scelto e quella base per chi deve ancora farlo, con lo stesso insertion sort stabile della coda vera. Un nemico in BREAK non compare, perche' salta il turno.
* **B. Dissolvenza d'ingresso reale.** `INTRO_FADE_IN` transitava in un solo frame: ora dura 32 frame e l'HUD dissolve dal nero via `bg_palettes::set_fade` / `sprite_palettes::set_fade`, dando al rintocco del Campanone il tempo di risuonare.
* **C. Nuovo asset:** `timeline_icons` 16x16 x6 (3 Ceri + 3 nemici).
* **Esito:** ROM **152 KB**, build pulita, su mGBA **zero assert e zero errori**, la FSM supera l'intro e raggiunge `CMD GIORGIO`.

* **D. AUDIT DI CONFORMITA' ALLE REGOLE** (richiesto dall'utente):
  * **`AGENTS.md` rispettato**, verificato con grep e non solo dichiarato: nessuna occorrenza di `new` / `malloc` / `std::vector` / `std::string` / `float` / `double` in `include/` e `src/`; 35 tabelle `constexpr` in ROM; ciclo di scena `update(); bn::core::update();` presente sia in `BattleSceneManager::run()` sia in `main`; formule sempre citate per sezione del GDD; `HANDOVER.md` aggiornato a ogni intervento.
  * **Le skill di `.agents/skills/` NON sono caricate automaticamente**: stanno nella convenzione Antigravity, mentre Claude Code legge `.claude/skills/`. Sono state lette manualmente in questa sessione. Confermano quanto implementato su Shield Break, moltiplicatori di Boost (1.0 / 1.5 / 2.0-doppio colpo / 3.5) e specifiche sprite (16 colori, colore 0 trasparente, misure potenze di due).
  * **DIVERGENZA APERTA:** la skill `butano-gba-dev` prescrive un pattern di scena con **classe base virtuale** (`class Scene { virtual ~Scene() = default; virtual SceneType update() = 0; };`). Non esiste nel progetto: `BattleSceneManager` e' una classe autonoma. Finche' la scena e' una sola l'astrazione sarebbe speculativa, ma **diventa necessaria al punto 5 della roadmap** (Overworld), quando serviranno due scene e un meccanismo di transizione. Da affrontare allora, non prima.
  * Nota minore: la skill `asset-pipeline` prevede `audio/music/` e `audio/sound_effects/`; oggi esiste un `audio/` piatto e vuoto.
  * **Subagenti:** non utilizzati. La configurazione di questa sessione richiede che l'utente li chieda esplicitamente. I due registrati nella Sessione 01 (`gba_engine_architect`, `asset_pipeline_agent`) appartengono a un altro ambiente e non sono disponibili qui.

### [2026-08-16] - Sessione 07: Skill Attivate, Revisione con Agenti, Contenuti di Battaglia

* **Autore / Agente:** Claude Opus 5 (Claude Code) con gruppo di subagenti
* **A. Skill del progetto rese operative.** Erano in `.agents/skills/` (convenzione Antigravity) e Claude Code **non le caricava**: ora esiste una copia in `.claude/skills/{butano-gba-dev,asset-pipeline}/SKILL.md`, con nota in testa che la sorgente canonica resta `.agents/`. **Le due copie vanno tenute allineate a mano.**
* **B. Struttura audio** allineata alla skill `asset-pipeline`: create `audio/music/` e `audio/sound_effects/` (prima esisteva un `audio/` piatto).

* **C. Quattro agenti di analisi in parallelo.** Consegne:
  * **`include/item_data.h` IMPLEMENTATO**: i 5 consumabili della Sez. 8E, numeri calibrati sui pool reali (il round peggiore della Pattuglia infligge ~110 HP, quindi la Crescia da 100 ne copre uno). Veleno/Confusione/Silenzio della Sez. 8E **non esistono** in `StatusEffect`: mappati sugli equivalenti implementati, con `ARMOR_BROKEN` escluso (curare lo Shield Break sarebbe un exploit) e `static_assert` a protezione. Il Baccala' restituisce 510 Fervore, cinque Boost MAX: `max_carry` bloccato a 1 da `static_assert`. L'inventario e' condiviso, quindi va scalato alla SELEZIONE, non all'esecuzione.
  * **[`docs/piano_ia_boss.md`](./docs/piano_ia_boss.md)**: IA dei boss della Sez. 26 come tabella di regole `constexpr` con un unico valutatore, immunita' condizionata di Corrado, le tre fasi di Monaldo come righe di `ENEMIES[]` concatenate. **Non implementato.**
  * **[`docs/piano_combo_tre_ceri.md`](./docs/piano_combo_tre_ceri.md)**: le 4 Combo della Sez. 12C, e la scoperta che l'**Alzata Trionfale E' la "Mossa Suprema dei Tre Ceri" della Sez. 12A** — lettura che dissolve il conflitto 12A/12C e da' finalmente un referente alla clausola "consuma l'intera barra", mai implementata. **Non implementato.**

* **D. REVISIONE INDIPENDENTE DEL MOTORE — tre correzioni applicate:**
  1. **[ALTA, confermato] La firma dell'HUD ignorava `is_enemy`.** Passando da Muro della Fede (alleato, slot 0) a Giudizio della Verga (nemico, slot 0) col tasto L, la firma non cambiava e **il cursore bersaglio restava nascosto** — al primo scontro del gioco.
  2. **[MEDIA] Il Fervor Boost sul Bastione Azzurro era spesa a vuoto:** fino a 115 Fervore invece di 15 senza alcun beneficio, e nulla lo segnalava. La durata della guardia ora scala col Boost (1/2/3/4 turni).
  3. **[BASSA] Commento fuorviante su `apply_burn`:** prometteva una fotografia *per carica*, mentre il codice riscrive il valore di tutte. Non osservabile oggi; corretto il commento invece di aggiungere un array per unita' che nessuno usa.
  * **Segnalazione respinta motivatamente:** il `return` in `_queue_enemy_actions` quando non c'e' un eroe vivo e' corretto, non un bug: se manca il bersaglio per un nemico manca per tutti.
  * Esito complessivo: **nessuna violazione zero-heap**, nessun `bn::vector` sforabile, nessun riferimento appeso, mirror Python fedele formula per formula.

* **Esito:** ROM 152 KB, build pulita, su mGBA zero assert, **31/31 test**.

* **E. Workflow a 10 agenti** (5 ricognizioni parallele -> sintesi -> 3 critici avversariali -> consolidamento). Prodotto: **[`docs/piano_fase_successiva.md`](./docs/piano_fase_successiva.md)**, 23 passi ordinati per dipendenza. Prima esecuzione fallita a meta' per limite di sessione, ripresa da cache: le 5 ricognizioni non sono state ripagate.

* **F. REGRESSIONE TROVATA DAI CRITICI E CORRETTA — l'autotest mentiva.**
  `GUBBIO_AUTOTEST_ALIGN` valeva `"00" "00"` (2 frame), calibrato nella Sessione 03 quando `INTRO_FADE_IN` transitava in un solo frame. **La Sessione 06 ha portato `INTRO_DURATION_FRAMES` a 32 senza aggiornare l'allineamento**: da allora lo script slittava di 31 posizioni. Verificato: **2 round eseguiti invece di 7**, con gli input applicati agli stati sbagliati.
  Il punto grave e' che **un autotest disallineato non fallisce, mente**: continuava a riportare "zero assert", che e' esattamente cio' che la Sessione 06 ("raggiunge CMD GIORGIO") e la 07 ("zero assert") hanno preso per verifica. Nessuna delle due ha ripubblicato una traccia di round, che avrebbe smascherato il problema.
  Corretto a 33 frame (1 di `core::init()` + 32 di intro), con commento che dichiara **l'accoppiamento** fra i due valori, che il preprocessore non puo' derivare. Riverificato: i due Fanti cadono entro il round 3 con Shield Break regolare (`SC 0 BRK 1`).
  **Lezione da tenere:** un oracolo di collaudo va fatto fallire quando deve fallire, prima di usarlo come criterio di accettazione (Passo 0a del piano).

* **G. Due lacune di controllo emerse dal piano, non ancora chiuse:**
  * `USERCXXFLAGS` nel Makefile e' **vuoto**: il divieto di `float`/`double` di AGENTS.md non e' applicato da nulla, e `bn::fixed v = 1.5;` compila senza un warning. Servono `-Wdouble-promotion -Wfloat-conversion -Werror=double-promotion`.
  * La politica zero-heap e' **dichiarata ma non misurata**. Il Passo 0b propone un gate su `arm-none-eabi-nm` dell'ELF, con un'avvertenza preziosa: un gate ingenuo su `malloc|free` **nascerebbe rosso**, perche' lo stub `free` di newlib e `mmAllocChannel` di maxmod sono gia' nella ROM pulita. La baseline attuale e' comunque sana: nessun `operator new/delete`, nessun `malloc`, nessun `__aeabi_d*`.

### [2026-08-17] - Sessione 08: Passo 0 — Gate di Verificabilita'

* **Autore / Agente:** Claude Opus 5 (Claude Code)
* **File creati:** `tools/check_zero_heap.sh`, `tests/test_assets.py`
* **File modificati:** `src/main.cpp` (allineamento autotest), `Makefile`, `tools/build_rom.sh`

Motivazione: fino a ieri le regole di `AGENTS.md` erano **dichiarate ma non misurate**, e nella Sessione 07 si e' scoperto che l'autotest riportava "zero assert" pur eseguendo un terzo dei round. Una verifica che non puo' fallire non e' una verifica. Questo passo rende ogni regola controllabile da una macchina.

* **0a. Autotest riallineato** (gia' descritto in Sessione 07F): da 2 a 33 frame di scarto. Riverificato: i due Fanti cadono entro il round 3 con Shield Break regolare.

* **0b. `tools/check_zero_heap.sh`**, agganciato a `tools/build_rom.sh` e quindi eseguito a ogni build riuscita. Ispeziona i simboli dell'ELF con `arm-none-eabi-nm` e fallisce su: `operator new`/`delete` (nomi storpiati `_Znwj`, `_ZdlPv`, ...), `malloc`/`calloc`/`realloc`/`_sbrk`, `__cxa_pure_virtual`, e ogni `__aeabi_d*` (doppia precisione, che sul GBA e' emulazione software).
  * **Esclusioni deliberate e documentate nel file:** `free` (stub inerte di newlib) e `mmAllocChannel` (maxmod, che alloca da un proprio buffer statico). **Verificato che entrambi sono nella ROM pulita**: un gate scritto come `grep -iE 'malloc|free'` sarebbe nato rosso e sarebbe stato disattivato al primo fastidio.
  * **PROVA NEGATIVA ESEGUITA:** inserito deliberatamente un `double` in `main.cpp`, il gate e' diventato **rosso segnalando 6 simboli** (`__aeabi_dadd`, `__adddf3`, ...); ripristinato il codice, e' tornato verde. Il gate puo' fallire, ed e' il punto.

* **0c. `Makefile`: `USERCXXFLAGS := -Wdouble-promotion -Wfloat-conversion -Werror=double-promotion -Werror=float-conversion`.** Prima era vuoto: il divieto di virgola mobile non era applicato da nulla. Build pulita da zero: **zero avvisi**, quindi anche Butano stesso e' conforme.
  * **Limite accertato, da non spacciare per risolto:** i flag **non** intercettano `bn::fixed x = 1.5;`, perche' `bn::fixed` ha un costruttore `constexpr` da `double` e non c'e' promozione. Verificato pero' che quel caso produce **zero simboli double a runtime** (ripiegamento a compile time): e' una questione di stile, non di costo. Il divieto sostanziale e' presidiato dal gate 0b sull'ELF, non dai flag.

* **0d. `tests/test_assets.py`**: valida ogni `.bmp` di `graphics/` contro il `.json` che lo accompagna — presenza del json, profondita' 4bpp, misure OBJ legali del GBA (con gestione dei fogli a piu' fotogrammi via campo `height`), misure di background valide, e conformita' dei tre Ceri alla Sez. 23A. Sposta a monte errori che altrimenti compaiono come fallimento oscuro di `grit` o come sprite storto a schermo.

* **Esito:** ROM 152 KB, build verde col gate in linea. `test_battle_engine.py` **31/31**, `test_assets.py` **5/5**.

### [2026-08-17] - Sessione 09: Passi 1-3 — Fondazione (MapId, StoryFlags, contratto Scene)

* **Autore / Agente:** Claude Opus 5 (Claude Code)
* **File creati:** `include/map_id.h`, `include/story_flags.h`, `include/scene.h`

* **Passo 1 - `map_id.h`.** La numerazione delle aree viveva in tre posti con convenzioni incompatibili: un commento in `save_data.h` (4 valori), la Sez. 38 del GDD (di piu'), i trigger della Sez. 21B (altri ancora). Un `current_map_id` scritto su FRAM con una numerazione e riletto con un'altra sposta il giocatore nell'area sbagliata **senza che il salvataggio se ne accorga**. Ora c'e' un solo `enum class MapId : uint8_t` autoritativo, con `static_assert` che congela i valori 0-3 gia' persistiti.

* **Passo 2 - `story_flags.h`.** 256 bit in 32 byte, con **intervalli riservati per modulo** (0-63 storia, 64-127 quest, 128-159 boss, 160-191 combo, 192-255 riserva). Il problema non era tecnico ma di governance: tre analisi indipendenti lo dimensionavano a 32/128/256 bit rivendicandone ciascuna la proprieta', e senza intervalli assegnati due moduli finiscono per scrivere lo stesso bit con un bug invisibile. Tre `static_assert` verificano che ogni bandiera dichiarata stia nel proprio intervallo.

* **Passo 3 - `scene.h`, e la riconciliazione fra skill e zero-heap.** La skill `butano-gba-dev` prescrive `virtual ~Scene() = default`, ma quella forma fa emettere a GCC il *deleting destructor* (slot D0 della vtable), che referenzia `operator delete` e lo trascina in ROM — dove il gate del Passo 0b lo intercetterebbe come violazione. Adottata la forma della linea guida **C.35: distruttore non virtuale e `protected`**, legittima perche' le scene vivono sullo stack e non sono mai distrutte tramite puntatore alla base; `protected` rende quell'errore impossibile da scrivere. Si ottiene il contratto della skill senza pagarne il costo.

* **VERIFICA CHE CONTAVA:** `Scene` ha un metodo virtuale puro, e il gate del Passo 0b **vieta `__cxa_pure_virtual`**. Costruita una scena concreta derivata, collegata nella ROM reale e misurato: **0 occorrenze** di `__cxa_pure_virtual` e `_ZdlPv`, gate verde. Il design sopravvive al proprio controllo — cosa che andava dimostrata, non assunta.

* **Esito:** ROM 152 KB, build verde col gate in linea, `test_battle_engine.py` 31/31, `test_assets.py` 5/5.

### [2026-08-17] - Sessione 10: Allineamento del Registro e Prova Reale End-to-End

* **Autore / Agente:** Claude Opus 5 (Claude Code)

* **A. Registro allineato.** Verificato per via automatica che ogni file di `include/`, `src/`, `tools/`, `tests/` e `docs/` sia citato in `HANDOVER.md`: **nessuno mancante**. La tabella dei componenti (Sez. 2) era pero' rimasta indietro rispetto ai log di sessione: aggiunte le 7 voci mancanti (`map_id.h`, `story_flags.h`, `scene.h`, `item_data.h`, `check_zero_heap.sh`, `test_assets.py`, `docs/`) e corretto il conteggio dei test da 30 a 31.

* **B. Prova reale eseguita da zero:** `clean`, cancellazione degli artefatti, ricompilazione integrale, gate zero-heap, entrambe le suite, esecuzione su mGBA con l'autotest. Esito: ROM 152 KB con header `GUBBIO1151`/`GU11`, gate verde, **31/31 + 5/5**, e una traccia di gioco coerente su piu' round:
  ```
  round 1  Fante HP 15  SC 1  UST 1     Antonio 210/210  Giorgio 349
  round 2  Fante HP 0   SC 0  BRK 1     Antonio 210/210  Giorgio 322
  round 3                                Antonio 210/210  Giorgio 299
  ```
  Ogni numero e' riconducibile alle regole: il Fuoco di Antonio erode lo scudo fino al BREAK, Sant'Antonio resta **illeso per tutto lo scontro** grazie al Bastione Azzurro mentre San Giorgio incassa al posto suo, e il Fervore di Giorgio **sale** (54 -> 84 -> 99) perche' le parate ne generano piu' di quanto costi la guardia.

* **C. Due warning emersi solo dalla build pulita** (le build incrementali li nascondevano):
  * `battle_hud.cpp`: cast inutile a `int` su `bn::vector::size()`, che ritorna gia' `int`. **Corretto.**
  * `battle_scene.cpp`: `-Wswitch-default` sulla FSM. **Non corretto di proposito**, con nota nel codice: elencando tutti gli stati senza `default:`, e' `-Wswitch` a fare la guardia e a segnalare uno stato dimenticato se domani se ne aggiunge uno. Con un `default: break;` quella protezione sparirebbe. Si accetta un warning per non perdere un controllo piu' utile.

* **Nota di metodo:** compilare sempre in modo incrementale nasconde i warning delle unita' non ricompilate. La build da zero va rifatta periodicamente, non solo quando qualcosa si rompe.

### [2026-08-17] - Sessione 11: Passi 4-6 — Stato di Partita, Transizioni e Trampolino di Scene

* **Autore / Agente:** Claude Opus 5 (Claude Code)
* **File creati:** `include/game_state.h`, `src/game_state.cpp`, `include/scene_fade.h`, `src/scene_fade.cpp`, `include/game_clock.h`, `include/scene_battle.h`, `src/scene_battle.cpp`
* **File modificati:** `src/main.cpp` (riscritto come trampolino), `include/battle_scene.h`, `src/battle_scene.cpp`, `src/battle_hud.cpp`, `tools/check_zero_heap.sh`

* **Passo 4 — `GameState`, 140 byte in EWRAM.** Fino a ieri lo stato del giocatore viveva dentro la scena di battaglia e moriva con essa. Ora c'e' un contenitore che nessuna scena possiede: party, mappa e spawn, posizione, atto, oro, Tavole, reputazione dei Quartieri, inventario, quest, 256 bandiere, `playtime_frames`. Tre invarianti verificati dal compilatore: banalmente copiabile (lo esige `bn::sram::write_offset` al Passo 8), `sizeof <= 256`, e **zero padding** — senza quest'ultimo i byte di riempimento entrerebbero nel CRC32 con valori indeterminati e lo stesso stato salvato due volte darebbe due checksum diversi.

* **DECISIONE PRESA — il carry-over di HP e Fervore fra le scene ESISTE** (decisione n.1 del piano, che bloccava la firma del Passo 6). La prova e' nel GDD e non e' un'opinione: la **Sez. 6 assegna all'Eremo di Sant'Ambrogio "riposo, salvataggio e recupero MP/Fervore"**. Un luogo che ripristina il Fervore non ha alcuna funzione se il Fervore si ripristina da solo a ogni scontro. Di conseguenza `HERO_START_FERVOR_PERCENT` **non e' stato rimosso ne' modificato**: e' degradato da inizializzatore di ogni battaglia a *default di nuova partita*, quindi `tests/test_battle_engine.py:295` e `:503` restano verdi **e restano significativi** — descrivono ora il percorso `reset_new_game()`. Corollari lasciati aperti di proposito: la vittoria **non** cura nulla (curare di nascosto renderebbe il carry-over invisibile), e cosa ripristini esattamente l'Eremo si decidera' quando l'Eremo esistera'.

* **Passo 5 — `scene_fade` (primitive senza ciclo) e `game_clock`.** La dissolvenza resta guidata dalla FSM gia' verificata (32 frame, Campanone al frame 0): `scene_fade` espone solo `apply(0-100)` e `reset()`, e `battle_hud.cpp` e' passato a usarle invece di toccare le palette globali per conto proprio. `gubbio::core_update()` e' l'unico punto del progetto che chiama `bn::core::update()`, e incrementa `playtime_frames`: un contatore in un posto solo non puo' rallentare in una scena che si dimentica di aggiornarlo.

* **Passo 6 — facade `BattleScene` e trampolino.** `main.cpp` non e' piu' una battaglia infinita: e' uno `switch` su `SceneId` con la scena come **variabile di scope**. Al piu' una scena viva per volta, garantito dallo scope e non dalla disciplina — cioe' la sequenza "fade-nero -> distruggi -> costruisci -> fade-in" ottenuta per costruzione. `BattleSceneManager::run()` e' stato **rimosso**: esisteva dalla Sessione 02, non era mai stato chiamato, e faceva girare il modello senza aggiornare l'HUD (la battaglia si sarebbe risolta a schermo fermo). Aggiunti l'overload `init_battle(encounter, const GameState&)` e `export_party_state(GameState&)`, che esporta **solo HP e Fervore**: un Cero non resta "in BREAK" mentre cammina per la piazza.

* **IL GATE ORA GUARDA ANCHE I SORGENTI, con prova negativa per ciascun controllo nuovo.** `tools/check_zero_heap.sh` verifica in piu': (a) che `g_game_state` stia in EWRAM; (d) che `bn::core::update()` non compaia fuori da `game_clock.h`; (e) che nei sorgenti non ci siano `new`, `unique_ptr` o factory che ritornano `Scene*`. **Tutti e tre sono stati fatti fallire di proposito** (regola n.1 del progetto):
  * tolto `BN_DATA_EWRAM_BSS`, la variabile si e' spostata a **`0x0300230c` — IWRAM**, esattamente il difetto che il piano prevedeva, e il gate e' diventato rosso. Con l'attributo sta a `0x020000e0`, 140 byte.
  * sostituito `core_update()` con `bn::core::update()` nel trampolino: rosso.
  * scritta una `Scene* prova = new BattleScene(...)`: rosso.
  * I controlli sui sorgenti **ignorano le righe di commento**: le regole vanno citate nei commenti dei file che le rispettano, e un gate che vietasse di nominarle costringerebbe a storpiare la prosa per farlo tacere — il modo tipico in cui un controllo di qualita' viene disattivato.

* **Esito dei test.** Build pulita da zero, gate verde su tutti e cinque i controlli. Traccia su mGBA **identica numero per numero** a quella di riferimento della Sessione 10 (round 1 Fante HP 15/SC 1/UST 1 e Giorgio 349; round 2 Fante 0/BRK 1 e Giorgio 322; round 3 Giorgio 299): il refactoring non ha cambiato il comportamento. In coda, la parte nuova:
  ```
  ESITO FUGA
    CARRY-OVER Sant'Ubaldo  HP 240  FER 84
    CARRY-OVER San Giorgio  HP 299  FER 99
    CARRY-OVER Sant'Antonio HP 210  FER  7
  SCENA -> ESPLORAZIONE mappa 0 (non implementata)
  ```

* **DIFETTO DELL'ORACOLO DIAGNOSTICATO (non del gioco).** Quella "FUGA" non e' una regressione: al round 4 Sant'Antonio ha 7 Fervore e il Fuoco ne costa 15, quindi il tasto A viene **rifiutato**, lo stato non avanza e da li' in poi lo script a tasti fissi **scivola di un eroe** — le pressioni destinate a Giorgio scorrono il menu di Antonio fino a `Fuga`. Prima non si vedeva solo perche' il vecchio `main` non terminava mai la battaglia e nessuno guardava oltre il round 3. Aggiunta una traccia `RIFIUTATO <eroe>: Fervore N < costo M`, che rende il fenomeno leggibile invece che deducibile. **La correzione strutturale resta il Passo 0a del piano** (autotest a confronto di sequenze di eventi, non di frame): finche' e' a tasti fissi, ogni comando rifiutato lo disallinea.

### [2026-08-18] - Sessione 11b: Passi 10-14 — PIAZZA GRANDE GIOCABILE

* **Autore / Agente:** Claude Opus 5 (Claude Code)
* **File creati:** `tools/make_piazza_art.py`, `tools/preview_piazza.py`, `include/map_data.h`, `include/overworld_player.h`, `src/overworld_player.cpp`, `include/scene_exploration.h`, `src/scene_exploration.cpp`, `graphics/piazza_ground.{bmp,json}`, `graphics/piazza_sky.{bmp,json}`, `graphics/overworld_ubaldo.{bmp,json}`
* **File modificati:** `include/piazza_grande_collision.h`, `src/main.cpp`, `src/game_state.cpp`, `include/game_state.h`, `tools/make_placeholder_art.py`, `tests/test_assets.py`, le 9 `.json` di `graphics/`, entrambe le copie della skill `butano-gba-dev`, `GUBBIO_1151_LA_BIBBIA_GDD.md` (Sez. 12A e 21D), `AGENTS.md`

* **Passo 10 — la collisione diventa un dato, derivato dalla funzione.** `PIAZZA_GRID` e' calcolata a compile time (`consteval`) dalla stessa `get_tile_type` che c'era gia': 2560 byte in ROM **una volta sola** (`inline constexpr`), nessuna seconda descrizione della piazza da tenere allineata a mano. Aggiunti `TileType`, `is_solid()`, `is_transition()` e `get_tile_type_px()`. Cinque `static_assert` verificano la derivazione su punti notevoli. **`>> 3` e non `/ 8`:** `-1 / 8` vale 0 e leggerebbe un pixel fuori dal bordo sinistro come suolo libero — il giocatore uscirebbe dalla mappa; `-1 >> 3` vale -1, che la griglia riconosce come muro. C'e' una `static_assert` anche su questo.

* **Passo 11 — arte segnaposto della piazza, e il difetto n.4 del piano chiuso.** `make_piazza_art.py` genera suolo (512x512, **9 tile unici**), cielo (256x256, 33) e l'eroe dell'overworld (16x256, 4 direzioni x 4 fotogrammi). Il suolo e' **derivato dalla griglia di collisione**: e' impossibile che il giocatore sbatta contro un palazzo che non si vede. Il generatore misura e fallisce su conteggio colori e tile unici contro il budget del Passo 9.
  * **`bpp_mode` esplicito ovunque.** Senza quel campo, `butano_graphics_tool.py` promuove in silenzio a 8bpp ogni BMP oltre i 16 colori — VRAM doppia per tile e, per un background, tutti e 16 i banchi di palette. **Nessuna delle 9 `.json` esistenti lo dichiarava.** Aggiunto un test in `test_assets.py` che lo esige, **verificato rosso sui 9 asset preesistenti** prima di correggerli, e aggiunto anche a `make_placeholder_art.py` perche' la rigenerazione non lo perda.
  * **512x512 e non 512x320:** le misure legali di un BG regolare sono multipli di 256, e un 512x256 farebbe ricomparire in cima la fascia sud della ringhiera per wrap hardware.

* **Passo 12 — `map_data.h`.** `MAPS[]` in ROM con la sola Piazza Grande popolata; le altre quattro righe sono vuote e `is_implemented()` le riconosce. Il **budget VRAM e' misurato, non sperato**: `GROUND_TILES` e `SKY_TILES` sono letti dagli item generati da grit, quindi un'arte definitiva che sforasse romperebbe la build invece di dare un assert dell'allocatore davanti al giocatore. Due `static_assert` verificano che nessuno spawn point cada dentro un ostacolo **ne' su un trigger** — quest'ultima e' la guardia contro il loop di transizione.

* **Passo 13 — `OverworldPlayer`, e tre correzioni al GDD.** Posizione in `int` pixel (niente `bn::fixed`, niente ambiguita' sullo `>> 3`), hitbox **12x8 ai piedi**, movimento ad **assi separati**, campionamento dell'**intervallo** di tile. Le ragioni sono nella nota di revisione aggiunta alla Sez. 21D del GDD: col bounding box 16x16 centrato che il documento prescrive, **il portone dei Consoli e' letteralmente irraggiungibile**. I 16 fotogrammi sono creati una volta e tenuti vivi (2 KB su 32 KB di VRAM OBJ): cambiare direzione e' un `set_tiles` che non alloca, invece di una release+create sull'allocatore best-fit a ogni cambio — che in diagonale e' continuo.

* **Passo 14 — `ExplorationScene`, parametrizzata da `MapId`.** Suolo agganciato alla camera (priority 2), cielo in parallasse a un quarto (priority 3, `create_bg_optional` con degrado gestito), camera rigida clampata, trigger valutati **sul solo punto centrale dei piedi** con debounce preimpostato al tile di comparsa. `ENTRY_POINT_RESUME` distingue "entro dalla porta" da "ricarico una partita salvata in mezzo alla piazza".

* **IL ROUND-TRIP COMPLETO E' VERIFICATO SU EMULATORE**, che era il criterio di accettazione del Passo 14:
  ```
  ESITO FUGA   CARRY-OVER Ubaldo HP 240 FER 84 | Giorgio 299/99 | Antonio 210/7
  === ESPLORAZIONE: Piazza Grande ===   comparsa a x 260 y 244 (entry point 0)
  TRIGGER tile 4 -> scena 2 parametro 0 rientro su spawn 3
  USCITA esplorazione: sprite 1  tile OBJ usati 64  disponibili 960  stack IWRAM 2380
  === BATTAGLIA: incontro 0 ===
  EROE Sant'Ubaldo  HP 240/240 FERVORE  84/180 (46%)
  EROE San Giorgio  HP 299/380 FERVORE  99/120 (82%)
  EROE Sant'Antonio HP 210/210 FERVORE   7/210 (3%)
  ... ESITO FUGA ...
  === ESPLORAZIONE: Piazza Grande ===   comparsa a x 44 y 172 (entry point 3)
  ```
  La seconda battaglia riparte **esattamente** con gli HP e il Fervore trasportati, e il rientro deposita il giocatore sullo spawn 3 — **non** sul trigger da cui era uscito: il loop di transizione non si verifica. Margini al picco: 1 sprite, 64/1024 tile OBJ, 2380 byte di stack IWRAM sui ~21 KB disponibili.

* **Autotest esteso per arrivarci.** Allo script a tasti fissi sono state aggiunte una coda di camminata (SINISTRA+SU+corsa, 256 frame) e una di conferme grossolane per chiudere la seconda battaglia. Sotto `GUBBIO_BATTLE_AUTOTEST` il gioco parte ancora dalla battaglia — lo script e' tarato sui suoi 33 frame di scarto — mentre **la build normale parte da Piazza Grande**, che e' l'hub.

* **DECISIONI PRESE, tutte motivate e nessuna delle quattro riservate al committente:**
  * *Dimensioni della piazza:* **64x40 tile** (Sez. 21A/14B.1, gia' in codice), non 86x26 della Sez. 15B — 86 eccede i 64 del riquadro.
  * *Foreground:* **assente per ora, e di proposito.** Un livello di occlusione decide dove possono stare i palazzi (512x512 su tutta l'altezza, oppure fascia alta con nulla sotto y=256 px): generarlo adesso significherebbe fissare con un segnaposto una scelta d'arte. Il campo in `MapDescriptor` esiste gia': quando l'arte arriva si popola una riga di tabella, non una riga di C++.
  * *Chi cammina:* **leader singolo fisso** (Sez. 21D), il meno costoso in VRAM OBJ; le altre due varianti (leader commutabile 23C, tre sprite in fila 28B) non richiederebbero modifiche architetturali.
  * *Velocita':* **1 px/frame a passo, 2 in corsa col tasto B**, camera rigida con clamping — la proposta del piano, ora adottata.
  * *Ingresso in battaglia:* **PROVVISORIO** — il varco occidentale (Bargello) apre l'incontro di prova. Il GDD non specifica in alcun punto come si entri in battaglia dall'overworld: niente incontri casuali, contatore di passi, nemici visibili o tile di battaglia nella legenda 21B. Finche' la decisione manca, questo trigger e' l'unico modo di collaudare il round-trip. **Va sostituito, non ereditato.**

* **Esito dei test:** build pulita da zero, ROM **178 KB**, gate verde su tutti e cinque i controlli, `test_battle_engine.py` **31/31**, `test_assets.py` **6/6** (uno nuovo). Restano i due `-Wswitch-default` accettati a verbale.

* **Rilievo non corretto, da valutare:** le tabelle `constexpr` preesistenti (`HEROES`, `SKILLS`, `ENEMIES`, `ENCOUNTERS`, `ITEMS`) **non sono `inline`**, contro la regola di stile introdotta al Passo 1 del piano. A namespace scope `constexpr` implica linkage interno: ogni `.cpp` che include l'header ne riceve una copia in `.rodata`. Con il facade del Passo 6 e la scena di esplorazione le unita' di traduzione che le includono sono passate da 3 a 7. Non toccato perche' esula dai passi in lavorazione e coinvolge `battle_scene.h`, il file piu' conteso del progetto; le tabelle nuove di questa sessione (`MAPS`, `PIAZZA_GRID`) sono invece tutte `inline constexpr`.

### [2026-08-18] - Sessione 11c: Passi 7-8 — CRC32 e Salvataggio su FRAM

* **Autore / Agente:** Claude Opus 5 (Claude Code)
* **File creati:** `include/save_crc32.h`, `src/save_system.cpp`, `tests/test_save_system.py`
* **File modificati:** `include/save_data.h` (riscritto), `src/main.cpp`, `src/scene_exploration.cpp`

* **Passo 7 — `save_crc32.h`.** CRC32 riflesso (0xEDB88320) interamente `constexpr`, con tabella **a nibble**: 16 voci = 64 byte di ROM invece del kilobyte della tabella a byte, al prezzo di due passaggi per byte — su un record da 276 byte scritto qualche volta per partita, il tempo non e' la risorsa scarsa. La tabella e' **derivata dal polinomio a compile time**, non trascritta: sedici costanti copiate a mano sono sedici occasioni di sbagliare una cifra, e un CRC sbagliato ma coerente con se stesso supera ogni verifica interna. Il vettore canonico `crc32("123456789") == 0xCBF43926` e' una `static_assert`.

* **Passo 8 — involucro congelato, payload riservato.** `SaveData` e' **276 byte**: magic, `write_counter`, `playtime_seconds`, `version`, `payload_size`, 256 byte di payload opaco, `checksum` ultimo. Il payload e' oggi l'immagine di `GameState` (140 byte) e sara' strutturato al Passo 17 **senza cambiare `sizeof`**, quindi senza spostare gli offset delle banche gia' scritte: un solo bump di versione, ottenuto ordinando i passi invece che sperando.
  * **Il memcpy non e' vietato, e' vincolato.** `bn::sram::write_offset` *e'* una copia di byte: cio' che la rende sicura fra ricompilazioni sono le cinque `static_assert` — POD banalmente copiabile, `sizeof` bloccato a 276, **tutti** gli `offsetof` verificati uno per uno, zero padding, e i quattro record che stanno nei 32 KB.
  * **Magic leggibile in hex dump:** i quattro byte sono `G','1','1','5'`, con `static_assert` sull'endianness — l'affermazione "i byte scritti sono G115" e' vera solo su little-endian, e ora la build lo verifica.
  * **Ping-pong su due banche per slot** (2 slot x 2 banche): si scrive sempre nella banca meno recente, cosi' la copia buona resta intatta finche' la nuova non e' completa. **Rilettura di verifica** dopo ogni scrittura.
  * **Nessun auto-format.** `EMPTY` e `CORRUPT` sono stati distinti: uno slot illeggibile non viene riscritto ne' azzerato.
  * I due buffer da 276 byte stanno in **EWRAM**, non sullo stack: il salvataggio puo' avvenire al punto di massima profondita' di scena, e mezzo kilobyte in IWRAM sarebbe tolto proprio alla risorsa piu' contesa.

* **Punto di salvataggio PROVVISORIO:** tasto **SELECT** durante l'esplorazione. Il GDD lo prevede dal menu di pausa (Sez. 33A) e all'Eremo (Sez. 6), che non esistono ancora; senza un punto qualsiasi in cui il gioco scriva davvero, il formato resterebbe codice mai eseguito. All'avvio, se lo slot 0 e' valido la partita viene **caricata**.

* **VERIFICATO SU HARDWARE EMULATO — il `.sav` non e' piu' 0 byte.** Tre esecuzioni consecutive della ROM di autotest:
  ```
  esecuzione 1   SLOT 0 non caricabile (stato 0): nuova partita
                 SAVE: slot 0 banca 0 scrittura n. 1 tempo 12s
  esecuzione 2   SLOT 0 valido, tempo di gioco 12s: partita CARICATA
                 SAVE: slot 0 banca 1 scrittura n. 2 tempo 25s
  esecuzione 3   SLOT 0 valido, tempo di gioco 25s: partita CARICATA
                 SAVE: slot 0 banca 0 scrittura n. 3 tempo 38s
  ```
  Banche alternate 0 -> 1 -> 0, contatore monotono 1 -> 2 -> 3, e il tempo di gioco che **si accumula fra le sessioni** (12 -> 25 -> 38 s) e' la prova indiretta che il payload viene davvero ripristinato e non solo riscritto. La ROM dichiara il tipo di salvataggio: stringa `SRAM_V` presente all'offset `0x2A2F4`.

* **TRE PROVE NEGATIVE, perche' un checksum che non ha mai respinto nulla e' un ornamento:**
  1. **Corrotto 1 byte nella banca piu' recente** (38s): il gioco ha caricato **la precedente, integra** (25s). E' esattamente il caso che il ping-pong esiste per coprire — un salvataggio interrotto a meta' non perde la partita.
  2. **Corrotte entrambe le banche:** stato `CORRUPT`, nuova partita in memoria, e **sha1 dei 552 byte identico prima e dopo l'esecuzione** — nessun auto-format, i byte restano disponibili a chi indaga.
  3. Il test Python del checksum **e' diventato rosso** sul `.sav` corrotto e verde su quello integro.

* **`tests/test_save_system.py` — due oracoli indipendenti, 9 test.** Il primo confronta il CRC del progetto con **`zlib`**, cioe' un'implementazione scritta da altri: e' l'unico modo di scoprire una convenzione sbagliata ma coerente con se stessa. Il secondo apre il **`.sav` prodotto da mGBA** e verifica magic, offset, checksum ricalcolato, coda del payload azzerata, monotonia del contatore e alternanza delle banche. Se il `.sav` manca, i test dichiarano `skip` invece di passare in silenzio.

* **Esito:** build pulita da zero, gate verde, `test_battle_engine.py` **31/31**, `test_assets.py` **6/6**, `test_save_system.py` **9/9**.

### [2026-08-18] - Sessione 11d: Controllo di Versione e Skill delle Decisioni

* **Autore / Agente:** Claude Opus 5 (Claude Code)
* **File creati:** `.gitignore`, `.gitattributes`, `.agents/skills/decisioni-aperte/SKILL.md`, `.claude/skills/decisioni-aperte/SKILL.md`

* **Il progetto ha una storia.** Fino alla Sessione 11c questa cartella **non era un repository git**: undici sessioni di lavoro, file critici riscritti da capo (`save_data.h` nella 11c), e nessun modo di vedere un diff, tornare indietro o sapere quando una riga fosse cambiata. Ora c'e' un commit iniziale con gli 80 file del progetto.
  * **Escluso dalla storia:** `build/`, ROM, ELF, mappe, anteprime e **il `.sav`** — che e' la memoria di chi gioca, non un file del progetto (i test lo leggono se c'e' e dichiarano `skip` se manca).
  * **Incluso di proposito:** i `.bmp` di `graphics/`, che sono la *fonte* da cui grit genera i tile e non un artefatto — oggi segnaposto, domani arte disegnata a mano.
  * **`.gitattributes` non e' cosmetico:** `tools/build_rom.sh` e `tools/check_zero_heap.sh` girano sotto Git Bash, e uno script shell con terminatori CRLF fallisce in modo ostile (`$'
': command not found`). Senza il vincolo `eol=lf`, il primo clone su una macchina con `core.autocrlf=true` avrebbe una build rotta e una diagnosi difficile.

* **Skill `decisioni-aperte`.** Il collo di bottiglia dichiarato del progetto non e' scrivere codice: e' che il GDD si contraddice e che una ventina di scelte non sono mai state prese — e in questo momento e' una di queste (il font) a bloccare il Passo 15. La skill formalizza cio' che le sessioni migliori hanno gia' fatto a mano: **round sulla frontiera** (solo le domande le cui premesse sono risolte), **prove dal GDD prima delle domande** (contare in quante sedi compare ciascuna lettura, come nella Sessione 02b), **tre classi di decisione** (riservate al committente / decidibili motivando / gia' chiuse e da non riaprire) e **chiusura obbligatoria in tre posti** — GDD nella sezione contraddetta, HANDOVER, e codice con `static_assert` dove possibile.
  * Il registro delle decisioni **non e' duplicato** nella skill: resta in `docs/piano_fase_successiva.md` e nella Sezione 0 di `HANDOVER.md`, che sono le fonti.
  * Spunto esterno: il metodo a round e' ripreso dalla skill `/grill-me` di aihero.dev, adattato al protocollo di continuita' di questo progetto. Il resto di quel catalogo e' stato valutato e **scartato**: `/tdd` prescriverebbe una disciplina piu' debole di quella gia' in vigore (gate sull'ELF, prove negative obbligatorie), `/to-issues` e `/triage` presuppongono un tracker inesistente, `/to-prd` e `/domain-model` un documento di dominio mancante — mentre qui il GDD c'e', e il problema e' opposto.

### [2026-08-18] - Sessione 12: Passo 15 — Il Font Italiano (decisione chiusa)

* **Autore / Agente:** Claude Opus 5 (Claude Code)
* **File creati:** `tools/make_font.py`, `graphics/font_gubbio.{bmp,json}`, `include/font_gubbio.h`
* **File modificati:** `src/battle_hud.cpp`, `include/item_data.h`, `Makefile`, `tools/preview_battle_screen.py`, `tests/test_assets.py`, `GUBBIO_1151_LA_BIBBIA_GDD.md` (Sez. 25A), entrambe le copie della skill `asset-pipeline`

* **DECISIONE DEL COMMITTENTE (via `/decisioni-aperte`): font 8x8 proprio del progetto**, non la convenzione con apostrofo e non il passaggio a 8x16. Chiusa anche la sotto-decisione sulle maiuscole: **compresse di una riga con accento sottile**, non apostrofo.

* **La premessa del piano era sbagliata, e la misura lo ha mostrato.** Il Passo 15 presentava la scelta come *"font custom (lavoro d'arte) contro apostrofo (gratuito)"*. Misurando i glifi di Butano:
  * le **minuscole hanno gia' lo spazio** — 3 righe libere sopra `a`, `o`, `u`, 2 sopra `e` — quindi `à è é ò ù` sono **derivate senza ridisegnare nulla**, e sulla `i` l'accento prende il posto del puntino;
  * le **maiuscole** riempiono tutte e 8 le righe: si toglie la riga la cui rimozione si nota di meno. Per `A I O U` esiste una riga **duplicata** e la compressione e' esatta (0 pixel alterati); per la `E`, che ha tutte le righe diverse, il costo misurato e' **2 pixel**.
  * La variante a 6 righe e' stata **generata, guardata e scartata**: accanto alle altre maiuscole la lettera appariva rimpicciolita. La scelta e' stata presa **guardando le tre varianti rese in immagine**, non descritte a parole.

* **Il fabbisogno reale, contato invece che stimato.** Nel GDD ci sono 168 caratteri accentati, ma la maggior parte e' prosa di design che non entra nel gioco. Nelle sole battute: **34 occorrenze, 7 caratteri distinti**. Le maiuscole accentate servono in due punti soli, ed entrambi pesano: `PODESTÀ GUIDO:` (etichetta ricorrente) e `GUBBIO È SALVA.` (schermata finale). Il font ne mappa comunque **12**, cioe' tutto il set italiano: costa 384 byte di ROM e chiude la questione per sempre.

* **Conseguenze applicate nello stesso passo:**
  * il Battle HUD usa il font del progetto — il menu comandi dice ora **"Abilità"** e l'oggetto e' **"Baccalà alla Ceraiola"**;
  * **`../butano/common` rimosso dal `Makefile`** (SOURCES, INCLUDES e GRAPHICS): serviva unicamente al font, ed era marcato "da rimuovere" dalla Sessione 02d;
  * `tools/preview_battle_screen.py` rende con **lo stesso font della ROM**, chiudendo la divergenza dichiarata nella Sessione 05.

* **Verifiche.** Build pulita senza `common`, gate verde. **Accento renderizzato davvero su mGBA**: la ROM di autotest ha disegnato "Abilità" senza alcun `BN_ERROR` — che e' il modo in cui un carattere non mappato si manifesta. Anteprima di battaglia rigenerata e ispezionata a occhio.
  * **Nuovo oracolo con prova negativa:** `tests/test_assets.py` scandisce le stringhe letterali dei sorgenti e fallisce se un carattere non esiste nel font. Verificato inserendo una `ñ` spagnola: il test e' diventato rosso nominando il file. Suite: **31/31 + 9/9 + 9/9**.

* **Nota di metodo.** Questa decisione e' stata sciolta con la skill `decisioni-aperte` alla sua prima applicazione: due round, prove raccolte prima delle domande, e la scoperta — mostrata al committente **prima** che scegliesse — che l'opzione ritenuta costosa costava quasi nulla. Il metodo ha cambiato il contenuto della decisione, non solo la sua forma.

### [2026-08-18] - Sessione 13: Passo 16 - Motore e Finestra di Dialogo

* **Autore / Agente:** Claude Opus 5 (Claude Code)
* **File creati:** `include/dialogue_view.h`, `src/dialogue_view.cpp`, `tools/make_dialogue_frame.py`, `graphics/dialogue_frame.{bmp,json}`
* **File modificati:** `include/dialogue_box.h` (riscritto), `include/scene_exploration.h`, `src/scene_exploration.cpp`, `src/main.cpp`, `GUBBIO_1151_LA_BIBBIA_GDD.md` (Sez. 25A)

* **Metodo: quattro ricognizioni in parallelo prima di scrivere codice** (workflow `gubbio-passo-16-ricognizione`, 4 agenti, ~370k token). Non e' stato un esercizio di stile: **ha corretto il piano su tre punti**, e due di quelle correzioni cambiano il codice.

* **CORREZIONE 1 - tagliare una `string_view` a meta' di una sequenza UTF-8 NON fa scattare alcun assert.** Il piano dava per scontato il contrario ("il primo `substr(0,n)` che taglia a meta' una sequenza a 2 byte fa scattare `BN_BASIC_ASSERT`"). Verificato sui sorgenti: `bn::utf8_character` legge il byte successivo - che e' ancora nel buffer originale - lo trova valido e **disegna il glifo intero** (bn_utf8_character.h:83). Il typewriter mostrerebbe un carattere non ancora rivelato, e se la view finisse esattamente a fine buffer si leggerebbe memoria non posseduta: un difetto che passa i test e sbaglia in produzione. L'assert scatta invece **copiando** il prefisso in una `bn::string` - cioe' proprio nella forma "prudente" che verrebbe naturale adottare.

* **CORREZIONE 2 - il terzo difetto elencato dal piano non esiste.** `bn::string_view::size_type` e' **`int`** (bn_string_view.h:38): non c'era alcun confronto signed/unsigned da normalizzare. Chi lo "correggesse" con cast a `unsigned` introdurrebbe il difetto che crede di togliere, perche' `npos` vale -1. **Confermato indipendentemente dal compilatore**: i cast `int(...)` scritti per prudenza hanno prodotto nove `-Wuseless-cast`. Annotato nel file perche' nessuno lo "ripari" domani.

* **CORREZIONE 3 - il confine di sprite non e' "4 caratteri a 32 px".** Il font del progetto e' a larghezza variabile: Butano chiude lo sprite quando la somma delle larghezze supera 32 px, che in prosa italiana sono ~6 caratteri. Contando 4 caratteri i pezzi finirebbero a x sbagliate (4 minuscole sono 20 px, non 32) e **il testo scivolerebbe verso destra riga dopo riga, senza alcun assert a segnalarlo**. `dialogue_view` misura il confine in pixel con `sprite_text_generator::width()`.

* **Difetti chiusi in `dialogue_box.h`**, che dalla Sessione 01 non era mai stato compilato: avanzamento per codepoint via `bn::utf8_character::size()`; contratto sulla durata statica delle view, con `show_composed()` che copia in un buffer membro da 64 byte; **guardia su `show_message` re-entrante** e **`close()` esplicito**, che mancavano del tutto - trovati dalla ricognizione, non erano in elenco. La classe espone ora `visible_row()`, cioe' la sottostringa gia' tagliata, e non un contatore che ogni chiamante dovrebbe interpretare a modo suo.

* **`dialogue_view`: si rigenera solo la coda in crescita.** Gli sprite gia' composti non si toccano piu'; la coda si chiude quando supererebbe i 32 px. Rigenerare tutto a ogni carattere sarebbe stato ~21 create/release ogni 2 frame, oltre 300 operazioni al secondo sull'allocatore best-fit. La cornice e' un BG su BG0 (`tools/make_dialogue_frame.py`, 12 tile unici), allocato all'ingresso della scena e tenuto invisibile finche' non serve.

* **VERIFICATO SU EMULATORE.** La battuta di prova contiene accenti di proposito:
  ```
  DIALOGO aperto (battuta di prova, 3 righe)
    riga 0 completata (28 byte), passa alla 1     <- 27 caratteri, 28 byte
    riga 1 completata (27 byte), passa alla 2     <- 25 caratteri, 27 byte
  DIALOGO chiuso: sprite al picco 15 tile OBJ 120
  ```
  I byte tornano esattamente: il typewriter ha attraversato le sequenze a 2 byte senza spezzarle. 15 sprite sulle 128 allocazioni disponibili, 120 tile su 1024.

* **PROVA NEGATIVA.** Aggiunto un invariante che verifica che il cursore non cada mai su un byte di continuazione (`10xxxxxx`). Rimesso l'avanzamento in byte - il difetto originale - **l'esecuzione si arresta sulla prima parola accentata**: il log si ferma a "DIALOGO aperto" e nessuna riga viene completata. Ripristinato l'avanzamento corretto, le tre righe si completano. E' l'unico modo di far fallire subito un difetto che, come dice la Correzione 1, altrimenti non fallirebbe affatto.

* **Conflitto di input messo a verbale.** B e' corsa nell'overworld e skip nel dialogo; A e' interazione e chiusura. Non c'e' danno perche' **il dialogo sospende l'esplorazione**: le due modalita' non sono mai attive nello stesso frame. Restera' vero finche' non ci sara' un dialogo *durante* la battaglia (previsto per boss e Mosse Supreme), dove fast-forward e skip collidono sullo stesso tasto; la regola gia' scritta e' che li' il fast-forward va sospeso.

* **Esito:** build pulita, gate verde, `test_battle_engine.py` 31/31, `test_assets.py` 9/9, `test_save_system.py` 9/9.

### [2026-08-18] - Sessione 14: Passo 17 - Copione, NPC e Quest in ROM

* **Autore / Agente:** Claude Opus 5 (Claude Code)
* **File creati:** `tools/dialogue_exporter.py`, `include/dialogue_data.h` (generato), `include/npc_registry.h`, `include/quest_data.h`, `tests/test_dialogue_quest.py`
* **File modificati:** `src/scene_exploration.cpp` (la battuta di prova viene ora dalle tabelle)

* **Il copione e' GENERATO, non trascritto.** `tools/dialogue_exporter.py` contiene le battute della Sez. 31B e produce `include/dialogue_data.h` con le righe **gia' spezzate**. Il wrap e' fatto **in pixel**, sommando le larghezze reali di `font_gubbio.h`: spezzare a 28 caratteri, il numero della Sez. 25, darebbe righe da 90 a 220 px — alcune fuori dal box, altre mezze vuote. Esito: 7 script, 21 battute, 47 righe, con la riga piu' larga a **211 px su 212 disponibili**.

* **Tabelle piatte, perche' il codice del GDD non e' trascrivibile.** La Sez. 31C usa `bn::vector<DialogueNode, 4>` dentro un array `constexpr`: `bn::vector` non e' un tipo letterale in Butano e non compilerebbe. Qui le battute stanno in un unico array e ogni script e' un **intervallo** su di esso; gli NPC puntano a intervalli di condizioni con la regola **prima-corrispondenza-vince**. Nessun contenitore annidato, tutto in ROM, zero RAM.

* **Due difetti veri trovati dai test, non dedotti:**
  1. **Le sostituzioni degli accenti non scattavano.** L'esportatore converte `citta'` in `città` — il font ha le accentate dalla Sessione 12 — ma la regex usava `\b` anche in coda, e **fra un apostrofo e lo spazio che segue non c'e' confine di parola**: nessuna sostituzione avveniva. Il copione sarebbe finito in ROM con gli apostrofi, cioe' con la resa che la decisione sul font aveva esplicitamente scartato. Il test `test_nessun_apostrofo_al_posto_di_un_accento` l'ha trovato elencando le sette parole colpite.
  2. **Una battuta non entrava nel box.** L'esportatore ha rifiutato `RANIERO_QUEST[1]` perche' occupava 4 righe su 3 disponibili, ed e' stata divisa in due battute successive — non troncata: tagliare il contenuto sarebbe una scelta di sceneggiatura, e non spetta a un esportatore.

* **Invarianti verificati dal COMPILATORE**, non dai test: ogni script sta dentro la tabella delle battute; ogni NPC punta a un intervallo valido; **nessun NPC e' collocato dentro un muro** (verificato contro la stessa `get_tile_type` della collisione); e le due condizioni del Podesta' sono nell'ordine giusto — l'Atto III precede l'Atto I, perche' con la regola prima-corrispondenza-vince invertirle mostrerebbe la battuta d'apertura durante l'assedio.

* **Quest: cinque, con una riserva dichiarata.** `quest_data.h` porta le cinque quest della Sez. 31A con obiettivi conformi (Q-SM01 tre blocchi di ferro, Q-SA01 quattro radici) e le lega agli indici di `GameState::quest_state` / `quest_counter`, che restano separati per la ragione a verbale dal Passo 4: **un bit non sa contare fino a 3**. Le ricompense vere della Sez. 31A sono equipaggiamenti e chiavi (Corazza Rinforzata, Spilla della Rosa, Patente da Matto) che **nel gioco non esistono**: non c'e' un sistema di equipaggiamento e la Patente e' una decisione aperta. Finche' non esistono, ogni quest consegna un consumabile della Sez. 8E, **dichiarato come segnaposto** nel file.

* **VERIFICATO SU EMULATORE:** la battuta non e' piu' un letterale nel codice ma viene dalle tabelle, scelta secondo l'atto in corso.
  ```
  DIALOGO da tabella: Podesta' Guido, atto 1, script 0 (5 battute)
    riga 0 completata (41 byte), passa alla 1
  DIALOGO chiuso: sprite al picco 10 tile OBJ 100
  ```

* **Esito:** build pulita, gate verde, `test_battle_engine.py` 31/31, `test_assets.py` 9/9, `test_save_system.py` 9/9, `test_dialogue_quest.py` 6/6.

### [2026-08-18] - Sessione 15: World building - la citta' reale come riferimento

* **Autore / Agente:** Claude Opus 5 (Claude Code)
* **File creati:** `docs/riferimenti/FONTI.md`, `tools/fetch_riferimenti.py`
* **File modificati:** `GUBBIO_1151_LA_BIBBIA_GDD.md` (Sez. 23), `.gitignore`

* **DECISIONE DEL COMMITTENTE: la citta' e' quella che si riconosce, non quella del 1151.** Presa dopo un rilievo che nessuna sessione aveva sollevato: **quasi nessuno dei monumenti che rendono Gubbio riconoscibile esisteva nel 1151**. Il Palazzo dei Consoli e' del **1332-1349** (Angelo da Orvieto, fonte verificata su Wikipedia), Piazza Grande esiste *perche'* esiste quel palazzo, il Palazzo Ducale e' quattrocentesco, e la Basilica di Sant'Ubaldo custodisce un santo che nel 1151 e' **vivo** ed e' il protagonista. Si riproducono tutti comunque: il valore perseguito e' che un eugubino riconosca la propria citta'. Annotato in Sez. 23 del GDD perche' nessuno "corregga" la mappa fra dieci sessioni.

* **LA SCALA ESISTEVA GIA' E NESSUNO L'AVEVA USATA.** La tabella dei monumenti della Sez. 23 riporta dimensioni reali *e* dimensioni GBA: dividendole viene **1,5 metri per tile**, coerente su cinque monumenti su sei (l'eccezione e' il ponte dell'acquedotto, 1,2 m reso con 2 tile perche' sotto quella soglia non sarebbe percorribile). Non serviva inventare una convenzione: ne esisteva una, inespressa.

* **CONSEGUENZA DA PORTARE AL COMMITTENTE:** con quella scala, **Piazza Grande come implementata non e' in scala**. 64x40 tile sono 96 x 60 m contro i 130 x 40 m reali: un quarto piu' corta, mezza volta piu' profonda. La motivazione con cui la Sessione 11b scelse 64x40 ("86 eccede i 64 del riquadro") **non regge**: 86 tile sono 688 px, e un BG regolare `big` da 1024x256 li contiene. Ma il conflitto vero e' un altro e non e' tecnico: la piazza vera e' **lunga e stretta**, e 26 tile di profondita' lasciano poco spazio verticale di gioco. Fedelta' e giocabilita' qui divergono davvero.

* **Il dislivello e' la struttura della citta', e il GDD lo tocca in due punti che non erano stati collegati.** La Sez. 23 descrive Piazza Grande con "ringhiera sud su vuoto con parallasse della piana" — e quella ringhiera e' gia' nella griglia di collisione (tile tipo 2, y >= 38) — mentre gli **Arconi di Sostruzione** restano "un secondo livello mai mappato" (decisione aperta n.10). Sono la stessa cosa vista da sopra e da sotto: la piazza e' **pensile**. Via raccomandata: **quota per area, scalinate come transizioni** (il meccanismo dei trigger gia' collaudato), con gli Arconi come mappa a se' sotto la piazza. Scartate: quota per singolo tile (potenza inutile su una citta' a terrazze) e vista a tre quarti (raddoppia il lavoro d'arte e contraddice la Sez. 21D).

* **La pianta turistica fornita dal committente** censisce 30 monumenti georiferiti, i toponimi delle vie e le piazze minori; **non** perimetra i quattro Quartieri dei Ceri, che restano da procurare. Da essa si legge la struttura urbana che conta: **fasce parallele che salgono da sud-ovest a nord-est** — Piazza 40 Martiri in basso, la fascia di via dei Consoli lungo il Camignano, il ripiano di Piazza Grande, via XX Settembre, il livello del Duomo e del Palazzo Ducale, la Rocca e il monte.

* **`docs/riferimenti/FONTI.md`**: i 30 monumenti classificati in canonici / sfondo / fuori scope, con la colonna "nel 1151" resa informativa, i riferimenti verificati su Wikimedia Commons (la categoria del Palazzo dei Consoli da sola ha **194 file**) e — la parte che serve a chi disegna — **i tre segni distintivi** per edificio. A 1,5 m/tile una facciata sta in venti tile: non ci stanno i dettagli, ci stanno tre segni. Un quarto non aggiunge riconoscibilita', aggiunge costo.

* **Le immagini NON sono versionate** (`.gitignore`): pesano e si porterebbero dietro le proprie licenze. In repo va `FONTI.md` con URL, autore e licenza; `tools/fetch_riferimenti.py` le scarica in locale. Si usa Wikimedia Commons e non una ricerca immagini generica, perche' li' la licenza e' dichiarata e l'attribuzione tracciabile.

* **Nessun download eseguito**: `fetch_riferimenti.py` e' pronto ma va lanciato dal committente, o su sua conferma.

### [2026-08-18] - Sessione 16: Riferimenti scaricati e griglia della piazza in scala

* **Autore / Agente:** Claude Opus 5 (Claude Code)
* **File modificati:** `include/piazza_grande_collision.h`, `tools/make_piazza_art.py`, `tools/fetch_riferimenti.py`

* **Riferimenti scaricati** da Wikimedia Commons su autorizzazione del committente: 4 immagini (Palazzo dei Consoli, Piazza Grande x2, via dei Consoli), con licenze **CC BY-SA 3.0/4.0 e CC BY 3.0** registrate in `riferimenti/CREDITI.txt` insieme agli autori. Il primo tentativo ha preso un **HTTP 429**: Wikimedia limita le richieste ravvicinate e pretende uno User-Agent descrittivo. Lo script ora attende fra una richiesta e l'altra e riprova con attesa crescente.

* **La griglia della piazza applica la regola dell'illusione.** Prima tutta la fascia nord era `WALL` indistinto: il palazzo simbolo della citta' non si distingueva da un magazzino. Ora ci sono tre tipi nuovi:
  * `CONSOLI_FACADE` — fronte di **22 tile**, che sono i 33 m reali alla scala di 1,5 m/tile, centrato sul portone;
  * `PRETORIO_FACADE` — 16 tile (25 m), che **fronteggia i Consoli dal lato opposto**, come nella citta' vera, stando davanti alla ringhiera e non al posto suo;
  * `STAIRS` — la scalinata a ventaglio davanti al portone, **calpestabile**: e' il primo dei tre segni distintivi del palazzo.

* **Due `static_assert` nuove tengono l'illusione.** Una **conta i tile del fronte** nella griglia derivata e pretende che siano 22: se qualcuno allargasse il palazzo "perche' sta meglio", la build si ferma sull'edificio che regge tutta la riconoscibilita'. L'altra verifica che la scalinata ci sia e che non sia solida.

* **Verifica visiva:** nell'anteprima il Palazzo dei Consoli in pietra chiara si stacca nettamente dagli edifici minori ai lati, resi piu' scuri, col portone e la scalinata al centro e la piazza in cotto rosso. E' la prima volta che la piazza somiglia a Piazza Grande invece che a un cortile.

* **Pretorio e lati corti (stessa sessione).** Il Pretorio ha ora il suo **ingresso** sul fronte che guarda la piazza — solo visivo, non un trigger: aprirlo vorrebbe dire una quarta regola in `MAPS[]` e le sale non esistono; disegnarlo costa un tile e rende il palazzo un edificio invece di un blocco cieco. I **lati corti sono edificati**: Piazza Grande e' uno spazio CHIUSO su quattro lati, ed e' da li' che viene l'effetto che fa — un vuoto vasto ritagliato dentro un tessuto fitto. Finche' restavano aperti, la piazza sfumava nel nulla e sembrava un cortile. Restano liberi i due varchi, che nella citta' vera sono passaggi voltati.

* **Altre tre `static_assert`:** che i lati corti non lascino suolo libero sui bordi; che **i due varchi non siano stati murati** chiudendo la piazza (l'errore che verrebbe naturale commettere); che l'ingresso del Pretorio ci sia.

* **Esito:** build verde, gate verde, `test_assets.py` 9/9. Tile unici del suolo da 9 a 11, ampiamente entro il budget di 512.

### [2026-08-18] - Sessione 17: Passo 18 - Runner dei dialoghi e NPC interattivi

* **Autore / Agente:** Claude Opus 5 (Claude Code)
* **File creati:** `include/dialogue_runner.h`, `graphics/overworld_npc.{bmp,json}`
* **File modificati:** `tools/make_piazza_art.py`, `include/scene_exploration.h`, `src/scene_exploration.cpp`, `src/main.cpp`

* **`DialogueRunner`: due interi di stato.** Uno script e' un intervallo di battute in `DIALOGUE_LINES`, quindi per eseguirlo bastano "quale script" e "a che punto sono". Niente stack di chiamate, niente contenitori. E' anche cio' che rendera' banale salvare lo stato di un dialogo interrotto, se un giorno servira'.
  * **Perche' non dentro `DialogueManager`:** il manager sa una cosa sola — come si rivela un testo — e la fa bene. Chi decide *quale* testo, *in che ordine* e *cosa succede dopo* e' un'altra responsabilita'. Separate, il motore del testo resta verificabile da solo e il runner puo' crescere senza toccarlo.

* **L'interazione e' quella definitiva:** tasto **A** davanti a un NPC, che rimpiazza il trigger provvisorio su R della Sessione 13. Lo script recitato dipende dall'atto in corso, con la regola prima-corrispondenza-vince gia' verificata a compile time. Raggio di 12 px, generoso di proposito: con una hitbox ai piedi e un NPC alto 16 px i centri non coincidono mai, e pretendere la sovrapposizione esatta darebbe un giocatore che preme A e non capisce perche' non succeda nulla.

* **Gli NPC sono sprite presi dalla tabella.** Chi autora il copione mette un personaggio in piazza **scrivendo una riga in `npc_registry.h`**, senza toccare la scena. Tre pose statiche distinte per colore della veste: a 16x16 e' il colore a distinguere un personaggio, non i lineamenti.

* **Effetti di fine script: deliberatamente minimi.** Solo le bandiere di "gia' visto". `START_QUEST`, `GIVE_ITEM` e le scelte entrano nello stesso `switch` quando avranno senso: **meta' meccanica in un salvataggio persistente e' peggio di nessuna meccanica** — una quest che parte e non puo' essere consegnata resterebbe aperta per sempre nei `.sav` gia' scritti.

* **VERIFICATO SU EMULATORE:** `PARLA CON Podesta' Guido (atto 1, script 0, 5 battute)`, con la macchina da scrivere che percorre le righe.
  * **La prima stesura dell'autotest sbagliava, e il log l'ha mostrato subito:** 128 frame di corsa sono 256 px, ma la distanza dal punto di rientro al Podesta' e' 200 — il giocatore lo **superava** e premeva A nel vuoto. Corretto a 100 frame esatti. E' il tipo di errore che senza una traccia leggibile si sarebbe scambiato per "l'interazione non funziona".

* **Esito:** build pulita, gate verde, tutte e quattro le suite verdi.

### [2026-08-18] - Sessione 18: La citta' vera entra nel gioco

* **Autore / Agente:** Claude Opus 5 (Claude Code)
* **File creati:** `tools/photo_to_tiles.py`, `docs/riferimenti/FONTI.md`, `tools/fetch_riferimenti.py`, `include/city_reference.h`
* **File modificati:** `tools/make_piazza_art.py`, `tools/make_placeholder_art.py`, `include/piazza_grande_collision.h`, `.gitignore`, GDD (Sez. 23 e 25)

* **IL VINCOLO CHE HA DETERMINATO TUTTO: zero budget, nessun artista, il committente non disegna.** Da qui l'unica strada praticabile — convertire fotografie in tile con uno strumento. Prima di costruirlo l'ho provato a mano: la facciata disegnata proceduralmente rendeva la merlatura (motivo regolare) ma sbagliava le arcate e non produceva affatto la torre. **La conversione fotografica batte il disegno procedurale** perche' conserva le PROPORZIONI vere, che sono cio' che l'occhio riconosce.

* **`tools/photo_to_tiles.py`**, e i tre problemi che una conversione ingenua non risolve:
  1. **Una foto non ha ripetizione**: ridurre e quantizzare da' 381 tile unici su 418 celle, mentre un tileset vive del contrario. I tile quasi identici vengono unificati con una **soglia che cresce finche' non si rientra nel budget**, e la soglia raggiunta viene stampata: dice quanto dettaglio si e' dovuto sacrificare.
  2. **La palette non puo' venire dalla foto**: sedici colori per tutto cio' che sta su un BG a 4bpp. La palette e' un parametro **per famiglia di asset** — provato: lo skyline quantizzato sui colori della piazza collassava a **UN solo tile unico**, cioe' a una macchia uniforme.
  3. **Il rumore fotografico diventa sporcizia**: si sfoca prima di ridurre, con raggio proporzionale al fattore di riduzione.

* **Cinque asset dal vero, tutti in gioco:** facciata dei Consoli (174 tile), selciato a spina di pesce (8), fronte del Pretorio (44), Fontana dei Matti (9), skyline nel fondale di battaglia (114). Il suolo di Piazza Grande e' passato da 14 a 234 tile unici, su un tetto di 512.

* **Tre difetti trovati guardando i risultati, non deducendoli:**
  * il **cielo della fotografia** finiva sulla mappa come un rettangolo azzurro attorno al palazzo, perche' la quantizzazione lo mandava sull'indice dell'acqua della fontana;
  * i **mattoni erano giganti** rispetto al giocatore: il ritaglio del selciato era troppo stretto, e un mattone reale e' un sesto di tile;
  * il **selciato veniva grigio** invece che rosso, perche' la foto e' in ombra e i suoi grigi somigliano alla pietra piu' che al cotto. Da qui `solo_indici`, che restringe la conversione a un sottoinsieme di colori.

* **Due difetti trovati dalla build e dai test:** gli ingredienti non possono stare in `graphics/`, dove grit pretende un `.json` accanto a ogni `.bmp` (ora stanno in `ingredienti/`, non versionata); e le entry inutilizzate della tavolozza erano nere, cosi' PIL poteva assegnare indici oltre la palette reale.

* **DECISIONI DEL COMMITTENTE, entrambe annotate nel GDD:** si riproducono **tutti** i monumenti anche se posteriori al 1151 — conta che un eugubino riconosca la propria citta' — e si accettano **compromessi per la giocabilita' purche' resti l'illusione**, tradotta in `city_reference.h`: la scala vincola gli EDIFICI (1,5 m/tile, entro un tile), non le DISTANZE (comprimibili, oggi al 73%); ordine e adiacenze restano vincolanti.

* **Esito:** build verde, gate verde, tutte le suite verdi.

### [2026-08-18] - Sessione 18b: Tre difetti che solo giocare poteva mostrare

* **Autore / Agente:** Claude Opus 5 (Claude Code)
* **File modificati:** `src/scene_exploration.cpp`, `src/dialogue_view.cpp`, `include/dialogue_box.h`

* **UNA SOLA RADICE PER DUE DEI TRE: in Butano l'origine di un background e' il suo CENTRO, non l'angolo in alto a sinistra.** Il suolo 512x512 lasciato a `(0,0)` metteva il proprio pixel centrale sull'origine del mondo, sfasando la mappa di meta' immagine: il giocatore camminava fuori dall'area disegnata e vedeva il cielo attraverso le zone trasparenti. La stessa cosa spostava la cornice del dialogo 48 px piu' in alto del testo — che essendo fatto di sprite usa coordinate di schermo — col risultato di un box nero sopra e le parole sotto.

* **Il crash:** `bn::string_view()` di default ha `data() == nullptr`, e costruirne una nuova su quel puntatore fa scattare `Null char array ptr` (bn_string_view.h:91). Capitava su ogni battuta con meno di tre righe. Le righe assenti sono ora stringhe vuote vere, che un puntatore valido ce l'hanno.

* **PERCHE' L'AUTOTEST NON LI AVEVA VISTI, ed e' il punto che vale piu' della correzione.** L'autotest legge i `BN_LOG` e riportava "zero assert, ciclo completo": era vero, la logica funzionava. Ma un oracolo che guarda solo il testo non puo' accorgersi che il pavimento e' nel posto sbagliato. E' la regola n.1 del progetto vista da un'angolazione nuova — non basta che un controllo POSSA fallire, deve poter fallire **su cio' che conta**. Aggiunta come regola 0 in Sezione 0.

* **Esito:** build pulita, gate verde, autotest senza errori a runtime.

### [2026-08-18] - Sessione 18c: I tre crash della giunzione testo/disegno

* **Autore / Agente:** Claude Opus 5 (Claude Code)
* **File modificati:** `include/dialogue_box.h`, `src/dialogue_view.cpp`, `src/scene_exploration.cpp`, `tools/photo_to_tiles.py`, `src/main.cpp`

* **TRE CRASH IN FILA, TUTTI NELLO STESSO PUNTO: la giunzione fra il motore che avanza per CARATTERI e la vista che disegna per PIXEL.** Nessuno era visibile senza giocare.
  1. `Null char array ptr` su `show_message`: `bn::string_view()` di default ha `data() == nullptr`.
  2. **Lo stesso errore, tornato**: avevo corretto `show_message` ma `visible_row` restituiva ancora la view di default in tre altri rami, e chi ci fa aritmetica sopra — la coda in crescita, che calcola `data() + offset` — sbatteva ugualmente. **Rincorrere il difetto nei chiamanti non basta**: ora esiste una sola `VUOTA` valida, restituita ovunque.
  3. `Invalid character` nel disegno: **la vista non taglia dove taglia il motore**. Il motore avanza per codepoint, ma la vista spezza la riga anche ai confini di sprite, decisi dalla larghezza in pixel — una misura che di UTF-8 non sa nulla. Bastava che un confine cadesse dentro una lettera accentata. Ora ogni offset e' arretrato al piu' vicino inizio di carattere, con un assert a guardia.

* **Perche' l'autotest non ne vedeva nessuno.** Andava solo dal Podesta', che ha battute da tre righe; il crash del puntatore nullo stava sulle battute a due righe di **Mastro Tano**. E l'errore UTF-8 richiedeva che un confine di sprite cadesse su una accentata — cioe' una coincidenza fra dati e larghezze che nessun log poteva mostrare.

* **DA VERIFICARE ALLA PROSSIMA SESSIONE:** il fix del taglio UTF-8 **non e' stato collaudato a runtime**. L'autotest e' stato puntato su Mastro Tano (`GUBBIO_SE_68`) ma la traiettoria non lo raggiunge: nel log non compare `PARLA CON`. Serve tarare la camminata, oppure — meglio — un test che simuli i confini di sprite sul copione vero e verifichi che nessun taglio cada dentro una sequenza.

* **Rilievi del committente dal gioco vero, entrambi corretti:** del Palazzo dei Consoli si vedeva solo la parte bassa (il ritaglio prendeva la sola fascia alta della foto; ora entra tutto, compresso in verticale) e la trama del selciato era troppo grossa (texture da 4 tile invece di 8).

### [2026-08-19] - Sessione 19: Largo del Bargello, la seconda area

* **Autore / Agente:** Claude Opus 5 (Claude Code)
* **File creati:** `include/largo_bargello_collision.h`, `graphics/bargello_ground.{bmp,json}`
* **File modificati:** `include/map_id.h`, `include/map_data.h`, `tools/make_piazza_art.py`, `tools/photo_to_tiles.py`, `include/piazza_grande_collision.h`, GDD (Sez. 21B)

* **NASCE DA UNA CORREZIONE DEL COMMITTENTE:** la Fontana dei Matti non e' in Piazza Grande, ma in **Largo del Bargello, lungo la salita di via dei Consoli**. La legenda della Sez. 21B GDD la elencava fra i tile della piazza e il codice l'aveva ereditata. **Nessuna verifica automatica poteva trovarlo**: il gioco funzionava benissimo con la fontana nel posto sbagliato. Serviva qualcuno che conoscesse la citta'.

* **La seconda area del gioco, e la prima che dimostra che l'architettura regge.** 32x24 tile in un **solo BG 256x256**, contro i quattro blocchi che Piazza Grande consuma con i suoi 512x512 — un largo non e' una piazza. Ground generato dalla foto del committente: facciata del Bargello (80 tile), fontana (9), stesso selciato della piazza, per **107 tile unici su 512**.

* **Quanto e' costato aggiungerla:** un header di collisione, una riga in `MAPS[]`, un ritaglio nella tabella di `photo_to_tiles`, e una funzione di disegno. **Nessuna modifica a `ExplorationScene`**, che e' parametrizzata da `MapId` dalla Sessione 11b proprio per questo. E' la prima verifica reale di quella scelta.

* **Topografia, per la regola delle adiacenze** (`city_reference.h` §3): il largo e' in salita e **Piazza Grande sta piu' in alto, a est**; l'uscita verso la piazza e' quindi sul lato orientale, e a ovest la via prosegue a scendere verso San Martino, non ancora autorato. Il varco occidentale della piazza — che apriva provvisoriamente una battaglia — porta ora dove deve.

* **Tre `static_assert` per la nuova area:** la fontana e' al posto suo; il fronte del palazzo misura i 12 tile che la scala impone ai suoi 18 metri; il varco verso la piazza non e' murato — un vicolo cieco si scoprirebbe solo giocando.

* **VERIFICATO SU EMULATORE:** `TRIGGER tile 4 -> scena 1 parametro 5` seguito da `=== ESPLORAZIONE: Largo del Bargello ===`. Zero errori a runtime, `test_assets.py` 9/9.

---

## 4. Prossimi Passi Immediati (Roadmap per la Prossima Sessione / IA)

1. **Sostituire i segnaposto con la pixel art vera (decisione: chi la produce):**
   - La pipeline e' pronta: basta sovrascrivere i `.bmp` in `graphics/` mantenendo misure (Sez. 23A) e limite di 16 colori. Nessuna modifica al C++.
   - Mancano ancora, rispetto al GDD: animazioni di battaglia (Sez. 23B: pose di attacco, colpito, evocazione), icone della timeline in alto a destra (Sez. 20A) e la vera dissolvenza di `INTRO_FADE_IN`.
   - Verificare a occhio la schermata su emulatore: l'anteprima e' una composizione, non una cattura.

2. **Code di bilanciamento minori (non bloccanti):**
   - Riconciliare l'immunita' condizionata di Corrado (Sez. 26A: "immune al taglio finche' non applicata l'Ustione") con l'attuale resistenza fissa al fisico x0.5.
   - Confermare i `magic_resist` derivati (72/40/56) e il bersaglio predefinito del Muro della Fede (oggi il lanciatore stesso, non l'alleato piu' esposto).
   - Valutare se anche Sant'Ubaldo debba guadagnarsi la Suprema: entra a 144 Fervore contro 125 di costo, quindi puo' aprire con essa.

3. **Asset audio:**
   - Riattivare `#include "bn_sound_items.h"` e le chiamate in `include/campanone_audio.h` quando i campioni del Campanone entrano in `audio/`: l'include e' disattivato perche' Butano genera quell'header solo in presenza di asset audio. La vera dissolvenza dello stato `INTRO_FADE_IN` va implementata insieme al rendering.

4. **Completamento dei Comandi:**
   - Il comando `Oggetti` e' inerte (nessun sistema di inventario). Implementare `include/item_data.h` con i consumabili gastronomici della Sez. 8E GDD.
   - Combo dei Tre Ceri (Sez. 12C): Lancia Incandescente, Egida della Purificazione, Giudizio del Monte Ingino, Alzata Trionfale.
   - Routine IA specifiche dei boss (Sez. 26): al momento tutti i nemici usano la regola del mob comune.

5. ~~**Overworld Scene Manager**~~ — **FATTO nella Sessione 11b.** La scena si chiama
   `ExplorationScene` ed e' parametrizzata da `MapId`; `scene_piazza_grande.h` non esiste e non
   deve essere creato (le mappe sono righe di `MAPS[]`, non classi). Quel che resta da fare li'
   sopra: NPC e dialoghi (Passi 16-18), e la sostituzione del trigger di battaglia provvisorio.

6. **Database Dialoghi & Quest 4 Quartieri (`include/quest_data.h` / `include/dialogues_data.h`):**
   - Trascrivere le tabelle NPC e quest censite nella Sezione 31 del GDD in array costanti C++ in ROM.
