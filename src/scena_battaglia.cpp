#include "scena_battaglia.h"

#include "bn_bg_palette_item.h"
#include "bn_bg_palette_ptr.h"
#include "bn_blending.h"
#include "bn_color.h"
#include "bn_core.h"
#include "bn_keypad.h"
#include "bn_log.h"
#include "bn_math.h"
#include "bn_optional.h"
#include "bn_regular_bg_map_item.h"
#include "bn_regular_bg_map_ptr.h"
#include "bn_regular_bg_ptr.h"
#include "bn_regular_bg_tiles_item.h"
#include "bn_regular_bg_tiles_ptr.h"
#include "bn_size.h"
#include "bn_sprite_palette_item.h"
#include "bn_sprite_ptr.h"
#include "bn_sprite_shape_size.h"
#include "bn_sprite_tiles_item.h"
#include "bn_sprite_tiles_ptr.h"
#include "bn_tile.h"
#include "bn_vector.h"

#include "animazione_battaglia.h"
#include "audio.h"
#include "battaglia_grafica.h"
#include "game_state.h"
#include "progressione.h"
#include "negozio.h"
#include "storia_logica.h"
#include "tabella.h"
#include "scheda_mosse.h"
#include "vista_battaglia.h"
#include "vista_menu.h"
#include "stile/cornice.h"
#include "vista_testo.h"

namespace gubbio
{

namespace
{
    using namespace battaglia;
    using testo::Contesto;
    using testo::TestoId;
    namespace G = battaglia::grafica;

    // Una sola battaglia a schermo, riavviata sul posto: sta in EWRAM, non sullo stack.
    constinit BN_DATA_EWRAM Battaglia g_scena(0, 1);

    namespace A = battaglia::animazione;

    constexpr int FILE = 3;
    constexpr int Y_FILA[FILE] = { -58, -30, -2 };     // centri degli sprite, sopra il pannello
    // L'ordine dei tre (regola di Cioti, 4 nov 2026): Ubaldo al centro e davanti, Giorgio secondo,
    // Antonio terzo. Nell'ordine degli eroi (UBALDO, GIORGIO, ANTONIO): la fila e il posto.
    constexpr int FILA_EROE[EROI] = { 1, 0, 2 };
    constexpr int X_EROI[EROI] = { -34, -46, -50 };     // a destra delle targhe (barre e PV)
    constexpr int X_NEMICI[FILE] = { 54, 64, 54 };     // i nemici sfalsati: quello di mezzo piu' indietro
    constexpr int X_CORRADO = 40;
    constexpr int X_BARRA_EROE = -100;
    constexpr int X_BARRA_NEMICO = 100;
    constexpr int LARGHEZZA_BARRA = 30;                 // pixel pieni possibili, dentro il bordo
    constexpr int INCHIOSTRO_CHIARO = 2;                // sulla scena (numeri, IMMUNE, targhe)
    constexpr int INCHIOSTRO_CONTORNO = 1;              // il contorno scuro dei numeri sulla scena (STANDARD C6)
    // La targa di un Santo, a sinistra della sua fila: la barra dei PV, sotto quella del Fervore (il bordo
    // in comune), e i PV in cifre a destra delle barre, alla loro altezza.
    constexpr int TARGA_PV_DY = -4;
    constexpr int TARGA_FERVORE_DY = 1;
    constexpr int TARGA_CIFRE_X = 120 + -100 + 19;      // subito a destra delle barre
    constexpr int TARGA_CIFRE_DY = -11;                 // le cifre (righe 2-8 del glifo) accanto alla barra dei PV
    constexpr int PANNELLO_Y = 104;                     // il pannello dei comandi: il riquadro del dialogo della Guida
    constexpr int INCHIOSTRO_SCURO = 1;                 // sul fondo chiaro del riquadro
    // Le tre righe del pannello dentro la cornice (interno x 8-231, y 112-151), con 4 px di respiro dal
    // piombo come i dialoghi: titolo, voce rientrata, aiuto.
    constexpr int PANNELLO_X = 12;
    constexpr int PANNELLO_TITOLO_Y = PANNELLO_Y + 12;
    constexpr int PANNELLO_VOCE_Y = PANNELLO_Y + 23;
    constexpr int PANNELLO_AIUTO_Y = PANNELLO_Y + 35;
    constexpr int FRAME_ESITO = 150;
    constexpr int FRAME_LIVELLO = 75;
    constexpr int FRECCIA_Y_MIN = -72;                  // la freccia del bersaglio resta tutta sullo schermo

    // Indici della palette dei Santi usati dalle barre (tools/genera_battaglia.py).
    constexpr int BARRA_BORDO = 1;
    constexpr int BARRA_VUOTA = 7;
    constexpr int BARRA_PV = 9;
    constexpr int BARRA_FERVORE = 5;

    struct Colori
    {
        bn::color colori[16];
    };

    constexpr Colori colori(const uint16_t (&parole)[16])
    {
        Colori c;

        for(int i = 0; i < 16; ++i)
        {
            c.colori[i] = bn::color(GUBBIO_VOCE(parole, i));
        }

        return c;
    }

    // i fondali (tools/fondali_battaglia.py): ognuno con la sua palette; l'incontro sceglie il suo (FONDALE_DI)
    constexpr Colori COLORI_SFONDO[G::FONDALI] = {
        colori(GUBBIO_VOCE(G::PALETTE_SFONDO, 0)), colori(GUBBIO_VOCE(G::PALETTE_SFONDO, 1)), colori(GUBBIO_VOCE(G::PALETTE_SFONDO, 2)),
        colori(GUBBIO_VOCE(G::PALETTE_SFONDO, 3)), colori(GUBBIO_VOCE(G::PALETTE_SFONDO, 4)) };
    static_assert(G::FONDALI == 5, "COLORI_SFONDO: una voce per fondale");
    constexpr Colori COLORI_SANTI = colori(G::PALETTE_SANTI);
    constexpr Colori COLORI_EFFETTI = colori(G::PALETTE_EFFETTI);
    // i lampi, nell'ordine di animazione::Lampo (NESSUNO escluso)
    constexpr Colori COLORI_LAMPI[3] = {
        colori(G::PALETTE_LAMPO_BIANCO), colori(G::PALETTE_LAMPO_FUOCO), colori(G::PALETTE_LAMPO_LUCE) };

    // Una figura della battaglia (tools/sagome_battaglia.py): le sue pose, una dopo l'altra, e la sua
    // palette; l'effetto del suo colpo.
    struct Figura
    {
        const bn::tile* tile;
        int tile_per_posa;
        int lato;
        Colori colori;
        A::Effetto colpo;
        bool mischia;       // colpisce da vicino: corre fino al bersaglio (no la balestra, no il fuoco)
    };

    constexpr Figura FIGURE_SANTI[EROI] = {
        { G::SPRITE_UBALDO, G::TILE_PER_POSA_UBALDO, G::LATO_UBALDO, colori(G::PALETTE_UBALDO), A::Effetto::SCINTILLA, true },
        { G::SPRITE_GIORGIO, G::TILE_PER_POSA_GIORGIO, G::LATO_GIORGIO, colori(G::PALETTE_GIORGIO), A::Effetto::SCIA, true },
        { G::SPRITE_ANTONIO, G::TILE_PER_POSA_ANTONIO, G::LATO_ANTONIO, colori(G::PALETTE_ANTONIO), A::Effetto::FIAMMA, false },
    };

    // Il Giudizio della Verga: con il Fervore il colpo di Ubaldo diventa la colonna di luce.
    constexpr A::Effetto COLPO_FORTE_SANTI[EROI] = { A::Effetto::RAGGIO, A::Effetto::SCIA, A::Effetto::FIAMMA };

    // Nell'ordine di NemicoId.
    constexpr Figura FIGURE_NEMICI[int(NemicoId::CONTEGGIO)] = {
        { G::SPRITE_FANTE, G::TILE_PER_POSA_FANTE, G::LATO_FANTE, colori(G::PALETTE_FANTE), A::Effetto::SCIA, true },
        { G::SPRITE_BALESTRIERE, G::TILE_PER_POSA_BALESTRIERE, G::LATO_BALESTRIERE, colori(G::PALETTE_BALESTRIERE),
          A::Effetto::SCINTILLA, false },
        { G::SPRITE_CORRADO, G::TILE_PER_POSA_CORRADO, G::LATO_CORRADO, colori(G::PALETTE_CORRADO), A::Effetto::SCINTILLA, true },
        { G::SPRITE_SPIA, G::TILE_PER_POSA_SPIA, G::LATO_SPIA, colori(G::PALETTE_SPIA), A::Effetto::SCIA, true },
        { G::SPRITE_SPETTRO, G::TILE_PER_POSA_SPETTRO, G::LATO_SPETTRO, colori(G::PALETTE_SPETTRO), A::Effetto::SCINTILLA, true },
        { G::SPRITE_GUERRIERO, G::TILE_PER_POSA_GUERRIERO, G::LATO_GUERRIERO, colori(G::PALETTE_GUERRIERO), A::Effetto::SCIA, true },
        { G::SPRITE_INFILTRATO, G::TILE_PER_POSA_INFILTRATO, G::LATO_INFILTRATO, colori(G::PALETTE_INFILTRATO),
          A::Effetto::SCIA, true },
    };

