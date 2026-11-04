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

// Le battute della scena da 'da' ad 'a' (indici in BATTUTA, 'a' escluso), spezzate dove entra una cutscene
// (INSERTO). Una scena con la battaglia a meta' (B-03) si recita in due tratti, prima e dopo la battaglia.
void Storia::recita_tratto(int da, int a, Esplorazione* esplorazione, const bn::sprite_palette_ptr& palette_testo,
                           bool automatica)
{
    for(int i = 0; i < INSERTI; ++i)
    {
        const Inserto& n = GUBBIO_VOCE(INSERTO, i);

        if(n.battuta >= da && n.battuta < a)
        {
            recita_battute(BATTUTA, da, n.battuta - da, palette_testo, automatica);
            da = n.battuta;

            // le battute del narratore che la cutscene ha detto nelle bande non si ripetono; se era gia'
            // vista (la scena rigiocata dopo una battaglia persa) si leggono nella vista di gioco
            if(recita_regia(n.regia, esplorazione, palette_testo, automatica))
            {
                da = da + n.copre < a ? da + n.copre : a;
            }

            if(esplorazione)
            {
                bn::bg_palettes::set_fade(bn::color(0, 0, 0), bn::fixed(0.6));
            }
        }
    }

    recita_battute(BATTUTA, da, a - da, palette_testo, automatica);
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
        // le battute fino alla battaglia (alla fine, o a meta' scena come in B-03)
        recita_tratto(s.prima_battuta, battuta_della_battaglia(k), esplorazione, palette_testo, automatica);
