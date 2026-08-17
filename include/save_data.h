#ifndef SAVE_DATA_H
#define SAVE_DATA_H

#include <stddef.h>
#include <stdint.h>

#include "bn_type_traits.h"

#include "game_state.h"

namespace gubbio {

// Formato del salvataggio su FRAM/SRAM: **INVOLUCRO CONGELATO, PAYLOAD RISERVATO**.
//
// PERCHE' COSI'. Un record di salvataggio si congela una volta sola: ogni campo aggiunto dopo
// costa un cambio di versione e una migrazione. Ma i dati che dovranno starci dentro — testi
// visti, stato delle quest, oggetti — arrivano solo con i Passi 16-18. Congelare adesso l'intero
// record significherebbe indovinare; rimandare tutto significherebbe non poter salvare finche'
// i dialoghi non esistono.
// La via d'uscita e' ordinare invece che sperare: qui si congela **solo l'involucro** — magic,
// versione, contatore di scrittura, tempo di gioco, checksum — e il payload e' un blocco opaco
// sovradimensionato. Quando il contenuto sara' noto (Passo 17) lo si struttura dentro quello
// spazio, con **un solo** bump di versione.
//
// SUL memcpy. Questo formato e' scritto e riletto con `bn::sram::write_offset`, che *e'* una
// copia di byte e pretende `is_trivially_copyable`. La disciplina che rende la copia sicura fra
// ricompilazioni non e' evitarla, ma vincolarne il layout: POD standard-layout, `sizeof`
// bloccato, **tutti** gli `offsetof` verificati, campi ordinati per allineamento decrescente e
// somma delle dimensioni uguale a `sizeof` (zero padding). Sono le cinque `static_assert` in
// fondo al file. Senza di esse, un byte di riempimento indeterminato entrerebbe nel CRC e lo
// stesso stato salvato due volte darebbe due checksum diversi.

// Magic scritto in ROM come intero, ma pensato per essere LEGGIBILE IN UN HEX DUMP del `.sav`:
// i quattro byte in memoria sono 'G','1','1','5' in quest'ordine. Un `uint32_t 0x35313147`
// scritto a mano non e' verificabile a occhio; questo si.
inline constexpr uint32_t SAVE_MAGIC = uint32_t('G') | (uint32_t('1') << 8) |
                                       (uint32_t('1') << 16) | (uint32_t('5') << 24);

static_assert(SAVE_MAGIC == 0x35313147u, "Il magic non corrisponde ai caratteri G115");

// L'affermazione "i byte scritti sono G,1,1,5 in quest'ordine" e' vera solo su una piattaforma
// little-endian. Il GBA lo e'; se un domani questo codice venisse portato altrove, la build si
// fermerebbe qui invece di produrre salvataggi illeggibili dall'altra parte.
static_assert(__BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__,
              "Il magic e' definito byte per byte: questa piattaforma non e' little-endian");

// Versione del FORMATO, non del gioco. Si incrementa quando il significato dei byte cambia; un
// salvataggio di versione diversa viene rifiutato, mai reinterpretato.
inline constexpr uint16_t SAVE_VERSION = 1;

// Spazio riservato al payload. `GameState` ne occupa oggi 140: il resto e' margine deliberato
// per dialoghi, quest e oggetti (Passo 17), che entreranno **senza** cambiare `sizeof(SaveData)`
// e quindi senza spostare gli offset delle banche gia' scritte su FRAM.
inline constexpr int SAVE_PAYLOAD_BYTES = 256;

static_assert(int(sizeof(GameState)) <= SAVE_PAYLOAD_BYTES,
              "GameState non entra nel payload riservato: serve un bump di versione");

// Slot di salvataggio visibili al giocatore. Due partite distinte (Sez. 33A) contro due copie
// ridondanti (Sez. 24) e' una decisione di design ancora aperta; con 32 KB di FRAM il dilemma e'
// economicamente finto, quindi si adotta la forma che soddisfa entrambe le letture: **2 slot
// utente, ciascuno con 2 banche in ping-pong**.
inline constexpr int SAVE_SLOT_COUNT = 2;
inline constexpr int SAVE_BANK_COUNT = 2;

// Slot usato finche' non esiste un menu di selezione (Sez. 33A).
inline constexpr int SAVE_SLOT_DEFAULT = 0;

struct SaveData
{
    // --- 4 byte ---
    uint32_t magic;
    uint32_t write_counter;      // monotono: identifica la banca piu' recente
    uint32_t playtime_seconds;   // derivato da GameState::playtime_frames

