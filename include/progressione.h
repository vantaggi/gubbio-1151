#ifndef GUBBIO_PROGRESSIONE_H
#define GUBBIO_PROGRESSIONE_H

#include <cstdint>

#include "battaglia_dati.h"
#include "game_state.h"
#include "mondo_logica.h"

// La crescita dei Santi (F5): esperienza, livelli da 1 a 8, statistiche che salgono con il livello,
// e gli scontri sulla mappa che danno l'esperienza. Tutto constexpr: src/autotest_progressione.cpp
// prova la curva, la crescita e le posizioni dei nemici a tempo di compilazione.
namespace gubbio::progressione
{

inline constexpr int LIVELLO_MAX = 8;

// L'esperienza totale per arrivare a ogni livello (indice = livello - 1). I salti crescono: un
// livello alto costa piu' di uno basso.
inline constexpr int ESPERIENZA_PER_LIVELLO[LIVELLO_MAX] = { 0, 40, 100, 190, 310, 470, 680, 950 };

// Le statistiche al livello, in percento di quelle di base (battaglia_dati.h). Al livello 1 sono
// quelle di base: le battaglie del mirror Python (giocate al livello 1) restano le stesse.
inline constexpr int CRESCITA_PERCENTO[LIVELLO_MAX] = { 100, 108, 116, 125, 134, 144, 155, 166 };

// L'esperienza che da' ogni nemico vinto, nell'ordine di NemicoId (F8, docs/bilanciamento.md):
// Pattuglia 115 (livello 3), Imboscata 81 (livello 4), Spettri 120 (livello 5), cosi' a Corrado si
// arriva al livello 5, o al 6 con le quest (55 ciascuna). Tarata con tools/bilanciamento.py.
// I nemici di F10 danno poco: i Guerrieri della Roccia di B-03 (40) stanno fra gli Spettri e Corrado e
// non devono portare al 6 chi arriva senza quest (316 + 40 = 356, il 6 e' a 470); le tre guardie delle
// fornaci (60) e l'infiltrato con le sue due spie (84) sono facoltativi e, con le tre quest, non devono
// portare al 7 (316 + 165 + 40 + 60 + 84 = 665, il 7 e' a 680). Lo provano src/autotest_progressione.cpp
// e tests/test_bilanciamento.py.
inline constexpr int ESPERIENZA_NEMICO[int(battaglia::NemicoId::CONTEGGIO)] = { 35, 45, 200, 27, 60, 20, 30 };

[[nodiscard]] constexpr int livello_da_esperienza(int esperienza)
{
    int livello = 1;

    for(int l = 1; l < LIVELLO_MAX; ++l)
    {
        if(esperienza >= ESPERIENZA_PER_LIVELLO[l])
        {
            livello = l + 1;
        }
    }

    return livello;
}

[[nodiscard]] constexpr int cresci(int valore, int livello)
{
    return valore * CRESCITA_PERCENTO[livello - 1] / 100;
}

// Le statistiche di un Santo al suo livello: crescono PV, Fervore, Attacco, Difesa, Mistico e
// Resistenza; la Velocita' no (l'ordine dei turni resta quello dei personaggi).
[[nodiscard]] constexpr battaglia::Statistiche statistiche_al_livello(const battaglia::Statistiche& base, int livello)
{
    battaglia::Statistiche s = base;
    s.pv = cresci(base.pv, livello);
    s.fervore = cresci(base.fervore, livello);
    s.attacco = cresci(base.attacco, livello);
    s.difesa = cresci(base.difesa, livello);
    s.mistico = cresci(base.mistico, livello);
    s.resistenza = cresci(base.resistenza, livello);
    return s;
}

[[nodiscard]] constexpr int esperienza_incontro(int incontro)
{
    const battaglia::Incontro& i = battaglia::INCONTRO[incontro];
    int somma = 0;

    for(int n = 0; n < i.nemici; ++n)
    {
        somma += ESPERIENZA_NEMICO[int(i.schieramento[n])];
    }

    return somma;
}

inline constexpr int ESPERIENZA_MASSIMA = 65535;

// L'esperienza di ogni quest consegnata (docs/bilanciamento.md, tools/bilanciamento.py): a ogni Santo,
// la stessa per tutte e tre.
inline constexpr int ESPERIENZA_QUEST = 55;

// Ogni Santo prende 'punti' di esperienza (fino a ESPERIENZA_MASSIMA) e sale di livello se ne ha
// abbastanza. 'saliti' dice chi e' salito, per il messaggio. Anche chi non e' ancora nel gruppo: la
// quest e' di tutti e tre, come l'esperienza degli scontri.
constexpr void assegna_esperienza_fissa(GameState& partita, int punti, bool (&saliti)[battaglia::EROI])
{
    for(int e = 0; e < battaglia::EROI; ++e)
    {
        int prima = partita.livello[e];
        int totale = partita.esperienza[e] + punti;
        partita.esperienza[e] = uint16_t(totale > ESPERIENZA_MASSIMA ? ESPERIENZA_MASSIMA : totale);
        partita.livello[e] = uint8_t(livello_da_esperienza(partita.esperienza[e]));
        saliti[e] = partita.livello[e] > prima;
    }
}

// Dopo una vittoria: ogni Santo prende l'esperienza dello scontro.
constexpr void assegna_esperienza(GameState& partita, int incontro, bool (&saliti)[battaglia::EROI])
{
    assegna_esperienza_fissa(partita, esperienza_incontro(incontro), saliti);
}

// La partita nuova: livello 1, nessuna esperienza, nessuno scontro vinto, qualche consumabile, nessun obiettivo.
constexpr void partita_nuova(GameState& partita)
{
    for(int e = 0; e < battaglia::EROI; ++e)
    {
        partita.livello[e] = 1;
        partita.esperienza[e] = 0;
    }

    for(uint8_t& o : partita.oggetti)
    {
        o = 0;
    }

    partita.oggetti[0] = 2;     // Crescia di Pasqua (item_data.h del prototipo)
    partita.oggetti[3] = 1;     // Biscotti all'Anice

    for(uint8_t& b : partita.scontri_vinti)
    {
        b = 0;
    }

    partita.tempo_frames = 0;

    // v4 (MOB): nessun obiettivo prima della prima riga OBIETTIVO, nessuna area vista, niente denari
    partita.obiettivo = NESSUN_OBIETTIVO;

    for(uint8_t& a : partita.aree_viste)
    {
        a = 0;
    }

    partita.scorte_comprate = 0;
    partita.denari = 0;
}

// --- Gli scontri sulla mappa ----------------------------------------------------------------------
// Fonte: copione v1 (sul cloud del progetto). La Pattuglia Perugina al Teatro Romano, dove i tre
// salvano Antonio; l'Imboscata sugli stradoni del Monte Ingino; Corrado di Spoleto sulla strada del
// Bottaccione, al Condotto in fondo alla gola: un duello da cui non si fugge. La gola e' un dungeon
// ancora da fare: per ora Corrado sta davanti al suo ingresso, quando ci sara' andra' al Condotto.

enum class Bandiera : uint8_t
{
    PATTUGLIA_SCONFITTA,
    IMBOSCATA_SCONFITTA,
    CORRADO_SCONFITTO,
    CONTEGGIO,
};

struct ScontroSullaMappa
{
    mondo::AreaId area;
    int tx;                 // la cella dove sta il nemico
    int ty;
    int incontro;           // battaglia::INCONTRO
    Bandiera bandiera;      // accesa quando lo scontro e' vinto: il nemico non torna
};

inline constexpr int SCONTRI = int(Bandiera::CONTEGGIO);
inline constexpr ScontroSullaMappa SCONTRI_SULLA_MAPPA[SCONTRI] = {
    { mondo::AreaId::TEATRO_ROMANO, 40, 15, 0, Bandiera::PATTUGLIA_SCONFITTA },
    { mondo::AreaId::MONTE_INGINO, 44, 78, 1, Bandiera::IMBOSCATA_SCONFITTA },
    { mondo::AreaId::CONDOTTO, 50, 14, 2, Bandiera::CORRADO_SCONFITTO },
};

// Il contatto: i piedi del giocatore a meno di tanti pixel dal nemico, in orizzontale e in verticale.
inline constexpr int DISTANZA_CONTATTO = 12;

[[nodiscard]] constexpr bool vinto(const GameState& partita, Bandiera b)
{
    return (partita.scontri_vinti[int(b) / 8] >> (int(b) % 8)) & 1;
}

constexpr void segna_vinto(GameState& partita, Bandiera b)
{
    partita.scontri_vinti[int(b) / 8] = uint8_t(partita.scontri_vinti[int(b) / 8] | (1 << (int(b) % 8)));
}

// Lo scontro che il giocatore tocca, -1 se nessuno: solo nella sua area e solo se non e' gia' vinto.
[[nodiscard]] constexpr int scontro_toccato(const GameState& partita, mondo::AreaId area, int x, int y)
{
    for(int k = 0; k < SCONTRI; ++k)
    {
        const ScontroSullaMappa& s = SCONTRI_SULLA_MAPPA[k];
        int dx = x - mondo::piedi_x(s.tx);
        int dy = y - mondo::piedi_y(s.ty);

        if(s.area == area && ! vinto(partita, s.bandiera) && dx > -DISTANZA_CONTATTO && dx < DISTANZA_CONTATTO &&
           dy > -DISTANZA_CONTATTO && dy < DISTANZA_CONTATTO)
        {
            return k;
        }
    }

    return -1;
}

// Un posto buono per un nemico: la cella e le otto intorno calpestabili, nessun varco, e lontano dagli
// spawn d'arrivo (chi entra nell'area non deve trovarselo addosso).
[[nodiscard]] constexpr bool posto_valido(mondo::AreaId id, int tx, int ty)
{
    const mondo::Area& a = mondo::area(id);

    for(int dy = -1; dy <= 1; ++dy)
    {
        for(int dx = -1; dx <= 1; ++dx)
        {
            int c = mondo::cella(a, tx + dx, ty + dy);

            if(mondo::solida(c) || mondo::varco(c))
            {
                return false;
            }
        }
    }

    // gli spawn d'arrivo: quelli a cui portano i varchi delle altre aree
    for(int altra = 0; altra < mondo::AREE_CONTEGGIO; ++altra)
    {
        const mondo::Area& b = mondo::area(mondo::AreaId(altra));

        for(int v = 0; v < b.varchi; ++v)
        {
            const mondo::Varco& varco = mondo::varco_di(b, v);

            if(varco.destinazione != int(id))
            {
                continue;
            }

            const mondo::Punto& p = mondo::spawn_di(a, varco.spawn);
            int dx = p.x - tx;
            int dy = p.y - ty;

            if(dx > -4 && dx < 4 && dy > -4 && dy < 4)
            {
                return false;
            }
        }
    }

    return true;
}

}

#endif
