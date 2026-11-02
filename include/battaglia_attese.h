// GENERATO da tools/battaglia_mirror.py: le firme che il mirror Python trova per ogni
// incontro e ogni seme. src/autotest_battaglia.cpp le confronta con il C++ (include/battaglia.h).
// Non modificare a mano.
#ifndef GUBBIO_BATTAGLIA_ATTESE_H
#define GUBBIO_BATTAGLIA_ATTESE_H

#include "battaglia.h"

namespace gubbio::battaglia
{

struct Attesa
{
    int incontro;
    uint32_t seme;
    uint32_t hash;
    int eventi;
    int round;
    Esito esito;
    uint32_t tipi;
};

inline constexpr int ATTESE_CONTEGGIO = 100;
inline constexpr Attesa ATTESE[ATTESE_CONTEGGIO] = {
    { 0, 1, 0xEBCCAFA4u, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 2, 0x0E9994E8u, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 3, 0x221FF367u, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 4, 0xDF92E913u, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 5, 0x90514C3Fu, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 6, 0xD9CAA07Fu, 42, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 7, 0xD9828BB2u, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 8, 0x6FF1E3CFu, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 9, 0x0EDC43A3u, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 10, 0x3F516080u, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 11, 0x7D40E9DCu, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 12, 0x0BFC7CDDu, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 13, 0x60FDB2FEu, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 14, 0x802D4546u, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 15, 0x94537C71u, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 16, 0x5D8A2444u, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 17, 0x92A93A3Eu, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 18, 0xB70245F0u, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 19, 0x5622BD9Cu, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 20, 0x6096E559u, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 21, 0x2F1EA455u, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 22, 0xBA2D9AD0u, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 23, 0x341956AAu, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 24, 0xC21EBADCu, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 25, 0x8A7E1923u, 42, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 26, 0x45199BA5u, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 27, 0xBC310AA0u, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 28, 0x28899096u, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 29, 0x8F03C369u, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 30, 0x7C012E74u, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 31, 0x23A64D63u, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 32, 0x5DA12123u, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 33, 0x1A8A111Bu, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 34, 0x7B481177u, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 35, 0x6A0BF518u, 42, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 36, 0xAAA0E202u, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 37, 0xB7B276FCu, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 38, 0xA96162AAu, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 39, 0x250DCDA0u, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 40, 0x556CF988u, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 41, 0xB918CE57u, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 42, 0x9D075322u, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 43, 0x58BF0836u, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 44, 0xA8AFAE20u, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 45, 0x501F2DB9u, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 46, 0x574A37F6u, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 47, 0xB70CB769u, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 48, 0x2BA3B1BFu, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 49, 0xE5DCC969u, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 0, 50, 0x120D0FB9u, 40, 5, Esito::VITTORIA, 0x01FFu },
    { 1, 1, 0x957C6BD5u, 62, 8, Esito::VITTORIA, 0x0FFFu },
    { 1, 2, 0x5F572C60u, 63, 9, Esito::VITTORIA, 0x0FFFu },
    { 1, 3, 0x6C8279E8u, 62, 8, Esito::VITTORIA, 0x0FFFu },
    { 1, 4, 0x97410B80u, 62, 8, Esito::VITTORIA, 0x0FFFu },
    { 1, 5, 0x8ECDBFDEu, 63, 9, Esito::VITTORIA, 0x0FFFu },
    { 1, 6, 0x1F707C43u, 62, 8, Esito::VITTORIA, 0x0FFFu },
    { 1, 7, 0xDE69FF55u, 62, 8, Esito::VITTORIA, 0x0FFFu },
    { 1, 8, 0x7880EAFDu, 63, 9, Esito::VITTORIA, 0x0FFFu },
    { 1, 9, 0xD7FF916Du, 62, 8, Esito::VITTORIA, 0x0FFFu },
    { 1, 10, 0x75840844u, 62, 8, Esito::VITTORIA, 0x0FFFu },
    { 1, 11, 0x4C40669Cu, 63, 9, Esito::VITTORIA, 0x0FFFu },
    { 1, 12, 0x46D1226Bu, 62, 8, Esito::VITTORIA, 0x0FFFu },
    { 1, 13, 0xF4149C77u, 62, 8, Esito::VITTORIA, 0x0FFFu },
    { 1, 14, 0x16F502F6u, 62, 8, Esito::VITTORIA, 0x0FFFu },
    { 1, 15, 0x6C76929Bu, 62, 8, Esito::VITTORIA, 0x0FFFu },
    { 1, 16, 0x89E9EA68u, 63, 9, Esito::VITTORIA, 0x0FFFu },
    { 1, 17, 0x17462ED9u, 62, 8, Esito::VITTORIA, 0x0FFFu },
    { 1, 18, 0x29478757u, 62, 8, Esito::VITTORIA, 0x0FFFu },
    { 1, 19, 0x90F3D96Du, 63, 9, Esito::VITTORIA, 0x0FFFu },
    { 1, 20, 0xB122A551u, 62, 8, Esito::VITTORIA, 0x0FFFu },
    { 1, 21, 0x711FBF60u, 62, 8, Esito::VITTORIA, 0x0FFFu },
    { 1, 22, 0x19CF5E73u, 62, 8, Esito::VITTORIA, 0x0FFFu },
    { 1, 23, 0x8451E30Au, 62, 8, Esito::VITTORIA, 0x0FFFu },
    { 1, 24, 0x53A77D56u, 62, 8, Esito::VITTORIA, 0x0FFFu },
    { 1, 25, 0x5048CC5Du, 62, 8, Esito::VITTORIA, 0x0FFFu },
    { 1, 26, 0x3CA5A057u, 63, 9, Esito::VITTORIA, 0x0FFFu },
    { 1, 27, 0x65FD16D9u, 62, 8, Esito::VITTORIA, 0x0FFFu },
    { 1, 28, 0x4075B994u, 62, 8, Esito::VITTORIA, 0x0FFFu },
    { 1, 29, 0x5E17B9CCu, 62, 8, Esito::VITTORIA, 0x0FFFu },
    { 1, 30, 0x20CE1171u, 62, 8, Esito::VITTORIA, 0x0FFFu },
    { 1, 31, 0x31002303u, 62, 8, Esito::VITTORIA, 0x0FFFu },
    { 1, 32, 0x5AB4C8ADu, 62, 8, Esito::VITTORIA, 0x0FFFu },
    { 1, 33, 0xE29085C8u, 63, 9, Esito::VITTORIA, 0x0FFFu },
    { 1, 34, 0xBFCD46FEu, 63, 9, Esito::VITTORIA, 0x0FFFu },
    { 1, 35, 0x08B06DD3u, 62, 8, Esito::VITTORIA, 0x0FFFu },
    { 1, 36, 0x4ADE41A7u, 62, 8, Esito::VITTORIA, 0x0FFFu },
    { 1, 37, 0x17E9C2C6u, 62, 8, Esito::VITTORIA, 0x0FFFu },
    { 1, 38, 0x6ACAC3EAu, 63, 9, Esito::VITTORIA, 0x0FFFu },
    { 1, 39, 0x8239711Au, 63, 9, Esito::VITTORIA, 0x0FFFu },
    { 1, 40, 0x7BE2048Cu, 62, 8, Esito::VITTORIA, 0x0FFFu },
    { 1, 41, 0x6C59328Eu, 62, 8, Esito::VITTORIA, 0x0FFFu },
    { 1, 42, 0xD35E8664u, 62, 8, Esito::VITTORIA, 0x0FFFu },
    { 1, 43, 0x6D89309Bu, 62, 8, Esito::VITTORIA, 0x0FFFu },
    { 1, 44, 0xF793B8CFu, 62, 8, Esito::VITTORIA, 0x0FFFu },
    { 1, 45, 0xB3005383u, 62, 8, Esito::VITTORIA, 0x0FFFu },
    { 1, 46, 0xB7AB425Eu, 62, 8, Esito::VITTORIA, 0x0FFFu },
    { 1, 47, 0xC4C1F03Du, 62, 8, Esito::VITTORIA, 0x0FFFu },
    { 1, 48, 0x5B0A96B3u, 63, 9, Esito::VITTORIA, 0x0FFFu },
    { 1, 49, 0x3A2F9A01u, 62, 8, Esito::VITTORIA, 0x0FFFu },
    { 1, 50, 0x6CC49510u, 62, 8, Esito::VITTORIA, 0x0FFFu },
};

}

#endif
