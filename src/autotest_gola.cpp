// Autotest della gola del Bottaccione (T2), a tempo di compilazione: le scene che partono su una cella (B-02
// sulla prima nebbia, B-03 sotto l'arco) e il fatto che quelle celle sbarrino la via; i miasmi che feriscono
// chi corre (poco, mai a morte) e le ferite che pesano sulla battaglia; i soldati di B-03 fino al piano di
// Corrado; l'uscita del Condotto chiusa nel duello; i forzieri presi una volta. Ogni prova ha la sua
// negativa; se una non regge, la ROM non compila.

#include "battaglia.h"
#include "mondo_logica.h"
#include "storia_logica.h"

namespace gubbio
{

namespace
{
    using namespace storia;

    constexpr bool uguali(const char* a, const char* b)
    {
        while(*a && *a == *b)
        {
            ++a;
            ++b;
        }

        return *a == *b;
    }

    constexpr int scena(const char* codice)
    {
        for(int k = 0; k < SCENE; ++k)
        {
            if(uguali(SCENA[k].codice, codice))
            {
                return k;
            }
        }

        return -1;
    }

    constexpr void accendi_bandiera(GameState& p, Bandiera b)
    {
        accendi(p, uint64_t(1) << int(b));
    }

    // Lo stato di chi entra nella gola per la prima volta (la storia giocata fino a B-01 compreso).
    consteval GameState dopo(const char* ultima)
    {
        GameState p = {};
        progressione::partita_nuova(p);

        for(int k = 0; k <= scena(ultima); ++k)
        {
            chiudi_scena(p, k);
        }

        return p;
    }

    // --- Le scene che partono su una cella --------------------------------------------------------------

    constexpr int B02 = scena("B-02");
    constexpr int B03 = scena("B-03");
    constexpr int B04 = scena("B-04");
    static_assert(B02 >= 0 && B03 >= 0 && B04 >= 0, "le scene della gola non ci sono");
    static_assert(cella_dell_innesco(B02) == int(mondo::Cella::MIASMA) && cella_dell_innesco(B03) == int(mondo::Cella::ARCO),
                  "B-02 parte sulla nebbia e B-03 sotto l'arco");
    static_assert(cella_dell_innesco(B04) < 0 && cella_dell_innesco(scena("B-01")) < 0,
                  "negativa: B-01 e B-04 partono come sempre (entrando, toccando Corrado)");

    constexpr int MIASMI = int(mondo::AreaId::GOLA_MIASMI);
    constexpr int ARCO = int(mondo::AreaId::GOLA_ARCO);
    static_assert(pronta(dopo("B-01"), B02, MIASMI) && pronta_qui(dopo("B-01"), B02, MIASMI, int(mondo::Cella::MIASMA)),
                  "B-02 non parte sulla nebbia");
    static_assert(! pronta_qui(dopo("B-01"), B02, MIASMI, int(mondo::Cella::STRADA)),
                  "negativa: B-02 parte appena entrati, prima della nebbia");
    static_assert(pronta_qui(dopo("B-02"), B03, ARCO, int(mondo::Cella::ARCO)) &&
                  ! pronta_qui(dopo("B-02"), B03, ARCO, int(mondo::Cella::STRADA)), "B-03 non parte sotto l'arco");

    // Dallo spawn 0 (l'arrivo da valle, dal varco 'da') a un altro varco della stanza camminando sulle celle non
    // solide, senza mai entrare nella cella 'vietata' (-1: nessuna). Se la cella d'innesco sbarra la via, la
    // scena non si salta.
    consteval bool si_passa_senza(mondo::AreaId id, mondo::AreaId da, int vietata)
    {
        const mondo::Area& a = mondo::area(id);
        constexpr int N = mondo::LATO_MAX * mondo::LATO_MAX;
        bool viste[N] = {};
        int coda[N] = {};
        int testa = 0;
        int fine = 0;
        const mondo::Punto& s = mondo::spawn_di(a, 0);
        int ingresso = mondo::PRIMO_VARCO + mondo::varco_verso(id, da);
        coda[fine++] = s.x + s.y * a.larghezza;
        viste[coda[0]] = true;

        while(testa < fine)
        {
            int i = coda[testa++];
            int x = i % a.larghezza;
            int y = i / a.larghezza;
            int passi[4][2] = { { 1, 0 }, { -1, 0 }, { 0, 1 }, { 0, -1 } };

            for(auto& d : passi)
            {
                int c = mondo::cella(a, x + d[0], y + d[1]);
                int j = (x + d[0]) + (y + d[1]) * a.larghezza;

                if(mondo::varco(c) && c != ingresso)
                {
                    return true;        // l'altro varco: si e' attraversata la stanza
                }

                if(! mondo::solida(c) && ! mondo::varco(c) && c != vietata && ! viste[j])
                {
                    viste[j] = true;
                    coda[fine++] = j;
                }
            }
        }

        return false;
    }

