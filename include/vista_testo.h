#ifndef GUBBIO_VISTA_TESTO_H
#define GUBBIO_VISTA_TESTO_H

#include "bn_regular_bg_ptr.h"
#include "bn_sprite_palette_ptr.h"
#include "bn_sprite_ptr.h"
#include "bn_sprite_tiles_ptr.h"
#include "bn_vector.h"

#include "testo.h"

namespace gubbio
{

// Testo a schermo in sprite 32x16 a 4bpp, una fila di sprite per riga. Disegna un glifo per
// passo della macchina da scrivere e accende gli sprite dai punti di taglio generati: non
// decide mai da sola dove andare a capo o dove tagliare. Niente heap: sprite e tile vengono dai
// gestori di Butano, i contenitori sono bn::vector a capacita' fissa.
class VistaTesto
{
public:
    static constexpr int SPRITE_MAX = 3 * testi::SPRITE_PER_RIGA;

    // x, y: angolo in alto a sinistra della prima riga, in pixel dello schermo.
    VistaTesto(testo::Contesto contesto, int x, int y, int inchiostro,
               const bn::sprite_palette_ptr& palette);

    void mostra(testo::TestoId id);
    void avanza();          // un passo della macchina da scrivere
    void rivela_tutto();
    void nascondi();
    [[nodiscard]] bool completo() const;
    [[nodiscard]] int rivelati() const;

private:
    testo::Contesto _contesto;
    int _sprite_per_riga;
    int _inchiostro;
    const testo::Testo* _testo = nullptr;
    int _rivelati = 0;
    int _riga = 0;
    int _nella_riga = 0;
    bn::vector<bn::sprite_tiles_ptr, SPRITE_MAX> _tiles;
    bn::vector<bn::sprite_ptr, SPRITE_MAX> _sprite;

    void _pulisci();
};

// Un numero a 16 bit con segno in un solo sprite 32x16, scritto da formatta_intero. Con 'contorno' (un
// indice della palette, -1 = nessuno) ogni cifra ha intorno un pixel scuro: si legge su ogni fondo
// (STANDARD_GRAFICO P1, C6), come i numeri del danno e i PV in battaglia.
class VistaNumero
{
public:
    VistaNumero(int x, int y, int inchiostro, const bn::sprite_palette_ptr& palette, int contorno = -1);

    void mostra(int valore);
    void colloca(int x, int y);     // angolo in alto a sinistra, in pixel dello schermo
    void nascondi();

private:
    int _inchiostro;
    int _contorno;
    bn::sprite_tiles_ptr _tiles;
    bn::sprite_ptr _sprite;
};

// Palette degli sprite di testo: quella della cornice (scelta 9), indice 0 trasparente.
[[nodiscard]] bn::sprite_palette_ptr crea_palette_testo();

// Il riquadro del dialogo composto a 9-slice con i tile della cornice, come stile.componi_cornice.
[[nodiscard]] bn::regular_bg_ptr crea_riquadro_dialogo();

}

#endif
