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
#include "regia_logica.h"
#include "regia_scena.h"
#include "scena_battaglia.h"
#include "scontri_mappa.h"
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
    constexpr int FRAME_TITOLI = 300;
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

    // Un NPC con la figura del suo mestiere (FIGURA_NPC) e i colori dei popolani.
    bn::sprite_ptr crea_npc(const bn::sprite_palette_ptr& palette, int figura)
    {
        bn::sprite_tiles_ptr tiles = bn::sprite_tiles_ptr::allocate(4, bn::bpp_mode::BPP_4);
        bn::span<bn::tile> vram = *tiles.vram();

        for(int t = 0; t < 4; ++t)
        {
            for(int r = 0; r < 8; ++r)
            {
                vram[t].data[r] = GUBBIO_VOCE(GUBBIO_VOCE(FIGURA_NPC, figura), t * 8 + r);
            }
        }

        return bn::sprite_ptr::create(0, 0, bn::sprite_shape_size(16, 16), bn::move(tiles), palette);
    }
}

// Una cutscene del copione di regia: usa tutti e quattro i BG, lo sfondo dell'area si libera e torna
// dopo. Una gia' vista non riparte da sola.
void Storia::recita_regia(int regia, Esplorazione* esplorazione, const bn::sprite_palette_ptr& palette_testo,
                          bool automatica)
{
    if(regia::vista(g_game_state, regia))
    {
        BN_LOG("Cutscene ", GUBBIO_VOCE(regia::CUTSCENE_DATI, regia).codice, " gia' vista");
        return;
    }

    if(esplorazione)
    {
        svuota();
        bn::bg_palettes::set_fade(bn::color(0, 0, 0), 0);
        esplorazione->sospendi();
        attendi(1);
    }

    recita_cutscene(regia, palette_testo, false, automatica);

    if(esplorazione)
    {
        esplorazione->ricompari();
    }
}

bool Storia::recita(int k, Esplorazione* esplorazione, const bn::sprite_palette_ptr& palette_testo, bool automatica,
                    bool battaglia_col_pilota)
{
    const Scena& s = GUBBIO_VOCE(SCENA, k);
    BN_LOG("Scena ", s.codice);

    if(esplorazione)
    {
        esplorazione->nascondi_etichetta();
        bn::bg_palettes::set_fade(bn::color(0, 0, 0), bn::fixed(0.6));
    }

    if(s.cutscene && s.regia >= 0)
    {
        // la cutscene del copione di regia; una gia' vista non riparte da sola
        if(regia::vista(g_game_state, s.regia))
        {
            BN_LOG("Cutscene ", s.codice, " gia' vista");
        }
        else
        {
            recita_regia(s.regia, esplorazione, palette_testo, automatica);
        }
    }
    else if(s.cutscene && s.regia == -2)
    {
        BN_LOG("Cutscene ", s.codice, " dentro la precedente");
    }
    else if(s.cutscene)
    {
        // il nodo segnaposto: il cartello col titolo, poi si passa oltre
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
        // le battute, spezzate dove entra una cutscene (INSERTO)
        int da = s.prima_battuta;

        for(int i = 0; i < INSERTI; ++i)
        {
            const Inserto& n = GUBBIO_VOCE(INSERTO, i);

            if(n.battuta >= s.prima_battuta && n.battuta < s.prima_battuta + s.battute)
            {
                recita_battute(BATTUTA, da, n.battuta - da, palette_testo, automatica);
                da = n.battuta;
                recita_regia(n.regia, esplorazione, palette_testo, automatica);

                if(esplorazione)
                {
                    bn::bg_palettes::set_fade(bn::color(0, 0, 0), bn::fixed(0.6));
                }
            }
        }

        recita_battute(BATTUTA, da, s.prima_battuta + s.battute - da, palette_testo, automatica);
    }

    if(esplorazione)
    {
        bn::bg_palettes::set_fade(bn::color(0, 0, 0), 0);
    }

    attendi(1);

    if(s.battaglia >= 0)
    {
        if(automatica && ! battaglia_col_pilota)
        {
            BN_LOG("Battaglia ", int(s.battaglia), " data per vinta");
        }
        else if(esplorazione)
        {
            svuota();
            esplorazione->sospendi();
            attendi(1);
            battaglia::Esito esito = scena_battaglia(s.battaglia, automatica ? 1u : (uint32_t(g_game_state.frames) | 1u),
                                                     automatica ? Guida::PILOTA : Guida::GIOCATORE, palette_testo,
                                                     automatica, &g_game_state);
            mondo::colloca(esplorazione->esploratore(), esplorazione->esploratore().area,
                           esito == battaglia::Esito::VITTORIA ? 0 : 1);
            esplorazione->ricompari();

            if(esito != battaglia::Esito::VITTORIA)
            {
                return false;   // la scena resta da giocare: si riprova rientrando nell'area
            }
        }

        // lo scontro della scena e' quello sulla mappa: vinto, il nemico non torna
        if(s.battaglia < progressione::SCONTRI)
        {
            progressione::segna_vinto(g_game_state, progressione::Bandiera(s.battaglia));
        }
    }

    bool finita_prima = accesa(g_game_state, Bandiera::CRONACA_V1_FINITA);
    chiudi_scena(g_game_state, k);

    // i titoli di coda: la cronaca della v1 e' finita (il resto arriva con gli aggiornamenti)
    if(! finita_prima && accesa(g_game_state, Bandiera::CRONACA_V1_FINITA))
    {
        BN_LOG("Titoli di coda");
        VistaTesto fine(Contesto::DIALOGO, 16, 72, INCHIOSTRO_CHIARO, palette_testo);
        fine.mostra(testi::TestoId::STORIA_FINE);
        fine.rivela_tutto();
        attendi(automatica ? FRAME_AUTOMATICA : FRAME_TITOLI);
    }

    return true;
}

