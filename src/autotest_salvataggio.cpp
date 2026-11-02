// Autotest del salvataggio a tempo di compilazione (include/save_data.h): se una prova non regge,
// la ROM non compila. Le tre negative del piano: una banca corrotta (vince l'altra), entrambe
// corrotte (lo slot e' CORROTTO e non si carica nulla), e un CRC sbagliato non passa mai
// (il CRC stesso e' confrontato con zlib in tests/test_save_system.py, sul .sav vero di mGBA).

#include "save_data.h"

namespace gubbio
{

namespace
{
    using namespace salvataggio;

    constexpr GameState STATO_A = { 1000, 3600, 120, 340, 2, { 0, 0, 0 } };
    constexpr GameState STATO_B = { 2000, 7260, -5, 17, 9, { 0, 0, 0 } };

    // Andata e ritorno: lo stato estratto dal record e' lo stesso, byte per byte.
    static_assert(stessi_byte(estrai(componi(STATO_A, 1)), STATO_A), "il record non restituisce lo stato");
    static_assert(! stessi_byte(STATO_A, STATO_B), "la prova di uguaglianza non distingue due stati");
    static_assert(componi(STATO_B, 1).tempo_secondi == 121, "tempo di gioco in secondi");

    // Il CRC copre tutto: cambiare un solo byte del payload o del contatore lo rompe.
    consteval bool un_byte_rompe_il_crc()
    {
        SaveData r = componi(STATO_A, 1);

        if(! banca_valida(r))
        {
            return false;
        }

        for(int i = 0; i < PAYLOAD_BYTE; i += 37)
        {
            SaveData guasto = r;
            guasto.payload[i] ^= 0x10;

            if(banca_valida(guasto))
            {
                return false;
            }
        }

        SaveData guasto = r;
        guasto.contatore += 1;
        return ! banca_valida(guasto);
    }

    static_assert(un_byte_rompe_il_crc(), "un record alterato passa ancora il CRC");

    // Ping-pong: due banche valide, si carica la piu' recente e si scrive sull'altra.
    constexpr SaveData BANCA_VECCHIA = componi(STATO_A, 4);
    constexpr SaveData BANCA_NUOVA = componi(STATO_B, 5);

    static_assert(banca_da_caricare(BANCA_VECCHIA, BANCA_NUOVA) == 1 && banca_da_caricare(BANCA_NUOVA, BANCA_VECCHIA) == 0,
                  "non si carica la banca piu' recente");
    static_assert(banca_da_scrivere(BANCA_VECCHIA, BANCA_NUOVA) == 0, "si scriverebbe sulla banca piu' recente");
    static_assert(prossimo_contatore(BANCA_VECCHIA, BANCA_NUOVA) == 6, "il contatore non cresce");
    static_assert(stato_slot(BANCA_VECCHIA, BANCA_NUOVA) == StatoSlot::VALIDO, "slot valido");

    // Negativa 1: la banca piu' recente corrotta (scrittura interrotta): vince la vecchia, intatta,
    // e la prossima scrittura va sulla corrotta.
    consteval SaveData corrotta(SaveData r)
    {
        r.payload[3] ^= 0xFF;
        return r;
    }

    static_assert(banca_da_caricare(BANCA_VECCHIA, corrotta(BANCA_NUOVA)) == 0 &&
                  stessi_byte(estrai(BANCA_VECCHIA), STATO_A), "con la banca nuova corrotta non vince la vecchia");
    static_assert(banca_da_scrivere(BANCA_VECCHIA, corrotta(BANCA_NUOVA)) == 1, "si scriverebbe sulla banca buona");

    // Negativa 2: entrambe corrotte: nessuna banca, slot CORROTTO (non VUOTO: c'era qualcosa).
    static_assert(banca_da_caricare(corrotta(BANCA_VECCHIA), corrotta(BANCA_NUOVA)) == -1 &&
                  stato_slot(corrotta(BANCA_VECCHIA), corrotta(BANCA_NUOVA)) == StatoSlot::CORROTTO,
                  "due banche corrotte non danno uno slot CORROTTO");

    // Lo slot vuoto (SRAM azzerata o mai scritta) e quello di un'altra versione.
    constexpr SaveData VUOTA = {};

    static_assert(stato_slot(VUOTA, VUOTA) == StatoSlot::VUOTO && banca_da_scrivere(VUOTA, VUOTA) == 0 &&
                  prossimo_contatore(VUOTA, VUOTA) == 1, "slot vuoto");

    consteval SaveData altra_versione(SaveData r)
    {
        r.versione = VERSIONE + 1;
        r.checksum = checksum_di(r);
        return r;
    }

    static_assert(stato_slot(altra_versione(BANCA_VECCHIA), VUOTA) == StatoSlot::ALTRA_VERSIONE &&
                  banca_da_caricare(altra_versione(BANCA_VECCHIA), VUOTA) == -1, "un'altra versione si caricherebbe");
}

}
