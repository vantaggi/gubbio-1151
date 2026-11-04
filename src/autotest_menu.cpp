// Autotest a tempo di compilazione del menu e degli aiuti al giocatore (menu/PROPOSTA.md). Se una prova non
// regge, la ROM non compila.
//
// MOB: l'obiettivo della cronaca e le aree viste (include/storia_logica.h, OBIETTIVO in storia.h generato da
// tools/genera_storia.py). Ogni riga OBIETTIVO delle scene e' nella tabella con la sua scena e un'area meta
// raggiungibile; la recita (e il giro senza camminare) aggiorna l'obiettivo, le righe degli incarichi no;
// ricavare l'obiettivo dalle scene fatte (un salvataggio v3) da' lo stesso obiettivo della recita; entrare in
// un'area la segna vista. Negative: una battuta che non e' OBIETTIVO, una riga d'incarico, un'area fuori dal
// mondo non cambiano nulla.
//
// MAI: gli aiuti senza il menu di pausa nuovo (include/aiuti.h). La strada piu' breve fra le aree (ogni passo
// accorcia la strada di uno, da ogni area a ogni altra), il varco verso la meta, la freccia, i cartelli (uno per
// ogni varco del mondo), il tempo "h:mm" e i livelli dell'anteprima, la fase e gli incarichi aperti, il Riprova
// solo per il duello con Corrado. Ogni prova ha la sua negativa.

#include "aiuti.h"
#include "stile/cornice.h"
#include "formatta.h"
#include "progressione.h"
#include "storia_logica.h"

namespace gubbio
{

namespace
{
    using namespace storia;

    // --- La tabella: ogni battuta OBIETTIVO delle scene e' una riga della cronaca, nella sua scena ----------
    consteval bool obiettivi_delle_scene()
    {
        int trovati = 0;

        for(int k = 0; k < SCENE; ++k)
        {
            for(int i = SCENA[k].prima_battuta; i < SCENA[k].prima_battuta + SCENA[k].battute; ++i)
            {
                if(BATTUTA[i].tipo != TipoBattuta::OBIETTIVO)
                {
                    continue;
                }

                int o = obiettivo_del_testo(BATTUTA[i].testo);

                if(o < 0 || OBIETTIVO[o].quest != -1 || OBIETTIVO[o].scena != k)
                {
                    return false;
                }

                ++trovati;
            }
        }

        int della_cronaca = 0;

        for(int o = 0; o < OBIETTIVI; ++o)
        {
            della_cronaca += OBIETTIVO[o].quest < 0 ? 1 : 0;

            if(OBIETTIVO[o].area < 0 || OBIETTIVO[o].area >= mondo::AREE_CONTEGGIO)
            {
                return false;
            }
        }

        return trovati == della_cronaca && trovati > 0;
    }

    static_assert(obiettivi_delle_scene(), "una riga OBIETTIVO di una scena manca dalla tabella o non e' della sua scena");
    static_assert(OBIETTIVI < NESSUN_OBIETTIVO, "GameState::obiettivo e' un byte e 255 vuol dire nessuno");

    // Le righe degli incarichi (le proposte di 04_quest.md) sono nella tabella con la loro quest.
    consteval bool obiettivi_degli_incarichi()
    {
        bool visti[QUEST] = {};

        for(int i = 0; i < FRASI_QUEST; ++i)
        {
            int o = obiettivo_del_testo(FRASE_QUEST[i].testo);

            if(o >= 0)
            {
                if(OBIETTIVO[o].quest < 0 || OBIETTIVO[o].quest >= QUEST || OBIETTIVO[o].scena != -1)
                {
                    return false;
                }

                visti[OBIETTIVO[o].quest] = true;
            }
        }

        return visti[0] && visti[1] && visti[2];
    }

    static_assert(obiettivi_degli_incarichi(), "le righe OBIETTIVO dei tre incarichi non sono nella tabella");

    // Le mete scritte a mano nel copione: A1-01 porta al Teatro (non a via dei Consoli, la scena dopo, che si
    // puo' saltare); A1-05 al Duomo (non al borgo di A1-05b, facoltativo).
    static_assert(OBIETTIVO[0].area == int(mondo::AreaId::TEATRO_ROMANO) && OBIETTIVO[3].area == int(mondo::AreaId::DUOMO_DUCALE),
                  "le aree meta scritte a mano («(area: ID)») non sono arrivate nella tabella");

