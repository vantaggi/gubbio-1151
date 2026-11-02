#include "storia_scena.h"

#include "bn_bg_palettes.h"
#include "bn_color.h"
#include "bn_core.h"
#include "bn_fixed.h"
#include "bn_keypad.h"
#include "bn_log.h"
#include "bn_sprite_palette_item.h"
#include "bn_sprite_shape_size.h"
#include "bn_sprite_tiles_ptr.h"

#include "battaglia_grafica.h"
#include "esplorazione.h"
#include "game_state.h"
#include "progressione.h"
#include "scena_battaglia.h"
#include "storia_logica.h"
#include "tabella.h"
#include "vista_testo.h"

namespace gubbio
{

namespace
{
    using testo::Contesto;
    using namespace storia;

    constexpr int INCHIOSTRO_CHIARO = 2;
    constexpr int NOME_Y = 104;
    constexpr int TESTO_Y = 118;
    constexpr int FRAME_CARTELLO = 90;
    constexpr int FRAME_AUTOMATICA = 3;
    constexpr int DISTANZA_PAROLA = 14;     // pixel fra i piedi del giocatore e quelli dell'NPC per parlarci

    bool s_dialogo_fotografato = false;

    void attendi(int frame)
    {
        for(int f = 0; f < frame; ++f)
        {
            ++g_game_state.frames;
            bn::core::update();
        }
    }

    // Le battute a schermo: il nome di chi parla sopra, il testo a macchina da scrivere sotto, A per
    // completare e poi per andare avanti. Lo sfondo si scurisce, il testo resta chiaro.
    void recita_battute(const Battuta* tabella, int prima, int quante, const bn::sprite_palette_ptr& palette_testo,
                        bool automatica)
    {
        VistaTesto nome(Contesto::HUD, 8, NOME_Y, INCHIOSTRO_CHIARO, palette_testo);
        VistaTesto testo(Contesto::DIALOGO, 8, TESTO_Y, INCHIOSTRO_CHIARO, palette_testo);

        for(int i = prima; i < prima + quante; ++i)
        {
            const Battuta& b = tabella[i];

            if(b.tipo == TipoBattuta::PERSONAGGIO)
            {
                nome.mostra(b.parlante);
                nome.rivela_tutto();
            }
            else
            {
                nome.nascondi();
            }

            testo.mostra(b.testo);

            if(automatica)
            {
                testo.rivela_tutto();
                attendi(FRAME_AUTOMATICA);

                // la prima battuta di un personaggio nella prova: l'istantanea del dialogo a schermo
                if(b.tipo == TipoBattuta::PERSONAGGIO && ! s_dialogo_fotografato)
                {
                    s_dialogo_fotografato = true;
                    attendi(20);
                    BN_LOG("Istantanea storia_dialogo");
                    attendi(30);
                }

                continue;
            }

            attendi(1);

            while(true)
            {
                if(! testo.completo())
                {
                    testo.avanza();

                    if(bn::keypad::a_pressed())
                    {
                        testo.rivela_tutto();
                    }
                }
                else if(bn::keypad::a_pressed())
                {
                    break;
                }

                attendi(1);
            }

            attendi(1);
        }
    }

    bn::sprite_palette_ptr palette_npc()
    {
        bn::color c[16];

        for(int i = 0; i < 16; ++i)
        {
            c[i] = bn::color(GUBBIO_VOCE(battaglia::grafica::PALETTE_NEMICI, i));
        }

        return bn::sprite_palette_ptr::create(bn::sprite_palette_item(bn::span<const bn::color>(c), bn::bpp_mode::BPP_4));
    }

