// Autotest delle quest e delle regole del copione che il gioco ora legge (include/storia_logica.h), a
// tempo di compilazione: la consegna delle tre quest (55 punti a ogni Santo, il premio, una volta sola,
// entro la conferma dell'alba), lo scudo in meno di Corrado (Q-SM01 o RUFINO_ASCOLTATO), il digiuno di
// Ubaldo (da CITTA_IN_DIGIUNO al rientro di B-05) e la gola del Bottaccione ancora percorribile dopo
// B-05, rientrando da Porta Metauro (regola «nessuna quest si perde», Q-SA01). Ogni prova ha la sua
// negativa; se una non regge, la ROM non compila.

#include "battaglia.h"
#include "mondo_logica.h"
#include "storia_logica.h"

namespace gubbio
{

namespace
{
    using namespace storia;

    constexpr void accendi_bandiera(GameState& p, Bandiera b)
    {
        accendi(p, uint64_t(1) << int(b));
    }

    // --- Le tabelle --------------------------------------------------------------------------------

    static_assert(QUEST == 3 && progressione::ESPERIENZA_QUEST == 55, "tre quest da 55 punti (docs/bilanciamento.md)");
    static_assert(QUEST_V1[0].oggetto == int(battaglia::OggettoId::CRESCIA) && QUEST_V1[0].quanti == 3 &&
                  QUEST_V1[1].oggetto == int(battaglia::OggettoId::BISCOTTI) && QUEST_V1[1].quanti == 3 &&
                  QUEST_V1[2].oggetto == int(battaglia::OggettoId::CENERE) && QUEST_V1[2].quanti == 1,
                  "i premi delle quest (04_quest.md)");
    static_assert(QUEST_V1[0].consegnata == Q_SM01_CONSEGNATA && QUEST_V1[1].consegnata == Q_SA01_CONSEGNATA &&
                  QUEST_V1[2].consegnata == Q_SP01_CONSEGNATA && Q_SM01_CONSEGNATA >= 64 && Q_SP01_CONSEGNATA < 128,
                  "le bandiere delle consegne stanno nell'intervallo quest (GameState::quest)");
    static_assert(battaglia::INCONTRO[INCONTRO_DI_CORRADO].nemici == 1 &&
                  battaglia::INCONTRO[INCONTRO_DI_CORRADO].schieramento[0] == battaglia::NemicoId::CORRADO_DI_SPOLETO,
                  "INCONTRO_DI_CORRADO e' il duello con Corrado");

    // --- La consegna -------------------------------------------------------------------------------

    struct Consegna
    {
        bool riuscita = false;
        bool seconda = true;
        int esperienza[battaglia::EROI] = {};
        int oggetti = 0;
        bool accesa = false;
    };

    // Consegna la quest q con le bandiere 'storia' accese, poi prova a consegnarla di nuovo.
    consteval Consegna consegna(int q, uint64_t storia_accesa)
    {
        GameState p = {};
        progressione::partita_nuova(p);
        accendi(p, storia_accesa);
        bool saliti[battaglia::EROI] = {};
        Consegna c;
        c.riuscita = consegna_quest(p, q, saliti);
        c.seconda = consegna_quest(p, q, saliti);

        for(int e = 0; e < battaglia::EROI; ++e)
        {
            c.esperienza[e] = p.esperienza[e];
        }

        c.oggetti = p.oggetti[QUEST_V1[q].oggetto];
        c.accesa = accesa(p, int(QUEST_V1[q].consegnata));
        return c;
    }

    constexpr uint64_t DIGIUNO = (uint64_t(1) << int(Bandiera::ULTIMATUM_RICEVUTO)) |
                                 (uint64_t(1) << int(Bandiera::CITTA_IN_DIGIUNO));
    constexpr uint64_t DOPO_E01 = DIGIUNO | (uint64_t(1) << int(Bandiera::ATTO_I_COMPLETATO));

    consteval bool consegna_buona(int q)
    {
        Consegna c = consegna(q, DIGIUNO);
        GameState nuova = {};
        progressione::partita_nuova(nuova);
        int atteso = nuova.oggetti[QUEST_V1[q].oggetto] + QUEST_V1[q].quanti;
        int massimo = battaglia::OGGETTI[QUEST_V1[q].oggetto].massimo;
        return c.riuscita && ! c.seconda && c.accesa && c.esperienza[0] == 55 && c.esperienza[1] == 55 &&
               c.esperienza[2] == 55 && c.oggetti == (atteso > massimo ? massimo : atteso);
    }

