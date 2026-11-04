#ifndef GUBBIO_PANNELLO_H
#define GUBBIO_PANNELLO_H

#include "bn_sprite_palette_ptr.h"
#include "bn_sprite_ptr.h"
#include "bn_sprite_tiles_ptr.h"
#include "bn_vector.h"

// I riquadri degli aiuti in esplorazione (mockup 09 e 12): una tela di sprite 64x32 su cui si disegnano a pixel il
// fondo, il bordo, le frecce e la stella, che si sposta tutta insieme (le entrate A2 e A3). Il testo ci sta sopra
// (VistaTesto, stessa palette, z piu' basso). Una palette sola per i due riquadri, coi colori della Guida.
namespace gubbio::pannello
{

inline constexpr int PIOMBO = 1;        // neutri 0: il bordo, il contorno delle frecce (k)
inline constexpr int CHIARO = 2;        // neutri 4: il testo
inline constexpr int SCURO = 3;         // neutri 1: il fondo del promemoria
inline constexpr int LEGNO = 4;         // legno e cuoio 1: il fondo del cartello
inline constexpr int LEGNO_LUCE = 5;    // legno e cuoio 2: la cornicetta del cartello
inline constexpr int PIETRA = 6;        // pietra calcarea 4: la seconda riga del cartello
inline constexpr int ORO = 7;           // oro e bronzo 3: l'oro acceso (O)
inline constexpr int ORO_SPENTO = 8;    // oro e bronzo 2: l'oro spento (o), e la freccia che lampeggia

[[nodiscard]] bn::sprite_palette_ptr crea_palette();

class Pannello
{
public:
    static constexpr int SPRITE_MAX = 8;

    // Angolo in alto a sinistra (x, y) sullo schermo, larghezza e altezza in pixel (fino a 256 x 64).
    Pannello(int x, int y, int larghezza, int altezza, const bn::sprite_palette_ptr& palette);

    // Rettangolo pieno e bordo di un pixel, in pixel del pannello, estremi compresi.
    void rett(int x0, int y0, int x1, int y1, int colore);
    void bordo(int x0, int y0, int x1, int y1, int colore);
    // Un disegno 8x8 dei mockup (k, O, o; '.' trasparente) con l'angolo in (x, y); con 'spento' O diventa o.
    void disegno(const char* const (&righe)[8], int x, int y, bool spento = false);
    // Lo stesso, da una funzione pixel(x, y) -> carattere (le frecce ruotate di aiuti.h).
    template<typename Pixel>
    void disegno_da(Pixel pixel, int x, int y, bool spento = false)
    {
        for(int yy = 0; yy < 8; ++yy)
        {
            for(int xx = 0; xx < 8; ++xx)
            {
                _punto_del_disegno(x + xx, y + yy, pixel(xx, yy), spento);
            }
        }
    }

    void sposta(int x, int y);
    [[nodiscard]] int x() const { return _x; }
    [[nodiscard]] int y() const { return _y; }
    [[nodiscard]] int larghezza() const { return _larghezza; }
    [[nodiscard]] int altezza() const { return _altezza; }

private:
    int _x;
    int _y;
    int _larghezza;
    int _altezza;
    int _colonne;
    bn::vector<bn::sprite_tiles_ptr, SPRITE_MAX> _tiles;
    bn::vector<bn::sprite_ptr, SPRITE_MAX> _sprite;

    void _punto(int x, int y, int colore);
    void _punto_del_disegno(int x, int y, char c, bool spento);
};

}

#endif
