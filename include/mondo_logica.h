#ifndef GUBBIO_MONDO_LOGICA_H
#define GUBBIO_MONDO_LOGICA_H

#include "mondo.h"
#include "tabella.h"

// Logica del mondo, tutta constexpr: la usa la scena di esplorazione, l'autotest a tempo di
// compilazione (include/mondo_autotest.h) e la camminata automatica sul GBA. Un solo codice
// per muoversi, urtare e attraversare i varchi: l'autotest misura il gioco, non una sua copia.
namespace gubbio::mondo
{

inline constexpr int TILE_PX = 8;

// Il giocatore e' un punto ai piedi; il suo ingombro e' un rettangolo di 7 x 4 px sopra quel
// punto. Sta dentro un tile, quindi passa in ogni corridoio largo almeno un tile.
inline constexpr int INGOMBRO_LATO = 3;
inline constexpr int INGOMBRO_ALTO = 3;

constexpr const Area& area(AreaId id)
{
    return GUBBIO_VOCE(AREE, int(id));
}

// Cella (tx, ty) dell'area: fuori dalla griglia e' muro.
constexpr int cella(const Area& a, int tx, int ty)
{
    if(tx < 0 || ty < 0 || tx >= a.larghezza || ty >= a.altezza)
    {
        return int(Cella::MURO);
    }

    int i = tx + ty * a.larghezza;
    BN_ASSERT(i >= 0 && i < a.larghezza * a.altezza, "Griglia: indice ", i, " fuori area");
    return a.griglia[i];
}

constexpr bool solida(int c)
{
    return c >= PRIMA_CELLA_SOLIDA && c < PRIMO_VARCO;
}

constexpr bool varco(int c)
{
    return c >= PRIMO_VARCO;
}

constexpr const Varco& varco_di(const Area& a, int indice)
{
    BN_ASSERT(indice >= 0 && indice < a.varchi, "Varco: indice ", indice, " fuori da 0..", a.varchi - 1);
    return GUBBIO_VOCE(a.varco, indice);
}

constexpr const Punto& spawn_di(const Area& a, int indice)
{
    return GUBBIO_VOCE(a.spawn, indice);
}

// Il punto ai piedi per stare al centro della cella (tx, ty).
constexpr int piedi_x(int tx)
{
    return tx * TILE_PX + TILE_PX / 2;
}

constexpr int piedi_y(int ty)
{
    return ty * TILE_PX + TILE_PX - 2;
}

enum class Evento : uint8_t
{
    NESSUNO,
    CAMBIO_AREA,
    INGRESSO_DUNGEON,
};

struct Esploratore
{
    AreaId area = AreaId(0);
    int x = 0;                 // piedi, in pixel dell'area
    int y = 0;
    int varco_sotto = -1;      // varco su cui sta: un ingresso scatta entrandoci, non restandoci
    int ultimo_varco = -1;     // varco dell'ultimo evento
};

constexpr void colloca(Esploratore& e, AreaId id, int spawn)
{
    const Punto& p = spawn_di(area(id), spawn);
    e.area = id;
    e.x = piedi_x(p.x);
    e.y = piedi_y(p.y);
    e.varco_sotto = -1;
}

// La cella su cui conta il giocatore: quella del centro del suo ingombro.
constexpr int cella_x(const Esploratore& e)
{
    return e.x / TILE_PX;
}

constexpr int cella_y(const Esploratore& e)
{
    return (e.y - 1) / TILE_PX;
}

constexpr bool libero(const Area& a, int x, int y)
{
    int sx = (x - INGOMBRO_LATO) / TILE_PX;
    int dx = (x + INGOMBRO_LATO) / TILE_PX;
    int su = (y - INGOMBRO_ALTO) / TILE_PX;
    int giu = y / TILE_PX;
    return x - INGOMBRO_LATO >= 0 && y - INGOMBRO_ALTO >= 0 &&
           ! solida(cella(a, sx, su)) && ! solida(cella(a, dx, su)) &&
           ! solida(cella(a, sx, giu)) && ! solida(cella(a, dx, giu));
}

// Dopo ogni spostamento: se il giocatore e' entrato in un varco, lo attraversa.
constexpr Evento controlla_varco(Esploratore& e)
{
    const Area& a = area(e.area);
    int c = cella(a, cella_x(e), cella_y(e));

    if(! varco(c))
    {
        e.varco_sotto = -1;
        return Evento::NESSUNO;
    }

    int indice = c - PRIMO_VARCO;

    if(indice == e.varco_sotto)
    {
        return Evento::NESSUNO;
    }

    e.varco_sotto = indice;
    e.ultimo_varco = indice;
    const Varco& v = varco_di(a, indice);

    if(v.destinazione == DUNGEON)
    {
        return Evento::INGRESSO_DUNGEON;
    }

    colloca(e, AreaId(v.destinazione), v.spawn);
    return Evento::CAMBIO_AREA;
}

// Un passo di un pixel (dx, dy in -1..1, uno dei due zero). Ritorna false se il passo e' bloccato.
constexpr bool muovi(Esploratore& e, int dx, int dy)
{
    const Area& a = area(e.area);

    if(! libero(a, e.x + dx, e.y + dy))
    {
        return false;
    }

    e.x += dx;
    e.y += dy;
    return true;
}

// Come muovi(), ma il passo che porterebbe il giocatore sul varco 'chiuso' (indice nell'area, -1 nessuno) non
// si fa: il varco si vede ma si urta come un muro. Quale varco sia chiuso lo dice chi chiama (il duello del
// Condotto, varco_chiuso in storia_logica.h): la logica del mondo resta senza stato di partita. False anche per
// l'urto col varco: chi chiama distingue con urta_il_varco().
[[nodiscard]] constexpr bool urta_il_varco(const Esploratore& e, int dx, int dy, int chiuso)
{
    return chiuso >= 0 && cella(area(e.area), (e.x + dx) / TILE_PX, (e.y + dy - 1) / TILE_PX) == PRIMO_VARCO + chiuso;
}

constexpr bool muovi_fino_al_varco(Esploratore& e, int dx, int dy, int chiuso)
{
    return ! urta_il_varco(e, dx, dy, chiuso) && muovi(e, dx, dy);
}

// Il navigatore: cerca la strada sulla griglia (in ampiezza, sulle celle non solide) fino a un
// varco e la percorre un pixel alla volta con muovi(), cioe' con la stessa collisione del gioco.
// Gli altri varchi non si attraversano: la strada li aggira.
class Navigatore
{

public:
    static constexpr int CELLE_MAX = LATO_MAX * LATO_MAX;

