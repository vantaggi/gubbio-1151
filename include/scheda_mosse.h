#ifndef GUBBIO_SCHEDA_MOSSE_H
#define GUBBIO_SCHEDA_MOSSE_H

#include "vista_battaglia.h"

// La schermata delle mosse (5 nov 2026, prova di Cioti: «non si capisce che effetti hanno, quanto danno
// fanno, che costo hanno»), senza Butano: quali voci ha il menu di un Santo e cosa dice la scheda della voce
// scelta. La scena (src/scena_battaglia.cpp) disegna soltanto.
//
// Il modello dei GBA e dei JRPG (Golden Sun, Final Fantasy Advance, Pokemon Rubino, Octopath):
//   - tutte le mosse in elenco, anche quelle che ora non si possono pagare (spente), cosi' nessuna
//     sparisce e il giocatore impara cosa gli manca;
//   - accanto all'elenco la scheda della voce scelta: cosa fa in parole, il numero che conta (danno,
//     barriera, cura) e il costo in Fervore contro il Fervore che il Santo ha;
//   - sul bersaglio l'anteprima di Fire Emblem: il danno su QUEL nemico e se e' il suo punto debole,
//     se resiste o se il colpo non lo scalfisce.
// Il danno mostrato e' quello delle formule del modello senza la varianza (che va dal 90 al 110 %).
namespace gubbio::battaglia
{

// Il numero della scheda e la sua etichetta.
enum class Cifra : uint8_t
{
    NESSUNA,
    DANNO,
    BARRIERA,
    CURA,
};

// Cosa dice l'anteprima sul bersaglio scelto, oltre al danno.
enum class Nota : uint8_t
{
    NESSUNA,
    DEBOLE,         // il suo punto debole: danno x1,5 e il suo scudo cede
    RESISTE,        // danno dimezzato
    IMMUNE,         // il ferro non lo scalfisce (Corrado non ustionato)
};

// Gli oggetti che si usano in battaglia, nell'ordine del menu.
inline constexpr int OGGETTI_IN_BATTAGLIA = 2;
inline constexpr OggettoId OGGETTI_USABILI[OGGETTI_IN_BATTAGLIA] = { OggettoId::CRESCIA, OggettoId::BISCOTTI };

// Le voci del menu: Attacco, le abilita' del Santo, la Carica (o la Suprema se ha caricato), gli oggetti.
inline constexpr int VOCI_MAX = 6;

// Le abilita' proprie di ogni Santo, oltre all'Attacco (Antonio ne ha una sola).
inline constexpr int PROPRIE_MAX = 2;
inline constexpr AbilitaId PROPRIE[EROI][PROPRIE_MAX] = {
    { AbilitaId::GIUDIZIO_DELLA_VERGA, AbilitaId::MURO_DELLA_FEDE },
    { AbilitaId::FENDENTE_DEL_DRAGO, AbilitaId::BASTIONE_AZZURRO },
    { AbilitaId::FUOCO_DI_SANTANTONIO, AbilitaId::FUOCO_DI_SANTANTONIO },
};
inline constexpr int QUANTE_PROPRIE[EROI] = { 2, 2, 1 };

struct Voce
{
    Comando comando;
    bool possibile = true;      // si puo' pagare (o usare) adesso: se no la voce e' spenta
};

struct Voci
{
    Voce voce[VOCI_MAX];
    int quante = 0;