    // --- La meta si raggiunge camminando: ricerca in ampiezza sui varchi delle aree ----------------------
    consteval bool raggiungibile(int da, int a)
    {
        bool viste[mondo::AREE_CONTEGGIO] = {};
        int coda[mondo::AREE_CONTEGGIO] = {};
        int testa = 0;
        int fine = 0;
        coda[fine++] = da;
        viste[da] = true;

        while(testa < fine)
        {
            int x = coda[testa++];

            if(x == a)
            {
                return true;
            }

            const mondo::Area& area = mondo::area(mondo::AreaId(x));

            for(int v = 0; v < area.varchi; ++v)
            {
                int y = area.varco[v].destinazione;

                if(y >= 0 && ! viste[y])
                {
                    viste[y] = true;
                    coda[fine++] = y;
                }
            }
        }

        return false;
    }

    consteval bool mete_raggiungibili()
    {
        for(int o = 0; o < OBIETTIVI; ++o)
        {
            int da = OBIETTIVO[o].scena >= 0 ? int(SCENA[OBIETTIVO[o].scena].area) : int(QUEST_V1[OBIETTIVO[o].quest].consegna);

            if(! raggiungibile(da < 0 ? int(mondo::AreaId::PIAZZA_GRANDE) : da, OBIETTIVO[o].area))
            {
                return false;
            }
        }

        return true;
    }

    static_assert(mete_raggiungibili(), "un obiettivo porta a un'area che dalla sua scena non si raggiunge");

    // --- La recita aggiorna l'obiettivo; le righe degli incarichi e le altre battute no -------------------
    consteval GameState partita()
    {
        GameState p = {};
        progressione::partita_nuova(p);
        return p;
    }

    static_assert(partita().obiettivo == NESSUN_OBIETTIVO && area_dell_obiettivo(partita()) == -1 && aree_viste(partita()) == 0,
                  "la partita nuova ha gia' un obiettivo o aree viste");

    consteval bool segna_solo_la_cronaca()
    {
        GameState p = partita();
        int prima_scena = SCENA[OBIETTIVO[1].scena].prima_battuta;
        const Battuta* cronaca = nullptr;

        for(int i = prima_scena; i < BATTUTE && ! cronaca; ++i)
        {
            cronaca = BATTUTA[i].testo == OBIETTIVO[1].testo ? &BATTUTA[i] : nullptr;
        }

        if(! cronaca || ! segna_obiettivo(p, *cronaca) || p.obiettivo != 1 || segna_obiettivo(p, *cronaca))
        {
            return false;
        }

        // negativa: una battuta qualunque della stessa scena, e la riga OBIETTIVO di un incarico
        if(segna_obiettivo(p, BATTUTA[prima_scena]) && BATTUTA[prima_scena].tipo != TipoBattuta::OBIETTIVO)
        {
            return false;
        }

        for(int i = 0; i < FRASI_QUEST; ++i)
        {
            Battuta b = FRASE_QUEST[i];
            b.tipo = TipoBattuta::OBIETTIVO;        // anche se fosse recitata come OBIETTIVO

            if(obiettivo_del_testo(b.testo) >= 0 && segna_obiettivo(p, b))
            {
                return false;
            }
        }

        return p.obiettivo == 1 && area_dell_obiettivo(p) == int(mondo::AreaId::TEATRO_ROMANO);
    }

    static_assert(segna_solo_la_cronaca(), "l'obiettivo della cronaca cambia con battute che non sono della cronaca");

    // Il giro senza camminare (che recita le righe OBIETTIVO come la recita): dopo ogni scena l'obiettivo
    // ricavato dalle scene fatte e' quello tenuto. Alla fine, con «Sì, è ora» si va a Piazza Grande all'alba.
    consteval bool ricavato_come_recitato(int voce)
    {
        GameState p = partita();
        bool avanti = true;
        int controlli = 0;

        while(avanti)
        {
            avanti = false;

            for(int k = 0; k < SCENE && ! avanti; ++k)
            {
                if(pronta(p, k, SCENA[k].area))
                {
                    scegli_tutto(p, k, voce);
                    chiudi_scena(p, k);

                    if(ricava_obiettivo(p) != p.obiettivo)
                    {
                        return false;
                    }

                    ++controlli;
                    avanti = true;
                }
            }

            if(! avanti)
            {
                avanti = risposta_di_un_npc(p);
            }
        }

        return controlli == SCENE;
    }

    static_assert(ricavato_come_recitato(0), "l'obiettivo ricavato dalle scene non e' quello della recita (prima voce)");

    consteval uint8_t obiettivo_finale(int voce)
    {
        GameState p = partita();
        gioca_tutta(p, SCENA, SCENE, voce);
        return p.obiettivo;
    }

