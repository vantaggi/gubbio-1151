#ifndef GUBBIO_MONDO_AUTOTEST_H
#define GUBBIO_MONDO_AUTOTEST_H

#include "mondo_logica.h"

// Autotest del mondo: percorre l'anello camminando, nei due sensi, poi ogni altro arco del grafo
// nei due sensi e ogni ingresso, guidato dal Navigatore (strada cercata sulla griglia, non tasti
// a frame fissi). Fallisce al primo errore e su un arco mai attraversato. Prima della camminata
// controlla gli spawn d'arrivo: calpestabili, ad almeno DISTANZA_MIN_SPAWN tile da ogni varco e ad
// almeno DISTANZA_MIN_SPAWN_USCITA dalla propria uscita, quella da cui si e' entrati.
namespace gubbio::mondo
{

enum class ErroreMondo : int
{
    NESSUNO,
    SPAWN_NON_CALPESTABILE,    // uno spawn d'arrivo cade su una cella solida o su un varco
    SPAWN_VICINO_AL_VARCO,     // uno spawn d'arrivo e' a meno di DISTANZA_MIN_SPAWN tile da un varco
    VARCO_IRRAGGIUNGIBILE,     // nessuna strada sulla griglia porta al varco
    PASSO_BLOCCATO,            // la strada c'e' ma la collisione ferma il giocatore
    STRADA_SENZA_VARCO,        // la strada e' finita senza attraversare il varco
    VARCO_SBAGLIATO,           // si e' attraversato un altro varco
    ARRIVO_SBAGLIATO,          // dopo il varco non si e' nell'area attesa
    AREA_IRRAGGIUNGIBILE,      // nessuna catena di archi porta all'area
    ARCO_NON_PERCORSO,         // a fine giro un arco non e' mai stato attraversato
    SPAWN_VICINO_ALLA_USCITA,  // uno spawn d'arrivo e' a meno di DISTANZA_MIN_SPAWN_USCITA tile dalla
                               // propria uscita
};

struct EsitoMondo
{
    int pixel = 0;             // pixel camminati
    int attraversamenti = 0;   // varchi attraversati, ingressi compresi
    int archi = 0;             // archi diversi attraversati
    ErroreMondo errore = ErroreMondo::NESSUNO;
    int area = -1;
    int varco = -1;
};

// L'osservatore riceve (esploratore, evento) dopo ogni pixel camminato: a tempo di compilazione
// non fa nulla, sul GBA ridisegna la scena e misura i picchi di memoria video.
struct NessunOsservatore
{
    constexpr void operator()(const Esploratore&, Evento) const
    {
    }

    // Il navigatore ha appena cercato una strada: lavoro dell'autotest, non del gioco.
    constexpr void strada_pronta() const
    {
    }
};

template<typename Osservatore>
class AutotestMondo
{

public:
    constexpr EsitoMondo esegui(Osservatore& osservatore)
    {
        _osservatore = &osservatore;

        if(! _controlla_spawn())
        {
            return _esito;
        }

        colloca(_e, GUBBIO_VOCE(ANELLO, 0), 0);

        // L'anello nei due sensi.
        for(int i = 0; i < ANELLO_CONTEGGIO; ++i)
        {
            if(! _verso(GUBBIO_VOCE(ANELLO, (i + 1) % ANELLO_CONTEGGIO)))
            {
                return _esito;
            }
        }

        for(int i = ANELLO_CONTEGGIO; i > 0; --i)
        {
            if(! _verso(GUBBIO_VOCE(ANELLO, (i - 1) % ANELLO_CONTEGGIO)))
            {
                return _esito;
            }
        }

        // Ogni arco ancora mai percorso, raggiungendo prima la sua area.
        for(int a = 0; a < AREE_CONTEGGIO; ++a)
        {
            for(int k = 0; k < area(AreaId(a)).varchi; ++k)
            {
                if(_percorso[a][k])
                {
                    continue;
                }

                if(! _raggiungi(AreaId(a)) || ! _attraversa(k))
                {
                    return _esito;
                }
            }
        }

        for(int a = 0; a < AREE_CONTEGGIO; ++a)
        {
            for(int k = 0; k < area(AreaId(a)).varchi; ++k)
            {
                if(! _percorso[a][k])
                {
                    _fallisci(ErroreMondo::ARCO_NON_PERCORSO, a, k);
                    return _esito;
                }

                ++_esito.archi;
            }
        }

        return _esito;
    }

private:
    Osservatore* _osservatore = nullptr;
    Esploratore _e;
    Navigatore _n;
    EsitoMondo _esito;
    bool _percorso[AREE_CONTEGGIO][VARCHI_MAX] = {};

    constexpr bool _fallisci(ErroreMondo errore, int a, int k)
    {
        _esito.errore = errore;
        _esito.area = a;
        _esito.varco = k;
        return false;
    }

