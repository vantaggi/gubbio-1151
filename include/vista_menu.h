#ifndef GUBBIO_VISTA_MENU_H
#define GUBBIO_VISTA_MENU_H

#include "bn_sprite_palette_ptr.h"
#include "bn_sprite_ptr.h"
#include "bn_sprite_tiles_ptr.h"
#include "bn_vector.h"

#include "stile/icone_menu.h"

// I pezzi grafici comuni ai menu (MPA, menu/PROPOSTA.md e i mockup di menu/mockup_menu.py): la palette delle
// scritte dei menu, le strisce disegnate a pixel (barre, fili, tessere delle pagine) e il cursore della Guida.
// Tutto sta a PRIORITA_RIQUADRI, sopra le cornici e la scena.
namespace gubbio::menu
{

// La palette dei menu: i colori della cornice (gli stessi indici delle scritte del gioco) piu' quelli che servono
// solo qui, negli indici che la cornice lascia vuoti. Colori della Guida, nessuno inventato (STANDARD C1).
inline constexpr int INCHIOSTRO = 1;        // legno e cuoio 0: il testo sui riquadri chiari
inline constexpr int CHIARO = 2;            // neutri 4: il testo nel cartiglio
inline constexpr int VERMIGLIO = 3;         // vermiglio comunale 2: la tessera della pagina aperta
inline constexpr int ORO = 4;               // oro e bronzo 2: la barra del Fervore
inline constexpr int VERDE = 6;             // verde dei monti 3: la barra dei PV
inline constexpr int TITOLO = 8;            // vermiglio comunale 1: i titoli dentro le pagine
inline constexpr int NOTA = 10;             // pietra calcarea 1: il testo secondario (contrasto >= 4,5)
inline constexpr int SPENTO = 11;           // neutri 2: gli aiuti dei tasti e le cose non ancora avute (>= 3)
inline constexpr int BORDO = 12;            // neutri 0: il bordo delle barre e delle tessere
inline constexpr int GRIGIO = 13;           // neutri 3: il filo che divide, le tessere spente

[[nodiscard]] bn::sprite_palette_ptr crea_palette();

// Una striscia alta 8 px e larga fino a 256, fatta di sprite 32x8: ci si disegnano rettangoli pieni.
class Striscia
{
public:
    static constexpr int SPRITE_MAX = 8;

    Striscia(int x, int y, int larghezza, const bn::sprite_palette_ptr& palette);

    void pulisci();
    // Rettangolo pieno, in pixel della striscia (0..larghezza-1, 0..7), estremi compresi.
    void rett(int x0, int y0, int x1, int y1, int colore);
    void set_visible(bool visibile);

private:
    int _larghezza;
    bn::vector<bn::sprite_tiles_ptr, SPRITE_MAX> _tiles;
    bn::vector<bn::sprite_ptr, SPRITE_MAX> _sprite;
};

// Barra di PV o Fervore (mockup: bordo scuro di 1 px, interno alto 2 px): 'larghezza' px d'interno.
void disegna_barra(Striscia& s, int x, int y, int larghezza, int valore, int massimo, int colore);

// Le sei tessere delle pagine, quella aperta in vermiglio (mockup: indicatore()): 54 px a partire da x.
void disegna_tessere(Striscia& s, int x, int aperta);

// Le icone 8x8 dei menu (tools/genera_icone_menu.py), con la loro palette: si crea una volta per schermata.
[[nodiscard]] bn::sprite_palette_ptr crea_palette_icone();
[[nodiscard]] bn::sprite_ptr crea_icona(stile::IconaMenu icona, int x, int y, const bn::sprite_palette_ptr& palette);

// Il cursore della Guida (il triangolo della cornice), un 8x8 con l'angolo in alto a sinistra in (x, y).
[[nodiscard]] bn::sprite_ptr crea_cursore(const bn::sprite_palette_ptr& palette);
void colloca(bn::sprite_ptr& sprite, int x, int y, int larghezza, int altezza);

}

#endif
