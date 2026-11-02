#include "scena_battaglia.h"

#include "bn_bg_palette_item.h"
#include "bn_bg_palette_ptr.h"
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
#include "bn_vector.h"

#include "battaglia_grafica.h"
#include "game_state.h"
#include "progressione.h"
#include "tabella.h"
#include "vista_battaglia.h"
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

    constexpr int FILE = 3;
    constexpr int Y_FILA[FILE] = { -58, -30, -2 };     // centri degli sprite, sopra il pannello
    constexpr int X_EROE = -64;
    constexpr int X_NEMICO = 56;
    constexpr int X_CORRADO = 40;
    constexpr int X_BARRA_EROE = -100;
    constexpr int X_BARRA_NEMICO = 100;
    constexpr int LARGHEZZA_BARRA = 30;                 // pixel pieni possibili, dentro il bordo
    constexpr int INCHIOSTRO_CHIARO = 2;                // sul pannello scuro e sulla scena
    constexpr int PANNELLO_Y = 104;                     // il pannello dei comandi nello sfondo (genera_battaglia.py)
    constexpr int FRAME_EVENTO = 28;
    constexpr int FRAME_FERVORE = 6;
    constexpr int FRAME_ESITO = 150;
    constexpr int FRAME_LIVELLO = 75;
    constexpr int FRECCIA_Y_MIN = -72;                  // la freccia del bersaglio resta tutta sullo schermo
    constexpr int PASSO_SCATTO = 2;                     // pixel per frame dello scatto verso il bersaglio

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

    constexpr Colori COLORI_SFONDO = colori(G::PALETTE_SFONDO);
    constexpr Colori COLORI_SANTI = colori(G::PALETTE_SANTI);
    constexpr Colori COLORI_NEMICI = colori(G::PALETTE_NEMICI);

    struct Figura
    {
        const bn::tile* tile;
        int tile_per_posa;
        int lato;
    };

    constexpr Figura FIGURE_SANTI[EROI] = {
        { G::SPRITE_UBALDO, G::TILE_PER_POSA_UBALDO, G::LATO_UBALDO },
        { G::SPRITE_GIORGIO, G::TILE_PER_POSA_GIORGIO, G::LATO_GIORGIO },
        { G::SPRITE_ANTONIO, G::TILE_PER_POSA_ANTONIO, G::LATO_ANTONIO },
    };

    // Nell'ordine di NemicoId.
    constexpr Figura FIGURE_NEMICI[int(NemicoId::CONTEGGIO)] = {
        { G::SPRITE_FANTE, G::TILE_PER_POSA_FANTE, G::LATO_FANTE },
        { G::SPRITE_BALESTRIERE, G::TILE_PER_POSA_BALESTRIERE, G::LATO_BALESTRIERE },
        { G::SPRITE_CORRADO, G::TILE_PER_POSA_CORRADO, G::LATO_CORRADO },
        { G::SPRITE_SPIA, G::TILE_PER_POSA_SPIA, G::LATO_SPIA },
    };

    constexpr TestoId NOMI_SANTI[EROI] = { TestoId::BATT_UBALDO, TestoId::BATT_GIORGIO, TestoId::BATT_ANTONIO };
    constexpr TestoId NOMI_INCONTRI[INCONTRI] = {
        TestoId::BATT_PATTUGLIA, TestoId::BATT_IMBOSCATA, TestoId::BATT_DUELLO };

    bn::sprite_palette_ptr crea_palette(const Colori& c)
    {
        return bn::sprite_palette_ptr::create(
            bn::sprite_palette_item(bn::span<const bn::color>(c.colori), bn::bpp_mode::BPP_4));
    }

    bn::sprite_tiles_item tiles_di(const Figura& f)
    {
        return bn::sprite_tiles_item(bn::span<const bn::tile>(f.tile, 2 * f.tile_per_posa), bn::bpp_mode::BPP_4, 2);
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

    void attendi(int frame)
    {
        for(int f = 0; f < frame; ++f)
        {
            ++g_game_state.frames;
            bn::core::update();
        }
    }

    // La scena vera e propria: gli oggetti di Butano vivono finche' vive lei.
    class Scena
    {
    public:
        Scena(int incontro, Guida guida, const bn::sprite_palette_ptr& palette_testo, bool istantanee) :
            _incontro(incontro),
            _guida(guida),
            _istantanee(istantanee),
            _palette_sfondo(bn::bg_palette_ptr::create(
                bn::bg_palette_item(bn::span<const bn::color>(COLORI_SFONDO.colori), bn::bpp_mode::BPP_4))),
            _tiles_sfondo(bn::regular_bg_tiles_ptr::create(bn::regular_bg_tiles_item(
                bn::span<const bn::tile>(G::TILE_SFONDO, G::TILE_SFONDO_CONTEGGIO), bn::bpp_mode::BPP_4))),
            _sfondo(bn::regular_bg_ptr::create(128 - 120, 128 - 80, bn::regular_bg_map_ptr::create(
                bn::regular_bg_map_item(GUBBIO_VOCE(G::SFONDO, incontro)[0], bn::size(32, 32)),
                _tiles_sfondo, _palette_sfondo))),
            _palette_santi(crea_palette(COLORI_SANTI)),
            _palette_nemici(crea_palette(COLORI_NEMICI)),
            _titolo(Contesto::DIALOGO, 8, PANNELLO_Y + 6, INCHIOSTRO_CHIARO, palette_testo),
            _voce(Contesto::DIALOGO, 16, PANNELLO_Y + 20, INCHIOSTRO_CHIARO, palette_testo),
            _aiuto(Contesto::DIALOGO, 8, PANNELLO_Y + 36, INCHIOSTRO_CHIARO, palette_testo),
            _immune(Contesto::HUD, 120 + X_CORRADO - 20, 80 - 30 - 40, INCHIOSTRO_CHIARO, palette_testo),
            _numero(0, 0, INCHIOSTRO_CHIARO, palette_testo),
            _freccia_tiles(bn::sprite_tiles_item(bn::span<const bn::tile>(G::SPRITE_FRECCIA, 2 * G::TILE_PER_POSA_FRECCIA),
                                                 bn::bpp_mode::BPP_4, 2)),
            _freccia(bn::sprite_ptr::create(0, 0, bn::sprite_shape_size(16, 16), _freccia_tiles.create_tiles(0),
                                            _palette_santi))
        {
            _freccia.set_visible(false);
            _numero.nascondi();
            int nemici = GUBBIO_VOCE(INCONTRO, incontro).nemici;
            _vista.inizia(g_scena, nemici);

            for(int e = 0; e < EROI; ++e)
            {
                const Figura& f = GUBBIO_VOCE(FIGURE_SANTI, e);
                _figure[e] = tiles_di(f);
                _x[e] = X_EROE;
                _y[e] = GUBBIO_VOCE(Y_FILA, e);
                _sprite[e] = bn::sprite_ptr::create(_x[e], _y[e], bn::sprite_shape_size(f.lato, f.lato),
                                                    _figure[e]->create_tiles(0), _palette_santi);
                _pv.emplace_back(X_BARRA_EROE, _y[e] - 4, BARRA_PV, _palette_santi);
                _fervore.emplace_back(X_BARRA_EROE, _y[e] + 6, BARRA_FERVORE, _palette_santi);
                // i PV in cifre accanto al Santo, dalla vista come le barre
                _numeri_pv.emplace_back(120 + X_EROE + 18, 80 + _y[e] - 4, INCHIOSTRO_CHIARO, palette_testo);
            }

            for(int n = 0; n < nemici; ++n)
            {
                int s = EROI + n;
                const Figura& f = GUBBIO_VOCE(FIGURE_NEMICI, int(GUBBIO_VOCE(INCONTRO, incontro).schieramento[n]));
                _figure[s] = tiles_di(f);
                bool grande = f.lato > 32;
                _x[s] = grande ? X_CORRADO : X_NEMICO;
                _y[s] = grande ? GUBBIO_VOCE(Y_FILA, 1) : GUBBIO_VOCE(Y_FILA, n);
                _sprite[s] = bn::sprite_ptr::create(_x[s], _y[s], bn::sprite_shape_size(f.lato, f.lato),
                                                    _figure[s]->create_tiles(0), _palette_nemici);
                _pv.emplace_back(X_BARRA_NEMICO, _y[s] + (grande ? 0 : 6), BARRA_PV, _palette_santi);
            }

            aggiorna_barre();
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
                    mostra_menu(UBALDO, TestoId::BATT_GIUDIZIO);
                    // la freccia del bersaglio sul nemico predefinito, come la vedrebbe il giocatore
                    int s = slot_vista(true, bersaglio_predefinito(g_scena, Puntamento::NEMICO));
                    _aiuto.mostra(TestoId::BATT_BERSAGLIO);
                    _aiuto.rivela_tutto();
                    _freccia.set_position(_x[s], bn::max(_y[s] - _sprite[s]->shape_size().height() / 2 - 6, FRECCIA_Y_MIN));
                    _freccia.set_visible(true);
                    attendi(20);
                    scatta(nome_istantanea("menu"), true);
                    attendi(40);
                    _freccia.set_visible(false);
                    nascondi_menu();
                }

                g_scena.avanza();       // CODA
                g_scena.avanza();       // ESECUZIONE
                g_scena.avanza();       // FINE_ROUND

                for(int i = 0; i < g_scena.eventi_round(); ++i)
                {
                    Mossa m = _vista.consuma(g_scena.evento(i));
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
            // l'esperienza dello scontro vinto, e chi sale di livello
            if(esito == Esito::VITTORIA && partita)
            {
                bool saliti[EROI] = {};
                progressione::assegna_esperienza(*partita, _incontro, saliti);
                constexpr TestoId SALE[EROI] = { TestoId::BATT_SALE_UBALDO, TestoId::BATT_SALE_GIORGIO,
                                                 TestoId::BATT_SALE_ANTONIO };

                for(int e = 0; e < EROI; ++e)
                {
                    if(saliti[e])
                    {
                        _voce.mostra(GUBBIO_VOCE(SALE, e));
                        _voce.rivela_tutto();
                        attendi(FRAME_LIVELLO);
                    }
                }
            }

            attendi(30);
            scatta(nome_istantanea("esito"), _istantanee);

            for(int f = 0; f < FRAME_ESITO && ! (_guida == Guida::GIOCATORE && bn::keypad::a_pressed()); ++f)
            {
                attendi(1);
            }

            return esito;
        }

    private:
        int _incontro;
        Guida _guida;
        bool _istantanee;
        bool _veloce = false;
        bn::bg_palette_ptr _palette_sfondo;
        bn::regular_bg_tiles_ptr _tiles_sfondo;
        bn::regular_bg_ptr _sfondo;
        bn::sprite_palette_ptr _palette_santi;
        bn::sprite_palette_ptr _palette_nemici;
        VistaTesto _titolo;
        VistaTesto _voce;
        VistaTesto _aiuto;
        VistaTesto _immune;
        VistaNumero _numero;
        bn::sprite_tiles_item _freccia_tiles;
        bn::sprite_ptr _freccia;
        bn::vector<VistaNumero, EROI> _numeri_pv;
        int _pv_scritti[EROI] = { -1, -1, -1 };
        VistaBattaglia _vista;
        bn::optional<bn::sprite_tiles_item> _figure[SLOT_VISTA];
        bn::optional<bn::sprite_ptr> _sprite[SLOT_VISTA];
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

        void posa(int s, bool azione)
        {
            _sprite[s]->set_tiles(*_figure[s], azione ? 1 : 0);
        }

        void mostra_menu(int eroe, TestoId voce)
        {
            _titolo.mostra(GUBBIO_VOCE(NOMI_SANTI, eroe));
            _titolo.rivela_tutto();
            _voce.mostra(voce);
            _voce.rivela_tutto();
            _aiuto.mostra(TestoId::BATT_SCEGLI);
            _aiuto.rivela_tutto();
        }

        void nascondi_menu()
        {
            _titolo.nascondi();
            _voce.nascondi();
            _aiuto.nascondi();
        }

        void scegli_comandi()
        {
            for(int e = 0; e < EROI; ++e)
            {
                const Unita& eroe = g_scena.eroe(e);

                if(! eroe.vivo())
                {
                    continue;
                }

                bn::vector<Opzione, 4> opzioni;
                AbilitaId firma = GUBBIO_VOCE(ABILITA_FIRMA, e);

                if(eroe.carica)
                {
                    opzioni.push_back({ TestoId::BATT_SUPREMA, { TipoComando::SUPREMA, firma, -1, BOOST_SUPREMA } });
                }
                else
                {
                    opzioni.push_back({ TestoId::BATT_ATTACCO, { TipoComando::USA_ABILITA, AbilitaId::ATTACCO, -1, 0 } });
                    const AbilitaId proprie[EROI][2] = {
                        { AbilitaId::GIUDIZIO_DELLA_VERGA, AbilitaId::MURO_DELLA_FEDE },
                        { AbilitaId::FENDENTE_DEL_DRAGO, AbilitaId::BASTIONE_AZZURRO },
                        { AbilitaId::FUOCO_DI_SANTANTONIO, AbilitaId::FUOCO_DI_SANTANTONIO },
                    };
                    const TestoId nomi[EROI][2] = {
                        { TestoId::BATT_GIUDIZIO, TestoId::BATT_MURO },
                        { TestoId::BATT_FENDENTE, TestoId::BATT_BASTIONE },
                        { TestoId::BATT_FUOCO, TestoId::BATT_FUOCO },
                    };

                    for(int k = 0; k < (e == ANTONIO ? 1 : 2); ++k)
                    {
                        AbilitaId a = GUBBIO_VOCE(GUBBIO_VOCE(proprie, e), k);

                        if(eroe.fervore >= GUBBIO_VOCE(ABILITA, int(a)).costo)
                        {
                            opzioni.push_back({ GUBBIO_VOCE(GUBBIO_VOCE(nomi, e), k), { TipoComando::USA_ABILITA, a, -1, 0 } });
                        }
                    }

                    if(eroe.fervore >= GUBBIO_VOCE(ABILITA, int(firma)).costo + GUBBIO_VOCE(BOOST_COSTO, BOOST_SUPREMA))
                    {
                        opzioni.push_back({ TestoId::BATT_CARICA, { TipoComando::CARICA, firma, -1, 0 } });
                    }
                }

                int scelta = 0;
                Comando comando;

                while(true)
                {
                    mostra_menu(e, opzioni[scelta].testo);

                    for(int f = 0; ; ++f)
                    {
                        if(bn::keypad::down_pressed() || bn::keypad::up_pressed())
                        {
                            int passo = bn::keypad::down_pressed() ? 1 : opzioni.size() - 1;
                            scelta = (scelta + passo) % opzioni.size();
                            _voce.mostra(opzioni[scelta].testo);
                            _voce.rivela_tutto();
                        }

                        if(bn::keypad::a_pressed())
                        {
                            break;
                        }

                        // chi sceglie dondola, per dire di chi e' il turno
                        _sprite[e]->set_y(_y[e] - ((f / 16) % 2));
                        attendi(1);
                    }

                    attendi(1);
                    comando = opzioni[scelta].comando;

                    if(scegli_bersaglio(e, comando))
                    {
                        break;
                    }
                }

                _sprite[e]->set_y(_y[e]);
                g_scena.imposta_comando(e, comando);
                attendi(1);
            }

            nascondi_menu();
        }

        // Il bersaglio del comando, se il comando ne sceglie uno: la freccia sopra, su e giu' la
        // spostano fra i vivi (include/vista_battaglia.h), A conferma, B torna alla scelta del comando.
        bool scegli_bersaglio(int eroe, Comando& comando)
        {
            Puntamento mira = mira_del_comando(comando);

            if(mira == Puntamento::NESSUNO)
            {
                return true;
            }

            int scelto = bersaglio_predefinito(g_scena, mira);
            _aiuto.mostra(TestoId::BATT_BERSAGLIO);
            _aiuto.rivela_tutto();
            bool confermato = false;

            for(int f = 0; ; ++f)
            {
                if(bn::keypad::down_pressed() || bn::keypad::up_pressed())
                {
                    scelto = prossimo_bersaglio(g_scena, mira, scelto, bn::keypad::down_pressed() ? 1 : -1);
                }

                if(bn::keypad::a_pressed() || bn::keypad::b_pressed())
                {
                    confermato = bn::keypad::a_pressed();
                    break;
                }

                int s = slot_vista(mira == Puntamento::NEMICO, scelto);
                int alto = (_sprite[s]->shape_size().height()) / 2;
                _freccia.set_position(_x[s], bn::max(_y[s] - alto - 6, FRECCIA_Y_MIN));
                _freccia.set_tiles(_freccia_tiles, (f / 12) % 2);
                _freccia.set_visible(true);
                _sprite[eroe]->set_y(_y[eroe] - ((f / 16) % 2));
                attendi(1);
            }

            _freccia.set_visible(false);
            attendi(1);

            if(confermato)
            {
                comando.bersaglio = scelto;
            }

            return confermato;
        }

        void anima(const Mossa& m, bool fotografa)
        {
            int durata = m.gesto == Gesto::NESSUNO ? FRAME_FERVORE : FRAME_EVENTO;

            if(_veloce)
            {
                durata = 1;
            }

            int verso = m.attore >= EROI ? -1 : 1;

            if(m.attore >= 0)
            {
                posa(m.attore, true);
            }

            if(m.gesto == Gesto::IMMUNE)
            {
                _immune.mostra(TestoId::BATT_IMMUNE);
                _immune.rivela_tutto();
                _titolo.mostra(TestoId::BATT_INDIZIO);
                _titolo.rivela_tutto();
            }

            for(int f = 0; f < durata; ++f)
            {
                // un attore solo si muove: scatta verso il bersaglio e torna
                if(m.attore >= 0)
                {
                    int scatto = f < 8 ? f * PASSO_SCATTO : (f < 20 ? 8 * PASSO_SCATTO : (durata - f) * PASSO_SCATTO);
                    _sprite[m.attore]->set_x(_x[m.attore] + verso * scatto);
                }

                if(m.bersaglio >= 0 && _sprite[m.bersaglio])
                {
                    bn::sprite_ptr& b = *_sprite[m.bersaglio];
                    bool reagisce = f >= 8 && f < 20;

                    if(m.gesto == Gesto::COLPO || m.gesto == Gesto::USTIONE || m.gesto == Gesto::PARATA ||
                       m.gesto == Gesto::CADUTA)
                    {
                        b.set_visible(! reagisce || (f / 2) % 2 == 0);
                    }
                    else if(m.gesto == Gesto::SCUDO_ROTTO)
                    {
                        b.set_x(_x[m.bersaglio] + (reagisce ? ((f % 4) < 2 ? 2 : -2) : 0));
                    }
                }

                if(m.numero > 0 && f >= 8 && m.bersaglio >= 0)
                {
                    _numero.mostra(m.numero);
                    _numero.colloca(120 + _x[m.bersaglio] - 16, 80 + _y[m.bersaglio] - 12 - (f - 8) / 2);
                }

                if(fotografa && f == 12)
                {
                    scatta(nome_istantanea(m.gesto == Gesto::IMMUNE ? "immune" : "colpo"), _istantanee);
                }

                attendi(1);
            }

            if(m.attore >= 0)
            {
                posa(m.attore, false);
                _sprite[m.attore]->set_x(_x[m.attore]);
            }

            if(m.bersaglio >= 0 && _sprite[m.bersaglio])
            {
                _sprite[m.bersaglio]->set_x(_x[m.bersaglio]);
                _sprite[m.bersaglio]->set_visible(! _vista.caduto(m.bersaglio));
            }

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
        VistaTesto voce(Contesto::DIALOGO, 8, PANNELLO_Y + 6, INCHIOSTRO_CHIARO, palette_testo);
        VistaTesto aiuto(Contesto::DIALOGO, 8, PANNELLO_Y + 36, INCHIOSTRO_CHIARO, palette_testo);
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

    g_scena.ricomincia(incontro, seme, false, eroi);
    Esito esito;

    {
        Scena scena(incontro, guida, palette_testo, istantanee);
        esito = scena.gioca(partita);
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
                                  crea_palette(COLORI_NEMICI));
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
