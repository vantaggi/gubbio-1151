// Autotest della storia a tempo di compilazione (include/storia_logica.h, include/storia.h generato
// dal copione v1): il runner gira dalla prima scena ai titoli di coda senza camminare, visita ogni
// scena una volta sola e arriva a CRONACA_V1_FINITA. Se una scena resta fuori, la ROM non compila.
// Negativa: una scena che chiede una bandiera che nessuno accende resta non visitata.

#include "storia_logica.h"

namespace gubbio
{

namespace
{
    using namespace storia;

    consteval bool tutta_la_storia()
    {
        GameState p = {};
        int visitate = gioca_tutta(p);

        for(int k = 0; k < SCENE; ++k)
        {
            if(! fatta(p, k))
            {
                return false;
            }
        }

        return visitate == SCENE && accesa(p, Bandiera::CRONACA_V1_FINITA) && accesa(p, Bandiera::CORRADO_SCONFITTO);
    }

    static_assert(tutta_la_storia(), "il runner della storia non visita ogni scena fino ai titoli di coda");

    consteval bool stesso_codice(const char* a, const char* b)
    {
        int i = 0;

        while(a[i] && b[i] && a[i] == b[i])
        {
            ++i;
        }

        return a[i] == b[i];
    }

    // L'ordine: il prologo prima di tutto, l'ultimatum prima di Antonio, Corrado prima del rientro.
    consteval int ordine(const char* a, const char* b)
    {
        GameState p = {};
        int pos_a = -1;
        int pos_b = -1;
        int passo = 0;
        bool avanti = true;

        while(avanti)
        {
            avanti = false;

            for(int area = NESSUNA_AREA; area < mondo::AREE_CONTEGGIO && ! avanti; ++area)
            {
                int k = prossima_scena(p, area);

                if(k >= 0)
                {
                    pos_a = stesso_codice(SCENA[k].codice, a) ? passo : pos_a;
                    pos_b = stesso_codice(SCENA[k].codice, b) ? passo : pos_b;
                    chiudi_scena(p, k);
                    ++passo;
                    avanti = true;
                }
            }
        }

        return pos_a >= 0 && pos_b >= 0 && pos_a < pos_b ? 1 : 0;
    }

    static_assert(ordine("P-02", "A1-01") && ordine("A1-01", "A1-04") && ordine("B-04", "B-05") &&
                  ordine("E-01", "E-02"), "le scene non vengono nell'ordine del copione");
    static_assert(! ordine("E-02", "P-01"), "la negativa dell'ordine non regge");

    // Negativa: una copia della tabella in cui A1-06 chiede una bandiera che nessuno accende
    // (CRONACA_V1_FINITA, che arriva solo alla fine): da li' in poi niente si visita.
    struct Tabella
    {
        Scena scene[SCENE];
    };

    consteval Tabella guasta()
    {
        Tabella t = {};

        for(int k = 0; k < SCENE; ++k)
        {
            t.scene[k] = SCENA[k];

            if(stesso_codice(SCENA[k].codice, "A1-06"))
            {
                t.scene[k].richieste |= uint64_t(1) << int(Bandiera::CRONACA_V1_FINITA);
            }
        }

        return t;
    }

    consteval int visitate_con_la_tabella_guasta()
    {
        Tabella t = guasta();
        GameState p = {};
        return gioca_tutta(p, t.scene, SCENE);
    }

    static_assert(visitate_con_la_tabella_guasta() < SCENE, "la negativa della storia non regge");

    // Le fasi degli NPC.
    consteval bool fasi()
    {
        GameState p = {};

        if(fase_npc(p) != Fase::ULTIMATUM)
        {
            return false;
        }

        accendi(p, uint64_t(1) << int(Bandiera::CITTA_IN_DIGIUNO));

        if(fase_npc(p) != Fase::DIGIUNO)
        {
            return false;
        }

        accendi(p, uint64_t(1) << int(Bandiera::RIENTRO_PORTA_METAURO));
        return fase_npc(p) == Fase::NOTTE;
    }

    static_assert(fasi(), "le fasi degli NPC");
}

}
