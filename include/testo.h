#ifndef GUBBIO_TESTO_H
#define GUBBIO_TESTO_H

#include "stile/font.h"
#include "tabella.h"
#include "testi.h"

// Accesso ai testi generati da tools/genera_testi.py. Il resto del codice non indicizza mai
// direttamente GLIFI, RIGHE, TAGLI o TESTI: passa da qui (tests/test_accesso_tabelle.py lo
// controlla).
namespace gubbio::testo
{

using testi::Contesto;
using testi::Riga;
using testi::Testo;
using testi::TestoId;

constexpr const Testo& dati(TestoId id)
{
    return GUBBIO_VOCE(testi::TESTI, int(id));
}

constexpr int larghezza_contesto(Contesto contesto)
{
    return GUBBIO_VOCE(testi::CONTESTO_LARGHEZZA, int(contesto));
}

constexpr int righe_contesto(Contesto contesto)
{
    return GUBBIO_VOCE(testi::CONTESTO_RIGHE, int(contesto));
}

// Sprite da 32 px che servono, al massimo, a una riga del contesto.
constexpr int sprite_per_riga(Contesto contesto)
{
    return (larghezza_contesto(contesto) + testi::LARGHEZZA_SPRITE - 1) / testi::LARGHEZZA_SPRITE;
}

// Indice globale (in RIGHE) della riga r del testo.
constexpr int indice_riga(const Testo& t, int r)
{
    BN_ASSERT(r >= 0 && r < t.righe, "Testo: riga ", r, " fuori da 0..", t.righe - 1);
    return t.prima_riga + r;
}

constexpr const Riga& riga(int indice_globale)
{
    return GUBBIO_VOCE(testi::RIGHE, indice_globale);
}

constexpr int glifo_font(int glifo)
{
    return GUBBIO_VOCE(testi::GLIFI, glifo);
}

constexpr int byte_glifo(int glifo)
{
    return GUBBIO_VOCE(testi::BYTE_GLIFO, glifo);
}

constexpr int x_glifo(int glifo)
{
    return GUBBIO_VOCE(testi::X_GLIFO, glifo);
}

// Primo glifo della riga che tocca lo sprite k.
constexpr int taglio(int indice_globale_riga, int k)
{
    BN_ASSERT(k >= 0 && k < testi::SPRITE_PER_RIGA, "Taglio: sprite ", k, " fuori riga");
    return GUBBIO_VOCE(testi::TAGLI, indice_globale_riga * testi::SPRITE_PER_RIGA + k);
}

// Sprite accesi in una riga quando ne sono stati rivelati 'rivelati' glifi.
constexpr int sprite_accesi(int indice_globale_riga, int rivelati)
{
    int accesi = 0;

    for(int k = 0; k < testi::SPRITE_PER_RIGA; ++k)
    {
        if(taglio(indice_globale_riga, k) < rivelati)
        {
            accesi = k + 1;
        }
    }

    return accesi;
}

constexpr const stile::Glifo& glifo(int indice_font)
{
    return GUBBIO_VOCE(stile::FONT, indice_font);
}

// Chiama accendi(x, y) per ogni pixel acceso del glifo, con x relativa alla riga.
template<typename Accendi>
constexpr void per_ogni_pixel(const stile::Glifo& g, int x, Accendi&& accendi)
{
    for(int y = 0; y < stile::FONT_ALTEZZA; ++y)
    {
        int bit = g.righe[y];

        for(int c = 0; c < g.larghezza; ++c)
        {
            if(bit & (0x80 >> c))
            {
                accendi(x + c, y);
            }
        }
    }
}

// Parola e spostamento del pixel (x, y) nei tile di uno sprite 32x16 a 4bpp (mappatura 1D:
// 4 tile per riga, 2 righe di tile, 8 parole per tile, un nibble per pixel).
constexpr int parola_pixel(int x_nello_sprite, int y)
{
    return (((y / 8) * 4) + (x_nello_sprite / 8)) * 8 + (y % 8);
}

constexpr int spostamento_pixel(int x_nello_sprite)
{
    return (x_nello_sprite % 8) * 4;
}

}

#endif