    constexpr TestoId NOMI_SANTI[EROI] = { TestoId::BATT_UBALDO, TestoId::BATT_GIORGIO, TestoId::BATT_ANTONIO };
    constexpr TestoId NOMI_INCONTRI[INCONTRI] = {
        TestoId::BATT_PATTUGLIA, TestoId::BATT_IMBOSCATA, TestoId::BATT_DUELLO, TestoId::BATT_RITO,
        TestoId::BATT_GUERRIERI, TestoId::BATT_FORNACE, TestoId::BATT_INFILTRATO };

    int fondale(int incontro)
    {
        return GUBBIO_VOCE(G::FONDALE_DI, incontro);
    }

    bn::sprite_palette_ptr crea_palette(const Colori& c)
    {
        return bn::sprite_palette_ptr::create(
            bn::sprite_palette_item(bn::span<const bn::color>(c.colori), bn::bpp_mode::BPP_4));
    }

    bn::sprite_tiles_item tiles_di(const Figura& f)
    {
        return bn::sprite_tiles_item(bn::span<const bn::tile>(f.tile, G::POSE_PER_FIGURA * f.tile_per_posa),
                                     bn::bpp_mode::BPP_4, G::POSE_PER_FIGURA);
    }

    // Una barra di 32x8: bordo scuro, i pixel pieni nel colore della barra, il resto grigio. Si
    // ridisegna nei suoi tile solo quando cambia.
    class Barra
    {
    public:
        Barra(int x, int y, int colore, const bn::sprite_palette_ptr& palette) :
            _tiles(bn::sprite_tiles_ptr::allocate(4, bn::bpp_mode::BPP_4)),
            _sprite(bn::sprite_ptr::create(x, y, bn::sprite_shape_size(32, 8), _tiles, palette)),
            _colore(colore)
        {
        }

        void nascondi()
        {
            _sprite.set_visible(false);
        }

        void mostra(int valore, int massimo)
        {
            int n = pieno(valore, massimo, LARGHEZZA_BARRA);

            if(n == _pieni)
            {
                return;
            }

            _pieni = n;
            bn::span<bn::tile> vram = *_tiles.vram();

            for(int k = 0; k < 4; ++k)
            {
                for(int r = 0; r < 8; ++r)
                {
                    uint32_t parola = 0;

                    for(int p = 0; p < 8; ++p)
                    {
                        int x = k * 8 + p;
                        int c = 0;

                        if(r == 1 || r == 6)
                        {
                            c = BARRA_BORDO;
                        }
                        else if(r >= 2 && r <= 5)
                        {
                            c = x == 0 || x == 31 ? BARRA_BORDO : (x - 1 < n ? _colore : BARRA_VUOTA);
                        }

                        parola |= uint32_t(c) << (4 * p);
                    }

                    vram[k].data[r] = parola;
                }
            }
        }

    private:
        bn::sprite_tiles_ptr _tiles;
        bn::sprite_ptr _sprite;
        int _colore;
        int _pieni = -1;
    };

    struct Opzione
    {
        TestoId testo;
        Comando comando;
    };

    void scatta(const char* nome, bool istantanee)
    {
        if(istantanee)
        {
            BN_LOG("Istantanea ", nome);
        }
    }

    // Chi deve fare qualcosa a ogni frame mentre la scena aspetta (le ombre che seguono le figure).
    void (*g_ogni_frame)(void*) = nullptr;
    void* g_ogni_frame_di = nullptr;

    void attendi(int frame)
    {
        for(int f = 0; f < frame; ++f)
        {
            ++g_game_state.frames;

            if(g_ogni_frame)
            {
                g_ogni_frame(g_ogni_frame_di);
            }

            bn::core::update();
        }
    }

    // L'ombra portata sotto i piedi (STANDARD L4, giro 9): un'ellisse scura in trasparenza, che scurisce il
    // suolo del fondale invece di dipingerci sopra del nero; spostata di 3 px a destra (luce da sinistra).
    // Uno sprite 32x8: l'ellisse e' larga 20 px sotto le figure 32x32, 32 sotto Corrado; alta 5.
    constexpr int OMBRA_DX = 3;
    constexpr int OMBRA_ALFA_DECIMI = 5;
    constexpr int OMBRA_MEZZA_RIGA[5] = { 6, 9, 10, 9, 6 };     // mezza larghezza di ogni riga, sotto una figura

    constexpr bool ombra_piena(int x, int y, int larga)
    {
        // x 0-31 nello sprite, y 0-4 nell'ellisse; 'larga' in ventesimi della figura piccola
        return y >= 0 && y < 5 && 2 * (x - 16) + 1 > -2 * OMBRA_MEZZA_RIGA[y] * larga / 20 &&
               2 * (x - 16) + 1 < 2 * OMBRA_MEZZA_RIGA[y] * larga / 20;
    }

    static_assert(ombra_piena(16, 2, 20) && ombra_piena(6, 2, 20) && ! ombra_piena(5, 2, 20) && ! ombra_piena(16, 5, 20));
    static_assert(ombra_piena(0, 2, 32) && ! ombra_piena(0, 2, 20));

    bn::sprite_ptr crea_ombra(int larga, const bn::sprite_palette_ptr& palette)
    {
        bn::sprite_tiles_ptr tiles = bn::sprite_tiles_ptr::allocate(4, bn::bpp_mode::BPP_4);
        bn::span<bn::tile> vram = *tiles.vram();

        for(int t = 0; t < 4; ++t)
        {
            for(int r = 0; r < 8; ++r)
            {
                uint32_t riga = 0;

                for(int c = 0; c < 8; ++c)
                {
                    // l'ellisse nelle righe 2-6: il centro dello sprite (riga 4) sta sui piedi
                    if(ombra_piena(t * 8 + c, r - 2, larga))
                    {
                        riga |= 1u << (c * 4);
                    }
                }

                vram[t].data[r] = riga;
            }
        }

        bn::sprite_ptr ombra = bn::sprite_ptr::create(0, 0, bn::sprite_shape_size(32, 8), bn::move(tiles), palette);
        ombra.set_blending_enabled(true);
        ombra.set_z_order(2);                   // dietro alle figure
        return ombra;
    }

    bn::sprite_palette_ptr crea_palette_ombra()
    {
        bn::color colori[16];
        colori[1] = bn::color(0, 0, 0);
        return bn::sprite_palette_ptr::create(bn::sprite_palette_item(bn::span<const bn::color>(colori),
                                                                      bn::bpp_mode::BPP_4));
    }

    // La schermata delle mosse (include/scheda_mosse.h): nel riquadro del pannello, a sinistra l'elenco delle
    // voci (quattro righe, il cursore della Guida, le frecce se ce ne sono altre), un filo, a destra la scheda
    // della voce scelta: il Santo e il suo Fervore, cosa fa la mossa, il numero (danno, barriera, cura) e il
    // costo. Vive solo mentre si scelgono i comandi: gli sprite tornano liberi per i colpi.
    // Le righe dentro la cornice (interno x 8-231, y 112-151): l'interlinea del font e' 10 px.
    constexpr int MOSSE_RIGA_Y[RIGHE_ELENCO] = { PANNELLO_Y + 8, PANNELLO_Y + 18, PANNELLO_Y + 28, PANNELLO_Y + 38 };
    constexpr int MOSSE_CURSORE_X = 10;
    constexpr int MOSSE_NOMI_X = 18;            // la voce piu' larga e' 84 px: fino a 101
    constexpr int MOSSE_FRECCE_X = 99;          // le frecce dell'elenco, 7 px alla base: 99-105
    constexpr int MOSSE_FILO_X = 107;
    constexpr int MOSSE_SCHEDA_X = 111;
    constexpr int MOSSE_DESTRA_X = 227;
    constexpr int MOSSE_STACCO = 4;             // fra un'etichetta e il suo numero

    static_assert(MOSSE_SCHEDA_X + 116 <= MOSSE_DESTRA_X + 1, "la scheda (contesto SCHEDA, 116 px) sta nella colonna destra");

