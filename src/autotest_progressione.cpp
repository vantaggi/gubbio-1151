// Autotest della crescita dei Santi a tempo di compilazione (include/progressione.h): la curva
// dell'esperienza, la crescita delle statistiche, l'esperienza degli scontri, le posizioni dei
// nemici sulla mappa. Ogni prova ha la sua negativa; se una non regge, la ROM non compila.

#include "battaglia.h"
#include "progressione.h"

namespace gubbio
{

namespace
{
    using namespace progressione;
    using battaglia::EROI;
    using battaglia::STATISTICHE_EROI;

    // La curva: parte da 0, cresce sempre, e ogni salto e' almeno grande quanto il precedente.
    consteval bool curva_buona(const int (&curva)[LIVELLO_MAX])
    {
        if(curva[0] != 0)
        {
            return false;
        }

        for(int l = 1; l < LIVELLO_MAX; ++l)
        {
            if(curva[l] <= curva[l - 1])
            {
                return false;
            }

            if(l >= 2 && curva[l] - curva[l - 1] < curva[l - 1] - curva[l - 2])
            {
                return false;
            }
        }

        return true;
    }

    static_assert(curva_buona(ESPERIENZA_PER_LIVELLO), "la curva dell'esperienza non e' crescente e convessa");

    // Negativa: una curva coi salti che si accorciano viene rifiutata.
    constexpr int CURVA_SBAGLIATA[LIVELLO_MAX] = { 0, 100, 150, 190, 220, 240, 250, 255 };
    static_assert(! curva_buona(CURVA_SBAGLIATA), "la negativa della curva non regge");

    static_assert(livello_da_esperienza(0) == 1 && livello_da_esperienza(39) == 1 && livello_da_esperienza(40) == 2 &&
                  livello_da_esperienza(949) == 7 && livello_da_esperienza(950) == 8 &&
                  livello_da_esperienza(ESPERIENZA_MASSIMA) == LIVELLO_MAX, "i livelli dall'esperienza");

    // La crescita: al livello 1 le statistiche di base (cosi' le battaglie del mirror non cambiano),
    // poi sempre in salita, e all'8 non oltre i due terzi in piu'.
    consteval bool crescita_buona()
    {
        if(CRESCITA_PERCENTO[0] != 100 || CRESCITA_PERCENTO[LIVELLO_MAX - 1] > 170)
        {
            return false;
        }

        for(int l = 1; l < LIVELLO_MAX; ++l)
        {
            if(CRESCITA_PERCENTO[l] <= CRESCITA_PERCENTO[l - 1])
            {
                return false;
            }
        }

        for(int e = 0; e < EROI; ++e)
        {
            battaglia::Statistiche base = STATISTICHE_EROI[e];
            battaglia::Statistiche uno = statistiche_al_livello(base, 1);
            battaglia::Statistiche otto = statistiche_al_livello(base, LIVELLO_MAX);

            if(uno.pv != base.pv || uno.attacco != base.attacco || uno.difesa != base.difesa ||
               uno.mistico != base.mistico || uno.fervore != base.fervore || uno.resistenza != base.resistenza ||
               uno.velocita != base.velocita)
            {
                return false;
            }

            if(otto.pv <= base.pv || otto.velocita != base.velocita)
            {
                return false;
            }
        }

        return true;
    }

    static_assert(crescita_buona(), "la crescita delle statistiche non e' quella attesa");

    // Il passo dell'atto: vinti i tre scontri della mappa, i Santi sono al livello 4.
    static_assert(esperienza_incontro(0) == 115 && esperienza_incontro(1) == 81 && esperienza_incontro(2) == 200 &&
                  esperienza_incontro(3) == 120, "l'esperienza degli scontri (F8, docs/bilanciamento.md)");

    // Nell'ordine della storia (Pattuglia, Imboscata, Spettri) i Santi arrivano a Corrado al livello 5.
    consteval int livello_prima_di_corrado()
    {
        GameState p = {};
        partita_nuova(p);
        bool saliti[EROI] = {};
        assegna_esperienza(p, 0, saliti);
        assegna_esperienza(p, 1, saliti);
        assegna_esperienza(p, 3, saliti);
        return p.livello[0];
    }

