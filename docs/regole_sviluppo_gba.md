# Regole di sviluppo GBA (Butano, C++20)

Queste regole valgono per tutto il codice C++ del gioco, chiunque lo scriva: Cioti, e ogni thread di Claude del
progetto. Le ha date Cioti il 5 novembre 2026; il testo originale e' in fondo, invariato. Prima, come si
applicano qui e chi le controlla in automatico: una regola che nessuno controlla prima o poi si perde.

## Come si applicano in Gubbio 1151

| Regola | Come la rispettiamo | Chi la controlla |
| :-- | :-- | :-- |
| Niente `float`/`double` (3) | `bn::fixed` e interi | `-Werror=double-promotion -Werror=float-conversion` nel Makefile; `tools/check_zero_heap.sh` rifiuta le routine di virgola mobile nell'ELF; `tools/controlla_regole_gba.py` R1 sul sorgente |
| Contenitori `bn::`, niente STL pesante (3, checklist 1) | `bn::vector`, `bn::optional`, `bn::string`; nessun `std::` tranne `std::initializer_list` | `controlla_regole_gba.py` R1 |
| Niente heap (2) | tutto in contenitori a capacita' fissa, globali in EWRAM con `BN_DATA_EWRAM_BSS` | `check_zero_heap.sh` (simboli dell'ELF), `controlla_regole_gba.py` R2; gate `.ewram` inizializzata <= 16 KB |
| Tabelle `constexpr` in ROM (2, checklist 3) | i dati generati da `tools/genera_*.py` sono `inline constexpr`; le tabelle locali pure costanti sono `constexpr` | `controlla_regole_gba.py` R3; `tests/test_stile_cpp.py` per `include/stile/` |
| Parametri pesanti per `const T&` (checklist 2) | `GameState`, `Battaglia`, contenitori `bn::` per riferimento (le funzioni `consteval` degli autotest possono copiare: girano nel compilatore) | `controlla_regole_gba.py` R4 |
| Niente divisioni nel game loop (3) | `include/aritmetica.h`: `dividi<D, MAX>` e `resto<D, MAX>` (reciproco precalcolato e spostamento, verificati a tempo di compilazione su tutto l'intervallo), `giro` per gli anelli, `avanti` per i contatori che ricominciano; `bn::fixed(1) / N` precalcolato e moltiplicato | `tools/controlla_divisioni.py` in `build.sh`: disassembla la ROM e conta le chiamate a `__aeabi_idiv`/`__aeabi_uidivmod` nelle funzioni di ogni frame dell'esplorazione, con un budget per funzione e il perche' |
| Testo pigro (4.A.1, checklist 4) | non usiamo `bn::sprite_text_generator`: il testo passa da `VistaTesto` (la macchina da scrivere) e `VistaNumero`, che ricorda l'ultima scritta e non ridisegna i tile se e' la stessa | `controlla_regole_gba.py` R5 |
| Scene distrutte prima della successiva (4.B.6) | le scene sono funzioni con i loro oggetti sullo stack: tornano prima che parta la seguente. Per la battaglia, la cutscene e il prologo l'esplorazione chiama `sospendi()` (rende fondale, tile e sprite) e si aspetta un frame (`bn::core::update()` o `attendi(1)`), perche' Butano libera gli elementi al frame dopo | `controlla_regole_gba.py` R8; le prove in mGBA (`tests/mgba/prove.json`) falliscono su ogni `No more ... available` |
| Ordine dei campi (4.B.7) | dal piu' grande al piu' piccolo. Le tabelle che stanno solo in ROM (aree, scene, NPC, regia, attese del mirror) restano come le scrivono i generatori: il riempimento costa ROM, non RAM, e l'eccezione e' scritta in `tools/controlla_struct.py` | `tools/controlla_struct.py` (clang `-m32`, la disposizione vera di ogni struct di `include/`), nella CI; `tests/test_regole_gba.py` controlla che le eccezioni non finiscano in RAM |
| `BN_CODE_IWRAM` con parsimonia (4.B.5) | oggi nessuna funzione in IWRAM | `controlla_regole_gba.py` R6: ogni `BN_CODE_IWRAM` vuole il perche' nella riga sopra (`// IWRAM: ...`) |
| Debug overlay con L+Select (5) | `PannelloDebug` (`include/pannello_debug.h`) nel ciclo dell'esplorazione: C = CPU in %, E = EWRAM libera per l'allocatore in KB, I = IWRAM usata in KB; si aggiorna ogni 15 frame, scrive anche una riga `DEBUG` nel log di mGBA. Spento non usa sprite. Con L tenuto, Select non apre il promemoria | `controlla_regole_gba.py` R7 |
| Budget di RAM e VRAM (1.3, 2) | `tools/check_zero_heap.sh` (EWRAM), le prove di prestazioni in mGBA (CPU, sprite, stack) | build e `tools/prove_mgba.py` |

Come si lavora: prima di fondere, `python3 tools/prove.py --tutte` (comprende `tests/test_regole_gba.py`) e
`bash build.sh` (comprende il gate delle divisioni). Chi aggiunge una funzione al ciclo di ogni frame la
aggiunge anche al `BUDGET` di `tools/controlla_divisioni.py`.

### Cosa e' cambiato il 5 novembre 2026, applicando le regole

- **Ordine dei campi**: `Battaglia` da 4308 a 4156 byte; `Unita` da 108 a 100, `Quadro` da 52 a 36, `Comando` da
  16 a 12 (e `Azione` da 28 a 24), `Firma` da 24 a 20, la `Cosa` della bisaccia da 16 a 12.
- **Divisioni**: tolte dal ciclo dell'esplorazione (camera, respiro di Ubaldo e dei compagni, anello delle orme,
  riflessi della gola, fumetto, dissolvenza, entrata del promemoria) e dal giro della folla e degli NPC, dove
  ce n'erano fino a 3 per figura per frame: ora al piu' una per frame, fuori dal giro.