    [[nodiscard]] TestoId nome_della_voce(const Comando& c)
    {
        switch(c.tipo)
        {

        case TipoComando::CARICA:
            return TestoId::BATT_CARICA;

        case TipoComando::SUPREMA:
            return TestoId::BATT_SUPREMA;

        case TipoComando::OGGETTO:
            return c.oggetto == OggettoId::CRESCIA ? TestoId::BATT_CRESCIA : TestoId::BATT_BISCOTTI;

        default:
            break;
        }

        switch(c.abilita)
        {

        case AbilitaId::GIUDIZIO_DELLA_VERGA:
            return TestoId::BATT_GIUDIZIO;

        case AbilitaId::MURO_DELLA_FEDE:
            return TestoId::BATT_MURO;

        case AbilitaId::FENDENTE_DEL_DRAGO:
            return TestoId::BATT_FENDENTE;

        case AbilitaId::BASTIONE_AZZURRO:
            return TestoId::BATT_BASTIONE;

        case AbilitaId::FUOCO_DI_SANTANTONIO:
            return TestoId::BATT_FUOCO;

        default:
            return TestoId::BATT_ATTACCO;
        }
    }

    [[nodiscard]] TestoId frase_della_voce(const Comando& c)
    {
        switch(c.tipo)
        {

        case TipoComando::CARICA:
            return TestoId::BATT_D_CARICA;

        case TipoComando::SUPREMA:
            return TestoId::BATT_D_SUPREMA;

        case TipoComando::OGGETTO:
            return c.oggetto == OggettoId::CRESCIA ? TestoId::BATT_D_CRESCIA : TestoId::BATT_D_BISCOTTI;

        default:
            break;
        }

        switch(c.abilita)
        {

        case AbilitaId::GIUDIZIO_DELLA_VERGA:
            return TestoId::BATT_D_GIUDIZIO;

        case AbilitaId::MURO_DELLA_FEDE:
            return TestoId::BATT_D_MURO;

        case AbilitaId::FENDENTE_DEL_DRAGO:
            return TestoId::BATT_D_FENDENTE;

        case AbilitaId::BASTIONE_AZZURRO:
            return TestoId::BATT_D_BASTIONE;

        case AbilitaId::FUOCO_DI_SANTANTONIO:
            return TestoId::BATT_D_FUOCO;

        default:
            return TestoId::BATT_D_ATTACCO;
        }
    }

    // Un 8x8 disegnato a righe: 'righe' sono 8 parole da 4 bit per pixel.
    bn::sprite_ptr crea_8x8(const uint32_t (&righe)[8], int x, int y, const bn::sprite_palette_ptr& palette)
    {
        bn::sprite_tiles_ptr tiles = bn::sprite_tiles_ptr::allocate(1, bn::bpp_mode::BPP_4);
        bn::span<bn::tile> vram = *tiles.vram();

        for(int r = 0; r < 8; ++r)
        {
            vram[0].data[r] = righe[r];
        }

        bn::sprite_ptr s = bn::sprite_ptr::create(0, 0, bn::sprite_shape_size(8, 8), bn::move(tiles), palette);
        s.set_bg_priority(PRIORITA_RIQUADRI);
        menu::colloca(s, x, y, 8, 8);
        return s;
    }

    // Una riga di pixel dell'8x8, piena per 'mezza' pixel intorno al 3 (al piu' 0-6).
    constexpr uint32_t riga_freccia(int mezza, int colore)
    {
        uint32_t r = 0;

        for(int p = 3 - mezza; p <= 3 + mezza; ++p)
        {
            r |= uint32_t(colore) << (4 * p);
        }

        return r;
    }

    constexpr uint32_t C = uint32_t(menu::GRIGIO);
    // le frecce dell'elenco (ce ne sono altre sopra, sotto): 7 px alla base, nell'inchiostro delle voci
    constexpr uint32_t I = uint32_t(menu::INCHIOSTRO);
    constexpr uint32_t FRECCIA_SU[8] = { riga_freccia(0, I), riga_freccia(1, I), riga_freccia(2, I), riga_freccia(3, I),
                                         0, 0, 0, 0 };
    constexpr uint32_t FRECCIA_GIU[8] = { 0, 0, 0, 0, riga_freccia(3, I), riga_freccia(2, I), riga_freccia(1, I),
                                          riga_freccia(0, I) };
    constexpr uint32_t FILO[8] = { C, C, C, C, C, C, C, C };     // il pixel 0 di ogni riga

    class PannelloMosse
    {
    public:
        PannelloMosse() :
            _palette(menu::crea_palette()),
            _righe{ VistaTesto(Contesto::DIALOGO, MOSSE_NOMI_X, MOSSE_RIGA_Y[0], menu::INCHIOSTRO, _palette),
                    VistaTesto(Contesto::DIALOGO, MOSSE_NOMI_X, MOSSE_RIGA_Y[1], menu::INCHIOSTRO, _palette),
                    VistaTesto(Contesto::DIALOGO, MOSSE_NOMI_X, MOSSE_RIGA_Y[2], menu::INCHIOSTRO, _palette),
                    VistaTesto(Contesto::DIALOGO, MOSSE_NOMI_X, MOSSE_RIGA_Y[3], menu::INCHIOSTRO, _palette) },
            _cursore(menu::crea_cursore(_palette)),
            _su(crea_8x8(FRECCIA_SU, MOSSE_FRECCE_X, MOSSE_RIGA_Y[0], _palette)),
            _giu(crea_8x8(FRECCIA_GIU, MOSSE_FRECCE_X, MOSSE_RIGA_Y[3] + 1, _palette)),
            _filo{ crea_8x8(FILO, MOSSE_FILO_X, PANNELLO_Y + 8, _palette), crea_8x8(FILO, MOSSE_FILO_X, PANNELLO_Y + 16, _palette),
                   crea_8x8(FILO, MOSSE_FILO_X, PANNELLO_Y + 24, _palette), crea_8x8(FILO, MOSSE_FILO_X, PANNELLO_Y + 32, _palette),
                   crea_8x8(FILO, MOSSE_FILO_X, PANNELLO_Y + 40, _palette) },
            _nome(Contesto::DIALOGO, MOSSE_SCHEDA_X, MOSSE_RIGA_Y[0], menu::TITOLO, _palette),
            _testata(Contesto::HUD, MOSSE_SCHEDA_X, MOSSE_RIGA_Y[0], menu::NOTA, _palette),
            _frase(Contesto::SCHEDA, MOSSE_SCHEDA_X, MOSSE_RIGA_Y[1], menu::INCHIOSTRO, _palette),
            _etichetta(Contesto::HUD, MOSSE_SCHEDA_X, MOSSE_RIGA_Y[3], menu::NOTA, _palette),
            _etichetta_destra(Contesto::HUD, MOSSE_SCHEDA_X, MOSSE_RIGA_Y[3], menu::NOTA, _palette),
            _fervore(0, MOSSE_RIGA_Y[0], menu::INCHIOSTRO, _palette),
            _valore(0, MOSSE_RIGA_Y[3], menu::INCHIOSTRO, _palette),
            _valore_destra(0, MOSSE_RIGA_Y[3], menu::INCHIOSTRO, _palette)
        {
            _fervore.nascondi();
            _valore.nascondi();
            _valore_destra.nascondi();
        }

        // Un altro Santo (o lo stesso, tornato con B): l'elenco si riscrive tutto.
        void nuovo_elenco()
        {
            _prima = -1;
        }

        // L'elenco da 'prima' in giu', la voce 'scelta' col cursore; le voci spente in grigio. Le scritte si
        // rifanno solo quando l'elenco scorre o e' nuovo.
        void elenco(const Voci& v, int prima, int scelta)
        {
            if(prima != _prima)
            {
                _prima = prima;

                for(int r = 0; r < RIGHE_ELENCO; ++r)
                {
                    int i = prima + r;

                    if(i < v.quante)
                    {
                        _righe[r].cambia_inchiostro(v.voce[i].possibile ? menu::INCHIOSTRO : menu::SPENTO);
                        _righe[r].mostra(nome_della_voce(v.voce[i].comando));
                        _righe[r].rivela_tutto();
                    }
                    else
                    {
                        _righe[r].nascondi();
                    }
                }

                _su.set_visible(prima > 0);
                _giu.set_visible(prima + RIGHE_ELENCO < v.quante);
            }

            menu::colloca(_cursore, MOSSE_CURSORE_X, MOSSE_RIGA_Y[scelta - prima] + 1, 8, 8);
            _cursore.set_visible(true);
        }

