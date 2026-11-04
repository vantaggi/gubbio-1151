// Autotest della colonna sonora (F7c), a tempo di compilazione: le tabelle di include/colonna_sonora.h
// hanno le misure del gioco (aree, cutscene, eventi, incontri) e i codici delle cutscene nello stesso
// ordine; il brano di fondo segue area, fase e luogo; il segnale di Fazio suona solo con Fazio in bottega;
// il colpo di Antonio e' fuoco. Ogni prova ha la sua negativa; se una non regge, la ROM non compila.

#include "audio_logica.h"

namespace gubbio
{

namespace
{
    using namespace audio;
    using colonna::Brano;

    constexpr bool uguali(const char* a, const char* b)
    {
        while(*a && *a == *b)
        {
            ++a;
            ++b;
        }

        return *a == *b;
    }

    constexpr uint64_t bit(storia::Bandiera b)
    {
        return uint64_t(1) << int(b);
    }

    constexpr GameState con(uint64_t bandiere)
    {
        GameState p = {};
        storia::accendi(p, bandiere);
        return p;
    }

    // --- Le misure del gioco ------------------------------------------------------------------------
    static_assert(colonna::AREE == mondo::AREE_CONTEGGIO, "colonna_sonora.h: le aree non sono quelle di mondo.h");
    static_assert(colonna::CUTSCENE == regia::CUTSCENE, "colonna_sonora.h: le cutscene non sono quelle di regia.h");
    static_assert(colonna::EVENTI == int(battaglia::EventKind::COUNT), "colonna_sonora.h: gli eventi di battaglia");
    static_assert(colonna::INCONTRI == battaglia::INCONTRI, "colonna_sonora.h: gli incontri di battaglia");
    static_assert(colonna::EROE_DEL_FUOCO == battaglia::ANTONIO, "il fuoco e' di Antonio");
    static_assert(colonna::FASI == 4 && int(colonna::Fase::NOTTE) == int(storia::Fase::NOTTE) &&
                  int(colonna::Fase::DIGIUNO) == int(storia::Fase::DIGIUNO), "le fasi della musica e degli NPC");

    constexpr bool codici_in_ordine()
    {
        for(int c = 0; c < regia::CUTSCENE; ++c)
        {
            if(! uguali(colonna::CODICE_CUTSCENE[c], regia::CUTSCENE_DATI[c].codice))
            {
                return false;
            }
        }

        return true;
    }

    static_assert(codici_in_ordine(), "colonna_sonora.h: le cutscene in un altro ordine di regia.h (rigenerare)");
    static_assert(! uguali(colonna::CODICE_CUTSCENE[1], regia::CUTSCENE_DATI[2].codice), "negativa: il confronto dei codici");

    constexpr int cutscene(const char* codice)
    {
        for(int c = 0; c < regia::CUTSCENE; ++c)
        {
            if(uguali(regia::CUTSCENE_DATI[c].codice, codice))
            {
                return c;
            }
        }

        return -1;
    }

    // C1-C4 come le vuole la musica (musica/LEGGIMI.md): prologo, undici bandiere, presentazione, terza alba
    // col Campanone
    static_assert(colonna::BRANO_CUTSCENE[cutscene("C1")] == int(Brano::PROLOGO) &&
                  colonna::BRANO_CUTSCENE[cutscene("C2")] == int(Brano::UNDICI_BANDIERE) &&
                  colonna::BRANO_CUTSCENE[cutscene("C3U")] == int(Brano::PRESENTAZIONE) &&
                  colonna::BRANO_CUTSCENE[cutscene("C4")] == int(Brano::TERZA_ALBA) &&
                  colonna::EFFETTO_CUTSCENE[cutscene("C4")] == int(colonna::Effetto::CAMPANONE),
                  "le cutscene C1-C4 hanno un altro brano");
    static_assert(colonna::EFFETTO_CUTSCENE[cutscene("C1")] == colonna::NESSUNO, "negativa: il Campanone solo in C4");

