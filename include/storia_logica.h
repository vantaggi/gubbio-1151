#ifndef GUBBIO_STORIA_LOGICA_H
#define GUBBIO_STORIA_LOGICA_H

#include "game_state.h"
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
