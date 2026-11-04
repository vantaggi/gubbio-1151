#include "menu_pagine.h"

#include "bn_bg_palette_item.h"
#include "bn_bg_palette_ptr.h"
#include "bn_keypad.h"
#include "bn_log.h"
#include "bn_optional.h"
#include "bn_regular_bg_map_cell_info.h"
#include "bn_regular_bg_map_ptr.h"
#include "bn_regular_bg_ptr.h"
#include "bn_regular_bg_tiles_ptr.h"
#include "bn_size.h"
#include "bn_tile.h"
#include "bn_vector.h"

#include "audio.h"
#include "mondo.h"
#include "stile/mappa_menu.h"
#include "storia_logica.h"
#include "tabella.h"

// La mappa della citta' (MMA, menu/PROPOSTA.md sez. 3.3; mockup menu/mockup/03_mappa.png e 03c_legenda.png). In alto
// la mappa a schema, col nord in alto come il gioco: il fondo viene da tools/genera_mappa_menu.py, e qui ci si disegnano sopra
// le strade (piene fra aree viste, a puntini verso quelle no), le porte e le aree (oro le viste, grigio la nebbia).
// Sopra, come sprite, i segnalini: dove sei, la cronaca, gli incarichi, il venditore, le botteghe, la taverna. In
// basso la scheda dell'area sotto il cursore: nome, quota, una riga. Le frecce spostano il cursore all'area piu'
// vicina in quella direzione; Select apre la legenda.
namespace gubbio::menu
{

namespace
{
    using testo::TestoId;
    using stile::IconaMenu;
    using namespace stile;

    constexpr int RIGHE_MAPPA = 13;     // il riquadro della mappa, in tile: tocca quello della scheda (y 104)
    constexpr int TILE_MAPPA = MAPPA_COLONNE * MAPPA_RIGHE;
    constexpr int SCHEDA_Y = 116;

    BN_DATA_EWRAM_BSS bn::tile s_tile[TILE_MAPPA + 1];

    // ------------------------------------------------------------------ le aree
    // L'area della mappa per un'area del gioco: un interno vale come la strada da cui si entra. -1 se nessuna.
    int nodo_di(int area)
    {
        if(area < 0 || area >= mondo::AREE_CONTEGGIO)
        {
            return -1;
        }

        const mondo::Area& a = mondo::area(mondo::AreaId(area));

        if(a.interno && a.varchi > 0 && a.varco[0].destinazione >= 0)
        {
            area = a.varco[0].destinazione;
        }

        for(int n = 0; n < NODI_MAPPA; ++n)
        {
            if(int(GUBBIO_VOCE(NODO_MAPPA, n).area) == area)
            {
                return n;
            }
        }

        return -1;
    }

    int nodo_dell_area(mondo::AreaId a)
    {
        return nodo_di(int(a));
    }

    bool vista(const GameState& p, int n)
    {
        return storia::area_vista(p, int(GUBBIO_VOCE(NODO_MAPPA, n).area));
    }

    int nodo_x(int n)
    {
        return MAPPA_X0 + GUBBIO_VOCE(NODO_MAPPA, n).x;
    }

    int nodo_y(int n)
    {
        return MAPPA_Y0 + GUBBIO_VOCE(NODO_MAPPA, n).y;
    }

    // ------------------------------------------------------------------ il disegno
    void pixel(int x, int y, int colore)
    {
        if(x < 0 || y < 0 || x >= MAPPA_COLONNE * 8 || y >= MAPPA_RIGHE * 8)
        {
            return;
        }

        bn::tile& t = s_tile[(y / 8) * MAPPA_COLONNE + x / 8];
        int s = 4 * (x % 8);
        t.data[y % 8] = (t.data[y % 8] & ~(0xFu << s)) | (unsigned(colore) << s);
    }