    static_assert(consegna_buona(0) && consegna_buona(1) && consegna_buona(2),
                  "una quest consegnata da' 55 punti a ogni Santo e il premio, una volta sola");

    // Negative: prima che la quest si prenda (Q-SA01 e Q-SP01 da CITTA_IN_DIGIUNO) e dopo E-01 non si
    // consegna, e nulla cambia; un indice fuori dalle tre nemmeno.
    static_assert(! consegna(1, uint64_t(1) << int(Bandiera::ULTIMATUM_RICEVUTO)).riuscita &&
                  consegna(1, uint64_t(1) << int(Bandiera::ULTIMATUM_RICEVUTO)).esperienza[0] == 0 &&
                  consegna(0, uint64_t(1) << int(Bandiera::ULTIMATUM_RICEVUTO)).riuscita,
                  "Q-SA01 si consegna prima del digiuno, o Q-SM01 non si consegna dall'ultimatum");
    static_assert(! consegna(0, DOPO_E01).riuscita && ! consegna(2, DOPO_E01).accesa && consegna(2, DOPO_E01).esperienza[1] == 0,
                  "una quest si consegna dopo la conferma dell'alba (E-01)");

    consteval bool fuori_dalle_tre()
    {
        GameState p = {};
        accendi(p, DIGIUNO);
        bool saliti[battaglia::EROI] = { true, true, true };
        return ! consegna_quest(p, QUEST, saliti) && ! consegna_quest(p, -1, saliti) && ! saliti[0] && p.esperienza[0] == 0;
    }

    static_assert(fuori_dalle_tre(), "una quest che non c'e' si consegna");

    // Il premio non supera quanti se ne portano: con 4 Crescie (massimo 5) Q-SM01 ne lascia 5.
    consteval int crescie_con(int prima)
    {
        GameState p = {};
        accendi(p, DIGIUNO);
        p.oggetti[int(battaglia::OggettoId::CRESCIA)] = uint8_t(prima);
        bool saliti[battaglia::EROI] = {};
        consegna_quest(p, 0, saliti);
        return p.oggetti[int(battaglia::OggettoId::CRESCIA)];
    }

    static_assert(crescie_con(4) == battaglia::OGGETTI[int(battaglia::OggettoId::CRESCIA)].massimo && crescie_con(0) == 3,
                  "il premio supera il massimo dei consumabili");

    // Le tre quest prima di Corrado: dopo Pattuglia, Imboscata e Spettri (316 punti) si arriva al duello
    // al livello 5, con le tre quest (165 in piu') al 6, come in docs/bilanciamento.md.
    consteval int livello_a_corrado(int quest)
    {
        GameState p = {};
        progressione::partita_nuova(p);
        accendi(p, DIGIUNO);
        bool saliti[battaglia::EROI] = {};

        const int prima_di_corrado[3] = { 0, 1, 3 };     // Pattuglia, Imboscata, Spettri

        for(int incontro : prima_di_corrado)
        {
            progressione::assegna_esperienza(p, incontro, saliti);
        }

        for(int q = 0; q < quest; ++q)
        {
            consegna_quest(p, q, saliti);
        }

        return p.livello[0];
    }

    static_assert(livello_a_corrado(0) == 5 && livello_a_corrado(3) == 6, "il livello a Corrado con e senza le quest");
    static_assert(livello_a_corrado(1) != 6, "negativa: una quest sola non basta per il livello 6");

    // La nuova funzione dell'esperienza fissa e quella degli scontri sono la stessa cosa.
    consteval bool esperienza_fissa_come_scontro()
    {
        GameState a = {};
        GameState b = {};
        progressione::partita_nuova(a);
        progressione::partita_nuova(b);
        bool saliti_a[battaglia::EROI] = {};
        bool saliti_b[battaglia::EROI] = {};
        progressione::assegna_esperienza(a, 0, saliti_a);
        progressione::assegna_esperienza_fissa(b, progressione::esperienza_incontro(0), saliti_b);
        return a.esperienza[1] == b.esperienza[1] && a.livello[1] == b.livello[1] && saliti_a[1] == saliti_b[1] &&
               saliti_b[1] && b.livello[1] == 3;
    }

    static_assert(esperienza_fissa_come_scontro(), "assegna_esperienza_fissa non fa come gli scontri");

    // --- Lo scudo in meno di Corrado ----------------------------------------------------------------

