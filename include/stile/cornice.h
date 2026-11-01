// GENERATO da stile/esporta_cpp.py a partire da stile/dati/cornice.json. Non modificare a mano.
#ifndef GUBBIO_STILE_CORNICE_H
#define GUBBIO_STILE_CORNICE_H

#include <cstdint>

namespace gubbio::stile
{

// Scelta 9: cornice a vetrata, tile 8x8 a 4bpp nel formato della VRAM.
// Si compone a 9-slice (angoli con flip, lati a tessere alternate, centro pieno).

inline constexpr uint16_t CORNICE_PALETTE[16] = {
    0x0000, 0x1085, 0x7BBD, 0x18D4, 0x26B8, 0x520A, 0x368F, 0x6670,
    0x148D, 0x4FBD, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000,
};

inline constexpr int TILE_ANGOLO = 0;
inline constexpr int TILE_ORIZ_0 = 1;
inline constexpr int TILE_ORIZ_1 = 2;
inline constexpr int TILE_ORIZ_2 = 3;
inline constexpr int TILE_VERT_0 = 4;
inline constexpr int TILE_VERT_1 = 5;
inline constexpr int TILE_VERT_2 = 6;
inline constexpr int TILE_CENTRO = 7;
inline constexpr int TILE_CARTIGLIO_SX = 8;
inline constexpr int TILE_CARTIGLIO_CENTRO = 9;
inline constexpr int TILE_CURSORE = 10;
inline constexpr int TILE_CORNICE = 11;

inline constexpr uint32_t CORNICE_TILE[TILE_CORNICE * 8] = {
    // angolo
    0x11111111, 0x11999911, 0x19999991, 0x19933991, 0x19933991, 0x19999991, 0x11999911, 0x11111111,
    // oriz_0
    0x11111111, 0x13333333, 0x13333323, 0x13333333, 0x13333333, 0x13333333, 0x13333333, 0x11111111,
    // oriz_1
    0x11111111, 0x14444444, 0x14444424, 0x14444444, 0x14444444, 0x14444444, 0x14444444, 0x11111111,
    // oriz_2
    0x11111111, 0x15555555, 0x15555525, 0x15555555, 0x15555555, 0x15555555, 0x15555555, 0x11111111,
    // vert_0
    0x16666661, 0x16666261, 0x16666661, 0x16666661, 0x16666661, 0x16666661, 0x16666661, 0x11111111,
    // vert_1
    0x17777771, 0x17777271, 0x17777771, 0x17777771, 0x17777771, 0x17777771, 0x17777771, 0x11111111,
    // vert_2
    0x18888881, 0x18888281, 0x18888881, 0x18888881, 0x18888881, 0x18888881, 0x18888881, 0x11111111,
    // centro
    0x22222222, 0x22222222, 0x22222222, 0x22222222, 0x22222222, 0x22222222, 0x22222222, 0x22222222,
    // cartiglio_sx
    0x11111111, 0x33333331, 0x33333331, 0x33333331, 0x33333331, 0x33333331, 0x33333331, 0x33333331,
    // cartiglio_centro
    0x11111111, 0x33333333, 0x33333333, 0x33333333, 0x33333333, 0x33333333, 0x33333333, 0x33333333,
    // cursore
    0x00000000, 0x00000011, 0x00000131, 0x00001331, 0x00013331, 0x00001331, 0x00000131, 0x00000011,
};

inline constexpr int LATO_ORIZZONTALE[3] = { TILE_ORIZ_0, TILE_ORIZ_1, TILE_ORIZ_2 };
inline constexpr int LATO_VERTICALE[3] = { TILE_VERT_0, TILE_VERT_1, TILE_VERT_2 };

inline constexpr int DIALOGO_X = 0;
inline constexpr int DIALOGO_Y = 104;
inline constexpr int DIALOGO_COLONNE = 30;
inline constexpr int DIALOGO_RIGHE = 7;
inline constexpr int DIALOGO_RIGHE_TESTO_MAX = 3;
inline constexpr int CARTIGLIO_NOME_X = 8;
inline constexpr int CARTIGLIO_NOME_Y = 96;
inline constexpr int CARTIGLIO_NOME_RIGHE = 2;
inline constexpr int MENU_X = 168;
inline constexpr int MENU_Y = 8;
inline constexpr int MENU_COLONNE = 8;
inline constexpr int MENU_RIGHE = 6;
inline constexpr int MENU_PASSO_VOCI = 10;
inline constexpr int MENU_VOCI_MAX = 3;

}

#endif