        // La riga in alto della scheda nel menu: il Santo e il suo Fervore.
        void testata_santo(TestoId nome, int fervore)
        {
            _nome.mostra(nome);
            _nome.rivela_tutto();
            _testata.mostra(TestoId::BATT_L_FERVORE);
            _testata.rivela_tutto();
            _fervore.mostra(fervore);
            _fervore.colloca_a_destra(MOSSE_DESTRA_X, MOSSE_RIGA_Y[0]);
            _testata.sposta(MOSSE_DESTRA_X + 1 - _fervore.larghezza() - MOSSE_STACCO - larghezza_testo(TestoId::BATT_L_FERVORE),
                            MOSSE_RIGA_Y[0]);
        }

        // ... e mentre si sceglie il bersaglio: i tasti.
        void testata_bersaglio()
        {
            _nome.nascondi();
            _fervore.nascondi();
            _testata.mostra(TestoId::BATT_L_BERSAGLIO);
            _testata.rivela_tutto();
            _testata.sposta(MOSSE_SCHEDA_X, MOSSE_RIGA_Y[0]);
        }

        // La scheda: la frase, il numero a sinistra, il costo (o quanti oggetti restano) a destra.
        // 'ne_hai' >= 0 per un oggetto; 'pagabile' false: il costo in vermiglio.
        void scheda(TestoId frase, const Scheda& s, int ne_hai, bool pagabile)
        {
            if(frase != _frase_mostrata)
            {
                _frase_mostrata = frase;
                _frase.mostra(frase);
                _frase.rivela_tutto();
            }

            if(s.cifra == Cifra::NESSUNA)
            {
                _etichetta.nascondi();
                _valore.nascondi();
            }
            else
            {
                TestoId e = s.cifra == Cifra::DANNO ? TestoId::BATT_L_DANNO :
                            (s.cifra == Cifra::BARRIERA ? TestoId::BATT_L_BARRIERA : TestoId::BATT_L_CURA);
                _etichetta.mostra(e);
                _etichetta.rivela_tutto();
                _valore.mostra(s.valore);
                _valore.colloca(MOSSE_SCHEDA_X + larghezza_testo(e) + MOSSE_STACCO, MOSSE_RIGA_Y[3]);
            }

            TestoId destra = ne_hai >= 0 ? TestoId::BATT_L_RIMASTI :
                             (s.costo > 0 ? TestoId::BATT_L_COSTO : TestoId::BATT_L_GRATIS);
            int numero = ne_hai >= 0 ? ne_hai : s.costo;
            _etichetta_destra.mostra(destra);
            _etichetta_destra.rivela_tutto();

            if(destra == TestoId::BATT_L_GRATIS)
            {
                _valore_destra.nascondi();
                _etichetta_destra.sposta(MOSSE_DESTRA_X + 1 - larghezza_testo(destra), MOSSE_RIGA_Y[3]);
                return;
            }

            _valore_destra.cambia_inchiostro(pagabile ? menu::INCHIOSTRO : menu::TITOLO);
            _valore_destra.mostra(numero);
            _valore_destra.colloca_a_destra(MOSSE_DESTRA_X, MOSSE_RIGA_Y[3]);
            _etichetta_destra.sposta(MOSSE_DESTRA_X + 1 - _valore_destra.larghezza() - MOSSE_STACCO - larghezza_testo(destra),
                                     MOSSE_RIGA_Y[3]);
        }

    private:
        bn::sprite_palette_ptr _palette;
        VistaTesto _righe[RIGHE_ELENCO];
        bn::sprite_ptr _cursore;
        bn::sprite_ptr _su;
        bn::sprite_ptr _giu;
        bn::sprite_ptr _filo[5];
        VistaTesto _nome;
        VistaTesto _testata;
        VistaTesto _frase;
        VistaTesto _etichetta;
        VistaTesto _etichetta_destra;
        VistaNumero _fervore;
        VistaNumero _valore;
        VistaNumero _valore_destra;
        TestoId _frase_mostrata = TestoId::BATT_SCEGLI;     // nessuna frase della scheda
        int _prima = -1;
    };

    // La scena vera e propria: gli oggetti di Butano vivono finche' vive lei.
    class Scena
    {
    public:
        Scena(int incontro, Guida guida, const bn::sprite_palette_ptr& palette_testo, bool istantanee,
              GameState* partita) :
            _partita(partita),
            _incontro(incontro),
            _guida(guida),
            _istantanee(istantanee),
            _palette_sfondo(bn::bg_palette_ptr::create(
                bn::bg_palette_item(bn::span<const bn::color>(GUBBIO_VOCE(COLORI_SFONDO, fondale(incontro)).colori),
                                    bn::bpp_mode::BPP_4))),
            _tiles_sfondo(bn::regular_bg_tiles_ptr::create(bn::regular_bg_tiles_item(
                bn::span<const bn::tile>(GUBBIO_VOCE(G::TILE_SFONDO, fondale(incontro)),
                                         GUBBIO_VOCE(G::TILE_SFONDO_CONTEGGIO, fondale(incontro))),
                bn::bpp_mode::BPP_4))),
            _sfondo(bn::regular_bg_ptr::create(128 - 120, 128 - 80, bn::regular_bg_map_ptr::create(
                bn::regular_bg_map_item(GUBBIO_VOCE(G::SFONDO, fondale(incontro))[0], bn::size(32, 32)),
                _tiles_sfondo, _palette_sfondo))),
            _palette_santi(crea_palette(COLORI_SANTI)),
            _palette_effetti(crea_palette(COLORI_EFFETTI)),
            _lampi{ crea_palette(COLORI_LAMPI[0]), crea_palette(COLORI_LAMPI[1]), crea_palette(COLORI_LAMPI[2]) },
            _effetti_tiles(bn::sprite_tiles_item(bn::span<const bn::tile>(G::SPRITE_EFFETTI, 16 * G::EFFETTI_FOTOGRAMMI),
                                                 bn::bpp_mode::BPP_4, G::EFFETTI_FOTOGRAMMI)),
            _effetto_attore(bn::sprite_ptr::create(0, 0, bn::sprite_shape_size(32, 32), _effetti_tiles.create_tiles(0),
                                                   _palette_effetti)),
            _effetto_bersaglio(bn::sprite_ptr::create(0, 0, bn::sprite_shape_size(32, 32), _effetti_tiles.create_tiles(0),
                                                      _palette_effetti)),
            _titolo(Contesto::DIALOGO, PANNELLO_X, PANNELLO_TITOLO_Y, INCHIOSTRO_SCURO, palette_testo),
            _voce(Contesto::DIALOGO, PANNELLO_X + 8, PANNELLO_VOCE_Y, INCHIOSTRO_SCURO, palette_testo),
            _aiuto(Contesto::DIALOGO, PANNELLO_X, PANNELLO_AIUTO_Y, INCHIOSTRO_SCURO, palette_testo),
            _immune(Contesto::HUD, 120 + X_CORRADO - 20, 80 - 30 - 40, INCHIOSTRO_CHIARO, palette_testo),
            _numero(0, 0, INCHIOSTRO_CHIARO, palette_testo, INCHIOSTRO_CONTORNO),
            _freccia_tiles(bn::sprite_tiles_item(bn::span<const bn::tile>(G::SPRITE_FRECCIA, 2 * G::TILE_PER_POSA_FRECCIA),
                                                 bn::bpp_mode::BPP_4, 2)),
            _freccia(bn::sprite_ptr::create(0, 0, bn::sprite_shape_size(16, 16), _freccia_tiles.create_tiles(0),
                                            _palette_santi))
        {
            _freccia.set_visible(false);
            _effetto_attore.set_visible(false);
            _effetto_bersaglio.set_visible(false);
            _effetto_attore.set_z_order(-2);
            _effetto_bersaglio.set_z_order(-2);
            _numero.nascondi();
            _riquadri.cornice(0, PANNELLO_Y, stile::DIALOGO_COLONNE, stile::DIALOGO_RIGHE);
            int nemici = GUBBIO_VOCE(INCONTRO, incontro).nemici;
            _vista.inizia(g_scena, nemici);

            for(int e = 0; e < EROI; ++e)
            {
                const Figura& f = GUBBIO_VOCE(FIGURE_SANTI, e);
                _figure[e] = tiles_di(f);
                _palette[e] = crea_palette(f.colori);
                _colpo[e] = f.colpo;
                _mischia[e] = f.mischia;
                _x[e] = GUBBIO_VOCE(X_EROI, e);
                _y[e] = GUBBIO_VOCE(Y_FILA, GUBBIO_VOCE(FILA_EROE, e));
                _sprite[e] = bn::sprite_ptr::create(_x[e], _y[e], bn::sprite_shape_size(f.lato, f.lato),
                                                    _figure[e]->create_tiles(0), *_palette[e]);
                _pv.emplace_back(X_BARRA_EROE, _y[e] + TARGA_PV_DY, BARRA_PV, _palette_santi);
                _fervore.emplace_back(X_BARRA_EROE, _y[e] + TARGA_FERVORE_DY, BARRA_FERVORE, _palette_santi);
                // i PV in cifre accanto alle barre, col contorno scuro: si leggono su ogni fondale
                _numeri_pv.emplace_back(TARGA_CIFRE_X, 80 + _y[e] + TARGA_CIFRE_DY, INCHIOSTRO_CHIARO, palette_testo,
                                        INCHIOSTRO_CONTORNO);
            }

            for(int n = 0; n < nemici; ++n)
            {
                int s = EROI + n;
                const Figura& f = GUBBIO_VOCE(FIGURE_NEMICI, int(GUBBIO_VOCE(INCONTRO, incontro).schieramento[n]));
                _figure[s] = tiles_di(f);
                _palette[s] = crea_palette(f.colori);
                _colpo[s] = f.colpo;
                _mischia[s] = f.mischia;
                bool grande = f.lato > 32;
                _x[s] = grande ? X_CORRADO : GUBBIO_VOCE(X_NEMICI, n);
                _y[s] = grande ? GUBBIO_VOCE(Y_FILA, 1) : GUBBIO_VOCE(Y_FILA, n);
                _sprite[s] = bn::sprite_ptr::create(_x[s], _y[s], bn::sprite_shape_size(f.lato, f.lato),
                                                    _figure[s]->create_tiles(0), *_palette[s]);
                _pv.emplace_back(X_BARRA_NEMICO, _y[s] + (grande ? 0 : 6), BARRA_PV, _palette_santi);
            }

            aggiorna_barre();

            // chi non e' nel gruppo non si vede: ne' figura, ne' barre, ne' PV in cifre
            for(int e = 0; e < EROI; ++e)
            {
                if(g_scena.eroe(e).pv_max > 0 && ! g_scena.eroe(e).vivo())
                {
                    _sprite[e]->set_visible(false);
                    _pv[e].nascondi();
                    _fervore[e].nascondi();
                    _numeri_pv[e].nascondi();
                }
            }

            // le ombre sotto i piedi, che seguono le figure a ogni frame
            bn::blending::set_transparency_alpha(bn::fixed(OMBRA_ALFA_DECIMI) / 10);

            for(int s = 0; s < SLOT_VISTA; ++s)
            {
                if(_sprite[s])
                {
                    _ombra[s] = crea_ombra(_sprite[s]->shape_size().width() > 32 ? 32 : 20, _palette_ombra);
                }
            }

            segui_le_ombre();
            g_ogni_frame = [](void* scena) { static_cast<Scena*>(scena)->segui_le_ombre(); };
            g_ogni_frame_di = this;
        }