    static_assert(obiettivo_finale(0) == 8 && OBIETTIVO[8].area == int(mondo::AreaId::PIAZZA_GRANDE),
                  "con «Sì, è ora» l'ultimo obiettivo non e' Piazza Grande all'alba");
    static_assert(OBIETTIVO[6].area == int(mondo::AreaId::CONDOTTO) && OBIETTIVO[6].scena >= 0 &&
                  SCENA[OBIETTIVO[6].scena].area == int8_t(mondo::AreaId::GOLA_STRISCIA),
                  "nella gola, dalla striscia nera, l'obiettivo non porta al Condotto");
    static_assert(obiettivo_finale(1) == 9, "con «Non ancora» l'ultimo obiettivo non e' parlare con Guido");

    // Con «Non ancora» il confronto regge fino a B-05; poi Guido accende ALBA_CONFERMATA e chi ricava
    // dalle bandiere legge «Sì, è ora» (documentato in ricava_obiettivo: l'obiettivo e' comunque Piazza Grande).
    consteval bool non_ancora_fino_a_b05()
    {
        GameState p = partita();

        for(int k = 0; k < SCENE; ++k)
        {
            for(int j = 0; j < SCENE; ++j)
            {
                if(pronta(p, j, SCENA[j].area))
                {
                    scegli_tutto(p, j, 1);
                    chiudi_scena(p, j);

                    if(ricava_obiettivo(p) != p.obiettivo)
                    {
                        return false;
                    }

                    break;
                }
            }
        }

        return p.obiettivo == 9 && ! accesa(p, Bandiera::ALBA_CONFERMATA);
    }

    static_assert(non_ancora_fino_a_b05(), "con «Non ancora» l'obiettivo ricavato non e' quello della recita");

    // --- Dopo il caricamento: un salvataggio v3 aggiornato ritrova obiettivo e aree viste ----------------
    consteval GameState a_meta_storia()
    {
        GameState p = partita();

        // fino a quando Antonio e' nel gruppo (A1-04 fatta): l'obiettivo e' tornare in citta'
        while(! accesa(p, Bandiera::ANTONIO_NEL_GRUPPO))
        {
            for(int k = 0; k < SCENE; ++k)
            {
                if(pronta(p, k, SCENA[k].area))
                {
                    scegli_tutto(p, k, 0);
                    chiudi_scena(p, k);
                    break;
                }
            }
        }

        p.area = uint8_t(mondo::AreaId::TEATRO_ROMANO);
        return p;
    }

    consteval bool dopo_il_caricamento_ritrova()
    {
        GameState tenuto = a_meta_storia();
        GameState v3 = tenuto;              // come lo da' salvataggio::migra_v3: niente obiettivo, niente aree
        v3.obiettivo = NESSUN_OBIETTIVO;

        for(uint8_t& a : v3.aree_viste)
        {
            a = 0;
        }

        dopo_il_caricamento(v3);
        GameState due = v3;
        dopo_il_caricamento(due);           // una seconda volta non cambia nulla

        return v3.obiettivo == tenuto.obiettivo && tenuto.obiettivo == 2 &&
               area_vista(v3, int(mondo::AreaId::TEATRO_ROMANO)) && area_vista(v3, int(mondo::AreaId::PIAZZA_GRANDE)) &&
               area_vista(v3, int(mondo::AreaId::SAN_MARTINO)) && ! area_vista(v3, int(mondo::AreaId::BASILICA)) &&
               due.obiettivo == v3.obiettivo && due.aree_viste[0] == v3.aree_viste[0] &&
               due.aree_viste[1] == v3.aree_viste[1] && due.aree_viste[2] == v3.aree_viste[2];
    }

    static_assert(dopo_il_caricamento_ritrova(), "un salvataggio v3 aggiornato non ritrova l'obiettivo e le aree viste");

    // Negativa: una partita appena cominciata resta senza obiettivo (nessuna scena con OBIETTIVO fatta), e un
    // obiettivo gia' tenuto non si ricalcola.
    consteval bool dopo_il_caricamento_non_inventa()
    {
        GameState p = partita();
        dopo_il_caricamento(p);
        GameState q = a_meta_storia();
        q.obiettivo = 5;
        dopo_il_caricamento(q);
        return p.obiettivo == NESSUN_OBIETTIVO && aree_viste(p) == 1 && q.obiettivo == 5;
    }

    static_assert(dopo_il_caricamento_non_inventa(), "dopo il caricamento compare un obiettivo che non c'era");