    constexpr mondo::AreaId GM = mondo::AreaId::GOLA_MIASMI;
    constexpr mondo::AreaId GA = mondo::AreaId::GOLA_ARCO;
    static_assert(si_passa_senza(GM, mondo::AreaId::GOLA_STRISCIA, -1) && si_passa_senza(GA, GM, -1),
                  "le stanze della gola non si attraversano");
    static_assert(! si_passa_senza(GM, mondo::AreaId::GOLA_STRISCIA, int(mondo::Cella::MIASMA)),
                  "nei miasmi si passa senza toccare la nebbia: B-02 si salta e la storia si ferma");
    static_assert(! si_passa_senza(GA, GM, int(mondo::Cella::ARCO)),
                  "si passa senza l'arco: B-03 si salta e la storia si ferma");
    static_assert(si_passa_senza(GM, mondo::AreaId::GOLA_STRISCIA, int(mondo::Cella::ARCO)),
                  "negativa: nei miasmi una cella che non c'e' sbarra la via");
    static_assert(! mondo::solida(int(mondo::Cella::MIASMA)) && ! mondo::solida(int(mondo::Cella::PONTE)),
                  "la nebbia o il ponticello bloccano (indice oltre PRIMA_CELLA_SOLIDA)");

    // --- I miasmi ---------------------------------------------------------------------------------------

    consteval GameState nella_nebbia(bool visti)
    {
        GameState p = dopo("A1-09");
        p.livello[0] = p.livello[1] = p.livello[2] = 5;

        if(visti)
        {
            accendi_bandiera(p, Bandiera::MIASMI_VISTI);
        }

        return p;
    }

    // Le ferite dopo 'frame' frame sulla cella 'cella', correndo o no.
    consteval GameState respira(GameState p, int cella, bool corre, int frame)
    {
        int respiro = 0;

        for(int f = 0; f < frame; ++f)
        {
            respira_i_miasmi(p, cella, corre, respiro);
        }

        return p;
    }

    constexpr int NEBBIA = int(mondo::Cella::MIASMA);
    static_assert(respira(nella_nebbia(true), NEBBIA, true, FRAME_PER_FERITA).ferite[1] == PV_PER_FERITA &&
                  respira(nella_nebbia(true), NEBBIA, true, FRAME_PER_FERITA).ferite[2] == PV_PER_FERITA,
                  "correndo nella nebbia Giorgio e Antonio non si feriscono");
    static_assert(respira(nella_nebbia(true), NEBBIA, true, 10 * FRAME_PER_FERITA).ferite[0] == 0,
                  "Ubaldo si ferisce: la benedizione e' sua");
    static_assert(respira(nella_nebbia(true), NEBBIA, false, 10 * FRAME_PER_FERITA).ferite[1] == 0,
                  "negativa: si ferisce anche chi resta al passo di Ubaldo");
    static_assert(respira(nella_nebbia(false), NEBBIA, true, 10 * FRAME_PER_FERITA).ferite[1] == 0,
                  "negativa: i miasmi feriscono prima dell'avviso di Ubaldo (MIASMI_VISTI)");
    static_assert(respira(nella_nebbia(true), int(mondo::Cella::STRADA), true, 10 * FRAME_PER_FERITA).ferite[1] == 0,
                  "negativa: si ferisce fuori dalla nebbia");
    static_assert(respira(nella_nebbia(true), NEBBIA, true, FRAME_PER_FERITA - 1).ferite[1] == 0,
                  "negativa: la ferita arriva prima del tempo");

    // Tanta corsa: le ferite si fermano al massimo, che e' poco (il 15% dei PV) e mai tutti i PV.
    consteval bool ferite_limitate()
    {
        GameState p = respira(nella_nebbia(true), NEBBIA, true, 1000 * FRAME_PER_FERITA);

        for(int e = 1; e < battaglia::EROI; ++e)
        {
            int pv = progressione::statistiche_al_livello(battaglia::STATISTICHE_EROI[e], p.livello[e]).pv;

            if(p.ferite[e] != ferite_massime(p, e) || p.ferite[e] <= 0 || p.ferite[e] * 100 > pv * FERITE_PERCENTO_MAX)
            {
                return false;
            }
        }

        return true;
    }

    static_assert(ferite_limitate(), "le ferite dei miasmi non si fermano al loro massimo");
    static_assert(ferite_massime(nella_nebbia(true), battaglia::UBALDO) == 0, "negativa: Ubaldo ha un massimo di ferite");