        ~Scena()
        {
            g_ogni_frame = nullptr;
            g_ogni_frame_di = nullptr;
            bn::blending::set_transparency_alpha(1);
        }

        Scena(const Scena&) = delete;
        Scena& operator=(const Scena&) = delete;

        // L'ombra resta sul suolo (la fila della figura) e segue solo la x: chi corre all'attacco se la porta
        // dietro, chi sobbalza o cade non la stacca da terra.
        void segui_le_ombre()
        {
            for(int s = 0; s < SLOT_VISTA; ++s)
            {
                if(_ombra[s] && _sprite[s])
                {
                    int piedi = _y[s] + _sprite[s]->shape_size().height() / 2 - 2;
                    _ombra[s]->set_position(_sprite[s]->x().integer() + OMBRA_DX, piedi);
                    _ombra[s]->set_visible(_sprite[s]->visible());
                }
            }
        }

        Esito gioca(GameState* partita)
        {
            bool colpo_fotografato = false;
            bool immune_fotografato = false;

            while(true)
            {
                g_scena.avanza();       // SCELTA_COMANDI: il pilota sceglie

                if(_guida == Guida::GIOCATORE)
                {
                    scegli_comandi();
                }
                else if(_istantanee && g_scena.firma().round == 1)
                {
                    istantanea_mosse();
                }

                g_scena.avanza();       // CODA
                g_scena.avanza();       // ESECUZIONE
                g_scena.avanza();       // FINE_ROUND

                for(int i = 0; i < g_scena.eventi_round(); ++i)
                {
                    const Evento& evento = g_scena.evento(i);
                    Mossa m = _vista.consuma(evento);
                    consuma_oggetto(evento);
                    audio::evento(evento);
                    aggiorna_barre();
                    bool fotografa = false;

                    if(m.gesto == Gesto::COLPO && ! colpo_fotografato)
                    {
                        colpo_fotografato = true;
                        fotografa = true;
                    }

                    if(m.gesto == Gesto::IMMUNE && ! immune_fotografato)
                    {
                        immune_fotografato = true;
                        fotografa = true;
                    }

                    // chi spende Fervore colpisce forte finche' agisce lui
                    if(evento.kind == EventKind::FERVOR_SPEND)
                    {
                        _forte_di = slot_vista(evento.attore_nemico, evento.attore);
                    }
                    else if(m.attore >= 0 && m.attore != _forte_di)
                    {
                        _forte_di = -1;
                    }

                    anima(m, fotografa);
                }

                // le istantanee prese, il resto dello scontro (col pilota) va spedito
                _veloce = _istantanee && colpo_fotografato && (immune_fotografato || _incontro != 2);

                if(! g_scena.avanza())  // ESITO
                {
                    break;
                }
            }

            Esito esito = g_scena.firma().esito;
            _titolo.mostra(esito == Esito::VITTORIA ? TestoId::BATT_VITTORIA :
                           (esito == Esito::SCONFITTA ? TestoId::BATT_SCONFITTA : TestoId::BATT_PARITA));
            _titolo.rivela_tutto();
            _voce.nascondi();
            _aiuto.nascondi();
            audio::fine_battaglia(esito == Esito::VITTORIA);
            // l'esperienza dello scontro vinto, e chi sale di livello
            if(esito == Esito::VITTORIA && partita)
            {
                bool saliti[EROI] = {};
                progressione::assegna_esperienza(*partita, _incontro, saliti);
                negozio::assegna_denari(*partita, _incontro);
                constexpr TestoId SALE[EROI] = { TestoId::BATT_SALE_UBALDO, TestoId::BATT_SALE_GIORGIO,
                                                 TestoId::BATT_SALE_ANTONIO };

                for(int e = 0; e < EROI; ++e)
                {
                    if(saliti[e])
                    {
                        audio::suona(colonna::Suono::LIVELLO);
                        _voce.mostra(GUBBIO_VOCE(SALE, e));
                        _voce.rivela_tutto();
                        aspetta(FRAME_LIVELLO);
                    }
                }
            }

            aspetta(30);
            scatta(nome_istantanea("esito"), _istantanee);

            for(int f = 0; f < FRAME_ESITO && ! (_guida == Guida::GIOCATORE && bn::keypad::a_pressed()); ++f)
            {
                aspetta(1);
            }

            return esito;
        }

    private:
        GameState* _partita;
        int _riservati[int(OggettoId::CONTEGGIO)] = {};     // oggetti gia' scelti in questo round
        int _incontro;
        Guida _guida;
        bool _istantanee;
        bool _veloce = false;
        bn::bg_palette_ptr _palette_sfondo;
        bn::regular_bg_tiles_ptr _tiles_sfondo;
        bn::regular_bg_ptr _sfondo;
        bn::sprite_palette_ptr _palette_santi;
        bn::sprite_palette_ptr _palette_effetti;
        bn::sprite_palette_ptr _lampi[3];
        bn::sprite_tiles_item _effetti_tiles;
        bn::sprite_ptr _effetto_attore;
        bn::sprite_ptr _effetto_bersaglio;
        VistaTesto _titolo;
        VistaTesto _voce;
        VistaTesto _aiuto;
        VistaTesto _immune;
        VistaNumero _numero;            // i numeri sulla scena (danni, cure)
        Riquadri _riquadri;             // il pannello: la cornice della Guida sopra il fondale
        bn::sprite_tiles_item _freccia_tiles;
        bn::sprite_ptr _freccia;
        bn::vector<VistaNumero, EROI> _numeri_pv;
        int _pv_scritti[EROI] = { -1, -1, -1 };
        VistaBattaglia _vista;
        bn::optional<bn::sprite_tiles_item> _figure[SLOT_VISTA];
        bn::optional<bn::sprite_ptr> _sprite[SLOT_VISTA];
        bn::sprite_palette_ptr _palette_ombra = crea_palette_ombra();
        bn::optional<bn::sprite_ptr> _ombra[SLOT_VISTA];
        bn::optional<bn::sprite_palette_ptr> _palette[SLOT_VISTA];
        A::Effetto _colpo[SLOT_VISTA] = {};
        bool _mischia[SLOT_VISTA] = {};
        bool _occupato[SLOT_VISTA] = {};    // chi sta recitando un gesto non respira da solo
        int _tick = 0;
        int _forte_di = -1;                 // chi ha appena speso Fervore: i suoi colpi sono forti
        int _x[SLOT_VISTA] = {};
        int _y[SLOT_VISTA] = {};
        bn::vector<Barra, SLOT_VISTA> _pv;
        bn::vector<Barra, EROI> _fervore;
        char _nome[32] = {};

