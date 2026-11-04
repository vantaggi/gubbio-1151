// GENERATO da tools/genera_cartelli.py da mondo/grafo.json: non modificare a mano.
#ifndef GUBBIO_CARTELLI_H
#define GUBBIO_CARTELLI_H

#include <cstdint>

#include "mondo.h"
#include "testi.h"

namespace gubbio::cartelli
{

// Il cartello del varco dall'area 'da' all'area 'verso' (mondo::AreaId): la seconda riga, sotto il nome
// della destinazione. Lo legge aiuti::cartello().
struct Cartello
{
    int8_t da;
    int8_t verso;
    testi::TestoId oltre;
};

inline constexpr int CARTELLI = 50;
inline constexpr Cartello CARTELLO[CARTELLI] = {
    { int8_t(mondo::AreaId::PIAZZA_GRANDE), int8_t(mondo::AreaId::VIA_DEI_CONSOLI), testi::TestoId::CARTELLO_PIAZZA_GRANDE_VIA_DEI_CONSOLI },
    { int8_t(mondo::AreaId::PIAZZA_GRANDE), int8_t(mondo::AreaId::VIA_XX_SETTEMBRE), testi::TestoId::CARTELLO_PIAZZA_GRANDE_VIA_XX_SETTEMBRE },
    { int8_t(mondo::AreaId::VIA_DEI_CONSOLI), int8_t(mondo::AreaId::PIAZZA_GRANDE), testi::TestoId::CARTELLO_VIA_DEI_CONSOLI_PIAZZA_GRANDE },
    { int8_t(mondo::AreaId::VIA_DEI_CONSOLI), int8_t(mondo::AreaId::LARGO_BARGELLO), testi::TestoId::CARTELLO_VIA_DEI_CONSOLI_LARGO_BARGELLO },
    { int8_t(mondo::AreaId::VIA_DEI_CONSOLI), int8_t(mondo::AreaId::PIAZZA_QUARANTA_MARTIRI), testi::TestoId::CARTELLO_VIA_DEI_CONSOLI_PIAZZA_QUARANTA_MARTIRI },
    { int8_t(mondo::AreaId::LARGO_BARGELLO), int8_t(mondo::AreaId::VIA_DEI_CONSOLI), testi::TestoId::CARTELLO_LARGO_BARGELLO_VIA_DEI_CONSOLI },
    { int8_t(mondo::AreaId::LARGO_BARGELLO), int8_t(mondo::AreaId::SAN_MARTINO), testi::TestoId::CARTELLO_LARGO_BARGELLO_SAN_MARTINO },
    { int8_t(mondo::AreaId::LARGO_BARGELLO), int8_t(mondo::AreaId::DUOMO_DUCALE), testi::TestoId::CARTELLO_LARGO_BARGELLO_DUOMO_DUCALE },
    { int8_t(mondo::AreaId::SAN_MARTINO), int8_t(mondo::AreaId::LARGO_BARGELLO), testi::TestoId::CARTELLO_SAN_MARTINO_LARGO_BARGELLO },
    { int8_t(mondo::AreaId::SAN_MARTINO), int8_t(mondo::AreaId::BOTTACCIONE), testi::TestoId::CARTELLO_SAN_MARTINO_BOTTACCIONE },
    { int8_t(mondo::AreaId::SAN_MARTINO), int8_t(mondo::AreaId::PIAZZA_QUARANTA_MARTIRI), testi::TestoId::CARTELLO_SAN_MARTINO_PIAZZA_QUARANTA_MARTIRI },
    { int8_t(mondo::AreaId::SAN_MARTINO), int8_t(mondo::AreaId::TEATRO_ROMANO), testi::TestoId::CARTELLO_SAN_MARTINO_TEATRO_ROMANO },
    { int8_t(mondo::AreaId::TEATRO_ROMANO), int8_t(mondo::AreaId::SAN_MARTINO), testi::TestoId::CARTELLO_TEATRO_ROMANO_SAN_MARTINO },
    { int8_t(mondo::AreaId::TEATRO_ROMANO), int8_t(mondo::AreaId::PIAZZA_QUARANTA_MARTIRI), testi::TestoId::CARTELLO_TEATRO_ROMANO_PIAZZA_QUARANTA_MARTIRI },
    { int8_t(mondo::AreaId::PIAZZA_QUARANTA_MARTIRI), int8_t(mondo::AreaId::SAN_MARTINO), testi::TestoId::CARTELLO_PIAZZA_QUARANTA_MARTIRI_SAN_MARTINO },
    { int8_t(mondo::AreaId::PIAZZA_QUARANTA_MARTIRI), int8_t(mondo::AreaId::TEATRO_ROMANO), testi::TestoId::CARTELLO_PIAZZA_QUARANTA_MARTIRI_TEATRO_ROMANO },
    { int8_t(mondo::AreaId::PIAZZA_QUARANTA_MARTIRI), int8_t(mondo::AreaId::VIA_DEI_CONSOLI), testi::TestoId::CARTELLO_PIAZZA_QUARANTA_MARTIRI_VIA_DEI_CONSOLI },
    { int8_t(mondo::AreaId::PIAZZA_QUARANTA_MARTIRI), int8_t(mondo::AreaId::VIA_XX_SETTEMBRE), testi::TestoId::CARTELLO_PIAZZA_QUARANTA_MARTIRI_VIA_XX_SETTEMBRE },
    { int8_t(mondo::AreaId::PIAZZA_QUARANTA_MARTIRI), int8_t(mondo::AreaId::SAN_PIETRO), testi::TestoId::CARTELLO_PIAZZA_QUARANTA_MARTIRI_SAN_PIETRO },
    { int8_t(mondo::AreaId::SAN_PIETRO), int8_t(mondo::AreaId::PIAZZA_QUARANTA_MARTIRI), testi::TestoId::CARTELLO_SAN_PIETRO_PIAZZA_QUARANTA_MARTIRI },
    { int8_t(mondo::AreaId::SAN_PIETRO), int8_t(mondo::AreaId::SANT_AGOSTINO), testi::TestoId::CARTELLO_SAN_PIETRO_SANT_AGOSTINO },
    { int8_t(mondo::AreaId::VIA_XX_SETTEMBRE), int8_t(mondo::AreaId::PIAZZA_QUARANTA_MARTIRI), testi::TestoId::CARTELLO_VIA_XX_SETTEMBRE_PIAZZA_QUARANTA_MARTIRI },
    { int8_t(mondo::AreaId::VIA_XX_SETTEMBRE), int8_t(mondo::AreaId::PIAZZA_GRANDE), testi::TestoId::CARTELLO_VIA_XX_SETTEMBRE_PIAZZA_GRANDE },
    { int8_t(mondo::AreaId::VIA_XX_SETTEMBRE), int8_t(mondo::AreaId::SANT_ANDREA), testi::TestoId::CARTELLO_VIA_XX_SETTEMBRE_SANT_ANDREA },
    { int8_t(mondo::AreaId::VIA_XX_SETTEMBRE), int8_t(mondo::AreaId::DUOMO_DUCALE), testi::TestoId::CARTELLO_VIA_XX_SETTEMBRE_DUOMO_DUCALE },
    { int8_t(mondo::AreaId::SANT_AGOSTINO), int8_t(mondo::AreaId::SANT_ANDREA), testi::TestoId::CARTELLO_SANT_AGOSTINO_SANT_ANDREA },
    { int8_t(mondo::AreaId::SANT_AGOSTINO), int8_t(mondo::AreaId::SAN_PIETRO), testi::TestoId::CARTELLO_SANT_AGOSTINO_SAN_PIETRO },
    { int8_t(mondo::AreaId::SANT_ANDREA), int8_t(mondo::AreaId::VIA_XX_SETTEMBRE), testi::TestoId::CARTELLO_SANT_ANDREA_VIA_XX_SETTEMBRE },
    { int8_t(mondo::AreaId::SANT_ANDREA), int8_t(mondo::AreaId::SANT_AGOSTINO), testi::TestoId::CARTELLO_SANT_ANDREA_SANT_AGOSTINO },
    { int8_t(mondo::AreaId::SANT_ANDREA), int8_t(mondo::AreaId::MONTE_INGINO), testi::TestoId::CARTELLO_SANT_ANDREA_MONTE_INGINO },
    { int8_t(mondo::AreaId::DUOMO_DUCALE), int8_t(mondo::AreaId::VIA_XX_SETTEMBRE), testi::TestoId::CARTELLO_DUOMO_DUCALE_VIA_XX_SETTEMBRE },
    { int8_t(mondo::AreaId::DUOMO_DUCALE), int8_t(mondo::AreaId::MONTE_INGINO), testi::TestoId::CARTELLO_DUOMO_DUCALE_MONTE_INGINO },
    { int8_t(mondo::AreaId::DUOMO_DUCALE), int8_t(mondo::AreaId::LARGO_BARGELLO), testi::TestoId::CARTELLO_DUOMO_DUCALE_LARGO_BARGELLO },
    { int8_t(mondo::AreaId::MONTE_INGINO), int8_t(mondo::AreaId::DUOMO_DUCALE), testi::TestoId::CARTELLO_MONTE_INGINO_DUOMO_DUCALE },
    { int8_t(mondo::AreaId::MONTE_INGINO), int8_t(mondo::AreaId::SANT_ANDREA), testi::TestoId::CARTELLO_MONTE_INGINO_SANT_ANDREA },
    { int8_t(mondo::AreaId::MONTE_INGINO), int8_t(mondo::AreaId::BASILICA), testi::TestoId::CARTELLO_MONTE_INGINO_BASILICA },
    { int8_t(mondo::AreaId::BASILICA), int8_t(mondo::AreaId::MONTE_INGINO), testi::TestoId::CARTELLO_BASILICA_MONTE_INGINO },
    { int8_t(mondo::AreaId::BASILICA), int8_t(mondo::AreaId::BOTTACCIONE), testi::TestoId::CARTELLO_BASILICA_BOTTACCIONE },
    { int8_t(mondo::AreaId::BASILICA), int8_t(mondo::AreaId::BASILICA_INTERNO), testi::TestoId::CARTELLO_BASILICA_BASILICA_INTERNO },
    { int8_t(mondo::AreaId::BASILICA_INTERNO), int8_t(mondo::AreaId::BASILICA), testi::TestoId::CARTELLO_BASILICA_INTERNO_BASILICA },
    { int8_t(mondo::AreaId::BOTTACCIONE), int8_t(mondo::AreaId::SAN_MARTINO), testi::TestoId::CARTELLO_BOTTACCIONE_SAN_MARTINO },
    { int8_t(mondo::AreaId::BOTTACCIONE), int8_t(mondo::AreaId::BASILICA), testi::TestoId::CARTELLO_BOTTACCIONE_BASILICA },
    { int8_t(mondo::AreaId::BOTTACCIONE), int8_t(mondo::AreaId::GOLA_STRISCIA), testi::TestoId::CARTELLO_BOTTACCIONE_GOLA_STRISCIA },
    { int8_t(mondo::AreaId::GOLA_STRISCIA), int8_t(mondo::AreaId::BOTTACCIONE), testi::TestoId::CARTELLO_GOLA_STRISCIA_BOTTACCIONE },
    { int8_t(mondo::AreaId::GOLA_STRISCIA), int8_t(mondo::AreaId::GOLA_MIASMI), testi::TestoId::CARTELLO_GOLA_STRISCIA_GOLA_MIASMI },
    { int8_t(mondo::AreaId::GOLA_MIASMI), int8_t(mondo::AreaId::GOLA_STRISCIA), testi::TestoId::CARTELLO_GOLA_MIASMI_GOLA_STRISCIA },
    { int8_t(mondo::AreaId::GOLA_MIASMI), int8_t(mondo::AreaId::GOLA_ARCO), testi::TestoId::CARTELLO_GOLA_MIASMI_GOLA_ARCO },
    { int8_t(mondo::AreaId::GOLA_ARCO), int8_t(mondo::AreaId::GOLA_MIASMI), testi::TestoId::CARTELLO_GOLA_ARCO_GOLA_MIASMI },
    { int8_t(mondo::AreaId::GOLA_ARCO), int8_t(mondo::AreaId::CONDOTTO), testi::TestoId::CARTELLO_GOLA_ARCO_CONDOTTO },
    { int8_t(mondo::AreaId::CONDOTTO), int8_t(mondo::AreaId::GOLA_ARCO), testi::TestoId::CARTELLO_CONDOTTO_GOLA_ARCO },
};

}

#endif