    // --- Le aree viste: entrando, una alla volta; fuori dal mondo, nulla -----------------------------------
    consteval bool aree_viste_entrando()
    {
        GameState p = partita();
        all_ingresso(p, int(mondo::AreaId::PIAZZA_GRANDE));
        all_ingresso(p, int(mondo::AreaId::TEATRO_ROMANO));
        all_ingresso(p, int(mondo::AreaId::TEATRO_ROMANO));
        all_ingresso(p, -1);
        all_ingresso(p, mondo::AREE_CONTEGGIO);
        segna_area_vista(p, 23);            // nei 3 byte ci sarebbe posto, ma non e' un'area
        return aree_viste(p) == 2 && area_vista(p, int(mondo::AreaId::TEATRO_ROMANO)) &&
               ! area_vista(p, int(mondo::AreaId::SAN_MARTINO)) && ((p.aree_viste[2] >> 7) & 1) == 0 &&
               ! area_vista(p, -1) && ! area_vista(p, mondo::AREE_CONTEGGIO);
    }

    static_assert(aree_viste_entrando(), "entrare in un'area non la segna vista, o si segna un'area che non c'e'");

    // La nebbia e' solo all'aperto: entrare in un interno non accende nessun bit, e l'interno non risulta visto
    // neanche se il suo bit fosse acceso (un salvataggio di prima). Le aree all'aperto stanno tutte nei 24 bit.
    consteval bool interni_fuori_dalla_nebbia()
    {
        int interni = 0;
        int aperte = 0;

        for(int a = 0; a < mondo::AREE_CONTEGGIO; ++a)
        {
            GameState p = partita();
            all_ingresso(p, a);
            bool interno = mondo::area(mondo::AreaId(a)).interno;
            bool nessun_bit = p.aree_viste[0] == 0 && p.aree_viste[1] == 0 && p.aree_viste[2] == 0;

            if(interno)
            {
                ++interni;

                if(a < BIT_AREE_VISTE)   // il bit di un salvataggio di prima; gli interni in coda non ce l'hanno
                {
                    p.aree_viste[a / 8] = uint8_t(p.aree_viste[a / 8] | (1 << (a % 8)));
                }

                if(! nessun_bit || area_vista(p, a) || aree_viste(p) != 0)
                {
                    return false;
                }
            }
            else
            {
                ++aperte;

                if(a >= BIT_AREE_VISTE || ! area_vista(p, a) || aree_viste(p) != 1)
                {
                    return false;
                }
            }
        }

        return interni >= 1 && aperte >= 1;
    }

    static_assert(interni_fuori_dalla_nebbia(), "un interno accende un bit della nebbia, o un'area all'aperto non ne ha uno");
    static_assert(mondo::area(mondo::AreaId::BASILICA_INTERNO).interno && ! mondo::area(mondo::AreaId::BASILICA).interno,
                  "la Basilica e' all'aperto, il suo interno no");

    // === MAI ==================================================================================================
    using namespace aiuti;

    consteval int scena_di(const char* codice)
    {
        for(int k = 0; k < SCENE; ++k)
        {
            int i = 0;

            while(codice[i] && SCENA[k].codice[i] == codice[i])
            {
                ++i;
            }

            if(! codice[i] && ! SCENA[k].codice[i])
            {
                return k;
            }
        }

        return -1;
    }

    // --- Il tempo e i livelli dell'anteprima ---------------------------------------------------------------
    static_assert(autotest_formatta_tempo() == 101 * 60 + 1, "formatta_tempo sbaglia un minuto fra 0 e 101 ore");

    consteval bool tempo_come(int secondi, const char* atteso)
    {
        char t[TEMPO_CARATTERI_MAX + 1] = {};
        int n = formatta_tempo(secondi, t);

        for(int i = 0; i <= n; ++i)
        {
            if(t[i] != atteso[i])
            {
                return false;
            }
        }

        return true;
    }

    static_assert(tempo_come(6120, "1:42") && tempo_come(0, "0:00") && tempo_come(36000, "10:00") &&
                  tempo_come(400000, "99:59") && tempo_come(-5, "0:00") && ! tempo_come(6120, "1:41"),
                  "il tempo dell'anteprima non e' h:mm");

    consteval bool livelli_come(int a, int b, int c, const char* atteso)
    {
        char t[LIVELLI_CARATTERI + 1] = {};
        formatta_livelli(a, b, c, t);

        for(int i = 0; i <= LIVELLI_CARATTERI; ++i)
        {
            if(t[i] != atteso[i])
            {
                return false;
            }
        }

        return true;
    }

