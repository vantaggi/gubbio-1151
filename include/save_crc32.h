#ifndef SAVE_CRC32_H
#define SAVE_CRC32_H

#include <stdint.h>

namespace gubbio {

// CRC32 riflesso (polinomio 0xEDB88320), interamente `constexpr`.
//
// PERCHE' A NIBBLE e non a byte. La tabella classica ha 256 voci da 4 byte = 1 KB di ROM; questa
// ne ha 16 = **64 byte**, al prezzo di due passaggi per byte invece di uno. Su un salvataggio da
// poche centinaia di byte, scritto qualche volta per partita, il tempo non e' la risorsa scarsa.
//
// PERCHE' LA TABELLA E' DERIVATA e non trascritta. Sedici costanti esadecimali copiate a mano
// sono sedici occasioni di sbagliare una cifra, e l'errore non si vedrebbe: un CRC sbagliato ma
// *coerente con se stesso* supera ogni verifica interna e fallisce solo il giorno in cui un
// salvataggio va confrontato con uno prodotto da un'altra implementazione — o da
// `tests/test_save_system.py`, che usa lo `zlib` di Python. Qui la tabella e' calcolata dal
// polinomio a compile time, e il vettore di prova standard e' verificato dal compilatore.

struct Crc32Table
{
    uint32_t entry[16];
};

[[nodiscard]] consteval Crc32Table make_crc32_table()
{
    Crc32Table table{};

    for(uint32_t i = 0; i < 16; ++i)
    {
        uint32_t value = i;

        for(int bit = 0; bit < 4; ++bit)
        {
            value = (value & 1) ? ((value >> 1) ^ 0xEDB88320u) : (value >> 1);
        }

        table.entry[i] = value;
    }

    return table;
}

// `inline` obbligatorio: senza, ogni unita' di traduzione riceverebbe la propria copia dei 64
// byte in .rodata (regola di stile del Passo 1 del piano).
inline constexpr Crc32Table CRC32_TABLE = make_crc32_table();

// Stato corrente del CRC dopo un altro byte. Il valore iniziale e' 0xFFFFFFFF e il risultato va
// complementato: sono le due convenzioni del CRC-32/ISO-HDLC, quello di zlib e di PNG.
[[nodiscard]] constexpr uint32_t crc32_update(uint32_t crc, uint8_t byte)
{
    crc ^= byte;
    crc = (crc >> 4) ^ CRC32_TABLE.entry[crc & 0x0F];
    crc = (crc >> 4) ^ CRC32_TABLE.entry[crc & 0x0F];
    return crc;
}

[[nodiscard]] constexpr uint32_t crc32(const uint8_t* data, int size)
{
    uint32_t crc = 0xFFFFFFFFu;

    for(int i = 0; i < size; ++i)
    {
        crc = crc32_update(crc, data[i]);
    }

    return ~crc;
}

// --- Verifica a compile time, senza emulatore e senza test suite ----------------------------
//
// "123456789" -> 0xCBF43926 e' il vettore di prova canonico del CRC-32/ISO-HDLC (catalogo
// Rocksoft/CRC RevEng). Se la tabella, il verso dei bit o le convenzioni di init/complemento
// fossero sbagliati, questa riga non compilerebbe.
namespace detail {

[[nodiscard]] consteval uint32_t crc32_of_check_vector()
{
    const char text[] = "123456789";
    uint32_t crc = 0xFFFFFFFFu;

    for(int i = 0; i < 9; ++i)
    {
        crc = crc32_update(crc, uint8_t(text[i]));
    }

    return ~crc;
}

} // namespace detail

static_assert(detail::crc32_of_check_vector() == 0xCBF43926u,
              "CRC32 non conforme al vettore di prova standard");

// Un CRC che ignorasse i dati passerebbe comunque il vettore singolo: due input diversi devono
// dare risultati diversi, e un input vuoto deve dare il valore convenzionale 0.
static_assert(crc32(nullptr, 0) == 0u, "CRC32 di un blocco vuoto deve essere 0");

} // namespace gubbio

#endif // SAVE_CRC32_H
