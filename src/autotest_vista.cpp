// Autotest della vista della battaglia a tempo di compilazione (include/vista_battaglia.h).
//
// La prova: per ogni round, la vista consuma gli eventi uno per volta. Una barra dei PV cambia solo
// consumando un HIT o un BURN_TICK su quell'unita', e prende il valore dell'evento; una barra del
// Fervore solo con FERVOR_GAIN o FERVOR_SPEND; a fine round vista e modello coincidono.
// La negativa: una barra che leggesse i PV dal modello sarebbe gia' al valore finale prima che il
// colpo venga mostrato (il modello risolve il round tutto insieme), quindi sbaglierebbe.
// Se una prova non regge, la ROM non compila, sul nome della funzione che fallisce.

#include "vista_battaglia.h"

namespace gubbio
{

void vista_barra_cambiata_fuori_dal_suo_evento(int incontro);
void vista_diversa_dal_modello_a_fine_round(int incontro);

namespace
{
    using namespace battaglia;

    consteval bool prova_vista(int incontro, uint32_t seme)
    {
        Battaglia b(incontro, seme);
        VistaBattaglia v;
        v.inizia(b, INCONTRO[incontro].nemici);
        int colpi = 0;

        while(b.avanza())
        {
            if(b.fase() != Fase::ESITO)
            {
                continue;
            }

            for(int i = 0; i < b.eventi_round(); ++i)
            {
                const Evento& e = b.evento(i);
                int pv_prima[SLOT_VISTA] = {};
                int fervore_prima[EROI] = {};

                for(int s = 0; s < SLOT_VISTA; ++s)
                {
                    pv_prima[s] = v.pv(s);
                }

                for(int s = 0; s < EROI; ++s)
                {
                    fervore_prima[s] = v.fervore(s);
                }

                v.consuma(e);
                int bersaglio = slot_vista(e.bersaglio_nemico, e.bersaglio);
                bool tocca_pv = e.kind == EventKind::HIT || e.kind == EventKind::BURN_TICK || e.kind == EventKind::CURA;
                bool tocca_fervore = e.kind == EventKind::FERVOR_GAIN || e.kind == EventKind::FERVOR_SPEND;

                for(int s = 0; s < SLOT_VISTA; ++s)
                {
                    if(v.pv(s) != pv_prima[s] && ! (tocca_pv && s == bersaglio && v.pv(s) == e.pv_dopo))
                    {
                        vista_barra_cambiata_fuori_dal_suo_evento(incontro);
                    }
                }

                for(int s = 0; s < EROI; ++s)
                {
                    if(v.fervore(s) != fervore_prima[s] && ! (tocca_fervore && s == bersaglio))
                    {
                        vista_barra_cambiata_fuori_dal_suo_evento(incontro);
                    }
                }

                colpi += tocca_pv ? 1 : 0;
            }

            for(int s = 0; s < EROI; ++s)
            {
                if(v.pv(s) != b.eroe(s).pv || v.fervore(s) != b.eroe(s).fervore)
                {
                    vista_diversa_dal_modello_a_fine_round(incontro);
                }
            }

            for(int n = 0; n < INCONTRO[incontro].nemici; ++n)
            {
                if(v.pv(EROI + n) != b.nemico(n).pv)
                {
                    vista_diversa_dal_modello_a_fine_round(incontro);
                }
            }
        }

        return colpi > 0;
    }

    // La negativa: nel primo round, prima di consumare il primo HIT, il modello ha gia' i PV finali
    // del bersaglio, diversi da quelli che la vista mostra ancora. Una barra letta dal modello
    // cambierebbe prima del frame del colpo.
    consteval bool barra_dal_modello_sbaglia(int incontro, uint32_t seme)
    {
        Battaglia b(incontro, seme);
        VistaBattaglia v;
        v.inizia(b, INCONTRO[incontro].nemici);

        while(b.avanza() && b.fase() != Fase::ESITO)
        {
        }

        for(int i = 0; i < b.eventi_round(); ++i)
        {
            const Evento& e = b.evento(i);

            if(e.kind == EventKind::HIT && e.quantita > 0)
            {
                int s = slot_vista(e.bersaglio_nemico, e.bersaglio);
                int dal_modello = e.bersaglio_nemico ? b.nemico(e.bersaglio).pv : b.eroe(e.bersaglio).pv;
                return dal_modello != v.pv(s);
            }

            v.consuma(e);
        }

        return false;
    }

    static_assert(prova_vista(0, 1) && prova_vista(0, 7) && prova_vista(1, 3) && prova_vista(1, 11) &&
                  prova_vista(2, 1) && prova_vista(2, 5),
                  "la vista della battaglia cambia una barra fuori dal suo evento, o non torna con il modello");
    static_assert(barra_dal_modello_sbaglia(0, 1) && barra_dal_modello_sbaglia(2, 1),
                  "la negativa non regge: il modello non e' gia' risolto quando la vista mostra il colpo");