    static_assert(livello_prima_di_corrado() == 5, "a Corrado si arriva al livello 5 senza quest");

    consteval int livello_dopo_i_tre_scontri()
    {
        GameState p = {};
        partita_nuova(p);
        bool saliti[EROI] = {};

        for(int i = 0; i < battaglia::INCONTRI; ++i)
        {
            assegna_esperienza(p, i, saliti);
        }

        return p.livello[0];
    }

    // dopo i quattro scontri, Corrado compreso: livello 6
    static_assert(livello_dopo_i_tre_scontri() == 6, "dopo i quattro scontri i Santi devono essere al livello 6");

    // I livelli contano: col pilota debole (solo l'Attacco), la Pattuglia Perugina batte i Santi al
    // livello 1 ma non all'8, almeno per un seme. La negativa e' il livello 1 stesso. (Con Corrado
    // il pilota debole non vince a nessun livello: e' immune al taglio finche' non e' ustionato.)
    consteval bool i_livelli_contano()
    {
        battaglia::Statistiche otto[EROI] = {};

        for(int e = 0; e < EROI; ++e)
        {
            otto[e] = statistiche_al_livello(STATISTICHE_EROI[e], LIVELLO_MAX);
        }

        for(uint32_t seme = 1; seme <= 60; ++seme)
        {
            battaglia::Battaglia uno(0, seme, true);
            battaglia::Battaglia forte(0, seme, true);
            forte.ricomincia(0, seme, true, otto);

            if(uno.gioca().esito == battaglia::Esito::SCONFITTA && forte.gioca().esito == battaglia::Esito::VITTORIA)
            {
                return true;
            }
        }

        return false;
    }

    static_assert(i_livelli_contano(), "al livello 8 i Santi non battono una Pattuglia che li batte al livello 1");

    // Le bandiere: segnata una, solo quella risulta vinta.
    consteval bool bandiere()
    {
        GameState p = {};
        segna_vinto(p, Bandiera::CORRADO_SCONFITTO);
        return vinto(p, Bandiera::CORRADO_SCONFITTO) && ! vinto(p, Bandiera::PATTUGLIA_SCONFITTA) &&
               ! vinto(p, Bandiera::IMBOSCATA_SCONFITTA);
    }

    static_assert(bandiere(), "le bandiere degli scontri");

    // I nemici sulla mappa stanno su posti buoni (calpestabili, lontani dai varchi e dagli arrivi),
    // ognuno col suo scontro. Negativa: l'angolo (0, 0) di un'area e' muro e non va bene.
    consteval bool posti_dei_nemici()
    {
        for(int k = 0; k < SCONTRI; ++k)
        {
            const ScontroSullaMappa& s = SCONTRI_SULLA_MAPPA[k];

            if(! posto_valido(s.area, s.tx, s.ty) || s.incontro != k || int(s.bandiera) != k)
            {
                return false;
            }
        }

        return true;
    }

    static_assert(posti_dei_nemici(), "un nemico sulla mappa sta su un posto non valido");
    static_assert(! posto_valido(mondo::AreaId::TEATRO_ROMANO, 0, 0), "la negativa dei posti non regge");

    // Il contatto: vicino al nemico si', lontano no, e uno scontro vinto non si tocca piu'.
    consteval bool contatto()
    {
        GameState p = {};
        const ScontroSullaMappa& s = SCONTRI_SULLA_MAPPA[0];
        int x = mondo::piedi_x(s.tx);
        int y = mondo::piedi_y(s.ty);

        if(scontro_toccato(p, s.area, x + 4, y) != 0 || scontro_toccato(p, s.area, x + 40, y) != -1 ||
           scontro_toccato(p, mondo::AreaId::PIAZZA_GRANDE, x, y) != -1)
        {
            return false;
        }

        segna_vinto(p, s.bandiera);
        return scontro_toccato(p, s.area, x, y) == -1;
    }

    static_assert(contatto(), "il contatto con i nemici sulla mappa");
}

}
