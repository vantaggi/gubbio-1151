#include "audio.h"

#include "bn_fixed.h"
#include "bn_music.h"
#include "bn_optional.h"

#include "audio_logica.h"
#include "tabella.h"

namespace gubbio::audio
{

namespace
{
    // I volumi proposti da musica/LEGGIMI.md: la musica sotto gli effetti, i jingle un poco sopra.
    constexpr bn::fixed VOLUME_MUSICA = 0.6;
    constexpr bn::fixed VOLUME_JINGLE = 0.7;
    constexpr bn::fixed VOLUME_EFFETTI = 0.8;

    // Lo stato del suono: pochi byte statici, nessuna allocazione (il mixer di maxmod ha i suoi
    // buffer statici dentro Butano).
    bool s_acceso = true;
    int s_brano = colonna::NESSUNO;     // l'ultimo brano fatto partire
    int s_luogo = -1;                    // il luogo col segnale in cui si e', per suonarlo una volta
    int s_area = -1;                     // dove si e' camminato l'ultima volta: l'area e la cella
    int s_cella_x = 0;
    int s_cella_y = 0;

    [[nodiscard]] bool suona_ancora(int b)
    {
        return s_brano == b && bn::music::playing();
    }

    void parti(int b)
    {
        bool anello = GUBBIO_VOCE(colonna::IN_ANELLO, b);
        GUBBIO_VOCE(colonna::MUSICA, b).play(anello ? VOLUME_MUSICA : VOLUME_JINGLE, anello);
        s_brano = b;
    }
}

void accendi(bool acceso)
{
    s_acceso = acceso;

    if(! acceso && bn::music::playing())
    {
        bn::music::stop();
    }

    s_brano = colonna::NESSUNO;
}

bool acceso()
{
    return s_acceso;
}

void brano(colonna::Brano b)
{
    if(s_acceso && ! suona_ancora(int(b)))
    {
        parti(int(b));
    }
}

void esplorazione(const GameState& partita, int area, int cella_x, int cella_y)
{
    // il segnale di un luogo suona entrandoci, una volta; si riarma uscendo o cambiando area
    int luogo = segnale_qui(partita, area, cella_x, cella_y);

    if(area != s_area)
    {
        s_area = area;
        s_luogo = -1;
    }

    s_cella_x = cella_x;
    s_cella_y = cella_y;

    if(luogo != s_luogo)
    {
        s_luogo = luogo;

        if(luogo >= 0)
        {
            brano(GUBBIO_VOCE(colonna::LUOGO, luogo).brano);
            return;
        }
    }

    if(! s_acceso)
    {
        return;
    }

    // un jingle (la vittoria, il segnale) si lascia finire: poi riparte il brano dell'area
    if(s_brano >= 0 && ! GUBBIO_VOCE(colonna::IN_ANELLO, s_brano) && bn::music::playing())
    {
        return;
    }

    brano(brano_di_fondo(partita, area, cella_x, cella_y));
}

void cutscene(int c)
{
    int b = GUBBIO_VOCE(colonna::BRANO_CUTSCENE, c);
    int e = GUBBIO_VOCE(colonna::EFFETTO_CUTSCENE, c);

    if(b >= 0)
    {
        brano(colonna::Brano(b));
    }

    if(e >= 0)
    {
        effetto(colonna::Effetto(e));
    }
}

void fine_cutscene(int c)
{
    // prima della prima passeggiata (il prologo di una partita nuova) non c'e' un'area a cui tornare
    if(GUBBIO_VOCE(colonna::BRANO_CUTSCENE, c) >= 0 && s_area >= 0)
    {
        brano(brano_di_fondo(g_game_state, s_area, s_cella_x, s_cella_y));
    }
}

void battaglia(int incontro)
{
    brano(GUBBIO_VOCE(colonna::BRANO_INCONTRO, incontro));
}

void fine_battaglia(bool vinta)
{
    if(s_acceso)
    {
        // la vittoria e la sconfitta partono sempre, anche dopo un'altra battaglia uguale
        parti(int(vinta ? colonna::BRANO_VITTORIA : colonna::BRANO_SCONFITTA));
    }
}

void evento(const battaglia::Evento& e)
{
    int k = effetto_dell_evento(e);

    if(k >= 0)
    {
        effetto(colonna::Effetto(k));
    }
}

void effetto(colonna::Effetto e)
{
    if(s_acceso)
    {
        GUBBIO_VOCE(colonna::SUONO, int(e)).play(VOLUME_EFFETTI);
    }
}

void suona(colonna::Suono s)
{
    effetto(GUBBIO_VOCE(colonna::EFFETTO_SUONO, int(s)));
}

}