    static_assert(livelli_come(4, 4, 3, "4 4 3") && livelli_come(0, 12, 8, "1 9 8") && ! livelli_come(4, 4, 3, "4 4 4"),
                  "i livelli dell'anteprima non sono «4 4 3»");

    // --- La strada piu' breve: da ogni area a ogni altra, ogni passo la accorcia di uno ----------------------
    consteval bool vicine(int a, int b)
    {
        const mondo::Area& x = mondo::area(mondo::AreaId(a));

        for(int v = 0; v < x.varchi; ++v)
        {
            if(x.varco[v].destinazione == b)
            {
                return true;
            }
        }

        return false;
    }

    consteval bool strade_piu_brevi()
    {
        for(int a = 0; a < mondo::AREE_CONTEGGIO; ++a)
        {
            for(int b = 0; b < mondo::AREE_CONTEGGIO; ++b)
            {
                int n = passi_fino_a(a, b);
                int p = prossima_area(a, b);

                if(n < 0 || (a == b) != (n == 0) || (a == b) != (p < 0))
                {
                    return false;
                }

                if(a != b && (! vicine(a, p) || passi_fino_a(p, b) != n - 1))
                {
                    return false;
                }
            }
        }

        return true;
    }

    static_assert(strade_piu_brevi(), "la strada del promemoria non e' la piu' breve, o un'area non si raggiunge");
    static_assert(passi_fino_a(int(mondo::AreaId::PIAZZA_GRANDE), int(mondo::AreaId::TEATRO_ROMANO)) == 3 &&
                  passi_fino_a(int(mondo::AreaId::PIAZZA_GRANDE), int(mondo::AreaId::CONDOTTO)) >= 6 &&
                  prossima_area(int(mondo::AreaId::PIAZZA_GRANDE), -1) == -1 &&
                  prossima_area(int(mondo::AreaId::PIAZZA_GRANDE), mondo::AREE_CONTEGGIO) == -1,
                  "la strada da Piazza Grande al Teatro non e' di tre varchi, o una meta fuori dal mondo ha una strada");

    // Ogni varco del mondo ha celle (il centro dove punta la freccia) e, se porta a un'area, il suo cartello.
    consteval bool varchi_con_centro_e_cartello()
    {
        for(int a = 0; a < mondo::AREE_CONTEGGIO; ++a)
        {
            const mondo::Area& x = mondo::area(mondo::AreaId(a));

            for(int v = 0; v < x.varchi; ++v)
            {
                Punto c = centro_del_varco(x, v);

                if(c.x < 0 || c.y < 0 || c.x >= x.larghezza * mondo::TILE_PX || c.y >= x.altezza * mondo::TILE_PX)
                {
                    return false;
                }

                if(x.varco[v].destinazione >= 0 && cartello(a, x.varco[v].destinazione) < 0)
                {
                    return false;
                }
            }
        }

        return true;
    }

    static_assert(varchi_con_centro_e_cartello(), "un varco senza celle o senza cartello");
    static_assert(cartello(int(mondo::AreaId::PIAZZA_GRANDE), int(mondo::AreaId::TEATRO_ROMANO)) < 0 &&
                  centro_del_varco(mondo::area(mondo::AreaId::PIAZZA_GRANDE), mondo::VARCHI_MAX).x < 0,
                  "un cartello fra aree che non si toccano, o un centro per un varco che non c'e'");

    // Il varco verso la meta porta alla prossima area della strada; nella meta stessa non c'e' freccia.
    consteval bool varco_giusto()
    {
        mondo::Esploratore e;
        mondo::colloca(e, mondo::AreaId::PIAZZA_GRANDE, 0);
        int meta = int(mondo::AreaId::TEATRO_ROMANO);
        int v = varco_verso_la_meta(e, meta);
        bool qui = varco_verso_la_meta(e, int(mondo::AreaId::PIAZZA_GRANDE)) == -1;
        return v >= 0 && mondo::area(e.area).varco[v].destinazione == prossima_area(int(e.area), meta) && qui;
    }

    static_assert(varco_giusto(), "il promemoria punta a un varco che non porta verso la meta");

    // Due varchi verso la stessa area (nel mondo di oggi non succede): vince il piu' vicino al giocatore, a
    // parita' il primo. Un'area finta di 8 x 1 celle: varco 0 a sinistra, varco 1 a destra, varco 2 altrove.
    inline constexpr uint8_t GRIGLIA_FINTA[8] = { mondo::PRIMO_VARCO, 0, 0, 0, 0, 0, 0, mondo::PRIMO_VARCO + 1 };