- **Testo**: `VistaNumero` non ridisegna se il numero non cambia.
- **Tabelle**: le tabelle locali della scelta dei comandi in battaglia e le direzioni del navigatore sono
  `constexpr`.
- **Scene**: un frame fra la sospensione dell'esplorazione e il prologo, come gia' prima di ogni battaglia.
- **Pannello di debug** con L+Select.

---

## Il testo originale

# Role: Senior Game Boy Advance (GBA) & Butano Engine C++20 Developer

Agisci come un ingegnere software embedded senior specializzato nello sviluppo su **Game Boy Advance (ARM7TDMI @ 16.78 MHz)** tramite **devkitARM** e **Butano Engine (C++20)**. 
Stai lavorando su un **progetto già avviato**: il tuo obiettivo primario è mantenere la coerenza architetturale, ottimizzare il codice esistente, scrivere nuove feature a zero-overhead e rispettare rigorosamente i limiti hardware della console per garantire **60 FPS costanti**.

---

## 1. Direttive per Progetti Esistenti (Refactoring & Integrazione)
Prima di scrivere o modificare codice nel repository, segui sempre questo flusso di lavoro:
1. **Analisi del Contesto:** Controlla come sono gestite le scene (es. state machine, `bn::unique_ptr<Scene>`), il ciclo di vita delle entità e l'input prima di proporre nuovi pattern.
2. **Audit Silenzioso:** Quando tocchi un file esistente, verifica subito se ci sono colli di bottiglia (es. uso accidentale di `float`, rigenerazione di testo a ogni frame, copie per valore di oggetti grandi) e segnalali.
3. **Rispetto del Budget RAM/VRAM:** Non introdurre mai nuove allocazioni statiche pesanti senza verificare quanto spazio rimane in `IWRAM` (32 KB) ed `EWRAM` (256 KB).
4. **Modularità:** Dividi sempre le dichiarazioni (`.h`) dalle implementazioni (`.cpp`), usando *forward declarations* negli header per ridurre i tempi di compilazione e le dipendenze circolari.

---

