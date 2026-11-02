#include "bn_core.h"
#include "bn_log.h"

#include "battaglia_attese.h"
#include "schermate.h"

namespace gubbio
{

namespace
{
    // Una sola battaglia, riavviata sul posto per ogni incontro e seme: sta in EWRAM, non sullo stack.
    constinit BN_DATA_EWRAM battaglia::Battaglia g_battaglia(0, 1);
}

void prova_battaglia()
{
    int uguali = 0;
    int diverse = 0;
    uint32_t tipi = 0;

    for(int i = 0; i < battaglia::ATTESE_CONTEGGIO; ++i)
    {
        const battaglia::Attesa& a = battaglia::ATTESE[i];
        g_battaglia.ricomincia(a.incontro, a.seme, a.pilota_debole);
        battaglia::Firma f = g_battaglia.gioca();
        bool uguale = f.hash == a.hash && f.eventi == a.eventi && f.round == a.round && f.esito == a.esito &&
                f.tipi == a.tipi && ! f.traboccato;
        uguali += uguale ? 1 : 0;
        diverse += uguale ? 0 : 1;
        tipi |= f.tipi;
        BN_LOG("BATTAGLIA ", a.incontro, " ", int(a.seme), " ", int(a.pilota_debole), " ", f.hash, " ", f.eventi, " ", f.round, " ",
               int(f.esito), uguale ? " OK" : " DIVERSA");
        bn::core::update();
    }

    bool copertura = tipi == (1u << int(battaglia::EventKind::COUNT)) - 1;
    BN_LOG("Battaglie: ", uguali, " uguali al mirror, ", diverse, " diverse, tipi ", tipi,
           copertura ? ", copertura completa" : ", copertura INCOMPLETA");
}

}