    static_assert(colonna::BRANO_INCONTRO[storia::INCONTRO_DI_CORRADO] == Brano::CORRADO &&
                  colonna::BRANO_INCONTRO[storia::INCONTRO_DEL_TEATRO] == Brano::BATTAGLIA,
                  "Corrado ha il suo brano, la Pattuglia quello della battaglia");

    // --- Il brano di fondo: area e fase -------------------------------------------------------------
    constexpr int PIAZZA = int(mondo::AreaId::PIAZZA_GRANDE);
    constexpr int GOLA = int(mondo::AreaId::GOLA_ARCO);

    static_assert(fase_musicale(GameState{}) == colonna::Fase::GIORNO &&
                  fase_musicale(con(bit(storia::Bandiera::CITTA_IN_DIGIUNO))) == colonna::Fase::DIGIUNO &&
                  fase_musicale(con(bit(storia::Bandiera::CITTA_IN_DIGIUNO) |
                                    bit(storia::Bandiera::RIENTRO_PORTA_METAURO))) == colonna::Fase::NOTTE &&
                  fase_musicale(con(bit(storia::Bandiera::RIENTRO_PORTA_METAURO) |
                                    bit(storia::Bandiera::ATTO_I_COMPLETATO))) == colonna::Fase::ALBA,
                  "la fase della musica non segue la storia");

    static_assert(brano_di_fondo(GameState{}, PIAZZA, 0, 0) == Brano::CITTA &&
                  brano_di_fondo(con(bit(storia::Bandiera::RIENTRO_PORTA_METAURO)), PIAZZA, 0, 0) == Brano::NOTTE &&
                  brano_di_fondo(con(bit(storia::Bandiera::ATTO_I_COMPLETATO)), PIAZZA, 0, 0) == Brano::BANDIERE,
                  "Piazza Grande: citta' di giorno, notte, bandiere in festa");
    static_assert(brano_di_fondo(con(bit(storia::Bandiera::RIENTRO_PORTA_METAURO)), GOLA, 0, 0) == Brano::BOTTACCIONE,
                  "la gola e' la gola anche di notte");
    static_assert(brano_di_fondo(GameState{}, int(mondo::AreaId::BASILICA_INTERNO), 0, 0) == Brano::BASILICA &&
                  brano_di_fondo(GameState{}, int(mondo::AreaId::MONTE_INGINO), 0, 0) == Brano::STRADONI,
                  "la salita e la basilica");

    // la musica di ogni area esce dalla tabella, e nessuna area resta muta in nessuna fase
    constexpr bool ogni_area_suona()
    {
        for(int a = 0; a < mondo::AREE_CONTEGGIO; ++a)
        {
            for(int f = 0; f < colonna::FASI; ++f)
            {
                if(int(colonna::BRANO_AREA[a][f]) >= colonna::BRANI || ! colonna::IN_ANELLO[int(colonna::BRANO_AREA[a][f])])
                {
                    return false;
                }
            }
        }

        return true;
    }

    static_assert(ogni_area_suona(), "un'area senza brano, o con un jingle che finisce e la lascia muta");
    static_assert(! colonna::IN_ANELLO[int(Brano::VITTORIA)] && ! colonna::IN_ANELLO[int(Brano::FAZIO)],
                  "negativa: i jingle non tornano da capo");

    // --- I luoghi: la taverna di fondo, il segnale di Fazio ---------------------------------------------
    constexpr const colonna::Luogo& TAVERNA = colonna::LUOGO[colonna::LUOGO_TAVERNA];
    constexpr const colonna::Luogo& FAZIO = colonna::LUOGO[colonna::LUOGO_FAZIO];

    static_assert(TAVERNA.area == int(mondo::AreaId::SAN_PIETRO) && TAVERNA.modo == colonna::Modo::FONDO &&
                  brano_di_fondo(GameState{}, TAVERNA.area, TAVERNA.x0, TAVERNA.y1) == Brano::TAVERNA,
                  "davanti alla taverna di Padellino lo stornello");
    static_assert(brano_di_fondo(GameState{}, TAVERNA.area, TAVERNA.x0 - 1, TAVERNA.y1) == Brano::CITTA &&
                  brano_di_fondo(GameState{}, PIAZZA, TAVERNA.x0, TAVERNA.y1) == Brano::CITTA,
                  "negativa: lo stornello fuori dalla taverna, o in un'altra area");

