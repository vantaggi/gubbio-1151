#ifndef GUBBIO_STORIA_LOGICA_H
#define GUBBIO_STORIA_LOGICA_H

#include "battaglia_dati.h"
#include "game_state.h"
#include "mondo_logica.h"
#include "progressione.h"
#include "storia.h"

// Il motore della storia, tutto constexpr: le bandiere nello stato di partita, quale scena del copione
// parte in un'area, cosa accende quando finisce, la fase degli NPC. Lo usano la scena del gioco, la
// prova sul GBA (GUBBIO_AVVIO=8) e l'autotest a tempo di compilazione (src/autotest_storia.cpp), che
// fa girare la storia dalla prima battuta ai titoli di coda senza camminare.
namespace gubbio::storia
{

[[nodiscard]] constexpr uint64_t bandiere(const GameState& p)
{
    uint64_t v = 0;

    for(int i = 0; i < 8; ++i)
    {
        v |= uint64_t(p.storia[i]) << (8 * i);
    }

    return v;
}

constexpr void accendi(GameState& p, uint64_t maschera)
{
    uint64_t v = bandiere(p) | maschera;

    for(int i = 0; i < 8; ++i)
    {
        p.storia[i] = uint8_t(v >> (8 * i));
    }
}

[[nodiscard]] constexpr bool accesa(const GameState& p, Bandiera b)
{
    return (bandiere(p) >> int(b)) & 1;
}

// Una bandiera qualunque per indice: 0-63 la storia, 64-127 le quest e gli indizi (GameState::quest).
[[nodiscard]] constexpr bool accesa(const GameState& p, int b)
{
    return b < 64 ? ((bandiere(p) >> b) & 1) : ((p.quest[(b - 64) / 8] >> ((b - 64) % 8)) & 1);
}

constexpr void accendi_una(GameState& p, int b)
{
    if(b == NESSUNA_BANDIERA)
    {
        return;
    }

    if(b < 64)
    {
        accendi(p, uint64_t(1) << b);
    }
    else
    {
        p.quest[(b - 64) / 8] = uint8_t(p.quest[(b - 64) / 8] | (1 << ((b - 64) % 8)));
    }
}

// Quanti pezzi dell'obiettivo della quest q sono raccolti: le sue bandiere consecutive da primo_pezzo accese
// (i blocchi di ferro, le radici, la Rosa). E' il contatore delle quest, fatto di bandiere (SV2c): nessun
// campo nuovo in GameState, il salvataggio resta v3.
[[nodiscard]] constexpr int pezzi_raccolti(const GameState& p, int q)
{
    const QuestGioco& g = QUEST_GIOCO[q];
    int n = 0;

    for(int i = 0; i < g.pezzi; ++i)
    {
        n += accesa(p, g.primo_pezzo + i) ? 1 : 0;
    }

    return n;
}

// La guardia di una battuta vale? 'scelta' e' la voce scelta nell'ultimo menu della recita (-1 nessuno).
[[nodiscard]] constexpr bool vale(const GameState& p, int guardia, int scelta)
{
    const Guardia& g = GUARDIA[guardia];

    switch(g.tipo)
    {
        case TipoGuardia::SEMPRE:
            return true;
        case TipoGuardia::BANDIERA:
        case TipoGuardia::VARIANTE_BANDIERA:
            return accesa(p, int(g.a));
        case TipoGuardia::NON_BANDIERA:
        case TipoGuardia::VARIANTE_NON_BANDIERA:
            return ! accesa(p, int(g.a));
        case TipoGuardia::SCELTA:
            return scelta == int(g.a);
        case TipoGuardia::ALMENO_DUE:
            return int(accesa(p, int(g.a))) + int(accesa(p, int(g.b))) + int(accesa(p, int(g.c))) >= 2;
        case TipoGuardia::OGGETTO_E_NON_BANDIERA:
            return p.oggetti[g.a] > 0 && ! accesa(p, int(g.b));
        case TipoGuardia::CONTEGGIO:
            return pezzi_raccolti(p, g.a) == g.b && (g.c == NESSUNA_BANDIERA || accesa(p, int(g.c)));
        case TipoGuardia::CONTEGGIO_E_NON_BANDIERA:
            return pezzi_raccolti(p, g.a) == g.b && ! accesa(p, int(g.c));
    }

    return false;
}

[[nodiscard]] constexpr bool variante(int guardia)
{
    TipoGuardia t = GUARDIA[guardia].tipo;
    return t == TipoGuardia::VARIANTE_BANDIERA || t == TipoGuardia::VARIANTE_NON_BANDIERA;
}

// La voce di un NPC in una fase: la prima variante "(se BANDIERA)" che vale parla da sola (ritorna il suo
// indice); se nessuna vale, -1 e parlano le altre righe della fase, in ordine.
[[nodiscard]] constexpr int variante_che_vale(const GameState& p, const Battuta* tabella, int prima, int quante)
{
    for(int i = prima; i < prima + quante; ++i)
    {
        if(variante(tabella[i].guardia) && vale(p, tabella[i].guardia, -1))
        {
            return i;
        }
    }

    return -1;
}

// Una scelta fatta: accende la bandiera della voce e, per la prima voce, consuma l'oggetto.
constexpr void scegli(GameState& p, const Battuta& b, int voce)
{
    accendi_una(p, b.accende[voce]);

    if(voce == 0 && b.consuma >= 0 && p.oggetti[b.consuma] > 0)
    {
        --p.oggetti[b.consuma];
    }
}

// Le scelte di una scena senza recitarla (il giro di tutta la storia): ogni menu prende la voce data.
constexpr void scegli_tutto(GameState& p, int k, int voce, const Scena* tabella = SCENA)
{
    const Scena& s = tabella[k];
    int scelta = -1;

    for(int i = s.prima_battuta; i < s.prima_battuta + s.battute; ++i)
    {
        const Battuta& b = BATTUTA[i];

        if(b.tipo == TipoBattuta::SCELTA && vale(p, b.guardia, scelta))
        {
            scelta = voce;
            scegli(p, b, voce);
        }
    }
}

// Entrando in un'area: chi sale agli Stradoni durante il digiuno senza aver deciso del borgo l'ha
// lasciato fuori (copione v2, A1-05b).
constexpr void all_ingresso(GameState& p, int area)
{
    if(area == int(mondo::AreaId::MONTE_INGINO) && accesa(p, Bandiera::CITTA_IN_DIGIUNO) &&
       ! accesa(p, Bandiera::BORGO_DENTRO) && ! accesa(p, Bandiera::BORGO_FUORI))
    {
        accendi(p, uint64_t(1) << int(Bandiera::BORGO_FUORI));
    }
}

[[nodiscard]] constexpr bool fatta(const GameState& p, int scena)
{
    return (p.scene_fatte[scena / 8] >> (scena % 8)) & 1;
}

static_assert(SCENE <= 32, "le scene fatte stanno in 4 byte di GameState");
static_assert(int(Bandiera::CONTEGGIO) <= 64, "le bandiere della storia stanno in 8 byte di GameState");

// La scena k parte nell'area 'area' (NESSUNA_AREA per quelle a schermo intero)?
[[nodiscard]] constexpr bool pronta(const GameState& p, int k, int area, const Scena* tabella = SCENA)
{
    const Scena& s = tabella[k];
    uint64_t v = bandiere(p);
    return ! fatta(p, k) && s.area == area && (v & s.richieste) == s.richieste && (v & s.vietate) == 0 &&
           (s.segue < 0 || fatta(p, s.segue));
}

// La prima scena pronta nell'area, -1 se nessuna.
[[nodiscard]] constexpr int prossima_scena(const GameState& p, int area, const Scena* tabella = SCENA, int quante = SCENE)
{
    for(int k = 0; k < quante; ++k)
    {
        if(pronta(p, k, area, tabella))
        {
            return k;
        }
    }

    return -1;
}

// La scena finita (battute lette, battaglia vinta): accende le sue bandiere e si segna fatta.
constexpr void chiudi_scena(GameState& p, int k, const Scena* tabella = SCENA)
{
    accendi(p, tabella[k].imposta);
    p.scene_fatte[k / 8] = uint8_t(p.scene_fatte[k / 8] | (1 << (k % 8)));
}

// La scena che contiene uno scontro sulla mappa (battaglia::INCONTRO), -1 se nessuna.
[[nodiscard]] constexpr int scena_dello_scontro(int incontro, const Scena* tabella = SCENA, int quante = SCENE)
{
    for(int k = 0; k < quante; ++k)
    {
        if(tabella[k].battaglia == incontro)
        {
            return k;
        }
    }

    return -1;
}

// Un nemico sulla mappa c'e' solo quando la sua scena e' pronta: niente Pattuglia al Teatro prima che
// la storia ci porti, niente doppia battaglia dopo. Toccarlo fa partire la scena (con la battaglia).
// La bandiera della storia che dice uno scontro vinto: con lei accesa il nemico non torna, anche se
// la scena fosse ancora da chiudere (un salvataggio a meta').
[[nodiscard]] constexpr Bandiera bandiera_dello_scontro(int incontro)
{
    return incontro == 0 ? Bandiera::ANTONIO_NEL_GRUPPO :
           (incontro == 1 ? Bandiera::IMBOSCATA_STRADONI : Bandiera::CORRADO_SCONFITTO);
}

[[nodiscard]] constexpr bool scontro_attivo(const GameState& p, int incontro)
{
    int k = scena_dello_scontro(incontro);
    return k >= 0 && pronta(p, k, SCENA[k].area) && ! accesa(p, bandiera_dello_scontro(incontro));
}

inline constexpr int INCONTRO_DEL_TEATRO = 0;     // la Pattuglia Perugina che circonda Antonio (A1-04)

// Chi c'e' nel gruppo in battaglia: Ubaldo sempre, Giorgio dall'ultimatum, Antonio da quando e' salvato
// (al Teatro, nella sua battaglia, e' gia' li': c'e' da ospite).
[[nodiscard]] constexpr uint8_t gruppo(const GameState& p, int incontro)
{
    uint8_t g = 1;
    g = uint8_t(g | (accesa(p, Bandiera::GIORGIO_NEL_GRUPPO) ? 2 : 0));
    bool antonio = accesa(p, Bandiera::ANTONIO_NEL_GRUPPO) || incontro == INCONTRO_DEL_TEATRO;
    return uint8_t(g | (antonio ? 4 : 0));
}

// La fase degli NPC dalle bandiere (README del copione): NOTTE dal rientro da Porta Metauro, DIGIUNO
// da quando la citta' si chiude, prima ULTIMATUM.
[[nodiscard]] constexpr Fase fase_npc(const GameState& p)
{
    if(accesa(p, Bandiera::RIENTRO_PORTA_METAURO))
    {
        return Fase::NOTTE;
    }

    return accesa(p, Bandiera::CITTA_IN_DIGIUNO) ? Fase::DIGIUNO : Fase::ULTIMATUM;
}

inline constexpr int INCONTRO_DI_CORRADO = 2;     // il duello sul Condotto (B-04)

// Gli scudi in meno dei nemici di uno scontro (Battaglia::ricomincia): Corrado ne ha uno in meno se Q-SM01
// e' consegnata (il ferro di Raniero torna alle fornaci della citta') o se Rufino ha detto che col calore il
// ferro si apre (RUFINO_ASCOLTATO). Le due cose non si sommano (copione 02 e 04, «uno scudo in meno»).
[[nodiscard]] constexpr int scudi_in_meno(const GameState& p, int incontro)
{
    return incontro == INCONTRO_DI_CORRADO && (accesa(p, int(RUFINO_ASCOLTATO)) || accesa(p, int(Q_SM01_CONSEGNATA)))
           ? 1 : 0;
}

// Chi e' a digiuno in battaglia (un bit per Santo, Battaglia::ricomincia): Ubaldo nel DIGIUNO, da
// CITTA_IN_DIGIUNO al rientro da Porta Metauro (B-05, RIENTRO_PORTA_METAURO), non usa il cibo e nessuno
// glielo da' (README del copione: «durante il DIGIUNO Ubaldo non puo' usare il cibo fino al rientro in
// citta'»; A1-05: «Il digiuno e' per chi prega. Chi combatte, mangi»).
[[nodiscard]] constexpr uint8_t a_digiuno(const GameState& p)
{
    return accesa(p, Bandiera::CITTA_IN_DIGIUNO) && ! accesa(p, Bandiera::RIENTRO_PORTA_METAURO)
           ? uint8_t(1 << battaglia::UBALDO) : uint8_t(0);
}

// Una quest si consegna se e' gia' stata data (la sua bandiera di partenza), prima della sua scadenza
// (ATTO_I_COMPLETATO: la conferma dell'alba che avvia E-01; regola «nessuna quest si perde») e una volta sola.
[[nodiscard]] constexpr bool quest_consegnabile(const GameState& p, int q)
{
    const Quest& d = QUEST_V1[q];
    return accesa(p, d.da) && ! accesa(p, d.entro) && ! accesa(p, int(d.consegnata));
}

// La quest q e' stata presa dal datore (la sua proposta e' stata detta).
[[nodiscard]] constexpr bool presa(const GameState& p, int q)
{
    return accesa(p, int(QUEST_GIOCO[q].presa));
}

// L'obiettivo e' finito: tutti i pezzi raccolti (3 blocchi, 4 radici, la Rosa).
[[nodiscard]] constexpr bool obiettivo_fatto(const GameState& p, int q)
{
    return pezzi_raccolti(p, q) == QUEST_GIOCO[q].pezzi;
}

// Si puo' consegnare adesso: nel suo tempo, non ancora consegnata, presa e con l'obiettivo finito.
[[nodiscard]] constexpr bool quest_pronta(const GameState& p, int q)
{
    return quest_consegnabile(p, q) && presa(p, q) && obiettivo_fatto(p, q);
}

// La consegna di una quest (presa e con l'obiettivo finito, quest_pronta): accende la sua bandiera, da' il
// premio (fino al massimo che se ne porta) e ESPERIENZA_QUEST a ogni Santo. Ritorna false, e non cambia
// nulla, se la quest non si puo' consegnare (fuori tempo, gia' consegnata, non presa, obiettivo a meta').
// 'saliti' dice chi e' salito.
constexpr bool consegna_quest(GameState& p, int q, bool (&saliti)[battaglia::EROI])
{
    for(bool& s : saliti)
    {
        s = false;
    }

    if(q < 0 || q >= QUEST || ! quest_pronta(p, q))
    {
        return false;
    }

    const Quest& d = QUEST_V1[q];
    accendi_una(p, d.consegnata);
    int quanti = p.oggetti[d.oggetto] + d.quanti;
    int massimo = battaglia::OGGETTI[d.oggetto].massimo;
    p.oggetti[d.oggetto] = uint8_t(quanti > massimo ? massimo : quanti);
    progressione::assegna_esperienza_fissa(p, progressione::ESPERIENZA_QUEST, saliti);
    return true;
}

// --- I datori, gli oggetti da raccogliere, gli indizi e l'infiltrato (SV2c) -----------------------------

// Cosa dice il datore di una quest adesso. ASSENTE: prima che la quest si prenda (o dopo E-01) non c'e'.
enum class Momento : uint8_t
{
    ASSENTE,
    PROPOSTA,
    ATTESA,
    CONSEGNA,
    DOPO,
};

[[nodiscard]] constexpr Momento momento_del_datore(const GameState& p, int q)
{
    if(accesa(p, int(QUEST_V1[q].consegnata)))
    {
        return Momento::DOPO;
    }

    if(! quest_consegnabile(p, q))
    {
        return Momento::ASSENTE;
    }

    if(! presa(p, q))
    {
        return Momento::PROPOSTA;
    }

    return obiettivo_fatto(p, q) ? Momento::CONSEGNA : Momento::ATTESA;
}

// La proposta detta: la quest e' presa. False (e nulla cambia) se il datore non era alla proposta.
constexpr bool prendi_quest(GameState& p, int q)
{
    if(momento_del_datore(p, q) != Momento::PROPOSTA)
    {
        return false;
    }

    accendi_una(p, QUEST_GIOCO[q].presa);
    return true;
}

// Le righe di FRASE_QUEST che il datore dice in quel momento (il dopo secondo la fase).
[[nodiscard]] constexpr Righe righe_del_datore(const GameState& p, int q, Momento m)
{
    const QuestGioco& g = QUEST_GIOCO[q];

    switch(m)
    {
        case Momento::PROPOSTA:
            return g.proposta;
        case Momento::ATTESA:
            return g.attesa;
        case Momento::CONSEGNA:
            return g.consegna;
        case Momento::DOPO:
            return g.dopo[int(fase_npc(p))];
        case Momento::ASSENTE:
            break;
    }

    return Righe{ 0, 0 };
}

// Il contatto con un oggetto da raccogliere: i piedi a meno di tanti pixel dal centro della sua cella.
inline constexpr int DISTANZA_RACCOLTA = 10;

// Un oggetto c'e' finche' non e' raccolto, anche se la quest non e' presa (regola «nessuna quest si perde»):
// non legge la fase ne' la storia, quindi le radici della gola ci sono anche dopo B-05.
[[nodiscard]] constexpr bool raccolta_presente(const GameState& p, int k)
{
    return ! accesa(p, int(RACCOLTA[k].bandiera));
}

// L'oggetto che il giocatore tocca nell'area, -1 se nessuno.
[[nodiscard]] constexpr int raccolta_toccata(const GameState& p, int area, int x, int y)
{
    for(int k = 0; k < RACCOLTE; ++k)
    {
        const Raccolta& r = RACCOLTA[k];
        int dx = x - mondo::piedi_x(r.tx);
        int dy = y - mondo::piedi_y(r.ty);

        if(r.area == area && raccolta_presente(p, k) && dx > -DISTANZA_RACCOLTA && dx < DISTANZA_RACCOLTA &&
           dy > -DISTANZA_RACCOLTA && dy < DISTANZA_RACCOLTA)
        {
            return k;
        }
    }

    return -1;
}

// Raccoglie l'oggetto k: accende la sua bandiera (il contatore della quest sale). False se era gia' preso.
// Dopo, le righe di raccolta della quest (QUEST_GIOCO[q].raccolta) valgono secondo il nuovo contatore.
constexpr bool raccogli(GameState& p, int k)
{
    if(k < 0 || k >= RACCOLTE || ! raccolta_presente(p, k))
    {
        return false;
    }

    accendi_una(p, RACCOLTA[k].bandiera);
    return true;
}

// Gli indizi di Q-SP01 si chiedono finche' la quest e' presa, la Rosa non e' ripresa e la quest si consegna.
[[nodiscard]] constexpr bool indizi_attivi(const GameState& p)
{
    return presa(p, QUEST_DEGLI_INDIZI) && ! obiettivo_fatto(p, QUEST_DEGLI_INDIZI) &&
           quest_consegnabile(p, QUEST_DEGLI_INDIZI);
}

// L'indizio che l'NPC d'ambiente 'npc' dice dopo le sue battute, -1 se nessuno (o se gli indizi non sono attivi).
[[nodiscard]] constexpr int indizio_dell_npc(const GameState& p, int npc)
{
    if(! indizi_attivi(p))
    {
        return -1;
    }

    for(int k = 0; k < INDIZI; ++k)
    {
        if(INDIZIO[k].npc == npc)
        {
            return k;
        }
    }

    return -1;
}

[[nodiscard]] constexpr int indizi_trovati(const GameState& p)
{
    int n = 0;

    for(const Indizio& i : INDIZIO)
    {
        n += accesa(p, int(i.bandiera)) ? 1 : 0;
    }

    return n;
}

// Accende l'indizio k. True se e' quello che li completa (la prima volta): allora si dice INDIZI_COMPLETI.
constexpr bool trova_indizio(GameState& p, int k)
{
    bool tutti_prima = indizi_trovati(p) == INDIZI;
    accendi_una(p, INDIZIO[k].bandiera);
    return ! tutti_prima && indizi_trovati(p) == INDIZI;
}

// L'infiltrato sta sotto le Logge con i tre indizi, finche' la Rosa non e' ripresa.
[[nodiscard]] constexpr bool infiltrato_presente(const GameState& p)
{
    return indizi_attivi(p) && indizi_trovati(p) == INDIZI;
}

static_assert(QUEST_GIOCO[QUEST_DEGLI_INDIZI].primo_pezzo == ROSA_RIPRESA && QUEST_GIOCO[QUEST_DEGLI_INDIZI].pezzi == 1,
              "l'obiettivo di Q-SP01 e' la Rosa");

// La battaglia con l'infiltrato vinta: la Rosa e' ripresa (l'obiettivo di Q-SP01). False se non c'era.
constexpr bool riprendi_la_rosa(GameState& p)
{
    if(! infiltrato_presente(p))
    {
        return false;
    }

    accendi_una(p, ROSA_RIPRESA);
    return true;
}

// Il giro senza camminare, quando nessuna scena e' pronta: la prima scelta di un NPC della fase che
// accende una bandiera ancora spenta prende la prima voce. E' la conferma dell'alba del console Guido
// (ALBA_CONFERMATA) per chi in B-05 ha detto «Non ancora». Ritorna true se ha acceso qualcosa.
constexpr bool risposta_di_un_npc(GameState& p)
{
    int fase = int(fase_npc(p));

    for(int i = 0; i < NPC; ++i)
    {
        const Npc& n = NPC_AMBIENTE[i];

        for(int j = n.prima_frase[fase]; n.frasi[fase] > 0 && j < n.prima_frase[fase] + n.frasi[fase]; ++j)
        {
            const Battuta& b = FRASE_NPC[j];

            if(b.tipo == TipoBattuta::SCELTA && b.accende[0] != NESSUNA_BANDIERA && vale(p, b.guardia, -1) &&
               ! accesa(p, int(b.accende[0])))
            {
                scegli(p, b, 0);
                return true;
            }
        }
    }

    return false;
}

// Il giro di tutta la storia senza camminare: si gioca la prima scena pronta nell'ordine del copione
// (ognuna nella sua area), finche' non ne resta nessuna. Ritorna quante scene sono state visitate; 'p' e'
// lo stato finale. Ogni menu di scelta prende la voce 'voce'.
constexpr int gioca_tutta(GameState& p, const Scena* tabella = SCENA, int quante = SCENE, int voce = 0)
{
    int visitate = 0;
    bool avanti = true;

    while(avanti)
    {
        avanti = false;

        for(int k = 0; k < quante && ! avanti; ++k)
        {
            if(pronta(p, k, tabella[k].area, tabella))
            {
                if(tabella == SCENA)
                {
                    scegli_tutto(p, k, voce, tabella);
                }

                chiudi_scena(p, k, tabella);
                ++visitate;
                avanti = true;
            }
        }

        // ferma la storia, si va a parlare con chi rifa' una domanda (la conferma dell'alba)
        if(! avanti && tabella == SCENA)
        {
            avanti = risposta_di_un_npc(p);
        }
    }

    return visitate;
}

}

#endif
