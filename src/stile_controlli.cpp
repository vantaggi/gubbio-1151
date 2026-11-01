// Controlli a tempo di compilazione sugli header generati da stile/esporta_cpp.py.
// Non produce codice: se i dati di stile escono dalle regole della Guida, la ROM non compila.

#include "stile/cornice.h"
#include "stile/font.h"
#include "stile/palette.h"
#include "stile/pose.h"

namespace
{
    using namespace gubbio::stile;

    static_assert(COLORI_PALETTE == 42, "scelta 3: 42 colori in 9 rampe");
    static_assert(PALETTE_GIORNO[0] < 0x8000 && PALETTE_NOTTE[0] < 0x8000, "parole BGR555 a 15 bit");

    static_assert(FONT_ALTEZZA == 10 && FONT_INTERLINEA == 10, "scelta 8: interlinea 10");
    static_assert(trova_glifo(U'à')->larghezza > 0, "accenti italiani");
    static_assert(trova_glifo(U'«')->larghezza > 0 && trova_glifo(U'»')->larghezza > 0, "virgolette basse");
    static_assert(trova_glifo(U'’') == trova_glifo(U'\''), "apostrofo curvo = apostrofo");

    static_assert(CORNICE_PALETTE[0] == 0, "indice 0 trasparente");
    static_assert(DIALOGO_RIGHE_TESTO_MAX == 3, "scelta 9: dialogo in 3 righe al massimo");

    constexpr int durata(const Fotogramma* f, int n)
    {
        int totale = 0;

        for(int i = 0; i < n; ++i)
        {
            totale += f[i].vblank;
        }

        return totale;
    }

    static_assert(durata(CAMMINATA, 6) == 36, "scelta 11: camminata 6 x 100 ms");
    static_assert(ATTACCO[2].vblank == 3, "scelta 11: colpo di 3 vblank");
}