    consteval mondo::Area area_finta()
    {
        mondo::Area a {};
        a.griglia = GRIGLIA_FINTA;
        a.larghezza = 8;
        a.altezza = 1;
        a.varchi = 3;
        a.varco[0].destinazione = 5;
        a.varco[1].destinazione = 5;
        a.varco[2].destinazione = 6;
        return a;
    }

    static_assert(varco_piu_vicino(area_finta(), 5, 6, 4) == 0 && varco_piu_vicino(area_finta(), 5, 60, 4) == 1 &&
                  varco_piu_vicino(area_finta(), 5, 32, 4) == 0 && varco_piu_vicino(area_finta(), 6, 6, 4) == -1 &&
                  varco_piu_vicino(area_finta(), 7, 6, 4) == -1,
                  "fra due varchi verso la stessa area il promemoria non sceglie il piu' vicino");

    // La freccia: verso l'asse piu' lungo; sempre dentro lo schermo e sotto la fascia del promemoria.
    static_assert(verso_di(10, 3) == Verso::DESTRA && verso_di(-10, 3) == Verso::SINISTRA && verso_di(2, 9) == Verso::GIU &&
                  verso_di(2, -9) == Verso::SU && verso_di(0, 0) == Verso::DESTRA, "la freccia punta dalla parte sbagliata");
    static_assert(posto_della_freccia(-500, -500).x == MARGINE_FRECCIA && posto_della_freccia(-500, -500).y == FASCIA_PROMEMORIA &&
                  posto_della_freccia(900, 900).x == SCHERMO_L - MARGINE_FRECCIA - LATO_FRECCIA &&
                  posto_della_freccia(900, 900).y == SCHERMO_A - MARGINE_FRECCIA - LATO_FRECCIA &&
                  posto_della_freccia(120, 80).x == 112 && posto_della_freccia(120, 80).y == 72,
                  "la freccia esce dallo schermo o non sta sul varco quando il varco si vede");

    static_assert(dentro_la_freccia(Verso::DESTRA, 14, 7) && ! dentro_la_freccia(Verso::DESTRA, 14, 1) &&
                  dentro_la_freccia(Verso::SU, 7, 1) && ! dentro_la_freccia(Verso::SU, 7, 14) &&
                  dentro_la_freccia(Verso::SINISTRA, 1, 8) && dentro_la_freccia(Verso::GIU, 8, 14),
                  "la freccia non punta dove dice");

    // --- Il contorno della freccia (STANDARD P1, P3): quasi nero e chiuso sugli 8 vicini, niente pixel orfani ---
    // Chiuso: nessun pixel del pieno chiaro tocca il fuori (il lastrico chiaro), nemmeno in diagonale.
    consteval bool contorno_chiuso(Verso verso, bool vicini_in_croce)
    {
        for(int y = 0; y < 16; ++y)
        {
            for(int x = 0; x < 16; ++x)
            {
                if(tono_della_freccia(verso, x, y, vicini_in_croce) != TONO_FRECCIA_PIENO)
                {
                    continue;
                }

                for(int dy = -1; dy <= 1; ++dy)
                {
                    for(int dx = -1; dx <= 1; ++dx)
                    {
                        if(! dentro_la_freccia(verso, x + dx, y + dy))
                        {
                            return false;
                        }
                    }
                }
            }
        }

        return true;
    }

    // Orfano (P3): un pixel pieno o di contorno con un tono diverso da tutti gli 8 vicini. 'buco' (x, y) toglie
    // il contorno a un pixel e lo fa pieno: la prova negativa.
    consteval bool senza_orfani(Verso verso, int buco_x = -1, int buco_y = -1)
    {
        auto tono = [&](int x, int y) {
            int t = x >= 0 && y >= 0 && x < 16 && y < 16 ? tono_della_freccia(verso, x, y) : 0;
            return x == buco_x && y == buco_y && t != 0 ? TONO_FRECCIA_PIENO + 1 : t;
        };

        for(int y = 0; y < 16; ++y)
        {
            for(int x = 0; x < 16; ++x)
            {
                int t = tono(x, y);
                bool uguale = false;

                for(int dy = -1; dy <= 1 && t != 0; ++dy)
                {
                    for(int dx = -1; dx <= 1; ++dx)
                    {
                        uguale = uguale || ((dx != 0 || dy != 0) && tono(x + dx, y + dy) == t);
                    }
                }

                if(t != 0 && ! uguale)
                {
                    return false;
                }
            }
        }

        return true;
    }

