#include "esplorazione.h"
#include "aritmetica.h"

#include "bn_bg_palette_item.h"
#include "bn_blending.h"
#include "bn_bg_palettes.h"
#include "bn_color.h"
#include "bn_fixed.h"
#include "bn_log.h"
#include "bn_timer.h"
#include "bn_timers.h"
#include "bn_regular_bg_map_item.h"
#include "bn_regular_bg_tiles_item.h"
#include "bn_regular_bg_map_ptr.h"
#include "bn_size.h"
#include "bn_sprite_palette_item.h"
#include "bn_sprite_palette_ptr.h"
#include "bn_sprite_palettes.h"
#include "bn_sprites.h"
#include "bn_sprite_shape_size.h"
#include "bn_sprite_tiles_item.h"
#include "bn_sprite_tiles_ptr.h"
#include "bn_tile.h"

#include "aiuti.h"
#include "compagni.h"
#include "game_state.h"
#include "opzioni.h"
#include "pannello.h"

namespace gubbio
{

namespace
{
    constexpr int LARGHEZZA_SCHERMO = 240;
    constexpr int ALTEZZA_SCHERMO = 160;
    constexpr int PASSI_DISSOLVENZA = 8;
    // il reciproco precalcolato: per moltiplicare invece di dividere (docs/regole_sviluppo_gba.md, punto 3)
    constexpr bn::fixed UN_PASSO_DI_DISSOLVENZA = bn::fixed(1) / PASSI_DISSOLVENZA;
    constexpr int FRAME_ETICHETTA = 150;
    // Etichetta chiara con ombra scura: si legge sui suoli chiari, sui tetti e sul fondo nero.
    constexpr int INCHIOSTRO_ETICHETTA = 2;
    constexpr int INCHIOSTRO_OMBRA = 1;

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

    constexpr Colori COLORI_FONDALI = colori(mondo::PALETTE_FONDALI);
    constexpr Colori COLORI_FONDALI_CUPI = colori(mondo::PALETTE_FONDALI_CUPA);

    // I banchi della palette dei fondali (pezzo EDI): 16 colori per banco, ogni tile ne usa uno (la cella della
    // mappa porta il banco nei bit 12-15). Il banco 0 e' PALETTE_FONDALI.
    struct Banchi
    {
        bn::color colori[mondo::BANCHI_FONDALI * 16];
    };

    constexpr Banchi banchi(const uint16_t (&parole)[mondo::BANCHI_FONDALI * 16])
    {
        Banchi b;

        for(int i = 0; i < mondo::BANCHI_FONDALI * 16; ++i)
        {
            b.colori[i] = bn::color(GUBBIO_VOCE(parole, i));
        }

        return b;
    }

    constexpr Banchi BANCHI_GIORNO = banchi(mondo::PALETTE_FONDALI_BANCHI);
    constexpr Banchi BANCHI_CUPI = banchi(mondo::PALETTE_FONDALI_BANCHI_CUPA);
    constexpr Banchi BANCHI_NOTTE = banchi(mondo::PALETTE_FONDALI_BANCHI_NOTTE);
    constexpr Banchi BANCHI_NOTTE_INTERNI = banchi(mondo::PALETTE_FONDALI_BANCHI_NOTTE_INTERNI);   // senza fiaccole
    constexpr int FRAME_RIFLESSI = 20;             // ogni quanto i riflessi dell'acqua cambiano
    constexpr int COLORE_ACQUA = 12;               // i due colori dell'acqua nella palette dei fondali
    constexpr int COLORE_ACQUA_CHIARA = 13;
    constexpr Colori COLORI_GIOCATORE = colori(mondo::PALETTE_GIOCATORE);
    constexpr Colori COLORI_GIOCATORE_NOTTE = colori(mondo::PALETTE_GIOCATORE_NOTTE);
    constexpr Colori COLORI_COMPAGNI[compagni::COMPAGNI] = { colori(compagni::PALETTE_GIORGIO), colori(compagni::PALETTE_ANTONIO) };
    constexpr Colori COLORI_COMPAGNI_NOTTE[compagni::COMPAGNI] = { colori(compagni::PALETTE_GIORGIO_NOTTE),
                                                                   colori(compagni::PALETTE_ANTONIO_NOTTE) };

    // La polvere della corsa (Loop 3, ok del custode visivo): uno sbuffo di 3-4 pixel dietro il piede che si
    // stacca, piu' chiaro del suolo: toni 5 (P5, sopra) e 4 (P4, a terra) del banco 0 dei fondali, letti dalla
    // palette caricata (di notte e nella gola cambiano da soli), un pixel sopra la riga dei piedi perche' non cada
    // sulla fuga del lastrico; tre fotogrammi da FRAME_SBUFFO vblank, solo sul selciato e sulla ghiaia.
    // Ogni pixel tocca un altro pixel (P3: niente pixel orfani). 4bpp: un nibble per pixel, il basso a sinistra.
    constexpr int FRAME_SBUFFO = 4;
    constexpr int VITA_SBUFFO = 3 * FRAME_SBUFFO;

    constexpr bn::tile riga_sbuffo(bn::tile t, int r, uint32_t pixel)
    {
        t.data[r] = pixel;
        return t;
    }

    constexpr bn::tile POLVERE[3] = {
        // nasce: due pixel a terra e uno sopra
        riga_sbuffo(riga_sbuffo(bn::tile{}, 6, 0x00001000), 7, 0x00022000),
        // si allarga: quattro pixel a terra e quattro sopra
        riga_sbuffo(riga_sbuffo(bn::tile{}, 6, 0x00111100), 7, 0x00222200),
        // si posa: tre pixel chiari, piu' in alto
        riga_sbuffo(riga_sbuffo(bn::tile{}, 5, 0x00010000), 6, 0x00001100),
    };

    // il selciato e la ghiaia: si' polvere; prato, scale, ponte, gola e acqua no
    constexpr bool suolo_che_fa_polvere(int c)
    {
        mondo::Cella t = mondo::Cella(c);
        return t == mondo::Cella::SUOLO || t == mondo::Cella::STRADA || t == mondo::Cella::LASTRICO ||
               t == mondo::Cella::CORSO || t == mondo::Cella::VIALETTO || t == mondo::Cella::BRECCIA;
    }

    constexpr bn::sprite_tiles_item POLVERE_ITEM(bn::span<const bn::tile>(POLVERE, 3), bn::bpp_mode::BPP_4,
                                                 bn::compression_type::NONE, 3);

    // La fila: lo z di Esplorazione::z_sulla_mappa, come la gente e gli NPC (prima la fila stava sempre davanti
    // alla gente, anche a chi le passava davanti piu' in basso); a pari y Ubaldo davanti; il fumetto davanti a tutti.
    constexpr int z_della_fila(int y)
    {
        return Esplorazione::z_sulla_mappa(y) - 2;
    }

    // Il cartiglio: sei pezzi da 32x16 (sinistro, quattro centrali, destro) in cima allo schermo,
    // dietro il nome dell'area, con la palette dei fondali. Nascosto finche' non c'e' un nome.
    constexpr int CARTIGLIO_X = 16;
    constexpr int CARTIGLIO_Y = 4;
    constexpr int CARTIGLIO_PEZZI = 6;

