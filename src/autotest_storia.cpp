// Autotest della storia a tempo di compilazione (include/storia_logica.h, include/storia.h generato
// dal copione v2): il runner gira dalla prima scena ai titoli di coda senza camminare, visita ogni
// scena una volta sola e arriva a CRONACA_V1_FINITA. Se una scena resta fuori, la ROM non compila.
// Negativa: una scena che chiede una bandiera che nessuno accende resta non visitata.

#include "battaglia.h"
#include "storia_logica.h"

namespace gubbio
{

namespace
{
    using namespace storia;

    consteval bool tutta_la_storia()
    {
        GameState p = {};
        int visitate = gioca_tutta(p);

        for(int k = 0; k < SCENE; ++k)
        {
            if(! fatta(p, k))
            {
                return false;
            }
        }

        return visitate == SCENE && accesa(p, Bandiera::CRONACA_V1_FINITA) && accesa(p, Bandiera::CORRADO_SCONFITTO);
    }

    static_assert(tutta_la_storia(), "il runner della storia non visita ogni scena fino ai titoli di coda");

    consteval bool stesso_codice(const char* a, const char* b)
    {
        int i = 0;

        while(a[i] && b[i] && a[i] == b[i])
        {
            ++i;
        }

        return a[i] == b[i];
    }

    // L'ordine: il prologo prima di tutto, l'ultimatum prima di Antonio, Corrado prima del rientro.
    consteval int ordine(const char* a, const char* b)
    {
        GameState p = {};
        int pos_a = -1;
        int pos_b = -1;
        int passo = 0;
        bool avanti = true;

        while(avanti)
        {
            avanti = false;

            for(int area = NESSUNA_AREA; area < mondo::AREE_CONTEGGIO && ! avanti; ++area)
            {
                int k = prossima_scena(p, area);

                if(k >= 0)
                {
                    pos_a = stesso_codice(SCENA[k].codice, a) ? passo : pos_a;
                    pos_b = stesso_codice(SCENA[k].codice, b) ? passo : pos_b;
                    chiudi_scena(p, k);
                    ++passo;
                    avanti = true;
                }
            }

            if(! avanti)
            {
                avanti = risposta_di_un_npc(p);     // la conferma dell'alba, dal console Guido
            }
        }

        return pos_a >= 0 && pos_b >= 0 && pos_a < pos_b ? 1 : 0;
    }

    static_assert(ordine("P-02", "A1-01") && ordine("A1-01", "A1-04") && ordine("B-04", "B-05") &&
                  ordine("E-01", "E-02"), "le scene non vengono nell'ordine del copione");
    static_assert(! ordine("E-02", "P-01"), "la negativa dell'ordine non regge");

    // Negativa: una copia della tabella in cui A1-06 chiede una bandiera che nessuno accende
    // (CRONACA_V1_FINITA, che arriva solo alla fine): da li' in poi niente si visita.
    struct Tabella
    {
        Scena scene[SCENE];
    };

    consteval Tabella guasta()
    {
        Tabella t = {};

        for(int k = 0; k < SCENE; ++k)
        {
            t.scene[k] = SCENA[k];

            if(stesso_codice(SCENA[k].codice, "A1-06"))
            {
                t.scene[k].richieste |= uint64_t(1) << int(Bandiera::CRONACA_V1_FINITA);
            }
        }

        return t;
    }

    consteval int visitate_con_la_tabella_guasta()
    {
        Tabella t = guasta();
        GameState p = {};
        return gioca_tutta(p, t.scene, SCENE);
    }

    static_assert(visitate_con_la_tabella_guasta() < SCENE, "la negativa della storia non regge");

    // Le fasi degli NPC.
    consteval bool fasi()
    {
        GameState p = {};

        if(fase_npc(p) != Fase::ULTIMATUM)
        {
            return false;
        }

        accendi(p, uint64_t(1) << int(Bandiera::CITTA_IN_DIGIUNO));

        if(fase_npc(p) != Fase::DIGIUNO)
        {
            return false;
        }

        accendi(p, uint64_t(1) << int(Bandiera::RIENTRO_PORTA_METAURO));
        return fase_npc(p) == Fase::NOTTE;
    }

    static_assert(fasi(), "le fasi degli NPC");

