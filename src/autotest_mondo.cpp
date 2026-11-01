// Autotest del mondo a tempo di compilazione: se una camminata dell'anello o di un arco fallisce,
// la ROM non compila, sul nome di autotest_mondo_fallito(errore, area, varco).

#include "mondo_autotest.h"

namespace gubbio
{

void autotest_mondo_fallito(int errore, int area, int varco);

namespace
{
    consteval int verifica_mondo()
    {
        mondo::EsitoMondo esito = mondo::autotest_mondo();

        if(esito.errore != mondo::ErroreMondo::NESSUNO)
        {
            autotest_mondo_fallito(int(esito.errore), esito.area, esito.varco);
        }

        return esito.archi;
    }

    static_assert(verifica_mondo() > 0, "autotest del mondo");
}

}
