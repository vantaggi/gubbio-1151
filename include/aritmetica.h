#ifndef GUBBIO_ARITMETICA_H
#define GUBBIO_ARITMETICA_H

#include "bn_assert.h"

// Divisioni senza divisione (docs/regole_sviluppo_gba.md, punto 3). L'ARM7TDMI non ha l'istruzione di
// divisione e in Thumb non ha la moltiplicazione a 64 bit: gcc chiama __aeabi_idiv (decine di cicli) anche
// per un divisore costante come 30. Per un dividendo che si sa piccolo, 0 <= x < MAX, basta moltiplicare per
// il reciproco precalcolato e spostare: dividi<30, 64>(x) == x / 30, verificato a tempo di compilazione per
// ogni x dell'intervallo. Il gate tools/controlla_divisioni.py controlla sulla ROM che il ciclo
// dell'esplorazione non chiami piu' la divisione software.
namespace gubbio
{

namespace aritmetica_dettaglio
{
    struct Reciproco
    {
        int moltiplica;
        int sposta;
    };

    // il primo spostamento s per cui (x * ceil(2^s / D)) >> s == x / D per ogni x in [0, MAX), senza che il
    // prodotto esca dai 31 bit
    consteval Reciproco reciproco(int d, int max)
    {
        for(int s = 0; s < 31; ++s)
        {
            long long m = ((1LL << s) + d - 1) / d;

            if(m * (max - 1) >= (1LL << 31))
            {
                break;
            }

            bool esatto = true;

            for(long long x = 0; x < max && esatto; ++x)
            {
                esatto = ((x * m) >> s) == x / d;
            }

            if(esatto)
            {
                return { int(m), s };
            }
        }

        return { 0, -1 };
    }
}

// x / D per 0 <= x < MAX, con una moltiplicazione e uno spostamento.
template<int D, int MAX = 1 << 15>
[[nodiscard]] constexpr int dividi(int x)
{
    static_assert(D > 0 && MAX > 0, "divisore e intervallo positivi");
    constexpr aritmetica_dettaglio::Reciproco r = aritmetica_dettaglio::reciproco(D, MAX);
    static_assert(r.sposta >= 0, "nessun reciproco esatto su tutto l'intervallo: ridurre MAX");
    BN_ASSERT(x >= 0 && x < MAX, "dividi: fuori intervallo ", x);
    return (x * r.moltiplica) >> r.sposta;
}

// x % D per 0 <= x < MAX.
template<int D, int MAX = 1 << 15>
[[nodiscard]] constexpr int resto(int x)
{
    return x - dividi<D, MAX>(x) * D;
}

// L'indice di un anello di n posti per i che sta in [-n, 2n): (i + n) % n senza modulo.
[[nodiscard]] constexpr int giro(int i, int n)
{
    BN_ASSERT(i >= -n && i < 2 * n, "giro: fuori intervallo ", i);
    return i < 0 ? i + n : (i >= n ? i - n : i);
}

// Un contatore che va da 0 a n - 1 e ricomincia: (c + 1) % n senza modulo.
[[nodiscard]] constexpr int avanti(int c, int n)
{
    return c + 1 >= n ? 0 : c + 1;
}

}

#endif