    // Fazio sta nel suo luogo: la sua cella e' dentro il rettangolo, nella stessa area
    constexpr const storia::Npc& FAZIO_NPC = storia::NPC_AMBIENTE[FAZIO.npc];

    static_assert(FAZIO.npc >= 0 && FAZIO.modo == colonna::Modo::SEGNALE && FAZIO.brano == Brano::FAZIO &&
                  FAZIO_NPC.area == FAZIO.area && nel_luogo(FAZIO, FAZIO_NPC.area, FAZIO_NPC.tx, FAZIO_NPC.ty),
                  "il segnale di Fazio non e' davanti alla sua bottega");
    static_assert(segnale_qui(GameState{}, FAZIO.area, FAZIO_NPC.tx, FAZIO_NPC.ty) == colonna::LUOGO_FAZIO,
                  "entrando nella bottega di Fazio non suona il suo segnale");
    static_assert(segnale_qui(GameState{}, FAZIO.area, FAZIO.x1 + 1, FAZIO.y0) < 0 &&
                  segnale_qui(GameState{}, PIAZZA, FAZIO_NPC.tx, FAZIO_NPC.ty) < 0,
                  "negativa: il segnale fuori dalla bottega o in un'altra area");
    // col borgo dentro le mura, nel DIGIUNO Fazio e' in Sant'Andrea: la bottega tace; nell'ULTIMATUM c'e'
    static_assert(segnale_qui(con(bit(storia::Bandiera::BORGO_DENTRO) | bit(storia::Bandiera::CITTA_IN_DIGIUNO)),
                              FAZIO.area, FAZIO_NPC.tx, FAZIO_NPC.ty) < 0 &&
                  segnale_qui(con(bit(storia::Bandiera::BORGO_DENTRO)), FAZIO.area, FAZIO_NPC.tx, FAZIO_NPC.ty) ==
                  colonna::LUOGO_FAZIO &&
                  segnale_qui(con(bit(storia::Bandiera::BORGO_FUORI) | bit(storia::Bandiera::CITTA_IN_DIGIUNO)),
                              FAZIO.area, FAZIO_NPC.tx, FAZIO_NPC.ty) == colonna::LUOGO_FAZIO,
                  "il segnale di Fazio senza Fazio, o Fazio in bottega senza segnale");
    static_assert(brano_di_fondo(GameState{}, FAZIO.area, FAZIO_NPC.tx, FAZIO_NPC.ty) == Brano::CITTA,
                  "il segnale non e' un brano di fondo: dopo torna quello dell'area");

    // --- Gli effetti della battaglia ------------------------------------------------------------------
    constexpr battaglia::Evento evento(battaglia::EventKind k, int attore, bool nemico)
    {
        return { k, uint8_t(attore), 0, nemico, ! nemico, 10, 10 };
    }

    static_assert(effetto_dell_evento(evento(battaglia::EventKind::HIT, battaglia::GIORGIO, false)) ==
                  int(colonna::Effetto::COLPO) &&
                  effetto_dell_evento(evento(battaglia::EventKind::HIT, battaglia::ANTONIO, false)) ==
                  int(colonna::Effetto::FUOCO) &&
                  effetto_dell_evento(evento(battaglia::EventKind::HIT, battaglia::ANTONIO, true)) ==
                  int(colonna::Effetto::COLPO) &&
                  effetto_dell_evento(evento(battaglia::EventKind::DEFEAT, 0, true)) == int(colonna::Effetto::SVANISCE) &&
                  effetto_dell_evento(evento(battaglia::EventKind::FERVOR_GAIN, 0, false)) == colonna::NESSUNO,
                  "gli effetti della battaglia: colpo, fuoco di Antonio (non del nemico allo stesso posto), caduta");
}

}