    consteval bool freccia_a_standard()
    {
        for(int k = 0; k < 4; ++k)
        {
            Verso v = Verso(k);
            int pieni = 0;

            for(int i = 0; i < 256; ++i)
            {
                pieni += tono_della_freccia(v, i % 16, i / 16) == TONO_FRECCIA_PIENO;
            }

            if(! contorno_chiuso(v, false) || ! senza_orfani(v) || pieni < 20)
            {
                return false;
            }
        }

        return true;
    }

    static_assert(freccia_a_standard(), "la freccia ha il contorno aperto, un pixel orfano o niente pieno");
    // prove negative: il contorno sui soli 4 vicini in croce lascia il pieno a contatto col fuori in diagonale;
    // un pixel di un tono diverso in mezzo al pieno e' un orfano
    static_assert(! contorno_chiuso(Verso::DESTRA, true) && ! contorno_chiuso(Verso::SU, true),
                  "la prova del contorno chiuso non vede i lati obliqui");
    static_assert(! senza_orfani(Verso::DESTRA, 6, 7), "la prova dei pixel orfani non vede un orfano");
    static_assert(TONO_FRECCIA_CONTORNO == 1 && GUBBIO_VOCE(stile::CORNICE_PALETTE, TONO_FRECCIA_CONTORNO) == 0x1085 &&
                  TONO_FRECCIA_PIENO == 2 && GUBBIO_VOCE(stile::CORNICE_PALETTE, TONO_FRECCIA_PIENO) == 0x7BBD,
                  "il contorno della freccia non e' il piombo quasi nero (neutri 0) o il pieno non e' il fondo chiaro");

    static_assert(CELLE_CARTELLO == 3, "il cartello compare a 3 celle dal varco (menu/PROPOSTA.md sez. 3.8)");

    // --- Il fumetto sopra il cartello: a 13 px dalla cella del varco si', a 14 no (come DISTANZA_PAROLA) -------
    // La cella piu' a destra del varco 0 di Piazza Grande e il giocatore a (dx, dy) px dai suoi piedi: con dx > 0
    // nessun'altra cella del varco e' piu' vicina in orizzontale. -2 se il punto trovato non sta in mezzo al varco,
    // sulla riga di una sua cella.
    consteval Punto cartello_spostato(int dx, int dy)
    {
        const mondo::Area& a = mondo::area(mondo::AreaId::PIAZZA_GRANDE);
        int destra = -1;

        for(int i = 0; i < a.larghezza * a.altezza; ++i)
        {
            if(a.griglia[i] == mondo::PRIMO_VARCO && (destra < 0 || i % a.larghezza > destra % a.larghezza))
            {
                destra = i;
            }
        }

        if(destra < 0)
        {
            return { -2, -2 };
        }

        mondo::Esploratore e;
        e.area = mondo::AreaId::PIAZZA_GRANDE;
        e.x = mondo::piedi_x(destra % a.larghezza) + dx;
        e.y = mondo::piedi_y(destra / a.larghezza) + dy;
        Punto p = cartello_a_portata(e, 0);

        if(p.x < 0)
        {
            return p;
        }

        // in mezzo al varco, sulla riga di una sua cella
        int ty = (p.y + 2 - mondo::TILE_PX) / mondo::TILE_PX;
        bool riga_del_varco = false;

        for(int tx = 0; tx < a.larghezza; ++tx)
        {
            riga_del_varco = riga_del_varco || a.griglia[tx + ty * a.larghezza] == mondo::PRIMO_VARCO;
        }

        return riga_del_varco && p.x == centro_del_varco(a, 0).x && p.y == mondo::piedi_y(ty) ? p : Punto{ -2, -2 };
    }

    static_assert(PORTATA_CARTELLO == 14, "il fumetto del cartello ha la portata del tasto A (14 px)");
    static_assert(cartello_spostato(0, 0).x >= 0 && cartello_spostato(13, 0).x >= 0 && cartello_spostato(13, 13).x >= 0 &&
                  cartello_spostato(13, -13).x >= 0, "a portata del cartello il fumetto non si accende");
    // negative: a 14 px (in orizzontale o in diagonale) il fumetto resta spento; un varco che l'area non ha non
    // ha cartello
    static_assert(cartello_spostato(14, 0).x == -1 && cartello_spostato(20, 0).x == -1,
                  "il fumetto del cartello si accende oltre la portata del tasto A");
    consteval bool varco_che_non_c_e()
    {
        mondo::Esploratore e;
        e.area = mondo::AreaId::PIAZZA_GRANDE;
        e.x = 0;
        e.y = 0;
        return cartello_a_portata(e, mondo::area(e.area).varchi).x == -1 && cartello_a_portata(e, -1).x == -1;
    }