    void disegna(const GameState& p)
    {
        for(int t = 0; t < TILE_MAPPA; ++t)
        {
            for(int r = 0; r < 8; ++r)
            {
                s_tile[t].data[r] = GUBBIO_VOCE(MAPPA_MENU_TILE, t * 8 + r);
            }
        }

        for(int r = 0; r < 8; ++r)
        {
            s_tile[TILE_MAPPA].data[r] = 0;
        }

        // le strade: piene fra due aree viste, se no un pixel ogni tre
        for(int a = 0; a < ARCHI_MAPPA; ++a)
        {
            const ArcoMappa& arco = GUBBIO_VOCE(ARCO_MAPPA, a);
            bool piena = vista(p, arco.a) && vista(p, arco.b);

            for(int k = 0; k < arco.quanti; ++k)
            {
                if(piena || k % 3 == 0)
                {
                    int i = (arco.primo + k) * 2;
                    pixel(GUBBIO_VOCE(ARCO_PIXEL, i), GUBBIO_VOCE(ARCO_PIXEL, i + 1), MAPPA_STRADA);
                }
            }
        }

        for(int k = 0; k < PORTE_MAPPA; ++k)
        {
            const PortaMappa& porta = GUBBIO_VOCE(PORTA_MAPPA, k);

            for(int r = 0; r < 8; ++r)
            {
                for(int c = 0; c < 8; ++c)
                {
                    int v = int((GUBBIO_VOCE(PORTA_MAPPA_TILE, r) >> (4 * c)) & 0xF);

                    if(v)
                    {
                        pixel(porta.x + c, porta.y + r, v);
                    }
                }
            }
        }

        // le aree: una tessera 7x7 col bordo scuro, oro se vista (con un punto di luce), grigia nella nebbia
        for(int n = 0; n < NODI_MAPPA; ++n)
        {
            const NodoMappa& nodo = GUBBIO_VOCE(NODO_MAPPA, n);
            bool v = vista(p, n);

            for(int dy = -3; dy <= 3; ++dy)
            {
                for(int dx = -3; dx <= 3; ++dx)
                {
                    bool bordo = dx == -3 || dx == 3 || dy == -3 || dy == 3;
                    pixel(nodo.x + dx, nodo.y + dy, bordo ? MAPPA_K : (v ? MAPPA_VISTA : MAPPA_NEBBIA));
                }
            }

            if(v)
            {
                pixel(nodo.x - 2, nodo.y - 2, MAPPA_LUCE);
            }
        }
    }

    // Il fondo della mappa: un BG coi tile disegnati sopra, l'angolo in (0, 0), dietro i riquadri (che li' sono bucati).
    class FondoMappa
    {
    public:
        explicit FondoMappa(const GameState& p) :
            _mappa(bn::regular_bg_map_ptr::allocate(bn::size(32, 32), tiles(p), palette())),
            _bg(bn::regular_bg_ptr::create(256 / 2 - 240 / 2, 256 / 2 - 160 / 2, _mappa))
        {
            bn::span<bn::regular_bg_map_cell> celle = *_mappa.vram();

            for(int ty = 0; ty < 32; ++ty)
            {
                for(int tx = 0; tx < 32; ++tx)
                {
                    int cx = tx - MAPPA_X0 / 8;
                    int cy = ty - MAPPA_Y0 / 8;
                    bool dentro = cx >= 0 && cx < MAPPA_COLONNE && cy >= 0 && cy < MAPPA_RIGHE;
                    bn::regular_bg_map_cell_info info;
                    info.set_tile_index((dentro ? cy * MAPPA_COLONNE + cx : TILE_MAPPA) + _mappa.tiles_offset());
                    info.set_palette_id(_mappa.palette().id());
                    celle[ty * 32 + tx] = info.cell();
                }
            }

            _bg.set_priority(PRIORITA_RIQUADRI);
            _bg.set_z_order(1);
        }

    private:
        bn::regular_bg_map_ptr _mappa;
        bn::regular_bg_ptr _bg;

        static bn::regular_bg_tiles_ptr tiles(const GameState& p)
        {
            disegna(p);
            bn::regular_bg_tiles_ptr t = bn::regular_bg_tiles_ptr::allocate(TILE_MAPPA + 1, bn::bpp_mode::BPP_4);
            bn::span<bn::tile> vram = *t.vram();

            for(int i = 0; i <= TILE_MAPPA; ++i)
            {
                vram[i] = s_tile[i];
            }

            return t;
        }

