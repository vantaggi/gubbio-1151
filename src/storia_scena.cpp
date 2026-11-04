#include "storia_scena.h"

#include "bn_bg_palettes.h"
#include "bn_color.h"
#include "bn_core.h"
#include "bn_fixed.h"
#include "bn_keypad.h"
#include "bn_log.h"
#include "bn_sprite_palette_item.h"
#include "bn_sprite_palettes.h"
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

    int s_voce_automatica = 0;              // la voce che prende ogni menu nelle prove senza tasti
    int s_scelte_fotografate = 0;           // le istantanee dei menu nelle prove

    constexpr int MENU_X = 32;                  // le voci dentro il riquadro del dialogo (y 104-160)
    constexpr int MENU_Y = 120;
    constexpr int MENU_PASSO = 16;

    // Il cursore del menu: un triangolo pieno verso destra, nell'inchiostro chiaro del testo.
    bn::sprite_ptr crea_cursore(const bn::sprite_palette_ptr& palette_testo)
    {
        bn::sprite_tiles_ptr tiles = bn::sprite_tiles_ptr::allocate(1, bn::bpp_mode::BPP_4);
        bn::span<bn::tile> vram = *tiles.vram();

        for(int r = 0; r < 8; ++r)
        {
            uint32_t riga = 0;
            int largo = r < 4 ? r + 1 : 7 - r;

            for(int x = 1; x <= largo && r < 7; ++x)
            {
                riga |= uint32_t(INCHIOSTRO_CHIARO) << (4 * x);
            }

            vram[0].data[r] = riga;
        }

        return bn::sprite_ptr::create(0, 0, bn::sprite_shape_size(8, 8), bn::move(tiles), palette_testo);
    }

    // Il menu di una scelta nella vista di gioco, sullo sfondo scurito come nei dialoghi: due voci, su e
    // giu' per spostarsi, A per scegliere. La voce col cursore e' chiara, l'altra in ombra.
    int menu_scelta(const Battuta& b, const bn::sprite_palette_ptr& palette_testo, bool automatica)
    {
        int voce = 0;
        bool cambiata = true;
        bn::optional<VistaTesto> voci[2];
        int attesa = 0;
        bn::sprite_ptr cursore = crea_cursore(palette_testo);
        bn::bg_palettes::set_fade(bn::color(0, 0, 0), bn::fixed(0.6));     // come nei dialoghi: lo sfondo scuro

        while(true)
        {
            if(cambiata)
            {
                for(int k = 0; k < 2; ++k)
                {
                    voci[k].reset();
                    voci[k].emplace(Contesto::SCELTA, MENU_X, MENU_Y + k * MENU_PASSO, k == voce ? INCHIOSTRO_CHIARO : 1,
                                    palette_testo);
                    voci[k]->mostra(k == 0 ? b.testo : b.parlante);
                    voci[k]->rivela_tutto();
                }

                // le coordinate degli sprite partono dal centro dello schermo
                cursore.set_position(MENU_X - 12 - 120 + 4, MENU_Y + voce * MENU_PASSO - 80 + 4);

                cambiata = false;
            }

            attendi(1);

            if(automatica)
            {
                // la prova: un secondo col menu aperto e il cursore sulla prima voce, l'istantanea, poi la voce
                if(++attesa == 60)
                {
                    BN_LOG("Istantanea scelta_", s_scelte_fotografate++);
                }
                else if(attesa == 80)
                {
                    BN_LOG("Scelta ", s_voce_automatica);
                    return s_voce_automatica;
                }

                continue;
            }

            if(bn::keypad::up_pressed() || bn::keypad::down_pressed())
            {
                voce = 1 - voce;
                cambiata = true;
            }
            else if(bn::keypad::a_pressed())
            {
                BN_LOG("Scelta ", voce);
                return voce;
            }
        }
    }

    // Le battute a schermo: il nome di chi parla sopra, il testo a macchina da scrivere sotto, A per
    // completare e poi per andare avanti. Lo sfondo si scurisce, il testo resta chiaro.
    void recita_battute(const Battuta* tabella, int prima, int quante, const bn::sprite_palette_ptr& palette_testo,
                        bool automatica, bool npc = false)
    {
        VistaTesto nome(Contesto::HUD, 8, NOME_Y, INCHIOSTRO_CHIARO, palette_testo);
        VistaTesto testo(Contesto::DIALOGO, 8, TESTO_Y, INCHIOSTRO_CHIARO, palette_testo);
        int scelta = -1;

        // un NPC: la prima variante "(se BANDIERA)" che vale parla da sola, se no le altre righe
        int sola = npc ? variante_che_vale(g_game_state, tabella, prima, quante) : -1;

        if(sola >= 0)
        {
            prima = sola;
            quante = 1;
        }

        for(int i = prima; i < prima + quante; ++i)
        {
            const Battuta& b = tabella[i];

            if((sola < 0 && variante(b.guardia)) || (sola < 0 && ! vale(g_game_state, b.guardia, scelta)))
            {
                continue;
            }

            if(b.tipo == TipoBattuta::SCELTA)
            {
                nome.nascondi();
                testo.nascondi();
                scelta = menu_scelta(b, palette_testo, automatica);
                scegli(g_game_state, b, scelta);
                continue;
            }

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

    constexpr int ALTEZZA_NPC = 30;      // lo sprite e' 16x32: i piedi due pixel sopra il bordo in basso

    // Un NPC con la sua figura (FIGURA_NPC, 16x32) e i colori dei popolani.
    bn::sprite_ptr crea_npc(const bn::sprite_palette_ptr& palette, int figura)
    {
        bn::sprite_tiles_ptr tiles = bn::sprite_tiles_ptr::allocate(8, bn::bpp_mode::BPP_4);
        bn::span<bn::tile> vram = *tiles.vram();

        for(int t = 0; t < 8; ++t)
        {
            for(int r = 0; r < 8; ++r)
            {
                vram[t].data[r] = GUBBIO_VOCE(GUBBIO_VOCE(FIGURA_NPC, figura), t * 8 + r);
            }
        }

        return bn::sprite_ptr::create(0, 0, bn::sprite_shape_size(16, 32), bn::move(tiles), palette);
    }

    // Dove sta un NPC adesso: quelli del borgo, con BORGO_DENTRO, nel digiuno e nella notte stanno
    // accampati in Sant'Andrea, dietro Porta Romana.
    struct Posto
    {
        int area;
        int tx;
        int ty;
    };

    Posto posto(const Npc& n)
    {
        if(n.del_borgo && accesa(g_game_state, Bandiera::BORGO_DENTRO) && fase_npc(g_game_state) != Fase::ULTIMATUM)
        {
            return { int(mondo::AreaId::SANT_ANDREA), n.tx_borgo, n.ty_borgo };
        }

        return { n.area, n.tx, n.ty };
    }

    // Dove sta una persona della lista di Storia: un NPC d'ambiente, un datore (NPC + quest), l'infiltrato.
    Posto posto_di(int indice)
    {
        if(indice < NPC)
        {
            return posto(GUBBIO_VOCE(NPC_AMBIENTE, indice));
        }

        if(indice < NPC + QUEST)
        {
            const QuestGioco& g = GUBBIO_VOCE(QUEST_GIOCO, indice - NPC);
            return { g.area, g.tx, g.ty };
        }

        return { INFILTRATO.area, INFILTRATO.tx, INFILTRATO.ty };
    }

    constexpr int ALTEZZA_RACCOLTA = 14;    // l'oggetto 16x16 poggia sui piedi della sua cella

    // Un oggetto da raccogliere con la sua figura (FIGURA_RACCOLTA, 16x16) e i colori dei popolani.
    bn::sprite_ptr crea_raccolta(const bn::sprite_palette_ptr& palette, int figura)
    {
        bn::sprite_tiles_ptr tiles = bn::sprite_tiles_ptr::allocate(4, bn::bpp_mode::BPP_4);
        bn::span<bn::tile> vram = *tiles.vram();

        for(int t = 0; t < 4; ++t)
        {
            for(int r = 0; r < 8; ++r)
            {
                vram[t].data[r] = GUBBIO_VOCE(GUBBIO_VOCE(FIGURA_RACCOLTA, figura), t * 8 + r);
            }
        }

        return bn::sprite_ptr::create(0, 0, bn::sprite_shape_size(16, 16), bn::move(tiles), palette);
    }

    // Le righe di FRASE_QUEST nel riquadro del dialogo, con lo sfondo scurito come per gli NPC.
    void dialogo_inizio(Esplorazione* esplorazione)
    {
        if(esplorazione)
        {
            esplorazione->nascondi_etichetta();
        }

        bn::bg_palettes::set_fade(bn::color(0, 0, 0), bn::fixed(0.6));
        attendi(1);
    }

    void dialogo_fine()
    {
        bn::bg_palettes::set_fade(bn::color(0, 0, 0), 0);
        attendi(1);
    }

    void recita_righe(const Righe& r, const bn::sprite_palette_ptr& palette_testo)
    {
        if(r.quante > 0)
        {
            recita_battute(FRASE_QUEST, r.prima, r.quante, palette_testo, false);
        }
    }

    // Una riga del SISTEMA nel riquadro del dialogo (i forzieri, l'uscita chiusa del Condotto).
    void di_sistema(testi::TestoId id, Esplorazione* esplorazione, const bn::sprite_palette_ptr& palette_testo)
    {
        const Battuta b = { id, id, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { NESSUNA_BANDIERA, NESSUNA_BANDIERA }, -1 };
        dialogo_inizio(esplorazione);
        recita_battute(&b, 0, 1, palette_testo, false);
        dialogo_fine();
    }

    // Il lampo dei miasmi: lo schermo vira verso il verde della nebbia (la voce 11 della palette cupa) e torna.
    // Forte e due volte alla prima nebbia (B-02), appena accennato a ogni ferita.
    void lampo(int volte, bn::fixed forza)
    {
        bn::color verde(GUBBIO_VOCE(mondo::PALETTE_FONDALI_CUPA, 11));
        constexpr int PASSI = 8;

        for(int v = 0; v < volte; ++v)
        {
            for(int f = 0; f < PASSI; ++f)
            {
                bn::bg_palettes::set_fade(verde, forza * (PASSI - f) / PASSI);
                bn::sprite_palettes::set_fade(verde, forza * (PASSI - f) / PASSI / 2);
                attendi(1);
            }
        }

        bn::bg_palettes::set_fade(verde, 0);
        bn::sprite_palettes::set_fade(verde, 0);
    }

    // Chi sale di livello con l'esperienza di una quest: le stesse frasi della battaglia, come SISTEMA.
    void annuncia_livelli(const bool (&saliti)[battaglia::EROI], const bn::sprite_palette_ptr& palette_testo)
    {
        constexpr testi::TestoId SALE[battaglia::EROI] = { testi::TestoId::BATT_SALE_UBALDO, testi::TestoId::BATT_SALE_GIORGIO,
                                                          testi::TestoId::BATT_SALE_ANTONIO };

        for(int e = 0; e < battaglia::EROI; ++e)
        {
            if(saliti[e])
            {
                const Battuta b = { GUBBIO_VOCE(SALE, e), GUBBIO_VOCE(SALE, e), TipoBattuta::SISTEMA, Espressione::CALMO, 0,
                                    { NESSUNA_BANDIERA, NESSUNA_BANDIERA }, -1 };
                recita_battute(&b, 0, 1, palette_testo, false);
            }
        }
    }
}

// Una cutscene del copione di regia: usa tutti e quattro i BG, lo sfondo dell'area si libera e torna
// dopo. Una gia' vista non riparte da sola (e ritorna false).
bool Storia::recita_regia(int regia, Esplorazione* esplorazione, const bn::sprite_palette_ptr& palette_testo,
                          bool automatica)
{
    if(regia::vista(g_game_state, regia))
    {
        BN_LOG("Cutscene ", GUBBIO_VOCE(regia::CUTSCENE_DATI, regia).codice, " gia' vista");
        return false;
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

    return true;
}

bool Storia::recita(int k, Esplorazione* esplorazione, const bn::sprite_palette_ptr& palette_testo, bool automatica,
                    bool battaglia_col_pilota)
{
    const Scena& s = GUBBIO_VOCE(SCENA, k);
    BN_LOG("Scena ", s.codice);
    // il duello gia' incontrato (CORRADO_INCONTRATO): al secondo tentativo niente battute, dritti alla battaglia
    bool salta_le_battute = gia_incontrata(g_game_state, k);

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
    else if(salta_le_battute)
    {
        BN_LOG("Scena ", s.codice, " gia' incontrata: si torna al duello");
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

                // le battute del narratore che la cutscene ha detto nelle bande non si ripetono; se era gia'
                // vista (la scena rigiocata dopo una battaglia persa) si leggono nella vista di gioco
                if(recita_regia(n.regia, esplorazione, palette_testo, automatica))
                {
                    da += n.copre;
                }

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
        // l'incontro e' avvenuto anche se la battaglia si perde: l'uscita del Condotto si chiude (varco_chiuso)
        all_incontro(g_game_state, k);

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
    _raccolte.clear();
    _gola.clear();
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

        Posto qui = posto(n);

        if(qui.area == _area && GUBBIO_VOCE(n.frasi, fase) > 0)
        {
            bn::sprite_ptr sprite = crea_npc(palette, n.figura);
            esplorazione.colloca_sulla_mappa(sprite, mondo::piedi_x(qui.tx), mondo::piedi_y(qui.ty), ALTEZZA_NPC);
            _npc.push_back(bn::move(sprite));
            _indici.push_back(i);
        }
    }

    // i datori delle quest, da quando la quest si prende (e, consegnata, per il dopo)
    for(int q = 0; q < QUEST; ++q)
    {
        const QuestGioco& g = GUBBIO_VOCE(QUEST_GIOCO, q);

        if(g.area == _area && momento_del_datore(g_game_state, q) != Momento::ASSENTE)
        {
            bn::sprite_ptr sprite = crea_npc(palette, g.figura);
            esplorazione.colloca_sulla_mappa(sprite, mondo::piedi_x(g.tx), mondo::piedi_y(g.ty), ALTEZZA_NPC);
            _npc.push_back(bn::move(sprite));
            _indici.push_back(NPC + q);
        }
    }

    // l'infiltrato sotto le Logge, con i tre indizi
    if(INFILTRATO.area == _area && infiltrato_presente(g_game_state))
    {
        bn::sprite_ptr sprite = crea_npc(palette, INFILTRATO.figura);
        esplorazione.colloca_sulla_mappa(sprite, mondo::piedi_x(INFILTRATO.tx), mondo::piedi_y(INFILTRATO.ty), ALTEZZA_NPC);
        _npc.push_back(bn::move(sprite));
        _indici.push_back(NPC + QUEST);
    }

    // i soldati di B-03 oltre l'arco, finche' il piano di Corrado non e' ascoltato
    for(int k = 0; k < SENTINELLE && sentinelle_presenti(g_game_state); ++k)
    {
        const Sentinella& s = GUBBIO_VOCE(SENTINELLA, k);

        if(s.area == _area)
        {
            bn::sprite_ptr sprite = crea_npc(palette, s.figura);
            sprite.set_horizontal_flip(true);       // guardano verso valle, verso l'arco
            esplorazione.colloca_sulla_mappa(sprite, mondo::piedi_x(s.tx), mondo::piedi_y(s.ty), ALTEZZA_NPC);
            _gola.push_back(bn::move(sprite));
        }
    }

    // i forzieri negli slarghi: chiusi, o aperti se gia' presi
    for(int k = 0; k < FORZIERI; ++k)
    {
        const Forziere& f = GUBBIO_VOCE(FORZIERE, k);

        if(f.area == _area)
        {
            bn::sprite_ptr sprite = crea_raccolta(palette, forziere_chiuso(g_game_state, k) ? FIGURA_FORZIERE
                                                                                             : FIGURA_FORZIERE_APERTO);
            esplorazione.colloca_sulla_mappa(sprite, mondo::piedi_x(f.tx), mondo::piedi_y(f.ty), ALTEZZA_RACCOLTA);
            _gola.push_back(bn::move(sprite));
        }
    }

    // gli oggetti da raccogliere ancora al loro posto
    for(int k = 0; k < RACCOLTE; ++k)
    {
        const Raccolta& r = GUBBIO_VOCE(RACCOLTA, k);

        if(r.area == _area && raccolta_presente(g_game_state, k))
        {
            bn::sprite_ptr sprite = crea_raccolta(palette, r.figura);
            esplorazione.colloca_sulla_mappa(sprite, mondo::piedi_x(r.tx), mondo::piedi_y(r.ty), ALTEZZA_RACCOLTA);
            _raccolte.push_back(bn::move(sprite));
        }
    }
}

// Il datore di una quest: la proposta (la quest e' presa e, se l'obiettivo e' gia' finito, segue la
// consegna), l'attesa, la consegna (storia::consegna_quest(): premio, 55 punti, una volta sola), il dopo.
void Storia::_parla_col_datore(int q, const bn::sprite_palette_ptr& palette_testo)
{
    Momento m = momento_del_datore(g_game_state, q);
    BN_LOG("Datore ", GUBBIO_VOCE(QUEST_V1, q).codice, " momento ", int(m));

    if(m == Momento::PROPOSTA)
    {
        recita_righe(righe_del_datore(g_game_state, q, m), palette_testo);
        prendi_quest(g_game_state, q);
        m = momento_del_datore(g_game_state, q) == Momento::CONSEGNA ? Momento::CONSEGNA : Momento::ASSENTE;
    }
    else if(m == Momento::ATTESA || m == Momento::DOPO)
    {
        recita_righe(righe_del_datore(g_game_state, q, m), palette_testo);
    }

    if(m == Momento::CONSEGNA)
    {
        recita_righe(righe_del_datore(g_game_state, q, m), palette_testo);
        bool saliti[battaglia::EROI] = {};

        if(consegna_quest(g_game_state, q, saliti))
        {
            BN_LOG("Quest ", GUBBIO_VOCE(QUEST_V1, q).codice, " consegnata");
            annuncia_livelli(saliti, palette_testo);
        }
    }
}

// L'infiltrato: le sue battute, la battaglia (non si fugge: persa, si torna all'ingresso dell'area e lui
// resta), vinta la Rosa e le battute di dopo.
void Storia::_affronta_l_infiltrato(Esplorazione& esplorazione, const bn::sprite_palette_ptr& palette_testo)
{
    recita_righe(INFILTRATO.prima, palette_testo);
    dialogo_fine();
    mondo::AreaId area = esplorazione.esploratore().area;
    svuota();
    esplorazione.sospendi();
    attendi(1);
    battaglia::Esito esito = scena_battaglia(INFILTRATO.incontro, uint32_t(g_game_state.frames) | 1u, Guida::GIOCATORE,
                                             palette_testo, false, &g_game_state);
    BN_LOG("Infiltrato: esito ", int(esito));

    if(esito != battaglia::Esito::VITTORIA)
    {
        mondo::colloca(esplorazione.esploratore(), area, 1);
    }

    esplorazione.ricompari();

    if(esito == battaglia::Esito::VITTORIA && riprendi_la_rosa(g_game_state))
    {
        dialogo_inizio(&esplorazione);
        recita_righe(INFILTRATO.dopo, palette_testo);
    }
}

bool Storia::aggiorna(Esplorazione& esplorazione, const bn::sprite_palette_ptr& palette_testo)
{
    const mondo::Esploratore& e = esplorazione.esploratore();

    if(int(e.area) != _area)
    {
        all_ingresso(g_game_state, int(e.area));
        _prepara_npc(esplorazione);
    }

    // l'uscita del Condotto chiusa durante il duello (T2): si urta come un muro, e lo si dice
    esplorazione.chiudi_varco(varco_chiuso(g_game_state, int(e.area)));

    if(esplorazione.in_dissolvenza())
    {
        return false;
    }

    if(esplorazione.urto_al_varco_chiuso() && g_game_state.frames - _ultimo_urto > 120)
    {
        _ultimo_urto = g_game_state.frames;
        di_sistema(testi::TestoId::CONDOTTO_CHIUSO, &esplorazione, palette_testo);
        return true;
    }

    // la cella sotto i piedi: le scene della gola partono su una cella (la nebbia, l'arco), i miasmi la leggono
    int cella = mondo::cella(mondo::area(e.area), mondo::cella_x(e), mondo::cella_y(e));

    // le scene con una battaglia partono toccando il loro nemico sulla mappa (ScontriSullaMappa);
    // quelle con una battaglia senza nemico sulla mappa (il rito) partono entrando, come le altre
    int k = -1;

    for(int j = 0; j < SCENE && k < 0; ++j)
    {
        int b = GUBBIO_VOCE(SCENA, j).battaglia;

        if((b < 0 || b >= progressione::SCONTRI) && pronta_qui(g_game_state, j, int(e.area), cella))
        {
            k = j;
        }
    }

    if(k >= 0)
    {
        // la prima nebbia (B-02): il lampo verde, poi l'avviso di Ubaldo, che accende MIASMI_VISTI
        if(cella_dell_innesco(k) == int(mondo::Cella::MIASMA))
        {
            esplorazione.nascondi_etichetta();
            lampo(2, bn::fixed(0.6));
        }

        // le scene a schermo intero che quella appena finita rende pronte partono subito, senza camminare:
        // la vetrata di E-02 dopo la terza alba (E-01), come il prologo all'avvio
        if(recita(k, &esplorazione, palette_testo))
        {
            for(int j = prossima_scena(g_game_state, NESSUNA_AREA); j >= 0; j = prossima_scena(g_game_state, NESSUNA_AREA))
            {
                recita(j, &esplorazione, palette_testo);
            }
        }

        svuota();       // la fase puo' essere cambiata: gli NPC si rifanno al prossimo frame
        return true;
    }

    // i miasmi: chi corre nella nebbia lascia indietro Ubaldo e si ferisce (poco, mai a morte)
    bool corre = bn::keypad::b_held() && (bn::keypad::left_held() || bn::keypad::right_held() ||
                                          bn::keypad::up_held() || bn::keypad::down_held());

    if(respira_i_miasmi(g_game_state, cella, corre, _respiro))
    {
        BN_LOG("Miasmi: ferite ", int(g_game_state.ferite[1]), " ", int(g_game_state.ferite[2]));
        lampo(1, bn::fixed(0.25));
    }

    // un forziere si apre toccandolo: l'oggetto, la bandiera; resta li' aperto
    int z = forziere_toccato(g_game_state, int(e.area), e.x, e.y);

    if(z >= 0 && apri_forziere(g_game_state, z))
    {
        BN_LOG("Forziere ", z);
        di_sistema(GUBBIO_VOCE(FORZIERE, z).testo, &esplorazione, palette_testo);
        svuota();       // il forziere si rifa' aperto al prossimo frame
        return true;
    }

    // un oggetto da raccogliere si prende toccandolo: il contatore sale, le righe di raccolta della quest
    int r = raccolta_toccata(g_game_state, int(e.area), e.x, e.y);

    if(r >= 0)
    {
        raccogli(g_game_state, r);
        BN_LOG("Raccolta ", r);
        dialogo_inizio(&esplorazione);
        recita_righe(GUBBIO_VOCE(QUEST_GIOCO, GUBBIO_VOCE(RACCOLTA, r).quest).raccolta, palette_testo);
        dialogo_fine();
        svuota();       // l'oggetto sparisce: si rifa' tutto al prossimo frame
        return true;
    }

    if(! bn::keypad::a_pressed())
    {
        return false;
    }

    for(int j = 0; j < _indici.size(); ++j)
    {
        int indice = _indici[j];
        Posto qui = posto_di(indice);
        int dx = e.x - mondo::piedi_x(qui.tx);
        int dy = e.y - mondo::piedi_y(qui.ty);

        if(dx > -DISTANZA_PAROLA && dx < DISTANZA_PAROLA && dy > -DISTANZA_PAROLA && dy < DISTANZA_PAROLA)
        {
            dialogo_inizio(&esplorazione);

            if(indice == NPC + QUEST)
            {
                _affronta_l_infiltrato(esplorazione, palette_testo);
                dialogo_fine();
                svuota();
                return true;
            }

            if(indice >= NPC)
            {
                _parla_col_datore(indice - NPC, palette_testo);
                dialogo_fine();
                svuota();   // il datore puo' essere passato al dopo
                return true;
            }

            const Npc& n = GUBBIO_VOCE(NPC_AMBIENTE, indice);
            int fase = int(fase_npc(g_game_state));
            recita_battute(FRASE_NPC, GUBBIO_VOCE(n.prima_frase, fase), GUBBIO_VOCE(n.frasi, fase), palette_testo, false,
                           true);

            if((n.imposta_fasi >> fase) & 1)
            {
                accendi_una(g_game_state, n.imposta);
            }

            // Q-SP01: dopo le sue battute (Giordano ha gia' acceso INDIZIO_ACQUA), l'indizio; col terzo, l'infiltrato
            int k = indizio_dell_npc(g_game_state, indice);

            if(k >= 0)
            {
                recita_righe(GUBBIO_VOCE(INDIZIO, k).righe, palette_testo);

                if(trova_indizio(g_game_state, k))
                {
                    recita_righe(INDIZI_COMPLETI, palette_testo);
                }

                svuota();   // l'infiltrato puo' essere comparso
            }

            dialogo_fine();
            return true;
        }
    }

    return false;
}

void prova_storia(const bn::sprite_palette_ptr& palette_testo)
{
    // due giri: nel primo ogni menu prende la prima voce, nel secondo la seconda
    int visitate = 0;
    int mancanti = 0;

    for(int giro = 0; giro < 2; ++giro)
    {
    g_game_state = GameState{};
    progressione::partita_nuova(g_game_state);
    s_voce_automatica = giro;
    Storia storia;
    BN_LOG("Giro ", giro);
    bool avanti = true;
    visitate = 0;

    // lo stesso giro di storia::gioca_tutta, ma recitando ogni scena a schermo
    while(avanti)
    {
        avanti = false;

        for(int k = 0; k < SCENE && ! avanti; ++k)
        {
            if(pronta(g_game_state, k, GUBBIO_VOCE(SCENA, k).area) && storia.recita(k, nullptr, palette_testo, true))
            {
                ++visitate;
                avanti = true;
            }
        }

        // con «Non ancora» in B-05 la conferma dell'alba la da' il console Guido
        if(! avanti && risposta_di_un_npc(g_game_state))
        {
            BN_LOG("Risposta a un NPC");
            avanti = true;
        }
    }

    for(int k = 0; k < SCENE; ++k)
    {
        if(! fatta(g_game_state, k))
        {
            BN_LOG("Scena NON visitata: ", GUBBIO_VOCE(SCENA, k).codice);
            ++mancanti;
        }
    }

    BN_LOG("Giro ", giro, ": ", visitate, " scene, borgo ", accesa(g_game_state, Bandiera::BORGO_DENTRO) ? "dentro" : "fuori",
           ", esule ", accesa(g_game_state, Bandiera::ESULE_PRIGIONIERO) ? "prigioniero" : "liberato",
           ", giustizia ", accesa(g_game_state, Bandiera::GIUSTIZIA_OFFERTA) ? "offerta" : "no");
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

void prova_figure_npc(Esplorazione& esplorazione, const bn::sprite_palette_ptr& palette_testo)
{
    esplorazione.entra(mondo::AreaId::PIAZZA_GRANDE, 0);
    bn::sprite_palette_ptr palette = palette_npc();
    bn::vector<bn::sprite_ptr, FIGURE_NPC> figure;
    const mondo::Esploratore& e = esplorazione.esploratore();

    // tutte le figure in file da dieci davanti al giocatore
    for(int f = 0; f < FIGURE_NPC; ++f)
    {
        bn::sprite_ptr sprite = crea_npc(palette, f);
        esplorazione.colloca_sulla_mappa(sprite, e.x + (f % 10) * 22 - 99, e.y - 44 + (f / 10) * 34, ALTEZZA_NPC);
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

    // il menu del dilemma della popolana (D3), come lo vede chi le parla col pane in tasca
    figure.clear();

    for(int i = 0; i < FRASI_NPC; ++i)
    {
        if(GUBBIO_VOCE(FRASE_NPC, i).tipo == TipoBattuta::SCELTA)
        {
            menu_scelta(GUBBIO_VOCE(FRASE_NPC, i), palette_testo, true);
            break;
        }
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
