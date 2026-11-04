// Autotest delle animazioni della battaglia a tempo di compilazione (include/animazione_battaglia.h).
//
// Le prove: il colpo ha l'ordine giusto (passo, anticipazione tenuta, colpo, fermo, ritorno), chi agisce
// torna esattamente al suo posto e chi subisce pure; il lampo bianco cade solo nell'impatto; il numero
// compare solo dopo l'impatto e finisce fermo; nell'IMMUNE nessun lampo e nessun numero; un nemico che
// cade sparisce, un eroe resta in ginocchio; ogni effetto ha un fotogramma valido.
// Le negative: un colpo senza fermo (il bersaglio non e' piu' COLPITO durante il fermo) e un ritorno che
// non arriva a zero vengono riconosciuti dalle stesse prove.
// Se una prova non regge, la ROM non compila.

#include "animazione_battaglia.h"

namespace gubbio
{

namespace
{
    using battaglia::Gesto;
    using namespace battaglia::animazione;

    constexpr Stile NORMALE = {};
    constexpr Stile FORTE = { Effetto::RAGGIO, true, false };

    // L'ordine del colpo: le pose di chi agisce passano per ANTICIPA e poi per COLPO, mai al contrario.
    consteval bool ordine_del_colpo(const Stile& s)
    {
        int prima_anticipa = -1;
        int primo_colpo = -1;

        for(int f = 0; f < durata(Gesto::COLPO, s); ++f)
        {
            Posa p = quadro(Gesto::COLPO, f, s).posa_attore;

            if(p == Posa::ANTICIPA && prima_anticipa < 0)
            {
                prima_anticipa = f;
            }

            if(p == Posa::COLPO && primo_colpo < 0)
            {
                primo_colpo = f;
            }
        }

        // l'anticipazione e' tenuta almeno 10 vblank, il colpo arriva dopo
        return prima_anticipa == CORSA && primo_colpo == inizio_scatto() && primo_colpo - prima_anticipa >= 10;
    }

    // Il fermo: per tutto il fermo chi subisce e' COLPITO e non torna indietro; chi colpisce non si muove.
    template<typename Q>
    consteval bool fermo_tenuto(const Stile& s, Q q)
    {
        int x = q(impatto(s), s).avanti_attore;

        for(int f = impatto(s); f < impatto(s) + fermo(s); ++f)
        {
            Quadro k = q(f, s);

            if(k.posa_bersaglio != Posa::COLPITO || k.indietro_bersaglio != RINCULO_PIXEL || k.avanti_attore != x)
            {
                return false;
            }
        }

        return true;
    }

    constexpr Quadro colpo_vero(int f, const Stile& s)
    {
        return quadro(Gesto::COLPO, f, s);
    }

    // la negativa: un colpo senza fermo, il bersaglio si riprende subito
    constexpr Quadro colpo_senza_fermo(int f, const Stile& s)
    {
        Quadro q = quadro(Gesto::COLPO, f, s);

        if(f > impatto())
        {
            q.posa_bersaglio = Posa::LIBERA;
            q.indietro_bersaglio = 0;
        }

        return q;
    }

    // Tutti tornano a posto: l'ultimo quadro di ogni gesto lascia tutti dove stavano, senza lampi ne' tremiti.
    template<typename Q>
    consteval bool tutti_a_posto(Gesto g, const Stile& s, Q q)
    {
        Quadro k = q(g, durata(g, s) - 1, s);
        return k.avanti_attore == 0 && k.indietro_bersaglio == 0 && k.scossa == 0 && k.lampo_attore == Lampo::NESSUNO &&
               k.lampo_bersaglio == Lampo::NESSUNO;
    }

    constexpr Quadro quadro_vero(Gesto g, int f, const Stile& s)
    {
        return quadro(g, f, s);
    }

    // la negativa: chi colpisce resta a meta' strada
    constexpr Quadro ritorno_monco(Gesto g, int f, const Stile& s)
    {
        Quadro q = quadro(g, f, s);
        q.avanti_attore += g == Gesto::COLPO ? 2 : 0;
        return q;
    }

    // Il lampo bianco solo nel fermo, il numero solo dopo l'impatto e alla fine fermo.
    consteval bool lampo_e_numero(const Stile& s)
    {
        for(int f = 0; f < durata(Gesto::COLPO, s); ++f)
        {
            Quadro q = quadro(Gesto::COLPO, f, s);
            bool nel_fermo = f >= impatto(s) && f < impatto(s) + fermo(s);

            if(q.lampo_bersaglio == Lampo::BIANCO && ! nel_fermo)
            {
                return false;
            }

            if(q.numero != (f >= impatto(s)))
            {
                return false;
            }
        }

        return quadro(Gesto::COLPO, durata(Gesto::COLPO, s) - 1, s).su_numero == 0 &&
               quadro(Gesto::COLPO, impatto(s), s).lampo_bersaglio == Lampo::BIANCO;
    }

    // L'IMMUNE: il ferro rimbalza, nessun lampo e nessun numero sul bersaglio.
    consteval bool immune_senza_danno()
    {
        bool rimbalza = false;

        for(int f = 0; f < durata(Gesto::IMMUNE); ++f)
        {
            Quadro q = quadro(Gesto::IMMUNE, f);

            if(q.numero || q.lampo_bersaglio != Lampo::NESSUNO || q.posa_bersaglio != Posa::LIBERA)
            {
                return false;
            }

            rimbalza = rimbalza || q.posa_attore == Posa::COLPITO;
        }

        return rimbalza;
    }