        static bn::bg_palette_ptr palette()
        {
            struct Colori
            {
                bn::color c[16];
            };

            static constexpr Colori COLORI = [] {
                Colori r;

                for(int i = 0; i < 16; ++i)
                {
                    r.c[i] = bn::color(GUBBIO_VOCE(MAPPA_MENU_PALETTE, i));
                }

                return r;
            }();

            return bn::bg_palette_ptr::create(bn::bg_palette_item(bn::span<const bn::color>(COLORI.c), bn::bpp_mode::BPP_4));
        }
    };

    // ------------------------------------------------------------------ i segnalini
    struct Rett
    {
        int x0;
        int y0;
        int x1;
        int y1;
    };

    bool tocca(const Rett& a, const Rett& b)
    {
        return ! (a.x1 < b.x0 || b.x1 < a.x0 || a.y1 < b.y0 || b.y1 < a.y0);
    }

    Rett pieno(IconaMenu icona, int x, int y)
    {
        int i = int(icona) * 4;
        return { x + GUBBIO_VOCE(ICONE_MENU_PIENO, i), y + GUBBIO_VOCE(ICONE_MENU_PIENO, i + 1),
                 x + GUBBIO_VOCE(ICONE_MENU_PIENO, i + 2), y + GUBBIO_VOCE(ICONE_MENU_PIENO, i + 3) };
    }

    struct Segnalino
    {
        IconaMenu icona;
        int nodo;
    };

    // Dove si fa ogni incarico (nell'ordine di storia::QUEST_V1): le fornaci del Teatro, le rocce del Bottaccione,
    // e per la Rosa la citta' stessa, a partire da chi l'ha chiesta.
    constexpr mondo::AreaId DOVE_SI_FA[storia::QUEST] = {
        mondo::AreaId::TEATRO_ROMANO, mondo::AreaId::BOTTACCIONE, mondo::AreaId::SAN_PIETRO };
    constexpr IconaMenu BANDIERA[storia::QUEST] = { IconaMenu::INCARICO_SM, IconaMenu::INCARICO_SA, IconaMenu::INCARICO_SP };
    constexpr IconaMenu CONSEGNA[storia::QUEST] = { IconaMenu::CONSEGNA_SM, IconaMenu::CONSEGNA_SA, IconaMenu::CONSEGNA_SP };

    static_assert(storia::QUEST == 3, "la mappa conosce tre incarichi: aggiungere i nuovi a DOVE_SI_FA");

    constexpr int SEGNALINI_MAX = 12;

    bn::vector<Segnalino, SEGNALINI_MAX> segnalini(const GameState& p)
    {
        bn::vector<Segnalino, SEGNALINI_MAX> v;
        auto aggiungi = [&](IconaMenu icona, int nodo) {
            if(nodo >= 0 && ! v.full())
            {
                v.push_back({ icona, nodo });
            }
        };

        aggiungi(IconaMenu::SEI_QUI, nodo_di(p.area));
        aggiungi(IconaMenu::OBIETTIVO, nodo_di(storia::area_dell_obiettivo(p)));

        for(int q = 0; q < storia::QUEST; ++q)
        {
            if(! storia::presa(p, q) || storia::accesa(p, int(GUBBIO_VOCE(storia::QUEST_V1, q).consegnata)))
            {
                continue;
            }

            if(storia::obiettivo_fatto(p, q))
            {
                aggiungi(GUBBIO_VOCE(CONSEGNA, q), nodo_di(GUBBIO_VOCE(storia::QUEST_V1, q).consegna));
            }
            else
            {
                aggiungi(GUBBIO_VOCE(BANDIERA, q), nodo_dell_area(GUBBIO_VOCE(DOVE_SI_FA, q)));
            }
        }

        // i posti fissi, solo nelle aree gia' viste
        struct Fisso
        {
            IconaMenu icona;
            mondo::AreaId area;
        };

        constexpr Fisso FISSI[] = {
            { IconaMenu::VENDITORE, mondo::AreaId::PIAZZA_QUARANTA_MARTIRI },
            { IconaMenu::TAVERNA, mondo::AreaId::SAN_PIETRO },
            { IconaMenu::BOTTEGA, mondo::AreaId::PIAZZA_QUARANTA_MARTIRI },
            { IconaMenu::BOTTEGA, mondo::AreaId::SANT_AGOSTINO },
        };

        for(const Fisso& f : FISSI)
        {
            int n = nodo_dell_area(f.area);

            if(n >= 0 && vista(p, n))
            {
                aggiungi(f.icona, n);
            }
        }

        return v;
    }

