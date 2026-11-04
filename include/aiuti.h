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

// --- I riquadri degli aiuti (mockup 09 e 12, animazioni A2 e A3) ------------------------------------------
// Il promemoria: un riquadro scuro in alto con la stella dell'obiettivo, e in basso a destra il nome della
// prossima area con una freccia 8x8 che punta verso il varco. Il cartello: un riquadro di legno in basso, dalla
// parte opposta al giocatore, con la freccia del varco, la via e dove porta. Le frecce e la stella sono i disegni
// dei mockup (menu/mockup_menu.py, FRECCE e ICONE["obiettivo"]): k il piombo, O l'oro acceso, o l'oro spento.

// Otto versi: la freccia punta in diagonale quando il lato corto e' almeno i due quinti del lungo.
enum class Verso : uint8_t
{
    DESTRA,
    GIU_DX,
    GIU,
    GIU_SX,
    SINISTRA,
    SU_SX,
    SU,
    SU_DX,
};

[[nodiscard]] constexpr Verso verso_di(int dx, int dy)
{
    int ax = dx < 0 ? -dx : dx;
    int ay = dy < 0 ? -dy : dy;

    if(ay * 5 <= ax * 2)
    {
        return dx >= 0 ? Verso::DESTRA : Verso::SINISTRA;
    }

    if(ax * 5 < ay * 2)
    {
        return dy >= 0 ? Verso::GIU : Verso::SU;
    }

    return dy >= 0 ? (dx >= 0 ? Verso::GIU_DX : Verso::GIU_SX) : (dx >= 0 ? Verso::SU_DX : Verso::SU_SX);
}

inline constexpr const char* FRECCIA_GIU[8] = {
    "..kkk...", "..kOk...", "..kOk...", "kkkOkkk.", ".kOOOk..", "..kOk...", "...k....", "........" };
inline constexpr const char* FRECCIA_GIU_DX[8] = {
    "kk......", "kOk.....", ".kOk..k.", "..kOkkOk", "...kOOOk", "...kOOOk", "..kkkkkk", "........" };
inline constexpr const char* STELLA[8] = {
    "...kk...", "..kOOk..", "kkkOokkk", "kOOooOOk", ".kOooOk.", ".kOkkOk.", "kOk..kOk", "kk....kk" };

// Il pixel (x, y) della freccia verso 'v': le dritte ruotano FRECCIA_GIU (disegnata su 7 righe e 7 colonne),
// le diagonali specchiano FRECCIA_GIU_DX.
[[nodiscard]] constexpr char pixel_freccia(Verso v, int x, int y)
{
    if(x < 0 || y < 0 || x > 7 || y > 7)
    {
        return '.';
    }

    switch(v)
    {
        case Verso::GIU:
            return FRECCIA_GIU[y][x];

        case Verso::SU:
            return y < 7 ? FRECCIA_GIU[6 - y][x] : '.';

        case Verso::DESTRA:
            return FRECCIA_GIU[x][y];

        case Verso::SINISTRA:
            return x < 7 ? FRECCIA_GIU[6 - x][y] : '.';

        case Verso::GIU_DX:
            return FRECCIA_GIU_DX[y][x];

        case Verso::GIU_SX:
            return FRECCIA_GIU_DX[y][7 - x];

        case Verso::SU_DX:
            return y < 7 ? FRECCIA_GIU_DX[6 - y][x] : '.';

        default:
            return y < 7 ? FRECCIA_GIU_DX[6 - y][7 - x] : '.';
    }
}

inline constexpr int SCHERMO_L = 240;
inline constexpr int SCHERMO_A = 160;
inline constexpr int FRAME_PROMEMORIA = 180;        // 3 secondi fermo, fra l'entrata e l'uscita
inline constexpr int FRAME_ENTRATA_PROMEMORIA = 5;  // A3: scende dall'alto in 5 vblank (e sale per uscire)
inline constexpr int FRAME_LAMPO = 30;              // A3: la freccia lampeggia ogni mezzo secondo
inline constexpr int FRAME_ENTRATA_CARTELLO = 4;    // A2: sale dal basso di 8 px a vblank

// Un rettangolo sullo schermo, estremi compresi.
struct Rettangolo
{
    int x0;
    int y0;
    int x1;
    int y1;
};

[[nodiscard]] constexpr bool si_toccano(const Rettangolo& a, const Rettangolo& b)
{
    return a.x0 <= b.x1 && b.x0 <= a.x1 && a.y0 <= b.y1 && b.y0 <= a.y1;
}

// Il riquadro del promemoria in alto (mockup 09): da x 2 a 237, una riga di testo alta 18 px, ogni riga in piu' 10.
// Dentro: la stella a (7, 6), il testo a (18, 6) come nell'animazione A3, largo fino a 4 px dal bordo: ci sta una
// riga intera del dialogo (216 px).
inline constexpr int PROMEMORIA_X0 = 2;
inline constexpr int PROMEMORIA_X1 = 237;
inline constexpr int PROMEMORIA_Y0 = 1;
inline constexpr int STELLA_X = 7;
inline constexpr int PROMEMORIA_TESTO_X = 18;
inline constexpr int PROMEMORIA_TESTO_DY = 5;
inline constexpr int PROMEMORIA_TESTO_MAX = PROMEMORIA_X1 - 4 - PROMEMORIA_TESTO_X + 1;