    // In battaglia: i PV in meno, mai sotto 1.
    consteval int pv_in_battaglia(int eroe, uint8_t ferita)
    {
        battaglia::Battaglia b(INCONTRO_DI_CORRADO, 1);
        uint8_t ferite[battaglia::EROI] = { ferita, ferita, ferita };
        b.ricomincia(INCONTRO_DI_CORRADO, 1, false, nullptr, battaglia::TUTTI_PRESENTI, 0, 0, ferite);
        return b.eroe(eroe).pv;
    }

    static_assert(pv_in_battaglia(1, 20) == battaglia::STATISTICHE_EROI[1].pv - 20, "le ferite non pesano sulla battaglia");
    static_assert(pv_in_battaglia(2, 255) == 1 && pv_in_battaglia(0, 255) == 1, "le ferite uccidono");
    static_assert(pv_in_battaglia(1, 0) == battaglia::STATISTICHE_EROI[1].pv, "negativa: senza ferite i PV non sono pieni");

    // Fuori dalla gola le ferite guariscono; dentro restano; la battaglia le azzera (guarisci).
    consteval uint8_t ferita_dopo_l_ingresso(mondo::AreaId area)
    {
        GameState p = respira(nella_nebbia(true), NEBBIA, true, 3 * FRAME_PER_FERITA);
        all_ingresso(p, int(area));
        return p.ferite[1];
    }

    static_assert(ferita_dopo_l_ingresso(mondo::AreaId::BOTTACCIONE) == 0 && ferita_dopo_l_ingresso(mondo::AreaId::SAN_MARTINO) == 0,
                  "fuori dalla gola le ferite dei miasmi restano");
    static_assert(ferita_dopo_l_ingresso(mondo::AreaId::GOLA_ARCO) == 3 * PV_PER_FERITA,
                  "negativa: le ferite guariscono passando da una stanza all'altra della gola");

    consteval bool guarite()
    {
        GameState p = respira(nella_nebbia(true), NEBBIA, true, 3 * FRAME_PER_FERITA);
        guarisci(p);
        return p.ferite[0] == 0 && p.ferite[1] == 0 && p.ferite[2] == 0;
    }

    static_assert(guarite(), "dopo la battaglia le ferite restano");

    // --- I soldati di B-03 ------------------------------------------------------------------------------

    static_assert(sentinelle_presenti(dopo("B-02")), "i soldati non ci sono prima del piano di Corrado");
    static_assert(! sentinelle_presenti(dopo("B-03")), "negativa: i soldati restano dopo B-03 (PIANO_DI_CORRADO)");
    static_assert(SENTINELLE == 2, "i soldati di B-03 sono due");

    consteval bool sentinelle_sulla_via()
    {
        for(int k = 0; k < SENTINELLE; ++k)
        {
            const Sentinella& s = SENTINELLA[k];
            mondo::Esploratore e;
            mondo::colloca(e, mondo::AreaId(s.area), 0);
            mondo::Navigatore n;

            if(s.area != ARCO || mondo::solida(mondo::cella(mondo::area(mondo::AreaId(s.area)), s.tx, s.ty)) ||
               ! n.prepara_cella(e, s.tx, s.ty))
            {
                return false;
            }
        }

        return true;
    }

    static_assert(sentinelle_sulla_via(), "un soldato di B-03 non sta sulla via della stanza dell'arco");

    // --- L'uscita del Condotto nel duello ---------------------------------------------------------------

    constexpr int CONDOTTO = int(mondo::AreaId::CONDOTTO);
    constexpr int VARCO_A = mondo::varco_verso(mondo::AreaId::CONDOTTO, mondo::AreaId::GOLA_ARCO);

    consteval GameState al_duello(bool sconfitto)
    {
        GameState p = dopo("B-03");
        all_incontro(p, B04);

        if(sconfitto)
        {
            chiudi_scena(p, B04);
        }

        return p;
    }

    static_assert(VARCO_A >= 0 && varco_chiuso(al_duello(false), CONDOTTO) == VARCO_A,
                  "durante il duello l'uscita del Condotto non si chiude");
    static_assert(varco_chiuso(al_duello(true), CONDOTTO) < 0, "negativa: battuto Corrado l'uscita resta chiusa");
    static_assert(varco_chiuso(dopo("B-03"), CONDOTTO) < 0, "negativa: l'uscita e' chiusa prima dell'incontro");
    static_assert(varco_chiuso(al_duello(false), ARCO) < 0, "negativa: si chiude un varco fuori dal Condotto");
    static_assert(gia_incontrata(al_duello(false), B04) && ! gia_incontrata(dopo("B-03"), B04),
                  "al secondo tentativo le battute di B-04 si ripetono");
    static_assert(incontro_della_scena(B03) == 0 && incontro_della_scena(scena("A1-04")) == 0,
                  "negativa: altre scene accendono bandiere all'incontro");