    // Un NPC con la figura del giocatore e i colori dei popolani (le vesti chiare).
    bn::sprite_ptr crea_npc(const bn::sprite_palette_ptr& palette)
    {
        bn::sprite_tiles_ptr tiles = bn::sprite_tiles_ptr::allocate(4, bn::bpp_mode::BPP_4);
        bn::span<bn::tile> vram = *tiles.vram();

        for(int t = 0; t < 4; ++t)
        {
            for(int r = 0; r < 8; ++r)
            {
                vram[t].data[r] = GUBBIO_VOCE(mondo::TILE_GIOCATORE, t * 8 + r);
            }
        }

        return bn::sprite_ptr::create(0, 0, bn::sprite_shape_size(16, 16), bn::move(tiles), palette);
    }
}

bool Storia::recita(int k, Esplorazione* esplorazione, const bn::sprite_palette_ptr& palette_testo, bool automatica)
{
    const Scena& s = GUBBIO_VOCE(SCENA, k);
    BN_LOG("Scena ", s.codice);

    if(esplorazione)
    {
        esplorazione->nascondi_etichetta();
        bn::bg_palettes::set_fade(bn::color(0, 0, 0), bn::fixed(0.6));
    }

    if(s.cutscene)
    {
        // il nodo segnaposto delle cutscene: per ora il cartello col titolo, poi si passa oltre
        VistaTesto cartello(Contesto::DIALOGO, 16, 72, INCHIOSTRO_CHIARO, palette_testo);
        cartello.mostra(s.titolo);
        cartello.rivela_tutto();
        BN_LOG("Cutscene ", s.codice, " (segnaposto)");

        for(int f = 0; f < (automatica ? FRAME_AUTOMATICA : FRAME_CARTELLO) && ! bn::keypad::a_pressed(); ++f)
        {
            attendi(1);
        }
    }
    else
    {
        recita_battute(BATTUTA, s.prima_battuta, s.battute, palette_testo, automatica);
    }

    if(esplorazione)
    {
        bn::bg_palettes::set_fade(bn::color(0, 0, 0), 0);
    }

    attendi(1);

    if(s.battaglia >= 0)
    {
        if(automatica)
        {
            BN_LOG("Battaglia ", int(s.battaglia), " data per vinta");
        }
        else if(esplorazione)
        {
            svuota();
            esplorazione->sospendi();
            attendi(1);
            battaglia::Esito esito = scena_battaglia(s.battaglia, uint32_t(g_game_state.frames) | 1u, Guida::GIOCATORE,
                                                     palette_testo, false, &g_game_state);
            mondo::colloca(esplorazione->esploratore(), esplorazione->esploratore().area,
                           esito == battaglia::Esito::VITTORIA ? 0 : 1);
            esplorazione->ricompari();

            if(esito != battaglia::Esito::VITTORIA)
            {
                return false;   // la scena resta da giocare: si riprova rientrando nell'area
            }
        }

        // lo scontro della scena e' quello sulla mappa: vinto, il nemico non torna
        progressione::segna_vinto(g_game_state, progressione::Bandiera(s.battaglia));
    }

    chiudi_scena(g_game_state, k);
    return true;
}

void Storia::prologo(const bn::sprite_palette_ptr& palette_testo)
{
    for(int k = prossima_scena(g_game_state, NESSUNA_AREA); k >= 0; k = prossima_scena(g_game_state, NESSUNA_AREA))
    {
        recita(k, nullptr, palette_testo);
    }
}

void Storia::svuota()
{
    _npc.clear();
    _indici.clear();
    _area = -1;
}

void Storia::_prepara_npc(const Esplorazione& esplorazione)
{
    svuota();
    _area = int(esplorazione.esploratore().area);
    int fase = int(fase_npc(g_game_state));
    bn::sprite_palette_ptr palette = palette_npc();

    for(int i = 0; i < NPC; ++i)
    {
        const Npc& n = GUBBIO_VOCE(NPC_AMBIENTE, i);

        if(n.area == _area && GUBBIO_VOCE(n.frasi, fase) > 0)
        {
            bn::sprite_ptr sprite = crea_npc(palette);
            esplorazione.colloca_sulla_mappa(sprite, mondo::piedi_x(n.tx), mondo::piedi_y(n.ty), 14);
            _npc.push_back(bn::move(sprite));
            _indici.push_back(i);
        }
    }
}

bool Storia::aggiorna(Esplorazione& esplorazione, const bn::sprite_palette_ptr& palette_testo)
{
    const mondo::Esploratore& e = esplorazione.esploratore();

    if(int(e.area) != _area)
    {
        _prepara_npc(esplorazione);
    }

    if(esplorazione.in_dissolvenza())
    {
        return false;
    }

    int k = prossima_scena(g_game_state, int(e.area));

    if(k >= 0)
    {
        recita(k, &esplorazione, palette_testo);
        svuota();       // la fase puo' essere cambiata: gli NPC si rifanno al prossimo frame
        return true;
    }

    if(! bn::keypad::a_pressed())
    {
        return false;
    }

    for(int j = 0; j < _indici.size(); ++j)
    {
        const Npc& n = GUBBIO_VOCE(NPC_AMBIENTE, _indici[j]);
        int dx = e.x - mondo::piedi_x(n.tx);
        int dy = e.y - mondo::piedi_y(n.ty);

        if(dx > -DISTANZA_PAROLA && dx < DISTANZA_PAROLA && dy > -DISTANZA_PAROLA && dy < DISTANZA_PAROLA)
        {
            int fase = int(fase_npc(g_game_state));
            esplorazione.nascondi_etichetta();
            bn::bg_palettes::set_fade(bn::color(0, 0, 0), bn::fixed(0.6));
            attendi(1);
            recita_battute(FRASE_NPC, GUBBIO_VOCE(n.prima_frase, fase), GUBBIO_VOCE(n.frasi, fase), palette_testo, false);
            bn::bg_palettes::set_fade(bn::color(0, 0, 0), 0);
            attendi(1);
            return true;
        }
    }

    return false;
}

void prova_storia(const bn::sprite_palette_ptr& palette_testo)
{
    progressione::partita_nuova(g_game_state);
    Storia storia;
    int visitate = 0;
    bool avanti = true;

    // lo stesso giro di storia::gioca_tutta, ma recitando ogni scena a schermo
    while(avanti)
    {
        avanti = false;

        for(int area = NESSUNA_AREA; area < mondo::AREE_CONTEGGIO && ! avanti; ++area)
        {
            int k = prossima_scena(g_game_state, area);

            if(k >= 0 && storia.recita(k, nullptr, palette_testo, true))
            {
                ++visitate;
                avanti = true;
            }
        }
    }

    int mancanti = 0;

    for(int k = 0; k < SCENE; ++k)
    {
        if(! fatta(g_game_state, k))
        {
            BN_LOG("Scena NON visitata: ", GUBBIO_VOCE(SCENA, k).codice);
            ++mancanti;
        }
    }

    BN_LOG("Istantanee finite");
    BN_LOG("Storia: ", visitate, " scene visitate su ", SCENE, ", ", mancanti, " mancanti, titoli di coda ",
           accesa(g_game_state, Bandiera::CRONACA_V1_FINITA) ? "raggiunti" : "NON raggiunti");

    while(true)
    {
        bn::core::update();
    }
}

}