    // Il posto di ogni segnalino attorno alla sua area, come nel mockup (posti_segnalini): sopra, a destra, a sinistra,
    // sotto, poi in diagonale. Il posto buono non tocca aree, porte, altri segnalini, il cartiglio, la rosa, il bordo;
    // sta entro 14 px dalla sua area e piu' vicino a lei che a ogni altra.
    constexpr int POSTI = 8;
    constexpr int POSTO_X[POSTI] = { -4, 9, -17, -4, 9, -17, 9, -17 };
    constexpr int POSTO_Y[POSTI] = { -16, -4, -4, 9, -14, -14, 6, 6 };

    struct Posto
    {
        int x;
        int y;
    };

    bn::vector<Posto, SEGNALINI_MAX> posti(const bn::vector<Segnalino, SEGNALINI_MAX>& segni)
    {
        bn::vector<Rett, NODI_MAPPA + PORTE_MAPPA + 2 + SEGNALINI_MAX> occupati;

        for(int n = 0; n < NODI_MAPPA; ++n)
        {
            occupati.push_back({ nodo_x(n) - 3, nodo_y(n) - 3, nodo_x(n) + 3, nodo_y(n) + 3 });
        }

        for(int k = 0; k < PORTE_MAPPA; ++k)
        {
            const PortaMappa& porta = GUBBIO_VOCE(PORTA_MAPPA, k);
            occupati.push_back(pieno(IconaMenu::PORTA, MAPPA_X0 + porta.x, MAPPA_Y0 + porta.y));
        }

        constexpr int X1 = MAPPA_X0 + MAPPA_COLONNE * 8;
        constexpr int Y1 = MAPPA_Y0 + MAPPA_RIGHE * 8;
        occupati.push_back({ 8, 4, 64, 19 });                       // il cartiglio
        occupati.push_back({ X1 - 18, Y1 - 11, X1 - 3, Y1 - 5 });   // la rosa dei venti
        bn::vector<Posto, SEGNALINI_MAX> out;

        for(const Segnalino& s : segni)
        {
            int x = nodo_x(s.nodo);
            int y = nodo_y(s.nodo);
            Posto trovato = { x + POSTO_X[0], y + POSTO_Y[0] };

            for(int k = 0; k < POSTI; ++k)
            {
                int px = x + GUBBIO_VOCE(POSTO_X, k);
                int py = y + GUBBIO_VOCE(POSTO_Y, k);
                Rett r = pieno(s.icona, px, py);
                int cx2 = r.x0 + r.x1;      // il centro, raddoppiato
                int cy2 = r.y0 + r.y1;
                bool buono = r.x0 >= MAPPA_X0 + 1 && r.y0 >= MAPPA_Y0 + 1 && r.x1 <= X1 - 2 && r.y1 <= Y1 - 2;

                for(int o = 0; buono && o < occupati.size(); ++o)
                {
                    buono = ! tocca(r, occupati[o]);
                }

                int mio = (cx2 - 2 * x) * (cx2 - 2 * x) + (cy2 - 2 * y) * (cy2 - 2 * y);
                buono = buono && mio <= 4 * 14 * 14;

                for(int n = 0; buono && n < NODI_MAPPA; ++n)
                {
                    if(n != s.nodo)
                    {
                        int nx = nodo_x(n);
                        int ny = nodo_y(n);
                        int altro = (cx2 - 2 * nx) * (cx2 - 2 * nx) + (cy2 - 2 * ny) * (cy2 - 2 * ny);
                        buono = ! tocca(r, { nx - 7, ny - 7, nx + 7, ny + 7 }) && altro >= mio;
                    }
                }

                if(buono)
                {
                    trovato = { px, py };
                    break;
                }
            }

            occupati.push_back(pieno(s.icona, trovato.x, trovato.y));
            out.push_back(trovato);
        }

        return out;
    }

