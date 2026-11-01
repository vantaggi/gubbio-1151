#ifndef GUBBIO_FORMATTA_H
#define GUBBIO_FORMATTA_H

#include "bn_assert.h"

namespace gubbio
{

// Unico formattatore numerico del gioco: interi a 16 bit con segno, in cifre ASCII. Niente
// bn::to_string sparsi: un numero a schermo passa sempre da qui.
inline constexpr int FORMATTA_CARATTERI_MAX = 6;   // "-32768"

constexpr int formatta_intero(int valore, char (&testo)[FORMATTA_CARATTERI_MAX + 1])
{
    BN_ASSERT(valore >= -32768 && valore <= 32767, "formatta_intero: ", valore, " fuori da int16");

    int n = 0;
    unsigned resto = valore < 0 ? unsigned(-valore) : unsigned(valore);

    if(valore < 0)
    {
        testo[n++] = '-';
    }

    char cifre[5] = {};
    int quante = 0;

    do
    {
        cifre[quante++] = char('0' + (resto % 10));
        resto /= 10;
    }
    while(resto);

    while(quante)
    {
        testo[n++] = cifre[--quante];
    }

    testo[n] = '\0';
    return n;
}

// Prova esaustiva su tutto int16: formatta, rilegge e confronta. Ritorna i valori controllati
// (65536) oppure -1 - valore al primo errore.
constexpr int autotest_formatta()
{
    int controllati = 0;

    for(int v = -32768; v <= 32767; ++v)
    {
        char testo[FORMATTA_CARATTERI_MAX + 1] = {};
        int n = formatta_intero(v, testo);
        int i = 0;
        bool negativo = false;

        if(n < 1 || n > FORMATTA_CARATTERI_MAX || testo[n] != '\0')
        {
            return -1 - v;
        }

        if(testo[0] == '-')
        {
            negativo = true;
            i = 1;
        }

        if(i == n || (testo[i] == '0' && n - i > 1) || (negativo && v >= 0))
        {
            return -1 - v;
        }

        int riletto = 0;

        for(; i < n; ++i)
        {
            if(testo[i] < '0' || testo[i] > '9')
            {
                return -1 - v;
            }

            riletto = riletto * 10 + (testo[i] - '0');
        }

        if((negativo ? -riletto : riletto) != v)
        {
            return -1 - v;
        }

        ++controllati;
    }

    return controllati;
}

}

#endif