    bn::vector<bn::sprite_ptr, CARTIGLIO_PEZZI> crea_cartiglio()
    {
        bn::sprite_palette_ptr palette = bn::sprite_palette_ptr::create(
            bn::sprite_palette_item(bn::span<const bn::color>(COLORI_FONDALI.colori), bn::bpp_mode::BPP_4));
        bn::vector<bn::sprite_ptr, CARTIGLIO_PEZZI> out;

        for(int i = 0; i < CARTIGLIO_PEZZI; ++i)
        {
            int pezzo = i == 0 ? 0 : (i == CARTIGLIO_PEZZI - 1 ? 2 : 1);
            bn::sprite_tiles_item tiles(bn::span<const bn::tile>(
                mondo::TILE_CARTIGLIO + pezzo * mondo::TILE_PER_PEZZO_CARTIGLIO, mondo::TILE_PER_PEZZO_CARTIGLIO),
                bn::bpp_mode::BPP_4);
            bn::sprite_ptr sprite = bn::sprite_ptr::create(
                CARTIGLIO_X + 16 + i * 32 - LARGHEZZA_SCHERMO / 2, CARTIGLIO_Y + 8 - ALTEZZA_SCHERMO / 2,
                bn::sprite_shape_size(32, 16), tiles.create_tiles(), palette);
            sprite.set_visible(false);
            out.push_back(bn::move(sprite));
        }

        return out;
    }

    // Il giocatore (tools/sagome_mappa.py): 16x32, 8 tile a fotogramma, 8 fotogrammi per direzione.
    constexpr int TILE_PER_FOTOGRAMMA = 8;

    template<int N>
    void scrivi_fotogramma_da(const uint32_t (&sorgente)[N], bn::sprite_tiles_ptr& tiles, int direzione, int fotogramma)
    {
        bn::span<bn::tile> vram = *tiles.vram();
        int primo = (direzione * mondo::GIOCATORE_FOTOGRAMMI + fotogramma) * TILE_PER_FOTOGRAMMA;

        for(int t = 0; t < TILE_PER_FOTOGRAMMA; ++t)
        {
            for(int r = 0; r < 8; ++r)
            {
                vram[t].data[r] = GUBBIO_VOCE(sorgente, (primo + t) * 8 + r);
            }
        }
    }

    void scrivi_fotogramma(bn::sprite_tiles_ptr& tiles, int direzione, int fotogramma)
    {
        scrivi_fotogramma_da(mondo::TILE_GIOCATORE, tiles, direzione, fotogramma);
    }

    void scrivi_fotogramma_compagno(int chi, bn::sprite_tiles_ptr& tiles, int direzione, int fotogramma)
    {
        if(chi == 0)
        {
            scrivi_fotogramma_da(compagni::TILE_GIORGIO, tiles, direzione, fotogramma);
        }
        else
        {
            scrivi_fotogramma_da(compagni::TILE_ANTONIO, tiles, direzione, fotogramma);
        }
    }

    bn::sprite_ptr crea_giocatore()
    {
        bn::sprite_tiles_ptr tiles = bn::sprite_tiles_ptr::allocate(TILE_PER_FOTOGRAMMA, bn::bpp_mode::BPP_4);
        scrivi_fotogramma(tiles, 0, mondo::GIOCATORE_RIPOSO);
        bn::sprite_palette_ptr palette = bn::sprite_palette_ptr::create(
            bn::sprite_palette_item(bn::span<const bn::color>(COLORI_GIOCATORE.colori), bn::bpp_mode::BPP_4));
        return bn::sprite_ptr::create(0, 0, bn::sprite_shape_size(16, 32), bn::move(tiles), bn::move(palette));
    }

    bn::sprite_ptr crea_fumetto(const bn::sprite_palette_ptr& palette)
    {
        bn::sprite_tiles_ptr tiles = bn::sprite_tiles_ptr::allocate(1, bn::bpp_mode::BPP_4);
        bn::span<bn::tile> vram = *tiles.vram();

        for(int r = 0; r < 8; ++r)
        {
            vram[0].data[r] = GUBBIO_VOCE(mondo::TILE_FUMETTO, r);
        }

        bn::sprite_ptr fumetto = bn::sprite_ptr::create(0, 0, bn::sprite_shape_size(8, 8), bn::move(tiles), palette);
        fumetto.set_z_order(bn::sprites::min_z_order());     // davanti a chi parla e alla fila
        fumetto.set_visible(false);
        return fumetto;
    }

    constexpr int limita(int v, int minimo, int massimo)
    {
        return v < minimo ? minimo : (v > massimo ? massimo : v);
    }

    constexpr int ANTICIPO_X = 24;
    constexpr int ANTICIPO_Y = 16;
    constexpr int PASSI_CAMERA = 6;

    // Il passo della camera verso il bersaglio: un sesto della distanza, almeno un pixel, mai oltre.
    constexpr int verso_il_bersaglio(int distanza)
    {
        // col reciproco (aritmetica.h), troncando verso lo zero come la divisione: le distanze stanno nell'area
        int modulo = dividi<PASSI_CAMERA, 1 << 14>(distanza < 0 ? -distanza : distanza);
        int passo = distanza < 0 ? -modulo : modulo;
        return passo != 0 ? passo : (distanza > 0 ? 1 : (distanza < 0 ? -1 : 0));
    }

    static_assert(verso_il_bersaglio(0) == 0 && verso_il_bersaglio(5) == 1 && verso_il_bersaglio(-5) == -1);
    static_assert(verso_il_bersaglio(60) == 10 && verso_il_bersaglio(-60) == -10);

