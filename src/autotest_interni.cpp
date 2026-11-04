// Autotest degli interni (INTC, INTB), a tempo di compilazione: le cose da esaminare si raggiungono camminando,
// si leggono da vicino e non da lontano, nessuno della stanza le copre; i doni di Padellino e Valenza si fanno
// una volta sola e non portano oltre il massimo. Ogni prova ha la sua negativa; se una non regge, la ROM non
// compila.

#include "battaglia.h"
#include "mondo_logica.h"
#include "progressione.h"
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

    // Il fumetto sta sull'oggetto (STANDARD I2): sopra la cella da cui lo si legge, a non piu' di 8 tile di lato (lo stemma sta dietro gli scranni).
    consteval bool fumetti_sulle_cose()
    {
        for(int k = 0; k < COSE; ++k)
        {
            const Cosa& c = COSA[k];
            int dx = int(c.fx) - mondo::piedi_x(c.tx);

            if(int(c.fy) >= mondo::piedi_y(c.ty) || dx < -64 || dx > 64)
            {
                return false;
            }
        }

        return true;
    }

    static_assert(fumetti_sulle_cose(), "il fumetto di una cosa non sta sull'oggetto");

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

    // --- Le stanze che cambiano con la fase (INTp) -------------------------------------------------------
    // fase: 0 ultimatum, 1 digiuno, 2 notte; borgo: 0 nessuna scelta, 1 dentro, 2 fuori
    consteval GameState in_fase(int fase, int borgo)
    {
        GameState p = {};
        progressione::partita_nuova(p);

        if(fase >= 1)
        {
            accendi_una(p, int(Bandiera::CITTA_IN_DIGIUNO));
        }

        if(fase >= 2)
        {
            accendi_una(p, int(Bandiera::RIENTRO_PORTA_METAURO));
        }

        if(borgo > 0)
        {
            accendi_una(p, int(borgo == 1 ? Bandiera::BORGO_DENTRO : Bandiera::BORGO_FUORI));
        }

        return p;
    }

    constexpr int TAVERNA = int(mondo::AreaId::TAVERNA_INTERNO);
    constexpr int CONTI = int(mondo::AreaId::BOTTEGA_CONTI_INTERNO);
    constexpr int DIGIUNO = int(mondo::VarianteId::TAVERNA_INTERNO_DIGIUNO);
    constexpr int ROVESCIATA = int(mondo::VarianteId::BOTTEGA_CONTI_INTERNO_ROVESCIATA);

    static_assert(variante_dell_area(in_fase(1, 0), TAVERNA) == DIGIUNO &&
                  variante_dell_area(in_fase(0, 0), TAVERNA) < 0 && variante_dell_area(in_fase(2, 0), TAVERNA) < 0,
                  "la taverna e' vuota solo nel digiuno");
    static_assert(variante_dell_area(in_fase(2, 2), CONTI) == ROVESCIATA &&
                  variante_dell_area(in_fase(2, 1), CONTI) < 0 && variante_dell_area(in_fase(1, 2), CONTI) < 0 &&
                  variante_dell_area(in_fase(0, 0), CONTI) < 0, "la bottega e' rovesciata solo di notte col borgo fuori");
    static_assert(variante_dell_area(in_fase(1, 0), int(mondo::AreaId::SALA_CONSOLI)) < 0,
                  "negativa: una stanza senza varianti ne prende una");

    // La porta della bottega e' sbarrata col borgo dentro, nel digiuno e nella notte; mai nell'ultimatum.
    constexpr int SANT_AGOSTINO = int(mondo::AreaId::SANT_AGOSTINO);
    constexpr int PORTA = mondo::varco_verso(mondo::AreaId::SANT_AGOSTINO, mondo::AreaId::BOTTEGA_CONTI_INTERNO);

    static_assert(PORTA >= 0 && varco_chiuso(in_fase(1, 1), SANT_AGOSTINO) == PORTA &&
                  varco_chiuso(in_fase(2, 1), SANT_AGOSTINO) == PORTA, "la bottega col borgo dentro non e' sbarrata");
    static_assert(varco_chiuso(in_fase(0, 1), SANT_AGOSTINO) < 0 && varco_chiuso(in_fase(2, 2), SANT_AGOSTINO) < 0 &&
                  varco_chiuso(in_fase(1, 0), SANT_AGOSTINO) < 0, "negativa: la bottega sbarrata quando non deve");

    static_assert(mondo::VARIANTI == 2 && mondo::VARIANTE[0].area == mondo::AreaId::TAVERNA_INTERNO &&
                  mondo::VARIANTE[1].area == mondo::AreaId::BOTTEGA_CONTI_INTERNO, "le due varianti di fase");
    static_assert(mondo::VARIANTE[0].tile_conteggio <= 512 && mondo::VARIANTE[1].tile_conteggio <= 512,
                  "una variante sfora i tile di un BG");
}

}
