#include "save_data.h"

#include "bn_log.h"
#include "bn_sram.h"

// La lettura e la scrittura del salvataggio su SRAM; le decisioni (quale banca, che stato) sono le
// funzioni constexpr di include/save_data.h, provate a tempo di compilazione.
namespace gubbio::salvataggio
{

namespace
{
    // Tre record in EWRAM e non sullo stack: le due banche lette e quello da comporre e verificare.
    BN_DATA_EWRAM_BSS SaveData s_banca_a;
    BN_DATA_EWRAM_BSS SaveData s_banca_b;
    BN_DATA_EWRAM_BSS SaveData s_record;

    [[nodiscard]] int scostamento(int slot, int banca)
    {
        return (slot * BANCHE + banca) * int(sizeof(SaveData));
    }

    [[nodiscard]] bool slot_valido(int slot)
    {
        return slot >= 0 && slot < SLOT;
    }

    void leggi_banche(int slot)
    {
        bn::sram::read_offset(s_banca_a, scostamento(slot, 0));
        bn::sram::read_offset(s_banca_b, scostamento(slot, 1));
    }

    [[nodiscard]] bool stessi_byte_record(const SaveData& a, const SaveData& b)
    {
        const uint8_t* pa = reinterpret_cast<const uint8_t*>(&a);
        const uint8_t* pb = reinterpret_cast<const uint8_t*>(&b);

        for(int i = 0; i < int(sizeof(SaveData)); ++i)
        {
            if(pa[i] != pb[i])
            {
                return false;
            }
        }

        return true;
    }
}

StatoSlot stato(int slot)
{
    if(! slot_valido(slot))
    {
        return StatoSlot::VUOTO;
    }

    leggi_banche(slot);
    return stato_slot(s_banca_a, s_banca_b);
}

bool carica(int slot, GameState& stato)
{
    if(! slot_valido(slot))
    {
        return false;
    }

    leggi_banche(slot);
    int banca = banca_da_caricare(s_banca_a, s_banca_b);

    if(banca < 0)
    {
        return false;
    }

    stato = estrai(banca == 0 ? s_banca_a : s_banca_b);
    return true;
}

bool salva(int slot, const GameState& stato)
{
    if(! slot_valido(slot))
    {
        return false;
    }

    leggi_banche(slot);
    int banca = banca_da_scrivere(s_banca_a, s_banca_b);
    uint32_t contatore = prossimo_contatore(s_banca_a, s_banca_b);
    s_record = componi(stato, contatore);
    bn::sram::write_offset(s_record, scostamento(slot, banca));

    // La rilettura di verifica: senza, una SRAM guasta (o un emulatore senza file di salvataggio)
    // si scoprirebbe solo al prossimo caricamento, a partita gia' persa.
    SaveData& riletto = banca == 0 ? s_banca_a : s_banca_b;
    bn::sram::read_offset(riletto, scostamento(slot, banca));

    if(! stessi_byte_record(s_record, riletto))
    {
        BN_LOG("SALVA: rilettura di verifica fallita, slot ", slot, " banca ", banca);
        return false;
    }

    BN_LOG("SALVA: slot ", slot, " banca ", banca, " scrittura n. ", int(contatore), " tempo ",
           int(s_record.tempo_secondi), "s crc ", int(s_record.checksum >> 16), ":", int(s_record.checksum & 0xFFFF));
    return true;
}

}