    constexpr void aggiungi(const Comando& c, bool possibile)
    {
        if(quante < VOCI_MAX)
        {
            voce[quante] = { c, possibile };
            ++quante;
        }
    }
};

// Quanto Fervore costa un comando: l'abilita', o per la Carica e la Suprema la firma piu' il Boost massimo
// (la Carica non spende niente subito, ma si sceglie solo se al turno dopo la Suprema si potra' pagare).
[[nodiscard]] constexpr int costo_del_comando(const Comando& c)
{
    if(c.tipo == TipoComando::OGGETTO)
    {
        return 0;
    }

    int costo = ABILITA[int(c.abilita)].costo;
    return c.tipo == TipoComando::USA_ABILITA ? costo + BOOST_COSTO[c.boost] : costo + BOOST_COSTO[BOOST_SUPREMA];
}

// Le voci di un Santo vivo. 'scorte' sono quanti Crescia e Biscotti restano (tolti quelli gia' promessi agli
// altri Santi in questo round). Un oggetto c'e' se ne resta almeno uno; si usa se il Santo non e' a digiuno e
// c'e' un alleato che mangi.
[[nodiscard]] constexpr Voci voci_del_menu(const Battaglia& b, int e, const int (&scorte)[OGGETTI_IN_BATTAGLIA])
{
    Voci v;
    const Unita& eroe = b.eroe(e);
    AbilitaId firma = ABILITA_FIRMA[e];

    if(eroe.carica)
    {
        Comando c(TipoComando::SUPREMA, firma, -1, BOOST_SUPREMA);
        v.aggiungi(c, eroe.fervore >= costo_del_comando(c));
        return v;
    }

    v.aggiungi(Comando(TipoComando::USA_ABILITA, AbilitaId::ATTACCO, -1, 0), true);

    for(int k = 0; k < QUANTE_PROPRIE[e]; ++k)
    {
        Comando c(TipoComando::USA_ABILITA, PROPRIE[e][k], -1, 0);
        v.aggiungi(c, eroe.fervore >= costo_del_comando(c));
    }

    Comando carica(TipoComando::CARICA, firma, -1, 0);
    v.aggiungi(carica, eroe.fervore >= costo_del_comando(carica));

    bool puo_dare = ! eroe.a_digiuno && bersaglio_predefinito(b, Puntamento::CHI_MANGIA) >= 0;

    for(int k = 0; k < OGGETTI_IN_BATTAGLIA; ++k)
    {
        if(scorte[k] > 0)
        {
            Comando c;
            c.tipo = TipoComando::OGGETTO;
            c.oggetto = OGGETTI_USABILI[k];
            v.aggiungi(c, puo_dare);
        }
    }

    return v;
}

struct Scheda
{
    int valore = 0;             // il numero della Cifra
    int costo = 0;              // Fervore
    Cifra cifra = Cifra::NESSUNA;
    Nota nota = Nota::NESSUNA;
    bool a_tutti = false;       // la Suprema: lo stesso colpo su ogni nemico (il numero e' quello sul primo)
};

// L'anteprima di un colpo su un nemico: il danno senza varianza e la nota.
[[nodiscard]] constexpr Scheda anteprima_colpo(const Unita& attore, const Unita& bersaglio, AbilitaId a, int boost)
{
    const Abilita& abilita = ABILITA[int(a)];
    Scheda s;
    s.cifra = Cifra::DANNO;

    if(bersaglio.immune_al_taglio && abilita.elemento == Elemento::FISICO && bersaglio.ustione_cariche == 0)
    {
        s.nota = Nota::IMMUNE;
        s.valore = 0;
        return s;
    }

    s.valore = calcola_danno(attore, bersaglio, abilita, boost) * BOOST_COLPI[boost];
    int m = moltiplicatore(bersaglio, abilita.elemento);
    s.nota = m > ELEMENTO_NEUTRO ? Nota::DEBOLE : (m < ELEMENTO_NEUTRO ? Nota::RESISTE : Nota::NESSUNA);
    return s;
}

// La scheda di un comando del Santo 'e'. 'bersaglio' e' quello scelto (nemico o alleato, secondo il comando);
// -1 nel menu: allora il numero si calcola sul bersaglio predefinito, e senza nota (la nota e' del bersaglio).
[[nodiscard]] constexpr Scheda scheda_del_comando(const Battaglia& b, int e, const Comando& c, int bersaglio)
{
    const Unita& eroe = b.eroe(e);
    Scheda s;
    s.costo = costo_del_comando(c);

    if(c.tipo == TipoComando::OGGETTO)
    {
        const Oggetto& o = OGGETTI[int(c.oggetto)];

        if(o.cura_pv > 0)
        {
            s.cifra = Cifra::CURA;
            s.valore = o.cura_pv;

            if(bersaglio >= 0 && bersaglio < EROI)
            {
                const Unita& u = b.eroe(bersaglio);
                s.valore = u.pv + o.cura_pv > u.pv_max ? u.pv_max - u.pv : o.cura_pv;
            }
        }

        return s;
    }

    const Abilita& abilita = ABILITA[int(c.abilita)];

    if(abilita.effetto == Effetto::MURO_DELLA_FEDE)
    {
        s.cifra = Cifra::BARRIERA;
        s.valore = calcola_muro(eroe, c.boost);
        return s;
    }

    if(abilita.bersaglio != Bersaglio::NEMICO)
    {
        return s;       // il Bastione: niente numeri, lo dice la frase
    }

    bool suprema = c.tipo != TipoComando::USA_ABILITA;
    int boost = suprema ? BOOST_SUPREMA : c.boost;
    int n = bersaglio >= 0 ? bersaglio : bersaglio_predefinito(b, Puntamento::NEMICO);

    if(n < 0)
    {
        return s;
    }

    Scheda colpo = anteprima_colpo(eroe, b.nemico(n), c.abilita, boost);
    colpo.costo = s.costo;
    colpo.a_tutti = suprema;

    if(bersaglio < 0 || suprema)
    {
        colpo.nota = Nota::NESSUNA;
    }

    return colpo;
}

// L'elenco mostra QUATTRO voci per volta (le quattro righe del pannello): la prima visibile, perche' la voce
// scelta resti dentro la finestra.
inline constexpr int RIGHE_ELENCO = 4;

[[nodiscard]] constexpr int prima_visibile(int prima, int scelta, int quante)
{
    if(scelta < prima)
    {
        prima = scelta;
    }

    if(scelta >= prima + RIGHE_ELENCO)
    {
        prima = scelta - RIGHE_ELENCO + 1;
    }

    int ultima_prima = quante > RIGHE_ELENCO ? quante - RIGHE_ELENCO : 0;
    return prima < 0 ? 0 : (prima > ultima_prima ? ultima_prima : prima);
}

}

#endif
