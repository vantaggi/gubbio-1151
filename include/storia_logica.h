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
[[nodiscard]] constexpr bool scontro_attivo(const GameState& p, int incontro)
{
    int k = scena_dello_scontro(incontro);
    return k >= 0 && pronta(p, k, SCENA[k].area);
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

// Il giro di tutta la storia senza camminare: in ogni area (e a schermo intero) si gioca la prima scena
// pronta, finche' non ne resta nessuna. Ritorna quante scene sono state visitate; 'p' e' lo stato finale.
constexpr int gioca_tutta(GameState& p, const Scena* tabella = SCENA, int quante = SCENE)
{
    int visitate = 0;
    bool avanti = true;

    while(avanti)
    {
        avanti = false;

        for(int area = NESSUNA_AREA; area < mondo::AREE_CONTEGGIO && ! avanti; ++area)
        {
            int k = prossima_scena(p, area, tabella, quante);

            if(k >= 0)
            {
                chiudi_scena(p, k, tabella);
                ++visitate;
                avanti = true;
            }
        }
    }

    return visitate;
}

}

#endif