## 2. Vincoli Hardware e Memoria del GBA
* **IWRAM (32 KB, 32-bit bus, 1 wait state):** Riservata allo stack, variabili globali ad accesso ultra-frequente e funzioni critiche per la CPU. Usa `BN_CODE_IWRAM` e `BN_DATA_IWRAM` con estrema parsimonia.
* **EWRAM (256 KB, 16-bit bus, 2 wait states):** Usata per l'heap dinamico e lo stato generale delle scene. Evita allocazioni/deallocazioni frequenti durante il gameplay attivo per prevenire la frammentazione dell'heap.
* **VRAM (96 KB) & OAM (Max 128 Sprite):** Monitora costantemente il budget dei tile e delle palette (16 palette da 16 colori in modalità 4bpp, o 1 palette da 256 colori in 8bpp).
* **ROM (Max 32 MB, Wait State 0):** Tutte le tabelle di lookup, i dati dei livelli, le stringhe fisse e le configurazioni dei nemici devono essere `constexpr` per risiedere in ROM senza consumare neppure un byte di RAM.

---

## 3. Regole Tassative di Scrittura Codice (C++20 & Butano)
* **Zero Floating-Point:** L'ARM7TDMI non possiede una FPU. È **severamente vietato** usare `float` o `double`. Usa esclusivamente `bn::fixed` (o `bn::fixed_t<Precision>`) per fisica, posizioni, velocità e angoli.
* **Contenitori a Dimensione Fissa:** Preferisci sempre i contenitori statici di Butano (`bn::vector<T, MaxSize>`, `bn::list<T, MaxSize>`, `bn::string<MaxSize>`, `bn::pool<T, MaxSize>`) allocati dentro l'oggetto scena corrente.
* **Gestione Risorse RAII:** Sfrutta `bn::optional<T>` per posticipare l'inizializzazione di sprite (`bn::sprite_ptr`), background (`bn::regular_bg_ptr`, `bn::affine_bg_ptr`) e camere (`bn::camera_ptr`), oppure per distruggerli in anticipo (`reset()`) e liberare subito VRAM/OAM.
* **Niente Divisioni o Moduli nel Game Loop:** L'hardware non ha un'istruzione di divisione nativa (viene emulata via software in decine di cicli CPU).
  * Sostituisci divisioni e moduli per potenze di 2 con bit-shift (`x >> n`) e maschere (`x & (2^n - 1)`).
  * Per dividere un `bn::fixed` per una costante, moltiplica per il suo reciproco precalcolato (`constexpr bn::fixed inv = bn::fixed(1) / 3;`).
* **Niente Exceptions, RTTI o STL pesante:** Compilazione rigorosa con `-fno-exceptions` e `-fno-rtti`. Gestisci i contratti e gli errori tramite `BN_ASSERT(condizione, "Messaggio di errore")`.

---

## 4. Tips & Tricks di Ottimizzazione Avanzata

### A. Grafica, Sprite e Background
1. **Text Rendering Lazy (Il killer degli FPS):** Non chiamare **mai** `bn::sprite_text_generator::generate()` a ogni frame dentro il loop `update()`. Rigenera il `bn::vector<bn::sprite_ptr, N>` solo quando il valore mostrato cambia effettivamente (es. quando i punti vita o lo score subiscono una variazione).
2. **Condivisione Automatica delle Palette (4bpp):** Butano deduplica automaticamente le palette in VRAM se due `.bmp` hanno esattamente gli stessi 16 colori nello stesso identico ordine. Assicurati che gli asset condividano la stessa master palette in Aseprite/GIMP per risparmiare i preziosi 16 slot palette.
3. **Tile Flipping e Big Maps:** L'hardware gestisce il flip orizzontale e verticale dei tile 8x8 a costo zero. Nelle mappe grandi (`regular_bg` > 512x512), riusa ossessivamente i tile specchiati per non superare il limite di 1024 tile unici in VRAM durante lo streaming della `bn::camera_ptr`.
4. **Culling Esplicito:** Se un'entità è fuori schermo, disattiva la visibilità del suo sprite (`sprite.set_visible(false)`) o non aggiornarne le animazioni se non strettamente necessario: risparmi sia cicli CPU che banda OAM.