        const char* nome_istantanea(const char* momento)
        {
            const char* prefisso = "battaglia_";
            int k = 0;

            for(const char* c = prefisso; *c; ++c)
            {
                _nome[k++] = *c;
            }

            _nome[k++] = char('0' + _incontro);
            _nome[k++] = '_';

            for(const char* c = momento; *c && k < 31; ++c)
            {
                _nome[k++] = *c;
            }

            _nome[k] = 0;
            return _nome;
        }

        void aggiorna_barre()
        {
            for(int s = 0; s < _pv.size(); ++s)
            {
                _pv[s].mostra(_vista.pv(s), _vista.pv_max(s));
            }

            for(int e = 0; e < EROI; ++e)
            {
                _fervore[e].mostra(_vista.fervore(e), _vista.fervore_max(e));

                if(_pv_scritti[e] != _vista.pv(e))
                {
                    _pv_scritti[e] = _vista.pv(e);
                    _numeri_pv[e].mostra(_vista.pv(e));
                }
            }
        }

        // L'oggetto si toglie dall'inventario quando il suo effetto arriva a schermo, non quando si
        // sceglie: chi cade prima di agire non lo spreca.
        void consuma_oggetto(const Evento& e)
        {
            OggettoId usato = e.kind == EventKind::CURA ? OggettoId::CRESCIA : OggettoId::BISCOTTI;

            if(! _partita || (e.kind != EventKind::CURA && e.kind != EventKind::PURIFICA))
            {
                return;
            }

            uint8_t& quanti = _partita->oggetti[int(usato)];
            quanti = quanti > 0 ? uint8_t(quanti - 1) : 0;
        }

        [[nodiscard]] int disponibili(OggettoId o) const
        {
            return _partita ? _partita->oggetti[int(o)] - _riservati[int(o)] : 0;
        }

        // La posa di una figura; LIBERA e' il respiro (o la figura in ginocchio, se e' un eroe caduto).
        void posa(int s, A::Posa p)
        {
            if(p == A::Posa::LIBERA)
            {
                p = _vista.caduto(s) ? A::Posa::CADUTO : A::respiro(_tick, s);
            }

            _sprite[s]->set_tiles(*_figure[s], int(p));
        }

        void lampo(int s, A::Lampo l)
        {
            _sprite[s]->set_palette(l == A::Lampo::NESSUNO ? *_palette[s] : _lampi[int(l) - 1]);
        }

        // Un effetto sopra una figura: centrato sulla figura, coi piedi allineati; specchiato se viene
        // da un nemico.
        void effetto(bn::sprite_ptr& sprite, int s, A::Effetto e, int fotogramma, bool specchiato, int dx, int dy)
        {
            if(e == A::Effetto::NESSUNO || s < 0)
            {
                sprite.set_visible(false);
                return;
            }

            int piedi = _y[s] + _sprite[s]->shape_size().height() / 2;
            sprite.set_tiles(_effetti_tiles, (int(e) - 1) * A::FOTOGRAMMI_EFFETTO + fotogramma);
            sprite.set_position(_x[s] + dx, piedi - 16 + dy);
            sprite.set_horizontal_flip(specchiato);
            sprite.set_visible(true);
        }

        // Chi non recita respira; un eroe caduto resta in ginocchio, un nemico caduto non c'e' piu'.
        void respira()
        {
            for(int s = 0; s < SLOT_VISTA; ++s)
            {
                if(_sprite[s] && ! _occupato[s] && _sprite[s]->visible())
                {
                    posa(s, A::Posa::LIBERA);
                }
            }
        }

        void aspetta(int frame)
        {
            for(int f = 0; f < frame; ++f)
            {
                ++_tick;
                respira();
                attendi(1);
            }
        }

        void nascondi_menu()
        {
            _titolo.nascondi();
            _voce.nascondi();
            _aiuto.nascondi();
        }

        // I comandi dei Santi vivi, uno per volta, nella schermata delle mosse. B torna al Santo prima.
        void scegli_comandi()
        {
            for(int& r : _riservati)
            {
                r = 0;
            }

            nascondi_menu();
            PannelloMosse pannello;
            Comando scelti[EROI];
            int e = 0;

            while(e < EROI)
            {
                if(! g_scena.eroe(e).vivo())
                {
                    ++e;
                    continue;
                }

                int prima = e - 1;

                while(prima >= 0 && ! g_scena.eroe(prima).vivo())
                {
                    --prima;
                }

                Comando comando;

                if(scegli_per(e, prima >= 0, pannello, comando))
                {
                    if(comando.tipo == TipoComando::OGGETTO)
                    {
                        _riservati[int(comando.oggetto)] += 1;
                    }

                    g_scena.imposta_comando(e, comando);
                    scelti[e] = comando;
                    ++e;
                }
                else
                {
                    // indietro: il Santo prima rifa' la sua scelta, e l'oggetto che aveva promesso torna libero
                    if(scelti[prima].tipo == TipoComando::OGGETTO)
                    {
                        _riservati[int(scelti[prima].oggetto)] -= 1;
                    }

                    e = prima;
                }

                aspetta(1);
            }
        }

        [[nodiscard]] Voci voci_di(int e) const
        {
            int scorte[OGGETTI_IN_BATTAGLIA] = {};

            for(int k = 0; k < OGGETTI_IN_BATTAGLIA; ++k)
            {
                scorte[k] = disponibili(GUBBIO_VOCE(OGGETTI_USABILI, k));
            }

            return voci_del_menu(g_scena, e, scorte);
        }

        // La scheda di una voce del menu, senza bersaglio scelto.
        void mostra_voce(PannelloMosse& pannello, int e, const Voce& v)
        {
            const Comando& c = v.comando;
            Scheda s = scheda_del_comando(g_scena, e, c, -1);
            bool oggetto = c.tipo == TipoComando::OGGETTO;
            TestoId frase = v.possibile ? frase_della_voce(c) : (oggetto ? TestoId::BATT_N_NONUSA : TestoId::BATT_N_FERVORE);
            pannello.scheda(frase, s, oggetto ? disponibili(c.oggetto) : -1, oggetto || g_scena.eroe(e).fervore >= s.costo);
        }

        // Il comando del Santo 'e': true se l'ha scelto, false se ha premuto B per tornare al Santo prima
        // ('indietro': ce n'e' uno).
        bool scegli_per(int e, bool indietro, PannelloMosse& pannello, Comando& comando)
        {
            Voci voci = voci_di(e);
            int scelta = 0;
            int prima = 0;
            bool scelto = false;
            pannello.nuovo_elenco();

            while(true)
            {
                pannello.elenco(voci, prima, scelta);
                pannello.testata_santo(GUBBIO_VOCE(NOMI_SANTI, e), g_scena.eroe(e).fervore);
                mostra_voce(pannello, e, voci.voce[scelta]);
                bool premuto_a = false;

                for(int f = 0; ; ++f)
                {
                    if(bn::keypad::down_pressed() || bn::keypad::up_pressed())
                    {
                        int passo = bn::keypad::down_pressed() ? 1 : voci.quante - 1;
                        scelta = (scelta + passo) % voci.quante;
                        prima = prima_visibile(prima, scelta, voci.quante);
                        audio::suona(colonna::Suono::CURSORE);
                        pannello.elenco(voci, prima, scelta);
                        mostra_voce(pannello, e, voci.voce[scelta]);
                    }

                    if(bn::keypad::a_pressed())
                    {
                        // una voce spenta non si sceglie: la scheda dice gia' perche'
                        premuto_a = voci.voce[scelta].possibile;
                        audio::suona(premuto_a ? colonna::Suono::CONFERMA : colonna::Suono::ANNULLA);

                        if(premuto_a)
                        {
                            break;
                        }
                    }

                    if(bn::keypad::b_pressed() && indietro)
                    {
                        audio::suona(colonna::Suono::ANNULLA);
                        break;
                    }

                    // chi sceglie dondola, per dire di chi e' il turno
                    _sprite[e]->set_y(_y[e] - ((f / 16) % 2));
                    aspetta(1);
                }

                aspetta(1);

                if(! premuto_a)
                {
                    break;
                }

                comando = voci.voce[scelta].comando;

                if(scegli_bersaglio(e, comando, pannello))
                {
                    scelto = true;
                    break;
                }
            }

            _sprite[e]->set_y(_y[e]);
            return scelto;
        }

