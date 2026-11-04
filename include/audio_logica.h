#ifndef GUBBIO_AUDIO_LOGICA_H
#define GUBBIO_AUDIO_LOGICA_H

#include "battaglia.h"
#include "colonna_sonora.h"
#include "storia_logica.h"
#include "tabella.h"

// Quale musica suona, tutto constexpr: il brano di fondo dell'esplorazione (area, fase, luogo), il
// segnale di un luogo (Fazio nella sua bottega), l'effetto di un evento di battaglia. I dati sono in
// include/colonna_sonora.h (da musica/colonna_sonora.txt); qui le regole, che src/autotest_audio.cpp
// prova a tempo di compilazione. Il suono vero (maxmod) e' in src/audio.cpp.
namespace gubbio::audio
{

// La fase della musica: quella degli NPC, piu' l'alba dopo la terza alba (E-01, ATTO_I_COMPLETATO).
[[nodiscard]] constexpr colonna::Fase fase_musicale(const GameState& p)
{
    if(storia::accesa(p, storia::Bandiera::ATTO_I_COMPLETATO))
    {
        return colonna::Fase::ALBA;
    }

    switch(storia::fase_npc(p))
    {
        case storia::Fase::DIGIUNO:
            return colonna::Fase::DIGIUNO;

        case storia::Fase::NOTTE:
            return colonna::Fase::NOTTE;

        default:
            return colonna::Fase::GIORNO;
    }
}

[[nodiscard]] constexpr bool nel_luogo(const colonna::Luogo& l, int area, int cx, int cy)
{
    return l.area == area && cx >= l.x0 && cx <= l.x1 && cy >= l.y0 && cy <= l.y1;
}

// L'amico e' nella sua bottega? Non c'e' quando, col borgo dentro le mura, nel DIGIUNO e nella NOTTE
// sta in Sant'Andrea (la stessa regola di Storia::posto_di).
[[nodiscard]] constexpr bool amico_a_casa(const GameState& p, int npc)
{
    if(npc < 0)
    {
        return true;
    }

    const storia::Npc& n = GUBBIO_VOCE(storia::NPC_AMBIENTE, npc);
    return ! (n.del_borgo && storia::accesa(p, storia::Bandiera::BORGO_DENTRO) &&
              storia::fase_npc(p) != storia::Fase::ULTIMATUM);
}

// Il brano che deve suonare camminando nella cella (cx, cy) dell'area: quello del luogo di fondo se ci si
// e' dentro, se no quello dell'area nella fase.
[[nodiscard]] constexpr colonna::Brano brano_di_fondo(const GameState& p, int area, int cx, int cy)
{
    for(int k = 0; k < colonna::LUOGHI; ++k)
    {
        const colonna::Luogo& l = GUBBIO_VOCE(colonna::LUOGO, k);

        if(l.modo == colonna::Modo::FONDO && nel_luogo(l, area, cx, cy) && amico_a_casa(p, l.npc))
        {
            return l.brano;
        }
    }

    return GUBBIO_VOCE(colonna::BRANO_AREA, area)[int(fase_musicale(p))];
}

// Il luogo col segnale in cui si e' (Fazio in bottega), o -1.
[[nodiscard]] constexpr int segnale_qui(const GameState& p, int area, int cx, int cy)
{
    for(int k = 0; k < colonna::LUOGHI; ++k)
    {
        const colonna::Luogo& l = GUBBIO_VOCE(colonna::LUOGO, k);

        if(l.modo == colonna::Modo::SEGNALE && nel_luogo(l, area, cx, cy) && amico_a_casa(p, l.npc))
        {
            return k;
        }
    }

    return -1;
}

// L'effetto di un evento di battaglia (colonna::Effetto), o colonna::NESSUNO: il colpo dell'eroe del
// fuoco (Antonio) e' il fuoco.
[[nodiscard]] constexpr int effetto_dell_evento(const battaglia::Evento& e)
{
    if(e.kind == battaglia::EventKind::HIT && ! e.attore_nemico && e.attore == colonna::EROE_DEL_FUOCO)
    {
        return int(colonna::EFFETTO_DEL_FUOCO);
    }

    return GUBBIO_VOCE(colonna::EFFETTO_EVENTO, int(e.kind));
}

}

#endif
