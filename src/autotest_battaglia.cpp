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
            battaglia::Firma f = battaglia::gioca(a.incontro, a.seme);

            if(f.hash != a.hash || f.eventi != a.eventi || f.round != a.round || f.esito != a.esito ||
               f.tipi != a.tipi || f.traboccato)
            {
                battaglia_diversa_dal_mirror(i);
            }
        }

        return battaglia::ATTESE_CONTEGGIO;
    }

    static_assert(verifica_battaglie() > 0, "autotest della battaglia");
}

}