    // I nemici sulla mappa seguono la storia: la Pattuglia c'e' solo con la postierla aperta e prima
    // che Antonio sia salvato. Negativa: all'inizio della partita non c'e'.
    consteval bool pattuglia_quando_serve()
    {
        GameState p = {};

        if(scontro_attivo(p, INCONTRO_DEL_TEATRO))
        {
            return false;
        }

        accendi(p, uint64_t(1) << int(Bandiera::POSTIERLA_APERTA));

        if(! scontro_attivo(p, INCONTRO_DEL_TEATRO))
        {
            return false;
        }

        chiudi_scena(p, scena_dello_scontro(INCONTRO_DEL_TEATRO));
        return ! scontro_attivo(p, INCONTRO_DEL_TEATRO) && accesa(p, Bandiera::ANTONIO_NEL_GRUPPO);
    }

    static_assert(pattuglia_quando_serve(), "la Pattuglia sulla mappa non segue la storia");
    static_assert(scena_dello_scontro(0) >= 0 && scena_dello_scontro(1) >= 0 && scena_dello_scontro(2) >= 0,
                  "ogni scontro sulla mappa ha la sua scena");

    // Il gruppo: Ubaldo sempre, Giorgio dall'ultimatum, Antonio ospite al Teatro e poi nel gruppo.
    consteval bool gruppo_della_storia()
    {
        GameState p = {};

        if(gruppo(p, 1) != 0b001 || gruppo(p, INCONTRO_DEL_TEATRO) != 0b101)
        {
            return false;
        }

        accendi(p, uint64_t(1) << int(Bandiera::GIORGIO_NEL_GRUPPO));

        if(gruppo(p, 1) != 0b011)
        {
            return false;
        }

        accendi(p, uint64_t(1) << int(Bandiera::ANTONIO_NEL_GRUPPO));
        return gruppo(p, 2) == 0b111;
    }

    static_assert(gruppo_della_storia(), "il gruppo in battaglia non segue la storia");

    // Chi non e' nel gruppo non agisce mai in battaglia. Negativa: con tutti presenti Giorgio agisce.
    consteval bool agisce(uint8_t presenti, int eroe)
    {
        battaglia::Battaglia b(1, 3);
        b.ricomincia(1, 3, false, nullptr, presenti);

        while(b.avanza())
        {
            if(b.fase() != battaglia::Fase::ESITO)
            {
                continue;
            }

            for(int i = 0; i < b.eventi_round(); ++i)
            {
                if(! b.evento(i).attore_nemico && b.evento(i).attore == eroe)
                {
                    return true;
                }
            }
        }

        return false;
    }

    static_assert(! agisce(0b001, battaglia::GIORGIO) && ! agisce(0b001, battaglia::ANTONIO) && agisce(0b001, battaglia::UBALDO),
                  "un Santo fuori dal gruppo ha agito");
    static_assert(agisce(0b111, battaglia::GIORGIO), "la negativa del gruppo non regge");

