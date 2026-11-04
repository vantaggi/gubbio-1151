#ifndef GUBBIO_NEGOZIO_H
#define GUBBIO_NEGOZIO_H

#include <cstdint>

#include "battaglia_dati.h"
#include "game_state.h"
#include "storia_logica.h"

// Il Venditore delle Logge (MNEG, menu/PROPOSTA.md sez. 3.9; mockup menu/mockup/11_bottega.png). Un solo negozio,
// sotto la Loggia dei Tiratori a Piazza Quaranta Martiri: si apre dopo le battute del Venditore (e dopo l'indizio di
// Q-SP01, se c'e'), in ogni fase: gia' prima del digiuno dice «Comprate oggi» (NPC_07_03). Si paga in denari, che
// danno i nemici sulla mappa (Corrado no). Vende solo cio' che si usa in battaglia, a scorte limitate: fino al
// rientro 3 Crescia (2 se il borgo e' dentro le mura, come dice A1-05b) e 3 Biscotti; nella notte altre 2 Crescia. Le scorte comprate stanno in GameState::scorte_comprate,
// due contatori da 4 bit. Tutto constexpr: lo prova src/autotest_negozio.cpp; il bilanciamento con tutte le scorte
// comprate e' in tools/bilanciamento.py (Corrado fra 55 e 75 %).
namespace gubbio::negozio
{

// I denari di ogni nemico vinto, nell'ordine di NemicoId: circa un terzo dell'esperienza (progressione.h).
inline constexpr int DENARI_NEMICO[int(battaglia::NemicoId::CONTEGGIO)] = { 12, 15, 0, 9, 20, 13, 10 };
inline constexpr int DENARI_MASSIMI = 9999;

[[nodiscard]] constexpr int denari_incontro(int incontro)
{
    const battaglia::Incontro& i = battaglia::INCONTRO[incontro];
    int somma = 0;

    for(int n = 0; n < i.nemici; ++n)
    {
        somma += DENARI_NEMICO[int(i.schieramento[n])];
    }

    return somma;
}

constexpr void assegna_denari(GameState& p, int incontro)
{
    int d = p.denari + denari_incontro(incontro);
    p.denari = uint16_t(d > DENARI_MASSIMI ? DENARI_MASSIMI : d);
}

// Il Venditore fra gli NPC d'ambiente (storia::NPC_AMBIENTE): lo controlla src/autotest_negozio.cpp.
inline constexpr int NPC_VENDITORE = 7;

// La merce, nell'ordine della bottega.
inline constexpr int MERCI = 2;
inline constexpr battaglia::OggettoId MERCE[MERCI] = { battaglia::OggettoId::CRESCIA, battaglia::OggettoId::BISCOTTI };
inline constexpr int PREZZO[MERCI] = { 30, 20 };

// Le scorte del Venditore fino a questa fase (sommate: nella notte ci sono quelle di prima piu' due Crescia).
[[nodiscard]] constexpr int scorte(const GameState& p, int merce)
{
    storia::Fase f = storia::fase_npc(p);
    int digiuno = merce == 0 ? (storia::accesa(p, storia::Bandiera::BORGO_DENTRO) ? 2 : 3) : 3;
    return digiuno + (f == storia::Fase::NOTTE && merce == 0 ? 2 : 0);
}

[[nodiscard]] constexpr int comprate(const GameState& p, int merce)
{
    return (p.scorte_comprate >> (4 * merce)) & 0xF;
}

[[nodiscard]] constexpr int restano(const GameState& p, int merce)
{
    int r = scorte(p, merce) - comprate(p, merce);
    return r > 0 ? r : 0;
}

// Il Venditore ha ancora qualcosa da dare.
[[nodiscard]] constexpr bool ha_merce(const GameState& p)
{
    for(int m = 0; m < MERCI; ++m)
    {
        if(restano(p, m) > 0)
        {
            return true;
        }
    }

    return false;
}

enum class Esito : uint8_t
{
    COMPRATO,
    FINITE,         // di questa non ne ha piu'
    POCHI_DENARI,
    PIENO,          // nella bisaccia non ne entra piu' (battaglia::OGGETTI[...].massimo)
};

[[nodiscard]] constexpr Esito prova(const GameState& p, int merce)
{
    int o = int(MERCE[merce]);

    if(restano(p, merce) <= 0)
    {
        return Esito::FINITE;
    }

    if(p.oggetti[o] >= battaglia::OGGETTI[o].massimo)
    {
        return Esito::PIENO;
    }

    return p.denari >= PREZZO[merce] ? Esito::COMPRATO : Esito::POCHI_DENARI;
}

constexpr Esito compra(GameState& p, int merce)
{
    Esito e = prova(p, merce);

    if(e == Esito::COMPRATO)
    {
        p.denari = uint16_t(p.denari - PREZZO[merce]);
        ++p.oggetti[int(MERCE[merce])];
        p.scorte_comprate = uint8_t(p.scorte_comprate + (1 << (4 * merce)));
    }

    return e;
}

}

#endif