void Storia::prologo(const bn::sprite_palette_ptr& palette_testo, bool automatica)
{
    for(int k = prossima_scena(g_game_state, NESSUNA_AREA); k >= 0; k = prossima_scena(g_game_state, NESSUNA_AREA))
    {
        recita(k, nullptr, palette_testo, automatica);
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
            bn::sprite_ptr sprite = crea_npc(palette, n.figura);
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

    // le scene con una battaglia partono toccando il loro nemico sulla mappa (ScontriSullaMappa);
    // quelle con una battaglia senza nemico sulla mappa (il rito) partono entrando, come le altre
    int k = -1;

    for(int j = 0; j < SCENE && k < 0; ++j)
    {
        int b = GUBBIO_VOCE(SCENA, j).battaglia;

        if((b < 0 || b >= progressione::SCONTRI) && pronta(g_game_state, j, int(e.area)))
        {
            k = j;
        }
    }

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

namespace gubbio
{

void prova_figure_npc(Esplorazione& esplorazione)
{
    esplorazione.entra(mondo::AreaId::PIAZZA_GRANDE, 0);
    bn::sprite_palette_ptr palette = palette_npc();
    bn::vector<bn::sprite_ptr, FIGURE_NPC> figure;
    const mondo::Esploratore& e = esplorazione.esploratore();

    for(int f = 0; f < FIGURE_NPC; ++f)
    {
        bn::sprite_ptr sprite = crea_npc(palette, f);
        esplorazione.colloca_sulla_mappa(sprite, e.x + (f - 2) * 20, e.y - 24, 14);
        figure.push_back(bn::move(sprite));
    }

    for(int f = 0; f < 90; ++f)
    {
        esplorazione.aggiorna();
        bn::core::update();
    }

    BN_LOG("Istantanea figure_npc");

    for(int f = 0; f < 60; ++f)
    {
        esplorazione.aggiorna();
        bn::core::update();
    }

    BN_LOG("Istantanee finite");

    while(true)
    {
        bn::core::update();
    }
}

void prova_prologo(Esplorazione& esplorazione, const bn::sprite_palette_ptr& palette_testo)
{
    progressione::partita_nuova(g_game_state);
    Storia storia;

    // il prologo (la cutscene C1) prima di entrare in citta': lo sfondo dell'area non c'e' ancora
    esplorazione.sospendi();
    attendi(1);
    storia.prologo(palette_testo, true);

    // l'ultimatum a Piazza Grande
    esplorazione.entra(mondo::AreaId::PIAZZA_GRANDE, 0);
    attendi(30);
    storia.recita(prossima_scena(g_game_state, int(mondo::AreaId::PIAZZA_GRANDE)), &esplorazione, palette_testo, true);

    // la postierla di San Martino
    esplorazione.entra(mondo::AreaId::SAN_MARTINO, 1);
    attendi(30);
    storia.recita(prossima_scena(g_game_state, int(mondo::AreaId::SAN_MARTINO)), &esplorazione, palette_testo, true);

    // il Teatro: la Pattuglia sulla mappa, che adesso c'e'
    esplorazione.entra(mondo::AreaId::TEATRO_ROMANO, 1);
    ScontriSullaMappa scontri(&storia);

    for(int f = 0; f < 90; ++f)
    {
        esplorazione.aggiorna();
        scontri.aggiorna(esplorazione, palette_testo);

        if(f == 70)
        {
            BN_LOG("Istantanea prologo_pattuglia");
        }

        attendi(1);
    }

    bool pattuglia_vista = scontri.visibili() > 0;
    scontri.svuota();
    bool salvato = storia.recita(scena_dello_scontro(INCONTRO_DEL_TEATRO), &esplorazione, palette_testo, true, true);

    BN_LOG("Prologo: Giorgio nel gruppo ", accesa(g_game_state, Bandiera::GIORGIO_NEL_GRUPPO) ? "si" : "NO",
           ", Pattuglia sulla mappa ", pattuglia_vista ? "si" : "NO",
           ", Antonio salvato ", salvato && accesa(g_game_state, Bandiera::ANTONIO_NEL_GRUPPO) ? "si" : "NO",
           ", gruppo ", int(gruppo(g_game_state, 1)), ", Pattuglia sulla mappa dopo ",
           scontro_attivo(g_game_state, INCONTRO_DEL_TEATRO) ? "ANCORA" : "sparita");
    BN_LOG("Istantanee finite");
}

}
