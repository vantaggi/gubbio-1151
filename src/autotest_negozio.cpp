// Autotest del Venditore delle Logge a tempo di compilazione (include/negozio.h): i denari dei nemici, le scorte per
// fase, il borgo dentro le mura, e i quattro esiti della compera.

#include "negozio.h"
#include "progressione.h"
#include "storia.h"

namespace gubbio
{

namespace
{
    using namespace negozio;
    using storia::Bandiera;

    constexpr uint64_t bit(Bandiera b)
    {
        return uint64_t(1) << int(b);
    }

    constexpr GameState nuova(uint64_t bandiere, int denari)
    {
        GameState p = {};
        progressione::partita_nuova(p);
        storia::accendi(p, bandiere);
        p.denari = uint16_t(denari);
        return p;
    }

    // la pattuglia: due fanti e un balestriere; Corrado non da' denari
    static_assert(denari_incontro(0) == 12 + 12 + 15, "i denari della pattuglia");
    static_assert(denari_incontro(2) == 0, "Corrado non da' denari");

    constexpr bool tetto()
    {
        GameState p = nuova(0, DENARI_MASSIMI - 1);
        assegna_denari(p, 0);
        return p.denari == DENARI_MASSIMI;
    }

    static_assert(tetto(), "i denari non passano il massimo");

    // le scorte per fase
    constexpr uint64_t DIGIUNO = bit(Bandiera::CITTA_IN_DIGIUNO);
    constexpr uint64_t NOTTE = DIGIUNO | bit(Bandiera::RIENTRO_PORTA_METAURO);

    static_assert(ha_merce(nuova(0, 0)) && scorte(nuova(0, 0), 0) == 3 && scorte(nuova(0, 0), 1) == 3,
                  "gia' prima del digiuno («Comprate oggi») tre Crescia e tre Biscotti");
    static_assert(scorte(nuova(DIGIUNO, 0), 0) == 3 && scorte(nuova(DIGIUNO, 0), 1) == 3,
                  "nel digiuno le stesse scorte");
    static_assert(scorte(nuova(DIGIUNO | bit(Bandiera::BORGO_DENTRO), 0), 0) == 2,
                  "col borgo dentro le mura una Crescia in meno (A1-05b)");

    constexpr bool borgo_dopo_tre()
    {
        // tre Crescia comprate prima che il borgo entri: poi non ne restano, e non si va sotto zero
        GameState p = nuova(0, 500);
        compra(p, 0);
        compra(p, 0);
        compra(p, 0);
        storia::accendi(p, DIGIUNO | bit(Bandiera::BORGO_DENTRO));
        return restano(p, 0) == 0 && compra(p, 0) == Esito::FINITE && p.denari == 500 - 3 * PREZZO[0];
    }

    static_assert(borgo_dopo_tre(), "il borgo entrato dopo le compere non da' scorte negative");
    static_assert(scorte(nuova(NOTTE, 0), 0) == 5 && scorte(nuova(NOTTE, 0), 1) == 3,
                  "nella notte altre due Crescia");

    // i quattro esiti
    static_assert(prova(nuova(DIGIUNO, PREZZO[0] - 1), 0) == Esito::POCHI_DENARI, "pochi denari");
    static_assert(prova(nuova(DIGIUNO, PREZZO[0]), 0) == Esito::COMPRATO, "denari giusti");

    constexpr bool compera()
    {
        GameState p = nuova(DIGIUNO, 100);
        int crescia = p.oggetti[int(battaglia::OggettoId::CRESCIA)];
        int biscotti = p.oggetti[int(battaglia::OggettoId::BISCOTTI)];

        if(compra(p, 0) != Esito::COMPRATO || compra(p, 1) != Esito::COMPRATO)
        {
            return false;
        }

        return p.denari == 100 - PREZZO[0] - PREZZO[1] && comprate(p, 0) == 1 && comprate(p, 1) == 1 &&
               restano(p, 0) == 2 && restano(p, 1) == 2 &&
               p.oggetti[int(battaglia::OggettoId::CRESCIA)] == crescia + 1 &&
               p.oggetti[int(battaglia::OggettoId::BISCOTTI)] == biscotti + 1;
    }

    static_assert(compera(), "la compera toglie i denari, da' l'oggetto e conta la scorta");

    constexpr bool finite_e_notte()
    {
        GameState p = nuova(DIGIUNO, 9000);

        for(int i = 0; i < 3; ++i)
        {
            if(compra(p, 1) != Esito::COMPRATO)
            {
                return false;
            }
        }

        if(compra(p, 1) != Esito::FINITE || p.denari != 9000 - 3 * PREZZO[1])
        {
            return false;
        }

        // nella notte: delle Crescia ne restano cinque, i Biscotti restano finiti
        storia::accendi(p, NOTTE);

        if(restano(p, 0) != 5 || restano(p, 1) != 0 || ! ha_merce(p))
        {
            return false;
        }

        p.oggetti[int(battaglia::OggettoId::CRESCIA)] = 0;     // la bisaccia ne tiene cinque

        for(int i = 0; i < 5; ++i)
        {
            if(compra(p, 0) != Esito::COMPRATO)
            {
                return false;
            }
        }

        return ! ha_merce(p) && compra(p, 0) == Esito::FINITE;
    }

    static_assert(finite_e_notte(), "le scorte finiscono, e la notte aggiunge solo Crescia");

    constexpr bool piena()
    {
        GameState p = nuova(NOTTE, 9000);
        p.oggetti[int(battaglia::OggettoId::CRESCIA)] = uint8_t(battaglia::OGGETTI[0].massimo);
        return prova(p, 0) == Esito::PIENO && compra(p, 0) == Esito::PIENO && p.denari == 9000;
    }

    static_assert(piena(), "nella bisaccia piena non se ne compra");

    // il Venditore e' l'NPC delle Logge, quello dell'indizio di Q-SP01
    static_assert(storia::NPC_AMBIENTE[NPC_VENDITORE].area == int8_t(mondo::AreaId::PIAZZA_QUARANTA_MARTIRI) &&
                  storia::INDIZIO[1].npc == NPC_VENDITORE && storia::INDIZIO[1].bandiera == storia::INDIZIO_VENDITORE,
                  "NPC_VENDITORE non e' il Venditore delle Logge");

    // i contatori da 4 bit bastano per tutte le scorte
    static_assert(3 + 2 < 16, "le scorte stanno nei 4 bit");
}

}
