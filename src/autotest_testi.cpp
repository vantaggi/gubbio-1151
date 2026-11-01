// Autotest a tempo di compilazione: se un testo, una tabella generata o il formattatore numerico
// sono sbagliati, la ROM non compila. Il primo errore ferma la compilazione su una funzione
// non constexpr il cui nome dice il tipo di controllo fallito.

#include "formatta.h"
#include "testo_autotest.h"

namespace gubbio
{

void autotest_testi_fallito(int errore, int testo, int riga, int passo);
void autotest_formatta_fallito(int valore);

namespace
{
    consteval int verifica_testi()
    {
        testo::EsitoAutotest esito = testo::autotest_testi();

        if(esito.errore != testo::ErroreAutotest::NESSUNO)
        {
            autotest_testi_fallito(int(esito.errore), esito.testo, esito.riga, esito.passo);
        }

        return esito.passi;
    }

    consteval int verifica_formatta()
    {
        int esito = autotest_formatta();

        if(esito != 65536)
        {
            autotest_formatta_fallito(-1 - esito);
        }

        return esito;
    }

    static_assert(verifica_testi() > 0, "autotest dei testi");
    static_assert(verifica_formatta() == 65536, "formatta_intero su tutto int16");
}

}