    constexpr bool _controlla_spawn()
    {
        for(int a = 0; a < AREE_CONTEGGIO; ++a)
        {
            const Area& da = area(AreaId(a));

            for(int k = 0; k < da.varchi; ++k)
            {
                const Varco& v = varco_di(da, k);

                if(v.destinazione == DUNGEON)
                {
                    continue;
                }

                const Area& arrivo = area(AreaId(v.destinazione));
                const Punto& p = spawn_di(arrivo, v.spawn);
                int c = cella(arrivo, p.x, p.y);

                if(solida(c) || varco(c))
                {
                    return _fallisci(ErroreMondo::SPAWN_NON_CALPESTABILE, v.destinazione, v.spawn);
                }

                for(int y = 0; y < arrivo.altezza; ++y)
                {
                    for(int x = 0; x < arrivo.larghezza; ++x)
                    {
                        int dx = x > p.x ? x - p.x : p.x - x;
                        int dy = y > p.y ? y - p.y : p.y - y;

                        if(varco(cella(arrivo, x, y)) && dx < DISTANZA_MIN_SPAWN && dy < DISTANZA_MIN_SPAWN)
                        {
                            return _fallisci(ErroreMondo::SPAWN_VICINO_AL_VARCO, v.destinazione, v.spawn);
                        }
                    }
                }

                // La propria uscita: il varco dell'area d'arrivo che riporta qui.
                int ritorno = -1;

                for(int j = 0; j < arrivo.varchi; ++j)
                {
                    if(varco_di(arrivo, j).destinazione == a)
                    {
                        ritorno = j;
                    }
                }

                for(int y = 0; y < arrivo.altezza; ++y)
                {
                    for(int x = 0; x < arrivo.larghezza; ++x)
                    {
                        int dx = x > p.x ? x - p.x : p.x - x;
                        int dy = y > p.y ? y - p.y : p.y - y;

                        if(cella(arrivo, x, y) == PRIMO_VARCO + ritorno && dx < DISTANZA_MIN_SPAWN_USCITA &&
                           dy < DISTANZA_MIN_SPAWN_USCITA)
                        {
                            return _fallisci(ErroreMondo::SPAWN_VICINO_ALLA_USCITA, v.destinazione, v.spawn);
                        }
                    }
                }
            }
        }

        return true;
    }

    // Cammina fino al varco k dell'area corrente e lo attraversa.
    constexpr bool _attraversa(int k)
    {
        int a = int(_e.area);
        const Varco& v = varco_di(area(_e.area), k);

        if(! _n.prepara(_e, k))
        {
            return _fallisci(ErroreMondo::VARCO_IRRAGGIUNGIBILE, a, k);
        }

        _osservatore->strada_pronta();

        while(true)
        {
            Evento evento = Evento::NESSUNO;

            if(! _n.passo(_e, evento))
            {
                return _fallisci(_n.lunghezza() ? ErroreMondo::PASSO_BLOCCATO : ErroreMondo::STRADA_SENZA_VARCO, a, k);
            }

            ++_esito.pixel;
            (*_osservatore)(_e, evento);

            if(evento == Evento::NESSUNO)
            {
                continue;
            }

            ++_esito.attraversamenti;

            if(_e.ultimo_varco != k)
            {
                return _fallisci(ErroreMondo::VARCO_SBAGLIATO, a, _e.ultimo_varco);
            }

            _percorso[a][k] = true;

            if(v.destinazione == DUNGEON)
            {
                return evento == Evento::INGRESSO_DUNGEON || _fallisci(ErroreMondo::VARCO_SBAGLIATO, a, k);
            }

            if(evento != Evento::CAMBIO_AREA || int(_e.area) != v.destinazione)
            {
                return _fallisci(ErroreMondo::ARRIVO_SBAGLIATO, a, k);
            }

            return true;
        }
    }

    constexpr bool _verso(AreaId destinazione)
    {
        int k = varco_verso(_e.area, destinazione);
        return k >= 0 ? _attraversa(k) : _fallisci(ErroreMondo::AREA_IRRAGGIUNGIBILE, int(_e.area), -1);
    }

    // Raggiunge l'area 'meta' attraversando archi (ricerca in ampiezza sul grafo delle aree).
    constexpr bool _raggiungi(AreaId meta)
    {
        while(_e.area != meta)
        {
            int da[AREE_CONTEGGIO] = {};
            int coda[AREE_CONTEGGIO] = {};
            int testa = 0;
            int fine = 0;

            for(int& d : da)
            {
                d = -1;
            }

            da[int(_e.area)] = int(_e.area);
            coda[fine++] = int(_e.area);

            while(testa < fine)
            {
                int a = coda[testa++];

                for(int k = 0; k < area(AreaId(a)).varchi; ++k)
                {
                    int b = varco_di(area(AreaId(a)), k).destinazione;

                    if(b != DUNGEON && da[b] < 0)
                    {
                        da[b] = a;
                        coda[fine++] = b;
                    }
                }
            }

            if(da[int(meta)] < 0)
            {
                return _fallisci(ErroreMondo::AREA_IRRAGGIUNGIBILE, int(meta), -1);
            }

            int passo = int(meta);

            while(da[passo] != int(_e.area))
            {
                passo = da[passo];
            }

            if(! _verso(AreaId(passo)))
            {
                return false;
            }
        }

        return true;
    }
};

constexpr EsitoMondo autotest_mondo()
{
    NessunOsservatore osservatore;
    AutotestMondo<NessunOsservatore> autotest;
    return autotest.esegui(osservatore);
}

}

#endif
