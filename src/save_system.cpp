#include "save_data.h"

#include "bn_log.h"
#include "bn_sram.h"

#include "game_clock.h"
#include "save_crc32.h"

namespace gubbio {

namespace {

// I DUE BUFFER stanno in EWRAM, non sullo stack.
//
// Il record e' 276 byte e la scrittura ne richiede due — uno da comporre, uno per la rilettura
// di verifica — cioe' oltre mezzo kilobyte. Il salvataggio puo' avvenire in qualunque momento,
// anche al punto di massima profondita' dello stack (scena -> menu -> conferma), e lo stack sta
// negli stessi ~21 KB di IWRAM che il resto del gioco si contende. In EWRAM quei 552 byte non
// tolgono nulla a nessuno. Sono `static` a scope di file: nessun altro modulo puo' raggiungerli.
BN_DATA_EWRAM_BSS SaveData s_compose_buffer;
BN_DATA_EWRAM_BSS SaveData s_verify_buffer;

[[nodiscard]] const uint8_t* as_bytes(const SaveData& record)
{
    return reinterpret_cast<const uint8_t*>(&record);
}

[[nodiscard]] bool same_bytes(const SaveData& a, const SaveData& b)
{
    const uint8_t* pa = as_bytes(a);
    const uint8_t* pb = as_bytes(b);

    for(int i = 0; i < int(sizeof(SaveData)); ++i)
    {
        if(pa[i] != pb[i])
        {
            return false;
        }
    }

    return true;
}

} // namespace

int SaveSystem::_bank_offset(int slot, int bank)
{
    return (slot * SAVE_BANK_COUNT + bank) * int(sizeof(SaveData));
}

bool SaveSystem::_bank_is_valid(const SaveData& record)
{
    if(record.magic != SAVE_MAGIC || record.version != SAVE_VERSION)
    {
        return false;
    }

    return crc32(as_bytes(record), SAVE_CHECKSUMMED_BYTES) == record.checksum;
}

bool SaveSystem::_read_bank(int slot, int bank, SaveData& out)
{
    bn::sram::read_offset(out, _bank_offset(slot, bank));
    return _bank_is_valid(out);
}

SlotStatus SaveSystem::probe(int slot)
{
    if(slot < 0 || slot >= SAVE_SLOT_COUNT)
    {
        return SlotStatus::EMPTY;
    }

    bool any_magic = false;
    bool wrong_version = false;

    for(int bank = 0; bank < SAVE_BANK_COUNT; ++bank)
    {
        if(_read_bank(slot, bank, s_verify_buffer))
        {
            return SlotStatus::VALID;
        }

        if(s_verify_buffer.magic == SAVE_MAGIC)
        {
            any_magic = true;

            if(s_verify_buffer.version != SAVE_VERSION)
            {
                wrong_version = true;
            }
        }
    }

    if(! any_magic)
    {
        return SlotStatus::EMPTY;
    }

    // C'e' un salvataggio, ma non e' utilizzabile. NON viene riscritto ne' azzerato: il
    // giocatore decidera' se sovrascriverlo, e chi indaga trovera' i byte com'erano.
    return wrong_version ? SlotStatus::WRONG_VERSION : SlotStatus::CORRUPT;
}

bool SaveSystem::load(int slot, GameState& state)
{
    if(slot < 0 || slot >= SAVE_SLOT_COUNT)
    {
        return false;
    }

    int best_bank = -1;
    uint32_t best_counter = 0;

    for(int bank = 0; bank < SAVE_BANK_COUNT; ++bank)
    {
        if(_read_bank(slot, bank, s_verify_buffer))
        {
            // Fra due banche valide vince quella scritta per ultima. E' tutto il meccanismo del
            // ping-pong: se la scrittura piu' recente e' stata interrotta, la sua banca non
            // supera il checksum e resta buona la precedente, che e' intatta per costruzione.
            if(best_bank < 0 || s_verify_buffer.write_counter > best_counter)
            {
                best_bank = bank;
                best_counter = s_verify_buffer.write_counter;
            }
        }
    }

    if(best_bank < 0)
    {
        return false;
    }

    if(! _read_bank(slot, best_bank, s_compose_buffer))
    {
        return false;      // difesa contro una FRAM che rilegge valori diversi ogni volta
    }

    if(s_compose_buffer.payload_size != uint16_t(sizeof(GameState)))
    {
        BN_LOG("SAVE: payload di ", int(s_compose_buffer.payload_size), " byte, attesi ",
               int(sizeof(GameState)), ": caricamento rifiutato");
        return false;
    }

    // Il payload e' oggi l'immagine di `GameState`. Al Passo 17 diventera' un record strutturato
    // dentro lo stesso spazio: `payload_size` e `version` sono cio' che permettera' di
    // distinguere le due forme invece di indovinare.
    uint8_t* destination = reinterpret_cast<uint8_t*>(&state);

    for(int i = 0; i < int(sizeof(GameState)); ++i)
    {
        destination[i] = s_compose_buffer.payload[i];
    }

    // Un salvataggio con CRC valido puo' comunque contenere valori fuori dominio: scritto da una
    // versione precedente, o manomesso in un editor di `.sav`. Il clamp e' l'ultima barriera fra
    // quei byte e un indice fuori tabella.
    state.clamp_after_load();
    return true;
}

bool SaveSystem::save(int slot, const GameState& state)
{
    if(slot < 0 || slot >= SAVE_SLOT_COUNT)
    {
        return false;
    }

    // Si scrive nella banca MENO recente: quella piu' recente resta intatta finche' la nuova non
    // e' completa e verificata. E' la garanzia contro l'interruzione a meta' scrittura.
    int target_bank = 0;
    int first_free_bank = -1;
    uint32_t next_counter = 1;
    uint32_t newest_counter = 0;
    bool found_valid = false;

    for(int bank = 0; bank < SAVE_BANK_COUNT; ++bank)
    {
        if(_read_bank(slot, bank, s_verify_buffer))
        {
            if(! found_valid || s_verify_buffer.write_counter > newest_counter)
            {
                newest_counter = s_verify_buffer.write_counter;
                target_bank = (bank + 1) % SAVE_BANK_COUNT;
                found_valid = true;
            }
        }
        else if(first_free_bank < 0)
        {
            first_free_bank = bank;   // vuota o illeggibile: la PRIMA, non l'ultima trovata
        }
    }

    if(! found_valid)
    {
        target_bank = first_free_bank < 0 ? 0 : first_free_bank;
    }

    if(found_valid)
    {
        next_counter = newest_counter + 1;
    }

    s_compose_buffer.magic = SAVE_MAGIC;
    s_compose_buffer.write_counter = next_counter;
    s_compose_buffer.playtime_seconds = uint32_t(playtime_seconds());
    s_compose_buffer.version = SAVE_VERSION;
    s_compose_buffer.payload_size = uint16_t(sizeof(GameState));

    const uint8_t* source = reinterpret_cast<const uint8_t*>(&state);

    for(int i = 0; i < SAVE_PAYLOAD_BYTES; ++i)
    {
        // Oltre `sizeof(GameState)` il payload e' azzerato, non lasciato com'era: byte residui
        // di un salvataggio precedente entrerebbero nel CRC e renderebbero il record dipendente
        // da cio' che c'era prima nella stessa banca.
        s_compose_buffer.payload[i] = i < int(sizeof(GameState)) ? source[i] : uint8_t(0);
    }

    s_compose_buffer.checksum = crc32(as_bytes(s_compose_buffer), SAVE_CHECKSUMMED_BYTES);

    // UNA SOLA scrittura: il record e' contiguo e banalmente copiabile proprio perche' questa
    // riga possa essere una sola.
    bn::sram::write_offset(s_compose_buffer, _bank_offset(slot, target_bank));

    // RILETTURA DI VERIFICA. Senza, una FRAM guasta — o un emulatore avviato senza file di
    // salvataggio — verrebbe scoperta solo al prossimo caricamento, cioe' quando la partita e'
    // gia' perduta.
    bn::sram::read_offset(s_verify_buffer, _bank_offset(slot, target_bank));

    if(! same_bytes(s_compose_buffer, s_verify_buffer))
    {
        BN_LOG("SAVE: rilettura di verifica FALLITA su slot ", slot, " banca ", target_bank);
        return false;
    }

    // Il CRC e' stampato come due meta' a 16 bit: `int(uint32_t)` lo renderebbe negativo per
    // meta' dei valori possibili, e un log che mente sui propri numeri e' peggio di nessun log.
    BN_LOG("SAVE: slot ", slot, " banca ", target_bank, " scrittura n. ", int(next_counter),
           " tempo ", int(s_compose_buffer.playtime_seconds), "s crc ",
           int(s_compose_buffer.checksum >> 16), ":", int(s_compose_buffer.checksum & 0xFFFF));
    return true;
}

uint32_t SaveSystem::stored_playtime_seconds(int slot)
{
    if(slot < 0 || slot >= SAVE_SLOT_COUNT)
    {
        return 0;
    }

    uint32_t best = 0;
    uint32_t best_counter = 0;
    bool found = false;

    for(int bank = 0; bank < SAVE_BANK_COUNT; ++bank)
    {
        if(_read_bank(slot, bank, s_verify_buffer) &&
           (! found || s_verify_buffer.write_counter > best_counter))
        {
            best = s_verify_buffer.playtime_seconds;
            best_counter = s_verify_buffer.write_counter;
            found = true;
        }
    }

    return best;
}

} // namespace gubbio
