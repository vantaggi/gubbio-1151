// Autotest a tempo di compilazione del menu e degli aiuti al giocatore (menu/PROPOSTA.md). Se una prova non
// regge, la ROM non compila.
//
// MOB: l'obiettivo della cronaca e le aree viste (include/storia_logica.h, OBIETTIVO in storia.h generato da
// tools/genera_storia.py). Ogni riga OBIETTIVO delle scene e' nella tabella con la sua scena e un'area meta
// raggiungibile; la recita (e il giro senza camminare) aggiorna l'obiettivo, le righe degli incarichi no;
// ricavare l'obiettivo dalle scene fatte (un salvataggio v3) da' lo stesso obiettivo della recita; entrare in
// un'area la segna vista. Negative: una battuta che non e' OBIETTIVO, una riga d'incarico, un'area fuori dal
// mondo non cambiano nulla.

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

    static_assert(obiettivo_finale(0) == 7 && OBIETTIVO[7].area == int(mondo::AreaId::PIAZZA_GRANDE),
                  "con «Sì, è ora» l'ultimo obiettivo non e' Piazza Grande all'alba");
    static_assert(obiettivo_finale(1) == 8, "con «Non ancora» l'ultimo obiettivo non e' parlare con Guido");

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

        return p.obiettivo == 8 && ! accesa(p, Bandiera::ALBA_CONFERMATA);
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
}

}