    consteval int scudi(bool rufino, bool ferro, int incontro)
    {
        GameState p = {};

        if(rufino)
        {
            accendi_una(p, RUFINO_ASCOLTATO);
        }

        if(ferro)
        {
            accendi_una(p, Q_SM01_CONSEGNATA);
        }

        return scudi_in_meno(p, incontro);
    }

    static_assert(scudi(true, false, INCONTRO_DI_CORRADO) == 1 && scudi(false, true, INCONTRO_DI_CORRADO) == 1 &&
                  scudi(true, true, INCONTRO_DI_CORRADO) == 1, "Corrado con Rufino o con il ferro di Raniero: uno scudo in meno");
    static_assert(scudi(false, false, INCONTRO_DI_CORRADO) == 0 && scudi(true, true, 0) == 0 && scudi(true, true, 1) == 0 &&
                  scudi(true, true, 3) == 0, "negativa: senza le due bandiere, o in un altro scontro, nessuno scudo in meno");

    // Le altre quest consegnate non tolgono scudi.
    consteval int scudi_con_le_altre()
    {
        GameState p = {};
        accendi_una(p, Q_SA01_CONSEGNATA);
        accendi_una(p, Q_SP01_CONSEGNATA);
        return scudi_in_meno(p, INCONTRO_DI_CORRADO);
    }

    static_assert(scudi_con_le_altre() == 0, "Q-SA01 o Q-SP01 tolgono uno scudo a Corrado");

    // --- Il digiuno di Ubaldo -----------------------------------------------------------------------

    consteval bool digiuno_di_ubaldo()
    {
        GameState p = {};
        accendi_bandiera(p, Bandiera::ULTIMATUM_RICEVUTO);

        if(a_digiuno(p) != 0)       // la Pattuglia al Teatro: si mangia ancora
        {
            return false;
        }

        accendi_bandiera(p, Bandiera::CITTA_IN_DIGIUNO);

        if(a_digiuno(p) != (1 << battaglia::UBALDO))
        {
            return false;
        }

        accendi_bandiera(p, Bandiera::CONDOTTO_SALVO);      // dopo Corrado, ancora fuori dalle mura

        if(a_digiuno(p) != (1 << battaglia::UBALDO))
        {
            return false;
        }

        accendi_bandiera(p, Bandiera::RIENTRO_PORTA_METAURO);   // B-05: si e' rientrati in citta'
        return a_digiuno(p) == 0;
    }

    static_assert(digiuno_di_ubaldo(), "Ubaldo a digiuno da CITTA_IN_DIGIUNO al rientro di B-05, e solo lui");

    // Il digiuno coincide con la fase DIGIUNO degli NPC, e lungo la storia vale proprio negli scontri dopo
    // A1-05: l'Imboscata, gli Spettri e Corrado. Negativa: alla Pattuglia del Teatro Ubaldo mangia.
    // La storia giocata (ogni menu alla prima voce) finche' la scena k e' pronta.
    consteval GameState fino_alla_scena(int k)
    {
        GameState p = {};

        for(int giri = 0; giri < 64 && ! pronta(p, k, SCENA[k].area); ++giri)
        {
            int prossima = -1;

            for(int j = 0; j < SCENE && prossima < 0; ++j)
            {
                prossima = pronta(p, j, SCENA[j].area) ? j : -1;
            }

            if(prossima < 0)
            {
                break;
            }

            scegli_tutto(p, prossima, 0);
            chiudi_scena(p, prossima);
        }

        return p;
    }

    consteval uint8_t digiuno_alla_scena_dello_scontro(int incontro)
    {
        int k = scena_dello_scontro(incontro);
        GameState p = fino_alla_scena(k);

        if(! pronta(p, k, SCENA[k].area))
        {
            return 0xFF;
        }

        return (a_digiuno(p) != 0) == (fase_npc(p) == Fase::DIGIUNO) ? a_digiuno(p) : 0xFE;
    }

    static_assert(digiuno_alla_scena_dello_scontro(1) == 1 && digiuno_alla_scena_dello_scontro(3) == 1 &&
                  digiuno_alla_scena_dello_scontro(INCONTRO_DI_CORRADO) == 1, "Ubaldo mangia negli scontri del digiuno");
    static_assert(digiuno_alla_scena_dello_scontro(0) == 0, "negativa: alla Pattuglia del Teatro Ubaldo e' gia' a digiuno");

    // --- La gola dopo B-05 ---------------------------------------------------------------------------