    // Dallo spawn del Condotto si cammina verso il varco A: chiuso lo si urta, aperto lo si attraversa.
    consteval mondo::Evento verso_l_uscita(int chiuso)
    {
        mondo::Esploratore e;
        mondo::colloca(e, mondo::AreaId::CONDOTTO, 0);

        for(int passo = 0; passo < 200; ++passo)
        {
            if(! mondo::muovi_fino_al_varco(e, -1, 0, chiuso))
            {
                return mondo::Evento::NESSUNO;
            }

            mondo::Evento ev = mondo::controlla_varco(e);

            if(ev != mondo::Evento::NESSUNO)
            {
                return ev;
            }
        }

        return mondo::Evento::NESSUNO;
    }

    static_assert(verso_l_uscita(VARCO_A) == mondo::Evento::NESSUNO, "il varco chiuso del Condotto si attraversa");
    static_assert(verso_l_uscita(-1) == mondo::Evento::CAMBIO_AREA, "negativa: il varco aperto del Condotto non si attraversa");

    // --- I forzieri ------------------------------------------------------------------------------------

    static_assert(FORZIERI == 2 && FORZIERE[0].oggetto == int(battaglia::OggettoId::CRESCIA) &&
                  FORZIERE[1].oggetto == int(battaglia::OggettoId::BISCOTTI), "i forzieri: Crescia e Biscotti");
    static_assert(FORZIERE_CRESCIA >= 64 && FORZIERE_BISCOTTI < 128 && FORZIERE_CRESCIA != FORZIERE_BISCOTTI &&
                  FORZIERE_CRESCIA > ROSA_RIPRESA && FORZIERE_BISCOTTI > ROSA_RIPRESA,
                  "le bandiere dei forzieri fuori dall'intervallo quest o sopra quelle di SV2c");

    consteval bool forziere_una_volta(int k)
    {
        GameState p = {};
        progressione::partita_nuova(p);
        const Forziere& f = FORZIERE[k];
        int prima = p.oggetti[f.oggetto];

        if(forziere_toccato(p, f.area, mondo::piedi_x(f.tx), mondo::piedi_y(f.ty)) != k || ! apri_forziere(p, k))
        {
            return false;
        }

        int dopo_uno = p.oggetti[f.oggetto];
        bool ancora = apri_forziere(p, k);
        int massimo = battaglia::OGGETTI[f.oggetto].massimo;
        int atteso = prima + f.quanti > massimo ? massimo : prima + f.quanti;
        return dopo_uno == atteso && ! ancora && p.oggetti[f.oggetto] == atteso && ! forziere_chiuso(p, k) &&
               forziere_toccato(p, f.area, mondo::piedi_x(f.tx), mondo::piedi_y(f.ty)) < 0;
    }

    static_assert(forziere_una_volta(0) && forziere_una_volta(1), "un forziere si apre due volte o non da' l'oggetto");

    consteval bool forziere_al_massimo()
    {
        GameState p = {};
        p.oggetti[FORZIERE[1].oggetto] = uint8_t(battaglia::OGGETTI[FORZIERE[1].oggetto].massimo);
        return apri_forziere(p, 1) && p.oggetti[FORZIERE[1].oggetto] == battaglia::OGGETTI[FORZIERE[1].oggetto].massimo;
    }

    static_assert(forziere_al_massimo(), "il forziere porta oltre il massimo che se ne porta");
    static_assert(forziere_toccato(GameState{}, FORZIERE[0].area, mondo::piedi_x(FORZIERE[0].tx) + DISTANZA_RACCOLTA,
                                   mondo::piedi_y(FORZIERE[0].ty)) < 0, "negativa: il forziere si apre da lontano");

    // Ci si arriva camminando, dallo spawn d'arrivo di ogni varco della sua stanza.
    consteval bool forziere_raggiungibile(int k)
    {
        const Forziere& f = FORZIERE[k];
        const mondo::Area& a = mondo::area(mondo::AreaId(f.area));

        for(int s = 0; s < a.varchi; ++s)
        {
            mondo::Esploratore e;
            mondo::colloca(e, mondo::AreaId(f.area), s);
            mondo::Navigatore n;

            if(! n.prepara_cella(e, f.tx, f.ty))
            {
                return false;
            }
        }

        return true;
    }

    static_assert(forziere_raggiungibile(0) && forziere_raggiungibile(1), "un forziere non si raggiunge camminando");
}

}
