// Autotest degli interni (INTC, INTB), a tempo di compilazione: le cose da esaminare si raggiungono camminando,
// si leggono da vicino e non da lontano, nessuno della stanza le copre; i doni di Padellino e Valenza si fanno
// una volta sola e non portano oltre il massimo. Ogni prova ha la sua negativa; se una non regge, la ROM non
// compila.

#include "battaglia.h"
#include "mondo_logica.h"
#include "storia_logica.h"

namespace gubbio
{

namespace
{
    using namespace storia;

    constexpr bool interno(int area)
    {
        return mondo::area(mondo::AreaId(area)).interno;
    }

    // --- Le cose da esaminare -------------------------------------------------------------------------
    static_assert(COSE == 12, "le cose da esaminare sono 12, due per stanza (interni/COPIONE_INTERNI.md sez. 3)");

    consteval bool cose_negli_interni()
    {
        for(int k = 0; k < COSE; ++k)
        {
            if(! interno(COSA[k].area))
            {
                return false;
            }
        }

        return true;
    }

    static_assert(cose_negli_interni(), "una cosa da esaminare sta fuori dagli interni");

    // Da sopra la cosa la si legge; un passo di parola piu' in la' no.
    consteval bool cose_da_vicino()
    {
        for(int k = 0; k < COSE; ++k)
        {
            const Cosa& c = COSA[k];
            int x = mondo::piedi_x(c.tx);
            int y = mondo::piedi_y(c.ty);

            if(cosa_a_portata(c.area, x, y) != k || cosa_a_portata(c.area, x + DISTANZA_COSA, y) == k ||
               cosa_a_portata(c.area, x, y + DISTANZA_COSA) == k)
            {
                return false;
            }
        }

        return true;
    }

    static_assert(cose_da_vicino(), "una cosa non si legge da vicino, o si legge da lontano");
    // Negativa: la stessa cella in un'altra area non legge niente (l'area di gioco della piazza non ha cose).
    static_assert(cosa_a_portata(int(mondo::AreaId::PIAZZA_GRANDE), mondo::piedi_x(COSA[0].tx),
                                 mondo::piedi_y(COSA[0].ty)) < 0, "negativa: una cosa si legge fuori dalla sua stanza");

    // Nessun NPC della stanza sta a portata di parola della cosa: risponderebbe lui e la cosa non si leggerebbe.
    consteval bool cose_scoperte()
    {
        for(int k = 0; k < COSE; ++k)
        {
            const Cosa& c = COSA[k];

            for(int j = 0; j < NPC; ++j)
            {
                const Npc& n = NPC_AMBIENTE[j];
                int dx = int(n.tx) - int(c.tx);
                int dy = int(n.ty) - int(c.ty);

                if(n.area == c.area && dx > -4 && dx < 4 && dy > -4 && dy < 4)
                {
                    return false;
                }
            }
        }

        return true;
    }

    static_assert(cose_scoperte(), "un NPC copre una cosa da esaminare");

    // Ci si arriva camminando, dallo spawn d'arrivo di ogni varco della stanza.
    consteval bool cose_raggiungibili()
    {
        for(int k = 0; k < COSE; ++k)
        {
            const Cosa& c = COSA[k];
            const mondo::Area& a = mondo::area(mondo::AreaId(c.area));

            for(int s = 0; s < a.varchi; ++s)
            {
                mondo::Esploratore e;
                mondo::colloca(e, mondo::AreaId(c.area), s);
                mondo::Navigatore n;

                if(! n.prepara_cella(e, c.tx, c.ty))
                {
                    return false;
                }
            }
        }

        return true;
    }

    static_assert(cose_raggiungibili(), "una cosa da esaminare non si raggiunge camminando");

    // --- I doni (INTB) --------------------------------------------------------------------------------
    static_assert(DONI == 2 && DONO[0].oggetto == int(battaglia::OggettoId::CRESCIA) && DONO[0].quanti == 1 &&
                  DONO[1].oggetto == int(battaglia::OggettoId::BISCOTTI) && DONO[1].quanti == 2,
                  "i doni: 1 Crescia (Padellino) e 2 Biscotti (Valenza)");
    static_assert(NPC_AMBIENTE[DONO[0].npc].area == int8_t(mondo::AreaId::TAVERNA_INTERNO) &&
                  NPC_AMBIENTE[DONO[1].npc].area == int8_t(mondo::AreaId::SPEZIERIA_INTERNO),
                  "chi fa i doni non sta nella sua bottega");
    static_assert(DONO_PADELLINO != DONO_VALENZA && DONO_PADELLINO < 128 && DONO_VALENZA < 128 &&
                  DONO_PADELLINO != FORZIERE_CRESCIA && DONO_VALENZA != FORZIERE_BISCOTTI,
                  "le bandiere dei doni non sono bandiere libere delle quest");

    consteval bool dono_una_volta(int k)
    {
        GameState p{};
        const Dono& d = DONO[k];

        if(dono_dell_npc(p, d.npc) != k || ! dai_dono(p, k))
        {
            return false;
        }

        bool ancora = dai_dono(p, k);
        return ! ancora && p.oggetti[d.oggetto] == d.quanti && dono_dell_npc(p, d.npc) < 0;
    }

    static_assert(dono_una_volta(0) && dono_una_volta(1), "un dono si fa due volte o non da' l'oggetto");

    consteval bool dono_al_massimo()
    {
        GameState p{};
        p.oggetti[DONO[1].oggetto] = uint8_t(battaglia::OGGETTI[DONO[1].oggetto].massimo);
        return dai_dono(p, 1) && p.oggetti[DONO[1].oggetto] == battaglia::OGGETTI[DONO[1].oggetto].massimo;
    }

    static_assert(dono_al_massimo(), "il dono porta oltre il massimo che se ne porta");
    // Negativa: chi non ha doni non ne fa (il primo NPC della lista non ne ha).
    static_assert(DONO[0].npc != 0 && DONO[1].npc != 0 && dono_dell_npc(GameState{}, 0) < 0,
                  "negativa: un NPC senza dono fa un dono");
}

}
