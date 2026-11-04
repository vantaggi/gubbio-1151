// Autotest delle opzioni a tempo di compilazione (include/opzioni.h): il record va e torna, un record guasto o di
// un'altra versione da' le normali, e le regole di testo, corsa e volume.

#include "opzioni.h"

namespace gubbio
{

namespace
{
    using namespace opzioni;

    constexpr Opzioni PROVA = { uint8_t(Velocita::LENTO), 1, 4, 1, 1, 0, { 0, 0 } };

    constexpr bool uguali(const Opzioni& a, const Opzioni& b)
    {
        return a.testo == b.testo && a.musica == b.musica && a.effetti == b.effetti &&
               a.sempre_corre == b.sempre_corre && a.piu_chiaro == b.piu_chiaro && a.cartelli == b.cartelli;
    }

    static_assert(uguali(da_record(componi(PROVA)), PROVA), "il record non restituisce le opzioni");
    static_assert(valide(NORMALI) && NORMALI.cartelli == 1 && NORMALI.testo == uint8_t(Velocita::NORMALE),
                  "le normali: testo normale, cartelli accesi");

    constexpr Record guasto()
    {
        Record r = componi(PROVA);
        r.opzioni.musica = 2;       // un byte cambiato dopo il CRC
        return r;
    }

    constexpr Record altra_versione()
    {
        Record r = componi(PROVA);
        r.versione = VERSIONE + 1;
        r.checksum = checksum_di(r);
        return r;
    }

    constexpr Record fuori_misura()
    {
        Record r = componi(PROVA);
        r.opzioni.effetti = TACCHE + 1;
        r.checksum = checksum_di(r);
        return r;
    }

    static_assert(uguali(da_record(guasto()), NORMALI), "un record guasto non torna alle normali");
    static_assert(uguali(da_record(altra_versione()), NORMALI), "un record di un'altra versione non torna alle normali");
    static_assert(uguali(da_record(fuori_misura()), NORMALI), "un valore fuori misura non torna alle normali");
    static_assert(uguali(da_record(Record{}), NORMALI), "la SRAM vuota non da' le normali");

    // il testo: lento una lettera ogni due frame, subito tutto
    static_assert(lettere_nel_frame(NORMALI, 7) == 1 && lettere_nel_frame(PROVA, 6) == 0 && lettere_nel_frame(PROVA, 7) == 1,
                  "la macchina da scrivere non segue la velocita'");
    static_assert(lettere_nel_frame(Opzioni{ uint8_t(Velocita::SUBITO), 3, 3, 0, 0, 1, { 0, 0 } }, 0) == -1,
                  "«subito» non rivela tutta la battuta");

    // la corsa: normale con B tenuto; con «sempre» B cammina
    static_assert(passi(NORMALI, true) == 2 && passi(NORMALI, false) == 1 && passi(PROVA, true) == 1 && passi(PROVA, false) == 2,
                  "la corsa non segue l'opzione");

    // il volume: le tacche normali danno quello proposto, zero tace, mai sopra il massimo
    static_assert(volume_percento(60, TACCHE_NORMALI) == 60 && volume_percento(60, 0) == 0 &&
                  volume_percento(60, TACCHE) == 80 && volume_percento(80, TACCHE) == 100,
                  "i volumi non seguono le tacche");
}

}