    // --- 2 byte ---
    uint16_t version;
    uint16_t payload_size;       // byte significativi del payload, per la migrazione futura

    // --- 1 byte ---
    uint8_t payload[SAVE_PAYLOAD_BYTES];

    // --- checksum, ULTIMO campo per contratto ---
    // Copre tutto cio' che lo precede. Stando in fondo, la sua estensione e' `offsetof(checksum)`
    // e non va ricalcolata a mano ogni volta che il record cambia.
    uint32_t checksum;
};

inline constexpr int SAVE_CHECKSUMMED_BYTES = int(offsetof(SaveData, checksum));

// --- Le cinque garanzie che rendono sicura la copia di byte ---------------------------------

static_assert(bn::is_trivially_copyable<SaveData>(),
              "bn::sram::write_offset esige un tipo banalmente copiabile");

static_assert(sizeof(SaveData) == 276, "sizeof(SaveData) e' congelato: cambiarlo invalida i .sav");

static_assert(offsetof(SaveData, magic) == 0);
static_assert(offsetof(SaveData, write_counter) == 4);
static_assert(offsetof(SaveData, playtime_seconds) == 8);
static_assert(offsetof(SaveData, version) == 12);
static_assert(offsetof(SaveData, payload_size) == 14);
static_assert(offsetof(SaveData, payload) == 16);
static_assert(offsetof(SaveData, checksum) == 272);

// Zero padding: se qualcuno inserisce un campo fuori dall'ordine di allineamento, la somma
// smette di quadrare e la build si ferma prima che un byte indeterminato entri nel CRC.
static_assert(sizeof(SaveData) == sizeof(uint32_t) * 3 + sizeof(uint16_t) * 2 +
                                  SAVE_PAYLOAD_BYTES + sizeof(uint32_t),
              "SaveData ha padding: riordinare i campi per allineamento decrescente");

static_assert(sizeof(SaveData) * SAVE_SLOT_COUNT * SAVE_BANK_COUNT <= 32 * 1024,
              "I quattro record non stanno nei 32 KB di FRAM");

// Esito dell'ispezione di uno slot. `CORRUPT` e `EMPTY` sono DISTINTI di proposito: uno slot
// corrotto non va riformattato in silenzio — il giocatore ha diritto di sapere che qualcosa
// c'era e non e' piu' leggibile, e un auto-format nasconderebbe per sempre la causa.
enum class SlotStatus : uint8_t
{
    EMPTY,           // nessuna banca porta il magic: slot mai usato
    VALID,           // almeno una banca ha magic, versione e checksum coerenti
    CORRUPT,         // c'e' qualcosa, ma nessuna banca supera le verifiche
    WRONG_VERSION    // salvataggio di un altro formato: si rifiuta, non si reinterpreta
};

class SaveSystem
{
public:
    // Ispeziona uno slot senza modificarlo ne' caricarlo.
    [[nodiscard]] static SlotStatus probe(int slot);

    // Carica la banca piu' recente e valida dello slot nello stato di partita.
    // Ritorna false — e **non tocca `state`** — se lo slot non e' caricabile.
    [[nodiscard]] static bool load(int slot, GameState& state);

    // Scrive nella banca meno recente (ping-pong), poi RILEGGE per verifica.
    // Ritorna false se la rilettura non corrisponde: su FRAM guasta o su un emulatore senza
    // file di salvataggio, e' l'unico modo di accorgersene subito invece che al caricamento.
    [[nodiscard]] static bool save(int slot, const GameState& state);

    // Tempo di gioco memorizzato nella banca piu' recente, per il menu di selezione slot.
    // Zero se lo slot non e' valido.
    [[nodiscard]] static uint32_t stored_playtime_seconds(int slot);

private:
    [[nodiscard]] static int _bank_offset(int slot, int bank);
    [[nodiscard]] static bool _read_bank(int slot, int bank, SaveData& out);
    [[nodiscard]] static bool _bank_is_valid(const SaveData& record);
};

} // namespace gubbio

#endif // SAVE_DATA_H