    // ------------------------------------------------------------------ il cursore
    // L'area piu' vicina nella direzione (dx, dy): conta di piu' lo scarto di lato che la distanza. -1 se nessuna.
    int accanto(int n, int dx, int dy)
    {
        int migliore = -1;
        int punti_migliori = 0;

        for(int m = 0; m < NODI_MAPPA; ++m)
        {
            int vx = nodo_x(m) - nodo_x(n);
            int vy = nodo_y(m) - nodo_y(n);
            int avanti = vx * dx + vy * dy;
            int lato = vx * dy - vy * dx;
            lato = lato < 0 ? -lato : lato;

            if(m == n || avanti <= 0 || lato > 2 * avanti)
            {
                continue;
            }

            int punti = avanti + 2 * lato;

            if(migliore < 0 || punti < punti_migliori)
            {
                migliore = m;
                punti_migliori = punti;
            }
        }

        return migliore;
    }

    class CursoreMappa
    {
    public:
        explicit CursoreMappa(const bn::sprite_palette_ptr& icone) :
            _angoli{ crea_icona(IconaMenu::ANGOLO, 0, 0, icone), crea_icona(IconaMenu::ANGOLO, 0, 0, icone),
                     crea_icona(IconaMenu::ANGOLO, 0, 0, icone), crea_icona(IconaMenu::ANGOLO, 0, 0, icone) }
        {
            _angoli[1].set_horizontal_flip(true);
            _angoli[2].set_vertical_flip(true);
            _angoli[3].set_horizontal_flip(true);
            _angoli[3].set_vertical_flip(true);
        }

        // quattro angoli a L larghi 15 px attorno all'area (x, y)
        void su(int x, int y)
        {
            colloca(_angoli[0], x - 7, y - 7, 8, 8);
            colloca(_angoli[1], x, y - 7, 8, 8);
            colloca(_angoli[2], x - 7, y, 8, 8);
            colloca(_angoli[3], x, y, 8, 8);
        }

    private:
        bn::sprite_ptr _angoli[4];
    };

    // ------------------------------------------------------------------ la scheda
    class Scheda
    {
    public:
        Scheda(const GameState& p, int n, int qui, const bn::sprite_palette_ptr& palette)
        {
            const NodoMappa& nodo = GUBBIO_VOCE(NODO_MAPPA, n);
            TestoId nome = mondo::area(nodo.area).etichetta;
            _nome.emplace(nome, MARGINE_X, SCHEDA_Y, TITOLO, palette);

            if(n == qui)
            {
                _sei_qui.emplace(TestoId::MAPPA_SEI_QUI, MARGINE_X + larghezza_testo(nome), SCHEDA_Y, TITOLO, palette);
            }

            _quota.emplace(nodo.quota, DESTRA_X + 1 - larghezza_testo(nodo.quota), SCHEDA_Y, NOTA, palette);
            bool v = vista(p, n);
            _riga.emplace(v ? nodo.riga : TestoId::MAPPA_NON_VISTA, MARGINE_X, SCHEDA_Y + 10, v ? INCHIOSTRO : NOTA, palette);
        }

    private:
        bn::optional<Scritta> _nome;
        bn::optional<Scritta> _sei_qui;
        bn::optional<Scritta> _quota;
        bn::optional<Scritta> _riga;
    };