    // Le guardie del copione v2, tutte quelle della tabella: con la bandiera accesa e spenta, con la
    // voce giusta e quella sbagliata, con due indizi e con uno, con la Crescia e senza.
    consteval bool guardie()
    {
        for(int i = 0; i < GUARDIE; ++i)
        {
            const Guardia& g = GUARDIA[i];
            GameState vuoto = {};
            GameState con = {};

            switch(g.tipo)
            {
                case TipoGuardia::SEMPRE:
                    if(! vale(vuoto, i, -1))
                    {
                        return false;
                    }
                    break;
                case TipoGuardia::BANDIERA:
                case TipoGuardia::VARIANTE_BANDIERA:
                    accendi_una(con, g.a);
                    if(! vale(con, i, -1) || vale(vuoto, i, -1))
                    {
                        return false;
                    }
                    break;
                case TipoGuardia::NON_BANDIERA:
                case TipoGuardia::VARIANTE_NON_BANDIERA:
                    accendi_una(con, g.a);
                    if(vale(con, i, -1) || ! vale(vuoto, i, -1))
                    {
                        return false;
                    }
                    break;
                case TipoGuardia::SCELTA:
                    if(! vale(vuoto, i, g.a) || vale(vuoto, i, 1 - g.a) || vale(vuoto, i, -1))
                    {
                        return false;
                    }
                    break;
                case TipoGuardia::ALMENO_DUE:
                    accendi_una(con, g.a);
                    if(vale(con, i, -1))
                    {
                        return false;
                    }
                    accendi_una(con, g.c);
                    if(! vale(con, i, -1))
                    {
                        return false;
                    }
                    break;
                case TipoGuardia::OGGETTO_E_NON_BANDIERA:
                    con.oggetti[g.a] = 1;
                    if(! vale(con, i, -1) || vale(vuoto, i, -1))
                    {
                        return false;
                    }
                    accendi_una(con, g.b);
                    if(vale(con, i, -1))
                    {
                        return false;
                    }
                    break;
                // le guardie delle quest (pezzi raccolti): con zero pezzi vale solo se ne chiede zero; con tutti i
                // pezzi della quest vale solo se ne chiede tanti; la bandiera c le accende (CONTEGGIO) o le spegne
                case TipoGuardia::CONTEGGIO:
                case TipoGuardia::CONTEGGIO_E_NON_BANDIERA:
                {
                    const bool non = g.tipo == TipoGuardia::CONTEGGIO_E_NON_BANDIERA;
                    if(g.c != NESSUNA_BANDIERA && ! non)
                    {
                        accendi_una(con, g.c);
                    }
                    if(vale(con, i, -1) != (g.b == 0))
                    {
                        return false;
                    }
                    const QuestGioco& q = QUEST_GIOCO[g.a];
                    for(int k = 0; k < q.pezzi; ++k)
                    {
                        accendi_una(con, q.primo_pezzo + k);
                    }
                    if(vale(con, i, -1) != (g.b == q.pezzi))
                    {
                        return false;
                    }
                    if(g.c != NESSUNA_BANDIERA)
                    {
                        // tutti i pezzi ma la bandiera c dalla parte sbagliata: non vale
                        GameState altro = {};
                        for(int k = 0; k < q.pezzi; ++k)
                        {
                            accendi_una(altro, q.primo_pezzo + k);
                        }
                        if(non)
                        {
                            accendi_una(altro, g.c);
                        }
                        if(g.b == q.pezzi && vale(altro, i, -1))
                        {
                            return false;
                        }
                    }
                    break;
                }
                default:
                    return false;
            }
        }

        return GUARDIE > 1;
    }

    static_assert(guardie(), "una guardia del copione v2 non fa quel che dice");

    // Negativa: un solo indizio non basta per la conferma della visione (A1-09).
    consteval bool guardie_guaste()
    {
        for(int i = 0; i < GUARDIE; ++i)
        {
            if(GUARDIA[i].tipo == TipoGuardia::ALMENO_DUE)
            {
                GameState p = {};
                accendi_una(p, GUARDIA[i].b);
                return vale(p, i, -1);
            }
        }

        return true;
    }

    static_assert(! guardie_guaste(), "la negativa delle guardie non regge");

    // Chi sale agli Stradoni durante il digiuno senza aver deciso del borgo l'ha lasciato fuori; chi ha
    // deciso no, e altrove non succede niente.
    consteval bool borgo_dimenticato()
    {
        GameState p = {};
        accendi(p, uint64_t(1) << int(Bandiera::CITTA_IN_DIGIUNO));
        GameState q = p;
        GameState r = p;
        all_ingresso(p, int(mondo::AreaId::MONTE_INGINO));
        accendi(q, uint64_t(1) << int(Bandiera::BORGO_DENTRO));
        all_ingresso(q, int(mondo::AreaId::MONTE_INGINO));
        all_ingresso(r, int(mondo::AreaId::SAN_PIETRO));
        return accesa(p, Bandiera::BORGO_FUORI) && ! accesa(q, Bandiera::BORGO_FUORI) && ! accesa(r, Bandiera::BORGO_FUORI);
    }

    static_assert(borgo_dimenticato(), "il borgo dimenticato non resta fuori");

    // Tutta la storia con ogni menu sulla prima voce, poi sulla seconda: ogni scena una volta, e le
    // bandiere dei dilemmi D1, D2 e D4 come le voci.
    consteval bool scelte_di_tutta_la_storia(int voce)
    {
        GameState p = {};
        int visitate = gioca_tutta(p, SCENA, SCENE, voce);
        bool prima = voce == 0;
        return visitate == SCENE && accesa(p, Bandiera::CRONACA_V1_FINITA) &&
               accesa(p, Bandiera::BORGO_DENTRO) == prima && accesa(p, Bandiera::BORGO_FUORI) == ! prima &&
               accesa(p, Bandiera::ESULE_PRIGIONIERO) == prima && accesa(p, Bandiera::ESULE_LIBERATO) == ! prima &&
               accesa(p, Bandiera::GIUSTIZIA_OFFERTA) == prima;
    }

