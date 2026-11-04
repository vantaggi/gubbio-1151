#ifndef GUBBIO_OPZIONI_H
#define GUBBIO_OPZIONI_H

#include <cstddef>
#include <cstdint>

#include "bn_type_traits.h"

#include "save_crc32.h"
#include "save_data.h"

// Le opzioni (MOP, menu/PROPOSTA.md sez. 3.7; mockup menu/mockup/07_opzioni.png): valgono per tutti e due gli slot
// e stanno in un piccolo record SRAM a parte, dopo i quattro del salvataggio, con il suo CRC: se il record e' guasto
// (o non c'e' ancora) si torna ai valori normali. La logica e' constexpr e la prova src/autotest_opzioni.cpp; la
// lettura, la scrittura e l'effetto sul gioco sono in src/opzioni.cpp.
namespace gubbio::opzioni
{

enum class Velocita : uint8_t
{
    LENTO,          // una lettera ogni due frame
    NORMALE,        // una lettera a frame
    SUBITO,         // la battuta intera
};

inline constexpr int TACCHE = 4;
inline constexpr int TACCHE_NORMALI = 3;    // i volumi proposti da musica/LEGGIMI.md; la quarta tacca e' piu' forte

struct Opzioni
{
    uint8_t testo;          // Velocita
    uint8_t musica;         // 0..TACCHE
    uint8_t effetti;        // 0..TACCHE
    uint8_t sempre_corre;   // 1: si corre senza tenere B, e B cammina
    uint8_t piu_chiaro;     // 1: lo schermo piu' luminoso, per il GBA senza retroilluminazione
    uint8_t cartelli;       // 1: i cartelli ai varchi
    uint8_t riservato[2];
};

static_assert(sizeof(Opzioni) == 8, "Opzioni: 8 byte congelati");

inline constexpr Opzioni NORMALI = { uint8_t(Velocita::NORMALE), TACCHE_NORMALI, TACCHE_NORMALI, 0, 0, 1, { 0, 0 } };

// 'G','1','O','P': si legge in un hex dump del .sav, accanto ai 'G115' degli slot.
inline constexpr uint32_t MAGIC = uint32_t('G') | (uint32_t('1') << 8) | (uint32_t('O') << 16) | (uint32_t('P') << 24);
inline constexpr uint16_t VERSIONE = 1;

struct Record
{
    uint32_t magic;
    uint16_t versione;
    uint16_t byte;          // sizeof(Opzioni)
    Opzioni opzioni;
    uint32_t checksum;      // ULTIMO campo: il CRC32 di tutto cio' che lo precede
};

static_assert(bn::is_trivially_copyable<Record>(), "bn::sram copia byte: serve un tipo banalmente copiabile");
static_assert(sizeof(Record) == 20 && offsetof(Record, opzioni) == 8 && offsetof(Record, checksum) == 16,
              "Record delle opzioni: gli offset sono congelati (e niente padding nel CRC)");

// Subito dopo i quattro record del salvataggio.
inline constexpr int SCOSTAMENTO = int(sizeof(salvataggio::SaveData)) * salvataggio::SLOT * salvataggio::BANCHE;
static_assert(SCOSTAMENTO + int(sizeof(Record)) <= 32 * 1024, "il record delle opzioni non sta nella SRAM");

struct ByteRecord
{
    uint8_t b[sizeof(Record)];
};

[[nodiscard]] constexpr uint32_t checksum_di(const Record& r)
{
    ByteRecord byte = __builtin_bit_cast(ByteRecord, r);
    uint32_t crc = 0xFFFFFFFFu;

    for(int i = 0; i < int(offsetof(Record, checksum)); ++i)
    {
        crc = crc32_update(crc, byte.b[i]);
    }

    return ~crc;
}

[[nodiscard]] constexpr bool valide(const Opzioni& o)
{
    return o.testo <= uint8_t(Velocita::SUBITO) && o.musica <= TACCHE && o.effetti <= TACCHE &&
           o.sempre_corre <= 1 && o.piu_chiaro <= 1 && o.cartelli <= 1;
}

[[nodiscard]] constexpr Record componi(const Opzioni& o)
{
    Record r{};
    r.magic = MAGIC;
    r.versione = VERSIONE;
    r.byte = uint16_t(sizeof(Opzioni));
    r.opzioni = o;
    r.opzioni.riservato[0] = 0;
    r.opzioni.riservato[1] = 0;
    r.checksum = checksum_di(r);
    return r;
}

// Le opzioni di un record letto: le sue se e' integro, se no le normali.
[[nodiscard]] constexpr Opzioni da_record(const Record& r)
{
    bool buono = r.magic == MAGIC && r.versione == VERSIONE && r.byte == sizeof(Opzioni) &&
                 checksum_di(r) == r.checksum && valide(r.opzioni);
    return buono ? r.opzioni : NORMALI;
}

// Quante lettere della macchina da scrivere si rivelano in questo frame (-1: tutte).
[[nodiscard]] constexpr int lettere_nel_frame(const Opzioni& o, uint32_t frame)
{
    return o.testo == uint8_t(Velocita::SUBITO) ? -1 : (o.testo == uint8_t(Velocita::LENTO) ? int(frame & 1) : 1);
}

// I passi del giocatore in questo frame: 2 di corsa, 1 camminando. Con «sempre», B fa camminare.
[[nodiscard]] constexpr int passi(const Opzioni& o, bool b_tenuto)
{
    return (o.sempre_corre ? ! b_tenuto : b_tenuto) ? 2 : 1;
}

// Il volume in centesimi: 'normale' a TACCHE_NORMALI, in proporzione alle tacche, mai sopra 100.
[[nodiscard]] constexpr int volume_percento(int normale_percento, int tacche)
{
    int v = normale_percento * tacche / TACCHE_NORMALI;
    return v > 100 ? 100 : v;
}

// L'opzione unica di tutto il gioco; la legge carica() all'accensione.
extern Opzioni g_opzioni;

void carica();
void salva();
// Applica volumi e luminosita' (dopo carica() e a ogni cambio nella pagina).
void applica();

}

#endif
