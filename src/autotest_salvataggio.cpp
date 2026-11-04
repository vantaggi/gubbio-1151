// Autotest del salvataggio a tempo di compilazione (include/save_data.h): se una prova non regge,
// la ROM non compila. Le tre negative del piano: una banca corrotta (vince l'altra), entrambe
// corrotte (lo slot e' CORROTTO e non si carica nulla), e un CRC sbagliato non passa mai
// (il CRC stesso e' confrontato con zlib in tests/test_save_system.py, sul .sav vero di mGBA).
// MOB: la v4 (80 byte) e l'aggiornamento dei salvataggi v3, con le loro negative.

#include "save_data.h"

namespace gubbio
{

namespace
{
    using namespace salvataggio;

    constexpr GameState STATO_A = { 1000, 3600, { 40, 40, 40 }, 120, 340, 2, { 2, 2, 2 }, { 2, 0, 0, 1 }, { 1 }, { 3 }, { 7 }, 0, {} };
    constexpr GameState STATO_B = { 2000, 7260, { 300, 290, 310 }, -5, 17, 9, { 4, 4, 5 }, { 0, 1 }, { 7 }, {}, {}, 0, {} };

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

    // --- v4 (MOB): i campi nuovi fanno andata e ritorno -------------------------------------------
    consteval GameState con_campi_v4(GameState s)
    {
        s.obiettivo = 3;
        s.aree_viste[0] = 0x81;
        s.aree_viste[2] = 0x04;
        s.scorte_comprate = 0x21;
        s.denari = 513;
        return s;
    }

    constexpr GameState STATO_V4 = con_campi_v4(STATO_B);

    static_assert(VERSIONE == 4 && sizeof(GameState) == 80 && componi(STATO_V4, 1).payload_byte == 80,
                  "il formato corrente e' la v4 con GameState di 80 byte");
    static_assert(stessi_byte(estrai(componi(STATO_V4, 1)), STATO_V4) && estrai(componi(STATO_V4, 1)).denari == 513 &&
                  estrai(componi(STATO_V4, 1)).obiettivo == 3, "i campi della v4 non tornano dal record");

    // --- v3: si aggiorna, non si rifiuta ---------------------------------------------------------
    // Un record v3 come lo scriveva il gioco prima di MOB (salvataggio::componi_v3), con un residuo nei 5 byte
    // che nella v3 erano riservati: l'aggiornamento non deve leggerlo.
    consteval bool prefisso_uguale(const GameState& a, const GameState& b)
    {
        ByteStato x = __builtin_bit_cast(ByteStato, a);
        ByteStato y = __builtin_bit_cast(ByteStato, b);

        for(int i = 0; i < BYTE_COMUNI_V3; ++i)
        {
            if(x.b[i] != y.b[i])
            {
                return false;
            }
        }

        return true;
    }

    constexpr SaveData V3 = componi_v3(STATO_A, 9, 0x77);

    static_assert(banca_valida(V3) && stato_slot(V3, VUOTA) == StatoSlot::VALIDO && banca_da_caricare(VUOTA, V3) == 1,
                  "un salvataggio v3 non si carica");
    static_assert(prefisso_uguale(estrai(V3), STATO_A) && estrai(V3).ferite[0] == STATO_A.ferite[0] &&
                  estrai(V3).obiettivo == NESSUN_OBIETTIVO && estrai(V3).aree_viste[0] == 0 &&
                  estrai(V3).scorte_comprate == 0 && estrai(V3).denari == 0 && estrai(V3).riservato[13] == 0,
                  "l'aggiornamento dalla v3 non copia i 59 byte comuni o legge il residuo dei riservati");

    // Negativa: senza aggiornamento (i byte copiati cosi' come sono) il residuo diventerebbe un obiettivo.
    static_assert(V3.payload[BYTE_COMUNI_V3] == 0x77 && estrai(V3).obiettivo != V3.payload[BYTE_COMUNI_V3],
                  "la prova del residuo non prova nulla");

    // Ping-pong fra versioni: vince la banca piu' recente, di qualunque delle due versioni; si scrive sull'altra,
    // e quel che si scrive e' sempre v4.
    static_assert(banca_da_caricare(V3, componi(STATO_B, 10)) == 1 && banca_da_caricare(componi(STATO_B, 8), V3) == 1 &&
                  banca_da_scrivere(componi(STATO_B, 8), V3) == 0 && prossimo_contatore(componi(STATO_B, 8), V3) == 10,
                  "le banche v3 e v4 dello stesso slot non si confrontano col contatore");

    // Negative: una v3 col payload della v4 (o viceversa) non e' valida; la v2 resta di un'altra versione.
    consteval SaveData con_misura(SaveData r, uint16_t versione, uint16_t byte)
    {
        r.versione = versione;
        r.payload_byte = byte;
        r.checksum = checksum_di(r);
        return r;
    }

    static_assert(! banca_valida(con_misura(V3, VERSIONE_V3, 80)) && ! banca_valida(con_misura(V3, VERSIONE, 64)) &&
                  stato_slot(con_misura(V3, VERSIONE_V3, 80), VUOTA) == StatoSlot::CORROTTO,
                  "una misura del payload che non e' quella della sua versione passa");
    static_assert(stato_slot(con_misura(V3, 2, 64), VUOTA) == StatoSlot::ALTRA_VERSIONE &&
                  banca_da_caricare(con_misura(V3, 2, 64), VUOTA) == -1, "la v2 si caricherebbe");
}

}