    // MAI: le entrate dei riquadri degli aiuti (A2, A3): di quanto sono fuori al passo k (k = 0: al posto loro).
    // k * (altezza + 1) / PASSI, col reciproco (aritmetica.h): k <= PASSI e l'altezza sta nello schermo
    template<int PASSI>
    constexpr int fuori_di(int k, int altezza)
    {
        return dividi<PASSI, (PASSI + 1) * 256>(k * (altezza + 1));
    }
}

Esplorazione::Esplorazione(const bn::sprite_palette_ptr& palette_testo) :
    _palette(bn::bg_palette_ptr::create(
        bn::bg_palette_item(bn::span<const bn::color>(BANCHI_GIORNO.colori), bn::bpp_mode::BPP_4))),
    _camera(bn::camera_ptr::create(0, 0)),
    _giocatore(crea_giocatore()),
    _fumetto(crea_fumetto(_giocatore.palette())),
    _cartiglio(crea_cartiglio()),
    _ombra(testo::Contesto::AREA, 25, 9, INCHIOSTRO_OMBRA, palette_testo),
    _etichetta(testo::Contesto::AREA, 24, 8, INCHIOSTRO_ETICHETTA, palette_testo),
    _palette_testo(palette_testo),
    _palette_aiuti(pannello::crea_palette())
{
    _giocatore.set_camera(_camera);
    _fumetto.set_camera(_camera);

    // la polvere: due sprite fissi riusati (si alterna un piede alla volta), nascosti finche' non servono
    bn::color colori[16] = {};
    _palette_polvere = bn::sprite_palette_ptr::create(bn::sprite_palette_item(bn::span<const bn::color>(colori),
                                                                              bn::bpp_mode::BPP_4));

    for(int i = 0; i < SBUFFI; ++i)
    {
        bn::sprite_ptr sprite = bn::sprite_ptr::create(0, 0, bn::sprite_shape_size(8, 8),
                                                       POLVERE_ITEM.create_tiles(0), *_palette_polvere);
        sprite.set_camera(_camera);
        sprite.set_visible(false);
        _sbuffi.push_back(Sbuffo{ bn::move(sprite), 0, 0, 0 });
    }
}

void Esplorazione::entra(mondo::AreaId id, int spawn)
{
    mondo::colloca(_e, id, spawn);
    _carica_fondale();
    _giocatore.set_visible(true);       // dopo il prologo (sospendi): Ubaldo torna solo in citta'
}

void Esplorazione::riprendi(mondo::AreaId id, int x, int y)
{
    _e.area = id;
    _e.x = x;
    _e.y = y;
    _e.varco_sotto = -1;
    _carica_fondale();
    _giocatore.set_visible(true);
}

void Esplorazione::segnala(int x, int y, int altezza)
{
    // il centro del tile 8x8: 2 px sopra la testa, 4 di meta' fumetto
    _fumetto_x = x;
    _fumetto_y = y - altezza - 2 - 4;

    if(! _fumetto_acceso)
    {
        _fumetto_acceso = true;
        _oscilla = 0;
    }
}

void Esplorazione::spegni_segnale()
{
    _fumetto_acceso = false;
    _fumetto.set_visible(false);
}

void Esplorazione::imposta_notte(bool notte)
{
    if(notte != _notte)
    {
        _notte = notte;
        // Ubaldo (e il fumetto, che ne usa la palette) passa alle rampe di notte con la citta'
        bn::sprite_palette_ptr palette = _giocatore.palette();
        palette.set_colors(bn::span<const bn::color>((notte ? COLORI_GIOCATORE_NOTTE : COLORI_GIOCATORE).colori));

        for(int i = 0; i < _fila.size(); ++i)
        {
            bn::sprite_palette_ptr p = _fila[i].sprite.palette();
            p.set_colors(bn::span<const bn::color>((notte ? COLORI_COMPAGNI_NOTTE[i] : COLORI_COMPAGNI[i]).colori));
        }

        if(_fondale)
        {
            _carica_fondale();
        }
    }
}

void Esplorazione::imposta_variante(int variante)
{
    _variante = variante;

    // il fondale gia' caricato e' quello dell'area: se la variante cambia, si ricarica (alla dissolvenza ci pensa
    // il caricamento di meta' strada)
    bool vale = variante >= 0 && variante < mondo::VARIANTI && mondo::VARIANTE[variante].area == _area_caricata;
    int voluta = vale ? variante : -1;

    if(_fondale && _area_caricata == _e.area && voluta != _variante_caricata)
    {
        _carica_fondale(false);
    }
}

void Esplorazione::sospendi()
{
    nascondi_etichetta();
    togli_compagni();
    _giocatore.set_visible(false);
    _spegni_polvere();
    _fondale.reset();
    _tiles.reset();
}

void Esplorazione::ricompari()
{
    // dopo una battaglia o una cutscene si resta nella stessa area: il cartiglio col nome non riappare,
    // se no resterebbe a meta' (la sola iniziale) sotto il dialogo che segue, che non fa avanzare l'etichetta
    _carica_fondale(false);
    _giocatore.set_visible(true);
}

void Esplorazione::colloca_sulla_mappa(bn::sprite_ptr& sprite, int x, int y, int altezza) const
{
    sprite.set_camera(_camera);
    sprite.set_position(x - _mezza_larghezza_mappa, y - altezza / 2 - _mezza_altezza_mappa);
    sprite.set_z_order(z_sulla_mappa(y));
}

void Esplorazione::_carica_fondale(bool etichetta)
{
    // Le celle sono gia' in ROM (include/mondo.h): Butano le copia in VRAM, o per una big map ne
    // carica solo la parte vicina allo schermo, e aggiunge da se' gli scostamenti di tile e palette.
    const mondo::Area& a = mondo::area(_e.area);
#ifdef GUBBIO_PRESTAZIONI
    bn::timer t;
    int tempi[4];
    auto segna = [&](int k) { tempi[k] = t.elapsed_ticks() * 100 / bn::timers::ticks_per_frame(); t.restart(); };
#else
    auto segna = [](int) {};
#endif
    _area_caricata = _e.area;
    _spegni_polvere();
    _fondale.reset();

    // Ogni area ha i suoi tile (suolo e monumenti): prima si lascia la mappa vecchia, poi i suoi tile.
    _tiles.reset();

    // le stanze della gola hanno la palette cupa; la citta' di notte le rampe di notte (pezzo EDI)
    const Banchi& c = a.cupa ? BANCHI_CUPI : (_notte ? (a.interno ? BANCHI_NOTTE_INTERNI : BANCHI_NOTTE) : BANCHI_GIORNO);
    _palette.set_colors(bn::span<const bn::color>(c.colori));

    // una stanza che cambia con la fase (INTp): stessi lati e stessa griglia, altri tile e altro fondale
    const bn::tile* tile = a.tile;
    int tile_conteggio = a.tile_conteggio;
    const uint16_t* fondale = a.fondale;

    if(_variante >= 0 && _variante < mondo::VARIANTI && mondo::VARIANTE[_variante].area == _e.area)
    {
        tile = mondo::VARIANTE[_variante].tile;
        tile_conteggio = mondo::VARIANTE[_variante].tile_conteggio;
        fondale = mondo::VARIANTE[_variante].fondale;
    }

    _variante_caricata = _variante >= 0 && fondale != a.fondale ? _variante : -1;
    segna(0);
    _tiles = bn::regular_bg_tiles_ptr::create(
        bn::regular_bg_tiles_item(bn::span<const bn::tile>(tile, tile_conteggio), bn::bpp_mode::BPP_4));

    segna(1);
    bn::size lati(a.larghezza_fondale, a.altezza_fondale);
    bn::regular_bg_map_item voce(*fondale, lati, bn::compression_type::NONE, 1, a.fondale_grande);
    _mezza_larghezza_mappa = lati.width() * mondo::TILE_PX / 2;
    _mezza_altezza_mappa = lati.height() * mondo::TILE_PX / 2;
    _fondale = bn::regular_bg_ptr::create(0, 0, bn::regular_bg_map_ptr::create(voce, *_tiles, _palette));
    _fondale->set_camera(_camera);
    _camera_ferma = true;
    segna(2);

    // i centri dei varchi: si cercano nei frame seguenti, un pezzo di griglia per frame (_cerca_i_varchi)
    _varchi_cella = 0;
    _varchi_pronti = false;

    for(int k = 0; k < mondo::VARCHI_MAX; ++k)
    {
        _varchi_sx[k] = _varchi_sy[k] = _varchi_n[k] = 0;
    }

    segna(3);
#ifdef GUBBIO_PRESTAZIONI
    BN_LOG("PREST carica area ", int(_e.area), " palette ", tempi[0], " tile ", tempi[1], " mappa ", tempi[2], " varchi ",
           tempi[3]);

#endif

    if(etichetta)
    {
        _mostra_etichetta(a.etichetta);
    }

    aggiorna();
}

void Esplorazione::_mostra_etichetta(testi::TestoId id)
{
    // l'ombra e la scritta si preparano nei due frame seguenti, una per frame (ognuna costa piu' di mezzo frame:
    // insieme, al cambio d'area, facevano perdere un frame in piu'); poi avanzano insieme
    _ombra.nascondi();
    _etichetta.nascondi();
    _testo_etichetta = id;
    _etichetta_passo = 2;
    _attesa_etichetta = FRAME_ETICHETTA;
}

void Esplorazione::_mostra_cartiglio(bool visibile)
{
    for(bn::sprite_ptr& pezzo : _cartiglio)
    {
        pezzo.set_visible(visibile);
    }
}

void Esplorazione::_dopo_evento(mondo::Evento evento)
{
    if(evento == mondo::Evento::CAMBIO_AREA)
    {
        _dissolvenza = PASSI_DISSOLVENZA;
    }
    else if(evento == mondo::Evento::INGRESSO_DUNGEON)
    {
        const mondo::Area& a = mondo::area(_e.area);
        _mostra_etichetta(mondo::varco_di(a, _e.ultimo_varco).etichetta);
        _camera_ferma = true;
    }
}

void Esplorazione::muovi(int dx, int dy, int passi)
{
    if(_dissolvenza)
    {
        return;
    }

    // In diagonale si andava il 41% piu' veloci che dritti: ora 0,707 passi per frame (mondo::passi_in_diagonale).
    // Contro un muro (uno dei due assi bloccato) si scivola lungo il muro alla velocita' piena, come dritti.
    int passi_ora = passi;
    const mondo::Area& qui = mondo::area(_e.area);
    bool diagonale_vera = dx && dy && mondo::libero(qui, _e.x + dx, _e.y) && mondo::libero(qui, _e.x, _e.y + dy);

    if(diagonale_vera)
    {
        mondo::PassiDiagonale d = mondo::passi_in_diagonale(_resto_diagonale, passi);
        passi_ora = d.passi;
        _resto_diagonale = d.resto;
    }
    else
    {
        _resto_diagonale = 0;
    }

    for(int p = 0; p < passi_ora; ++p)
    {
        mondo::Evento evento = mondo::Evento::NESSUNO;

        _urto_al_varco = _urto_al_varco || (dx && mondo::urta_il_varco(_e, dx, 0, _varco_chiuso)) ||
                         (dy && mondo::urta_il_varco(_e, 0, dy, _varco_chiuso));

        bool passato_x = dx && mondo::muovi_fino_al_varco(_e, dx, 0, _varco_chiuso);

        if(passato_x)
        {
            evento = mondo::controlla_varco(_e);
        }

        bool passato_y = false;

        if(evento == mondo::Evento::NESSUNO && dy)
        {
            passato_y = mondo::muovi_fino_al_varco(_e, 0, dy, _varco_chiuso);

            if(passato_y)
            {
                evento = mondo::controlla_varco(_e);
            }
        }

        // contro uno spigolo mancato di poco si scivola di lato invece di impuntarsi (solo coi passi dritti)
        if(evento == mondo::Evento::NESSUNO && ! passato_x && ! passato_y && (dx == 0) != (dy == 0) &&
           mondo::scivola(_e, dx, dy, _varco_chiuso))
        {
            evento = mondo::controlla_varco(_e);
        }

        if(evento != mondo::Evento::NESSUNO)
        {
            _dopo_evento(evento);
            return;
        }
    }

    // la direzione della figura: di lato se ci si muove in orizzontale, se no di fronte o di schiena
    if(dx || dy)
    {
        _direzione = dx > 0 ? DESTRA : (dx < 0 ? SINISTRA : (dy > 0 ? GIU : SU));
        _mosso = true;
        _corre = passi > 1;
    }
}

void Esplorazione::_alza_polvere(bool piede_destro)
{
    const mondo::Area& a = mondo::area(_e.area);

    if(! suolo_che_fa_polvere(mondo::cella(a, mondo::cella_x(_e), mondo::cella_y(_e))))
    {
        return;
    }

    // dietro il piede che si stacca: di lato, alle spalle; davanti o di schiena, dal lato di quel piede
    int x = _e.x;
    int y = _e.y;

    if(_direzione == DESTRA || _direzione == SINISTRA)
    {
        x += _direzione == DESTRA ? -5 : 5;
    }
    else
    {
        // andando giu' il piede dietro sta sotto la veste: lo sbuffo esce di fianco, a terra
        int lato = _direzione == GIU ? 5 : 3;
        x += (piede_destro == (_direzione == GIU)) ? -lato : lato;
        y += _direzione == GIU ? 0 : 1;
    }

    // i toni 5 e 4 del suolo (banco 0: P4 e P3 si confondevano con la pietra) della palette caricata, cosi' di notte e nella gola segue il fondale
    bn::span<const bn::color> fondale = _palette.colors();
    bn::color colori[16] = {};
    colori[1] = fondale[5];
    colori[2] = fondale[4];
    _palette_polvere->set_colors(bn::span<const bn::color>(colori));

    Sbuffo& b = _sbuffi[_sbuffo_prossimo];
    _sbuffo_prossimo = (_sbuffo_prossimo + 1) % SBUFFI;
    b.vita = VITA_SBUFFO;
    b.x = x;
    b.y = y;
    b.sprite.set_tiles(POLVERE_ITEM, 0);
    b.sprite.set_position(x - _mezza_larghezza_mappa, y - 5 - _mezza_altezza_mappa);      // un pixel sopra i piedi
    b.sprite.set_z_order(z_sulla_mappa(y) + 1);         // dietro chi sta alla stessa riga
    b.sprite.set_blending_enabled(_scura);
    b.sprite.set_visible(true);
}

void Esplorazione::_anima_polvere()
{
    for(Sbuffo& b : _sbuffi)
    {
        if(b.vita <= 0)
        {
            continue;
        }

        if(--b.vita == 0)
        {
            b.sprite.set_visible(false);
        }
        else if(b.vita % FRAME_SBUFFO == 0)
        {
            b.sprite.set_tiles(POLVERE_ITEM, (VITA_SBUFFO - b.vita) / FRAME_SBUFFO);
        }
    }
}

void Esplorazione::_spegni_polvere()
{
    for(Sbuffo& b : _sbuffi)
    {
        b.vita = 0;
        b.sprite.set_visible(false);
    }
}

void Esplorazione::_anima_giocatore()
{
    // camminata (A6): 6 fotogrammi da 6 vblank, 4 se si corre; da fermi il respiro (A5), 2 x 30 vblank
    int fotogramma;

    if(_mosso)
    {
        int vblank = _corre ? mondo::GIOCATORE_VBLANK_CORSA : mondo::GIOCATORE_VBLANK_PASSO;
        int prima = _camminata.fotogramma;
        fotogramma = mondo::avanza_camminata(_camminata, vblank, mondo::GIOCATORE_CAMMINATA);
        _fermo = 0;

        // correndo, nei due fotogrammi col passo lungo (0 e 3: un piede avanti) il piede dietro si stacca
        if(_corre && fotogramma != prima && (fotogramma == 0 || fotogramma == 3))
        {
            _alza_polvere(fotogramma == 0);
        }
    }
    else
    {
        _camminata = mondo::Camminata();
        // il respiro: RESPIRO vblank fermo, RESPIRO col petto alzato; il contatore gira su due respiri, senza modulo
        _fermo = avanti(_fermo, 2 * mondo::GIOCATORE_VBLANK_RESPIRO);
        fotogramma = _fermo >= mondo::GIOCATORE_VBLANK_RESPIRO ? mondo::GIOCATORE_RESPIRO : mondo::GIOCATORE_RIPOSO;
    }

    int direzione = _direzione == SINISTRA ? DESTRA : _direzione;
    int chiave = direzione * mondo::GIOCATORE_FOTOGRAMMI + fotogramma;

    if(chiave != _mostrato)
    {
        _mostrato = chiave;
        bn::sprite_tiles_ptr tiles = _giocatore.tiles();
        scrivi_fotogramma(tiles, direzione, fotogramma);
    }

    _giocatore.set_horizontal_flip(_direzione == SINISTRA);
    _mosso = false;
}

// I centri dei varchi dell'area caricata (come aiuti::centro_del_varco, per tutti insieme), CELLE_PER_FRAME celle a
// frame: tutta la griglia in un frame costava un quinto di frame in una big map, proprio nel frame gia' pesante del
// cambio d'area. Le celle dei varchi valgono da PRIMO_VARCO (64) in su: una parola di 4 celle senza i bit 6 e 7 accesi
// non ne ha nessuna e si salta. 'tutto' finisce subito (il promemoria di Select, che li vuole adesso).
void Esplorazione::_cerca_i_varchi(bool tutto)
{
    static_assert(mondo::PRIMO_VARCO == 64, "il salto a parole cerca i bit 6 e 7 delle celle");
    constexpr int CELLE_PER_FRAME = 2048;

    if(_varchi_pronti)
    {
        return;
    }

    const mondo::Area& a = mondo::area(_area_caricata);
    const uint8_t* g = a.griglia;
    int celle = a.larghezza * a.altezza;
    int i = _varchi_cella;
    int fine = tutto || celle - i < CELLE_PER_FRAME ? celle : i + CELLE_PER_FRAME;

    auto conta = [&](int j)
    {
        int k = int(g[j]) - mondo::PRIMO_VARCO;

        if(k >= 0 && k < a.varchi)
        {
            _varchi_sx[k] += j % a.larghezza;
            _varchi_sy[k] += j / a.larghezza;
            ++_varchi_n[k];
        }
    };

    for(; i < fine && (reinterpret_cast<uintptr_t>(g + i) & 3); ++i)
    {
        conta(i);
    }

    const uint32_t* parole = reinterpret_cast<const uint32_t*>(g + i);

    for(; i + 4 <= fine; i += 4, ++parole)
    {
        if(*parole & 0xC0C0C0C0u)
        {
            for(int j = i; j < i + 4; ++j)
            {
                conta(j);
            }
        }
    }

    for(; i < fine; ++i)
    {
        conta(i);
    }

    _varchi_cella = i;

    if(i < celle)
    {
        return;
    }

    for(int k = 0; k < a.varchi; ++k)
    {
        int n = _varchi_n[k];
        _centri[k] = n ? aiuti::Punto{ (_varchi_sx[k] * mondo::TILE_PX) / n + mondo::TILE_PX / 2,
                                       (_varchi_sy[k] * mondo::TILE_PX) / n + mondo::TILE_PX / 2 } : aiuti::Punto{ -1, -1 };
#ifdef GUBBIO_PRESTAZIONI
        aiuti::Punto c = aiuti::centro_del_varco(a, k);
        BN_ASSERT(c.x == _centri[k].x && c.y == _centri[k].y, "Centro del varco ", k);
#endif
    }

    _varchi_pronti = true;
}

// --- La fila: Giorgio e Antonio sulle orme di Ubaldo ---------------------------------------------------------

void Esplorazione::imposta_compagni(int quanti)
{
    _compagni = quanti < 0 ? 0 : (quanti > COMPAGNI_MAX ? COMPAGNI_MAX : quanti);
}

void Esplorazione::togli_compagni()
{
    _fila.clear();
}

void Esplorazione::_azzera_orme()
{
    _orma = 0;
    _orme_n = 1;
    _orme[0] = { int16_t(_e.x), int16_t(_e.y) };
}

void Esplorazione::_segna_orme()
{
    if(_orme_n == 0)
    {
        _azzera_orme();
        return;
    }

    Orma ultima = _orme[_orma];
    int dx = _e.x - ultima.x;
    int dy = _e.y - ultima.y;
    int ax = dx < 0 ? -dx : dx;
    int ay = dy < 0 ? -dy : dy;

    // un salto (un varco, un ingresso, la storia che sposta Ubaldo): i compagni ripartono da dietro di lui
    if(ax + ay > 8)
    {
        _azzera_orme();

        for(Compagno& c : _fila)
        {
            c.x = _e.x;
            c.y = _e.y;
        }

        return;
    }

    // un'orma per pixel: prima in orizzontale poi in verticale (come i passi di muovi())
    int x = ultima.x;
    int y = ultima.y;

    while(x != _e.x || y != _e.y)
    {
        if(x != _e.x)
        {
            x += x < _e.x ? 1 : -1;
        }
        else
        {
            y += y < _e.y ? 1 : -1;
        }

        _orma = avanti(_orma, ORME);
        _orme[_orma] = { int16_t(x), int16_t(y) };
        _orme_n = _orme_n < ORME ? _orme_n + 1 : ORME;
    }
}

void Esplorazione::_anima_compagni()
{
    int voluti = _fondale && _giocatore.visible() ? _compagni : 0;

    while(_fila.size() > voluti)
    {
        _fila.pop_back();
    }

    while(_fila.size() < voluti)
    {
        int i = _fila.size();
        bn::sprite_tiles_ptr tiles = bn::sprite_tiles_ptr::allocate(TILE_PER_FOTOGRAMMA, bn::bpp_mode::BPP_4);
        scrivi_fotogramma_compagno(i, tiles, 0, mondo::GIOCATORE_RIPOSO);
        bn::sprite_palette_ptr palette = bn::sprite_palette_ptr::create(bn::sprite_palette_item(
            bn::span<const bn::color>((_notte ? COLORI_COMPAGNI_NOTTE[i] : COLORI_COMPAGNI[i]).colori), bn::bpp_mode::BPP_4));
        bn::sprite_ptr sprite = bn::sprite_ptr::create(0, 0, bn::sprite_shape_size(16, 32), bn::move(tiles), bn::move(palette));
        sprite.set_camera(_camera);
        sprite.set_blending_enabled(_scura);
        // il nuovo compagno esce da dietro Ubaldo: l'orma piu' vecchia che c'e'
        Orma o = _orme[_orme_n > 0 ? giro(_orma - (_orme_n - 1), ORME) : _orma];
        _fila.push_back(Compagno{ bn::move(sprite), o.x, o.y, _direzione == SINISTRA ? int(DESTRA) : _direzione, {}, 0, -1 });
    }

    int indietro = 0;

    for(int i = 0; i < _fila.size(); ++i)
    {
        Compagno& c = _fila[i];
        // il posto sulle orme: COMPAGNO_DISTANZA dietro chi lo precede (di lato 18 px, in verticale 21); finche' le
        // orme sono poche, la piu' vecchia
        for(int costo = 0; costo < COMPAGNO_DISTANZA && indietro < _orme_n - 1; ++indietro)
        {
            Orma a = _orme[giro(_orma - indietro, ORME)];
            Orma b = _orme[giro(_orma - indietro - 1, ORME)];
            costo += a.x != b.x ? COSTO_LATO : COSTO_SU;
        }

        Orma o = _orme[giro(_orma - indietro, ORME)];
        int dx = o.x - c.x;
        int dy = o.y - c.y;
        bool mosso = dx || dy;

        if(mosso)
        {
            int ax = dx < 0 ? -dx : dx;
            int ay = dy < 0 ? -dy : dy;
            c.direzione = ax >= ay ? (dx > 0 ? DESTRA : SINISTRA) : (dy > 0 ? GIU : SU);
            c.x = o.x;
            c.y = o.y;
        }

        // la camminata e il respiro come Ubaldo (A6, A5); il respiro sfasato, cosi' non respirano tutti insieme
        int fotogramma;

        if(mosso)
        {
            int vblank = _corre ? mondo::GIOCATORE_VBLANK_CORSA : mondo::GIOCATORE_VBLANK_PASSO;
            fotogramma = mondo::avanza_camminata(c.camminata, vblank, mondo::GIOCATORE_CAMMINATA);
            c.fermo = 0;
        }
        else
        {
            c.camminata = mondo::Camminata();
            // come Ubaldo, il contatore gira su due respiri; lo sfasamento si somma e si riporta nel giro
            constexpr int DUE_RESPIRI = 2 * mondo::GIOCATORE_VBLANK_RESPIRO;
            static_assert(COMPAGNI_MAX * 17 < DUE_RESPIRI, "lo sfasamento sta in un giro");
            c.fermo = avanti(c.fermo, DUE_RESPIRI);
            int sfasato = giro(c.fermo + (i + 1) * 17, DUE_RESPIRI);
            fotogramma = sfasato >= mondo::GIOCATORE_VBLANK_RESPIRO ? mondo::GIOCATORE_RESPIRO : mondo::GIOCATORE_RIPOSO;
        }

        int direzione = c.direzione == SINISTRA ? DESTRA : c.direzione;
        int chiave = direzione * mondo::GIOCATORE_FOTOGRAMMI + fotogramma;

        if(chiave != c.mostrato)
        {
            c.mostrato = chiave;
            bn::sprite_tiles_ptr tiles = c.sprite.tiles();
            scrivi_fotogramma_compagno(i, tiles, direzione, fotogramma);
        }

        c.sprite.set_horizontal_flip(c.direzione == SINISTRA);
        c.sprite.set_position(c.x - _mezza_larghezza_mappa, c.y - 15 - _mezza_altezza_mappa);
        // a pari y il compagno sta dietro a chi lo precede (Ubaldo davanti a tutti)
        c.sprite.set_z_order(z_della_fila(c.y) + i + 1);
    }
}

void Esplorazione::sincronizza(mondo::Evento evento)
{
    if(evento == mondo::Evento::CAMBIO_AREA)
    {
        _carica_fondale();
    }
    else if(evento == mondo::Evento::INGRESSO_DUNGEON)
    {
        _dopo_evento(evento);
    }
}

void Esplorazione::aggiorna()
{
    // i riflessi del torrente nelle stanze della gola: i due colori dell'acqua si scambiano
    // (il contatore gira su due scambi, senza modulo: 0 e FRAME_RIFLESSI sono i due momenti dello scambio)
    if(mondo::area(_area_caricata).cupa &&
       ((_riflessi = avanti(_riflessi, 2 * FRAME_RIFLESSI)) == 0 || _riflessi == FRAME_RIFLESSI))
    {
        const Colori& c = COLORI_FONDALI_CUPI;
        bool scambio = _riflessi == FRAME_RIFLESSI;
        _palette.set_color(COLORE_ACQUA, c.colori[scambio ? COLORE_ACQUA_CHIARA : COLORE_ACQUA]);
        _palette.set_color(COLORE_ACQUA_CHIARA, c.colori[scambio ? COLORE_ACQUA : COLORE_ACQUA_CHIARA]);
    }

    // Dissolvenza: in uscita scurisce, a meta' carica la nuova area, in entrata schiarisce.
    if(_dissolvenza > 0)
    {
        --_dissolvenza;
        bn::fixed intensita = UN_PASSO_DI_DISSOLVENZA * (PASSI_DISSOLVENZA - _dissolvenza);
        bn::bg_palettes::set_fade(bn::color(0, 0, 0), intensita);
        bn::sprite_palettes::set_fade(bn::color(0, 0, 0), intensita);

        if(_dissolvenza == 0)
        {
            _carica_fondale();
            _dissolvenza = -PASSI_DISSOLVENZA;
        }

        return;
    }

    if(_dissolvenza < 0)
    {
        ++_dissolvenza;
        bn::fixed intensita = UN_PASSO_DI_DISSOLVENZA * -_dissolvenza;
        bn::bg_palettes::set_fade(bn::color(0, 0, 0), intensita);
        bn::sprite_palettes::set_fade(bn::color(0, 0, 0), intensita);
    }

    // La camera inquadra il corpo (8 px sopra i piedi) con un anticipo di 24 px in orizzontale e 16 in
    // verticale verso dove guarda il giocatore, cosi' si vede la strada davanti e non quella alle spalle;
    // ci arriva per gradi (un sesto della distanza a frame) e non mostra oltre i bordi dell'area.
    // Un'area piu' stretta dello schermo resta centrata.
    const mondo::Area& a = mondo::area(_e.area);
    int larghezza = a.larghezza * mondo::TILE_PX;
    int altezza = a.altezza * mondo::TILE_PX;
    int anticipo_x = _direzione == DESTRA ? ANTICIPO_X : _direzione == SINISTRA ? -ANTICIPO_X : 0;
    int anticipo_y = _direzione == GIU ? ANTICIPO_Y : _direzione == SU ? -ANTICIPO_Y : 0;
    int bersaglio_x = larghezza <= LARGHEZZA_SCHERMO ? larghezza / 2 :
                      limita(_e.x + anticipo_x, LARGHEZZA_SCHERMO / 2, larghezza - LARGHEZZA_SCHERMO / 2);
    int bersaglio_y = altezza <= ALTEZZA_SCHERMO ? altezza / 2 :
                      limita(_e.y - 8 + anticipo_y, ALTEZZA_SCHERMO / 2, altezza - ALTEZZA_SCHERMO / 2);

    if(_camera_ferma)
    {
        _cam_x = bersaglio_x;
        _cam_y = bersaglio_y;
        _camera_ferma = false;
    }
    else
    {
        _cam_x += verso_il_bersaglio(bersaglio_x - _cam_x);
        _cam_y += verso_il_bersaglio(bersaglio_y - _cam_y);
    }

    int cx = _cam_x;
    int cy = _cam_y;
    _camera.set_position(cx - _mezza_larghezza_mappa, cy - _mezza_altezza_mappa);

    // Lo sprite 16x32 ha i piedi sull'ultima riga (31): il centro sta 15 pixel sopra.
    _giocatore.set_position(_e.x - _mezza_larghezza_mappa, _e.y - 15 - _mezza_altezza_mappa);
    _giocatore.set_z_order(z_della_fila(_e.y));
    _anima_giocatore();
    _anima_polvere();
    _segna_orme();
    _anima_compagni();

    // il fumetto oscilla di un pixel ogni FUMETTO_OSCILLA vblank (STANDARD I2)
    if(_fumetto_acceso)
    {
        int su = _oscilla >= mondo::FUMETTO_OSCILLA ? 1 : 0;
        _oscilla = avanti(_oscilla, 2 * mondo::FUMETTO_OSCILLA);
        _fumetto.set_position(_fumetto_x - _mezza_larghezza_mappa, _fumetto_y - su - _mezza_altezza_mappa);
        _fumetto.set_visible(true);
    }

    _aggiorna_aiuti();

    if(_attesa_etichetta > 0 && _etichetta_passo > 0)
    {
        if(--_etichetta_passo == 1)
        {
            _ombra.mostra(_testo_etichetta);
        }
        else
        {
            _etichetta.mostra(_testo_etichetta);
            _mostra_cartiglio(true);
        }
    }
    else if(_attesa_etichetta > 0)
    {
        _ombra.avanza();
        _etichetta.avanza();

        if(--_attesa_etichetta == 0)
        {
            _ombra.nascondi();
            _etichetta.nascondi();
            _mostra_cartiglio(false);
        }
    }
}

void Esplorazione::nascondi_etichetta()
{
    spegni_segnale();
    _attesa_etichetta = 0;
    _ombra.nascondi();
    _etichetta.nascondi();
    _mostra_cartiglio(false);
    _nascondi_aiuti();
}

void Esplorazione::scurisci(bool scura)
{
    // BUIO_MENU dei mockup (menu/mockup_menu.py): uno solo per tutti i menu
    constexpr int BUIO_CENTESIMI = 65;

    if(_fondale)
    {
        _fondale->set_blending_enabled(scura);
    }

    _giocatore.set_blending_enabled(scura);

    for(Compagno& c : _fila)
    {
        c.sprite.set_blending_enabled(scura);
    }

    _scura = scura;
    bn::blending::set_black_fade_color();
    bn::blending::set_fade_alpha(scura ? bn::fixed(BUIO_CENTESIMI) / 100 : bn::fixed(0));
}

int Esplorazione::schermo_x(int x) const
{
    return x - _camera.x().right_shift_integer() - _mezza_larghezza_mappa + LARGHEZZA_SCHERMO / 2;
}

int Esplorazione::schermo_y(int y) const
{
    return y - _camera.y().right_shift_integer() - _mezza_altezza_mappa + ALTEZZA_SCHERMO / 2;
}

void Esplorazione::_nascondi_aiuti()
{
    _promemoria_t = -1;
    _promemoria.reset();
    _promemoria_fondo.reset();
    _targa_nome.reset();
    _targa.reset();
    _varco_cartello = -1;
    _cartello_k = -1;
    _cartello_scrivi = 0;
    _cartello.reset();
    _oltre.reset();
    _cartello_fondo.reset();
}

aiuti::Rettangolo Esplorazione::_rettangolo_del_giocatore() const
{
    int x = schermo_x(_e.x);
    int y = schermo_y(_e.y);
    return { x - 8, y - 31, x + 7, y };
}

void Esplorazione::promemoria()
{
    if(! _aiuti || _dissolvenza)
    {
        return;
    }

    // l'etichetta d'area sta nella stessa fascia in alto: lascia il posto
    _attesa_etichetta = 0;
    _ombra.nascondi();
    _etichetta.nascondi();
    _mostra_cartiglio(false);

    _cerca_i_varchi(true);
    int meta = storia::area_dell_obiettivo(g_game_state);
    testi::TestoId testo = meta >= 0 ? storia::OBIETTIVO[g_game_state.obiettivo].testo : testi::TestoId::PROMEMORIA_NESSUNO;

    // il riquadro scuro con la stella e l'obiettivo (mockup 09), alto quanto le sue righe
    _promemoria.reset();
    _promemoria_fondo.reset();
    _targa_nome.reset();
    _targa.reset();
    int righe = testo::dati(testo).righe;
    _promemoria_alto = aiuti::altezza_promemoria(righe);
    int w = aiuti::PROMEMORIA_X1 - aiuti::PROMEMORIA_X0 + 1;
    _promemoria_fondo.emplace(aiuti::PROMEMORIA_X0, aiuti::PROMEMORIA_Y0, w, _promemoria_alto, _palette_aiuti);
    _promemoria_fondo->rett(0, 0, w - 1, _promemoria_alto - 1, pannello::SCURO);
    _promemoria_fondo->bordo(0, 0, w - 1, _promemoria_alto - 1, pannello::PIOMBO);
    _promemoria_fondo->disegno(aiuti::STELLA, aiuti::STELLA_X - aiuti::PROMEMORIA_X0, 5);
    _promemoria.emplace(testo::Contesto::DIALOGO, aiuti::PROMEMORIA_TESTO_X, aiuti::PROMEMORIA_Y0 + aiuti::PROMEMORIA_TESTO_DY,
                        pannello::CHIARO, _palette_aiuti);
    _promemoria->mostra(testo);
    _promemoria->rivela_tutto();

    // la targa: il nome della prossima area e la freccia verso il suo varco
    int varco = meta >= 0 ? aiuti::varco_verso_la_meta(_e, meta) : -1;

    if(varco >= 0)
    {
        const mondo::Area& a = mondo::area(_e.area);
        const mondo::Varco& v = mondo::varco_di(a, varco);
        testi::TestoId dove = v.destinazione >= 0 ? mondo::area(mondo::AreaId(v.destinazione)).etichetta : v.etichetta;
        aiuti::Punto c = _centri[varco];
        _targa_verso = aiuti::verso_di(c.x - _e.x, c.y - _e.y);
        int largo = larghezza_testo(dove);
        aiuti::Rettangolo cartello = _cartello_fondo ? aiuti::Rettangolo{ _cartello_fondo->x(), _cartello_fondo->y(),
                _cartello_fondo->x() + _cartello_fondo->larghezza() - 1, _cartello_fondo->y() + _cartello_fondo->altezza() - 1 } :
                aiuti::Rettangolo{ -100, -100, -90, -90 };
        aiuti::Rettangolo r = aiuti::posto_della_targa(largo, righe, _rettangolo_del_giocatore(), cartello);
        _targa_x = r.x0;
        _targa_y = r.y0;
        _targa.emplace(r.x0, r.y0, r.x1 - r.x0 + 1, aiuti::TARGA_ALTEZZA, _palette_aiuti);
        _targa->rett(0, 0, r.x1 - r.x0, aiuti::TARGA_ALTEZZA - 1, pannello::SCURO);
        _targa->bordo(0, 0, r.x1 - r.x0, aiuti::TARGA_ALTEZZA - 1, pannello::PIOMBO);
        _disegna_freccia_della_targa(false);
        _targa_nome.emplace(testo::Contesto::AREA, r.x0 + 4, r.y0 + 3, pannello::CHIARO, _palette_aiuti);
        _targa_nome->mostra(dove);
        _targa_nome->rivela_tutto();
    }

    _promemoria_t = 0;
    _anima_promemoria();
    BN_LOG("Promemoria: obiettivo ", int(g_game_state.obiettivo), " meta ", meta, " varco ", varco);
}

void Esplorazione::_disegna_freccia_della_targa(bool spenta)
{
    if(_targa)
    {
        aiuti::Verso v = _targa_verso;
        _targa->disegno_da([v](int x, int y) { return aiuti::pixel_freccia(v, x, y); }, _targa->larghezza() - 11, 4,
                           spenta);
    }
}

// A3: scende dall'alto in 5 vblank (la targa sale dal basso), sta 3 secondi con la freccia che lampeggia ogni mezzo
// secondo, poi esce come e' entrata.
void Esplorazione::_anima_promemoria()
{
    constexpr int E = aiuti::FRAME_ENTRATA_PROMEMORIA;
    constexpr int FERMO = E + 1 + aiuti::FRAME_PROMEMORIA;
    int t = _promemoria_t;
    int k = t <= E ? E - t : (t < FERMO ? 0 : t - FERMO + 1);

    if(k > E)
    {
        _promemoria_t = -1;
        _promemoria.reset();
        _promemoria_fondo.reset();
        _targa_nome.reset();
        _targa.reset();
        return;
    }

    int su = fuori_di<E>(k, _promemoria_alto + aiuti::PROMEMORIA_Y0);
    _promemoria_fondo->sposta(aiuti::PROMEMORIA_X0, aiuti::PROMEMORIA_Y0 - su);
    _promemoria->sposta(aiuti::PROMEMORIA_TESTO_X, aiuti::PROMEMORIA_Y0 + aiuti::PROMEMORIA_TESTO_DY - su);

    if(_targa)
    {
        // in basso esce dal basso; sotto il promemoria (posto_della_targa) esce con lui, dall'alto
        bool in_basso = _targa_y == aiuti::TARGA_Y0;
        int via = fuori_di<E>(k, in_basso ? aiuti::SCHERMO_A - _targa_y : _targa_y + aiuti::TARGA_ALTEZZA);
        int y = _targa_y + (in_basso ? via : -via);
        _targa->sposta(_targa_x, y);
        _targa_nome->sposta(_targa_x + 4, y + 3);

        if(k == 0 && t > E)
        {
            int fermo = t - E - 1;

            if(resto<aiuti::FRAME_LAMPO, FERMO>(fermo) == 0)
            {
                _disegna_freccia_della_targa((dividi<aiuti::FRAME_LAMPO, FERMO>(fermo) & 1) == 1);
            }
        }
    }
}

void Esplorazione::_mostra_aiuto(bn::optional<VistaTesto>& vista, testo::Contesto contesto, int x, int y, int inchiostro,
                                 testo::TestoId testo)
{
    if(! vista)
    {
        vista.emplace(contesto, x, y, inchiostro, _palette_aiuti);
    }

    vista->mostra(testo);
    vista->rivela_tutto();
}

bool Esplorazione::segnala_cartello()
{
    if(! _aiuti || _dissolvenza || _varco_cartello < 0 || ! _varchi_pronti)
    {
        return false;
    }

    aiuti::Punto p = aiuti::cartello_a_portata(_e, _varco_cartello, _centri[_varco_cartello].x);

    if(p.x < 0)
    {
        return false;
    }

    segnala(p.x, p.y, aiuti::ALTEZZA_CARTELLO);
    return true;
}

// Il cartello del varco (mockup 12): legno scuro col bordo di piombo e la cornicetta di luce, la freccia verso il
// varco, la via in chiaro e dove porta in pietra.
void Esplorazione::_crea_cartello(int varco)
{
#ifdef GUBBIO_PRESTAZIONI
    bn::timer t;
    int tempi[4];
    auto segna = [&](int k) { tempi[k] = t.elapsed_ticks() * 100 / bn::timers::ticks_per_frame(); t.restart(); };
#else
    auto segna = [](int) {};
#endif
    const mondo::Area& a = mondo::area(_e.area);
    const mondo::Varco& v = mondo::varco_di(a, varco);
    testi::TestoId dove = v.destinazione >= 0 ? mondo::area(mondo::AreaId(v.destinazione)).etichetta : v.etichetta;
    int k = aiuti::cartello(int(_e.area), v.destinazione);
    bool due = k >= 0;
    int largo = larghezza_testo(dove);

    if(due)
    {
        int l2 = larghezza_testo(cartelli::CARTELLO[k].oltre);
        largo = l2 > largo ? l2 : largo;
    }

    aiuti::Rettangolo r = aiuti::posto_del_cartello(largo, due, _rettangolo_del_giocatore());
    int w = r.x1 - r.x0 + 1;
    int h = r.y1 - r.y0 + 1;
    _cartello.reset();
    _oltre.reset();
    _cartello_fondo.reset();
    segna(0);
    _cartello_fondo.emplace(r.x0, r.y0, w, h, _palette_aiuti);
    _cartello_fondo->rett(0, 0, w - 1, h - 1, pannello::LEGNO);
    _cartello_fondo->bordo(0, 0, w - 1, h - 1, pannello::PIOMBO);
    _cartello_fondo->bordo(2, 2, w - 3, h - 3, pannello::LEGNO_LUCE);
    segna(1);
    aiuti::Punto c = _centri[varco];
    aiuti::Verso verso = aiuti::verso_di(c.x - _e.x, c.y - _e.y);
    _cartello_fondo->disegno_da([verso](int x, int y) { return aiuti::pixel_freccia(verso, x, y); }, 5, (h - 8) / 2);
    segna(2);
#ifdef GUBBIO_PRESTAZIONI
    BN_LOG("PREST cartello misure ", tempi[0], " fondo ", tempi[1], " freccia ", tempi[2]);
#endif
    // le due righe si scrivono nei due frame seguenti, una per frame (ognuna costa quasi mezzo frame): tutto
    // insieme il cartello faceva perdere un frame avvicinandosi al varco. Il cartello e' ancora fuori schermo.
    _cartello_dove = dove;
    _cartello_oltre = k;
    _cartello_scrivi = due ? 2 : 1;
    _cartello_x = r.x0;
    _cartello_y = r.y0;
    _cartello_k = aiuti::FRAME_ENTRATA_CARTELLO;
    _cartello_esce = false;
}

// A2: il cartello sale dal bordo di 8 px a vblank (scende dall'alto se sta in alto); allontanandosi esce allo stesso
// modo.
void Esplorazione::_anima_cartello()
{
    if(_cartello_k < 0 || ! _cartello_fondo)
    {
        return;
    }

    if(_cartello_scrivi > 0)
    {
        if(! _cartello)
        {
            _mostra_aiuto(_cartello, testo::Contesto::AREA, _cartello_x + 16, _cartello_y + 4, pannello::CHIARO, _cartello_dove);
        }
        else
        {
            _mostra_aiuto(_oltre, testo::Contesto::AREA, _cartello_x + 16, _cartello_y + 14, pannello::PIETRA,
                          cartelli::CARTELLO[_cartello_oltre].oltre);
        }

        --_cartello_scrivi;
    }

    bool in_alto = _cartello_y < aiuti::SCHERMO_A / 2;
    int via = _cartello_k * 8;
    int y = _cartello_y + (in_alto ? -via : via);
    _cartello_fondo->sposta(_cartello_x, y);

    if(_cartello)
    {
        _cartello->sposta(_cartello_x + 16, y + 4);
    }

    if(_oltre)
    {
        _oltre->sposta(_cartello_x + 16, y + 14);
    }

    if(_cartello_esce)
    {
        if(++_cartello_k > aiuti::FRAME_ENTRATA_CARTELLO)
        {
            _cartello_k = -1;
            _cartello.reset();
            _oltre.reset();
            _cartello_fondo.reset();
        }
    }
    else if(_cartello_k > 0 && _cartello_scrivi == 0)
    {
        --_cartello_k;
    }
}

void Esplorazione::_aggiorna_aiuti()
{
    if(! _aiuti)
    {
        return;
    }

    if(_promemoria_t >= 0)
    {
        ++_promemoria_t;
        _anima_promemoria();
    }

    // il cartello del varco vicino: compare a CELLE_CARTELLO celle, sparisce allontanandosi (se le opzioni lo
    // vogliono, MOP)
    _cerca_i_varchi(false);
    int varco = _dissolvenza || ! _varchi_pronti || ! opzioni::g_opzioni.cartelli ? -1 : aiuti::varco_vicino(_e);

    if(varco != _varco_cartello)
    {
        _varco_cartello = varco;

        if(varco >= 0)
        {
            _crea_cartello(varco);
        }
        else if(_cartello_fondo)
        {
            _cartello_esce = true;
            _cartello_k = _cartello_k < 0 ? 0 : _cartello_k;
        }
    }

    _anima_cartello();
}

}