    // Prepara la strada dalla cella del giocatore al varco 'obiettivo'. false se non esiste.
    constexpr bool prepara(const Esploratore& e, int obiettivo)
    {
        return _prepara(e, obiettivo, -1, -1);
    }

    // Prepara la strada fino alla cella (tx, ty), senza attraversare varchi (un oggetto da raccogliere,
    // le quest). false se non esiste.
    constexpr bool prepara_cella(const Esploratore& e, int tx, int ty)
    {
        return _prepara(e, -1, tx, ty);
    }

    // Un pixel verso la prossima cella della strada. Ritorna false se il passo e' bloccato o se
    // la strada e' finita senza evento.
    constexpr bool passo(Esploratore& e, Evento& evento)
    {
        evento = Evento::NESSUNO;

        if(_prossimo >= _lunghezza)
        {
            return false;
        }

        int obiettivo = _strada[_prossimo];
        int tx = piedi_x(obiettivo % _larghezza);
        int ty = piedi_y(obiettivo / _larghezza);
        int dx = tx > e.x ? 1 : (tx < e.x ? -1 : 0);
        int dy = dx ? 0 : (ty > e.y ? 1 : (ty < e.y ? -1 : 0));

        if(dx == 0 && dy == 0)
        {
            ++_prossimo;
            return true;
        }

        if(! muovi(e, dx, dy))
        {
            return false;
        }

        evento = controlla_varco(e);
        return true;
    }

    [[nodiscard]] constexpr int lunghezza() const
    {
        return _lunghezza;
    }

private:
    int16_t _da[CELLE_MAX] = {};
    int16_t _coda[CELLE_MAX] = {};
    int16_t _strada[CELLE_MAX] = {};
    int _lunghezza = 0;
    int _larghezza = 0;
    int _prossimo = 0;

    // La ricerca in ampiezza: fino al varco 'obiettivo' o, con obiettivo < 0, fino alla cella (cx, cy).
    constexpr bool _prepara(const Esploratore& e, int obiettivo, int cx, int cy)
    {
        const Area& a = area(e.area);
        int w = a.larghezza;
        int n = w * a.altezza;
        BN_ASSERT(n <= CELLE_MAX, "Navigatore: area troppo grande");

        for(int i = 0; i < n; ++i)
        {
            _da[i] = -1;
        }

        int inizio = cella_x(e) + cella_y(e) * w;
        int testa = 0;
        int coda = 0;
        int arrivo = obiettivo < 0 && inizio == cx + cy * w ? inizio : -1;
        _coda[coda++] = int16_t(inizio);
        _da[inizio] = int16_t(inizio);

        while(testa < coda && arrivo < 0)
        {
            int i = _coda[testa++];
            int x = i % w;
            int y = i / w;
            const int passi[4][2] = { { 1, 0 }, { -1, 0 }, { 0, 1 }, { 0, -1 } };

            for(const auto& p : passi)
            {
                int nx = x + p[0];
                int ny = y + p[1];
                int c = cella(a, nx, ny);

                if(nx < 0 || ny < 0 || nx >= w || ny >= a.altezza || solida(c))
                {
                    continue;
                }

                int j = nx + ny * w;

                if(_da[j] >= 0 || (varco(c) && (obiettivo < 0 || c - PRIMO_VARCO != obiettivo)))
                {
                    continue;
                }

                _da[j] = int16_t(i);

                if((obiettivo >= 0 && c - PRIMO_VARCO == obiettivo) || (obiettivo < 0 && nx == cx && ny == cy))
                {
                    arrivo = j;
                    break;
                }

                _coda[coda++] = int16_t(j);
            }
        }

        if(arrivo < 0)
        {
            return false;
        }

        // Strada al contrario, poi raddrizzata.
        _lunghezza = 0;

        for(int i = arrivo; i != inizio; i = _da[i])
        {
            _strada[_lunghezza++] = int16_t(i);
        }

        for(int i = 0; i < _lunghezza / 2; ++i)
        {
            int16_t t = _strada[i];
            _strada[i] = _strada[_lunghezza - 1 - i];
            _strada[_lunghezza - 1 - i] = t;
        }

        _larghezza = w;
        _prossimo = 0;
        return true;
    }
};

// Il varco dell'area 'da' che porta all'area 'verso', o -1.
constexpr int varco_verso(AreaId da, AreaId verso)
{
    const Area& a = area(da);

    for(int k = 0; k < a.varchi; ++k)
    {
        if(varco_di(a, k).destinazione == int(verso))
        {
            return k;
        }
    }

    return -1;
}

}

#endif