    // La caduta: un nemico alla fine non si vede, un eroe si'.
    consteval bool caduta()
    {
        Stile nemico = {};
        Stile eroe = {};
        eroe.resta_a_terra = true;
        int ultimo = durata(Gesto::CADUTA) - 1;
        return ! quadro(Gesto::CADUTA, ultimo, nemico).bersaglio_visibile && quadro(Gesto::CADUTA, ultimo, eroe).bersaglio_visibile &&
               quadro(Gesto::CADUTA, 0, nemico).posa_bersaglio == Posa::CADUTO;
    }

    // Ogni fotogramma di effetto e' dentro i suoi quattro, per ogni gesto e ogni istante.
    consteval bool effetti_validi()
    {
        constexpr Gesto GESTI[] = { Gesto::NESSUNO, Gesto::COLPO, Gesto::IMMUNE, Gesto::SCUDO_ROTTO, Gesto::PARATA,
                                    Gesto::POTERE, Gesto::USTIONE, Gesto::CADUTA, Gesto::CURA };

        for(Gesto g : GESTI)
        {
            constexpr Stile STILI[] = { NORMALE, FORTE };

            for(const Stile& s : STILI)
            {
                for(int f = 0; f < durata(g, s); ++f)
                {
                    Quadro q = quadro(g, f, s);

                    if(q.fotogramma_attore < 0 || q.fotogramma_attore >= FOTOGRAMMI_EFFETTO ||
                       q.fotogramma_bersaglio < 0 || q.fotogramma_bersaglio >= FOTOGRAMMI_EFFETTO ||
                       q.scossa < -3 || q.scossa > 3)
                    {
                        return false;
                    }
                }

                if(! tutti_a_posto(g, s, quadro_vero))
                {
                    return false;
                }
            }
        }

        return true;
    }

    // Il colpo forte dura di piu' e trema di piu'; e un colpo intero sta in meno di un secondo e mezzo.
    consteval bool forte_piu_pesante()
    {
        int tremito_normale = 0;
        int tremito_forte = 0;

        for(int f = 0; f < durata(Gesto::COLPO, FORTE); ++f)
        {
            int n = quadro(Gesto::COLPO, f, NORMALE).scossa;
            int k = quadro(Gesto::COLPO, f, FORTE).scossa;
            tremito_normale = n > tremito_normale ? n : tremito_normale;
            tremito_forte = k > tremito_forte ? k : tremito_forte;
        }

        return durata(Gesto::COLPO, FORTE) > durata(Gesto::COLPO, NORMALE) && tremito_forte > tremito_normale &&
               durata(Gesto::COLPO, FORTE) <= 90;
    }

    static_assert(ordine_del_colpo(NORMALE) && ordine_del_colpo(FORTE));
    static_assert(fermo_tenuto(NORMALE, colpo_vero) && fermo_tenuto(FORTE, colpo_vero));
    static_assert(! fermo_tenuto(NORMALE, colpo_senza_fermo));
    static_assert(tutti_a_posto(Gesto::COLPO, NORMALE, quadro_vero) && tutti_a_posto(Gesto::IMMUNE, NORMALE, quadro_vero));
    static_assert(! tutti_a_posto(Gesto::COLPO, NORMALE, ritorno_monco));
    static_assert(lampo_e_numero(NORMALE) && lampo_e_numero(FORTE));
    static_assert(immune_senza_danno());
    static_assert(caduta());
    static_assert(effetti_validi());
    static_assert(forte_piu_pesante());
    static_assert(respiro(0, 0) == Posa::RIPOSO && respiro(30, 0) == Posa::RESPIRO && respiro(0, 0) != respiro(0, 2));
    static_assert(int(Effetto::CONTEGGIO) - 1 == 9 && POSE_DISEGNATE == 7);

    // Il colpo da lontano: il proiettile vola per tutto il VOLO, l'impatto arriva quando arriva lui, l'effetto
    // sul bersaglio parte solo allora; il resto del colpo (fermo, ritorno) e' quello di sempre.
    consteval bool proiettile_in_volo()
    {
        Stile tiro = {};
        tiro.proiettile = Effetto::DARDO;
        int voli = 0;

        for(int f = 0; f < durata(Gesto::COLPO, tiro); ++f)
        {
            Quadro q = quadro(Gesto::COLPO, f, tiro);
            bool in_volo = f >= inizio_scatto() && f < impatto(tiro);

            if(in_volo != (q.volo >= 0) || (in_volo && q.effetto_attore != Effetto::DARDO) ||
               (in_volo && q.effetto_bersaglio != Effetto::NESSUNO))
            {
                return false;
            }

            voli += in_volo;
        }

        return voli == VOLO && impatto(tiro) == impatto() + VOLO - SCATTO &&
               quadro(Gesto::COLPO, impatto(tiro), tiro).effetto_bersaglio != Effetto::NESSUNO &&
               tutti_a_posto(Gesto::COLPO, tiro, quadro_vero) && lampo_e_numero(tiro);
    }

    static_assert(proiettile_in_volo());
    // la negativa: un colpo da vicino non ha proiettile
    static_assert(scatto() == SCATTO && quadro(Gesto::COLPO, inizio_scatto()).volo < 0);
}

}
