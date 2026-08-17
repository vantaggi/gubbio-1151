# GUBBIO 1151 - LINEE GUIDA & REGOLE DI SVILUPPO PER AGENTI AI

## 1. Stack Tecnologico & Vincoli Hardware GBA
- **Piattaforma Target:** Game Boy Advance (ARM7TDMI 32-bit @ 16.78 MHz)
- **Engine:** Butano Engine (C++20) con toolchain devkitARM / devkitPro
- **Risoluzione & Refresh:** 240x160 pixel a 60 FPS
- **Memoria RAM Disponibile:** 32 KB IWRAM (fast execution) + 256 KB EWRAM (general data) + 96 KB VRAM
- **Salvataggio Non-Volatile:** Chip FRAM / SRAM 256 Kbit (32 KB) a indirizzamento statico con Magic Header **"G115"** (4 caratteri) e Checksum CRC32.
  > **Correzione (2026-08-18, Sessione 11):** questa riga diceva `"G1151"`, 5 caratteri, mentre
  > `include/save_data.h` dichiara `char magic_header[4] = "G115"` e la skill `butano-gba-dev`
  > prescrive `{'G','1','1','5'}`. Due fonti su tre concordavano sui 4 caratteri; corretta la
  > terza. Senza questa correzione, la prima sessione che avesse "riparato" il codice verso il
  > documento avrebbe invalidato ogni salvataggio esistente.

## 2. Regole di Codifica C++20 (Zero-Heap Policy)
1. **Nessuna Allocazione Dinamica a Runtime:**
   - VIETATO l'uso di `new`, `malloc`, `std::vector`, `std::string`, o heap allocation non controllate durante il gameplay loop.
   - USARE ESCLUSIVAMENTE i contenitori a dimensione fissa di Butano:
     - `bn::vector<T, Capacity>` per liste fisse (es. eroi nel party `bn::vector<BattleUnit, 3>`).
     - `bn::string_view` o `bn::string<Capacity>` per manipolazione stringhe.
     - `bn::fixed` o interi per calcoli matematici (no `float`/`double` pesanti per la CPU ARM7TDMI priva di FPU hardware).
     - `bn::sprite_ptr`, `bn::regular_bg_ptr`, `bn::camera_ptr` per gli handle hardware.
2. **Strutture Dati Statiche & ROM Placement:**
   - Tutte le tabelle di statistiche eroi/boss, matrici di collisione e testi dei dialoghi devono essere marcate `constexpr` o `const` per essere compilate direttamente nella Flash ROM da 32MB senza consumare RAM.
3. **Loop di Rendering e Aggiornamento:**
   - Ogni scena deve implementare il ciclo standard `while(!exit_condition) { update(); bn::core::update(); }`.

## 3. Riferimento Master Document
Fare sempre riferimento a [GUBBIO_1151_LA_BIBBIA_GDD.md](file:///c:/Users/cioti/Desktop/PROGETTI/Gubbio-1051/GUBBIO_1151_LA_BIBBIA_GDD.md) per:
- Formule di danno e bilanciamento statistico (Golden Sun / Octopath Shield Break).
- Sceneggiatura, dialoghi e quest secondarie dei 4 Quartieri.
- Nomi storici, araldica e sound design del Campanone.

## 4. REGOLA FERREA: Protocollo di Continuità & Storico (HANDOVER.md)
Per garantire la massima tracciabilità e un passaggio di consegne impeccabile tra diverse IA o sessioni:
1. **Verifica Iniziale:** Ogni IA/agente che inizia a lavorare su questo progetto DEVE prioritariamente leggere [`HANDOVER.md`](file:///c:/Users/cioti/Desktop/PROGETTI/Gubbio-1051/HANDOVER.md) per acquisire lo stato di avanzamento e i task aperti.
2. **Aggiornamento Continuo Obbligatorio:** Al termine di ogni sessione o dopo ogni intervento significativo (nuova feature, refactoring, fix), l'IA DEVE aggiornare [`HANDOVER.md`](file:///c:/Users/cioti/Desktop/PROGETTI/Gubbio-1051/HANDOVER.md) registrando:
   - **Timestamp / Session ID**
   - **Lavoro svolto & File modificati/creati**
   - **Decisioni tecniche e note architetturali**
   - **Esito dei test (Test Harness & Build Status)**
   - **Roadmap & Prossimi passi immediati (Actionable Next Steps)** per consentire alla sessione/IA successiva di riprendere all'istante senza perdita di contesto.