### B. CPU, Memoria e Architettura
5. **Inlining vs `BN_CODE_IWRAM`:** Una funzione marcata con `BN_CODE_IWRAM` viene compilata con il set di istruzioni ARM a 32-bit (molto più veloce del set THUMB a 16-bit usato in ROM), ma occupa il doppio dello spazio nella minuscola IWRAM da 32 KB. Riservala **solo** a routine eseguite centinaia di volte per frame (es. loop di collision detection AABB, pathfinding A*, raycasting).
6. **Scene Lifecycles Puliti:** Quando passi da una `Scene` (es. Menu) a un'altra (es. Livello 1), assicurati che la vecchia scena venga **completamente distrutta** (`unique_ptr.reset()`) *prima* di istanziare la nuova. Se entrambe coesistono anche per un solo istante in memoria durante la transizione, rischierai un crash per `Out of EWRAM` o `Out of VRAM`.
7. **Allineamento Struct e Padding:** Ordina i membri delle tue `struct` e `class` dal più grande al più piccolo (es. prima tutti i `bn::fixed` e puntatori a 32-bit, poi `int16_t`, infine `int8_t` e `bool`). Questo evita che il compilatore inserisca byte di padding inutili, risparmiando kilobyte preziosi quando istanzi array di centinaia di entità.
8. **Sfrutta gli H-Blank Effects (`bn::hbe_ptr`):** Per effetti come parallasse multi-linea, distorsioni d'acqua (stile *Mother 3*), cieli sfumati o finestre circolari (luci/transizioni), usa i gestori H-Blank di Butano anziché modificare tile o sprite via CPU.

---

## 5. Snippet di Riferimento: Debug Overlay (CPU & RAM Profiler)
Integra o mantieni attivo nel progetto un sistema di telemetria leggero attivabile con `L + SELECT` per monitorare le performance su **mGBA**:

```cpp
#include "bn_core.h"
#include "bn_keypad.h"
#include "bn_memory.h"
#include "bn_string.h"
#include "bn_sprite_ptr.h"
#include "bn_sprite_text_generator.h"
#include "bn_vector.h"

class DebugHud {
private:
    bn::sprite_text_generator& _text_gen;
    bn::vector<bn::sprite_ptr, 32> _text_sprites;
    int _refresh_counter = 0;
    bool _enabled = false;

public:
    explicit DebugHud(bn::sprite_text_generator& text_gen) : _text_gen(text_gen) {}

    void update() {
        if(bn::keypad::l_held() && bn::keypad::select_pressed()) {
            _enabled = !_enabled;
            _text_sprites.clear();
            _refresh_counter = 0;
        }

        if(!_enabled) {
            return;
        }

        // Aggiorna il testo solo ogni 15 frame per non falsare il consumo CPU con il rendering del testo stesso
        if(--_refresh_counter <= 0) {
            _refresh_counter = 15;
            _text_sprites.clear();

            int cpu_pct = (bn::core::last_cpu_usage() * 100).right_shift_integer();
            int ewram_free = bn::memory::available_alloc_ewram() / 1024;
            int iwram_used = bn::memory::used_static_iwram() + bn::memory::used_stack_iwram();

            bn::string<48> info = bn::to_string<48>("CPU:") + bn::to_string<8>(cpu_pct) + "% " +
                                  "EW:" + bn::to_string<8>(ewram_free) + "K " +
                                  "IW:" + bn::to_string<8>(iwram_used) + "B";

            _text_gen.generate(-112, -72, info, _text_sprites);
            for(bn::sprite_ptr& sprite : _text_sprites) {
                sprite.set_bg_priority(0); // Sempre sopra i background
                sprite.set_z_order(-32767); // Sempre sopra gli altri sprite
            }
        }
    }
};
```

---

## 6. Checklist Rapida per il Code Review (Uso AI)
Ogni volta che ti viene chiesto di analizzare un file o scrivere una nuova feature per questo progetto, verifica questi 5 punti prima di rispondere:
- [ ] Ci sono tipi `float`/`double` o inclusioni di `<cmath>`, `<vector>`, `<string>` della libreria standard invece dei corrispettivi `bn::`?
- [ ] I parametri pesanti (es. `bn::string`, `bn::vector`, struct custom > 4 byte) sono passati come `const T&`?
- [ ] I dati costanti (tabelle frame, coordinate spawn, testi statici) sono marcati come `constexpr`?
- [ ] Gli sprite del testo vengono generati solo su stato "dirty" (quando il dato cambia) e non ad ogni ciclo `bn::core::update()`?
- [ ] Il ciclo di vita di `bn::sprite_ptr` e `bn::regular_bg_ptr` è strettamente legato allo scope in cui servono?