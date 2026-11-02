// Autotest del lettore delle cutscene a tempo di compilazione (include/regia_logica.h): nessuna
// cutscene oltre i 60 s, senza tasti si arriva in fondo nel suo tempo esatto, Start salta tutto al
// primo frame, A avanza il testo (e accorcia), la dissolvenza c'e' solo all'inizio e alla fine, gli
// stacchi sono netti, il primo piano scorre piu' veloce di quelli dietro. Ogni prova ha la negativa.

#include "regia_logica.h"

namespace gubbio
{

namespace
{
    using namespace regia;

    consteval bool durate_entro_il_minuto()
    {
        for(int c = 0; c < CUTSCENE; ++c)
        {
            int somma = 0;

            for(int i = 0; i < CUTSCENE_DATI[c].inquadrature; ++i)
            {
                somma += INQUADRATURA[CUTSCENE_DATI[c].prima_inquadratura + i].frame;
            }

            if(somma != CUTSCENE_DATI[c].frame || somma > SECONDI_MAX * FRAME_PER_SECONDO)
            {
                return false;
            }
        }

        return true;
    }

    static_assert(durate_entro_il_minuto(), "una cutscene supera i 60 s");

    // Quanti frame dura con una sequenza di tasti: A ogni 'ogni_a' frame (0 mai), Start al frame 'start'.
    consteval int dura(int cutscene, int ogni_a, int start)
    {
        Lettore l;
        l.inizia(cutscene);
        int f = 0;

        while(l.passo(ogni_a > 0 && f % ogni_a == ogni_a - 1, f == start))
        {
            ++f;
        }

        return f + 1;
    }

    static_assert(dura(0, 0, -1) == CUTSCENE_DATI[0].frame, "senza tasti la cutscene non dura il suo tempo");
    static_assert(dura(0, 0, 0) == 1, "Start non salta tutto al primo frame");
    static_assert(dura(0, 30, -1) < CUTSCENE_DATI[0].frame, "A non porta avanti il testo");
    // negativa: Start premuto a meta' non arriva in fondo
    static_assert(dura(0, 0, 100) == 101 && dura(0, 0, 100) < dura(0, 0, -1), "la negativa del salto non regge");

    // La dissolvenza solo all'inizio e alla fine; stacchi netti nel mezzo (al cambio d'inquadratura
    // il buio e' 0). Il primo piano scorre piu' veloce dei piani dietro.
    consteval bool luce_e_stacchi()
    {
        Lettore l;
        l.inizia(0);

        if(l.buio() != FRAME_DISSOLVENZA)
        {
            return false;
        }

        int stacchi = 0;

        while(l.passo(false, false))
        {
            if(l.stacco())
            {
                ++stacchi;

                if(l.buio() != 0)
                {
                    return false;
                }
            }

            if(l.indice_inquadratura() > 0 && l.indice_inquadratura() < CUTSCENE_DATI[0].inquadrature - 1 && l.buio() != 0)
            {
                return false;
            }
        }

        return stacchi == CUTSCENE_DATI[0].inquadrature - 1;
    }

    static_assert(luce_e_stacchi(), "dissolvenze nel mezzo o stacchi mancanti");

    consteval bool parallasse()
    {
        Lettore l;
        l.inizia(0);

        for(int f = 0; f < 120; ++f)
        {
            l.passo(false, false);
        }

        // 2 s a 12 px/s: il primo piano e' scorso di 24 px, gli altri di 18, 12 e 6
        return l.scorrimento(3, 4) == 24 && l.scorrimento(2, 4) == 18 && l.scorrimento(1, 4) == 12 &&
               l.scorrimento(0, 4) == 6;
    }

    static_assert(parallasse(), "la parallasse non va a 1/4, 1/2, 3/4 e 1");

    // Le cutscene viste: segnata una, solo quella; una vista non riparte da sola. Anche oltre l'ottava
    // (il secondo byte).
    consteval bool viste()
    {
        GameState p = {};
        segna_vista(p, 0);
        segna_vista(p, 9);
        return vista(p, 0) && ! vista(p, 1) && vista(p, 9) && ! vista(p, 8) && p.cutscene_viste[1] == 2;
    }

    static_assert(viste(), "le cutscene viste");

    // Il colpo (C2P): a FRAME_COLPO il lampo pieno e la scossa, poi si spengono; prima niente. In
    // un'inquadratura senza colpo (C0) mai.
    consteval bool colpo(int cutscene)
    {
        Lettore l;
        l.inizia(cutscene);
        bool lampo = false;
        bool scossa = false;

        for(int f = 0; f < CUTSCENE_DATI[cutscene].frame - 1; ++f)
        {
            if(f < FRAME_COLPO && (l.lampo() || l.scossa()))
            {
                return false;
            }

            lampo = lampo || (f == FRAME_COLPO && l.lampo() == FRAME_LAMPO);
            scossa = scossa || (f > FRAME_COLPO && l.scossa() != 0);

            if(f >= FRAME_COLPO + FRAME_SCOSSA && (l.lampo() || l.scossa()))
            {
                return false;
            }

            l.passo(false, false);
        }

        return lampo && scossa;
    }

    static_assert(colpo(int(CutsceneId::C2P)), "il colpo del pastorale: niente lampo o scossa al momento giusto");
    static_assert(! colpo(0), "la negativa del colpo: C0 non ha colpo");

    // Il passo dei fanti: la posa cambia ogni FRAME_PASSO frame.
    consteval bool passo()
    {
        Lettore l;
        l.inizia(int(CutsceneId::C2));
        int prima = l.posa();

        for(int f = 0; f < FRAME_PASSO; ++f)
        {
            l.passo(false, false);
        }

        return prima == 0 && l.posa() == 1;
    }

    static_assert(passo(), "i fanti non cambiano posa");
}

}
