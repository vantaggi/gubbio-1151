#ifndef GUBBIO_TABELLA_H
#define GUBBIO_TABELLA_H

#include "bn_assert.h"

namespace gubbio
{

// Unico accesso alle tabelle generate: un indice fuori tabella e' un BN_ASSERT che dice quale
// tabella e quale indice, invece di una lettura silenziosa fuori dall'array. Vale anche a tempo
// di compilazione, dove BN_ASSERT ferma la compilazione.
template<typename Tipo, int Dimensione>
constexpr const Tipo& voce(const Tipo (&tabella)[Dimensione], int indice, const char* nome)
{
    BN_ASSERT(indice >= 0 && indice < Dimensione,
              "Tabella ", nome, ": indice ", indice, " fuori da 0..", Dimensione - 1);
    return tabella[indice];
}

}

#define GUBBIO_VOCE(tabella, indice) ::gubbio::voce(tabella, indice, #tabella)

#endif
