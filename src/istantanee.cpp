#include "bn_core.h"
#include "bn_log.h"

#include "esplorazione.h"
#include "schermate.h"

namespace gubbio
{

namespace
{
    constexpr int FRAME_PER_ASSESTARSI = 60;   // dissolvenza d'entrata finita, etichetta in vista
    constexpr int FRAME_PER_LO_SCATTO = 60;    // tempo per tools/istantanee.py di premere lo scatto

    void aspetta(Esplorazione& esplorazione, int frame)
    {
        for(int i = 0; i < frame; ++i)
        {
            esplorazione.aggiorna();
            bn::core::update();
        }
    }
}

void istantanee(Esplorazione& esplorazione)
{
    for(int a = 0; a < mondo::AREE_CONTEGGIO; ++a)
    {
        esplorazione.entra(mondo::AreaId(a), 0);
        aspetta(esplorazione, FRAME_PER_ASSESTARSI);
        BN_LOG("Istantanea ", a);
        aspetta(esplorazione, FRAME_PER_LO_SCATTO);
    }

    BN_LOG("Istantanee finite");
}

}
