#ifndef GUBBIO_SAVE_DATA_H
#define GUBBIO_SAVE_DATA_H

#include <cstddef>
#include <cstdint>

#include "bn_type_traits.h"

#include "game_state.h"
#include "save_crc32.h"

// Il formato del salvataggio su SRAM, ripreso dal prototipo (tag prototipo-v0: include/save_data.h):
// INVOLUCRO CONGELATO, PAYLOAD RISERVATO. Si congelano magic, versione, contatore di scrittura,
// tempo di gioco e checksum; il payload e' un blocco di 256 byte in cui GameState entra con largo
// margine (esperienza, inventario e il resto arriveranno li' dentro senza spostare gli offset).
// Due slot per il giocatore, ognuno con due banche in ping-pong: si scrive nella meno recente e si
// carica la piu' recente valida, cosi' una scrittura interrotta non perde la partita.
//
// La logica (quale banca caricare, quale scrivere, com'e' uno slot) e' constexpr su record gia'
// letti: src/autotest_salvataggio.cpp la prova a tempo di compilazione; src/save_system.cpp fa
// solo la lettura e la scrittura su SRAM.
namespace gubbio::salvataggio
{

// 'G','1','1','5' in quest'ordine: si legge in un hex dump del .sav.
inline constexpr uint32_t MAGIC = uint32_t('G') | (uint32_t('1') << 8) | (uint32_t('1') << 16) | (uint32_t('5') << 24);
static_assert(MAGIC == 0x35313147u, "il magic non e' G115");
static_assert(__BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__, "il magic e' definito byte per byte: serve little-endian");

// Versione del FORMATO: un salvataggio di un'altra versione si rifiuta, non si reinterpreta.
inline constexpr uint16_t VERSIONE = 1;
inline constexpr int PAYLOAD_BYTE = 256;
inline constexpr int SLOT = 2;
inline constexpr int BANCHE = 2;

static_assert(int(sizeof(GameState)) <= PAYLOAD_BYTE, "GameState non entra nel payload: serve una versione nuova");

struct SaveData
{
    uint32_t magic;
    uint32_t contatore;         // monotono: la banca con il contatore piu' alto e' la piu' recente
    uint32_t tempo_secondi;
    uint16_t versione;
    uint16_t payload_byte;      // i byte significativi del payload (sizeof(GameState))
    uint8_t payload[PAYLOAD_BYTE];
    uint32_t checksum;          // ULTIMO campo: il CRC32 di tutto cio' che lo precede
};

inline constexpr int BYTE_CON_CHECKSUM = int(offsetof(SaveData, checksum));

static_assert(bn::is_trivially_copyable<SaveData>(), "bn::sram copia byte: serve un tipo banalmente copiabile");
static_assert(sizeof(SaveData) == 276, "sizeof(SaveData) e' congelato: cambiarlo invalida i .sav");
static_assert(offsetof(SaveData, magic) == 0 && offsetof(SaveData, contatore) == 4 &&
              offsetof(SaveData, tempo_secondi) == 8 && offsetof(SaveData, versione) == 12 &&
              offsetof(SaveData, payload_byte) == 14 && offsetof(SaveData, payload) == 16 &&
              offsetof(SaveData, checksum) == 272, "SaveData: gli offset sono congelati");
static_assert(sizeof(SaveData) == sizeof(uint32_t) * 3 + sizeof(uint16_t) * 2 + PAYLOAD_BYTE + sizeof(uint32_t),
              "SaveData ha padding: un byte indeterminato entrerebbe nel CRC");
static_assert(sizeof(SaveData) * SLOT * BANCHE <= 32 * 1024, "i quattro record non stanno nei 32 KB di SRAM");

struct ByteRecord
{
    uint8_t b[sizeof(SaveData)];
};

struct ByteStato
{
    uint8_t b[sizeof(GameState)];
};

[[nodiscard]] constexpr uint32_t checksum_di(const SaveData& r)
{
    ByteRecord byte = __builtin_bit_cast(ByteRecord, r);
    uint32_t crc = 0xFFFFFFFFu;

    for(int i = 0; i < BYTE_CON_CHECKSUM; ++i)
    {
        crc = crc32_update(crc, byte.b[i]);
    }

    return ~crc;
}

[[nodiscard]] constexpr bool banca_valida(const SaveData& r)
{
    return r.magic == MAGIC && r.versione == VERSIONE && r.payload_byte == sizeof(GameState) &&
           checksum_di(r) == r.checksum;
}

// Il record da scrivere per uno stato: oltre GameState il payload e' azzerato, non lasciato com'era
// (byte residui renderebbero il CRC dipendente da cio' che c'era prima nella banca).
[[nodiscard]] constexpr SaveData componi(const GameState& stato, uint32_t contatore)
{
    SaveData r{};
    r.magic = MAGIC;
    r.contatore = contatore;
    r.tempo_secondi = stato.tempo_frames / 60;
    r.versione = VERSIONE;
    r.payload_byte = uint16_t(sizeof(GameState));
    ByteStato byte = __builtin_bit_cast(ByteStato, stato);

    for(int i = 0; i < PAYLOAD_BYTE; ++i)
    {
        r.payload[i] = i < int(sizeof(GameState)) ? byte.b[i] : uint8_t(0);
    }

    r.checksum = checksum_di(r);
    return r;
}

[[nodiscard]] constexpr GameState estrai(const SaveData& r)
{
    ByteStato byte{};

    for(int i = 0; i < int(sizeof(GameState)); ++i)
    {
        byte.b[i] = r.payload[i];
    }

    return __builtin_bit_cast(GameState, byte);
}

// La banca da caricare: la piu' recente fra le valide, -1 se nessuna lo e'. Se la scrittura piu'
// recente e' stata interrotta, la sua banca non passa il CRC e vince la precedente, intatta.
[[nodiscard]] constexpr int banca_da_caricare(const SaveData& a, const SaveData& b)
{
    bool va = banca_valida(a);
    bool vb = banca_valida(b);

    if(va && vb)
    {
        return b.contatore > a.contatore ? 1 : 0;
    }

    return va ? 0 : (vb ? 1 : -1);
}

// La banca da scrivere: la meno recente se sono valide tutte e due, altrimenti la prima non valida.
// La piu' recente resta intatta finche' la nuova non e' scritta e verificata.
[[nodiscard]] constexpr int banca_da_scrivere(const SaveData& a, const SaveData& b)
{
    int recente = banca_da_caricare(a, b);

    if(recente < 0)
    {
        return 0;
    }

    return 1 - recente;
}

[[nodiscard]] constexpr uint32_t prossimo_contatore(const SaveData& a, const SaveData& b)
{
    int recente = banca_da_caricare(a, b);
    return recente < 0 ? 1 : (recente == 0 ? a.contatore : b.contatore) + 1;
}

// Com'e' uno slot. CORROTTO e VUOTO sono distinti di proposito: uno slot illeggibile non si
// riformatta in silenzio, il giocatore deve sapere che li' c'era qualcosa.
enum class StatoSlot : uint8_t
{
    VUOTO,              // nessuna banca porta il magic
    VALIDO,             // almeno una banca regge magic, versione e CRC
    CORROTTO,           // c'e' qualcosa, ma nessuna banca regge
    ALTRA_VERSIONE,     // un salvataggio di un altro formato: si rifiuta
};

[[nodiscard]] constexpr StatoSlot stato_slot(const SaveData& a, const SaveData& b)
{
    if(banca_da_caricare(a, b) >= 0)
    {
        return StatoSlot::VALIDO;
    }

    if(a.magic != MAGIC && b.magic != MAGIC)
    {
        return StatoSlot::VUOTO;
    }

    bool altra = (a.magic == MAGIC && a.versione != VERSIONE) || (b.magic == MAGIC && b.versione != VERSIONE);
    return altra ? StatoSlot::ALTRA_VERSIONE : StatoSlot::CORROTTO;
}

[[nodiscard]] constexpr bool stessi_byte(const GameState& a, const GameState& b)
{
    ByteStato x = __builtin_bit_cast(ByteStato, a);
    ByteStato y = __builtin_bit_cast(ByteStato, b);

    for(int i = 0; i < int(sizeof(GameState)); ++i)
    {
        if(x.b[i] != y.b[i])
        {
            return false;
        }
    }

    return true;
}

// --- Su SRAM (src/save_system.cpp) ------------------------------------------------------------

[[nodiscard]] StatoSlot stato(int slot);

// Carica la banca piu' recente e valida; false (e 'stato' non toccato) se lo slot non si carica.
[[nodiscard]] bool carica(int slot, GameState& stato);

// Scrive nella banca meno recente e rilegge per verifica: false se la rilettura non torna.
[[nodiscard]] bool salva(int slot, const GameState& stato);

// Il tempo di gioco della banca piu' recente, per il titolo; 0 se lo slot non e' valido.
[[nodiscard]] uint32_t tempo_secondi(int slot);

}

#endif