    static_assert(varco_che_non_c_e(), "un varco che l'area non ha accende il fumetto");

    // --- I cartelli: vicino a un varco (entro 3 celle) si', sopra il varco o lontano no -----------------------
    consteval bool cartello_vicino_al_varco()
    {
        const mondo::Area& a = mondo::area(mondo::AreaId::PIAZZA_GRANDE);
        bool vicino = false;
        bool sopra = false;
        bool lontano = false;

        for(int ty = 0; ty < a.altezza; ++ty)
        {
            for(int tx = 0; tx < a.larghezza; ++tx)
            {
                int c = mondo::cella(a, tx, ty);

                if(mondo::solida(c))
                {
                    continue;
                }

                mondo::Esploratore e;
                e.area = mondo::AreaId::PIAZZA_GRANDE;
                e.x = mondo::piedi_x(tx);
                e.y = mondo::piedi_y(ty);
                int v = varco_vicino(e);
                int d = 99;     // la distanza dal varco piu' vicino, contata qui a parte

                for(int dy = -4; dy <= 4; ++dy)
                {
                    for(int dx = -4; dx <= 4; ++dx)
                    {
                        int m = (dx < 0 ? -dx : dx) > (dy < 0 ? -dy : dy) ? (dx < 0 ? -dx : dx) : (dy < 0 ? -dy : dy);
                        d = mondo::varco(mondo::cella(a, tx + dx, ty + dy)) && m < d ? m : d;
                    }
                }

                if(mondo::varco(c))
                {
                    sopra = true;

                    if(v >= 0)
                    {
                        return false;
                    }
                }
                else if(d <= 3)     // 3 celle: menu/PROPOSTA.md sez. 3.8, non la costante del gioco
                {
                    vicino = true;

                    if(v < 0)
                    {
                        return false;
                    }
                }
                else
                {
                    lontano = true;

                    if(v >= 0)
                    {
                        return false;
                    }
                }
            }
        }

        return vicino && sopra && lontano;
    }

    static_assert(cartello_vicino_al_varco(), "il cartello compare lontano dal varco, o non compare vicino");

    // --- La fase, gli incarichi aperti -------------------------------------------------------------------
    consteval bool fasi_e_incarichi()
    {
        GameState p = partita();
        bool inizio = fase_della_cronaca(p) == FaseCronaca::ULTIMATUM && incarichi_aperti(p) == 0;
        p.quest[(QUEST_V1[0].consegnata - 64) / 8] = 0;
        accendi_una(p, QUEST_GIOCO[0].presa);
        bool una = incarichi_aperti(p) == 1;
        accendi_una(p, QUEST_V1[0].consegnata);
        bool nessuna = incarichi_aperti(p) == 0;
        GameState fine = partita();
        gioca_tutta(fine);
        return inizio && una && nessuna && fase_della_cronaca(fine) == FaseCronaca::DOPO_L_ALBA;
    }

    static_assert(fasi_e_incarichi(), "la fase della cronaca o il conto degli incarichi aperti sbaglia");

    // --- La sconfitta: il Riprova solo nel duello con Corrado ------------------------------------------------
    static_assert(riprova_dopo_la_sconfitta(scena_di("B-04")) && ! riprova_dopo_la_sconfitta(scena_di("A1-04")) &&
                  ! riprova_dopo_la_sconfitta(scena_di("B-03")) && ! riprova_dopo_la_sconfitta(-1),
                  "il Riprova vale per una scena che non e' il duello con Corrado, o non vale per il duello");

    consteval int riprove()
    {
        int n = 0;

        for(int k = 0; k < SCENE; ++k)
        {
            n += riprova_dopo_la_sconfitta(k) ? 1 : 0;
        }

        return n;
    }

    static_assert(riprove() == 1, "il Riprova vale per piu' di una scena");
    static_assert(ritirata_della_scena(scena_di("B-03")) == Ritirata::ARCO &&
                  ritirata_della_scena(scena_di("A1-08")) == Ritirata::SUBITO &&
                  ritirata_della_scena(scena_di("A1-04")) == Ritirata::INGRESSO &&
                  ritirata_della_scena(scena_di("A1-07")) == Ritirata::INGRESSO,
                  "la riga dopo la sconfitta non dice dove si e' stati riportati");
}

}