    // La storia giocata fino al rientro di B-05 (RIENTRO_PORTA_METAURO), prima della conferma di E-01.
    consteval GameState dopo_il_rientro()
    {
        GameState p = {};

        for(int giri = 0; giri < 64 && ! accesa(p, Bandiera::RIENTRO_PORTA_METAURO); ++giri)
        {
            int k = -1;

            for(int j = 0; j < SCENE && k < 0; ++j)
            {
                k = pronta(p, j, SCENA[j].area) ? j : -1;
            }

            if(k >= 0)
            {
                scegli_tutto(p, k, 0);
                chiudi_scena(p, k);
            }
            else if(! risposta_di_un_npc(p))
            {
                break;
            }
        }

        return p;
    }

    constexpr mondo::AreaId GOLA[] = { mondo::AreaId::BOTTACCIONE, mondo::AreaId::GOLA_STRISCIA, mondo::AreaId::GOLA_MIASMI,
                                       mondo::AreaId::GOLA_ARCO, mondo::AreaId::CONDOTTO };

    // Nella gola, dopo B-05, nessuna scena riparte e nessun nemico sulla mappa sbarra la strada; la quest
    // si consegna ancora. Negativa: prima di B-04 il Condotto ha la sua scena e Corrado.
    consteval bool gola_libera(const GameState& p)
    {
        for(mondo::AreaId a : GOLA)
        {
            if(prossima_scena(p, int(a)) >= 0)
            {
                return false;
            }
        }

        return ! scontro_attivo(p, INCONTRO_DI_CORRADO);
    }

    consteval bool gola_dopo_il_rientro()
    {
        GameState p = dopo_il_rientro();
        return accesa(p, Bandiera::RIENTRO_PORTA_METAURO) && ! accesa(p, Bandiera::ATTO_I_COMPLETATO) &&
               fase_npc(p) == Fase::NOTTE && gola_libera(p) && quest_consegnabile(p, 1);
    }

    static_assert(gola_dopo_il_rientro(), "dopo B-05 la gola non e' libera o Q-SA01 non si consegna piu'");

    consteval bool condotto_prima_di_b04()
    {
        int k = scena_dello_scontro(INCONTRO_DI_CORRADO);
        GameState p = fino_alla_scena(k);
        return pronta(p, k, int(mondo::AreaId::CONDOTTO)) && ! gola_libera(p);
    }

    static_assert(condotto_prima_di_b04(), "negativa: prima di B-04 la gola risulta libera");

    // La camminata vera (stessa collisione del gioco, mondo_logica.h): da San Martino si esce da Porta
    // Metauro sulla Strada del Bottaccione, si risale la gola fino al Condotto e si torna in citta'. I varchi
    // non leggono lo stato di partita: quel che si cammina qui si cammina in ogni momento della storia.
    consteval bool cammina(const mondo::AreaId* tappe, int quante)
    {
        mondo::Esploratore e;
        mondo::colloca(e, tappe[0], 0);
        mondo::Navigatore n;

        for(int t = 1; t < quante; ++t)
        {
            int k = mondo::varco_verso(e.area, tappe[t]);

            if(k < 0 || ! n.prepara(e, k))
            {
                return false;
            }

            mondo::Evento evento = mondo::Evento::NESSUNO;

            while(evento == mondo::Evento::NESSUNO)
            {
                if(! n.passo(e, evento))
                {
                    return false;
                }
            }

            if(evento != mondo::Evento::CAMBIO_AREA || e.area != tappe[t])
            {
                return false;
            }
        }

        return true;
    }

    constexpr mondo::AreaId DA_PORTA_METAURO[] = {
        mondo::AreaId::SAN_MARTINO, mondo::AreaId::BOTTACCIONE, mondo::AreaId::GOLA_STRISCIA, mondo::AreaId::GOLA_MIASMI,
        mondo::AreaId::GOLA_ARCO, mondo::AreaId::CONDOTTO, mondo::AreaId::GOLA_ARCO, mondo::AreaId::GOLA_MIASMI,
        mondo::AreaId::GOLA_STRISCIA, mondo::AreaId::BOTTACCIONE, mondo::AreaId::SAN_MARTINO };

    static_assert(cammina(DA_PORTA_METAURO, 11), "da Porta Metauro non si risale la gola fino al Condotto e ritorno");

    // Negativa: una tappa senza varco (da San Martino dritti nella gola) non si cammina.
    constexpr mondo::AreaId SCORCIATOIA[] = { mondo::AreaId::SAN_MARTINO, mondo::AreaId::GOLA_STRISCIA };
    static_assert(! cammina(SCORCIATOIA, 2), "negativa: da San Martino si entra nella gola senza la Strada del Bottaccione");
}

}
