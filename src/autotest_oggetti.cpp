// Autotest dei consumabili in battaglia a tempo di compilazione (OGGETTI in battaglia_dati.h,
// TipoComando::OGGETTO in battaglia.h): la Crescia cura un alleato senza superare i suoi PV massimi,
// i Biscotti purificano, un oggetto non ancora usabile non fa nulla. Il pilota non usa oggetti: le
// battaglie del mirror non cambiano.

#include "battaglia.h"

namespace gubbio
{

namespace
{
    using namespace battaglia;

    struct Esito1
    {
        bool trovato = false;
        int bersaglio = -1;
        int quantita = 0;
        int pv_dopo = 0;
        int pv_prima = 0;
        int pv_max = 0;
        int cure = 0;
        int purifiche = 0;
    };

    // Gioca col pilota finche' un Santo e' ferito, poi al round dopo Ubaldo usa l'oggetto su di lui.
    consteval Esito1 usa(OggettoId oggetto, uint32_t seme)
    {
        Battaglia b(0, seme);
        Esito1 r;

        for(int round = 0; round < 10; ++round)
        {
            b.avanza();     // SCELTA_COMANDI
            int ferito = -1;

            for(int e = 0; e < EROI; ++e)
            {
                if(b.eroe(e).vivo() && b.eroe(e).pv < b.eroe(e).pv_max && ferito < 0)
                {
                    ferito = e;
                }
            }

            if(ferito >= 0 && b.eroe(UBALDO).vivo())
            {
                Comando c;
                c.tipo = TipoComando::OGGETTO;
                c.bersaglio = ferito;
                c.oggetto = oggetto;
                b.imposta_comando(UBALDO, c);
                r.bersaglio = ferito;
                r.pv_max = b.eroe(ferito).pv_max;
            }

            b.avanza();     // CODA
            b.avanza();     // ESECUZIONE

            for(int i = 0; i < b.eventi_round(); ++i)
            {
                const Evento& e = b.evento(i);

                if(e.kind == EventKind::CURA)
                {
                    r.trovato = true;
                    r.quantita = e.quantita;
                    r.pv_dopo = e.pv_dopo;
                    r.cure += 1;
                }

                if(e.kind == EventKind::PURIFICA)
                {
                    r.purifiche += 1;
                }
            }

            b.avanza();     // FINE_ROUND

            if(! b.avanza() || r.bersaglio >= 0)   // ESITO
            {
                break;
            }
        }

        return r;
    }

    constexpr Esito1 CRESCIA = usa(OggettoId::CRESCIA, 1);

    static_assert(CRESCIA.trovato && CRESCIA.cure == 1, "la Crescia non ha curato");
    static_assert(CRESCIA.quantita > 0 && CRESCIA.quantita <= OGGETTI[int(OggettoId::CRESCIA)].cura_pv,
                  "la Crescia cura al massimo i suoi PV");
    static_assert(CRESCIA.pv_dopo <= CRESCIA.pv_max, "la Crescia porta oltre i PV massimi");
    static_assert(usa(OggettoId::BISCOTTI, 1).purifiche == 1 && usa(OggettoId::BISCOTTI, 1).cure == 0,
                  "i Biscotti non purificano");

    // Negativa: la Crescia sotto la Cenere non e' ancora usabile: nessun evento, nulla si consuma.
    static_assert(! OGGETTI[int(OggettoId::CENERE)].usabile && usa(OggettoId::CENERE, 1).cure == 0 &&
                  usa(OggettoId::CENERE, 1).purifiche == 0, "un oggetto non usabile ha fatto qualcosa");

    // I Biscotti sono un consumabile rapido: la loro priorita' supera quella del Bastione.
    static_assert(OGGETTI[int(OggettoId::BISCOTTI)].priorita > ABILITA[int(AbilitaId::BASTIONE_AZZURRO)].priorita,
                  "i Biscotti devono precedere il Bastione");

    // Il Baccala' restituisce tutto il Fervore: se ne porta uno solo (dal prototipo).
    static_assert(OGGETTI[int(OggettoId::BACCALA)].massimo == 1, "il Baccala' si porta uno solo");
}

}
