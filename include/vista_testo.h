#ifndef GUBBIO_VISTA_TESTO_H
#define GUBBIO_VISTA_TESTO_H

#include "bn_regular_bg_map_ptr.h"
#include "bn_regular_bg_ptr.h"
#include "bn_sprite_palette_ptr.h"
#include "bn_sprite_ptr.h"
#include "bn_sprite_tiles_ptr.h"
#include "bn_vector.h"

#include "stile/cornice.h"
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
    int _x;
    int _y;
    bn::sprite_palette_ptr _palette;
    int _primo[3] = {};             // il primo sprite di ogni riga del testo mostrato
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
    void mostra_tempo(int secondi);             // "h:mm" (formatta_tempo)
    void mostra_livelli(int a, int b, int c);   // "4 4 3" (formatta_livelli)
    void mostra_frazione(int a, int b);         // "2/3": i contatori degli incarichi (MDI)
    void colloca(int x, int y);     // angolo in alto a sinistra, in pixel dello schermo
    // Con il bordo destro in x_destra (i numeri allineati a destra dei menu, MPA).
    void colloca_a_destra(int x_destra, int y)
    {
        colloca(x_destra + 1 - _larghezza, y);
    }
    [[nodiscard]] int larghezza() const
    {
        return _larghezza;
    }
    void nascondi();

private:
    void _scrivi(const char* caratteri, int n);

    int _inchiostro;
    int _contorno;
    int _larghezza = 0;
    bn::sprite_tiles_ptr _tiles;
    bn::sprite_ptr _sprite;
};

// Palette degli sprite di testo: quella della cornice (scelta 9), indice 0 trasparente.
[[nodiscard]] bn::sprite_palette_ptr crea_palette_testo();

// I riquadri della Guida (scelta 9) stanno su un fondo loro, sopra la scena (priorita' 3) e sotto le scritte:
// gli sprite del testo e del cursore hanno la stessa priorita' del fondo, e a pari priorita' lo sprite
// sta sopra. Cosi' il riquadro non si scurisce con la scena e il testo non ci finisce mai sotto.
inline constexpr int PRIORITA_RIQUADRI = 1;

struct TileRiquadro
{
    int tile;
    bool hflip;
    bool vflip;
};

// Il tile della cella cx, cy di una cornice colonne x righe: la stessa regola di stile.componi_cornice
// (angoli col flip, lati a tessere alternate senza flip, centro pieno), cosi' gioco e mockup coincidono.
[[nodiscard]] constexpr TileRiquadro tile_cornice(int cx, int cy, int colonne, int righe)
{
    bool bordo_x = cx == 0 || cx == colonne - 1;
    bool bordo_y = cy == 0 || cy == righe - 1;

    if(bordo_x && bordo_y)
    {
        return { stile::TILE_ANGOLO, cx != 0, cy != 0 };
    }

    if(bordo_y)
    {
        return { GUBBIO_VOCE(stile::LATO_ORIZZONTALE, (cx - 1) % 3), false, false };
    }

    if(bordo_x)
    {
        return { GUBBIO_VOCE(stile::LATO_VERTICALE, (cy - 1) % 3), false, false };
    }

    return { stile::TILE_CENTRO, false, false };
}

// Il cartiglio alto 2 tile: estremita' sinistra, centro, estremita' destra (la sinistra con hflip); la
// riga di sotto e' quella di sopra con vflip (nota della scelta 9).
[[nodiscard]] constexpr TileRiquadro tile_cartiglio(int cx, int cy, int colonne)
{
    bool estremo = cx == 0 || cx == colonne - 1;
    return { estremo ? stile::TILE_CARTIGLIO_SX : stile::TILE_CARTIGLIO_CENTRO, cx == colonne - 1 && colonne > 1,
             cy == 1 };
}

// Colonne di un cartiglio che contiene un testo largo larghezza_testo px: 6 px di margine per parte,
// almeno 3 tile (come mockup_menu.cartiglio).
[[nodiscard]] constexpr int colonne_cartiglio(int larghezza_testo)
{
    int colonne = (larghezza_testo + 12 + 7) / 8;
    return colonne < 3 ? 3 : colonne;
}

// Le regole provate a tempo di compilazione.
static_assert(tile_cornice(0, 0, 30, 7).tile == stile::TILE_ANGOLO && ! tile_cornice(0, 0, 30, 7).hflip);
static_assert(tile_cornice(29, 6, 30, 7).hflip && tile_cornice(29, 6, 30, 7).vflip, "angolo in basso a destra");
static_assert(tile_cornice(1, 0, 30, 7).tile == stile::TILE_ORIZ_0 && tile_cornice(4, 6, 30, 7).tile == stile::TILE_ORIZ_0);
static_assert(tile_cornice(29, 2, 30, 7).tile == stile::TILE_VERT_1 && ! tile_cornice(29, 2, 30, 7).hflip);
static_assert(tile_cornice(5, 3, 30, 7).tile == stile::TILE_CENTRO);
static_assert(tile_cartiglio(5, 1, 6).hflip && tile_cartiglio(5, 1, 6).vflip && ! tile_cartiglio(0, 0, 6).vflip);
static_assert(colonne_cartiglio(0) == 3 && colonne_cartiglio(61) == 10);

// Un fondo 256x256 dove si compongono cornici 9-slice e cartigli in pixel dello schermo (multipli di 8).
// Una sola implementazione per dialogo, menu di scelta, pannello della battaglia e schermata di prova.
class Riquadri
{
public:
    Riquadri();

    void cornice(int x, int y, int colonne, int righe);
    void cartiglio(int x, int y, int colonne);
    void svuota();
    void set_visible(bool visibile);
    [[nodiscard]] const bn::regular_bg_ptr& bg() const { return _bg; }

private:
    bn::regular_bg_map_ptr _mappa;
    bn::regular_bg_ptr _bg;

    void _cella(int tx, int ty, TileRiquadro t);
};

// Il riquadro del dialogo composto a 9-slice con i tile della cornice, come stile.componi_cornice.
[[nodiscard]] bn::regular_bg_ptr crea_riquadro_dialogo();

// Larghezza in pixel della prima riga di un testo (dal generatore: niente misure a mano).
[[nodiscard]] int larghezza_testo(testo::TestoId id);

}

#endif
