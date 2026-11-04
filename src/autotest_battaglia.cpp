// Autotest della battaglia a tempo di compilazione: ogni incontro, ogni seme, la firma della
// sequenza di eventi del C++ (include/battaglia.h) deve essere quella del mirror Python
// (include/battaglia_attese.h, scritto da tools/battaglia_mirror.py). Se una differisce, la ROM non
// compila, sul nome di battaglia_diversa_dal_mirror(indice).

#include "battaglia_attese.h"

namespace gubbio
{

void battaglia_diversa_dal_mirror(int indice);

namespace
{
    consteval int verifica_battaglie()
    {
        for(int i = 0; i < battaglia::ATTESE_CONTEGGIO; ++i)
        {
            const battaglia::Attesa& a = battaglia::ATTESE[i];
            battaglia::Firma f = battaglia::gioca(a.incontro, a.seme, a.pilota_debole);

            if(f.hash != a.hash || f.eventi != a.eventi || f.round != a.round || f.esito != a.esito ||
               f.tipi != a.tipi || f.traboccato)
            {
                battaglia_diversa_dal_mirror(i);
            }
        }

        return battaglia::ATTESE_CONTEGGIO;
    }

    static_assert(verifica_battaglie() > 0, "autotest della battaglia");

    // Ogni incontro, anche quelli di F10 (i Guerrieri della Roccia, la guardia della fornace, l'infiltrato), ha le
    // sue 100 firme confrontate: 50 semi per due piloti.
    consteval bool ogni_incontro_confrontato()
    {
        for(int incontro = 0; incontro < battaglia::INCONTRI; ++incontro)
        {
            int quante = 0;

            for(int i = 0; i < battaglia::ATTESE_CONTEGGIO; ++i)
            {
                quante += battaglia::ATTESE[i].incontro == incontro;
            }

            if(quante != 100)
            {
                return false;
            }
        }

        return battaglia::ATTESE_CONTEGGIO == 100 * battaglia::INCONTRI;
    }

    static_assert(ogni_incontro_confrontato(), "un incontro non ha le sue firme del mirror");

    // Negativa: una firma attesa alterata (un nemico di F10) non torna con il C++.
    consteval bool firma_torna(const battaglia::Attesa& a)
    {
        battaglia::Firma f = battaglia::gioca(a.incontro, a.seme, a.pilota_debole);
        return f.hash == a.hash && f.eventi == a.eventi && f.round == a.round && f.esito == a.esito && f.tipi == a.tipi;
    }

    consteval battaglia::Attesa alterata(int i)
    {
        battaglia::Attesa a = battaglia::ATTESE[i];
        a.hash ^= 1u;
        return a;
    }

    static_assert(battaglia::ATTESE[600].incontro == battaglia::INCONTRO_INFILTRATO && firma_torna(battaglia::ATTESE[600]) &&
                  ! firma_torna(alterata(600)) && battaglia::ATTESE[400].incontro == battaglia::INCONTRO_GUERRIERI &&
                  ! firma_torna(alterata(400)), "negativa: una firma alterata torna lo stesso");

    // Il duello con Corrado con uno scudo in meno (Q-SM01 o RUFINO_ASCOLTATO): le firme del C++ con
    // scudi_in_meno = 1 sono quelle del mirror con la stessa manopola.
    void scudo_in_meno_diverso_dal_mirror(int indice);

    consteval int verifica_scudo_in_meno()
    {
        for(int i = 0; i < battaglia::ATTESE_SCUDO_IN_MENO_CONTEGGIO; ++i)
        {
            const battaglia::Attesa& a = battaglia::ATTESE_SCUDO_IN_MENO[i];
            battaglia::Firma f = battaglia::gioca(a.incontro, a.seme, a.pilota_debole, 1);

            if(f.hash != a.hash || f.eventi != a.eventi || f.round != a.round || f.esito != a.esito ||
               f.tipi != a.tipi || f.traboccato)
            {
                scudo_in_meno_diverso_dal_mirror(i);
            }
        }

        return battaglia::ATTESE_SCUDO_IN_MENO_CONTEGGIO;
    }

    static_assert(verifica_scudo_in_meno() == 100, "autotest dello scudo in meno di Corrado");

    // Negativa: lo scudo in meno cambia davvero la battaglia (stesso seme, firma diversa), e senza
    // la manopola la firma e' quella delle 400 di sempre.
    consteval bool scudo_in_meno_conta()
    {
        int diverse = 0;

        for(uint32_t seme = 1; seme <= 50; ++seme)
        {
            diverse += battaglia::gioca(2, seme, false, 1).hash != battaglia::gioca(2, seme, false).hash;
        }

        return diverse > 0 && battaglia::gioca(2, 7, false, 0).hash == battaglia::gioca(2, 7, false).hash;
    }

    static_assert(scudo_in_meno_conta(), "lo scudo in meno di Corrado non cambia la battaglia");

    // Gli scudi in meno non vanno mai sotto zero, e toccano solo i nemici.
    consteval bool scudi_di_corrado(int in_meno, int atteso)
    {
        battaglia::Battaglia b(2, 1);
        b.ricomincia(2, 1, false, nullptr, battaglia::TUTTI_PRESENTI, in_meno);
        return b.nemico(0).scudo == atteso && b.nemico(0).scudo_max == atteso && b.eroe(0).scudo == 0;
    }

    static_assert(battaglia::NEMICI[int(battaglia::NemicoId::CORRADO_DI_SPOLETO)].statistiche.scudo == 4 &&
                  scudi_di_corrado(0, 4) && scudi_di_corrado(1, 3) && scudi_di_corrado(9, 0),
                  "gli scudi di Corrado");
    static_assert(! scudi_di_corrado(1, 4), "negativa: con uno scudo in meno Corrado non ne ha 4");
}

}
