// GENERATO da stile/esporta_cpp.py a partire da stile/dati/palette.json. Non modificare a mano.
#ifndef GUBBIO_STILE_PALETTE_H
#define GUBBIO_STILE_PALETTE_H

#include <cstdint>

namespace gubbio::stile
{

// Scelta 3: palette maestra in BGR555. Toni dal piu' scuro al piu' chiaro.
// PALETTE_NOTTE ha gli stessi indici: notte e Bottaccione sono un cambio di palette.

inline constexpr int RAMPA_PIETRA_CALCAREA = 0;   // 6 toni
inline constexpr int RAMPA_COTTO_E_COPPI = 6;   // 6 toni
inline constexpr int RAMPA_VERMIGLIO_COMUNALE = 12;   // 4 toni
inline constexpr int RAMPA_VERDE_DEI_MONTI = 16;   // 5 toni
inline constexpr int RAMPA_CIELO_E_ACQUA = 21;   // 5 toni
inline constexpr int RAMPA_LEGNO_E_CUOIO = 26;   // 4 toni
inline constexpr int RAMPA_ORO_E_BRONZO = 30;   // 4 toni
inline constexpr int RAMPA_PELLE = 34;   // 3 toni
inline constexpr int RAMPA_NEUTRI = 37;   // 5 toni
inline constexpr int COLORI_PALETTE = 42;

inline constexpr uint16_t PALETTE_GIORNO[COLORI_PALETTE] = {
    0x2109, 0x2D8D, 0x35F1, 0x4295, 0x5739, 0x6BBD, 0x14A7, 0x18CB,
    0x1D0F, 0x2593, 0x3657, 0x533B, 0x1487, 0x148D, 0x18D4, 0x425A,
    0x14C6, 0x1D69, 0x25EB, 0x368F, 0x5334, 0x2D68, 0x3DCA, 0x520A,
    0x6670, 0x7717, 0x1085, 0x190A, 0x218F, 0x3E74, 0x214C, 0x1DD2,
    0x26B8, 0x4FBD, 0x39F1, 0x3A37, 0x5F5C, 0x0842, 0x2529, 0x41EF,
    0x5ED6, 0x7BBD,
};

inline constexpr uint16_t PALETTE_NOTTE[COLORI_PALETTE] = {
    0x20A5, 0x28E7, 0x3128, 0x356A, 0x3DCD, 0x4250, 0x1C84, 0x20A5,
    0x24C7, 0x2909, 0x314B, 0x35CE, 0x1C84, 0x1C86, 0x24C9, 0x314D,
    0x1C84, 0x20C5, 0x2506, 0x3148, 0x39C9, 0x28C5, 0x3106, 0x3926,
    0x4948, 0x6168, 0x1883, 0x20A5, 0x24E7, 0x3549, 0x24C6, 0x2508,
    0x296A, 0x3250, 0x3128, 0x314B, 0x39CF, 0x1462, 0x24C5, 0x3528,
    0x458A, 0x61AC,
};


}

#endif
