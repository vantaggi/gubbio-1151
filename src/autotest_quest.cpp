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

    // La quest q presa e con l'obiettivo finito, senza camminare (le prove della sola consegna).
    constexpr void completa(GameState& p, int q)
    {
        accendi_una(p, QUEST_GIOCO[q].presa);

        for(int i = 0; i < QUEST_GIOCO[q].pezzi; ++i)
        {
            accendi_una(p, QUEST_GIOCO[q].primo_pezzo + i);
        }
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
        completa(p, q);
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
        completa(p, 0);
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
            completa(p, q);
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

    // --- I Ceri risvegliati -------------------------------------------------------------------------

    // Lungo la storia i Ceri (CERI_RISVEGLIATI, accesa alla fine di A1-08) alzano il Fervore negli scontri dopo il
    // rito: i Guerrieri di B-03 e Corrado. Negativa: la Pattuglia, l'Imboscata e gli Spettri (nella scena stessa,
    // prima che la bandiera si accenda) si combattono senza.
    consteval int ceri_alla_scena_dello_scontro(int incontro)
    {
        int k = scena_dello_scontro(incontro);
        GameState p = fino_alla_scena(k);
        return pronta(p, k, SCENA[k].area) ? int(ceri_accesi(p)) : -1;
    }

    static_assert(ceri_alla_scena_dello_scontro(battaglia::INCONTRO_GUERRIERI) == 1 &&
                  ceri_alla_scena_dello_scontro(INCONTRO_DI_CORRADO) == 1, "i Ceri accesi dopo il rito");
    static_assert(ceri_alla_scena_dello_scontro(0) == 0 && ceri_alla_scena_dello_scontro(1) == 0 &&
                  ceri_alla_scena_dello_scontro(3) == 0, "negativa: i Ceri accesi prima del rito");

    consteval bool ceri_solo_dalla_bandiera()
    {
        GameState p = {};
        bool prima = ceri_accesi(p);
        accendi_bandiera(p, Bandiera::CERI_RISVEGLIATI);
        return ! prima && ceri_accesi(p);
    }

    static_assert(ceri_solo_dalla_bandiera(), "i Ceri si accendono con CERI_RISVEGLIATI");

    // Le fiamme sopra i tre ceri dell'altare: tre nell'interno della Basilica con i Ceri risvegliati, nessuna prima;
    // e fuori dalla Basilica mai (regola di Cioti: i ceri stanno solo dentro).
    consteval int fiamme(bool ceri, mondo::AreaId area)
    {
        GameState p = {};

        if(ceri)
        {
            accendi_bandiera(p, Bandiera::CERI_RISVEGLIATI);
        }

        return fiamme_dei_ceri(p, int(area));
    }

    consteval bool ceri_solo_nella_basilica()
    {
        for(int k = 0; k < CERI_ALTARE; ++k)
        {
            if(CERO_ALTARE[k].area != int8_t(mondo::AreaId::BASILICA_INTERNO))
            {
                return false;
            }
        }

        return true;
    }

    static_assert(fiamme(true, mondo::AreaId::BASILICA_INTERNO) == 3 && ceri_solo_nella_basilica(),
                  "le fiamme dei ceri nella Basilica");
    static_assert(fiamme(false, mondo::AreaId::BASILICA_INTERNO) == 0 && fiamme(true, mondo::AreaId::BASILICA) == 0 &&
                  fiamme(true, mondo::AreaId::PIAZZA_GRANDE) == 0, "negativa: fiamme senza i Ceri o fuori dalla Basilica");

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

    // --- Le quest giocabili (SV2c) ------------------------------------------------------------------
    // Le bandiere nuove stanno nell'intervallo quest (64-127, GameState::quest): nessun campo nuovo, il
    // salvataggio resta v3. I contatori sono bandiere consecutive (pezzi_raccolti).

    consteval bool bandiere_nell_intervallo_quest()
    {
        const int nuove[] = { Q_SM01_PRESA, Q_SA01_PRESA, Q_SP01_PRESA, FERRO_1, FERRO_2, FERRO_3, ELLEBORO_1, ELLEBORO_2,
                              ELLEBORO_3, ELLEBORO_4, ROSA_RIPRESA, Q_SM01_CONSEGNATA, Q_SA01_CONSEGNATA, Q_SP01_CONSEGNATA };

        for(int i = 0; i < int(sizeof(nuove) / sizeof(nuove[0])); ++i)
        {
            if(nuove[i] < 64 || nuove[i] >= 128)
            {
                return false;
            }

            for(int j = 0; j < i; ++j)
            {
                if(nuove[i] == nuove[j])
                {
                    return false;
                }
            }
        }

        return true;
    }

    static_assert(bandiere_nell_intervallo_quest() && sizeof(GameState) == 64,
                  "le bandiere delle quest giocabili fuori da 64-127, doppie, o GameState cambiato");
    static_assert(QUEST_GIOCO[0].pezzi == 3 && QUEST_GIOCO[0].primo_pezzo == FERRO_1 && QUEST_GIOCO[1].pezzi == 4 &&
                  QUEST_GIOCO[1].primo_pezzo == ELLEBORO_1 && QUEST_GIOCO[2].pezzi == 1 && QUEST_GIOCO[2].primo_pezzo == ROSA_RIPRESA,
                  "3 blocchi, 4 radici, la Rosa (04_quest.md)");

    // Ogni pezzo di una quest raccolta sulla mappa ha uno e un solo oggetto; Q-SP01 nessuno (la Rosa la da'
    // l'infiltrato). Negativa: togliendo l'ultimo oggetto, una radice resta senza posto.
    consteval bool pezzi_coperti(int q, int sulla_mappa, const Raccolta* tabella, int quante)
    {
        int contati = 0;

        for(int i = 0; i < QUEST_GIOCO[q].pezzi && sulla_mappa; ++i)
        {
            int trovati = 0;

            for(int k = 0; k < quante; ++k)
            {
                trovati += tabella[k].bandiera == QUEST_GIOCO[q].primo_pezzo + i && tabella[k].quest == q ? 1 : 0;
            }

            if(trovati != 1)
            {
                return false;
            }
        }

        for(int k = 0; k < quante; ++k)
        {
            contati += tabella[k].quest == q ? 1 : 0;
        }

        return contati == (sulla_mappa ? QUEST_GIOCO[q].pezzi : 0);
    }

    static_assert(pezzi_coperti(0, true, RACCOLTA, RACCOLTE) && pezzi_coperti(1, true, RACCOLTA, RACCOLTE) &&
                  pezzi_coperti(2, false, RACCOLTA, RACCOLTE), "gli oggetti sulla mappa non coprono i pezzi delle quest");
    static_assert(! pezzi_coperti(1, true, RACCOLTA, RACCOLTE - 1), "negativa: una radice senza posto non si vede");

    // Il giocatore cammina con la collisione vera (mondo_logica.h) dal punto d'arrivo 'spawn' dell'area fino
    // alla cella (tx, ty): ritorna dove si e' fermato, o x = -1 se non ci arriva.
    consteval mondo::Esploratore fino_alla_cella(mondo::AreaId area, int spawn, int tx, int ty)
    {
        mondo::Esploratore e;
        mondo::colloca(e, area, spawn);
        mondo::Navigatore n;

        if(! n.prepara_cella(e, tx, ty))
        {
            e.x = -1;
            return e;
        }

        mondo::Evento evento = mondo::Evento::NESSUNO;

        while(n.passo(e, evento))
        {
            if(evento != mondo::Evento::NESSUNO)
            {
                e.x = -1;
                return e;
            }
        }

        return e;
    }

    // Le guardie delle fornaci battute tutte (F10): i blocchi di ferro sono liberi.
    consteval GameState guardie_battute()
    {
        GameState p = {};

        for(int g = 0; g < GUARDIE_FORNACE; ++g)
        {
            batti_la_guardia(p, g);
        }

        return p;
    }

    // Da ogni ingresso dell'area (lo spawn d'arrivo di ogni varco che ci porta) si arriva a toccare l'oggetto k
    // (con le guardie delle fornaci gia' battute: davanti a una guardia in piedi il blocco non si prende).
    consteval bool raggiungibile_da_ogni_ingresso(int k)
    {
        const Raccolta& r = RACCOLTA[k];
        GameState p = guardie_battute();
        int ingressi = 0;

        for(int d = 0; d < mondo::AREE_CONTEGGIO; ++d)
        {
            const mondo::Area& da = mondo::area(mondo::AreaId(d));

            for(int v = 0; v < da.varchi; ++v)
            {
                if(mondo::varco_di(da, v).destinazione != r.area)
                {
                    continue;
                }

                mondo::Esploratore e = fino_alla_cella(mondo::AreaId(r.area), mondo::varco_di(da, v).spawn, r.tx, r.ty);

                if(e.x < 0 || raccolta_toccata(p, r.area, e.x, e.y) != k)
                {
                    return false;
                }

                ++ingressi;
            }
        }

        return ingressi > 0;
    }

    static_assert(raggiungibile_da_ogni_ingresso(0) && raggiungibile_da_ogni_ingresso(1) && raggiungibile_da_ogni_ingresso(2),
                  "un blocco di ferro del Teatro non si raggiunge camminando");
    static_assert(raggiungibile_da_ogni_ingresso(3) && raggiungibile_da_ogni_ingresso(4), "una radice non si raggiunge camminando");
    static_assert(raggiungibile_da_ogni_ingresso(5) && raggiungibile_da_ogni_ingresso(6), "una radice non si raggiunge camminando");

    // Negativa: dentro il muro del Teatro (la cavea) non si arriva; e lontano dall'oggetto non lo si tocca.
    static_assert(fino_alla_cella(mondo::AreaId::TEATRO_ROMANO, 0, 30, 30).x < 0, "negativa: si cammina dentro la cavea");
    static_assert(raccolta_toccata(guardie_battute(), RACCOLTA[0].area, mondo::piedi_x(RACCOLTA[0].tx) + DISTANZA_RACCOLTA,
                                   mondo::piedi_y(RACCOLTA[0].ty)) == -1 &&
                  raccolta_toccata(guardie_battute(), RACCOLTA[0].area, mondo::piedi_x(RACCOLTA[0].tx) + DISTANZA_RACCOLTA - 1,
                                   mondo::piedi_y(RACCOLTA[0].ty)) == 0,
                  "il contatto con un oggetto non e' DISTANZA_RACCOLTA");

    // --- Le guardie delle fornaci (F10, Q-SM01) ---------------------------------------------------------
    // Una guardia per blocco di ferro, ognuna davanti al suo, con la sua bandiera nell'intervallo quest e libera.
    consteval bool guardie_al_loro_posto()
    {
        for(int g = 0; g < GUARDIE_FORNACE; ++g)
        {
            const GuardiaFornace& gu = GUARDIA_FORNACE[g];
            const Raccolta& r = RACCOLTA[gu.raccolta];
            int dx = gu.tx - r.tx;
            int dy = gu.ty - r.ty;
            int lontano = (dx < 0 ? -dx : dx) > (dy < 0 ? -dy : dy) ? (dx < 0 ? -dx : dx) : (dy < 0 ? -dy : dy);

            if(r.quest != 0 || gu.area != r.area || lontano != 2 || gu.bandiera != GUARDIA_FORNACE_1 + g ||
               gu.bandiera <= FORZIERE_BISCOTTI || gu.raccolta != g)
            {
                return false;
            }
        }

        return GUARDIE_FORNACE == QUEST_GIOCO[0].pezzi;
    }

    static_assert(guardie_al_loro_posto(), "le guardie delle fornaci non stanno davanti ai loro blocchi");

    // Ci si arriva camminando da ogni ingresso del Teatro, su un posto buono, e arrivati la si tocca.
    consteval bool guardia_raggiungibile(int g)
    {
        const GuardiaFornace& gu = GUARDIA_FORNACE[g];
        int ingressi = 0;

        for(int d = 0; d < mondo::AREE_CONTEGGIO; ++d)
        {
            const mondo::Area& da = mondo::area(mondo::AreaId(d));

            for(int v = 0; v < da.varchi; ++v)
            {
                if(mondo::varco_di(da, v).destinazione != gu.area)
                {
                    continue;
                }

                mondo::Esploratore e = fino_alla_cella(mondo::AreaId(gu.area), mondo::varco_di(da, v).spawn, gu.tx, gu.ty);

                if(e.x < 0 || guardia_toccata(GameState{}, gu.area, e.x, e.y) != g)
                {
                    return false;
                }

                ++ingressi;
            }
        }

        return ingressi > 0 && progressione::posto_valido(mondo::AreaId(gu.area), gu.tx, gu.ty);
    }

    static_assert(guardia_raggiungibile(0) && guardia_raggiungibile(1) && guardia_raggiungibile(2),
                  "una guardia delle fornaci non si raggiunge camminando");

    // Davanti a una guardia in piedi il blocco non si prende (ne' toccandolo ne' con raccogli); battuta, si'. La
    // guardia battuta non si tocca piu' e non si batte due volte; le radici non hanno guardie.
    consteval bool il_blocco_aspetta_la_guardia()
    {
        GameState p = {};
        const Raccolta& r = RACCOLTA[0];
        const GuardiaFornace& gu = GUARDIA_FORNACE[0];
        int x = mondo::piedi_x(r.tx);
        int y = mondo::piedi_y(r.ty);
        bool chiuso = raccolta_presente(p, 0) && ! raccolta_libera(p, 0) && raccolta_toccata(p, r.area, x, y) == -1 &&
                      ! raccogli(p, 0) && pezzi_raccolti(p, 0) == 0 && raccolta_libera(p, 3);
        bool toccata = guardia_toccata(p, gu.area, mondo::piedi_x(gu.tx) + progressione::DISTANZA_CONTATTO - 1,
                                       mondo::piedi_y(gu.ty)) == 0 &&
                       guardia_toccata(p, gu.area, mondo::piedi_x(gu.tx) + progressione::DISTANZA_CONTATTO,
                                       mondo::piedi_y(gu.ty)) == -1 &&
                       guardia_toccata(p, int(mondo::AreaId::PIAZZA_GRANDE), mondo::piedi_x(gu.tx), mondo::piedi_y(gu.ty)) == -1;
        bool battuta = batti_la_guardia(p, 0) && ! batti_la_guardia(p, 0) && ! guardia_presente(p, 0) &&
                       guardia_toccata(p, gu.area, mondo::piedi_x(gu.tx), mondo::piedi_y(gu.ty)) == -1 &&
                       accesa(p, int(GUARDIA_FORNACE_1)) && ! accesa(p, int(GUARDIA_FORNACE_2));
        bool libero = raccolta_libera(p, 0) && raccolta_toccata(p, r.area, x, y) == 0 && ! raccolta_libera(p, 1) &&
                      raccogli(p, 0) && pezzi_raccolti(p, 0) == 1;
        return chiuso && toccata && battuta && libero && ! batti_la_guardia(p, -1) && ! batti_la_guardia(p, GUARDIE_FORNACE);
    }

    static_assert(il_blocco_aspetta_la_guardia(), "il blocco di ferro non aspetta la sua guardia");

    // Negativa: senza battere la guardia, il blocco toccato camminando non si prende.
    consteval bool blocco_senza_guardia_battuta()
    {
        GameState p = {};
        const Raccolta& r = RACCOLTA[1];
        mondo::Esploratore e = fino_alla_cella(mondo::AreaId(r.area), 0, r.tx, r.ty);
        return e.x >= 0 && raccolta_toccata(p, r.area, e.x, e.y) == 1;
    }

    static_assert(! blocco_senza_guardia_battuta(), "negativa: il blocco si prende con la guardia in piedi");

    // La battaglia dell'infiltrato e' la sua (F10): l'infiltrato e due spie umbre, non piu' l'Imboscata.
    static_assert(INFILTRATO.incontro == battaglia::INCONTRO_INFILTRATO && INFILTRATO.incontro != 1 &&
                  battaglia::INCONTRO[INFILTRATO.incontro].nemici == 3 &&
                  battaglia::INCONTRO[INFILTRATO.incontro].schieramento[0] == battaglia::NemicoId::INFILTRATO &&
                  battaglia::INCONTRO[INFILTRATO.incontro].schieramento[1] == battaglia::NemicoId::SPIA_UMBRA &&
                  battaglia::INCONTRO[INFILTRATO.incontro].schieramento[2] == battaglia::NemicoId::SPIA_UMBRA,
                  "l'infiltrato e due spie umbre");

    // I datori e l'infiltrato stanno su un posto buono (la cella e le otto intorno calpestabili, nessun varco,
    // lontano dagli spawn) e ci si arriva camminando dallo spawn 0 della loro area.
    consteval bool ci_si_arriva(int area, int tx, int ty)
    {
        mondo::Esploratore e = fino_alla_cella(mondo::AreaId(area), 0, tx, ty);
        return progressione::posto_valido(mondo::AreaId(area), tx, ty) && e.x == mondo::piedi_x(tx) && e.y == mondo::piedi_y(ty);
    }

    static_assert(ci_si_arriva(QUEST_GIOCO[0].area, QUEST_GIOCO[0].tx, QUEST_GIOCO[0].ty) &&
                  ci_si_arriva(QUEST_GIOCO[1].area, QUEST_GIOCO[1].tx, QUEST_GIOCO[1].ty) &&
                  ci_si_arriva(QUEST_GIOCO[2].area, QUEST_GIOCO[2].tx, QUEST_GIOCO[2].ty) &&
                  ci_si_arriva(INFILTRATO.area, INFILTRATO.tx, INFILTRATO.ty), "un datore o l'infiltrato fuori posto");
    static_assert(QUEST_GIOCO[0].area == QUEST_V1[0].consegna && QUEST_GIOCO[1].area == QUEST_V1[1].consegna &&
                  QUEST_GIOCO[2].area == QUEST_V1[2].consegna && INFILTRATO.area == int(mondo::AreaId::PIAZZA_QUARANTA_MARTIRI),
                  "i datori stanno dove si consegna: San Martino, Sant'Andrea, San Pietro; l'infiltrato alle Logge");
    static_assert(! ci_si_arriva(int(mondo::AreaId::TEATRO_ROMANO), 30, 30), "negativa: un posto nella cavea risulta buono");

    // --- Le tre quest giocate dall'inizio alla fine ----------------------------------------------------

    // Le righe di raccolta della quest q che valgono adesso, come bit (il bit i e' la riga i della sezione).
    consteval uint32_t righe_di_raccolta(const GameState& p, int q)
    {
        const Righe& r = QUEST_GIOCO[q].raccolta;
        uint32_t v = 0;

        for(int i = 0; i < r.quante; ++i)
        {
            v |= vale(p, FRASE_QUEST[r.prima + i].guardia, -1) ? (uint32_t(1) << i) : 0;
        }

        return v;
    }

    struct Giro
    {
        bool proposta = false;          // il datore comincia dalla proposta
        bool non_presa_rifiutata = false;   // prima di prenderla non si consegna
        bool attesa = false;
        bool a_meta_rifiutata = false;      // con l'obiettivo a meta' non si consegna
        bool pezzi = false;             // ogni pezzo raccolto camminando (o la Rosa dall'infiltrato)
        bool consegna = false;
        bool seconda_rifiutata = false;
        bool dopo = false;
        bool righe = false;             // le righe di raccolta giuste a ogni pezzo
    };

    // La quest q giocata dallo stato p: si parla col datore, si raccoglie camminando (la collisione vera,
    // dall'ingresso della sua area), si torna a consegnare, si riprova.
    consteval Giro gioca_la_quest(GameState p, int q)
    {
        Giro g;
        bool saliti[battaglia::EROI] = {};
        g.proposta = momento_del_datore(p, q) == Momento::PROPOSTA;
        g.non_presa_rifiutata = ! consegna_quest(p, q, saliti) && ! presa(p, q);
        g.attesa = prendi_quest(p, q) && ! prendi_quest(p, q) && momento_del_datore(p, q) == Momento::ATTESA;
        g.a_meta_rifiutata = ! consegna_quest(p, q, saliti);
        g.pezzi = true;
        g.righe = true;

        if(q == QUEST_DEGLI_INDIZI)
        {
            // gli indizi dai tre NPC (in ordine qualunque), poi l'infiltrato e la sua battaglia
            for(int k = 0; k < INDIZI; ++k)
            {
                g.pezzi = g.pezzi && ! infiltrato_presente(p) && indizio_dell_npc(p, INDIZIO[k].npc) == k &&
                          trova_indizio(p, k) == (k == INDIZI - 1);
            }

            g.pezzi = g.pezzi && infiltrato_presente(p) && ! obiettivo_fatto(p, q) && riprendi_la_rosa(p) &&
                      ! infiltrato_presente(p) && ! riprendi_la_rosa(p) && indizio_dell_npc(p, INDIZIO[0].npc) < 0;
        }
        else
        {
            int n = 0;

            for(int k = 0; k < RACCOLTE; ++k)
            {
                if(RACCOLTA[k].quest != q)
                {
                    continue;
                }

                // Q-SM01: prima la guardia della fornace, camminando fino a toccarla, e la sua battaglia vinta
                for(int gu = 0; gu < GUARDIE_FORNACE; ++gu)
                {
                    const GuardiaFornace& gf = GUARDIA_FORNACE[gu];

                    if(gf.raccolta == k)
                    {
                        mondo::Esploratore eg = fino_alla_cella(mondo::AreaId(gf.area), 0, gf.tx, gf.ty);
                        g.pezzi = g.pezzi && eg.x >= 0 && guardia_toccata(p, gf.area, eg.x, eg.y) == gu &&
                                  batti_la_guardia(p, gu);
                    }
                }

                // camminando dallo spawn 0 dell'area fino a toccarlo
                const Raccolta& r = RACCOLTA[k];
                mondo::Esploratore e = fino_alla_cella(mondo::AreaId(r.area), 0, r.tx, r.ty);
                int toccato = e.x < 0 ? -1 : raccolta_toccata(p, r.area, e.x, e.y);
                g.pezzi = g.pezzi && toccato == k && raccogli(p, toccato) && ! raccogli(p, toccato) &&
                          raccolta_toccata(p, r.area, e.x, e.y) == -1;
                ++n;

                // Q-SM01: la riga n di SISTEMA («Ancora 2», «Ancora 1», «l'ultimo») e, al primo, Antonio;
                // Q-SA01: la riga di SISTEMA sempre, Antonio al primo (Ubaldo no: la quest e' presa)
                uint32_t attese = q == 0 ? ((uint32_t(1) << (n - 1)) | (n == 1 ? 8u : 0u)) : (1u | (n == 1 ? 2u : 0u));
                g.righe = g.righe && righe_di_raccolta(p, q) == attese;
            }

            g.pezzi = g.pezzi && n == QUEST_GIOCO[q].pezzi;
        }

        g.consegna = momento_del_datore(p, q) == Momento::CONSEGNA && consegna_quest(p, q, saliti);
        g.seconda_rifiutata = ! consegna_quest(p, q, saliti) && accesa(p, int(QUEST_V1[q].consegnata));
        g.dopo = momento_del_datore(p, q) == Momento::DOPO && righe_del_datore(p, q, Momento::DOPO).quante > 0 &&
                 ! prendi_quest(p, q);
        return g;
    }

    consteval bool tutto(const Giro& g)
    {
        return g.proposta && g.non_presa_rifiutata && g.attesa && g.a_meta_rifiutata && g.pezzi && g.consegna &&
               g.seconda_rifiutata && g.dopo && g.righe;
    }

    // Con Antonio nel gruppo (dopo A1-04), nel digiuno e nella notte dopo B-05 (dopo_il_rientro).
    consteval GameState nel_digiuno()
    {
        GameState p = {};
        progressione::partita_nuova(p);
        accendi(p, DIGIUNO | (uint64_t(1) << int(Bandiera::ANTONIO_NEL_GRUPPO)));
        return p;
    }

    static_assert(tutto(gioca_la_quest(nel_digiuno(), 0)), "Q-SM01 non si gioca dall'inizio alla fine nel digiuno");
    static_assert(tutto(gioca_la_quest(nel_digiuno(), 1)), "Q-SA01 non si gioca dall'inizio alla fine nel digiuno");
    static_assert(tutto(gioca_la_quest(nel_digiuno(), 2)), "Q-SP01 non si gioca dall'inizio alla fine nel digiuno");
    static_assert(tutto(gioca_la_quest(dopo_il_rientro(), 1)), "Q-SA01 non si gioca dopo B-05 (la gola resta aperta)");
    static_assert(tutto(gioca_la_quest(dopo_il_rientro(), 2)), "Q-SP01 non si gioca nella notte");

    // Q-SM01 dall'ultimatum, prima del digiuno: si prende e si consegna, e il dopo ha la sua riga ULTIMATUM.
    consteval GameState all_ultimatum()
    {
        GameState p = {};
        progressione::partita_nuova(p);
        accendi(p, (uint64_t(1) << int(Bandiera::ULTIMATUM_RICEVUTO)) | (uint64_t(1) << int(Bandiera::ANTONIO_NEL_GRUPPO)));
        return p;
    }

    static_assert(tutto(gioca_la_quest(all_ultimatum(), 0)), "Q-SM01 non si gioca nell'ultimatum");

    // Negative: prima che si prenda (Q-SA01 nell'ultimatum) il datore non c'e' e non si propone; dopo E-01 nemmeno.
    static_assert(! gioca_la_quest(all_ultimatum(), 1).proposta && momento_del_datore(all_ultimatum(), 1) == Momento::ASSENTE,
                  "negativa: Agnese propone la quest prima del digiuno");

    consteval Momento dopo_e01(int q)
    {
        GameState p = nel_digiuno();
        accendi_bandiera(p, Bandiera::ATTO_I_COMPLETATO);
        completa(p, q);
        return momento_del_datore(p, q);
    }

    static_assert(dopo_e01(0) == Momento::ASSENTE && dopo_e01(2) == Momento::ASSENTE, "negativa: si consegna dopo E-01");

    // Una quest non si consegna senza l'obiettivo: con 3 radici su 4, o con 2 blocchi su 3, Agnese e Raniero
    // aspettano; con l'obiettivo finito ma senza averla presa, nemmeno.
    consteval bool senza_obiettivo(int q)
    {
        GameState p = nel_digiuno();
        prendi_quest(p, q);

        for(int i = 0; i + 1 < QUEST_GIOCO[q].pezzi; ++i)
        {
            accendi_una(p, QUEST_GIOCO[q].primo_pezzo + i);
        }

        bool saliti[battaglia::EROI] = {};
        return momento_del_datore(p, q) == Momento::ATTESA && ! quest_pronta(p, q) && ! consegna_quest(p, q, saliti) &&
               p.esperienza[0] == 0 && ! accesa(p, int(QUEST_V1[q].consegnata));
    }

    static_assert(senza_obiettivo(0) && senza_obiettivo(1) && senza_obiettivo(2), "una quest si consegna senza l'obiettivo");

    consteval bool obiettivo_senza_presa(int q)
    {
        GameState p = nel_digiuno();

        for(int i = 0; i < QUEST_GIOCO[q].pezzi; ++i)
        {
            accendi_una(p, QUEST_GIOCO[q].primo_pezzo + i);
        }

        bool saliti[battaglia::EROI] = {};
        bool rifiutata = ! consegna_quest(p, q, saliti) && momento_del_datore(p, q) == Momento::PROPOSTA;

        // presa la quest con l'obiettivo gia' finito, la consegna segue subito la proposta
        return rifiutata && prendi_quest(p, q) && momento_del_datore(p, q) == Momento::CONSEGNA && consegna_quest(p, q, saliti);
    }

    static_assert(obiettivo_senza_presa(0) && obiettivo_senza_presa(1), "con l'obiettivo gia' fatto la consegna non segue la proposta");

    // Le righe della prima radice senza la quest presa: SISTEMA, Antonio e Ubaldo («Prendiamolo»). Il primo
    // blocco senza Antonio nel gruppo: solo SISTEMA. Negativa: alla seconda radice, Ubaldo non parla piu'.
    consteval uint32_t prima_raccolta(int q, bool antonio, int quante)
    {
        GameState p = guardie_battute();
        accendi(p, DIGIUNO | (antonio ? uint64_t(1) << int(Bandiera::ANTONIO_NEL_GRUPPO) : 0));

        for(int k = 0, n = 0; k < RACCOLTE && n < quante; ++k)
        {
            if(RACCOLTA[k].quest == q)
            {
                raccogli(p, k);
                ++n;
            }
        }

        return righe_di_raccolta(p, q);
    }

    static_assert(prima_raccolta(1, true, 1) == 7u && prima_raccolta(0, false, 1) == 1u && prima_raccolta(0, true, 1) == 9u,
                  "le righe della prima raccolta");
    static_assert(prima_raccolta(1, true, 2) == 1u && prima_raccolta(0, true, 3) == 4u,
                  "negativa: Ubaldo o Antonio parlano anche dopo il primo pezzo");

    // Gli indizi: senza la quest presa nessun NPC li dice e l'infiltrato non c'e'; con due su tre nemmeno lui.
    consteval bool indizi_senza_quest()
    {
        GameState p = nel_digiuno();

        for(const Indizio& i : INDIZIO)
        {
            if(indizio_dell_npc(p, i.npc) >= 0)
            {
                return false;
            }

            accendi_una(p, i.bandiera);
        }

        return ! infiltrato_presente(p) && ! riprendi_la_rosa(p) && indizio_dell_npc(p, 0) < 0;
    }

    static_assert(indizi_senza_quest(), "negativa: gli indizi o l'infiltrato senza Q-SP01 presa");

    consteval bool due_indizi()
    {
        GameState p = nel_digiuno();
        prendi_quest(p, QUEST_DEGLI_INDIZI);
        trova_indizio(p, 0);
        trova_indizio(p, 2);
        return ! infiltrato_presente(p) && ! riprendi_la_rosa(p) && indizi_trovati(p) == 2;
    }

    static_assert(due_indizi(), "negativa: l'infiltrato compare con due indizi");

    // Giordano: l'indizio di Q-SP01 si dice dopo la sua battuta del DIGIUNO (che accende INDIZIO_ACQUA): il
    // gioco recita prima le battute della fase, poi l'indizio (README del copione, T7).
    static_assert(NPC_AMBIENTE[INDIZIO[2].npc].imposta == INDIZIO_ACQUA && INDIZIO[2].bandiera == INDIZIO_FONTANIERE,
                  "il terzo indizio e' di Giordano, che accende INDIZIO_ACQUA");

    // La gola dopo B-05: dalla notte si esce da Porta Metauro, si risale la gola fino all'arco e ogni radice si
    // raccoglie camminando dall'ingresso di ogni stanza (raggiungibile_da_ogni_ingresso), con la storia finita
    // fino al rientro. Le radici non leggono la storia: ci sono anche nella notte.
    consteval bool radici_nella_notte()
    {
        GameState p = dopo_il_rientro();

        for(int k = 0; k < RACCOLTE; ++k)
        {
            if(RACCOLTA[k].quest == 1 && ! raccolta_presente(p, k))
            {
                return false;
            }
        }

        return cammina(DA_PORTA_METAURO, 11) && fase_npc(p) == Fase::NOTTE && momento_del_datore(p, 1) == Momento::PROPOSTA;
    }

    static_assert(radici_nella_notte(), "dopo B-05 le radici non ci sono o Agnese non propone piu' la quest");

    // Con le tre quest e tutte le battaglie facoltative (le tre guardie delle fornaci, l'infiltrato con le sue spie)
    // e i Guerrieri di B-03 si arriva a Corrado ancora al livello 6 (docs/bilanciamento.md: 316 + 165 + 60 + 84 + 40
    // = 665 punti, il 7 e' a 680).
    static_assert(progressione::esperienza_incontro(battaglia::INCONTRO_FORNACE) * 3 +
                  progressione::esperienza_incontro(battaglia::INCONTRO_INFILTRATO) +
                  progressione::esperienza_incontro(battaglia::INCONTRO_GUERRIERI) == 184, "l'esperienza delle battaglie di F10");

    consteval int livello_con_l_infiltrato()
    {
        GameState p = {};
        progressione::partita_nuova(p);
        bool saliti[battaglia::EROI] = {};
        // Pattuglia, Imboscata, Spettri, le tre guardie delle fornaci, l'infiltrato, i Guerrieri di B-03 (F10)
        const int prima_di_corrado[8] = { 0, 1, 3, battaglia::INCONTRO_FORNACE, battaglia::INCONTRO_FORNACE,
                                          battaglia::INCONTRO_FORNACE, battaglia::INCONTRO_INFILTRATO,
                                          battaglia::INCONTRO_GUERRIERI };

        for(int incontro : prima_di_corrado)
        {
            progressione::assegna_esperienza(p, incontro, saliti);
        }

        accendi(p, DIGIUNO);

        for(int q = 0; q < QUEST; ++q)
        {
            completa(p, q);
            consegna_quest(p, q, saliti);
        }

        return p.livello[0];
    }

    static_assert(livello_con_l_infiltrato() == 6, "con le battaglie facoltative si arriva a Corrado oltre il livello 6");

    // Negativa: con un'altra guardia di fornace (20 punti in piu') si passerebbe al livello 7 prima di Corrado: il
    // margine e' stretto, chi aggiunge un nemico facoltativo deve rifare i conti.
    consteval int livello_con_un_altra_guardia()
    {
        GameState p = {};
        progressione::partita_nuova(p);
        bool saliti[battaglia::EROI] = {};
        progressione::assegna_esperienza_fissa(p, 316 + 3 * progressione::ESPERIENZA_QUEST + 184 +
                                                  progressione::esperienza_incontro(battaglia::INCONTRO_FORNACE), saliti);
        return p.livello[0];
    }

    static_assert(livello_con_un_altra_guardia() == 7, "negativa: il margine prima del livello 7 non e' quello atteso");
}

}
