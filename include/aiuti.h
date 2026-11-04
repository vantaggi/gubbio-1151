#ifndef GUBBIO_AIUTI_H
#define GUBBIO_AIUTI_H

#include "cartelli.h"
#include "storia_logica.h"

// Gli aiuti al giocatore che non chiedono il menu di pausa nuovo (MAI, menu/PROPOSTA.md sez. 3.8): la logica,
// tutta constexpr, provata in src/autotest_menu.cpp. Il disegno a schermo sta in src/aiuti.cpp.
//  - Select: l'obiettivo e una freccia verso il varco della strada piu' breve per la meta (ricerca in ampiezza
//    sulle aree e i loro varchi);
//  - «Dove eravamo» dopo Continua e l'anteprima degli slot nel titolo: area, fase della cronaca, livelli,
//    incarichi aperti, tempo;
//  - i cartelli ai varchi: a 3 celle da un varco, dove porta;
//  - la sconfitta: il duello con Corrado chiede «Riprova / Carica / Titolo», le altre riportano indietro e lo
//    dicono con una riga di SISTEMA.
namespace gubbio::aiuti
{

using namespace storia;

// --- La fase della cronaca (titolo, «Dove eravamo») ----------------------------------------------------------

enum class FaseCronaca : uint8_t
{
    ULTIMATUM,
    DIGIUNO,
    NOTTE,
    DOPO_L_ALBA,
};

[[nodiscard]] constexpr FaseCronaca fase_della_cronaca(const GameState& p)
{
    if(accesa(p, Bandiera::ATTO_I_COMPLETATO))
    {
        return FaseCronaca::DOPO_L_ALBA;
    }

    return FaseCronaca(int(fase_npc(p)));
}

// Gli incarichi presi e non ancora consegnati.
[[nodiscard]] constexpr int incarichi_aperti(const GameState& p)
{
    int n = 0;

    for(int q = 0; q < QUEST; ++q)
    {
        n += presa(p, q) && ! accesa(p, int(QUEST_V1[q].consegnata)) ? 1 : 0;
    }

    return n;
}

// --- La strada piu' breve fra le aree (Select) -------------------------------------------------------------

// La prima area da attraversare sulla strada piu' breve da 'da' alla 'meta', camminando per i varchi; -1 se
// si e' gia' nella meta o se la meta non si raggiunge. A parita' di passi vince il varco che viene prima.
[[nodiscard]] constexpr int prossima_area(int da, int meta)
{
    if(da == meta || da < 0 || meta < 0 || da >= mondo::AREE_CONTEGGIO || meta >= mondo::AREE_CONTEGGIO)
    {
        return -1;
    }

    int prima[mondo::AREE_CONTEGGIO] = {};      // per ogni area raggiunta, il primo passo da 'da'
    bool viste[mondo::AREE_CONTEGGIO] = {};
    int coda[mondo::AREE_CONTEGGIO] = {};
    int testa = 0;
    int fine = 0;
    coda[fine++] = da;
    viste[da] = true;
    prima[da] = -1;

    while(testa < fine)
    {
        int x = coda[testa++];
        const mondo::Area& a = mondo::area(mondo::AreaId(x));

        for(int v = 0; v < a.varchi; ++v)
        {
            int y = a.varco[v].destinazione;

            if(y < 0 || viste[y])
            {
                continue;
            }

            viste[y] = true;
            prima[y] = x == da ? y : prima[x];

            if(y == meta)
            {
                return prima[y];
            }

            coda[fine++] = y;
        }
    }

    return -1;
}

// I passi (varchi da attraversare) da 'da' alla 'meta', -1 se non si raggiunge.
[[nodiscard]] constexpr int passi_fino_a(int da, int meta)
{
    int passi = 0;

    for(int x = da; x != meta; ++passi)
    {
        x = prossima_area(x, meta);

        if(x < 0 || passi > mondo::AREE_CONTEGGIO)
        {
            return -1;
        }
    }

    return passi;
}

struct Punto
{
    int x;
    int y;
};

// Il centro del varco k dell'area, in pixel dell'area: la media delle sue celle. (-1, -1) se non ha celle.
[[nodiscard]] constexpr Punto centro_del_varco(const mondo::Area& a, int k)
{
    int sx = 0;
    int sy = 0;
    int n = 0;

    for(int ty = 0; ty < a.altezza; ++ty)
    {
        for(int tx = 0; tx < a.larghezza; ++tx)
        {
            if(a.griglia[tx + ty * a.larghezza] == mondo::PRIMO_VARCO + k)
            {
                sx += tx;
                sy += ty;
                ++n;
            }
        }
    }

    if(n == 0)
    {
        return { -1, -1 };
    }

    return { (sx * mondo::TILE_PX) / n + mondo::TILE_PX / 2, (sy * mondo::TILE_PX) / n + mondo::TILE_PX / 2 };
}

// Fra i varchi dell'area che portano all'area 'verso', il piu' vicino al punto (x, y) in pixel dell'area; a
// parita' vince quello che viene prima. -1 se nessuno.
[[nodiscard]] constexpr int varco_piu_vicino(const mondo::Area& a, int verso, int x, int y)
{
    int scelto = -1;
    int migliore = 0;

    for(int k = 0; k < a.varchi; ++k)
    {
        if(a.varco[k].destinazione != verso)
        {
            continue;
        }

        Punto c = centro_del_varco(a, k);
        int d = (c.x - x) * (c.x - x) + (c.y - y) * (c.y - y);

        if(c.x >= 0 && (scelto < 0 || d < migliore))
        {
            scelto = k;
            migliore = d;
        }
    }

    return scelto;
}

// Il varco dell'area del giocatore verso la meta: fra quelli che portano alla prossima area della strada piu'
// breve, il piu' vicino al giocatore. -1 se si e' gia' nella meta o non c'e' strada.
[[nodiscard]] constexpr int varco_verso_la_meta(const mondo::Esploratore& e, int meta)
{
    int verso = prossima_area(int(e.area), meta);
    return verso < 0 ? -1 : varco_piu_vicino(mondo::area(e.area), verso, e.x, e.y);
}

// La freccia del promemoria: punta verso il varco lungo l'asse piu' lungo, e sta sullo schermo dentro un margine
// (il varco fuori schermo: sul bordo; sullo schermo: accanto al varco, dalla parte del giocatore).
enum class Verso : uint8_t
{
    DESTRA,
    GIU,
    SINISTRA,
    SU,
};

[[nodiscard]] constexpr Verso verso_di(int dx, int dy)
{
    int ax = dx < 0 ? -dx : dx;
    int ay = dy < 0 ? -dy : dy;

    if(ax >= ay)
    {
        return dx >= 0 ? Verso::DESTRA : Verso::SINISTRA;
    }

    return dy >= 0 ? Verso::GIU : Verso::SU;
}

inline constexpr int SCHERMO_L = 240;
inline constexpr int SCHERMO_A = 160;
inline constexpr int LATO_FRECCIA = 16;
inline constexpr int MARGINE_FRECCIA = 8;
// La freccia non scende sotto la fascia del promemoria in alto (due righe di testo dall'alto).
inline constexpr int FASCIA_PROMEMORIA = 32;

[[nodiscard]] constexpr int limita(int v, int minimo, int massimo)
{
    return v < minimo ? minimo : (v > massimo ? massimo : v);
}

// L'angolo in alto a sinistra della freccia (16x16), dato il varco in coordinate di schermo.
[[nodiscard]] constexpr Punto posto_della_freccia(int vx, int vy)
{
    return { limita(vx - LATO_FRECCIA / 2, MARGINE_FRECCIA, SCHERMO_L - MARGINE_FRECCIA - LATO_FRECCIA),
             limita(vy - LATO_FRECCIA / 2, FASCIA_PROMEMORIA, SCHERMO_A - MARGINE_FRECCIA - LATO_FRECCIA) };
}

inline constexpr int FRAME_PROMEMORIA = 180;        // 3 secondi

// Il disegno della freccia 16x16 verso destra, giu', sinistra o su: un triangolo con la base sulla colonna 2
// (righe 1-14) e la punta sulla colonna 14; gli altri versi lo ruotano. dentro_la_freccia dice se il pixel
// (x, y) e' nel triangolo.
[[nodiscard]] constexpr bool dentro_la_freccia(Verso verso, int x, int y)
{
    if(x < 0 || y < 0 || x > 15 || y > 15)
    {
        return false;
    }

    int u = verso == Verso::DESTRA ? x : (verso == Verso::SINISTRA ? 15 - x : (verso == Verso::GIU ? y : 15 - y));
    int v = verso == Verso::DESTRA || verso == Verso::SINISTRA ? y : x;
    int distanza = v < 8 ? 7 - v : v - 8;           // dalla mezzeria, 0..7
    return u >= 2 && distanza <= 6 && u <= 14 - distanza * 12 / 7;
}

// I toni della freccia nella palette del testo (stile/dati/cornice.json, ruoli): 0 trasparente, 1 il piombo
// (quasi nero, `neutri` 0) per il contorno, 2 il fondo chiaro per il pieno. Nessun colore nuovo.
inline constexpr int TONO_FRECCIA_CONTORNO = 1;
inline constexpr int TONO_FRECCIA_PIENO = 2;

// Il tono del pixel (x, y). Il contorno (STANDARD P1, P3) e' ogni pixel del triangolo con uno degli 8 vicini
// fuori: cosi' il pieno chiaro non tocca mai il lastrico chiaro, nemmeno in diagonale lungo i lati obliqui.
// vicini_in_croce = true e' il contorno vecchio, coi soli 4 vicini in croce: lo usa solo la prova negativa.
[[nodiscard]] constexpr int tono_della_freccia(Verso verso, int x, int y, bool vicini_in_croce = false)
{
    if(! dentro_la_freccia(verso, x, y))
    {
        return 0;
    }

    for(int dy = -1; dy <= 1; ++dy)
    {
        for(int dx = -1; dx <= 1; ++dx)
        {
            if((vicini_in_croce && dx != 0 && dy != 0) || (dx == 0 && dy == 0))
            {
                continue;
            }

            if(! dentro_la_freccia(verso, x + dx, y + dy))
            {
                return TONO_FRECCIA_CONTORNO;
            }
        }
    }

    return TONO_FRECCIA_PIENO;
}

// --- I cartelli ai varchi --------------------------------------------------------------------------------

inline constexpr int CELLE_CARTELLO = 3;
// Il fumetto d'interazione (STANDARD I2) sopra il cartello: alla stessa portata del tasto A con le persone
// (DISTANZA_PAROLA in src/storia_scena.cpp, 14 px fra i piedi), 2 px sopra la cella del varco.
inline constexpr int PORTATA_CARTELLO = 14;
inline constexpr int ALTEZZA_CARTELLO = mondo::TILE_PX;

// Il varco piu' vicino al giocatore entro CELLE_CARTELLO celle (distanza di Chebyshev fra le celle), -1 se
// nessuno. Sul varco stesso no: ci si sta passando.
[[nodiscard]] constexpr int varco_vicino(const mondo::Esploratore& e)
{
    const mondo::Area& a = mondo::area(e.area);
    int cx = mondo::cella_x(e);
    int cy = mondo::cella_y(e);

    if(mondo::varco(mondo::cella(a, cx, cy)))
    {
        return -1;
    }

    int scelto = -1;
    int distanza = CELLE_CARTELLO + 1;

    for(int dy = -CELLE_CARTELLO; dy <= CELLE_CARTELLO; ++dy)
    {
        for(int dx = -CELLE_CARTELLO; dx <= CELLE_CARTELLO; ++dx)
        {
            int c = mondo::cella(a, cx + dx, cy + dy);
            int d = (dx < 0 ? -dx : dx) > (dy < 0 ? -dy : dy) ? (dx < 0 ? -dx : dx) : (dy < 0 ? -dy : dy);

            if(mondo::varco(c) && c - mondo::PRIMO_VARCO < a.varchi && d < distanza)
            {
                scelto = c - mondo::PRIMO_VARCO;
                distanza = d;
            }
        }
    }

    return scelto;
}

// Dove sta il cartello del varco k per il giocatore: i piedi (piedi_x, piedi_y) della cella del varco piu'
// vicina a lui. Si legge (e si accende il fumetto) se quei piedi stanno a meno di PORTATA_CARTELLO px dai suoi,
// in orizzontale e in verticale, come per le persone; se no (-1, -1).
[[nodiscard]] constexpr Punto cartello_a_portata(const mondo::Esploratore& e, int k)
{
    const mondo::Area& a = mondo::area(e.area);

    if(k < 0 || k >= a.varchi)
    {
        return { -1, -1 };
    }

    Punto scelto = { -1, -1 };
    int migliore = 0;

    for(int ty = 0; ty < a.altezza; ++ty)
    {
        for(int tx = 0; tx < a.larghezza; ++tx)
        {
            if(a.griglia[tx + ty * a.larghezza] != mondo::PRIMO_VARCO + k)
            {
                continue;
            }

            int dx = e.x - mondo::piedi_x(tx);
            int dy = e.y - mondo::piedi_y(ty);
            int ax = dx < 0 ? -dx : dx;
            int ay = dy < 0 ? -dy : dy;
            int d = ax > ay ? ax : ay;

            if(ax < PORTATA_CARTELLO && ay < PORTATA_CARTELLO && (scelto.x < 0 || d < migliore))
            {
                scelto = { mondo::piedi_x(tx), mondo::piedi_y(ty) };
                migliore = d;
            }
        }
    }

    return scelto;
}

// Il cartello del varco dall'area 'da' all'area 'verso' (indice in cartelli::CARTELLO), -1 se non c'e' (un
// ingresso senza area, DUNGEON: il cartello dice solo il nome dell'ingresso).
[[nodiscard]] constexpr int cartello(int da, int verso)
{
    for(int k = 0; k < cartelli::CARTELLI; ++k)
    {
        if(cartelli::CARTELLO[k].da == da && cartelli::CARTELLO[k].verso == verso)
        {
            return k;
        }
    }

    return -1;
}

// --- La sconfitta --------------------------------------------------------------------------------------------

// La scena k chiede «Riprova lo scontro / Carica / Titolo» quando la sua battaglia si perde: il duello con
// Corrado (B-04), da cui non si fugge (l'incontro chiude l'uscita del Condotto). Le altre sconfitte riportano
// indietro come prima.
[[nodiscard]] constexpr bool riprova_dopo_la_sconfitta(int k)
{
    return k >= 0 && k < SCENE && incontro_della_scena(k) != 0;
}

// Cosa dire dopo una sconfitta che riporta indietro.
enum class Ritirata : uint8_t
{
    INGRESSO,           // all'ingresso dell'area (spawn 1), il nemico resta dov'e'
    ARCO,               // B-03: dalla parte dei miasmi (spawn 0), si ripassa sotto l'arco
    SUBITO,             // la scena senza nemico sulla mappa (il rito, A1-08) riparte appena si e' nell'area
};

[[nodiscard]] constexpr Ritirata ritirata_della_scena(int k)
{
    if(a_meta_della_scena(k) >= 0)
    {
        return Ritirata::ARCO;
    }

    return SCENA[k].battaglia >= progressione::SCONTRI && cella_dell_innesco(k) < 0 ? Ritirata::SUBITO : Ritirata::INGRESSO;
}

}

#endif
