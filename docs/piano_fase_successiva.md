# PIANO: FASE SUCCESSIVA (overworld, scene, dialoghi, salvataggio, animazioni)

> Prodotto dal workflow `gubbio-fase-successiva` (Sessione 07): 5 ricognizioni parallele,
> sintesi, 3 critici avversariali (hardware GBA, regole AGENTS.md, coerenza col costruito),
> consolidamento finale. **Non ancora implementato**, salvo il Passo 0a gia' applicato
> (riallineamento dell'autotest).

---

# PIANO DEFINITIVO — Fondazione Architetturale, Overworld, Dialoghi, Salvataggio, Animazioni

> Revisione del piano dopo il vaglio di tre critici indipendenti. Tutte le affermazioni tecniche qui sotto sono state **verificate sui sorgenti reali** (Butano in `C:/Users/cioti/Desktop/PROGETTI/butano`, ELF `gubbio1151.elf`, ROM `gubbio1151.gba`); dove il piano originale o un critico avevano torto, la prova è citata con file e riga.

---

## 0. Regola permanente (vale per tutti i passi)

Ogni passo che tocca codice si chiude con **due scritture obbligatorie**, non negoziabili (AGENTS.md §4, "REGOLA FERREA: Protocollo di Continuità"):
1. `HANDOVER.md`: file toccati, decisione tecnica, esito dei test, prossimo passo.
2. `GUBBIO_1151_LA_BIBBIA_GDD.md`: se il passo ha risolto una contraddizione del documento master, la sezione contraddetta va corretta con nota di revisione datata, **nella forma già usata nelle Sessioni 02b e 04**. Il precedente è a verbale: *"Senza questo passo la riconciliazione non sarebbe durevole: la sessione successiva avrebbe letto 70 nel documento master e lo avrebbe ripristinato."*

Regola di stile introdotta al Passo 1 ed ereditata da tutti i successivi: **ogni tabella `constexpr` a namespace scope in un header è `inline constexpr`**. In C++17/20 `constexpr` a namespace scope implica linkage interno: senza `inline` ogni `.cpp` che include l'header riceve la propria copia in `.rodata` e i puntatori memorizzati in `MapDescriptor` differiscono fra unità di traduzione, distruggendo proprio la "fonte di verità unica" che il piano vuole garantire.

---

## PASSO 0 — Gate di verificabilità (bloccante, prima di qualunque altra cosa)

**File:** `src/main.cpp`, `tools/check_zero_heap.sh`, `tools/build_rom.sh`, `tests/test_zero_heap.py`, `tests/test_assets.py`, `Makefile`, `HANDOVER.md`

Nessun passo successivo può essere collaudato finché questi quattro controlli non sono verdi, perché oggi **l'oracolo principale del piano è rotto** e la policy zero-heap è dichiarata, non misurata.

**0a. Ricalibrare l'autotest — difetto verificato.** `src/main.cpp:64` fissa `GUBBIO_AUTOTEST_ALIGN "00" "00"`, con il commento (righe 59-63) che documenta "due frame di scarto: uno da `bn::core::init()`, uno dallo stato INTRO_FADE_IN". Quel 2 è della Sessione 03, quando l'intro transitava in un frame. La Sessione 06 ha portato `INTRO_DURATION_FRAMES = 32` (`src/battle_scene.cpp:26`) e l'intro consuma ora 32 update (`src/battle_scene.cpp:169`) senza leggere input: **lo script slitta di 31 posizioni**. È il difetto della Sessione 02e tornato in silenzio, e nessuna sessione dopo la 06 ha pubblicato una traccia di round — la 06 dichiara solo "raggiunge CMD GIORGIO", la 07 "zero assert", che è esattamente ciò che un autotest disallineato continua a produrre.
- Correzione immediata: `ALIGN` a `1 + INTRO_DURATION_FRAMES` frame.
- Correzione strutturale (necessaria comunque, perché i Passi 5 e 6 spostano ancora il budget di frame iniziale): l'autotest non deve più essere a frame fissi. Emettere un `BN_LOG` per ogni azione accodata (attore, `SkillId`, boost, bersaglio) e far confrontare a `tests/` la **sequenza registrata** con quella attesa.
- Ripubblicare in `HANDOVER.md` la traccia dei 4 round come baseline. *Prima di usarlo come criterio di accettazione, l'autotest deve fallire quando deve fallire.*

**0b. `tools/check_zero_heap.sh`, invocato da `build_rom.sh`.** Fallisce la build se `arm-none-eabi-nm gubbio1151.elf` contiene: `_Znwj`, `_ZnwjSt11align_val_t`, `_Znaj`, `_ZdlPv`, `_ZdaPv`, `__cxa_pure_virtual`, `^malloc$`, `_malloc_r`, `_calloc_r`, `_realloc_r`, `_sbrk`, `ewram_alloc`, o qualunque `__aeabi_d[a-z]+` / `__aeabi_f2d` (divieto float/double). **Esclusioni obbligatorie, con commento che ne spieghi il perché:** `free` (stub newlib da 12 byte a `0x080149cc`) e `mm*` (maxmod, `mmAllocChannel` a `0x0300080c`) sono presenti nella ROM pulita di oggi — un gate scritto come `grep -iE 'malloc|free'`, quello suggerito dai conflitti del piano originale, **nascerebbe rosso**. Baseline misurata ora: nessun `operator new/delete`, nessun `malloc`, nessun `__aeabi_d*`. La policy regge: questo è il momento di congelarla.
Il gate verifica inoltre: (a) `g_game_state` a indirizzo `0x02......` e non `0x03......`; (b) ogni tabella nota compare **una sola volta** in `nm --print-size`; (c) nessun simbolo del namespace `gubbio` con classe `b`/`B`/`d`/`D` a parte `g_game_state`; (d) `bn::core::update()` non compare in nessun file fuori da `include/game_clock.h`; (e) nessun `new `, `unique_ptr`, o factory che ritorni `Scene*` nei sorgenti del progetto.

**0c. `Makefile`: `USERCXXFLAGS := -Wdouble-promotion -Wfloat-conversion -Wfloat-equal -Werror=double-promotion`.** Oggi è vuoto: il divieto float/double di AGENTS.md non è applicato da nulla. `bn::fixed` ha costruttori impliciti `constexpr` da `float` e da `double`, quindi `bn::fixed v = 1.5;` compila senza un warning.

**0d. `tests/test_assets.py`.** Rilegge ogni `.bmp` in `graphics/` con la sua `.json` e verifica: `bpp_mode` **esplicito**; palette indicizzata ≤ 16 colori se `bpp_4`; per gli sprite, presenza del campo `height`, `bmp.height % height == 0`, e `(width, height)` fra le misure OBJ legali; conteggio dei tile unici entro il budget del Passo 9.

---

## PASSO 0-BIS — Allineamento del GDD alle decisioni del designer (bloccante)

**File:** `GUBBIO_1151_LA_BIBBIA_GDD.md`, `HANDOVER.md`, `.agents/skills/butano-gba-dev/SKILL.md`, `.claude/skills/butano-gba-dev/SKILL.md`

Le decisioni elencate in fondo a questo documento sono quasi tutte **riconciliazioni di contraddizioni del GDD**. Nessun passo che dipende da una di esse parte prima che la decisione sia scritta nella sezione che oggi la contraddice: 15B stralciata o annotata, 28B corretta a 23A, 21B/21C/15C riconciliate, 8A/31A sulla Patente, 30/31A sull'esperienza, 24/33A sugli slot, 14C annotata come intenzione d'arte e non allocazione hardware.

Correzione da fare comunque, indipendente dalle decisioni: **AGENTS.md §1 dice Magic Header "G1151"** (5 caratteri), `include/save_data.h:20` usa `char magic_header[4]` = `"G115"`, la skill §3 prescrive `{'G','1','1','5'}`. Correggere AGENTS.md a `G115` con nota, altrimenti la prossima sessione "ripara" il codice verso il documento.

Ogni volta che si scrive "annotare nella skill" si intende **nelle due copie**, `.agents/` (canonica) e `.claude/`: la Sessione 07A avverte che vanno tenute allineate a mano.

---

## PASSO 1 — `include/map_id.h`

Un solo `enum class MapId : uint8_t` autoritativo, `MAP_COUNT`, `static_assert`. Nessuna logica. In testa al file, la regola `inline constexpr` per tutte le tabelle in header, che i passi 7, 10, 12, 17 e 20 ereditano.

Motivo invariato: quattro aree scrivono un `map_id` con tre numerazioni incompatibili (`save_data.h:23` ne documenta 4, la Sez. 38 ne elenca 8-9, i trigger della Sez. 21B ne implicano altri).

---

## PASSO 2 — `include/story_flags.h`

`uint8_t[32]` (256 bit), `is_set/set/clear`, e **range riservati per modulo dichiarati in testa**: 0-63 storia/atti, 64-127 quest e dialoghi, 128-159 boss (Sez. 26, altro agente), 160-191 combo (Sez. 12C, altro agente), 192-255 riserva. `static_assert` che l'ultimo flag dichiarato stia nella maschera. È un conflitto di governance, non di codice: tre dossier dimensionano i flag a 32, 128 e 256 bit e due ne rivendicano la proprietà.

---

## PASSO 3 — `include/scene.h` — contratto completo, **nessuna decisione all'utente**

**File:** `include/scene.h`

Il dilemma del piano originale era falso, e su due fronti.

**(a) Il distruttore virtuale non è un problema di zero-heap.** La forma corretta è una base polimorfica con distruttore **non virtuale e protected** — linea guida C.35, applicabile qui perché le scene vivono sullo stack e non sono mai distrutte tramite puntatore alla base:
```cpp
class Scene {
public:
    [[nodiscard]] SceneRequest run();          // NON virtuale: possiede il ciclo
protected:
    ~Scene() = default;                        // non virtuale, protected: nessuno slot D0
    virtual void update() = 0;                 // il polimorfismo è qui
    bool _exit = false;
    SceneRequest _next{};
};
```
Non emette il distruttore deallocante, non referenzia `operator delete`, non trascina newlib. Costo reale misurato: vtable in `.rodata` (oggi 41.032 byte su 32 MB), zero IWRAM, zero EWRAM, zero VRAM — e la regione heap `__eheap_start 0x020083e4 → __eheap_end 0x02040000` è **riservata dal linkscript a prescindere**, che il codice la usi o no. La "DIVERGENZA APERTA" della Sessione 06D si chiude qui **senza deroghe da annotare**.

**(b) La forma `run()` è già la regola scritta.** AGENTS.md §2.3, riga 21: *"Ogni scena deve implementare il ciclo standard `while(!exit_condition) { update(); bn::core::update(); }`"* — il ciclo appartiene alla scena. `BattleSceneManager::run()` esiste già (`include/battle_scene.h:112`, "Ciclo di scena standard imposto da AGENTS.md") e non è mai chiamato da nessuno. L'argomento del piano ("`run()` rende IMPOSSIBILE il punto unico di incremento di `playtime_frames`") è falso: basta che nessuna scena chiami `bn::core::update()` direttamente e che tutte passino da `gubbio::core_update()` (Passo 5), con il gate 0b a renderlo verificabile.

**(c) Dove vivono gli oggetti-scena — il buco che il piano non chiudeva.** Il dispatch è uno `switch` su `SceneId` con la scena come **variabile di scope**:
```cpp
SceneRequest req{SceneId::EXPLORATION, 0, 0};
while(true) {
    switch(req.id) {
        case SceneId::BATTLE:      { BattleScene s(g_game_state, req);      req = s.run(); } break;
        case SceneId::EXPLORATION: { ExplorationScene s(g_game_state, req); req = s.run(); } break;
    }
}
```
Vietati per contratto: puntatori possedenti, `new`, `bn::unique_ptr`, factory che ritornano per puntatore, tabelle di funzioni che costruiscono scene. Al più **una scena viva alla volta**, garantito dallo scope — che è esattamente la sequenza "fade-nero → distruggi → costruisci → fade-in" che il Passo 5 dichiara condizione di correttezza, ottenuta per costruzione invece che per disciplina. La forma alternativa (`update()` nel main) costringerebbe a `bn::optional<BattleScene>` + `bn::optional<ExplorationScene>` a scope di main, con la **somma** delle due dimensioni riservata per sempre.

`static_assert(sizeof(BattleScene) < 4096)` e `static_assert(sizeof(ExplorationScene) < 4096)`, più `BN_LOG(bn::memory::used_stack_iwram())` alla profondità massima. Margine attuale misurato: IWRAM statica occupata 11.104 byte (`.iwram` 8.944 + `.bss` 2.160, quest'ultima a `0x030022f0`), ~21 KB residui per lo stack. Se una scena supera il tetto, i suoi buffer grandi vanno in EWRAM, non la scena intera.

---

## PASSO 4 — `include/game_state.h` + `src/game_state.cpp`

Campi: `HeroRuntimeState party[3]`, `MapId current_map`, `entry_point`, `player_pos_x/y`, `current_act`, `gold`, `tavole_mask`, `story_flags[32]`, `quest_state[32]`, `quest_counter[32]`, `quartieri_reputation[4]`, inventario, `playtime_frames`. Metodi `reset_new_game()` e `clamp_after_load()`. Nessun handle Butano, nessuna `bn::string_view`.

**Collocazione, scritta esplicitamente perché il default della toolchain è l'opposto di quello che il piano dava per scontato.** Nell'ELF attuale `.bss` sta a `0x030022f0`, cioè **IWRAM**; in EWRAM ci sono solo `.ewram` (224 B) e `.sbss` (33.540 B, buffer audio di Butano). Una `GameState g_state;` scritta ingenuamente finisce in IWRAM, cioè nei ~21 KB condivisi con lo stack. La riga esatta, in **un solo `.cpp`**, mai nell'header:
```cpp
BN_DATA_EWRAM_BSS gubbio::GameState g_game_state;   // extern nell'header
```
`BN_DATA_EWRAM_BSS` (`bn_hw_common.h:24`) e non `BN_DATA_EWRAM` (`:12`): la seconda punta alla sezione `.ewram` **inizializzata**, cioè ~220 byte di zeri in ROM più una copia ROM→RAM al boot per nulla.

**Proprietà: una sola istanza, ma passata per riferimento.** Il piano si contraddiceva ("istanza statica" + "prima che una scena ne prenda un riferimento nel costruttore"). Si adotta il modello già in uso nel progetto (`BattleHud::update(const BattleSceneManager&)`): il trampolino passa `g_game_state` per riferimento a ogni costruttore di scena; nessun codice vi accede per nome globale. La singola istanza garantisce la fonte di verità, il passaggio per riferimento evita la scrivibilità globale.

`static_assert(sizeof(GameState) <= 256)` e `static_assert(bn::is_trivially_copyable<GameState>())` (quest'ultima serve comunque al Passo 8).

**L'inventario si deriva da `include/item_data.h`, che esiste già dalla Sessione 07** con `ItemId`, `ITEMS[]`, `max_carry` protetto da `static_assert` (il Baccalà bloccato a 1) e la decisione a verbale che l'inventario è **condiviso e va scalato alla SELEZIONE**. Il piano inventava un secondo `inventory[32]` ignorando tutto questo. `static_assert(int(ItemId::COUNT) <= INVENTORY_SLOTS)` rompe la build se le due rappresentazioni divergono.

---

## PASSO 5 — `scene_fade.h/.cpp` (primitive, senza ciclo) + `game_clock.h`

**File:** `include/scene_fade.h`, `src/scene_fade.cpp`, `include/game_clock.h`

Il piano chiamava questo passo "estrazione". Non lo è: la dissolvenza d'ingresso è **guidata dalla FSM già verificata su emulatore** — stato `INTRO_FADE_IN`, 32 frame, con `CampanoneAudio::play_siege_double()` al frame 0 (`src/battle_scene.cpp:162`, decisione della Sessione 06B "dando al rintocco del Campanone il tempo di risuonare") e letta dall'HUD via `battle.intro_progress()` (`src/battle_hud.cpp:154`). Un `fade_in(frames)` che possieda il proprio ciclo creerebbe due dissolvenze sovrapposte, o imporrebbe di smontare la FSM.

Forma adottata: `scene_fade` espone **solo primitive senza ciclo** — `apply(intensity)`, `reset()`. Ogni scena continua a guidare l'avanzamento dal proprio contatore (la battaglia da `_intro_frames`, l'esplorazione dal suo). `reset()` è **obbligatoria all'uscita da ogni scena**: `bn::sprite_palettes::set_fade` è globale e va azzerata prima che il flash per-palette del Passo 21 parta, altrimenti i due effetti si sommano.

**Regola scritta ora, non fra sei passi:** tutte le transizioni sono dissolvenze su palette. Qualunque effetto affine — Boost MAX "a schermo intero" (Sez. 20A/28B), **Battle Swirl d'ingresso (Sez. 35C)**, Cinematica 2 (Sez. 34B) — è una **scena a sé** con teardown completo dei BG regolari, mai un sotto-stato. In Mode 1 restano 2 BG regolari + 1 affine: si perdono due layer proprio nell'istante in cui le risorse di due scene rischiano di coesistere. Annotare nelle due copie della skill.

`game_clock.h` contiene l'**unico** wrapper del progetto:
```cpp
inline void gubbio::core_update() { bn::core::update(); ++g_game_state.playtime_frames; }
```
Criterio di accettazione: una sola occorrenza di `bn::core::update()` in tutto `src/` e `include/` (oggi ce n'è una, `src/main.cpp:132`), verificata dal gate 0b.

---

## PASSO 6 — Facade `BattleScene` + trampolino di scene

**File:** `include/scene_battle.h`, `src/scene_battle.cpp`, `include/battle_scene.h`, `src/battle_scene.cpp`, `src/main.cpp`

`BattleScene` possiede `BattleSceneManager` + `BattleHud` come **membri per valore** ed è una variabile di scope nel `switch` del trampolino. Aggiungere a `battle_scene.h` l'**OVERLOAD** `init_battle(int encounter_id, const GameState&)` e `export_party_state(GameState&) const` (solo `current_hp` e `current_fervor`: barriera, BREAK, ustione e guardia non escono dalla scena). **Mantenere** `init_battle(encounter_id, party_level)`: sostituirlo romperebbe `src/main.cpp:86`, l'unico collaudo a runtime della FSM.

Motivo di farlo ora invariato e confermato: oggi `main` costruisce `BattleHud` e lo tiene vivo per sempre, quindi la sua VRAM non sarebbe mai liberata da una transizione.

**Criterio di successo riscritto — quello originale non poteva fallire.** `tests/test_battle_engine.py` è un port fedele in Python delle **formule** (HANDOVER, Sessione 02): non compila, non linka, non esegue una riga di `battle_scene.cpp` o del nuovo facade. Passerebbe 31/31 anche se il facade non costruisse mai l'HUD, se il round-trip perdesse HP e Fervore, o se `export_party_state` scrivesse nello slot sbagliato. I 31 test restano come **regressione delle formule**, dichiarandolo. I criteri veri:
- traccia `BN_LOG` del round-trip con HP e Fervore **prima e dopo** la battaglia, confrontata da script;
- `bn::sprites::used_items_count()`, `bn::sprite_tiles::used_items_count()`, `bn::sprite_tiles::available_tiles_count()` e `bn::memory::used_stack_iwram()` loggati al picco;
- `arm-none-eabi-size -A gubbio1151.elf`: `.bss` non cresce;
- gate 0b verde;
- autotest ricalibrato che riproduce la sequenza di azioni attesa.

Se e quando il carry-over viene approvato, aggiornare **contestualmente** `tests/test_battle_engine.py:295` (mirror di `HERO_START_FERVOR_PERCENT`) e `:503` (`test_battle_start_fervor_follows_hud_mockup`), più la nota della Sessione 02c: altrimenti restano un test verde su una regola morta.

---

## PASSO 7 — `include/save_crc32.h`

CRC32 riflesso `0xEDB88320`, tabella a nibble `inline constexpr uint32_t[16]` (64 byte di ROM), interamente `constexpr`, con `static_assert(crc32("123456789") == 0xCBF43926)`. Indipendente da tutto, verificabile a compile time senza emulatore.

---

## PASSO 8 — Formato di salvataggio: **involucro congelato, payload riservato**

**File:** `include/save_data.h`, `src/save_system.cpp`, `tests/test_save_system.py`

Il piano si contraddiceva: dichiarava "il record è congelabile una volta sola, i fabbisogni di dialoghi/quest e degli oggetti Sez. 8E vanno raccolti PRIMA", poi metteva il salvataggio in posizione 8 e le quest in posizione 16. Risoluzione: al Passo 8 si congela **solo l'involucro** — magic `0x35313147`, `version`, `write_counter` monotono, `playtime_seconds`, ping-pong fra due banche, rilettura di verifica, `slot_status`, nessun auto-format su lettura fallita, `checksum` ultimo campo. Il **payload** è un blocco opaco a dimensione fissa sovradimensionata, riempito campo per campo al Passo 17, quando dialoghi, quest e oggetti hanno consegnato. Un solo bump di versione, come voleva il piano, ottenuto ordinando i passi invece che sperando.

**Il divieto di memcpy è rimosso.** Era autocontraddittorio: (a) l'unica API disponibile è `bn::sram::write_offset<Type>`, che *è* un memcpy e pretende `is_trivially_copyable`; (b) lo stesso passo chiede un checksum su `sizeof(SaveData) - 4` byte contigui, che con la serializzazione campo per campo non esistono e vanno ricostruiti in un buffer — due buffer con la rilettura di verifica, ~500 byte sullo stack IWRAM, cioè proprio la risorsa da preservare; (c) gli `static_assert` su `sizeof` e su **tutti** gli `offsetof`, che il passo già richiede, sono esattamente ciò che rende il memcpy sicuro fra ricompilazioni. Contratto sostitutivo: `SaveData` POD standard-layout, `static_assert(bn::is_trivially_copyable<SaveData>())`, `static_assert(sizeof(SaveData) == N)`, `offsetof` verificati campo per campo, campi ordinati per allineamento decrescente con `static_assert` che la somma delle dimensioni sia uguale a `sizeof` (zero padding), una sola `write_offset`, un solo buffer di rilettura.

Aggiungere `static_assert` byte-wise sul magic: che i 4 byte scritti siano `'G','1','1','5'` nell'ordine atteso su questa piattaforma. Un `uint32_t 0x35313147` non è verificabile a occhio in un hex dump del `.sav`, un array di char sì.

**Criteri di accettazione hardware:** dopo un salvataggio reale, `gubbio1151.sav` prodotto da mGBA non nullo (oggi è 0 byte) e con magic corretto in hex dump; presenza della stringa di tipo salvataggio in ROM.

---

## PASSO 9 — Budget VRAM, palette e OAM scritto come tabella (nuovo, prima dell'arte)

**File:** `include/map_data.h` (sezione budget con `static_assert`), `HANDOVER.md`

Il piano metteva a budget OAM e palette con cura e **non contava un solo blocco BG né un solo tile OBJ**, cioè le due risorse che overworld e animazioni consumano davvero.

**Blocchi BG: 32 blocchi da 2 KB (64 KB), condivisi fra tileset e mappe.** Un tileset è collocabile solo se sta interamente dentro un charblock da 16 KB o inizia a multiplo di 8 blocchi. Tetto duro per singolo tileset: **1024 tile a 4bpp** (`bn_regular_bg_tiles_item.h:57`). Una ground 512x512 ha 4096 celle: serve ≥75% di riuso tile, requisito che il generatore deve **imporre**, non sperare.
Conto con padding: mappe ground 64x64 = 4 blocchi, foreground 64x64 = 4, cielo 32x32 = 1, BG0 32x32 = 1 → 10 blocchi. Restano 22 blocchi = 1408 tile per quattro tileset. Soglie proposte con `static_assert`: ground ≤ 512 tile, foreground ≤ 256, cielo ≤ 128, BG0 ≤ 128 → 1024 tile = 16 blocchi; totale 26/32, 6 di margine.
`BN_CFG_BG_BLOCKS_MAX_ITEMS` è **16 di default** (`bn_config_bg_blocks.h:26`) e conta insieme tileset e mappe: l'overworld ne usa 8; se una transizione non pulita lascia vivi `battle_bg` e i suoi blocchi si arriva a 10-11. Si manifesta come assert, non come degrado grafico.

**BG0 va allocato una volta all'ingresso della scena, non "a richiesta".** Tre BG residenti più uno intermittente è il caso in cui l'allocatore best-fit fallisce per frammentazione anche con blocchi liberi a sufficienza. Per qualunque risorsa condizionale, usare le varianti `create_optional` e gestire il fallimento invece di lasciare un assert davanti al giocatore.

**Palette: il modello del piano non è quello del GBA.** Un `regular_bg_item` a 4bpp importa **UNA** palette da 16 colori per l'intero background — verificabile su `build/bn_regular_bg_items_battle_bg.h`: "256x256@4, + palette 16 entries, + 127 tiles". Quattro BG regolari consumano **4 palette su 16, non 16 su 16**. La Sez. 14C ("4 palette ai terreni, 4 alla vegetazione, 4 al cielo, 4 all'HUD") non è implementabile a 4bpp: o `bpp_4_auto` (quantizzazione multi-banco) o 8bpp (tutte e 16). La raccomandazione del piano ("progettare il ground a 2-3 palette invece di 4") era priva di significato operativo, e la premessa "senza uno slot per l'alpha blending della Sez. 28A" è errata: l'alpha blending è BLDCNT/BLDALPHA e non consuma palette. Il vincolo vero del flash bianco per-palette: **ogni sprite item 4bpp porta la propria palette**, quindi i personaggi lampeggiabili sono tanti quanti gli sprite item distinti a schermo — oggi 7 (3 eroi + 4 nemici), ampiamente sotto 16, **a meno che uno non diventi 8bpp** per il difetto del Passo 11.

**Sprite: tre tetti separati, non uno.** 128 slot OAM hardware, `BN_CFG_SPRITES_MAX_ITEMS` 128 (`bn_config_sprites.h:29`), e soprattutto `BN_CFG_SPRITE_TILES_MAX_ITEMS` 128 (`bn_config_sprite_tiles.h:27`), allocazioni **distinte** di tile OBJ — ogni sprite di `bn::sprite_text_generator` è un'allocazione a sé. Scenario peggiore: ~40 testi in battaglia (`MAX_TEXT_SPRITES` in `battle_hud.h`) + ~21 di dialogo + 9 unità + 6 barre + 9 gettoni timeline + cursore ≈ 87/128. Sotto, ma con metà del margine implicito nel piano.
**32 KB / 1024 tile di VRAM OBJ, mai messi a budget dal piano:** 6 frame × 512 B (32x32 4bpp) × 9 unità ≈ 27 KB, cioè quasi tutto, prima dei testi. Decisioni conseguenti, ai Passi 13 e 21.
**Particelle Sez. 35B:** 32 faville da 2x2 px costano 32 slot OAM per 128 px² utili (lo sprite minimo è 8x8, spreco del 94%). Raggrupparle in 2-4 sprite 32x32 con i frame precalcolati dallo stesso generatore d'arte recupera ~28 slot: da sola questa mossa risolve lo sforamento 131/128 **senza sacrificare né i numeri di danno né i dialoghi in battaglia**, che il piano dichiarava inconciliabili. Nascondere il menu comandi durante la fase di animazione libera altri ~16 slot.
Nota di calibrazione a favore del piano: il limite di cicli OBJ per scanline **non** è vincolante — Butano non imposta `DCNT_OBJ_HBL`, quindi il budget è ~1210 cicli/riga e lo scenario peggiore sta sotto ~600. Il vincolo vero resta il conteggio, come dice il piano.

**A verbale per dopo:** `BN_CFG_HBES_MAX_ITEMS` è 6 (`bn_config_hbes.h:29`) e ogni `regular_bg_position_hbe_ptr` richiede 160 `bn::fixed` = 640 byte vivi per tutta la durata dell'effetto, da mettere in EWRAM. Riguarda la Sez. 35A (acqua del Camignano, distorsione delle fiamme), fuori dallo scope immediato.

---

## PASSO 10 — Collisione: estendere, e **parametrizzare l'exporter che esiste già**

**File:** `include/piazza_grande_collision.h`, `tools/map_exporter.py`

Estendere senza riscrivere: `enum class TileType`, `is_solid()`, `is_transition()`, `get_tile_type_px(px, py)` con `>> 3`, `PIAZZA_WIDTH_PX/HEIGHT_PX`. La funzione `get_tile_type(int x, int y)` è già `inline constexpr` (`piazza_grande_collision.h:20`) e resta la fonte.

Il difetto della Sez. 21D va chiuso, non aggirato: il GDD stampa `get_tile_type(const uint8_t* grid, int pixel_x, int pixel_y)` — puntatore e **pixel** — mentre il codice implementa `get_tile_type(int x, int y)` in **tile**. Omettendo il puntatore le due firme hanno lo stesso numero di argomenti: un chiamante che segue il GDD sbaglia di un fattore 8 senza errore di compilazione. La funzione `_px` esplicita è la chiusura.

Array a runtime, nella forma che non duplica:
```cpp
struct CollisionGrid { uint8_t data[PIAZZA_WIDTH * PIAZZA_HEIGHT]; };
consteval CollisionGrid make_piazza_grid();
inline constexpr CollisionGrid PIAZZA_GRID = make_piazza_grid();
static_assert(PIAZZA_GRID.data[32 + 18 * PIAZZA_WIDTH] == 3);   // portone Consoli
static_assert(PIAZZA_GRID.data[0  + 39 * PIAZZA_WIDTH] == 2);   // ringhiera sud
```
2560 byte di ROM **una volta sola**, non per unità di traduzione, e la derivazione dalla funzione verificata a compile time invece che asserita in un piano.

**`tools/map_exporter.py` esiste già** ed è censito in HANDOVER come "parser Python da Tiled JSON a header `constexpr uint8_t`". Il piano non lo nominava mai. Va parametrizzato **ora**, perché ha tre difetti che `MAPS[]` rende bloccanti: emette nomi fissi `MAP_WIDTH`, `MAP_HEIGHT`, `COLLISION_MAP` nello stesso namespace (righe 40-42), quindi due mappe esportate non possono coesistere in una TU; il terzo argomento `variable_name` è documentato ma mai passato (righe 56-57); non emette `inline`.

**Respingo però il rovesciamento chiesto dal critico** ("fare di map_exporter la fonte unica, autorando Piazza Grande in Tiled a partire dalla griglia implicita"): richiede un artefatto Tiled che non esiste, uno script di dump aggiuntivo, e un round-trip che nessuno può verificare oggi, per sostituire una griglia che è già in repo, già `constexpr`, già leggibile. Regola scritta invece in HANDOVER: **Piazza Grande resta autorata in codice** (è la mappa zero, e la sua griglia è il riferimento con cui il generatore d'arte è tenuto coerente); **le mappe 2..9 della Sez. 38 passano da Tiled via `map_exporter.py`**. `MapDescriptor` accetta entrambe le origini perché in entrambi i casi vede un `const uint8_t*`.

---

## PASSO 11 — `tools/make_piazza_art.py` e gli asset della piazza

**File:** `tools/make_piazza_art.py`, `tools/preview_piazza.py`, `graphics/piazza_ground.{bmp,json}`, `graphics/piazza_fg.{bmp,json}`, `graphics/piazza_sky.{bmp,json}`, `graphics/overworld_ubaldo.{bmp,json}`

Motivo di farlo prima del C++ invariato e confermato dal precedente: Butano genera `bn_regular_bg_items_*.h` e `bn_sprite_items_*.h` **solo** dagli asset presenti in `graphics/`, ed è l'inciampo di `bn_sound_items.h` della Sessione 02c.

**Tre correzioni obbligatorie che il piano non aveva.**

**(1) `bpp_mode` esplicito in ogni `.json`, BG e sprite.** Il piano elencava come "misure hardware valide obbligatorie" solo i pixel: il conteggio colori non compariva mai. Senza il campo, `butano_graphics_tool.py` promuove **silenziosamente** a 8bpp qualunque BMP indicizzato oltre i 16 colori (`RegularBgItem`, ramo `except KeyError` → `if self.__colors_count > 16: self.__bpp_8 = True`; per gli sprite, `parse_sprite_bpp_mode` riga 50 `return colors_count > 16`). Conseguenze: tile da 32 a 64 byte (VRAM raddoppiata) e, per un BG, uso della palette a 256 colori, cioè **tutti e 16 i banchi** — ground+foreground+cielo+BG0 diventa aritmeticamente impossibile. Per uno sprite overworld a 17 colori significa occupare l'intera palette OBJ e **annullare il flash bianco per-palette** del Passo 21. `graphics/battle_bg.bmp` è uscito 4bpp/127 tile solo perché il segnaposto è piatto: caso fortunato, non garanzia — e infatti **nessuna delle `.json` esistenti dichiara `bpp_mode`**. Se la piazza richiede più colore, `"bpp_mode": "bpp_4_auto"` (quantizzazione multi-banco, supportata) dichiarando quante palette consuma.

**(2) Campo `height` nelle `.json` degli sprite.** Fogli `16x512` / `32x512` senza `height` vengono letti come **un unico sprite 16x512**, misura OBJ inesistente → `Invalid sprite height`. Verificato nel progetto: `ubaldo.json`, `giorgio.json`, `antonio.json`, `enemy_*.json` sono `{"type":"sprite"}` nudo perché a frame singolo, mentre `hud_bar.json` (32x272) e `timeline_icons.json` (16x96) hanno correttamente `"height": 8` e `"height": 16`. I generatori emettono `{"type":"sprite","bpp_mode":"bpp_4","height":32}` **contestualmente al `.bmp`**, mai a mano. Lo stesso vale al Passo 20, che porta `ubaldo` a 16x672 e `corrado` a 64x1216: quelle `.json` oggi non hanno `height` e diventerebbero illegali all'istante.

**(3) Le misure interne del piano non tornavano.** La mappa è 64x40 tile = **512x320 px**, e lo conferma il clamp di camera y[80,240] del Passo 14. Il piano prescriveva `foreground 512x256`: un BG regolare 512x256 ha wrap hardware a 256, quindi le righe 256-319 — proprio la fascia sud della ringhiera panoramica (`piazza_grande_collision.h:24`, `y >= 38`) — mostrerebbero di nuovo la cima del foreground. Le uniche misure legali sono multipli di 256 (`butano_graphics_tool.py`, `RegularBgItem`, righe 616-617 e 631-632), quindi **512x320 non esiste in nessuna forma**. Le due sole vie sono foreground a 512x512, oppure foreground dichiarato come fascia alta con nulla di occludente sotto y=256 px — decisione d'arte, perché vincola dove possono stare i palazzi (vedi decisioni in fondo).

Il generatore deve inoltre **stampare e far fallire**: conteggio tile unici per tileset contro le soglie del Passo 9, conteggio colori contro `bpp_mode`, e derivare il layout dei muri dalla stessa `get_tile_type` del Passo 10.

---

## PASSO 12 — `include/map_data.h`

`struct MapDescriptor { const uint8_t* collision; int width_tiles, height_tiles; const bn::regular_bg_item* ground/foreground/parallax; bool foreground_covers_full_height; SpawnPoint spawns[N]; TriggerRule triggers[N]; }` e `inline constexpr MapDescriptor MAPS[]` in ROM, con la sola riga di Piazza Grande popolata. I trigger mappano il valore di tile (3/4/5/6) su una `SceneRequest`; gli spawn point risolvono il rientro per porta — senza tabella di spawn, il rientro dal Bargello riposiziona il player sul trigger 4 e la transizione si ripete all'infinito.

Qui vive anche il budget blocchi del Passo 9 come `static_assert` sulla somma dei tile dei quattro tileset.

**`big` è una scelta reale, non preclusa: il conflitto n.13 del piano era una grep sbagliata e va corretto agli atti.** Il piano cercava la stringa `big_map`, che nel Butano attuale appartiene alla sola API affine. L'API dei BG regolari si chiama `big` ed è completa: `bn::regular_bg_item::big()` a `bn_regular_bg_item.h:116`; `_big_dimensions` (>64 tile) a `bn_regular_bg_map_item.h:491`; campo json `"big"` con validazione a `butano_graphics_tool.py:637`; streaming a runtime con `big_map` / `commit_big_map` / `full_commit_big_map` e `check_commit_big_map()` in `bn_bgs_manager.cpp` (righe 76-78, 205, 324, 349-353, 376). **Un critico ha "confermato" la grep del piano: la conferma è sbagliata e va respinta**, altrimenti fra due sessioni qualcuno riproporrà `big` e verrà respinto citando una prova negativa mal condotta.
Numeri per decidere, non slogan: `big` **non** consente 512x320 (le dimensioni restano multipli di 256, quindi il padding a 512 di altezza serve comunque); quello che compra è la mappa in **1 blocco** invece di 4, al prezzo del commit celle a ogni scroll oltre il canvas. Concretamente attraente proprio per il foreground, che è per lo più vuoto e paga i suoi 4 blocchi in celle e non in tile. Scelta da mettere a verbale in HANDOVER con il conto, dopo che il Passo 11 ha misurato i tile veri.

---

## PASSO 13 — `OverworldPlayer`

**File:** `include/overworld_player.h`, `src/overworld_player.cpp`

Confermato dal piano: hitbox 12x8 ai piedi (non il bounding box 16x16 della Sez. 21D, con cui il portone dei Consoli è **letteralmente irraggiungibile**: per posare il centro su y=18 il bordo superiore ricade su y=17, che `piazza_grande_collision.h:27-30` restituisce come muro); movimento ad **assi separati** (`try_move_x` poi `try_move_y`), perché il test del solo punto d'arrivo diagonale blocca il movimento appena uno dei due assi tocca un muro; `box_free()` che campiona l'**intervallo** di tile coperto (max 3x2 celle) e non i quattro angoli.

**Due correzioni.**

**Posizione logica in `int` pixel, non in `bn::fixed_point`.** La velocità proposta è intera (1 px/frame, 2 in corsa), la collisione lavora in tile e i trigger sul punto centrale dei piedi: nessun consumatore chiede il sub-pixel, e il `bn::fixed` porta due trappole — i costruttori impliciti da `float`/`double` (chiusi dai flag del Passo 0c) e l'ambiguità del `>> 3`, che su un `bn::fixed` opera sul valore grezzo a 12 bit di frazione, cioè un errore di fattore 4096. Precisare nel Passo 10 che `>> 3` si applica a un `int`; da un `bn::fixed` si passa per `.floor_integer()` e mai per `.integer()`, che tronca verso zero e sbaglia in negativo. `bn::fixed` resta riservato alla camera, se e quando servirà lo smorzamento.

**Animazione con `bn::sprite_cached_animate_action`, e niente ricostruzione al cambio di direzione.** La versione non-cached rilascia e ricrea un `sprite_tiles_ptr` a ogni fotogramma e a ogni cambio di direzione: in movimento diagonale il cambio è continuo, e ogni ciclo release/create è un'operazione sull'allocatore best-fit, cioè frammentazione progressiva. La cached costa 16 frame × 16x16 4bpp (128 B) = **2 KB** su 32 KB di VRAM OBJ, trascurabile, e rende la ricostruzione inutile.

---

## PASSO 14 — `ExplorationScene`

**File:** `include/scene_exploration.h`, `src/scene_exploration.cpp`, `src/main.cpp`

Una classe parametrizzata da `MapId`, non N classi-mappa: con le 8-9 aree della Sez. 38 e gli NPC censiti su 5 di esse, la duplicazione di classe è insostenibile. Il file `scene_piazza_grande.h` proposto dall'overworld è assorbito qui e in `map_data.h`.

Tre background (ground priority 2, foreground priority 1, cielo priority 3 mosso a camera/4 con wrap hardware), BG0 **allocato all'ingresso** (Passo 9), camera clampata a x[120,392] y[80,240] agganciata a ground/foreground/sprite ma non al cielo, trigger valutati sul solo punto centrale dei piedi con debounce (`_last_trigger_tile` preimpostato al tile di spawn). Trigger 3/4/5 senza destinazione: fade-to-black e rientro sullo spawn point corrispondente — non è un ripiego, è l'unico modo di collaudare a runtime il ciclo uscita/rientro, dove si annida il bug del loop di transizione.

Convergenza sui 4 BG, che il GDD non risolve (la Sez. 14A assegna a BG0 finestra dialoghi + barre + menu comandi senza precedenza; la Sez. 33B mette il menu di pausa a schermo pieno su BG0+BG1, già occupati): **il menu di pausa è un sotto-stato della scena ospite, mai una scena a sé, e mai un quinto layer.**

Criteri di successo: round-trip esplorazione → battaglia → esplorazione con HP e Fervore che sopravvivono; zero assert dell'allocatore; log di `bn::sprite_tiles::used_tiles_count()` / `available_tiles_count()`, `bn::sprites::used_items_count()`, `bn::memory::used_stack_iwram()` al picco; `arm-none-eabi-size -A` con `.bss` invariata; sequenza "fade-nero → distruggi → costruisci → fade-in" rispettata, che è ciò che garantisce che i due insiemi di `bg_blocks` non coesistano mai (tetto 16 item).

---

## PASSO 15 — Font

**File:** `graphics/font_gubbio.{bmp,json}`, `include/font_gubbio.h`, `Makefile`, `tools/preview_battle_screen.py`

Rischio confermato e verificato: `common_variable_8x8_sprite_font_utf8_characters` (`common_variable_8x8_sprite_font.h:16-18`) mappa 16 caratteri non-ASCII, **tutti spagnoli** — `Á É Í Ó Ú Ü Ñ á é í ó ú ü ñ ¡ ¿` — e **nessun accento grave italiano**. Nel solo GDD compaiono 98 `à`, 28 `è`, 13 `ù`, 10 `ò`. Un carattere non mappato produce `BN_ERROR` a runtime, non un errore di build. Va chiuso **prima** di scrivere una riga di copione.

Tre aggiunte rispetto al piano:
1. **Cella dello spazio dichiarata e testata.** La tabella delle larghezze del font common parte dal carattere 32 (spazio, 6 px): il font custom deve conservare la stessa origine, e il generatore deve emettere la cella o dichiararla esplicitamente saltata. È il difetto della Sessione 05 ("senza lo scarto di uno ogni lettera scivolava e Sant'Ubaldo usciva Tbou..."): si ripresenterebbe identico.
2. **Rimuovere `../butano/common/{src,include,graphics}` dal `Makefile`** quando nessuno usa più `common::variable_8x8_sprite_font`. HANDOVER (Sessione 02d) lo marca "da rimuovere quando l'HUD avrà asset propri": questo è il passo.
3. **`tools/preview_battle_screen.py` legge lo stesso `font_gubbio.bmp` e la stessa tabella di larghezze del C++.** Altrimenti l'anteprima renderizza con un font diverso dalla ROM, aggravando la divergenza già dichiarata nella Sessione 05. È la stessa contromisura che il piano adotta al Passo 20 per le tabelle di animazione, qui semplicemente non applicata.

Se si sceglie il font custom, va adottato anche in `battle_hud.cpp`.

---

## PASSO 16 — `dialogue_box.h` corretto + `dialogue_view`

**File:** `include/dialogue_box.h`, `include/dialogue_view.h`, `src/dialogue_view.cpp`

`dialogue_box.h` esiste dalla Sessione 01 ma **non è mai stato compilato né eseguito** (il main lo usava solo nella demo poi rimossa): non va dato per funzionante. Tre difetti nello stesso file, tutti chiusi qui.

1. **UTF-8 per byte invece che per codepoint.** `_visible_chars` avanza di 1 e si confronta con `_current_text.size()`, che è in byte (`dialogue_box.h:42, 46, 54`). Il primo `substr(0,n)` che taglia a metà una sequenza a 2 byte fa scattare `BN_BASIC_ASSERT` in `bn_utf8_character.h`. Latente solo perché nulla disegna ancora il testo.
2. **`_current_text` è una `bn::string_view` (riga 21): non possiede la memoria.** Finché le battute sono letterali in ROM va bene; la prima battuta interpolata — nome del quartiere, "3 blocchi di ferro" di Q-SM01, nome dell'oggetto di `GIVE_ITEM` al Passo 18 — vivrebbe in una locale del chiamante e la view resterebbe appesa a stack riutilizzato: testo corrotto o assert in un punto non riproducibile. Contratto scritto in testa al file: **`show_message` accetta solo view su memoria a durata statica**; per l'interpolazione, un buffer `bn::string<64>` **membro** di `DialogueManager` con `show_composed()` che vi copia dentro e punta la view al proprio buffer. 64 byte decisi ora contro un bug non riproducibile fra dieci sessioni.
3. Normalizzare i confronti signed/unsigned con `int(_current_text.size())`.

`dialogue_view`: cornice su BG0, testo con `bn::sprite_text_generator` in `bn::vector<bn::sprite_ptr, 24>`, rigenerando **solo la riga in corso** (~7 sprite) e non tutte e tre (~21) — e, dentro la riga, solo quando il conteggio di caratteri visibili attraversa il confine di uno sprite (4 caratteri a 32 px), che riduce il churn dell'allocatore di 4x rispetto a rigenerare ogni 2 frame di typewriter (~200 create/release al secondo).

---

## PASSO 17 — Copione, tabelle, e riempimento del payload di salvataggio

**File:** `include/dialogue_text.h`, `include/dialogue_data.h`, `include/npc_registry.h`, `include/quest_data.h`, `tools/dialogue_exporter.py`, `tests/test_dialogue_quest.py`, `include/save_data.h`

`dialogue_text.h` (sole stringhe), `dialogue_data.h` (`DialogueLine` con `bn::string_view row[3]` già spezzate, `ScriptStep` a 4 byte, `ChoiceOption` piatte), `npc_registry.h` (`NpcDef` con coordinate in tile + `DialogueEntry` a regola prima-corrispondenza-vince), `quest_data.h` (le 5 quest della Sez. 31A). Tutte `inline constexpr`.

Il codice della Sez. 31C del GDD **non è trascrivibile**: usa `bn::vector<DialogueNode,4>` dentro un array `constexpr`, e `bn::vector` non è un tipo letterale in Butano. Va appiattito in tabelle e indici, non copiato.

`tools/dialogue_exporter.py` fa il word-wrap **in pixel** sulle larghezze reali del font del Passo 15 e fallisce la build sui caratteri non mappati.

**Qui, e non al Passo 8, si riempie il payload di `SaveData`**: `story_flags[32]`, `quest_state[32]`, `quest_counter[32]` (un bit non sa contare fino a 3: Q-SM01 vuole 3 blocchi di ferro, Q-SA01 4 radici), `gold`, `tavole_mask`, inventario derivato da `item_data.h`. Le 5 ricompense quest sono `ItemId` della Sez. 8E, di competenza di un altro agente: il coordinamento è su quell'enum, non sul formato.

---

## PASSO 18 — `dialogue_runner.h` agganciato a `ExplorationScene`

**File:** `include/dialogue_runner.h`, `src/scene_exploration.cpp`

Esecutore di script: LINE, CHOICE, SET_FLAG, JUMP_IF_FLAG, START_QUEST, ADVANCE_QUEST, GIVE_ITEM, END; solo due `uint16_t` di stato. NPC come `bn::vector<OverworldNpc, 8>`, interazione su tasto A. Il valore di tile 6 è promosso da "Fontana dei Matti" a **interazione generica**, con la coordinata che seleziona lo script: è ciò che rende la legenda della Sez. 21B riusabile su tutte le aree della Sez. 38 senza inventare un valore di tile per ogni NPC.

**Conflitto di input da mettere a verbale ora.** A e B sono assegnati tre volte: fast-forward delle animazioni (Passo 21), skip del typewriter / chiusura del box (`dialogue_box.h:41, 54`), corsa e interazione nell'overworld. Finché le modalità sono mutuamente esclusive nel tempo non c'è danno; un **dialogo durante la battaglia** (previsto per boss e mosse supreme) fa collidere fast-forward e skip sullo stesso tasto nello stesso istante. Regola: durante un dialogo in battaglia il fast-forward è sospeso, e il box lo dichiara con il proprio prompt.

---

## PASSO 19 — Fogli di animazione di battaglia (cantiere parallelo, serializzato su `battle_scene.cpp`)

**File:** `tools/make_placeholder_art.py`, `include/battle_anim_table.h`, `tools/preview_battle_screen.py`, `graphics/*.json`

Da `make_X()` monolitico a `draw_X(px, pose)` guidato da tabelle di keyframe interi, con le pose come strisce verticali negli stessi `.bmp` (ubaldo 16x672, giorgio 32x608, antonio 16x672, nemici 32x448, corrado 64x1216) e `include/battle_anim_table.h` **generato dalla stessa tabella Python**. È la contromisura al problema già dichiarato nella Sessione 05 (costanti di `preview_battle_screen.py` duplicate a mano rispetto a `battle_hud.cpp`). Compatibilità garantita: `create_sprite(x,y)` usa l'indice 0, che resta IDLE frame 0.

**Aggiornare contestualmente le `.json`** con `bpp_mode` e `height` (32, o 64 per corrado): oggi sono `{"type":"sprite"}` nudo e diventerebbero misure illegali all'istante.

---

## PASSO 20 — `battle_events.h`

**File:** `include/battle_events.h`, `include/battle_scene.h`, `src/battle_scene.cpp`, `tests/test_battle_engine.py`

Log POD riempito dagli 8 punti di emissione già individuati, più lo stato FSM `PLAY_ROUND_ANIMATIONS` fra EXECUTE e CHECK come puro temporizzatore. Spostare `CampanoneAudio::play_strike()` da `_apply_hit()` alla riproduzione dell'evento: senza, tutti gli SFX del round suonano nel frame in cui il round viene risolto, fino a un secondo prima dell'animazione che dovrebbero accompagnare.

**Politica di saturazione obbligatoria.** `bn::ivector::push_back` su contenitore pieno non tronca: fa scattare `BN_ASSERT`. Il caso peggiore non è remoto — 9 attori, il Boost livello 2 è un doppio colpo reale (2 eventi per attore), più scudo/BREAK, barriera assorbita, guardia del Bastione, e i tick di fine round su ogni nemico in ustione. Un `bn::vector<BattleEvent, 64>` scelto a occhio è un crash in una battaglia avanzata, che l'autotest a 4 round non vedrebbe mai. Quindi: (a) tutto l'inserimento passa da `void _emit(const BattleEvent&)` che **scarta** a contenitore pieno e alza `_event_log_overflow` loggato con `BN_LOG` — l'evento perso degrada l'animazione, non uccide la partita; (b) il tetto è **derivato**, `static_assert(MAX_EVENTS >= (PARTY_SIZE + MAX_ENEMIES_PER_ENCOUNTER) * EVENTS_PER_ACTOR_WORST_CASE + END_OF_ROUND_EVENTS)`; (c) `tests/test_battle_engine.py` guadagna un caso che forza il round peggiore (tutti i boost al massimo, tutti i nemici in ustione) e verifica che il conteggio resti sotto la capacità. È la stessa disciplina che il piano applica giustamente ai bit di storia.

**Serializzazione imposta su `src/battle_scene.cpp`, il file più conteso del progetto** — quattro cantieri lo toccano: overload `init_battle` + `export_party_state` (Passo 6), facade (Passo 6), log eventi + nuovo stato FSM + spostamento audio (questo passo), e la ristrutturazione di `_execute_all_queued_actions()` di RevisoreMotore (altro agente). **Nessuno dei quattro può essere concorrente agli altri**: i punti di emissione si spostano sotto i piedi. Questo passo va dopo il 6 e dopo la consegna di RevisoreMotore.

---

## PASSO 21 — `battle_animator.h` e le due cadenze dell'HUD

**File:** `include/battle_animator.h`, `include/battle_hud.h`, `src/battle_hud.cpp`

Wrapper di `bn::sprite_animate_action<6>`, flash bianco per-palette, lunge, shake. `BattleHud::update()` spezzato in `_tick_animations()` ogni frame e `_refresh()` solo al cambio di `_signature()`. Le barre HP alimentate da `hp_after` dell'ultimo evento riprodotto, non dallo stato già risolto nel modello.

**Vincolo VRAM OBJ, che decide la forma dell'animatore.** Cached per 9 attori sarebbe 6 frame × 512 B × 9 ≈ 27 KB su 32 KB, prima dei ~40 sprite di testo e delle particelle; non-cached sarebbe 9 flussi simultanei di release/create sull'allocatore best-fit. Nessuna delle due sta in piedi. Regola adottata: **un solo attore animato per volta**, che è già ciò che impone la FSM a turni con lo stato `PLAY_ROUND_ANIMATIONS` — un unico animate action cached da 6 frame, costruito all'inizio dell'evento e distrutto alla fine, tetto ~3 KB.

**Invariante di `_signature()` scritto per iscritto, perché è già stato un bug ad alta gravità.** La Sessione 07D ha trovato che *"la firma dell'HUD ignorava `is_enemy` ... il cursore bersaglio restava nascosto — al primo scontro del gioco"*. Cambiare cadenza e sorgente dei dati senza fissare cosa la firma deve contenere rimette in gioco esattamente quel difetto in un componente oggi verificato. La firma deve includere almeno: stato FSM, indice dell'eroe attivo, comando selezionato, indice di abilità, livello di boost, **`is_enemy` e slot del bersaglio**, HP/Fervore/scudo/BREAK di tutte le unità. Estrarla in una funzione documentata con l'elenco dei campi e un rimando alla Sessione 07D.

**Ordine di reset delle palette:** prima riga di `_tick_animations()`, azzerare `bn::sprite_palettes::set_fade` globale (Passo 5) prima che parta il primo flash per-palette. I due meccanismi restano separati per costruzione.

`_refresh()` va inoltre allineato alla regola già prevista per il dialogo — rigenerare solo ciò che cambia: oggi ricrea tutti i `_texts` a ogni cambio di firma, fino a 40 allocazioni tile in un frame su un tetto di 128 item.

**Fast-forward tenendo A o B fin dalla prima versione**: un round con 9 attori a queste durate costa 250-350 frame, 4-6 secondi per ogni scontro comune.

---

# Obiezioni accolte e come

| # | Obiezione | Come è stata accolta |
| :-- | :-- | :-- |
| 1 | Autotest disallineato (ALIGN=2 contro INTRO=32 frame) | **Passo 0a.** Verificata su `main.cpp:64` e `battle_scene.cpp:26/169`. Ricalibrazione + passaggio a oracolo event-driven; nessun criterio di accettazione usa l'autotest finché non fallisce quando deve. |
| 2 | Nessun gate zero-heap; `grep -i malloc` nascerebbe rotto | **Passo 0b.** Baseline misurata (nessun `new/delete/malloc/__aeabi_d*`); esclusioni documentate per `free` @`0x080149cc` e `mmAllocChannel` @`0x0300080c`. |
| 3 | Divieto float/double non applicato da nulla | **Passo 0c.** `USERCXXFLAGS` oggi vuoto → flag stretti + controllo simboli. |
| 4 | Promozione silenziosa a 8bpp | **Passo 11(1).** `bpp_mode` esplicito obbligatorio + test su tutte le `.json`, incluse le 9 esistenti che oggi ne sono prive. |
| 5 | Campo `height` mancante nelle `.json` sprite | **Passi 11(2) e 19.** Emesso dal generatore, mai a mano; test `bmp.height % height == 0` e misura OBJ legale. |
| 6 | Budget 32 blocchi BG e tetto 1024 tile mai calcolati | **Passo 9**, nuovo, con `static_assert` in `map_data.h` e soglie per tileset. |
| 7 | `BN_CFG_BG_BLOCKS_MAX_ITEMS` = 16 | **Passi 9 e 14**, come criterio di accettazione della transizione. |
| 8 | BG0 "a richiesta" → frammentazione | **Passo 9.** Allocato all'ingresso scena; `create_optional` per il condizionale. |
| 9 | Foreground 512x256 si ripete su mappa alta 320 | **Passo 11(3).** 512x320 illegale in ogni forma; scelta 512x512 o fascia alta, da prendere prima di disegnare. |
| 10 | Budget palette descrive un modello che il GBA non ha | **Passo 9.** Sostituito con quello reale (1 palette per BG/sprite item 4bpp); 14C annotata come intenzione d'arte; alpha blending non consuma palette. |
| 11 | Limiti sprite separati (`SPRITE_TILES_MAX_ITEMS`) e budget VRAM OBJ assente | **Passi 9, 13, 21.** Contati; cached action per l'overworld, un solo attore animato in battaglia. |
| 12 | Particelle 2x2 sprecano il 94% dello slot | **Passo 9.** Raggruppate in 2-4 sprite 32x32: risolve lo sforamento 131/128 senza sacrificare feature. |
| 13 | "Istanza statica in EWRAM" non è ciò che farà il compilatore | **Passo 4.** `BN_DATA_EWRAM_BSS` (non `BN_DATA_EWRAM`), in un solo `.cpp`, con controllo indirizzo `0x02......` nel gate. |
| 14 | Contraddizione sulla proprietà di `GameState` | **Passo 4.** Una sola istanza in EWRAM, passata **per riferimento**, coerente con `BattleHud::update(const BattleSceneManager&)`. |
| 15 | `constexpr` in header è per-TU (ROM duplicata, puntatori divergenti) | **Passo 1** come regola generale + **Passo 10** con `consteval`/`inline constexpr` e `static_assert` sui valori. |
| 16 | Il dilemma su `scene.h` è falso: basta `protected: ~Scene() = default;` | **Passo 3.** Decisione **tolta** dall'elenco per il designer; divergenza della Sessione 06D chiusa senza deroghe. |
| 17 | L'argomento contro `run()` è falso, e `run()` è già la regola (AGENTS.md §2.3) | **Passo 3.** Adottato `run()`; wrapper unico `gubbio::core_update()`; verifica "una sola `bn::core::update()`". |
| 18 | Il dispatch non dice dove vivono le scene: buco per l'heap | **Passo 3(c).** `switch` con scene a scope, divieti espliciti, `static_assert` su `sizeof`. |
| 19 | Divieto di memcpy autocontraddittorio | **Passo 8.** Sostituito dal contratto POD + `static_assert` su `sizeof`/`offsetof`/no-padding; una sola `write_offset`, un solo buffer di rilettura. |
| 20 | Formato congelato prima dei dati che gli servono; `item_data.h` ignorato | **Passi 8 e 17.** Involucro congelato subito, payload riservato e riempito dopo dialoghi/quest; inventario derivato da `ItemId`/`max_carry` con `static_assert`. |
| 21 | Il Passo 5 non è un'estrazione: tocca la FSM verificata | **Passo 5.** `scene_fade` espone solo primitive; la FSM resta intatta; criterio: Campanone al primo frame, dissolvenza ancora 32 frame. |
| 22 | Sez. 35C (Battle Swirl) ha lo stesso blocco del Boost MAX ma non era in elenco | **Passo 5.** Regola generale su affine = scena a sé, annotata nelle due copie della skill. |
| 23 | `test_battle_engine.py` non può vedere le modifiche architetturali | **Passo 6.** Criteri sostituiti con misure che possono fallire; i 31 test restano come regressione delle formule, dichiarandolo. Righe 295 e 503 da aggiornare col carry-over. |
| 24 | `bn::vector<BattleEvent,64>` senza politica di saturazione | **Passo 20.** `_emit()` che scarta + flag, tetto derivato da `static_assert`, test sul round peggiore. |
| 25 | Il Passo 19/21 riapre il difetto di `_signature()` della Sessione 07D | **Passo 21.** Invariante della firma scritto ed estratto in funzione documentata. |
| 26 | `fixed_point` inutile e `>> 3` ambiguo | **Passo 13.** Posizione in `int` pixel; `bn::fixed` solo per la camera; `.floor_integer()`. |
| 27 | `dialogue_box.h`: la `string_view` non possiede la memoria | **Passo 16(2).** Contratto sulle view statiche + buffer `bn::string<64>` membro. |
| 28 | Nessun write-back su HANDOVER e GDD (AGENTS.md §4) | **Regola permanente §0 + Passo 0-bis.** Le 16 decisioni sarebbero altrettanti "70 nel documento master". |
| 29 | Magic header in tre versioni | **Passo 0-bis + Passo 8.** AGENTS.md corretto a `G115`; `static_assert` byte-wise. |
| 30 | `map_exporter.py` esiste già ed emette nomi fissi | **Passo 10**, parzialmente: exporter parametrizzato ora, ma vedi respinte. |
| 31 | Il Passo 14 (font) ignora tre fatti a verbale | **Passo 15.** Cella dello spazio, rimozione di `../butano/common` dal Makefile, anteprima allineata al font vero. |
| 32 | `BN_CFG_HBES_MAX_ITEMS` = 6, 640 B per effetto | **Passo 9**, messo a verbale per la Sez. 35A. |
| 33 | `big` regular BG esiste: la grep del piano era sbagliata | **Passo 12.** Conflitto n.13 corretto agli atti con i riferimenti; scelta padding/big rifatta sui numeri. |

---

# Obiezioni respinte, e perché

**1. "Il conflitto n.13 è corretto: `big_map` non esiste per i BG regolari — verifica che confermo."** *(uno dei critici avalla la grep del piano)* — **Falso, verificato.** L'API si chiama `big`, non `big_map`, ed è completa a tutti e tre i livelli: `bn_regular_bg_item.h:116` (`big()`), `bn_regular_bg_map_item.h:491` (`_big_dimensions`, soglia > 64 tile), campo json `"big"` a `butano_graphics_tool.py:637` con validazione alle righe 634-649, e streaming a runtime in `bn_bgs_manager.cpp` (`big_map`, `commit_big_map`, `full_commit_big_map`, `check_commit_big_map()` alle righe 76-78, 205, 324, 349-353, 376). Due critici si contraddicono su questo punto e uno dei due ha torto: la conferma va respinta e il verbale corretto, altrimenti la prova negativa mal condotta viene ereditata come verità. **Ma va respinta anche la parte eccessiva dell'obiezione opposta:** `big` **non** sblocca 512x320 (le dimensioni restano multipli di 256, `butano_graphics_tool.py:631-632`), quindi il padding in altezza serve comunque; ciò che `big` compra è la mappa in 1 blocco invece di 4.

**2. "`strings gubbio1151.gba | grep SRAM_V` è vuoto: la conclusione 'il Makefile non va toccato' è asserita e non verificata."** — **Premessa falsa, verificata.** La stringa `SRAM_V113` è **presente** nella ROM attuale, all'offset `0x22FB4` (143.284 decimale), pur non essendoci alcuna unità di traduzione che includa `save_data.h`. La conclusione del piano ("`bn::core::init()` inizializza WAITCNT, il Makefile non va toccato") è quindi **confermata dai fatti**, non solo asserita. Il controllo proposto resta accolto al Passo 8 come gate di regressione — costa dieci secondi e chiude una classe di guasto che si manifesterebbe solo su flash cart — ma non come correzione di un difetto inesistente. (Il `.sav` a 0 byte è coerente: nulla ha ancora scritto.)

**3. "Invertire il verso: `map_exporter.py` diventa la fonte unica, Piazza Grande va autorata in Tiled a partire dalla griglia oggi implicita in `get_tile_type`."** — **Respinto nel merito, accolto nel presupposto.** Il presupposto è giusto (l'exporter esiste, il piano lo ignorava, e i suoi nomi fissi `MAP_WIDTH`/`MAP_HEIGHT`/`COLLISION_MAP` a `map_exporter.py:40-42` impediscono a due mappe di coesistere in una TU): quello è **accolto** al Passo 10. Il rovesciamento no: richiede un `.tmx` che non esiste, uno script di dump aggiuntivo e un round-trip che nessuno può verificare oggi, per sostituire una griglia che è già in repo, già `constexpr`, già leggibile in 20 righe (`piazza_grande_collision.h`), e che è l'unico riferimento contro cui il generatore d'arte può essere tenuto coerente. Regola adottata: Piazza Grande resta autorata in codice; le mappe 2..9 della Sez. 38 passano da Tiled. `MapDescriptor` vede un `const uint8_t*` in entrambi i casi, quindi non esistono "due pipeline" nel punto che conta.

**4. "Il costo del `virtual ~Scene()` è un vincolo di memoria che va sottoposto all'utente."** *(posizione del piano originale)* — **Respinto.** Misurato sull'ELF: la regione heap `__eheap_start 0x020083e4 → __eheap_end 0x02040000` (~223 KB) è riservata dal linkscript **a prescindere**; una vtable costa `.rodata` (41.032 byte su 32 MB) e 1-2 chiamate indirette per frame, cioè zero IWRAM, zero EWRAM, zero VRAM. Il problema era di **igiene di link**, non di memoria, e si risolve con una parola chiave (`protected`) invece che con una deroga permanente che nessuno rimuoverà più.

**5. "`update()` per-frame nel main è una forma equivalente a `run()`, da sottoporre all'utente."** — **Respinto.** AGENTS.md §2.3 riga 21 si è già pronunciato, `BattleSceneManager::run()` esiste già con quel commento in `battle_scene.h:112`, e l'impedimento addotto contro `run()` (impossibilità del punto unico di incremento) è falso. In più `update()` costa di più: due `bn::optional` di scena a scope di main con la somma delle dimensioni riservata per sempre, contro una scena sola garantita dallo scope. Non è una decisione di design: è una regola scritta più una misura.

**6. "Le tre feature (particellare completo + numeri di danno + dialoghi in battaglia) non stanno insieme: almeno una va sacrificata."** *(posizione del piano originale)* — **Respinto.** Lo sforamento 131/128 nasce da 32 particelle 2x2 che occupano uno slot OAM ciascuna. Raggruppandole in 2-4 sprite 32x32 con frame precalcolati si recuperano ~28 slot, e nascondendo il menu comandi durante la fase di animazione altri ~16. Le tre feature tornano a stare insieme senza sacrifici; resta invece da misurare il tetto vero, che è la VRAM OBJ (Passo 9), che il piano non contava affatto.

---

# Decisioni che spettano al designer

Nessuna riga di codice dei passi indicati parte prima che la decisione sia scritta nel GDD (Passo 0-bis).

1. **Carry-over di HP e Fervore fra le scene.** `HERO_START_FERVOR_PERCENT = {80,45,20}` va degradato a default di nuova partita, o resta inizializzatore di ogni battaglia (nel qual caso il salvataggio non ha nulla da trasportare)? Regola di cura: l'Eremo di Sant'Ambrogio (Sez. 6) ripristina HP e Fervore o solo HP? La vittoria cura qualcosa? *Blocca la firma del costruttore di `BattleScene` (Passo 6) e i test 295/503.*
2. **Come si entra in battaglia dall'overworld.** Nessuna sezione lo specifica: niente incontri casuali, contatore di passi, nemici visibili o tile di battaglia nella legenda 21B. Se Piazza Grande è un hub sicuro va dichiarato. *Senza, il round-trip resta collaudabile solo da autotest (Passo 14).*
3. **Dimensioni di Piazza Grande:** 64x40 tile (Sez. 21A/14B.1, già in codice) contro 86x26 (Sez. 15B). Non riconciliabili: 86 eccede i 64 del riquadro. Raccomandazione 64x40, con la 15B annotata come misura reale non trasposta.
4. **Copertura del foreground della piazza:** 512x512 (occlusione su tutta l'altezza, costo in blocchi/tile) oppure fascia alta con nulla di occludente sotto y=256 px. *Vincola dove possono stare i palazzi; da decidere prima di disegnare (Passo 11).*
5. **Densità di colore della piazza:** entro 16 colori per ciascun BG (`bpp_4`) o quantizzazione multi-banco (`bpp_4_auto`), dichiarando quante palette consuma. *Passo 11.*
6. **Chi cammina nell'overworld:** leader singolo fisso (Sez. 21D), leader commutabile (Sez. 23C), o tre sprite in fila (Sez. 28B). *Impatto diretto su VRAM OBJ, OAM e numero di fogli da generare.*
7. **Velocità di camminata e camera.** Proposta da approvare: 1 px/frame a passo (60 px/s, ~8,5 s per attraversare la piazza), 2 px/frame in corsa col tasto B, camera rigida con clamping.
8. **Patente da Matto**, tre assi aperti: come si ottiene (tasto A sul tile 6, Sez. 21B, o rito dei tre giri di Mastro Tano, Q-CIV01); che effetto ha (+50% Velocità / -20% Difesa / immune alla paura, Sez. 8A, o "buff velocità + schivata", Sez. 31A); quanto dura (temporaneo, permanente via flag, o ricompensa di quest).
9. **Fontana dei Matti:** dimensione 2x2 (codice, x 23-24 y 24-25) contro 3x3 (Sez. 15B); solidità (oggi il tipo 6 è calpestabile, l'eroe cammina dentro il bacino); posizione (storicamente davanti al Bargello, Sez. 8A, cioè presso il trigger 4; nella griglia è al centro a x=23).
10. **Topografia delle uscite:** il trigger 5 (x≥61) porta a Porta Romana, ma la Sez. 15C colloca a est il Quartiere Sant'Andrea e Porta Romana oltre. Inoltre: i bordi laterali della piazza sono indefiniti (la 21C mostra il calpestabile fra x=8 e x=58, il codice restituisce 0 fino a x=0 e x=63); gli "Arconi di Sostruzione" (14B.1) sono un secondo livello mai mappato — o mappa separata con un quinto trigger, o stralciati.
11. **Doppio slot di salvataggio:** due partite distinte (Sez. 33A) o due copie ridondanti (Sez. 24)? Con 32 KB di FRAM il dilemma è economicamente finto (proposta: 2 slot utente × 2 banche = 528 byte), ma cambia il menu.
12. **Sistema di esperienza:** non esiste in nessun punto del GDD, pur essendoci `level` in `HeroSaveState`, la curva 13B, il cap 20 della Sez. 30 e quest che "conferiscono esperienza". Serve un campo XP? Costa 2-4 byte **ora**, un bump di versione dopo. Collegata: livello condiviso o per eroe (il mockup 33B mostra tutti a LV 8, `init_battle` prende un solo `party_level`).
13. **Font:** custom con i 7 accenti gravi italiani mancanti (lavoro d'arte, poi adottato anche dal Battle HUD), o convenzione con apostrofo già in uso in HANDOVER (gratuita, ma stampa gli apostrofi nel testo di gioco per sempre).
14. **Misura degli sprite di battaglia:** 16x32 / 32x32 (Sez. 23A, già adottate) o 32x48 (Sez. 28B, **non è una misura OBJ legale** sul GBA). Correggere la 28B, oppure salire a 32x64 quadruplicando il costo di Giorgio. Collegate e non coperte dal GDD: manca una posa di **BREAK** (unico stato prolungato del gioco privo di rappresentazione) e una di **KO**; non è fissata la durata di un round.
15. **Numeri di danno fluttuanti:** non esistono in nessuna sezione e il mockup 14B.3 non li prevede, ma senza di essi l'HUD non comunica quanto ha fatto un colpo (le barre hanno 17 tacche). Con il raggruppamento delle particelle il budget OAM li regge.
16. **Effetti affini:** Boost MAX "a schermo intero" (Sez. 20A), zoom/rotazione Mode 7 (28B), Battle Swirl d'ingresso (35C), Cinematica 2 (34B). O sono scene a sé con teardown completo dei BG regolari, o restano effetti su sprite e palette. Non possono essere sotto-stati di una scena Mode 0, e il pannello HUD dipinto nelle righe 112-159 del fondale (Sessione 05) ruoterebbe con tutto il resto.
17. **Q-CIV01, ramo "Tira dritto":** cosa accade rifiutando il rito di Mastro Tano — quest fallita, rinviata o ripetibile? È l'unica ramificazione esplicita della Sez. 31 e la tabella CHOICE non si riempie senza. Collegata: i bonus mura dei 4 Quartieri si attivano al completamento della singola quest o al superamento di una soglia di `quartieri_reputation` (campo `uint8_t`, quindi il design presuppone una scala numerica di cui nessuna sezione fornisce valori né soglia)?