    static_assert(scelte_di_tutta_la_storia(0), "la storia con le prime voci");
    static_assert(scelte_di_tutta_la_storia(1), "la storia con le seconde voci");

    // F10, C7S: la cartolina degli Stradoni parte entrando nel Monte Ingino con A1-07 pronta (dopo A1-06,
    // PORTA_DEL_MONTE), prima di toccare l'Imboscata (il nemico c'e' ancora); una volta sola. Negative: in
    // un'altra area, prima di A1-06, gia' vista, a scena fatta (il nemico toccato e la scena chiusa) non parte.
    consteval int scena_col_codice(const char* codice)
    {
        for(int k = 0; k < SCENE; ++k)
        {
            if(stesso_codice(SCENA[k].codice, codice))
            {
                return k;
            }
        }

        return -1;
    }

    consteval GameState fino_a(const char* ultima)
    {
        GameState p = {};
        progressione::partita_nuova(p);

        for(int k = 0; k <= scena_col_codice(ultima); ++k)
        {
            chiudi_scena(p, k);
        }

        return p;
    }

    consteval int regia_col_codice(const char* codice)
    {
        for(int c = 0; c < regia::CUTSCENE; ++c)
        {
            if(stesso_codice(regia::CUTSCENE_DATI[c].codice, codice))
            {
                return c;
            }
        }

        return -1;
    }

    constexpr int MONTE = int(mondo::AreaId::MONTE_INGINO);
    constexpr int C7S = regia_col_codice("C7S");

    static_assert(C7S >= 0 && INGRESSI == 1 && INGRESSO[0].scena == scena_col_codice("A1-07") && INGRESSO[0].regia == C7S,
                  "C7S non e' la cartolina all'ingresso di A1-07");
    static_assert(SCENA[scena_col_codice("A1-07")].area == MONTE, "A1-07 non e' sul Monte Ingino");

    // entrando con A1-07 pronta parte, e l'Imboscata e' ancora sulla mappa: la cartolina viene prima del contatto
    static_assert(cutscene_all_ingresso(fino_a("A1-06"), MONTE) == C7S && scontro_attivo(fino_a("A1-06"), 1),
                  "C7S non parte entrando negli Stradoni prima dell'Imboscata");
    static_assert(cutscene_all_ingresso(fino_a("A1-06"), int(mondo::AreaId::DUOMO_DUCALE)) < 0 &&
                  cutscene_all_ingresso(fino_a("A1-06"), int(mondo::AreaId::PIAZZA_GRANDE)) < 0 &&
                  cutscene_all_ingresso(fino_a("A1-06"), NESSUNA_AREA) < 0, "C7S parte fuori dal Monte Ingino");
    static_assert(cutscene_all_ingresso(fino_a("A1-05b"), MONTE) < 0, "C7S parte prima della porta del monte (A1-06)");

    consteval bool c7s_una_volta()
    {
        GameState p = fino_a("A1-06");
        regia::segna_vista(p, C7S);
        GameState q = fino_a("A1-07");
        return cutscene_all_ingresso(p, MONTE) < 0 && cutscene_all_ingresso(q, MONTE) < 0 &&
               ! scontro_attivo(q, 1);
    }

    static_assert(c7s_una_volta(), "C7S riparte gia' vista o a scena fatta");

    // l'inserto alla battuta 0 di A1-07 resta (la prova senza camminare) e non copre battute: vista all'ingresso,
    // la scena non ripete nulla
    consteval bool inserto_di_c7s()
    {
        int prima = SCENA[scena_col_codice("A1-07")].prima_battuta;

        for(int i = 0; i < INSERTI; ++i)
        {
            if(INSERTO[i].regia == C7S)
            {
                return INSERTO[i].battuta == prima && INSERTO[i].copre == 0;
            }
        }

        return false;
    }

    static_assert(inserto_di_c7s(), "l'inserto di C7S in A1-07 manca o copre battute");
}

}
