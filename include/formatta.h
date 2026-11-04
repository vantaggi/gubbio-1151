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

// Il tempo di gioco come "h:mm" (MAI: titolo e «Dove eravamo»): le ore senza zeri davanti, fino a 99 (oltre
// resta 99:59), i minuti sempre a due cifre. Ritorna i caratteri scritti (al massimo 5).
inline constexpr int TEMPO_CARATTERI_MAX = 5;      // "99:59"

constexpr int formatta_tempo(int secondi, char (&testo)[TEMPO_CARATTERI_MAX + 1])
{
    int minuti_totali = secondi < 0 ? 0 : secondi / 60;
    int ore = minuti_totali / 60;
    int minuti = minuti_totali % 60;

    if(ore > 99)
    {
        ore = 99;
        minuti = 59;
    }

    int n = 0;

    if(ore >= 10)
    {
        testo[n++] = char('0' + ore / 10);
    }

    testo[n++] = char('0' + ore % 10);
    testo[n++] = ':';
    testo[n++] = char('0' + minuti / 10);
    testo[n++] = char('0' + minuti % 10);
    testo[n] = '\0';
    return n;
}

// I livelli dei tre Santi come "4 4 3" (MAI: l'anteprima degli slot). Livelli da 1 a 9.
inline constexpr int LIVELLI_CARATTERI = 5;

constexpr int formatta_livelli(int a, int b, int c, char (&testo)[LIVELLI_CARATTERI + 1])
{
    const int livelli[3] = { a, b, c };

    for(int i = 0; i < 3; ++i)
    {
        int l = livelli[i] < 1 ? 1 : (livelli[i] > 9 ? 9 : livelli[i]);
        testo[2 * i] = char('0' + l);

        if(i < 2)
        {
            testo[2 * i + 1] = ' ';
        }
    }

    testo[LIVELLI_CARATTERI] = '\0';
    return LIVELLI_CARATTERI;
}

// Prova su ogni minuto fino a 100 ore e oltre: formatta, rilegge ore e minuti e confronta. Ritorna i valori
// controllati, oppure -1 - minuto al primo errore.
constexpr int autotest_formatta_tempo()
{
    int controllati = 0;

    for(int m = 0; m <= 101 * 60; ++m)
    {
        char testo[TEMPO_CARATTERI_MAX + 1] = {};
        int n = formatta_tempo(m * 60 + 59, testo);     // i secondi oltre il minuto non contano

        if(n < 4 || n > TEMPO_CARATTERI_MAX || testo[n] != '\0' || testo[n - 3] != ':')
        {
            return -1 - m;
        }

        int ore = 0;

        for(int i = 0; i < n - 3; ++i)
        {
            ore = ore * 10 + (testo[i] - '0');
        }

        int minuti = (testo[n - 2] - '0') * 10 + (testo[n - 1] - '0');
        int atteso_ore = m / 60 > 99 ? 99 : m / 60;
        int attesi_minuti = m / 60 > 99 ? 59 : m % 60;

        if(ore != atteso_ore || minuti != attesi_minuti || (n == 5 && testo[0] == '0'))
        {
            return -1 - m;
        }

        ++controllati;
    }

    return controllati;
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