[[nodiscard]] constexpr int altezza_promemoria(int righe)
{
    return 18 + 10 * (righe - 1);
}

// La targa della prossima area, in basso a destra (mockup 09): il nome 'largo' px, la freccia a 2 px dal nome.
inline constexpr int TARGA_ALTEZZA = 16;
inline constexpr int TARGA_Y0 = 142;

[[nodiscard]] constexpr int larghezza_targa(int largo)
{
    return largo + 21;
}

// Dove va la targa: in basso a destra; se li' tocca il giocatore o il cartello, in basso a sinistra; se tocca
// anche li', subito sotto il promemoria, a destra.
[[nodiscard]] constexpr Rettangolo posto_della_targa(int largo, int righe_promemoria, const Rettangolo& giocatore,
                                                     const Rettangolo& cartello)
{
    int w = larghezza_targa(largo);
    Rettangolo destra = { PROMEMORIA_X1 - w + 1, TARGA_Y0, PROMEMORIA_X1, TARGA_Y0 + TARGA_ALTEZZA - 1 };
    Rettangolo sinistra = { PROMEMORIA_X0, TARGA_Y0, PROMEMORIA_X0 + w - 1, TARGA_Y0 + TARGA_ALTEZZA - 1 };
    int sotto = PROMEMORIA_Y0 + altezza_promemoria(righe_promemoria) + 2;
    Rettangolo in_alto = { destra.x0, sotto, destra.x1, sotto + TARGA_ALTEZZA - 1 };

    const Rettangolo prove[2] = { destra, sinistra };   // un array: niente std::initializer_list (host)

    for(const Rettangolo& r : prove)
    {
        if(! si_toccano(r, giocatore) && ! si_toccano(r, cartello))
        {
            return r;
        }
    }

    return in_alto;
}

// Il cartello (mockup 12): largo quanto la riga piu' lunga piu' 22 px, alto 28 (18 con una riga sola), a 3 px
// dal bordo in basso dalla parte opposta al giocatore (A2, scelta all'entrata e poi ferma); se anche li' tocca il
// giocatore (un cartello largo, Ubaldo in basso al centro), in alto.
inline constexpr int CARTELLO_Y0 = 129;
inline constexpr int CARTELLO_MARGINE = 3;

[[nodiscard]] constexpr int altezza_cartello(bool due_righe)
{
    return due_righe ? 28 : 18;
}

[[nodiscard]] constexpr Rettangolo posto_del_cartello(int largo, bool due_righe, const Rettangolo& giocatore)
{
    int w = largo + 22;
    int h = altezza_cartello(due_righe);
    bool a_destra = (giocatore.x0 + giocatore.x1) / 2 < SCHERMO_L / 2;
    int x0 = a_destra ? SCHERMO_L - CARTELLO_MARGINE - w : CARTELLO_MARGINE;
    int y0 = CARTELLO_Y0 + altezza_cartello(true) - h;
    Rettangolo sotto = { x0, y0, x0 + w - 1, y0 + h - 1 };

    if(! si_toccano(sotto, giocatore))
    {
        return sotto;
    }

    return { x0, CARTELLO_MARGINE, x0 + w - 1, CARTELLO_MARGINE + h - 1 };
}

// --- I cartelli ai varchi --------------------------------------------------------------------------------

inline constexpr int CELLE_CARTELLO = 3;
// Il fumetto d'interazione (STANDARD I2) sopra il cartello: alla stessa portata del tasto A con le persone
// (DISTANZA_PAROLA in src/storia_scena.cpp, 14 px fra i piedi). Il cartello non ha uno sprite: la «cosa» e' la
// soglia del varco, alta 0: il fumetto sta 2 px sopra i piedi della riga del varco piu' vicina, in mezzo al
// varco (con un'altezza da persona coprirebbe Ubaldo, che sta proprio li' davanti).
inline constexpr int PORTATA_CARTELLO = 14;
inline constexpr int ALTEZZA_CARTELLO = 0;

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

// Dove sta il fumetto del cartello del varco k: in mezzo al varco (centro_del_varco, come la freccia) sulla riga
// delle sue celle piu' vicina al giocatore, cioe' sulla soglia. Si accende se una cella del varco ha i piedi
// (piedi_x, piedi_y) a meno di PORTATA_CARTELLO px dai suoi, in orizzontale e in verticale, come per le persone;
// se no (-1, -1). In mezzo al varco, e non sulla cella sotto i piedi, il fumetto non sta sotto Ubaldo.
[[nodiscard]] constexpr Punto cartello_a_portata(const mondo::Esploratore& e, int k)
{
    const mondo::Area& a = mondo::area(e.area);

    if(k < 0 || k >= a.varchi)
    {
        return { -1, -1 };
    }

    int soglia = -1;
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

            if(ax < PORTATA_CARTELLO && ay < PORTATA_CARTELLO && (soglia < 0 || d < migliore))
            {
                soglia = mondo::piedi_y(ty);
                migliore = d;
            }
        }
    }

    return soglia < 0 ? Punto{ -1, -1 } : Punto{ centro_del_varco(a, k).x, soglia };
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