    // La scelta del bersaglio: parte dal predefinito del modello, gira solo fra i vivi.
    consteval bool prova_bersagli()
    {
        Battaglia b(0, 1);

        if(bersaglio_predefinito(b, Puntamento::NEMICO) != 0 || prossimo_bersaglio(b, Puntamento::NEMICO, 0, 1) != 1 ||
           prossimo_bersaglio(b, Puntamento::NEMICO, 2, 1) != 0 || prossimo_bersaglio(b, Puntamento::NEMICO, 0, -1) != 2 ||
           prossimo_bersaglio(b, Puntamento::ALLEATO, 2, 1) != 0)
        {
            return false;
        }

        if(mira_del_comando({ TipoComando::USA_ABILITA, AbilitaId::MURO_DELLA_FEDE, -1, 0 }) != Puntamento::ALLEATO ||
           mira_del_comando({ TipoComando::USA_ABILITA, AbilitaId::BASTIONE_AZZURRO, -1, 0 }) != Puntamento::NESSUNO ||
           mira_del_comando({ TipoComando::SUPREMA, AbilitaId::FENDENTE_DEL_DRAGO, -1, 3 }) != Puntamento::NESSUNO ||
           mira_del_comando({ TipoComando::USA_ABILITA, AbilitaId::ATTACCO, -1, 0 }) != Puntamento::NEMICO)
        {
            return false;
        }

        // si gioca finche' un nemico cade: il cursore non ci si ferma piu'
        while(b.avanza() && b.nemico(0).vivo() && b.nemico(1).vivo() && b.nemico(2).vivo())
        {
        }

        for(int i = 0; i < 3; ++i)
        {
            for(int passo = -1; passo <= 1; passo += 2)
            {
                int j = prossimo_bersaglio(b, Puntamento::NEMICO, i, passo);

                if(! b.nemico(j).vivo() && (b.nemico(0).vivo() || b.nemico(1).vivo() || b.nemico(2).vivo()))
                {
                    return false;
                }
            }
        }

        return true;
    }

    // Il bersaglio di un consumabile: chi mangia. Con Ubaldo a digiuno (storia::a_digiuno()) il cursore non
    // ci si ferma mai e il predefinito e' un altro; la negativa: senza digiuno Ubaldo si sceglie, e il
    // Muro della Fede (che non e' cibo) lo sceglie anche a digiuno.
    consteval bool chi_mangia(uint8_t digiuno, bool atteso_ubaldo)
    {
        Battaglia b(0, 1);
        b.ricomincia(0, 1, false, nullptr, TUTTI_PRESENTI, 0, digiuno);
        Comando oggetto;
        oggetto.tipo = TipoComando::OGGETTO;

        if(mira_del_comando(oggetto) != Puntamento::CHI_MANGIA || ! sceglibile(b, Puntamento::ALLEATO, UBALDO))
        {
            return false;
        }

        bool trovato = bersaglio_predefinito(b, Puntamento::CHI_MANGIA) == UBALDO;

        for(int da = 0; da < EROI; ++da)
        {
            trovato = trovato || prossimo_bersaglio(b, Puntamento::CHI_MANGIA, da, 1) == UBALDO ||
                      prossimo_bersaglio(b, Puntamento::CHI_MANGIA, da, -1) == UBALDO;
        }

        return sceglibile(b, Puntamento::CHI_MANGIA, UBALDO) == atteso_ubaldo && trovato == atteso_ubaldo &&
               bersaglio_predefinito(b, Puntamento::CHI_MANGIA) >= 0;
    }

    static_assert(chi_mangia(1 << UBALDO, false), "Ubaldo a digiuno si sceglie per un consumabile");
    static_assert(chi_mangia(0, true), "negativa: senza digiuno Ubaldo non si sceglie per un consumabile");

    // La negativa: girare "al prossimo slot" senza guardare chi e' caduto finirebbe su un morto.
    consteval bool giro_cieco_finisce_su_un_caduto()
    {
        Battaglia b(0, 1);

        while(b.avanza() && b.nemico(0).vivo() && b.nemico(1).vivo() && b.nemico(2).vivo())
        {
        }

        for(int i = 0; i < 3; ++i)
        {
            if(b.nemico(i).vivo() && ! b.nemico((i + 1) % 3).vivo())
            {
                return true;
            }
        }

        return false;
    }

    static_assert(prova_bersagli(), "la scelta del bersaglio parte male o si ferma su chi e' caduto");
    static_assert(giro_cieco_finisce_su_un_caduto(), "la negativa del bersaglio non regge");

    static_assert(pieno(0, 100, 30) == 0 && pieno(1, 100, 30) == 1 && pieno(100, 100, 30) == 30 &&
                  pieno(50, 100, 30) == 15, "barre: pixel pieni");
}

}