        // La scheda sul bersaglio puntato: il danno su di lui (o la barriera, la cura) e la sua nota.
        void mostra_bersaglio(PannelloMosse& pannello, int e, const Comando& comando, int scelto)
        {
            Scheda s = scheda_del_comando(g_scena, e, comando, scelto);
            TestoId frase = s.nota == Nota::DEBOLE ? TestoId::BATT_N_DEBOLE :
                            (s.nota == Nota::RESISTE ? TestoId::BATT_N_RESISTE :
                             (s.nota == Nota::IMMUNE ? TestoId::BATT_N_IMMUNE : frase_della_voce(comando)));
            bool oggetto = comando.tipo == TipoComando::OGGETTO;
            pannello.scheda(frase, s, oggetto ? disponibili(comando.oggetto) : -1, true);
        }

        // Il bersaglio del comando, se il comando ne sceglie uno: la freccia sopra, su e giu' la
        // spostano fra i vivi (include/vista_battaglia.h), A conferma, B torna alla scelta del comando.
        bool scegli_bersaglio(int eroe, Comando& comando, PannelloMosse& pannello)
        {
            Puntamento mira = mira_del_comando(comando);

            if(mira == Puntamento::NESSUNO)
            {
                return true;
            }

            int scelto = bersaglio_predefinito(g_scena, mira);
            pannello.testata_bersaglio();
            mostra_bersaglio(pannello, eroe, comando, scelto);
            bool confermato = false;

            for(int f = 0; ; ++f)
            {
                if(bn::keypad::down_pressed() || bn::keypad::up_pressed())
                {
                    scelto = prossimo_bersaglio(g_scena, mira, scelto, bn::keypad::down_pressed() ? 1 : -1);
                    audio::suona(colonna::Suono::CURSORE);
                    mostra_bersaglio(pannello, eroe, comando, scelto);
                }

                if(bn::keypad::a_pressed() || bn::keypad::b_pressed())
                {
                    confermato = bn::keypad::a_pressed();
                    audio::suona(confermato ? colonna::Suono::CONFERMA : colonna::Suono::ANNULLA);
                    break;
                }

                punta(scelto, mira, f);
                _sprite[eroe]->set_y(_y[eroe] - ((f / 16) % 2));
                aspetta(1);
            }

            _freccia.set_visible(false);
            aspetta(1);

            if(confermato)
            {
                comando.bersaglio = scelto;
            }

            return confermato;
        }

        // La freccia sopra il bersaglio puntato, che pulsa.
        void punta(int scelto, Puntamento mira, int f)
        {
            int s = slot_vista(mira == Puntamento::NEMICO, scelto);
            int alto = (_sprite[s]->shape_size().height()) / 2;
            _freccia.set_position(_x[s], bn::max(_y[s] - alto - 6, FRECCIA_Y_MIN));
            _freccia.set_tiles(_freccia_tiles, (f / 12) % 2);
            _freccia.set_visible(true);
        }

        // Le istantanee (GUBBIO_AVVIO=5): la schermata delle mosse di Ubaldo, come la vede il giocatore, prima
        // nel menu sul Giudizio della Verga e poi sul bersaglio.
        void istantanea_mosse()
        {
            PannelloMosse pannello;
            Voci voci = voci_di(UBALDO);
            pannello.nuovo_elenco();
            pannello.elenco(voci, 0, 1);
            pannello.testata_santo(GUBBIO_VOCE(NOMI_SANTI, UBALDO), g_scena.eroe(UBALDO).fervore);
            mostra_voce(pannello, UBALDO, voci.voce[1]);
            aspetta(20);
            scatta(nome_istantanea("menu"), true);
            int scelto = bersaglio_predefinito(g_scena, Puntamento::NEMICO);
            pannello.testata_bersaglio();
            mostra_bersaglio(pannello, UBALDO, voci.voce[1].comando, scelto);
            punta(scelto, Puntamento::NEMICO, 0);
            aspetta(20);
            scatta(nome_istantanea("bersaglio"), true);
            aspetta(20);
            _freccia.set_visible(false);
        }

        // Lo stile di un gesto: l'effetto del colpo di chi agisce, forte se ha appena speso Fervore (un'abilita',
        // la Suprema) o se e' Corrado; chi cade resta a terra se e' un eroe.
        [[nodiscard]] A::Stile stile_di(const Mossa& m) const
        {
            A::Stile st;

            if(m.attore >= 0)
            {
                bool fervore = m.attore == _forte_di;
                st.forte = fervore || _sprite[m.attore]->shape_size().width() > 32;
                st.colpo = fervore && m.attore < EROI ? GUBBIO_VOCE(COLPO_FORTE_SANTI, m.attore) : _colpo[m.attore];
            }

            st.resta_a_terra = m.bersaglio >= 0 && m.bersaglio < EROI;

            // chi tira da lontano manda il colpo in volo: il fuoco di Antonio, il verrettone della balestra
            if(m.attore >= 0 && m.bersaglio >= 0 && m.attore != m.bersaglio && ! _mischia[m.attore] &&
               (m.gesto == Gesto::COLPO || m.gesto == Gesto::IMMUNE))
            {
                st.proiettile = _colpo[m.attore] == A::Effetto::FIAMMA ? A::Effetto::FIAMMA : A::Effetto::DARDO;
            }

            return st;
        }

        // Il punto della corsa: 'avanti' fino ad AVANZATA e' la frazione del tragitto da 'da' a 'meta', oltre
        // sono pixel in piu' nel verso del colpo (l'affondo).
        [[nodiscard]] static int lungo_la_corsa(int da, int meta, int avanti, int verso)
        {
            if(avanti <= A::AVANZATA)
            {
                return da + (meta - da) * avanti / A::AVANZATA;
            }

            return meta + verso * (avanti - A::AVANZATA);
        }