    // ------------------------------------------------------------------ il libro di Gubbio (mockup 03d)
    // Una pagina per area gia' vista, nell'ordine della mappa: com'e' quel luogo oggi. Destra e sinistra passano alle
    // altre aree viste; B torna alla mappa col cursore sull'ultima pagina letta.
    Esito libro(const GameState& p, int& nodo, const bn::sprite_palette_ptr& palette, bool istantanea)
    {
        bn::vector<int, NODI_MAPPA> viste;
        int i = 0;

        for(int n = 0; n < NODI_MAPPA; ++n)
        {
            if(vista(p, n))
            {
                i = n == nodo ? viste.size() : i;
                viste.push_back(n);
            }
        }

        while(true)
        {
            Esito esito = Esito::INDIETRO;
            int passo = 0;

            {
                const NodoMappa& pagina_nodo = GUBBIO_VOCE(NODO_MAPPA, viste[i]);
                Pagina pagina(PAGINA_MAPPA, TestoId::LIBRO_AIUTO, palette, TestoId::LIBRO_TITOLO);
                Scritta nome(mondo::area(pagina_nodo.area).etichetta, 13, 24, TITOLO, palette);
                // «3 di 10» contro il bordo destro
                VistaNumero quante(0, 24, NOTA, palette);
                quante.mostra(viste.size());
                quante.colloca_a_destra(DESTRA_X, 24);
                int di_x = DESTRA_X + 1 - quante.larghezza() - 4 - larghezza_testo(TestoId::LIBRO_DI);
                Scritta di(TestoId::LIBRO_DI, di_x, 24, NOTA, palette);
                VistaNumero questa(0, 24, NOTA, palette);
                questa.mostra(i + 1);
                questa.colloca_a_destra(di_x - 4, 24);
                Scritta oggi(TestoId::LIBRO_OGGI, 13, 35, NOTA, palette);
                TestoId primo = GUBBIO_VOCE(pagina_nodo.libro, 0);
                Scritta uno(primo, 13, 52, INCHIOSTRO, palette);
                Scritta due(GUBBIO_VOCE(pagina_nodo.libro, 1), 13, 52 + testo::dati(primo).righe * 10 + 5, INCHIOSTRO, palette);

                if(istantanea)
                {
                    attendi(30);
                    BN_LOG("Istantanea pausa_mappa_libro");
                    attendi(30);
                    return Esito::INDIETRO;
                }

                while(passo == 0)
                {
                    attendi(1);

                    if(navigazione(esito))
                    {
                        audio::suona(colonna::Suono::ANNULLA);
                        nodo = viste[i];
                        return esito;
                    }

                    if(viste.size() > 1 && (bn::keypad::left_pressed() || bn::keypad::right_pressed()))
                    {
                        passo = bn::keypad::right_pressed() ? 1 : -1;
                        audio::suona(colonna::Suono::CURSORE);
                    }
                }
            }

            i = (i + passo + viste.size()) % viste.size();
            attendi(1);
        }
    }

    // ------------------------------------------------------------------ la legenda (mockup 03c)
    Esito legenda(const bn::sprite_palette_ptr& palette, const bn::sprite_palette_ptr& icone, bool istantanea)
    {
        struct Voce
        {
            IconaMenu icona;
            TestoId testo;
        };

        constexpr Voce VOCI_LEGENDA[] = {
            { IconaMenu::SEI_QUI, TestoId::LEGENDA_SEI_QUI }, { IconaMenu::OBIETTIVO, TestoId::LEGENDA_CRONACA },
            { IconaMenu::INCARICO_SM, TestoId::LEGENDA_INCARICO }, { IconaMenu::CONSEGNA_SA, TestoId::DIARIO_COMPIUTO },
            { IconaMenu::VENDITORE, TestoId::LEGENDA_VENDITORE }, { IconaMenu::BOTTEGA, TestoId::LEGENDA_BOTTEGA },
            { IconaMenu::TAVERNA, TestoId::LEGENDA_TAVERNA }, { IconaMenu::PORTA, TestoId::LEGENDA_PORTA },
        };

        constexpr int N = int(sizeof(VOCI_LEGENDA) / sizeof(VOCI_LEGENDA[0]));
        Riquadri riquadri;
        riquadri.cornice(8, 8, 28, 18);
        riquadri.cartiglio(16, 0, colonne_cartiglio(larghezza_testo(TestoId::LEGENDA_TITOLO)));
        Scritta titolo(TestoId::LEGENDA_TITOLO,
                       16 + (colonne_cartiglio(larghezza_testo(TestoId::LEGENDA_TITOLO)) * 8 -
                             larghezza_testo(TestoId::LEGENDA_TITOLO)) / 2, 4, CHIARO, palette);
        bn::optional<bn::sprite_ptr> segni[N];
        bn::optional<Scritta> scritte[N];

        for(int i = 0; i < N; ++i)
        {
            segni[i] = crea_icona(VOCI_LEGENDA[i].icona, 23, 24 + i * 11, icone);
            scritte[i].emplace(VOCI_LEGENDA[i].testo, 34, 24 + i * 11, INCHIOSTRO, palette);
        }

        Scritta grigio(TestoId::LEGENDA_GRIGIO, 23, 24 + N * 11 + 5, NOTA, palette);

        if(istantanea)
        {
            attendi(30);
            BN_LOG("Istantanea pausa_mappa_legenda");
            attendi(30);
            return Esito::INDIETRO;
        }

        Esito esito = Esito::INDIETRO;

        while(true)
        {
            attendi(1);

            if(bn::keypad::select_pressed() || bn::keypad::a_pressed())
            {
                audio::suona(colonna::Suono::ANNULLA);
                return Esito::INDIETRO;
            }

            if(navigazione(esito))
            {
                audio::suona(colonna::Suono::ANNULLA);
                // B chiude la legenda e torna alla mappa; Start, L e R valgono come nella mappa
                return esito == Esito::INDIETRO ? Esito::INDIETRO : esito;
            }
        }
    }
}

Esito pagina_mappa(const bn::sprite_palette_ptr& palette, bool istantanea)
{
    const GameState& p = g_game_state;
    bn::sprite_palette_ptr icone = crea_palette_icone();
    int qui = nodo_di(p.area);
    int voce = qui >= 0 ? qui : nodo_dell_area(mondo::AreaId::PIAZZA_GRANDE);

    while(true)
    {
        Esito esito = Esito::INDIETRO;
        bool apri_legenda = false;
        bool apri_libro = false;

        {
            Pagina pagina(PAGINA_MAPPA, TestoId::MAPPA_AIUTO_A, TestoId::MAPPA_AIUTO_SELECT, palette);
            pagina.con_mappa(RIGHE_MAPPA);
            FondoMappa fondo(p);
            bn::vector<Segnalino, SEGNALINI_MAX> segni = segnalini(p);
            bn::vector<Posto, SEGNALINI_MAX> dove = posti(segni);
            bn::vector<bn::sprite_ptr, SEGNALINI_MAX> sprite;

            for(int i = 0; i < segni.size(); ++i)
            {
                sprite.push_back(crea_icona(segni[i].icona, dove[i].x, dove[i].y, icone));
            }

            CursoreMappa cursore(icone);
            bn::optional<Scheda> scheda;
            bool cambia = true;

            while(true)
            {
                if(cambia)
                {
                    cursore.su(nodo_x(voce), nodo_y(voce));
                    scheda.reset();
                    scheda.emplace(p, voce, qui, palette);
                    cambia = false;
                }

                if(istantanea)
                {
                    attendi(30);
                    BN_LOG("Istantanea pausa_mappa");
                    attendi(30);
                    break;
                }

                attendi(1);

                if(navigazione(esito))
                {
                    audio::suona(colonna::Suono::ANNULLA);
                    return esito;
                }

                if(bn::keypad::select_pressed())
                {
                    audio::suona(colonna::Suono::CONFERMA);
                    apri_legenda = true;
                    break;
                }

                if(bn::keypad::a_pressed())
                {
                    // il libro c'e' solo per le aree gia' viste
                    bool aperto = vista(p, voce);
                    audio::suona(aperto ? colonna::Suono::CONFERMA : colonna::Suono::ANNULLA);

                    if(aperto)
                    {
                        apri_libro = true;
                        break;
                    }
                }

                int dx = bn::keypad::left_pressed() ? -1 : (bn::keypad::right_pressed() ? 1 : 0);
                int dy = bn::keypad::up_pressed() ? -1 : (bn::keypad::down_pressed() ? 1 : 0);

                if(dx || dy)
                {
                    int m = accanto(voce, dx, dy);

                    if(m >= 0)
                    {
                        voce = m;
                        cambia = true;
                        audio::suona(colonna::Suono::CURSORE);
                    }
                }
            }
        }

        attendi(1);

        if(istantanea)
        {
            [[maybe_unused]] Esito e = legenda(palette, icone, true);
            attendi(1);

            if(vista(p, voce))
            {
                e = libro(p, voce, palette, true);
                attendi(1);
            }

            return Esito::INDIETRO;
        }

        if(apri_libro)
        {
            Esito e = libro(p, voce, palette, false);
            attendi(1);

            if(e != Esito::INDIETRO)
            {
                return e;
            }
        }

        if(apri_legenda)
        {
            Esito e = legenda(palette, icone, false);
            attendi(1);

            if(e != Esito::INDIETRO)
            {
                return e;
            }
        }
    }
}

}