        // Un evento a schermo, fotogramma per fotogramma dalla tabella di include/animazione_battaglia.h:
        // chi agisce fa il passo, carica, colpisce e torna; chi subisce lampeggia, arretra, cade.
        void anima(const Mossa& m, bool fotografa)
        {
            A::Stile stile = stile_di(m);
            int durata = A::durata(m.gesto, stile);
            int da = _veloce ? durata - 1 : 0;
            int verso = m.attore >= EROI ? -1 : 1;          // verso il nemico di chi agisce
            int via = m.bersaglio >= EROI ? 1 : -1;         // lontano da chi colpisce
            bool colpo = m.gesto == Gesto::COLPO || m.gesto == Gesto::IMMUNE;
            int scatto_foto = colpo ? A::impatto(stile) + 1 : 12;
            bool su_se_stesso = m.attore == m.bersaglio;
            // Dove arriva il passo: chi colpisce da vicino corre fino davanti al bersaglio, coi piedi alla
            // sua altezza; chi colpisce da lontano (la balestra, il fuoco, la luce della Verga) fa un passo.
            int meta_x = m.attore >= 0 ? _x[m.attore] + verso * A::AVANZATA : 0;
            int meta_y = m.attore >= 0 ? _y[m.attore] : 0;

            if(colpo && m.attore >= 0 && m.bersaglio >= 0 && _mischia[m.attore] &&
               ! (m.attore == UBALDO && stile.colpo == A::Effetto::RAGGIO))
            {
                int lato_a = _sprite[m.attore]->shape_size().width();
                int lato_b = _sprite[m.bersaglio]->shape_size().width();
                meta_x = _x[m.bersaglio] - verso * (lato_b / 4 + lato_a / 4 + 6);
                meta_y = _y[m.bersaglio] + (lato_b - lato_a) / 2;
            }

            if(m.attore >= 0)
            {
                _occupato[m.attore] = true;
            }

            if(m.bersaglio >= 0 && _sprite[m.bersaglio])
            {
                _occupato[m.bersaglio] = true;
            }

            if(m.gesto == Gesto::IMMUNE)
            {
                _immune.mostra(TestoId::BATT_IMMUNE);
                _immune.rivela_tutto();
                _titolo.mostra(TestoId::BATT_INDIZIO);
                _titolo.rivela_tutto();
            }

            for(int f = da; f < durata; ++f)
            {
                A::Quadro q = A::quadro(m.gesto, f, stile);

                if(m.attore >= 0)
                {
                    posa(m.attore, q.posa_attore);
                    lampo(m.attore, q.lampo_attore);
                    _sprite[m.attore]->set_x(lungo_la_corsa(_x[m.attore], meta_x, q.avanti_attore, verso));
                    _sprite[m.attore]->set_z_order(-1);
                    if(q.volo >= 0 && m.bersaglio >= 0 && _sprite[m.bersaglio])
                    {
                        // il proiettile: dalla mano di chi tira al petto del bersaglio
                        int a_x = lungo_la_corsa(_x[m.attore], meta_x, q.avanti_attore, verso) + verso * 12;
                        int b_x = _x[m.bersaglio] - verso * 6;
                        int piedi_a = _y[m.attore] + _sprite[m.attore]->shape_size().height() / 2;
                        int piedi_b = _y[m.bersaglio] + _sprite[m.bersaglio]->shape_size().height() / 2;
                        int k = q.volo + 1;
                        effetto(_effetto_attore, m.attore, q.effetto_attore, q.fotogramma_attore, verso < 0,
                                a_x - _x[m.attore] + (b_x - a_x) * k / A::VOLO, (piedi_b - piedi_a) * k / A::VOLO - 6);
                    }
                    else
                    {
                        effetto(_effetto_attore, m.attore, q.effetto_attore, q.fotogramma_attore, false, 0, 0);
                    }
                }

                if(m.bersaglio >= 0 && _sprite[m.bersaglio])
                {
                    // il potere su se stesso (Bastione, Carica) non ha un secondo effetto sopra il primo
                    bool sopra = ! (su_se_stesso && m.gesto == Gesto::POTERE);

                    if(! su_se_stesso)
                    {
                        posa(m.bersaglio, q.posa_bersaglio);
                        lampo(m.bersaglio, q.lampo_bersaglio);
                        _sprite[m.bersaglio]->set_x(_x[m.bersaglio] + via * q.indietro_bersaglio);
                    }

                    _sprite[m.bersaglio]->set_visible(q.bersaglio_visibile);
                    effetto(_effetto_bersaglio, m.bersaglio, sopra ? q.effetto_bersaglio : A::Effetto::NESSUNO,
                            q.fotogramma_bersaglio, verso < 0, 0, 0);
                }

                // il tremito: lo sfondo e le figure, insieme
                _sfondo.set_y(128 - 80 + q.scossa);

                for(int s = 0; s < SLOT_VISTA; ++s)
                {
                    if(_sprite[s])
                    {
                        int y = s == m.attore ? lungo_la_corsa(_y[s], meta_y, bn::min(q.avanti_attore, A::AVANZATA), 0) : _y[s];
                        _sprite[s]->set_y(y + q.scossa);
                    }
                }

                if(m.numero > 0 && q.numero && m.bersaglio >= 0)
                {
                    _numero.mostra(m.numero);
                    _numero.colloca(120 + _x[m.bersaglio] - 8, bn::max(2, 80 + _y[m.bersaglio] - 22 - q.su_numero));
                }

                if(fotografa && f == scatto_foto)
                {
                    scatta(nome_istantanea(m.gesto == Gesto::IMMUNE ? "immune" : "colpo"), _istantanee);
                }

                aspetta(1);
            }

            // tutto torna a posto: chi e' caduto resta giu' (un eroe) o sparisce (un nemico)
            for(int s : { m.attore, m.bersaglio })
            {
                if(s >= 0 && _sprite[s])
                {
                    _occupato[s] = false;
                    lampo(s, A::Lampo::NESSUNO);
                    posa(s, A::Posa::LIBERA);
                    _sprite[s]->set_position(_x[s], _y[s]);
                    _sprite[s]->set_z_order(0);
                    _sprite[s]->set_visible(! _vista.caduto(s) || s < EROI);
                }
            }

            _effetto_attore.set_visible(false);
            _effetto_bersaglio.set_visible(false);
            _sfondo.set_y(128 - 80);
            _numero.nascondi();

            if(m.gesto == Gesto::IMMUNE)
            {
                _immune.nascondi();
                _titolo.nascondi();
            }
        }
    };

    int scegli_incontro(const bn::sprite_palette_ptr& palette_testo)
    {
        Riquadri riquadri;
        riquadri.cornice(0, PANNELLO_Y, stile::DIALOGO_COLONNE, stile::DIALOGO_RIGHE);
        VistaTesto voce(Contesto::DIALOGO, PANNELLO_X, PANNELLO_TITOLO_Y, INCHIOSTRO_SCURO, palette_testo);
        VistaTesto aiuto(Contesto::DIALOGO, PANNELLO_X, PANNELLO_AIUTO_Y, INCHIOSTRO_SCURO, palette_testo);
        int scelta = 0;
        voce.mostra(GUBBIO_VOCE(NOMI_INCONTRI, scelta));
        voce.rivela_tutto();
        aiuto.mostra(TestoId::BATT_SCEGLI);
        aiuto.rivela_tutto();

        while(! bn::keypad::a_pressed())
        {
            if(bn::keypad::down_pressed() || bn::keypad::up_pressed())
            {
                scelta = (scelta + (bn::keypad::down_pressed() ? 1 : INCONTRI - 1)) % INCONTRI;
                voce.mostra(GUBBIO_VOCE(NOMI_INCONTRI, scelta));
                voce.rivela_tutto();
            }

            attendi(1);
        }

        attendi(1);
        return scelta;
    }
}

Esito scena_battaglia(int incontro, uint32_t seme, Guida guida, const bn::sprite_palette_ptr& palette_testo,
                      bool istantanee, GameState* partita)
{
    // i Santi al loro livello, se c'e' una partita; se no al livello 1 (il menu di prova, le istantanee)
    Statistiche eroi[EROI] = {};

    for(int e = 0; e < EROI; ++e)
    {
        int livello = partita ? partita->livello[e] : 1;
        eroi[e] = progressione::statistiche_al_livello(GUBBIO_VOCE(STATISTICHE_EROI, e),
                                                      livello < 1 ? 1 : (livello > progressione::LIVELLO_MAX ?
                                                                         progressione::LIVELLO_MAX : livello));
    }

    // il gruppo della storia (Giorgio dall'ultimatum, Antonio dal Teatro); senza partita, tutti e tre
    uint8_t presenti = partita ? storia::gruppo(*partita, incontro) : TUTTI_PRESENTI;
    // Corrado con uno scudo in meno (Q-SM01 o Rufino), Ubaldo che nel DIGIUNO non mangia
    int scudi_in_meno = partita ? storia::scudi_in_meno(*partita, incontro) : 0;
    uint8_t a_digiuno = partita ? storia::a_digiuno(*partita) : 0;
    // i Ceri risvegliati (A1-08): il Fervore dei Santi parte piu' alto
    bool ceri = partita && storia::ceri_accesi(*partita);
    // e i PV che i miasmi della gola hanno tolto: pesano su questa battaglia, poi si azzerano (storia::guarisci)
    g_scena.ricomincia(incontro, seme, false, eroi, presenti, scudi_in_meno, a_digiuno, partita ? partita->ferite : nullptr,
                       ceri);
    Esito esito;
    audio::battaglia(incontro);

    {
        Scena scena(incontro, guida, palette_testo, istantanee, partita);
        esito = scena.gioca(partita);
    }

    if(partita)
    {
        storia::guarisci(*partita);
    }

    // Butano libera i tile e gli sprite della scena al prossimo aggiornamento: prima di crearne
    // un'altra si lascia passare un frame
    attendi(1);
    return esito;
}

bn::sprite_ptr sprite_sulla_mappa(int incontro)
{
    const Figura& f = GUBBIO_VOCE(FIGURE_NEMICI, int(GUBBIO_VOCE(INCONTRO, incontro).schieramento[0]));
    bn::sprite_tiles_item tiles = tiles_di(f);
    return bn::sprite_ptr::create(0, 0, bn::sprite_shape_size(f.lato, f.lato), tiles.create_tiles(0),
                                  crea_palette(f.colori));
}

void menu_battaglie(const bn::sprite_palette_ptr& palette_testo)
{
    while(true)
    {
        int incontro = scegli_incontro(palette_testo);
        attendi(1);     // i tile del menu tornano liberi prima della scena
        uint32_t seme = uint32_t(g_game_state.frames) | 1u;
        Esito esito = scena_battaglia(incontro, seme, Guida::GIOCATORE, palette_testo);
        BN_LOG("Scontro ", incontro, " seme ", seme, " esito ", int(esito));
    }
}

void istantanee_battaglie(const bn::sprite_palette_ptr& palette_testo)
{
    for(int i = 0; i < INCONTRI; ++i)
    {
        Esito esito = scena_battaglia(i, 1, Guida::PILOTA, palette_testo, true);
        BN_LOG("Scontro ", i, " esito ", int(esito));
    }

    BN_LOG("Istantanee finite");

    while(true)
    {
        bn::core::update();
    }
}

}
